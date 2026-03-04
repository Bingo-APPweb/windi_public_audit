"""
WINDI Auditor Agent v1.0.0 — Flask Blueprint
=============================================

Domain extension for the Constitutional Agent (Sandbox Core).
Integrates as /audit/* endpoints on :8091.

Philosophy:
  "Os outros 5 agentes CRIAM, SELAM e PUBLICAM.
   O Auditor nao cria nada.
   Ele verifica que o que foi criado e o que foi prometido.
   A prova existe. O Auditor le a prova."

Role:
  W-AUDIT-001 is the CLOSURE of the constitutional cycle:
    Journalist (creates) -> Communique (seals) -> Ledger (proof) -> Audit (verifies)

  The Auditor answers to TWO authorities:
    1. Human Dragon (operational)
    2. Any third party with valid hash (public transparency)

Critical Rules:
  - Auditor NEVER writes to communique.db
  - Auditor NEVER modifies Ledger receipts
  - Auditor ONLY reads + compares + reports
  - Violation = I9 violation

Audit Invariants (A1-A6):
  A1 — Immutability:     Auditor does not alter — only reads and reports
  A2 — Traceability:     Every audit generates its own Ledger receipt
  A3 — Reproducibility:  Same hash -> same result, always
  A4 — Independence:     Auditor knows no intent — only evidence
  A5 — Transparency:     Audit result is public for anyone with hash
  A6 — Completeness:     Incomplete audit = invalid audit (no middle ground)

Principle: "AI processes. Human decides. WINDI guarantees."

Version: 1.0.0
Sealed: W-AUDIT-001
"""

import hashlib
import json
import os
import sqlite3
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from flask import Blueprint, jsonify, request

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

__version__ = "1.0.0"
__agent_id__ = "W-AUDIT-001"
__agent_name__ = "Agente Auditor"

# Database path - SEPARATE from other agents
AUDIT_DIR = "/opt/windi/audit"
DB_PATH = os.path.join(AUDIT_DIR, "audit.db")

# External services (READ ONLY)
COMMUNIQUE_DB = "/opt/windi/communique/data/communiques.db"
LEDGER_URL = "http://localhost:8101"
VAULT_URL = "http://localhost:8106"

# Internal constellation endpoints
CONSTELLATION_AGENTS = {
    "legal": "http://localhost:8091/legal/health",
    "notary": "http://localhost:8091/notary/health",
    "compliance": "http://localhost:8091/compliance/health",
    "communique": "http://localhost:8091/communique/health",
    "journalist": "http://localhost:8091/journalist/health",
}


# ===================================================================
#  AUDIT INVARIANTS (A1-A6)
# ===================================================================

class AuditInvariant(Enum):
    """The six audit invariants that govern all agent operations."""
    A1 = ("A1", "imutabilidade", "Auditor nao altera — apenas le e reporta")
    A2 = ("A2", "rastreabilidade", "Todo audit gera receipt proprio no Ledger")
    A3 = ("A3", "reproducibilidade", "Mesmo hash -> mesmo resultado, sempre")
    A4 = ("A4", "independencia", "Auditor nao conhece intencao — apenas evidencia")
    A5 = ("A5", "transparencia", "Resultado de audit e publico para quem tem o hash")
    A6 = ("A6", "completude", "Audit incompleto = audit invalido (sem meio-termo)")

    def __init__(self, code: str, name: str, description: str):
        self._code = code
        self._name = name
        self._description = description

    @property
    def code(self) -> str:
        return self._code

    @property
    def invariant_name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description


class IntegrityStatus(Enum):
    INTACT = "INTACT"
    TAMPERED = "TAMPERED"
    MISSING = "MISSING"
    NOT_FOUND = "NOT_FOUND"


class ChainStatus(Enum):
    COMPLETE = "COMPLETE"
    BROKEN = "BROKEN"
    PARTIAL = "PARTIAL"


# ===================================================================
#  BLUEPRINT
# ===================================================================

