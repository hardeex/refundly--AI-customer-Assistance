"""Application configuration, loaded from environment variables / .env."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = "AI-Powered Customer Support Refund System"
    environment: str = "development"
    debug: bool = True

    # Database
    database_url: str

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # JWT authentication (admin/support dashboard login)
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30
    password_reset_token_expire_minutes: int = 15

    # Anthropic / AI configuration
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"
    anthropic_version: str = "2023-06-01"
    anthropic_timeout: int = 120

    # Refund policy defaults, used when a tenant hasn't overridden them
    default_auto_approve_ceiling: float = 500.0
    default_return_window_days: int = 30

    # Seed script only - see seed/seed_data.py for why this exists
    demo_api_key: str | None = None


@lru_cache
def get_settings() -> Settings:
    """Settings are read once and cached; env vars don't change at runtime."""
    return Settings()
