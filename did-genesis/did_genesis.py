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

# P0 §299 — Ledger client for birth_receipt emission
try:
    from ledger_client import seal_birth, check_receipt_exists, generate_birth_receipt_id
    LEDGER_ENABLED = True
except ImportError:
    LEDGER_ENABLED = False
    seal_birth = None
    check_receipt_exists = None
    generate_birth_receipt_id = None

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
            status TEXT DEFAULT 'active',
            classification TEXT DEFAULT NULL,
            superseded_by TEXT DEFAULT NULL,
            sovereign_name TEXT
        );

        CREATE UNIQUE INDEX IF NOT EXISTS idx_identities_sovereign_name
        ON identities(sovereign_name) WHERE sovereign_name IS NOT NULL;

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

        -- §191 P0 FIX: recovery_tokens table - schema ready, logic NOT IMPLEMENTED
        -- TODO-SOVEREIGN: Implement recovery flow in §191-F3 post-Berlin
        -- Receipt: WINDI-191-RECOVERY-DEFERRED-20260419
        CREATE TABLE IF NOT EXISTS recovery_tokens (
            token_hash TEXT PRIMARY KEY,
            did TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            expires_at TEXT NOT NULL,
            used_at TEXT,
            FOREIGN KEY (did) REFERENCES identities(did)
        );

        -- §191 DID aliases table
        CREATE TABLE IF NOT EXISTS did_aliases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            canonical_did TEXT NOT NULL,
            alias_actor TEXT NOT NULL UNIQUE,
            alias_type TEXT NOT NULL CHECK(alias_type IN ('STRING', 'DID', 'EMAIL')),
            status TEXT DEFAULT 'active' CHECK(status IN ('active', 'superseded', 'revoked')),
            resolved_at TEXT DEFAULT (datetime('now')),
            notes TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_aliases_canonical ON did_aliases(canonical_did);
        CREATE INDEX IF NOT EXISTS idx_aliases_actor ON did_aliases(alias_actor);

        -- §191 Genesis settings (kill-switch)
        CREATE TABLE IF NOT EXISTS genesis_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT DEFAULT (datetime('now'))
        );
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
# §191 RESOLVE IDENTITY — Multi-layer resolution
# ══════════════════════════════════════════════════════════════════════════════

def resolve_identity(input_value: str, conn=None) -> Optional[dict]:
    """
    §191 BERÇÁRIO — Resolve any input form to canonical identity.

    Resolution order (human-first):
    1. sovereign_name → "dragon-001" (face humana)
    2. did_aliases → "Human Dragon", "human-dragon" (Ledger actors)
    3. email → "jober@a4desk.de" (recovery/UX)
    4. exact did → "did:windi:dragon-001" (técnico/auditor)

    Returns full identity row or None if not found.

    "Humano digita dragon-001. Sistema resolve. Alma encontrada."
    """
    if not input_value or not isinstance(input_value, str):
        return None

    input_clean = input_value.strip()
    input_lower = input_clean.lower()

    close_conn = False
    if conn is None:
        conn = get_db()
        close_conn = True

    cursor = conn.cursor()
    result = None
    resolution_path = None

    try:
        # 1. Try sovereign_name (human face - most common)
        # §191 P0 FIX: Filter status='active' — classified/superseded identities must not resolve
        cursor.execute("""
            SELECT did, passphrase_hash, display_name, email, role, tier, status, sovereign_name, created_at
            FROM identities WHERE LOWER(sovereign_name) = ? AND status = 'active'
        """, (input_lower,))
        row = cursor.fetchone()
        if row:
            result = dict(row)
            resolution_path = "sovereign_name"

        # 2. Try did_aliases (Ledger actors, legacy strings)
        if not result:
            cursor.execute("""
                SELECT i.did, i.passphrase_hash, i.display_name, i.email, i.role, i.tier, i.status, i.sovereign_name, i.created_at
                FROM did_aliases a
                JOIN identities i ON i.did = a.canonical_did
                WHERE LOWER(a.alias_actor) = ? AND a.status = 'active' AND i.status = 'active'
            """, (input_lower,))
            row = cursor.fetchone()
            if row:
                result = dict(row)
                resolution_path = "alias"

        # 3. Try email (recovery/UX alternative)
        if not result:
            cursor.execute("""
                SELECT did, passphrase_hash, display_name, email, role, tier, status, sovereign_name, created_at
                FROM identities WHERE LOWER(email) = ? AND status = 'active'
            """, (input_lower,))
            row = cursor.fetchone()
            if row:
                result = dict(row)
                resolution_path = "email"

        # 4. Try exact DID (technical/auditor)
        if not result:
            cursor.execute("""
                SELECT did, passphrase_hash, display_name, email, role, tier, status, sovereign_name, created_at
                FROM identities WHERE LOWER(did) = ? AND status = 'active'
            """, (input_lower,))
            row = cursor.fetchone()
            if row:
                result = dict(row)
                resolution_path = "did"

        if result:
            result['_resolution_path'] = resolution_path
            log.info(f"Identity resolved: '{input_value[:20]}...' → {result['did'][:30]} via {resolution_path}")

        return result

    finally:
        if close_conn:
            conn.close()

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

    # §206 DID Guardian — Auto-healing on startup
    try:
        from did_guardian import run_guardian
        guardian_result = run_guardian()
        log.info(f"§206 DID Guardian: {guardian_result['healed_aliases']} aliases, {guardian_result['healed_sessions']} sessions healed")
    except Exception as e:
        log.warning(f"§206 DID Guardian skipped: {e}")

    log.info(f"W-DID-GENESIS v{VERSION} started on :{PORT}")
    log.info("DECRETO-001 Art.4: Seiva DID activa")
    log.info("§207 DID-Web Bridge: W3C DID-CORE 1.1 endpoints active")


