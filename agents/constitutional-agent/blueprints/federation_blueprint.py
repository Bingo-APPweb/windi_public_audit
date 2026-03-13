"""
W-PROV-004 — Federation Protocol
================================
WINDI Publishing House · Kempten, Bavaria · 2026-03-13

Domain extension for the Constitutional Agent (Sandbox Core).
Integrates as /federation/* endpoints on :8091.

Philosophy:
  "A soberania não se delega — federe-se."

  A Federation não cria hierarquia.
  Ela conecta nós WINDI soberanos que escolhem confiar uns nos outros.
  Cada nó mantém a sua autonomia. A federação amplifica, não subordina.

Role:
  W-PROV-004 is LAYER 5 of the Proof Constellation:
    Genesis -> Propagation -> Forensic -> Reputation -> Federation

  The Protocol answers:
    - Quem são os nós federados?
    - Este receipt existe noutro Ledger?
    - Qual a confiança inter-nós?
    - Como verificar cross-border?

Architecture:
  ┌─────────────────┐         ┌─────────────────┐
  │   Nó Berlim     │◄───────►│   Nó Floripa    │
  │   (windi-eu)    │  Trust  │   (windi-br)    │
  │   Ledger A      │  Bridge │   Ledger B      │
  └─────────────────┘         └─────────────────┘
           │                           │
           └───────────┬───────────────┘
                       │
              Cross-Reference
              (receipt em A referencia B)

Critical Rules:
  - Nenhum nó controla outro (C-FED-001)
  - Federação é opt-in (C-FED-002)
  - Falha de um não afeta outros (C-FED-003)
  - Trust bridges são bidirecionais (C-FED-004)
  - Tudo é criptograficamente verificável (C-FED-005)

Federation Invariants (C-FED-001 to C-FED-005):
  C-FED-001 — Sovereignty:     No node is authoritative over another
  C-FED-002 — Opt-in:          Federation requires explicit consent
  C-FED-003 — Isolation:       Node failure doesn't cascade
  C-FED-004 — Bidirectional:   Trust bridges require mutual acknowledgment
  C-FED-005 — Verifiable:      All federation events are cryptographically provable

Principle: "AI processes. Human decides. WINDI guarantees."

Version: 1.0.0
Sealed: W-PROV-004
"""

import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import time
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import urllib.request
import urllib.error

from flask import Blueprint, jsonify, request

__version__ = "1.0.0"
__agent_id__ = "W-PROV-004"
__agent_name__ = "Federation Protocol"

# ═══════════════════════════════════════════════════════════════════════════════
# Blueprint Setup
# ═══════════════════════════════════════════════════════════════════════════════

federation_bp = Blueprint('federation', __name__, url_prefix='/federation')

# Database paths
FEDERATION_DIR = "/opt/windi/federation"
DB_PATH = os.path.join(FEDERATION_DIR, "federation.db")

# This node's identity
NODE_DID = os.environ.get('WINDI_NODE_DID', 'did:windi:node:floripa-001')
NODE_NAME = os.environ.get('WINDI_NODE_NAME', 'WINDI Florianópolis')
NODE_ENDPOINT = os.environ.get('WINDI_NODE_ENDPOINT', 'https://windi-domain.com')

# External services
LEDGER_API = os.environ.get('LEDGER_API', 'http://localhost:8101')

# ═══════════════════════════════════════════════════════════════════════════════
# Federation Invariants (C-FED-001 to C-FED-005)
# ═══════════════════════════════════════════════════════════════════════════════

class FederationInvariant(Enum):
    """The five federation invariants that govern inter-node operations."""
    C_FED_001 = ("C-FED-001", "sovereignty", "Nenhum no e autoritativo sobre outro")
    C_FED_002 = ("C-FED-002", "opt_in", "Federacao requer consentimento explicito")
    C_FED_003 = ("C-FED-003", "isolation", "Falha de um no nao cascateia")
    C_FED_004 = ("C-FED-004", "bidirectional", "Trust bridges requerem reconhecimento mutuo")
    C_FED_005 = ("C-FED-005", "verifiable", "Todos eventos sao criptograficamente provaveis")

    def __init__(self, code: str, name: str, description: str):
        self._code = code
        self._name = name
        self._description = description

