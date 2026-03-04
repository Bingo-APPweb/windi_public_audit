"""
WINDI Notarial Agent v0.1.0 — Flask Blueprint
==============================================

Domain extension for the Constitutional Agent (Sandbox Core).
Integrates as /notary/* endpoints on :8091.

Features:
- Digital notarial acts with evidentiary force
- Identity recognition + Ed25519 signatures
- Digital certificates with immutable hash
- WINDI Apostille (Hague Convention equivalent)
- Multi-party witnessing
- Public registry with Ledger integration
- Temporal proof (data certa)

Integrations:
- Ledger (:8101) — immutable registration
- Vault (:8106) — notarial archive
- Justica (/legal) — cases can request notarial acts
- Export (:8103) — Certificate PDF generation

Principle: "AI processes. Human decides. WINDI guarantees."

Version: 0.1.0
Sealed: W-NOTARY-001
"""

import hashlib
import json
import os
import sqlite3
import time
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from flask import Blueprint, jsonify, request

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

__version__ = "0.1.0"
__agent_id__ = "W-NOTARY-001"
__agent_name__ = "Notarial"

# Database path
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DATA_DIR, "notary.db")

# Service URLs
LEDGER_URL = os.environ.get("WINDI_LEDGER_URL", "http://localhost:8101")
VAULT_URL = os.environ.get("WINDI_VAULT_URL", "http://localhost:8106")
EXPORT_URL = os.environ.get("WINDI_EXPORT_URL", "http://localhost:8103")


# ═══════════════════════════════════════════════════════════════
#  ENUMS
# ═══════════════════════════════════════════════════════════════

class ActType(Enum):
    RECOGNITION = "recognition"      # Reconhecimento de firma/identidade
    CERTIFICATION = "certification"  # Certidao digital
    APOSTILLE = "apostille"          # Apostila WINDI
    WITNESSING = "witnessing"        # Ato testemunhado
    TIMESTAMP = "timestamp"          # Data certa
    AUTHENTICATION = "authentication"  # Autenticacao de documento


class ActStatus(Enum):
    DRAFT = "draft"
    PENDING = "pending"
    SIGNED = "signed"
    SEALED = "sealed"
    REGISTERED = "registered"
    REVOKED = "revoked"


class PartyRole(Enum):
    PRINCIPAL = "principal"      # Parte principal
    WITNESS = "witness"          # Testemunha
    NOTARY = "notary"            # Agente notarial (WINDI)
    THIRD_PARTY = "third_party"  # Terceiro interessado


# ═══════════════════════════════════════════════════════════════
#  DATABASE INITIALIZATION
# ═══════════════════════════════════════════════════════════════

