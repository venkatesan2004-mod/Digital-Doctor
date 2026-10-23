from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.entities import UploadedDocument, ConsultationSession
from app.schemas.clinical import DocumentUploadResponse
from app.documents.service import DocumentService
from app.security.auth import get_current_user_claims

router = APIRouter(prefix="/documents", tags=["Medical Document & Image Uploads"])


@router.post("/upload", response_model=DocumentUploadResponse)
def upload_medical_document(
    session_id: str = Form(...),
    document_type: str = Form("Medical Report"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    claims: dict = Depends(get_current_user_claims)
):
    """
    Secure upload endpoint for clinical laboratory reports, radiology scans,
    and prescriptions.
    Enforces MIME type checking, size limitations, path traversal defenses,
    and text extraction.
    """
    # Verify session access
    session = db.query(ConsultationSession).filter(
        ConsultationSession.session_id == session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Consultation session not found.")

    if claims.get("token_type") == "kiosk" and session.patient_id != claims.get("patient_id"):
        raise HTTPException(status_code=403, detail="Forbidden session access.")

    doc = DocumentService.save_and_process_upload(
        db=db,
        session_id=session_id,
        file=file,
        document_type=document_type
    )

    return DocumentUploadResponse(
        document_uuid=doc.document_uuid,
        original_filename=doc.original_filename,
        file_size_bytes=doc.file_size_bytes,
        document_type=doc.document_type,
        processing_status=doc.processing_status,
        ocr_extracted_text=doc.ocr_extracted_text,
        ai_summary=doc.ai_summary,
        requires_clinician_review=True,
        message="Document uploaded and processed successfully. Grounded summary presented."
    )


@router.get("/session/{session_id}")
def list_session_documents(
    session_id: str,
    db: Session = Depends(get_db),
    claims: dict = Depends(get_current_user_claims)
):
    """Lists all uploaded documents attached to this consultation session."""
    session = db.query(ConsultationSession).filter(
        ConsultationSession.session_id == session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")

    if claims.get("token_type") == "kiosk" and session.patient_id != claims.get("patient_id"):
        raise HTTPException(status_code=403, detail="Forbidden session access.")

    docs = db.query(UploadedDocument).filter(
        UploadedDocument.session_id == session.id
    ).order_by(UploadedDocument.created_at.desc()).all()

    return [
        {
            "document_uuid": d.document_uuid,
            "original_filename": d.original_filename,
            "document_type": d.document_type,
            "mime_type": d.mime_type,
            "file_size_bytes": d.file_size_bytes,
            "ocr_extracted_text": d.ocr_extracted_text,
            "ai_summary": d.ai_summary,
            "processing_status": d.processing_status.value,
            "created_at": d.created_at.isoformat()
        }
        for d in docs
    ]
