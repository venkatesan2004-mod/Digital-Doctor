from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from app.models.entities import ReviewStatus, ProvenanceSource, DocumentProcessingStatus


class MedicationItem(BaseModel):
    id: int
    medication_name: str
    dosage: str
    frequency: str
    duration: str
    instructions: Optional[str] = None
    prescribed_date: datetime
    doctor_name: Optional[str] = None
    provenance_source: ProvenanceSource


class LabResultItem(BaseModel):
    id: int
    test_name: str
    result_value: str
    reference_range: str
    is_abnormal: bool
    performed_at: datetime
    reported_by: str
    provenance_source: ProvenanceSource


class RadiologyReportItem(BaseModel):
    id: int
    procedure_name: str
    modality: str
    findings: str
    impression: str
    is_abnormal: bool
    reported_at: datetime
    radiologist_name: str
    provenance_source: ProvenanceSource


class DocumentUploadResponse(BaseModel):
    document_uuid: str
    original_filename: str
    file_size_bytes: int
    document_type: str
    processing_status: DocumentProcessingStatus
    ocr_extracted_text: Optional[str] = None
    ai_summary: Optional[str] = None
    requires_clinician_review: bool = True
    message: str


class ClinicianReviewQueueItem(BaseModel):
    review_id: int
    item_type: str  # MEDICATION_ORDER, LAB_REQUEST, RADIOLOGY_REQUEST
    item_id: int
    session_id: str
    patient_id: int
    patient_name: str
    patient_mrn: str
    item_title: str
    item_details: str
    clinical_rationale: Optional[str] = None
    review_status: ReviewStatus
    created_at: datetime
    rejection_reason: Optional[str] = None


class ClinicianReviewActionRequest(BaseModel):
    action: str = Field(..., description="APPROVE or REJECT")
    notes: Optional[str] = None
    rejection_reason: Optional[str] = None


class ClinicianReviewActionResponse(BaseModel):
    item_type: str
    item_id: int
    review_status: ReviewStatus
    message: str
    action_recorded_at: datetime
