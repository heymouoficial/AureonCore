-- ==========================================================================
-- Knowledge Chunks (Vectorized)
-- ==========================================================================

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    source_id UUID NOT NULL REFERENCES knowledge_sources(id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding VECTOR(1536),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_tenant ON knowledge_chunks(tenant_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_source ON knowledge_chunks(source_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_embedding ON knowledge_chunks
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

ALTER TABLE knowledge_chunks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "knowledge_chunks_tenant_isolation" ON knowledge_chunks
    FOR ALL
    USING (
        tenant_id IN (
            SELECT tenant_id FROM tenant_users WHERE user_id = auth.uid()
        )
    );

-- Search function
CREATE OR REPLACE FUNCTION search_knowledge_chunks(
    p_tenant_id UUID,
    p_query_embedding VECTOR(1536),
    p_limit INT DEFAULT 5
)
RETURNS TABLE (
    id UUID,
    source_id UUID,
    chunk_text TEXT,
    similarity REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        kc.id,
        kc.source_id,
        kc.chunk_text,
        1 - (kc.embedding <=> p_query_embedding) AS similarity
    FROM knowledge_chunks kc
    WHERE kc.tenant_id = p_tenant_id
        AND kc.embedding IS NOT NULL
    ORDER BY kc.embedding <=> p_query_embedding
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