# ══════════════════════════════════════════════════════════════════════════════
# §207 DID-WEB BRIDGE — W3C Compliant Endpoints
# ══════════════════════════════════════════════════════════════════════════════
try:
    from did_web_bridge import create_did_web_router
    app.include_router(create_did_web_router())
    log.info("§207 DID-Web Bridge: LOADED")
except Exception as e:
    log.warning(f"§207 DID-Web Bridge unavailable: {e}")

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
    §191 BERÇÁRIO — Authenticate via sovereign_name, email, alias, or DID.
    Sets cookie that works across all WINDI services.

    Accepts:
    - sovereign_name: "dragon-001" (face humana)
    - email: "jober@a4desk.de" (recovery/UX)
    - alias: "Human Dragon" (Ledger actors)
    - did: "did:windi:dragon-001" (técnico)
    """
    conn = get_db()
    cursor = conn.cursor()

    # §191: Multi-layer identity resolution
    row = resolve_identity(body.did, conn)

    if not row:
        conn.close()
        log.warning(f"Login failed: identity not found: {body.did[:20]}...")
        # §191 I14: Trilingual helpful error
        raise HTTPException(status_code=401, detail={
            "error_code": "IDENTITY_NOT_FOUND",
            "error": {
                "de": f"Identität '{body.did[:30]}' nicht gefunden. Prüfen Sie Ihren sovereign name oder erstellen Sie eine neue Identität.",
                "en": f"Identity '{body.did[:30]}' not found. Check your sovereign name or create a new identity.",
                "pt": f"Identidade '{body.did[:30]}' não encontrada. Verifique seu nome soberano ou crie uma nova identidade."
            },
            "resolution_attempted": ["sovereign_name", "alias", "email", "did"]
        })

    if row["status"] != "active":
        conn.close()
        # §191 I14: Helpful error with guidance
        sovereign = row.get("sovereign_name") or row["did"][:30]
        raise HTTPException(status_code=403, detail={
            "error_code": "IDENTITY_INACTIVE",
            "status": row["status"],
            "error": {
                "de": f"Diese Identität ist '{row['status']}'. Kontaktieren Sie den Support.",
                "en": f"This identity is '{row['status']}'. Contact support.",
                "pt": f"Esta identidade está '{row['status']}'. Contacte o suporte."
            },
            "sovereign_name": sovereign
        })

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

    # §191 Fix: Use canonical DID (row["did"]), not input (body.did)
    canonical_did = row["did"]

    # Store session
    cursor.execute("""
        INSERT INTO sessions (token_hash, did, created_at, expires_at, ip, user_agent, last_used_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (hash_token(token), canonical_did, now, expires,
          request.client.host, request.headers.get("user-agent", "")[:200], now))

    # Update identity
    cursor.execute("""
        UPDATE identities
        SET last_login_at = ?, login_count = login_count + 1
        WHERE did = ?
    """, (now, canonical_did))

    # Log success
    cursor.execute("""
        INSERT INTO login_events (did, event_type, ip, user_agent, timestamp, return_url, success)
        VALUES (?, 'login_success', ?, ?, ?, ?, 1)
    """, (canonical_did, request.client.host, request.headers.get("user-agent", "")[:200],
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

# ══════════════════════════════════════════════════════════════════════════════
# §191 SECURITY — Change Passphrase
# ══════════════════════════════════════════════════════════════════════════════

class ChangePassphraseRequest(BaseModel):
    current_passphrase: str
    new_passphrase: str
    invalidate_other_sessions: bool = True  # Security best practice

@app.post("/api/genesis/change-passphrase")
async def change_passphrase(
    body: ChangePassphraseRequest,
    request: Request,
    windi_did_session: Optional[str] = Cookie(None)
):
    """
    §191 — Change passphrase for authenticated user.

    Security flow:
    1. Validate current session
    2. Verify current passphrase
    3. Validate new passphrase strength
    4. Update hash
    5. Optionally invalidate other sessions
    """
    # 1. Validate session
    validation = await validate_session(request, windi_did_session)
    if not validation.get("valid"):
        raise HTTPException(status_code=401, detail={
            "error_code": "NOT_AUTHENTICATED",
            "error": {
                "de": "Nicht authentifiziert. Bitte melde dich erneut an.",
                "en": "Not authenticated. Please log in again.",
                "pt": "Não autenticado. Por favor, faça login novamente."
            }
        })

    canonical_did = validation["did"]

    # 2. Get current identity and verify passphrase
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT passphrase_hash FROM identities WHERE did = ?", (canonical_did,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Identity not found")

    current_hash = hash_passphrase(body.current_passphrase)
    if not hmac.compare_digest(row["passphrase_hash"], current_hash):
        conn.close()
        log.warning(f"Passphrase change failed: invalid current passphrase for {canonical_did[:25]}...")
        raise HTTPException(status_code=401, detail={
            "error_code": "INVALID_CURRENT_PASSPHRASE",
            "error": {
                "de": "Aktuelle Passphrase ist falsch.",
                "en": "Current passphrase is incorrect.",
                "pt": "Passphrase atual está incorreta."
            }
        })

    # 3. Validate new passphrase
    if len(body.new_passphrase) < 12:
        conn.close()
        raise HTTPException(status_code=400, detail={
            "error_code": "PASSPHRASE_TOO_SHORT",
            "error": {
                "de": "Neue Passphrase muss mindestens 12 Zeichen haben.",
                "en": "New passphrase must be at least 12 characters.",
                "pt": "Nova passphrase deve ter pelo menos 12 caracteres."
            }
        })

    if body.new_passphrase == body.current_passphrase:
        conn.close()
        raise HTTPException(status_code=400, detail={
            "error_code": "SAME_PASSPHRASE",
            "error": {
                "de": "Neue Passphrase muss sich von der aktuellen unterscheiden.",
                "en": "New passphrase must be different from current.",
                "pt": "Nova passphrase deve ser diferente da atual."
            }
        })

    # 4. Update passphrase hash
    new_hash = hash_passphrase(body.new_passphrase)
    now = datetime.now(timezone.utc).isoformat()

    cursor.execute("""
        UPDATE identities
        SET passphrase_hash = ?
        WHERE did = ?
    """, (new_hash, canonical_did))

    # 5. Invalidate other sessions if requested (security best practice)
    sessions_invalidated = 0
    if body.invalidate_other_sessions:
        current_token_hash = hash_token(windi_did_session) if windi_did_session else None
        if current_token_hash:
            cursor.execute("""
                DELETE FROM sessions
                WHERE did = ? AND token_hash != ?
            """, (canonical_did, current_token_hash))
            sessions_invalidated = cursor.rowcount
        else:
            cursor.execute("DELETE FROM sessions WHERE did = ?", (canonical_did,))
            sessions_invalidated = cursor.rowcount

    # Log security event
    cursor.execute("""
        INSERT INTO login_events (did, event_type, ip, user_agent, timestamp, success)
        VALUES (?, 'passphrase_changed', ?, ?, ?, 1)
    """, (canonical_did, request.client.host, request.headers.get("user-agent", "")[:200], now))

    conn.commit()
    conn.close()

    log.info(f"Passphrase changed: {canonical_did[:25]}... · {sessions_invalidated} other sessions invalidated")

    return {
        "success": True,
        "message": {
            "de": "Passphrase erfolgreich geändert.",
            "en": "Passphrase changed successfully.",
            "pt": "Passphrase alterada com sucesso."
        },
        "sessions_invalidated": sessions_invalidated
    }

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
    §191 BERÇÁRIO — Public Identity Lookup
    ======================================
    SINGLE SOURCE OF TRUTH for identity validation.

    Accepts:
    - sovereign_name: "dragon-001" (face humana)
    - email: "jober@a4desk.de" (recovery/UX)
    - alias: "Human Dragon" (Ledger actors)
    - did: "did:windi:dragon-001" (técnico)

    Returns identity info if found and active.

    "Um nome. Uma fonte. Zero confusão."
    """
    if not did or len(did) < 3:
        return {
            "valid": False,
            "input": did,
            "error_code": "INPUT_TOO_SHORT",
            "error": {
                "de": "Eingabe zu kurz (min. 3 Zeichen)",
                "en": "Input too short (min. 3 characters)",
                "pt": "Entrada muito curta (mín. 3 caracteres)"
            }
        }

    # §191: Multi-layer identity resolution
    row = resolve_identity(did)

    if not row:
        return {
            "valid": False,
            "input": did,
            "active": False,
            "tier": None,
            "error_code": "IDENTITY_NOT_FOUND",
            "error": {
                "de": f"'{did[:30]}' nicht gefunden. Versuchen Sie Ihren sovereign name (z.B. 'dragon-001').",
                "en": f"'{did[:30]}' not found. Try your sovereign name (e.g. 'dragon-001').",
                "pt": f"'{did[:30]}' não encontrado. Tente seu nome soberano (ex: 'dragon-001')."
            },
            "hint": "Use sovereign_name, email, or full DID"
        }

    is_active = row["status"] == "active"
    tier = row["tier"] or "SEED"
    tier_info = DID_TIERS.get(tier, DID_TIERS["SEED"])

    return {
        "valid": True,
        "did": row["did"],
        "sovereign_name": row.get("sovereign_name") or "",
        "active": is_active,
        "tier": tier,
        "tier_emoji": tier_info["emoji"],
        "tier_level": tier_info["level"],
        "access": tier_info["access"],
        "display_name": row["display_name"] or "",
        "role": row["role"],
        "created_at": row.get("created_at"),  # §ACHADO-1 fix: expose DID creation timestamp
        "resolution_path": row.get("_resolution_path", "direct"),
        "source": "W-DID-GENESIS",
        "decree": "DECRETO-001 Art.4 · §191 BERÇÁRIO"
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
# §191 BERÇÁRIO — Birth, Recovery, Kill-switch
# ══════════════════════════════════════════════════════════════════════════════

class BirthRequest(BaseModel):
    """§191 BERÇÁRIO — Request model for sovereign birth."""
    name: str
    email: str
    passphrase: str
    sovereign_name: Optional[str] = None  # If not provided, system suggests
    lang: str = "de"  # de | en | pt

class RecoveryRequest(BaseModel):
    """§191 BERÇÁRIO — Request model for recovery."""
    email: str

def is_birth_enabled() -> bool:
    """Check if birth is enabled (kill-switch)."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM genesis_settings WHERE key = 'birth_enabled'")
        row = cursor.fetchone()
        conn.close()
        return row and row[0] == 'true'
    except:
        return True  # Default to enabled if table doesn't exist

