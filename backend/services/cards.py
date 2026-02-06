"""
🎴 Aureon Cortex - Card Generator
Generates structured UI cards for different response types.
Based on Manus AI & GenSpark patterns.
Python 3.9 compatible.
"""
from typing import Optional, List, Dict, Literal
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import time


class CardType(str, Enum):
    RESEARCH = "research"
    REASONING = "reasoning"
    ACTION = "action"
    DATA = "data"
    INTEGRATION = "integration"
    CHAT = "chat"


class CardStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class Source:
    """A source reference for research cards."""
    title: str
    url: Optional[str] = None
    snippet: Optional[str] = None
    confidence: float = 1.0


@dataclass
class ReasoningStep:
    """A single step in the reasoning process."""
    number: int
    description: str
    status: CardStatus = CardStatus.PENDING
    duration_ms: Optional[int] = None
    result: Optional[str] = None


@dataclass
class KeyPoint:
    """A key point with optional icon."""
    text: str
    icon: str = "•"


@dataclass
class ResponseCard:
    """A structured response card."""
    id: str
    type: CardType
    title: str
    status: CardStatus = CardStatus.COMPLETE
    # Content
    summary: Optional[str] = None
    content: Optional[str] = None
    key_points: List[KeyPoint] = field(default_factory=list)
    # Metadata
    sources: List[Source] = field(default_factory=list)
    reasoning_steps: List[ReasoningStep] = field(default_factory=list)
    confidence: Optional[float] = None
    duration_ms: int = 0
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """Convert to JSON-serializable dict."""
        return {
            "id": self.id,
            "type": self.type.value,
            "title": self.title,
            "status": self.status.value,
            "summary": self.summary,
            "content": self.content,
            "key_points": [{"text": kp.text, "icon": kp.icon} for kp in self.key_points],
            "sources": [
                {"title": s.title, "url": s.url, "snippet": s.snippet}
                for s in self.sources
            ],
            "reasoning_steps": [
                {
                    "number": rs.number,
                    "description": rs.description,
                    "status": rs.status.value,
                    "duration_ms": rs.duration_ms,
                    "result": rs.result
                }
                for rs in self.reasoning_steps
            ],
            "confidence": self.confidence,
            "duration_ms": self.duration_ms,
            "created_at": self.created_at.isoformat()
        }


class CardGenerator:
    """
    Generates response cards for different types of AI outputs.
    """
    
    def __init__(self):
        self._step_counter = 0
    
    def create_research_card(
        self,
        title: str,
        summary: str,
        key_points: List[str],
        sources: List[Dict] = None,
        confidence: float = 0.85,
        duration_ms: int = 0
    ) -> ResponseCard:
        """Create a research-type card."""
        import uuid
        
        return ResponseCard(
            id=str(uuid.uuid4())[:8],
            type=CardType.RESEARCH,
            title=title,
            status=CardStatus.COMPLETE,
            summary=summary,
            key_points=[KeyPoint(text=kp, icon="🔹") for kp in key_points],
            sources=[
                Source(title=s.get("title", ""), url=s.get("url"), snippet=s.get("snippet"))
                for s in (sources or [])
            ],
            confidence=confidence,
            duration_ms=duration_ms
        )
    
    def create_reasoning_card(
        self,
        title: str,
        steps: List[str],
        conclusion: str,
        confidence: float = 0.9
    ) -> ResponseCard:
        """Create a reasoning-type card with visible steps."""
        import uuid
        
        reasoning_steps = [
            ReasoningStep(
                number=i + 1,
                description=step,
                status=CardStatus.COMPLETE
            )
            for i, step in enumerate(steps)
        ]
        
        return ResponseCard(
            id=str(uuid.uuid4())[:8],
            type=CardType.REASONING,
            title=title,
            status=CardStatus.COMPLETE,
            summary=conclusion,
            reasoning_steps=reasoning_steps,
            confidence=confidence
        )
    
    def create_action_card(
        self,
        title: str,
        action_type: str,
        result: str,
        success: bool = True
    ) -> ResponseCard:
        """Create an action-type card for executed tasks."""
        import uuid
        
        return ResponseCard(
            id=str(uuid.uuid4())[:8],
            type=CardType.ACTION,
            title=title,
            status=CardStatus.COMPLETE if success else CardStatus.FAILED,
            summary=result,
            key_points=[
                KeyPoint(text=f"Action: {action_type}", icon="⚡"),
                KeyPoint(text=f"Result: {'Success' if success else 'Failed'}", icon="✅" if success else "❌")
            ]
        )
    
    def create_data_card(
        self,
        title: str,
        data: Dict,
        insights: List[str]
    ) -> ResponseCard:
        """Create a data-type card for analysis results."""
        import uuid
        
        return ResponseCard(
            id=str(uuid.uuid4())[:8],
            type=CardType.DATA,
            title=title,
            status=CardStatus.COMPLETE,
            content=str(data),
            key_points=[KeyPoint(text=insight, icon="📊") for insight in insights]
        )
    
    def create_chat_card(
        self,
        content: str,
        user_name: Optional[str] = None,
        duration_ms: int = 0
    ) -> ResponseCard:
        """Create a simple chat response card."""
        import uuid
        
        title = f"Respuesta para {user_name}" if user_name else "Respuesta"
        
        return ResponseCard(
            id=str(uuid.uuid4())[:8],
            type=CardType.CHAT,
            title=title,
            status=CardStatus.COMPLETE,
            content=content,
            duration_ms=duration_ms
        )
    
    def detect_card_type(self, content: str, task_type: str) -> CardType:
        """Detect the appropriate card type based on content and task."""
        content_lower = content.lower()
        
        if task_type == "researcher" or "investigación" in content_lower or "busqué" in content_lower:
            return CardType.RESEARCH
        elif "pasos" in content_lower or "primero" in content_lower or "entonces" in content_lower:
            return CardType.REASONING
        elif task_type in ["coder", "analyst"] or "ejecuté" in content_lower or "completado" in content_lower:
            return CardType.ACTION
        elif "datos" in content_lower or "análisis" in content_lower or "%" in content:
            return CardType.DATA
        else:
            return CardType.CHAT


# Singleton
card_generator = CardGenerator()
