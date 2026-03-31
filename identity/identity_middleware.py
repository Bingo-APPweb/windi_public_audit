#!/usr/bin/env python3
"""
WINDI Identity Middleware v1.0.0
================================
P0 — Identity Sovereignty Layer

Princípios:
- I9: Sem identidade válida = sem acção
- Fail-closed: Na dúvida, bloqueia
- Backend = autoridade absoluta
- Middleware = guardião da identidade
- Ledger = registrador, não juiz
- Frontend = apenas interface

"O sistema só começa quando a identidade é obrigatória."
— Human Dragon, 01 Apr 2026

Usage:
    from identity_middleware import require_identity, validate_did

    # In FastAPI endpoint:
    @app.post("/seal")
    async def seal(request: Request):
        identity = require_identity(request)
        if identity.error:
            return JSONResponse(identity.error, 401)
        # ... proceed with identity.did

    # Quick validation:
    if not validate_did(did):
        return JSONResponse({"error": "invalid_identity"}, 403)

Author: Liga IA+H — Guardian + Architect
Sealed: 2026-04-01
"""

import sqlite3
import hashlib
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

# ═══════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════

VERSION = "1.0.0"

# Database paths for identity lookup
LAW_DB = "/opt/windi/data/windi_law_identity.db"
TRAVEL_DB = "/opt/windi/data/travel_users.db"

# Public routes that don't require identity
PUBLIC_ROUTES = [
    "/health",
    "/gate",
    "/verify",
    "/verify-public",
    "/static",
    "/favicon.ico",
    "/robots.txt",
]

# Valid identity states
VALID_STATES = ("VERIFIED", "ACTIVE")


# ═══════════════════════════════════════════════════════════════
# Identity Data Class
# ═══════════════════════════════════════════════════════════════

@dataclass
class Identity:
    """
    Resolved identity from request.

    Either contains valid identity data OR an error dict.
    Never both.
    """
    did: Optional[str] = None
    email: Optional[str] = None
    state: Optional[str] = None
    fingerprint: Optional[str] = None
    domain: str = "unknown"  # law | travel
    source: str = "unknown"  # header | cookie | param
    error: Optional[Dict[str, Any]] = None

    @property
    def is_valid(self) -> bool:
        """Check if identity is valid (no error)."""
        return self.error is None and self.did is not None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        if self.error:
            return self.error
        return {
            "did": self.did,
            "email": self.email,
            "state": self.state,
            "fingerprint": self.fingerprint,
            "domain": self.domain,
            "source": self.source,
        }


# ═══════════════════════════════════════════════════════════════
# DID Extraction
# ═══════════════════════════════════════════════════════════════

def extract_did_from_request(request) -> tuple[Optional[str], str]:
    """
    Extract DID from request using priority:
    1. X-WINDI-DID header (most secure)
    2. ?did= query param (for redirects)
    3. windi_did cookie (persistent sessions)

    Args:
        request: FastAPI/Starlette Request object

    Returns:
        Tuple of (did, source) where source is 'header'|'param'|'cookie'|'none'
    """
    # Priority 1: Header (most secure, explicit)
    did = request.headers.get("X-WINDI-DID", "").strip()
    if did:
        return did, "header"

    # Priority 2: Query param (for redirects from gate)
    did = request.query_params.get("did", "").strip()
    if did:
        return did, "param"

    # Priority 3: Cookie (persistent sessions)
    did = request.cookies.get("windi_did", "").strip()
    if did:
        return did, "cookie"

    return None, "none"


# ═══════════════════════════════════════════════════════════════
# Database Lookups
# ═══════════════════════════════════════════════════════════════

