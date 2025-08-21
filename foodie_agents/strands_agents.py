"""Foodie Agents using Strands framework — multi-agent system with LLM (Ollama) for planner/writer/reviewer."""

import time
from typing import Dict, Any, List
from strands import Agent
from strands.tools import tool

from foodie_agents.types import (
    FoodieState, WhyBasic, WhyPlanner, RoutingPlan, ItineraryJSON,
    DEFAULT_ORDER, ALLOWED_STEPS, add_reasoning, create_correlation_id
)
from foodie_agents.tools import get_weather, filter_venues, call_budget_service
from foodie_agents.llm_client import structured_json, simple_text, LLMError
from foodie_agents.prompts import WRITER_SYSTEM, REVIEWER_SYSTEM, PLANNER_SYSTEM
from foodie_agents.langfuse_integration import (
    start_agent_execution, add_agent_reasoning, end_agent_execution,
    add_planner_llm_status, add_planner_llm_routing_reasoning
)

# ============================================================================
# Core Agent Classes
# ============================================================================

class ResearcherAgent(Agent):
    """Deterministic weather fetch via MCP tool."""
    
    def __init__(self):
        super().__init__()
        self.tools = [get_weather]
    
    async def run(self, state: FoodieState, context: Any = None) -> FoodieState:
        start_time = time.time()
        
        # Start agent execution tracing
        span_id = start_agent_execution("researcher", "check_weather", {"date": state.date})
        
        # Get weather data via MCP tool
        weather_data = get_weather(state.date)
        state.weather = weather_data
        
        execution_time = time.time() - start_time
        
        # Add reasoning with new type system
        reasoning = WhyBasic(
            agent="researcher",
            decision="weather_indoor",
            criteria=["precip_prob>=0.5"],
            evidence=[f"precip_prob={state.weather.get('precip_prob', 0)}"],
            confidence=0.9,
            next_action="03_scout_restaurants"
        )
        add_reasoning(state, reasoning)
        
        # Add reasoning to trace
        add_agent_reasoning(
            span_id, "researcher", "check_weather",
            f"Determined indoor requirement: {state.weather.get('indoor_required')}",
            weather_data
        )
        
        # End agent execution tracing
        end_agent_execution(span_id, weather_data, execution_time)
        
        return state

class ScoutAgent(Agent):
    """Deterministic venue filtering via MCP tool."""
    
    def __init__(self):
        super().__init__()
        self.tools = [filter_venues]
    
    async def run(self, state: FoodieState, context: Any = None) -> FoodieState:
        start_time = time.time()
        
        # Start agent execution tracing
        span_id = start_agent_execution("scout", "scout_venues", {"vibe": state.vibe, "indoor_required": state.weather.get("indoor_required")})
        
        # Get indoor requirement from weather
        indoor_required = bool(state.weather.get("indoor_required"))
        
        # Filter venues via MCP tool
        filtered = filter_venues(state.vibe, indoor_required)
        state.shortlist = filtered
        
        execution_time = time.time() - start_time
        
        # Add reasoning
        reasoning = WhyBasic(
            agent="scout",
            decision="venue_filter_pass",
            criteria=["indoor_required", f"vibe={state.vibe}"],
            evidence=[f"count={len(filtered)}", f"indoor_compliant={indoor_required}"],
            confidence=0.9,
            next_action="04_split_budget"
        )
        add_reasoning(state, reasoning)
        
        # Add reasoning to trace
        add_agent_reasoning(
            span_id, "scout", "scout_venues",
            f"Selected {len(filtered)} venues matching vibe and indoor requirements",
            {"venues": filtered, "count": len(filtered)}
        )
        
        # End agent execution tracing
        end_agent_execution(span_id, {"venues": filtered, "count": len(filtered)}, execution_time)
        
        return state

