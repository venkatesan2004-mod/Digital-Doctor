from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.entities import (
    Patient, ConsultationSession, ClinicalEncounter,
    HistoricalPrescription, LaboratoryResult, RadiologyReport,
    VitalSign, Symptom
)
from app.security.auth import get_current_user_claims, require_authenticated_staff

router = APIRouter(prefix="/clinical-records", tags=["Clinical Records & History"])


@router.get("/session/{session_id}/history")
def get_session_clinical_history(
    session_id: str,
    db: Session = Depends(get_db),
    claims: dict = Depends(get_current_user_claims)
):
    """
    Returns authorized clinical history for the patient linked to this session.
    Enforces strict patient-level boundary access.
    """
    session = db.query(ConsultationSession).filter(
        ConsultationSession.session_id == session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Consultation session not found.")

    if claims.get("token_type") == "kiosk" and session.patient_id != claims.get("patient_id"):
        raise HTTPException(status_code=403, detail="Forbidden: Cross-patient data access denied.")

    patient_id = session.patient_id

    # Encounters
    encounters = db.query(ClinicalEncounter).filter(
        ClinicalEncounter.patient_id == patient_id
    ).order_by(ClinicalEncounter.encounter_date.desc()).all()

    # Prescriptions
    prescriptions = db.query(HistoricalPrescription).filter(
        HistoricalPrescription.patient_id == patient_id
    ).order_by(HistoricalPrescription.prescribed_date.desc()).all()

    # Labs
    labs = db.query(LaboratoryResult).filter(
        LaboratoryResult.patient_id == patient_id
    ).order_by(LaboratoryResult.performed_at.desc()).all()

    # Radiology
    radiology = db.query(RadiologyReport).filter(
        RadiologyReport.patient_id == patient_id
    ).order_by(RadiologyReport.reported_at.desc()).all()

    return {
        "patient_id": patient_id,
        "encounters": [
            {
                "id": e.id,
                "date": e.encounter_date.isoformat(),
                "chief_complaint": e.chief_complaint,
                "summary": e.clinical_summary,
                "source": e.provenance_source.value,
            }
            for e in encounters
        ],
        "prescriptions": [
            {
                "id": p.id,
                "date": p.prescribed_date.isoformat(),
                "medication_name": p.medication_name,
                "dosage": p.dosage,
                "frequency": p.frequency,
                "duration": p.duration,
                "instructions": p.instructions,
                "source": p.provenance_source.value,
            }
            for p in prescriptions
        ],
        "laboratory_results": [
            {
                "id": l.id,
                "date": l.performed_at.isoformat(),
                "test_name": l.test_name,
                "result_value": l.result_value,
                "reference_range": l.reference_range,
                "is_abnormal": l.is_abnormal,
                "reported_by": l.reported_by,
                "source": l.provenance_source.value,
            }
            for l in labs
        ],
        "radiology_reports": [
            {
                "id": r.id,
                "date": r.reported_at.isoformat(),
                "procedure_name": r.procedure_name,
                "modality": r.modality,
                "findings": r.findings,
                "impression": r.impression,
                "is_abnormal": r.is_abnormal,
                "radiologist": r.radiologist_name,
                "source": r.provenance_source.value,
            }
            for r in radiology
        ]
    }


@router.get("/patient/{patient_id}")
def get_patient_record_for_staff(
    patient_id: int,
    db: Session = Depends(get_db),
    staff_claims: dict = Depends(require_authenticated_staff)
):
    """Staff dashboard view for full clinical history of a patient."""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found.")

    return {
        "id": patient.id,
        "mrn": patient.mrn,
        "full_name": f"{patient.first_name} {patient.last_name}",
        "date_of_birth": patient.date_of_birth,
        "gender": patient.gender,
        "contact_phone": patient.contact_phone,
        "contact_email": patient.contact_email,
        "preferred_language": patient.preferred_language,
        "registrations_count": len(patient.registrations),
        "sessions_count": len(patient.sessions),
    }
