#!/usr/bin/env python3
"""
WINDI Wallet Auth Patch
=======================
Adds authentication endpoints and serves the login frontend.
Blueprint to be registered in the existing Wallet Flask app.

Endpoints:
  GET  /                  → Login page (serves wallet_login.html)
  POST /api/auth/login    → Authenticate with wallet_id + passphrase
  GET  /api/auth/session  → Validate current session
  POST /api/auth/logout   → Destroy session

Security: HMAC-signed session tokens (no external deps needed)
Protocol: "AI processes. Human decides. WINDI guarantees."

Date: 2026-02-16
"""

import hashlib
import hmac
import json
import os
import time
from functools import wraps
from pathlib import Path

from flask import Blueprint, request, jsonify, send_file, make_response

# ── Config ────────────────────────────────────────────────
SECRET_KEY = os.environ.get("WINDI_AUTH_SECRET", "windi-wallet-dragon-2026-change-me")
SESSION_DURATION = 86400  # 24 hours
STATIC_DIR = Path(__file__).parent / "static"

auth_bp = Blueprint("auth", __name__)


# ── Token Utils ───────────────────────────────────────────
def _sign_token(payload: dict) -> str:
    """Create HMAC-signed session token."""
    payload_json = json.dumps(payload, sort_keys=True)
    signature = hmac.new(
        SECRET_KEY.encode(), payload_json.encode(), hashlib.sha256
    ).hexdigest()[:32]
    import base64
    token = base64.urlsafe_b64encode(payload_json.encode()).decode()
    return f"{token}.{signature}"


def _verify_token(token: str) -> dict | None:
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


