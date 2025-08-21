"""Budget Agent for external budget management integration."""

import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
import uvicorn
# OpenTelemetry imports (optional - will work without them)
try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.propagate import extract
    from opentelemetry import trace
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Budget Agent", version="0.1.0")
if OTEL_AVAILABLE:
    FastAPIInstrumentor().instrument_app(app)  # server spans


class BudgetRequest(BaseModel):
    """Request model for budget operations."""
    user_id: str
    budget_type: str  # "daily", "weekly", "monthly"
    amount: float
    currency: str = "USD"
    category: str = "dining"


class BudgetResponse(BaseModel):
    """Response model for budget operations."""
    request: BudgetRequest
    success: bool
    message: str
    remaining_budget: float
    timestamp: str


class BudgetSplitRequest(BaseModel):
    """Request model for budget splitting."""
    budget_per_person: float
    stops: int


class BudgetSplitResponse(BaseModel):
    """Response model for budget splitting."""
    per_stop: List[float]
    per_person_total: float
    buffer_pct: float = 0.1


class BudgetAgent:
    """Agent for managing dining budgets and spending limits."""
    
    def __init__(self):
        self.name = "BudgetAgent"
        self.budgets: Dict[str, Dict[str, Any]] = {}
        logger.info(f"Initialized {self.name}")
    
    def split_budget(self, budget_per_person: float, stops: int) -> BudgetSplitResponse:
        """Split budget across restaurant stops with 10% buffer."""
        # Apply 10% buffer
        buffer_amount = budget_per_person * 0.1
        available_budget = budget_per_person - buffer_amount
        
        if stops <= 3:
            # Use weighted split: [0.5, 0.3, 0.2] for up to 3 stops
            weights = [0.5, 0.3, 0.2][:stops]
            # Normalize weights to sum to 1
            total_weight = sum(weights)
            weights = [w / total_weight for w in weights]
            
            per_stop = [available_budget * weight for weight in weights]
        else:
            # Even split for more than 3 stops
            per_stop = [available_budget / stops] * stops
        
        return BudgetSplitResponse(
            per_stop=per_stop,
            per_person_total=budget_per_person,
            buffer_pct=0.1
        )
    
    async def set_budget(self, request: BudgetRequest) -> BudgetResponse:
        """Set a budget for a user."""
        logger.info(f"Setting budget for user: {request.user_id}")
        
        budget_key = f"{request.user_id}_{request.budget_type}_{request.category}"
        
        self.budgets[budget_key] = {
            "amount": request.amount,
            "currency": request.currency,
            "category": request.category,
            "budget_type": request.budget_type,
            "created_at": datetime.now().isoformat(),
            "spent": 0.0
        }
        
        return BudgetResponse(
            request=request,
            success=True,
            message=f"Budget set successfully: {request.amount} {request.currency} for {request.budget_type} {request.category}",
            remaining_budget=request.amount,
            timestamp=datetime.now().isoformat()
        )
    
    async def check_budget(self, user_id: str, amount: float, budget_type: str = "daily", category: str = "dining") -> Dict[str, Any]:
        """Check if a purchase fits within the user's budget."""
        logger.info(f"Checking budget for user: {user_id}")
        
        budget_key = f"{user_id}_{budget_type}_{category}"
        budget = self.budgets.get(budget_key)
        
        if not budget:
            return {
                "has_budget": False,
                "can_afford": True,
                "remaining": 0.0,
                "message": "No budget set for this period/category"
            }
        
        remaining = budget["amount"] - budget["spent"]
        can_afford = remaining >= amount
        
        return {
            "has_budget": True,
            "can_afford": can_afford,
            "remaining": remaining,
            "message": f"Budget: {budget['amount']} {budget['currency']}, Spent: {budget['spent']}, Remaining: {remaining}"
        }
    
    async def record_expense(self, user_id: str, amount: float, budget_type: str = "daily", category: str = "dining") -> Dict[str, Any]:
        """Record an expense against the user's budget."""
        logger.info(f"Recording expense for user: {user_id}")
        
        budget_key = f"{user_id}_{budget_type}_{category}"
        budget = self.budgets.get(budget_key)
        
        if not budget:
            return {
                "success": False,
                "message": "No budget found for this period/category"
            }
        
        budget["spent"] += amount
        remaining = budget["amount"] - budget["spent"]
        
        return {
            "success": True,
            "message": f"Expense recorded: {amount} {budget['currency']}",
            "remaining_budget": remaining,
            "total_spent": budget["spent"]
        }
    
    async def get_budget_summary(self, user_id: str) -> Dict[str, Any]:
        """Get a summary of all budgets for a user."""
        logger.info(f"Getting budget summary for user: {user_id}")
        
        user_budgets = {}
        for key, budget in self.budgets.items():
            if key.startswith(f"{user_id}_"):
                budget_type = budget["budget_type"]
                category = budget["category"]
                if budget_type not in user_budgets:
                    user_budgets[budget_type] = {}
                
                user_budgets[budget_type][category] = {
                    "total": budget["amount"],
                    "spent": budget["spent"],
                    "remaining": budget["amount"] - budget["spent"],
                    "currency": budget["currency"]
                }
        
        return {
            "user_id": user_id,
            "budgets": user_budgets,
            "timestamp": datetime.now().isoformat()
        }


# Global budget agent instance
budget_agent = BudgetAgent()


@app.middleware("http")
async def otel_context(request: Request, call_next):
    """Ensure incoming traceparent is honored."""
    if OTEL_AVAILABLE:
        ctx = extract(request.headers)
        token = trace.set_span_in_context(trace.get_current_span(), ctx)
        try:
            response = await call_next(request)
        finally:
            pass
        return response
    else:
        return await call_next(request)


@app.post("/split_budget", response_model=BudgetSplitResponse)
async def split_budget(request: BudgetSplitRequest):
    """Split budget across restaurant stops."""
    try:
        result = budget_agent.split_budget(request.budget_per_person, request.stops)
        logger.info(f"Budget split: {request.budget_per_person} across {request.stops} stops")
        return result
        
    except Exception as e:
        logger.error(f"Budget split failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Budget Agent Service", "endpoints": ["/split_budget", "/health"]}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8089)
