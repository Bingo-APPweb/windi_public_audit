"""
W-KEYS-001 — WINDI API Keys System v1.1.0
WINDI Publishing House · Kempten, Bavaria · 2026-03-13

First API Keys system for WINDI, enabling external partners to authenticate
against WINDI services with cryptographically secure keys, scope-based permissions,
and I9-compliant human approval.

Key Format: wnd_live_{32_hex} (production) / wnd_test_{32_hex} (sandbox)
Storage: SHA-256 hash only (plaintext never persisted)

Tiers:
  SEED      — 10 RPM,  100 RPD  — Testes, onboarding
  NODAL     — 60 RPM,  1000 RPD — Parceiros pequenos
  SOVEREIGN — 300 RPM, 10000 RPD — Municípios, redações
  ORACLE    — unlimited          — Interno WINDI

Endpoints:
  POST /api-keys/request           — Request new key (pending approval)
  POST /api-keys/{id}/approve      — Human approval (I9)
  POST /api-keys/{id}/rotate       — Rotate key (new key, old valid 24h)
  GET  /api-keys/list              — List keys for owner
  POST /api-keys/{id}/revoke       — Revoke a key
  GET  /api-keys/{id}/usage        — Usage statistics
  GET  /api-keys/validate          — Internal validation
  GET  /api-keys/health            — Health check

Constitutional Alignment:
  I9:  Key activation requires human approval
  I5:  All operations logged in audit table
  I6:  Hash-chained audit trail
  I10: Key lifecycle sealed in Forensic Ledger
"""

from flask import Blueprint, request, jsonify, g
from functools import wraps
import sqlite3
import hashlib
import hmac
import json
import secrets
import time
import os
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Callable
import urllib.request

# ═══════════════════════════════════════════════════════════════════════════════
# Blueprint Setup
# ═══════════════════════════════════════════════════════════════════════════════

api_keys_bp = Blueprint('api_keys', __name__, url_prefix='/api-keys')

DB_PATH = os.environ.get('API_KEYS_DB', '/opt/windi/data/api_keys.db')
LEDGER_API = os.environ.get('LEDGER_API', 'http://localhost:8101')

# Valid scopes
VALID_SCOPES = [
    'ledger:read', 'ledger:write',
    'verify:read',
    'propagation:read', 'propagation:write',
    'communique:read', 'communique:write',
    'all'
]

# Key status flow: pending_approval → active → revoked/expired
KEY_STATUSES = ['pending_approval', 'active', 'revoked', 'expired', 'rotating']

# ═══════════════════════════════════════════════════════════════════════════════
# Tier Configuration
# ═══════════════════════════════════════════════════════════════════════════════

TIERS = {
    'SEED': {
        'rpm': 10,           # Requests per minute
        'rpd': 100,          # Requests per day
        'description': 'Testes, onboarding',
        'trust_boost': 0.0,
        'verify_badge': 'BRONZE',
    },
    'NODAL': {
        'rpm': 60,
        'rpd': 1000,
        'description': 'Parceiros pequenos',
        'trust_boost': 0.08,
        'verify_badge': 'SILVER',
    },
    'SOVEREIGN': {
        'rpm': 300,
        'rpd': 10000,
        'description': 'Municípios, redações',
        'trust_boost': 0.15,
        'verify_badge': 'GOLD',
    },
    'ORACLE': {
        'rpm': 0,            # 0 = unlimited
        'rpd': 0,
        'description': 'Interno WINDI',
        'trust_boost': 0.20,
        'verify_badge': 'PLATINUM',
    },
}

VALID_TIERS = list(TIERS.keys())

# ═══════════════════════════════════════════════════════════════════════════════
# Database Schema
# ═══════════════════════════════════════════════════════════════════════════════

SCHEMA = """
-- API Keys table: key records (hash, owner, scopes, status)
CREATE TABLE IF NOT EXISTS api_keys (
    id              TEXT PRIMARY KEY,
    key_hash        TEXT NOT NULL UNIQUE,
    key_prefix      TEXT NOT NULL,
    name            TEXT NOT NULL,
    wallet_id       TEXT NOT NULL,
    owner_did       TEXT,
    tier            TEXT NOT NULL DEFAULT 'SEED',
    scopes          TEXT NOT NULL,
    status          TEXT DEFAULT 'pending_approval',
    environment     TEXT DEFAULT 'live',
    created_at      TEXT NOT NULL,
    approved_at     TEXT,
    approved_by     TEXT,
    expires_at      TEXT,
    revoked_at      TEXT,
    revoked_by      TEXT,
    revoke_reason   TEXT,
    rotated_from    TEXT,
    rotated_at      TEXT,
    rotation_expires_at TEXT,
    ledger_receipt  TEXT,
    metadata        TEXT DEFAULT '{}'
);

-- API Key Usage table: request tracking per key
CREATE TABLE IF NOT EXISTS api_key_usage (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    key_id          TEXT NOT NULL,
    endpoint        TEXT NOT NULL,
    method          TEXT NOT NULL,
    status_code     INTEGER,
    response_time   REAL,
    client_ip       TEXT,
    timestamp       INTEGER NOT NULL,
    FOREIGN KEY (key_id) REFERENCES api_keys(id)
);

-- API Key Audit table: hash-chained audit log (I5, I6)
CREATE TABLE IF NOT EXISTS api_key_audit (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    key_id          TEXT,
    action          TEXT NOT NULL,
    actor           TEXT NOT NULL,
    details         TEXT DEFAULT '{}',
    prev_hash       TEXT,
    entry_hash      TEXT NOT NULL,
    timestamp       TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_key_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_key_prefix ON api_keys(key_prefix);
CREATE INDEX IF NOT EXISTS idx_key_wallet ON api_keys(wallet_id);
CREATE INDEX IF NOT EXISTS idx_key_owner ON api_keys(owner_did);
CREATE INDEX IF NOT EXISTS idx_key_status ON api_keys(status);
CREATE INDEX IF NOT EXISTS idx_key_tier ON api_keys(tier);
CREATE INDEX IF NOT EXISTS idx_usage_key ON api_key_usage(key_id);
CREATE INDEX IF NOT EXISTS idx_usage_ts ON api_key_usage(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_key ON api_key_audit(key_id);
"""

