#!/usr/bin/env python3
"""Main Foodie Agents application using Strands framework - production-ready multi-agent AI system."""

import argparse
import os
import asyncio
from typing import Dict, Any
from .strands_agents import (
    FoodieState, PlannerAgent, ResearcherAgent, ScoutAgent, 
    WriterAgent, ReviewerAgent, call_budget_service
)
from .reasoning_analyzer import ReasoningAnalyzer


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
    planner = PlannerAgent()
    researcher = ResearcherAgent()
    scout = ScoutAgent()
    writer = WriterAgent()
    reviewer = ReviewerAgent()
    
    try:
        # Execute agent workflow using Strands framework
        print("Starting Foodie Agents tour planning with Strands framework...")
        print(f"Date: {state.date}")
        print(f"Budget: ${state.budget}")
        print(f"Vibe: {state.vibe}")
        print(f"City: {state.city}")
        print()
        
        print("Executing agent workflow with Strands framework...")
        
        # 1. Planner
        state = await planner.run(state)
        print("Planner: Tasks routed and assigned")
        if args.analyze:
            print(f"   Reasoning: {len(state.reasoning)} decision(s) captured")
        
        # 2. Researcher
        state = await researcher.run(state)
        print(f"Researcher: Weather checked - {state.weather['condition']} (indoor: {state.weather['indoor_required']})")
        if args.analyze:
            print(f"   Reasoning: {len(state.reasoning)} decision(s) captured")
        
        # 3. Scout
        state = await scout.run(state)
        print(f"Scout: {len(state.shortlist)} venues selected")
        if args.analyze:
            print(f"   Reasoning: {len(state.reasoning)} decision(s) captured")
        
        # 4. Budget service (A2A communication)
        budget_result = call_budget_service(state.budget, len(state.shortlist))
        state.budget_split = budget_result["per_stop"]
        print(f"Budget: Split into {len(state.budget_split)} stops")
        
        # 5. Writer
        state = await writer.run(state)
        print("Writer: Itinerary generated")
        if args.analyze:
            print(f"   Reasoning: {len(state.reasoning)} decision(s) captured")
        
        # 6. Reviewer
        state = await reviewer.run(state)
        print(f"Reviewer: Plan scored {state.review_score:.1f}/1.0")
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
        
    except Exception as e:
        print(f"Error during tour planning: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
