import uuid
import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.models.entities import (
    Patient, Registration, Department, Doctor,
    ConsultationType, RegistrationStatus, StaffRole
)
from app.schemas.front_office import PatientRegistrationRequest, RegistrationResponse
from app.integrations.hims.adapter import get_hims_adapter
from app.security.auth import hash_secondary_factor, require_role, require_authenticated_staff
from app.audit.service import AuditService

router = APIRouter(prefix="/front-office", tags=["Front Office & HIMS"])


@router.get("/departments")
def list_departments(db: Session = Depends(get_db)):
    """Returns all active hospital departments."""
    deps = db.query(Department).filter(Department.is_active == True).all()
    return [{"id": d.id, "code": d.code, "name": d.name, "description": d.description} for d in deps]


@router.get("/doctors")
def list_doctors(
    department_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Returns active doctors, optionally filtered by department."""
    query = db.query(Doctor).filter(Doctor.is_active == True)
    if department_id:
        query = query.filter(Doctor.department_id == department_id)
    doctors = query.all()
    return [
        {
            "id": doc.id,
            "full_name": doc.full_name,
            "specialization": doc.specialization,
            "employee_id": doc.employee_id,
            "department_id": doc.department_id,
            "department_name": doc.department.name if doc.department else "General"
        }
        for doc in doctors
    ]


@router.post("/register", response_model=RegistrationResponse)
def register_patient(
    payload: PatientRegistrationRequest,
    db: Session = Depends(get_db),
    staff_claims: dict = Depends(require_role([StaffRole.FRONT_OFFICE, StaffRole.ADMIN]))
):
    """
    Front-Office registration with explicit dual-pathway routing.
    - DIRECT_DOCTOR: Dispatches to external/mock HIMS; does not enter kiosk workflow.
    - DIGITAL_DOCTOR: Enters self-service kiosk system.
    """
    # 1. Validate department and doctor
    department = db.query(Department).filter(Department.id == payload.department_id).first()
    if not department:
        raise HTTPException(status_code=400, detail="Invalid department ID.")

    doctor = db.query(Doctor).filter(Doctor.id == payload.assigned_doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=400, detail="Invalid doctor ID.")

    # 2. Find or create patient record (by phone & name)
    patient = db.query(Patient).filter(
        Patient.contact_phone == payload.contact_phone.strip(),
        Patient.first_name == payload.first_name.strip(),
        Patient.last_name == payload.last_name.strip()
    ).first()

    if not patient:
        mrn = f"MRN-{uuid.uuid4().hex[:8].upper()}"
        patient = Patient(
            mrn=mrn,
            first_name=payload.first_name.strip(),
            last_name=payload.last_name.strip(),
            date_of_birth=payload.date_of_birth.strip(),
            gender=payload.gender.strip(),
            contact_phone=payload.contact_phone.strip(),
            contact_email=payload.contact_email,
            address=payload.address,
            preferred_language=payload.preferred_language,
        )
        db.add(patient)
        db.commit()
        db.refresh(patient)

    # 3. Handle DIRECT_DOCTOR pathway
    if payload.consultation_type == ConsultationType.DIRECT_DOCTOR:
        hims_adapter = get_hims_adapter()
        hims_result = hims_adapter.dispatch_direct_consultation({
            "mrn": patient.mrn,
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "department": department.name,
            "doctor": doctor.full_name,
        })

        AuditService.log_event(
            db=db,
            event_type="FRONT_OFFICE_DIRECT_DOCTOR_DISPATCH",
            actor_type="STAFF",
            actor_id=str(staff_claims.get("user_id")),
            patient_id=patient.id,
            resource_type="HIMS_DISPATCH",
            details=hims_result
        )

        return RegistrationResponse(
            registration_id=0,
            registration_number=hims_result.get("hims_ticket_number", "DIRECT-HIMS"),
            patient_mrn=patient.mrn,
            patient_full_name=f"{patient.first_name} {patient.last_name}",
            consultation_type=ConsultationType.DIRECT_DOCTOR,
            status=RegistrationStatus.ACTIVE,
            department_name=department.name,
            doctor_name=doctor.full_name,
            registration_time=datetime.datetime.utcnow(),
            message="Direct Doctor Consultation: Patient transferred to standard hospital OPD queue. No digital kiosk session created.",
            kiosk_eligible=False,
            hims_dispatch_status="DISPATCHED_TO_HIMS"
        )

    # 4. Handle DIGITAL_DOCTOR pathway
    reg_number = f"DD-{datetime.datetime.utcnow().strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}"
    sec_factor = payload.secondary_verification_pin or payload.date_of_birth.split("-")[0] or str(settings.DEMO_VERIFICATION_DEFAULT_YEAR)
    sec_hash = hash_secondary_factor(sec_factor)

    registration = Registration(
        registration_number=reg_number,
        patient_id=patient.id,
        department_id=department.id,
        assigned_doctor_id=doctor.id,
        consultation_type=ConsultationType.DIGITAL_DOCTOR,
        status=RegistrationStatus.ACTIVE,
        secondary_verification_hash=sec_hash,
    )
    db.add(registration)
    db.commit()
    db.refresh(registration)

    AuditService.log_event(
        db=db,
        event_type="FRONT_OFFICE_DIGITAL_DOCTOR_REGISTERED",
        actor_type="STAFF",
        actor_id=str(staff_claims.get("user_id")),
        patient_id=patient.id,
        resource_type="REGISTRATION",
        details={"registration_number": reg_number, "doctor_id": doctor.id}
    )

    return RegistrationResponse(
        registration_id=registration.id,
        registration_number=registration.registration_number,
        patient_mrn=patient.mrn,
        patient_full_name=f"{patient.first_name} {patient.last_name}",
        consultation_type=ConsultationType.DIGITAL_DOCTOR,
        status=registration.status,
        department_name=department.name,
        doctor_name=doctor.full_name,
        registration_time=registration.registration_time,
        message="Digital Doctor Consultation: Registration confirmed. Patient may proceed to the Self-Service Kiosk.",
        kiosk_eligible=True,
        hims_dispatch_status=None
    )


@router.get("/registrations")
def list_registrations(
    consultation_type: Optional[ConsultationType] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    staff_claims: dict = Depends(require_authenticated_staff)
):
    """Lists recent front-office registrations."""
    query = db.query(Registration).order_by(Registration.created_at.desc())
    if consultation_type:
        query = query.filter(Registration.consultation_type == consultation_type)
    registrations = query.limit(limit).all()

    return [
        {
            "id": r.id,
            "registration_number": r.registration_number,
            "patient_name": f"{r.patient.first_name} {r.patient.last_name}",
            "patient_mrn": r.patient.mrn,
            "consultation_type": r.consultation_type.value,
            "status": r.status.value,
            "department": r.department.name,
            "assigned_doctor": r.assigned_doctor.full_name,
            "registration_time": r.registration_time.isoformat(),
        }
        for r in registrations
    ]