class BudgetAgent(Agent):
    """Deterministic budget split via microservice (with fallback)."""
    
    async def run(self, state: FoodieState, context: Any = None) -> FoodieState:
        start_time = time.time()
        
        # Start agent execution tracing
        span_id = start_agent_execution("budget", "split_budget", {"budget": state.budget, "stops": len(state.shortlist)})
        
        # Calculate stops from shortlist
        stops = max(1, len(state.shortlist))
        
        # Call budget service via MCP tool
        result = call_budget_service(float(state.budget), stops)
        state.budget_split = result.get("per_stop", [])
        
        execution_time = time.time() - start_time
        
        # Add reasoning
        reasoning = WhyBasic(
            agent="budget",
            decision="split_computed",
            criteria=["buffer=10%", f"stops={stops}"],
            evidence=[f"per_stop={state.budget_split}"],
            confidence=0.9,
            next_action="05_write_itinerary"
        )
        add_reasoning(state, reasoning)
        
        # Add reasoning to trace
        add_agent_reasoning(
            span_id, "budget", "split_budget",
            f"Split ${state.budget} across {stops} stops with 10% buffer",
            result
        )
        
        # End agent execution tracing
        end_agent_execution(span_id, result, execution_time)
        
        return state

class WriterAgent(Agent):
    """LLM (Ollama) creates itinerary JSON; fallback to template if JSON invalid/unavailable."""
    
    async def run(self, state: FoodieState, context: Any = None) -> FoodieState:
        start_time = time.time()
        
        # Start agent execution tracing
        span_id = start_agent_execution("writer", "write_itinerary", {"vibe": state.vibe, "budget": state.budget, "venues": len(state.shortlist)})
        
        # Get indoor requirement from weather
        indoor_required = bool(state.weather.get("indoor_required"))
        
        # Prepare user prompt for LLM
        user_prompt = (
            f"City: {state.city}\n"
            f"Vibe: {state.vibe}\n"
            f"Budget (total): {state.budget}\n"
            f"Indoor required: {indoor_required}\n"
            f"Weather: {state.weather}\n"
            f"Shortlist: {state.shortlist}\n"
            f"Budget split: {state.budget_split}\n\n"
            f"Create a food tour itinerary. Return ONLY valid JSON matching this schema:\n"
            f'{{"title": "string", "stops": ["venue1", "venue2"], "summary": "string"}}'
        )
        
        try:
            # Try LLM generation first
            js = structured_json(ItineraryJSON, WRITER_SYSTEM, user_prompt)
            state.itinerary = f"{js.title}: {', '.join(js.stops)} — {js.summary}"
            method = "llm"
            
            reasoning = WhyBasic(
                agent="writer",
                decision="llm_itinerary_v1",
                criteria=["mention_all_venues_if_possible", "respect_indoor_rule"],
                evidence=[f"llm_success=true", f"title={js.title}"],
                confidence=0.85,
                next_action="06_review_plan"
            )
        except Exception as e:
            # Fallback to template
            state.itinerary = (
                f"Join us for a {state.vibe} food tour in {state.city} featuring "
                f"{', '.join(v['name'] for v in state.shortlist[:2])}. "
                f"With {'indoor' if indoor_required else 'outdoor'} seating available, "
                f"we'll enjoy {len(state.shortlist)} stops within your ${state.budget} budget."
            )
            method = "template"
            
            reasoning = WhyBasic(
                agent="writer",
                decision="template_fallback",
                criteria=["llm_unavailable", "basic_coverage"],
                evidence=[f"fallback_reason={str(e)}", f"template_generated=true"],
                confidence=0.7,
                next_action="06_review_plan"
            )
        
        add_reasoning(state, reasoning)
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        # Add reasoning to trace
        add_agent_reasoning(
            span_id, "writer", "write_itinerary",
            f"Generated itinerary using {method}: {state.itinerary[:100]}...",
            {"itinerary": state.itinerary, "method": method}
        )
        
        # End agent execution tracing
        end_agent_execution(span_id, {"itinerary": state.itinerary, "method": method}, execution_time)
        
        return state

