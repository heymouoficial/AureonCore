"""
💬 Aureon Cortex - Telegram Channel Service
Envío y recepción de mensajes via Telegram Bot API.
Python 3.9 compatible.
"""
from typing import Optional, Dict, List, Union
import httpx
from core.config import settings


class TelegramService:
    """Servicio para Telegram Bot API."""
    
    BASE_URL = "https://api.telegram.org"
    
    def __init__(self):
        self.token = settings.telegram_bot_token
        self.allowed_ids = settings.telegram_allowed_ids
    
    @property
    def api_url(self) -> str:
        return f"{self.BASE_URL}/bot{self.token}"
    
    def is_allowed(self, user_id: int) -> bool:
        """Verifica si el usuario está en la whitelist."""
        return user_id in self.allowed_ids or not self.allowed_ids
    
    async def send_message(self, chat_id: Union[int, str], message: str, parse_mode: str = "HTML") -> Dict:
        """Envía un mensaje a un chat de Telegram."""
        if not self.token:
            return {"error": "Telegram not configured"}
        
        url = f"{self.api_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message[:4096],  # Telegram limit
            "parse_mode": parse_mode
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=30)
                return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def set_webhook(self, webhook_url: str) -> Dict:
        """Configura el webhook de Telegram."""
        if not self.token:
            return {"error": "Telegram not configured"}
        
        url = f"{self.api_url}/setWebhook"
        payload = {"url": webhook_url}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=30)
                return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def parse_incoming(self, data: Dict) -> Optional[Dict]:
        """Extrae información del update entrante."""
        try:
            message = data.get("message", {})
            if not message:
                return None
            
            return {
                "chat_id": message.get("chat", {}).get("id"),
                "user_id": message.get("from", {}).get("id"),
                "username": message.get("from", {}).get("username", ""),
                "text": message.get("text", ""),
                "msg_id": message.get("message_id")
            }
        except Exception:
            return None


# Singleton
telegram_service = TelegramService()
