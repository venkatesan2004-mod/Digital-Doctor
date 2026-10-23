# Digital Doctor: Troubleshooting & Diagnostic Guide

## 1. Common Operational Issues

### 1.1 Backend Container Fails to Connect to MySQL
- **Symptom**: `OperationalError: (2003, "Can't connect to MySQL server on 'mysql'")`
- **Cause**: MySQL initialization takes 10-15 seconds on initial start while initializing InnoDB tables.
- **Resolution**:
  - The `compose.yaml` relies on `service_healthy` conditions. Ensure MySQL healthcheck ping succeeds:
    ```cmd
    docker compose logs -f mysql
    ```
  - Verify that host port 3306 is not in conflict with a locally running MySQL instance. Modify `MYSQL_PORT` in `.env` if needed.

### 1.2 Kiosk Registration Lookup Returns 404
- **Symptom**: Registration lookup yields "Registration not found or not registered for Digital Doctor kiosk."
- **Causes**:
  1. The registration was created under `DIRECT_DOCTOR` pathway. (Direct Doctor registrations are intentionally routed exclusively to external HIMS and cannot access Kiosks).
  2. The registration ID was entered incorrectly. Check the recent list in the Staff Dashboard (`/staff` -> Registrations).
  3. The secondary verification factor did not match. (Default demo birth year for synthetic records: `1985` for Karthik Raja, `1990` for Meena Swaminathan).

### 1.3 OpenAI Provider Returning Rate Limit or Timeout Errors
- **Symptom**: `OpenAI provider failed after 3 attempts. Falling back to Mock.`
- **Cause**: Invalid or expired `OPENAI_API_KEY`, network proxy blocking `api.openai.com`, or insufficient account quota.
- **Resolution**:
  - The application automatically degrades gracefully to `MockAIProvider` so clinical testing is never halted.
  - Set `AI_PROVIDER=mock` in `.env` to operate completely offline.

### 1.4 Rate Limiting Lockout on Kiosk Screen
- **Symptom**: HTTP 429 "Too many verification attempts."
- **Resolution**:
  - The sliding window allows 5 attempts per 300 seconds. Wait 5 minutes or reset the in-memory limiter by restarting the backend container.
