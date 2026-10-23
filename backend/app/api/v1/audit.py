from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.entities import AuditEvent, StaffRole
from app.schemas.audit import AuditEventItem
from app.security.auth import require_role

router = APIRouter(prefix="/audit", tags=["Audit & Governance"])


@router.get("/logs", response_model=List[AuditEventItem])
def get_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    event_type: Optional[str] = None,
    db: Session = Depends(get_db),
    staff_claims: dict = Depends(require_role([StaffRole.AUDITOR, StaffRole.ADMIN, StaffRole.DOCTOR]))
):
    """Retrieves immutable system and clinical audit event logs."""
    query = db.query(AuditEvent).order_by(AuditEvent.created_at.desc())
    if event_type:
        query = query.filter(AuditEvent.event_type == event_type)

    events = query.limit(limit).all()
    return [
        AuditEventItem(
            id=e.id,
            event_type=e.event_type,
            actor_type=e.actor_type,
            actor_id=e.actor_id,
            ip_address=e.ip_address,
            session_id=e.session_id,
            patient_id=e.patient_id,
            resource_type=e.resource_type,
            action_details=e.action_details,
            created_at=e.created_at
        )
        for e in events
    ]
