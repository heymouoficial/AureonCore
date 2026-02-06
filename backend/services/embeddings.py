"""
🧬 Embedding Generator with multi-provider fallback.
"""
from __future__ import annotations

from typing import List
import hashlib

from core.config import settings


def _hash_embedding(text: str, dims: int = 1536) -> List[float]:
    hash_bytes = hashlib.sha256(text.encode()).digest()
    embedding = []
    for i in range(dims):
        byte_idx = i % len(hash_bytes)
        embedding.append((hash_bytes[byte_idx] - 128) / 128.0)
    return embedding


def _normalize_embedding(embedding: List[float], dims: int = 1536) -> List[float]:
    if len(embedding) >= dims:
        return embedding[:dims]
    return embedding + [0.0] * (dims - len(embedding))


async def generate_embedding(text: str, dims: int = 1536) -> List[float]:
    text = text.strip()
    if not text:
        return [0.0] * dims

    try:
        if settings.gemini_api_key:
            import google.generativeai as genai
            genai.configure(api_key=settings.gemini_api_key)
            result = genai.embed_content(
                model="models/embedding-001",
                content=text[:8000],
                task_type="retrieval_document"
            )
            embedding = result.get("embedding") if isinstance(result, dict) else result
            return _normalize_embedding(embedding, dims)
    except Exception:
        pass

    return _hash_embedding(text, dims)
