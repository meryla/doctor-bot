from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Single source of truth for all configuration.

    Values are loaded from environment variables / a .env file.
    Nothing in the app should call os.getenv() directly anymore ---
    everything goes through an instance of this class (see get_settings()
    below).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ---------- App ----------
    environment: str = Field(default="development")  # development | staging | production
    debug: bool = Field(default=True)

    # ---------- OpenAI ----------
    openai_api_key: str

    # ---------- Database (Postgres, async) ----------
    # Expected form: postgresql+asyncpg://user:password@host:port/dbname
    database_url: str = Field(default="postgresql+asyncpg://doctorbot:doctorbot@localhost:5432/doctorbot")

    # ---------- Auth / JWT ----------
    jwt_secret: str
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_token_expire_minutes: int = Field(default=60)

    # ---------- Redis / Celery ----------
    redis_url: str = Field(default="redis://localhost:6379/0")

    # ---------- Google Calendar OAuth (web flow) ----------
    google_client_id: str = Field(default="")
    google_client_secret: str = Field(default="")
    google_redirect_uri: str = Field(default="http://localhost:8000/calendar/oauth/callback")

    # ---------- CORS ----------
    # Comma-separated list in .env, e.g. "http://localhost:8501,https://myapp.com"
    allowed_origins: str = Field(default="http://localhost:8501")

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings accessor. Import and call this everywhere you need
    config, e.g.:

        from app.core.config import get_settings
        settings = get_settings()

    The lru_cache means the .env file is only read once per process,
    and FastAPI's dependency injection can use get_settings directly
    as a dependency if a route ever needs request-scoped access to it.
    """
    return Settings()