def generate_sovereign_suggestions(name: str) -> list:
    """
    §191 — Generate 3 sovereign_name suggestions from display name.

    "Max Mustermann" → ["max-mustermann", "max-m-2026", "mustermann"]
    """
    import re
    import unicodedata

    # Normalize and clean name
    name_clean = unicodedata.normalize('NFKD', name.lower())
    name_clean = name_clean.encode('ascii', 'ignore').decode('ascii')
    name_clean = re.sub(r'[^a-z0-9\s-]', '', name_clean)
    parts = name_clean.split()

    if not parts:
        # Fallback if name is empty after cleaning
        import secrets
        return [f"user-{secrets.token_hex(4)}", f"windi-{secrets.token_hex(3)}", f"pioneer-{secrets.token_hex(3)}"]

    suggestions = []

    # 1. Full name hyphenated: "max-mustermann"
    full = "-".join(parts)
    if len(full) >= 3:
        suggestions.append(full)

    # 2. First name + initial + year: "max-m-2026"
    if len(parts) >= 2:
        year = datetime.now().year
        initial = parts[1][0] if parts[1] else "x"
        suggestions.append(f"{parts[0]}-{initial}-{year}")
    elif len(parts) == 1:
        year = datetime.now().year
        suggestions.append(f"{parts[0]}-{year}")

    # 3. Last name only: "mustermann"
    if len(parts) >= 2 and len(parts[-1]) >= 3:
        suggestions.append(parts[-1])
    elif len(parts) == 1 and len(parts[0]) >= 3:
        import secrets
        suggestions.append(f"{parts[0]}-{secrets.token_hex(2)}")

    return suggestions[:3]

