# AureonCore

> **Backend híbrido** de CortexOS — Aureon (cerebro) + Runa (alma)  
> Fabricado por MultiversaGroup. El core que convierte MultiversaGroup en fábrica de cash flow.

## Despliegue

| Componente | Dominio | Plataforma |
|------------|---------|------------|
| **Backend** (AureonCore) | core.multiversa.group | Railway |
| **Frontend** (Admin / Aureon Visual) | app.multiversa.group | Vercel |

## Railway

1. Conecta este repo a Railway (GitHub App instalada)
2. Configura variables de entorno en Railway Dashboard (ver `.env.example`)
3. Añade dominio personalizado: `core.multiversa.group`
4. Railway usa Nixpacks/Procfile para desplegar

### Variables requeridas en Railway

- `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_ANON_KEY`
- `GEMINI_API_KEY`, `GROQ_API_KEY`, `MISTRAL_API_KEY`
- `CORS_ORIGINS` (incluir `https://app.multiversa.group` para el frontend en Vercel)

## Local

```bash
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

Health: http://localhost:8000/health
