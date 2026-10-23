import json
from typing import Optional, Any, Dict
from sqlalchemy.orm import Session
from app.models.entities import AuditEvent
from app.core.logging import logger


class AuditService:
    """Central service for recording immutable audit logs."""

    @staticmethod
    def log_event(
        db: Session,
        event_type: str,
        actor_type: str,
        resource_type: str,
        actor_id: Optional[str] = None,
        session_id: Optional[str] = None,
        patient_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        """Persists audit record and emits structured sanitized log."""
        details_json = json.dumps(details or {})
        audit = AuditEvent(
            event_type=event_type,
            actor_type=actor_type,
            actor_id=str(actor_id) if actor_id else None,
            ip_address=ip_address,
            session_id=str(session_id) if session_id else None,
            patient_id=patient_id,
            resource_type=resource_type,
            action_details=details_json,
        )
        try:
            db.add(audit)
            db.commit()
            db.refresh(audit)
            logger.info(
                f"[AUDIT] Event={event_type} Actor={actor_type}:{actor_id} "
                f"Resource={resource_type} Session={session_id} Patient={patient_id}"
            )
            return audit
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to record audit event: {str(e)}")
            return audit
