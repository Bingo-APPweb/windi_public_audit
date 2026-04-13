# ═══════════════════════════════════════════════
# W-CACHE-001 · KEY GENERATOR
# Deterministic cache key with temporal binding
# ═══════════════════════════════════════════════

import hashlib
from typing import Optional


def normalize(value: Optional[str]) -> str:
    """Normalize value for key generation - empty string if None"""
    return value or ""


def generate_cache_key(
    namespace: str,
    tier: str,
    input_hash: Optional[str] = None,
    context_hash: Optional[str] = None,
    policy_hash: Optional[str] = None,
    actor_did: Optional[str] = None,
    tenant_id: Optional[str] = None,
    timeline_id: Optional[str] = None,
    state_version: Optional[int] = None,
    version: str = "v1"
) -> str:
    """
    Generate deterministic cache key.

    🔥 CRITICAL: Key includes timeline_id + state_version
    This guarantees temporal consistency - impossible to reuse
    cache from different timeline or state version.
    """
    raw = "|".join([
        namespace,
        tier,
        normalize(input_hash),
        normalize(context_hash),
        normalize(policy_hash),
        normalize(actor_did),
        normalize(tenant_id),
        normalize(timeline_id),
        str(state_version or 0),
        version
    ])

    return hashlib.sha256(raw.encode()).hexdigest()


def generate_cache_key_from_dict(data: dict) -> str:
    """Generate cache key from dictionary input"""
    timeline = data.get("timeline", {})

    return generate_cache_key(
        namespace=data.get("namespace", ""),
        tier=data.get("tier", ""),
        input_hash=data.get("input_hash"),
        context_hash=data.get("context_hash"),
        policy_hash=data.get("policy_hash"),
        actor_did=data.get("actor_did"),
        tenant_id=data.get("tenant_id"),
        timeline_id=timeline.get("timeline_id") if isinstance(timeline, dict) else data.get("timeline_id"),
        state_version=timeline.get("state_version") if isinstance(timeline, dict) else data.get("state_version"),
        version="v1"
    )
