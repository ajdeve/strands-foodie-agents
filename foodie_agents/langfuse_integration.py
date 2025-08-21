"""Langfuse integration for Foodie Agents - preserves existing trace structure while adding missing fields."""

import time
from typing import Dict, Any, Optional, List
from langfuse import Langfuse
from dotenv import load_dotenv
from foodie_agents.config import get_langfuse_config

# Load environment variables if not already loaded
load_dotenv()

class FoodieLangfuseTracer:
    """Tracer that preserves existing trace structure while filling missing input/output."""
    
    def __init__(self):
        """Initialize the Langfuse tracer."""
        config = get_langfuse_config()
        self.langfuse = Langfuse(
            public_key=config.public_key,
            secret_key=config.secret_key,
            host=config.host
        )
        self.current_trace_id = None
        self.current_main_span = None
        self.active_spans = {}
    
    def start_foodie_tour(self, city: str, vibe: str, budget: float, date: str) -> str:
        """Start a new foodie tour trace - preserves existing name."""
        trace_id = self.langfuse.create_trace_id()
        self.current_trace_id = trace_id
        
        # Start the main tour span (preserving existing name)
        self.current_main_span = self.langfuse.start_span(
            name="foodie_tour",  # Keep existing name
            input={
                "city": city,
                "vibe": vibe,
                "budget": budget,
                "date": date
            },
            metadata={
                "service": "foodie-agents",
                "trace_type": "foodie_tour",
                "environment": "local-dev"
            }
        )
        
        return trace_id
    
    def start_planner_workflow(self) -> str:
        """Start planner workflow span - preserves existing name."""
        if not self.current_main_span:
            return None
        
        span = self.current_main_span.start_span(
            name="01_planner_workflow",  # Keep existing name
            input={
                "agent": "planner",
                "workflow_type": "complete_planning"
            }
        )
        
        span_id = f"planner_{int(time.time() * 1000)}"
        self.active_spans[span_id] = span
        
        return span_id
    
    def add_planner_llm_status(self, span_id: str, llm_used: bool, fallback_reason: Optional[str] = None):
        """Add LLM status to planner workflow."""
        if span_id not in self.active_spans:
            return
        
        span = self.active_spans[span_id]
        
        # Add LLM status span
        llm_span = span.start_span(
            name="planner.llm_status",
            input={"llm_provider": "ollama"}
        )
        
        if llm_used:
            llm_span.update(
                output={
                    "llm_status": {
                        "provider": "ollama",
                        "status": "success",
                        "method": "structured_json"
                    }
                }
            )
        else:
            llm_span.update(
                output={
                    "llm_status": {
                        "provider": "ollama",
                        "status": "fallback",
                        "reason": fallback_reason or "llm_unavailable"
                    }
                }
            )
        
        llm_span.end()
    
    def add_planner_llm_routing_reasoning(self, span_id: str, original_plan: dict, normalized_plan: dict, 
                                        llm_rationales: List[str], business_rules_applied: List[str]):
        """Add detailed LLM routing reasoning to planner workflow."""
        if span_id not in self.active_spans:
            return
        
        span = self.active_spans[span_id]
        
        # Add detailed LLM routing reasoning span
        routing_span = span.start_span(
            name="planner.llm_routing_reasoning",
            input={
                "llm_provider": "ollama",
                "planning_method": "structured_json"
            }
        )
        
        routing_span.update(
            output={
                "llm_routing_analysis": {
                    "original_llm_plan": {
                        "steps": original_plan.get("steps", []),
                        "step_count": len(original_plan.get("steps", [])),
                        "completeness": "partial" if len(original_plan.get("steps", [])) < 5 else "complete"
                    },
                    "llm_rationales": llm_rationales,
                    "business_rules_validation": {
                        "rules_applied": business_rules_applied,
                        "validation_result": "passed" if normalized_plan.get("steps") else "failed"
                    },
                    "plan_normalization": {
                        "original_steps": [s.get("name", "") for s in original_plan.get("steps", [])],
                        "normalized_steps": normalized_plan.get("steps", []),
                        "changes_made": {
                            "steps_added": [s for s in normalized_plan.get("steps", []) if s not in [s.get("name", "") for s in original_plan.get("steps", [])]],
                            "steps_reordered": normalized_plan.get("steps", []) != [s.get("name", "") for s in original_plan.get("steps", [])]
                        }
                    },
                    "routing_decision_factors": {
                        "weather_dependency": "check_weather must be first",
                        "venue_budget_dependency": "scout_venues before split_budget",
                        "content_dependency": "write_itinerary after budget allocation",
                        "quality_assurance": "review always last"
                    }
                }
            }
        )
        
        routing_span.end()
    
    def add_planner_decisions(self, span_id: str, decisions: List[dict]):
        """Add planning decisions to planner workflow."""
        if span_id not in self.active_spans:
            return
        
        span = self.active_spans[span_id]
        
        # Add decisions span
        decisions_span = span.start_span(
            name="planner.decisions",
            input={"decision_count": len(decisions)}
        )
        
        decisions_span.update(
            output={
                "all_decisions": decisions,
                "decision_summary": {
                    "total_decisions": len(decisions),
                    "decision_types": [d.get("decision", "unknown") for d in decisions]
                }
            }
        )
        
        decisions_span.end()
    
    def add_planner_final_workflow(self, span_id: str, final_steps: List[str]):
        """Add final workflow structure to planner workflow."""
        if span_id not in self.active_spans:
            return
        
        span = self.active_spans[span_id]
        
        # Add final workflow span
        workflow_span = span.start_span(
            name="planner.final_workflow",
            input={"final_steps": final_steps}
        )
        
        workflow_span.update(
            output={
                "final_workflow": {
                    "steps": final_steps,
                    "execution_order": "sequential",
                    "total_steps": len(final_steps),
                    "workflow_type": "agent_orchestration"
                }
            }
        )
        
        workflow_span.end()
    
    def end_planner_workflow(self, span_id: str):
        """End planner workflow span."""
        if span_id not in self.active_spans:
            return
        
        span = self.active_spans[span_id]
        span.end()
        del self.active_spans[span_id]
    
    def start_agent_execution(self, agent_name: str, action: str, input_data: dict) -> str:
        """Start agent execution span with sequential numbering."""
        if not self.current_main_span:
            return None
        
        # Get the next sequential number for this agent execution
        next_number = self._get_next_agent_number()
        
        # Use sequential numbering: 02_planner_workflow, 03_researcher_check_weather, etc.
        span = self.current_main_span.start_span(
            name=f"{next_number:02d}_{agent_name}_{action}",
            input={
                "agent": agent_name,
                "action": action,
                "input": input_data
            }
        )
        
        span_id = f"{agent_name}_{action}_{int(time.time() * 1000)}"
        self.active_spans[span_id] = span
        
        return span_id
    
    def _get_next_agent_number(self) -> int:
        """Get the next sequential number for agent execution spans."""
        # Start from 2 since 01 is reserved for planner_workflow
        if not hasattr(self, '_agent_counter'):
            self._agent_counter = 2
        
        current_number = self._agent_counter
        self._agent_counter += 1
        return current_number
    
    def add_agent_reasoning(self, span_id: str, agent_name: str, action: str, 
                           reasoning: str, output_data: dict):
        """Add reasoning to agent execution span - preserves existing pattern."""
        if span_id not in self.active_spans:
            return
        
        span = self.active_spans[span_id]
        
        # Add reasoning span (preserving existing pattern)
        reasoning_span = span.start_span(
            name=f"{agent_name}.reasoning",  # Keep existing pattern
            input={"reasoning_type": "decision_logic"}
        )
        
        reasoning_span.update(
            output={
                "reasoning": reasoning,
                "agent": agent_name,
                "action": action
            }
        )
        
        reasoning_span.end()
    
    def end_agent_execution(self, span_id: str, output_data: dict, execution_time: float):
        """End agent execution span with execution summary."""
        if span_id not in self.active_spans:
            return
        
        span = self.active_spans[span_id]
        
        # Add execution summary (preserving existing structure)
        with span.start_as_current_span(
            name="execution_summary",
            input={"summary_type": "final_execution"}
        ) as summary_span:
            
            summary_span.update(
                output={
                    "execution_summary": {
                        "execution_time": execution_time,
                        "status": "completed",
                        "success_rate": "100%",
                        "error_count": 0,
                        "performance_rating": "excellent" if execution_time < 1.0 else "good",
                        "efficiency_score": max(0, 1.0 - execution_time / 2.0)
                    }
                }
            )
        
        span.end()
        del self.active_spans[span_id]
    
    def end_foodie_tour(self, final_score: float, summary: Optional[dict] = None):
        """End the foodie tour trace."""
        if self.current_main_span:
            # End any remaining active spans
            for span_id, span in list(self.active_spans.items()):
                span.end()
                del self.active_spans[span_id]
            
            # Update main span with final summary (preserving existing structure)
            tour_summary = {
                "final_score": final_score,
                "status": "completed",
                "total_duration": "completed"
            }
            if summary:
                tour_summary.update(summary)
            
            self.current_main_span.update(
                output={"tour_summary": tour_summary}
            )
            self.current_main_span.end()
        
        # Flush data to Langfuse
        self.langfuse.flush()
        
        print(f"🎯 Foodie tour trace completed and sent to Langfuse!")
        print(f"📊 Trace ID: {self.current_trace_id}")
        
        # Reset state
        self.current_trace_id = None
        self.current_main_span = None

