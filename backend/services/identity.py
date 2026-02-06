"""
🔐 Aureon Cortex - Identity Service (Supabase)
Unified user identity management across channels.
"""
from __future__ import annotations

from typing import Optional, Dict
from dataclasses import dataclass
from datetime import datetime, timedelta
import uuid
import random
import string

from core.supabase import get_supabase_admin


@dataclass
class ChannelVerification:
    id: str
    user_id: str
    channel: str
    verification_code: str
    channel_identifier: Optional[str] = None
    expires_at: datetime = None
    verified_at: Optional[datetime] = None
    created_at: datetime = None


class IdentityService:
    """Manages unified identity across PWA, Telegram, and WhatsApp."""

    def _generate_code(self, length: int = 6) -> str:
        return ''.join(random.choices(string.digits, k=length))

    async def ensure_profile_from_auth(self, auth_user: Dict) -> Dict:
        """Ensure user_profiles row exists for auth user."""
        admin = get_supabase_admin()
        user_id = auth_user.get("id")
        email = auth_user.get("email")
        if not user_id:
            return {}

        existing = admin.table("user_profiles").select("id, email").eq("id", user_id).limit(1).execute()
        if existing and existing.data:
            return existing.data[0]

        profile = {
            "id": user_id,
            "auth_id": user_id,
            "email": email,
            "display_name": (email or "User").split("@")[0],
        }
        inserted = admin.table("user_profiles").insert(profile).execute()
        return inserted.data[0] if inserted and inserted.data else profile

    async def get_profile(self, user_id: str) -> Optional[Dict]:
        admin = get_supabase_admin()
        res = admin.table("user_profiles").select("*").eq("id", user_id).limit(1).execute()
        return res.data[0] if res and res.data else None

    async def get_by_email(self, email: str) -> Optional[Dict]:
        admin = get_supabase_admin()
        res = admin.table("user_profiles").select("*").eq("email", email).limit(1).execute()
        return res.data[0] if res and res.data else None

    async def get_by_telegram(self, telegram_id: int) -> Optional[Dict]:
        admin = get_supabase_admin()
        res = admin.table("user_profiles").select("*").eq("telegram_id", telegram_id).limit(1).execute()
        return res.data[0] if res and res.data else None

    async def get_by_whatsapp(self, phone: str) -> Optional[Dict]:
        phone_clean = phone.replace("+", "").replace(" ", "")
        admin = get_supabase_admin()
        res = admin.table("user_profiles").select("*").eq("whatsapp_phone", phone_clean).limit(1).execute()
        return res.data[0] if res and res.data else None

    async def get_or_create_from_channel(
        self,
        channel: str,
        identifier: str,
        metadata: Optional[Dict] = None,
        auth_user_id: Optional[str] = None,
    ) -> Optional[Dict]:
        metadata = metadata or {}

        if channel == "pwa":
            user_id = auth_user_id or identifier
            profile = await self.get_profile(user_id)
            if not profile:
                profile = await self.ensure_profile_from_auth({
                    "id": user_id,
                    "email": metadata.get("email"),
                })
            return profile

        if channel == "telegram":
            return await self.get_by_telegram(int(identifier))

        if channel == "whatsapp":
            return await self.get_by_whatsapp(identifier)

        return None

    async def create_verification(self, user_id: str, channel: str) -> ChannelVerification:
        admin = get_supabase_admin()
        code = self._generate_code()
        payload = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "channel": channel,
            "verification_code": code,
            "expires_at": (datetime.utcnow() + timedelta(minutes=15)).isoformat(),
        }
        admin.table("channel_verifications").insert(payload).execute()
        return ChannelVerification(
            id=payload["id"],
            user_id=user_id,
            channel=channel,
            verification_code=code,
            expires_at=datetime.utcnow() + timedelta(minutes=15),
            created_at=datetime.utcnow(),
        )

    async def verify_channel(self, code: str, channel: str, channel_identifier: str) -> Optional[Dict]:
        admin = get_supabase_admin()
        verification = admin.table("channel_verifications").select("*").eq("verification_code", code).eq("channel", channel).limit(1).execute()
        if not verification or not verification.data:
            return None

        record = verification.data[0]
        if record.get("verified_at"):
            return None

        # Update profile
        user_id = record["user_id"]
        updates = {}
        now_iso = datetime.utcnow().isoformat()
        if channel == "telegram":
            updates = {
                "telegram_id": int(channel_identifier),
                "telegram_verified_at": now_iso,
            }
        elif channel == "whatsapp":
            phone_clean = channel_identifier.replace("+", "").replace(" ", "")
            updates = {
                "whatsapp_phone": phone_clean,
                "whatsapp_verified_at": now_iso,
            }
        else:
            return None

        admin.table("user_profiles").update(updates).eq("id", user_id).execute()
        admin.table("channel_verifications").update({
            "verified_at": now_iso,
            "channel_identifier": channel_identifier,
        }).eq("id", record["id"]).execute()

        return await self.get_profile(user_id)


identity_service = IdentityService()
