"""
🧠 Aureon Cortex - Configuration Module
Carga todas las variables de entorno y provee settings tipados.
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
from typing import Literal
import json


class Settings(BaseSettings):
    """Configuración central de Aureon Cortex."""
    
    # --- Core ---
    app_env: Literal["development", "staging", "production"] = "development"
    port: int = 8000
    domain: str = "https://core.multiversa.group"
    
    # --- Invite-only (Founder bypass) ---
    founder_user_id: str = ""  # FOUNDER_USER_ID
    allowed_emails_raw: str = Field("[]", validation_alias="ALLOWED_EMAILS")
    
    @property
    def allowed_emails(self) -> list[str]:
        try:
            return json.loads(self.allowed_emails_raw or "[]")
        except Exception:
            return []
    
    # --- Supabase (optional for local dev) ---
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_anon_key: str = ""
    supabase_storage_bucket: str = "knowledge"
    
    # --- AI Providers (Pool Founder: GROQ + Gemini + Mistral) ---
    gemini_api_key: str = ""
    mistral_api_key: str = ""
    groq_api_key: str = ""
    deepseek_api_key: str = ""

    # --- Research ---
    tavily_api_key: str = ""
    
    # Gemini Key Pool (for rotation)
    gemini_pool_raw: str = Field("", alias="VITE_GEMINI_KEY_POOL")
    
    @property
    def gemini_key_pool(self) -> list[str]:
        if self.gemini_pool_raw:
            try:
                return json.loads(self.gemini_pool_raw)
            except:
                return [self.gemini_api_key] if self.gemini_api_key else []
        return [self.gemini_api_key] if self.gemini_api_key else []
    
    # --- Telegram ---
    telegram_bot_token: str = ""
    allowed_telegram_ids: str = "[]"  # JSON array string
    
    @property
    def telegram_allowed_ids(self) -> list[int]:
        try:
            return json.loads(self.allowed_telegram_ids)
        except:
            return []
    
    # --- WhatsApp ---
    whatsapp_phone_id: str = ""
    whatsapp_api_token: str = ""
    whatsapp_verify_token: str = ""
    allowed_phone_numbers: str = ""
    
    @property
    def whatsapp_allowed_phones(self) -> list[str]:
        return [p.strip() for p in self.allowed_phone_numbers.split(",") if p.strip()]
    
    # --- Notion ---
    notion_token: str = ""
    
    # --- n8n ---
    n8n_webhook_url: str = ""
    n8n_api_key: str = ""
    
    # --- MCP / Vector ---
    pinecone_api_key: str = ""
    github_token: str = ""
    context7_api_key: str = ""

    # --- Security ---
    integrations_enc_key: str = ""
    # CORS: lista separada por comas (ej: https://core.multiversa.group,https://*.vercel.app)
    # Vacío = permitir todos (dev)
    cors_origins_raw: str = Field("", validation_alias="CORS_ORIGINS")

    @property
    def cors_origins(self) -> list[str]:
        if not self.cors_origins_raw:
            return ["*"]
        return [o.strip() for o in self.cors_origins_raw.split(",") if o.strip()]

    # --- Upload Limits ---
    max_upload_mb: int = 25
    
    # --- Google Workspace ---
    google_client_id: str = ""
    google_client_secret: str = ""
    google_refresh_token: str = ""
    
    # --- Marketing ---
    kajabi_api_key: str = ""
    kajabi_api_secret: str = ""
    ghl_access_token: str = ""
    
    class Config:
        env_file = ("../../.env", "../.env", ".env")  # Project root, backend/, core/
        env_file_encoding = "utf-8"
        extra = "ignore"
        populate_by_name = True  # Allow alias for ALLOWED_EMAILS


@lru_cache()
def get_settings() -> Settings:
    """Singleton para acceder a la configuración."""
    return Settings()


# Alias para importación directa
settings = get_settings()
