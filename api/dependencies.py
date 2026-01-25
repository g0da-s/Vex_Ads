"""
FastAPI dependencies for dependency injection.
"""

from supabase import create_client, Client
from config import get_settings

settings = get_settings()

# Create a single Supabase client instance
_supabase_client: Client | None = None


def get_supabase() -> Client:
    """
    Get Supabase client instance.
    Creates client on first call, reuses for subsequent calls.
    """
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(
            settings.supabase_url,
            settings.supabase_key,
        )
    return _supabase_client
