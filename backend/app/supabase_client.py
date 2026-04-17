"""
OVO Backend — Supabase Client
──────────────────────────────
Initializes a singleton Supabase client using the service role key.
The service role key bypasses RLS — needed for server-side inserts.

The client is lazily initialized so the server can start even if
Supabase credentials are not yet configured (returns None).
"""

import logging
from typing import Optional

from supabase import create_client, Client
from app.config import get_settings

logger = logging.getLogger("ovo")

# ─── Module-level singleton (lazily set) ───
_client: Optional[Client] = None
_initialized: bool = False


def get_supabase() -> Optional[Client]:
    """
    Returns the Supabase client singleton.
    Lazily initializes on first call.
    Returns None if credentials are invalid (server still starts).
    Will retry initialization if a previous attempt failed.
    """
    global _client, _initialized

    # If already successfully initialized, return the client
    if _initialized and _client is not None:
        return _client

    _initialized = True

    try:
        settings = get_settings()
        _client = create_client(
            supabase_url=settings.supabase_url,
            supabase_key=settings.supabase_service_role_key,
        )
        logger.info("✓ Supabase client initialized successfully")
    except Exception as e:
        logger.warning(f"⚠ Supabase client failed to initialize: {e}")
        logger.warning("  → Server will start, but DB operations will fail.")
        logger.warning("  → Update backend/.env with valid Supabase credentials.")
        _client = None
        _initialized = False  # Allow retry on next call

    return _client