def is_sovereign_name_available(name: str) -> bool:
    """Check if sovereign_name is available."""
    if not name or len(name) < 3:
        return False
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM identities WHERE LOWER(sovereign_name) = ?", (name.lower(),))
    exists = cursor.fetchone() is not None
    conn.close()
    return not exists

@app.post("/api/genesis/suggest-names")
async def suggest_names(name: str):
    """§191 — Get sovereign_name suggestions for a display name."""
    suggestions = generate_sovereign_suggestions(name)

    # Check availability of each
    available = []
    for s in suggestions:
        if is_sovereign_name_available(s):
            available.append({"name": s, "available": True})
        else:
            available.append({"name": s, "available": False})

    return {
        "suggestions": available,
        "custom_allowed": True,
        "validation": {
            "min_length": 3,
            "max_length": 32,
            "pattern": "[a-z0-9-]+"
        }
    }

@app.post("/api/genesis/check-name")
async def check_name(name: str):
    """§191 — Check if a sovereign_name is available."""
    import re

    name_clean = name.lower().strip()

    # Validate format
    if len(name_clean) < 3:
        return {"available": False, "error": "Too short (min 3 characters)"}
    if len(name_clean) > 32:
        return {"available": False, "error": "Too long (max 32 characters)"}
    if not re.match(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]{1,2}$', name_clean):
        return {"available": False, "error": "Invalid format (use a-z, 0-9, -)"}

    available = is_sovereign_name_available(name_clean)
    return {"name": name_clean, "available": available}

