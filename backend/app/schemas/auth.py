from typing import Optional
from pydantic import BaseModel, EmailStr


class StaffLoginRequest(BaseModel):
    username: str
    password: str


class StaffTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int
    role: str
    full_name: str
    username: str
    doctor_id: Optional[int] = None


class StaffUserProfile(BaseModel):
    id: int
    username: str
    email: str
    role: str
    full_name: str
    is_active: bool
    doctor_id: Optional[int] = None
