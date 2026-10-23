import uuid
import datetime
from datetime import timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.models.entities import (
    Registration, ConsultationSession, Patient, Doctor,
    ConsultationType, SessionStatus, RegistrationStatus
)
from app.schemas.kiosk import (
    KioskLookupRequest, KioskLookupResponse,
    KioskVerifyRequest, KioskAuthResponse, ResumableSessionInfo,
    CreateOrResumeSessionRequest, KioskSessionDetail,
    CloseSessionRequest, CloseSessionResponse
)
from app.security.auth import (
    hash_secondary_factor, create_access_token, require_kiosk_session
)
from app.security.rate_limiter import kiosk_rate_limiter
from app.audit.service import AuditService

router = APIRouter(prefix="/kiosk", tags=["Kiosk Consultation"])


def mask_name(first_name: str, last_name: str) -> str:
    """Masks patient name for unverified public kiosk screen privacy."""
    f = first_name[0] + "***" if first_name else "*"
    l = last_name[0] + "***" if last_name else "*"
    return f"{f} {l}"


@router.post("/lookup", response_model=KioskLookupResponse)
def lookup_registration(payload: KioskLookupRequest, request: Request, db: Session = Depends(get_db)):
    """
    Patient enters Registration ID at the kiosk.
    Rate-limited to prevent brute-force probing.
    Returns masked information and requests secondary verification.
    """
    client_ip = request.client.host if request.client else "unknown"
    kiosk_rate_limiter.check_rate_limit(f"lookup_{client_ip}")

    reg = db.query(Registration).filter(
        Registration.registration_number == payload.registration_number.strip()
    ).first()

    # Generic error if not found or direct-doctor workflow to avoid enumeration
    if not reg or reg.consultation_type != ConsultationType.DIGITAL_DOCTOR:
        kiosk_rate_limiter.record_attempt(f"lookup_{client_ip}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registration not found or not registered for Digital Doctor kiosk. Please verify with front desk."
        )

    patient = reg.patient
    return KioskLookupResponse(
        registration_number=reg.registration_number,
        masked_patient_name=mask_name(patient.first_name, patient.last_name),
        department_name=reg.department.name,
        doctor_name=reg.assigned_doctor.full_name,
        preferred_language=patient.preferred_language,
        verification_factor_prompt="Please enter your 4-digit Year of Birth (e.g. 1985) or Demo PIN to verify identity:",
        requires_verification=True
    )


@router.post("/verify", response_model=KioskAuthResponse)
def verify_patient_identity(payload: KioskVerifyRequest, request: Request, db: Session = Depends(get_db)):
    """
    Verifies secondary factor (DOB/PIN) and issues temporary kiosk session authorization token.
    """
    client_ip = request.client.host if request.client else "unknown"
    kiosk_rate_limiter.check_rate_limit(f"verify_{payload.registration_number}")

    reg = db.query(Registration).filter(
        Registration.registration_number == payload.registration_number.strip()
    ).first()

    if not reg or reg.consultation_type != ConsultationType.DIGITAL_DOCTOR:
        kiosk_rate_limiter.record_attempt(f"verify_{payload.registration_number}")
        raise HTTPException(status_code=404, detail="Invalid registration.")

    computed_hash = hash_secondary_factor(payload.verification_factor)
    if computed_hash != reg.secondary_verification_hash:
        kiosk_rate_limiter.record_attempt(f"verify_{payload.registration_number}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Verification factor did not match our records. Please try again."
        )

    # Verification succeeded; clear rate limit
    kiosk_rate_limiter.clear(f"verify_{payload.registration_number}")

    patient = reg.patient

    # Find resumable sessions for this registration
    active_sessions = db.query(ConsultationSession).filter(
        ConsultationSession.registration_id == reg.id,
        ConsultationSession.status.in_([SessionStatus.ACTIVE, SessionStatus.CREATED, SessionStatus.AWAITING_CLINICIAN_REVIEW])
    ).order_by(ConsultationSession.last_activity_at.desc()).all()

    resumable_list = []
    for s in active_sessions:
        resumable_list.append(ResumableSessionInfo(
            session_id=s.session_id,
            started_at=s.started_at,
            last_activity_at=s.last_activity_at,
            status=s.status,
            language_preference=s.language_preference,
            assigned_doctor_name=s.assigned_doctor.full_name,
            message_count=len(s.messages)
        ))

    # Issue short-lived kiosk token
    token_claims = {
        "token_type": "kiosk",
        "registration_id": reg.id,
        "registration_number": reg.registration_number,
        "patient_id": patient.id,
        "patient_name": f"{patient.first_name} {patient.last_name}",
        "doctor_id": reg.assigned_doctor_id,
    }
    session_token = create_access_token(
        subject=reg.registration_number,
        claims=token_claims,
        expires_delta=timedelta(minutes=settings.KIOSK_SESSION_TIMEOUT_MINUTES)
    )

    AuditService.log_event(
        db=db,
        event_type="KIOSK_PATIENT_VERIFIED",
        actor_type="PATIENT",
        actor_id=str(patient.id),
        patient_id=patient.id,
        resource_type="KIOSK_SESSION",
        details={"registration_number": reg.registration_number}
    )

    return KioskAuthResponse(
        session_token=session_token,
        token_type="bearer",
        expires_in_seconds=settings.KIOSK_SESSION_TIMEOUT_MINUTES * 60,
        registration_number=reg.registration_number,
        patient_id=patient.id,
        patient_full_name=f"{patient.first_name} {patient.last_name}",
        patient_mrn=patient.mrn,
        department_name=reg.department.name,
        doctor_name=reg.assigned_doctor.full_name,
        doctor_id=reg.assigned_doctor_id,
        language_preference=patient.preferred_language,
        resumable_sessions=resumable_list
    )


