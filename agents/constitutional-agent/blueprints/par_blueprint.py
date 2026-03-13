"""
W-STD-PAR-001 — Protocol for Remote Activation (PAR)
WINDI Publishing House · Kempten, Bavaria · 2026-03-13

The PAR protocol enables .jmpg files to act as "seeds" that can activate
heavy content (4K video, raw footage, 360° media) stored in the WINDI Vault.

Architecture:
  SEED (.jmpg)  → Lightweight proxy with video_bridge metadata
  ROOT (Vault)  → Heavy content with forensic_hash sealed in Ledger
  BRIDGE        → Cryptographic handshake linking seed to root

Flow:
  1. Journalist captures 4K video → POST /vault/ingest → forensic_hash sealed
  2. JmpgAtomizer extracts keyframe → injects video_bridge → .jmpg (~150KB)
  3. .jmpg travels via WhatsApp/Telegram/Instagram (lightweight)
  4. Recipient opens in Canvas Gen 7 → detects video_bridge
  5. UI: "▶ WATCH VERIFIED VIDEO" → POST /par/activate
  6. forensic_hash verified vs Ledger → stream_token generated (TTL: 1h)
  7. Original 4K video streams with verification badge ✅

Constitutional Alignment:
  I9:  Human decides to activate (button click required)
  I5:  All activations logged in audit table
  I6:  Hash-chained audit trail
  I10: Activation receipts sealed in Forensic Ledger
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
from typing import Optional, Dict, Any
import urllib.request
import urllib.error

# ═══════════════════════════════════════════════════════════════════════════════
# Blueprint Setup
# ═══════════════════════════════════════════════════════════════════════════════

par_bp = Blueprint('par', __name__, url_prefix='/par')

DB_PATH = os.environ.get('PAR_DB', '/opt/windi/data/par_activations.db')
VAULT_API = os.environ.get('VAULT_API', 'http://localhost:8101')
LEDGER_API = os.environ.get('LEDGER_API', 'http://localhost:8101')

# Stream token TTL
STREAM_TOKEN_TTL_HOURS = 1

# Activation tiers
ACTIVATION_TIERS = {
    'FREE': {'max_resolution': '480p', 'max_duration_sec': 60, 'watermark': True},
    'MED': {'max_resolution': '720p', 'max_duration_sec': 300, 'watermark': True},
    'HIGH': {'max_resolution': '4K', 'max_duration_sec': 3600, 'watermark': False},
    'SOVEREIGN': {'max_resolution': '8K', 'max_duration_sec': None, 'watermark': False},
    'ORACLE': {'max_resolution': 'RAW', 'max_duration_sec': None, 'watermark': False},
}

# Schema types for video content
SCHEMA_TYPES = [
    'JOURNALISM',
    'TOURISM',
    'EDUCATION',
    'GOVERNANCE',
    'MEDICAL',
    'LEGAL',
    'INSURANCE',
    'REAL_ESTATE',
    'CUSTOM'
]

# ═══════════════════════════════════════════════════════════════════════════════
# Database Initialization
# ═══════════════════════════════════════════════════════════════════════════════

def get_db():
    """Get database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_par_db():
    """Initialize PAR database tables."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    with get_db() as conn:
        c = conn.cursor()

        # Vault entries (ingested videos)
        c.execute("""
            CREATE TABLE IF NOT EXISTS vault_entries (
                id              TEXT PRIMARY KEY,
                remote_id       TEXT NOT NULL UNIQUE,
                forensic_hash   TEXT NOT NULL,
                schema_type     TEXT DEFAULT 'CUSTOM',
                governance_level TEXT DEFAULT 'MED',
                video_duration_sec INTEGER,
                video_resolution TEXT,
                video_codec     TEXT,
                file_size_bytes INTEGER,
                storage_path    TEXT,
                owner_did       TEXT,
                created_at      TEXT NOT NULL,
                ledger_receipt  TEXT,
                status          TEXT DEFAULT 'active',
                metadata        TEXT DEFAULT '{}'
            )
        """)

        # Atomized seeds (.jmpg files created from vault entries)
        c.execute("""
            CREATE TABLE IF NOT EXISTS atomized_seeds (
                id              TEXT PRIMARY KEY,
                seed_id         TEXT NOT NULL UNIQUE,
                vault_entry_id  TEXT NOT NULL,
                keyframe_timestamp REAL,
                video_bridge    TEXT NOT NULL,
                jmpg_hash       TEXT,
                created_at      TEXT NOT NULL,
                created_by      TEXT,
                downloads       INTEGER DEFAULT 0,
                FOREIGN KEY (vault_entry_id) REFERENCES vault_entries(id)
            )
        """)

        # Activation records (PAR activations)
        c.execute("""
            CREATE TABLE IF NOT EXISTS activations (
                id              TEXT PRIMARY KEY,
                activation_id   TEXT NOT NULL UNIQUE,
                seed_id         TEXT NOT NULL,
                vault_entry_id  TEXT NOT NULL,
                requester_did   TEXT,
                requester_ip    TEXT,
                tier            TEXT DEFAULT 'FREE',
                stream_token    TEXT,
                token_expires_at TEXT,
                forensic_verified BOOLEAN DEFAULT FALSE,
                verification_time_ms INTEGER,
                activated_at    TEXT NOT NULL,
                ledger_receipt  TEXT,
                status          TEXT DEFAULT 'active',
                metadata        TEXT DEFAULT '{}'
            )
        """)

        # Audit log
        c.execute("""
            CREATE TABLE IF NOT EXISTS par_audit (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp       TEXT NOT NULL,
                action          TEXT NOT NULL,
                entity_type     TEXT NOT NULL,
                entity_id       TEXT NOT NULL,
                actor           TEXT,
                details         TEXT DEFAULT '{}',
                prev_hash       TEXT,
                entry_hash      TEXT NOT NULL
            )
        """)

        # Indexes
        c.execute("CREATE INDEX IF NOT EXISTS idx_vault_remote ON vault_entries(remote_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_vault_hash ON vault_entries(forensic_hash)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_seed_vault ON atomized_seeds(vault_entry_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_activation_seed ON activations(seed_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_activation_token ON activations(stream_token)")

        conn.commit()
        print(f"[W-PAR-001] DB initialized: {DB_PATH}")

# ═══════════════════════════════════════════════════════════════════════════════
# Utility Functions
# ═══════════════════════════════════════════════════════════════════════════════

def now_iso() -> str:
    """Current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def generate_id(prefix: str = "PAR") -> str:
    """Generate unique ID with prefix."""
    return f"{prefix}-{secrets.token_hex(12)}"

