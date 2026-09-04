"""Application settings, loaded from environment variables / .env file."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/ directory (two levels up from this file: app/core/config.py -> app -> backend)
BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Central configuration. Everything is overridable via environment variables."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- App ----
    app_name: str = "RadioAI"
    environment: str = "development"
    log_level: str = "INFO"
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"]
    )

    # ---- Security ----
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # ---- Demo account ----
    demo_username: str = "demo123"
    demo_password: str = "demo123"

    # ---- Database ----
    database_url: str = "sqlite+aiosqlite:///./data/app.db"

    # ---- Storage ----
    storage_backend: str = "local"  # local | supabase
    local_storage_dir: str = "./uploads"
    supabase_url: str = ""
    supabase_service_key: str = ""
    supabase_bucket: str = "xray-uploads"

    # ---- ML ----
    model_path: str = "./app/ml/artifacts/model.keras"
    enable_tta: bool = False
    ood_threshold: float = 0.45  # cosine similarity below this → out-of-distribution
    ood_reference_dir: str = "../examples"  # directory with known X-ray images

    # ---- Rate Limits ----
    rate_limit_prediction: str = "60/minute"
    rate_limit_report: str = "60/minute"

    # ---- Multi-LLM Report Generation ----
    gemini_api_key: str = ""
    opencode_api_key: str = ""
    opencode_base_url: str = "https://opencode.ai/zen/v1"
    default_llm_model: str = "gemini-3.8-flash"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        """Allow CORS_ORIGINS to be a comma-separated string in the .env file."""
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    def resolve_path(self, value: str) -> Path:
        """Resolve a possibly-relative path against the backend directory."""
        path = Path(value)
        return path if path.is_absolute() else (BACKEND_DIR / path).resolve()


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()


settings = get_settings()
