import abc
import json
import time
from typing import Dict, Any, List, Optional
import httpx
from app.core.config import settings
from app.core.logging import logger
from app.schemas.ai import StructuredAIResponse, SourceReference, DraftOrder
from app.ai.safety.emergency import EmergencyClassifier


class AIProviderBase(abc.ABC):
    """Abstract interface for AI consultation providers."""

    @abc.abstractmethod
    def generate_consultation_response(
        self,
        query: str,
        patient_context: Dict[str, Any],
        retrieved_documents: List[Dict[str, Any]],
        language: str = "en"
    ) -> StructuredAIResponse:
        """Generates grounded clinical decision support response."""
        pass


class MockAIProvider(AIProviderBase):
    """
    Deterministic clinical decision-support simulation engine.
    Ensures zero-cost, reliable, offline-compatible operation in development.
    """

    def generate_consultation_response(
        self,
        query: str,
        patient_context: Dict[str, Any],
        retrieved_documents: List[Dict[str, Any]],
        language: str = "en"
    ) -> StructuredAIResponse:
        logger.info(f"[MOCK AI] Generating consultation decision support for query: {query[:50]}... (Lang: {language})")

        # 1. Evaluate Emergency Safety Rules
        is_emergency, conditions, instructions = EmergencyClassifier.evaluate(query, language=language)
        if is_emergency:
            alerts = instructions
            if language == "ta":
                answer_text = (
                    "எச்சரிக்கை: நீங்கள் விவரித்த அறிகுறிகள் தீவிர அவசர மருத்துவ நிலையை குறிக்கின்றன. "
                    "தயவுசெய்து உடனடியாக மருத்துவமனையின் அவசர சிகிச்சை மையத்திற்கு (Triage) செல்லவும். "
                    "இந்த அமைப்பு ஒரு நேரடி மருத்துவருக்கு மாற்று அல்ல."
                )
            else:
                answer_text = (
                    "CRITICAL SAFETY ALERT: The symptoms you described indicate a potential acute medical emergency. "
                    "Please proceed immediately to the Hospital Emergency Department / Triage Counter for in-person evaluation. "
                    "This AI consultation is temporarily paused to ensure patient safety."
                )
            return StructuredAIResponse(
                answer=f"[Digital Doctor Safety Shield - Demo Mode] {answer_text}",
                answer_language=language,
                symptom_summary=f"Emergency red-flags detected: {', '.join(conditions)}",
                relevant_history=[f"Past conditions: {', '.join(patient_context.get('past_diagnoses', ['None']))}"],
                source_references=[
                    SourceReference(
                        title="Hospital Emergency Triage Protocol (v4.2)",
                        date="2026-01-01",
                        author="Clinical Safety Committee",
                        record_type="Hospital Guideline",
                        provenance_source="CLINICIAN",
                        summary="Mandatory immediate triage referral for acute chest pain, neurological deficits, or severe dyspnea."
                    )
                ],
                uncertainties=["High acute risk cannot be ruled out by automated kiosk."],
                suggested_next_steps=[
                    "Inform the triage nurse at Room 101 immediately.",
                    "Do not leave the hospital premises."
                ],
                requires_clinician_review=True,
                safety_alerts=alerts,
                draft_orders=[],
                response_status="EMERGENCY_ESCALATION"
            )

        # 2. General Clinical Guidance Synthesis
        patient_name = patient_context.get("patient_name", "Patient")
        past_meds = patient_context.get("active_medications", [])
        past_diagnoses = patient_context.get("past_diagnoses", [])
        doctor_name = patient_context.get("doctor_name", "Assigned Physician")

        # Build grounded references from retrieved records
        references = []
        for doc in retrieved_documents[:3]:
            references.append(
                SourceReference(
                    title=doc.get("title", "Clinical Encounter Note"),
                    date=doc.get("date", "2026-01-15"),
                    author=doc.get("author", doctor_name),
                    record_type=doc.get("type", "Doctor Note"),
                    provenance_source=doc.get("source", "CLINICIAN"),
                    summary=doc.get("snippet", "Historical encounter details.")
                )
            )

        if not references:
            references.append(
                SourceReference(
                    title="OPD Registration Record",
                    date="2026-10-23",
                    author=doctor_name,
                    record_type="Encounter Intake",
                    provenance_source="CLINICIAN",
                    summary="Current self-service kiosk consultation intake."
                )
            )

        # Synthetic Draft Orders depending on query context
        draft_orders = []
        lower_q = query.lower()
        if "fever" in lower_q or "temperature" in lower_q or "காய்ச்சல்" in lower_q:
            draft_orders.append(
                DraftOrder(
                    order_type="MEDICATION",
                    item_name="Paracetamol 500mg Oral Tablet",
                    details="1 tablet PO every 6 hours PRN for fever",
                    dosage="500mg",
                    frequency="1 tablet Q6H PRN",
                    duration="3 days",
                    clinical_rationale="Symptomatic relief for reported febrile episode. Requires supervising clinician sign-off.",
                    review_status="DRAFT_PENDING_REVIEW"
                )
            )
            draft_orders.append(
                DraftOrder(
                    order_type="LABORATORY",
                    item_name="Complete Blood Count (CBC)",
                    details="Specimen: Whole Blood",
                    urgency="Routine",
                    clinical_rationale="Assess leukocyte count and inflammatory markers for recurrent fever.",
                    review_status="DRAFT_PENDING_REVIEW"
                )
            )
        elif "cough" in lower_q or "cold" in lower_q or "இருமல்" in lower_q:
            draft_orders.append(
                DraftOrder(
                    order_type="LABORATORY",
                    item_name="Sputum Examination & Culture",
                    details="Specimen: Sputum",
                    urgency="Routine",
                    clinical_rationale="Evaluate bacterial etiology for persistent productive cough.",
                    review_status="DRAFT_PENDING_REVIEW"
                )
            )

        if language == "ta":
            answer = (
                f"வணக்கம் {patient_name}. உங்கள் அறிகுறிகளை அடிப்படையாகக் கொண்டு, "
                f"மருத்துவர் {doctor_name} அவர்களின் முந்தைய ஆலோசனைகள் மற்றும் மருத்துவ வழிகாட்டுதல்கள் "
                f"பரிசீலிக்கப்பட்டுள்ளன. நீங்கள் விவரித்த அறிகுறிகளுக்கு ஆரம்ப மதிப்பீடு உருவாக்கப்பட்டுள்ளது. "
                f"கீழே பரிந்துரைக்கப்பட்ட பரிசோதனைகள் மற்றும் மருந்துகள் உங்களின் மேற்பார்வை மருத்துவரின் "
                f"அங்கீகாரத்திற்குப் பிறகே இறுதி செய்யப்படும்."
            )
            symptom_summary = f"நோயாளி குறிப்பிட்ட அறிகுறிகள்: {query}."
            uncertainties = [
                "உடற்பரிசோதனை (physical examination) இல்லாமல் முழுமையான நோயறிதலை உறுதிப்படுத்த முடியாது.",
                "மருத்துவர் சரிபார்த்த பின்னரே பரிந்துரைக்கப்பட்ட மருந்துகள் விநியோகிக்கப்படும்."
            ]
            next_steps = [
                "மருத்துவர் மதிப்பாய்வு வரிசையில் (Review Queue) வரைவு பரிந்துரைகளை சமர்ப்பிக்கவும்.",
                "அறிகுறிகள் தீவிரமடைந்தால் உடனடியாக நேரில் மருத்துவரை அணுகவும்."
            ]
        else:
            answer = (
                f"Hello {patient_name}. Based on your reported symptoms and historical records reviewed under "
                f"Dr. {doctor_name}, an initial clinical decision-support evaluation has been prepared. "
                f"Relevant findings from your authorized hospital history have been incorporated into the recommendations below. "
                f"Please note that all proposed medication orders or laboratory tests are currently in DRAFT status "
                f"and must be reviewed and signed off by Dr. {doctor_name} before they can be dispensed."
            )
            symptom_summary = f"Patient-reported symptoms: {query}"
            uncertainties = [
                "Diagnosis cannot be definitively confirmed without formal clinical physical examination and vital sign verification.",
                "Pending laboratory and radiology review."
            ]
            next_steps = [
                "Awaiting attending clinician verification and digital signature.",
                "Follow standard hydration and rest guidelines.",
                "Proceed to consultation room if in-person review is scheduled."
            ]

        return StructuredAIResponse(
            answer=f"[Digital Doctor AI - Synthetic Demo Mode] {answer}",
            answer_language=language,
            symptom_summary=symptom_summary,
            relevant_history=[
                f"Diagnoses on file: {', '.join(past_diagnoses) if past_diagnoses else 'None recorded'}",
                f"Active medications: {', '.join(past_meds) if past_meds else 'None'}",
            ],
            source_references=references,
            uncertainties=uncertainties,
            suggested_next_steps=next_steps,
            requires_clinician_review=True,
            safety_alerts=[],
            draft_orders=draft_orders,
            response_status="COMPLETED"
        )


