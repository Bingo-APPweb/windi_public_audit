#!/usr/bin/env python3
"""
W-ACTUARY-001 — Verifiable Actuarial Intelligence Layer
Port: 8015 | Invariants: I9, I11, I14 | Version: 0.2.0 (HARDENED)

"We augment actuarial models with verifiable ground truth."

Security Level: LEVEL 2 (Controlled Core)
- Audit logging
- API key protection for sensitive endpoints
- Sanitized responses (no internal logic exposed)
- System fingerprint
- Request tracing
"""

import json
import hashlib
import secrets
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
from functools import wraps

from fastapi import FastAPI, HTTPException, Header, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

APP_VERSION = "0.2.0"
APP_NAME = "W-ACTUARY-001"
SYSTEM_ID = "W-ACTUARY-001@WINDI"
VERIFY_BASE_URL = "https://windi-domain.com/verify-public/?id="
DATA_PATH = Path(__file__).parent.parent / "demo_data" / "receipts.json"
AUDIT_LOG_PATH = Path(__file__).parent.parent / "logs" / "audit.log"

# API Key for protected endpoints (in production, use env var)
API_KEY = os.environ.get("WINDI_ACTUARY_KEY", "windi-actuary-demo-2026")

# Ensure logs directory exists
AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════════════════════════
# AUDIT LOGGING
# ═══════════════════════════════════════════════════════════════════════════════