def generate_stream_token() -> str:
    """Generate secure stream token."""
    return secrets.token_urlsafe(32)

def hash_entry(data: str, prev_hash: str = "") -> str:
    """Generate SHA-256 hash for audit chain."""
    content = f"{prev_hash}:{data}"
    return hashlib.sha256(content.encode()).hexdigest()

def add_audit_entry(conn, action: str, entity_type: str, entity_id: str,
                    actor: str = None, details: dict = None):
    """Add hash-chained audit entry."""
    c = conn.cursor()

    # Get previous hash
    c.execute("SELECT entry_hash FROM par_audit ORDER BY id DESC LIMIT 1")
    row = c.fetchone()
    prev_hash = row['entry_hash'] if row else "GENESIS"

    timestamp = now_iso()
    details_json = json.dumps(details or {})

    # Compute entry hash
    entry_data = f"{timestamp}:{action}:{entity_type}:{entity_id}:{actor}:{details_json}"
    entry_hash = hash_entry(entry_data, prev_hash)

    c.execute("""
        INSERT INTO par_audit (timestamp, action, entity_type, entity_id, actor, details, prev_hash, entry_hash)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (timestamp, action, entity_type, entity_id, actor, details_json, prev_hash, entry_hash))

def verify_forensic_hash(remote_id: str, expected_hash: str) -> dict:
    """Verify forensic_hash against Ledger."""
    try:
        url = f"{LEDGER_API}/api/receipts?doc_id={remote_id}"
        req = urllib.request.Request(url, headers={'Accept': 'application/json'})

        start_time = time.time()
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
        elapsed_ms = int((time.time() - start_time) * 1000)

        if data.get('receipts') and len(data['receipts']) > 0:
            receipt = data['receipts'][0]
            ledger_hash = receipt.get('forensic_hash') or receipt.get('hash')

            if ledger_hash and hmac.compare_digest(ledger_hash, expected_hash):
                return {
                    'verified': True,
                    'elapsed_ms': elapsed_ms,
                    'receipt_id': receipt.get('id'),
                    'sealed_at': receipt.get('created_at')
                }

        return {'verified': False, 'elapsed_ms': elapsed_ms, 'reason': 'hash_mismatch'}

    except Exception as e:
        return {'verified': False, 'error': str(e), 'reason': 'ledger_unavailable'}

def seal_in_ledger(entity_id: str, action: str, payload: dict) -> Optional[str]:
    """Seal activation in Forensic Ledger."""
    try:
        url = f"{LEDGER_API}/api/receipts"
        data = json.dumps({
            "doc_id": entity_id,
            "doc_type": f"PAR_{action}",
            "governance_level": payload.get('governance_level', 'MED'),
            "metadata": payload
        }).encode('utf-8')

        req = urllib.request.Request(
            url,
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode())
            return result.get('receipt_id') or result.get('id')

    except Exception as e:
        print(f"[W-PAR-001] Ledger seal failed: {e}")
        return None

# ═══════════════════════════════════════════════════════════════════════════════
# Video Bridge Schema
# ═══════════════════════════════════════════════════════════════════════════════

class VideoBridgeSchema:
    """Schema for video_bridge payload in .jmpg files."""

    REQUIRED_FIELDS = ['source_type', 'remote_id', 'forensic_hash', 'gateway_endpoint']

    @staticmethod
    def build(remote_id: str, forensic_hash: str, keyframe_timestamp: float = 0,
              activation_tier: str = 'MED', schema_type: str = 'CUSTOM',
              video_duration_sec: int = None, video_resolution: str = None,
              video_codec: str = None, custom_claims: dict = None) -> dict:
        """Build a valid video_bridge payload."""

        bridge = {
            'source_type': 'WINDI_CLOUD_VIDEO',
            'remote_id': remote_id,
            'forensic_hash': forensic_hash,
            'gateway_endpoint': 'https://windi-domain.com/par/activate',
            'keyframe_timestamp': keyframe_timestamp,
            'activation_tier': activation_tier,
            'schema_type': schema_type,
            'version': '1.0.0',
            'created_at': now_iso()
        }

        if video_duration_sec:
            bridge['video_duration_sec'] = video_duration_sec
        if video_resolution:
            bridge['video_resolution'] = video_resolution
        if video_codec:
            bridge['video_codec'] = video_codec
        if custom_claims:
            bridge['custom_claims'] = custom_claims

        return bridge

    @staticmethod
    def validate(bridge: dict) -> tuple:
        """Validate video_bridge payload. Returns (valid, errors)."""
        errors = []

        for field in VideoBridgeSchema.REQUIRED_FIELDS:
            if field not in bridge or not bridge[field]:
                errors.append(f"Missing required field: {field}")

        if bridge.get('source_type') != 'WINDI_CLOUD_VIDEO':
            errors.append("Invalid source_type (must be WINDI_CLOUD_VIDEO)")

        if bridge.get('activation_tier') and bridge['activation_tier'] not in ACTIVATION_TIERS:
            errors.append(f"Invalid activation_tier: {bridge.get('activation_tier')}")

        if bridge.get('schema_type') and bridge['schema_type'] not in SCHEMA_TYPES:
            errors.append(f"Invalid schema_type: {bridge.get('schema_type')}")

        return (len(errors) == 0, errors)

# ═══════════════════════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@par_bp.route('/health', methods=['GET'])
def health():
    """Health check for PAR service."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) as total FROM vault_entries WHERE status = 'active'")
        vault_count = c.fetchone()['total']

        c.execute("SELECT COUNT(*) as total FROM atomized_seeds")
        seed_count = c.fetchone()['total']

        c.execute("SELECT COUNT(*) as total FROM activations WHERE status = 'active'")
        activation_count = c.fetchone()['total']

    return jsonify({
        "agent": "W-PAR-001",
        "version": "1.0.0",
        "status": "GREEN",
        "timestamp": now_iso(),
        "stats": {
            "vault_entries": vault_count,
            "atomized_seeds": seed_count,
            "active_activations": activation_count
        },
        "tiers": list(ACTIVATION_TIERS.keys()),
        "schema_types": SCHEMA_TYPES,
        "constitutional": {
            "I9": "Human activation required (button click)",
            "I5": "All activations logged",
            "I6": "Hash-chained audit trail",
            "I10": "Activations sealed in Forensic Ledger"
        }
    })


