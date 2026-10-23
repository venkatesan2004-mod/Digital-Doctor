import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.entities import ConsultationSession, ConversationMessage
from app.schemas.ai import ConsultationMessageRequest, StructuredAIResponse, ConsultationHistoryItem
from app.ai.rag.pipeline import RAGConsultationPipeline
from app.security.auth import get_current_user_claims

router = APIRouter(prefix="/consultations", tags=["Consultation AI Engine"])


@router.post("/message", response_model=StructuredAIResponse)
def send_consultation_message(
    payload: ConsultationMessageRequest,
    db: Session = Depends(get_db),
    claims: dict = Depends(get_current_user_claims)
):
    """
    Submits patient symptom query to the RAG Consultation Engine.
    Executes authoritative retrieval, vector similarity search, safety checks,
    and returns grounded structured decision-support response.
    """
    # Verify session access
    session = db.query(ConsultationSession).filter(
        ConsultationSession.session_id == payload.session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Consultation session not found.")

    # Check permission (either kiosk patient owner or hospital staff)
    if claims.get("token_type") == "kiosk":
        if session.patient_id != claims.get("patient_id"):
            raise HTTPException(status_code=403, detail="Unauthorized access to patient session.")

    return RAGConsultationPipeline.execute(
        db=db,
        session_id=payload.session_id,
        patient_message=payload.message,
        language=payload.language or session.language_preference or "en"
    )


@router.get("/{session_id}/messages")
def get_session_messages(
    session_id: str,
    db: Session = Depends(get_db),
    claims: dict = Depends(get_current_user_claims)
):
    """Retrieves conversation message history for a consultation session."""
    session = db.query(ConsultationSession).filter(
        ConsultationSession.session_id == session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    if claims.get("token_type") == "kiosk" and session.patient_id != claims.get("patient_id"):
        raise HTTPException(status_code=403, detail="Forbidden session access.")

    messages = db.query(ConversationMessage).filter(
        ConversationMessage.session_id == session.id
    ).order_by(ConversationMessage.created_at.asc()).all()

    items = []
    for m in messages:
        structured = None
        if m.structured_payload_json:
            try:
                structured = json.loads(m.structured_payload_json)
            except Exception:
                structured = None
        items.append({
            "id": m.id,
            "sender_type": m.sender_type.value,
            "message_text": m.message_text,
            "structured_payload": structured,
            "created_at": m.created_at.isoformat()
        })

    return items
