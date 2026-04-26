---
inclusion: always
---

# Architecture Standards

This project follows clean architecture with strict layer separation. Kiro must enforce these boundaries in all generated code.

## Layer Structure

```
backend/
  app/
    api/          ← HTTP layer only: routing, request parsing, response serialization
    domain/       ← Pure business logic: no I/O, no framework imports
    services/     ← Orchestration: calls domain + repositories + external adapters
    repositories/ ← Data access only: SQLAlchemy queries, no business logic
    adapters/     ← External integrations: JIRA, Azure DevOps, SMTP
    models/       ← SQLAlchemy ORM models
    schemas/      ← Pydantic request/response schemas
    core/         ← Config, security utilities, logging setup
frontend/
  src/
    pages/        ← Route-level components
    components/   ← Reusable UI components
    hooks/        ← Custom React hooks
    api/          ← Axios API client functions
    types/        ← TypeScript interfaces and types
```

## Mandatory Rules

- `domain/` modules MUST NOT import from `api/`, `repositories/`, `adapters/`, or any framework (FastAPI, SQLAlchemy)
- `api/` routers MUST NOT contain business logic — delegate to `services/`
- `repositories/` MUST NOT contain business logic — only query construction and result mapping
- `adapters/` MUST implement the `SyncAdapter` interface defined in `domain/interfaces.py`
- JIRA-specific logic MUST live exclusively in `adapters/jira_adapter.py` — never in services or domain
- Azure DevOps logic MUST live exclusively in `adapters/azure_devops_adapter.py`
- The active adapter is selected at startup via the `SYNC_ADAPTER` environment variable — never hardcoded
- Cross-layer imports flow in one direction only: `api → services → domain`, `services → repositories`, `services → adapters`
- Circular imports between layers are forbidden

## Domain Model Rules

- Domain entities in `domain/` are plain Python dataclasses or Pydantic models — no ORM decorators
- ORM models in `models/` are separate from domain entities — use repository mappers to convert between them
- Business rules (e.g., valid status transitions, director approval computation) live in `domain/` as pure functions
- Status transition validation MUST use the transition table in `domain/ticket_lifecycle.py` — not ad-hoc if/else chains

## Frontend Rules

- API calls MUST go through `src/api/` client functions — no direct `axios` calls in components
- Business logic MUST NOT live in React components — extract to custom hooks in `src/hooks/`
- Role-based UI rendering MUST use a central `usePermissions()` hook — not inline role string comparisons
