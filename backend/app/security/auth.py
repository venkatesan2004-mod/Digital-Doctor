import os
import hashlib
import hmac
import time
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List

import jwt
from fastapi import HTTPException, Security, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
from app.core.logging import logger
from app.models.entities import StaffRole

security_bearer = HTTPBearer(auto_error=False)


# ==============================================================================
# SECURE PASSWORD HASHING (Argon2id with PBKDF2 Fallback)
# ==============================================================================

def hash_password(password: str) -> str:
    """Hashes a password using Argon2id or secure PBKDF2 HMAC SHA-256."""
    try:
        from argon2 import PasswordHasher
        ph = PasswordHasher()
        return ph.hash(password)
    except ImportError:
        # Fallback to PBKDF2 with 200,000 iterations and 16-byte random salt
        salt = os.urandom(16).hex()
        key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 200000)
        return f"pbkdf2${salt}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against an Argon2id or PBKDF2 hash."""
    if not hashed_password or not plain_password:
        return False
    try:
        if hashed_password.startswith("$argon2"):
            from argon2 import PasswordHasher
            ph = PasswordHasher()
            return ph.verify(hashed_password, plain_password)
        elif hashed_password.startswith("pbkdf2$"):
            parts = hashed_password.split("$")
            if len(parts) == 3:
                salt = parts[1]
                expected_key = parts[2]
                computed = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 200000).hex()
                return hmac.compare_digest(computed, expected_key)
        # Fallback for plain synthetic demo hashes if any
        return hmac.compare_digest(hashlib.sha256(plain_password.encode("utf-8")).hexdigest(), hashed_password)
    except Exception as e:
        logger.warning(f"Password verification encountered an error: {str(e)}")
        return False


def hash_secondary_factor(factor: str) -> str:
    """Hashes a secondary patient verification factor (such as DOB or demo PIN)."""
    normalized = factor.strip().replace("-", "").replace("/", "")
    return hashlib.sha256(f"dd_salt_{normalized}".encode("utf-8")).hexdigest()


# ==============================================================================
# JWT TOKEN GENERATION & DECODING
# ==============================================================================

def create_access_token(
    subject: str,
    claims: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """Encodes a signed JWT access token for staff or kiosk session."""
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        **claims
    }
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    """Decodes and validates a JWT token; raises HTTP 401 on failure."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session token has expired. Please authenticate or verify again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or malformed authentication credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ==============================================================================
# AUTHENTICATION DEPENDENCIES
# ==============================================================================

def get_current_user_claims(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer)
) -> Dict[str, Any]:
    """Validates the Authorization Bearer header and extracts payload claims."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_token(credentials.credentials)


def require_authenticated_staff(
    claims: Dict[str, Any] = Depends(get_current_user_claims)
) -> Dict[str, Any]:
    """Ensures token belongs to authenticated hospital staff."""
    if claims.get("token_type") != "staff":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Staff credentials required."
        )
    return claims


def require_role(allowed_roles: List[StaffRole]):
    """Returns a dependency checking if the staff user possesses one of the allowed roles."""
    def role_checker(claims: Dict[str, Any] = Depends(require_authenticated_staff)) -> Dict[str, Any]:
        user_role = claims.get("role")
        # System ADMIN has access to all clinical/staff views
        if user_role == StaffRole.ADMIN.value:
            return claims
        if user_role not in [r.value for r in allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Action requires one of roles {[r.value for r in allowed_roles]}."
            )
        return claims
    return role_checker


def require_kiosk_session(
    claims: Dict[str, Any] = Depends(get_current_user_claims)
) -> Dict[str, Any]:
    """Ensures token is an active, verified patient kiosk session token."""
    if claims.get("token_type") != "kiosk":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Active verified kiosk session required."
        )
    return claims
