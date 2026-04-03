"""
W-VD-CUT-001 — Seal Service
Ledger integration with I9 gate and I11 compliance

I9: human_approved=true MUST be verified before ANY seal
I11: Only content_hash goes to Ledger, NEVER raw video content

Liga IA+H · Kempten, Bavaria · 2026
"""

import os
import httpx
import logging
from datetime import datetime, timezone
from typing import Dict, Any

LEDGER_URL = os.environ.get("LEDGER_URL", "http://127.0.0.1:8101")
VERIFY_URL = os.environ.get("VERIFY_URL", "https://windi-domain.com/verify-public/")
TIMEOUT = 15.0

log = logging.getLogger("w-vd-cut-001.seal")


async def health_check() -> bool:
    """Check if Ledger is healthy."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{LEDGER_URL}/health",
                timeout=5.0
            )
            return response.status_code == 200
    except Exception as e:
        log.warning(f"Ledger health check failed: {e}")
        return False


def generate_verify_url(receipt_id: str) -> str:
    """Generate public verification URL."""
    return f"{VERIFY_URL}?id={receipt_id}"


def generate_qr_payload(receipt_id: str, content_hash: str) -> str:
    """
    Generate QR code payload.
    Format: WINDI:{receipt_id}|{hash[:16]}
    """
    hash_short = content_hash.replace("sha256:", "")[:16]
    return f"WINDI:{receipt_id}|{hash_short}"


async def seal_to_ledger(
    wallet_id: str,
    content_hash: str,
    project_id: str,
    title: str = None,
    duration: float = None,
    resolution: str = None,
    metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Seal video export to Forensic Ledger.

    CRITICAL I11 COMPLIANCE:
    - Only the content_hash goes to Ledger
    - Never raw video content or file data
    - The hash proves integrity without exposing content

    CRITICAL I9 COMPLIANCE:
    - Caller MUST verify human_approved=true before calling
    - This function trusts that I9 gate was passed

    Args:
        wallet_id: WINDI DID of the actor
        content_hash: SHA-256 hash of the video file (I11)
        project_id: VD-CUT project ID
        title: Video title
        duration: Video duration in seconds
        resolution: Video resolution (e.g., "1080x1920")
        metadata: Additional metadata

    Returns:
        Receipt dict with receipt_id, verify_url, qr_payload
        Or error dict if seal fails
    """
    import uuid

    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y%m%d%H%M%S")

    # Generate receipt ID
    receipt_id = f"WINDI-VDCUT-{timestamp}-{uuid.uuid4().hex[:8].upper()}"

    # Build receipt payload - I11 compliant (hash only, no content)
    receipt_payload = {
        "id": receipt_id,
        "receipt_id": receipt_id,
        "actor": wallet_id,
        "app": "w-vd-cut-001",
        "doc_name": title or f"Video Moment {project_id}",
        "doc_type": "doc",  # Ledger-compatible type (video metadata in metadata field)
        "governance_level": "MEDIUM",
        "content_hash": content_hash,  # I11: ONLY hash, never content
        "invariants": ["I9", "I11"],
        "stage": "C6",  # Sealed
        "sealed_at": now.isoformat(),
        "witness": "W-VD-CUT-001 — WINDI Video Cut Engine",
        "metadata": {
            "project_id": project_id,
            "duration_seconds": duration,
            "resolution": resolution,
            "source": "telegram_nomad_bot",
            "human_approved": True,  # I9 gate was passed
            **(metadata or {})
        },
        "sge_score": 0.7  # Default SGE score for video seals
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{LEDGER_URL}/api/receipts",
                json=receipt_payload,
                timeout=TIMEOUT
            )

            if response.status_code in (200, 201):
                data = response.json()

                # Normalize response
                final_receipt_id = data.get("id") or data.get("receipt_id") or receipt_id
                verify_url = generate_verify_url(final_receipt_id)
                qr_payload = generate_qr_payload(final_receipt_id, content_hash)

                log.info(f"Ledger seal created: {final_receipt_id}")

                return {
                    "success": True,
                    "receipt_id": final_receipt_id,
                    "verify_url": verify_url,
                    "qr_payload": qr_payload,
                    "sealed_at": now.isoformat(),
                    "content_hash": content_hash
                }

            else:
                log.error(f"Ledger error: {response.status_code} - {response.text[:200]}")
                return {
                    "error": True,
                    "status_code": response.status_code,
                    "message": f"Ledger seal failed: HTTP {response.status_code}"
                }

    except httpx.TimeoutException:
        log.error("Ledger timeout")
        return {
            "error": True,
            "message": "Ledger timeout - please try again"
        }

    except httpx.ConnectError:
        log.error("Ledger connection failed")
        return {
            "error": True,
            "message": "Ledger unavailable"
        }

    except Exception as e:
        log.error(f"Ledger exception: {e}")
        return {
            "error": True,
            "message": str(e)
        }


async def verify_seal(receipt_id: str) -> Dict[str, Any]:
    """
    Verify a seal exists in the Ledger.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{LEDGER_URL}/api/receipts/{receipt_id}",
                timeout=TIMEOUT
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "exists": True,
                    "receipt": data,
                    "verify_url": generate_verify_url(receipt_id)
                }
            else:
                return {
                    "exists": False,
                    "status_code": response.status_code
                }

    except Exception as e:
        log.error(f"Verify exception: {e}")
        return {
            "error": True,
            "message": str(e),
            "exists": False
        }