class OpenAIProvider(AIProviderBase):
    """Production-grade OpenAI API provider utilizing JSON Structured Outputs and resilient retries."""

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.timeout = settings.OPENAI_TIMEOUT_SECONDS
        self.max_retries = settings.OPENAI_MAX_RETRIES

    def generate_consultation_response(
        self,
        query: str,
        patient_context: Dict[str, Any],
        retrieved_documents: List[Dict[str, Any]],
        language: str = "en"
    ) -> StructuredAIResponse:
        if not self.api_key:
            logger.warning("OpenAI API key missing; gracefully falling back to MockAIProvider.")
            return MockAIProvider().generate_consultation_response(
                query, patient_context, retrieved_documents, language
            )

        # Evaluate emergency safety filter first
        is_emergency, conditions, instructions = EmergencyClassifier.evaluate(query, language=language)
        if is_emergency:
            return MockAIProvider().generate_consultation_response(
                query, patient_context, retrieved_documents, language
            )

        system_prompt = (
            "You are Digital Doctor, a clinical decision-support AI assistant operating in a hospital self-service kiosk. "
            "You are NOT a licensed physician. You must NEVER claim to give definitive medical diagnoses. "
            "All recommendations, medications, and laboratory tests must be treated as DRAFT suggestions requiring supervising doctor approval. "
            f"Respond in language code: {language}. Output MUST conform strictly to the required JSON schema."
        )

        user_content = {
            "query": query,
            "patient_context": patient_context,
            "retrieved_clinical_records": retrieved_documents,
            "required_schema": {
                "answer": "string",
                "answer_language": language,
                "symptom_summary": "string",
                "relevant_history": ["string"],
                "source_references": [{"title": "str", "date": "str", "author": "str", "record_type": "str", "provenance_source": "str", "summary": "str"}],
                "uncertainties": ["string"],
                "suggested_next_steps": ["string"],
                "requires_clinician_review": True,
                "safety_alerts": ["string"],
                "draft_orders": [{"order_type": "MEDICATION|LABORATORY|RADIOLOGY", "item_name": "str", "details": "str", "dosage": "str", "frequency": "str", "duration": "str", "urgency": "str", "clinical_rationale": "str"}],
                "response_status": "COMPLETED"
            }
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_content)},
            ],
            "response_format": {"type": "json_object"},
            "temperature": settings.OPENAI_TEMPERATURE,
        }

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        raw_content = data["choices"][0]["message"]["content"]
                        parsed = json.loads(raw_content)
                        return StructuredAIResponse(**parsed)
                    else:
                        logger.error(f"OpenAI API error HTTP {resp.status_code}: {resp.text}")
                        last_error = f"HTTP {resp.status_code}"
            except Exception as e:
                logger.warning(f"OpenAI attempt {attempt} failed: {str(e)}")
                last_error = str(e)
                time.sleep(1.0 * attempt)

        logger.error(f"OpenAI provider failed after {self.max_retries} attempts: {last_error}. Falling back to Mock.")
        return MockAIProvider().generate_consultation_response(
            query, patient_context, retrieved_documents, language
        )


def get_ai_provider() -> AIProviderBase:
    """Factory creating the configured AI provider based on application settings."""
    if settings.AI_PROVIDER.lower() == "openai" and settings.OPENAI_API_KEY:
        return OpenAIProvider()
    return MockAIProvider()
