# Digital Doctor: Security, Privacy & Compliance Architecture

## 1. Security Architecture Summary

Digital Doctor implements multi-tiered defense-in-depth protections tailored for hospital environments handling Protected Health Information (PHI).

---

## 2. Implemented Security Controls

### 2.1 Staff Authentication & Role-Based Access Control (RBAC)
- **Password Hashing**: Staff passwords use Argon2id with random salt and memory-hardness parameters (PBKDF2 HMAC-SHA256 fallback).
- **JWT Cryptography**: Signed with HMAC SHA-256 (`HS256`), carrying user ID, role, and expiration timestamp.
- **Role Enforcement**: Backend endpoints enforce strict role checks (`ADMIN`, `FRONT_OFFICE`, `DOCTOR`, `LAB_STAFF`, `RADIOLOGY_STAFF`, `PHARMACY_STAFF`, `AUDITOR`).

### 2.2 Kiosk Multi-Factor Identity Verification & Privacy Reset
- **Secondary Factor Verification**: Kiosk lookup reveals only masked patient initials (`K*** R***`). Full records require matching the secondary factor (Birth Year or PIN).
- **Short-Lived Kiosk Tokens**: 15-minute sliding session window.
- **Inactivity Expiration**: Automated server-side and client-side expiration.
- **Atomic Kiosk State Wipe**: On consultation closure, browser tokens, cached conversation state, and temporary upload previews are wiped, returning the kiosk to the welcome screen.

### 2.3 Strict Cross-Patient Isolation
- All database queries and vector retrievals are filtered by the authenticated session's `patient_id`.
- Automated security test (`test_cross_patient_data_isolation`) verifies that Patient A's session token cannot read Patient B's records.

### 2.4 File Upload Security
- **MIME & Magic Byte Verification**: Validates file headers (`%PDF`, `\x89PNG`, `\xff\xd8\xff`).
- **Path Traversal Defense**: Uploaded files are renamed to server-generated UUID4 strings and stored outside web root directories (`/app/uploads/`).
- **File Size Limits**: Enforced maximum of 10MB per upload.

### 2.5 Structured Logging & PHI Redaction
- `RedactingFormatter` automatically scrubs API keys, bearer tokens, passwords, patient phone numbers, and email addresses from application logs.

---

## 3. Production Deployment Checklist
Prior to clinical deployment in a live hospital environment:
1. Enforce TLS 1.3 across all ingress routers.
2. Enable MySQL Transparent Data Encryption (TDE) for data-at-rest.
3. Configure institutional identity federation (SAML / OAuth2 / OIDC) for hospital staff.
4. Conduct independent third-party penetration testing and statutory privacy review under applicable national healthcare data laws.
