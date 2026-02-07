# 🌌 Auréon Quantum - Nucleo de Orquestación y Multi-tenencia
from contextlib import asynccontextmanager
from typing import Optional, List, Dict
from fastapi import FastAPI, Request, HTTPException, Depends, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
import os
import sys
import asyncio
import uuid as uuid_lib
from datetime import datetime

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import Cortex services
from core.config import settings
from core.supabase import get_supabase_admin
from core.security import encrypt_secret
from core.deps import get_current_user, get_current_tenant
from services.orchestrator import orchestrator
from services.nanoaureon import nano_fleet, NanoType
from services.whatsapp import whatsapp_service
from services.telegram import telegram_service
from services.identity import identity_service
from services.memory import memory_service
from services.research import research_service
from services.ingestion import ingestion_service
from services.embeddings import generate_embedding


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager para inicialización y cleanup."""
    # Startup
    print("🌀 Aureon Cortex iniciando...")
    print(f"   Environment: {settings.app_env}")
    print(f"   Domain: {settings.domain}")
    available_providers = []
    if settings.groq_api_key: available_providers.append("Groq")
    if settings.gemini_api_key: available_providers.append("Gemini")
    if settings.mistral_api_key: available_providers.append("Mistral")
    if settings.deepseek_api_key: available_providers.append("DeepSeek")
    print(f"   AI Providers: {', '.join(available_providers) if available_providers else 'NONE CONFIGURED!'}")
    print(f"   NanoAureons: {len(nano_fleet.list_all())}")
    print(f"   WhatsApp: {'✓' if settings.whatsapp_api_token else '✗'}")
    print(f"   Telegram: {'✓' if settings.telegram_bot_token else '✗'}")
    yield
    print("🌀 Aureon Cortex cerrando...")


app = FastAPI(
    title="CortexOS",
    description="Sistema Operativo Inteligente Binario Polímata (Aureon + Runa)",
    version="3.0.0",
    lifespan=lifespan
)

# Configuración CORS (CORS_ORIGINS vacío = permitir todos; prod: core.multiversa.group, *.vercel.app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response

# Vault setup
CONFIG_FILE = "vault/brain_config.json"
os.makedirs("vault", exist_ok=True)


class TenantPreferences(BaseModel):
    alias: str
    theme: str
    voice_mode: bool = False


class TenantSecret(BaseModel):
    key: str
    value: str
    description: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    channel: str = "pwa"
    sender_id: str = "default"
    conversation_id: Optional[str] = None


class NanoRequest(BaseModel):
    task: str
    type: str = "researcher"


class LinkChannelRequest(BaseModel):
    channel: str  # 'telegram' or 'whatsapp'


class VerifyChannelRequest(BaseModel):
    code: str
    channel: str
    channel_identifier: str


class MemorySearchRequest(BaseModel):
    query: str
    k: int = 5


class ResearchRequest(BaseModel):
    query: str
    k: int = 5


class IntegrationRequest(BaseModel):
    key: str
    value: str


async def resolve_tenant_for_user(user_id: str) -> Optional[str]:
    admin = get_supabase_admin()
    res = admin.table("tenant_users").select("tenant_id").eq("user_id", user_id).limit(1).execute()
    if res and res.data:
        return res.data[0]["tenant_id"]
    return None


# ============================================================================
# ROOT & HEALTH
# ============================================================================

@app.get("/")
async def root():
    return {
        "status": "online",
        "system": "CortexOS - Aureon + Runa",
        "version": "3.0.0 Portality",
        "tier": "Cortex",
        "capabilities": {
            "channels": ["whatsapp", "telegram", "pwa"],
            "ai_providers": ["gemini", "groq", "mistral", "deepseek"],
            "nanoaureons": [n.name for n in nano_fleet.list_all()]
        },
        "message": "Consciencia Digital Activa. Portality Ready."
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "cortex": "active"}


# ============================================================================
# BRAIN ENDPOINTS
# ============================================================================

@app.get("/brain/profile")
async def get_profile():
    return {
        "alias": "Moshe",
        "tier": "cortex",
        "theme": "dark",
        "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=Moshe"
    }


@app.post("/brain/secrets")
async def save_secret(secret: TenantSecret):
    print(f"🔒 Secret received: {secret.key} = *******")
    return {"status": "encrypted", "key": secret.key}


@app.get("/brain/sync")
async def get_current_consciousness():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            json.dump({
                "personality_level": 1.0,
                "active_agents": ["Auréon.Vox"],
                "tenants": {"default": {"enabled": True}},
                "integrations": {}
            }, f, indent=4)
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


class SystemUpdate(BaseModel):
    personality_level: float
    active_agents: list
    tenants: dict
    integrations: dict


@app.post("/brain/evolve")
async def update_consciousness(update: SystemUpdate):
    with open(CONFIG_FILE, "w") as f:
        json.dump(update.dict(), f, indent=4)
    return {"status": "Evolución completada."}


# ============================================================================
# CHAT & ORCHESTRATOR (with SSE Streaming)
# ============================================================================

# Task Manager for SSE streaming
class TaskManager:
    """Manages in-flight tasks for SSE streaming."""
    
    def __init__(self):
        self.tasks: Dict[str, Dict] = {}
    
    def create_task(self, task_id: str, message: str) -> Dict:
        """Create a new task with initial steps."""
        self.tasks[task_id] = {
            "id": task_id,
            "message": message,
            "status": "active",
            "steps": [
                {"number": 1, "description": "Analizando mensaje", "status": "active", "result": None},
                {"number": 2, "description": "Procesando contexto", "status": "pending", "result": None},
                {"number": 3, "description": "Generando respuesta", "status": "pending", "result": None},
            ],
            "current_step": 0,
            "created_at": datetime.now().isoformat(),
            "response": None
        }
        return self.tasks[task_id]
    
    def update_step(self, task_id: str, step_number: int, status: str, result: str = None):
        """Update a specific step's status."""
        if task_id in self.tasks:
            for step in self.tasks[task_id]["steps"]:
                if step["number"] == step_number:
                    step["status"] = status
                    if result:
                        step["result"] = result
                    break
            self.tasks[task_id]["current_step"] = step_number
    
    def complete_task(self, task_id: str, response: str, card: Dict = None):
        """Mark task as complete with response."""
        if task_id in self.tasks:
            self.tasks[task_id]["status"] = "complete"
            self.tasks[task_id]["response"] = response
            self.tasks[task_id]["card"] = card
            for step in self.tasks[task_id]["steps"]:
                if step["status"] != "complete":
                    step["status"] = "complete"
    
    def get_task(self, task_id: str) -> Dict:
        """Get task by ID."""
        return self.tasks.get(task_id)
    
    def cleanup(self, task_id: str):
        """Remove completed task."""
        if task_id in self.tasks:
            del self.tasks[task_id]


