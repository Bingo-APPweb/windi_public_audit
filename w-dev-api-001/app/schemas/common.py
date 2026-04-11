"""
Standard response envelope for W-DEV-API-001
"""
from datetime import datetime, timezone
from typing import Any, Optional

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def ok(data: Any, request_id: str = None) -> dict:
    return {
        "success": True,
        "data": data,
        "meta": {
            "request_id": request_id or "req_unknown",
            "timestamp": now_iso(),
            "version": "v1"
        },
        "error": None
    }

def fail(code: str, message: str, details: dict = None) -> dict:
    return {
        "success": False,
        "data": None,
        "meta": {
            "timestamp": now_iso(),
            "version": "v1"
        },
        "error": {
            "code": code,
            "message": message,
            "details": details or {}
        }
    }
