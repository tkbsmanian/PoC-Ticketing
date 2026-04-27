# Implementation Tasks

## Epic 1: Project Foundation and Infrastructure

### Story 1.1: Backend project setup
- [x] 1.1.1 Initialise Python project with pyproject.toml, install FastAPI, SQLAlchemy, passlib, python-jose, httpx, pydantic-settings, hypothesis, pytest
- [x] 1.1.2 Create directory structure per architecture steering rules (domain, services, repositories, adapters, api, models, schemas, core)
- [x] 1.1.3 Implement core/config.py with pydantic-settings and production secret validation
- [x] 1.1.4 Implement core/logging.py with structured JSON/text logging and configure_logging()
- [x] 1.1.5 Implement core/middleware.py with RequestIDMiddleware and SecurityHeadersMiddleware
- [x] 1.1.6 Create .env.example with all required variables documented

### Story 1.2: Database initialisation
- [x] 1.2.1 Implement db/base.py declarative base and db/session.py SQLAlchemy engine for SQLite
- [x] 1.2.2 Create all ORM models (users, departments, tickets, approvals, comments, attachments, notifications, audit_log, sync_queue)
- [x] 1.2.3 Implement db/init_db.py and wire into FastAPI startup event
- [x] 1.2.4 Add indexes per design schema (ticket_id, status, submitter_id, department_id, created_at, sync_queue.status)

### Story 1.3: Frontend project setup
- [x] 1.3.1 Scaffold Vite + React + TypeScript project with path aliases (@/)
- [x] 1.3.2 Install react-router-dom, axios, vitest, @testing-library/react
- [x] 1.3.3 Create src/types/index.ts with all domain types
- [x] 1.3.4 Create API client layer (src/api/client.ts with 401 interceptor, auth.ts, tickets.ts, comments.ts, attachments.ts, approvals.ts, notifications.ts, admin.ts)
- [x] 1.3.5 Create AuthContext, useAuth hook, and AuthGuard component
- [x] 1.3.6 Create usePermissions hook as single source of truth for role-based UI rendering

---

## Epic 2: Authentication and User Management

### Story 2.1: Backend authentication
- [x] 2.1.1 Implement core/security.py — bcrypt hashing (cost 12), JWT creation/decode, token blocklist, reset token generation
- [x] 2.1.2 Implement AuthService — login, logout, request_password_reset, confirm_password_reset
- [x] 2.1.3 Implement POST /auth/login — validate credentials, set httpOnly JWT cookie, return AuthUser
- [x] 2.1.4 Implement POST /auth/logout — revoke JTI, clear cookie
- [x] 2.1.5 Implement POST /auth/password-reset/request and /auth/password-reset/confirm
- [x] 2.1.6 Implement GET /auth/me — return current user from JWT cookie
- [x] 2.1.7 Implement require_role() FastAPI dependency factory
- [x] 2.1.8 Write unit tests: password hashing, JWT encode/decode, token expiry, blocklist, reset token flow

### Story 2.2: User and department management API
- [x] 2.2.1 Implement GET/POST /users and PATCH /users/{id} (platform_admin only)
- [x] 2.2.2 Implement GET /users/managers — list users with it_manager role for submission dropdown
- [x] 2.2.3 Implement GET/POST /departments and PATCH /departments/{id} (platform_admin only)
- [x] 2.2.4 Write integration tests: create user, deactivate user, 403 for non-admin

### Story 2.3: Frontend authentication screens
- [x] 2.3.1 Implement LoginPage with form validation, error display, and role-based redirect after login
- [x] 2.3.2 Implement PasswordResetPage (request and confirm flows)
- [x] 2.3.3 Wire AuthGuard to redirect unauthenticated users to /login
- [x] 2.3.4 Write component tests: LoginPage renders error on bad credentials, AuthGuard redirects unauthenticated

---

## Epic 3: Ticket Domain and Core API

### Story 3.1: Domain logic
- [x] 3.1.1 Implement domain/enums.py — TicketStatus, UserRole, UrgencyLevel, PriorityLevel, SyncOperation, SyncStatus
- [x] 3.1.2 Implement domain/ticket_lifecycle.py — VALID_TRANSITIONS table, is_valid_transition(), is_terminal(), is_deletable(), is_removable_by_submitter()
- [x] 3.1.3 Implement domain/approval_rules.py — requires_director_approval() pure function
- [x] 3.1.4 Implement domain/exceptions.py — all domain exception classes
- [x] 3.1.5 Implement domain/interfaces.py — SyncAdapter ABC and ExternalTaskRef dataclass
- [x] 3.1.6 Write unit tests for all 8 urgency×cost combinations in requires_director_approval()
- [x] 3.1.7 Write unit tests for every valid and invalid transition pair in VALID_TRANSITIONS

