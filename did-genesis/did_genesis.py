#!/usr/bin/env python3
"""
§167 W-DID-GENESIS — Sovereign Identity Tree
============================================
Port: 8096 · Path: /api/genesis/
"A semente germina uma vez. A seiva flui para sempre."

DECRETO-001 Art.4 Implementation:
- DID = Semente única (login uma vez)
- Token = Seiva (flui para todos os galhos)
- Serviços = Galhos (validam contra o tronco)

Liga IA+H · Kempten, Bavaria · 2026
"""

import hashlib
import hmac
import json
import os
import time
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from functools import wraps

from fastapi import FastAPI, HTTPException, Request, Response, Cookie
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

VERSION = "1.0.0"
SERVICE_ID = "W-DID-GENESIS"
PORT = 8096

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "did_genesis.db"
LOG_DIR = Path("/opt/windi/logs")

# Security
SECRET_KEY = os.environ.get("WINDI_DID_SECRET", "windi-did-genesis-dragon-2026")
SALT = "windi-dragon-salt-2026"
SESSION_DURATION = 86400 * 30  # 30 days (sovereign session)
TOKEN_COOKIE_NAME = "windi_did_session"

# Domain
DOMAIN = os.environ.get("WINDI_DOMAIN", "windi-domain.com")
SECURE_COOKIE = os.environ.get("WINDI_SECURE_COOKIE", "true").lower() == "true"

# Logging
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [DID-GENESIS] %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "did-genesis.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("did-genesis")

# ══════════════════════════════════════════════════════════════════════════════
# DID TIERS (DECRETO-001 Art.4)
# ══════════════════════════════════════════════════════════════════════════════

DID_TIERS = {
    "SEED": {
        "level": 1,
        "access": ["/verify-public/"],
        "emoji": "🌱"
    },
    "NODAL": {
        "level": 2,
        "access": ["/verify-public/", "/wallet/", "/travel/"],
        "emoji": "🌿"
    },
    "SOVEREIGN": {
        "level": 3,
        "access": ["/verify-public/", "/wallet/", "/travel/", "/law/", "/enterprise/"],
        "emoji": "🌳"
    },
    "ORACLE": {
        "level": 4,
        "access": ["*"],  # Full access
        "emoji": "🏛"
    }
}

ROLE_TO_TIER = {
    "founder": "ORACLE",
    "admin": "SOVEREIGN",
    "operator": "NODAL",
    "user": "SEED"
}

# ══════════════════════════════════════════════════════════════════════════════
# DATABASE
# ══════════════════════════════════════════════════════════════════════════════

def init_db():
    """Initialize SQLite database with DID tables."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS identities (
            did TEXT PRIMARY KEY,
            passphrase_hash TEXT NOT NULL,
            display_name TEXT,
            email TEXT,
            role TEXT DEFAULT 'user',
            tier TEXT DEFAULT 'SEED',
            created_at TEXT NOT NULL,
            last_login_at TEXT,
            login_count INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active'
        );

        CREATE TABLE IF NOT EXISTS sessions (
            token_hash TEXT PRIMARY KEY,
            did TEXT NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            ip TEXT,
            user_agent TEXT,
            last_used_at TEXT,
            FOREIGN KEY (did) REFERENCES identities(did)
        );

        CREATE TABLE IF NOT EXISTS login_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            did TEXT NOT NULL,
            event_type TEXT NOT NULL,
            ip TEXT,
            user_agent TEXT,
            timestamp TEXT NOT NULL,
            return_url TEXT,
            success INTEGER DEFAULT 1
        );

        CREATE INDEX IF NOT EXISTS idx_sessions_did ON sessions(did);
        CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);
        CREATE INDEX IF NOT EXISTS idx_events_did ON login_events(did);
    """)
    conn.commit()
    conn.close()
    log.info(f"Database initialized: {DB_PATH}")

def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

