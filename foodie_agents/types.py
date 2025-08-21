"""Core types and interfaces for Foodie Agents system."""

from typing import Dict, Any, List, Literal, Optional
from dataclasses import dataclass, field
from pydantic import BaseModel
from datetime import datetime
import uuid

# ============================================================================
# Core State and Reasoning
# ============================================================================

@dataclass
class FoodieState:
    """Core state for food tour planning."""
    budget: float = 100.0
    city: str = "Chicago"
    vibe: str = "cozy"
    date: str = "2025-08-23"
    weather: Dict[str, Any] = field(default_factory=dict)
    shortlist: List[Dict[str, Any]] = field(default_factory=list)
    budget_split: List[float] = field(default_factory=list)
    itinerary: str = ""
    review_score: float = 0.0
    reviewer_notes: str = ""
    reasoning: List[Dict[str, Any]] = field(default_factory=list)

# ============================================================================
# A2A Communication Types
# ============================================================================

class Task(BaseModel):
    """Task definition for agent-to-agent communication."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    agent: str
    input: Dict[str, Any]
    priority: int = 1
    created_at: datetime = field(default_factory=datetime.now)

class Assignment(BaseModel):
    """Task assignment to an agent."""
    task_id: str
    agent: str
    assigned_at: datetime = field(default_factory=datetime.now)
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))

class Result(BaseModel):
    """Result from agent task execution."""
    task_id: str
    agent: str
    output: Dict[str, Any]
    success: bool
    execution_time: float
    completed_at: datetime = field(default_factory=datetime.now)
    correlation_id: str

# ============================================================================
# LLM Integration Types
# ============================================================================

class PlanStep(BaseModel):
    """Single step in a workflow plan."""
    name: Literal["check_weather", "scout_venues", "split_budget", "write_itinerary", "review"]
    rationale: str

class RoutingPlan(BaseModel):
    """Complete workflow routing plan from LLM."""
    steps: List[PlanStep]

class ItineraryJSON(BaseModel):
    """Structured itinerary from LLM."""
    title: str
    stops: List[str]
    summary: str

# ============================================================================
# Reasoning Types
# ============================================================================

@dataclass
class WhyBasic:
    """Basic reasoning for any agent decision."""
    agent: str
    decision: str
    criteria: List[str]
    evidence: List[str]
    confidence: float
    next_action: Optional[str] = None

@dataclass
class WhyPlanner(WhyBasic):
    """Extended reasoning for planner agent."""
    llm_used: bool = False
    fallback_reason: Optional[str] = None
    workflow_complexity: str = "medium"
    optimization_potential: str = "moderate"

# ============================================================================
# Tool Response Types
# ============================================================================

class WeatherData(BaseModel):
    """Weather information from weather tool."""
    precip_prob: float
    condition: str
    indoor_required: bool
    source: str = "api"

class VenueInfo(BaseModel):
    """Venue information from venue tool."""
    name: str
    neighborhood: str
    tags: List[str]
    avg_price: float
    outdoor: bool
    indoor_compliant: bool

class BudgetSplit(BaseModel):
    """Budget allocation result."""
    per_stop: List[float]
    per_person_total: float
    buffer_pct: float = 0.1

# ============================================================================
# Constants
# ============================================================================

DEFAULT_ORDER = ["check_weather", "scout_venues", "split_budget", "write_itinerary", "review"]
ALLOWED_STEPS = set(DEFAULT_ORDER)

# ============================================================================
# Utility Functions
# ============================================================================

def add_reasoning(state: FoodieState, reasoning: WhyBasic) -> None:
    """Add reasoning to state with consistent structure."""
    state.reasoning.append({
        "agent": reasoning.agent,
        "decision": reasoning.decision,
        "criteria": reasoning.criteria,
        "evidence": reasoning.evidence,
        "confidence": reasoning.confidence,
        "next_action": reasoning.next_action,
        "timestamp": datetime.now().isoformat()
    })

def create_correlation_id() -> str:
    """Create a unique correlation ID for tracing."""
    return str(uuid.uuid4())
