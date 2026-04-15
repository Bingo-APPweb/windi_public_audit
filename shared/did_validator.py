#!/usr/bin/env python3
"""
§173 DID SIMPLIFICATION — Universal DID Validator
=================================================
SINGLE SOURCE OF TRUTH for DID validation across all WINDI services.

Usage:
    from shared.did_validator import validate_did, DIDResult

    result = await validate_did("did:windi:dragon-001")
    if result.valid:
        print(f"Tier: {result.tier}")  # ORACLE

Principle: "Um DID. Uma fonte. Zero fallbacks."

Liga IA+H · Kempten, Bavaria · 2026
"""

import os
import logging
from dataclasses import dataclass
from typing import Optional, List
import httpx

log = logging.getLogger("windi.did")

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION — Single Source
# ═══════════════════════════════════════════════════════════════════════════════

DID_GENESIS_URL = os.getenv("WINDI_DID_GENESIS", "http://localhost:8096")
DID_LOOKUP_ENDPOINT = "/api/genesis/lookup/{did}"
DID_TIMEOUT_SECONDS = 5

# ═══════════════════════════════════════════════════════════════════════════════
# RESULT MODEL
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class DIDResult:
    """Result of DID validation against Genesis."""
    valid: bool
    did: str
    active: bool = False
    tier: Optional[str] = None
    tier_level: int = 0
    tier_emoji: str = ""
    access: List[str] = None
    display_name: str = ""
    role: str = ""
    created_at: Optional[str] = None
    last_seen: Optional[str] = None
    error: Optional[str] = None
    source: str = "W-DID-GENESIS"

    def __post_init__(self):
        if self.access is None:
            self.access = []

    @property
    def is_oracle(self) -> bool:
        return self.tier == "ORACLE"

    @property
    def is_sovereign(self) -> bool:
        return self.tier in ("SOVEREIGN", "ORACLE")

    @property
    def has_full_access(self) -> bool:
        return "*" in self.access

    def can_access(self, path: str) -> bool:
        """Check if DID can access a given path."""
        if "*" in self.access:
            return True
        return any(path.startswith(allowed) for allowed in self.access)


# ═══════════════════════════════════════════════════════════════════════════════
# VALIDATION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

async def validate_did(did: str) -> DIDResult:
    """
    Validate a DID against W-DID-GENESIS.

    This is THE ONLY function any WINDI service should use for DID validation.
    No fallbacks. No graceful degradation. Explicit failure (I14).

    Args:
        did: The DID to validate (e.g., "did:windi:dragon-001")

    Returns:
        DIDResult with validation status and tier information

    Raises:
        Never raises — returns DIDResult with valid=False on error
    """
    # Basic format check
    if not did or len(did) < 10:
        return DIDResult(
            valid=False,
            did=did or "",
            error="DID inválido ou muito curto"
        )

    if not did.startswith("did:windi:"):
        return DIDResult(
            valid=False,
            did=did,
            error="DID deve começar com 'did:windi:'"
        )

    # Call Genesis — Single Source of Truth
    url = f"{DID_GENESIS_URL}{DID_LOOKUP_ENDPOINT.format(did=did)}"

    try:
        async with httpx.AsyncClient(timeout=DID_TIMEOUT_SECONDS) as client:
            r = await client.get(url)

            if r.status_code == 200:
                data = r.json()

                if data.get("valid"):
                    log.info(f"DID validated: {did[:25]}... → tier={data.get('tier')}")
                    return DIDResult(
                        valid=True,
                        did=did,
                        active=data.get("active", True),
                        tier=data.get("tier", "SEED"),
                        tier_level=data.get("tier_level", 1),
                        tier_emoji=data.get("tier_emoji", "🌱"),
                        access=data.get("access", []),
                        display_name=data.get("display_name", ""),
                        role=data.get("role", ""),
                        created_at=data.get("created_at"),
                        last_seen=data.get("last_seen"),
                        source=data.get("source", "W-DID-GENESIS")
                    )
                else:
                    log.warning(f"DID not found in Genesis: {did[:25]}...")
                    return DIDResult(
                        valid=False,
                        did=did,
                        error=data.get("error", "DID não encontrado na Genesis")
                    )
            else:
                log.error(f"Genesis returned HTTP {r.status_code}")
                return DIDResult(
                    valid=False,
                    did=did,
                    error=f"Genesis error: HTTP {r.status_code}"
                )

    except httpx.ConnectError:
        log.error("Genesis unavailable — cannot validate DID")
        return DIDResult(
            valid=False,
            did=did,
            error="W-DID-GENESIS offline — validação impossível [I14]"
        )
    except Exception as e:
        log.error(f"DID validation error: {e}")
        return DIDResult(
            valid=False,
            did=did,
            error=f"Validation error: {str(e)}"
        )


def validate_did_sync(did: str) -> DIDResult:
    """
    Synchronous version of validate_did for non-async contexts.

    Use the async version when possible for better performance.
    """
    import asyncio

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(validate_did(did))


def validate_did_format(did: str) -> bool:
    """
    Quick format check without calling Genesis.

    Use this ONLY for preliminary validation before calling validate_did().
    This does NOT confirm the DID exists — only that the format is correct.
    """
    if not did or len(did) < 15:
        return False
    if not did.startswith("did:windi:"):
        return False
    # Must have something after the prefix
    identifier = did[10:]  # After "did:windi:"
    return len(identifier) >= 5


# ═══════════════════════════════════════════════════════════════════════════════
# FRONTEND STORAGE KEY — Single Standard
# ═══════════════════════════════════════════════════════════════════════════════

# All WINDI frontends should use this single key
FRONTEND_DID_KEY = "windi_did"

# JavaScript snippet for frontend (copy to any WINDI frontend):
FRONTEND_JS_SNIPPET = """
// §173 DID SIMPLIFICATION — Frontend Standard
// Use this in ALL WINDI frontends

const WINDI_DID_KEY = 'windi_did';

function getWindiDID() {
    return localStorage.getItem(WINDI_DID_KEY) || null;
}

function setWindiDID(did) {
    if (did) {
        localStorage.setItem(WINDI_DID_KEY, did);
    } else {
        localStorage.removeItem(WINDI_DID_KEY);
    }
}

function clearWindiDID() {
    localStorage.removeItem(WINDI_DID_KEY);
}

// Validate DID against Genesis
async function validateWindiDID(did) {
    const resp = await fetch(`/api/genesis/lookup/${encodeURIComponent(did)}`);
    return await resp.json();
}
"""


# ═══════════════════════════════════════════════════════════════════════════════
# TIER CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

class DIDTier:
    """DID tier constants for comparison."""
    SEED = "SEED"           # Level 1 — Basic access
    NODAL = "NODAL"         # Level 2 — Extended access
    SOVEREIGN = "SOVEREIGN" # Level 3 — Full service access
    ORACLE = "ORACLE"       # Level 4 — God mode

    LEVELS = {
        SEED: 1,
        NODAL: 2,
        SOVEREIGN: 3,
        ORACLE: 4
    }

    @classmethod
    def level(cls, tier: str) -> int:
        return cls.LEVELS.get(tier, 0)

    @classmethod
    def is_at_least(cls, tier: str, minimum: str) -> bool:
        return cls.level(tier) >= cls.level(minimum)


# ═══════════════════════════════════════════════════════════════════════════════
# MODULE INFO
# ═══════════════════════════════════════════════════════════════════════════════

__version__ = "1.0.0"
__author__ = "Liga IA+H"
__doc_section__ = "§173"
