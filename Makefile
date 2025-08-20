.PHONY: help setup run run-budget-agent lint format obs-up obs-down clean

# Default target
help:
	@echo "Foodie Agents - Available targets:"
	@echo "  setup           - Install dependencies and setup environment"
	@echo "  run             - Run the main foodie agents application"
	@echo "  run-budget-agent - Run the budget agent demo"
	@echo "  lint            - Run linting with ruff"
	@echo "  format          - Format code with black"
	@echo "  smoke           - Run end-to-end smoke test"
	@echo "  smoke-export    - Run exporter smoke test"
	@echo "  export-dry      - Test exporter with dry-run"
	@echo "  export          - Export traces from Langfuse Cloud"
	@echo "  analyze         - Analyze reasoning data from trace files"
	@echo "  obs-up          - Start observability services (Postgres)"
	@echo "  obs-down        - Stop observability services"
	@echo "  clean           - Clean up generated files and containers"

# Setup environment and install dependencies
setup:
	@echo "Setting up Foodie Agents environment..."
	@echo "Checking Python version..."
	@python3 --version
	@echo "Installing dependencies..."
	uv sync || pip install -e .
	pip install -e ".[dev]"
	@echo "Setup complete!"

# Run the main application
run:
	@echo "Starting Foodie Agents application..."
	python -m foodie_agents.run_foodie --city Chicago --budget 100 --vibe cozy

# Run with real-time reasoning analysis
run-analyze:
	@echo "Starting Foodie Agents with reasoning analysis..."
	python -m foodie_agents.run_foodie --city Chicago --budget 100 --vibe cozy --analyze

# Run budget agent demo
run-budget-agent:
	@echo "Running Budget Agent demo..."
	uvicorn foodie_agents.interop.budget_agent:app --port 8089 --reload

# Lint code
lint:
	@echo "Running linting with ruff..."
	ruff lint .

# Format code
format:
	@echo "Formatting code with black..."
	black .

# Start observability services
obs-up:
	@echo "Starting observability services..."
	docker-compose up -d
	@echo "Waiting for services to be ready..."
	@echo "Postgres will be available on localhost:5432"
	@echo ""
	@echo "Postgres credentials:"
	@echo "  Database: foodie_agents"
	@echo "  Username: foodie_user"
	@echo "  Password: foodie_password"
	@echo ""
	@echo "Langfuse Cloud Setup:"
	@echo "1. Go to https://cloud.langfuse.com"
	@echo "2. Sign up for free tier account"
	@echo "3. Create a new project"
	@echo "4. Go to Project Settings > API Keys"
	@echo "5. Copy PUBLIC_KEY and SECRET_KEY"
	@echo "6. Update your .env file with these values"
	@echo ""
	@echo "Note: Langfuse Cloud provides free observability without infrastructure setup"

# Stop observability services
obs-down:
	@echo "Stopping observability services..."
	docker-compose down
	@echo "Services stopped"

# Clean up
clean:
	@echo "Cleaning up..."
	rm -rf __pycache__/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	@echo "Cleanup complete!"

# Show service status
status:
	@echo "Service status:"
	docker-compose ps
	@echo ""
	@echo "Postgres logs:"
	docker-compose logs postgres --tail=10

PYTHON ?= python

# Analysis
analyze: ## Run application with reasoning analysis
	@echo "🧠 Running with reasoning analysis..."
	@$(PYTHON) -m foodie_agents.run_foodie --city Chicago --budget 100 --vibe lively --analyze