"""RelayOps API configuration with environment-aware validation."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


Environment = Literal["development", "staging", "production", "test"]


class Settings(BaseSettings):
    """Application settings loaded from environment variables (RELAYOPS_ prefix)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="RELAYOPS_",
        extra="ignore",
        case_sensitive=False,
    )

    environment: Environment = "development"
    debug: bool = False
    database_url: str = "postgresql+asyncpg://relayops:relayops@localhost:5432/relayops"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = Field(default="change-me-in-production")
    access_token_expire_minutes: int = Field(default=60, ge=5, le=1440)
    refresh_token_expire_days: int = Field(default=7, ge=1, le=90)
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    log_level: str = "INFO"
    log_json: bool = True
    default_page_size: int = Field(default=50, ge=1, le=200)
    max_page_size: int = Field(default=200, ge=10, le=500)
    request_timeout_seconds: float = Field(default=30.0, ge=1.0)
    rate_limit_per_minute: int = Field(default=120, ge=10)
    export_max_rows: int = Field(default=10_000, ge=100)
    search_max_results: int = Field(default=500, ge=50)
    webhook_timeout_seconds: int = Field(default=30, ge=5)
    bcrypt_rounds: int = Field(default=12, ge=10, le=14)

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, value: str, info) -> str:
        env = info.data.get("environment", "development")
        if env == "production" and value == "change-me-in-production":
            raise ValueError("RELAYOPS_SECRET_KEY must be set in production")
        if len(value) < 16:
            raise ValueError("secret_key must be at least 16 characters")
        return value

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if isinstance(value, str):
            return [part.strip() for part in value.split(",") if part.strip()]
        return value

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def sqlalchemy_echo(self) -> bool:
        return self.debug and not self.is_production


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
# history-note: evolutionary edit 39
