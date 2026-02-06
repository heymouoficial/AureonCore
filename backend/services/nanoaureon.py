"""
🤖 Aureon Cortex - NanoAureon Fleet Manager
Gestiona sub-agentes especializados para tareas específicas.
Python 3.9 compatible.
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from datetime import datetime
import uuid

from .intelligence import intelligence_pool


class NanoType(Enum):
    """Tipos de NanoAureons especializados."""
    RESEARCHER = "researcher"
    CODER = "coder"
    ANALYST = "analyst"
    WRITER = "writer"


@dataclass
class NanoAureon:
    """Un sub-agente especializado."""
    id: str
    name: str
    type: NanoType
    system_prompt: str
    status: str = "idle"  # idle, working, error
    current_task: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    async def execute(self, task: str) -> str:
        """Ejecuta una tarea con este NanoAureon."""
        self.status = "working"
        self.current_task = task
        
        try:
            result = await intelligence_pool.complete(
                prompt=task,
                system_prompt=self.system_prompt,
                max_tokens=2048,
                temperature=0.5  # Lower for more focused responses
            )
            self.status = "idle"
            self.current_task = None
            return result
        except Exception as e:
            self.status = "error"
            raise e


class NanoFleet:
    """
    Gestor de la flota de NanoAureons.
    Crea, administra y asigna NanoAureons a tareas.
    """
    
    # Prompts predefinidos para cada tipo
    SYSTEM_PROMPTS = {
        NanoType.RESEARCHER: """Eres un NanoAureon especializado en investigación.
Tu rol es buscar, analizar y sintetizar información de forma precisa.
- Proporciona fuentes cuando sea posible
- Sé objetivo y basado en datos
- Resume los hallazgos de forma clara""",
        
        NanoType.CODER: """Eres un NanoAureon especializado en programación.
Tu rol es escribir código limpio, eficiente y bien documentado.
- Usa tipado estricto (TypeScript, Python type hints)
- Sigue las mejores prácticas del lenguaje
- Incluye comentarios explicativos
- Prefiere FastAPI para backend, React para frontend""",
        
        NanoType.ANALYST: """Eres un NanoAureon especializado en análisis de datos.
Tu rol es interpretar métricas, identificar patrones y generar insights.
- Usa visualizaciones mentales al explicar
- Proporciona conclusiones accionables
- Sé preciso con los números""",
        
        NanoType.WRITER: """Eres un NanoAureon especializado en redacción.
Tu rol es crear contenido claro, persuasivo y bien estructurado.
- Adapta el tono al contexto
- Usa estructura jerárquica (headers, bullets)
- Sé conciso pero completo"""
    }
    
    def __init__(self):
        self._fleet: Dict[str, NanoAureon] = {}
        self._initialize_default_fleet()
    
    def _initialize_default_fleet(self):
        """Crea los NanoAureons por defecto."""
        for nano_type in NanoType:
            nano = self.create(nano_type)
            self._fleet[nano.id] = nano
    
    def create(
        self,
        nano_type: NanoType,
        name: Optional[str] = None,
        custom_prompt: Optional[str] = None
    ) -> NanoAureon:
        """Crea un nuevo NanoAureon."""
        nano_id = str(uuid.uuid4())
        nano_name = name or f"NanoAureon.{nano_type.value.capitalize()}"
        system_prompt = custom_prompt or self.SYSTEM_PROMPTS[nano_type]
        
        nano = NanoAureon(
            id=nano_id,
            name=nano_name,
            type=nano_type,
            system_prompt=system_prompt
        )
        
        self._fleet[nano_id] = nano
        return nano
    
    def get(self, nano_id: str) -> Optional[NanoAureon]:
        """Obtiene un NanoAureon por ID."""
        return self._fleet.get(nano_id)
    
    def get_by_type(self, nano_type: NanoType) -> List[NanoAureon]:
        """Obtiene todos los NanoAureons de un tipo."""
        return [n for n in self._fleet.values() if n.type == nano_type]
    
    def get_available(self, nano_type: Optional[NanoType] = None) -> List[NanoAureon]:
        """Obtiene NanoAureons disponibles (idle)."""
        nanos = list(self._fleet.values())
        if nano_type:
            nanos = [n for n in nanos if n.type == nano_type]
        return [n for n in nanos if n.status == "idle"]
    
    def list_all(self) -> List[NanoAureon]:
        """Lista todos los NanoAureons."""
        return list(self._fleet.values())
    
    async def delegate(self, nano_type: NanoType, task: str) -> str:
        """
        Delega una tarea al primer NanoAureon disponible del tipo especificado.
        Si no hay disponibles, crea uno nuevo temporalmente.
        """
        available = self.get_available(nano_type)
        
        if available:
            nano = available[0]
        else:
            # Create temporary nano
            nano = self.create(nano_type, name=f"TempNano.{nano_type.value}")
        
        result = await nano.execute(task)
        return result


# Singleton
nano_fleet = NanoFleet()
