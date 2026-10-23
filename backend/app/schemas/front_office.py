from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.models.entities import ConsultationType, RegistrationStatus


class PatientRegistrationRequest(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=64)
    last_name: str = Field(..., min_length=1, max_length=64)
    date_of_birth: str = Field(..., description="Format: YYYY-MM-DD")
    gender: str = Field(..., description="Male, Female, or Other")
    contact_phone: str = Field(..., min_length=7, max_length=20)
    contact_email: Optional[str] = None
    address: Optional[str] = None
    preferred_language: str = Field("en", description="en or ta")
    department_id: int
    assigned_doctor_id: int
    consultation_type: ConsultationType
    secondary_verification_pin: Optional[str] = Field(
        None,
        description="Demo synthetic 4-digit PIN or year of birth for secondary verification"
    )


class RegistrationResponse(BaseModel):
    registration_id: int
    registration_number: str
    patient_mrn: str
    patient_full_name: str
    consultation_type: ConsultationType
    status: RegistrationStatus
    department_name: str
    doctor_name: str
    registration_time: datetime
    message: str
    kiosk_eligible: bool
    hims_dispatch_status: Optional[str] = None
