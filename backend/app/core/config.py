"""Application settings loaded from environment / repo-root .env (pydantic-settings)."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# .env lives at the repository root (transitops/.env), regardless of the CWD the
# process is launched from (Makefile targets `cd backend` first).
_REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Environment-driven configuration; every key mirrors `.env.example`."""

    DATABASE_URL: str
    DATABASE_URL_TEST: str = ""

    JWT_SECRET: str
    JWT_ACCESS_TTL_MIN: int = 30
    JWT_REFRESH_TTL_DAYS: int = 7

    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    CORS_ORIGINS: str = "http://localhost:5173"
    VITE_API_BASE_URL: str = "http://localhost:8000/api/v1"

    model_config = SettingsConfigDict(
        env_file=str(_REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """CORS_ORIGINS is a comma-separated allowlist → list of origins."""
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def ai_configured(self) -> bool:
        """True only when an OpenRouter key is present (drives AI_DISABLED)."""
        return bool(self.OPENROUTER_API_KEY.strip())


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
