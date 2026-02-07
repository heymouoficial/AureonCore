# AureonCore

> **Backend híbrido** de CortexOS — Aureon (cerebro) + Runa (alma)  
> Fabricado por MultiversaGroup. El core que convierte MultiversaGroup en fábrica de cash flow.

## Despliegue

| Componente | Dominio | Plataforma |
|------------|---------|------------|
| **Backend** (AureonCore) | core.multiversa.group | Railway |
| **Frontend** (Admin / Aureon Visual) | app.multiversa.group | Vercel |

**Vercel**: Importar este repo → Root Directory = `frontend` → Variables: `VITE_API_URL`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`

## Crear repo en GitHub

```bash
# En GitHub: New repository → nombre: AureonCore

cd /Users/moshe/Proyectos/AureonCore
git remote add origin https://github.com/TU_USUARIO/AureonCore.git
git branch -M main
git push -u origin main
```

## Railway

1. En [Railway](https://railway.app) → **New Project** → **Deploy from GitHub repo**
2. Conecta y selecciona el repo **AureonCore**
3. Configura variables de entorno en **Variables** (ver `.env.example`)
4. **Settings** → **Domains** → añade `core.multiversa.group`
5. Railway detecta Procfile/Nixpacks y despliega

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
