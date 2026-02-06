-- ==========================================================================
-- Integrations (Encrypted Secrets)
-- ==========================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS integrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    key TEXT NOT NULL,
    value_encrypted TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (tenant_id, key)
);

CREATE INDEX IF NOT EXISTS idx_integrations_tenant ON integrations(tenant_id);

ALTER TABLE integrations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "integrations_tenant_isolation" ON integrations
    FOR ALL
    USING (
        tenant_id IN (
            SELECT tenant_id FROM tenant_users WHERE user_id = auth.uid()
        )
    );

CREATE OR REPLACE FUNCTION integrations_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER integrations_updated_at
    BEFORE UPDATE ON integrations
    FOR EACH ROW EXECUTE FUNCTION integrations_updated_at();
