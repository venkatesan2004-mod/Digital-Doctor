from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.models.entities import StaffUser, Doctor
from app.schemas.auth import StaffLoginRequest, StaffTokenResponse, StaffUserProfile
from app.security.auth import verify_password, create_access_token, require_authenticated_staff
from app.audit.service import AuditService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/staff/login", response_model=StaffTokenResponse)
def staff_login(payload: StaffLoginRequest, db: Session = Depends(get_db)):
    """Authenticates hospital clinical or administrative staff members."""
    user = db.query(StaffUser).filter(StaffUser.username == payload.username.strip()).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff account has been deactivated. Contact Hospital IT.",
        )

    doctor_id = None
    if user.doctor_profile:
        doctor_id = user.doctor_profile.id

    token_claims = {
        "token_type": "staff",
        "user_id": user.id,
        "username": user.username,
        "role": user.role.value,
        "full_name": user.full_name,
        "doctor_id": doctor_id,
    }

    access_token = create_access_token(
        subject=str(user.id),
        claims=token_claims,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    AuditService.log_event(
        db=db,
        event_type="STAFF_LOGIN_SUCCESS",
        actor_type="STAFF",
        actor_id=str(user.id),
        resource_type="STAFF_USER",
        details={"username": user.username, "role": user.role.value}
    )

    return StaffTokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        role=user.role.value,
        full_name=user.full_name,
        username=user.username,
        doctor_id=doctor_id,
    )


@router.get("/staff/me", response_model=StaffUserProfile)
def get_staff_me(
    claims: dict = Depends(require_authenticated_staff),
    db: Session = Depends(get_db)
):
    """Retrieves authenticated staff profile."""
    user = db.query(StaffUser).filter(StaffUser.id == claims.get("user_id")).first()
    if not user:
        raise HTTPException(status_code=404, detail="Staff user record not found.")

    return StaffUserProfile(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role.value,
        full_name=user.full_name,
        is_active=user.is_active,
        doctor_id=user.doctor_profile.id if user.doctor_profile else None
    )