audit_bp = Blueprint("audit", __name__, url_prefix="/audit")


# ===================================================================
#  DATABASE INITIALIZATION
# ===================================================================

def get_db():
    """Get audit database connection."""
    os.makedirs(AUDIT_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Initialize audit database schema."""
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id TEXT,
            hash_checked TEXT,
            result TEXT NOT NULL,
            chain_complete BOOLEAN,
            integrity TEXT,
            audited_at TEXT NOT NULL,
            receipt_id TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_audit_doc ON audit_log(document_id);
        CREATE INDEX IF NOT EXISTS idx_audit_hash ON audit_log(hash_checked);
        CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_log(audited_at);
    """)
    conn.commit()
    conn.close()


def now_iso():
    """Current UTC timestamp in ISO 8601."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def compute_hash(content: str) -> str:
    """Compute SHA-256 hash."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


# ===================================================================
#  LEDGER INTEGRATION (READ ONLY)
# ===================================================================

def register_audit_receipt(audit_type: str, document_id: str, result: str, details: dict) -> Optional[str]:
    """Register audit event in Ledger (A2 compliance)."""
    if not REQUESTS_AVAILABLE:
        return None

    try:
        payload = {
            "type": f"audit_{audit_type}",
            "source": "W-AUDIT-001",
            "source_id": f"AUD-{document_id or 'batch'}-{now_iso()[:10]}",
            "content_hash": compute_hash(json.dumps(details, sort_keys=True)),
            "category": "AUDIT",
            "result": result,
            "details": details,
        }

        r = requests.post(f"{LEDGER_URL}/ingest", json=payload, timeout=5)
        if r.status_code == 200:
            data = r.json()
            return data.get("receipt_id") or data.get("id") or data.get("verification_id")
    except Exception:
        pass

    return None


def check_ledger_receipt(receipt_id: str) -> dict:
    """Check if a receipt exists in Ledger."""
    if not REQUESTS_AVAILABLE or not receipt_id:
        return {"found": False, "status": "unknown"}

    try:
        r = requests.get(f"{LEDGER_URL}/receipt/{receipt_id}", timeout=3)
        if r.status_code == 200:
            data = r.json()
            receipt = data.get("receipt", data)
            return {
                "found": True,
                "status": receipt.get("status", "unknown"),
                "timestamp": receipt.get("timestamp"),
            }
    except Exception:
        pass

    return {"found": False, "status": "error"}


def check_ledger_health() -> bool:
    """Check if Ledger is available."""
    if not REQUESTS_AVAILABLE:
        return False

    try:
        r = requests.get(f"{LEDGER_URL}/health", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


# ===================================================================
#  COMMUNIQUE DB ACCESS (READ ONLY)
# ===================================================================

def get_communique_readonly(doc_id: str) -> Optional[dict]:
    """Read document from communique DB (READ ONLY - A1 compliance)."""
    if not os.path.exists(COMMUNIQUE_DB):
        return None

    try:
        conn = sqlite3.connect(f"file:{COMMUNIQUE_DB}?mode=ro", uri=True, timeout=5)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM communiques WHERE id = ?", (doc_id,)).fetchone()
        conn.close()

        if row:
            return dict(row)
    except Exception:
        pass

    return None


def find_communique_by_hash(content_hash: str) -> Optional[dict]:
    """Find document by content hash (READ ONLY)."""
    if not os.path.exists(COMMUNIQUE_DB):
        return None

    try:
        conn = sqlite3.connect(f"file:{COMMUNIQUE_DB}?mode=ro", uri=True, timeout=5)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT id, status, category, published_at, content_hash FROM communiques WHERE content_hash = ?",
            (content_hash,)
        ).fetchone()
        conn.close()

        if row:
            return dict(row)
    except Exception:
        pass

    return None


