"""
W-SEC-001 Security Sentinel — Canonicalization
Deterministic serialization for hash computation.
"""

import hashlib
import json
from typing import Any


def canonical_json(data: Any) -> str:
    """
    Produce canonical JSON for hash computation.
    - Sorted keys
    - No whitespace
    - UTF-8
    """
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str  # Handle datetime and other non-serializable types
    )


def sha256_hex(data: str) -> str:
    """Compute SHA-256 hex digest."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def hash_for_indicator(*parts: str) -> str:
    """
    Create indicator hash from multiple parts.
    Used for correlation keys and actor fingerprints.
    """
    raw = "|".join(str(p) for p in parts if p)
    return sha256_hex(raw)
