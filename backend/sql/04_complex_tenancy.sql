-- Enable UUID extension if not exists
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- PROJECTS TABLE
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'active',
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- TASKS TABLE
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'blocked')),
    priority TEXT DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    assigned_agent_id UUID REFERENCES agents(id),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- KNOWLEDGE SOURCES TABLE (Mirroring NotebookLM sources)
CREATE TABLE IF NOT EXISTS knowledge_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    source_type TEXT NOT NULL CHECK (source_type IN ('url', 'pdf', 'drive', 'text', 'notebook')),
    source_url TEXT,
    summary TEXT,
    notebooklm_source_id TEXT, -- Link to external NLM ID
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- RLS POLICIES (Simple isolation)
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_sources ENABLE ROW LEVEL SECURITY;

-- Projects Policy
CREATE POLICY "Tenants can see their own projects" ON projects
    FOR ALL
    USING (
        tenant_id IN (
            SELECT tenant_id FROM tenant_users WHERE user_id = auth.uid()
        )
    );

-- Tasks Policy (via Project)
CREATE POLICY "Tenants can see tasks in their projects" ON tasks
    FOR ALL
    USING (
        project_id IN (
            SELECT id FROM projects
            WHERE tenant_id IN (
                SELECT tenant_id FROM tenant_users WHERE user_id = auth.uid()
            )
        )
    );

-- Knowledge Sources Policy
CREATE POLICY "Tenants can see their own knowledge sources" ON knowledge_sources
    FOR ALL
    USING (
        tenant_id IN (
            SELECT tenant_id FROM tenant_users WHERE user_id = auth.uid()
        )
    );

-- Indexes for performance
CREATE INDEX idx_projects_tenant ON projects(tenant_id);
CREATE INDEX idx_tasks_project ON tasks(project_id);
CREATE INDEX idx_knowledge_tenant ON knowledge_sources(tenant_id);
