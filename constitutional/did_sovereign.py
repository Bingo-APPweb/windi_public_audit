"""
did_sovereign.py — DECREE-001 Article 4: DID Cross-Validation
Supreme DID validation endpoint for the Living Tree.

"One DID, one identity, the whole tree."

Endpoint: /api/did/validate/{did}
Port: 8101 (via Forensic Ledger — the TRUNK)

Liga IA+H · 12 Abril 2026
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from enum import Enum

import httpx

log = logging.getLogger("windi.did.sovereign")


# ═══════════════════════════════════════════════════════════════════════════
# DID Tiers — The Four Levels of Trust
# ═══════════════════════════════════════════════════════════════════════════

class DIDTier(Enum):
    SEED = "SEED"           # Just registered, unverified
    NODAL = "NODAL"         # Email verified
    SOVEREIGN = "SOVEREIGN" # Human Dragon verified
    ORACLE = "ORACLE"       # Cross-validated across multiple organs


# Tier hierarchy (higher = more trust)
TIER_HIERARCHY = {
    DIDTier.SEED: 1,
    DIDTier.NODAL: 2,
    DIDTier.SOVEREIGN: 3,
    DIDTier.ORACLE: 4,
}


# ═══════════════════════════════════════════════════════════════════════════
# Identity Gates — Sources of DID Validation
# ═══════════════════════════════════════════════════════════════════════════

IDENTITY_GATES = [
    {
        "id": "windi_law",
        "name": "WINDI-LAW",
        "port": 8122,
        "endpoint": "/identity/{did}",
        "tier_mapping": {
            "VERIFIED": DIDTier.SOVEREIGN,
            "PROVISIONAL": DIDTier.SEED,
            "EMAIL_PENDING": DIDTier.NODAL,
        },
    },
    {
        "id": "wallet",
        "name": "WINDI Wallet",
        "port": 8099,
        "endpoint": "/api/wallet/did/{did}",
        "tier_mapping": {
            "ACTIVE": DIDTier.NODAL,
            "VERIFIED": DIDTier.SOVEREIGN,
        },
    },
    {
        "id": "travel",
        "name": "WINDI Travel",
        "port": 8126,
        "endpoint": "/api/identity/{did}",
        "tier_mapping": {
            "VERIFIED": DIDTier.SOVEREIGN,
            "ACTIVE": DIDTier.NODAL,
        },
    },
]


# ═══════════════════════════════════════════════════════════════════════════
# Organ Access Matrix — What each tier can access
# ═══════════════════════════════════════════════════════════════════════════

ORGAN_ACCESS = {
    DIDTier.SEED: [
        "/verify-public/",  # Always public
    ],
    DIDTier.NODAL: [
        "/verify-public/",
        "/wallet/",
        "/travel/",
    ],
    DIDTier.SOVEREIGN: [
        "/verify-public/",
        "/wallet/",
        "/travel/",
        "/law/",
        "/enterprise/",
    ],
    DIDTier.ORACLE: [
        "/verify-public/",
        "/wallet/",
        "/travel/",
        "/law/",
        "/enterprise/",
        "/sec/dashboard/",
        "/dev-api/",
    ],
}


# ═══════════════════════════════════════════════════════════════════════════
# DID Validation Functions
# ═══════════════════════════════════════════════════════════════════════════

async def validate_did_at_gate(did: str, gate: dict) -> Optional[Dict[str, Any]]:
    """
    Validate DID at a specific identity gate.
    Returns validation result or None if not found.
    """
    url = f"http://localhost:{gate['port']}{gate['endpoint'].format(did=did)}"

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(url)

            if r.status_code == 200:
                data = r.json()

                # Extract state from response
                state = data.get("state") or data.get("status", "").upper()

                # Map state to tier
                tier = gate["tier_mapping"].get(state, DIDTier.SEED)

                return {
                    "valid": True,
                    "gate": gate["id"],
                    "gate_name": gate["name"],
                    "state": state,
                    "tier": tier,
                    "data": data,
                }

            return None

    except Exception as e:
        log.debug(f"[DID] Gate {gate['name']} unavailable: {e}")
        return None


async def cross_validate_did(did: str) -> Dict[str, Any]:
    """
    §173 SIMPLIFIED: Single Source of Truth — W-DID-GENESIS.

    Replaced complex multi-gate validation with direct Genesis lookup.
    "Um DID. Uma fonte. Zero fallbacks."

    DECREE-001 Article 4 still applies — now enforced at Genesis level.
    """
    if not did or not did.startswith("did:windi:"):
        return {
            "valid": False,
            "error": "invalid_did_format",
            "message": "DID must start with 'did:windi:'",
            "tier": None,
            "accessible_organs": [],
        }

    # §173 — Single Source: W-DID-GENESIS
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"http://localhost:8096/api/genesis/lookup/{did}")
            if resp.status_code == 200:
                data = resp.json()
                if data.get("valid"):
                    tier_str = data.get("tier", "SEED")
                    tier = DIDTier(tier_str) if tier_str in [t.value for t in DIDTier] else DIDTier.SEED
                    tier_level = TIER_HIERARCHY.get(tier, 1)
                    accessible_organs = ORGAN_ACCESS.get(tier, ORGAN_ACCESS[DIDTier.SEED])

                    return {
                        "valid": True,
                        "did": did,
                        "tier": tier.value,
                        "tier_level": tier_level,
                        "accessible_organs": accessible_organs,
                        "source": "W-DID-GENESIS",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "decree": "DECREE-001-LIVING-TREE",
                        "article": "Article 4 (§173 Simplified)",
                        "principle": "Um DID. Uma fonte. Zero fallbacks.",
                    }
    except Exception as e:
        log.warning(f"[DID] Genesis lookup failed: {e}")

    # DID not found or Genesis unavailable
    return {
        "valid": False,
        "error": "did_not_found",
        "message": "DID not recognized by W-DID-GENESIS",
        "did": did,
        "tier": None,
        "accessible_organs": ORGAN_ACCESS[DIDTier.SEED],
        "source": "W-DID-GENESIS",
        "decree": "DECREE-001-LIVING-TREE",
    }


def validate_did_format(did: str) -> bool:
    """Quick format validation without network calls."""
    if not did:
        return False
    if not did.startswith("did:windi:"):
        return False
    if len(did) < 15:
        return False
    return True


def get_tier_info(tier: DIDTier) -> Dict[str, Any]:
    """Get information about a DID tier."""
    descriptions = {
        DIDTier.SEED: {
            "name": "SEED",
            "name_full": "Seed Identity",
            "level": 1,
            "description": "Initial registration, pending verification",
            "icon": "🌱",
        },
        DIDTier.NODAL: {
            "name": "NODAL",
            "name_full": "Nodal Identity",
            "level": 2,
            "description": "Email verified, basic access",
            "icon": "🌿",
        },
        DIDTier.SOVEREIGN: {
            "name": "SOVEREIGN",
            "name_full": "Sovereign Identity",
            "level": 3,
            "description": "Human Dragon verified, full access",
            "icon": "🌳",
        },
        DIDTier.ORACLE: {
            "name": "ORACLE",
            "name_full": "Oracle Identity",
            "level": 4,
            "description": "Cross-validated across multiple organs, maximum trust",
            "icon": "🏛",
        },
    }
    return descriptions.get(tier, {})


# ═══════════════════════════════════════════════════════════════════════════
# Synchronous wrapper for non-async contexts
# ═══════════════════════════════════════════════════════════════════════════

def validate_did_sync(did: str) -> Dict[str, Any]:
    """Synchronous wrapper for cross_validate_did."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(cross_validate_did(did))
    finally:
        loop.close()