# ══════════════════════════════════════════════════════════════════════════════
# CRYPTO UTILS
# ══════════════════════════════════════════════════════════════════════════════

def hash_passphrase(passphrase: str) -> str:
    """Hash passphrase with SHA-256 + salt (compatible with existing wallet)."""
    return hashlib.sha256(f"{SALT}:{passphrase}".encode()).hexdigest()

def create_session_token(did: str, role: str, tier: str, display_name: str) -> str:
    """Create HMAC-signed session token."""
    import base64
    payload = {
        "did": did,
        "role": role,
        "tier": tier,
        "display_name": display_name,
        "iat": int(time.time()),
        "exp": int(time.time()) + SESSION_DURATION
    }
    payload_json = json.dumps(payload, sort_keys=True)
    signature = hmac.new(
        SECRET_KEY.encode(), payload_json.encode(), hashlib.sha256
    ).hexdigest()[:32]
    token = base64.urlsafe_b64encode(payload_json.encode()).decode()
    return f"{token}.{signature}"

def verify_session_token(token: str) -> Optional[dict]:
    """Verify and decode session token."""
    try:
        import base64
        parts = token.split(".")
        if len(parts) != 2:
            return None
        payload_b64, signature = parts
        payload_json = base64.urlsafe_b64decode(payload_b64).decode()
        expected_sig = hmac.new(
            SECRET_KEY.encode(), payload_json.encode(), hashlib.sha256
        ).hexdigest()[:32]
        if not hmac.compare_digest(signature, expected_sig):
            return None
        payload = json.loads(payload_json)
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None

def hash_token(token: str) -> str:
    """Hash token for storage (don't store raw tokens)."""
    return hashlib.sha256(token.encode()).hexdigest()[:32]

# ══════════════════════════════════════════════════════════════════════════════
# MIGRATION: Import existing credentials
# ══════════════════════════════════════════════════════════════════════════════

