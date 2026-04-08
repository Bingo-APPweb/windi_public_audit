"""
W-SEC-001 Security Sentinel — Maestro Client
Creates and updates security incident cases in Maestro (:8106).
"""

import httpx
from typing import Dict, Any, Optional
from config import MAESTRO_URL


class MaestroClientError(Exception):
    """Error communicating with Maestro."""
    pass


async def create_security_case(
    incident_id: str,
    title: str,
    summary: str,
    severity: str,
    confidence: float,
    event_count: int,
    primary_vector: str,
    affected_assets: list,
    recommended_action: str,
    actor_fingerprint: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a security incident case in Maestro.

    This integrates W-SEC-001 with the existing case management system.
    """
    payload = {
        "case_type": "security_incident",
        "source": "w-sec-001",
        "incident_id": incident_id,
        "title": title,
        "summary": summary,
        "threat_level": severity,
        "confidence": confidence,
        "event_count": event_count,
        "threat_family": classify_threat_level(severity),
        "primary_vector": primary_vector,
        "affected_assets": affected_assets,
        "recommended_action": recommended_action,
        "actor_fingerprint": actor_fingerprint,
        "invariants": ["I9"],  # Requires human approval
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{MAESTRO_URL}/cases",
                json=payload
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.TimeoutException:
        raise MaestroClientError(f"Maestro timeout at {MAESTRO_URL}")
    except httpx.HTTPStatusError as e:
        # Maestro might not be running in MVP — graceful degradation
        if e.response.status_code == 404:
            return {"case_id": None, "status": "maestro_unavailable"}
        raise MaestroClientError(f"Maestro HTTP error: {e.response.status_code}")
    except Exception as e:
        # Graceful degradation if Maestro unavailable
        return {"case_id": None, "status": "maestro_unavailable", "error": str(e)}


async def update_security_case(
    case_id: str,
    updates: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update an existing security case.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.patch(
                f"{MAESTRO_URL}/cases/{case_id}",
                json=updates
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        return {"case_id": case_id, "status": "update_failed", "error": str(e)}


def classify_threat_level(severity: str) -> str:
    """
    Map severity to threat level for Maestro.
    """
    mapping = {
        "low": "T1",
        "medium": "T2",
        "high": "T3",
        "critical": "T4",
    }
    return mapping.get(severity, "T1")