class ReviewerAgent(Agent):
    """Deterministic scoring with optional LLM rationale."""
    
    async def run(self, state: FoodieState, context: Any = None) -> FoodieState:
        start_time = time.time()
        
        # Start agent execution tracing
        span_id = start_agent_execution("reviewer", "review", {"score_criteria": ["indoor_compliance", "variety", "budget_efficiency"]})
        
        # Calculate deterministic score
        score = 0.0
        indoor_required = bool(state.weather.get("indoor_required"))
        
        # Indoor rule compliance
        if indoor_required and all(not v.get("outdoor", False) for v in state.shortlist):
            score += 0.4
        
        # Variety assessment
        all_tags = {t for v in state.shortlist for t in v.get("tags", []) if t not in {"indoor","outdoor"}}
        if len(all_tags) >= 3:
            score += 0.3
        elif len(all_tags) >= 2:
            score += 0.2
        
        # Budget efficiency
        if state.budget_split and sum(state.budget_split) <= state.budget:
            score += 0.3
        
        state.review_score = min(score, 1.0)
        
        # Try LLM for rationale
        try:
            rationale = simple_text(
                REVIEWER_SYSTEM,
                (
                    f"Shortlist={state.shortlist}\n"
                    f"Budget split={state.budget_split}\n"
                    f"Score={state.review_score}\n"
                    f"Explain why this score in 2-3 bullet points."
                )
            )
            if rationale:
                state.reviewer_notes = rationale
            else:
                state.reviewer_notes = "Score calculated based on indoor compliance, variety, and budget efficiency."
        except Exception:
            state.reviewer_notes = "Score calculated based on indoor compliance, variety, and budget efficiency."
        
        execution_time = time.time() - start_time
        
        # Add reasoning
        reasoning = WhyBasic(
            agent="reviewer",
            decision="rubric_score",
            criteria=["indoor_compliance", "variety_assessment", "budget_efficiency"],
            evidence=[f"final_score={state.review_score}", f"rationale_generated=true"],
            confidence=0.9,
            next_action=None
        )
        add_reasoning(state, reasoning)
        
        # Add reasoning to trace
        add_agent_reasoning(
            span_id, "reviewer", "review",
            f"Scored plan {state.review_score}/1.0 based on {len(state.reviewer_notes)} criteria",
            {"score": state.review_score, "notes": state.reviewer_notes}
        )
        
        # End agent execution tracing
        end_agent_execution(span_id, {"score": state.review_score, "notes": state.reviewer_notes}, execution_time)
        
        return state

