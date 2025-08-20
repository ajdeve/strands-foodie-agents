"""Enhanced reasoning analyzer for Foodie Agents - shows why decisions are made."""

import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class AgentReasoning:
    """Extracted reasoning data from an agent."""
    agent: str
    decision: str
    criteria: List[str]
    evidence: List[str]
    confidence: float
    next_action: Optional[str]


@dataclass
class TraceSummary:
    """Summary of a trace's reasoning."""
    trace_id: str
    total_reasoning: int
    agents_involved: List[str]
    confidence_distribution: Dict[str, int]
    decision_patterns: Dict[str, int]
    insights: List[str]
    decision_quality: Dict[str, str]  # agent -> quality assessment


class ReasoningAnalyzer:
    """Analyzes reasoning data from agent state to show WHY decisions are made."""
    
    def analyze_state_reasoning(self, state_data: Dict[str, Any]) -> TraceSummary:
        """Analyze reasoning from a state object to understand decision-making."""
        
        reasoning = state_data.get("reasoning", [])
        if not reasoning:
            return TraceSummary(
                trace_id="unknown",
                total_reasoning=0,
                agents_involved=[],
                confidence_distribution={},
                decision_patterns={},
                insights=["No reasoning data found"],
                decision_quality={}
            )
        
        # Extract agent info
        agents = list(set(r.get("agent", "unknown") for r in reasoning))
        
        # Analyze confidence distribution
        confidence_dist = {}
        for reason in reasoning:
            conf = reason.get("confidence", 0)
            if conf >= 0.8:
                level = "high"
            elif conf >= 0.5:
                level = "medium"
            elif conf >= 0.0:
                level = "low"
            else:
                level = "negative"
            
            confidence_dist[level] = confidence_dist.get(level, 0) + 1
        
        # Analyze decision patterns
        decision_patterns = {}
        for reason in reasoning:
            decision = reason.get("decision", "unknown")
            decision_patterns[decision] = decision_patterns.get(decision, 0) + 1
        
        # Assess decision quality per agent
        decision_quality = {}
        for reason in reasoning:
            agent = reason.get("agent", "unknown")
            criteria = reason.get("criteria", [])
            evidence = reason.get("evidence", [])
            confidence = reason.get("confidence", 0)
            
            # Quality assessment based on reasoning completeness
            quality_score = 0
            if len(criteria) >= 2:
                quality_score += 1
            if len(evidence) >= 1:
                quality_score += 1
            if confidence >= 0.7:
                quality_score += 1
            
            if quality_score >= 2:
                quality = "excellent"
            elif quality_score >= 1:
                quality = "good"
            else:
                quality = "needs_improvement"
            
            decision_quality[agent] = quality
        
        # Generate insights about WHY decisions were made
        insights = []
        if confidence_dist.get("high", 0) > 0:
            insights.append(f"🎯 {confidence_dist['high']} high-confidence decisions made")
        if confidence_dist.get("negative", 0) > 0:
            insights.append(f"⚠️  {confidence_dist['negative']} negative-confidence decisions (may indicate issues)")
        if len(agents) > 1:
            insights.append(f"🤖 Multi-agent coordination: {', '.join(agents)} working together")
        if reasoning:
            insights.append(f"📊 Total decision points: {len(reasoning)}")
        
        # Add decision-specific insights
        for decision, count in decision_patterns.items():
            if count > 1:
                insights.append(f"🔄 Decision pattern '{decision}' used {count} times (consistent approach)")
        
        # Add quality insights
        excellent_agents = [agent for agent, quality in decision_quality.items() if quality == "excellent"]
        if excellent_agents:
            insights.append(f"⭐ {', '.join(excellent_agents)} made excellent decisions with strong reasoning")
        
        needs_improvement = [agent for agent, quality in decision_quality.items() if quality == "needs_improvement"]
        if needs_improvement:
            insights.append(f"🔧 {', '.join(needs_improvement)} could improve decision reasoning")
        
        return TraceSummary(
            trace_id=state_data.get("trace_id", "unknown"),
            total_reasoning=len(reasoning),
            agents_involved=agents,
            confidence_distribution=confidence_dist,
            decision_patterns=decision_patterns,
            insights=insights,
            decision_quality=decision_quality
        )
    
    def print_summary(self, summary: TraceSummary):
        """Print a formatted summary showing WHY decisions were made."""
        print("=" * 80)
        print("🧠 FOODIE AGENTS REASONING ANALYSIS")
        print("=" * 80)
        
        print(f"📊 Execution Summary:")
        print(f"   • Total Decisions: {summary.total_reasoning}")
        print(f"   • Agents Active: {', '.join(summary.agents_involved)}")
        
        print(f"\n🎯 Decision Patterns (WHY they chose this approach):")
        for decision, count in summary.decision_patterns.items():
            print(f"   • {decision}: {count} times")
        
        print(f"\n📈 Confidence Distribution (HOW sure they were):")
        for level, count in summary.confidence_distribution.items():
            print(f"   • {level.capitalize()}: {count} decisions")
        
        print(f"\n⭐ Decision Quality Assessment (HOW well they reasoned):")
        for agent, quality in summary.decision_quality.items():
            print(f"   • {agent.capitalize()}: {quality.replace('_', ' ').title()}")
        
        print(f"\n💡 Key Insights (WHAT this tells us):")
        for insight in summary.insights:
            print(f"   {insight}")
        
        print("=" * 80)
    
    def explain_agent_decisions(self, reasoning_data: List[Dict[str, Any]]):
        """Explain WHY each agent made their decisions."""
        print(f"\n🔍 DETAILED DECISION ANALYSIS:")
        print("=" * 60)
        
        for i, reason in enumerate(reasoning_data, 1):
            agent = reason.get("agent", "unknown")
            decision = reason.get("decision", "unknown")
            criteria = reason.get("criteria", [])
            evidence = reason.get("evidence", [])
            confidence = reason.get("confidence", 0)
            next_action = reason.get("next_action")
            
            print(f"\n{i}. {agent.upper()} - {decision}")
            print(f"   🎯 WHY this decision?")
            print(f"      Criteria: {', '.join(criteria)}")
            print(f"      Evidence: {', '.join(evidence)}")
            print(f"   📊 HOW confident? {confidence:.2f}")
            if next_action:
                print(f"   ➡️  WHAT next? {next_action}")
            
            # Add decision explanation
            if decision == "planner_route_v1":
                print(f"   💭 EXPLANATION: Planner created task slots based on {', '.join(criteria)}")
            elif decision == "weather_indoor":
                print(f"   💭 EXPLANATION: Researcher determined indoor requirement from precipitation data")
            elif decision == "venue_filter_pass":
                print(f"   💭 EXPLANATION: Scout filtered venues using {', '.join(criteria)}")
            elif decision == "template_writer_v1":
                print(f"   💭 EXPLANATION: Writer generated itinerary following {', '.join(criteria)}")
            elif decision == "rubric_score":
                print(f"   💭 EXPLANATION: Reviewer scored plan using {', '.join(criteria)}")


