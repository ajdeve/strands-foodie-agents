# MCP Tool Integration in Foodie Agents

> **Comprehensive guide to how Model Context Protocol (MCP) tools are implemented and utilized in the Foodie Agents system**

## Table of Contents

1. [Overview](#overview)
2. [MCP Architecture](#mcp-architecture)
3. [Communication Pattern Distinction](#communication-pattern-distinction)
4. [Tool Implementations](#tool-implementations)
5. [Tool Abstraction Layer](#tool-abstraction-layer)
6. [External Service Integration](#external-service-integration)
7. [Tool Validation & Fallbacks](#tool-validation--fallbacks)
8. [Best Practices](#best-practices)

## Overview

**Model Context Protocol (MCP) tools** in Foodie Agents provide a standardized way for agents to interact with external services and APIs. MCP tools act as **adapters** that abstract away the complexity of external APIs and services, allowing agents to focus on their core logic without making direct HTTP calls.

**Note:** This document covers MCP tools, but the system also includes local data processing and A2A communication patterns that are documented separately.

### **Key Benefits:**
- **Tool Abstraction** - Agents never make direct HTTP calls
- **Standardized Interfaces** - Consistent tool patterns across the system
- **Fallback Handling** - Local logic when external services fail
- **Type Safety** - Pydantic models for input/output validation
- **Observability** - Complete tracing of tool usage and performance

## MCP Architecture

### **Tool Layer Architecture**

```
┌─────────────────────────────────────────────────────────────────┐
│                    FOODIE AGENTS                               │
│                    (Strands Framework)                         │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   Planner   │  │ Researcher  │  │    Scout    │            │
│  │   Agent     │  │   Agent     │  │    Agent    │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│         │                │                │                   │
│         └────────────────┼────────────────┘                   │
│                          │                                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   Budget    │  │   Writer    │  │  Reviewer   │            │
│  │   Agent     │  │   Agent     │  │   Agent     │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                                │
                                │ MCP Tool Layer
                                │ (External API integration)
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MCP TOOL ADAPTERS                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐                     │
│  │   Weather Tool  │  │  LLM Client     │                     │
│  │   (API Client)  │  │  (Ollama)       │                     │
│  └─────────────────┘  └─────────────────┘                     │
└─────────────────────────────────────────────────────────────────┘
                                │
                                │ External Services
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                            │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐                     │
│  │  Open-Meteo    │  │  Ollama LLM     │                     │
│  │  Weather API   │  │  Service        │                     │
│  └─────────────────┘  └─────────────────┘                     │
└─────────────────────────────────────────────────────────────────┘
```

### **Core Principles**

1. **Agents Never Make Direct HTTP Calls** - All external communication goes through MCP tools
2. **Tool Abstraction** - Tools hide the complexity of external services
3. **Fallback Logic** - Local alternatives when external services fail
4. **Type Safety** - Input/output validation with Pydantic models
5. **Observability** - Complete tracing of tool usage and performance

### **Communication Pattern Distinction**

**MCP Tools (External API Integration):**
- **Weather Tool** → Open-Meteo API (External HTTP service)
- **LLM Client** → Ollama service (Local LLM service)

**Local Data Processing (No External Calls):**
- **Venue Filtering** → Local JSON data + business logic

**A2A Communication (External Service):**
- **Budget Service** → External FastAPI microservice (Port 8089)

## Communication Pattern Distinction

### **MCP Tools (External API Integration)**
MCP tools provide standardized interfaces to external services and APIs, abstracting away the complexity of external communication.

### **Local Data Processing**
Local functions that process data without making external calls, often wrapped in `@tool` decorators for consistency.

### **A2A Communication (External Services)**
Agent-to-Agent communication with external microservices running as independent processes.

## Tool Implementations

### **1. Weather Tool (MCP API Client)**

```python
# foodie_agents/tools.py
@tool(name="weather_tool", description="Get weather data for tour planning")
def get_weather(date: str) -> Dict[str, Any]:
    """MCP tool for external weather API integration."""
    
    # Tool input validation
    if not date:
        return {
            "precip_prob": 0.0,
            "condition": "unknown",
            "indoor_required": False,
            "source": "validation_error",
            "error": "Date parameter required"
        }
    
    # External API call (abstracted from agents)
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": 41.8781,  # Chicago
            "longitude": -87.6298,
            "daily": "precipitation_probability_max",
            "timezone": "America/Chicago"
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Extract and process weather data
        precip_prob = data["daily"]["precipitation_probability_max"][0]
        
        return {
            "precip_prob": precip_prob,
            "condition": "rain" if precip_prob >= 50 else "clear",
            "indoor_required": precip_prob >= 50,
            "source": "open_meteo_api",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        # Fallback to default weather (tool handles failure)
        return {
            "precip_prob": 0.0,
            "condition": "clear",
            "indoor_required": False,
            "source": "fallback",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
```

**MCP Benefits:**
- **Input Validation** - Tool validates date parameter
- **Error Handling** - Tool manages API failures gracefully
- **Data Processing** - Tool transforms raw API data into usable format
- **Fallback Logic** - Tool provides sensible defaults when API fails

### **2. Local Data Processing (Venue Filtering)**

```python
# foodie_agents/tools.py
@tool(name="venue_tool", description="Filter venues by criteria")
def filter_venues(vibe: str, indoor_required: bool) -> List[Dict[str, Any]]:
    """Local data processing for venue filtering and selection."""
    
    try:
        # Load venue data from local JSON file
        with ir.files("foodie_agents.data").joinpath("chicago_venues.json").open("r", encoding="utf-8") as f:
            venues = json.load(f)
    except Exception:
        # Fallback to hardcoded venues
        venues = get_fallback_venues()
    
    # Apply business logic filters
    filtered = []
    for venue in venues:
        # Indoor requirement check
        if indoor_required and not is_indoor(venue):
            continue
        
        # Vibe matching (simple tag-based)
        venue_tags = [t.lower() for t in venue.get("tags", [])]
        if vibe.lower() and not any(vibe.lower() in tag for tag in venue_tags):
            continue
            
        filtered.append(venue)
    
    # Sort by price and return top 3
    filtered.sort(key=lambda x: x.get("avg_price", 999))
    return filtered[:3]
```

**Local Processing Benefits:**
- **No External Calls** - Pure local data processing
- **Business Logic** - Encapsulates venue filtering rules
- **Fast Execution** - No network latency
- **Reliable** - No dependency on external services
- **Fallback Data** - Hardcoded backup venue options

### **4. LLM Client (MCP Local Service Integration)**

```python
# foodie_agents/llm_client.py
def structured_json(schema: Type[T], system_prompt: str, user_prompt: str) -> T:
    """MCP tool for Ollama LLM integration with structured output."""
    
    prompt = f"{system_prompt}\n\nUser:\n{user_prompt}"
    
    try:
        config = get_ollama_config()
        resp = requests.post(
            _ollama_url(),
            json={
                "model": config.model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": float(os.getenv("LLM_TEMPERATURE", "0.3"))}
            },
            timeout=config.timeout
        )
        resp.raise_for_status()
        response_text = resp.json().get("response", "")
        
        # Parse and validate structured output
        return schema.model_validate_json(response_text)
        
    except Exception as e:
        raise LLMError(f"LLM request failed: {e}")
```

**MCP Benefits:**
- **Service Integration** - Standardized Ollama communication
- **Structured Output** - Schema validation and parsing
- **Error Handling** - Consistent error reporting
- **Configuration** - Centralized LLM settings

### **5. A2A Communication (Budget Service Integration)**

```python
# foodie_agents/tools.py
def call_budget_service(budget: float, stops: int) -> Dict[str, Any]:
    """A2A communication with external budget service."""
    
    # Input validation
    if budget <= 0 or stops <= 0:
        return {
            "per_stop": [],
            "per_person_total": budget,
            "buffer_pct": 0.1,
            "error": "Invalid budget or stops parameters"
        }
    
    # External service call (A2A communication)
    try:
        response = requests.post(
            f"{config.url}/split_budget",
            json={"budget_per_person": budget, "stops": stops},
            timeout=config.timeout
        )
        response.raise_for_status()
        
        # Validate and return response
        result = response.json()
        if validate_budget_response(result):
            return result
        else:
            raise ValueError("Invalid response format from budget service")
            
    except Exception as e:
        # Fallback to local budget logic
        return local_budget_split(budget, stops)
```

**A2A Communication Benefits:**
- **Service Abstraction** - Hides FastAPI service complexity
- **Response Validation** - Ensures data integrity
- **Timeout Handling** - Manages service response times
- **Local Fallback** - Provides backup allocation logic
- **Independent Process** - External service with its own lifecycle

## Tool Abstraction Layer

### **Tool Registration & Discovery**

```python
# foodie_agents/tools.py
from typing import Dict, Any, Callable
from functools import wraps

class MCPToolRegistry:
    """Registry for MCP tools in the system."""
    
    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self.descriptions: Dict[str, str] = {}
    
    def register_tool(self, name: str, func: Callable, description: str):
        """Register an MCP tool."""
        self.tools[name] = func
        self.descriptions[name] = description
    
    def get_tool(self, name: str) -> Callable:
        """Get an MCP tool by name."""
        if name not in self.tools:
            raise ValueError(f"Unknown tool: {name}")
        return self.tools[name]
    
    def list_tools(self) -> Dict[str, str]:
        """List all available MCP tools."""
        return self.descriptions.copy()

# Global tool registry
tool_registry = MCPToolRegistry()

# Tool decorator for automatic registration
def mcp_tool(name: str, description: str):
    """Decorator to register MCP tools automatically."""
    def decorator(func: Callable) -> Callable:
        tool_registry.register_tool(name, func, description)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Add tool usage tracing
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Log successful tool usage
                logger.info(f"Tool {name} executed successfully in {execution_time:.2f}s")
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                # Log tool failure
                logger.error(f"Tool {name} failed after {execution_time:.2f}s: {e}")
                raise
        
        return wrapper
    return decorator

# Usage example
@mcp_tool("weather_tool", "Get weather data for tour planning")
def get_weather(date: str) -> Dict[str, Any]:
    # Tool implementation...
    pass
```

### **Tool Input/Output Validation**

```python
# foodie_agents/tools.py
from pydantic import BaseModel, ValidationError

class WeatherToolInput(BaseModel):
    date: str
    city: str = "Chicago"
    country: str = "US"

class WeatherToolOutput(BaseModel):
    precip_prob: float
    condition: str
    indoor_required: bool
    source: str
    timestamp: str
    error: str = None

def get_weather_validated(date: str, city: str = "Chicago", country: str = "US") -> WeatherToolOutput:
    """MCP tool with Pydantic validation."""
    
    try:
        # Validate input
        input_data = WeatherToolInput(date=date, city=city, country=country)
        
        # Call actual tool
        result = get_weather_impl(input_data.date, input_data.city, input_data.country)
        
        # Validate output
        output_data = WeatherToolOutput(**result)
        return output_data
        
    except ValidationError as e:
        # Return error with validation details
        return WeatherToolOutput(
            precip_prob=0.0,
            condition="unknown",
            indoor_required=False,
            source="validation_error",
            timestamp=datetime.now().isoformat(),
            error=f"Validation error: {e}"
        )
```

## External Service Integration

### **1. API Client Abstraction**

```python
# foodie_agents/tools.py
class APIClient:
    """Abstract base class for API clients."""
    
    def __init__(self, base_url: str, timeout: int = 10):
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
    
    def get(self, endpoint: str, params: Dict = None) -> Dict[str, Any]:
        """Make GET request with error handling."""
        try:
            response = self.session.get(
                f"{self.base_url}{endpoint}",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            raise Exception(f"API timeout after {self.timeout}s")
        except requests.exceptions.ConnectionError:
            raise Exception("API connection failed")
        except requests.exceptions.HTTPError as e:
            raise Exception(f"API error: {e.response.status_code}")
        except Exception as e:
            raise Exception(f"Unexpected API error: {e}")
    
    def post(self, endpoint: str, data: Dict = None) -> Dict[str, Any]:
        """Make POST request with error handling."""
        try:
            response = self.session.post(
                f"{self.base_url}{endpoint}",
                json=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            raise Exception(f"API timeout after {self.timeout}s")
        except requests.exceptions.ConnectionError:
            raise Exception("API connection failed")
        except requests.exceptions.HTTPError as e:
            raise Exception(f"API error: {e.response.status_code}")
        except Exception as e:
            raise Exception(f"Unexpected API error: {e}")

# Weather API client
class WeatherAPIClient(APIClient):
    """Client for Open-Meteo weather API."""
    
    def __init__(self):
        super().__init__("https://api.open-meteo.com", timeout=10)
    
    def get_forecast(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Get weather forecast for location."""
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": "precipitation_probability_max",
            "timezone": "auto"
        }
        return self.get("/v1/forecast", params)

# Budget service client
class BudgetServiceClient(APIClient):
    """Client for budget allocation service."""
    
    def __init__(self, base_url: str):
        super().__init__(base_url, timeout=5)
    
    def split_budget(self, budget: float, stops: int) -> Dict[str, Any]:
        """Split budget across stops."""
        data = {
            "budget_per_person": budget,
            "stops": stops
        }
        return self.post("/split_budget", data)
```

### **2. Local Data Source Abstraction**

```python
# foodie_agents/tools.py
class VenueDataSource:
    """Abstract data source for venue information."""
    
    def __init__(self, data_path: str = None):
        self.data_path = data_path or "foodie_agents/data/chicago_venues.json"
        self._venues = None
    
    def load_venues(self) -> List[Dict[str, Any]]:
        """Load venues from data source."""
        if self._venues is None:
            try:
                with open(self.data_path, 'r') as f:
                    self._venues = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load venues from {self.data_path}: {e}")
                self._venues = self._get_fallback_venues()
        
        return self._venues
    
    def _get_fallback_venues(self) -> List[Dict[str, Any]]:
        """Provide fallback venue data."""
        return [
            {
                "name": "The Violet Hour",
                "vibe": "cozy",
                "indoor_compliant": True,
                "avg_price": 45.0,
                "rating": 4.8,
                "tags": ["cocktails", "speakeasy", "romantic"]
            },
            {
                "name": "Mott Street",
                "vibe": "cozy",
                "indoor_compliant": False,
                "avg_price": 27.0,
                "rating": 4.6,
                "tags": ["asian_fusion", "patio", "creative"]
            }
        ]
    
    def filter_venues(self, vibe: str, indoor_required: bool, max_price: float = None) -> List[Dict[str, Any]]:
        """Filter venues by criteria."""
        venues = self.load_venues()
        
        filtered = []
        for venue in venues:
            if venue["vibe"] != vibe:
                continue
            
            if indoor_required and not venue["indoor_compliant"]:
                continue
            
            if max_price and venue["avg_price"] > max_price:
                continue
            
            filtered.append(venue)
        
        # Sort by rating and price
        filtered.sort(key=lambda x: (x["rating"], -x["avg_price"]))
        return filtered[:3]
```

## Tool Validation & Fallbacks

### **1. Response Validation**

```python
# foodie_agents/tools.py
def validate_budget_response(response: Dict[str, Any]) -> bool:
    """Validate budget service response."""
    required_fields = ["per_stop", "per_person_total"]
    
    # Check required fields
    if not all(field in response for field in required_fields):
        return False
    
    # Validate data types
    if not isinstance(response["per_stop"], list):
        return False
    
    if not isinstance(response["per_person_total"], (int, float)):
        return False
    
    # Validate business logic
    if sum(response["per_stop"]) > response["per_person_total"]:
        return False
    
    return True

def validate_weather_response(response: Dict[str, Any]) -> bool:
    """Validate weather API response."""
    required_fields = ["precip_prob", "condition", "indoor_required"]
    
    # Check required fields
    if not all(field in response for field in required_fields):
        return False
    
    # Validate data types
    if not isinstance(response["precip_prob"], (int, float)):
        return False
    
    if not isinstance(response["condition"], str):
        return False
    
    if not isinstance(response["indoor_required"], bool):
        return False
    
    # Validate business logic
    if response["precip_prob"] < 0 or response["precip_prob"] > 100:
        return False
    
    return True
```

### **2. Fallback Logic**

```python
# foodie_agents/tools.py
def local_budget_split(budget: float, stops: int) -> Dict[str, Any]:
    """Local fallback for budget allocation."""
    
    if stops <= 0:
        return {"per_stop": [], "per_person_total": budget, "buffer_pct": 0.1}
    
    # Simple weighted allocation
    weights = [0.5, 0.3, 0.2]  # First stop gets 50%, second 30%, third 20%
    
    per_stop = []
    remaining_budget = budget * 0.9  # 10% buffer
    
    for i in range(min(stops, len(weights))):
        if i < len(weights):
            amount = remaining_budget * weights[i]
        else:
            amount = remaining_budget / (stops - i)
        
        per_stop.append(round(amount, 2))
        remaining_budget -= amount
    
    return {
        "per_stop": per_stop,
        "per_person_total": budget,
        "buffer_pct": 0.1,
        "source": "local_fallback"
    }

def get_fallback_venues(vibe: str, indoor_required: bool, max_price: float = None) -> List[Dict[str, Any]]:
    """Fallback venue data when local source fails."""
    
    fallback_venues = [
        {
            "name": "The Violet Hour",
            "vibe": "cozy",
            "indoor_compliant": True,
            "avg_price": 45.0,
            "rating": 4.8,
            "tags": ["cocktails", "speakeasy", "romantic"]
        },
        {
            "name": "Mott Street",
            "vibe": "cozy",
            "indoor_compliant": False,
            "avg_price": 27.0,
            "rating": 4.6,
            "tags": ["asian_fusion", "patio", "creative"]
        },
        {
            "name": "Girl & The Goat",
            "vibe": "cozy",
            "indoor_compliant": True,
            "avg_price": 18.0,
            "rating": 4.7,
            "tags": ["new_american", "farm_to_table", "creative"]
        }
    ]
    
    # Apply filters
    filtered = []
    for venue in fallback_venues:
        if venue["vibe"] != vibe:
            continue
        
        if indoor_required and not venue["indoor_compliant"]:
            continue
        
        if max_price and venue["avg_price"] > max_price:
            continue
        
        filtered.append(venue)
    
    return filtered[:3]
```

## Best Practices

### **1. Tool Design Principles**

```python
# foodie_agents/tools.py
# ✅ Good: Tool handles all external complexity
@mcp_tool("weather_tool", "Get weather data for tour planning")
def get_weather(date: str) -> Dict[str, Any]:
    """Tool that completely abstracts weather API complexity."""
    
    # Input validation
    if not date:
        return get_default_weather()
    
    # External API call
    try:
        result = weather_api_client.get_forecast(date)
        return process_weather_data(result)
    except Exception:
        return get_default_weather()

# ❌ Bad: Agent making direct API calls
class WeatherAgent(Agent):
    async def run(self, state: FoodieState) -> FoodieState:
        # Agent should NOT make direct API calls
        response = requests.get("https://api.weather.com/forecast")  # ❌
        # ... rest of agent logic
```

### **2. Error Handling Patterns**

```python
# foodie_agents/tools.py
def robust_tool_call(func: Callable, *args, **kwargs) -> Any:
    """Robust tool execution with comprehensive error handling."""
    
    start_time = time.time()
    
    try:
        # Execute tool
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        
        # Log success
        logger.info(f"Tool {func.__name__} succeeded in {execution_time:.2f}s")
        return result
        
    except requests.exceptions.Timeout:
        execution_time = time.time() - start_time
        logger.warning(f"Tool {func.__name__} timed out after {execution_time:.2f}s")
        return get_fallback_result(func.__name__)
        
    except requests.exceptions.ConnectionError:
        execution_time = time.time() - start_time
        logger.error(f"Tool {func.__name__} connection failed after {execution_time:.2f}s")
        return get_fallback_result(func.__name__)
        
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"Tool {func.__name__} failed after {execution_time:.2f}s: {e}")
        return get_fallback_result(func.__name__)

# Usage in tools
@mcp_tool("weather_tool", "Get weather data for tour planning")
def get_weather(date: str) -> Dict[str, Any]:
    """Tool with robust error handling."""
    return robust_tool_call(get_weather_impl, date)
```

### **3. Performance Optimization**

```python
# foodie_agents/tools.py
from functools import lru_cache
import time

class ToolPerformanceOptimizer:
    """Performance optimization for MCP tools."""
    
    def __init__(self):
        self.cache_ttl = 300  # 5 minutes
        self.cache = {}
    
    def cached_call(self, tool_name: str, func: Callable, *args, **kwargs):
        """Cache tool results for performance."""
        
        # Create cache key
        cache_key = f"{tool_name}:{hash(str(args) + str(kwargs))}"
        
        # Check cache
        if cache_key in self.cache:
            cached_result, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return cached_result
        
        # Execute tool
        result = func(*args, **kwargs)
        
        # Cache result
        self.cache[cache_key] = (result, time.time())
        
        return result

# Global optimizer
tool_optimizer = ToolPerformanceOptimizer()

# Usage in tools
@mcp_tool("venue_tool", "Filter venues by criteria")
def filter_venues(vibe: str, indoor_required: bool) -> List[Dict[str, Any]]:
    """Tool with performance optimization."""
    return tool_optimizer.cached_call(
        "venue_tool",
        filter_venues_impl,
        vibe,
        indoor_required
    )
```

## Summary

**Model Context Protocol (MCP) tools** in Foodie Agents provide:

### **Key Benefits:**
1. **Tool Abstraction** - Agents never make direct HTTP calls
2. **Standardized Interfaces** - Consistent tool patterns across the system
3. **Fallback Handling** - Local logic when external services fail
4. **Type Safety** - Pydantic models for input/output validation
5. **Observability** - Complete tracing of tool usage and performance

### **Implementation Patterns:**
1. **API Client Abstraction** - Standardized HTTP client patterns
2. **Data Source Abstraction** - Local and remote data handling
3. **Response Validation** - Ensure data integrity and business logic
4. **Fallback Logic** - Graceful degradation when services fail

### **Best Practices:**
1. **Complete Abstraction** - Tools handle all external complexity
2. **Comprehensive Error Handling** - Graceful degradation with fallbacks
3. **Input/Output Validation** - Ensure data integrity
4. **Performance Optimization** - Caching and efficient execution
5. **Observability** - Complete tracing and monitoring

### **Current Communication Patterns:**
1. **MCP Tools:** Weather API (External), LLM Client (Local)
2. **Local Processing:** Venue filtering (Local JSON, business logic)
3. **A2A Communication:** Budget Service (External FastAPI, Port 8089)

The Foodie Agents system demonstrates **enterprise-grade MCP tool integration** with robust error handling, comprehensive validation, and scalable architecture!
