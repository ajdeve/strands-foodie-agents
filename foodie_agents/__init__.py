"""Foodie Agents - Multi-agent AI system for food tour planning."""

__version__ = "0.1.0"
__author__ = "Foodie Agents Team"

from .strands_agents import (
    FoodieState, PlannerLLMAgent, ResearcherAgent, ScoutAgent, 
    WriterAgent, ReviewerAgent
)
from .types import WhyBasic, WhyPlanner, Task, Assignment, Result
from .tools import get_weather, filter_venues, call_budget_service
from .config import get_config, get_langfuse_config, get_ollama_config

__all__ = [
    "FoodieState",
    "PlannerLLMAgent", 
    "ResearcherAgent",
    "ScoutAgent",
    "WriterAgent",
    "ReviewerAgent",
    "WhyBasic",
    "WhyPlanner", 
    "Task",
    "Assignment",
    "Result",
    "get_weather",
    "filter_venues", 
    "call_budget_service",
    "get_config",
    "get_langfuse_config",
    "get_ollama_config"
]
