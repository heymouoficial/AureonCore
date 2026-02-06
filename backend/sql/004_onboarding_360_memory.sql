-- ============================================================================
-- Aureon Portality - Phase 4: Onboarding 360 & Memory System
-- User profiles with channel linking and vectorized memory vault
-- ============================================================================

-- Enable pgvector extension for embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- USER PROFILES - Unified Identity
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    auth_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    
    -- Core Identity
    email TEXT UNIQUE,
    display_name TEXT,
    avatar_url TEXT,
    
    -- Channel Links
    telegram_id BIGINT UNIQUE,
    telegram_username TEXT,
    telegram_verified_at TIMESTAMPTZ,
    
    whatsapp_phone TEXT UNIQUE,
    whatsapp_verified_at TIMESTAMPTZ,
    
    -- Profile Settings
    preferences JSONB DEFAULT '{
        "language": "es",
        "timezone": "America/Caracas",
        "voice_mode": false,
        "notifications": true
    }'::jsonb,
    
    tier TEXT DEFAULT 'trial' CHECK (tier IN ('trial', 'nano', 'smart', 'cortex')),
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Index for channel lookups
CREATE INDEX IF NOT EXISTS idx_user_profiles_telegram ON user_profiles(telegram_id) WHERE telegram_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_user_profiles_whatsapp ON user_profiles(whatsapp_phone) WHERE whatsapp_phone IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_user_profiles_email ON user_profiles(email) WHERE email IS NOT NULL;

-- RLS: Users can only see their own profile
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "users_own_profile" ON user_profiles;
CREATE POLICY "users_own_profile" ON user_profiles
    FOR ALL USING (auth.uid() = auth_id);

-- Service role can do everything
DROP POLICY IF EXISTS "service_role_full_access" ON user_profiles;
CREATE POLICY "service_role_full_access" ON user_profiles
    FOR ALL TO service_role USING (true);

-- ============================================================================
-- CHANNEL VERIFICATIONS - Temporary linking codes
-- ============================================================================

CREATE TABLE IF NOT EXISTS channel_verifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
    
    channel TEXT NOT NULL CHECK (channel IN ('telegram', 'whatsapp')),
    verification_code TEXT NOT NULL,
    channel_identifier TEXT, -- telegram_id or phone number
    
    expires_at TIMESTAMPTZ NOT NULL DEFAULT (now() + INTERVAL '15 minutes'),
    verified_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Index for code lookups
CREATE INDEX IF NOT EXISTS idx_verifications_code ON channel_verifications(verification_code) 
    WHERE verified_at IS NULL;

-- RLS
ALTER TABLE channel_verifications ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "users_own_verifications" ON channel_verifications;
CREATE POLICY "users_own_verifications" ON channel_verifications
    FOR ALL USING (user_id IN (
        SELECT id FROM user_profiles WHERE auth_id = auth.uid()
    ));

DROP POLICY IF EXISTS "service_role_verifications" ON channel_verifications;
CREATE POLICY "service_role_verifications" ON channel_verifications
    FOR ALL TO service_role USING (true);

-- ============================================================================
-- MEMORY VAULT - Vectorized conversation memories
-- ============================================================================

CREATE TABLE IF NOT EXISTS memory_vault (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE NOT NULL,
    
    -- Memory Content
    content TEXT NOT NULL,
    summary TEXT,
    
    -- Vector Embedding (1536 dimensions for OpenAI, 768 for Gemini)
    embedding VECTOR(1536),
    
    -- Source Tracking
    source_channel TEXT CHECK (source_channel IN ('pwa', 'telegram', 'whatsapp')),
    source_conversation_id UUID,
    message_count INT DEFAULT 0,
    
    -- Time Range of included messages
    time_start TIMESTAMPTZ,
    time_end TIMESTAMPTZ,
    
    -- Metadata
    tags TEXT[] DEFAULT '{}',
    importance REAL DEFAULT 0.5, -- 0-1 scale
    
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Vector similarity search index (IVFFlat for performance)
CREATE INDEX IF NOT EXISTS idx_memory_embedding ON memory_vault 
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Index for user queries
CREATE INDEX IF NOT EXISTS idx_memory_user ON memory_vault(user_id);
CREATE INDEX IF NOT EXISTS idx_memory_created ON memory_vault(user_id, created_at DESC);

-- RLS: Strict user isolation
ALTER TABLE memory_vault ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "users_own_memories" ON memory_vault;
CREATE POLICY "users_own_memories" ON memory_vault
    FOR ALL USING (user_id IN (
        SELECT id FROM user_profiles WHERE auth_id = auth.uid()
    ));

DROP POLICY IF EXISTS "service_role_memories" ON memory_vault;
CREATE POLICY "service_role_memories" ON memory_vault
    FOR ALL TO service_role USING (true);

-- ============================================================================
-- UPDATE CONVERSATIONS TABLE - Add user_id link
-- ============================================================================

-- Add user_id column if not exists
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'conversations' AND column_name = 'user_id'
    ) THEN
        ALTER TABLE conversations ADD COLUMN user_id UUID REFERENCES user_profiles(id);
        CREATE INDEX idx_conversations_user ON conversations(user_id);
    END IF;
END $$;

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to search memories by similarity
CREATE OR REPLACE FUNCTION search_memories(
    p_user_id UUID,
    p_query_embedding VECTOR(1536),
    p_limit INT DEFAULT 5
)
RETURNS TABLE (
    id UUID,
    content TEXT,
    summary TEXT,
    similarity REAL,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        mv.id,
        mv.content,
        mv.summary,
        1 - (mv.embedding <=> p_query_embedding) AS similarity,
        mv.created_at
    FROM memory_vault mv
    WHERE mv.user_id = p_user_id
        AND mv.embedding IS NOT NULL
    ORDER BY mv.embedding <=> p_query_embedding
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get user by any channel identifier
CREATE OR REPLACE FUNCTION get_user_by_channel(
    p_channel TEXT,
    p_identifier TEXT
)
RETURNS UUID AS $$
DECLARE
    v_user_id UUID;
BEGIN
    CASE p_channel
        WHEN 'telegram' THEN
            SELECT id INTO v_user_id FROM user_profiles 
            WHERE telegram_id = p_identifier::BIGINT;
        WHEN 'whatsapp' THEN
            SELECT id INTO v_user_id FROM user_profiles 
            WHERE whatsapp_phone = p_identifier;
        WHEN 'pwa' THEN
            SELECT id INTO v_user_id FROM user_profiles 
            WHERE email = p_identifier OR auth_id::TEXT = p_identifier;
    END CASE;
    
    RETURN v_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Updated timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS user_profiles_updated_at ON user_profiles;
CREATE TRIGGER user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================================================
-- GRANTS
-- ============================================================================

GRANT ALL ON user_profiles TO service_role;
GRANT ALL ON channel_verifications TO service_role;
GRANT ALL ON memory_vault TO service_role;
GRANT EXECUTE ON FUNCTION search_memories TO service_role;
GRANT EXECUTE ON FUNCTION get_user_by_channel TO service_role;
