import logging
import re
import sys
from typing import Any, Dict


# Patterns to redact from application logs
SENSITIVE_PATTERNS = [
    (re.compile(r'(?i)(password|passwd|pwd)\s*[=:]\s*["\']?([^"\'\s]+)["\']?'), r'\1="[REDACTED]"'),
    (re.compile(r'(?i)(api[_-]?key|secret|token|bearer)\s*[=:]\s*["\']?([^"\'\s]+)["\']?'), r'\1="[REDACTED]"'),
    (re.compile(r'(?i)(contact_phone|phone)\s*[=:]\s*["\']?(\+?[0-9\-\s]{7,15})["\']?'), r'\1="[REDACTED_PHONE]"'),
    (re.compile(r'(?i)(email)\s*[=:]\s*["\']?([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)["\']?'), r'\1="[REDACTED_EMAIL]"'),
]


class RedactingFormatter(logging.Formatter):
    """Custom logging formatter that strips API keys, passwords, and sensitive PHI."""

    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        redacted = original
        for pattern, replacement in SENSITIVE_PATTERNS:
            redacted = pattern.sub(replacement, redacted)
        return redacted


def setup_logger(name: str = "digital_doctor") -> logging.Logger:
    """Configures structured, sanitized logger for application modules."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        formatter = RedactingFormatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] [%(filename)s:%(lineno)d] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False
    return logger


logger = setup_logger()
