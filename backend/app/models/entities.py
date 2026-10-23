import enum
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, ForeignKey,
    Enum, Numeric, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin, utc_now


# ==============================================================================
# ENUMERATIONS
# ==============================================================================

class StaffRole(str, enum.Enum):
    ADMIN = "ADMIN"
    FRONT_OFFICE = "FRONT_OFFICE"
    DOCTOR = "DOCTOR"
    LAB_STAFF = "LAB_STAFF"
    RADIOLOGY_STAFF = "RADIOLOGY_STAFF"
    PHARMACY_STAFF = "PHARMACY_STAFF"
    AUDITOR = "AUDITOR"


class ConsultationType(str, enum.Enum):
    DIRECT_DOCTOR = "DIRECT_DOCTOR"
    DIGITAL_DOCTOR = "DIGITAL_DOCTOR"


class RegistrationStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class SessionStatus(str, enum.Enum):
    CREATED = "CREATED"
    ACTIVE = "ACTIVE"
    AWAITING_CLINICIAN_REVIEW = "AWAITING_CLINICIAN_REVIEW"
    CLOSED = "CLOSED"
    EXPIRED = "EXPIRED"


class MessageSender(str, enum.Enum):
    PATIENT = "PATIENT"
    AI_ASSISTANT = "AI_ASSISTANT"
    CLINICIAN = "CLINICIAN"
    SYSTEM = "SYSTEM"


class ReviewStatus(str, enum.Enum):
    DRAFT_PENDING_REVIEW = "DRAFT_PENDING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class ProvenanceSource(str, enum.Enum):
    CLINICIAN = "CLINICIAN"
    PATIENT_REPORTED = "PATIENT_REPORTED"
    HIMS_IMPORTED = "HIMS_IMPORTED"
    AI_GENERATED = "AI_GENERATED"


class DocumentProcessingStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"


# ==============================================================================
# RELATIONAL ENTITIES
# ==============================================================================

