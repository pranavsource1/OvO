"""
OVO Backend — Configuration
───────────────────────────
Loads environment variables from .env into a typed Settings object.
Uses pydantic-settings for validation and auto-coercion.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    All environment variables required by the OVO backend.
    Values are read from a .env file in the backend/ directory.
    """

    # ─── Supabase ───
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str

    # ─── Groq (LLM Inference) ───
    groq_api_key: str

    # ─── ListenBrainz ───
    listenbrainz_token: str | None = None

    # ─── Server ───
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = SettingsConfigDict(
        # Look for .env in the backend/ directory (one level up from app/)
        env_file=".env",
        env_file_encoding="utf-8",
        # Case-insensitive env var matching
        case_sensitive=False,
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Returns a cached Settings instance.
    The @lru_cache ensures we only parse .env once per process lifetime.
    """
    return Settings()
