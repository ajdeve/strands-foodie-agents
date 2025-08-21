# foodie_agents/llm_client.py
from __future__ import annotations
import json
import os
from typing import Type
from pydantic import BaseModel, ValidationError
import requests
from foodie_agents.config import get_ollama_config

class LLMError(Exception):
    ...

def _ollama_url() -> str:
    config = get_ollama_config()
    base = config.base_url.rstrip("/")
    return f"{base}/api/generate"

def structured_json(schema: Type[BaseModel], system_prompt: str, user_prompt: str) -> BaseModel:
    """
    Call Ollama /api/generate and expect ONLY a JSON object back; validate with Pydantic.
    """
    prompt = (
        f"{system_prompt}\n\n"
        "Return ONLY a valid JSON object. Do not include code fences or extra text.\n\n"
        f"User:\n{user_prompt}"
    )
    try:
        config = get_ollama_config()
        resp = requests.post(
            _ollama_url(),
            json={
                "model": config.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": float(os.getenv("LLM_TEMPERATURE", "0.3"))
                }
            },
            timeout=config.timeout
        )
        resp.raise_for_status()
        text = resp.json().get("response", "{}")
        data = json.loads(text)
        return schema.model_validate(data)
    except (ValidationError, ValueError) as e:
        raise LLMError(f"JSON validation failed: {e}") from e
    except Exception as e:
        raise LLMError(str(e)) from e

def simple_text(system_prompt: str, user_prompt: str, max_chars: int = 2000) -> str:
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
        
        # Validate we got actual content
        if not response_text or response_text.strip() == "":
            raise LLMError("LLM returned empty response")
            
        return response_text[:max_chars]
        
    except requests.exceptions.Timeout:
        raise LLMError(f"LLM request timed out after {config.timeout}s")
    except requests.exceptions.ConnectionError:
        raise LLMError("LLM service connection failed")
    except requests.exceptions.HTTPError as e:
        raise LLMError(f"LLM service error: {e.response.status_code}")
    except json.JSONDecodeError as e:
        raise LLMError(f"Invalid JSON response from LLM: {e}")
    except Exception as e:
        raise LLMError(f"Unexpected LLM error: {e}")