class Department(Base, TimestampMixin):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(32), unique=True, nullable=False, index=True)
    name = Column(String(128), nullable=False)
    description = Column(String(256), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    doctors = relationship("Doctor", back_populates="department")
    registrations = relationship("Registration", back_populates="department")


class StaffUser(Base, TimestampMixin):
    __tablename__ = "staff_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(128), unique=True, nullable=False, index=True)
    hashed_password = Column(String(256), nullable=False)
    role = Column(Enum(StaffRole), nullable=False, default=StaffRole.DOCTOR)
    full_name = Column(String(128), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    doctor_profile = relationship("Doctor", back_populates="staff_user", uselist=False)


class Doctor(Base, TimestampMixin):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    staff_user_id = Column(Integer, ForeignKey("staff_users.id"), nullable=True, unique=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    employee_id = Column(String(64), unique=True, nullable=False, index=True)
    full_name = Column(String(128), nullable=False)
    specialization = Column(String(128), nullable=False)
    license_number = Column(String(64), unique=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    staff_user = relationship("StaffUser", back_populates="doctor_profile")
    department = relationship("Department", back_populates="doctors")
    registrations = relationship("Registration", back_populates="assigned_doctor")
    sessions = relationship("ConsultationSession", back_populates="assigned_doctor")


class Patient(Base, TimestampMixin):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    mrn = Column(String(64), unique=True, nullable=False, index=True)  # Medical Record Number
    first_name = Column(String(64), nullable=False)
    last_name = Column(String(64), nullable=False)
    date_of_birth = Column(String(10), nullable=False)  # YYYY-MM-DD
    gender = Column(String(16), nullable=False)  # Male, Female, Other
    contact_phone = Column(String(32), nullable=False)
    contact_email = Column(String(128), nullable=True)
    address = Column(String(256), nullable=True)
    preferred_language = Column(String(8), default="en", nullable=False)  # 'en' or 'ta'

    registrations = relationship("Registration", back_populates="patient", cascade="all, delete-orphan")
    sessions = relationship("ConsultationSession", back_populates="patient")
    encounters = relationship("ClinicalEncounter", back_populates="patient")
    historical_prescriptions = relationship("HistoricalPrescription", back_populates="patient")
    uploaded_documents = relationship("UploadedDocument", back_populates="patient")


class Registration(Base, TimestampMixin):
    __tablename__ = "registrations"

    id = Column(Integer, primary_key=True, index=True)
    registration_number = Column(String(64), unique=True, nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    assigned_doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    consultation_type = Column(Enum(ConsultationType), nullable=False)
    status = Column(Enum(RegistrationStatus), default=RegistrationStatus.ACTIVE, nullable=False)
    registration_time = Column(DateTime, default=utc_now, nullable=False)
    secondary_verification_hash = Column(String(128), nullable=False)  # hashed DOB or PIN

    patient = relationship("Patient", back_populates="registrations")
    department = relationship("Department", back_populates="registrations")
    assigned_doctor = relationship("Doctor", back_populates="registrations")
    sessions = relationship("ConsultationSession", back_populates="registration", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_reg_patient_type", "patient_id", "consultation_type"),
    )


class ConsultationSession(Base, TimestampMixin):
    __tablename__ = "consultation_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(64), unique=True, nullable=False, index=True)  # UUID4
    registration_id = Column(Integer, ForeignKey("registrations.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    assigned_doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    status = Column(Enum(SessionStatus), default=SessionStatus.CREATED, nullable=False)
    language_preference = Column(String(8), default="en", nullable=False)
    started_at = Column(DateTime, default=utc_now, nullable=False)
    last_activity_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
    closed_at = Column(DateTime, nullable=True)
    closure_reason = Column(String(256), nullable=True)

    registration = relationship("Registration", back_populates="sessions")
    patient = relationship("Patient", back_populates="sessions")
    assigned_doctor = relationship("Doctor", back_populates="sessions")
    messages = relationship("ConversationMessage", back_populates="session", cascade="all, delete-orphan")
    documents = relationship("UploadedDocument", back_populates="session")
    medication_orders = relationship("MedicationOrder", back_populates="session")
    laboratory_requests = relationship("LaboratoryRequest", back_populates="session")
    radiology_requests = relationship("RadiologyRequest", back_populates="session")
    ai_recommendations = relationship("AIRecommendation", back_populates="session")


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("consultation_sessions.id"), nullable=False, index=True)
    sender_type = Column(Enum(MessageSender), nullable=False)
    message_text = Column(Text, nullable=False)
    structured_payload_json = Column(Text, nullable=True)  # JSON formatted metadata / references
    created_at = Column(DateTime, default=utc_now, nullable=False)

    session = relationship("ConsultationSession", back_populates="messages")


class ClinicalEncounter(Base, TimestampMixin):
    __tablename__ = "clinical_encounters"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)
    session_id = Column(Integer, ForeignKey("consultation_sessions.id"), nullable=True)
    encounter_date = Column(DateTime, default=utc_now, nullable=False)
    chief_complaint = Column(String(512), nullable=False)
    clinical_summary = Column(Text, nullable=False)
    provenance_source = Column(Enum(ProvenanceSource), default=ProvenanceSource.CLINICIAN, nullable=False)

    patient = relationship("Patient", back_populates="encounters")
    symptoms = relationship("Symptom", back_populates="encounter")
    vital_signs = relationship("VitalSign", back_populates="encounter")


class Symptom(Base):
    __tablename__ = "symptoms"

    id = Column(Integer, primary_key=True, index=True)
    encounter_id = Column(Integer, ForeignKey("clinical_encounters.id"), nullable=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    symptom_name = Column(String(128), nullable=False)
    severity = Column(String(32), default="Moderate", nullable=False)  # Mild, Moderate, Severe, Critical
    onset_date = Column(String(16), nullable=True)
    duration_days = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    encounter = relationship("ClinicalEncounter", back_populates="symptoms")


class VitalSign(Base):
    __tablename__ = "vital_signs"

    id = Column(Integer, primary_key=True, index=True)
    encounter_id = Column(Integer, ForeignKey("clinical_encounters.id"), nullable=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    recorded_at = Column(DateTime, default=utc_now, nullable=False)
    systolic_bp = Column(Integer, nullable=True)
    diastolic_bp = Column(Integer, nullable=True)
    heart_rate = Column(Integer, nullable=True)
    respiratory_rate = Column(Integer, nullable=True)
    body_temperature = Column(Numeric(4, 1), nullable=True)  # e.g., 98.6 F
    sp_o2 = Column(Integer, nullable=True)  # Oxygen saturation %
    recorded_by = Column(String(64), default="Staff Nurse", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    encounter = relationship("ClinicalEncounter", back_populates="vital_signs")


class HistoricalPrescription(Base):
    __tablename__ = "historical_prescriptions"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)
    encounter_id = Column(Integer, ForeignKey("clinical_encounters.id"), nullable=True)
    prescribed_date = Column(DateTime, default=utc_now, nullable=False)
    medication_name = Column(String(128), nullable=False)
    dosage = Column(String(64), nullable=False)
    frequency = Column(String(64), nullable=False)
    route = Column(String(32), default="Oral", nullable=False)
    duration = Column(String(64), nullable=False)
    instructions = Column(String(256), nullable=True)
    provenance_source = Column(Enum(ProvenanceSource), default=ProvenanceSource.CLINICIAN, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    patient = relationship("Patient", back_populates="historical_prescriptions")


class MedicationCatalogue(Base):
    __tablename__ = "medication_catalogue"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(32), unique=True, nullable=False, index=True)
    brand_name = Column(String(128), nullable=False)
    generic_name = Column(String(128), nullable=False)
    dosage_form = Column(String(32), nullable=False)  # Tablet, Capsule, Syrup, Injection
    standard_strength = Column(String(64), nullable=False)
    warnings = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)


class MedicationOrder(Base, TimestampMixin):
    """Prescription order; MUST start as DRAFT_PENDING_REVIEW and require clinician approval."""
    __tablename__ = "medication_orders"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("consultation_sessions.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    medication_catalogue_id = Column(Integer, ForeignKey("medication_catalogue.id"), nullable=True)
    medication_name = Column(String(128), nullable=False)
    dosage = Column(String(64), nullable=False)
    frequency = Column(String(64), nullable=False)
    duration = Column(String(64), nullable=False)
    instructions = Column(String(256), nullable=True)
    review_status = Column(Enum(ReviewStatus), default=ReviewStatus.DRAFT_PENDING_REVIEW, nullable=False)
    rejection_reason = Column(String(256), nullable=True)
    reviewed_by_doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    session = relationship("ConsultationSession", back_populates="medication_orders")


class LaboratoryCatalogue(Base):
    __tablename__ = "laboratory_catalogue"

    id = Column(Integer, primary_key=True, index=True)
    test_code = Column(String(32), unique=True, nullable=False, index=True)
    test_name = Column(String(128), nullable=False)
    category = Column(String(64), nullable=False)  # Hematology, Biochemistry, etc.
    reference_range = Column(String(128), nullable=True)
    specimen_type = Column(String(64), nullable=False)  # Blood, Urine, Serum
    created_at = Column(DateTime, default=utc_now, nullable=False)


class LaboratoryRequest(Base, TimestampMixin):
    __tablename__ = "laboratory_requests"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("consultation_sessions.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    lab_catalogue_id = Column(Integer, ForeignKey("laboratory_catalogue.id"), nullable=True)
    test_name = Column(String(128), nullable=False)
    urgency = Column(String(32), default="Routine", nullable=False)  # Routine, Urgent, STAT
    clinical_notes = Column(Text, nullable=True)
    review_status = Column(Enum(ReviewStatus), default=ReviewStatus.DRAFT_PENDING_REVIEW, nullable=False)
    rejection_reason = Column(String(256), nullable=True)
    reviewed_by_doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    session = relationship("ConsultationSession", back_populates="laboratory_requests")
    results = relationship("LaboratoryResult", back_populates="request")


class LaboratoryResult(Base):
    __tablename__ = "laboratory_results"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("laboratory_requests.id"), nullable=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    test_name = Column(String(128), nullable=False)
    result_value = Column(String(64), nullable=False)
    reference_range = Column(String(64), nullable=False)
    is_abnormal = Column(Boolean, default=False, nullable=False)
    performed_at = Column(DateTime, default=utc_now, nullable=False)
    reported_by = Column(String(64), default="Chief Pathologist", nullable=False)
    provenance_source = Column(Enum(ProvenanceSource), default=ProvenanceSource.CLINICIAN, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    request = relationship("LaboratoryRequest", back_populates="results")


class RadiologyCatalogue(Base):
    __tablename__ = "radiology_catalogue"

    id = Column(Integer, primary_key=True, index=True)
    procedure_code = Column(String(32), unique=True, nullable=False, index=True)
    procedure_name = Column(String(128), nullable=False)
    modality = Column(String(32), nullable=False)  # X-Ray, CT, MRI, Ultrasound
    body_part = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)


class RadiologyRequest(Base, TimestampMixin):
    __tablename__ = "radiology_requests"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("consultation_sessions.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    radiology_catalogue_id = Column(Integer, ForeignKey("radiology_catalogue.id"), nullable=True)
    procedure_name = Column(String(128), nullable=False)
    clinical_indication = Column(Text, nullable=True)
    review_status = Column(Enum(ReviewStatus), default=ReviewStatus.DRAFT_PENDING_REVIEW, nullable=False)
    rejection_reason = Column(String(256), nullable=True)
    reviewed_by_doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    session = relationship("ConsultationSession", back_populates="radiology_requests")
    reports = relationship("RadiologyReport", back_populates="request")


class RadiologyReport(Base):
    __tablename__ = "radiology_reports"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("radiology_requests.id"), nullable=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    procedure_name = Column(String(128), nullable=False)
    modality = Column(String(32), nullable=False)
    findings = Column(Text, nullable=False)
    impression = Column(Text, nullable=False)
    is_abnormal = Column(Boolean, default=False, nullable=False)
    reported_at = Column(DateTime, default=utc_now, nullable=False)
    radiologist_name = Column(String(128), nullable=False)
    provenance_source = Column(Enum(ProvenanceSource), default=ProvenanceSource.CLINICIAN, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    request = relationship("RadiologyRequest", back_populates="reports")


class UploadedDocument(Base, TimestampMixin):
    __tablename__ = "uploaded_documents"

    id = Column(Integer, primary_key=True, index=True)
    document_uuid = Column(String(64), unique=True, nullable=False, index=True)
    session_id = Column(Integer, ForeignKey("consultation_sessions.id"), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    original_filename = Column(String(256), nullable=False)
    stored_filename = Column(String(256), nullable=False)
    mime_type = Column(String(64), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    document_type = Column(String(64), default="Medical Report", nullable=False)
    ocr_extracted_text = Column(Text, nullable=True)
    ai_summary = Column(Text, nullable=True)
    processing_status = Column(Enum(DocumentProcessingStatus), default=DocumentProcessingStatus.PENDING, nullable=False)

    session = relationship("ConsultationSession", back_populates="documents")
    patient = relationship("Patient", back_populates="uploaded_documents")


class AIRecommendation(Base):
    __tablename__ = "ai_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("consultation_sessions.id"), nullable=False, index=True)
    recommendation_type = Column(String(64), nullable=False)
    content_json = Column(Text, nullable=False)
    requires_clinician_review = Column(Boolean, default=True, nullable=False)
    emergency_flag = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    session = relationship("ConsultationSession", back_populates="ai_recommendations")


class ClinicianReview(Base):
    __tablename__ = "clinician_reviews"

    id = Column(Integer, primary_key=True, index=True)
    item_type = Column(String(64), nullable=False)  # MEDICATION_ORDER, LAB_REQUEST, RADIOLOGY_REQUEST, AI_RECOMMENDATION
    item_id = Column(Integer, nullable=False, index=True)
    reviewing_doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    action = Column(String(32), nullable=False)  # APPROVED, REJECTED
    notes = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, default=utc_now, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(64), nullable=False, index=True)
    actor_type = Column(String(32), nullable=False)  # PATIENT, STAFF, SYSTEM
    actor_id = Column(String(64), nullable=True)
    ip_address = Column(String(64), nullable=True)
    session_id = Column(String(64), nullable=True, index=True)
    patient_id = Column(Integer, nullable=True, index=True)
    resource_type = Column(String(64), nullable=False)
    action_details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
