# Foodie Agents - AI-Powered Food Tour Planning

> **Multi-agent AI system for intelligent food tour planning using Strands framework, A2A routing, MCP tool adapters, and comprehensive observability with Langfuse tracing.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Strands Framework](https://img.shields.io/badge/strands-framework-green.svg)](https://github.com/strands-ai/strands)
[![Langfuse](https://img.shields.io/badge/langfuse-observability-orange.svg)](https://langfuse.com/)

## Overview

Foodie Agents is a multi-agent AI system that creates personalized food tours using advanced agent orchestration, LLM-powered planning, and comprehensive observability. Built on the **Strands framework** with **Agent-to-Agent (A2A) routing**, **Model Context Protocol (MCP) tool adapters**, and **Langfuse tracing** for complete system visibility.

## Architecture

### **Core Framework: Strands**
- **Multi-agent orchestration** with intelligent routing
- **Asynchronous execution** for optimal performance
- **Type-safe agent communication** with Pydantic models
- **Built-in observability** with OpenTelemetry integration

### **Agent-to-Agent (A2A) Communication**
- **Explicit typed messages** (`Task`, `Assignment`, `Result`)
- **Correlation IDs** for end-to-end request tracing
- **Structured data flow** between specialized agents
- **LLM-powered routing decisions** with business rule validation

### **Model Context Protocol (MCP) Tools**
- **Weather API integration** via MCP adapters
- **Venue filtering** with intelligent criteria matching
- **Budget service integration** with external FastAPI microservice
- **Tool abstraction** - agents never make direct HTTP calls

### **Observability Stack**
- **Langfuse** for trace collection and analysis
- **OpenTelemetry** for distributed tracing
- **Structured reasoning capture** for all agent decisions
- **Performance metrics** and execution timing

## Agent Architecture

### **Actual Implementation Flow**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PlannerLLMAgent (Orchestrator)                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐ │
│  │   LLM Planning  │  │ Business Rules  │  │    Sequential Execution     │ │
│  │  (Ollama)       │  │  Validation     │  │   (Step-by-step)           │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Agent Execution Chain                          │
│                                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │ Researcher  │─▶│    Scout    │─▶│   Budget    │─▶│   Writer    │       │
│  │ (Weather)   │  │ (Venues)    │  │ (Split)     │  │ (Content)   │       │
│  │ [MCP Tool]  │  │ [MCP Tool]  │  │ [Service]   │  │ [LLM]      │       │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘       │
│                                                                             │
│  ┌─────────────┐                                                           │
│  │  Reviewer   │                                                           │
│  │ (Quality)   │                                                           │
│  │ [LLM]      │                                                           │
│  └─────────────┘                                                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

### **Data Flow Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Input    │───▶│  FoodieState    │───▶│  Planner Agent  │
│  (city, vibe,   │    │  (Pydantic)     │    │  (LLM + Rules)  │
│   budget, date) │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              MCP Tool Layer                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │ get_weather │  │filter_venues│  │call_budget  │  │  LLM Client │       │
│  │ (Open-Meteo)│  │ (Local JSON)│  │ _service    │  │ (Ollama)    │       │
│  │             │  │             │  │ (FastAPI)   │  │             │       │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘       │
└─────────────────────────────────────────────────────────────────────────────┘
                                                       │
                                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Langfuse Observability                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │ Tour Trace  │  │ Agent Spans │  │ LLM Calls   │  │  Reasoning  │       │
│  │ (Main)      │  │ (Sequential)│  │ (Input/Out) │  │ (Decisions) │       │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### **Agent Responsibilities**

| Agent | Purpose | LLM Usage | Key Features |
|-------|---------|-----------|--------------|
| **Planner** | Orchestrates workflow | ✅ Primary | LLM routing + business rules |
| **Researcher** | Weather analysis | ❌ None | API integration, deterministic logic |
| **Scout** | Venue selection | ❌ None | Filtering, vibe matching |
| **Budget** | Financial allocation | ❌ None | Weighted splits, buffer management |
| **Writer** | Content generation | ✅ Primary | Rich itinerary descriptions |
| **Reviewer** | Quality assessment | ⚠️ Fallback | Multi-criteria scoring |

## Quick Start

### **Prerequisites**
- Python 3.11+
- Ollama with `llama3:latest` model
- Langfuse Cloud account (free tier available)

### **Installation**

#### **Windows Users**
```cmd
# Clone the repository
git clone <your-repo-url>
cd strands-foodie-agents

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
copy .env.example .env
# Edit .env with your Langfuse and Ollama credentials
```

#### **macOS/Linux Users**
```bash
# Clone the repository
git clone <your-repo-url>
cd strands-foodie-agents

# Install dependencies
make setup

# Set up environment variables
cp .env.example .env
# Edit .env with your Langfuse and Ollama credentials
```

### **Environment Configuration**
```bash
# .env file
LANGFUSE_PUBLIC_KEY=your_public_key
LANGFUSE_SECRET_KEY=your_secret_key
LANGFUSE_HOST=https://cloud.langfuse.com

OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3:latest
OLLAMA_TIMEOUT=60
```

### **Run the System**

#### **Windows Users**
```cmd
# Start with reasoning analysis (recommended)
python -m foodie_agents.run_foodie

# Or run individual components
python -m foodie_agents.run_foodie              # Main application
python -m foodie_agents.interop.budget_agent    # Budget service (in separate terminal)
```

#### **macOS/Linux Users**
```bash
# Start with reasoning analysis (recommended)
make run-analyze

# Or run individual components
make run              # Main application
make run-budget-agent # Budget service
```

## Observability & Tracing

### **Langfuse Integration**
- **Complete trace visibility** for all agent interactions
- **LLM reasoning capture** with detailed decision analysis
- **Performance metrics** and execution timing
- **Business rule application** tracking

### **Actual Langfuse Trace Structure**

```
📊 foodie_tour (main trace)
├── 01_planner_workflow
│   ├── planner.llm_routing_reasoning  # LLM plan + business rules
│   ├── planner.llm_status             # LLM success/failure tracking
│   ├── planner.decisions              # 3-4 decision points
│   └── planner.final_workflow         # Normalized execution steps
├── 02_researcher_check_weather
│   ├── researcher.check_weather       # Open-Meteo API call
│   └── researcher.reasoning           # Indoor requirement logic
├── 03_scout_scout_venues
│   ├── scout.scout_venues             # Local JSON venue filtering
│   └── scout.reasoning                # Vibe + indoor compliance
├── 04_budget_split_budget
│   ├── budget.split_budget            # FastAPI service call
│   └── budget.reasoning               # Weighted allocation logic
├── 05_writer_write_itinerary
│   ├── writer.write_itinerary         # Ollama LLM content generation
│   └── writer.reasoning               # Content quality decisions
└── 06_reviewer_review
    ├── reviewer.review                 # Ollama LLM + scoring
    └── reviewer.reasoning              # Quality assessment logic
```

**Actual Trace Data:**
- **Trace ID:** `6fe53beafcce38c7a2a50c0fdfe4be62`
- **Total Spans:** 6 main agent executions
- **LLM Calls:** 3 successful (Planner, Writer, Reviewer)
- **Tool Calls:** 3 deterministic (Weather, Venues, Budget)
- **Execution Time:** ~3.2 seconds
- **Success Rate:** 100%

### **Reasoning Capture**
Every agent decision is captured with:
- **Decision criteria** and evidence
- **Confidence scores** and reasoning
- **Next action** flows
- **Execution timing** and performance

## LLM Integration

### **Planner Agent**
- **Structured JSON generation** for workflow planning
- **Business rule validation** and normalization
- **Fallback logic** for robust execution
- **Dependency enforcement** (weather → venues → budget → content → review)

### **Writer Agent**
- **Rich content generation** with venue-specific details
- **JSON schema validation** for structured output
- **Template fallback** for reliability

### **Reviewer Agent**
- **Multi-criteria scoring** (weather, variety, budget)
- **LLM rationale generation** with fallback
- **Quality assessment** and recommendations

## Development

### **Code Quality**

#### **Windows Users**
```cmd
# Lint code
python -m flake8 foodie_agents/

# Format code
python -m black foodie_agents/

# Run tests
python -m pytest tests/
```

#### **macOS/Linux Users**
```bash
# Lint code
make lint

# Format code
make format

# Run tests
make test
```

### **Project Structure**
```
strands-foodie-agents/
├── foodie_agents/
│   ├── __init__.py              # Public API exports
│   ├── strands_agents.py        # Core agent implementations
│   ├── types.py                 # Data models and interfaces
│   ├── tools.py                 # MCP tool adapters
│   ├── config.py                # Configuration management
│   ├── llm_client.py            # Ollama integration
│   ├── prompts.py               # LLM system prompts
│   ├── langfuse_integration.py  # Observability layer
│   ├── reasoning_analyzer.py    # Real-time analysis
│   ├── run_foodie.py            # Main application entry
│   └── interop/
│       ├── budget_agent.py      # FastAPI budget service
│       └── client.py            # External service client
├── Makefile                     # Build and run targets
├── pyproject.toml               # Project configuration
├── requirements.txt              # Dependencies
└── README.md                    # This file
```

## Performance & Reliability

### **Execution Metrics**
- **Typical execution time**: <4 seconds
- **Success rate**: 100% (with fallback logic)
- **LLM integration**: 3/3 agents use LLM successfully

### **Real Data Flow Example**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Venue Selection Flow                          │
│                                                                             │
│  Input: vibe="cozy", indoor_required=False                                │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐ │
│  │   Local JSON    │  │   Filter Logic  │  │      Top 3 Results         │ │
│  │   (12 venues)   │  │                 │  │                             │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘ │
│           │                       │                       │                 │
│           ▼                       ▼                       ▼                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐ │
│  │  The Violet Hour│  │   Mott Street   │  │    Girl & The Goat         │ │
│  │  (Wicker Park)  │  │  (Wicker Park)  │  │   (West Loop)             │ │
│  │  $45, indoor    │  │   $45, outdoor  │  │    $85, indoor            │ │
│  │  [cocktails,    │  │ [asian_fusion,  │  │ [new_american,            │ │
│  │   cozy,         │  │   cozy,         │  │   cozy, creative]         │ │
│  │   speakeasy]    │  │   creative]     │  │                             │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                              Budget Allocation Flow                        │
│                                                                             │
│  Input: $100 total, 3 stops                                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐ │
│  │   FastAPI       │  │  Weighted Split │  │      Final Allocation      │ │
│  │  Budget Service │  │   Algorithm     │  │                             │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘ │
│           │                       │                       │                 │
│           ▼                       ▼                       ▼                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐ │
│  │   $100 Input    │  │  10% Buffer     │  │  $45 + $27 + $18 = $90     │ │
│  │   (3 stops)     │  │  Applied        │  │  (Weighted by stop order)  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Windows-Specific Setup

### **Prerequisites for Windows**
- **Python 3.11+** installed and added to PATH
- **Git for Windows** for repository cloning
- **PowerShell** or **Command Prompt** (avoid Git Bash for Python commands)

### **Common Windows Issues & Solutions**

#### **1. Python Not Found**
```cmd
# Check if Python is in PATH
python --version

# If not found, add Python to PATH or use full path
C:\Users\YourUsername\AppData\Local\Programs\Python\Python311\python.exe --version
```

#### **2. Module Import Errors**
```cmd
# Always run from project root directory
cd C:\path\to\strands-foodie-agents

# Use module syntax for imports
python -m foodie_agents.run_foodie
```

#### **3. Environment Variables**
```cmd
# Windows environment variable syntax
set LANGFUSE_PUBLIC_KEY=your_key_here
set OLLAMA_BASE_URL=http://localhost:11434

# Or use .env file (recommended)
copy .env.example .env
# Edit .env with Notepad or your preferred editor
```

#### **4. Ollama on Windows**
- **WSL2** (Windows Subsystem for Linux) recommended for Ollama
- **Docker Desktop** alternative for containerized Ollama
- **Native Windows** Ollama support (experimental)
- **Decision confidence**: 90%+ across all agents

### **Fallback Mechanisms**
- **LLM failure handling** with deterministic fallbacks
- **Business rule enforcement** regardless of LLM output
- **Graceful degradation** for external service failures
- **Comprehensive error tracking** in Langfuse

## Configuration

### **LLM Settings**
```python
# Adjust creativity vs. consistency
LLM_TEMPERATURE=0.3  # Lower = more deterministic

# Model selection
OLLAMA_MODEL=llama3:latest  # or other Ollama models
```

### **Business Rules**
```python
# Workflow dependencies (enforced by normalization)
DEFAULT_ORDER = [
    "check_weather",      # Always first
    "scout_venues",       # After weather
    "split_budget",       # After venues
    "write_itinerary",    # After budget
    "review"              # Always last
]
```

## Key Features

### **Intelligent Planning**
- **LLM-powered workflow generation** with business rule validation
- **Dynamic step ordering** based on dependencies
- **Automatic plan normalization** for completeness

### **Robust Execution**
- **100% success rate** with intelligent fallbacks
- **Performance monitoring** and optimization
- **Error handling** and recovery

### **Complete Observability**
- **End-to-end tracing** for all operations
- **LLM reasoning capture** with detailed analysis
- **Performance metrics** and bottleneck identification
- **Business rule application** tracking

### **System Capabilities**
- **Type safety** with Python 3.11+ and Pydantic
- **Async execution** for optimal performance
- **External service integration** with MCP adapters
- **Comprehensive testing** and validation

## Use Cases

### **Food Tour Planning**
- **Personalized recommendations** based on vibe and budget
- **Weather-aware planning** for indoor/outdoor venues
- **Budget optimization** with intelligent allocation
- **Rich content generation** for customer experience

### **Agent System Development**
- **Strands framework** examples and patterns
- **A2A communication** best practices
- **MCP tool integration** patterns
- **Observability implementation** with Langfuse

### **LLM Integration**
- **Structured output generation** with validation
- **Business rule enforcement** post-LLM
- **Fallback mechanisms** for reliability
- **Reasoning capture** for transparency

## Contributing

1. **Fork** the repository
2. **Create** a feature branch
3. **Make** your changes
4. **Test** thoroughly
5. **Submit** a pull request

### **Development Setup**
```bash
# Install development dependencies
pip install -e ".[dev]"

# Run linting and formatting
make lint
make format

# Test the system
make run-analyze
```



## Acknowledgments

- **Strands AI** for the multi-agent framework
- **Langfuse** for observability tools
- **Ollama** for local LLM capabilities
- **OpenTelemetry** for distributed tracing standards

---

**Built with modern AI agent technologies**

*For questions and support, please open an issue or reach out to the maintainers.*

---

## TLDR: What Does This Foodie Agent Do?

**In simple terms:** This is an AI system that plans food tours for you automatically.

### **What You Get:**
- **Input:** Tell it your city, vibe preference (like "cozy"), and budget
- **Output:** A complete food tour plan with restaurant recommendations, budget allocation, and a written itinerary

### **How It Works:**
1. **Checks the weather** to decide if venues should be indoor/outdoor
2. **Finds restaurants** that match your vibe and budget
3. **Splits your budget** intelligently across the selected venues
4. **Writes a detailed itinerary** describing your food tour
5. **Reviews the plan** to ensure quality and completeness

### **Real Example:**
- **Input:** "Chicago, cozy vibe, $100 budget"
- **Output:** A 3-stop food tour with specific restaurants, budget allocation ($45 + $27 + $18), and a written description of your experience

### **Why It's Useful:**
- **Saves time** - No more researching restaurants manually
- **Smart planning** - Considers weather, vibe, and budget constraints
- **Complete package** - Gets you from idea to ready-to-use itinerary
- **Transparent** - You can see exactly how it made decisions

**Bottom line:** It's like having a personal food tour planner that works in seconds instead of hours.
