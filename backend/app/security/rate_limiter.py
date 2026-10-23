import time
from typing import Dict, List
from fastapi import HTTPException, status
from app.core.config import settings
from app.core.logging import logger


class InMemoryRateLimiter:
    """Sliding-window rate limiter preventing brute-force registration lookup attacks."""

    def __init__(self, max_attempts: int = 5, window_seconds: int = 300):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.attempts: Dict[str, List[float]] = {}

    def check_rate_limit(self, identifier: str) -> None:
        current_time = time.time()
        timestamps = self.attempts.get(identifier, [])

        # Filter out timestamps older than the active window
        valid_timestamps = [t for t in timestamps if current_time - t < self.window_seconds]
        self.attempts[identifier] = valid_timestamps

        if len(valid_timestamps) >= self.max_attempts:
            logger.warning(f"Rate limit exceeded for client/identifier: {identifier}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many verification attempts. Please wait a few minutes before trying again or visit the front desk.",
            )

    def record_attempt(self, identifier: str) -> None:
        current_time = time.time()
        if identifier not in self.attempts:
            self.attempts[identifier] = []
        self.attempts[identifier].append(current_time)

    def clear(self, identifier: str) -> None:
        if identifier in self.attempts:
            del self.attempts[identifier]


kiosk_rate_limiter = InMemoryRateLimiter(
    max_attempts=settings.KIOSK_RATE_LIMIT_MAX_ATTEMPTS,
    window_seconds=settings.KIOSK_RATE_LIMIT_WINDOW_SECONDS
)
