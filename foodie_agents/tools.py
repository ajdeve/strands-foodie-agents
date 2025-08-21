"""MCP tool adapters for Foodie Agents system."""

import json
import requests
import importlib.resources as ir
from typing import Dict, Any, List
from strands.tools import tool
from foodie_agents.types import WeatherData, VenueInfo, BudgetSplit

# ============================================================================
# Weather Tool
# ============================================================================

@tool(name="weather_tool", description="Get weather data for tour planning")
def get_weather(date: str) -> Dict[str, Any]:
    """Date-aware weather from Open-Meteo; returns precip probability and indoor rule."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 41.8781,         # Chicago
        "longitude": -87.6298,
        "daily": "precipitation_probability_max",
        "start_date": date,
        "end_date": date,
        "timezone": "America/Chicago"
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json() or {}
        daily = data.get("daily") or {}
        probs = daily.get("precipitation_probability_max") or []
        precip_prob = probs[0] if probs else 0
        indoor_required = precip_prob >= 50
        
        weather_data = WeatherData(
            precip_prob=precip_prob,
            condition="rain" if indoor_required else "clear",
            indoor_required=indoor_required,
            source="api"
        )
        
        return weather_data.model_dump()
    except Exception:
        fallback_data = WeatherData(
            precip_prob=0,
            condition="clear",
            indoor_required=False,
            source="fallback"
        )
        return fallback_data.model_dump()

# ============================================================================
# Venue Tool
# ============================================================================

@tool(name="venue_tool", description="Filter venues by criteria")
def filter_venues(vibe: str, indoor_required: bool) -> List[Dict[str, Any]]:
    """Load venues from packaged data (with fallback). Enforce vibe & indoor rules; return top 3 cheapest."""
    try:
        with ir.files("foodie_agents.data").joinpath("chicago_venues.json").open("r", encoding="utf-8") as f:
            venues = json.load(f)
    except Exception:
        venues = [
            {"name": "Au Cheval", "neighborhood": "West Loop", "tags": ["burgers", "indoor", "lively"], "avg_price": 40, "outdoor": False},
            {"name": "Pequod's Pizza", "neighborhood": "Lincoln Park", "tags": ["pizza", "indoor", "casual"], "avg_price": 35, "outdoor": False},
            {"name": "The Publican", "neighborhood": "West Loop", "tags": ["new_american", "indoor", "lively"], "avg_price": 75, "outdoor": False}
        ]

    vibe_lc = (vibe or "").lower()

    def is_indoor(v: Dict[str, Any]) -> bool:
        tags = [t.lower() for t in v.get("tags", [])]
        return ("indoor" in tags) or (not v.get("outdoor", False))

    filtered = []
    for v in venues:
        if indoor_required and not is_indoor(v):
            continue
        
        # Vibe matching (simple tag-based)
        venue_tags = [t.lower() for t in v.get("tags", [])]
        if vibe_lc and not any(vibe_lc in tag for tag in venue_tags):
            continue
            
        filtered.append(v)
    
    # Sort by price and return top 3
    filtered.sort(key=lambda x: x.get("avg_price", 999))
    return filtered[:3]

# ============================================================================
# Budget Tool
# ============================================================================

@tool(name="budget_tool", description="Split budget across restaurant stops")
def split_budget(total_budget: float, stops: int) -> Dict[str, Any]:
    """Split budget across stops with 10% buffer and smart allocation."""
    # Apply 10% buffer
    buffer_amount = total_budget * 0.1
    available_budget = total_budget - buffer_amount
    
    if stops <= 3:
        # Use weighted split: [0.5, 0.3, 0.2] for up to 3 stops
        weights = [0.5, 0.3, 0.2][:stops]
        # Normalize weights to sum to 1
        total_weight = sum(weights)
        weights = [w / total_weight for w in weights]
        
        per_stop = [round(available_budget * weight, 2) for weight in weights]
    else:
        # Even split for more than 3 stops
        per_stop = [round(available_budget / stops, 2)] * stops
    
    budget_split = BudgetSplit(
        per_stop=per_stop,
        per_person_total=total_budget,
        buffer_pct=0.1
    )
    
    return budget_split.model_dump()

# ============================================================================
# External Service Integration
# ============================================================================

def call_budget_service(budget: float, stops: int) -> Dict[str, Any]:
    """Call external budget service with fallback to local tool."""
    from foodie_agents.config import get_budget_service_config
    
    config = get_budget_service_config()
    try:
        # Try external service first
        response = requests.post(
            f"{config.url}/split_budget",
            json={"budget_per_person": budget, "stops": stops},
            timeout=config.timeout
        )
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    
    # Fallback to local tool
    return split_budget(budget, stops)
