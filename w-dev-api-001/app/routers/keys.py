"""
Key Request & Management Router
POST /v1/keys/request   — Public form submission
GET  /v1/keys/pending   — Admin: list pending (requires ORACLE key)
POST /v1/keys/approve   — Admin: approve request (I9 gate)
"""

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional

router = APIRouter(prefix="/keys", tags=["Keys"])

# Import will be available after full setup
try:
    from app.db.session import get_conn, now_iso
except ImportError:
    def get_conn():
        import sqlite3
        import os
        conn = sqlite3.connect(os.environ.get("WDEV_DB_PATH", "/opt/windi/data/wdev_api.db"))
        conn.row_factory = sqlite3.Row
        return conn
    def now_iso():
        return datetime.now(timezone.utc).isoformat()


class KeyRequest(BaseModel):
    email: EmailStr
    name: str
    company: Optional[str] = None
    tier_requested: str = "SEED"
    use_case: str


@router.post("/request")
def request_key(body: KeyRequest):
    """
    Public endpoint — anyone can request an API key.
    Key is NOT issued immediately (I9 requires human approval).
    """
    conn = get_conn()

    request_id = f"req_{uuid.uuid4().hex[:16]}"

    conn.execute("""
        INSERT INTO key_requests
        (request_id, email, name, company, tier_requested, use_case, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
    """, (
        request_id,
        body.email,
        body.name,
        body.company,
        body.tier_requested,
        body.use_case,
        now_iso()
    ))
    conn.commit()
    conn.close()

    return {
        "success": True,
        "data": {
            "request_id": request_id,
            "status": "pending",
            "message": "Your request has been submitted. You'll receive your API key via email after approval."
        },
        "meta": {
            "timestamp": now_iso(),
            "version": "v1"
        },
        "error": None
    }


@router.get("/pending")
def list_pending():
    """
    Admin: List pending key requests.
    TODO: Add ORACLE key authentication
    """
    conn = get_conn()
    rows = conn.execute("""
        SELECT * FROM key_requests WHERE status = 'pending' ORDER BY created_at DESC
    """).fetchall()
    conn.close()

    return {
        "success": True,
        "data": {
            "count": len(rows),
            "requests": [dict(r) for r in rows]
        },
        "meta": {
            "timestamp": now_iso(),
            "version": "v1"
        },
        "error": None
    }


class ApproveRequest(BaseModel):
    request_id: str
    approved_by: str = "human-dragon"
    tier: Optional[str] = None  # Override tier if needed


@router.post("/approve")
def approve_key(body: ApproveRequest):
    """
    Admin: Approve a key request (I9 gate).
    Generates the actual API key and updates the request.
    TODO: Add ORACLE key authentication
    """
    import hashlib
    import secrets

    conn = get_conn()

    # Find request
    req = conn.execute(
        "SELECT * FROM key_requests WHERE request_id = ?", (body.request_id,)
    ).fetchone()

    if not req:
        conn.close()
        raise HTTPException(404, detail={"error": {"code": "REQUEST_NOT_FOUND", "message": "Key request not found"}})

    req = dict(req)

    if req["status"] != "pending":
        conn.close()
        raise HTTPException(400, detail={"error": {"code": "ALREADY_PROCESSED", "message": f"Request already {req['status']}"}})

    # Generate key
    tier = body.tier or req["tier_requested"]
    raw_key = f"wnd_live_{secrets.token_hex(16)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key_id = f"key_{uuid.uuid4().hex[:12]}"
    now = now_iso()

    # Create API key
    conn.execute("""
        INSERT INTO api_keys
        (key_id, key_hash, environment, tier, status, scopes, owner_email, owner_name, note, approved_by, approved_at, created_at)
        VALUES (?, ?, 'live', ?, 'active', '["seal:create","verify:read","ledger:read"]', ?, ?, ?, ?, ?, ?)
    """, (
        key_id, key_hash, tier,
        req["email"], req["name"], req.get("use_case", ""),
        body.approved_by, now, now
    ))

    # Update request
    conn.execute("""
        UPDATE key_requests
        SET status = 'approved', reviewed_by = ?, reviewed_at = ?, key_id = ?
        WHERE request_id = ?
    """, (body.approved_by, now, key_id, body.request_id))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "data": {
            "request_id": body.request_id,
            "key_id": key_id,
            "api_key": raw_key,  # Only shown ONCE
            "tier": tier,
            "email": req["email"],
            "status": "approved",
            "approved_by": body.approved_by,
            "approved_at": now,
            "warning": "SAVE THIS KEY NOW. It will not be shown again."
        },
        "meta": {
            "timestamp": now,
            "version": "v1"
        },
        "error": None
    }