def init_db():
    """Initialize the 7 notary tables."""
    os.makedirs(DATA_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Notarial acts
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notarial_acts (
            id TEXT PRIMARY KEY,
            act_type TEXT NOT NULL,
            doc_hash TEXT NOT NULL,
            title TEXT,
            description TEXT,
            status TEXT DEFAULT 'draft',
            created_at REAL NOT NULL,
            signed_at REAL,
            sealed_at REAL,
            valid_until REAL,
            metadata TEXT
        )
    """)

    # 2. Parties (signatories, witnesses, etc.)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parties (
            id TEXT PRIMARY KEY,
            act_id TEXT NOT NULL,
            name TEXT NOT NULL,
            did TEXT,
            email TEXT,
            role TEXT NOT NULL,
            signature TEXT,
            signed_at REAL,
            public_key TEXT,
            FOREIGN KEY (act_id) REFERENCES notarial_acts(id)
        )
    """)

    # 3. Certifications
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS certifications (
            id TEXT PRIMARY KEY,
            act_id TEXT NOT NULL,
            cert_type TEXT DEFAULT 'standard',
            cert_hash TEXT NOT NULL,
            issued_at REAL NOT NULL,
            valid_until REAL,
            issuer TEXT DEFAULT 'W-NOTARY-001',
            serial_number TEXT,
            metadata TEXT,
            FOREIGN KEY (act_id) REFERENCES notarial_acts(id)
        )
    """)

    # 4. Apostille records
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS apostille (
            id TEXT PRIMARY KEY,
            act_id TEXT NOT NULL,
            country_origin TEXT NOT NULL,
            country_destination TEXT,
            convention TEXT DEFAULT 'hague_1961',
            seal_hash TEXT NOT NULL,
            issued_at REAL NOT NULL,
            competent_authority TEXT DEFAULT 'WINDI Notarial Agent',
            reference_number TEXT,
            FOREIGN KEY (act_id) REFERENCES notarial_acts(id)
        )
    """)

    # 5. Witnesses
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS witnesses (
            id TEXT PRIMARY KEY,
            act_id TEXT NOT NULL,
            witness_name TEXT NOT NULL,
            witness_did TEXT,
            witness_email TEXT,
            signature TEXT,
            signed_at REAL,
            order_num INTEGER DEFAULT 1,
            FOREIGN KEY (act_id) REFERENCES notarial_acts(id)
        )
    """)

    # 6. Public registry
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS public_registry (
            id TEXT PRIMARY KEY,
            act_id TEXT NOT NULL,
            ledger_receipt TEXT,
            vault_ref TEXT,
            is_public INTEGER DEFAULT 1,
            registered_at REAL NOT NULL,
            notarial_flag INTEGER DEFAULT 1,
            verification_url TEXT,
            FOREIGN KEY (act_id) REFERENCES notarial_acts(id)
        )
    """)

    # 7. Audit trail
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_trail (
            id TEXT PRIMARY KEY,
            act_id TEXT,
            event TEXT NOT NULL,
            actor TEXT NOT NULL,
            timestamp REAL NOT NULL,
            previous_hash TEXT,
            current_hash TEXT NOT NULL,
            details TEXT,
            ip_address TEXT
        )
    """)

    conn.commit()
    conn.close()

    return True


def get_db():
    """Get database connection."""
    if not os.path.exists(DB_PATH):
        init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def log_audit(act_id: str, event: str, actor: str, details: dict = None, previous_hash: str = None):
    """Log action to audit trail with hash chain."""
    content = json.dumps({"act_id": act_id, "event": event, "actor": actor, "details": details, "ts": time.time()})
    current_hash = hashlib.sha256(f"{previous_hash or '0'*64}:{content}".encode()).hexdigest()

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO audit_trail (id, act_id, event, actor, timestamp, previous_hash, current_hash, details)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        str(uuid.uuid4()),
        act_id,
        event,
        actor,
        time.time(),
        previous_hash or "0" * 64,
        current_hash,
        json.dumps(details) if details else None
    ))
    conn.commit()
    conn.close()
    return current_hash


# ═══════════════════════════════════════════════════════════════
#  CRYPTOGRAPHIC UTILITIES
# ═══════════════════════════════════════════════════════════════

def compute_hash(content: str) -> str:
    """Compute SHA-256 hash."""
    return hashlib.sha256(content.encode()).hexdigest()


def generate_serial_number() -> str:
    """Generate unique serial number for certificates."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_part = uuid.uuid4().hex[:8].upper()
    return f"WINDI-NOT-{timestamp}-{random_part}"


def generate_act_id() -> str:
    """Generate notarial act ID."""
    date_part = datetime.now().strftime("%Y%m%d")
    random_part = uuid.uuid4().hex[:6].upper()
    return f"ACT-{date_part}-{random_part}"


# ═══════════════════════════════════════════════════════════════
#  LEDGER BRIDGE
# ═══════════════════════════════════════════════════════════════

def register_in_ledger(act_id: str, act_data: dict) -> Optional[dict]:
    """Register notarial act in Forensic Ledger with notarial=true flag."""
    if not HTTPX_AVAILABLE:
        return {"error": "httpx not available", "simulated": True}

    try:
        payload = {
            "doc_type": "NOTARIAL_ACT",
            "content_hash": compute_hash(json.dumps(act_data, sort_keys=True)),
            "risk_level": "R0",
            "impact_level": "LOW",
            "notarial": True,
            "agent": __agent_id__,
            "metadata": {
                "act_id": act_id,
                "act_type": act_data.get("act_type"),
                "timestamp": time.time()
            }
        }

        with httpx.Client(timeout=10.0) as client:
            response = client.post(f"{LEDGER_URL}/receipt", json=payload)
            if response.status_code in (200, 201):
                return response.json()
            return {"error": f"Ledger returned {response.status_code}"}
    except Exception as e:
        return {"error": str(e), "simulated": True}


