"""
GET /v1/auth/me — Inspect API key context
"""
import json
from fastapi import APIRouter, Depends
from app.deps.auth import validate_api_key
from app.schemas.common import ok

router = APIRouter(tags=["Auth"])


@router.get("/auth/me")
async def auth_me(key: dict = Depends(validate_api_key)):
    """Return current API key context"""
    scopes = key.get("scopes", "[]")
    if isinstance(scopes, str):
        scopes = json.loads(scopes)

    return ok({
        "key_id": key.get("key_id"),
        "environment": key.get("environment", "live"),
        "workspace_id": key.get("workspace_id"),
        "tier": key.get("tier", "SEED"),
        "scopes": scopes,
        "rate_limit": {
            "limit_per_minute": key.get("rpm_limit", 10),
            "remaining": key.get("rpm_remaining", 0)
        }
    })
