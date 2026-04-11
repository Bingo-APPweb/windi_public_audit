"""
API Key Authentication + Rate Limiting
"""
import hashlib
import time
from collections import defaultdict
from fastapi import Request, HTTPException
from app.db.session import get_conn

# In-memory rate limiting (per key_id)
_rate_limits: dict = defaultdict(list)

TIER_LIMITS = {
    "SEED": 10,
    "NODAL": 60,
    "SOVEREIGN": 300,
    "ORACLE": 9999
}

async def validate_api_key(request: Request) -> dict:
    """
    Validate API key from Authorization header.
    Returns key metadata dict.
    """
    auth_header = request.headers.get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        raise HTTPException(401, detail={
            "success": False,
            "error": {"code": "UNAUTHORIZED", "message": "Missing or invalid Authorization header"}
        })

    raw_key = auth_header[7:].strip()

    if not (raw_key.startswith("wnd_") or raw_key.startswith("windi_")):
        raise HTTPException(401, detail={
            "success": False,
            "error": {"code": "INVALID_KEY_FORMAT", "message": "API key must start with wnd_ or windi_"}
        })

    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM api_keys WHERE key_hash = ? AND status = 'active'",
        (key_hash,)
    ).fetchone()
    conn.close()

    if not row:
        raise HTTPException(401, detail={
            "success": False,
            "error": {"code": "INVALID_KEY", "message": "API key not found or inactive"}
        })

    key_data = dict(row)

    # Rate limiting
    tier = key_data.get("tier", "SEED")
    rpm_limit = TIER_LIMITS.get(tier, 10)
    key_id = key_data["key_id"]

    now = time.time()
    window_start = now - 60

    # Clean old entries
    _rate_limits[key_id] = [t for t in _rate_limits[key_id] if t > window_start]

    if len(_rate_limits[key_id]) >= rpm_limit:
        raise HTTPException(429, detail={
            "success": False,
            "error": {"code": "RATE_LIMIT_EXCEEDED", "message": f"Rate limit: {rpm_limit} req/min"}
        })

    _rate_limits[key_id].append(now)

    # Update last_used
    conn = get_conn()
    conn.execute(
        "UPDATE api_keys SET request_count = request_count + 1, last_used_at = ? WHERE key_id = ?",
        (time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), key_id)
    )
    conn.commit()
    conn.close()

    key_data["rpm_remaining"] = rpm_limit - len(_rate_limits[key_id])
    key_data["rpm_limit"] = rpm_limit

    return key_data


def require_scope(key: dict, scope: str):
    """Check if key has required scope"""
    import json
    scopes = key.get("scopes", "[]")
    if isinstance(scopes, str):
        scopes = json.loads(scopes)

    if scope not in scopes and "admin" not in scopes:
        raise HTTPException(403, detail={
            "success": False,
            "error": {"code": "FORBIDDEN", "message": f"Scope '{scope}' required"}
        })
