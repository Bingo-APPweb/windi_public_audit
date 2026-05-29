"""
GET /v1/health — Service health check
"""
import httpx
from fastapi import APIRouter
from app.schemas.common import ok, now_iso

router = APIRouter(tags=["Health"])

LEDGER_URL = "http://localhost:8101/api/receipts"
VERIFY_URL = "http://localhost:8114/health"


@router.get("/health")
async def health():
    """Check service and dependencies health"""
    ledger_ok = False
    verify_ok = False

    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            r = await client.get(LEDGER_URL)
            ledger_ok = r.status_code == 200
        except:
            pass

        try:
            r = await client.get(VERIFY_URL)
            verify_ok = r.status_code == 200
        except:
            pass

    return ok({
        "status": "healthy" if (ledger_ok and verify_ok) else "degraded",
        "service": "W-DEV-API-001",
        "version": "1.0.0",
        "dependencies": {
            "ledger": "healthy" if ledger_ok else "unavailable",
            "verify_public": "healthy" if verify_ok else "unavailable"
        }
    })
