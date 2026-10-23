from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class AuditEventItem(BaseModel):
    id: int
    event_type: str
    actor_type: str
    actor_id: Optional[str] = None
    ip_address: Optional[str] = None
    session_id: Optional[str] = None
    patient_id: Optional[int] = None
    resource_type: str
    action_details: Optional[str] = None
    created_at: datetime


class HealthCheckResponse(BaseModel):
    status: str
    app_name: str
    environment: str
    database: str
    vector_store: str
    ai_provider: str
    timestamp: datetime