def analyze_langfuse_trace(trace_data: List[Dict[str, Any]]) -> TraceSummary:
    """Analyze a trace from Langfuse data."""
    analyzer = ReasoningAnalyzer()
    
    # Look for reasoning data in observations
    reasoning_entries = []
    
    for obs in trace_data:
        if obs.get("type") == "SPAN":
            metadata = obs.get("metadata", {})
            if isinstance(metadata, dict) and "attributes" in metadata:
                attrs = metadata["attributes"]
                
                # Check for reasoning in span.output or output_data
                for key in ["span.output", "output_data"]:
                    if key in attrs:
                        try:
                            output = eval(attrs[key])
                            if isinstance(output, dict) and "why" in output:
                                why = output["why"]
                                reasoning_entries.append({
                                    "agent": attrs.get("agent", "unknown"),
                                    "decision": why.get("decision_reason_code", "unknown"),
                                    "criteria": why.get("criteria", []),
                                    "evidence": why.get("evidence", []),
                                    "confidence": why.get("confidence", 0.0),
                                    "next_action": why.get("next_action")
                                })
                        except:
                            pass
    
    # Create a mock state for analysis
    mock_state = {"reasoning": reasoning_entries}
    return analyzer.analyze_state_reasoning(mock_state)


def print_reasoning_summary(trace_data: List[Dict[str, Any]]) -> TraceSummary:
    """Analyze and print a trace summary."""
    analyzer = ReasoningAnalyzer()
    summary = analyze_langfuse_trace(trace_data)
    analyzer.print_summary(summary)
    return summary


def print_summary_direct(summary: TraceSummary) -> None:
    """Print a summary directly."""
    analyzer = ReasoningAnalyzer()
    analyzer.print_summary(summary)