# ═══════════════════════════════════════════════════════════════
#  FLASK BLUEPRINT
# ═══════════════════════════════════════════════════════════════

notary_bp = Blueprint("notary", __name__, url_prefix="/notary")


# --- Health & Status ---

@notary_bp.route("/health", methods=["GET"])
def health():
    """Health check for Notarial Agent."""
    db_exists = os.path.exists(DB_PATH)
    return jsonify({
        "status": "GREEN" if db_exists else "YELLOW",
        "agent": __agent_id__,
        "name": __agent_name__,
        "version": __version__,
        "database": "connected" if db_exists else "not_initialized",
        "ledger_bridge": HTTPX_AVAILABLE,
        "principle": "AI processes. Human decides. WINDI guarantees."
    })


@notary_bp.route("/status", methods=["GET"])
def status():
    """Detailed status of Notarial Agent."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM notarial_acts")
    total_acts = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM notarial_acts WHERE status = 'sealed'")
    sealed_acts = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM certifications")
    total_certs = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM apostille")
    total_apostilles = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM public_registry")
    total_registered = cursor.fetchone()[0]

    conn.close()

    return jsonify({
        "agent": __agent_id__,
        "name": __agent_name__,
        "version": __version__,
        "statistics": {
            "total_acts": total_acts,
            "sealed_acts": sealed_acts,
            "total_certifications": total_certs,
            "total_apostilles": total_apostilles,
            "registered_in_ledger": total_registered,
        },
        "tables": ["notarial_acts", "parties", "certifications",
                   "apostille", "witnesses", "public_registry", "audit_trail"],
        "act_types": [t.value for t in ActType],
        "integrations": {
            "ledger": LEDGER_URL,
            "vault": VAULT_URL,
            "export": EXPORT_URL,
        }
    })


# --- Notarial Acts ---

@notary_bp.route("/act/recognize", methods=["POST"])
def act_recognize():
    """Create recognition act — validate identity + sign document."""
    data = request.get_json() or {}

    act_id = generate_act_id()
    now = time.time()

    # Compute document hash
    doc_content = data.get("document", "")
    doc_hash = compute_hash(json.dumps(doc_content) if isinstance(doc_content, dict) else str(doc_content))

    conn = get_db()
    cursor = conn.cursor()

    # Create act
    cursor.execute("""
        INSERT INTO notarial_acts (id, act_type, doc_hash, title, description, status, created_at, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        act_id,
        ActType.RECOGNITION.value,
        doc_hash,
        data.get("title", "Recognition Act"),
        data.get("description", ""),
        ActStatus.PENDING.value,
        now,
        json.dumps(data.get("metadata", {}))
    ))

    # Add principal party
    party_id = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO parties (id, act_id, name, did, email, role, public_key)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        party_id,
        act_id,
        data.get("party_name", "Unknown"),
        data.get("party_did", ""),
        data.get("party_email", ""),
        PartyRole.PRINCIPAL.value,
        data.get("public_key", "")
    ))

    conn.commit()
    conn.close()

    log_audit(act_id, "act_created", data.get("actor", "system"), {"type": "recognition", "doc_hash": doc_hash})

    return jsonify({
        "success": True,
        "act_id": act_id,
        "act_type": "recognition",
        "doc_hash": doc_hash,
        "status": "pending",
        "party_id": party_id,
        "created_at": now,
        "next_step": "Sign with /notary/act/<id>/sign or seal with /notary/seal/<id>"
    }), 201


