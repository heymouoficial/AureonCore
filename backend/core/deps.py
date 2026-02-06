"""
🔐 FastAPI Dependencies for Auth + Tenant Context
Acceso por invitación (excepto founder).
"""
from __future__ import annotations

from typing import Dict, Optional

from fastapi import Header, HTTPException, Request, Depends

from core.config import settings
from core.supabase import get_supabase_admin
from services.identity import identity_service


def _extract_token(authorization: Optional[str]) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    return authorization.split(" ", 1)[1].strip()


async def get_current_user(
    request: Request,
    authorization: Optional[str] = Header(None),
) -> Dict:
    if hasattr(request.state, "current_user"):
        return request.state.current_user

    token = _extract_token(authorization)
    admin = get_supabase_admin()
    try:
        user_resp = admin.auth.get_user(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_obj = getattr(user_resp, "user", None) or getattr(user_resp, "data", None) or user_resp
    user = getattr(user_obj, "user", None) or user_obj

    user_id = getattr(user, "id", None) or user.get("id") if isinstance(user, dict) else None
    email = getattr(user, "email", None) or user.get("email") if isinstance(user, dict) else None

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    current_user = {
        "id": user_id,
        "email": email,
        "access_token": token,
    }

    # Invite-only: bypass si es founder o email en allowlist
    is_founder = settings.founder_user_id and str(user_id) == str(settings.founder_user_id)
    is_allowed = settings.allowed_emails and email and email.lower() in [e.lower() for e in settings.allowed_emails]
    if settings.founder_user_id or settings.allowed_emails:
        if not is_founder and not is_allowed:
            raise HTTPException(
                status_code=403,
                detail="Acceso por invitación. Contacta al equipo para solicitar acceso."
            )

    # Ensure profile exists for auth user
    await identity_service.ensure_profile_from_auth(current_user)

    request.state.current_user = current_user
    return current_user


async def get_current_tenant(
    request: Request,
    current_user: Dict = Depends(get_current_user),
) -> Dict:
    if hasattr(request.state, "current_tenant"):
        return request.state.current_tenant

    admin = get_supabase_admin()
    user_id = current_user["id"]

    try:
        existing = admin.table("tenant_users").select("tenant_id,role").eq("user_id", user_id).limit(1).execute()
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Tenant lookup failed") from exc

    if existing and getattr(existing, "data", None):
        tenant_id = existing.data[0]["tenant_id"]
        role = existing.data[0].get("role", "owner")
        tenant_resp = admin.table("tenants").select("id,name,owner_user_id").eq("id", tenant_id).limit(1).execute()
        tenant = tenant_resp.data[0] if tenant_resp and tenant_resp.data else {"id": tenant_id, "name": "Tenant"}
    else:
        tenant_name = (current_user.get("email") or "Aureon").split("@")[0]
        tenant_insert = admin.table("tenants").insert({
            "name": tenant_name,
            "owner_user_id": user_id,
        }).execute()
        tenant = tenant_insert.data[0]
        tenant_id = tenant["id"]
        role = "owner"
        admin.table("tenant_users").insert({
            "tenant_id": tenant_id,
            "user_id": user_id,
            "role": role,
        }).execute()

    current_tenant = {
        "id": tenant_id,
        "name": tenant.get("name"),
        "role": role,
    }

    request.state.current_tenant = current_tenant
    return current_tenant
