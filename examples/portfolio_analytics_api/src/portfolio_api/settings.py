"""Pydantic-settings configuration. Mirrors notebook 4.3."""
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="PORTFOLIO_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Portfolio Analytics API"
    environment: Literal["dev", "staging", "prod"] = "dev"
    log_level: Literal["debug", "info", "warning", "error"] = "info"

    repo_backend: Literal["memory", "sqlite"] = "memory"
    sqlite_path: str = ":memory:"

    jwt_secret: str = Field(
        default="dev-only-secret-change-me",
        description="HS256 signing key. MUST be overridden in non-dev environments.",
    )
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "portfolio-api"
    jwt_audience: str = "portfolio-api"
    access_token_ttl_seconds: int = 3600

    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    rate_limit_per_minute: int = 120

    enable_otel: bool = True


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """The single source of truth for runtime configuration.

    `lru_cache` so deps that pull settings don't re-parse env on every request.
    Tests override by clearing the cache or overriding the dep directly.
    """
    return Settings()
