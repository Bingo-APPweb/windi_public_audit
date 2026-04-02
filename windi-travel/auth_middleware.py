"""
W-SESSION-001 — Auth Middleware for WINDI Travel
=================================================
WINDI Publishing House · Kempten, Bavaria
Created: 02 Apr 2026

Middleware de autenticação que unifica:
- Sessões soberanas (W-SESSION-001) com device binding
- Sessões legacy (travel_sessions) para compatibilidade

Princípios:
- Fail-closed: DB down = nega acesso
- Soberana primeiro, fallback legacy
- device_id como sinal, não como autenticação

Invariantes:
- I1: Soberania Humana
- I9: Proibição de Autonomia
- I13: Soberania de Dados
"""

import os
import sqlite3
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, Union
from pathlib import Path

from fastapi import Request
from fastapi.responses import RedirectResponse

# Import sovereign session module
import sys
sys.path.insert(0, '/opt/windi/session')
from sovereign_session import (
    verify_session_token,
    SessionValidation,
    SessionPayload,
    ENABLE_SOVEREIGN_SESSION,
    generate_device_id,
    hash_ip_for_signal
)

# ── Config ────────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "travel_users.db"
IDENTITY_DB_PATH = BASE_DIR / "identity-gate" / "windi_travel_identity.db"

# Cookie names
SOVEREIGN_COOKIE = "windi_sovereign_session"
LEGACY_COOKIE = "windi_travel_session"

# ── Dataclasses ───────────────────────────────────────────────────────────────

@dataclass
class AuthResult:
    """Resultado da autenticação."""
    authenticated: bool
    wallet_id: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    email_verified: bool = False
    tier: str = "FREE"

    # Sovereign session info
    is_sovereign: bool = False
    session_id: Optional[str] = None
    device_id: Optional[str] = None
    device_trust: str = "NEW"

    # Error info
    error: Optional[str] = None
    error_code: Optional[str] = None


# ── Database Helpers ──────────────────────────────────────────────────────────

