from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class SourceReference(BaseModel):
    title: str
    date: str
    author: str
    record_type: str  # Clinical Note, Lab Result, Radiology Scan, Drug Monograph
    provenance_source: str
    summary: str


class DraftOrder(BaseModel):
    order_type: str  # MEDICATION, LABORATORY, RADIOLOGY
    item_name: str
    details: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    urgency: Optional[str] = "Routine"
    clinical_rationale: str
    review_status: str = "DRAFT_PENDING_REVIEW"


class StructuredAIResponse(BaseModel):
    answer: str
    answer_language: str = "en"
    symptom_summary: str
    relevant_history: List[str] = []
    source_references: List[SourceReference] = []
    uncertainties: List[str] = []
    suggested_next_steps: List[str] = []
    requires_clinician_review: bool = True
    safety_alerts: List[str] = []
    draft_orders: List[DraftOrder] = []
    response_status: str = "COMPLETED"  # COMPLETED, EMERGENCY_ESCALATION, RETRIEVAL_LIMITATION


class ConsultationMessageRequest(BaseModel):
    session_id: str
    message: str
    language: Optional[str] = "en"


class ConsultationHistoryItem(BaseModel):
    id: int
    sender_type: str
    message_text: str
    structured_payload: Optional[StructuredAIResponse] = None
    created_at: str