@app.post("/api/genesis/birth")
async def birth(body: BirthRequest, request: Request, response: Response):
    """
    §191 BERÇÁRIO — Sovereign Birth
    ================================
    Create a new sovereign identity with one atomic transaction.

    "A semente nasce. O nome é escolhido. A alma existe."

    Flow:
    1. Validate inputs
    2. Check kill-switch
    3. Generate/validate sovereign_name
    4. Create identity with Ed25519 key (server-side)
    5. Create session
    6. Return canonical_did + backup payload
    """
    import secrets
    import uuid

    # 1. Kill-switch check
    if not is_birth_enabled():
        raise HTTPException(status_code=503, detail={
            "error_code": "BIRTH_DISABLED",
            "error": {
                "de": "Registrierung vorübergehend deaktiviert. Bitte versuchen Sie es später.",
                "en": "Registration temporarily disabled. Please try again later.",
                "pt": "Registro temporariamente desativado. Tente novamente mais tarde."
            }
        })

    # 2. Validate inputs
    if not body.name or len(body.name.strip()) < 2:
        raise HTTPException(status_code=400, detail={
            "error_code": "NAME_REQUIRED",
            "error": {"de": "Name erforderlich", "en": "Name required", "pt": "Nome obrigatório"}
        })

    if not body.email or "@" not in body.email:
        raise HTTPException(status_code=400, detail={
            "error_code": "EMAIL_INVALID",
            "error": {"de": "Gültige E-Mail erforderlich", "en": "Valid email required", "pt": "Email válido obrigatório"}
        })

    if not body.passphrase or len(body.passphrase) < 8:
        raise HTTPException(status_code=400, detail={
            "error_code": "PASSPHRASE_TOO_SHORT",
            "error": {"de": "Passphrase mind. 8 Zeichen", "en": "Passphrase min. 8 characters", "pt": "Frase secreta mín. 8 caracteres"}
        })

    conn = get_db()
    cursor = conn.cursor()

    try:
        # 3. Check email uniqueness
        cursor.execute("SELECT did FROM identities WHERE LOWER(email) = ?", (body.email.lower(),))
        if cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=409, detail={
                "error_code": "EMAIL_EXISTS",
                "error": {
                    "de": "E-Mail bereits registriert. Bitte anmelden.",
                    "en": "Email already registered. Please sign in.",
                    "pt": "Email já registrado. Faça login."
                }
            })

        # 4. Generate or validate sovereign_name
        if body.sovereign_name:
            sovereign = body.sovereign_name.lower().strip()
            if not is_sovereign_name_available(sovereign):
                conn.close()
                suggestions = generate_sovereign_suggestions(body.name)
                raise HTTPException(status_code=409, detail={
                    "error_code": "NAME_TAKEN",
                    "error": {
                        "de": f"'{sovereign}' ist bereits vergeben.",
                        "en": f"'{sovereign}' is already taken.",
                        "pt": f"'{sovereign}' já está em uso."
                    },
                    "suggestions": suggestions
                })
        else:
            # Generate from name
            suggestions = generate_sovereign_suggestions(body.name)
            sovereign = None
            for s in suggestions:
                if is_sovereign_name_available(s):
                    sovereign = s
                    break
            if not sovereign:
                sovereign = f"pioneer-{secrets.token_hex(4)}"

        # 5. Generate canonical DID (UUIDv4 for now, UUIDv7 would require uuid7 package)
        did_uuid = str(uuid.uuid4())[:13]  # Short UUID
        canonical_did = f"did:windi:{did_uuid}"

        # 6. Generate Ed25519 key (server-side)
        # For now, using SHA256 of passphrase+salt as "key" (simplified)
        # Real Ed25519 would require nacl/cryptography package
        backup_key = hashlib.sha256(f"{SECRET_KEY}:{canonical_did}:{body.passphrase}".encode()).hexdigest()

        now = datetime.now(timezone.utc).isoformat()
        passphrase_hash = hash_passphrase(body.passphrase)

        # 7. Generate expected receipt ID (deterministic)
        expected_receipt_id = None
        if LEDGER_ENABLED:
            expected_receipt_id = generate_birth_receipt_id(canonical_did)

        # 8. Insert identity with birth_receipt_status='pending'
        # G2: SQLite commits first, Ledger POST after (no orphan receipts)
        cursor.execute("""
            INSERT INTO identities
            (did, passphrase_hash, display_name, email, role, tier, sovereign_name,
             created_at, status, birth_receipt_status, birth_receipt_id)
            VALUES (?, ?, ?, ?, 'user', 'SEED', ?, ?, 'active', 'pending', ?)
        """, (canonical_did, passphrase_hash, body.name.strip(), body.email.lower(),
              sovereign, now, expected_receipt_id))

        # 9. Create session
        token = create_session_token(
            did=canonical_did,
            role="user",
            tier="SEED",
            display_name=body.name.strip()
        )

        expires = datetime.fromtimestamp(time.time() + SESSION_DURATION, tz=timezone.utc).isoformat()

        cursor.execute("""
            INSERT INTO sessions (token_hash, did, created_at, expires_at, ip, user_agent, last_used_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (hash_token(token), canonical_did, now, expires,
              request.client.host, request.headers.get("user-agent", "")[:200], now))

        # 10. Log birth event
        cursor.execute("""
            INSERT INTO login_events (did, event_type, ip, user_agent, timestamp, success)
            VALUES (?, 'birth', ?, ?, ?, 1)
        """, (canonical_did, request.client.host, request.headers.get("user-agent", "")[:200], now))

        # 11. COMMIT SQLite — DID exists, receipt pending
        conn.commit()
        log.info(f"🌱 BIRTH (pending): {sovereign} → {canonical_did}")

        # 12. P0 §299: POST to Ledger (outside SQLite transaction)
        birth_receipt_status = "pending"
        if LEDGER_ENABLED:
            try:
                import httpx
                status, receipt_id = seal_birth(
                    canonical_did=canonical_did,
                    sovereign_name=sovereign,
                    email=body.email.lower(),
                    birth_timestamp=now
                )
                birth_receipt_status = status

                if status == "sealed":
                    # Update status in DB
                    cursor.execute("""
                        UPDATE identities
                        SET birth_receipt_status = 'sealed'
                        WHERE did = ? AND birth_receipt_status = 'pending'
                    """, (canonical_did,))
                    conn.commit()
                    log.info(f"🌱 BIRTH (sealed): {sovereign} → {canonical_did} · receipt={receipt_id}")

                elif status == "pending":
                    # Ledger unreachable — strict mode: check if receipt exists
                    try:
                        exists, _ = check_receipt_exists(expected_receipt_id)
                        if exists:
                            # Reconciled
                            cursor.execute("""
                                UPDATE identities
                                SET birth_receipt_status = 'sealed'
                                WHERE did = ? AND birth_receipt_status = 'pending'
                            """, (canonical_did,))
                            conn.commit()
                            birth_receipt_status = "sealed"
                            log.info(f"🌱 BIRTH (reconciled): {sovereign} → {canonical_did}")
                        else:
                            # Ledger confirmed 404 — strict mode: DELETE
                            cursor.execute("DELETE FROM identities WHERE did = ?", (canonical_did,))
                            cursor.execute("DELETE FROM sessions WHERE did = ?", (canonical_did,))
                            cursor.execute("""
                                UPDATE login_events SET event_type = 'birth_failure',
                                       failure_cause = 'ledger_confirmed_404'
                                WHERE did = ? AND event_type = 'birth'
                            """, (canonical_did,))
                            conn.commit()
                            log.warning(f"🌱 BIRTH FAILED (404): {sovereign} → {canonical_did}")
                            raise HTTPException(status_code=503, detail={
                                "error_code": "BIRTH_LEDGER_FAILED",
                                "error": {
                                    "de": "Geburt fehlgeschlagen: Ledger konnte nicht bestätigen",
                                    "en": "Birth failed: Ledger could not confirm",
                                    "pt": "Nascimento falhou: Ledger não conseguiu confirmar"
                                }
                            })
                    except httpx.RequestError:
                        # Ledger truly unreachable — leave pending for reconciler
                        log.warning(f"🌱 BIRTH (pending, Ledger down): {sovereign} → {canonical_did}")
                        # In strict mode v0, we fail if Ledger is down
                        cursor.execute("DELETE FROM identities WHERE did = ?", (canonical_did,))
                        cursor.execute("DELETE FROM sessions WHERE did = ?", (canonical_did,))
                        cursor.execute("""
                            UPDATE login_events SET event_type = 'birth_failure',
                                   failure_cause = 'ledger_unreachable'
                            WHERE did = ? AND event_type = 'birth'
                        """, (canonical_did,))
                        conn.commit()
                        raise HTTPException(status_code=503, detail={
                            "error_code": "BIRTH_LEDGER_UNREACHABLE",
                            "error": {
                                "de": "Geburt fehlgeschlagen: Ledger nicht erreichbar",
                                "en": "Birth failed: Ledger unreachable",
                                "pt": "Nascimento falhou: Ledger inacessível"
                            }
                        })

            except HTTPException:
                raise
            except Exception as ledger_err:
                log.error(f"Ledger error during birth: {ledger_err}")
                # Strict mode: fail birth if Ledger has any error
                cursor.execute("DELETE FROM identities WHERE did = ?", (canonical_did,))
                cursor.execute("DELETE FROM sessions WHERE did = ?", (canonical_did,))
                cursor.execute("""
                    UPDATE login_events SET event_type = 'birth_failure',
                           failure_cause = 'ledger_unreachable'
                    WHERE did = ? AND event_type = 'birth'
                """, (canonical_did,))
                conn.commit()
                raise HTTPException(status_code=503, detail={
                    "error_code": "BIRTH_LEDGER_ERROR",
                    "error": {
                        "de": "Geburt fehlgeschlagen: Ledger-Fehler",
                        "en": "Birth failed: Ledger error",
                        "pt": "Nascimento falhou: erro no Ledger"
                    }
                })
        else:
            # P0 §299 STRICT MODE: Ledger not enabled = birth FAILS
            # Legacy mode removed by Guardian review (backdoor vulnerability)
            log.error(f"🌱 BIRTH BLOCKED: Ledger not enabled (LEDGER_ENABLED=False)")
            cursor.execute("DELETE FROM identities WHERE did = ?", (canonical_did,))
            cursor.execute("DELETE FROM sessions WHERE did = ?", (canonical_did,))
            cursor.execute("""
                UPDATE login_events SET event_type = 'birth_failure',
                       failure_cause = 'ledger_not_enabled'
                WHERE did = ? AND event_type = 'birth'
            """, (canonical_did,))
            conn.commit()
            raise HTTPException(status_code=503, detail={
                "error_code": "BIRTH_LEDGER_NOT_ENABLED",
                "error": {
                    "de": "Geburt fehlgeschlagen: Ledger-Client nicht verfügbar",
                    "en": "Birth failed: Ledger client not available",
                    "pt": "Nascimento falhou: cliente Ledger não disponível"
                }
            })

        # 10. Set session cookie
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

        tier_info = DID_TIERS["SEED"]

        # §191-F1.C: backup_required flag (I14 - explicit requirement)
        # P0 §299: Include birth_receipt in response
        return {
            "success": True,
            "canonical_did": canonical_did,
            "sovereign_name": sovereign,
            "display_name": body.name.strip(),
            "tier": "SEED",
            "tier_emoji": tier_info["emoji"],
            "birth_receipt": {
                "status": birth_receipt_status,
                "receipt_id": expected_receipt_id,
                "verify_url": f"https://windi-domain.com/verify-public/?id={expected_receipt_id}" if expected_receipt_id else None
            },
            "backup_required": True,  # §191-F1.C: I14 explicit
            "backup": {
                "key": backup_key,
                "filename": f"{sovereign}.windikey",
                "warning": {
                    "de": "PFLICHT: Speichern Sie diesen Schlüssel sicher. Er kann nicht wiederhergestellt werden.",
                    "en": "REQUIRED: Save this key securely. It cannot be recovered.",
                    "pt": "OBRIGATÓRIO: Guarde esta chave com segurança. Não pode ser recuperada."
                }
            },
            "session": {
                "token": token,
                "expires_in": SESSION_DURATION
            },
            "next_steps": {
                "de": f"Willkommen {body.name}! Du bist jetzt {sovereign} im WINDI.",
                "en": f"Welcome {body.name}! You are now {sovereign} in WINDI.",
                "pt": f"Bem-vindo {body.name}! Agora você é {sovereign} no WINDI."
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        log.error(f"Birth failed: {e}")
        raise HTTPException(status_code=500, detail={
            "error_code": "BIRTH_FAILED",
            "error": {"de": "Geburt fehlgeschlagen", "en": "Birth failed", "pt": "Nascimento falhou"}
        })
    finally:
        conn.close()

@app.post("/api/genesis/kill-switch")
async def toggle_kill_switch(enabled: bool, request: Request, windi_did_session: Optional[str] = Cookie(None)):
    """
    §191 — Toggle birth kill-switch (ORACLE only).
    """
    # Validate session
    validation = await validate_session(request, windi_did_session)
    if not validation.get("valid"):
        raise HTTPException(status_code=401, detail="Not authenticated")

    if validation.get("tier") != "ORACLE":
        raise HTTPException(status_code=403, detail="ORACLE tier required")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO genesis_settings (key, value) VALUES ('birth_enabled', ?)",
        ('true' if enabled else 'false',)
    )
    conn.commit()
    conn.close()

    status = "enabled" if enabled else "disabled"
    log.info(f"🔒 Kill-switch: birth {status} by {validation.get('did')}")

    return {"birth_enabled": enabled, "changed_by": validation.get("did")}

@app.get("/api/genesis/birth-status")
async def birth_status():
    """§191 — Check if birth is enabled."""
    return {"birth_enabled": is_birth_enabled()}


# ══════════════════════════════════════════════════════════════════════════════
# §191-F1 PRAGMATIC — Authenticate Alias + Backup Required
# Receipt: WINDI-191-F1-CLOSE-20260418
# ══════════════════════════════════════════════════════════════════════════════

# TODO-SOVEREIGN: Ed25519 real pendente §191-F1.5
# Receipt: WINDI-191-ED25519-DEFERRED-20260418
# NUNCA remover este comentário sem selar F1.5
# Actual: passphrase-based auth via /login
# Futuro: signature challenge via Ed25519

@app.post("/api/genesis/authenticate")
async def authenticate(body: LoginRequest, request: Request, response: Response):
    """
    §191-F1.A — Authenticate Endpoint (Semantic Alias)
    ===================================================
    This is a semantic alias for /login to satisfy the §191 API contract.

    Current: Passphrase-based authentication (pragmatic for Berlin demo)
    Future (F1.5): Ed25519 signature challenge (post-Berlin)

    Accepts same inputs as /login:
    - did: sovereign_name, email, alias, or canonical DID
    - passphrase: user passphrase
    - return_url: optional redirect after auth

    Returns: session token + user info
    """
    # Delegate to login (same logic, semantic alias)
    return await login(body, request, response)


class BirthRequestV2(BaseModel):
    """§191-F1.B — Birth request with method support."""
    name: str
    email: str
    passphrase: str
    sovereign_name: Optional[str] = None
    birth_method: Optional[str] = "server"  # "server" (default) or "client" (future WebCrypto)
    public_key: Optional[str] = None  # Required if birth_method="client"


@app.post("/api/genesis/birth-v2")
async def birth_v2(body: BirthRequestV2, request: Request, response: Response):
    """
    §191-F1.B — Birth with Method Support (Pragmatic)
    ==================================================
    Prepares the API contract for hybrid birth (server/client).

    Current (pragmatic):
    - birth_method="server" → works (default)
    - birth_method="client" → returns error (not yet implemented)

    Future (F1.5):
    - birth_method="client" → accepts public_key, user keeps private key

    TODO-SOVEREIGN: Ed25519 client-side pendente §191-F1.5
    """
    # F1.B: Validate birth_method
    if body.birth_method == "client":
        # Not yet implemented — return helpful error
        raise HTTPException(status_code=501, detail={
            "error_code": "CLIENT_BIRTH_NOT_IMPLEMENTED",
            "error": {
                "de": "Souveräne Schlüsselgenerierung (WebCrypto) kommt nach Berlin.",
                "en": "Sovereign key generation (WebCrypto) coming after Berlin.",
                "pt": "Geração soberana de chave (WebCrypto) vem após Berlin."
            },
            "fallback": "Use birth_method='server' (default)",
            "deferred_receipt": "WINDI-191-ED25519-DEFERRED-20260418"
        })

    # Delegate to existing birth (server-side)
    # Convert to BirthRequest format
    from pydantic import create_model
    birth_body = type('BirthRequest', (), {
        'name': body.name,
        'email': body.email,
        'passphrase': body.passphrase,
        'sovereign_name': body.sovereign_name
    })()

    result = await birth(
        body=type('obj', (object,), {
            'name': body.name,
            'email': body.email,
            'passphrase': body.passphrase,
            'sovereign_name': body.sovereign_name
        })(),
        request=request,
        response=response
    )

    # F1.C: Add backup_required flag
    if isinstance(result, dict):
        result["backup_required"] = True
        result["backup_instructions"] = {
            "de": "PFLICHT: Laden Sie die .windikey-Datei herunter und speichern Sie sie sicher.",
            "en": "REQUIRED: Download the .windikey file and store it securely.",
            "pt": "OBRIGATÓRIO: Baixe o arquivo .windikey e guarde-o com segurança."
        }

    return result


# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="info")
