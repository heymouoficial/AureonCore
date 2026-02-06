"""
🧩 Supabase Client Factory
Admin + user-scoped clients with caching.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Optional

from supabase import Client, create_client

from core.config import settings


@lru_cache()
def get_supabase_admin() -> Client:
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise RuntimeError("Supabase admin credentials not configured")
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


@lru_cache()
def get_supabase_anon() -> Client:
    if not settings.supabase_url or not settings.supabase_anon_key:
        raise RuntimeError("Supabase anon credentials not configured")
    return create_client(settings.supabase_url, settings.supabase_anon_key)


def get_supabase_user(access_token: str) -> Client:
    """Return a user-scoped client with RLS enforced."""
    client = get_supabase_anon()
    # Try available auth hooks across supabase-py versions
    try:
        client.postgrest.auth(access_token)
    except Exception:
        try:
            client.auth.set_session(access_token, "")
        except Exception:
            pass
    return client
