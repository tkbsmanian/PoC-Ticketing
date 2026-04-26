---
inclusion: always
---

# Security Standards

All generated code must comply with these security rules. No exceptions for PoC scope.

## Secrets and Configuration

- NEVER hardcode secrets, API tokens, passwords, or connection strings in source code
- NEVER commit `.env` files — only `.env.example` with placeholder values is permitted
- ALL secrets are loaded exclusively from environment variables via `core/config.py` using `pydantic-settings`
- JIRA credentials (`JIRA_API_TOKEN`, `JIRA_USER_EMAIL`) MUST be read from environment — never from the database or any config file checked into source control
- The `SECRET_KEY` used for JWT signing MUST be a minimum 32-byte random value set via environment variable

## Authentication

- Passwords MUST be hashed with `bcrypt` at a minimum cost factor of 12 — use `passlib[bcrypt]`
- JWT tokens MUST be stored in `httpOnly`, `Secure`, `SameSite=Strict` cookies — NEVER in `localStorage` or `sessionStorage`
- JWT tokens MUST include: `sub` (user ID), `role`, `jti` (unique token ID), `exp` (expiry)
- Session timeout is 8 hours of inactivity — implement as a sliding window by refreshing `exp` on each authenticated request
- Logout MUST add the token `jti` to an in-memory blocklist and clear the cookie
- Password reset tokens MUST be cryptographically random (32 bytes, `secrets.token_urlsafe`), stored as a bcrypt hash, and expire after 1 hour

## Authorization

- Every API endpoint MUST declare its required role(s) via `Depends(require_role(...))`
- Service-layer ownership checks MUST be applied for submitter-scoped actions (e.g., only the ticket submitter can call `/remove`)
- A 403 response MUST be returned for authorization failures — NEVER a 404 that leaks resource existence to unauthorized callers
- Role checks MUST be enforced at both the API layer (router dependency) and the service layer — never rely on frontend-only gating

## Input Validation

- ALL request bodies MUST be validated via Pydantic schemas before reaching service or domain logic
- String fields MUST have explicit `max_length` constraints defined in schemas
- File uploads MUST be rejected if size exceeds 10MB — enforce at the FastAPI endpoint before writing to disk
- File uploads MUST validate MIME type against an allowlist: `image/png`, `image/jpeg`, `application/pdf`, `text/plain`, `application/vnd.openxmlformats-officedocument.*`
- File names MUST be sanitized — strip path separators, replace with UUID-based names on disk
- SQL queries MUST use SQLAlchemy ORM or parameterized queries — raw string interpolation into SQL is forbidden

## Encryption

- ALL traffic between browser and backend MUST use HTTPS — Uvicorn must be configured with `ssl_keyfile` and `ssl_certfile`
- The SQLite database file MUST be stored outside the web root and outside any Docker volume mount accessible to the frontend container
- Attachment files MUST be stored outside the web root in a dedicated `uploads/` directory not served directly by the reverse proxy

## Security Logging (OWASP-aligned)

Log the following events at `WARNING` or `ERROR` level. NEVER log passwords, tokens, or full request bodies containing sensitive fields.

| Event | Log Level | Fields to Log |
|---|---|---|
| Successful login | INFO | user_id, timestamp, ip_address |
| Failed login attempt | WARNING | attempted_email (masked after @), timestamp, ip_address |
| Session expiry | INFO | user_id, timestamp |
| Authorization failure (403) | WARNING | user_id, role, endpoint, method, timestamp |
| Invalid status transition attempt | WARNING | user_id, ticket_id, attempted_transition, timestamp |
| File upload rejected | WARNING | user_id, filename, reason, timestamp |
| JIRA sync permanent failure | ERROR | ticket_id, operation, http_status, error_summary, timestamp |
| Admin action (delete, role change) | INFO | admin_user_id, action, target_id, timestamp |
| Password reset requested | INFO | masked_email, timestamp |
| Audit log access | INFO | user_id, query_params, timestamp |

Do NOT log: raw passwords, JWT token values, full JIRA API tokens, full file contents, or PII beyond what is listed above.