def get_travel_db():
    """Conexão ao travel_users.db (legacy)."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def get_identity_db():
    """Conexão ao windi_travel_identity.db (sovereign sessions)."""
    conn = sqlite3.connect(str(IDENTITY_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


# ── Sovereign Session Validation ──────────────────────────────────────────────

def validate_sovereign_session(
    token: str,
    device_id_from_header: Optional[str] = None,
    ip_hash: Optional[str] = None
) -> AuthResult:
    """
    Valida sessão soberana com verificação de revogação.

    Fluxo:
    1. Verificação stateless do token (HMAC)
    2. Verificação de revogação no DB
    3. Actualização de last_used_at
    4. Carrega dados do utilizador

    Args:
        token: Token de sessão soberana
        device_id_from_header: X-Device-ID header (sinal auxiliar)
        ip_hash: Hash do IP actual (sinal auxiliar)

    Returns:
        AuthResult com estado da autenticação

    Security:
        - Fail-closed: qualquer erro = não autenticado
        - device_id é sinal, não factor de autenticação
        - Revogação é verificada no DB
    """
    # Step 1: Stateless verification
    validation = verify_session_token(token)

    if not validation.valid:
        return AuthResult(
            authenticated=False,
            error=validation.error,
            error_code=validation.error_code
        )

    payload = validation.payload

    try:
        # Step 2: Check revocation in DB (FAIL-CLOSED)
        with get_identity_db() as db:
            session = db.execute(
                """SELECT s.*, u.full_name, u.email, u.state as user_state
                   FROM sovereign_sessions s
                   LEFT JOIN admins u ON u.did = s.wallet_id
                   WHERE s.session_id = ?""",
                (payload.sid,)
            ).fetchone()

            # Session not found = invalid
            if not session:
                return AuthResult(
                    authenticated=False,
                    error="Sessão não encontrada",
                    error_code="session_not_found"
                )

            # Session revoked
            if session["revoked"] == 1:
                return AuthResult(
                    authenticated=False,
                    error="Sessão revogada",
                    error_code="session_revoked"
                )

            # Session expired (double-check DB)
            if session["expires_at"] < datetime.utcnow().isoformat():
                return AuthResult(
                    authenticated=False,
                    error="Sessão expirada",
                    error_code="expired"
                )

            # User state check
            if session["user_state"] and session["user_state"] != "VERIFIED":
                return AuthResult(
                    authenticated=False,
                    error="Conta não verificada",
                    error_code="account_not_verified"
                )

            # Step 3: Update last_used_at
            db.execute(
                "UPDATE sovereign_sessions SET last_used_at = datetime('now') WHERE session_id = ?",
                (payload.sid,)
            )

            # Step 4: Get device trust level (informational only)
            device_binding = db.execute(
                """SELECT trust_level FROM device_bindings
                   WHERE wallet_id = ? AND device_id = ? AND state = 'ACTIVE'""",
                (payload.did, payload.device_id)
            ).fetchone()

            device_trust = device_binding["trust_level"] if device_binding else "NEW"

            db.commit()

        # Step 5: Load user data from travel_users (for compatibility)
        with get_travel_db() as db:
            user = db.execute(
                "SELECT * FROM travel_users WHERE wallet_id = ?",
                (payload.did,)
            ).fetchone()

        # Success
        return AuthResult(
            authenticated=True,
            wallet_id=payload.did,
            email=user["email"] if user else session["email"],
            name=user["name"] if user else session["full_name"],
            email_verified=True,  # Sovereign session implies verified
            tier=user["tier"] if user else "FREE",
            is_sovereign=True,
            session_id=payload.sid,
            device_id=payload.device_id,
            device_trust=device_trust
        )

    except sqlite3.Error as e:
        # FAIL-CLOSED: DB error = deny access
        return AuthResult(
            authenticated=False,
            error=f"Erro de base de dados: {str(e)}",
            error_code="db_error"
        )
    except Exception as e:
        # FAIL-CLOSED: Any error = deny access
        return AuthResult(
            authenticated=False,
            error=f"Erro de verificação: {str(e)}",
            error_code="verification_error"
        )


# ── Legacy Session Validation ─────────────────────────────────────────────────

def validate_legacy_session(token: str) -> AuthResult:
    """
    Valida sessão legacy (travel_sessions).
    Mantido para compatibilidade com sessões existentes.

    Args:
        token: Token de sessão legacy

    Returns:
        AuthResult com estado da autenticação
    """
    if not token:
        return AuthResult(
            authenticated=False,
            error="Token vazio",
            error_code="empty_token"
        )

    try:
        with get_travel_db() as db:
            row = db.execute(
                """SELECT u.* FROM travel_sessions s
                   JOIN travel_users u ON u.wallet_id = s.wallet_id
                   WHERE s.token = ? AND s.expires_at > datetime('now')
                   AND u.email_verified = 1""",
                (token,)
            ).fetchone()

        if not row:
            return AuthResult(
                authenticated=False,
                error="Sessão inválida ou expirada",
                error_code="invalid_session"
            )

        return AuthResult(
            authenticated=True,
            wallet_id=row["wallet_id"],
            email=row["email"],
            name=row["name"],
            email_verified=bool(row["email_verified"]),
            tier=row["tier"],
            is_sovereign=False,
            session_id=None,
            device_id=None,
            device_trust="LEGACY"
        )

    except sqlite3.Error as e:
        # FAIL-CLOSED
        return AuthResult(
            authenticated=False,
            error=f"Erro de base de dados: {str(e)}",
            error_code="db_error"
        )


# ── Main Auth Function ────────────────────────────────────────────────────────

def authenticate_request(request: Request) -> AuthResult:
    """
    Autenticar request usando:
    1. Sessão soberana (se ENABLE_SOVEREIGN_SESSION=true)
    2. Sessão legacy (fallback)

    Args:
        request: FastAPI Request object

    Returns:
        AuthResult com estado completo da autenticação

    Usage:
        auth = authenticate_request(request)
        if not auth.authenticated:
            return RedirectResponse(url="/travel/gate")
    """
    # Extract device_id from header (signal only)
    device_id_header = request.headers.get("X-Device-ID")

    # Get IP hash for signal
    client_ip = request.client.host if request.client else "unknown"
    ip_hash = hash_ip_for_signal(client_ip)

    # Try sovereign session first (if enabled)
    if ENABLE_SOVEREIGN_SESSION:
        sovereign_token = request.cookies.get(SOVEREIGN_COOKIE)
        if sovereign_token:
            result = validate_sovereign_session(
                sovereign_token,
                device_id_from_header=device_id_header,
                ip_hash=ip_hash
            )
            if result.authenticated:
                return result
            # If sovereign session invalid, don't fallback for security
            # User should re-authenticate
            if result.error_code in ("session_revoked", "account_not_verified"):
                return result

    # Fallback to legacy session
    legacy_token = request.cookies.get(LEGACY_COOKIE)
    if legacy_token:
        return validate_legacy_session(legacy_token)

    # No valid session
    return AuthResult(
        authenticated=False,
        error="Nenhuma sessão válida",
        error_code="no_session"
    )


# ── Convenience Functions ─────────────────────────────────────────────────────

def require_auth(request: Request) -> Union[AuthResult, RedirectResponse]:
    """
    Drop-in replacement para o require_auth existente.

    Retorna AuthResult se autenticado, RedirectResponse se não.

    Usage:
        auth = require_auth(request)
        if isinstance(auth, RedirectResponse):
            return auth
        # auth.wallet_id, auth.email, etc.
    """
    auth = authenticate_request(request)
    if not auth.authenticated:
        return RedirectResponse(url="/travel/gate", status_code=302)
    return auth


def get_auth_context(request: Request) -> dict:
    """
    Retorna contexto de autenticação para templates/API.

    Returns:
        Dict com informação do utilizador ou vazio se não autenticado
    """
    auth = authenticate_request(request)
    if not auth.authenticated:
        return {}

    return {
        "wallet_id": auth.wallet_id,
        "email": auth.email,
        "name": auth.name,
        "tier": auth.tier,
        "is_sovereign": auth.is_sovereign,
        "device_trust": auth.device_trust,
        "authenticated": True
    }


def is_authenticated(request: Request) -> bool:
    """Quick check se request está autenticado."""
    return authenticate_request(request).authenticated


# ── Module Info ───────────────────────────────────────────────────────────────

__version__ = "1.0.0"
__module__ = "W-SESSION-001-MIDDLEWARE"
__author__ = "WINDI Publishing House"
__invariants__ = ["I1", "I9", "I13"]
