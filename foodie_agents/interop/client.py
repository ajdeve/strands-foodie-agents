"""Budget client for A2A communication with trace context propagation."""

import requests
from opentelemetry.propagate import inject


def call_budget(url: str, payload: dict) -> dict:
    """Call budget service with trace context propagation."""
    headers = {"Content-Type": "application/json"}
    inject(headers)  # adds W3C traceparent so server joins the same trace
    r = requests.post(url, json=payload, headers=headers, timeout=15)
    r.raise_for_status()
    return r.json()
