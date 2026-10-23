import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.entities import (
    MedicationOrder, LaboratoryRequest, RadiologyRequest,
    ClinicianReview, ReviewStatus, StaffRole, Doctor
)
from app.schemas.clinical import (
    ClinicianReviewQueueItem,
    ClinicianReviewActionRequest,
    ClinicianReviewActionResponse
)
from app.security.auth import require_role
from app.audit.service import AuditService

router = APIRouter(prefix="/clinician-review", tags=["Clinician Review & Approval Queue"])


@router.get("/queue", response_model=List[ClinicianReviewQueueItem])
def get_review_queue(
    db: Session = Depends(get_db),
    staff_claims: dict = Depends(require_role([StaffRole.DOCTOR, StaffRole.ADMIN]))
):
    """
    Returns pending AI-drafted clinical orders requiring licensed physician approval.
    Unapproved items are strictly non-dispensable.
    """
    queue_items: List[ClinicianReviewQueueItem] = []

    # 1. Medication Orders in DRAFT_PENDING_REVIEW
    med_orders = db.query(MedicationOrder).filter(
        MedicationOrder.review_status == ReviewStatus.DRAFT_PENDING_REVIEW
    ).order_by(MedicationOrder.created_at.desc()).all()

    for m in med_orders:
        patient = m.session.patient
        queue_items.append(
            ClinicianReviewQueueItem(
                review_id=m.id,
                item_type="MEDICATION_ORDER",
                item_id=m.id,
                session_id=m.session.session_id,
                patient_id=m.patient_id,
                patient_name=f"{patient.first_name} {patient.last_name}",
                patient_mrn=patient.mrn,
                item_title=f"Draft Rx: {m.medication_name} ({m.dosage})",
                item_details=f"Dosage: {m.dosage} | Frequency: {m.frequency} | Duration: {m.duration}",
                clinical_rationale=m.instructions,
                review_status=m.review_status,
                created_at=m.created_at,
                rejection_reason=m.rejection_reason
            )
        )

    # 2. Lab Requests in DRAFT_PENDING_REVIEW
    lab_requests = db.query(LaboratoryRequest).filter(
        LaboratoryRequest.review_status == ReviewStatus.DRAFT_PENDING_REVIEW
    ).order_by(LaboratoryRequest.created_at.desc()).all()

    for l in lab_requests:
        patient = l.session.patient
        queue_items.append(
            ClinicianReviewQueueItem(
                review_id=l.id,
                item_type="LAB_REQUEST",
                item_id=l.id,
                session_id=l.session.session_id,
                patient_id=l.patient_id,
                patient_name=f"{patient.first_name} {patient.last_name}",
                patient_mrn=patient.mrn,
                item_title=f"Draft Lab: {l.test_name} ({l.urgency})",
                item_details=f"Test: {l.test_name} | Urgency: {l.urgency}",
                clinical_rationale=l.clinical_notes,
                review_status=l.review_status,
                created_at=l.created_at,
                rejection_reason=l.rejection_reason
            )
        )

    # 3. Radiology Requests in DRAFT_PENDING_REVIEW
    rad_requests = db.query(RadiologyRequest).filter(
        RadiologyRequest.review_status == ReviewStatus.DRAFT_PENDING_REVIEW
    ).order_by(RadiologyRequest.created_at.desc()).all()

    for r in rad_requests:
        patient = r.session.patient
        queue_items.append(
            ClinicianReviewQueueItem(
                review_id=r.id,
                item_type="RADIOLOGY_REQUEST",
                item_id=r.id,
                session_id=r.session.session_id,
                patient_id=r.patient_id,
                patient_name=f"{patient.first_name} {patient.last_name}",
                patient_mrn=patient.mrn,
                item_title=f"Draft Scan: {r.procedure_name}",
                item_details=f"Procedure: {r.procedure_name}",
                clinical_rationale=r.clinical_indication,
                review_status=r.review_status,
                created_at=r.created_at,
                rejection_reason=r.rejection_reason
            )
        )

    return queue_items


@router.post("/action/{item_type}/{item_id}", response_model=ClinicianReviewActionResponse)
def execute_review_action(
    item_type: str,
    item_id: int,
    payload: ClinicianReviewActionRequest,
    db: Session = Depends(get_db),
    staff_claims: dict = Depends(require_role([StaffRole.DOCTOR, StaffRole.ADMIN]))
):
    """
    Physician decision sign-off: Approves or Rejects an AI-generated draft recommendation.
    Only authorized physicians can transition draft orders to APPROVED status.
    """
    now = datetime.datetime.utcnow()
    action_upper = payload.action.upper().strip()
    new_status = ReviewStatus.APPROVED if action_upper == "APPROVE" else ReviewStatus.REJECTED

    doctor_id = staff_claims.get("doctor_id")
    if not doctor_id:
        # Fallback to first doctor if admin
        first_doc = db.query(Doctor).first()
        doctor_id = first_doc.id if first_doc else 1

    item_title = ""
    patient_id = None

    if item_type.upper() == "MEDICATION_ORDER":
        order = db.query(MedicationOrder).filter(MedicationOrder.id == item_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Medication order not found.")
        order.review_status = new_status
        order.reviewed_by_doctor_id = doctor_id
        order.reviewed_at = now
        if new_status == ReviewStatus.REJECTED:
            order.rejection_reason = payload.rejection_reason or payload.notes or "Rejected by physician"
        item_title = order.medication_name
        patient_id = order.patient_id

    elif item_type.upper() == "LAB_REQUEST":
        lab = db.query(LaboratoryRequest).filter(LaboratoryRequest.id == item_id).first()
        if not lab:
            raise HTTPException(status_code=404, detail="Laboratory request not found.")
        lab.review_status = new_status
        lab.reviewed_by_doctor_id = doctor_id
        lab.reviewed_at = now
        if new_status == ReviewStatus.REJECTED:
            lab.rejection_reason = payload.rejection_reason or payload.notes or "Rejected by physician"
        item_title = lab.test_name
        patient_id = lab.patient_id

    elif item_type.upper() == "RADIOLOGY_REQUEST":
        rad = db.query(RadiologyRequest).filter(RadiologyRequest.id == item_id).first()
        if not rad:
            raise HTTPException(status_code=404, detail="Radiology request not found.")
        rad.review_status = new_status
        rad.reviewed_by_doctor_id = doctor_id
        rad.reviewed_at = now
        if new_status == ReviewStatus.REJECTED:
            rad.rejection_reason = payload.rejection_reason or payload.notes or "Rejected by physician"
        item_title = rad.procedure_name
        patient_id = rad.patient_id
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported item type '{item_type}'.")

    # Record historical review log
    review_record = ClinicianReview(
        item_type=item_type.upper(),
        item_id=item_id,
        reviewing_doctor_id=doctor_id,
        action=new_status.value,
        notes=payload.notes,
        reviewed_at=now
    )
    db.add(review_record)
    db.commit()

    AuditService.log_event(
        db=db,
        event_type=f"CLINICIAN_{new_status.value}",
        actor_type="STAFF",
        actor_id=str(staff_claims.get("user_id")),
        patient_id=patient_id,
        resource_type=item_type.upper(),
        details={
            "item_id": item_id,
            "action": new_status.value,
            "title": item_title,
            "doctor_id": doctor_id,
            "notes": payload.notes,
            "rejection_reason": payload.rejection_reason
        }
    )

    return ClinicianReviewActionResponse(
        item_type=item_type.upper(),
        item_id=item_id,
        review_status=new_status,
        message=f"{item_type} marked as {new_status.value} by attending physician.",
        action_recorded_at=now
    )
