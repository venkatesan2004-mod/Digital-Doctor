"""Initial schema with complete hospital clinical entities

Revision ID: 001_initial_schema
Revises: None
Create Date: 2026-10-23 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. departments
    op.create_table(
        'departments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=32), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('description', sa.String(length=256), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index('ix_departments_code', 'departments', ['code'])

    # 2. staff_users
    op.create_table(
        'staff_users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=64), nullable=False),
        sa.Column('email', sa.String(length=128), nullable=False),
        sa.Column('hashed_password', sa.String(length=256), nullable=False),
        sa.Column('role', sa.String(length=32), nullable=False),
        sa.Column('full_name', sa.String(length=128), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email')
    )
    op.create_index('ix_staff_users_username', 'staff_users', ['username'])

    # 3. doctors
    op.create_table(
        'doctors',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('staff_user_id', sa.Integer(), nullable=True),
        sa.Column('department_id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.String(length=64), nullable=False),
        sa.Column('full_name', sa.String(length=128), nullable=False),
        sa.Column('specialization', sa.String(length=128), nullable=False),
        sa.Column('license_number', sa.String(length=64), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id']),
        sa.ForeignKeyConstraint(['staff_user_id'], ['staff_users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('employee_id'),
        sa.UniqueConstraint('license_number'),
        sa.UniqueConstraint('staff_user_id')
    )

    # 4. patients
    op.create_table(
        'patients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('mrn', sa.String(length=64), nullable=False),
        sa.Column('first_name', sa.String(length=64), nullable=False),
        sa.Column('last_name', sa.String(length=64), nullable=False),
        sa.Column('date_of_birth', sa.String(length=10), nullable=False),
        sa.Column('gender', sa.String(length=16), nullable=False),
        sa.Column('contact_phone', sa.String(length=32), nullable=False),
        sa.Column('contact_email', sa.String(length=128), nullable=True),
        sa.Column('address', sa.String(length=256), nullable=True),
        sa.Column('preferred_language', sa.String(length=8), nullable=False, server_default='en'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('mrn')
    )
    op.create_index('ix_patients_mrn', 'patients', ['mrn'])

    # 5. registrations
    op.create_table(
        'registrations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('registration_number', sa.String(length=64), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('department_id', sa.Integer(), nullable=False),
        sa.Column('assigned_doctor_id', sa.Integer(), nullable=False),
        sa.Column('consultation_type', sa.String(length=32), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='ACTIVE'),
        sa.Column('registration_time', sa.DateTime(), nullable=False),
        sa.Column('secondary_verification_hash', sa.String(length=128), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['assigned_doctor_id'], ['doctors.id']),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id']),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('registration_number')
    )
    op.create_index('ix_registrations_reg_num', 'registrations', ['registration_number'])
    op.create_index('ix_reg_patient_type', 'registrations', ['patient_id', 'consultation_type'])

    # 6. consultation_sessions
    op.create_table(
        'consultation_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(length=64), nullable=False),
        sa.Column('registration_id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('assigned_doctor_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='CREATED'),
        sa.Column('language_preference', sa.String(length=8), nullable=False, server_default='en'),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('last_activity_at', sa.DateTime(), nullable=False),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.Column('closure_reason', sa.String(length=256), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['assigned_doctor_id'], ['doctors.id']),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id']),
        sa.ForeignKeyConstraint(['registration_id'], ['registrations.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id')
    )
    op.create_index('ix_consultation_sessions_session_id', 'consultation_sessions', ['session_id'])

    # 7. conversation_messages
    op.create_table(
        'conversation_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('sender_type', sa.String(length=32), nullable=False),
        sa.Column('message_text', sa.Text(), nullable=False),
        sa.Column('structured_payload_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['consultation_sessions.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # 8. clinical_encounters
    op.create_table(
        'clinical_encounters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('doctor_id', sa.Integer(), nullable=True),
        sa.Column('session_id', sa.Integer(), nullable=True),
        sa.Column('encounter_date', sa.DateTime(), nullable=False),
        sa.Column('chief_complaint', sa.String(length=512), nullable=False),
        sa.Column('clinical_summary', sa.Text(), nullable=False),
        sa.Column('provenance_source', sa.String(length=32), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['doctor_id'], ['doctors.id']),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # 9. symptoms
    op.create_table(
        'symptoms',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('encounter_id', sa.Integer(), nullable=True),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('symptom_name', sa.String(length=128), nullable=False),
        sa.Column('severity', sa.String(length=32), nullable=False),
        sa.Column('onset_date', sa.String(length=16), nullable=True),
        sa.Column('duration_days', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['encounter_id'], ['clinical_encounters.id']),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # 10. vital_signs
    op.create_table(
        'vital_signs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('encounter_id', sa.Integer(), nullable=True),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('recorded_at', sa.DateTime(), nullable=False),
        sa.Column('systolic_bp', sa.Integer(), nullable=True),
        sa.Column('diastolic_bp', sa.Integer(), nullable=True),
        sa.Column('heart_rate', sa.Integer(), nullable=True),
        sa.Column('respiratory_rate', sa.Integer(), nullable=True),
        sa.Column('body_temperature', sa.Numeric(precision=4, scale=1), nullable=True),
        sa.Column('sp_o2', sa.Integer(), nullable=True),
        sa.Column('recorded_by', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['encounter_id'], ['clinical_encounters.id']),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # 11. historical_prescriptions
    op.create_table(
        'historical_prescriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('doctor_id', sa.Integer(), nullable=True),
        sa.Column('encounter_id', sa.Integer(), nullable=True),
        sa.Column('prescribed_date', sa.DateTime(), nullable=False),
        sa.Column('medication_name', sa.String(length=128), nullable=False),
        sa.Column('dosage', sa.String(length=64), nullable=False),
        sa.Column('frequency', sa.String(length=64), nullable=False),
        sa.Column('route', sa.String(length=32), nullable=False),
        sa.Column('duration', sa.String(length=64), nullable=False),
        sa.Column('instructions', sa.String(length=256), nullable=True),
        sa.Column('provenance_source', sa.String(length=32), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['doctor_id'], ['doctors.id']),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # 12. medication_catalogue
    op.create_table(
        'medication_catalogue',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=32), nullable=False),
        sa.Column('brand_name', sa.String(length=128), nullable=False),
        sa.Column('generic_name', sa.String(length=128), nullable=False),
        sa.Column('dosage_form', sa.String(length=32), nullable=False),
        sa.Column('standard_strength', sa.String(length=64), nullable=False),
        sa.Column('warnings', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )

    # 13. medication_orders
    op.create_table(
        'medication_orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('medication_catalogue_id', sa.Integer(), nullable=True),
        sa.Column('medication_name', sa.String(length=128), nullable=False),
        sa.Column('dosage', sa.String(length=64), nullable=False),
        sa.Column('frequency', sa.String(length=64), nullable=False),
        sa.Column('duration', sa.String(length=64), nullable=False),
        sa.Column('instructions', sa.String(length=256), nullable=True),
        sa.Column('review_status', sa.String(length=32), nullable=False, server_default='DRAFT_PENDING_REVIEW'),
        sa.Column('rejection_reason', sa.String(length=256), nullable=True),
        sa.Column('reviewed_by_doctor_id', sa.Integer(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['medication_catalogue_id'], ['medication_catalogue.id']),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id']),
        sa.ForeignKeyConstraint(['reviewed_by_doctor_id'], ['doctors.id']),
        sa.ForeignKeyConstraint(['session_id'], ['consultation_sessions.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # 14. laboratory_catalogue
    op.create_table(
        'laboratory_catalogue',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('test_code', sa.String(length=32), nullable=False),
        sa.Column('test_name', sa.String(length=128), nullable=False),
        sa.Column('category', sa.String(length=64), nullable=False),
        sa.Column('reference_range', sa.String(length=128), nullable=True),
        sa.Column('specimen_type', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('test_code')
    )

    # 15. laboratory_requests
    op.create_table(
        'laboratory_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('lab_catalogue_id', sa.Integer(), nullable=True),
        sa.Column('test_name', sa.String(length=128), nullable=False),
        sa.Column('urgency', sa.String(length=32), nullable=False, server_default='Routine'),
        sa.Column('clinical_notes', sa.Text(), nullable=True),
        sa.Column('review_status', sa.String(length=32), nullable=False, server_default='DRAFT_PENDING_REVIEW'),
        sa.Column('rejection_reason', sa.String(length=256), nullable=True),
        sa.Column('reviewed_by_doctor_id', sa.Integer(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['lab_catalogue_id'], ['laboratory_catalogue.id']),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id']),
        sa.ForeignKeyConstraint(['reviewed_by_doctor_id'], ['doctors.id']),
        sa.ForeignKeyConstraint(['session_id'], ['consultation_sessions.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # 16. laboratory_results
    op.create_table(
        'laboratory_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('request_id', sa.Integer(), nullable=True),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('test_name', sa.String(length=128), nullable=False),
        sa.Column('result_value', sa.String(length=64), nullable=False),
        sa.Column('reference_range', sa.String(length=64), nullable=False),
        sa.Column('is_abnormal', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('performed_at', sa.DateTime(), nullable=False),
        sa.Column('reported_by', sa.String(length=64), nullable=False),
        sa.Column('provenance_source', sa.String(length=32), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id']),
        sa.ForeignKeyConstraint(['request_id'], ['laboratory_requests.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # 17. radiology_catalogue
    op.create_table(
        'radiology_catalogue',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('procedure_code', sa.String(length=32), nullable=False),
        sa.Column('procedure_name', sa.String(length=128), nullable=False),
        sa.Column('modality', sa.String(length=32), nullable=False),
        sa.Column('body_part', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('procedure_code')
    )

    # 18. radiology_requests
    op.create_table(
        'radiology_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('radiology_catalogue_id', sa.Integer(), nullable=True),
        sa.Column('procedure_name', sa.String(length=128), nullable=False),
        sa.Column('clinical_indication', sa.Text(), nullable=True),
        sa.Column('review_status', sa.String(length=32), nullable=False, server_default='DRAFT_PENDING_REVIEW'),
        sa.Column('rejection_reason', sa.String(length=256), nullable=True),
        sa.Column('reviewed_by_doctor_id', sa.Integer(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id']),
        sa.ForeignKeyConstraint(['radiology_catalogue_id'], ['radiology_catalogue.id']),
        sa.ForeignKeyConstraint(['reviewed_by_doctor_id'], ['doctors.id']),
        sa.ForeignKeyConstraint(['session_id'], ['consultation_sessions.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # 19. radiology_reports
    op.create_table(
        'radiology_reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('request_id', sa.Integer(), nullable=True),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('procedure_name', sa.String(length=128), nullable=False),
        sa.Column('modality', sa.String(length=32), nullable=False),
        sa.Column('findings', sa.Text(), nullable=False),
        sa.Column('impression', sa.Text(), nullable=False),
        sa.Column('is_abnormal', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('reported_at', sa.DateTime(), nullable=False),
        sa.Column('radiologist_name', sa.String(length=128), nullable=False),
        sa.Column('provenance_source', sa.String(length=32), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id']),
        sa.ForeignKeyConstraint(['request_id'], ['radiology_requests.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # 20. uploaded_documents
    op.create_table(
        'uploaded_documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_uuid', sa.String(length=64), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('patient_id', sa.Integer(), nullable=False),
        sa.Column('original_filename', sa.String(length=256), nullable=False),
        sa.Column('stored_filename', sa.String(length=256), nullable=False),
        sa.Column('mime_type', sa.String(length=64), nullable=False),
        sa.Column('file_size_bytes', sa.Integer(), nullable=False),
        sa.Column('document_type', sa.String(length=64), nullable=False),
        sa.Column('ocr_extracted_text', sa.Text(), nullable=True),
        sa.Column('ai_summary', sa.Text(), nullable=True),
        sa.Column('processing_status', sa.String(length=32), nullable=False, server_default='PENDING'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id']),
        sa.ForeignKeyConstraint(['session_id'], ['consultation_sessions.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('document_uuid')
    )
    op.create_index('ix_uploaded_documents_uuid', 'uploaded_documents', ['document_uuid'])

    # 21. ai_recommendations
    op.create_table(
        'ai_recommendations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('recommendation_type', sa.String(length=64), nullable=False),
        sa.Column('content_json', sa.Text(), nullable=False),
        sa.Column('requires_clinician_review', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('emergency_flag', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['consultation_sessions.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # 22. clinician_reviews
    op.create_table(
        'clinician_reviews',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('item_type', sa.String(length=64), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('reviewing_doctor_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(length=32), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['reviewing_doctor_id'], ['doctors.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_clinician_reviews_item', 'clinician_reviews', ['item_type', 'item_id'])

    # 23. audit_events
    op.create_table(
        'audit_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('actor_type', sa.String(length=32), nullable=False),
        sa.Column('actor_id', sa.String(length=64), nullable=True),
        sa.Column('ip_address', sa.String(length=64), nullable=True),
        sa.Column('session_id', sa.String(length=64), nullable=True),
        sa.Column('patient_id', sa.Integer(), nullable=True),
        sa.Column('resource_type', sa.String(length=64), nullable=False),
        sa.Column('action_details', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_events_type', 'audit_events', ['event_type'])
    op.create_index('ix_audit_events_session', 'audit_events', ['session_id'])


def downgrade() -> None:
    tables = [
        'audit_events',
        'clinician_reviews',
        'ai_recommendations',
        'uploaded_documents',
        'radiology_reports',
        'radiology_requests',
        'radiology_catalogue',
        'laboratory_results',
        'laboratory_requests',
        'laboratory_catalogue',
        'medication_orders',
        'medication_catalogue',
        'historical_prescriptions',
        'vital_signs',
        'symptoms',
        'clinical_encounters',
        'conversation_messages',
        'consultation_sessions',
        'registrations',
        'patients',
        'doctors',
        'staff_users',
        'departments'
    ]
    for table in tables:
        op.drop_table(table)