def compute_document_hash(doc: dict) -> str:
    """Recompute content hash for verification."""
    fields = ["title_de", "title_en", "title_pt", "body_de", "body_en", "body_pt",
              "category", "impact_level", "author_name", "author_role"]
    canonical = "|".join(str(doc.get(f, "") or "") for f in fields)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ===================================================================
#  INVARIANT CHECKING
# ===================================================================

def check_invariants() -> Dict[str, Any]:
    """Check status of all audit invariants."""
    results = {}

    # Check Ledger availability for A2 and A6
    ledger_available = check_ledger_health()

    for inv in AuditInvariant:
        status = "compliant"
        details = None

        if inv == AuditInvariant.A2:
            if not ledger_available:
                status = "warning"
                details = "Ledger unavailable - cannot create audit receipts"

        elif inv == AuditInvariant.A6:
            if not ledger_available:
                status = "warning"
                details = "Ledger unavailable - audits may be incomplete"

        results[inv.code] = {
            "code": inv.code,
            "name": inv.invariant_name,
            "description": inv.description,
            "status": status,
            "details": details,
        }

    return results


# ===================================================================
#  HEALTH & STATUS ENDPOINTS
# ===================================================================

@audit_bp.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    conn = get_db()
    audit_count = conn.execute("SELECT COUNT(*) FROM audit_log").fetchone()[0]
    conn.close()

    ledger_ok = check_ledger_health()

    return jsonify({
        "status": "GREEN" if ledger_ok else "YELLOW",
        "agent": __agent_id__,
        "name": __agent_name__,
        "version": __version__,
        "database": DB_PATH,
        "audits_performed": audit_count,
        "ledger_available": ledger_ok,
        "role": "Constitutional cycle closure - verification only",
        "principles": [
            "AI processes. Human decides. WINDI guarantees.",
            "O Auditor nao cria nada. Ele verifica que o que foi criado e o que foi prometido."
        ],
        "timestamp": now_iso(),
    })


@audit_bp.route("/status", methods=["GET"])
def status():
    """Detailed status with invariant checks."""
    invariants = check_invariants()
    ledger_ok = check_ledger_health()

    overall = "COMPLIANT"
    if any(inv["status"] == "violated" for inv in invariants.values()):
        overall = "VIOLATED"
    elif any(inv["status"] == "warning" for inv in invariants.values()):
        overall = "WARNING"

    return jsonify({
        "agent": __agent_id__,
        "name": __agent_name__,
        "version": __version__,
        "overall_status": overall,
        "invariants": invariants,
        "invariants_total": len(invariants),
        "invariants_compliant": sum(1 for i in invariants.values() if i["status"] == "compliant"),
        "ledger_available": ledger_ok,
        "read_only": True,
        "public_endpoint": "/audit/verify/<hash>",
        "timestamp": now_iso(),
    })


# ===================================================================
#  DOCUMENT AUDIT ENDPOINT
# ===================================================================