@router.post("/session/create-or-resume", response_model=KioskSessionDetail)
def create_or_resume_session(
    payload: CreateOrResumeSessionRequest,
    kiosk_claims: dict = Depends(require_kiosk_session),
    db: Session = Depends(get_db)
):
    """Initializes a new consultation session or resumes an existing eligible session."""
    reg = db.query(Registration).filter(
        Registration.registration_number == payload.registration_number
    ).first()

    if not reg or reg.patient_id != kiosk_claims.get("patient_id"):
        raise HTTPException(status_code=403, detail="Unauthorized registration access.")

    # Check resumption
    if payload.existing_session_id:
        existing = db.query(ConsultationSession).filter(
            ConsultationSession.session_id == payload.existing_session_id,
            ConsultationSession.registration_id == reg.id
        ).first()

        if existing and existing.status in [SessionStatus.ACTIVE, SessionStatus.CREATED, SessionStatus.AWAITING_CLINICIAN_REVIEW]:
            existing.last_activity_at = datetime.datetime.utcnow()
            db.commit()
            db.refresh(existing)
            return KioskSessionDetail(
                session_id=existing.session_id,
                registration_number=reg.registration_number,
                patient_id=reg.patient.id,
                patient_mrn=reg.patient.mrn,
                patient_name=f"{reg.patient.first_name} {reg.patient.last_name}",
                department_name=reg.department.name,
                doctor_name=reg.assigned_doctor.full_name,
                status=existing.status,
                language_preference=existing.language_preference,
                started_at=existing.started_at,
                last_activity_at=existing.last_activity_at,
                is_resumed=True
            )

    # Otherwise create fresh session
    new_session_id = str(uuid.uuid4())
    session = ConsultationSession(
        session_id=new_session_id,
        registration_id=reg.id,
        patient_id=reg.patient_id,
        assigned_doctor_id=reg.assigned_doctor_id,
        status=SessionStatus.ACTIVE,
        language_preference=payload.language_preference or reg.patient.preferred_language or "en",
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    AuditService.log_event(
        db=db,
        event_type="CONSULTATION_SESSION_CREATED",
        actor_type="PATIENT",
        actor_id=str(reg.patient_id),
        session_id=new_session_id,
        patient_id=reg.patient_id,
        resource_type="CONSULTATION_SESSION",
        details={"session_id": new_session_id}
    )

    return KioskSessionDetail(
        session_id=session.session_id,
        registration_number=reg.registration_number,
        patient_id=reg.patient.id,
        patient_mrn=reg.patient.mrn,
        patient_name=f"{reg.patient.first_name} {reg.patient.last_name}",
        department_name=reg.department.name,
        doctor_name=reg.assigned_doctor.full_name,
        status=session.status,
        language_preference=session.language_preference,
        started_at=session.started_at,
        last_activity_at=session.last_activity_at,
        is_resumed=False
    )


@router.post("/session/close", response_model=CloseSessionResponse)
def close_consultation_session(
    payload: CloseSessionRequest,
    kiosk_claims: dict = Depends(require_kiosk_session),
    db: Session = Depends(get_db)
):
    """
    Terminates active consultation session.
    Preserves all records in MySQL and invalidates kiosk active state.
    """
    session = db.query(ConsultationSession).filter(
        ConsultationSession.session_id == payload.session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    if session.patient_id != kiosk_claims.get("patient_id"):
        raise HTTPException(status_code=403, detail="Forbidden: session ownership mismatch.")

    session.status = SessionStatus.CLOSED
    session.closed_at = datetime.datetime.utcnow()
    session.closure_reason = payload.reason
    db.commit()

    AuditService.log_event(
        db=db,
        event_type="CONSULTATION_SESSION_CLOSED",
        actor_type="PATIENT",
        actor_id=str(session.patient_id),
        session_id=session.session_id,
        patient_id=session.patient_id,
        resource_type="CONSULTATION_SESSION",
        details={"closure_reason": payload.reason}
    )

    return CloseSessionResponse(
        session_id=session.session_id,
        status="CLOSED",
        message="Consultation closed securely. Records saved to hospital repository. Kiosk session reset.",
        closed_at=session.closed_at
    )
