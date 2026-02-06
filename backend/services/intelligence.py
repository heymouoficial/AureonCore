"""
🧠 Aureon Cortex - Intelligence Pool
Selector dinámico de proveedores de IA con fallback y rotación.
Python 3.9 compatible.
"""
from enum import Enum
from typing import Optional, List
import random
import httpx
from core.config import settings


class AIProvider(Enum):
    """Proveedores de IA disponibles."""
    GEMINI = "gemini"
    MISTRAL = "mistral"
    GROQ = "groq"
    DEEPSEEK = "deepseek"


class IntelligencePool:
    """
    Pool de inteligencia que maneja múltiples proveedores de IA.
    Soporta rotación de keys y fallback automático.
    """
    
    def __init__(self):
        self._gemini_index = 0
        # Founder tier: GROQ + Gemini + Mistral (free combo)
        self._provider_order = [
            AIProvider.GROQ,      # Fastest, free tier
            AIProvider.GEMINI,    # Default, free tier
            AIProvider.MISTRAL,   # European, free tier
            AIProvider.DEEPSEEK,  # Cost-effective
        ]
    
    def _get_next_gemini_key(self) -> str:
        """Rotación round-robin de Gemini keys."""
        pool = settings.gemini_key_pool
        if not pool:
            return settings.gemini_api_key
        key = pool[self._gemini_index % len(pool)]
        self._gemini_index += 1
        return key
    
    def get_available_providers(self) -> List[AIProvider]:
        """Lista de proveedores con API key configurada."""
        available = []
        if settings.gemini_api_key:
            available.append(AIProvider.GEMINI)
        if settings.mistral_api_key:
            available.append(AIProvider.MISTRAL)
        if settings.groq_api_key:
            available.append(AIProvider.GROQ)
        if settings.deepseek_api_key:
            available.append(AIProvider.DEEPSEEK)
        return available
    
    async def complete(
        self,
        prompt: str,
        system_prompt: str = "Eres Auréon, un polímata digital.",
        provider: Optional[AIProvider] = None,
        model: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> str:
        """
        Genera una respuesta usando el provider especificado o el primero disponible.
        """
        if provider is None:
            # Use first available in priority order
            for p in self._provider_order:
                if p in self.get_available_providers():
                    provider = p
                    break
        
        if provider is None:
            raise ValueError("No AI providers configured")
        
        # Route to provider-specific implementation
        if provider == AIProvider.GEMINI:
            return await self._complete_gemini(prompt, system_prompt, model, max_tokens, temperature)
        elif provider == AIProvider.GROQ:
            return await self._complete_groq(prompt, system_prompt, model, max_tokens, temperature)
        elif provider == AIProvider.MISTRAL:
            return await self._complete_mistral(prompt, system_prompt, model, max_tokens, temperature)
        elif provider == AIProvider.DEEPSEEK:
            return await self._complete_deepseek(prompt, system_prompt, model, max_tokens, temperature)
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    async def _complete_gemini(
        self, prompt: str, system: str, model: Optional[str], max_tokens: int, temp: float
    ) -> str:
        """Google Gemini API."""
        import google.generativeai as genai
        
        api_key = self._get_next_gemini_key()
        genai.configure(api_key=api_key)
        
        model_name = model or "gemini-2.0-flash"
        model_instance = genai.GenerativeModel(
            model_name,
            system_instruction=system
        )
        
        response = model_instance.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temp
            )
        )
        return response.text
    
    async def _complete_groq(
        self, prompt: str, system: str, model: Optional[str], max_tokens: int, temp: float
    ) -> str:
        """Groq API (ultra-fast inference)."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.groq_api_key}"},
                json={
                    "model": model or "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": max_tokens,
                    "temperature": temp
                },
                timeout=60
            )
            data = response.json()
            return data["choices"][0]["message"]["content"]
    
    async def _complete_mistral(
        self, prompt: str, system: str, model: Optional[str], max_tokens: int, temp: float
    ) -> str:
        """Mistral API."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.mistral.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.mistral_api_key}"},
                json={
                    "model": model or "mistral-small-latest",
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": max_tokens,
                    "temperature": temp
                },
                timeout=60
            )
            data = response.json()
            return data["choices"][0]["message"]["content"]
    
    async def _complete_deepseek(
        self, prompt: str, system: str, model: Optional[str], max_tokens: int, temp: float
    ) -> str:
        """DeepSeek API (OpenAI-compatible)."""
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(
            api_key=settings.deepseek_api_key,
            base_url="https://api.deepseek.com"
        )
        response = await client.chat.completions.create(
            model=model or "deepseek-chat",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temp
        )
        return response.choices[0].message.content


# Singleton
intelligence_pool = IntelligencePool()