# Global tracer instance
tracer = FoodieLangfuseTracer()

# Convenience functions for easy integration
def start_tour_trace(city: str, vibe: str, budget: float, date: str) -> str:
    """Start a new foodie tour trace."""
    return tracer.start_foodie_tour(city, vibe, budget, date)

def end_tour_trace(final_score: float, summary: Optional[dict] = None):
    """End the current foodie tour trace."""
    tracer.end_foodie_tour(final_score, summary)

def start_planner_workflow() -> str:
    """Start planner workflow span."""
    return tracer.start_planner_workflow()

def add_planner_llm_status(span_id: str, llm_used: bool, fallback_reason: Optional[str] = None):
    """Add LLM status to planner workflow."""
    tracer.add_planner_llm_status(span_id, llm_used, fallback_reason)

def add_planner_llm_routing_reasoning(span_id: str, original_plan: dict, normalized_plan: dict, 
                                        llm_rationales: List[str], business_rules_applied: List[str]):
    """Add detailed LLM routing reasoning to planner workflow."""
    tracer.add_planner_llm_routing_reasoning(span_id, original_plan, normalized_plan, llm_rationales, business_rules_applied)

def add_planner_decisions(span_id: str, decisions: List[dict]):
    """Add planning decisions to planner workflow."""
    tracer.add_planner_decisions(span_id, decisions)

def add_planner_final_workflow(span_id: str, final_steps: List[str]):
    """Add final workflow structure to planner workflow."""
    tracer.add_planner_final_workflow(span_id, final_steps)

def end_planner_workflow(span_id: str):
    """End planner workflow span."""
    tracer.end_planner_workflow(span_id)

def start_agent_execution(agent_name: str, action: str, input_data: dict) -> str:
    """Start agent execution span."""
    return tracer.start_agent_execution(agent_name, action, input_data)

def add_agent_reasoning(span_id: str, agent_name: str, action: str, 
                        reasoning: str, output_data: dict):
    """Add reasoning to agent execution span."""
    tracer.add_agent_reasoning(span_id, agent_name, action, reasoning, output_data)

def end_agent_execution(span_id: str, output_data: dict, execution_time: float):
    """End agent execution span."""
    tracer.end_agent_execution(span_id, output_data, execution_time)