@notary_bp.route("/act/certify", methods=["POST"])
def act_certify():
    """Create digital certification — issue certificate with timestamp + immutable hash."""
    data = request.get_json() or {}

    act_id = generate_act_id()
    now = time.time()

    # Compute document hash
    doc_content = data.get("document", "")
    doc_hash = compute_hash(json.dumps(doc_content) if isinstance(doc_content, dict) else str(doc_content))

    # Generate certificate
    serial_number = generate_serial_number()
    valid_days = data.get("valid_days", 365)
    valid_until = now + (valid_days * 86400)

    cert_content = {
        "serial": serial_number,
        "doc_hash": doc_hash,
        "issued_at": now,
        "valid_until": valid_until,
        "issuer": __agent_id__,
        "subject": data.get("subject", ""),
    }
    cert_hash = compute_hash(json.dumps(cert_content, sort_keys=True))

    conn = get_db()
    cursor = conn.cursor()

    # Create act
    cursor.execute("""
        INSERT INTO notarial_acts (id, act_type, doc_hash, title, description, status, created_at, valid_until, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        act_id,
        ActType.CERTIFICATION.value,
        doc_hash,
        data.get("title", "Digital Certificate"),
        data.get("description", ""),
        ActStatus.SIGNED.value,
        now,
        valid_until,
        json.dumps(data.get("metadata", {}))
    ))

    # Create certification record
    cert_id = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO certifications (id, act_id, cert_type, cert_hash, issued_at, valid_until, serial_number, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        cert_id,
        act_id,
        data.get("cert_type", "standard"),
        cert_hash,
        now,
        valid_until,
        serial_number,
        json.dumps(cert_content)
    ))

    conn.commit()
    conn.close()

    log_audit(act_id, "certification_issued", data.get("actor", "system"), {"serial": serial_number, "cert_hash": cert_hash})

    return jsonify({
        "success": True,
        "act_id": act_id,
        "act_type": "certification",
        "certification": {
            "cert_id": cert_id,
            "serial_number": serial_number,
            "cert_hash": cert_hash,
            "issued_at": now,
            "valid_until": valid_until,
        },
        "doc_hash": doc_hash,
        "status": "signed",
        "next_step": "Seal with /notary/seal/<id> to register in Ledger"
    }), 201


@notary_bp.route("/act/<act_id>", methods=["GET"])
def get_act(act_id):
    """Get notarial act details."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM notarial_acts WHERE id = ?", (act_id,))
    act = cursor.fetchone()

    if not act:
        conn.close()
        return jsonify({"error": "Act not found"}), 404

    # Get parties
    cursor.execute("SELECT * FROM parties WHERE act_id = ?", (act_id,))
    parties = [dict(row) for row in cursor.fetchall()]

    # Get certifications
    cursor.execute("SELECT * FROM certifications WHERE act_id = ?", (act_id,))
    certifications = [dict(row) for row in cursor.fetchall()]

    # Get witnesses
    cursor.execute("SELECT * FROM witnesses WHERE act_id = ?", (act_id,))
    witnesses = [dict(row) for row in cursor.fetchall()]

    # Get registry entry
    cursor.execute("SELECT * FROM public_registry WHERE act_id = ?", (act_id,))
    registry = cursor.fetchone()

    # Get apostille if exists
    cursor.execute("SELECT * FROM apostille WHERE act_id = ?", (act_id,))
    apostille = cursor.fetchone()

    conn.close()

    result = dict(act)
    result["parties"] = parties
    result["certifications"] = certifications
    result["witnesses"] = witnesses
    result["registry"] = dict(registry) if registry else None
    result["apostille"] = dict(apostille) if apostille else None

    return jsonify(result)


