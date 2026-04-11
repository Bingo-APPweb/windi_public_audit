"""
POST /v1/verify — Verify by receipt_id or sha256
"""
import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from app.deps.auth import validate_api_key, require_scope
from app.db.session import get_conn
from app.schemas.common import ok, fail

router = APIRouter(tags=["Verify"])

VERIFY_PUBLIC_URL = "http://localhost:8145/verify"


class VerifyRequest(BaseModel):
    receipt_id: Optional[str] = None
    sha256: Optional[str] = None


@router.post("/verify")
async def verify(body: VerifyRequest, key: dict = Depends(validate_api_key)):
    """
    Verify a receipt or hash.
    Cascades: local DB → verify public :8145
    """
    require_scope(key, "verify:read")

    if not body.receipt_id and not body.sha256:
        return fail("INVALID_PAYLOAD", "Either receipt_id or sha256 required")

    conn = get_conn()

    # Try local DB first
    if body.receipt_id:
        row = conn.execute(
            "SELECT * FROM receipts WHERE receipt_id = ?", (body.receipt_id,)
        ).fetchone()
        if row:
            conn.close()
            return ok({
                "result": "verified",
                "match_type": "receipt",
                "source": "local_ledger",
                "receipt_id": row["receipt_id"],
                "artifact_id": row["artifact_id"],
                "seal_id": row["seal_id"],
                "did": row["did"],
                "sha256": row["sha256"],
                "verify_url": row["verify_url"],
                "sealed_at": row["created_at"]
            })

    if body.sha256:
        row = conn.execute(
            "SELECT * FROM receipts WHERE sha256 = ?", (body.sha256,)
        ).fetchone()
        if row:
            conn.close()
            return ok({
                "result": "verified",
                "match_type": "hash",
                "source": "local_ledger",
                "receipt_id": row["receipt_id"],
                "artifact_id": row["artifact_id"],
                "sha256": row["sha256"],
                "verify_url": row["verify_url"],
                "sealed_at": row["created_at"]
            })

    conn.close()

    # Fallback to verify public :8145
    if body.receipt_id:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(f"{VERIFY_PUBLIC_URL}/{body.receipt_id}")
                if r.status_code == 200:
                    data = r.json()
                    if data.get("verified"):
                        return ok({
                            "result": "verified",
                            "match_type": "receipt",
                            "source": "verify_public",
                            "receipt_id": body.receipt_id,
                            "ledger_data": data.get("ledger_data")
                        })
        except:
            pass

    return ok({
        "result": "not_found",
        "match_type": "receipt" if body.receipt_id else "hash",
        "source": "all",
        "message": "No matching record found in any ledger"
    })
