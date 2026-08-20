from functools import lru_cache
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env relative to this file (backend/.env), never relative to the
# process cwd, so the app behaves identically from any working directory.
# In Docker, real environment variables from compose override this file.
_BACKEND_DIR = Path(__file__).resolve().parents[2]
_ENV_FILE = _BACKEND_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE if _ENV_FILE.exists() else ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "ERP/MRP ARPIA API"
    VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"

    # Database - no default for production, dev default only for local
    DATABASE_URL: str = "postgresql+psycopg://arpia:arpia_secret@localhost:5432/arpia"

    # JWT - no default secret for production
    JWT_SECRET_KEY: str = "dev_secret_change_me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # Reduced from 1440 (24h) to 15 min
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        if self.ENVIRONMENT in ("production", "staging"):
            if self.JWT_SECRET_KEY in ("dev_secret_change_me", "CHANGE_ME_USE_SECURE_RANDOM_32_BYTES"):
                raise ValueError(
                    "JWT_SECRET_KEY must be configured with a secure secret in production/staging!"
                )
            if self.DATABASE_URL in (
                "postgresql+psycopg://arpia:arpia_secret@localhost:5432/arpia",
                "postgresql+psycopg://arpia:CHANGE_ME@db:5432/arpia",
            ):
                raise ValueError(
                    "DATABASE_URL must be configured with the production database in production/staging!"
                )
            if self.CORS_ORIGINS in ("", "http://localhost:5173,http://localhost:3000"):
                raise ValueError(
                    "CORS_ORIGINS must be explicitly configured for production/staging!"
                )
            if self.REFRESH_TOKEN_EXPIRE_DAYS > 30:
                raise ValueError(
                    "REFRESH_TOKEN_EXPIRE_DAYS should not exceed 30 days in production!"
                )
            if self.ACCESS_TOKEN_EXPIRE_MINUTES > 60:
                raise ValueError(
                    "ACCESS_TOKEN_EXPIRE_MINUTES should not exceed 60 minutes in production!"
                )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()