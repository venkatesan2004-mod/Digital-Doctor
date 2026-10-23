import datetime
from sqlalchemy.orm import Session
from app.models.entities import (
    Department, StaffUser, Doctor, Patient, Registration,
    ConsultationSession, ClinicalEncounter, Symptom, VitalSign,
    HistoricalPrescription, MedicationCatalogue, MedicationOrder,
    LaboratoryCatalogue, LaboratoryRequest, LaboratoryResult,
    RadiologyCatalogue, RadiologyRequest, RadiologyReport,
    StaffRole, ConsultationType, RegistrationStatus, SessionStatus,
    ReviewStatus, ProvenanceSource, ConversationMessage, MessageSender
)
from app.models.base import Base
from app.core.database import engine
from app.security.auth import hash_password, hash_secondary_factor
from app.ai.retrieval.vector_store import vector_store
from app.core.logging import logger


def seed_synthetic_data(db: Session) -> None:
    """Populates repeatable, idempotent synthetic clinical demonstration data."""
    logger.info("Verifying synthetic clinical seed data...")
    # Ensure tables are created if running directly
    try:
        Base.metadata.create_all(bind=db.get_bind())
    except Exception as e:
        logger.warning(f"Notice during table verification: {str(e)}")

    # 1. Departments
    dept_gen = db.query(Department).filter(Department.code == "GEN_MED").first()
    if not dept_gen:
        dept_gen = Department(code="GEN_MED", name="General Medicine", description="Adult primary care and acute internal medicine.")
        db.add(dept_gen)

    dept_cardio = db.query(Department).filter(Department.code == "CARDIO").first()
    if not dept_cardio:
        dept_cardio = Department(code="CARDIO", name="Cardiology", description="Cardiovascular diagnostics and patient management.")
        db.add(dept_cardio)

    dept_pulmo = db.query(Department).filter(Department.code == "PULMO").first()
    if not dept_pulmo:
        dept_pulmo = Department(code="PULMO", name="Pulmonology", description="Respiratory illnesses and lung health.")
        db.add(dept_pulmo)

    db.commit()

    # 2. Staff Users & Doctors
    # Demo password for all synthetic staff: "DoctorDemo2026!"
    demo_pw_hash = hash_password("DoctorDemo2026!")

    staff_admin = db.query(StaffUser).filter(StaffUser.username == "admin").first()
    if not staff_admin:
        staff_admin = StaffUser(
            username="admin",
            email="admin@digitaldoctor.hospital.internal",
            hashed_password=demo_pw_hash,
            role=StaffRole.ADMIN,
            full_name="Hospital System Administrator",
            is_active=True
        )
        db.add(staff_admin)

    staff_front = db.query(StaffUser).filter(StaffUser.username == "frontoffice").first()
    if not staff_front:
        staff_front = StaffUser(
            username="frontoffice",
            email="reception@digitaldoctor.hospital.internal",
            hashed_password=demo_pw_hash,
            role=StaffRole.FRONT_OFFICE,
            full_name="Front Desk Executive",
            is_active=True
        )
        db.add(staff_front)

    staff_dr_anand = db.query(StaffUser).filter(StaffUser.username == "dr.anand").first()
    if not staff_dr_anand:
        staff_dr_anand = StaffUser(
            username="dr.anand",
            email="anand.ramanathan@digitaldoctor.hospital.internal",
            hashed_password=demo_pw_hash,
            role=StaffRole.DOCTOR,
            full_name="Dr. Anand Ramanathan, MD",
            is_active=True
        )
        db.add(staff_dr_anand)
        db.commit()

        doc_anand = Doctor(
            staff_user_id=staff_dr_anand.id,
            department_id=dept_gen.id,
            employee_id="DOC-IND-1001",
            full_name="Dr. Anand Ramanathan",
            specialization="Internal Medicine",
            license_number="TN-MCI-45892",
            is_active=True
        )
        db.add(doc_anand)

    staff_dr_priya = db.query(StaffUser).filter(StaffUser.username == "dr.priya").first()
    if not staff_dr_priya:
        staff_dr_priya = StaffUser(
            username="dr.priya",
            email="priya.sundaram@digitaldoctor.hospital.internal",
            hashed_password=demo_pw_hash,
            role=StaffRole.DOCTOR,
            full_name="Dr. Priya Sundaram, MBBS DNB",
            is_active=True
        )
        db.add(staff_dr_priya)
        db.commit()

        doc_priya = Doctor(
            staff_user_id=staff_dr_priya.id,
            department_id=dept_cardio.id,
            employee_id="DOC-IND-1002",
            full_name="Dr. Priya Sundaram",
            specialization="Cardiology",
            license_number="TN-MCI-78214",
            is_active=True
        )
        db.add(doc_priya)

    db.commit()

    # Query doctors for foreign keys
    dr_anand = db.query(Doctor).filter(Doctor.employee_id == "DOC-IND-1001").first()
    dr_priya = db.query(Doctor).filter(Doctor.employee_id == "DOC-IND-1002").first()

    # 3. Medication Catalogue
    meds = [
        ("MED-PCM500", "Calpol", "Paracetamol", "Tablet", "500mg", "Do not exceed 4000mg/day. Caution in liver impairment."),
        ("MED-AMX500", "Moxikind", "Amoxicillin", "Capsule", "500mg", "Hypersensitivity to beta-lactams. Take with meals."),
        ("MED-MET500", "Glycomet", "Metformin", "Tablet", "500mg", "Contraindicated in severe renal failure eGFR < 30."),
        ("MED-AML5", "Amlip", "Amlodipine", "Tablet", "5mg", "Monitor blood pressure. Peripheral edema reported."),
        ("MED-CET10", "Cetzine", "Cetirizine", "Tablet", "10mg", "Mild sedation possible. Take before bed."),
    ]
    for code, bname, gname, form, strength, warn in meds:
        if not db.query(MedicationCatalogue).filter(MedicationCatalogue.code == code).first():
            db.add(MedicationCatalogue(
                code=code, brand_name=bname, generic_name=gname,
                dosage_form=form, standard_strength=strength, warnings=warn
            ))

    # 4. Laboratory Catalogue
    labs = [
        ("LAB-CBC", "Complete Blood Count", "Hematology", "Hb: 12-16 g/dL, WBC: 4000-11000", "Whole Blood (EDTA)"),
        ("LAB-FBS", "Fasting Blood Sugar", "Biochemistry", "70 - 100 mg/dL", "Fluoride Plasma"),
        ("LAB-HBA1C", "Glycated Hemoglobin (HbA1c)", "Biochemistry", "< 5.7% Normal, 5.7-6.4% Prediabetes", "Whole Blood (EDTA)"),
        ("LAB-LIPID", "Lipid Profile", "Biochemistry", "Total Chol < 200, LDL < 100, HDL > 40", "Serum"),
        ("LAB-URINE", "Routine Urine Examination", "Clinical Pathology", "Proteins: Nil, Sugar: Nil", "Midstream Urine"),
    ]
    for code, tname, cat, rng, spec in labs:
        if not db.query(LaboratoryCatalogue).filter(LaboratoryCatalogue.test_code == code).first():
            db.add(LaboratoryCatalogue(
                test_code=code, test_name=tname, category=cat,
                reference_range=rng, specimen_type=spec
            ))

    # 5. Radiology Catalogue
    rads = [
        ("RAD-CXR-PA", "Chest X-Ray PA View", "X-Ray", "Chest / Thorax"),
        ("RAD-USG-ABD", "Ultrasound Whole Abdomen", "Ultrasound", "Abdomen & Pelvis"),
        ("RAD-CT-HEAD", "CT Brain Non-Contrast", "CT Scan", "Brain / Head"),
    ]
    for code, pname, mod, body in rads:
        if not db.query(RadiologyCatalogue).filter(RadiologyCatalogue.procedure_code == code).first():
            db.add(RadiologyCatalogue(
                procedure_code=code, procedure_name=pname, modality=mod, body_part=body
            ))

    db.commit()

    # 6. Synthetic Patients & Encounters
    # Patient 1: Karthik Raja (Resumable Digital Doctor Consultation with extensive history)
    p1 = db.query(Patient).filter(Patient.mrn == "MRN-KART-001").first()
    if not p1:
        p1 = Patient(
            mrn="MRN-KART-001",
            first_name="Karthik",
            last_name="Raja",
            date_of_birth="1985-06-15",
            gender="Male",
            contact_phone="+91 98765 43210",
            contact_email="karthik.raja.synthetic@example.org",
            address="42, Gandhi Road, Chennai, Tamil Nadu",
            preferred_language="en",
        )
        db.add(p1)
        db.commit()

        # Previous Encounters
        enc1 = ClinicalEncounter(
            patient_id=p1.id,
            doctor_id=dr_anand.id,
            encounter_date=datetime.datetime.utcnow() - datetime.timedelta(days=45),
            chief_complaint="Follow-up on Mild Essential Hypertension and Glycemic Check",
            clinical_summary="Patient reports good compliance with morning Amlodipine. Denies palpitations or pedal edema. Advised diet control.",
            provenance_source=ProvenanceSource.CLINICIAN
        )
        db.add(enc1)
        db.commit()

        # Vitals
        v1 = VitalSign(
            encounter_id=enc1.id,
            patient_id=p1.id,
            recorded_at=datetime.datetime.utcnow() - datetime.timedelta(days=45),
            systolic_bp=128,
            diastolic_bp=82,
            heart_rate=74,
            respiratory_rate=16,
            body_temperature=98.4,
            sp_o2=99,
            recorded_by="Staff Nurse Shanthi"
        )
        db.add(v1)

        # Historical Prescriptions
        rx1 = HistoricalPrescription(
            patient_id=p1.id,
            doctor_id=dr_anand.id,
            encounter_id=enc1.id,
            prescribed_date=datetime.datetime.utcnow() - datetime.timedelta(days=45),
            medication_name="Amlodipine 5mg",
            dosage="5mg",
            frequency="Once daily in the morning",
            route="Oral",
            duration="30 days",
            instructions="Take after breakfast. Regular BP monitoring advised.",
            provenance_source=ProvenanceSource.CLINICIAN
        )
        db.add(rx1)

        # Lab Results
        lab_res1 = LaboratoryResult(
            patient_id=p1.id,
            test_name="Fasting Blood Sugar",
            result_value="94 mg/dL",
            reference_range="70 - 100 mg/dL",
            is_abnormal=False,
            performed_at=datetime.datetime.utcnow() - datetime.timedelta(days=44),
            reported_by="Dr. Balaji, Chief Biochemist",
            provenance_source=ProvenanceSource.CLINICIAN
        )
        db.add(lab_res1)

        lab_res2 = LaboratoryResult(
            patient_id=p1.id,
            test_name="Glycated Hemoglobin (HbA1c)",
            result_value="5.6%",
            reference_range="< 5.7%",
            is_abnormal=False,
            performed_at=datetime.datetime.utcnow() - datetime.timedelta(days=44),
            reported_by="Dr. Balaji, Chief Biochemist",
            provenance_source=ProvenanceSource.CLINICIAN
        )
        db.add(lab_res2)

        # Radiology
        rad_rep1 = RadiologyReport(
            patient_id=p1.id,
            procedure_name="Chest X-Ray PA View",
            modality="X-Ray",
            findings="Bilateral lung fields clear. Costophrenic angles sharp. Cardiothoracic ratio normal.",
            impression="Normal chest radiograph.",
            is_abnormal=False,
            reported_at=datetime.datetime.utcnow() - datetime.timedelta(days=90),
            radiologist_name="Dr. Sivakumar, Radiologist",
            provenance_source=ProvenanceSource.CLINICIAN
        )
        db.add(rad_rep1)

        # Active Digital Doctor Registration for Karthik
        # Secondary verification hash is birth year "1985"
        sec_hash = hash_secondary_factor("1985")
        reg1 = Registration(
            registration_number="DD-202610-KART01",
            patient_id=p1.id,
            department_id=dept_gen.id,
            assigned_doctor_id=dr_anand.id,
            consultation_type=ConsultationType.DIGITAL_DOCTOR,
            status=RegistrationStatus.ACTIVE,
            secondary_verification_hash=sec_hash
        )
        db.add(reg1)
        db.commit()

        # Resumable Session for Karthik
        sess1 = ConsultationSession(
            session_id="a1b2c3d4-e5f6-47a8-b9c0-112233445566",
            registration_id=reg1.id,
            patient_id=p1.id,
            assigned_doctor_id=dr_anand.id,
            status=SessionStatus.ACTIVE,
            language_preference="en",
            started_at=datetime.datetime.utcnow() - datetime.timedelta(minutes=30),
            last_activity_at=datetime.datetime.utcnow() - datetime.timedelta(minutes=5),
        )
        db.add(sess1)
        db.commit()

        # Initial message in session
        m1 = ConversationMessage(
            session_id=sess1.id,
            sender_type=MessageSender.PATIENT,
            message_text="Hello, I have had a mild dry cough for the past 2 days without fever.",
            created_at=datetime.datetime.utcnow() - datetime.timedelta(minutes=25)
        )
        db.add(m1)

    # Patient 2: Meena Swaminathan (Has pending clinician review items)
    p2 = db.query(Patient).filter(Patient.mrn == "MRN-MEEN-002").first()
    if not p2:
        p2 = Patient(
            mrn="MRN-MEEN-002",
            first_name="Meena",
            last_name="Swaminathan",
            date_of_birth="1990-03-22",
            gender="Female",
            contact_phone="+91 98765 43211",
            contact_email="meena.swami.synthetic@example.org",
            address="15, Anna Salai, Chennai, Tamil Nadu",
            preferred_language="ta",
        )
        db.add(p2)
        db.commit()

        sec_hash_p2 = hash_secondary_factor("1990")
        reg2 = Registration(
            registration_number="DD-202610-MEEN02",
            patient_id=p2.id,
            department_id=dept_gen.id,
            assigned_doctor_id=dr_anand.id,
            consultation_type=ConsultationType.DIGITAL_DOCTOR,
            status=RegistrationStatus.ACTIVE,
            secondary_verification_hash=sec_hash_p2
        )
        db.add(reg2)
        db.commit()

        sess2 = ConsultationSession(
            session_id="b2c3d4e5-f6a7-48b9-c0d1-223344556677",
            registration_id=reg2.id,
            patient_id=p2.id,
            assigned_doctor_id=dr_anand.id,
            status=SessionStatus.AWAITING_CLINICIAN_REVIEW,
            language_preference="ta",
            started_at=datetime.datetime.utcnow() - datetime.timedelta(hours=1),
            last_activity_at=datetime.datetime.utcnow() - datetime.timedelta(minutes=10),
        )
        db.add(sess2)
        db.commit()

        # Pending Draft Orders requiring Doctor Approval
        med_draft = MedicationOrder(
            session_id=sess2.id,
            patient_id=p2.id,
            medication_name="Paracetamol 500mg Oral Tablet",
            dosage="500mg",
            frequency="1 tablet Q6H PRN",
            duration="3 days",
            instructions="Draft recommendation for reported febrile symptoms. Awaiting Dr. Anand's approval.",
            review_status=ReviewStatus.DRAFT_PENDING_REVIEW
        )
        db.add(med_draft)

        lab_draft = LaboratoryRequest(
            session_id=sess2.id,
            patient_id=p2.id,
            test_name="Complete Blood Count (CBC)",
            urgency="Routine",
            clinical_notes="Fever workup and leukocyte differential count.",
            review_status=ReviewStatus.DRAFT_PENDING_REVIEW
        )
        db.add(lab_draft)

    # Patient 3: Suresh Babu (Closed consultation)
    p3 = db.query(Patient).filter(Patient.mrn == "MRN-SURE-003").first()
    if not p3:
        p3 = Patient(
            mrn="MRN-SURE-003",
            first_name="Suresh",
            last_name="Babu",
            date_of_birth="1978-11-09",
            gender="Male",
            contact_phone="+91 98765 43212",
            address="7, Trunk Road, Vellore, Tamil Nadu",
            preferred_language="en",
        )
        db.add(p3)
        db.commit()

        sec_hash_p3 = hash_secondary_factor("1978")
        reg3 = Registration(
            registration_number="DD-202610-SURE03",
            patient_id=p3.id,
            department_id=dept_cardio.id,
            assigned_doctor_id=dr_priya.id,
            consultation_type=ConsultationType.DIGITAL_DOCTOR,
            status=RegistrationStatus.COMPLETED,
            secondary_verification_hash=sec_hash_p3
        )
        db.add(reg3)
        db.commit()

        sess3 = ConsultationSession(
            session_id="c3d4e5f6-a7b8-49c0-d1e2-334455667788",
            registration_id=reg3.id,
            patient_id=p3.id,
            assigned_doctor_id=dr_priya.id,
            status=SessionStatus.CLOSED,
            language_preference="en",
            started_at=datetime.datetime.utcnow() - datetime.timedelta(days=2),
            closed_at=datetime.datetime.utcnow() - datetime.timedelta(days=2, hours=-1),
            closure_reason="Patient completed routine follow-up advice.",
        )
        db.add(sess3)

    # Patient 4: Deepa Natarajan (Direct Doctor OPD registration - not in kiosk)
    p4 = db.query(Patient).filter(Patient.mrn == "MRN-DEEP-004").first()
    if not p4:
        p4 = Patient(
            mrn="MRN-DEEP-004",
            first_name="Deepa",
            last_name="Natarajan",
            date_of_birth="1995-08-30",
            gender="Female",
            contact_phone="+91 98765 43213",
            address="28, South Usman Road, T. Nagar, Chennai",
            preferred_language="en",
        )
        db.add(p4)
        db.commit()

        reg4 = Registration(
            registration_number="HIMS-OPD-78912",
            patient_id=p4.id,
            department_id=dept_gen.id,
            assigned_doctor_id=dr_anand.id,
            consultation_type=ConsultationType.DIRECT_DOCTOR,
            status=RegistrationStatus.ACTIVE,
            secondary_verification_hash="n/a_direct_hims"
        )
        db.add(reg4)

    db.commit()

    # 7. Seed Public Knowledge Monographs & Doctor Notes into Vector Store
    logger.info("Indexing synthetic clinical monographs into vector store...")
    vector_store.index_document(
        doc_id="guideline_fever_01",
        content="CLINICAL GUIDELINE: Management of Acute Febrile Illness. Recommend hydration, temperature charting, and antipyretics (Paracetamol 500-650mg PO). If fever persists > 72 hours, complete blood count (CBC) and infectious serology are indicated.",
        metadata={
            "patient_id": None,
            "is_public": True,
            "title": "Hospital Protocol: Acute Febrile Illness",
            "author": "Clinical Safety Committee",
            "doc_type": "Hospital Guideline",
            "source": "CLINICIAN",
            "date": "2026-01-01"
        }
    )
    vector_store.index_document(
        doc_id="guideline_cough_02",
        content="CLINICAL GUIDELINE: Evaluation of Subacute Cough. Assess for red flags: hemoptysis, nocturnal dyspnea, weight loss. Recommend saline gargles, honey-lemon demulcents, and observation. Sputum culture indicated for persistent productive purulent sputum.",
        metadata={
            "patient_id": None,
            "is_public": True,
            "title": "Hospital Protocol: Respiratory Symptom Assessment",
            "author": "Pulmonology Department",
            "doc_type": "Hospital Guideline",
            "source": "CLINICIAN",
            "date": "2026-01-01"
        }
    )

    # Index Doctor's encounter note specifically for Karthik Raja (Patient 1)
    if p1:
        vector_store.index_document(
            doc_id=f"enc_kart_{p1.id}",
            content="DOCTOR NOTE by Dr. Anand Ramanathan for Karthik Raja: Patient maintained on Amlodipine 5mg for mild hypertension. Blood pressure well-controlled. Advised low-sodium diet and 30 minutes daily aerobic exercise. Next review in 3 months.",
            metadata={
                "patient_id": p1.id,
                "is_public": False,
                "title": "Encounter Note - Dr. Anand Ramanathan",
                "author": "Dr. Anand Ramanathan",
                "doc_type": "Clinical Note",
                "source": "CLINICIAN",
                "date": "2026-09-08"
            }
        )

    logger.info("Synthetic demonstration records successfully initialized.")


if __name__ == "__main__":
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        seed_synthetic_data(db)
        print("Seed data loaded successfully.")
    finally:
        db.close()