@par_bp.route('/vault/ingest', methods=['POST'])
def vault_ingest():
    """
    Ingest video into WINDI Vault.
    This creates the ROOT of the PAR protocol.
    """
    data = request.get_json() or {}

    # Required fields
    forensic_hash = data.get('forensic_hash')
    if not forensic_hash:
        return jsonify({"error": "forensic_hash required"}), 400

    # Generate IDs
    entry_id = generate_id("VE")
    remote_id = data.get('remote_id') or generate_id("W-VID")

    schema_type = data.get('schema_type', 'CUSTOM')
    if schema_type not in SCHEMA_TYPES:
        return jsonify({"error": f"Invalid schema_type: {schema_type}"}), 400

    governance_level = data.get('governance_level', 'MED')

    with get_db() as conn:
        c = conn.cursor()

        # Check for duplicate
        c.execute("SELECT id FROM vault_entries WHERE forensic_hash = ?", (forensic_hash,))
        if c.fetchone():
            return jsonify({"error": "Video with this forensic_hash already exists"}), 409

        created_at = now_iso()

        c.execute("""
            INSERT INTO vault_entries
            (id, remote_id, forensic_hash, schema_type, governance_level,
             video_duration_sec, video_resolution, video_codec, file_size_bytes,
             storage_path, owner_did, created_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry_id, remote_id, forensic_hash, schema_type, governance_level,
            data.get('video_duration_sec'), data.get('video_resolution'),
            data.get('video_codec'), data.get('file_size_bytes'),
            data.get('storage_path'), data.get('owner_did'),
            created_at, json.dumps(data.get('metadata', {}))
        ))

        # Seal in Ledger
        receipt_id = seal_in_ledger(remote_id, "VAULT_INGEST", {
            "forensic_hash": forensic_hash,
            "schema_type": schema_type,
            "governance_level": governance_level,
            "owner_did": data.get('owner_did')
        })

        if receipt_id:
            c.execute("UPDATE vault_entries SET ledger_receipt = ? WHERE id = ?",
                     (receipt_id, entry_id))

        add_audit_entry(conn, "VAULT_INGEST", "vault_entry", entry_id,
                       data.get('owner_did'), {"remote_id": remote_id})

        conn.commit()

    return jsonify({
        "entry_id": entry_id,
        "remote_id": remote_id,
        "forensic_hash": forensic_hash,
        "vault_url": f"https://windi-domain.com/vault/{remote_id}",
        "ledger_receipt": receipt_id,
        "status": "SEALED",
        "message": "Video ingested. Ready for atomization."
    }), 201


@par_bp.route('/atomize', methods=['POST'])
def atomize():
    """
    Create a SEED (.jmpg) from a vault entry.
    Returns the video_bridge payload to inject into .jmpg.
    """
    data = request.get_json() or {}

    remote_id = data.get('remote_id')
    if not remote_id:
        return jsonify({"error": "remote_id required"}), 400

    with get_db() as conn:
        c = conn.cursor()

        # Find vault entry
        c.execute("SELECT * FROM vault_entries WHERE remote_id = ? AND status = 'active'",
                 (remote_id,))
        vault = c.fetchone()

        if not vault:
            return jsonify({"error": "Vault entry not found"}), 404

        # Build video_bridge
        video_bridge = VideoBridgeSchema.build(
            remote_id=vault['remote_id'],
            forensic_hash=vault['forensic_hash'],
            keyframe_timestamp=data.get('keyframe_timestamp', 0),
            activation_tier=data.get('activation_tier', 'MED'),
            schema_type=vault['schema_type'],
            video_duration_sec=vault['video_duration_sec'],
            video_resolution=vault['video_resolution'],
            video_codec=vault['video_codec'],
            custom_claims=data.get('custom_claims')
        )

        # Create seed record
        seed_id = generate_id("SEED")
        created_at = now_iso()

        c.execute("""
            INSERT INTO atomized_seeds
            (id, seed_id, vault_entry_id, keyframe_timestamp, video_bridge, created_at, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            generate_id("AS"), seed_id, vault['id'],
            data.get('keyframe_timestamp', 0),
            json.dumps(video_bridge), created_at,
            data.get('created_by')
        ))

        add_audit_entry(conn, "ATOMIZE", "seed", seed_id,
                       data.get('created_by'), {"remote_id": remote_id})

        conn.commit()

    return jsonify({
        "seed_id": seed_id,
        "remote_id": remote_id,
        "video_bridge": video_bridge,
        "inject_as": "custom_claims.video_bridge",
        "message": "Inject this video_bridge into .jmpg APP1 metadata",
        "next_step": "Use irma-encoder to create .jmpg with this payload"
    }), 201


