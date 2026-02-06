"""
📝 Aureon Cortex - Summarizer Service
Background service for conversation summarization and vectorization.
Python 3.9 compatible.
"""
from typing import Optional, List
from datetime import datetime, timedelta
import asyncio

from .memory import memory_service, Memory
from .intelligence import intelligence_pool
from .embeddings import generate_embedding
from core.config import settings


class SummarizerService:
    """
    Background service that periodically summarizes and vectorizes conversations.
    
    Responsibilities:
    - Summarize old context windows
    - Generate embeddings for new memories
    - Clean up expired data
    """
    
    def __init__(self):
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(self, interval_hours: int = 24):
        """Start the background summarization job."""
        if self.is_running:
            return
        
        self.is_running = True
        self._task = asyncio.create_task(self._run_loop(interval_hours))
    
    async def stop(self):
        """Stop the background job."""
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
    
    async def _run_loop(self, interval_hours: int):
        """Main loop for periodic summarization."""
        while self.is_running:
            try:
                await self.run_summarization()
            except Exception as e:
                print(f"[Summarizer] Error: {e}")
            
            # Wait for next cycle
            await asyncio.sleep(interval_hours * 3600)
    
    async def run_summarization(self):
        """Run summarization for all users with pending context."""
        print("[Summarizer] Starting summarization cycle...")
        
        # In production, query Supabase for users with large context windows
        # For now, use in-memory data
        from .memory import _context_db
        
        summarized = 0
        for user_id in list(_context_db.keys()):
            memory = await memory_service.summarize_and_archive(user_id, force=False)
            if memory:
                summarized += 1
        
        print(f"[Summarizer] Completed. Summarized {summarized} context windows.")
    
    async def generate_smart_summary(self, content: str) -> str:
        """
        Generate an AI-powered summary of conversation content.
        Uses the intelligence pool for generation.
        """
        system_prompt = """Eres un asistente especializado en resumir conversaciones.
Tu tarea es crear un resumen conciso pero informativo.
El resumen debe:
- Capturar los temas principales discutidos
- Resaltar cualquier decisión o acción tomada
- Ser útil para recordar el contexto en futuras conversaciones
- Ser de máximo 2-3 oraciones."""

        try:
            summary = await intelligence_pool.complete(
                prompt=f"Resume esta conversación:\n\n{content}",
                system_prompt=system_prompt,
                max_tokens=200,
                temperature=0.3
            )
            return summary
        except Exception as e:
            # Fallback to simple summary
            lines = content.split("\n")
            return f"Conversación de {len(lines)} mensajes"
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text.
        Uses Gemini embeddings o hash fallback.
        """
        try:
            # Gemini embeddings
            import google.generativeai as genai
            
            if settings.gemini_api_key:
                genai.configure(api_key=settings.gemini_api_key)
                result = genai.embed_content(
                    model="models/embedding-001",
                    content=text[:8000],
                    task_type="retrieval_document"
                )
                # Pad to 1536 dimensions if needed
                embedding = result['embedding']
                if len(embedding) < 1536:
                    embedding.extend([0.0] * (1536 - len(embedding)))
                return embedding[:1536]
        except Exception as e:
            print(f"[Summarizer] Gemini embedding failed: {e}")
        
        # Fallback: embeddings module (Gemini o hash)
        return await generate_embedding(text)
    
    async def reprocess_memory(self, memory: Memory) -> Memory:
        """Reprocess a memory with better summary and embedding."""
        # Generate new summary
        memory.summary = await self.generate_smart_summary(memory.content)
        
        # Generate new embedding
        memory.embedding = await self.generate_embedding(memory.summary)
        
        return memory


# Singleton
summarizer_service = SummarizerService()
