# ═══════════════════════════════════════════════
# W-CACHE-001 · CONTEXT HASH
# Deterministic context hashing for cache validity
# ═══════════════════════════════════════════════

import hashlib
import json
from typing import Any, Dict


def sort_object(obj: Any) -> Any:
    """Recursively sort object keys for deterministic serialization"""
    if isinstance(obj, dict):
        return {k: sort_object(v) for k, v in sorted(obj.items())}
    elif isinstance(obj, list):
        return [sort_object(item) for item in obj]
    return obj


def generate_context_hash(context: Dict[str, Any]) -> str:
    """
    Generate deterministic hash of context.

    Context includes things like:
    - did_status: "ACTIVE"
    - governance_level: "HIGH"
    - tenant_id: "bank-01"
    - document_stage: "REVIEW"
    - seal_state: "UNSEALED"
    - engine_version: "maria-1.8"
    - policy_version: "pho-004-v2"

    If ANY of these change, cache entry becomes invalid.
    """
    canonical = json.dumps(sort_object(context), separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def generate_state_hash(state: Dict[str, Any]) -> str:
    """Generate hash of complete state for timeline tracking"""
    return generate_context_hash(state)
