"""
🧠 Aureon Cortex - Memory Service (Supabase)
Manages conversation context, summarization, and vectorized memories.
"""
from __future__ import annotations

from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from core.supabase import get_supabase_admin
from services.embeddings import generate_embedding
from services.intelligence import intelligence_pool

# Context window settings
MAX_CONTEXT_MESSAGES = 20
SUMMARIZE_AFTER_MESSAGES = 30


@dataclass
class ContextMessage:
    id: str
    user_id: str
    channel: str
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict = field(default_factory=dict)


@dataclass
class Memory:
    id: str
    user_id: str
    content: str
    summary: str
    embedding: Optional[List[float]] = None
    source_channel: Optional[str] = None
    message_count: int = 0
    time_start: Optional[datetime] = None
    time_end: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    importance: float = 0.5
    created_at: datetime = field(default_factory=datetime.utcnow)


class MemoryService:
    """Supabase-backed memory vault with summarization and RAG search."""

    async def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        admin = get_supabase_admin()
        res = admin.table("conversations").select("*").eq("id", conversation_id).limit(1).execute()
        return res.data[0] if res and res.data else None

    async def get_or_create_conversation(
        self,
        tenant_id: str,
        user_id: str,
        channel: str,
        channel_user_id: str,
    ) -> Dict:
        admin = get_supabase_admin()
        existing = admin.table("conversations").select("*") \
            .eq("tenant_id", tenant_id) \
            .eq("channel", channel) \
            .eq("channel_user_id", channel_user_id) \
            .limit(1).execute()
        if existing and existing.data:
            return existing.data[0]

        created = admin.table("conversations").insert({
            "tenant_id": tenant_id,
            "channel": channel,
            "channel_user_id": channel_user_id,
            "user_id": user_id,
            "status": "active",
        }).execute()
        return created.data[0]

    async def add_message(
        self,
        conversation_id: str,
        user_id: str,
        channel: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None,
    ) -> ContextMessage:
        admin = get_supabase_admin()
        payload = {
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "metadata": metadata or {},
        }
        admin.table("messages").insert(payload).execute()
        return ContextMessage(
            id=conversation_id,
            user_id=user_id,
            channel=channel,
            role=role,
            content=content,
            metadata=metadata or {},
        )

    async def get_context(self, user_id: str, limit: int = MAX_CONTEXT_MESSAGES) -> List[ContextMessage]:
        admin = get_supabase_admin()
        convs = admin.table("conversations").select("id,channel").eq("user_id", user_id).execute()
        conversation_ids = [c["id"] for c in (convs.data or [])]
        if not conversation_ids:
            return []

        messages = admin.table("messages") \
            .select("id,content,role,created_at,conversation_id,metadata") \
            .in_("conversation_id", conversation_ids) \
            .order("created_at", desc=True) \
            .limit(limit).execute()

        results = []
        for msg in (messages.data or [])[::-1]:
            channel = next((c["channel"] for c in (convs.data or []) if c["id"] == msg["conversation_id"]), "pwa")
            results.append(ContextMessage(
                id=msg["id"],
                user_id=user_id,
                channel=channel,
                role=msg["role"],
                content=msg["content"],
                timestamp=datetime.fromisoformat(msg["created_at"].replace("Z", "+00:00")) if msg.get("created_at") else datetime.utcnow(),
                metadata=msg.get("metadata") or {},
            ))
        return results

    async def get_context_text(self, user_id: str, limit: int = 10) -> str:
        messages = await self.get_context(user_id, limit)
        if not messages:
            return ""
        lines = []
        for msg in messages:
            role = "Tú" if msg.role == "assistant" else "Usuario"
            lines.append(f"[{role}]: {msg.content}")
        return "\n".join(lines)

    async def summarize_and_archive(self, user_id: str, force: bool = False) -> Optional[Memory]:
        admin = get_supabase_admin()
        convs = admin.table("conversations").select("id,channel").eq("user_id", user_id).execute()
        conversation_ids = [c["id"] for c in (convs.data or [])]
        if not conversation_ids:
            return None

        messages = admin.table("messages") \
            .select("content,role,created_at,conversation_id") \
            .in_("conversation_id", conversation_ids) \
            .order("created_at", desc=False).execute()

        if not messages.data:
            return None

        if len(messages.data) < SUMMARIZE_AFTER_MESSAGES and not force:
            return None

        lines = []
        channels = set()
        for msg in messages.data:
            role = "Aureon" if msg["role"] == "assistant" else "Usuario"
            lines.append(f"[{role}]: {msg['content']}")
            channel = next((c["channel"] for c in (convs.data or []) if c["id"] == msg["conversation_id"]), "pwa")
            channels.add(channel)

        content = "\n".join(lines)
        summary = await self._generate_summary(content)
        embedding = await generate_embedding(summary)

        memory_payload = {
            "user_id": user_id,
            "content": content,
            "summary": summary,
            "embedding": embedding,
            "source_channel": list(channels)[0] if len(channels) == 1 else "mixed",
            "message_count": len(messages.data),
            "time_start": messages.data[0]["created_at"],
            "time_end": messages.data[-1]["created_at"],
        }
        inserted = admin.table("memory_vault").insert(memory_payload).execute()
        if not inserted or not inserted.data:
            return None

        record = inserted.data[0]
        return Memory(
            id=record["id"],
            user_id=record["user_id"],
            content=record["content"],
            summary=record.get("summary") or "",
            embedding=record.get("embedding"),
            source_channel=record.get("source_channel"),
            message_count=record.get("message_count", 0),
            time_start=None,
            time_end=None,
        )

    async def _generate_summary(self, content: str) -> str:
        system_prompt = (
            "Eres un asistente especializado en resumir conversaciones. "
            "Crea un resumen conciso (2-3 oraciones) que capture temas y decisiones."
        )
        try:
            summary = await intelligence_pool.complete(
                prompt=f"Resume esta conversación:\n\n{content}",
                system_prompt=system_prompt,
                max_tokens=200,
                temperature=0.3,
            )
            return summary
        except Exception:
            lines = content.split("\n")
            return f"Conversación de {len(lines)} mensajes"

    async def search_memories(self, user_id: str, query: str, k: int = 5) -> List[Tuple[Memory, float]]:
        admin = get_supabase_admin()
        query_embedding = await generate_embedding(query)
        try:
            results = admin.rpc("search_memories", {
                "p_user_id": user_id,
                "p_query_embedding": query_embedding,
                "p_limit": k,
            }).execute()
        except Exception:
            return []

        memories: List[Tuple[Memory, float]] = []
        for row in (results.data or []):
            memories.append((
                Memory(
                    id=row["id"],
                    user_id=user_id,
                    content=row.get("content", ""),
                    summary=row.get("summary", ""),
                    created_at=row.get("created_at"),
                ),
                row.get("similarity", 0.0)
            ))
        return memories

    async def get_relevant_context(self, user_id: str, query: str, k: int = 3) -> str:
        memories = await self.search_memories(user_id, query, k)
        if not memories:
            return ""
        lines = ["[Memorias relevantes:]"]
        for memory, score in memories:
            if score > 0.3:
                lines.append(f"- {memory.summary}")
        return "\n".join(lines) if len(lines) > 1 else ""

    async def get_user_stats(self, user_id: str) -> Dict:
        admin = get_supabase_admin()
        convs = admin.table("conversations").select("id").eq("user_id", user_id).execute()
        conversation_ids = [c["id"] for c in (convs.data or [])]
        msg_count = 0
        if conversation_ids:
            msgs = admin.table("messages").select("id", count="exact") \
                .in_("conversation_id", conversation_ids).execute()
            msg_count = msgs.count or 0
        memories = admin.table("memory_vault").select("id", count="exact") \
            .eq("user_id", user_id).execute()

        return {
            "active_context_messages": msg_count,
            "archived_memories": memories.count or 0,
            "total_messages": msg_count,
        }

    async def clear_context(self, user_id: str) -> None:
        admin = get_supabase_admin()
        convs = admin.table("conversations").select("id").eq("user_id", user_id).execute()
        conversation_ids = [c["id"] for c in (convs.data or [])]
        if conversation_ids:
            admin.table("messages").delete().in_("conversation_id", conversation_ids).execute()


memory_service = MemoryService()