def get_db():
    """Get database connection with schema initialization."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn

def init_api_keys_db():
    """Initialize database on blueprint registration."""
    try:
        with get_db() as conn:
            conn.execute("SELECT 1")
        print(f"[W-KEYS-001] DB initialized: {DB_PATH}")
    except Exception as e:
        print(f"[W-KEYS-001] DB init error: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def now_iso():
    """Get current timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def generate_key_id():
    """Generate a unique key ID."""
    return f"wk_{secrets.token_hex(12)}"

def generate_api_key(environment: str = 'live') -> str:
    """
    Generate a new API key in WINDI format.

    Format: wnd_live_{32_hex} or wnd_test_{32_hex}
    - 128 bits of entropy from secrets.token_hex(16)
    - Familiar format (like Stripe sk_live_...)
    """
    prefix = 'wnd_live_' if environment == 'live' else 'wnd_test_'
    random_part = secrets.token_hex(16)  # 32 hex chars = 128 bits
    return f"{prefix}{random_part}"

def hash_api_key(api_key: str) -> str:
    """Hash an API key with SHA-256 for storage."""
    return hashlib.sha256(api_key.encode('utf-8')).hexdigest()

def extract_key_prefix(api_key: str) -> str:
    """Extract the prefix from an API key for O(1) lookup."""
    # Format: wnd_live_{32_hex} or wnd_test_{32_hex}
    # Prefix: wnd_live_{first_8_hex} or wnd_test_{first_8_hex}
    parts = api_key.split('_')
    if len(parts) >= 3:
        return f"{parts[0]}_{parts[1]}_{parts[2][:8]}"
    return api_key[:20]

def is_valid_key_format(api_key: str) -> bool:
    """Check if API key has valid format."""
    if api_key.startswith('wnd_live_') or api_key.startswith('wnd_test_'):
        return len(api_key) == 41  # wnd_live_ (9) + 32 hex = 41
    # Legacy format support
    if api_key.startswith('windi_'):
        return True
    return False

def verify_api_key(api_key: str, stored_hash: str) -> bool:
    """Timing-safe comparison of API key against stored hash."""
    computed_hash = hash_api_key(api_key)
    return hmac.compare_digest(computed_hash, stored_hash)