# ═══════════════════════════════════════════════════════════════════════════════
# Trust Bridge States
# ═══════════════════════════════════════════════════════════════════════════════

class BridgeState(Enum):
    """States of a trust bridge between nodes."""
    PROPOSED = "proposed"           # One side proposed
    PENDING_MUTUAL = "pending"      # Waiting for other side
    ACTIVE = "active"               # Both sides confirmed
    SUSPENDED = "suspended"         # Temporarily disabled
    REVOKED = "revoked"             # Permanently terminated

# ═══════════════════════════════════════════════════════════════════════════════
# Database Schema
# ═══════════════════════════════════════════════════════════════════════════════

SCHEMA = """
-- Known nodes in the federation
CREATE TABLE IF NOT EXISTS nodes (
    did                 TEXT PRIMARY KEY,
    name                TEXT NOT NULL,
    endpoint            TEXT NOT NULL,
    public_key          TEXT,
    jurisdiction        TEXT,
    first_seen          TEXT,
    last_seen           TEXT,
    trust_score         REAL DEFAULT 0.5,
    status              TEXT DEFAULT 'discovered'
);

-- Trust bridges between this node and others
CREATE TABLE IF NOT EXISTS trust_bridges (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    bridge_id           TEXT UNIQUE NOT NULL,
    remote_did          TEXT NOT NULL,
    state               TEXT DEFAULT 'proposed',
    initiated_by        TEXT,
    challenge_sent      TEXT,
    challenge_received  TEXT,
    shared_secret_hash  TEXT,
    created_at          TEXT,
    confirmed_at        TEXT,
    last_heartbeat      TEXT,
    FOREIGN KEY (remote_did) REFERENCES nodes(did)
);

-- Cross-references to receipts in other nodes
CREATE TABLE IF NOT EXISTS cross_references (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    local_receipt       TEXT NOT NULL,
    remote_node_did     TEXT NOT NULL,
    remote_receipt      TEXT NOT NULL,
    reference_type      TEXT DEFAULT 'verification',
    verified            INTEGER DEFAULT 0,
    verified_at         TEXT,
    created_at          TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (remote_node_did) REFERENCES nodes(did)
);

-- Federation events log (immutable)
CREATE TABLE IF NOT EXISTS federation_events (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type          TEXT NOT NULL,
    local_did           TEXT NOT NULL,
    remote_did          TEXT,
    receipt_id          TEXT,
    event_hash          TEXT NOT NULL,
    previous_hash       TEXT,
    payload             TEXT,
    created_at          TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_bridge_remote ON trust_bridges(remote_did);
CREATE INDEX IF NOT EXISTS idx_xref_local ON cross_references(local_receipt);
CREATE INDEX IF NOT EXISTS idx_xref_remote ON cross_references(remote_receipt);
CREATE INDEX IF NOT EXISTS idx_events_type ON federation_events(event_type);
"""

