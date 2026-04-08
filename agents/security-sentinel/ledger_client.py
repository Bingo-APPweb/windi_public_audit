"""
W-SEC-001 Security Sentinel — Ledger Client
Anchors security incidents in the Forensic Ledger (:8101).
"""

import httpx
from typing import Dict, Any, Optional
from config import LEDGER_URL


class LedgerClientError(Exception):
    """Error communicating with Forensic Ledger."""
    pass


async def anchor_security_incident(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Anchor a security incident in the Forensic Ledger.

    Payload should contain:
    - type: "security_incident"
    - incident_id
    - hash
    - severity
    - confidence
    - event_count
    - summary

    Returns ledger response with receipt_id.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{LEDGER_URL}/api/receipts",
                json=payload
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.TimeoutException:
        raise LedgerClientError(f"Ledger timeout at {LEDGER_URL}")
    except httpx.HTTPStatusError as e:
        raise LedgerClientError(f"Ledger HTTP error: {e.response.status_code}")
    except Exception as e:
        raise LedgerClientError(f"Ledger error: {str(e)}")


async def verify_ledger_health() -> bool:
    """
    Check if Forensic Ledger is reachable.
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{LEDGER_URL}/health")
            return resp.status_code == 200
    except Exception:
        return False


def build_ledger_payload(
    incident_id: str,
    canonical_hash: str,
    severity: str,
    confidence: float,
    event_count: int,
    summary: str,
    created_at: str
) -> Dict[str, Any]:
    """
    Build canonical payload for ledger anchoring.

    This follows the WINDI receipt schema.
    """
    return {
        "type": "security_incident",
        "source": "w-sec-001",
        "incident_id": incident_id,
        "hash": f"sha256:{canonical_hash}",
        "severity": severity,
        "confidence": confidence,
        "event_count": event_count,
        "summary": summary,
        "created_at": created_at,
        "invariants": ["I9", "I11"],  # Human approval, permanent evidence
    }
