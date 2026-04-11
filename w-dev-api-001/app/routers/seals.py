"""
POST /v1/seals         — Seal artifact (I9 gate)
GET  /v1/seals/{id}    — Get seal details
"""
import httpx
import json
import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.deps.auth import validate_api_key, require_scope
from app.db.session import get_conn
from app.schemas.common import ok, fail, now_iso

router = APIRouter(tags=["Seals"])

LEDGER_URL = "http://localhost:8101/api/receipts"
VERIFY_BASE = "https://windi-domain.com/verify-public/web/verify.html?id="


class SealIntent(BaseModel):
    action: str = "approve_and_seal"
    confirmed_by_human: bool = False


class SealCreate(BaseModel):
    artifact_id: str
    did: str
    seal_type: str = "evidence"
    intent: SealIntent
    metadata: Optional[dict] = None


@router.post("/seals", status_code=201)
async def create_seal(body: SealCreate, key: dict = Depends(validate_api_key)):
    """Seal an artifact. Requires human confirmation (I9)."""
    require_scope(key, "seal:create")

    # I9 Gate — NON-NEGOTIABLE
    if not body.intent.confirmed_by_human:
        raise HTTPException(422, detail=fail(
            "I9_CONFIRMATION_REQUIRED",
            "Human confirmation required. Set intent.confirmed_by_human: true"
        ))

    # Fetch artifact
    conn = get_conn()
    art = conn.execute(
        "SELECT * FROM artifacts WHERE artifact_id = ?", (body.artifact_id,)
    ).fetchone()

    if not art:
        conn.close()
        raise HTTPException(404, detail=fail("ARTIFACT_NOT_FOUND", f"Artifact '{body.artifact_id}' not found"))

    art = dict(art)

    seal_id = f"seal_{uuid.uuid4().hex[:16]}"
    receipt_id = f"WINDI-DEV-{now_iso()[:10].replace('-','')}-{uuid.uuid4().hex[:8].upper()}"
    sealed_at = now_iso()
    ledger_id = None
    verify_url = f"{VERIFY_BASE}{receipt_id}"

    # Write to Ledger :8101
    ledger_payload = {
        "id": receipt_id,
        "actor": body.did,
        "app": "w-dev-api-001",
        "doc_name": art.get("title") or art.get("artifact_id"),
        "doc_type": body.seal_type,
        "content_hash": art.get("sha256", "unknown"),
        "governance_level": "HIGH",
        "sge_score": 0
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(LEDGER_URL, json=ledger_payload)
            if r.status_code in (200, 201):
                ledger_data = r.json()
                ledger_id = ledger_data.get("receipt_id") or receipt_id
    except Exception as e:
        # Graceful degradation - seal locally even if ledger offline
        ledger_id = f"LOCAL_{receipt_id}"

    # Store seal
    conn.execute("""
        INSERT INTO seals
        (seal_id, artifact_id, did, seal_type, status, confirmed_by_human,
         ledger_entry_id, receipt_id, verify_url, metadata, sealed_at, created_by_key, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        seal_id, body.artifact_id, body.did, body.seal_type, "sealed", 1,
        ledger_id, receipt_id, verify_url,
        json.dumps(body.metadata) if body.metadata else None,
        sealed_at, key.get("key_id"), sealed_at
    ))

    # Index receipt
    conn.execute("""
        INSERT OR IGNORE INTO receipts
        (receipt_id, artifact_id, seal_id, ledger_entry_id, did, sha256, verify_url, status, created_at)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (
        receipt_id, body.artifact_id, seal_id, ledger_id,
        body.did, art.get("sha256"), verify_url, "valid", sealed_at
    ))

    conn.commit()
    conn.close()

    return ok({
        "seal_id": seal_id,
        "artifact_id": body.artifact_id,
        "did": body.did,
        "seal_type": body.seal_type,
        "status": "sealed",
        "ledger_entry_id": ledger_id,
        "receipt_id": receipt_id,
        "verify_url": verify_url,
        "sealed_at": sealed_at
    })


@router.get("/seals/{seal_id}")
async def get_seal(seal_id: str, key: dict = Depends(validate_api_key)):
    """Get seal details"""
    conn = get_conn()
    row = conn.execute("SELECT * FROM seals WHERE seal_id = ?", (seal_id,)).fetchone()
    conn.close()

    if not row:
        raise HTTPException(404, detail=fail("SEAL_NOT_FOUND", f"Seal '{seal_id}' not found"))

    return ok(dict(row))
