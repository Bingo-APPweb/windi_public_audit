"""
W-SESSION-001 — Sovereign Session Core
======================================
WINDI Publishing House · Kempten, Bavaria
Sealed: 02 Apr 2026

Modulo partilhado para sessoes soberanas.
Usado por Travel, LAW e futuros servicos WINDI.

Principios:
- DID e identidade primaria (nao email)
- Device binding via device_id (hash)
- Token HMAC-SHA256 (assinatura completa)
- Revogavel e com expiracao
- Fail-closed (DB down = nega acesso)

Invariantes:
- I1: Soberania Humana
- I9: Proibicao de Autonomia
- I13: Soberania de Dados
"""

import hmac
import hashlib
import json
import base64
import time
import uuid
import os
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, Tuple

# ==============================================================================
# CONFIGURACAO
# ==============================================================================

SESSION_SECRET_KEY = os.environ.get("WINDI_SESSION_SECRET")
if not SESSION_SECRET_KEY:
    raise RuntimeError(
        "WINDI_SESSION_SECRET not set! "
        "Generate with: python3 -c \"import secrets; print(secrets.token_hex(32))\""
    )
SESSION_TTL_DAYS = int(os.environ.get("SESSION_TTL_DAYS", "30"))
MAX_DEVICES_PER_DID = int(os.environ.get("MAX_DEVICES_PER_DID", "5"))
ENABLE_SOVEREIGN_SESSION = os.environ.get("ENABLE_SOVEREIGN_SESSION", "false").lower() == "true"

# ==============================================================================
# DATACLASSES
# ==============================================================================

@dataclass
class SessionPayload:
    """Payload do token de sessao."""
    did: str           # Identidade (did:windi:travel:xxx)
    device_id: str     # Hash do device fingerprint
    iat: int           # Issued at (Unix timestamp)
    exp: int           # Expires at (Unix timestamp)
    sid: str           # Session ID unico
    ver: int = 1       # Versao do schema


@dataclass
class SessionValidation:
    """Resultado da validacao do token."""
    valid: bool
    payload: Optional[SessionPayload] = None
    error: Optional[str] = None
    error_code: Optional[str] = None


# ==============================================================================
# TOKEN FUNCTIONS
# ==============================================================================

def create_session_token(
    did: str,
    device_id: str,
    ttl_days: int = None
) -> Tuple[str, SessionPayload]:
    """
    Cria token de sessao assinado com HMAC-SHA256.

    Args:
        did: Identidade do utilizador (did:windi:travel:xxx)
        device_id: Hash do device fingerprint (SHA-256)
        ttl_days: Tempo de vida em dias (default: SESSION_TTL_DAYS)

    Returns:
        Tuple[token_string, payload]
        Token format: base64url(payload).signature_hex

    Security:
        - Assinatura completa (64 chars hex)
        - Payload JSON sorted keys (deterministic)
        - device_id binding (previne token roubado)
    """
    ttl = ttl_days or SESSION_TTL_DAYS
    now = int(time.time())
    session_id = str(uuid.uuid4())

    payload = SessionPayload(
        did=did,
        device_id=device_id,
        iat=now,
        exp=now + (ttl * 86400),
        sid=session_id,
        ver=1
    )

    # JSON deterministic (sorted keys, no spaces)
    payload_dict = asdict(payload)
    payload_json = json.dumps(payload_dict, sort_keys=True, separators=(',', ':'))

    # Base64url encode (URL-safe, no padding)
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode().rstrip('=')

    # HMAC-SHA256 signature (COMPLETA - nao truncada)
    signature = hmac.new(
        SESSION_SECRET_KEY.encode(),
        payload_json.encode(),
        hashlib.sha256
    ).hexdigest()  # 64 chars hex

    token = f"{payload_b64}.{signature}"

    return token, payload