class PlannerLLMAgent(Agent):
    """Planner asks LLM for an ordered plan, validates/normalizes it, then executes sub-agents."""
    
    async def run(self, state: FoodieState, context: Any = None, planner_span_id: str = None) -> FoodieState:
        start_time = time.time()
        
        # Prepare user prompt for LLM
        user_prompt = (
            f"Inputs: city={state.city}, vibe={state.vibe}, date={state.date}, budget={state.budget}.\n"
            "Return JSON: {\"steps\":[{\"name\":\"check_weather|scout_venues|split_budget|write_itinerary|review\","
            "\"rationale\":\"why this step now\"}]}\n"
            "Keep the plan concise (3–5 steps)."
        )
        
        # Track decisions for reasoning
        decisions = []
        llm_used = False
        fallback_reason = None
        original_plan = None
        llm_rationales = []
        business_rules_applied = []
        
        try:
            # Try LLM planning
            plan = structured_json(RoutingPlan, PLANNER_SYSTEM, user_prompt)
            llm_used = True
            original_plan = {"steps": [{"name": s.name, "rationale": s.rationale} for s in plan.steps]}
            llm_rationales = [s.rationale for s in plan.steps]
            
            # Extract steps and rationales
            steps = [s.name for s in plan.steps if s.name in ALLOWED_STEPS]
            
            # Add LLM decision to reasoning
            decisions.append({
                "decision": "llm_plan_received",
                "criteria": ["llm_rationales", "step_validation"],
                "evidence": [f"{s.name}: {s.rationale}" for s in plan.steps if s.name in ALLOWED_STEPS],
                "confidence": 0.9,
                "next_action": "validate_and_normalize"
            })
            
            # Dedupe preserve order
            seen = set()
            steps = [s for s in steps if not (s in seen or seen.add(s))]
            
            # Track business rules applied
            if "check_weather" not in steps:
                steps.insert(0, "check_weather")
                business_rules_applied.append("weather_first_rule: Added check_weather as first step")
            
            if "review" in steps:
                steps = [s for s in steps if s != "review"] + ["review"]
                business_rules_applied.append("review_last_rule: Moved review to end")
            else:
                steps.append("review")
                business_rules_applied.append("review_last_rule: Added review as final step")
            
            # Ensure other defaults exist in reasonable order
            for s in DEFAULT_ORDER:
                if s not in steps:
                    insert_at = min(len(steps), DEFAULT_ORDER.index(s))
                    if s == "write_itinerary" and "split_budget" in steps:
                        insert_at = max(insert_at, steps.index("split_budget") + 1)
                        business_rules_applied.append(f"dependency_rule: write_itinerary after split_budget")
                    steps.insert(insert_at, s)
                    business_rules_applied.append(f"default_step_rule: Added missing step {s}")
            
            # Add normalization decision
            decisions.append({
                "decision": "llm_plan_normalized",
                "criteria": ["step_validation", "ordering_rules"],
                "evidence": [f"final_order: {', '.join(steps)}"],
                "confidence": 0.85,
                "next_action": "begin_execution"
            })
            
        except Exception as e:
            # Fallback to default order
            steps = DEFAULT_ORDER[:]
            fallback_reason = str(e)
            business_rules_applied.append(f"fallback_rule: Using DEFAULT_ORDER due to LLM error: {str(e)}")
            
            decisions.append({
                "decision": "llm_plan_fallback",
                "criteria": ["validation_error"],
                "evidence": [str(e)],
                "confidence": 0.3,
                "next_action": "deterministic_flow"
            })
        
        # Add final execution decision
        decisions.append({
            "decision": "execute_workflow",
            "criteria": ["ordered_steps"],
            "evidence": [", ".join(steps)],
            "confidence": 0.9,
            "next_action": "begin_execution"
        })
        
        # Add all decisions to reasoning
        for decision in decisions:
            reasoning = WhyPlanner(
                agent="planner",
                decision=decision["decision"],
                criteria=decision["criteria"],
                evidence=decision["evidence"],
                confidence=decision["confidence"],
                next_action=decision["next_action"],
                llm_used=llm_used,
                fallback_reason=fallback_reason
            )
            add_reasoning(state, reasoning)
        
        # Add LLM status to trace
        if planner_span_id:
            add_planner_llm_status(planner_span_id, llm_used, fallback_reason)
            
            # Add detailed LLM routing reasoning if we have the data
            if original_plan and llm_rationales:
                normalized_plan = {"steps": steps}
                add_planner_llm_routing_reasoning(
                    planner_span_id, 
                    original_plan, 
                    normalized_plan, 
                    llm_rationales, 
                    business_rules_applied
                )
        
        # Execute sub-agents by step
        step_map = {
            "check_weather":  ResearcherAgent(),
            "scout_venues":   ScoutAgent(),
            "split_budget":   BudgetAgent(),
            "write_itinerary": WriterAgent(),
            "review":         ReviewerAgent(),
        }
        
        for step in steps:
            # Add step execution reasoning
            step_reasoning = WhyBasic(
                agent="planner",
                decision="execute_step",
                criteria=[step],
                evidence=["from_llm_plan"],
                confidence=0.9,
                next_action=f"do:{step}"
            )
            add_reasoning(state, step_reasoning)
            
            # Execute the agent
            state = await step_map[step].run(state)
        
        execution_time = time.time() - start_time
        return state

# ============================================================================
# Public Exports
# ============================================================================

__all__ = [
    "FoodieState",
    "PlannerLLMAgent",
    "ResearcherAgent", 
    "ScoutAgent",
    "BudgetAgent",
    "WriterAgent",
    "ReviewerAgent",
    "add_reasoning",
    "create_correlation_id"
]
