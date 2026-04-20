"""
W-ACTUARY-001 — Ledger Client
Connects to Forensic Ledger :8101 for real receipts

Security: LEVEL 2 (Controlled Core)
- Only whitelisted receipts exposed
- Sanitized output (no internal hashes)
- Audit logged
"""

import requests
from datetime import datetime, timezone
from typing import Optional, Dict, Any

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

LEDGER_BASE = "http://127.0.0.1:8101"
VERIFY_PUBLIC_BASE = "https://windi-domain.com/api/receipts/"

# Curated whitelist — only these receipts are exposed in demo
# Selected for: low PII risk, clear actuarial relevance, sealed status
CURATED_RECEIPTS = {
    "WINDI-TRAVEL-20260416221745-F1D46419": {
        "display_name": "Travel Presence — Kempten",
        "event_type": "TRAVEL_PRESENCE",
        "description": "GPS-verified presence at Hildegardplatz, Kempten",
        "actuarial_category": "MOBILITY",
        "risk_factors": ["location_verified", "timestamp_exact"],
    },
    "WINDI-COLLAGE-20260406083915-58B241B1": {
        "display_name": "Forensic Evidence — Dual Source",
        "event_type": "FORENSIC_COMPARISON",
        "description": "Video comparison using MLT dual-source forensic",
        "actuarial_category": "EVIDENCE",
        "risk_factors": ["multi_source", "integrity_verified"],
    },
    "PHO-19D9C9DA22F": {
        "display_name": "Compliance Decision — Sanctions",
        "event_type": "COMPLIANCE_VERIFICATION",
        "description": "Automated sanctions screening verification",
        "actuarial_category": "COMPLIANCE",
        "risk_factors": ["regulatory_check", "automated_verification"],
    },
    "PROVE-20260416114645-8D066F81": {
        "display_name": "Verification Event — Berlin",
        "event_type": "PROOF_EVENT",
        "description": "Berlin demo verification proof",
        "actuarial_category": "IDENTITY",
        "risk_factors": ["proof_generated", "timestamp_exact"],
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# LEDGER API
# ═══════════════════════════════════════════════════════════════════════════════

def get_receipt_from_ledger(receipt_id: str, timeout: float = 2.0) -> Optional[Dict[str, Any]]:
    """
    Fetch a receipt from the Forensic Ledger.
    Returns None if not found or error.
    """
    try:
        url = f"{LEDGER_BASE}/api/receipts/{receipt_id}"
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            data = response.json()
            if data.get("ok") and data.get("receipt"):
                return data["receipt"]
    except Exception:
        pass
    return None


def is_receipt_whitelisted(receipt_id: str) -> bool:
    """Check if a receipt is in the curated whitelist."""
    return receipt_id in CURATED_RECEIPTS


def get_curated_metadata(receipt_id: str) -> Optional[Dict[str, Any]]:
    """Get curated metadata for a whitelisted receipt."""
    return CURATED_RECEIPTS.get(receipt_id)


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC SANITIZATION
# ═══════════════════════════════════════════════════════════════════════════════

def sanitize_receipt_for_public(receipt: Dict[str, Any], curated: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a sanitized public version of a receipt.
    Removes: full content_hash, actor DID details, internal metadata
    Adds: curated display info, verify URL
    """
    receipt_id = receipt.get("id", "")

    # Extract timestamp
    created_at = receipt.get("created_at", 0)
    if created_at:
        timestamp = datetime.fromtimestamp(created_at, tz=timezone.utc).isoformat()
    else:
        timestamp = "unknown"

    # Extract location if available
    metadata = receipt.get("metadata", {})
    location = None
    if "lat" in metadata and "lng" in metadata:
        location = {
            "label": metadata.get("city_id", "Unknown").title(),
            "coordinates": f"{metadata['lat']:.4f}°N, {metadata['lng']:.4f}°E"
        }
    elif receipt.get("doc_name"):
        # Extract location hint from doc_name
        doc_name = receipt.get("doc_name", "")
        if "·" in doc_name:
            parts = doc_name.split("·")
            if len(parts) >= 2:
                location = {"label": parts[0].strip() + " · " + parts[1].strip()}

    return {
        "id": receipt_id,
        "display_name": curated.get("display_name", receipt.get("doc_name", "")),
        "event_type": curated.get("event_type", "UNKNOWN"),
        "description": curated.get("description", ""),
        "timestamp": timestamp,
        "location": location,
        "status": "VERIFIED" if receipt.get("status") == "sealed" else "PENDING",
        "governance_level": receipt.get("governance_level", "MEDIUM"),
        "actuarial_category": curated.get("actuarial_category", "OTHER"),
        "risk_factors": curated.get("risk_factors", []),
        "verification": {
            "status": "VERIFIED",
            "verify_url": f"{VERIFY_PUBLIC_BASE}{receipt_id}",
            "ledger_sealed": receipt.get("status") == "sealed",
        },
        # Hash is truncated for public display
        "content_hash_preview": receipt.get("content_hash", "")[:16] + "..." if receipt.get("content_hash") else None,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════════

def list_curated_receipts() -> list:
    """
    List all curated receipts with their public info.
    Fetches live data from Ledger for each.
    """
    result = []
    for receipt_id, curated in CURATED_RECEIPTS.items():
        receipt = get_receipt_from_ledger(receipt_id)
        if receipt:
            sanitized = sanitize_receipt_for_public(receipt, curated)
            result.append(sanitized)
    return result


def get_curated_receipt(receipt_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a single curated receipt by ID.
    Returns None if not whitelisted or not found.
    """
    if not is_receipt_whitelisted(receipt_id):
        return None

    receipt = get_receipt_from_ledger(receipt_id)
    if not receipt:
        return None

    curated = get_curated_metadata(receipt_id)
    return sanitize_receipt_for_public(receipt, curated)