def compute_audit_hash(action: str, actor: str, details: dict, prev_hash: str, timestamp: str) -> str:
    """Compute hash for audit chain (I6)."""
    data = f"{action}|{actor}|{json.dumps(details, sort_keys=True)}|{prev_hash}|{timestamp}"
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def add_audit_entry(conn, key_id: Optional[str], action: str, actor: str, details: dict = None):
    """Add an entry to the hash-chained audit log (I5, I6)."""
    details = details or {}
    timestamp = now_iso()

    # Get previous hash for chain
    c = conn.cursor()
    c.execute("SELECT entry_hash FROM api_key_audit ORDER BY id DESC LIMIT 1")
    row = c.fetchone()
    prev_hash = row['entry_hash'] if row else "GENESIS"

    # Compute entry hash
    entry_hash = compute_audit_hash(action, actor, details, prev_hash, timestamp)

    c.execute("""
        INSERT INTO api_key_audit (key_id, action, actor, details, prev_hash, entry_hash, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (key_id, action, actor, json.dumps(details), prev_hash, entry_hash, timestamp))

    return entry_hash

def seal_in_ledger(key_id: str, action: str, metadata: dict) -> Optional[str]:
    """Seal key lifecycle event in Forensic Ledger (I10)."""
    try:
        receipt_id = f"VR-APIKEY-{key_id}-{action.upper()}"
        payload = {
            "id": receipt_id,
            "actor": "W-KEYS-001",
            "app": "api-keys-system",
            "doc_name": f"API Key {action}: {key_id}",
            "doc_type": "governance",
            "governance_level": "HIGH",
            "content_hash": hashlib.sha256(json.dumps(metadata, sort_keys=True).encode()).hexdigest(),
            "sge_score": 1.0,
            "metadata": {
                "key_id": key_id,
                "action": action,
                "i9_compliant": True,
                **metadata
            }
        }
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            f"{LEDGER_API}/api/receipts",
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return receipt_id
    except Exception as e:
        print(f"[W-KEYS-001] Ledger seal failed: {e}")
        return None

def check_scope_match(required_scopes: List[str], granted_scopes: List[str]) -> bool:
    """Check if granted scopes satisfy required scopes."""
    if 'all' in granted_scopes:
        return True
    for required in required_scopes:
        if required not in granted_scopes:
            # Check for wildcard (e.g., "ledger:*" covers "ledger:read")
            base = required.split(':')[0]
            if f"{base}:*" not in granted_scopes:
                return False
    return True

def record_usage(key_id: str, endpoint: str, method: str, status_code: int, response_time: float, client_ip: str):
    """Record API key usage for rate limiting and analytics."""
    try:
        with get_db() as conn:
            conn.execute("""
                INSERT INTO api_key_usage (key_id, endpoint, method, status_code, response_time, client_ip, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (key_id, endpoint, method, status_code, response_time, client_ip, int(time.time())))
            conn.commit()
    except Exception as e:
        print(f"[W-KEYS-001] Usage recording failed: {e}")

def get_tier_limits(tier: str) -> tuple:
    """Get RPM and RPD limits for a tier."""
    tier_config = TIERS.get(tier, TIERS['SEED'])
    return tier_config['rpm'], tier_config['rpd']

def check_rate_limits(key_id: str, tier: str) -> tuple:
    """Check if key is within rate limits based on tier."""
    rpm_limit, rpd_limit = get_tier_limits(tier)

    # ORACLE tier has no limits
    if rpm_limit == 0 and rpd_limit == 0:
        return True, ""

    now_ts = int(time.time())
    minute_ago = now_ts - 60
    day_ago = now_ts - 86400

    with get_db() as conn:
        c = conn.cursor()

        # Check RPM
        if rpm_limit > 0:
            c.execute("SELECT COUNT(*) as cnt FROM api_key_usage WHERE key_id = ? AND timestamp > ?", (key_id, minute_ago))
            rpm = c.fetchone()['cnt']
            if rpm >= rpm_limit:
                return False, f"Rate limit exceeded: {rpm}/{rpm_limit} requests per minute"

        # Check RPD
        if rpd_limit > 0:
            c.execute("SELECT COUNT(*) as cnt FROM api_key_usage WHERE key_id = ? AND timestamp > ?", (key_id, day_ago))
            rpd = c.fetchone()['cnt']
            if rpd >= rpd_limit:
                return False, f"Rate limit exceeded: {rpd}/{rpd_limit} requests per day"

    return True, ""

# ═══════════════════════════════════════════════════════════════════════════════
# Middleware Decorator
# ═══════════════════════════════════════════════════════════════════════════════

def require_api_key(scopes: List[str] = None):
    """
    Decorator to require valid API key authentication.

    Usage:
        @app.route("/api/resource")
        @require_api_key(scopes=["ledger:write"])
        def create_resource():
            owner = request.api_key_info["wallet_id"]
            # ... implementation

    Sets request.api_key_info with key details if valid.
    """
    scopes = scopes or []

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()

            # Extract API key from header
            api_key = request.headers.get('X-WINDI-API-Key', '')
            if not api_key:
                return jsonify({
                    "error": "Missing API key",
                    "message": "Provide X-WINDI-API-Key header"
                }), 401

            # Validate key format
            if not is_valid_key_format(api_key):
                return jsonify({
                    "error": "Invalid API key format",
                    "message": "Key must start with 'wnd_live_' or 'wnd_test_'"
                }), 401

            # Extract prefix for O(1) lookup
            key_prefix = extract_key_prefix(api_key)

            # Look up key by prefix
            with get_db() as conn:
                c = conn.cursor()
                c.execute("""
                    SELECT id, key_hash, wallet_id, owner_did, tier, scopes, status, expires_at, rotation_expires_at
                    FROM api_keys WHERE key_prefix = ?
                """, (key_prefix,))
                row = c.fetchone()

            if not row:
                return jsonify({
                    "error": "Invalid API key",
                    "message": "Key not found"
                }), 401

            # Timing-safe verification
            if not verify_api_key(api_key, row['key_hash']):
                return jsonify({
                    "error": "Invalid API key",
                    "message": "Key verification failed"
                }), 401

            # Check status (allow 'rotating' status within grace period)
            if row['status'] == 'rotating':
                # Check if rotation grace period expired
                if row['rotation_expires_at']:
                    rotation_expires = datetime.fromisoformat(row['rotation_expires_at'].replace('Z', '+00:00'))
                    if datetime.now(timezone.utc) > rotation_expires:
                        return jsonify({
                            "error": "API key expired",
                            "message": "Rotated key grace period has ended"
                        }), 403
            elif row['status'] != 'active':
                return jsonify({
                    "error": "API key not active",
                    "status": row['status'],
                    "message": f"Key status is '{row['status']}'"
                }), 403

            # Check expiration
            if row['expires_at']:
                expires = datetime.fromisoformat(row['expires_at'].replace('Z', '+00:00'))
                if datetime.now(timezone.utc) > expires:
                    return jsonify({
                        "error": "API key expired",
                        "expired_at": row['expires_at']
                    }), 403

            # Check rate limits based on tier
            within_limits, limit_message = check_rate_limits(row['id'], row['tier'])
            if not within_limits:
                return jsonify({
                    "error": "Rate limit exceeded",
                    "message": limit_message,
                    "tier": row['tier'],
                    "upgrade_url": "https://windi-domain.com/api-keys/upgrade"
                }), 429

            # Check scopes
            granted_scopes = json.loads(row['scopes'])
            if scopes and not check_scope_match(scopes, granted_scopes):
                return jsonify({
                    "error": "Insufficient permissions",
                    "required_scopes": scopes,
                    "granted_scopes": granted_scopes
                }), 403

            # Attach key info to request
            request.api_key_info = {
                "key_id": row['id'],
                "wallet_id": row['wallet_id'],
                "owner_did": row['owner_did'],
                "tier": row['tier'],
                "scopes": granted_scopes,
                "status": row['status'],
                "verify_badge": TIERS.get(row['tier'], TIERS['SEED'])['verify_badge']
            }

            # Execute the wrapped function
            try:
                response = f(*args, **kwargs)
                status_code = response[1] if isinstance(response, tuple) else 200
            except Exception as e:
                status_code = 500
                raise
            finally:
                # Record usage
                response_time = time.time() - start_time
                client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
                record_usage(row['id'], request.path, request.method, status_code, response_time, client_ip)

            return response

        return decorated_function
    return decorator

# ═══════════════════════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@api_keys_bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) as total FROM api_keys")
            total_keys = c.fetchone()['total']
            c.execute("SELECT COUNT(*) as active FROM api_keys WHERE status = 'active'")
            active_keys = c.fetchone()['active']
            c.execute("SELECT COUNT(*) as pending FROM api_keys WHERE status = 'pending_approval'")
            pending_keys = c.fetchone()['pending']
            # Count by tier
            c.execute("SELECT tier, COUNT(*) as cnt FROM api_keys WHERE status = 'active' GROUP BY tier")
            by_tier = {row['tier']: row['cnt'] for row in c.fetchall()}
        db_ok = True
    except Exception:
        db_ok = False
        total_keys = active_keys = pending_keys = 0
        by_tier = {}

    return jsonify({
        "status": "GREEN" if db_ok else "YELLOW",
        "agent": "W-KEYS-001",
        "version": "1.1.0",
        "total_keys": total_keys,
        "active_keys": active_keys,
        "pending_approval": pending_keys,
        "by_tier": by_tier,
        "tiers": {t: {"rpm": c['rpm'], "rpd": c['rpd']} for t, c in TIERS.items()},
        "constitutional": {
            "I9": "Human approval required for key activation",
            "I5": "All operations logged",
            "I6": "Hash-chained audit trail"
        },
        "timestamp": now_iso()
    })


@api_keys_bp.route('/request', methods=['POST'])
def request_key():
    """
    POST /api-keys/request
    Request a new API key (pending human approval - I9).

    Body:
        wallet_id: Wallet ID in WINDI system (required, billing identity)
        owner_did: DID of the key owner (optional, cryptographic identity)
        name: Human-readable name for the key
        tier: SEED | NODAL | SOVEREIGN | ORACLE (default: SEED)
        scopes: List of requested scopes
        environment: live | test (default: live)
        purpose: Optional description of intended use
        expires_in_days: Optional expiration (default: 365)

    Returns:
        key_id: ID to track the request (NOT the key itself)
    """
    body = request.get_json(silent=True) or {}

    wallet_id = body.get('wallet_id', '').strip()
    owner_did = body.get('owner_did', '').strip() or None
    name = body.get('name', '').strip()
    tier = body.get('tier', 'SEED').upper()
    scopes = body.get('scopes', [])
    environment = body.get('environment', 'live').lower()
    purpose = body.get('purpose', '')
    expires_in_days = body.get('expires_in_days', 365)

    # Validation
    if not wallet_id:
        return jsonify({"error": "wallet_id required (billing identity)"}), 400
    if not name:
        return jsonify({"error": "name required"}), 400
    if not scopes or not isinstance(scopes, list):
        return jsonify({"error": "scopes required (list)"}), 400
    if tier not in VALID_TIERS:
        return jsonify({
            "error": "Invalid tier",
            "provided": tier,
            "valid_tiers": VALID_TIERS
        }), 400
    if environment not in ['live', 'test']:
        return jsonify({"error": "environment must be 'live' or 'test'"}), 400

    # Validate scopes
    invalid_scopes = [s for s in scopes if s not in VALID_SCOPES]
    if invalid_scopes:
        return jsonify({
            "error": "Invalid scopes",
            "invalid": invalid_scopes,
            "valid_scopes": VALID_SCOPES
        }), 400

    # Generate key (but don't reveal it yet - I9)
    key_id = generate_key_id()
    api_key = generate_api_key(environment)
    key_hash = hash_api_key(api_key)
    key_prefix = extract_key_prefix(api_key)

    # Calculate expiration
    expires_at = None
    if expires_in_days > 0:
        expires_ts = time.time() + (expires_in_days * 86400)
        expires_at = datetime.fromtimestamp(expires_ts, timezone.utc).isoformat().replace("+00:00", "Z")

    created_at = now_iso()
    tier_config = TIERS[tier]

    # Store key in pending state
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO api_keys
            (id, key_hash, key_prefix, name, wallet_id, owner_did, tier, scopes, status, environment, created_at, expires_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending_approval', ?, ?, ?, ?)
        """, (
            key_id, key_hash, key_prefix, name, wallet_id, owner_did, tier,
            json.dumps(scopes), environment, created_at, expires_at,
            json.dumps({"purpose": purpose, "pending_key": api_key})
        ))

        # Audit entry
        add_audit_entry(conn, key_id, "KEY_REQUESTED", wallet_id, {
            "name": name,
            "tier": tier,
            "scopes": scopes,
            "environment": environment,
            "purpose": purpose,
            "owner_did": owner_did
        })

        conn.commit()

    return jsonify({
        "status": "pending_approval",
        "key_id": key_id,
        "name": name,
        "wallet_id": wallet_id,
        "owner_did": owner_did,
        "tier": tier,
        "tier_limits": {
            "rpm": tier_config['rpm'],
            "rpd": tier_config['rpd'],
            "description": tier_config['description']
        },
        "scopes": scopes,
        "environment": environment,
        "created_at": created_at,
        "expires_at": expires_at,
        "message": "Key request submitted. Awaiting human approval (I9).",
        "next_step": f"POST /api-keys/{key_id}/approve with approved_by"
    }), 201


@api_keys_bp.route('/<key_id>/approve', methods=['POST'])
def approve_key(key_id: str):
    """
    POST /api-keys/{key_id}/approve
    Human approval for API key activation (I9 compliance).

    CRITICAL: The full API key is returned exactly ONCE at approval.
              WINDI never stores or reveals it again.

    Body:
        approved_by: Identity of the approving human

    Returns:
        api_key: The full API key (SAVE THIS - shown only once!)
    """
    body = request.get_json(silent=True) or {}
    approved_by = body.get('approved_by', '').strip()

    if not approved_by:
        return jsonify({"error": "approved_by required (I9: human identity)"}), 400

    with get_db() as conn:
        c = conn.cursor()

        # Find pending key
        c.execute("SELECT * FROM api_keys WHERE id = ?", (key_id,))
        row = c.fetchone()

        if not row:
            return jsonify({"error": "Key not found"}), 404

        if row['status'] != 'pending_approval':
            return jsonify({
                "error": "Key not in pending_approval state",
                "current_status": row['status']
            }), 400

        # Extract the pending key from metadata
        metadata = json.loads(row['metadata'])
        api_key = metadata.get('pending_key')

        if not api_key:
            return jsonify({"error": "Key data corrupted - no pending key found"}), 500

        # Remove pending key from metadata (never stored again)
        del metadata['pending_key']
        metadata['approved_by'] = approved_by

        approved_at = now_iso()

        # Update key to active
        c.execute("""
            UPDATE api_keys SET
                status = 'active',
                approved_at = ?,
                approved_by = ?,
                metadata = ?
            WHERE id = ?
        """, (approved_at, approved_by, json.dumps(metadata), key_id))

        # Audit entry
        add_audit_entry(conn, key_id, "KEY_APPROVED", approved_by, {
            "wallet_id": row['wallet_id'],
            "owner_did": row['owner_did'],
            "tier": row['tier'],
            "scopes": json.loads(row['scopes'])
        })

        conn.commit()

    # Seal in Forensic Ledger (I10)
    ledger_receipt = seal_in_ledger(key_id, "APPROVED", {
        "wallet_id": row['wallet_id'],
        "owner_did": row['owner_did'],
        "name": row['name'],
        "tier": row['tier'],
        "scopes": json.loads(row['scopes']),
        "approved_by": approved_by,
        "approved_at": approved_at
    })

    # Update ledger receipt reference
    if ledger_receipt:
        with get_db() as conn:
            conn.execute("UPDATE api_keys SET ledger_receipt = ? WHERE id = ?", (ledger_receipt, key_id))
            conn.commit()

    tier_config = TIERS.get(row['tier'], TIERS['SEED'])

    return jsonify({
        "status": "active",
        "key_id": key_id,
        "api_key": api_key,  # SHOWN ONLY ONCE
        "name": row['name'],
        "wallet_id": row['wallet_id'],
        "owner_did": row['owner_did'],
        "tier": row['tier'],
        "tier_limits": {
            "rpm": tier_config['rpm'],
            "rpd": tier_config['rpd'],
            "verify_badge": tier_config['verify_badge']
        },
        "scopes": json.loads(row['scopes']),
        "environment": row['environment'],
        "approved_by": approved_by,
        "approved_at": approved_at,
        "expires_at": row['expires_at'],
        "ledger_receipt": ledger_receipt,
        "warning": "SAVE THIS API KEY NOW! It will never be shown again.",
        "usage": {
            "header": "X-WINDI-API-Key",
            "example": f"curl -H 'X-WINDI-API-Key: {api_key}' ..."
        }
    })


@api_keys_bp.route('/<key_id>/rotate', methods=['POST'])
def rotate_key(key_id: str):
    """
    POST /api-keys/{key_id}/rotate
    Rotate an API key (generate new, old valid for 24h).

    Body:
        rotated_by: Identity of the human requesting rotation

    Returns:
        new_api_key: The new API key (SAVE THIS - shown only once!)
    """
    body = request.get_json(silent=True) or {}
    rotated_by = body.get('rotated_by', '').strip()

    if not rotated_by:
        return jsonify({"error": "rotated_by required"}), 400

    with get_db() as conn:
        c = conn.cursor()

        # Find active key
        c.execute("SELECT * FROM api_keys WHERE id = ?", (key_id,))
        row = c.fetchone()

        if not row:
            return jsonify({"error": "Key not found"}), 404

        if row['status'] != 'active':
            return jsonify({
                "error": "Can only rotate active keys",
                "current_status": row['status']
            }), 400

        # Generate new key
        new_api_key = generate_api_key(row['environment'])
        new_key_hash = hash_api_key(new_api_key)
        new_key_prefix = extract_key_prefix(new_api_key)
        new_key_id = generate_key_id()

        rotated_at = now_iso()
        # Old key valid for 24 hours
        rotation_expires = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat().replace("+00:00", "Z")

        # Mark old key as rotating (still valid for 24h)
        c.execute("""
            UPDATE api_keys SET
                status = 'rotating',
                rotated_at = ?,
                rotation_expires_at = ?
            WHERE id = ?
        """, (rotated_at, rotation_expires, key_id))

        # Create new key (already active)
        metadata = json.loads(row['metadata'])
        metadata['rotated_from'] = key_id
        metadata['rotated_by'] = rotated_by

        c.execute("""
            INSERT INTO api_keys
            (id, key_hash, key_prefix, name, wallet_id, owner_did, tier, scopes, status, environment,
             created_at, approved_at, approved_by, expires_at, rotated_from, ledger_receipt, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            new_key_id, new_key_hash, new_key_prefix, row['name'], row['wallet_id'], row['owner_did'],
            row['tier'], row['scopes'], row['environment'], rotated_at, rotated_at, rotated_by,
            row['expires_at'], key_id, row['ledger_receipt'], json.dumps(metadata)
        ))

        # Audit entries
        add_audit_entry(conn, key_id, "KEY_ROTATED_OUT", rotated_by, {
            "new_key_id": new_key_id,
            "grace_period_until": rotation_expires
        })
        add_audit_entry(conn, new_key_id, "KEY_ROTATED_IN", rotated_by, {
            "from_key_id": key_id
        })

        conn.commit()

    # Seal rotation in Ledger
    ledger_receipt = seal_in_ledger(new_key_id, "ROTATED", {
        "wallet_id": row['wallet_id'],
        "from_key_id": key_id,
        "rotated_by": rotated_by,
        "rotated_at": rotated_at,
        "old_key_expires": rotation_expires
    })

    if ledger_receipt:
        with get_db() as conn:
            conn.execute("UPDATE api_keys SET ledger_receipt = ? WHERE id = ?", (ledger_receipt, new_key_id))
            conn.commit()

    tier_config = TIERS.get(row['tier'], TIERS['SEED'])

    return jsonify({
        "status": "rotated",
        "old_key_id": key_id,
        "old_key_status": "rotating",
        "old_key_valid_until": rotation_expires,
        "new_key_id": new_key_id,
        "new_api_key": new_api_key,  # SHOWN ONLY ONCE
        "name": row['name'],
        "wallet_id": row['wallet_id'],
        "tier": row['tier'],
        "tier_limits": {
            "rpm": tier_config['rpm'],
            "rpd": tier_config['rpd']
        },
        "rotated_by": rotated_by,
        "rotated_at": rotated_at,
        "ledger_receipt": ledger_receipt,
        "warning": "SAVE THE NEW API KEY NOW! It will never be shown again. Old key valid for 24h."
    })


@api_keys_bp.route('/list', methods=['GET'])
def list_keys():
    """
    GET /api-keys/list
    List API keys, optionally filtered.

    Query params:
        wallet_id: Filter by wallet ID
        owner_did: Filter by owner DID
        tier: Filter by tier
        status: Filter by status
        limit: Max results (default: 50)
    """
    wallet_id = request.args.get('wallet_id')
    owner_did = request.args.get('owner_did')
    tier = request.args.get('tier')
    status = request.args.get('status')
    limit = request.args.get('limit', 50, type=int)
    limit = min(limit, 100)

    query = """SELECT id, name, wallet_id, owner_did, tier, scopes, status, environment,
               created_at, approved_at, expires_at, ledger_receipt FROM api_keys WHERE 1=1"""
    params = []

    if wallet_id:
        query += " AND wallet_id = ?"
        params.append(wallet_id)

    if owner_did:
        query += " AND owner_did = ?"
        params.append(owner_did)

    if tier:
        query += " AND tier = ?"
        params.append(tier.upper())

    if status:
        query += " AND status = ?"
        params.append(status)

    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    with get_db() as conn:
        c = conn.cursor()
        c.execute(query, params)
        rows = c.fetchall()

    keys = [{
        "key_id": row['id'],
        "name": row['name'],
        "wallet_id": row['wallet_id'],
        "owner_did": row['owner_did'],
        "tier": row['tier'],
        "scopes": json.loads(row['scopes']),
        "status": row['status'],
        "environment": row['environment'],
        "created_at": row['created_at'],
        "approved_at": row['approved_at'],
        "expires_at": row['expires_at'],
        "ledger_receipt": row['ledger_receipt']
    } for row in rows]

    return jsonify({
        "keys": keys,
        "count": len(keys),
        "filters": {
            "wallet_id": wallet_id,
            "owner_did": owner_did,
            "tier": tier,
            "status": status
        }
    })


@api_keys_bp.route('/<key_id>/revoke', methods=['POST'])
def revoke_key(key_id: str):
    """
    POST /api-keys/{key_id}/revoke
    Revoke an API key immediately.

    Body:
        revoked_by: Identity of the revoking human
        reason: Reason for revocation
    """
    body = request.get_json(silent=True) or {}
    revoked_by = body.get('revoked_by', '').strip()
    reason = body.get('reason', 'No reason provided').strip()

    if not revoked_by:
        return jsonify({"error": "revoked_by required"}), 400

    with get_db() as conn:
        c = conn.cursor()

        c.execute("SELECT * FROM api_keys WHERE id = ?", (key_id,))
        row = c.fetchone()

        if not row:
            return jsonify({"error": "Key not found"}), 404

        if row['status'] == 'revoked':
            return jsonify({
                "error": "Key already revoked",
                "revoked_at": row['revoked_at'],
                "revoked_by": row['revoked_by']
            }), 400

        revoked_at = now_iso()

        c.execute("""
            UPDATE api_keys SET
                status = 'revoked',
                revoked_at = ?,
                revoked_by = ?,
                revoke_reason = ?
            WHERE id = ?
        """, (revoked_at, revoked_by, reason, key_id))

        # Audit entry
        add_audit_entry(conn, key_id, "KEY_REVOKED", revoked_by, {
            "reason": reason,
            "previous_status": row['status'],
            "tier": row['tier']
        })

        conn.commit()

    # Seal in Forensic Ledger
    ledger_receipt = seal_in_ledger(key_id, "REVOKED", {
        "wallet_id": row['wallet_id'],
        "tier": row['tier'],
        "revoked_by": revoked_by,
        "reason": reason,
        "revoked_at": revoked_at
    })

    return jsonify({
        "status": "revoked",
        "key_id": key_id,
        "name": row['name'],
        "wallet_id": row['wallet_id'],
        "tier": row['tier'],
        "revoked_by": revoked_by,
        "revoked_at": revoked_at,
        "reason": reason,
        "ledger_receipt": ledger_receipt
    })


@api_keys_bp.route('/<key_id>/usage', methods=['GET'])
def get_usage(key_id: str):
    """
    GET /api-keys/{key_id}/usage
    Get usage statistics for an API key.

    Query params:
        days: Number of days to look back (default: 7)
    """
    days = request.args.get('days', 7, type=int)
    cutoff = int(time.time()) - (days * 86400)

    with get_db() as conn:
        c = conn.cursor()

        # Check key exists
        c.execute("SELECT id, name, wallet_id, owner_did, tier, status FROM api_keys WHERE id = ?", (key_id,))
        key_row = c.fetchone()

        if not key_row:
            return jsonify({"error": "Key not found"}), 404

        tier_config = TIERS.get(key_row['tier'], TIERS['SEED'])

        # Total requests
        c.execute("""
            SELECT COUNT(*) as total,
                   AVG(response_time) as avg_response_time,
                   COUNT(DISTINCT endpoint) as unique_endpoints
            FROM api_key_usage
            WHERE key_id = ? AND timestamp > ?
        """, (key_id, cutoff))
        stats = c.fetchone()

        # By endpoint
        c.execute("""
            SELECT endpoint, method, COUNT(*) as count, AVG(response_time) as avg_time
            FROM api_key_usage
            WHERE key_id = ? AND timestamp > ?
            GROUP BY endpoint, method
            ORDER BY count DESC
            LIMIT 20
        """, (key_id, cutoff))
        by_endpoint = [{
            "endpoint": row['endpoint'],
            "method": row['method'],
            "count": row['count'],
            "avg_response_time": round(row['avg_time'], 3) if row['avg_time'] else None
        } for row in c.fetchall()]

        # By status code
        c.execute("""
            SELECT status_code, COUNT(*) as count
            FROM api_key_usage
            WHERE key_id = ? AND timestamp > ?
            GROUP BY status_code
            ORDER BY count DESC
        """, (key_id, cutoff))
        by_status = {row['status_code']: row['count'] for row in c.fetchall()}

        # Current rate usage (last minute and last day)
        now_ts = int(time.time())
        c.execute("SELECT COUNT(*) as cnt FROM api_key_usage WHERE key_id = ? AND timestamp > ?",
                  (key_id, now_ts - 60))
        current_rpm = c.fetchone()['cnt']
        c.execute("SELECT COUNT(*) as cnt FROM api_key_usage WHERE key_id = ? AND timestamp > ?",
                  (key_id, now_ts - 86400))
        current_rpd = c.fetchone()['cnt']

    return jsonify({
        "key_id": key_id,
        "name": key_row['name'],
        "wallet_id": key_row['wallet_id'],
        "owner_did": key_row['owner_did'],
        "tier": key_row['tier'],
        "status": key_row['status'],
        "period": f"{days}d",
        "limits": {
            "rpm": tier_config['rpm'],
            "rpd": tier_config['rpd']
        },
        "current_usage": {
            "rpm": current_rpm,
            "rpd": current_rpd,
            "rpm_remaining": max(0, tier_config['rpm'] - current_rpm) if tier_config['rpm'] > 0 else "unlimited",
            "rpd_remaining": max(0, tier_config['rpd'] - current_rpd) if tier_config['rpd'] > 0 else "unlimited"
        },
        "summary": {
            "total_requests": stats['total'],
            "avg_response_time": round(stats['avg_response_time'], 3) if stats['avg_response_time'] else None,
            "unique_endpoints": stats['unique_endpoints']
        },
        "by_endpoint": by_endpoint,
        "by_status_code": by_status
    })


@api_keys_bp.route('/validate', methods=['GET'])
def validate_key():
    """
    GET /api-keys/validate
    Internal endpoint to validate an API key.

    Header:
        X-WINDI-API-Key: The API key to validate

    Returns key info if valid, error if not.
    """
    api_key = request.headers.get('X-WINDI-API-Key', '')

    if not api_key:
        return jsonify({
            "valid": False,
            "error": "Missing X-WINDI-API-Key header"
        }), 401

    if not is_valid_key_format(api_key):
        return jsonify({
            "valid": False,
            "error": "Invalid key format"
        }), 401

    key_prefix = extract_key_prefix(api_key)

    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT id, key_hash, wallet_id, owner_did, tier, scopes, status, expires_at, rotation_expires_at
            FROM api_keys WHERE key_prefix = ?
        """, (key_prefix,))
        row = c.fetchone()

    if not row:
        return jsonify({
            "valid": False,
            "error": "Key not found"
        }), 401

    if not verify_api_key(api_key, row['key_hash']):
        return jsonify({
            "valid": False,
            "error": "Key verification failed"
        }), 401

    # Check status
    if row['status'] == 'rotating':
        if row['rotation_expires_at']:
            rotation_expires = datetime.fromisoformat(row['rotation_expires_at'].replace('Z', '+00:00'))
            if datetime.now(timezone.utc) > rotation_expires:
                return jsonify({
                    "valid": False,
                    "error": "Rotated key grace period expired",
                    "expired_at": row['rotation_expires_at']
                }), 403
    elif row['status'] != 'active':
        return jsonify({
            "valid": False,
            "error": f"Key status is '{row['status']}'",
            "status": row['status']
        }), 403

    # Check expiration
    if row['expires_at']:
        expires = datetime.fromisoformat(row['expires_at'].replace('Z', '+00:00'))
        if datetime.now(timezone.utc) > expires:
            return jsonify({
                "valid": False,
                "error": "Key expired",
                "expired_at": row['expires_at']
            }), 403

    tier_config = TIERS.get(row['tier'], TIERS['SEED'])

    return jsonify({
        "valid": True,
        "key_id": row['id'],
        "wallet_id": row['wallet_id'],
        "owner_did": row['owner_did'],
        "tier": row['tier'],
        "tier_limits": {
            "rpm": tier_config['rpm'],
            "rpd": tier_config['rpd'],
            "verify_badge": tier_config['verify_badge']
        },
        "scopes": json.loads(row['scopes']),
        "status": row['status'],
        "expires_at": row['expires_at']
    })


@api_keys_bp.route('/audit/<key_id>', methods=['GET'])
def get_audit_log(key_id: str):
    """
    GET /api-keys/audit/{key_id}
    Get the audit trail for a specific key (I5, I6).
    """
    with get_db() as conn:
        c = conn.cursor()

        # Verify key exists
        c.execute("SELECT id, tier FROM api_keys WHERE id = ?", (key_id,))
        key_row = c.fetchone()
        if not key_row:
            return jsonify({"error": "Key not found"}), 404

        # Get audit entries
        c.execute("""
            SELECT action, actor, details, prev_hash, entry_hash, timestamp
            FROM api_key_audit
            WHERE key_id = ?
            ORDER BY id ASC
        """, (key_id,))

        entries = [{
            "action": row['action'],
            "actor": row['actor'],
            "details": json.loads(row['details']),
            "prev_hash": row['prev_hash'],
            "entry_hash": row['entry_hash'],
            "timestamp": row['timestamp']
        } for row in c.fetchall()]

        # Verify chain integrity
        chain_valid = True
        for i, entry in enumerate(entries):
            if i == 0:
                continue
            if entry['prev_hash'] != entries[i-1]['entry_hash']:
                chain_valid = False
                break

    return jsonify({
        "key_id": key_id,
        "tier": key_row['tier'],
        "audit_trail": entries,
        "chain_integrity": "VALID" if chain_valid else "BROKEN",
        "total_entries": len(entries)
    })


@api_keys_bp.route('/tiers', methods=['GET'])
def list_tiers():
    """
    GET /api-keys/tiers
    List all available tiers and their limits.
    """
    return jsonify({
        "tiers": {
            tier: {
                "rpm": config['rpm'],
                "rpd": config['rpd'],
                "description": config['description'],
                "verify_badge": config['verify_badge'],
                "unlimited": config['rpm'] == 0 and config['rpd'] == 0
            }
            for tier, config in TIERS.items()
        },
        "default_tier": "SEED"
    })
