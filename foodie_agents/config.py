"""Configuration management for Foodie Agents system."""

import os
from typing import Optional
from dataclasses import dataclass

@dataclass
class LangfuseConfig:
    """Langfuse observability configuration."""
    public_key: str
    secret_key: str
    host: str = "https://us.cloud.langfuse.com"
    
    @classmethod
    def from_env(cls) -> "LangfuseConfig":
        return cls(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY", ""),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY", ""),
            host=os.getenv("LANGFUSE_HOST", "https://us.cloud.langfuse.com")
        )

@dataclass
class OllamaConfig:
    """Ollama LLM configuration."""
    base_url: str = "http://localhost:11434"
    model: str = "llama3.2:3b"
    timeout: int = 30
    
    @classmethod
    def from_env(cls) -> "OllamaConfig":
        return cls(
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            model=os.getenv("OLLAMA_MODEL", "llama3.2:3b"),
            timeout=int(os.getenv("OLLAMA_TIMEOUT", "30"))
        )

@dataclass
class BudgetServiceConfig:
    """Budget service configuration."""
    url: str = "http://localhost:8001"
    timeout: int = 5
    
    @classmethod
    def from_env(cls) -> "BudgetServiceConfig":
        return cls(
            url=os.getenv("BUDGET_SERVICE_URL", "http://localhost:8001"),
            timeout=int(os.getenv("BUDGET_SERVICE_TIMEOUT", "5"))
        )

@dataclass
class AppConfig:
    """Main application configuration."""
    langfuse: LangfuseConfig
    ollama: OllamaConfig
    budget_service: BudgetServiceConfig
    debug: bool = False
    environment: str = "local-dev"
    
    @classmethod
    def from_env(cls) -> "AppConfig":
        return cls(
            langfuse=LangfuseConfig.from_env(),
            ollama=OllamaConfig.from_env(),
            budget_service=BudgetServiceConfig.from_env(),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            environment=os.getenv("ENVIRONMENT", "local-dev")
        )

# Global config instance (lazy loaded)
_config: Optional[AppConfig] = None

def _get_config() -> AppConfig:
    """Get or create the global config instance."""
    global _config
    if _config is None:
        _config = AppConfig.from_env()
    return _config

# Convenience accessors
def get_langfuse_config() -> LangfuseConfig:
    """Get Langfuse configuration."""
    return _get_config().langfuse

def get_ollama_config() -> OllamaConfig:
    """Get Ollama configuration."""
    return _get_config().ollama

def get_budget_service_config() -> BudgetServiceConfig:
    """Get budget service configuration."""
    return _get_config().budget_service

def is_debug() -> bool:
    """Check if debug mode is enabled."""
    return _get_config().debug

def get_environment() -> str:
    """Get current environment."""
    return _get_config().environment

# For backwards compatibility
def get_config() -> AppConfig:
    """Get the global config instance."""
    return _get_config()
