# Internal Ticketing System — PoC

A locally hosted web portal for business users to submit service requests, with JIRA synchronisation and a two-tier approval workflow.

## Stack

- **Frontend**: React + TypeScript (Vite)
- **Backend**: Python 3.12 + FastAPI
- **Database**: SQLite (local file)
- **Reverse proxy**: nginx (HTTPS)
- **Dev email**: MailHog (view at http://localhost:8025)

---

## Quick Start

### 1. Prerequisites

- Docker Desktop (Windows / macOS) or Docker Engine + Compose (Linux)
- `openssl` available in your terminal

### 2. Generate a self-signed TLS certificate

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/certs/key.pem \
  -out nginx/certs/cert.pem \
  -subj "/CN=localhost"
```

### 3. Configure environment

```bash
cp .env.example backend/.env
```

Open `backend/.env` and set:

```dotenv
SECRET_KEY=<output of: openssl rand -hex 32>
SYNC_ADAPTER=mock          # use 'jira' when you have real credentials
```

To use real JIRA, also set:
```dotenv
SYNC_ADAPTER=jira
JIRA_BASE_URL=https://your-org.atlassian.net
JIRA_USER_EMAIL=service-account@your-org.com
JIRA_API_TOKEN=<token from id.atlassian.com>
JIRA_PROJECT_KEY=BB
```

### 4. Start the application

```bash
docker compose up --build
```

The portal is available at **https://localhost** (accept the self-signed cert warning in your browser).

MailHog web UI (view sent emails): **http://localhost:8025**

### 5. Create the first admin user

Once the backend is running, exec into the container to seed an admin account:

```bash
docker compose exec backend python -c "
from app.db.session import SessionLocal
from app.db.init_db import init_db
from app.models.user import UserModel, DepartmentModel
from app.core.security import hash_password

init_db()
db = SessionLocal()
dept = DepartmentModel(name='IT', is_active=True)
db.add(dept)
db.commit()
admin = UserModel(
    email='admin@example.com',
    display_name='Platform Admin',
    password_hash=hash_password('ChangeMe123!'),
    role='platform_admin',
    department_id=dept.id,
    is_active=True,
)
db.add(admin)
db.commit()
print('Admin created: admin@example.com / ChangeMe123!')
"
```

Log in at https://localhost with those credentials, then use the Admin panel to create additional users.

---

## Running Tests

### Backend unit + integration tests

```bash
cd backend
pip install -e ".[dev]"
pytest tests/unit tests/integration -v
```

### Property-based tests (Hypothesis)

```bash
pytest tests/property -v --hypothesis-show-statistics
```

### Frontend tests

```bash
cd frontend
npm install
npm test
```

---

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/          # HTTP routers (no business logic)
│   │   ├── domain/       # Pure business rules (no I/O)
│   │   ├── services/     # Orchestration layer
│   │   ├── repositories/ # Data access
│   │   ├── adapters/     # JIRA, SMTP, mock integrations
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── schemas/      # Pydantic request/response schemas
│   │   ├── core/         # Config, security, middleware
│   │   ├── db/           # Engine, session, init
│   │   └── workers/      # Background sync + approval timeout jobs
│   └── tests/
│       ├── unit/         # Pure logic tests
│       ├── integration/  # API tests against in-memory SQLite
│       └── property/     # Hypothesis property-based tests
├── frontend/
│   └── src/
│       ├── api/          # Axios API client functions
│       ├── components/   # Shared UI components
│       ├── context/      # AuthContext
│       ├── hooks/        # useAuth, usePermissions, useNotifications
│       ├── layouts/      # BusinessLayout, ITLayout
│       ├── pages/        # Route-level page components
│       └── types/        # TypeScript domain types
├── nginx/
│   ├── nginx.conf        # Reverse proxy + HTTPS termination
│   └── certs/            # TLS certificate (not committed)
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Switching to Real JIRA

1. Set `SYNC_ADAPTER=jira` in `backend/.env`
2. Fill in `JIRA_BASE_URL`, `JIRA_USER_EMAIL`, `JIRA_API_TOKEN`, `JIRA_PROJECT_KEY`
3. Ensure the JIRA service account has: Browse projects, Create issues, Edit issues, Add comments, Create attachments
4. Restart: `docker compose restart backend`

Sync health is visible at **https://localhost/api/sync/health** (IT Triage and Admin roles).

---

## Stopping

```bash
docker compose down
```

Data persists in Docker volumes (`backend_data`, `backend_uploads`). To wipe everything:

```bash
docker compose down -v
```
