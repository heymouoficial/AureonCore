"""
📥 Aureon Cortex - Knowledge Ingestion Service
Uploads files to Supabase Storage and creates vectorized chunks.
"""
from __future__ import annotations

from typing import List, Dict
import io
import uuid

from core.config import settings
from core.supabase import get_supabase_admin
from services.embeddings import generate_embedding


def _chunk_text(text: str, chunk_size: int = 900, overlap: int = 120) -> List[str]:
    text = text.strip()
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlap
        if start < 0:
            start = 0
        if start >= len(text):
            break
    return chunks


def _extract_text_from_pdf(file_bytes: bytes) -> str:
    try:
        from pypdf import PdfReader
    except Exception:
        return ""
    reader = PdfReader(io.BytesIO(file_bytes))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages)


def _extract_text_from_docx(file_bytes: bytes) -> str:
    try:
        import docx
    except Exception:
        return ""
    document = docx.Document(io.BytesIO(file_bytes))
    return "\n".join(p.text for p in document.paragraphs)


def _extract_text(file_bytes: bytes, content_type: str, filename: str) -> str:
    content_type = (content_type or "").lower()
    if content_type == "application/pdf" or filename.lower().endswith(".pdf"):
        return _extract_text_from_pdf(file_bytes)
    if content_type in ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword") or filename.lower().endswith(".docx"):
        return _extract_text_from_docx(file_bytes)
    # Plain text fallback
    try:
        return file_bytes.decode("utf-8")
    except Exception:
        return ""


class IngestionService:
    async def ingest_upload(self, tenant_id: str, user_id: str, filename: str, content_type: str, file_bytes: bytes) -> Dict:
        admin = get_supabase_admin()
        storage = admin.storage.from_(settings.supabase_storage_bucket)

        file_id = str(uuid.uuid4())
        storage_path = f"{tenant_id}/{file_id}-{filename}"

        storage.upload(
            storage_path,
            file_bytes,
            file_options={"content-type": content_type or "application/octet-stream"},
        )

        text = _extract_text(file_bytes, content_type, filename)
        chunks = _chunk_text(text)

        source_payload = {
            "tenant_id": tenant_id,
            "title": filename,
            "source_type": "pdf" if filename.lower().endswith(".pdf") else "text",
            "source_url": storage_path,
            "summary": (text[:280] + "...") if len(text) > 280 else text,
        }
        source_insert = admin.table("knowledge_sources").insert(source_payload).execute()
        source = source_insert.data[0]

        chunk_rows = []
        for idx, chunk in enumerate(chunks):
            embedding = await generate_embedding(chunk)
            chunk_rows.append({
                "tenant_id": tenant_id,
                "source_id": source["id"],
                "chunk_index": idx,
                "chunk_text": chunk,
                "embedding": embedding,
            })

        if chunk_rows:
            admin.table("knowledge_chunks").insert(chunk_rows).execute()

        return {
            "source": source,
            "chunk_count": len(chunk_rows),
        }


ingestion_service = IngestionService()
