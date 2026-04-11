"""
GET /v1/receipts/{id} — Get receipt details
"""
from fastapi import APIRouter, Depends, HTTPException
from app.deps.auth import validate_api_key
from app.db.session import get_conn
from app.schemas.common import ok, fail

router = APIRouter(tags=["Receipts"])


@router.get("/receipts/{receipt_id}")
async def get_receipt(receipt_id: str, key: dict = Depends(validate_api_key)):
    """Get receipt by ID"""
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM receipts WHERE receipt_id = ?", (receipt_id,)
    ).fetchone()
    conn.close()

    if not row:
        raise HTTPException(404, detail=fail("RECEIPT_NOT_FOUND", f"Receipt '{receipt_id}' not found"))

    return ok(dict(row))
