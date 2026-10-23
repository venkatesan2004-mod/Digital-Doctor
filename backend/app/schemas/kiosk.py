from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from app.models.entities import SessionStatus


class KioskLookupRequest(BaseModel):
    registration_number: str = Field(..., min_length=3, max_length=64)


class KioskLookupResponse(BaseModel):
    registration_number: str
    masked_patient_name: str
    department_name: str
    doctor_name: str
    preferred_language: str
    verification_factor_prompt: str
    requires_verification: bool = True


class KioskVerifyRequest(BaseModel):
    registration_number: str
    verification_factor: str = Field(..., description="Birth year (e.g. 1985) or demo PIN (e.g. 1234)")


class ResumableSessionInfo(BaseModel):
    session_id: str
    started_at: datetime
    last_activity_at: datetime
    status: SessionStatus
    language_preference: str
    assigned_doctor_name: str
    message_count: int


class KioskAuthResponse(BaseModel):
    session_token: str
    token_type: str = "bearer"
    expires_in_seconds: int
    registration_number: str
    patient_id: int
    patient_full_name: str
    patient_mrn: str
    department_name: str
    doctor_name: str
    doctor_id: int
    language_preference: str
    resumable_sessions: List[ResumableSessionInfo] = []


class CreateOrResumeSessionRequest(BaseModel):
    registration_number: str
    existing_session_id: Optional[str] = None
    language_preference: Optional[str] = "en"


class KioskSessionDetail(BaseModel):
    session_id: str
    registration_number: str
    patient_id: int
    patient_mrn: str
    patient_name: str
    department_name: str
    doctor_name: str
    status: SessionStatus
    language_preference: str
    started_at: datetime
    last_activity_at: datetime
    is_resumed: bool


class CloseSessionRequest(BaseModel):
    session_id: str
    reason: Optional[str] = "Patient Completed Consultation"


class CloseSessionResponse(BaseModel):
    session_id: str
    status: str = "CLOSED"
    message: str
    closed_at: datetime