def audit_log(event_type: str, details: dict, request: Request = None):
    """Write audit event to log file."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "system": SYSTEM_ID,
        "event": event_type,
        "details": details,
    }
    if request:
        entry["client_ip"] = request.client.host if request.client else "unknown"
        entry["user_agent"] = request.headers.get("user-agent", "unknown")[:100]

    try:
        with open(AUDIT_LOG_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass  # Silent fail for logging (don't break the app)


# ═══════════════════════════════════════════════════════════════════════════════
# SECURITY: API KEY VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════

async def verify_api_key(
    request: Request,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    """Verify API key for protected endpoints."""
    # Allow requests from same origin (browser frontend)
    origin = request.headers.get("origin", "")
    referer = request.headers.get("referer", "")

    if "windi-domain.com" in origin or "windi-domain.com" in referer:
        return True  # Same-origin request allowed

    if not x_api_key:
        audit_log("AUTH_FAILED", {"reason": "missing_key"}, request)
        raise HTTPException(status_code=401, detail="API key required")

    if not secrets.compare_digest(x_api_key, API_KEY):
        audit_log("AUTH_FAILED", {"reason": "invalid_key"}, request)
        raise HTTPException(status_code=403, detail="Invalid API key")

    return True


# ═══════════════════════════════════════════════════════════════════════════════
# FASTAPI APP
# ═══════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title=APP_NAME,
    description="Verifiable Actuarial Intelligence Layer",
    version=APP_VERSION,
    docs_url=None,  # Disable Swagger in production
    redoc_url=None,  # Disable ReDoc in production
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://windi-domain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)


# ═══════════════════════════════════════════════════════════════════════════════
# MODELS (PUBLIC — sanitized output)
# ═══════════════════════════════════════════════════════════════════════════════

class NormalizedEventInput(BaseModel):
    """Input for scoring (from frontend)."""
    receipt_id: str
    event_type: str
    event_class: str
    confidence: str
    time_precision: str
    location_anchored: bool
    risk_category: str
    base_weight: float
    content_hash: str
    timestamp: str


class PublicNormalizedEvent(BaseModel):
    """Sanitized normalized event (public output)."""
    receipt_id: str
    event_type: str
    event_class: str
    confidence: str
    time_precision: str
    location_anchored: bool
    risk_category: str
    timestamp: str
    # Note: base_weight and content_hash hidden from public response


class PublicRiskScore(BaseModel):
    """Sanitized risk score (public output)."""
    receipt_id: str
    risk_category: str
    adjustment_factor: float
    confidence: str
    verify_url: str
    scored_at: str
    explanation: str
    # Note: internal scoring details hidden


# ═══════════════════════════════════════════════════════════════════════════════
# DATA LOADING
# ═══════════════════════════════════════════════════════════════════════════════

def load_receipts() -> list[dict]:
    """Load demo receipts from JSON file."""
    if not DATA_PATH.exists():
        return []
    with open(DATA_PATH, "r") as f:
        return json.load(f)


def get_receipt_by_id(receipt_id: str) -> Optional[dict]:
    """Find a receipt by its ID."""
    receipts = load_receipts()
    for r in receipts:
        if r.get("id") == receipt_id:
            return r
    return None


def sanitize_receipt_for_list(r: dict) -> dict:
    """Sanitize receipt for public listing (LEVEL 2 protection)."""
    return {
        "id": r.get("id"),
        "event_type": r.get("event_type"),
        "location": r.get("location", "N/A"),
        "timestamp": r.get("timestamp", "N/A"),
        "verified": r.get("verified", False),
        # Removed: content_hash, actor, metadata
    }


# ═══════════════════════════════════════════════════════════════════════════════
# INTERNAL SCORING ENGINE (PRIVATE — never exposed)
# ═══════════════════════════════════════════════════════════════════════════════

# These constants are internal only
_EVENT_RISK_MAP = {
    "TRAVEL_MOVEMENT": {"category": "MOBILITY", "weight": 0.3},
    "HOTEL_CHECKIN": {"category": "ACCOMMODATION", "weight": 0.2},
    "MOBILITY_SEQUENCE": {"category": "MOBILITY", "weight": 0.35},
    "PAYMENT_VERIFIED": {"category": "FINANCIAL", "weight": 0.4},
    "DOCUMENT_SEALED": {"category": "LEGAL", "weight": 0.5},
    "PRESENCE_CONFIRMED": {"category": "IDENTITY", "weight": 0.25},
}

_CONFIDENCE_MULTIPLIERS = {
    "VERIFIED": 1.0,
    "WITNESSED": 0.85,
    "DECLARED": 0.5,
    "INFERRED": 0.3,
}


def _internal_normalize(receipt: dict) -> dict:
    """Internal normalization logic (PRIVATE)."""
    event_type = receipt.get("event_type", "UNKNOWN")
    risk_info = _EVENT_RISK_MAP.get(event_type, {"category": "OTHER", "weight": 0.5})

    confidence = "VERIFIED" if receipt.get("verified", False) else "DECLARED"
    timestamp = receipt.get("timestamp", "")
    time_precision = "EXACT" if timestamp else "APPROXIMATE"
    location = receipt.get("location", "")
    location_anchored = bool(location and location != "unknown")

    content_hash = receipt.get("content_hash", "")
    if not content_hash:
        hash_input = f"{receipt.get('id', '')}{timestamp}{event_type}"
        content_hash = f"sha256:{hashlib.sha256(hash_input.encode()).hexdigest()[:16]}"

    return {
        "receipt_id": receipt.get("id", "UNKNOWN"),
        "event_type": event_type,
        "event_class": "INSURABLE_EVENT",
        "confidence": confidence,
        "time_precision": time_precision,
        "location_anchored": location_anchored,
        "risk_category": risk_info["category"],
        "base_weight": risk_info["weight"],  # Internal only
        "content_hash": content_hash,  # Internal only
        "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
    }


def _internal_score(normalized: dict) -> dict:
    """Internal scoring logic (PRIVATE)."""
    confidence = normalized.get("confidence", "DECLARED")
    conf_mult = _CONFIDENCE_MULTIPLIERS.get(confidence, 0.5)

    loc_bonus = 0.1 if normalized.get("location_anchored") else 0.0
    time_bonus = 0.05 if normalized.get("time_precision") == "EXACT" else 0.0

    # Core algorithm (hidden from public)
    adjustment = 1.0 - (conf_mult * 0.2) - loc_bonus - time_bonus
    adjustment = max(0.5, min(1.0, adjustment))

    base = normalized.get("base_weight", 0.5)
    final = base * adjustment

    return {
        "receipt_id": normalized["receipt_id"],
        "risk_category": normalized["risk_category"],
        "base_weight": base,  # Internal
        "adjustment_factor": round(adjustment, 3),
        "final_score": round(final, 4),  # Internal
        "confidence": confidence,
        "verify_url": f"{VERIFY_BASE_URL}{normalized['receipt_id']}",
        "scored_at": datetime.now(timezone.utc).isoformat() + "Z",
    }


def _generate_explanation(confidence: str, adjustment: float) -> str:
    """Generate human-readable explanation (no internal details)."""
    if confidence == "VERIFIED":
        return "Risk adjusted based on cryptographically verified event data."
    elif confidence == "WITNESSED":
        return "Risk adjusted based on multi-attestation event data."
    else:
        return "Standard risk assessment applied to declared event."


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/health")
async def health_check(request: Request):
    """Health check endpoint (public)."""
    audit_log("HEALTH_CHECK", {}, request)
    return {
        "status": "healthy",
        "system": SYSTEM_ID,
        "version": APP_VERSION,
        "invariants": ["I9", "I11", "I14"],
        "security_level": "LEVEL_2",
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
    }


@app.get("/receipts")
async def list_receipts(request: Request):
    """List available receipts (sanitized)."""
    audit_log("LIST_RECEIPTS", {}, request)
    receipts = load_receipts()
    return [sanitize_receipt_for_list(r) for r in receipts]


@app.get("/normalize/{receipt_id}")
async def normalize_event(receipt_id: str, request: Request):
    """Normalize a receipt into an actuarial event (sanitized output)."""
    receipt = get_receipt_by_id(receipt_id)
    if not receipt:
        audit_log("NORMALIZE_NOT_FOUND", {"receipt_id": receipt_id}, request)
        raise HTTPException(status_code=404, detail="Receipt not found")

    normalized = _internal_normalize(receipt)
    audit_log("NORMALIZE_SUCCESS", {"receipt_id": receipt_id}, request)

    # Return full normalized data (needed for scoring)
    # but base_weight is intentionally generic in demo
    return normalized


@app.post("/score")
async def score_event(
    event: NormalizedEventInput,
    request: Request,
    _: bool = Depends(verify_api_key)
):
    """Score a normalized event (protected endpoint)."""
    internal_score = _internal_score(event.model_dump())

    audit_log("SCORE_CALCULATED", {
        "receipt_id": event.receipt_id,
        "confidence": event.confidence,
    }, request)

    # Return sanitized public response
    return {
        "receipt_id": internal_score["receipt_id"],
        "risk_category": internal_score["risk_category"],
        "adjustment_factor": internal_score["adjustment_factor"],
        "confidence": internal_score["confidence"],
        "verify_url": internal_score["verify_url"],
        "scored_at": internal_score["scored_at"],
        "explanation": _generate_explanation(
            internal_score["confidence"],
            internal_score["adjustment_factor"]
        ),
    }


@app.get("/demo/full-flow/{receipt_id}")
async def demo_full_flow(receipt_id: str, request: Request):
    """Demo endpoint: full pipeline (sanitized)."""
    receipt = get_receipt_by_id(receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")

    normalized = _internal_normalize(receipt)
    score = _internal_score(normalized)

    audit_log("DEMO_FLOW", {"receipt_id": receipt_id}, request)

    # Sanitized demo output
    return {
        "receipt": sanitize_receipt_for_list(receipt),
        "normalized": {
            "receipt_id": normalized["receipt_id"],
            "event_type": normalized["event_type"],
            "event_class": normalized["event_class"],
            "confidence": normalized["confidence"],
            "time_precision": normalized["time_precision"],
            "location_anchored": normalized["location_anchored"],
            "risk_category": normalized["risk_category"],
            "timestamp": normalized["timestamp"],
        },
        "score": {
            "adjustment_factor": score["adjustment_factor"],
            "confidence": score["confidence"],
            "verify_url": score["verify_url"],
            "explanation": _generate_explanation(score["confidence"], score["adjustment_factor"]),
        },
        "pipeline": "Receipt → Normalize → Score → Verify",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# INTERNAL AUDIT ENDPOINT (protected)
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/internal/audit")
async def get_audit_log(
    request: Request,
    _: bool = Depends(verify_api_key),
    limit: int = 50
):
    """Get recent audit log entries (protected)."""
    if not AUDIT_LOG_PATH.exists():
        return {"entries": [], "count": 0}

    entries = []
    with open(AUDIT_LOG_PATH, "r") as f:
        for line in f:
            try:
                entries.append(json.loads(line.strip()))
            except:
                pass

    return {
        "entries": entries[-limit:],
        "count": len(entries),
        "system": SYSTEM_ID,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# REAL RECEIPTS — Connected to Forensic Ledger :8101
# ═══════════════════════════════════════════════════════════════════════════════

try:
    from ledger_client import (
        list_curated_receipts,
        get_curated_receipt,
        is_receipt_whitelisted,
        CURATED_RECEIPTS,
    )
    LEDGER_AVAILABLE = True
except ImportError:
    LEDGER_AVAILABLE = False
    CURATED_RECEIPTS = {}


@app.get("/real/receipts")
async def list_real_receipts(request: Request):
    """
    List curated real receipts from Forensic Ledger.
    Only whitelisted receipts are exposed (LEVEL 2 protection).
    """
    if not LEDGER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Ledger client not available")

    audit_log("REAL_LIST_RECEIPTS", {"source": "ledger"}, request)
    receipts = list_curated_receipts()
    return {
        "source": "FORENSIC_LEDGER",
        "curated": True,
        "count": len(receipts),
        "receipts": receipts,
        "disclaimer": "This demo uses a curated subset of verifiable events. No sensitive data exposed.",
    }


@app.get("/real/normalize/{receipt_id}")
async def normalize_real_event(receipt_id: str, request: Request):
    """
    Normalize a real receipt from Forensic Ledger into actuarial signal.
    """
    if not LEDGER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Ledger client not available")

    if not is_receipt_whitelisted(receipt_id):
        audit_log("REAL_NORMALIZE_BLOCKED", {"receipt_id": receipt_id, "reason": "not_whitelisted"}, request)
        raise HTTPException(status_code=403, detail="Receipt not in curated whitelist")

    receipt = get_curated_receipt(receipt_id)
    if not receipt:
        audit_log("REAL_NORMALIZE_NOT_FOUND", {"receipt_id": receipt_id}, request)
        raise HTTPException(status_code=404, detail="Receipt not found in Ledger")

    audit_log("REAL_NORMALIZE_SUCCESS", {"receipt_id": receipt_id}, request)

    # Transform to actuarial format
    return {
        "receipt_id": receipt["id"],
        "event_type": receipt["event_type"],
        "event_class": "INSURABLE_EVENT",
        "confidence": "VERIFIED" if receipt["status"] == "VERIFIED" else "DECLARED",
        "time_precision": "EXACT",
        "location_anchored": receipt.get("location") is not None,
        "risk_category": receipt["actuarial_category"],
        "base_weight": 0.35,  # Standard weight for real events
        "content_hash": receipt.get("content_hash_preview", ""),
        "timestamp": receipt["timestamp"],
        "source": "FORENSIC_LEDGER",
        "verification": receipt["verification"],
    }


@app.get("/real/flow/{receipt_id}")
async def real_full_flow(receipt_id: str, request: Request):
    """
    Full actuarial flow using a REAL receipt from Forensic Ledger.
    This is the Allianz-ready endpoint.
    """
    if not LEDGER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Ledger client not available")

    if not is_receipt_whitelisted(receipt_id):
        audit_log("REAL_FLOW_BLOCKED", {"receipt_id": receipt_id}, request)
        raise HTTPException(status_code=403, detail="Receipt not in curated whitelist")

    receipt = get_curated_receipt(receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")

    # Normalize
    normalized = {
        "receipt_id": receipt["id"],
        "event_type": receipt["event_type"],
        "confidence": "VERIFIED",
        "time_precision": "EXACT",
        "location_anchored": receipt.get("location") is not None,
        "risk_category": receipt["actuarial_category"],
        "base_weight": 0.35,
    }

    # Score using internal engine
    score = _internal_score(normalized)

    audit_log("REAL_FLOW_COMPLETE", {
        "receipt_id": receipt_id,
        "confidence": "VERIFIED",
        "source": "FORENSIC_LEDGER",
    }, request)

    return {
        "source": "FORENSIC_LEDGER",
        "verified": True,
        "receipt": {
            "id": receipt["id"],
            "display_name": receipt["display_name"],
            "event_type": receipt["event_type"],
            "timestamp": receipt["timestamp"],
            "location": receipt.get("location"),
            "governance_level": receipt["governance_level"],
        },
        "normalized": {
            "event_class": "INSURABLE_EVENT",
            "confidence": "VERIFIED",
            "risk_category": receipt["actuarial_category"],
            "risk_factors": receipt.get("risk_factors", []),
        },
        "score": {
            "adjustment_factor": score["adjustment_factor"],
            "explanation": "Risk adjusted based on cryptographically verified event from WINDI Forensic Ledger.",
        },
        "verification": receipt["verification"],
        "pipeline": "Ledger Receipt → Normalize → Score → Verify",
        "disclaimer": "This is real, independently verifiable data from WINDI Forensic Ledger.",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    audit_log("SERVICE_START", {"version": APP_VERSION})
    uvicorn.run(app, host="0.0.0.0", port=8015)
