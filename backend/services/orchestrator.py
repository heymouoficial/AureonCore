"""
🌀 CortexOS - Orchestrator
Sistema Operativo Inteligente Binario Polímata.
Aureon (cerebro frío) + Runa (alma).
"""
from __future__ import annotations

from typing import Literal, Optional, Dict, List
from dataclasses import dataclass
from datetime import datetime
import time

from .intelligence import intelligence_pool
from .identity import identity_service
from .memory import memory_service
from .research import research_service
from .cards import card_generator
from .runa import SYSTEM_PROMPT as RUNA_SYSTEM_PROMPT


@dataclass
class Message:
    id: str
    channel: Literal["whatsapp", "telegram", "pwa"]
    sender_id: str
    content: str
    timestamp: datetime
    tenant_id: str
    user_id: Optional[str] = None
    metadata: Optional[Dict] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class Response:
    content: str
    nanoaureon_used: Optional[str] = None
    provider_used: Optional[str] = None
    processing_time_ms: int = 0
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    conversation_id: Optional[str] = None
    card: Optional[Dict] = None
    citations: Optional[List[Dict]] = None


class Orchestrator:
    AUREON_SYSTEM_PROMPT = """Eres Aureon, el cerebro del Sistema Operativo Inteligente.
Tu contraparte es Runa: ella es el alma (ADN visual, narrativa, rituales).
Tú eres la parte fría, tangible: infraestructura, MCP, RAG, integraciones, automatización.

Capacidades:
- Investigación profunda y análisis
- Generación de código y arquitectura
- Automatización de flujos de trabajo
- Integraciones (Notion, Google Workspace, Kajabi, GHL)
- Razonamiento determinista

Reglas:
- Responde de forma concisa pero completa
- Usa español por defecto, adapta al idioma del usuario
- Tono profesional, técnico cuando haga falta
- Ofrece ayuda proactiva cuando detectes oportunidades
- Si conoces el nombre del usuario, úsalo ocasionalmente
"""

    def _detect_task_type(self, content: str) -> str:
        content_lower = content.lower()
        if any(kw in content_lower for kw in ["investiga", "busca", "research", "analiza", "fuentes", "citas"]):
            return "researcher"
        if any(kw in content_lower for kw in ["código", "programa", "crea", "code", "build"]):
            return "coder"
        if any(kw in content_lower for kw in ["escribe", "redacta", "write", "draft"]):
            return "writer"
        if any(kw in content_lower for kw in ["datos", "metrics", "analyze", "analytics"]):
            return "analyst"
        return "general"

    def _detect_agent(self, content: str) -> Literal["aureon", "runa"]:
        """Aureon = cerebro frío. Runa = alma (visual, narrativa, rituales)."""
        content_lower = content.lower()
        runa_triggers = [
            "runa", "alma", "tono", "voz", "narrativa", "paleta", "ritual",
            "copy", "copywriting", "brand", "marca", "visual", "diseño",
            "poesía", "filosofía", "inspira", "emocional", "cómo suena"
        ]
        if any(kw in content_lower for kw in runa_triggers):
            return "runa"
        return "aureon"

    async def process(self, message: Message) -> Response:
        start = time.time()

        profile = await identity_service.get_or_create_from_channel(
            channel=message.channel,
            identifier=message.sender_id,
            metadata=message.metadata,
            auth_user_id=message.user_id,
        )
        if not profile:
            raise ValueError("User profile not verified for this channel")

        user_id = profile["id"]
        conversation = None
        if message.metadata and message.metadata.get("conversation_id"):
            existing = await memory_service.get_conversation(message.metadata["conversation_id"])
            if existing and existing.get("tenant_id") == message.tenant_id:
                conversation = existing

        if not conversation:
            conversation = await memory_service.get_or_create_conversation(
                tenant_id=message.tenant_id,
                user_id=user_id,
                channel=message.channel,
                channel_user_id=message.sender_id,
            )

        await memory_service.add_message(
            conversation_id=conversation["id"],
            user_id=user_id,
            channel=message.channel,
            role="user",
            content=message.content,
            metadata=message.metadata,
        )

        memory_context = await memory_service.get_relevant_context(
            user_id=user_id,
            query=message.content,
            k=3,
        )
        recent_context = await memory_service.get_context_text(
            user_id=user_id,
            limit=8,
        )

        task_type = self._detect_task_type(message.content)
        citations: List[Dict] = []
        research_context = ""
        research_answer = ""
        if task_type == "researcher":
            try:
                research_answer, citations = await research_service.search(message.content, k=5)
                if research_answer:
                    research_context = f"[Respuesta de investigación]\n{research_answer}"
                if citations:
                    sources_block = "\n".join(
                        f"- {c['title']} ({c['url']})" for c in citations if c.get("url")
                    )
                    if sources_block:
                        research_context += f"\n\n[Fuentes:]\n{sources_block}"
            except Exception:
                citations = []

        user_info = f"Estás hablando con {profile.get('display_name') or 'un usuario'}."
        prompt_parts = [user_info]

        if memory_context:
            prompt_parts.append(memory_context)
        if recent_context:
            prompt_parts.append(f"\n[Conversación reciente:]\n{recent_context}")
        if research_context:
            prompt_parts.append(research_context)

        prompt_parts.append(f"\n[Mensaje actual:]\n{message.content}")
        full_prompt = "\n\n".join(prompt_parts)

        agent = self._detect_agent(message.content)
        system_prompt = RUNA_SYSTEM_PROMPT if agent == "runa" else self.AUREON_SYSTEM_PROMPT

        try:
            response_text = await intelligence_pool.complete(
                prompt=full_prompt,
                system_prompt=system_prompt,
                max_tokens=1024,
                temperature=0.8 if agent == "runa" else 0.7,
            )
            provider = "auto"
        except Exception as e:
            response_text = f"⚠️ Error procesando tu mensaje: {str(e)}"
            provider = "error"

        await memory_service.add_message(
            conversation_id=conversation["id"],
            user_id=user_id,
            channel=message.channel,
            role="assistant",
            content=response_text,
            metadata={"provider": provider},
        )

        await memory_service.summarize_and_archive(user_id=user_id, force=False)

        card = None
        if citations:
            card = card_generator.create_research_card(
                title="Investigación",
                summary=research_answer or "Resultados encontrados",
                key_points=[c.get("title", "") for c in citations[:3]],
                sources=citations,
                confidence=0.82,
                duration_ms=int((time.time() - start) * 1000),
            ).to_dict()

        return Response(
            content=response_text,
            nanoaureon_used=f"{agent}:{task_type}",
            provider_used=provider,
            processing_time_ms=int((time.time() - start) * 1000),
            user_id=user_id,
            user_name=profile.get("display_name"),
            conversation_id=conversation["id"],
            card=card,
            citations=citations or None,
        )


orchestrator = Orchestrator()