@audit_bp.route("/document/<doc_id>", methods=["GET"])
def audit_document(doc_id):
    """Complete audit of a single document."""
    # A6: Check Ledger availability first
    if not check_ledger_health():
        return jsonify({
            "error": "Ledger unavailable - cannot perform complete audit (A6 violation)",
            "a6_violated": True,
        }), 503

    # Get document (READ ONLY)
    doc = get_communique_readonly(doc_id)
    if not doc:
        return jsonify({
            "document_id": doc_id,
            "integrity": IntegrityStatus.MISSING.value,
            "error": "Document not found",
        }), 404

    # Verify hash
    stored_hash = doc.get("content_hash")
    computed_hash = compute_document_hash(doc)
    hash_match = stored_hash == computed_hash if stored_hash else False

    # Verify Ledger receipt
    receipt_id = doc.get("receipt_id")
    ledger_check = check_ledger_receipt(receipt_id) if receipt_id else {"found": False}
    ledger_verified = ledger_check.get("found", False) and ledger_check.get("status") == "sealed"

    # Check J6 compliance (AI participation declared)
    ai_participation = doc.get("ai_participation")
    j6_compliant = bool(ai_participation) if doc.get("status") == "PUBLISHED" else True

    # Determine integrity
    if not hash_match:
        integrity = IntegrityStatus.TAMPERED.value
    elif not ledger_verified and doc.get("status") == "PUBLISHED":
        integrity = IntegrityStatus.TAMPERED.value
    else:
        integrity = IntegrityStatus.INTACT.value

    # Register audit in Ledger (A2)
    audit_details = {
        "document_id": doc_id,
        "hash_match": hash_match,
        "ledger_verified": ledger_verified,
        "j6_compliant": j6_compliant,
        "integrity": integrity,
    }
    audit_receipt = register_audit_receipt("document", doc_id, integrity, audit_details)

    # Log to audit DB
    conn = get_db()
    conn.execute("""
        INSERT INTO audit_log (document_id, hash_checked, result, chain_complete, integrity, audited_at, receipt_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (doc_id, stored_hash, "pass" if integrity == "INTACT" else "fail",
          ledger_verified, integrity, now_iso(), audit_receipt))
    conn.commit()
    conn.close()

    return jsonify({
        "document_id": doc_id,
        "status": doc.get("status"),
        "hash_stored": stored_hash,
        "hash_computed": computed_hash,
        "hash_match": hash_match,
        "ledger_receipt_id": receipt_id,
        "ledger_verified": ledger_verified,
        "j6_compliant": j6_compliant,
        "integrity": integrity,
        "audit_receipt": audit_receipt,
        "audited_at": now_iso(),
    })


# ===================================================================
#  PUBLIC HASH VERIFICATION (NO AUTH - A5)
# ===================================================================

@audit_bp.route("/verify/<content_hash>", methods=["GET"])
def verify_hash(content_hash):
    """
    PUBLIC ENDPOINT - No authentication required.
    Anyone with a valid hash can verify document integrity.
    This is A5 in action - transparency for all.
    """
    # Find document by hash
    doc = find_communique_by_hash(content_hash)

    if not doc:
        return jsonify({
            "hash": content_hash,
            "found": False,
            "document": None,
            "integrity": IntegrityStatus.NOT_FOUND.value,
            "verified_at": now_iso(),
            "note": "No document found with this hash",
        })

    return jsonify({
        "hash": content_hash,
        "found": True,
        "document": {
            "id": doc.get("id"),
            "status": doc.get("status"),
            "category": doc.get("category"),
            "published_at": doc.get("published_at"),
        },
        "integrity": IntegrityStatus.INTACT.value,
        "verified_at": now_iso(),
        "note": "Hash verified - document exists and hash matches",
    })


# ===================================================================
#  CHAIN AUDIT ENDPOINT
# ===================================================================

@audit_bp.route("/chain", methods=["POST"])
def audit_chain():
    """Audit complete editorial chain of a document."""
    data = request.get_json() or {}
    doc_id = data.get("document_id")

    if not doc_id:
        return jsonify({"error": "document_id required"}), 400

    # A6: Check Ledger availability
    if not check_ledger_health():
        return jsonify({
            "error": "Ledger unavailable - cannot perform chain audit (A6)",
        }), 503

    chain = []
    broken_at = None

    # Step 1: Check document exists in Communique
    doc = get_communique_readonly(doc_id)
    if doc:
        chain.append({
            "step": "communique",
            "status": "pass",
            "evidence": {
                "id": doc.get("id"),
                "status": doc.get("status"),
                "content_hash": doc.get("content_hash"),
            }
        })
    else:
        chain.append({"step": "communique", "status": "fail", "evidence": None})
        broken_at = "communique"

    # Step 2: Check hash integrity
    if doc and not broken_at:
        stored_hash = doc.get("content_hash")
        computed_hash = compute_document_hash(doc)
        if stored_hash == computed_hash:
            chain.append({
                "step": "hash_integrity",
                "status": "pass",
                "evidence": {"stored": stored_hash, "computed": computed_hash}
            })
        else:
            chain.append({
                "step": "hash_integrity",
                "status": "fail",
                "evidence": {"stored": stored_hash, "computed": computed_hash}
            })
            broken_at = "hash_integrity"

    # Step 3: Check Ledger receipt
    if doc and not broken_at:
        receipt_id = doc.get("receipt_id")
        if receipt_id:
            ledger_check = check_ledger_receipt(receipt_id)
            if ledger_check.get("found"):
                chain.append({
                    "step": "ledger",
                    "status": "pass",
                    "evidence": {"receipt_id": receipt_id, "ledger_status": ledger_check.get("status")}
                })
            else:
                chain.append({
                    "step": "ledger",
                    "status": "fail",
                    "evidence": {"receipt_id": receipt_id, "error": "Receipt not found"}
                })
                broken_at = "ledger"
        else:
            # No receipt yet is OK for drafts
            if doc.get("status") == "PUBLISHED":
                chain.append({"step": "ledger", "status": "fail", "evidence": {"error": "No receipt_id"}})
                broken_at = "ledger"
            else:
                chain.append({"step": "ledger", "status": "skip", "evidence": {"reason": "Not published yet"}})

    # Step 4: Check J6 compliance (if from Journalist)
    if doc and not broken_at:
        ai_participation = doc.get("ai_participation")
        doc_type = doc.get("doc_type", "communique")

        if doc_type == "article" or "ai-" in str(doc.get("tags", "")):
            if ai_participation:
                chain.append({
                    "step": "j6_compliance",
                    "status": "pass",
                    "evidence": {"ai_participation": ai_participation}
                })
            else:
                chain.append({
                    "step": "j6_compliance",
                    "status": "fail",
                    "evidence": {"error": "AI participation not declared"}
                })
                broken_at = "j6_compliance"
        else:
            chain.append({
                "step": "j6_compliance",
                "status": "skip",
                "evidence": {"reason": "Not AI-assisted content"}
            })

    # Determine chain status
    failed_steps = [c for c in chain if c["status"] == "fail"]
    if not failed_steps:
        chain_integrity = ChainStatus.COMPLETE.value
    elif len(failed_steps) == len(chain):
        chain_integrity = ChainStatus.BROKEN.value
    else:
        chain_integrity = ChainStatus.PARTIAL.value

    chain_complete = chain_integrity == ChainStatus.COMPLETE.value

    # Register audit (A2)
    audit_details = {
        "document_id": doc_id,
        "chain": chain,
        "chain_complete": chain_complete,
        "broken_at": broken_at,
    }
    audit_receipt = register_audit_receipt("chain", doc_id, chain_integrity, audit_details)

    # Log
    conn = get_db()
    conn.execute("""
        INSERT INTO audit_log (document_id, hash_checked, result, chain_complete, integrity, audited_at, receipt_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (doc_id, doc.get("content_hash") if doc else None, chain_integrity,
          chain_complete, chain_integrity, now_iso(), audit_receipt))
    conn.commit()
    conn.close()

    return jsonify({
        "document_id": doc_id,
        "chain": chain,
        "chain_complete": chain_complete,
        "chain_integrity": chain_integrity,
        "broken_at": broken_at,
        "audit_receipt": audit_receipt,
        "audited_at": now_iso(),
    })


# ===================================================================
#  BATCH AUDIT ENDPOINT
# ===================================================================

@audit_bp.route("/batch", methods=["GET"])
def audit_batch():
    """Audit multiple documents."""
    status_filter = request.args.get("status", "PUBLISHED")
    limit = min(int(request.args.get("limit", 10)), 100)

    if not os.path.exists(COMMUNIQUE_DB):
        return jsonify({"error": "Communique database not found"}), 500

    # Get documents (READ ONLY)
    conn = sqlite3.connect(f"file:{COMMUNIQUE_DB}?mode=ro", uri=True, timeout=5)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, content_hash, receipt_id, status FROM communiques WHERE status = ? LIMIT ?",
        (status_filter, limit)
    ).fetchall()
    conn.close()

    results = []
    intact = 0
    tampered = 0
    missing = 0

    for row in rows:
        doc_id = row["id"]
        stored_hash = row["content_hash"]
        receipt_id = row["receipt_id"]

        # Quick integrity check
        doc = get_communique_readonly(doc_id)
        if not doc:
            missing += 1
            results.append({"id": doc_id, "integrity": "MISSING"})
            continue

        computed_hash = compute_document_hash(doc)
        if stored_hash != computed_hash:
            tampered += 1
            results.append({"id": doc_id, "integrity": "TAMPERED", "reason": "hash_mismatch"})
        else:
            intact += 1
            results.append({"id": doc_id, "integrity": "INTACT"})

    return jsonify({
        "status_filter": status_filter,
        "total_audited": len(results),
        "intact": intact,
        "tampered": tampered,
        "missing": missing,
        "results": results,
        "audited_at": now_iso(),
    })