@par_bp.route('/activate', methods=['POST'])
def activate():
    """
    Activate remote content from a .jmpg seed.
    This is the core PAR handshake.

    I9 Compliant: Requires human action (button click) to trigger.
    """
    data = request.get_json() or {}

    video_bridge = data.get('video_bridge')
    if not video_bridge:
        return jsonify({"error": "video_bridge required"}), 400

    # Validate video_bridge
    valid, errors = VideoBridgeSchema.validate(video_bridge)
    if not valid:
        return jsonify({"error": "Invalid video_bridge", "details": errors}), 400

    remote_id = video_bridge['remote_id']
    expected_hash = video_bridge['forensic_hash']

    with get_db() as conn:
        c = conn.cursor()

        # Find vault entry
        c.execute("SELECT * FROM vault_entries WHERE remote_id = ? AND status = 'active'",
                 (remote_id,))
        vault = c.fetchone()

        if not vault:
            return jsonify({
                "error": "Content not found",
                "remote_id": remote_id,
                "suggestion": "The referenced video may have been removed or is not yet ingested"
            }), 404

        # Verify forensic_hash against Ledger (core security check)
        verification = verify_forensic_hash(remote_id, expected_hash)

        if not verification.get('verified'):
            return jsonify({
                "error": "Forensic verification failed",
                "reason": verification.get('reason'),
                "details": verification.get('error'),
                "message": "The content hash does not match the Ledger record. Possible tampering."
            }), 403

        # Check stored hash matches
        if not hmac.compare_digest(vault['forensic_hash'], expected_hash):
            return jsonify({
                "error": "Hash mismatch",
                "message": "The seed's forensic_hash does not match vault record"
            }), 403

        # Determine tier and capabilities
        requested_tier = video_bridge.get('activation_tier', 'FREE')
        tier_config = ACTIVATION_TIERS.get(requested_tier, ACTIVATION_TIERS['FREE'])

        # Generate stream token
        stream_token = generate_stream_token()
        token_expires = (datetime.now(timezone.utc) +
                        timedelta(hours=STREAM_TOKEN_TTL_HOURS)).isoformat().replace("+00:00", "Z")

        # Create activation record
        activation_id = generate_id("ACT")
        activated_at = now_iso()

        c.execute("""
            INSERT INTO activations
            (id, activation_id, seed_id, vault_entry_id, requester_did, requester_ip,
             tier, stream_token, token_expires_at, forensic_verified, verification_time_ms,
             activated_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            generate_id("A"), activation_id,
            video_bridge.get('seed_id', 'DIRECT'),
            vault['id'],
            data.get('requester_did'),
            request.remote_addr,
            requested_tier,
            stream_token,
            token_expires,
            True,
            verification.get('elapsed_ms', 0),
            activated_at,
            json.dumps(data.get('metadata', {}))
        ))

        # Seal activation in Ledger
        receipt_id = seal_in_ledger(activation_id, "ACTIVATION", {
            "remote_id": remote_id,
            "forensic_hash": expected_hash,
            "tier": requested_tier,
            "requester": data.get('requester_did'),
            "verified_at": activated_at
        })

        if receipt_id:
            c.execute("UPDATE activations SET ledger_receipt = ? WHERE activation_id = ?",
                     (receipt_id, activation_id))

        add_audit_entry(conn, "PAR_ACTIVATE", "activation", activation_id,
                       data.get('requester_did'), {
                           "remote_id": remote_id,
                           "tier": requested_tier,
                           "verification_ms": verification.get('elapsed_ms')
                       })

        conn.commit()

    # Build stream URL
    stream_url = f"https://windi-domain.com/par/stream/{remote_id}?token={stream_token}"

    return jsonify({
        "status": "activated",
        "activation_id": activation_id,
        "remote_id": remote_id,
        "stream_url": stream_url,
        "stream_token": stream_token,
        "token_expires_at": token_expires,
        "token_ttl_hours": STREAM_TOKEN_TTL_HOURS,
        "tier": requested_tier,
        "tier_capabilities": tier_config,
        "forensic_verification": {
            "verified": True,
            "elapsed_ms": verification.get('elapsed_ms'),
            "ledger_receipt": verification.get('receipt_id')
        },
        "activation_receipt": receipt_id,
        "video_info": {
            "duration_sec": vault['video_duration_sec'],
            "resolution": vault['video_resolution'],
            "codec": vault['video_codec'],
            "schema_type": vault['schema_type']
        },
        "message": "Content activated. Stream URL valid for 1 hour.",
        "i9_compliance": "Activation triggered by human action"
    })


@par_bp.route('/stream/<remote_id>', methods=['GET'])
def stream_info(remote_id):
    """
    Get stream information for activated content.
    Requires valid stream_token.
    """
    token = request.args.get('token')
    if not token:
        return jsonify({"error": "stream_token required"}), 401

    with get_db() as conn:
        c = conn.cursor()

        # Find activation by token
        c.execute("""
            SELECT a.*, v.storage_path, v.video_resolution, v.video_codec
            FROM activations a
            JOIN vault_entries v ON a.vault_entry_id = v.id
            WHERE a.stream_token = ? AND a.status = 'active'
        """, (token,))

        activation = c.fetchone()

        if not activation:
            return jsonify({"error": "Invalid or expired token"}), 403

        # Check expiration
        expires = datetime.fromisoformat(activation['token_expires_at'].replace('Z', '+00:00'))
        if datetime.now(timezone.utc) > expires:
            return jsonify({
                "error": "Token expired",
                "expired_at": activation['token_expires_at'],
                "message": "Request a new activation"
            }), 403

    return jsonify({
        "status": "valid",
        "remote_id": remote_id,
        "activation_id": activation['activation_id'],
        "tier": activation['tier'],
        "expires_at": activation['token_expires_at'],
        "stream_ready": True,
        "video_info": {
            "resolution": activation['video_resolution'],
            "codec": activation['video_codec']
        }
    })


@par_bp.route('/vault/<remote_id>', methods=['GET'])
def vault_info(remote_id):
    """Get vault entry info (public metadata only)."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT remote_id, schema_type, governance_level, video_duration_sec,
                   video_resolution, created_at, ledger_receipt, status
            FROM vault_entries WHERE remote_id = ?
        """, (remote_id,))

        entry = c.fetchone()

        if not entry:
            return jsonify({"error": "Not found"}), 404

    return jsonify({
        "remote_id": entry['remote_id'],
        "schema_type": entry['schema_type'],
        "governance_level": entry['governance_level'],
        "duration_sec": entry['video_duration_sec'],
        "resolution": entry['video_resolution'],
        "created_at": entry['created_at'],
        "ledger_receipt": entry['ledger_receipt'],
        "status": entry['status'],
        "activation_url": f"https://windi-domain.com/par/activate"
    })


@par_bp.route('/tiers', methods=['GET'])
def list_tiers():
    """List available activation tiers and their capabilities."""
    return jsonify({
        "tiers": ACTIVATION_TIERS,
        "schema_types": SCHEMA_TYPES,
        "stream_token_ttl_hours": STREAM_TOKEN_TTL_HOURS
    })