def get_db():
    """Get database connection with schema initialization."""
    os.makedirs(FEDERATION_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn

def init_federation_db():
    """Initialize database on blueprint registration."""
    try:
        with get_db() as conn:
            # Register self as a node
            conn.execute("""
                INSERT OR IGNORE INTO nodes (did, name, endpoint, first_seen, status)
                VALUES (?, ?, ?, datetime('now'), 'self')
            """, (NODE_DID, NODE_NAME, NODE_ENDPOINT))
            conn.commit()
        print(f"[W-PROV-004] DB initialized: {DB_PATH}")
        print(f"[W-PROV-004] Node DID: {NODE_DID}")
    except Exception as e:
        print(f"[W-PROV-004] DB init error: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def generate_bridge_id(local_did: str, remote_did: str) -> str:
    """Generate deterministic bridge ID from two DIDs."""
    combined = "".join(sorted([local_did, remote_did]))
    return f"bridge-{hashlib.sha256(combined.encode()).hexdigest()[:16]}"

def generate_challenge() -> str:
    """Generate cryptographic challenge for bridge establishment."""
    return secrets.token_hex(32)

def hash_event(event_type: str, payload: dict, previous_hash: str = None) -> str:
    """Create hash-chain entry for federation event."""
    data = json.dumps({
        "type": event_type,
        "payload": payload,
        "previous": previous_hash,
        "timestamp": now_iso()
    }, sort_keys=True)
    return hashlib.sha256(data.encode()).hexdigest()

def get_last_event_hash() -> Optional[str]:
    """Get hash of last federation event for chain continuity."""
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT event_hash FROM federation_events ORDER BY id DESC LIMIT 1")
        row = c.fetchone()
        return row['event_hash'] if row else None

def log_federation_event(event_type: str, remote_did: str = None,
                         receipt_id: str = None, payload: dict = None) -> str:
    """Log immutable federation event with hash chain."""
    previous_hash = get_last_event_hash()
    event_hash = hash_event(event_type, payload or {}, previous_hash)

    with get_db() as conn:
        conn.execute("""
            INSERT INTO federation_events
            (event_type, local_did, remote_did, receipt_id, event_hash, previous_hash, payload)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (event_type, NODE_DID, remote_did, receipt_id, event_hash,
              previous_hash, json.dumps(payload) if payload else None))
        conn.commit()

    return event_hash

# ═══════════════════════════════════════════════════════════════════════════════
# Node Discovery & Registration
# ═══════════════════════════════════════════════════════════════════════════════

def discover_node(endpoint: str) -> Optional[Dict]:
    """
    Discover a WINDI node by querying its federation endpoint.
    Returns node info if valid WINDI node, None otherwise.
    """
    try:
        url = f"{endpoint.rstrip('/')}/federation/identity"
        req = urllib.request.Request(url, method='GET')
        req.add_header('User-Agent', f'WINDI-Federation/{__version__}')

        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))

            if data.get('ok') and data.get('did'):
                return {
                    "did": data['did'],
                    "name": data.get('name', 'Unknown Node'),
                    "endpoint": endpoint,
                    "jurisdiction": data.get('jurisdiction'),
                    "public_key": data.get('public_key'),
                    "version": data.get('version')
                }
    except Exception as e:
        print(f"[W-PROV-004] Discovery failed for {endpoint}: {e}")

    return None


def register_node(node_info: Dict) -> bool:
    """Register a discovered node in local database."""
    with get_db() as conn:
        conn.execute("""
            INSERT INTO nodes (did, name, endpoint, jurisdiction, public_key, first_seen, last_seen, status)
            VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'), 'discovered')
            ON CONFLICT(did) DO UPDATE SET
                name = excluded.name,
                endpoint = excluded.endpoint,
                jurisdiction = excluded.jurisdiction,
                public_key = excluded.public_key,
                last_seen = datetime('now')
        """, (
            node_info['did'],
            node_info['name'],
            node_info['endpoint'],
            node_info.get('jurisdiction'),
            node_info.get('public_key')
        ))
        conn.commit()

    log_federation_event("NODE_DISCOVERED", node_info['did'], payload=node_info)
    return True

# ═══════════════════════════════════════════════════════════════════════════════
# Trust Bridge Management
# ═══════════════════════════════════════════════════════════════════════════════

def propose_bridge(remote_did: str) -> Dict[str, Any]:
    """
    Propose a trust bridge to another node.
    This is step 1 of the bidirectional handshake (C-FED-004).
    """
    bridge_id = generate_bridge_id(NODE_DID, remote_did)
    challenge = generate_challenge()

    with get_db() as conn:
        # Check if bridge already exists
        c = conn.cursor()
        c.execute("SELECT * FROM trust_bridges WHERE bridge_id = ?", (bridge_id,))
        existing = c.fetchone()

        if existing:
            return {
                "ok": False,
                "error": "Bridge already exists",
                "bridge_id": bridge_id,
                "state": existing['state']
            }

        # Get remote node info
        c.execute("SELECT * FROM nodes WHERE did = ?", (remote_did,))
        node = c.fetchone()

        if not node:
            return {
                "ok": False,
                "error": "Remote node not discovered. Use /federation/discover first."
            }

        # Create bridge proposal
        conn.execute("""
            INSERT INTO trust_bridges
            (bridge_id, remote_did, state, initiated_by, challenge_sent, created_at)
            VALUES (?, ?, 'proposed', ?, ?, datetime('now'))
        """, (bridge_id, remote_did, NODE_DID, challenge))
        conn.commit()

    log_federation_event("BRIDGE_PROPOSED", remote_did, payload={
        "bridge_id": bridge_id,
        "initiated_by": NODE_DID
    })

    return {
        "ok": True,
        "bridge_id": bridge_id,
        "state": "proposed",
        "challenge": challenge,
        "message": f"Bridge proposed to {remote_did}. Send challenge to remote node for confirmation."
    }


def accept_bridge(bridge_id: str, remote_challenge: str) -> Dict[str, Any]:
    """
    Accept a bridge proposal from another node.
    This is step 2 of the bidirectional handshake (C-FED-004).
    """
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM trust_bridges WHERE bridge_id = ?", (bridge_id,))
        bridge = c.fetchone()

        if not bridge:
            return {"ok": False, "error": "Bridge not found"}

        if bridge['state'] == 'active':
            return {"ok": False, "error": "Bridge already active"}

        # Generate our response challenge
        our_challenge = generate_challenge()

        # Create shared secret from both challenges
        shared_secret = hashlib.sha256(
            f"{bridge['challenge_sent'] or ''}{remote_challenge}".encode()
        ).hexdigest()

        # Update bridge state
        conn.execute("""
            UPDATE trust_bridges SET
                state = 'active',
                challenge_received = ?,
                shared_secret_hash = ?,
                confirmed_at = datetime('now'),
                last_heartbeat = datetime('now')
            WHERE bridge_id = ?
        """, (remote_challenge, shared_secret[:32], bridge_id))
        conn.commit()

    log_federation_event("BRIDGE_ACTIVATED", bridge['remote_did'], payload={
        "bridge_id": bridge_id
    })

    return {
        "ok": True,
        "bridge_id": bridge_id,
        "state": "active",
        "challenge_response": our_challenge,
        "message": "Bridge activated. Cross-references now enabled."
    }

# ═══════════════════════════════════════════════════════════════════════════════
# Cross-Reference Operations
# ═══════════════════════════════════════════════════════════════════════════════

def create_cross_reference(local_receipt: str, remote_did: str,
                           remote_receipt: str, ref_type: str = "verification") -> Dict[str, Any]:
    """
    Create a cross-reference from a local receipt to a remote receipt.
    This enables inter-node proof verification.
    """
    with get_db() as conn:
        c = conn.cursor()

        # Verify we have an active bridge
        c.execute("""
            SELECT * FROM trust_bridges
            WHERE remote_did = ? AND state = 'active'
        """, (remote_did,))
        bridge = c.fetchone()

        if not bridge:
            return {
                "ok": False,
                "error": "No active trust bridge with this node",
                "invariant": "C-FED-004 - Bidirectional trust required"
            }

        # Create cross-reference
        conn.execute("""
            INSERT INTO cross_references
            (local_receipt, remote_node_did, remote_receipt, reference_type)
            VALUES (?, ?, ?, ?)
        """, (local_receipt, remote_did, remote_receipt, ref_type))
        conn.commit()

    # Log event
    event_hash = log_federation_event("CROSS_REFERENCE_CREATED", remote_did,
                                       local_receipt, payload={
        "local_receipt": local_receipt,
        "remote_receipt": remote_receipt,
        "reference_type": ref_type
    })

    return {
        "ok": True,
        "local_receipt": local_receipt,
        "remote_node": remote_did,
        "remote_receipt": remote_receipt,
        "reference_type": ref_type,
        "event_hash": event_hash,
        "message": "Cross-reference created. Verification pending."
    }


def verify_cross_reference(local_receipt: str, remote_did: str) -> Dict[str, Any]:
    """
    Verify a cross-reference by querying the remote node.
    """
    with get_db() as conn:
        c = conn.cursor()

        # Get cross-reference
        c.execute("""
            SELECT cr.*, n.endpoint
            FROM cross_references cr
            JOIN nodes n ON cr.remote_node_did = n.did
            WHERE cr.local_receipt = ? AND cr.remote_node_did = ?
        """, (local_receipt, remote_did))
        xref = c.fetchone()

        if not xref:
            return {"ok": False, "error": "Cross-reference not found"}

        # Query remote node
        try:
            url = f"{xref['endpoint']}/federation/verify/{xref['remote_receipt']}"
            req = urllib.request.Request(url, method='GET')
            req.add_header('X-WINDI-Node-DID', NODE_DID)

            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode('utf-8'))

                if data.get('ok') and data.get('verified'):
                    # Mark as verified
                    conn.execute("""
                        UPDATE cross_references SET
                            verified = 1,
                            verified_at = datetime('now')
                        WHERE local_receipt = ? AND remote_node_did = ?
                    """, (local_receipt, remote_did))
                    conn.commit()

                    log_federation_event("CROSS_REFERENCE_VERIFIED", remote_did,
                                         local_receipt, payload={"remote_receipt": xref['remote_receipt']})

                    return {
                        "ok": True,
                        "verified": True,
                        "local_receipt": local_receipt,
                        "remote_node": remote_did,
                        "remote_receipt": xref['remote_receipt'],
                        "verified_at": now_iso()
                    }
                else:
                    return {
                        "ok": True,
                        "verified": False,
                        "reason": data.get('error', 'Remote verification failed')
                    }

        except Exception as e:
            return {
                "ok": False,
                "error": f"Remote verification failed: {e}",
                "invariant": "C-FED-003 - Isolation preserved"
            }

# ═══════════════════════════════════════════════════════════════════════════════
# API Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@federation_bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) as nodes FROM nodes WHERE status != 'self'")
            known_nodes = c.fetchone()['nodes']
            c.execute("SELECT COUNT(*) as bridges FROM trust_bridges WHERE state = 'active'")
            active_bridges = c.fetchone()['bridges']
            c.execute("SELECT COUNT(*) as xrefs FROM cross_references")
            cross_refs = c.fetchone()['xrefs']
            c.execute("SELECT COUNT(*) as events FROM federation_events")
            events = c.fetchone()['events']
        db_ok = True
    except Exception:
        db_ok = False
        known_nodes = active_bridges = cross_refs = events = 0

    return jsonify({
        "status": "GREEN" if db_ok else "YELLOW",
        "agent": __agent_id__,
        "agent_name": __agent_name__,
        "version": __version__,
        "node": {
            "did": NODE_DID,
            "name": NODE_NAME,
            "endpoint": NODE_ENDPOINT
        },
        "known_nodes": known_nodes,
        "active_bridges": active_bridges,
        "cross_references": cross_refs,
        "federation_events": events,
        "invariants": ["C-FED-001", "C-FED-002", "C-FED-003", "C-FED-004", "C-FED-005"],
        "db_path": DB_PATH,
        "timestamp": now_iso()
    })


@federation_bp.route('/identity', methods=['GET'])
def get_identity():
    """
    GET /federation/identity

    Return this node's identity for discovery by other nodes.
    This is the entry point for federation handshakes.
    """
    return jsonify({
        "ok": True,
        "did": NODE_DID,
        "name": NODE_NAME,
        "endpoint": NODE_ENDPOINT,
        "jurisdiction": "BR",  # Could be configurable
        "version": __version__,
        "federation_api": f"{NODE_ENDPOINT}/federation",
        "capabilities": [
            "cross_reference",
            "trust_bridge",
            "receipt_verification"
        ],
        "invariants": ["C-FED-001", "C-FED-002", "C-FED-003", "C-FED-004", "C-FED-005"]
    })


@federation_bp.route('/discover', methods=['POST'])
def discover():
    """
    POST /federation/discover

    Discover and register a remote WINDI node.
    Body: { "endpoint": "https://remote-node.com" }
    """
    body = request.get_json(silent=True) or {}
    endpoint = body.get('endpoint', '').strip()

    if not endpoint:
        return jsonify({"ok": False, "error": "endpoint required"}), 400

    node_info = discover_node(endpoint)

    if not node_info:
        return jsonify({
            "ok": False,
            "error": "Could not discover WINDI node at this endpoint",
            "invariant": "C-FED-003 - Isolation preserved"
        }), 404

    register_node(node_info)

    return jsonify({
        "ok": True,
        "discovered": True,
        "node": node_info,
        "message": "Node discovered and registered. Use /federation/bridge/propose to establish trust."
    })


@federation_bp.route('/nodes', methods=['GET'])
def list_nodes():
    """
    GET /federation/nodes

    List all known nodes in the federation.
    """
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT n.*,
                   (SELECT state FROM trust_bridges WHERE remote_did = n.did ORDER BY id DESC LIMIT 1) as bridge_state
            FROM nodes n
            WHERE n.status != 'self'
            ORDER BY n.last_seen DESC
        """)
        rows = c.fetchall()

    nodes = [{
        "did": r['did'],
        "name": r['name'],
        "endpoint": r['endpoint'],
        "jurisdiction": r['jurisdiction'],
        "trust_score": r['trust_score'],
        "bridge_state": r['bridge_state'],
        "last_seen": r['last_seen']
    } for r in rows]

    return jsonify({
        "ok": True,
        "count": len(nodes),
        "nodes": nodes,
        "self": {
            "did": NODE_DID,
            "name": NODE_NAME
        }
    })


@federation_bp.route('/bridge/propose', methods=['POST'])
def propose_bridge_endpoint():
    """
    POST /federation/bridge/propose

    Propose a trust bridge to another node.
    Body: { "remote_did": "did:windi:node:xxx" }
    """
    body = request.get_json(silent=True) or {}
    remote_did = body.get('remote_did', '').strip()

    if not remote_did:
        return jsonify({"ok": False, "error": "remote_did required"}), 400

    result = propose_bridge(remote_did)
    return jsonify(result), 200 if result['ok'] else 400


@federation_bp.route('/bridge/accept', methods=['POST'])
def accept_bridge_endpoint():
    """
    POST /federation/bridge/accept

    Accept a bridge proposal from another node.
    Body: { "bridge_id": "bridge-xxx", "challenge": "xxx" }
    """
    body = request.get_json(silent=True) or {}
    bridge_id = body.get('bridge_id', '').strip()
    challenge = body.get('challenge', '').strip()

    if not bridge_id or not challenge:
        return jsonify({"ok": False, "error": "bridge_id and challenge required"}), 400

    result = accept_bridge(bridge_id, challenge)
    return jsonify(result), 200 if result['ok'] else 400


@federation_bp.route('/bridges', methods=['GET'])
def list_bridges():
    """
    GET /federation/bridges

    List all trust bridges.
    """
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT tb.*, n.name as remote_name
            FROM trust_bridges tb
            JOIN nodes n ON tb.remote_did = n.did
            ORDER BY tb.created_at DESC
        """)
        rows = c.fetchall()

    bridges = [{
        "bridge_id": r['bridge_id'],
        "remote_did": r['remote_did'],
        "remote_name": r['remote_name'],
        "state": r['state'],
        "initiated_by": r['initiated_by'],
        "created_at": r['created_at'],
        "confirmed_at": r['confirmed_at'],
        "last_heartbeat": r['last_heartbeat']
    } for r in rows]

    return jsonify({
        "ok": True,
        "count": len(bridges),
        "bridges": bridges,
        "invariant": "C-FED-004 - Bidirectional trust"
    })


@federation_bp.route('/xref/create', methods=['POST'])
def create_xref_endpoint():
    """
    POST /federation/xref/create

    Create a cross-reference to a receipt in another node.
    Body: {
        "local_receipt": "WINDI-xxx",
        "remote_did": "did:windi:node:xxx",
        "remote_receipt": "WINDI-yyy",
        "reference_type": "verification"
    }
    """
    body = request.get_json(silent=True) or {}

    local_receipt = body.get('local_receipt', '').strip()
    remote_did = body.get('remote_did', '').strip()
    remote_receipt = body.get('remote_receipt', '').strip()
    ref_type = body.get('reference_type', 'verification')

    if not all([local_receipt, remote_did, remote_receipt]):
        return jsonify({"ok": False, "error": "local_receipt, remote_did, and remote_receipt required"}), 400

    result = create_cross_reference(local_receipt, remote_did, remote_receipt, ref_type)
    return jsonify(result), 200 if result['ok'] else 400


@federation_bp.route('/xref/verify', methods=['POST'])
def verify_xref_endpoint():
    """
    POST /federation/xref/verify

    Verify a cross-reference against the remote node.
    Body: { "local_receipt": "WINDI-xxx", "remote_did": "did:windi:node:xxx" }
    """
    body = request.get_json(silent=True) or {}

    local_receipt = body.get('local_receipt', '').strip()
    remote_did = body.get('remote_did', '').strip()

    if not all([local_receipt, remote_did]):
        return jsonify({"ok": False, "error": "local_receipt and remote_did required"}), 400

    result = verify_cross_reference(local_receipt, remote_did)
    return jsonify(result)


@federation_bp.route('/xrefs', methods=['GET'])
def list_xrefs():
    """
    GET /federation/xrefs

    List all cross-references.
    Query params: verified (true/false), limit
    """
    verified_filter = request.args.get('verified')
    limit = min(request.args.get('limit', 50, type=int), 200)

    with get_db() as conn:
        c = conn.cursor()

        if verified_filter == 'true':
            c.execute("""
                SELECT cr.*, n.name as remote_name
                FROM cross_references cr
                JOIN nodes n ON cr.remote_node_did = n.did
                WHERE cr.verified = 1
                ORDER BY cr.created_at DESC
                LIMIT ?
            """, (limit,))
        elif verified_filter == 'false':
            c.execute("""
                SELECT cr.*, n.name as remote_name
                FROM cross_references cr
                JOIN nodes n ON cr.remote_node_did = n.did
                WHERE cr.verified = 0
                ORDER BY cr.created_at DESC
                LIMIT ?
            """, (limit,))
        else:
            c.execute("""
                SELECT cr.*, n.name as remote_name
                FROM cross_references cr
                JOIN nodes n ON cr.remote_node_did = n.did
                ORDER BY cr.created_at DESC
                LIMIT ?
            """, (limit,))

        rows = c.fetchall()

    xrefs = [{
        "local_receipt": r['local_receipt'],
        "remote_node": r['remote_node_did'],
        "remote_name": r['remote_name'],
        "remote_receipt": r['remote_receipt'],
        "reference_type": r['reference_type'],
        "verified": bool(r['verified']),
        "verified_at": r['verified_at'],
        "created_at": r['created_at']
    } for r in rows]

    return jsonify({
        "ok": True,
        "count": len(xrefs),
        "cross_references": xrefs
    })


@federation_bp.route('/verify/<path:receipt_id>', methods=['GET'])
def verify_receipt_for_federation(receipt_id: str):
    """
    GET /federation/verify/<receipt_id>

    Verify a receipt exists in this node's Ledger.
    Called by remote nodes during cross-reference verification.
    """
    caller_did = request.headers.get('X-WINDI-Node-DID', 'unknown')

    # Query local Ledger
    try:
        url = f"{LEDGER_API}/api/receipts/{receipt_id}"
        req = urllib.request.Request(url, method='GET')

        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))

            if data.get('ok') and data.get('receipt'):
                rec = data['receipt']

                # Log the federation verification event
                log_federation_event("RECEIPT_VERIFIED_BY_REMOTE", caller_did,
                                     receipt_id, payload={"status": rec.get('status')})

                return jsonify({
                    "ok": True,
                    "verified": True,
                    "receipt_id": receipt_id,
                    "status": rec.get('status'),
                    "governance_level": rec.get('governance_level'),
                    "created_at": rec.get('created_at'),
                    "node": NODE_DID
                })
    except Exception as e:
        pass

    return jsonify({
        "ok": True,
        "verified": False,
        "receipt_id": receipt_id,
        "error": "Receipt not found in this node's Ledger",
        "node": NODE_DID
    })


@federation_bp.route('/events', methods=['GET'])
def list_events():
    """
    GET /federation/events

    List federation events (hash-chained log).
    Query params: limit, type
    """
    limit = min(request.args.get('limit', 50, type=int), 200)
    event_type = request.args.get('type')

    with get_db() as conn:
        c = conn.cursor()

        if event_type:
            c.execute("""
                SELECT * FROM federation_events
                WHERE event_type = ?
                ORDER BY id DESC
                LIMIT ?
            """, (event_type, limit))
        else:
            c.execute("""
                SELECT * FROM federation_events
                ORDER BY id DESC
                LIMIT ?
            """, (limit,))

        rows = c.fetchall()

    events = [{
        "id": r['id'],
        "event_type": r['event_type'],
        "local_did": r['local_did'],
        "remote_did": r['remote_did'],
        "receipt_id": r['receipt_id'],
        "event_hash": r['event_hash'],
        "previous_hash": r['previous_hash'],
        "created_at": r['created_at']
    } for r in rows]

    return jsonify({
        "ok": True,
        "count": len(events),
        "events": events,
        "invariant": "C-FED-005 - Hash-chained event log"
    })


@federation_bp.route('/stats', methods=['GET'])
def stats():
    """
    GET /federation/stats

    Get federation statistics.
    """
    with get_db() as conn:
        c = conn.cursor()

        c.execute("SELECT COUNT(*) as n FROM nodes WHERE status != 'self'")
        known_nodes = c.fetchone()['n']

        c.execute("SELECT state, COUNT(*) as n FROM trust_bridges GROUP BY state")
        bridges_by_state = {r['state']: r['n'] for r in c.fetchall()}

        c.execute("SELECT verified, COUNT(*) as n FROM cross_references GROUP BY verified")
        xrefs_by_status = {
            "verified": 0,
            "pending": 0
        }
        for r in c.fetchall():
            if r['verified']:
                xrefs_by_status['verified'] = r['n']
            else:
                xrefs_by_status['pending'] = r['n']

        c.execute("SELECT event_type, COUNT(*) as n FROM federation_events GROUP BY event_type")
        events_by_type = {r['event_type']: r['n'] for r in c.fetchall()}

    return jsonify({
        "ok": True,
        "node": NODE_DID,
        "known_nodes": known_nodes,
        "bridges": bridges_by_state,
        "cross_references": xrefs_by_status,
        "events": events_by_type,
        "timestamp": now_iso()
    })


# ═══════════════════════════════════════════════════════════════════════════════
# Initialize on import
# ═══════════════════════════════════════════════════════════════════════════════

init_federation_db()