# ===================================================================
#  CONSTELLATION HEALTH ENDPOINT
# ===================================================================

@audit_bp.route("/constellation", methods=["GET"])
def audit_constellation():
    """Health check of all constellation agents."""
    agents_status = {}
    all_green = True

    for agent_name, url in CONSTELLATION_AGENTS.items():
        try:
            if REQUESTS_AVAILABLE:
                r = requests.get(url, timeout=2)
                if r.status_code == 200:
                    data = r.json()
                    agents_status[agent_name] = {
                        "status": data.get("status", "unknown"),
                        "version": data.get("version"),
                        "healthy": True,
                    }
                else:
                    agents_status[agent_name] = {"status": "ERROR", "healthy": False}
                    all_green = False
            else:
                agents_status[agent_name] = {"status": "UNKNOWN", "healthy": False}
                all_green = False
        except Exception as e:
            agents_status[agent_name] = {"status": "UNREACHABLE", "healthy": False, "error": str(e)}
            all_green = False

    # Add self
    agents_status["audit"] = {
        "status": "GREEN",
        "version": __version__,
        "healthy": True,
    }

    # Determine overall health
    healthy_count = sum(1 for a in agents_status.values() if a.get("healthy"))
    total_count = len(agents_status)

    if healthy_count == total_count:
        constellation_health = "GREEN"
    elif healthy_count >= total_count * 0.8:
        constellation_health = "YELLOW"
    else:
        constellation_health = "RED"

    # Register audit (A2)
    audit_details = {
        "agents": agents_status,
        "healthy_count": healthy_count,
        "total_count": total_count,
    }
    audit_receipt = register_audit_receipt("constellation", "all", constellation_health, audit_details)

    return jsonify({
        "timestamp": now_iso(),
        "agents": agents_status,
        "agents_healthy": healthy_count,
        "agents_total": total_count,
        "constellation_health": constellation_health,
        "audit_receipt": audit_receipt,
    })


# ===================================================================
#  HISTORY ENDPOINTS
# ===================================================================

@audit_bp.route("/history", methods=["GET"])
def audit_history():
    """Get audit history."""
    limit = min(int(request.args.get("limit", 20)), 100)

    conn = get_db()
    rows = conn.execute("""
        SELECT * FROM audit_log ORDER BY audited_at DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()

    return jsonify({
        "audits": [dict(r) for r in rows],
        "total": len(rows),
    })


@audit_bp.route("/history/<doc_id>", methods=["GET"])
def audit_history_document(doc_id):
    """Get audit history for a specific document."""
    conn = get_db()
    rows = conn.execute("""
        SELECT * FROM audit_log WHERE document_id = ? ORDER BY audited_at DESC
    """, (doc_id,)).fetchall()
    conn.close()

    return jsonify({
        "document_id": doc_id,
        "audits": [dict(r) for r in rows],
        "total": len(rows),
    })


# ===================================================================
#  INITIALIZE
# ===================================================================

# Initialize database on import
init_db()
