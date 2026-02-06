-- Seed Data for "Clínica Vida" (Cortex Tenant)

DO $$ 
DECLARE 
    new_tenant_id UUID;
    project_id UUID;
    agent_id UUID;
BEGIN
    -- 1. Create Tenant
    INSERT INTO tenants (name, tier, preferences)
    VALUES (
        'Clínica Vida', 
        'cortex', 
        '{"alias": "Dr. AI", "theme": "clinical_blue", "voice": "formal"}'::jsonb
    )
    RETURNING id INTO new_tenant_id;

    -- 2. Create Agent for this tenant
    INSERT INTO agents (name, role, status, tenant_id)
    VALUES (
        'MediBot Beta', 
        'medical_assistant', 
        'active', 
        new_tenant_id
    )
    RETURNING id INTO agent_id;

    -- 3. Create Project
    INSERT INTO projects (tenant_id, name, description, status)
    VALUES (
        new_tenant_id,
        'Digitalización de Historias Clínicas',
        'Proyecto para migrar expedientes físicos a digital usando OCR + AI',
        'active'
    )
    RETURNING id INTO project_id;

    -- 4. Create Tasks
    INSERT INTO tasks (project_id, title, description, status, priority, assigned_agent_id)
    VALUES 
        (project_id, 'Escanear lote 2023', 'Procesar los expedientes de Enero 2023', 'pending', 'high', agent_id),
        (project_id, 'Validar PII', 'Verificar que no se filtren datos sensibles sin encriptar', 'pending', 'critical', agent_id),
        (project_id, 'Entrenar modelo local', 'Fine-tuning del modelo con terminología local', 'blocked', 'medium', NULL);

    RAISE NOTICE 'Seed completed. Tenant ID: %, Project ID: %', new_tenant_id, project_id;
END $$;