def migrate_existing_credentials():
    """Import credentials from old wallet_credentials.json."""
    old_creds_file = Path("/opt/windi/data/wallet_credentials.json")
    if not old_creds_file.exists():
        return

    try:
        with open(old_creds_file) as f:
            old_creds = json.load(f)

        conn = get_db()
        cursor = conn.cursor()
        now = datetime.now(timezone.utc).isoformat()

        migrated = 0
        for wallet_id, data in old_creds.items():
            # Check if already exists
            cursor.execute("SELECT did FROM identities WHERE did = ?", (wallet_id,))
            if cursor.fetchone():
                continue

            cursor.execute("""
                INSERT INTO identities (did, passphrase_hash, display_name, role, tier, created_at, status)
                VALUES (?, ?, ?, ?, ?, ?, 'active')
            """, (
                wallet_id,
                data.get("passphrase_hash", ""),
                data.get("display_name", ""),
                data.get("role", "user"),
                ROLE_TO_TIER.get(data.get("role", "user"), "SEED"),
                data.get("registered_at", now)
            ))
            migrated += 1

        conn.commit()
        conn.close()

        if migrated > 0:
            log.info(f"Migrated {migrated} identities from wallet_credentials.json")
    except Exception as e:
        log.warning(f"Migration failed: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# FASTAPI APP
# ══════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="W-DID-GENESIS",
    version=VERSION,
    description="§167 Sovereign Identity Tree · DECRETO-001 Art.4",
    docs_url="/api/genesis/docs",
    openapi_url="/api/genesis/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        f"https://{DOMAIN}",
        f"https://www.{DOMAIN}",
        "http://localhost:8096"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# ══════════════════════════════════════════════════════════════════════════════
# MODELS
# ══════════════════════════════════════════════════════════════════════════════

class LoginRequest(BaseModel):
    did: str
    passphrase: str
    return_url: Optional[str] = None

class RegisterRequest(BaseModel):
    did: str
    passphrase: str
    display_name: Optional[str] = None
    email: Optional[str] = None

class SessionInfo(BaseModel):
    did: str
    role: str
    tier: str
    display_name: str
    tier_emoji: str
    tier_level: int
    access: list
    expires_in: int

# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup():
    init_db()
    migrate_existing_credentials()
    log.info(f"W-DID-GENESIS v{VERSION} started on :{PORT}")
    log.info("DECRETO-001 Art.4: Seiva DID activa")

@app.get("/api/genesis/health")
async def health():
    """Health check."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM identities WHERE status = 'active'")
    active_ids = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM sessions WHERE expires_at > datetime('now')")
    active_sessions = cursor.fetchone()[0]
    conn.close()

    return {
        "service": SERVICE_ID,
        "version": VERSION,
        "status": "live",
        "port": PORT,
        "active_identities": active_ids,
        "active_sessions": active_sessions,
        "decree": "DECRETO-001 Art.4",
        "principle": "A semente germina uma vez. A seiva flui para sempre.",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.post("/api/genesis/login")
async def login(body: LoginRequest, request: Request, response: Response):
    """
    Authenticate and create sovereign session.
    Sets cookie that works across all WINDI services.
    """
    conn = get_db()
    cursor = conn.cursor()

    # Find identity
    cursor.execute("""
        SELECT did, passphrase_hash, display_name, role, tier, status
        FROM identities WHERE did = ?
    """, (body.did,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        log.warning(f"Login failed: DID not found: {body.did[:20]}...")
        raise HTTPException(status_code=401, detail="DID not found")

    if row["status"] != "active":
        conn.close()
        raise HTTPException(status_code=403, detail=f"Identity {row['status']}")

    # Verify passphrase
    provided_hash = hash_passphrase(body.passphrase)
    if not hmac.compare_digest(row["passphrase_hash"], provided_hash):
        # Log failed attempt
        cursor.execute("""
            INSERT INTO login_events (did, event_type, ip, user_agent, timestamp, success)
            VALUES (?, 'login_failed', ?, ?, ?, 0)
        """, (body.did, request.client.host, request.headers.get("user-agent", "")[:200],
              datetime.now(timezone.utc).isoformat()))
        conn.commit()
        conn.close()
        log.warning(f"Login failed: invalid passphrase for {body.did[:20]}...")
        raise HTTPException(status_code=401, detail="Invalid passphrase")

    # Create session
    tier = row["tier"] or ROLE_TO_TIER.get(row["role"], "SEED")
    token = create_session_token(
        did=row["did"],
        role=row["role"],
        tier=tier,
        display_name=row["display_name"] or ""
    )

    now = datetime.now(timezone.utc).isoformat()
    expires = datetime.fromtimestamp(time.time() + SESSION_DURATION, tz=timezone.utc).isoformat()

    # Store session
    cursor.execute("""
        INSERT INTO sessions (token_hash, did, created_at, expires_at, ip, user_agent, last_used_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (hash_token(token), body.did, now, expires,
          request.client.host, request.headers.get("user-agent", "")[:200], now))

    # Update identity
    cursor.execute("""
        UPDATE identities
        SET last_login_at = ?, login_count = login_count + 1
        WHERE did = ?
    """, (now, body.did))

    # Log success
    cursor.execute("""
        INSERT INTO login_events (did, event_type, ip, user_agent, timestamp, return_url, success)
        VALUES (?, 'login_success', ?, ?, ?, ?, 1)
    """, (body.did, request.client.host, request.headers.get("user-agent", "")[:200],
          now, body.return_url or ""))

    conn.commit()
    conn.close()

    log.info(f"Login success: {row['display_name'] or body.did[:20]} · tier={tier}")

    # Set sovereign cookie (works across all subdomains)
    response.set_cookie(
        key=TOKEN_COOKIE_NAME,
        value=token,
        max_age=SESSION_DURATION,
        httponly=True,
        secure=SECURE_COOKIE,
        samesite="lax",
        domain=f".{DOMAIN}" if SECURE_COOKIE else None,
        path="/"
    )

    tier_info = DID_TIERS.get(tier, DID_TIERS["SEED"])

    result = {
        "success": True,
        "did": body.did,
        "display_name": row["display_name"] or "",
        "role": row["role"],
        "tier": tier,
        "tier_emoji": tier_info["emoji"],
        "tier_level": tier_info["level"],
        "access": tier_info["access"],
        "token": token,
        "expires_in": SESSION_DURATION,
        "return_url": body.return_url
    }

    return result

@app.get("/api/genesis/validate")
async def validate_session(
    request: Request,
    windi_did_session: Optional[str] = Cookie(None)
):
    """
    Validate session token. Called by all WINDI services.
    This is the SINGLE SOURCE OF TRUTH for authentication.
    """
    # Get token from cookie or header
    token = windi_did_session
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

    if not token:
        return {"valid": False, "reason": "no_token"}

    # Verify token signature
    payload = verify_session_token(token)
    if not payload:
        return {"valid": False, "reason": "invalid_or_expired"}

    # Check session in database
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.did, s.expires_at, i.display_name, i.role, i.tier, i.status
        FROM sessions s
        JOIN identities i ON s.did = i.did
        WHERE s.token_hash = ? AND s.expires_at > datetime('now')
    """, (hash_token(token),))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return {"valid": False, "reason": "session_not_found"}

    if row["status"] != "active":
        conn.close()
        return {"valid": False, "reason": f"identity_{row['status']}"}

    # Update last used
    cursor.execute("""
        UPDATE sessions SET last_used_at = ? WHERE token_hash = ?
    """, (datetime.now(timezone.utc).isoformat(), hash_token(token)))
    conn.commit()
    conn.close()

    tier = row["tier"] or ROLE_TO_TIER.get(row["role"], "SEED")
    tier_info = DID_TIERS.get(tier, DID_TIERS["SEED"])

    return {
        "valid": True,
        "did": row["did"],
        "display_name": row["display_name"] or "",
        "role": row["role"],
        "tier": tier,
        "tier_emoji": tier_info["emoji"],
        "tier_level": tier_info["level"],
        "access": tier_info["access"],
        "expires_in": int(payload.get("exp", 0) - time.time())
    }

@app.post("/api/genesis/logout")
async def logout(
    request: Request,
    response: Response,
    windi_did_session: Optional[str] = Cookie(None)
):
    """Destroy session and clear cookie."""
    token = windi_did_session
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

    if token:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE token_hash = ?", (hash_token(token),))
        conn.commit()
        conn.close()

    # Clear cookie
    response.delete_cookie(
        key=TOKEN_COOKIE_NAME,
        domain=f".{DOMAIN}" if SECURE_COOKIE else None,
        path="/"
    )

    return {"success": True, "message": "Session destroyed"}

@app.post("/api/genesis/register")
async def register(body: RegisterRequest, request: Request):
    """Register new DID identity."""
    conn = get_db()
    cursor = conn.cursor()

    # Check if exists
    cursor.execute("SELECT did FROM identities WHERE did = ?", (body.did,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=409, detail="DID already registered")

    now = datetime.now(timezone.utc).isoformat()

    cursor.execute("""
        INSERT INTO identities (did, passphrase_hash, display_name, email, role, tier, created_at, status)
        VALUES (?, ?, ?, ?, 'user', 'SEED', ?, 'active')
    """, (
        body.did,
        hash_passphrase(body.passphrase),
        body.display_name or "",
        body.email or "",
        now
    ))

    conn.commit()
    conn.close()

    log.info(f"Registered new DID: {body.did[:30]}...")

    return {
        "success": True,
        "did": body.did,
        "tier": "SEED",
        "message": "Identity registered. Seiva pronta para fluir."
    }

@app.get("/api/genesis/lookup/{did}")
async def lookup_did(did: str):
    """
    §173 DID SIMPLIFICATION — Public DID Lookup
    ============================================
    SINGLE SOURCE OF TRUTH for DID validation.

    Any service can call this endpoint to validate a DID.
    No cookie required. No authentication required.
    Just pass the DID and get the truth.

    Returns:
    - valid: bool (does the DID exist and is active?)
    - tier: str (SEED/NODAL/SOVEREIGN/ORACLE)
    - active: bool
    - display_name: str
    - created_at: str

    "Um DID. Uma fonte. Zero fallbacks."
    """
    if not did or len(did) < 10:
        return {
            "valid": False,
            "did": did,
            "error": "DID inválido ou muito curto"
        }

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT did, display_name, role, tier, status, created_at, last_login_at
        FROM identities WHERE did = ?
    """, (did,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return {
            "valid": False,
            "did": did,
            "active": False,
            "tier": None,
            "error": "DID não encontrado na Genesis"
        }

    is_active = row["status"] == "active"
    tier = row["tier"] or "SEED"
    tier_info = DID_TIERS.get(tier, DID_TIERS["SEED"])

    return {
        "valid": True,
        "did": row["did"],
        "active": is_active,
        "tier": tier,
        "tier_emoji": tier_info["emoji"],
        "tier_level": tier_info["level"],
        "access": tier_info["access"],
        "display_name": row["display_name"] or "",
        "role": row["role"],
        "created_at": row["created_at"],
        "last_seen": row["last_login_at"],
        "source": "W-DID-GENESIS",
        "decree": "DECRETO-001 Art.4"
    }

@app.get("/api/genesis/tiers")
async def list_tiers():
    """List all DID tiers and their access levels."""
    return {
        "tiers": DID_TIERS,
        "role_mapping": ROLE_TO_TIER,
        "decree": "DECRETO-001 Art.4 — As 4 Leis da Seiva"
    }

@app.get("/api/genesis/me")
async def get_current_identity(
    request: Request,
    windi_did_session: Optional[str] = Cookie(None)
):
    """Get current authenticated identity details."""
    validation = await validate_session(request, windi_did_session)

    if not validation.get("valid"):
        raise HTTPException(status_code=401, detail=validation.get("reason", "not_authenticated"))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT did, display_name, email, role, tier, created_at, last_login_at, login_count
        FROM identities WHERE did = ?
    """, (validation["did"],))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Identity not found")

    tier_info = DID_TIERS.get(row["tier"], DID_TIERS["SEED"])

    return {
        "did": row["did"],
        "display_name": row["display_name"],
        "email": row["email"],
        "role": row["role"],
        "tier": row["tier"],
        "tier_emoji": tier_info["emoji"],
        "tier_level": tier_info["level"],
        "access": tier_info["access"],
        "created_at": row["created_at"],
        "last_login_at": row["last_login_at"],
        "login_count": row["login_count"]
    }

# ══════════════════════════════════════════════════════════════════════════════
# REDIRECT FLOW (return_url handling)
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/api/genesis/redirect")
async def smart_redirect(
    request: Request,
    return_url: Optional[str] = None,
    windi_did_session: Optional[str] = Cookie(None)
):
    """
    Smart redirect after login.
    If authenticated: redirect to return_url or default dashboard.
    If not: redirect to login with return_url preserved.
    """
    validation = await validate_session(request, windi_did_session)

    if validation.get("valid"):
        # Authenticated — go to destination
        destination = return_url or f"https://{DOMAIN}/desktop/"

        # Validate return_url is within WINDI domain
        if return_url and not return_url.startswith(f"https://{DOMAIN}"):
            if not return_url.startswith(f"https://www.{DOMAIN}"):
                destination = f"https://{DOMAIN}/desktop/"

        return RedirectResponse(url=destination, status_code=302)
    else:
        # Not authenticated — go to login
        login_url = f"https://{DOMAIN}/wallet/"
        if return_url:
            login_url += f"?return={return_url}"
        return RedirectResponse(url=login_url, status_code=302)

# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="info")