### Story 3.2: Ticket service and API
- [x] 3.2.1 Implement TicketService — create_ticket, transition_status, remove_ticket, soft_delete, update_category_priority
- [x] 3.2.2 Implement POST /tickets — create ticket, enqueue JIRA sync, return TicketDetail
- [x] 3.2.3 Implement GET /tickets — role-scoped list with filters (status, category, priority, department_id, submitter_id, page)
- [x] 3.2.4 Implement GET /tickets/{id} — role-scoped detail with comments, attachments, history, approvals
- [x] 3.2.5 Implement PATCH /tickets/{id}/status — validate transition, update, enqueue sync, notify submitter
- [x] 3.2.6 Implement PATCH /tickets/{id}/category-priority — IT triage only
- [x] 3.2.7 Implement POST /tickets/{id}/remove — submitter withdraws own ticket
- [x] 3.2.8 Implement POST /tickets/{id}/reopen — IT or submitter re-opens Resolved ticket
- [x] 3.2.9 Implement DELETE /tickets/{id} — platform_admin soft-delete of Closed/Rejected only
- [x] 3.2.10 Write integration tests: submit ticket returns 201 with ticket_id, missing title returns 422, business_user cannot see other users' tickets (403), invalid transition returns 422

### Story 3.3: Approval workflow API
- [x] 3.3.1 Implement ApprovalService — create_manager_approval, decide (approve/reject with sequential Director step)
- [x] 3.3.2 Implement GET /approvals/pending — list open approvals for current it_manager user
- [x] 3.3.3 Implement POST /approvals/{id}/approve — record decision, create Director approval row if required, notify parties
- [x] 3.3.4 Implement POST /approvals/{id}/reject — record rejection, set ticket to Rejected, notify submitter
- [x] 3.3.5 Implement 48-hour approval timeout background job — re-notify approver, write audit entry
- [x] 3.3.6 Write integration tests: Manager approve triggers Director approval when director_required=true, Manager reject sets ticket to Rejected immediately, approver cannot act on approval not assigned to them (403)

---

## Epic 4: Comments, Attachments, and Notifications

### Story 4.1: Comments API
- [x] 4.1.1 Implement GET /tickets/{id}/comments — filter internal comments by role
- [x] 4.1.2 Implement POST /tickets/{id}/comments — create comment, enqueue JIRA sync for public comments only, notify other party
- [x] 4.1.3 Write integration tests: internal comment hidden from business_user, public comment visible to all, comment on Closed ticket returns 403

### Story 4.2: Attachments API
- [x] 4.2.1 Implement POST /tickets/{id}/attachments — validate MIME type allowlist, enforce 10MB limit, store with UUID filename, enqueue JIRA sync
- [x] 4.2.2 Implement GET /tickets/{id}/attachments/{aid} — role-scoped download, stream file
- [x] 4.2.3 Write integration tests: file over 10MB returns 413, disallowed MIME type returns 422, attachment stored with UUID name not original filename

### Story 4.3: Notification service
- [x] 4.3.1 Implement NotificationService — write in-portal rows and send plain-text emails via SmtpAdapter
- [x] 4.3.2 Implement adapters/smtp_adapter.py — send() with TLS support, failure logged not raised
- [x] 4.3.3 Implement adapters/email_templates.py — all notification message templates as constants
- [x] 4.3.4 Implement GET /notifications, POST /notifications/{id}/read, POST /notifications/read-all
- [x] 4.3.5 Write integration tests: notification row created for each trigger event, SMTP failure does not block ticket creation

---

## Epic 5: Audit Trail

### Story 5.1: Audit service and API
- [x] 5.1.1 Implement AuditService.record() — append-only INSERT, never UPDATE/DELETE
- [x] 5.1.2 Wire AuditService into TicketService, ApprovalService, and AuthService for all required events
- [x] 5.1.3 Implement GET /audit/tickets/{id} — full audit trail for a ticket (platform_admin and auditor only)
- [x] 5.1.4 Implement GET /audit/log — filterable system-wide audit log (platform_admin and auditor only)
- [x] 5.1.5 Write integration tests: audit log count never decreases after mutations, business_user cannot access audit endpoints (403)

---

## Epic 6: JIRA Sync Integration

### Story 6.1: Sync queue and worker
- [x] 6.1.1 Implement SyncService.enqueue() with deduplication guard and jira_task_id guard
- [x] 6.1.2 Implement SyncWorker — poll sync_queue every 10s, dispatch to adapter, retry with 10s/30s/90s backoff, mark failed after 3 attempts
- [x] 6.1.3 Wire SyncWorker into FastAPI lifespan using APScheduler or asyncio background task
- [x] 6.1.4 Implement GET /sync/health — return last_success_at, pending_count, failed_count, adapter name

