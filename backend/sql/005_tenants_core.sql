-- ==========================================================================
-- Aureon Core Tenancy
-- ==========================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

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

CREATE INDEX IF NOT EXISTS idx_tenant_users_user ON tenant_users(user_id);

ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_users ENABLE ROW LEVEL SECURITY;

CREATE POLICY "tenants_owner_access" ON tenants
    FOR ALL
    USING (id IN (
        SELECT tenant_id FROM tenant_users WHERE user_id = auth.uid()
    ));

CREATE POLICY "tenant_users_isolation" ON tenant_users
    FOR ALL
    USING (user_id = auth.uid());