def require_auth(f):
    """Decorator to require valid session."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # Check Authorization header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
        # Check cookie
        if not token:
            token = request.cookies.get("windi_session")
        if not token:
            return jsonify({"error": "authentication required"}), 401
        session = _verify_token(token)
        if not session:
            return jsonify({"error": "invalid or expired session"}), 401
        request.windi_session = session
        return f(*args, **kwargs)
    return decorated


# ── Auth Credentials Store ────────────────────────────────
# Simple file-based credential store
# Format: wallet_id → hashed_passphrase
CREDENTIALS_FILE = Path("/opt/windi/data/wallet_credentials.json")


def _load_credentials() -> dict:
    """Load credentials from file."""
    if CREDENTIALS_FILE.exists():
        with open(CREDENTIALS_FILE) as f:
            return json.load(f)
    return {}


def _save_credentials(creds: dict):
    """Save credentials to file."""
    CREDENTIALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(creds, f, indent=2)


def _hash_passphrase(passphrase: str) -> str:
    """Hash passphrase with SHA-256 + salt."""
    salt = "windi-dragon-salt-2026"
    return hashlib.sha256(f"{salt}:{passphrase}".encode()).hexdigest()


# ── Routes ────────────────────────────────────────────────

@auth_bp.route("/")
def login_page():
    """Serve the login/dashboard frontend."""
    html_path = STATIC_DIR / "wallet_login.html"
    if html_path.exists():
        return send_file(html_path, mimetype="text/html")
    return "<h1>WINDI Wallet — Frontend not deployed</h1>", 404


@auth_bp.route("/api/auth/login", methods=["POST"])
def login():
    """
    Authenticate user.
    Body: { "wallet_id": "WALLET-...", "passphrase": "..." }
    Returns: { "token": "...", "wallet_id": "...", "display_name": "..." }
    """
    data = request.get_json(silent=True) or {}
    wallet_id = data.get("wallet_id", "").strip()
    passphrase = data.get("passphrase", "").strip()

    if not wallet_id or not passphrase:
        return jsonify({"error": "wallet_id and passphrase required"}), 400

    # Load credentials
    creds = _load_credentials()

    if wallet_id not in creds:
        return jsonify({"error": "wallet not found or not registered"}), 404

    # Verify passphrase
    expected_hash = creds[wallet_id]["passphrase_hash"]
    provided_hash = _hash_passphrase(passphrase)

    if not hmac.compare_digest(expected_hash, provided_hash):
        return jsonify({"error": "invalid passphrase"}), 401

    # Create session token
    payload = {
        "wallet_id": wallet_id,
        "display_name": creds[wallet_id].get("display_name", wallet_id),
        "role": creds[wallet_id].get("role", "user"),
        "iat": int(time.time()),
        "exp": int(time.time()) + SESSION_DURATION,
    }
    token = _sign_token(payload)

    resp = make_response(jsonify({
        "token": token,
        "wallet_id": wallet_id,
        "display_name": payload["display_name"],
        "role": payload["role"],
        "expires_in": SESSION_DURATION,
    }))
    resp.set_cookie(
        "windi_session", token,
        httponly=True, secure=True, samesite="Strict",
        max_age=SESSION_DURATION
    )
    return resp


@auth_bp.route("/api/auth/session", methods=["GET"])
@require_auth
def session_check():
    """Check if current session is valid."""
    return jsonify({
        "valid": True,
        "wallet_id": request.windi_session["wallet_id"],
        "display_name": request.windi_session["display_name"],
        "role": request.windi_session["role"],
        "expires_at": request.windi_session["exp"],
    })


@auth_bp.route("/api/auth/logout", methods=["POST"])
def logout():
    """Destroy session."""
    resp = make_response(jsonify({"status": "logged out"}))
    resp.delete_cookie("windi_session")
    return resp


@auth_bp.route("/api/auth/register", methods=["POST"])
def register_passphrase():
    """
    Register a passphrase for an existing wallet.
    Body: { "wallet_id": "WALLET-...", "passphrase": "...", "admin_key": "..." }
    Requires admin_key for first-time registration.
    """
    data = request.get_json(silent=True) or {}
    wallet_id = data.get("wallet_id", "").strip()
    passphrase = data.get("passphrase", "").strip()
    admin_key = data.get("admin_key", "").strip()

    # Admin key for registration (change this!)
    ADMIN_KEY = os.environ.get("WINDI_ADMIN_KEY", "dragon-genesis-2026")

    if not wallet_id or not passphrase:
        return jsonify({"error": "wallet_id and passphrase required"}), 400

    if len(passphrase) < 8:
        return jsonify({"error": "passphrase must be at least 8 characters"}), 400

    if admin_key != ADMIN_KEY:
        return jsonify({"error": "invalid admin key"}), 403

    # Verify wallet exists in the wallet system
    # Import from parent app context
    try:
        from flask import current_app
        # Try to get wallet data
        import requests as req
        resp = req.get(f"http://127.0.0.1:8099/api/wallet/me?wallet_id={wallet_id}", timeout=5)
        if resp.status_code != 200:
            return jsonify({"error": "wallet_id not found in system"}), 404
        wallet_data = resp.json()
        display_name = wallet_data.get("display_name", wallet_id)
        role = wallet_data.get("role", "user")
    except Exception:
        display_name = wallet_id
        role = "user"

    creds = _load_credentials()
    creds[wallet_id] = {
        "passphrase_hash": _hash_passphrase(passphrase),
        "display_name": display_name,
        "role": role,
        "registered_at": time.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
    }
    _save_credentials(creds)

    return jsonify({
        "status": "registered",
        "wallet_id": wallet_id,
        "display_name": display_name,
    })


# ── Integration Helper ────────────────────────────────────
def register_auth(app):
    """
    Call this from the main wallet app to register auth routes.
    
    Usage in wallet main:
        from wallet_auth_patch import register_auth
        register_auth(app)
    """
    app.register_blueprint(auth_bp)
    print("  🔐 Auth blueprint registered")
    print("  📍 GET  /                  → Login page")
    print("  📍 POST /api/auth/login    → Authenticate")
    print("  📍 GET  /api/auth/session  → Session check")
    print("  📍 POST /api/auth/logout   → Logout")
    print("  📍 POST /api/auth/register → Register passphrase")