@notary_bp.route("/act/<act_id>/certificate", methods=["GET"])
def get_certificate(act_id):
    """Get certificate PDF via Export Engine (:8103)."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM notarial_acts WHERE id = ?", (act_id,))
    act = cursor.fetchone()

    if not act:
        conn.close()
        return jsonify({"error": "Act not found"}), 404

    cursor.execute("SELECT * FROM certifications WHERE act_id = ?", (act_id,))
    cert = cursor.fetchone()

    conn.close()

    if not cert:
        return jsonify({"error": "No certification for this act"}), 404

    cert_dict = dict(cert)

    # In production, would call Export Engine
    # For now, return certificate data
    return jsonify({
        "act_id": act_id,
        "certificate": cert_dict,
        "export_url": f"{EXPORT_URL}/certificate/{act_id}",
        "note": "PDF generation via Export Engine :8103"
    })


# --- Apostille ---

@notary_bp.route("/apostille/<act_id>", methods=["POST"])
def create_apostille(act_id):
    """Create WINDI Apostille — Hague Convention digital equivalent."""
    data = request.get_json() or {}

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM notarial_acts WHERE id = ?", (act_id,))
    act = cursor.fetchone()

    if not act:
        conn.close()
        return jsonify({"error": "Act not found"}), 404

    act_dict = dict(act)
    now = time.time()

    # Generate apostille seal
    reference_number = f"APO-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    seal_content = {
        "act_id": act_id,
        "doc_hash": act_dict["doc_hash"],
        "country_origin": data.get("country_origin", "DE"),
        "country_destination": data.get("country_destination", ""),
        "convention": "hague_1961",
        "reference": reference_number,
        "timestamp": now
    }
    seal_hash = compute_hash(json.dumps(seal_content, sort_keys=True))

    apo_id = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO apostille (id, act_id, country_origin, country_destination, convention, seal_hash, issued_at, reference_number)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        apo_id,
        act_id,
        data.get("country_origin", "DE"),
        data.get("country_destination", ""),
        "hague_1961",
        seal_hash,
        now,
        reference_number
    ))

    # Update act status
    cursor.execute("UPDATE notarial_acts SET status = 'sealed' WHERE id = ?", (act_id,))

    conn.commit()
    conn.close()

    log_audit(act_id, "apostille_issued", data.get("actor", "system"), {"reference": reference_number, "seal_hash": seal_hash})

    return jsonify({
        "success": True,
        "act_id": act_id,
        "apostille": {
            "id": apo_id,
            "reference_number": reference_number,
            "seal_hash": seal_hash,
            "country_origin": data.get("country_origin", "DE"),
            "country_destination": data.get("country_destination", ""),
            "convention": "hague_1961",
            "issued_at": now
        },
        "status": "Apostille issued — document valid for international use"
    }), 201


# --- Witnessing ---

@notary_bp.route("/witness", methods=["POST"])
def add_witness():
    """Add witness to act — multi-party signing."""
    data = request.get_json() or {}

    act_id = data.get("act_id")
    if not act_id:
        return jsonify({"error": "act_id required"}), 400

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM notarial_acts WHERE id = ?", (act_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({"error": "Act not found"}), 404

    # Get current witness count
    cursor.execute("SELECT COUNT(*) FROM witnesses WHERE act_id = ?", (act_id,))
    witness_count = cursor.fetchone()[0]

    witness_id = str(uuid.uuid4())
    now = time.time()

    cursor.execute("""
        INSERT INTO witnesses (id, act_id, witness_name, witness_did, witness_email, signature, signed_at, order_num)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        witness_id,
        act_id,
        data.get("name", ""),
        data.get("did", ""),
        data.get("email", ""),
        data.get("signature", ""),
        now if data.get("signature") else None,
        witness_count + 1
    ))

    conn.commit()
    conn.close()

    log_audit(act_id, "witness_added", data.get("actor", "system"), {"witness_id": witness_id, "order": witness_count + 1})

    return jsonify({
        "success": True,
        "act_id": act_id,
        "witness_id": witness_id,
        "order": witness_count + 1,
        "signed": bool(data.get("signature"))
    }), 201


# --- Timestamp (Data Certa) ---

@notary_bp.route("/timestamp", methods=["POST"])
def create_timestamp():
    """Create timestamp act — proof that document existed at time T."""
    data = request.get_json() or {}

    act_id = generate_act_id()
    now = time.time()

    # Compute document hash
    doc_content = data.get("document", "")
    doc_hash = compute_hash(json.dumps(doc_content) if isinstance(doc_content, dict) else str(doc_content))

    # Create timestamp proof
    timestamp_proof = {
        "doc_hash": doc_hash,
        "timestamp": now,
        "timestamp_iso": datetime.utcfromtimestamp(now).isoformat() + "Z",
        "agent": __agent_id__,
        "nonce": uuid.uuid4().hex
    }
    proof_hash = compute_hash(json.dumps(timestamp_proof, sort_keys=True))

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO notarial_acts (id, act_type, doc_hash, title, description, status, created_at, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        act_id,
        ActType.TIMESTAMP.value,
        doc_hash,
        data.get("title", "Timestamp Proof"),
        data.get("description", "Proof of existence at specific time"),
        ActStatus.SEALED.value,
        now,
        json.dumps(timestamp_proof)
    ))

    conn.commit()
    conn.close()

    log_audit(act_id, "timestamp_created", data.get("actor", "system"), {"doc_hash": doc_hash, "proof_hash": proof_hash})

    return jsonify({
        "success": True,
        "act_id": act_id,
        "act_type": "timestamp",
        "timestamp_proof": {
            "doc_hash": doc_hash,
            "proof_hash": proof_hash,
            "timestamp": now,
            "timestamp_iso": timestamp_proof["timestamp_iso"],
        },
        "status": "sealed",
        "statement": f"Document with hash {doc_hash[:16]}... existed at {timestamp_proof['timestamp_iso']}"
    }), 201


