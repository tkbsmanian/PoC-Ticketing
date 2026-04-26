---
inclusion: always
---

# Logging Standards

All generated code must use structured logging. Print statements are not acceptable in production code.

## Logger Setup

Use Python's `structlog` or the standard `logging` module configured in `core/logging.py`. Every module gets its own logger:

```python
import logging
logger = logging.getLogger(__name__)
```

Never use the root logger directly. Never use `print()` for diagnostic output.

## Log Format

All log output MUST be structured JSON in production mode and human-readable in development mode. Controlled by `LOG_FORMAT` environment variable (`json` or `text`).

Required fields on every log entry:
- `timestamp` (ISO 8601 UTC)
- `level`
- `logger` (module name)
- `message`
- `request_id` (injected by middleware for HTTP requests)

## Log Levels

| Level | When to use |
|---|---|
| `DEBUG` | Detailed flow tracing — disabled in production |
| `INFO` | Normal operations: login, ticket created, sync success |
| `WARNING` | Recoverable issues: failed login, retry attempt, validation rejection |
| `ERROR` | Failures requiring attention: sync exhausted, DB error, unhandled exception |
| `CRITICAL` | System cannot continue: startup failure, DB unreachable |

## What to Log

### Always log (INFO):
- Ticket created: `ticket_id`, `submitter_id`, `department`
- Status transition: `ticket_id`, `old_status`, `new_status`, `actor_id`
- JIRA sync success: `ticket_id`, `jira_task_id`, `operation`, `duration_ms`
- Approval decision: `ticket_id`, `approver_id`, `decision`
- User created/deactivated: `admin_id`, `target_user_id`, `action`

### Always log (WARNING):
- Failed login: masked email only (`j***@example.com`), `ip_address`
- Authorization failure: `user_id`, `role`, `endpoint`, `method`
- Sync retry: `ticket_id`, `operation`, `attempt_number`, `error_type`
- File upload rejected: `user_id`, `reason` (no filename with path)
- Invalid transition attempt: `ticket_id`, `attempted_transition`, `user_id`

### Always log (ERROR):
- Sync permanently failed: `ticket_id`, `operation`, `final_error_type`, `attempt_count`
- Unhandled exception: exception type, message, stack trace (no request body)
- DB write failure: operation type, error message (no row data)
- JIRA auth failure (401/403): `operation`, `http_status` (no token value)

## What NEVER to Log

- Passwords (plain or hashed)
- JWT token values or `jti`
- JIRA API tokens or any credential value
- Full request or response bodies
- File contents
- Full email addresses in warning/error logs (mask to `j***@domain.com`)
- SQLite row data containing ticket descriptions or comment bodies
- PII beyond user_id and masked email

## Request ID Middleware

Every HTTP request MUST be assigned a `request_id` (UUID4) by FastAPI middleware. This ID is:
- Added to all log entries during the request lifecycle
- Returned in the response header `X-Request-ID`
- Used to correlate logs across service calls within a single request

```python
# core/middleware.py
import uuid
from starlette.middleware.base import BaseHTTPMiddleware

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = str(uuid.uuid4())
        # bind to context var for logger access
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
```

## Background Worker Logging

The JIRA sync worker MUST log each poll cycle at `DEBUG` level and each sync event outcome at `INFO` or `ERROR`. Include `sync_event_id` and `ticket_id` on every sync log entry.
