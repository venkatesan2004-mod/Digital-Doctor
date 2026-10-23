# Digital Doctor: Automated Testing & Quality Assurance

## 1. Test Suite Architecture

The test suite covers API endpoints, authorization rules, RAG pipelines, emergency detection, front-office pathway routing, and cross-patient isolation.

```text
backend/tests/
├── conftest.py                       # In-memory test engine, fixtures, seed data
├── api/
│   ├── test_health.py                # Health endpoint and runtime status
│   ├── test_auth.py                  # JWT creation, claims, invalid credentials
│   ├── test_front_office.py          # DIRECT vs DIGITAL pathway separation
│   ├── test_kiosk_sessions.py        # Masked lookup, verification, session lifecycle
│   ├── test_consultations_ai.py      # Structured AI schema, emergency escalation
│   └── test_clinician_approval.py    # Draft review queue, approval & rejection
└── security/
    └── test_security_isolation.py    # Cross-patient data boundary & vector isolation
```

---

## 2. Test Execution Commands

### Local Windows Command Prompt / PowerShell:
```cmd
cd backend
python -m pytest tests/ -v
```

### Via Docker Compose:
```cmd
docker compose exec backend pytest -v
```

### Windows Helper Script:
```cmd
scripts\run-tests.bat
```

---

## 3. Verified Test Results (Executed on 2026-10-23)

```text
============================= test session starts =============================
platform win32 -- Python 3.15.1, pytest-9.1.1, pluggy-1.7.0
rootdir: C:\Users\BEAUTITY INDIA MNG\.gemini\antigravity\scratch\digital-doctor\backend
collected 15 items

tests/api/test_auth.py::test_staff_login_success PASSED                  [  6%]
tests/api/test_auth.py::test_staff_login_invalid_credentials PASSED      [ 13%]
tests/api/test_auth.py::test_staff_me_endpoint_authorized PASSED         [ 20%]
tests/api/test_clinician_approval.py::test_clinician_review_queue_and_approval PASSED [ 26%]
tests/api/test_clinician_approval.py::test_unauthorized_user_cannot_approve_clinical_draft PASSED [ 33%]
tests/api/test_consultations_ai.py::test_consultation_ai_rag_response_format PASSED [ 40%]
tests/api/test_consultations_ai.py::test_consultation_ai_emergency_detection PASSED [ 46%]
tests/api/test_front_office.py::test_front_office_direct_doctor_pathway PASSED [ 53%]
tests/api/test_front_office.py::test_front_office_digital_doctor_pathway PASSED [ 60%]
tests/api/test_health.py::test_health_check_endpoint PASSED              [ 66%]
tests/api/test_kiosk_sessions.py::test_kiosk_lookup_masks_identity PASSED [ 73%]
tests/api/test_kiosk_sessions.py::test_kiosk_direct_doctor_registration_rejected_at_kiosk PASSED [ 80%]
tests/api/test_kiosk_sessions.py::test_kiosk_verification_and_session_lifecycle PASSED [ 86%]
tests/security/test_security_isolation.py::test_cross_patient_data_isolation PASSED [ 93%]
tests/security/test_security_isolation.py::test_vector_store_strict_patient_boundary PASSED [100%]

================== 15 passed, 1 warning in 73.97s ===================
```