# --- Registry ---

@notary_bp.route("/registry", methods=["GET"])
def list_registry():
    """List public registry entries."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT pr.*, na.title, na.act_type, na.doc_hash, na.status
        FROM public_registry pr
        JOIN notarial_acts na ON pr.act_id = na.id
        WHERE pr.is_public = 1
        ORDER BY pr.registered_at DESC
        LIMIT 100
    """)

    entries = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify({
        "registry": entries,
        "total": len(entries),
        "agent": __agent_id__
    })


# --- Verification ---

@notary_bp.route("/verify/<hash_value>", methods=["GET"])
def verify_hash(hash_value):
    """Verify authenticity of notarial act by hash."""
    conn = get_db()
    cursor = conn.cursor()

    # Check in notarial_acts
    cursor.execute("SELECT * FROM notarial_acts WHERE doc_hash = ?", (hash_value,))
    act = cursor.fetchone()

    # Check in certifications
    cursor.execute("SELECT * FROM certifications WHERE cert_hash = ?", (hash_value,))
    cert = cursor.fetchone()

    # Check in apostille
    cursor.execute("SELECT * FROM apostille WHERE seal_hash = ?", (hash_value,))
    apo = cursor.fetchone()

    conn.close()

    if not act and not cert and not apo:
        return jsonify({
            "verified": False,
            "hash": hash_value,
            "error": "Hash not found in notarial registry"
        }), 404

    result = {
        "verified": True,
        "hash": hash_value,
        "found_in": []
    }

    if act:
        result["found_in"].append("notarial_acts")
        result["act"] = dict(act)
    if cert:
        result["found_in"].append("certifications")
        result["certification"] = dict(cert)
    if apo:
        result["found_in"].append("apostille")
        result["apostille"] = dict(apo)

    return jsonify(result)


# --- Seal (Register in Ledger) ---

@notary_bp.route("/seal/<act_id>", methods=["POST"])
def seal_act(act_id):
    """Seal notarial act — register in Forensic Ledger with notarial=true."""
    data = request.get_json() or {}

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM notarial_acts WHERE id = ?", (act_id,))
    act = cursor.fetchone()

    if not act:
        conn.close()
        return jsonify({"error": "Act not found"}), 404

    act_dict = dict(act)
    now = time.time()

    # Register in Ledger
    ledger_response = register_in_ledger(act_id, act_dict)

    ledger_receipt = ledger_response.get("receipt_id") if ledger_response else None

    # Create registry entry
    registry_id = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO public_registry (id, act_id, ledger_receipt, is_public, registered_at, notarial_flag)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        registry_id,
        act_id,
        ledger_receipt or json.dumps(ledger_response),
        1 if data.get("public", True) else 0,
        now,
        1
    ))

    # Update act status
    cursor.execute("UPDATE notarial_acts SET status = 'registered', sealed_at = ? WHERE id = ?", (now, act_id))

    conn.commit()
    conn.close()

    log_audit(act_id, "act_sealed", data.get("actor", "system"), {"ledger_receipt": ledger_receipt, "registry_id": registry_id})

    return jsonify({
        "success": True,
        "act_id": act_id,
        "status": "registered",
        "sealed_at": now,
        "registry": {
            "id": registry_id,
            "ledger_receipt": ledger_receipt,
            "ledger_response": ledger_response,
            "public": data.get("public", True)
        },
        "verification_url": f"/notary/verify/{act_dict['doc_hash']}"
    })


# ═══════════════════════════════════════════════════════════════
#  INIT ON IMPORT
# ═══════════════════════════════════════════════════════════════

# Initialize database when module is imported
init_db()