def lookup_identity_law(did: str) -> Optional[Dict]:
    """
    Lookup identity in WINDI-LAW database.

    Returns dict with: did, email, state, fingerprint, legal_name
    or None if not found.
    """
    try:
        conn = sqlite3.connect(LAW_DB)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.did, a.email, a.state, a.fingerprint, c.legal_name
            FROM admins a
            LEFT JOIN companies c ON a.company_id = c.id
            WHERE a.did = ?
        """, (did,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception as e:
        print(f"[IDENTITY] LAW lookup error: {e}")
        return None


def lookup_identity_travel(did: str) -> Optional[Dict]:
    """
    Lookup identity in WINDI-TRAVEL database.

    Returns dict with: did (wallet_id), email, state, name
    or None if not found.
    """
    try:
        conn = sqlite3.connect(TRAVEL_DB)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT wallet_id as did, email, state, name
            FROM users
            WHERE wallet_id = ?
        """, (did,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception as e:
        print(f"[IDENTITY] TRAVEL lookup error: {e}")
        return None


def resolve_identity(did: str) -> tuple[Optional[Dict], str]:
    """
    Resolve identity from any WINDI identity store.
    Checks LAW first, then TRAVEL.

    Returns:
        Tuple of (identity_dict, domain) where domain is 'law'|'travel'|'unknown'
    """
    # Try LAW
    identity = lookup_identity_law(did)
    if identity:
        return identity, "law"

    # Try TRAVEL
    identity = lookup_identity_travel(did)
    if identity:
        return identity, "travel"

    return None, "unknown"


# ═══════════════════════════════════════════════════════════════
# Main Entry Points
# ═══════════════════════════════════════════════════════════════

def require_identity(request, require_signature: bool = False) -> Identity:
    """
    Main entry point: Extract and validate identity from request.

    Args:
        request: FastAPI/Starlette Request object
        require_signature: If True, require cryptographic proof (P1 future)

    Returns:
        Identity object with either:
        - Valid identity (did, email, state, etc.)
        - Error dict if validation failed

    Usage:
        identity = require_identity(request)
        if identity.error:
            return JSONResponse(identity.error, 401)
        # Use identity.did, identity.email, etc.
    """
    # Extract DID from request
    did, source = extract_did_from_request(request)

    # ─── No DID found ───
    if not did:
        return Identity(error={
            "ok": False,
            "error": "identity_required",
            "message": "No DID found in request.",
            "hint": "Provide X-WINDI-DID header, ?did= param, or windi_did cookie.",
            "invariant": "I9"
        })

    # ─── Reject 'anon' explicitly ───
    if did == "anon":
        return Identity(error={
            "ok": False,
            "error": "anonymous_forbidden",
            "message": "Anonymous identity is forbidden.",
            "hint": "Please authenticate via /gate",
            "invariant": "I9"
        })

    # ─── Validate DID format (basic) ───
    valid_prefixes = ("did:windi:", "WID-")
    is_email = "@" in did and "." in did.split("@")[-1]
    is_did = any(did.startswith(p) for p in valid_prefixes)

    if not (is_did or is_email):
        return Identity(error={
            "ok": False,
            "error": "invalid_did_format",
            "message": f"Invalid DID format: {did[:30]}...",
            "expected": "did:windi:* or WID-* or valid email",
            "received_prefix": did[:10] if len(did) > 10 else did
        })

    # ─── Resolve identity from database ───
    db_identity, domain = resolve_identity(did)

    if not db_identity:
        return Identity(error={
            "ok": False,
            "error": "identity_not_found",
            "message": f"DID not registered in any identity store.",
            "did_prefix": did[:20] + "..." if len(did) > 20 else did,
            "invariant": "I9",
            "hint": "Register via /law/gate or /travel/gate"
        })

    # ─── Check state ───
    state = db_identity.get("state", "UNKNOWN")
    if state not in VALID_STATES:
        return Identity(error={
            "ok": False,
            "error": "identity_not_verified",
            "message": f"Identity state is {state}, required: {VALID_STATES}",
            "did": did,
            "state": state,
            "hint": "Complete email verification or contact admin."
        })

    # ─── Future: Signature validation (P1) ───
    if require_signature:
        # TODO: Implement Ed25519 signature validation
        # signature = request.headers.get("X-WINDI-SIGNATURE")
        # if not verify_signature(did, signature, request.body):
        #     return Identity(error={...})
        pass

    # ─── Success ───
    return Identity(
        did=did,
        email=db_identity.get("email"),
        state=state,
        fingerprint=db_identity.get("fingerprint"),
        domain=domain,
        source=source
    )


def validate_did(did: str) -> bool:
    """
    Quick validation: Does this DID exist and is it VERIFIED?

    Use for lightweight checks where full Identity object not needed.

    Args:
        did: The DID string to validate

    Returns:
        True if DID exists and is in VERIFIED/ACTIVE state
    """
    if not did or did == "anon":
        return False

    db_identity, _ = resolve_identity(did)
    if not db_identity:
        return False

    return db_identity.get("state") in VALID_STATES


def is_public_route(path: str) -> bool:
    """
    Check if path is a public route that doesn't require identity.

    Args:
        path: Request path (e.g., "/health", "/law/gate")

    Returns:
        True if route is public
    """
    # Normalize path
    path = path.rstrip("/").lower()

    # Check against public routes
    for public in PUBLIC_ROUTES:
        if path == public or path.startswith(public + "/"):
            return True

    return False


# ═══════════════════════════════════════════════════════════════
# FastAPI Middleware (optional integration)
# ═══════════════════════════════════════════════════════════════

async def identity_middleware(request, call_next):
    """
    FastAPI middleware for automatic identity validation.

    Adds request.state.identity with resolved Identity object.
    Returns 401 if identity validation fails on protected routes.

    Usage:
        from identity_middleware import identity_middleware
        app.middleware("http")(identity_middleware)

        # Then in endpoints:
        @app.get("/protected")
        async def protected(request: Request):
            identity = request.state.identity
            return {"did": identity.did}
    """
    # Skip public routes
    if is_public_route(request.url.path):
        return await call_next(request)

    # Skip GET requests to allow browsing (optional - remove for strict mode)
    # if request.method == "GET":
    #     return await call_next(request)

    # Validate identity
    identity = require_identity(request)

    if identity.error:
        # Import here to avoid circular dependency
        from fastapi.responses import JSONResponse
        return JSONResponse(identity.error, status_code=401)

    # Inject into request state
    request.state.identity = identity

    return await call_next(request)


# ═══════════════════════════════════════════════════════════════
# CLI Testing
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print(f"WINDI Identity Middleware v{VERSION}")
    print(f"LAW DB: {LAW_DB}")
    print(f"TRAVEL DB: {TRAVEL_DB}")
    print(f"Public routes: {PUBLIC_ROUTES}")
    print(f"Valid states: {VALID_STATES}")
    print()
    print("Usage:")
    print("  from identity_middleware import require_identity, validate_did")
    print()
    print("Test validate_did:")

    # Quick test
    test_dids = ["anon", "", "did:windi:test", "invalid"]
    for did in test_dids:
        result = validate_did(did)
        print(f"  validate_did('{did}') = {result}")
