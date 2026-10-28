from functools import lru_cache

from supabase import Client, create_client

from app.config import get_settings


@lru_cache
def get_anon_client() -> Client:
    """Singleton client authenticated with the anon key.

    Used for auth operations only (verifying a user's JWT via
    `client.auth.get_user(token)`). Does not bypass RLS.
    """
    settings = get_settings()
    return create_client(str(settings.supabase_url), settings.supabase_anon_key)


@lru_cache
def get_service_role_client() -> Client:
    """Singleton client authenticated with the service_role key.

    Bypasses Row Level Security entirely — use only for trusted,
    backend-internal operations (e.g. ingestion writes to
    source_documents/document_chunks), never for user-facing requests.
    """
    settings = get_settings()
    return create_client(
        str(settings.supabase_url), settings.supabase_service_role_key
    )