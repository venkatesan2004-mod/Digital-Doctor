# Digital Doctor: Implementation Plan & Architecture Blueprint

## Executive Overview
**Project Name:** Digital Doctor  
**Type:** Hospital-based, self-service digital consultation kiosk with clinician-supervised AI  
**Deployment Target:** Docker Compose (Windows Docker Desktop / Hospital Linux On-Premise)  
**Authoritative Store:** MySQL 8.0 (Relational schema, ACID compliance, transactions, migrations)  
**Semantic Index:** ChromaDB (Patient-isolated vector search, clinical monographs, knowledge embeddings)  
**Primary Languages:** Python 3.11+ (Backend), JavaScript ES6+ React 18+ (Frontend), English & Tamil  
**AI Subsystem:** Configurable OpenAI API adapter with resilient Mock AI engine for local zero-cost/offline testing  
**Clinical Oversight:** Mandatory Human-In-The-Loop (HITL) review queue. AI generates decision-support drafts; only authorized clinicians approve prescriptions, lab orders, and radiology requests.

---

## 1. Architectural Principles & Non-Negotiables
1. **Clinical Decision Support Only:** The AI engine never acts as an autonomous medical practitioner. All prescriptions, lab orders, and radiology requisitions originate as `DRAFT_PENDING_REVIEW` and require cryptographic/JWT-authenticated clinician sign-off before being issued.
2. **Strict Dual-Pathway Isolation:**
   - `DIRECT_DOCTOR`: Diverted exclusively to the mock Hospital Information Management System (HIMS) workflow. No Digital Doctor session is ever initialized.
   - `DIGITAL_DOCTOR`: Enters the digital consultation kiosk workflow with synthetic patient record linking, registration tokens, and doctor assignment.
3. **Multi-Factor Kiosk Verification:** Registration ID entry must be verified by a secondary factor (demo synthetic DOB/PIN verification) before any protected health information (PHI) or historical records are exposed.
4. **Session Lifecycle & Privacy Reset:** Explicit state transitions (`CREATED` -> `ACTIVE` -> `AWAITING_CLINICIAN_REVIEW` -> `CLOSED` / `EXPIRED`). On session closure or timeout, client browser tokens and cached state are purged, returning the kiosk to the welcome screen while preserving audit logs and encounter records in MySQL.
5. **Patient-Isolated RAG:** Vector search queries are strictly partitioned by patient permissions and tenant context. Unchecked vector retrieval across patient boundaries is architecturally forbidden.
6. **No CSS Frameworks / No Inline Styles:** Pure, clean external CSS files organized by tokens, layouts, components, and pages.
7. **Bilingual By Design:** English and Tamil language dictionaries covering all patient-facing kiosk flows, buttons, warnings, and AI instructions.

---

## 2. Phase-by-Phase Roadmap

### Phase 1: Repository & Infrastructure Foundation
- Directory structure layout matching specification.
- Docker Compose files: `compose.yaml` (base), `compose.dev.yaml` (hot reloading), `compose.prod.yaml` (hardened production).
- Multi-stage Dockerfiles for backend (Python Uvicorn) and frontend (Vite/Node build + Nginx).
- Environment configuration: `.env.example` with documented environment variables, `.gitignore`, `.dockerignore`.
- Developer convenience scripts for Windows (`start-dev.bat`, `stop-dev.bat`, `run-tests.bat`, `seed-demo.bat`).

### Phase 2: Database Schema, Migrations & Security
- Normalized SQLAlchemy 2.0 ORM models:
  - `departments`, `doctors`, `staff_users`, `patients`, `registrations`
  - `consultation_sessions`, `conversation_messages`, `clinical_encounters`
  - `symptoms`, `vital_signs`, `historical_prescriptions`, `medication_catalogue`
  - `medication_orders`, `laboratory_catalogue`, `laboratory_requests`, `laboratory_results`
  - `radiology_catalogue`, `radiology_requests`, `radiology_reports`
  - `uploaded_documents`, `ai_recommendations`, `clinician_reviews`, `audit_events`
