"""
📱 Aureon Cortex - WhatsApp Channel Service
Envío y recepción de mensajes via WhatsApp Cloud API.
Python 3.9 compatible.
"""
from typing import Optional, Dict, List
import httpx
from core.config import settings


class WhatsAppService:
    """Servicio para WhatsApp Cloud API."""
    
    BASE_URL = "https://graph.facebook.com/v18.0"
    
    def __init__(self):
        self.phone_id = settings.whatsapp_phone_id
        self.token = settings.whatsapp_api_token
        self.verify_token = settings.whatsapp_verify_token
        self.allowed_phones = settings.whatsapp_allowed_phones
    
    def is_allowed(self, phone: str) -> bool:
        """Verifica si el número está en la whitelist."""
        # Normalize phone (remove +)
        phone_clean = phone.replace("+", "")
        allowed_clean = [p.replace("+", "") for p in self.allowed_phones]
        return phone_clean in allowed_clean or not self.allowed_phones
    
    async def send_message(self, to: str, message: str) -> Dict:
        """Envía un mensaje de texto a un número de WhatsApp."""
        if not self.phone_id or not self.token:
            return {"error": "WhatsApp not configured"}
        
        url = f"{self.BASE_URL}/{self.phone_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to.replace("+", ""),
            "type": "text",
            "text": {"body": message[:4096]}  # WhatsApp limit
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers, timeout=30)
                return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def parse_incoming(self, data: Dict) -> Optional[Dict]:
        """Extrae información del webhook entrante."""
        try:
            entry = data.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})
            messages = value.get("messages", [])
            
            if not messages:
                return None
            
            msg = messages[0]
            return {
                "from": msg.get("from", ""),
                "text": msg.get("text", {}).get("body", ""),
                "msg_id": msg.get("id", ""),
                "timestamp": msg.get("timestamp", "")
            }
        except Exception:
            return None


# Singleton
whatsapp_service = WhatsAppService()