def verify_session_token(token: str) -> SessionValidation:
    """
    Verifica token de sessao.

    Checks:
        1. Formato valido (payload.signature)
        2. Assinatura HMAC-SHA256 valida
        3. Token nao expirado

    Returns:
        SessionValidation com valid=True/False

    Note:
        Esta funcao faz verificacao STATELESS.
        Verificacao de revogacao requer DB lookup.
    """
    if not token or not isinstance(token, str):
        return SessionValidation(
            valid=False,
            error="Token vazio ou invalido",
            error_code="empty_token"
        )

    try:
        # Split token
        parts = token.split('.')
        if len(parts) != 2:
            return SessionValidation(
                valid=False,
                error="Formato de token invalido",
                error_code="invalid_format"
            )

        payload_b64, signature = parts

        # Restore base64 padding
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += '=' * padding

        # Decode payload
        try:
            payload_json = base64.urlsafe_b64decode(payload_b64).decode('utf-8')
        except Exception:
            return SessionValidation(
                valid=False,
                error="Payload corrompido",
                error_code="corrupt_payload"
            )

        # Verify signature (COMPLETA)
        expected_sig = hmac.new(
            SESSION_SECRET_KEY.encode(),
            payload_json.encode(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(expected_sig, signature):
            return SessionValidation(
                valid=False,
                error="Assinatura invalida",
                error_code="invalid_signature"
            )

        # Parse payload
        try:
            payload_dict = json.loads(payload_json)
        except json.JSONDecodeError:
            return SessionValidation(
                valid=False,
                error="JSON invalido",
                error_code="invalid_json"
            )

        # Check required fields
        required = ['did', 'device_id', 'iat', 'exp', 'sid']
        for field in required:
            if field not in payload_dict:
                return SessionValidation(
                    valid=False,
                    error=f"Campo obrigatorio em falta: {field}",
                    error_code="missing_field"
                )

        # Check expiration
        if payload_dict.get("exp", 0) < int(time.time()):
            return SessionValidation(
                valid=False,
                error="Sessao expirada",
                error_code="expired"
            )

        # Success
        payload = SessionPayload(
            did=payload_dict["did"],
            device_id=payload_dict["device_id"],
            iat=payload_dict["iat"],
            exp=payload_dict["exp"],
            sid=payload_dict["sid"],
            ver=payload_dict.get("ver", 1)
        )

        return SessionValidation(valid=True, payload=payload)

    except Exception as e:
        return SessionValidation(
            valid=False,
            error=f"Erro de verificacao: {str(e)}",
            error_code="verification_error"
        )


# ==============================================================================
# DEVICE FUNCTIONS
# ==============================================================================

def generate_device_id(device_seed: str, user_agent: str = "") -> str:
    """
    Gera device_id a partir do seed e user agent.

    Args:
        device_seed: Seed aleatorio gerado no browser (localStorage)
        user_agent: User-Agent header

    Returns:
        SHA-256 hash (64 chars hex)

    Note:
        device_seed NUNCA e armazenado no backend.
        Apenas o device_id (hash) e conhecido pelo servidor.
    """
    # Combinar seed com UA para fingerprint mais forte
    data = f"windi:device:{device_seed}:{user_agent}"
    return hashlib.sha256(data.encode()).hexdigest()


def hash_ip_for_signal(ip: str) -> str:
    """
    Hash do IP para sinal de risco (NAO para autenticacao).

    Args:
        ip: Endereco IP

    Returns:
        SHA-256 truncado (16 chars) - apenas para comparacao

    Security:
        Este hash e usado APENAS como sinal secundario.
        Mudanca de IP nao bloqueia acesso.
        Usado para detectar anomalias.
    """
    if not ip:
        return "unknown"
    # Truncar para privacidade - apenas para comparacao
    return hashlib.sha256(f"windi:ip:{ip}".encode()).hexdigest()[:16]


# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================

def is_valid_windi_did(did: str) -> bool:
    """
    Valida formato de DID WINDI.

    Formatos aceites:
        - did:windi:travel:xxx (4 parts)
        - did:windi:law:xxx (4 parts)
        - did:windi:xxx (3 parts - generic)
        - WID-TRAVEL-xxx (legacy)
        - WID-LAW-xxx (legacy)
    """
    if not did or not isinstance(did, str):
        return False

    # Formato novo
    if did.startswith("did:windi:"):
        parts = did.split(":")
        # Accept both 3-part (did:windi:uuid) and 4-part (did:windi:travel:uuid)
        if len(parts) == 3:
            return len(parts[2]) > 0  # Just check uuid exists
        if len(parts) >= 4:
            return parts[2] in ("travel", "law", "wallet")
        return False

    # Formato legacy
    if did.startswith("WID-TRAVEL-") or did.startswith("WID-LAW-"):
        return len(did) > 12

    return False


def get_device_name_from_ua(user_agent: str) -> str:
    """
    Extrai nome amigavel do device a partir do User-Agent.
    """
    if not user_agent:
        return "Unknown Device"

    ua = user_agent.lower()

    # Mobile
    if 'iphone' in ua:
        return 'iPhone'
    if 'ipad' in ua:
        return 'iPad'
    if 'android' in ua:
        if 'mobile' in ua:
            return 'Android Phone'
        return 'Android Tablet'

    # Desktop
    if 'macintosh' in ua or 'mac os' in ua:
        browser = 'Safari' if 'safari' in ua and 'chrome' not in ua else 'Chrome' if 'chrome' in ua else 'Browser'
        return f'{browser} on macOS'
    if 'windows' in ua:
        browser = 'Edge' if 'edg' in ua else 'Chrome' if 'chrome' in ua else 'Firefox' if 'firefox' in ua else 'Browser'
        return f'{browser} on Windows'
    if 'linux' in ua:
        browser = 'Chrome' if 'chrome' in ua else 'Firefox' if 'firefox' in ua else 'Browser'
        return f'{browser} on Linux'

    return 'Unknown Device'


def format_did_short(did: str) -> str:
    """
    Formata DID para exibicao (truncado).
    Exemplo: did:windi:travel:a1b2c3... -> did:windi:travel:a1b2...
    """
    if not did:
        return "Unknown"
    if len(did) <= 25:
        return did
    return did[:22] + "..."


def seconds_until_expiry(exp: int) -> int:
    """Retorna segundos ate expiracao."""
    return max(0, exp - int(time.time()))


def days_until_expiry(exp: int) -> int:
    """Retorna dias ate expiracao."""
    return seconds_until_expiry(exp) // 86400


# ==============================================================================
# CONSTANTS
# ==============================================================================

# Estados de sessao
SESSION_STATE_ACTIVE = "ACTIVE"
SESSION_STATE_REVOKED = "REVOKED"
SESSION_STATE_EXPIRED = "EXPIRED"

# Trust levels para devices
DEVICE_TRUST_NEW = "NEW"           # Primeiro uso
DEVICE_TRUST_KNOWN = "KNOWN"       # 3+ logins
DEVICE_TRUST_TRUSTED = "TRUSTED"   # 10+ logins

# Razoes de revogacao
REVOKE_REASON_USER = "user_request"
REVOKE_REASON_SECURITY = "security"
REVOKE_REASON_ADMIN = "admin"
REVOKE_REASON_EXPIRED = "expired"


# ==============================================================================
# MODULE INFO
# ==============================================================================

__version__ = "1.0.0"
__module__ = "W-SESSION-001"
__author__ = "WINDI Publishing House"
__invariants__ = ["I1", "I9", "I13"]