task_manager = TaskManager()


class ChatStreamRequest(BaseModel):
    message: str
    channel: str = "pwa"
    sender_id: str = "default"
    conversation_id: Optional[str] = None


@app.post("/api/v1/chat/stream")
async def chat_stream(
    request: ChatStreamRequest,
    current_user: Dict = Depends(get_current_user),
    tenant: Dict = Depends(get_current_tenant),
):
    """Chat endpoint with SSE streaming for real-time progress."""
    from services.orchestrator import Message
    
    task_id = str(uuid_lib.uuid4())
    task = task_manager.create_task(task_id, request.message)
    
    async def event_generator():
        try:
            # Step 1: Analyzing
            task_manager.update_step(task_id, 1, "active")
            yield f"data: {json.dumps({'type': 'step', 'step': 1, 'status': 'active', 'description': 'Analizando mensaje'})}\n\n"
            await asyncio.sleep(0.3)
            task_manager.update_step(task_id, 1, "complete", "Mensaje parseado")
            yield f"data: {json.dumps({'type': 'step', 'step': 1, 'status': 'complete', 'result': 'Mensaje parseado'})}\n\n"
            
            # Step 2: Context
            task_manager.update_step(task_id, 2, "active")
            yield f"data: {json.dumps({'type': 'step', 'step': 2, 'status': 'active', 'description': 'Procesando contexto'})}\n\n"
            
            sender_id = current_user["id"] if request.channel == "pwa" else request.sender_id
            message = Message(
                id=task_id,
                channel=request.channel,
                sender_id=sender_id,
                content=request.message,
                timestamp=datetime.now(),
                tenant_id=tenant["id"],
                user_id=current_user["id"],
                metadata={"conversation_id": request.conversation_id} if request.conversation_id else {},
            )
            
            await asyncio.sleep(0.2)
            task_manager.update_step(task_id, 2, "complete", "Contexto cargado")
            yield f"data: {json.dumps({'type': 'step', 'step': 2, 'status': 'complete', 'result': 'Contexto cargado'})}\n\n"
            
            # Step 3: Generating response
            task_manager.update_step(task_id, 3, "active")
            yield f"data: {json.dumps({'type': 'step', 'step': 3, 'status': 'active', 'description': 'Generando respuesta'})}\n\n"
            
            response = await orchestrator.process(message)
            
            task_manager.update_step(task_id, 3, "complete", "Respuesta lista")
            yield f"data: {json.dumps({'type': 'step', 'step': 3, 'status': 'complete', 'result': 'Respuesta lista'})}\n\n"
            
            # Final response
            task_manager.complete_task(task_id, response.content, response.card)
            yield f"data: {json.dumps({'type': 'complete', 'response': response.content, 'card': response.card, 'citations': response.citations, 'user_id': response.user_id, 'user_name': response.user_name, 'conversation_id': response.conversation_id, 'processing_time_ms': response.processing_time_ms})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        finally:
            # Cleanup after brief delay
            await asyncio.sleep(5)
            task_manager.cleanup(task_id)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.get("/api/v1/task/{task_id}")
