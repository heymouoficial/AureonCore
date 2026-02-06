"""
🔎 Aureon Cortex - Research Service (Tavily)
Fetches sources with citations.
"""
from __future__ import annotations

from typing import List, Dict, Tuple

import httpx

from core.config import settings


class ResearchService:
    async def search(self, query: str, k: int = 5) -> Tuple[str, List[Dict]]:
        if not settings.tavily_api_key:
            raise ValueError("Tavily API key not configured")

        payload = {
            "api_key": settings.tavily_api_key,
            "query": query,
            "max_results": k,
            "include_answer": True,
            "include_raw_content": False,
            "search_depth": "basic",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post("https://api.tavily.com/search", json=payload)
            response.raise_for_status()
            data = response.json()

        answer = data.get("answer", "")
        citations: List[Dict] = []
        for item in data.get("results", [])[:k]:
            citations.append({
                "title": item.get("title"),
                "url": item.get("url"),
                "source": item.get("source") or "web",
                "snippet": (item.get("content") or "")[:240],
            })

        return answer, citations


research_service = ResearchService()
