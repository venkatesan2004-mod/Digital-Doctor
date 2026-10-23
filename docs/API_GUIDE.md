# Digital Doctor: REST API Reference Guide

All API endpoints are versioned under `/api/v1`. Interactive Swagger documentation is accessible at `http://localhost:8000/docs`.

---

## 1. System Health
### `GET /health`
Returns system operational status, database connectivity, vector database health, and active AI engine mode.
- **Auth**: None
- **Response**: `200 OK`
```json
{
  "status": "OPERATIONAL",
  "app_name": "Digital Doctor",
  "environment": "development",
  "database": "healthy",
  "vector_store": "healthy (in-memory fallback active)",
  "ai_provider": "mock",
  "timestamp": "2026-10-23T12:00:00Z"
}
```

---

## 2. Authentication & Staff Operations
### `POST /api/v1/auth/staff/login`
Authenticates hospital staff via username and password.
- **Request Body**:
```json
{
  "username": "dr.anand",
  "password": "DoctorDemo2026!"
}
```
- **Response**: `200 OK` with JWT bearer token.

### `GET /api/v1/auth/staff/me`
Retrieves claims and profile of the authenticated staff member.
- **Auth**: Bearer Token (`StaffRole`)

---

## 3. Front Office & HIMS Dispatch
### `POST /api/v1/front-office/register`
Dual-pathway patient intake registration.
- **Auth**: Bearer Token (`FRONT_OFFICE` or `ADMIN`)
- **Request Body**:
```json
{
  "first_name": "Karthik",
  "last_name": "Raja",
  "date_of_birth": "1985-06-15",
  "gender": "Male",
  "contact_phone": "+91 98765 43210",
  "department_id": 1,
  "assigned_doctor_id": 1,
  "consultation_type": "DIGITAL_DOCTOR",
  "secondary_verification_pin": "1985"
}
```
- **Behavior**:
  - `DIRECT_DOCTOR`: Dispatches to `MockHIMSAdapter`. `kiosk_eligible = false`.
  - `DIGITAL_DOCTOR`: Generates `DD-YYYYMM-XXXXXX` registration token. `kiosk_eligible = true`.

---

## 4. Kiosk Consultation Lifecycle
### `POST /api/v1/kiosk/lookup`
Rate-limited registration lookup. Masks patient name to protect privacy on public screens.
- **Request Body**: `{"registration_number": "DD-202610-KART01"}`
- **Response**:
```json
{
  "registration_number": "DD-202610-KART01",
  "masked_patient_name": "K*** R***",
  "department_name": "General Medicine",
  "doctor_name": "Dr. Anand Ramanathan",
  "requires_verification": true
}
```

### `POST /api/v1/kiosk/verify`
Verifies secondary factor (Birth Year or PIN) and issues short-lived kiosk token.
- **Request Body**: `{"registration_number": "DD-202610-KART01", "verification_factor": "1985"}`
- **Response**: Kiosk session token, patient demographics, and list of resumable sessions.

### `POST /api/v1/kiosk/session/create-or-resume`
Initializes or continues a consultation session.
- **Auth**: Bearer Token (Kiosk Token)
- **Request Body**: `{"registration_number": "DD-202610-KART01", "existing_session_id": null}`

### `POST /api/v1/kiosk/session/close`
Terminates active consultation session. Invalidates kiosk token and wipes screen.
- **Auth**: Bearer Token (Kiosk Token)

---

## 5. Consultation AI & RAG Engine
### `POST /api/v1/consultations/message`
Submits patient query, executes grounding against MySQL records and ChromaDB chunks, applies safety filters, and returns structured decision support.
- **Auth**: Bearer Token (Kiosk or Staff)
- **Request Body**:
```json
{
  "session_id": "a1b2c3d4-e5f6-47a8-b9c0-112233445566",
  "message": "I have had a mild dry cough for two days without fever.",
  "language": "en"
}
```
- **Response**: `StructuredAIResponse` schema.

---

## 6. Clinician Review Queue (HITL)
### `GET /api/v1/clinician-review/queue`
Returns all draft orders in `DRAFT_PENDING_REVIEW` status.
- **Auth**: Bearer Token (`DOCTOR` or `ADMIN`)

### `POST /api/v1/clinician-review/action/{item_type}/{item_id}`
Licensed physician signs off on draft prescription or diagnostic order.
- **Request Body**:
```json
{
  "action": "APPROVE",
  "notes": "Verified against patient's previous antibiotic tolerance."
}
```
