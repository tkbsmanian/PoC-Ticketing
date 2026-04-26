"""
Application configuration loaded exclusively from environment variables.
Never read os.environ directly in application code — use the settings singleton.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── Application ──────────────────────────────────────────────────────────
    APP_ENV: str = "development"          # development | production
    SECRET_KEY: str                        # min 32 bytes — NO DEFAULT, must be set
    LOG_FORMAT: str = "text"              # text | json
    LOG_LEVEL: str = "INFO"

    # ── Database ─────────────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite:///./data/ticketing.db"

    # ── Integration adapter ───────────────────────────────────────────────────
    SYNC_ADAPTER: str = "jira"            # jira | azure_devops

    # ── JIRA Cloud ────────────────────────────────────────────────────────────
    JIRA_BASE_URL: str = ""               # NO DEFAULT in production — must be set
    JIRA_USER_EMAIL: str = ""
    JIRA_API_TOKEN: str = ""              # NO DEFAULT — must be set
    JIRA_PROJECT_KEY: str = "BB"
    JIRA_ISSUE_TYPE: str = "Task"
    JIRA_SYNC_POLL_INTERVAL_SECONDS: int = 10
    JIRA_MAX_RETRY_ATTEMPTS: int = 3

    # ── SMTP ──────────────────────────────────────────────────────────────────
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_ADDRESS: str = "noreply@ticketing.local"
    SMTP_USE_TLS: bool = False

    # ── Frontend ──────────────────────────────────────────────────────────────
    FRONTEND_URL: str = "https://localhost"

    # ── File uploads ──────────────────────────────────────────────────────────
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_BYTES: int = 10_485_760  # 10 MB

    # ── JWT ───────────────────────────────────────────────────────────────────
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_HOURS: int = 8

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    def validate_production_secrets(self) -> None:
        """Fail fast if placeholder secrets are detected in production."""
        if self.is_production():
            if self.SECRET_KEY.startswith("CHANGE_ME"):
                raise RuntimeError(
                    "SECRET_KEY must be set to a real value in production. "
                    "Generate with: openssl rand -hex 32"
                )
            if not self.JIRA_API_TOKEN or self.JIRA_API_TOKEN.startswith("CHANGE_ME"):
                raise RuntimeError("JIRA_API_TOKEN must be set in production.")


@lru_cache
def get_settings() -> Settings:
    """Return the cached settings singleton. Use via FastAPI Depends(get_settings)."""
    settings = Settings()
    settings.validate_production_secrets()
    return settings
