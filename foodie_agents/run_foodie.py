#!/usr/bin/env python3
"""Main Foodie Agents application using Strands framework - production-ready multi-agent AI system."""

import argparse
import os
import asyncio
import time
from typing import Dict, Any
from dotenv import load_dotenv
from .strands_agents import (
    FoodieState, PlannerLLMAgent, ResearcherAgent, ScoutAgent, 
    WriterAgent, ReviewerAgent
)
from .reasoning_analyzer import ReasoningAnalyzer
from .langfuse_integration import (
    start_tour_trace, end_tour_trace, start_planner_workflow,
    add_planner_llm_status, add_planner_decisions, add_planner_final_workflow,
    end_planner_workflow, start_agent_execution, add_agent_reasoning,
    end_agent_execution, add_planner_llm_routing_reasoning
)


def analyze_reasoning_in_realtime(state: FoodieState):
    """Analyze reasoning data in real-time during execution - maintaining current functionality."""
    analyzer = ReasoningAnalyzer()
    summary = analyzer.analyze_state_reasoning({
        "trace_id": "live_execution",
        "reasoning": state.reasoning
    })
    
    # Print the summary
    analyzer.print_summary(summary)
    
    # Explain WHY each agent made their decisions
    analyzer.explain_agent_decisions(state.reasoning)


async def main():
    """Main application entry point using Strands framework."""
    # Load environment variables from .env file
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Foodie Agents - AI-powered food tour planning with Strands framework")
    parser.add_argument("--date", default="2025-08-23", help="Tour date (YYYY-MM-DD)")
    parser.add_argument("--budget", type=float, default=100.0, help="Budget per person")
    parser.add_argument("--vibe", default="cozy", help="Tour vibe preference (cozy|lively)")
    parser.add_argument("--city", default="Chicago", help="City for tour")
    parser.add_argument("--analyze", action="store_true", help="Show real-time reasoning analysis")
    
    args = parser.parse_args()
    
    # Initialize state
    state = FoodieState(
        budget=args.budget,
        city=args.city,
        vibe=args.vibe,
        date=args.date
    )
    
    # Initialize agents
    planner = PlannerLLMAgent()
    
    try:
        # Start Langfuse tracing
        print("Starting Foodie Agents tour planning with Strands framework...")
        print(f"Date: {state.date}")
        print(f"Budget: ${state.budget}")
        print(f"Vibe: {state.vibe}")
        print(f"City: {state.city}")
        print()
        
        trace_id = start_tour_trace(
            city=state.city,
            vibe=state.vibe,
            budget=state.budget,
            date=state.date
        )
        print(f"📊 Langfuse trace started: {trace_id}")
        
        print("Executing agent workflow with Strands framework...")
        
        # Start planner workflow tracing
        planner_span_id = start_planner_workflow()
        
        # Execute complete workflow via planner
        start_time = time.time()
        state = await planner.run(state, planner_span_id=planner_span_id)
        execution_time = time.time() - start_time
        
        # Add planner decisions to trace
        planner_decisions = [r for r in state.reasoning if r["agent"] == "planner"]
        add_planner_decisions(planner_span_id, planner_decisions)
        
        # Add final workflow structure
        final_steps = ["check_weather", "scout_venues", "split_budget", "write_itinerary", "review"]
        add_planner_final_workflow(planner_span_id, final_steps)
        
        # End planner workflow
        end_planner_workflow(planner_span_id)
        
        print("Planner: Complete workflow executed")
        if args.analyze:
            print(f"   Reasoning: {len(state.reasoning)} decision(s) captured")
        
        # Real-time reasoning analysis (maintaining current functionality)
        if args.analyze:
            analyze_reasoning_in_realtime(state)
        
        # Print results (maintaining current format)
        print("\n" + "="*60)
        print("FOODIE TOUR PLAN COMPLETE")
        print("="*60)
        print(f"Date: {state.date}")
        print(f"Budget: ${state.budget} per person")
        print(f"Vibe: {state.vibe}")
        print(f"Weather: {state.weather['condition']}")
        print(f"Indoor required: {state.weather['indoor_required']}")
        print(f"Review Score: {state.review_score:.1f}/1.0")
        print()
        
        print("RESTAURANT STOPS:")
        for i, venue in enumerate(state.shortlist, 1):
            budget = state.budget_split[i-1] if i <= len(state.budget_split) else 0
            tags = ", ".join(venue.get("tags", []))
            print(f"  {i}. {venue['name']} ({venue['neighborhood']})")
            print(f"     Budget: ${budget:.2f}")
            print(f"     Tags: {tags}")
            print()
        
        print("ITINERARY:")
        print(f'"{state.itinerary}"')
        print()
        
        print("Tour planning completed successfully with Strands framework!")
        
        # End Langfuse trace
        end_tour_trace(
            final_score=state.review_score,
            summary={
                "total_venues": len(state.shortlist),
                "total_budget": state.budget,
                "execution_time": execution_time,
                "reasoning_count": len(state.reasoning)
            }
        )
        
    except Exception as e:
        print(f"Error during tour planning: {e}")
        # End trace even on error
        try:
            end_tour_trace(final_score=0.0, summary={"error": str(e)})
        except:
            pass
        raise


if __name__ == "__main__":
    asyncio.run(main())