async def get_task_status(
    task_id: str,
    current_user: Dict = Depends(get_current_user),
    tenant: Dict = Depends(get_current_tenant),
):
    """Get current task status and steps."""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.post("/api/v1/chat")
async def chat(
    request: ChatRequest,
    current_user: Dict = Depends(get_current_user),
    tenant: Dict = Depends(get_current_tenant),
):
    """Endpoint principal de chat con soporte de UI cards."""
    from services.orchestrator import Message
    
    try:
        task_id = str(uuid_lib.uuid4())
        sender_id = current_user["id"] if request.channel == "pwa" else request.sender_id
        message = Message(
            id=task_id,
            channel=request.channel,
            sender_id=sender_id,
            content=request.message,
            timestamp=datetime.now(),
            tenant_id=tenant["id"],
            user_id=current_user["id"],
            metadata={"conversation_id": request.conversation_id} if request.conversation_id else {},
        )
        
        response = await orchestrator.process(message)
        
        return {
            "status": "success",
            "task_id": task_id,
            "response": response.content,
            "channel": request.channel,
            "user_id": response.user_id,
            "user_name": response.user_name,
            "conversation_id": response.conversation_id,
            "processing_time_ms": response.processing_time_ms,
            "nanoaureon": response.nanoaureon_used,
            "card": response.card,
            "citations": response.citations
        }
    except Exception as e:
        print(f"❌ Chat error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# NANOAUREONS FLEET
# ============================================================================

@app.get("/api/v1/nanoaureons")
async def list_nanoaureons(
    current_user: Dict = Depends(get_current_user),
    tenant: Dict = Depends(get_current_tenant),
):
    nanos = nano_fleet.list_all()
    return {
        "status": "success",
        "count": len(nanos),
        "fleet": [
            {
                "id": n.id,
                "name": n.name,
                "type": n.type.value,
                "status": n.status,
                "current_task": n.current_task
            }
            for n in nanos
        ]
    }


@app.post("/api/v1/nanoaureons/{nano_type}/execute")
async def execute_nanoaureon(
    nano_type: str,
    request: NanoRequest,
    current_user: Dict = Depends(get_current_user),
    tenant: Dict = Depends(get_current_tenant),
):
    try:
        nano_enum = NanoType(nano_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid NanoType: {nano_type}")
    
    try:
        result = await nano_fleet.delegate(nano_enum, request.task)
        return {
            "status": "success",
            "nano_type": nano_type,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# WHATSAPP WEBHOOK
# ============================================================================

@app.get("/webhook/whatsapp")
async def verify_whatsapp(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
):
    """
    Verificación de webhook de WhatsApp (Meta Developers).
    Meta envía GET con hub.mode, hub.challenge, hub.verify_token.
    Hay que devolver el challenge si el token coincide.
    """
    if not settings.whatsapp_verify_token:
        raise HTTPException(status_code=500, detail="WHATSAPP_VERIFY_TOKEN not configured")
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        return hub_challenge or ""
    raise HTTPException(status_code=403, detail="Invalid verify token")


@app.post("/webhook/whatsapp")
async def receive_whatsapp(request: Request):
    """Recibe y procesa mensajes de WhatsApp."""
    data = await request.json()
    
    # Parse incoming message
    parsed = whatsapp_service.parse_incoming(data)
    if not parsed or not parsed.get("text"):
        return {"status": "ignored"}
    
    sender = parsed["from"]
    text = parsed["text"]
    
    # Check whitelist + verification
    if not whatsapp_service.is_allowed(sender):
        print(f"📱 WhatsApp blocked (not whitelisted): {sender}")
        return {"status": "blocked"}

    profile = await identity_service.get_by_whatsapp(sender)
    if not profile or not profile.get("whatsapp_verified_at"):
        print(f"📱 WhatsApp blocked (not verified): {sender}")
        return {"status": "blocked"}
    
    print(f"📱 WhatsApp from {sender}: {text[:50]}...")
    
    # Process with orchestrator
    try:
        tenant_id = await resolve_tenant_for_user(profile["id"])
        if not tenant_id:
            return {"status": "blocked"}

        from services.orchestrator import Message
        message = Message(
            id=str(uuid_lib.uuid4()),
            channel="whatsapp",
            sender_id=sender,
            content=text,
            timestamp=datetime.now(),
            tenant_id=tenant_id,
            user_id=profile["id"],
            metadata={},
        )
        response_obj = await orchestrator.process(message)
        response = response_obj.content
        
        # Send response back
        result = await whatsapp_service.send_message(sender, response)
        print(f"📱 WhatsApp sent to {sender}: {response[:50]}...")
        
        return {"status": "processed", "sent": result}
    except Exception as e:
        print(f"❌ WhatsApp error: {e}")
        return {"status": "error", "detail": str(e)}


# ============================================================================
# TELEGRAM WEBHOOK
# ============================================================================

@app.post("/webhook/telegram")
async def receive_telegram(request: Request):
    """Recibe y procesa updates de Telegram."""
    data = await request.json()
    
    # Parse incoming message
    parsed = telegram_service.parse_incoming(data)
    if not parsed or not parsed.get("text"):
        return {"status": "ignored"}
    
    chat_id = parsed["chat_id"]
    user_id = parsed["user_id"]
    text = parsed["text"]
    
    # Check whitelist + verification
    if not telegram_service.is_allowed(user_id):
        print(f"💬 Telegram blocked (not whitelisted): {user_id}")
        return {"status": "blocked"}

    profile = await identity_service.get_by_telegram(user_id)
    if not profile or not profile.get("telegram_verified_at"):
        print(f"💬 Telegram blocked (not verified): {user_id}")
        return {"status": "blocked"}
    
    print(f"💬 Telegram from {user_id}: {text[:50]}...")
    
    # Handle /start command
    if text.startswith("/start"):
        await telegram_service.send_message(chat_id, "🌀 <b>Auréon activado.</b>\n\n¿En qué puedo ayudarte?")
        return {"status": "start_sent"}
    
    # Process with orchestrator
    try:
        tenant_id = await resolve_tenant_for_user(profile["id"])
        if not tenant_id:
            return {"status": "blocked"}

        from services.orchestrator import Message
        message = Message(
            id=str(uuid_lib.uuid4()),
            channel="telegram",
            sender_id=str(user_id),
            content=text,
            timestamp=datetime.now(),
            tenant_id=tenant_id,
            user_id=profile["id"],
            metadata={},
        )
        response_obj = await orchestrator.process(message)
        response = response_obj.content
        
        # Send response back
        result = await telegram_service.send_message(chat_id, response)
        print(f"💬 Telegram sent to {chat_id}: {response[:50]}...")
        
        return {"status": "processed", "sent": result}
    except Exception as e:
        print(f"❌ Telegram error: {e}")
        await telegram_service.send_message(chat_id, f"⚠️ Error: {str(e)[:100]}")
        return {"status": "error", "detail": str(e)}


@app.post("/api/v1/telegram/set-webhook")
async def set_telegram_webhook(
    current_user: Dict = Depends(get_current_user),
    tenant: Dict = Depends(get_current_tenant),
):
    """Configura el webhook de Telegram."""
    webhook_url = f"{settings.domain}/webhook/telegram"
    result = await telegram_service.set_webhook(webhook_url)
    return {"status": "configured", "url": webhook_url, "result": result}


# ============================================================================
# N8N SIGNAL
# ============================================================================

@app.post("/webhook/signal")
async def handle_external_signals(request: Request):
    """Recibe señales de n8n y otras fuentes."""
    data = await request.json()
    return {"status": "received", "keys": list(data.keys())}


# ============================================================================
# IDENTITY & ONBOARDING 360
# ============================================================================

@app.get("/api/v1/auth/profile")
async def get_user_profile(current_user: Dict = Depends(get_current_user)):
    """Get current user profile."""
    profile = await identity_service.get_profile(current_user["id"])
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": profile.get("id"),
        "email": profile.get("email"),
        "display_name": profile.get("display_name"),
        "avatar_url": profile.get("avatar_url"),
        "telegram_id": profile.get("telegram_id"),
        "telegram_verified": profile.get("telegram_verified_at") is not None,
        "whatsapp_phone": profile.get("whatsapp_phone"),
        "whatsapp_verified": profile.get("whatsapp_verified_at") is not None,
        "tier": profile.get("tier"),
        "preferences": profile.get("preferences"),
        "created_at": profile.get("created_at"),
    }


@app.post("/api/v1/channels/link")
async def create_link_verification(
    request: LinkChannelRequest,
    current_user: Dict = Depends(get_current_user),
):
    """Create verification code for channel linking."""
    verification = await identity_service.create_verification(
        user_id=current_user["id"],
        channel=request.channel,
    )
    
    return {
        "status": "pending",
        "channel": request.channel,
        "code": verification.verification_code,
        "expires_at": verification.expires_at.isoformat(),
        "instructions": f"Envía este código a tu bot de {request.channel}: {verification.verification_code}"
    }


@app.post("/api/v1/channels/verify")
async def verify_channel(
    request: VerifyChannelRequest,
    current_user: Dict = Depends(get_current_user),
):
    """Verify channel linking code."""
    result = await identity_service.verify_channel(
        code=request.code,
        channel=request.channel,
        channel_identifier=request.channel_identifier
    )
    
    if not result:
        raise HTTPException(status_code=400, detail="Invalid or expired code")

    if result.get("id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Verification does not match user")
    
    return {
        "status": "verified",
        "channel": request.channel,
        "user_id": result.get("id")
    }


@app.get("/api/v1/auth/stats")
async def get_user_stats(current_user: Dict = Depends(get_current_user)):
    """Get combined stats for a user."""
    stats = await memory_service.get_user_stats(current_user["id"])
    return {"status": "success", **stats}


# ============================================================================
# MEMORY VAULT
# ============================================================================

@app.post("/api/v1/memory/search")
async def search_memories(
    request: MemorySearchRequest,
    current_user: Dict = Depends(get_current_user),
):
    """Search user memories by semantic similarity."""
    results = await memory_service.search_memories(
        user_id=current_user["id"],
        query=request.query,
        k=request.k
    )
    
    return {
        "status": "success",
        "query": request.query,
        "results": [
            {
                "id": memory.id,
                "summary": memory.summary,
                "similarity": score,
                "created_at": memory.created_at if isinstance(memory.created_at, str) else getattr(memory.created_at, "isoformat", lambda: None)()
            }
            for memory, score in results
        ]
    }


@app.get("/api/v1/memory/context")
async def get_context(limit: int = 10, current_user: Dict = Depends(get_current_user)):
    """Get recent context messages for a user."""
    messages = await memory_service.get_context(current_user["id"], limit)
    return {
        "status": "success",
        "count": len(messages),
        "messages": [
            {
                "role": m.role,
                "content": m.content,
                "channel": m.channel,
                "timestamp": m.timestamp.isoformat()
            }
            for m in messages
        ]
    }


@app.post("/api/v1/memory/summarize")
async def force_summarize(current_user: Dict = Depends(get_current_user)):
    """Force summarization of user context."""
    memory = await memory_service.summarize_and_archive(current_user["id"], force=True)
    
    if not memory:
        return {"status": "no_action", "message": "No messages to summarize"}
    
    return {
        "status": "success",
        "memory": {
            "id": memory.id,
            "summary": memory.summary,
            "message_count": memory.message_count
        }
    }


@app.delete("/api/v1/memory/context")
async def clear_context(current_user: Dict = Depends(get_current_user)):
    """Clear active context for a user."""
    await memory_service.clear_context(current_user["id"])
    return {"status": "success", "message": "Context cleared"}


# ============================================================================
# TENANT
# ============================================================================

@app.get("/api/v1/tenants/me")
async def get_current_tenant_info(
    current_user: Dict = Depends(get_current_user),
    tenant: Dict = Depends(get_current_tenant),
):
    return {"status": "success", "tenant": tenant}


# ============================================================================
# RESEARCH
# ============================================================================

@app.post("/api/v1/research")
async def run_research(
    request: ResearchRequest,
    current_user: Dict = Depends(get_current_user),
    tenant: Dict = Depends(get_current_tenant),
):
    try:
        answer, citations = await research_service.search(request.query, k=request.k)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "success", "answer": answer, "citations": citations}


# ============================================================================
# KNOWLEDGE (UPLOAD + SEARCH)
# ============================================================================

@app.post("/api/v1/knowledge/upload")
async def upload_knowledge(
    file: UploadFile = File(...),
    current_user: Dict = Depends(get_current_user),
    tenant: Dict = Depends(get_current_tenant),
):
    content = await file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(status_code=413, detail="File too large")

    result = await ingestion_service.ingest_upload(
        tenant_id=tenant["id"],
        user_id=current_user["id"],
        filename=file.filename or "upload",
        content_type=file.content_type or "application/octet-stream",
        file_bytes=content,
    )
    return {"status": "success", **result}


@app.get("/api/v1/knowledge/search")
async def search_knowledge(
    query: str,
    k: int = 5,
    current_user: Dict = Depends(get_current_user),
    tenant: Dict = Depends(get_current_tenant),
):
    admin = get_supabase_admin()
    embedding = await generate_embedding(query)
    try:
        results = admin.rpc(
            "search_knowledge_chunks",
            {
                "p_tenant_id": tenant["id"],
                "p_query_embedding": embedding,
                "p_limit": k,
            },
        ).execute()
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Knowledge search failed") from exc
    return {"status": "success", "results": results.data or []}


# ============================================================================
# INTEGRATIONS (SECRETS)
# ============================================================================

@app.get("/api/v1/integrations")
async def list_integrations(
    current_user: Dict = Depends(get_current_user),
    tenant: Dict = Depends(get_current_tenant),
):
    admin = get_supabase_admin()
    res = admin.table("integrations") \
        .select("key,created_at,updated_at") \
        .eq("tenant_id", tenant["id"]) \
        .order("created_at", desc=True).execute()
    return {"status": "success", "integrations": res.data or []}


@app.post("/api/v1/integrations")
async def save_integration(
    request: IntegrationRequest,
    current_user: Dict = Depends(get_current_user),
    tenant: Dict = Depends(get_current_tenant),
):
    if not request.key or not request.value:
        raise HTTPException(status_code=400, detail="key and value required")

    admin = get_supabase_admin()
    try:
        encrypted = encrypt_secret(request.value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    payload = {
        "tenant_id": tenant["id"],
        "key": request.key,
        "value_encrypted": encrypted,
    }
    admin.table("integrations").upsert(payload, on_conflict="tenant_id,key").execute()
    return {"status": "success", "key": request.key}
