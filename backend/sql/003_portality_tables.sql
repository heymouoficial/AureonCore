-- ============================================================================
-- Aureon Portality - Database Migration
-- Multi-channel conversations, messages, and NanoAureons
-- ============================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- TENANTS CORE (dependency for RLS policies)
-- ============================================================================
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    owner_user_id UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tenant_users (
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    role TEXT DEFAULT 'owner' CHECK (role IN ('owner')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (tenant_id, user_id)
);

-- ============================================================================
-- CONVERSATIONS: Multi-channel conversation tracking
-- ============================================================================
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    channel TEXT NOT NULL CHECK (channel IN ('whatsapp', 'telegram', 'pwa')),
    channel_user_id TEXT NOT NULL,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'closed', 'archived')),
    context JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Unique conversation per channel user per tenant
    UNIQUE (tenant_id, channel, channel_user_id)
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_conversations_tenant ON conversations(tenant_id);
CREATE INDEX IF NOT EXISTS idx_conversations_channel ON conversations(channel, channel_user_id);

-- ============================================================================
-- MESSAGES: Conversation history
-- ============================================================================
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for conversation history
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at);

-- ============================================================================
-- NANOAUREONS: Sub-agent fleet
-- ============================================================================
CREATE TABLE IF NOT EXISTS nanoaureons (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('researcher', 'coder', 'analyst', 'writer', 'custom')),
    system_prompt TEXT,
    capabilities JSONB DEFAULT '[]',
    status TEXT DEFAULT 'idle' CHECK (status IN ('idle', 'working', 'error', 'disabled')),
    current_task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    stats JSONB DEFAULT '{"tasks_completed": 0, "avg_response_ms": 0}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for fleet management
CREATE INDEX IF NOT EXISTS idx_nanoaureons_tenant ON nanoaureons(tenant_id);
CREATE INDEX IF NOT EXISTS idx_nanoaureons_type ON nanoaureons(type);
CREATE INDEX IF NOT EXISTS idx_nanoaureons_status ON nanoaureons(status);

-- ============================================================================
-- RLS POLICIES: Multi-tenant isolation
-- ============================================================================

-- Enable RLS
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE nanoaureons ENABLE ROW LEVEL SECURITY;

-- Conversations: Users can only see their tenant's conversations
CREATE POLICY "conversations_tenant_isolation" ON conversations
    FOR ALL USING (
        tenant_id IN (
            SELECT tenant_id FROM tenant_users 
            WHERE user_id = auth.uid()
        )
    );

-- Messages: Inherit from conversation access
CREATE POLICY "messages_conversation_access" ON messages
    FOR ALL USING (
        conversation_id IN (
            SELECT id FROM conversations
            WHERE tenant_id IN (
                SELECT tenant_id FROM tenant_users 
                WHERE user_id = auth.uid()
            )
        )
    );

-- NanoAureons: Tenant isolation
CREATE POLICY "nanoaureons_tenant_isolation" ON nanoaureons
    FOR ALL USING (
        tenant_id IN (
            SELECT tenant_id FROM tenant_users 
            WHERE user_id = auth.uid()
        )
    );

-- ============================================================================
-- FUNCTIONS: Auto-update timestamps
-- ============================================================================
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for auto-update
CREATE TRIGGER conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER nanoaureons_updated_at
    BEFORE UPDATE ON nanoaureons
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================================================
-- SEED: Default NanoAureons for new tenants
-- ============================================================================
-- This would be called by a trigger or function when a new tenant is created
-- For now, we'll create them for the existing tenants

INSERT INTO nanoaureons (tenant_id, name, type, system_prompt)
SELECT 
    t.id,
    'NanoAureon.Researcher',
    'researcher',
    'Eres un NanoAureon especializado en investigación. Analiza, busca y sintetiza información.'
FROM tenants t
WHERE NOT EXISTS (
    SELECT 1 FROM nanoaureons n WHERE n.tenant_id = t.id AND n.type = 'researcher'
);

INSERT INTO nanoaureons (tenant_id, name, type, system_prompt)
SELECT 
    t.id,
    'NanoAureon.Coder',
    'coder',
    'Eres un NanoAureon especializado en programación. Escribe código limpio y documentado.'
FROM tenants t
WHERE NOT EXISTS (
    SELECT 1 FROM nanoaureons n WHERE n.tenant_id = t.id AND n.type = 'coder'
);

INSERT INTO nanoaureons (tenant_id, name, type, system_prompt)
SELECT 
    t.id,
    'NanoAureon.Analyst',
    'analyst',
    'Eres un NanoAureon especializado en análisis. Interpreta datos y genera insights.'
FROM tenants t
WHERE NOT EXISTS (
    SELECT 1 FROM nanoaureons n WHERE n.tenant_id = t.id AND n.type = 'analyst'
);

INSERT INTO nanoaureons (tenant_id, name, type, system_prompt)
SELECT 
    t.id,
    'NanoAureon.Writer',
    'writer',
    'Eres un NanoAureon especializado en redacción. Crea contenido claro y persuasivo.'
FROM tenants t
WHERE NOT EXISTS (
    SELECT 1 FROM nanoaureons n WHERE n.tenant_id = t.id AND n.type = 'writer'
);