- Alembic migration environment and baseline version.
- Security module: Argon2id password hashing, JWT creation/validation, role-based authorization (Admin, FrontOffice, Clinician, Lab, Radiology, Pharmacy, Auditor).
- Synthetic seed data generator populating realistic, fictitious clinical scenarios.

### Phase 3: Registration Engine & Kiosk Session Management
- Front-office API: dual registration dispatch (`DIRECT_DOCTOR` to mock HIMS, `DIGITAL_DOCTOR` to kiosk repository).
- Kiosk verification service: rate-limited registration lookup with secondary verification factor.
- Short-lived kiosk session tokens, resumption of eligible sessions, state transition manager, and explicit session closure/reset endpoint.
- Audit event capture on all access attempts.

### Phase 4: Frontend Kiosk & Clinician Web Application
- Reusable React components: `Button`, `Input`, `Select`, `Modal`, `ConfirmDialog`, `Toast`, `DataTable`, `Pagination`, `StatusBadge`, `LoadingState`, `EmptyState`, `ErrorState`, `LanguageSwitcher`.
- External CSS styling system: `tokens.css`, `global.css`, `layout.css`, `components.css`, `pages.css`.
- English (`en.js`) and Tamil (`ta.js`) comprehensive translation dictionaries.
- Kiosk feature views: Welcome screen, verification screen, consultation chat workspace, clinical history drawer, document upload modal, emergency red-flag alert banners, session closure confirmation.
- Staff dashboard: Role-based views, registration list, active sessions, clinician review queue (interactive approve/reject), lab/radiology result viewer, pharmacy queue, audit logs, AI & retrieval health diagnostics.

### Phase 5: AI Engine, Vector DB & Clinical RAG Pipeline
- Provider abstraction interface (`AIProviderBase`) with implementations:
  - `MockAIProvider`: rule-grounded, deterministic/semantic simulated responses with structured JSON output, emergency detection, Tamil/English synthesis, and source references.
  - `OpenAIProvider`: real OpenAI API caller with configurable model (`gpt-4o-mini`, etc.), timeouts, retries, and schema validation.
- Vector store abstraction (`VectorStoreBase`) with ChromaDB implementation and graceful in-memory mock fallback for offline test environments.
- RAG pipeline: retrieves MySQL patient encounters + ChromaDB knowledge embeddings, merges approved doctor notes, injects safety guardrails, outputs structured Pydantic schema.
- Emergency symptom classifier: flags chest pain, severe dyspnea, acute neurological deficits, uncontrolled hemorrhage, immediately directing patient to the hospital emergency counter.

### Phase 6: Clinical Workflows, Document Uploads & Human-In-The-Loop Review
- Document ingestion endpoint: MIME type validation, magic byte verification, safe UUID storage, path traversal defenses.
- Document parsing/OCR abstraction with text extraction and vision model explanation.
- Clinician review queue API: approve or reject draft medication orders, lab requests, and radiology orders with audit trail and clinician ID stamp.
- Clinical safety guards preventing unapproved drafts from entering active pharmacy or lab workflows.

### Phase 7: Automated Testing & Verification
- Backend unit and API tests with Pytest and HTTPX:
  - Health checks, auth, registration pathway separation, patient verification, session transitions, emergency detection, doctor approval enforcement, cross-patient isolation.
- Integration tests simulating the complete patient-kiosk-clinician lifecycle.
- Frontend test definitions verifying rendering, language toggles, and form states.

### Phase 8: Documentation & Developer Experience
- Master `README.md` with complete installation guides, Docker instructions, troubleshooting, and architecture diagrams.
- Technical documentation in `docs/` (`ARCHITECTURE.md`, `DATABASE_SCHEMA.md`, `API_GUIDE.md`, `AI_RAG_DESIGN.md`, `CLINICAL_SAFETY.md`, `SECURITY.md`, `TESTING.md`, `DEPLOYMENT.md`, `BACKUP_RESTORE.md`, `TROUBLESHOOTING.md`, `DECISIONS.md`).
- Final delivery verification report.
