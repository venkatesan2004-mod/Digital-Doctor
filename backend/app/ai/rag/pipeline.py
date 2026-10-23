import json
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.entities import (
    ConsultationSession,
    Patient,
    ClinicalEncounter,
    HistoricalPrescription,
    LaboratoryResult,
    RadiologyReport,
    ConversationMessage,
    MessageSender,
    MedicationOrder,
    LaboratoryRequest,
    ReviewStatus,
    SessionStatus,
)
from app.integrations.ai.provider import get_ai_provider
from app.ai.retrieval.vector_store import vector_store
from app.audit.service import AuditService
from app.schemas.ai import StructuredAIResponse
from app.core.logging import logger


class RAGConsultationPipeline:
    """End-to-end Retrieval-Augmented Generation consultation workflow."""

    @staticmethod
    def execute(
        db: Session,
        session_id: str,
        patient_message: str,
        language: str = "en"
    ) -> StructuredAIResponse:
        # 1. Authorize and Retrieve Active Session
        session = db.query(ConsultationSession).filter(
            ConsultationSession.session_id == session_id
        ).first()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consultation session not found."
            )

        if session.status in [SessionStatus.CLOSED, SessionStatus.EXPIRED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot interact with session in {session.status.value} status."
            )

        patient = db.query(Patient).filter(Patient.id == session.patient_id).first()
        doctor = session.assigned_doctor

        # 2. Extract Authoritative MySQL Patient Records
        # Past diagnoses & summaries
        encounters = db.query(ClinicalEncounter).filter(
            ClinicalEncounter.patient_id == patient.id
        ).order_by(ClinicalEncounter.encounter_date.desc()).limit(5).all()

        past_diagnoses = [enc.chief_complaint for enc in encounters]

        # Active / historical prescriptions
        prescriptions = db.query(HistoricalPrescription).filter(
            HistoricalPrescription.patient_id == patient.id
        ).order_by(HistoricalPrescription.prescribed_date.desc()).limit(5).all()

        active_medications = [f"{p.medication_name} ({p.dosage})" for p in prescriptions]

        # Lab results
        labs = db.query(LaboratoryResult).filter(
            LaboratoryResult.patient_id == patient.id
        ).order_by(LaboratoryResult.performed_at.desc()).limit(5).all()

        # Radiology
        radiology = db.query(RadiologyReport).filter(
            RadiologyReport.patient_id == patient.id
        ).order_by(RadiologyReport.reported_at.desc()).limit(3).all()

        patient_context = {
            "patient_id": patient.id,
            "patient_name": f"{patient.first_name} {patient.last_name}",
            "age_or_dob": patient.date_of_birth,
            "gender": patient.gender,
            "doctor_name": doctor.full_name if doctor else "Assigned Clinician",
            "department": session.registration.department.name if session.registration and session.registration.department else "General OPD",
            "past_diagnoses": past_diagnoses,
            "active_medications": active_medications,
            "recent_labs": [f"{l.test_name}: {l.result_value} ({l.reference_range})" for l in labs],
            "recent_radiology": [f"{r.procedure_name}: {r.impression}" for r in radiology],
        }

        # 3. Retrieve Authorized Semantic Chunks from ChromaDB/VectorStore
        retrieved_docs = vector_store.search_authorized(
            query=patient_message,
            patient_id=patient.id,
            limit=4
        )

        # 4. Invoke Configured AI Provider (Mock or OpenAI)
        provider = get_ai_provider()
        ai_response: StructuredAIResponse = provider.generate_consultation_response(
            query=patient_message,
            patient_context=patient_context,
            retrieved_documents=retrieved_docs,
            language=language
        )

        # 5. Persist Conversation in MySQL
        user_msg = ConversationMessage(
            session_id=session.id,
            sender_type=MessageSender.PATIENT,
            message_text=patient_message,
            structured_payload_json=None
        )
        db.add(user_msg)

        ai_msg = ConversationMessage(
            session_id=session.id,
            sender_type=MessageSender.AI_ASSISTANT,
            message_text=ai_response.answer,
            structured_payload_json=ai_response.model_dump_json()
        )
        db.add(ai_msg)

        # 6. If AI drafted any orders, persist them as DRAFT_PENDING_REVIEW in MySQL
        if ai_response.draft_orders:
            for draft in ai_response.draft_orders:
                if draft.order_type == "MEDICATION":
                    med_order = MedicationOrder(
                        session_id=session.id,
                        patient_id=patient.id,
                        medication_name=draft.item_name,
                        dosage=draft.dosage or "Standard Dose",
                        frequency=draft.frequency or "As directed",
                        duration=draft.duration or "3 days",
                        instructions=draft.clinical_rationale,
                        review_status=ReviewStatus.DRAFT_PENDING_REVIEW,
                    )
                    db.add(med_order)
                elif draft.order_type == "LABORATORY":
                    lab_req = LaboratoryRequest(
                        session_id=session.id,
                        patient_id=patient.id,
                        test_name=draft.item_name,
                        urgency=draft.urgency or "Routine",
                        clinical_notes=draft.clinical_rationale,
                        review_status=ReviewStatus.DRAFT_PENDING_REVIEW,
                    )
                    db.add(lab_req)

            # Update session status if review required
            session.status = SessionStatus.AWAITING_CLINICIAN_REVIEW

        db.commit()
        db.refresh(session)

        # 7. Audit Event Logging
        AuditService.log_event(
            db=db,
            event_type="AI_CONSULTATION_INFERENCE",
            actor_type="PATIENT",
            actor_id=str(patient.id),
            session_id=session.session_id,
            patient_id=patient.id,
            resource_type="CONSULTATION_SESSION",
            details={
                "message_length": len(patient_message),
                "language": language,
                "status": ai_response.response_status,
                "draft_orders_count": len(ai_response.draft_orders),
                "emergency_flag": ai_response.response_status == "EMERGENCY_ESCALATION"
            }
        )

        return ai_response
