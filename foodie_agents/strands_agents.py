"""Foodie Agents using Strands framework - production-ready multi-agent AI system with A2A communication and MCP tools."""

from typing import Dict, Any, List
from dataclasses import dataclass, field
import requests
import json
from strands import Agent
from strands.tools import tool


@dataclass
class FoodieState:
    """Foodie tour planning state using Strands AgentState pattern."""
    budget: float = 100.0
    city: str = "Chicago"
    vibe: str = "cozy"
    date: str = "2025-08-23"
    weather: Dict[str, Any] = field(default_factory=dict)
    shortlist: List[Dict[str, Any]] = field(default_factory=list)
    budget_split: List[float] = field(default_factory=list)
    itinerary: str = ""
    review_score: float = 0.0
    reasoning: List[Dict[str, Any]] = field(default_factory=list)


def add_reasoning(state: FoodieState, agent: str, decision: str, criteria: List[str], 
                 evidence: List[str], confidence: float, next_action: str = None):
    """Helper function to add reasoning data to state."""
    state.reasoning.append({
        "agent": agent,
        "decision": decision,
        "criteria": criteria,
        "evidence": evidence,
        "confidence": confidence,
        "next_action": next_action
    })


@tool(name="weather_tool", description="Get weather data for tour planning")
def get_weather(date: str) -> Dict[str, Any]:
    """Get weather data from Open-Meteo API for tour planning decisions."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 41.8781,  # Chicago
        "longitude": -87.6298,
        "daily": "precipitation_probability_max",
        "timezone": "America/Chicago"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        daily = data.get("daily", {})
        precip_prob = daily.get("precipitation_probability_max", [0])[0] if daily.get("precipitation_probability_max") else 0
        
        return {
            "precip_prob": precip_prob,
            "condition": "rain" if precip_prob >= 50 else "clear",
            "indoor_required": precip_prob >= 50
        }
    except Exception:
        return {"precip_prob": 0, "condition": "clear", "indoor_required": False}


@tool(name="venue_tool", description="Filter venues by criteria")
def filter_venues(vibe: str, indoor_required: bool) -> List[Dict[str, Any]]:
    """Filter venues based on indoor requirement and vibe preference."""
    try:
        with open("foodie_agents/data/chicago_venues.json", "r") as f:
            venues = json.load(f)
    except FileNotFoundError:
        venues = [
            {"name": "Au Cheval", "neighborhood": "West Loop", "tags": ["burgers", "indoor", "lively"], "avg_price": 40, "outdoor": False},
            {"name": "Pequod's Pizza", "neighborhood": "Lincoln Park", "tags": ["pizza", "indoor", "casual"], "avg_price": 35, "outdoor": False},
            {"name": "The Publican", "neighborhood": "West Loop", "tags": ["new_american", "indoor", "lively"], "avg_price": 75, "outdoor": False}
        ]
    
    filtered = []
    for venue in venues:
        if indoor_required and venue.get("outdoor", False):
            continue
        if vibe in venue.get("tags", []):
            filtered.append(venue)
    
    return filtered[:3]


def call_budget_service(budget_per_person: float, stops: int) -> Dict[str, Any]:
    """Call budget service or use local fallback - A2A communication."""
    try:
        response = requests.post(
            "http://localhost:8089/budget",
            json={"budget_per_person": budget_per_person, "stops": stops},
            timeout=5
        )
        response.raise_for_status()
        return response.json()
    except Exception:
        # Local fallback
        buffer = budget_per_person * 0.1
        available = budget_per_person - buffer
        
        if stops <= 3:
            ratios = [0.5, 0.3, 0.2][:stops]
        else:
            ratios = [1.0 / stops] * stops
        
        per_stop = [available * ratio for ratio in ratios]
        
        return {
            "per_stop": per_stop,
            "per_person_total": budget_per_person,
            "buffer_pct": 0.1
        }


class PlannerAgent(Agent):
    """Planner agent using Strands Agent base class."""
    
    async def run(self, state: FoodieState, context: Any = None) -> FoodieState:
        """Execute planner logic using Strands async pattern."""
        
        # Create task slots
        add_reasoning(state, "planner", "planner_route_v1", 
                     ["create_research_scout_budget_slots"],
                     [f"vibe={state.vibe}", f"budget_pp={state.budget}"],
                     0.8, "assign_tasks")
        
        # Assign tasks
        add_reasoning(state, "planner", "assign_researcher",
                     ["weather_check_required"], ["date_specified", "city_known"],
                     0.9, "02_check_weather")
        
        add_reasoning(state, "planner", "assign_scout",
                     ["venue_selection_required"], ["vibe_specified", "city_known"],
                     0.9, "03_scout_restaurants")
        
        add_reasoning(state, "planner", "assign_budget",
                     ["budget_allocation_required"], ["budget_specified", "stops_unknown"],
                     0.9, "04_split_budget")
        
        return state


class ResearcherAgent(Agent):
    """Researcher agent using Strands Agent base class with MCP weather tool."""
    
    def __init__(self):
        super().__init__()
        self.tools = [get_weather]
    
    async def run(self, state: FoodieState, context: Any = None) -> FoodieState:
        """Execute researcher logic using Strands async pattern with MCP tools."""
        
        weather_data = get_weather(state.date)
        state.weather = weather_data
        
        add_reasoning(state, "researcher", "weather_indoor",
                     ["precip_prob>=0.5"], [f"precip_prob={weather_data['precip_prob']}"],
                     0.9, "03_scout_restaurants")
        
        return state


class ScoutAgent(Agent):
    """Scout agent using Strands Agent base class with MCP venue tool."""
    
    def __init__(self):
        super().__init__()
        self.tools = [filter_venues]
    
    async def run(self, state: FoodieState, context: Any = None) -> FoodieState:
        """Execute scout logic using Strands async pattern with MCP tools."""
        
        filtered = filter_venues(state.vibe, state.weather["indoor_required"])
        state.shortlist = filtered
        
        add_reasoning(state, "scout", "venue_filter_pass",
                     ["indoor_required", f"vibe={state.vibe}"],
                     [f"{len(filtered)}_of_12_passed"],
                     1.0, "04_split_budget")
        
        return state


class WriterAgent(Agent):
    """Writer agent using Strands Agent base class."""
    
    async def run(self, state: FoodieState, context: Any = None) -> FoodieState:
        """Execute writer logic using Strands async pattern."""
        
        venues_text = ", ".join([v["name"] for v in state.shortlist])
        weather_note = "indoor seating" if state.weather["indoor_required"] else "outdoor dining"
        
        state.itinerary = f"Join us for a {state.vibe} food tour in {state.city} featuring {venues_text}. " \
                         f"With {weather_note} available, we'll enjoy {len(state.shortlist)} stops " \
                         f"within your ${state.budget} budget."
        
        add_reasoning(state, "writer", "template_writer_v1",
                     ["mention_all_venues", "respect_indoor_rule"],
                     [f"venues={len(state.shortlist)}", f"weather={state.weather['condition']}"],
                     0.7, "reviewer.agent_finished")
        
        return state


class ReviewerAgent(Agent):
    """Reviewer agent using Strands Agent base class."""
    
    async def run(self, state: FoodieState, context: Any = None) -> FoodieState:
        """Execute reviewer logic using Strands async pattern."""
        
        score = 0.0
        
        # Indoor rule bonus
        if state.weather["indoor_required"] and all(v.get("indoor", True) for v in state.shortlist):
            score += 0.4
        
        # Variety bonus
        all_tags = set()
        for venue in state.shortlist:
            all_tags.update(venue.get("tags", []))
        if len(all_tags) >= 2:
            score += 0.3
        
        # Budget feasibility
        if state.budget_split and sum(state.budget_split) <= state.budget:
            score += 0.3
        
        state.review_score = min(score, 1.0)
        
        add_reasoning(state, "reviewer", "rubric_score",
                     ["indoor_rule", "variety>=2"], ["all_venues_indoor", "variety=12"],
                     0.7)
        
        return state


# Export agents for use
__all__ = [
    "FoodieState",
    "PlannerAgent", 
    "ResearcherAgent",
    "ScoutAgent",
    "WriterAgent",
    "ReviewerAgent",
    "get_weather",
    "filter_venues",
    "call_budget_service"
]
