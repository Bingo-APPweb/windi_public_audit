"""
W-COST-001 Hook Module
=======================
Import this module in W-GATEWAY to automatically record costs.

Usage in windi-gateway/server.py:
    from w_cost_001.cost_hook import record_cost_async

    # After LLM call:
    await record_cost_async(
        service="W-GATEWAY",
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        tokens_in=response["usage"]["input_tokens"],
        tokens_out=response["usage"]["output_tokens"],
        tier="HIGH",
        task_type="legal"
    )

Liga IA+H · 15 Abril 2026
"""

import httpx
import logging
from typing import Optional

log = logging.getLogger("w-cost-hook")

COST_API_URL = "http://127.0.0.1:8152/api/cost/record"


async def record_cost_async(
    service: str,
    provider: str,
    model: str,
    tokens_in: int,
    tokens_out: int,
    tier: str = "FREE",
    wallet_id: Optional[str] = None,
    task_type: Optional[str] = None,
) -> bool:
    """
    Record cost event to W-COST-001.
    Non-blocking, fails silently if service unavailable.
    """
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.post(COST_API_URL, json={
                "service": service,
                "provider": provider,
                "model": model,
                "tier": tier,
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "wallet_id": wallet_id,
                "task_type": task_type,
            })
            if resp.status_code == 200:
                log.debug(f"Cost recorded: {tokens_in}+{tokens_out} tokens")
                return True
    except Exception as e:
        log.warning(f"Cost recording failed (non-critical): {e}")
    return False


def record_cost_sync(
    service: str,
    provider: str,
    model: str,
    tokens_in: int,
    tokens_out: int,
    tier: str = "FREE",
    wallet_id: Optional[str] = None,
    task_type: Optional[str] = None,
) -> bool:
    """
    Synchronous version of record_cost.
    Use in non-async contexts.
    """
    import requests
    try:
        resp = requests.post(COST_API_URL, json={
            "service": service,
            "provider": provider,
            "model": model,
            "tier": tier,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "wallet_id": wallet_id,
            "task_type": task_type,
        }, timeout=2.0)
        return resp.status_code == 200
    except Exception as e:
        log.warning(f"Cost recording failed (non-critical): {e}")
    return False


# Pricing reference for manual calculation if needed
PRICING = {
    "claude-opus-4-5-20251101": {"input": 15.0, "output": 75.0},
    "claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},
    "claude-haiku-3-5-20241022": {"input": 0.25, "output": 1.25},
    "mistral-large-latest": {"input": 2.0, "output": 6.0},
    "mistral-small-latest": {"input": 0.2, "output": 0.6},
}


def estimate_cost(model: str, tokens_in: int, tokens_out: int) -> float:
    """Estimate cost in EUR without recording."""
    pricing = PRICING.get(model, {"input": 3.0, "output": 15.0})
    cost_in = (tokens_in / 1_000_000) * pricing["input"]
    cost_out = (tokens_out / 1_000_000) * pricing["output"]
    return round(cost_in + cost_out, 6)
