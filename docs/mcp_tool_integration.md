# MCP Tool Integration in Foodie Agents

> **Comprehensive guide to how Model Context Protocol (MCP) tools are implemented and utilized in the Foodie Agents system**

## Table of Contents

1. [Overview](#overview)
2. [MCP Architecture](#mcp-architecture)
3. [Tool Implementations](#tool-implementations)
4. [Tool Abstraction Layer](#tool-abstraction-layer)
5. [External Service Integration](#external-service-integration)
6. [Tool Validation & Fallbacks](#tool-validation--fallbacks)
7. [Best Practices](#best-practices)

## Overview

**Model Context Protocol (MCP) tools** in Foodie Agents provide a standardized way for agents to interact with external services and data sources. MCP tools act as **adapters** that abstract away the complexity of external APIs, databases, and services, allowing agents to focus on their core logic without making direct HTTP calls.

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
                                │ (No direct HTTP calls)
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MCP TOOL ADAPTERS                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   Weather Tool  │  │   Venue Tool    │  │  Budget Tool    │ │
│  │   (API Client)  │  │   (Data Filter) │  │  (Service)      │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                │ External Services
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                            │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  Open-Meteo    │  │  Local JSON     │  │  FastAPI       │ │
│  │  Weather API   │  │  Venue DB       │  │  Budget Service │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### **Core Principles**

1. **Agents Never Make Direct HTTP Calls** - All external communication goes through MCP tools
2. **Tool Abstraction** - Tools hide the complexity of external services
3. **Fallback Logic** - Local alternatives when external services fail
4. **Type Safety** - Input/output validation with Pydantic models
5. **Observability** - Complete tracing of tool usage and performance

## Tool Implementations

### **1. Weather Tool (MCP API Client)**

```python
# foodie_agents/tools.py
@tool(name="weather_tool", description="Get weather data for tour planning")
def get_weather(date: str) -> Dict[str, Any]:
    """MCP tool for weather data retrieval."""
    
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

### **2. Venue Tool (MCP Data Filter)**

```python
# foodie_agents/tools.py
@tool(name="venue_tool", description="Filter venues by criteria")
def filter_venues(vibe: str, indoor_required: bool, max_price: float = None) -> List[Dict[str, Any]]:
    """MCP tool for venue filtering and selection."""
    
    # Tool input validation
    if not vibe:
        return []
    
    if max_price is not None and max_price <= 0:
        return []
    
    try:
        # Load venue data (abstracted from agents)
        venues = load_local_venues()
        
        # Apply business logic filters
        filtered = []
        for venue in venues:
            # Vibe matching
            if venue["vibe"] != vibe:
                continue
            
            # Indoor requirement
            if indoor_required and not venue["indoor_compliant"]:
                continue
            
            # Price filtering
            if max_price and venue["avg_price"] > max_price:
                continue
            
            filtered.append(venue)
        
        # Sort by relevance and price
        filtered.sort(key=lambda x: (x["rating"], -x["avg_price"]))
        
        # Return top results
        return filtered[:3]
        
    except Exception as e:
        # Fallback to hardcoded venues (tool handles failure)
        return get_fallback_venues(vibe, indoor_required, max_price)
```

**MCP Benefits:**
- **Business Logic** - Tool encapsulates venue filtering rules
- **Data Loading** - Tool manages data source complexity
- **Sorting Logic** - Tool applies ranking algorithms
- **Fallback Data** - Tool provides backup venue options

### **3. Budget Tool (MCP Service Integration)**

```python
# foodie_agents/tools.py
@tool(name="budget_tool", description="Split budget across venues")
def call_budget_service(budget: float, stops: int) -> Dict[str, Any]:
    """MCP tool for budget allocation via external service."""
    
    # Tool input validation
    if budget <= 0 or stops <= 0:
        return {
            "per_stop": [],
            "per_person_total": budget,
            "buffer_pct": 0.1,
            "error": "Invalid budget or stops parameters"
        }
    
    # External service call (abstracted from agents)
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
        # Fallback to local budget logic (tool handles failure)
        return local_budget_split(budget, stops)
```

**MCP Benefits:**
- **Service Abstraction** - Tool hides FastAPI service complexity
- **Response Validation** - Tool ensures data integrity
- **Timeout Handling** - Tool manages service response times
- **Local Fallback** - Tool provides backup allocation logic

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

### **Current MCP Tools:**
1. **Weather Tool** - Open-Meteo API integration with fallback
2. **Venue Tool** - Local JSON data filtering with backup data
3. **Budget Tool** - FastAPI service integration with local logic

The Foodie Agents system demonstrates **enterprise-grade MCP tool integration** with robust error handling, comprehensive validation, and scalable architecture!
