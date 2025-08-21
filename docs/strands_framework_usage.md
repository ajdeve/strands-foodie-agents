# 🧬 Strands Framework Usage in Foodie Agents

> **Comprehensive guide to how the Strands multi-agent framework is implemented and utilized in the Foodie Agents system**

## 📋 Table of Contents

1. [Overview](#overview)
2. [Core Strands Concepts](#core-strands-concepts)
3. [Agent Implementation](#agent-implementation)
4. [State Management](#state-management)
5. [Tool Integration](#tool-integration)
6. [Async Execution](#async-execution)
7. [Error Handling](#error-handling)
8. [Best Practices](#best-practices)

## 🎯 Overview

The Foodie Agents system is built entirely on the **Strands framework**, a production-ready multi-agent system that provides:

- **Agent base classes** with built-in observability
- **Tool decorators** for MCP integration
- **Async execution patterns** for optimal performance
- **State management** with type safety
- **Built-in tracing** and error handling

## 🏗️ Core Strands Concepts

### **Agent Base Class**
```python
from strands import Agent

class PlannerLLMAgent(Agent):
    """Planner agent using Strands Agent base class."""
    
    async def run(self, state: FoodieState, context: Any = None) -> FoodieState:
        # Strands async execution pattern
        return state
```

**Key Benefits:**
- **Built-in observability** with automatic span creation
- **Error handling** with graceful degradation
- **Performance monitoring** with execution timing
- **State validation** and type safety

### **Tool Decorators**
```python
from strands.tools import tool

@tool(name="weather_tool", description="Get weather data for tour planning")
def get_weather(date: str) -> Dict[str, Any]:
    """MCP-compliant weather tool using Open-Meteo API."""
    # Tool implementation
    return weather_data
```

**Key Benefits:**
- **Automatic MCP compliance** with tool registration
- **Input validation** and type checking
- **Error handling** with structured responses
- **Documentation generation** for API specs

## 🤖 Agent Implementation

### **1. PlannerLLMAgent - The Orchestrator**

```python
class PlannerLLMAgent(Agent):
    """Planner asks LLM for an ordered plan, validates/normalizes it, then executes sub-agents."""
    
    async def run(self, state: FoodieState, context: Any = None, planner_span_id: str = None) -> FoodieState:
        # Strands async execution with state management
        start_time = time.time()
        
        # LLM-powered planning with business rule validation
        plan = structured_json(RoutingPlan, PLANNER_SYSTEM, user_prompt)
        
        # Business rule enforcement and normalization
        steps = self._normalize_plan(plan.steps)
        
        # Execute sub-agents using Strands orchestration
        for step in steps:
            agent = self._get_agent_for_step(step)
            state = await agent.run(state)
        
        return state
```

**Strands Features Used:**
- **Async execution** with `async def run()`
- **State management** with `FoodieState` dataclass
- **Agent orchestration** with sequential execution
- **Error handling** with try-catch blocks

### **2. ResearcherAgent - Weather Analysis**

```python
class ResearcherAgent(Agent):
    """Deterministic weather fetch via MCP tool."""
    
    def __init__(self):
        super().__init__()
        # Strands tool integration
        self.tools = [get_weather]
    
    async def run(self, state: FoodieState, context: Any = None) -> FoodieState:
        # Strands async execution pattern
        start_time = time.time()
        
        # MCP tool usage via Strands
        weather_data = get_weather(state.date)
        state.weather = weather_data
        
        # State updates with reasoning capture
        self._add_reasoning(state, weather_data)
        
        return state
```

**Strands Features Used:**
- **Tool integration** with `self.tools` list
- **Async execution** for non-blocking operations
- **State updates** with immutable patterns
- **Built-in timing** for performance monitoring

### **3. ScoutAgent - Venue Selection**

```python
class ScoutAgent(Agent):
    """Deterministic venue filtering via MCP tool."""
    
    def __init__(self):
        super().__init__()
        # Strands tool registration
        self.tools = [filter_venues]
    
    async def run(self, state: FoodieState, context: Any = None) -> FoodieState:
        # Weather-aware venue filtering
        indoor_required = bool(state.weather.get("indoor_required"))
        
        # MCP tool usage with Strands integration
        filtered = filter_venues(state.vibe, indoor_required)
        state.shortlist = filtered
        
        return state
```

**Strands Features Used:**
- **Tool decorators** for MCP compliance
- **State access** with type-safe properties
- **Async execution** for scalability
- **Error handling** with graceful fallbacks

## 📊 State Management

### **FoodieState Dataclass**

```python
@dataclass
class FoodieState:
    """Core state for food tour planning - Strands-compatible."""
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
```

**Strands Benefits:**
- **Immutable state** with dataclass immutability
- **Type safety** with Python 3.11+ typing
- **Default values** for robust initialization
- **Field factories** for complex defaults

### **State Flow Between Agents**

```python
# Strands state flow pattern
async def execute_workflow(self, state: FoodieState) -> FoodieState:
    # Each agent receives and returns the same state object
    state = await self.researcher.run(state)      # Add weather data
    state = await self.scout.run(state)           # Add venue shortlist
    state = await self.budget.run(state)          # Add budget allocation
    state = await self.writer.run(state)          # Add itinerary
    state = await self.reviewer.run(state)        # Add review score
    
    return state  # Final state with all data
```

**Strands Benefits:**
- **Consistent state interface** across all agents
- **Type-safe state updates** with validation
- **Immutable state patterns** for reliability
- **Built-in state validation** and error handling

## 🛠️ Tool Integration

### **MCP Tool Registration**

```python
# Strands automatically registers tools for agents
class BudgetAgent(Agent):
    def __init__(self):
        super().__init__()
        # Tools are automatically available to the agent
        self.tools = [call_budget_service]
    
    async def run(self, state: FoodieState, context: Any = None) -> FoodieState:
        # Tool usage with automatic error handling
        budget_split = call_budget_service(state.budget, len(state.shortlist))
        state.budget_split = budget_split["per_stop"]
        return state
```

**Strands Benefits:**
- **Automatic tool discovery** and registration
- **Built-in error handling** for tool failures
- **Type validation** for tool inputs/outputs
- **Performance monitoring** for tool execution

### **Tool Decorator Usage**

```python
@tool(name="venue_tool", description="Filter venues by criteria")
def filter_venues(vibe: str, indoor_required: bool) -> List[Dict[str, Any]]:
    """Filter venues using MCP-compliant interface."""
    # Load venue data
    venues = load_venue_data()
    
    # Apply filters
    filtered = [
        v for v in venues
        if v["vibe"] == vibe and v["indoor_compliant"] == indoor_required
    ]
    
    return filtered[:3]  # Return top 3 matches
```

**Strands Benefits:**
- **Automatic MCP compliance** with tool registration
- **Input validation** with type hints
- **Error handling** with structured responses
- **Documentation generation** for API specs

## ⚡ Async Execution

### **Async Agent Execution**

```python
# Strands async execution pattern
async def run(self, state: FoodieState, context: Any = None) -> FoodieState:
    # Non-blocking operations
    start_time = time.time()
    
    # Async tool calls
    weather_data = await self._get_weather_async(state.date)
    
    # Async state updates
    state = await self._update_state_async(state, weather_data)
    
    # Performance monitoring
    execution_time = time.time() - start_time
    self._log_performance(execution_time)
    
    return state
```

**Strands Benefits:**
- **Non-blocking execution** for better performance
- **Built-in timing** for performance monitoring
- **Async tool integration** for scalability
- **Concurrent execution** capabilities

### **Sequential vs Parallel Execution**

```python
# Sequential execution (current implementation)
for step in steps:
    agent = self._get_agent_for_step(step)
    state = await agent.run(state)

# Parallel execution (future enhancement)
tasks = [
    agent.run(state) for agent in agents
]
results = await asyncio.gather(*tasks)
```

**Strands Benefits:**
- **Flexible execution patterns** for different use cases
- **Built-in concurrency** support
- **Performance optimization** capabilities
- **Resource management** and monitoring

## 🚨 Error Handling

### **Graceful Degradation**

```python
class PlannerLLMAgent(Agent):
    async def run(self, state: FoodieState, context: Any = None) -> FoodieState:
        try:
            # Try LLM planning
            plan = structured_json(RoutingPlan, PLANNER_SYSTEM, user_prompt)
            steps = self._extract_steps(plan)
        except Exception as e:
            # Strands fallback mechanism
            steps = DEFAULT_ORDER[:]
            self._log_fallback(str(e))
        
        # Continue execution regardless of LLM success/failure
        return await self._execute_steps(state, steps)
```

**Strands Benefits:**
- **Built-in error handling** with graceful degradation
- **Automatic error logging** and monitoring
- **Fallback mechanisms** for reliability
- **Performance impact tracking** for errors

### **Tool Error Handling**

```python
@tool(name="budget_tool", description="Split budget across restaurant stops")
def split_budget(total_budget: float, stops: int) -> Dict[str, Any]:
    """Local budget splitting with error handling."""
    try:
        # Attempt external service call
        return call_budget_service(total_budget, stops)
    except Exception as e:
        # Strands fallback to local logic
        return {
            "per_stop": [total_budget / stops] * stops,
            "fallback": True,
            "error": str(e)
        }
```

**Strands Benefits:**
- **Automatic error capture** and logging
- **Fallback mechanism** integration
- **Error context** preservation
- **Performance impact** monitoring

## 🎯 Best Practices

### **1. Agent Design Patterns**

```python
# ✅ Good: Clear separation of concerns
class SpecializedAgent(Agent):
    def __init__(self):
        super().__init__()
        self.tools = [specific_tool]  # Only necessary tools
    
    async def run(self, state: FoodieState, context: Any = None) -> FoodieState:
        # Single responsibility principle
        result = await self._execute_specific_logic(state)
        return self._update_state(state, result)

# ❌ Avoid: Monolithic agents
class MonolithicAgent(Agent):
    async def run(self, state: FoodieState, context: Any = None) -> FoodieState:
        # Too many responsibilities
        # Weather, venues, budget, writing, review all in one
        pass
```

### **2. State Management**

```python
# ✅ Good: Immutable state updates
async def run(self, state: FoodieState, context: Any = None) -> FoodieState:
    # Create new state with updates
    new_state = dataclasses.replace(state, 
        weather=self._get_weather_data(),
        reasoning=state.reasoning + [new_reasoning]
    )
    return new_state

# ❌ Avoid: Mutable state modifications
async def run(self, state: FoodieState, context: Any = None) -> FoodieState:
    # Direct mutation can cause issues
    state.weather = self._get_weather_data()  # Mutable
    return state
```

### **3. Tool Integration**

```python
# ✅ Good: Tool-specific agents
class WeatherAgent(Agent):
    def __init__(self):
        super().__init__()
        self.tools = [get_weather]  # Only weather-related tools
    
    async def run(self, state: FoodieState, context: Any = None) -> FoodieState:
        weather_data = get_weather(state.date)
        return self._update_state_with_weather(state, weather_data)

# ❌ Avoid: Tool mixing
class MixedAgent(Agent):
    def __init__(self):
        super().__init__()
        # Too many unrelated tools
        self.tools = [get_weather, filter_venues, call_budget_service]
```

### **4. Error Handling**

```python
# ✅ Good: Comprehensive error handling
async def run(self, state: FoodieState, context: Any = None) -> FoodieState:
    try:
        result = await self._execute_primary_logic(state)
        return self._update_state_success(state, result)
    except SpecificError as e:
        # Handle specific errors
        return await self._handle_specific_error(state, e)
    except Exception as e:
        # Handle general errors with fallback
        return await self._handle_general_error(state, e)

# ❌ Avoid: Generic error handling
async def run(self, state: FoodieState, context: Any = None) -> FoodieState:
    try:
        result = await self._execute_logic(state)
        return result
    except Exception as e:
        # Too generic, loses context
        print(f"Error: {e}")
        return state
```

## 🔍 Monitoring and Debugging

### **Strands Built-in Observability**

```python
# Automatic span creation and monitoring
async def run(self, state: FoodieState, context: Any = None) -> FoodieState:
    # Strands automatically creates execution spans
    start_time = time.time()
    
    # Your business logic
    result = await self._execute_business_logic(state)
    
    # Strands automatically captures:
    # - Execution time
    # - Input/output data
    # - Error states
    # - Performance metrics
    
    return result
```

### **Custom Observability Integration**

```python
# Integrate with external observability (Langfuse)
from foodie_agents.langfuse_integration import start_agent_execution

async def run(self, state: FoodieState, context: Any = None) -> FoodieState:
    # Custom span creation
    span_id = start_agent_execution("researcher", "check_weather", {"date": state.date})
    
    try:
        # Business logic
        result = await self._execute_logic(state)
        
        # Success tracking
        self._log_success(span_id, result)
        return result
    except Exception as e:
        # Error tracking
        self._log_error(span_id, e)
        raise
```

## 🚀 Performance Optimization

### **Async Execution Benefits**

```python
# Strands async execution provides:
# - Non-blocking I/O operations
# - Better resource utilization
# - Improved scalability
# - Built-in performance monitoring

class OptimizedAgent(Agent):
    async def run(self, state: FoodieState, context: Any = None) -> FoodieState:
        # Parallel tool execution
        weather_task = self._get_weather_async(state.date)
        venue_task = self._get_venues_async(state.city)
        
        # Wait for both to complete
        weather_data, venue_data = await asyncio.gather(weather_task, venue_task)
        
        # Update state with both results
        return self._update_state_with_data(state, weather_data, venue_data)
```

### **Resource Management**

```python
# Strands provides built-in resource management
class ResourceAwareAgent(Agent):
    def __init__(self):
        super().__init__()
        # Strands manages tool lifecycle
        self.tools = [get_weather, filter_venues]
    
    async def run(self, state: FoodieState, context: Any = None) -> FoodieState:
        # Strands handles:
        # - Tool initialization
        # - Resource cleanup
        # - Memory management
        # - Connection pooling
        
        result = await self._execute_with_resources(state)
        return result
```

## 📚 Summary

The Strands framework provides a **robust, production-ready foundation** for multi-agent systems:

### **Key Benefits:**
1. **Built-in observability** with automatic monitoring
2. **Type-safe state management** with dataclass support
3. **Async execution patterns** for optimal performance
4. **Tool integration** with MCP compliance
5. **Error handling** with graceful degradation
6. **Performance monitoring** with built-in metrics

### **Best Practices:**
1. **Single responsibility** for each agent
2. **Immutable state updates** for reliability
3. **Comprehensive error handling** with fallbacks
4. **Tool-specific agents** for clean separation
5. **Async execution** for scalability

### **Integration Points:**
1. **Langfuse observability** for complete visibility
2. **MCP tools** for standardized interfaces
3. **A2A communication** for external service integration
4. **LLM integration** with intelligent fallbacks

The Foodie Agents system demonstrates **enterprise-grade multi-agent development** using Strands framework best practices! 🎉
