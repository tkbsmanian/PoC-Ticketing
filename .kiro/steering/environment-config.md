---
inclusion: always
---

# Environment and Configuration Standards

All configuration must be environment-driven. No hardcoded values, no config files checked into source control.

## Configuration Loading

All settings are loaded in `backend/app/core/config.py` using `pydantic-settings`:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Application
    APP_ENV: str = "development"          # development | production
    SECRET_KEY: str                        # min 32 bytes, no default
    LOG_FORMAT: str = "text"              # text | json
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "sqlite:///./data/ticketing.db"

    # JIRA
    SYNC_ADAPTER: str = "jira"            # jira | azure_devops
    JIRA_BASE_URL: str
    JIRA_USER_EMAIL: str
    JIRA_API_TOKEN: str                    # no default — must be set
    JIRA_PROJECT_KEY: str = "BB"
    JIRA_ISSUE_TYPE: str = "Task"
    JIRA_SYNC_POLL_INTERVAL_SECONDS: int = 10
    JIRA_MAX_RETRY_ATTEMPTS: int = 3

    # SMTP
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""               # empty = no auth (dev only)
    SMTP_FROM_ADDRESS: str = "noreply@ticketing.local"
    SMTP_USE_TLS: bool = True

    # Frontend
    FRONTEND_URL: str = "https://localhost"

    # File uploads
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_BYTES: int = 10_485_760  # 10MB

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

## Rules

- `SECRET_KEY`, `JIRA_API_TOKEN`, `JIRA_USER_EMAIL`, `JIRA_BASE_URL` have NO defaults — the application MUST fail to start if they are missing
- Settings MUST be accessed via the `settings` singleton — never via `os.environ.get()` directly in application code
- The `settings` singleton is created once in `core/config.py` and injected via FastAPI `Depends(get_settings)`
- `.env` files MUST be listed in `.gitignore` — only `.env.example` is committed
- Docker Compose passes secrets via `environment:` block referencing host environment variables — never hardcoded in `docker-compose.yml`

## .env.example Template

The repository MUST contain `.env.example` at the root with all variables documented:

```dotenv
# Application
APP_ENV=development
SECRET_KEY=CHANGE_ME_generate_with_openssl_rand_hex_32
LOG_FORMAT=text
LOG_LEVEL=INFO

# Database
DATABASE_URL=sqlite:///./data/ticketing.db

# Integration adapter
SYNC_ADAPTER=jira

# JIRA Cloud
JIRA_BASE_URL=https://your-org.atlassian.net
JIRA_USER_EMAIL=service-account@your-org.com
JIRA_API_TOKEN=CHANGE_ME_from_id.atlassian.com
JIRA_PROJECT_KEY=BB
JIRA_ISSUE_TYPE=Task
JIRA_SYNC_POLL_INTERVAL_SECONDS=10
JIRA_MAX_RETRY_ATTEMPTS=3

# SMTP
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM_ADDRESS=noreply@ticketing.local
SMTP_USE_TLS=false

# Frontend
FRONTEND_URL=https://localhost

# File uploads
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE_BYTES=10485760
```

## Environment-Specific Behaviour

| Setting | Development | Production |
|---|---|---|
| `LOG_FORMAT` | `text` | `json` |
| `SMTP_USE_TLS` | `false` (MailHog) | `true` |
| `DATABASE_URL` | SQLite file | SQLite file (same for PoC) |
| SSL certs | Self-signed | Org-issued |
| `APP_ENV` | `development` | `production` |

When `APP_ENV=production`, the application MUST:
- Reject startup if `SECRET_KEY` is the placeholder value `CHANGE_ME*`
- Set all cookies with `Secure=True`
- Use JSON log format regardless of `LOG_FORMAT` setting