### Story 6.2: JIRA Cloud adapter
- [x] 6.2.1 Implement adapters/jira_mappings.py — PORTAL_STATUS_TO_JIRA, PORTAL_PRIORITY_TO_JIRA, ALLOWED_MIME_TYPES constants
- [x] 6.2.2 Implement adapters/jira_utils.py — to_adf(), truncate_summary(), build_labels()
- [x] 6.2.3 Implement JiraAdapter.create_task() — create metadata discovery with 1h cache, idempotency label check, ADF description, reporter lookup with fallback
- [x] 6.2.4 Implement JiraAdapter.update_status() — dynamic transition ID lookup, map portal status to JIRA status
- [x] 6.2.5 Implement JiraAdapter.add_comment() — ADF body, [Portal] prefix, skip internal comments
- [x] 6.2.6 Implement JiraAdapter.attach_file() — multipart upload with X-Atlassian-Token header
- [x] 6.2.7 Implement error classification — transient (5xx, 429, timeout) vs permanent (400, 401, 403, 404), 401/403 triggers platform_admin notification
- [x] 6.2.8 Write unit tests using mock HTTP client: create_task returns ExternalTaskRef, duplicate prevention via label search, ADF conversion, priority mapping (Critical→Highest), internal comment not synced

### Story 6.3: Azure DevOps adapter stub
- [x] 6.3.1 Implement AzureDevOpsAdapter stub that raises NotImplementedError with clear message
- [x] 6.3.2 Verify SYNC_ADAPTER=azure_devops raises at startup with actionable error

---

## Epic 7: Business Portal Frontend

### Story 7.1: Portal routing and layouts
- [x] 7.1.1 Implement BusinessLayout with nav (My Requests, Submit Request, Approvals if manager), NotificationBell, user name, sign out
- [x] 7.1.2 Implement ITLayout with nav (Ticket Queue, Dashboard, Audit Log, Admin), role badge
- [x] 7.1.3 Wire App.tsx routes with AuthGuard role restrictions per design route table

### Story 7.2: Business ticket list and submission
- [x] 7.2.1 Implement BusinessTicketListPage — own tickets only, status badge, sync failed badge, link to detail
- [x] 7.2.2 Implement SubmitTicketPage — all form fields with validation, department and manager dropdowns, file upload with 10MB client-side check, director approval hint text
- [x] 7.2.3 Write component tests: form shows error when title is empty, cost field shows director approval hint, file over 10MB shows error

### Story 7.3: Ticket detail page
- [x] 7.3.1 Implement TicketDetailPage — header with status badge, JIRA link, meta fields, description
- [x] 7.3.2 Implement StatusTimeline — chronological history entries with event formatting
- [x] 7.3.3 Implement CommentThread — public/internal toggle for IT roles, internal badge, closed ticket disables form
- [x] 7.3.4 Implement ITActionPanel — valid next-status buttons from lifecycle table, category/priority form
- [x] 7.3.5 Write component tests: internal comments hidden for business_user, closed ticket shows disabled comment form, JIRA link renders when jira_task_url present

---

## Epic 8: IT Operations Portal Frontend

### Story 8.1: IT ticket queue
- [x] 8.1.1 Implement ITTicketListPage — all tickets, filter bar (status, department, priority), sync failed row highlight, pagination
- [x] 8.1.2 Implement DashboardPage — ticket counts by status, sync health panel for permitted roles
- [x] 8.1.3 Write component tests: filter bar updates ticket list, sync health shows failed count in red when > 0

### Story 8.2: Admin configuration screen
- [x] 8.2.1 Implement AdminPage with tabs (Users, Departments, Audit Log)
- [x] 8.2.2 Implement UserManagement — list users, create user form, activate/deactivate toggle
- [x] 8.2.3 Implement DepartmentManagement — list departments, add department, activate/deactivate
- [x] 8.2.4 Implement AuditLogView — filterable table, event type filter input
- [x] 8.2.5 Write component tests: create user form validates required fields, deactivate button calls correct API

---

## Epic 9: Property-Based Tests

- [x] 9.1 Property 1 — valid ticket submission creates persisted ticket with status Pending
- [x] 9.2 Property 2 — empty/whitespace title or description is rejected, ticket count unchanged
- [x] 9.3 Property 3 — director_approval_required flag correct for all urgency×cost combinations
- [x] 9.4 Property 4 — only valid status transitions accepted; terminal states reject all transitions
- [x] 9.5 Property 5 — audit log entry count is monotonically non-decreasing across any mutation sequence
- [x] 9.6 Property 6 — internal comments never visible to business_user, it_manager, or auditor roles
- [x] 9.7 Property 7 — soft-deleted ticket invisible to all non-admin roles, data retained in DB
- [x] 9.8 Property 8 — Director approval row not created until Manager has approved
- [x] 9.9 Property 9 — comment body and author preserved on round-trip
- [x] 9.10 Property 10 — GET /tickets returns only tickets the authenticated user is authorised to see

---

## Epic 10: Deployment and Operations

- [x] 10.1 Create Dockerfile for backend (Python 3.12, non-root user, uploads volume mount)
- [x] 10.2 Create Dockerfile for frontend (Node build stage, nginx serve stage)
- [x] 10.3 Create docker-compose.yml with backend, frontend, nginx reverse proxy, MailHog for dev SMTP
- [x] 10.4 Create nginx.conf — HTTPS termination with self-signed cert, proxy /api to backend, serve React SPA
- [x] 10.5 Create .env.example at repo root with all variables documented
- [x] 10.6 Write README.md with local setup steps (generate cert, copy .env.example, docker compose up)
- [x] 10.7 Implement GET /health endpoint returning app status and DB connectivity check
