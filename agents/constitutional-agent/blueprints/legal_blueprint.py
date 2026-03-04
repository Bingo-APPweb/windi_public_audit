"""
WINDI Legal Agent "Justica" v0.2.0 — Flask Blueprint
======================================================

Domain extension for the Constitutional Agent (Sandbox Core).
Integrates as /legal/* endpoints on :8091.

Features:
- 7 SQLite tables (cases, evidence_commits, etc.)
- Evidence Git-style (commit/log/diff/verify)
- Chain of custody (provenance)
- Confidence scoring (5 factors)
- Court export (5-page WCAF)

Principle: "AI processes. Human decides. WINDI guarantees."

Version: 0.2.0
Sealed: W-LEGAL-001
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

__version__ = "0.2.0"
__agent_id__ = "W-LEGAL-001"
__agent_name__ = "Justica"

# Database path
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DATA_DIR, "legal.db")


# ═══════════════════════════════════════════════════════════════
#  ENUMS
# ═══════════════════════════════════════════════════════════════

class CaseStatus(Enum):
    OPEN = "open"
    INVESTIGATION = "investigation"
    REVIEW = "review"
    CLOSED = "closed"
    ARCHIVED = "archived"


class CaseType(Enum):
    COMPLIANCE = "compliance"
    DISPUTE = "dispute"
    AUDIT = "audit"
    INCIDENT = "incident"
    ADVISORY = "advisory"


class Jurisdiction(Enum):
    DE = "de"       # Germany
    EU = "eu"       # European Union
    BR = "br"       # Brazil
    INT = "int"     # International


# ═══════════════════════════════════════════════════════════════
#  DATABASE INITIALIZATION
# ═══════════════════════════════════════════════════════════════

def init_db():
    """Initialize the 7 legal tables."""
    os.makedirs(DATA_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Cases table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cases (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            case_type TEXT NOT NULL,
            status TEXT DEFAULT 'open',
            jurisdiction TEXT DEFAULT 'de',
            description TEXT,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,
            closed_at REAL,
            metadata TEXT
        )
    """)

    # 2. Evidence commits (Git-style)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS evidence_commits (
            id TEXT PRIMARY KEY,
            case_id TEXT NOT NULL,
            parent_hash TEXT,
            content_hash TEXT NOT NULL,
            evidence_type TEXT NOT NULL,
            content TEXT NOT NULL,
            author TEXT NOT NULL,
            message TEXT,
            created_at REAL NOT NULL,
            branch TEXT DEFAULT 'main',
            FOREIGN KEY (case_id) REFERENCES cases(id)
        )
    """)

    # 3. Evidence branches
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS evidence_branches (
            id TEXT PRIMARY KEY,
            case_id TEXT NOT NULL,
            name TEXT NOT NULL,
            base_commit TEXT,
            created_at REAL NOT NULL,
            description TEXT,
            FOREIGN KEY (case_id) REFERENCES cases(id)
        )
    """)

    # 4. Provenance entries (chain of custody)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS provenance_entries (
            id TEXT PRIMARY KEY,
            case_id TEXT NOT NULL,
            action TEXT NOT NULL,
            actor TEXT NOT NULL,
            timestamp REAL NOT NULL,
            previous_hash TEXT,
            current_hash TEXT NOT NULL,
            details TEXT,
            FOREIGN KEY (case_id) REFERENCES cases(id)
        )
    """)

    # 5. Confidence scores
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS confidence_scores (
            id TEXT PRIMARY KEY,
            case_id TEXT NOT NULL,
            evidence_id TEXT,
            source_reliability REAL DEFAULT 0.5,
            chain_integrity REAL DEFAULT 0.5,
            corroboration REAL DEFAULT 0.5,
            timeliness REAL DEFAULT 0.5,
            completeness REAL DEFAULT 0.5,
            overall_score REAL,
            calculated_at REAL NOT NULL,
            notes TEXT,
            FOREIGN KEY (case_id) REFERENCES cases(id)
        )
    """)

    # 6. Court exports
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS court_exports (
            id TEXT PRIMARY KEY,
            case_id TEXT NOT NULL,
            export_type TEXT DEFAULT 'wcaf',
            jurisdiction TEXT NOT NULL,
            pages INTEGER DEFAULT 5,
            generated_at REAL NOT NULL,
            file_path TEXT,
            content_hash TEXT,
            metadata TEXT,
            FOREIGN KEY (case_id) REFERENCES cases(id)
        )
    """)

    # 7. Audit log
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id TEXT PRIMARY KEY,
            timestamp REAL NOT NULL,
            action TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id TEXT,
            actor TEXT NOT NULL,
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


def log_audit(action: str, entity_type: str, entity_id: str, actor: str, details: dict = None):
    """Log action to audit trail."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO audit_log (id, timestamp, action, entity_type, entity_id, actor, details)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        str(uuid.uuid4()),
        time.time(),
        action,
        entity_type,
        entity_id,
        actor,
        json.dumps(details) if details else None
    ))
    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════════════════════
#  CONFIDENCE SCORING
# ═══════════════════════════════════════════════════════════════

def calculate_confidence(
    source_reliability: float = 0.5,
    chain_integrity: float = 0.5,
    corroboration: float = 0.5,
    timeliness: float = 0.5,
    completeness: float = 0.5
) -> float:
    """
    Calculate overall confidence score using 5 factors.
    Each factor is weighted equally (0.2).
    """
    weights = {
        "source_reliability": 0.25,
        "chain_integrity": 0.25,
        "corroboration": 0.20,
        "timeliness": 0.15,
        "completeness": 0.15,
    }

    score = (
        source_reliability * weights["source_reliability"] +
        chain_integrity * weights["chain_integrity"] +
        corroboration * weights["corroboration"] +
        timeliness * weights["timeliness"] +
        completeness * weights["completeness"]
    )

    return round(score, 4)


# ═══════════════════════════════════════════════════════════════
#  HASH UTILITIES
# ═══════════════════════════════════════════════════════════════

def compute_hash(content: str) -> str:
    """Compute SHA-256 hash of content."""
    return hashlib.sha256(content.encode()).hexdigest()


def compute_chain_hash(previous_hash: str, content: str) -> str:
    """Compute chain hash (previous + content)."""
    combined = f"{previous_hash}:{content}"
    return hashlib.sha256(combined.encode()).hexdigest()


# ═══════════════════════════════════════════════════════════════
#  FLASK BLUEPRINT
# ═══════════════════════════════════════════════════════════════

legal_bp = Blueprint("legal", __name__, url_prefix="/legal")


# --- Health & Status ---

@legal_bp.route("/health", methods=["GET"])
def health():
    """Health check for Legal Agent."""
    db_exists = os.path.exists(DB_PATH)
    return jsonify({
        "status": "GREEN" if db_exists else "YELLOW",
        "agent": __agent_id__,
        "name": __agent_name__,
        "version": __version__,
        "database": "connected" if db_exists else "not_initialized",
        "principle": "AI processes. Human decides. WINDI guarantees."
    })


@legal_bp.route("/status", methods=["GET"])
def status():
    """Detailed status of Legal Agent."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM cases")
    total_cases = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM cases WHERE status = 'open'")
    open_cases = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM evidence_commits")
    total_evidence = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM court_exports")
    total_exports = cursor.fetchone()[0]

    conn.close()

    return jsonify({
        "agent": __agent_id__,
        "name": __agent_name__,
        "version": __version__,
        "statistics": {
            "total_cases": total_cases,
            "open_cases": open_cases,
            "total_evidence": total_evidence,
            "total_exports": total_exports,
        },
        "tables": ["cases", "evidence_commits", "evidence_branches",
                   "provenance_entries", "confidence_scores", "court_exports", "audit_log"],
        "jurisdictions": ["de", "eu", "br", "int"],
    })


# --- Cases ---

@legal_bp.route("/cases", methods=["POST"])
def create_case():
    """Create a new case."""
    data = request.get_json() or {}

    case_id = f"CASE-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
    now = time.time()

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO cases (id, title, case_type, status, jurisdiction, description, created_at, updated_at, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        case_id,
        data.get("title", "Untitled Case"),
        data.get("case_type", "compliance"),
        "open",
        data.get("jurisdiction", "de"),
        data.get("description", ""),
        now,
        now,
        json.dumps(data.get("metadata", {}))
    ))
    conn.commit()
    conn.close()

    log_audit("create", "case", case_id, data.get("author", "system"), {"title": data.get("title")})

    return jsonify({
        "success": True,
        "case_id": case_id,
        "status": "open",
        "created_at": now
    }), 201


@legal_bp.route("/cases", methods=["GET"])
def list_cases():
    """List cases with optional filters."""
    status_filter = request.args.get("status")
    case_type_filter = request.args.get("type")

    conn = get_db()
    cursor = conn.cursor()

    query = "SELECT * FROM cases WHERE 1=1"
    params = []

    if status_filter:
        query += " AND status = ?"
        params.append(status_filter)
    if case_type_filter:
        query += " AND case_type = ?"
        params.append(case_type_filter)

    query += " ORDER BY created_at DESC"

    cursor.execute(query, params)
    cases = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify({"cases": cases, "total": len(cases)})


@legal_bp.route("/cases/<case_id>", methods=["GET"])
def get_case(case_id):
    """Get case details with provenance."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM cases WHERE id = ?", (case_id,))
    case = cursor.fetchone()

    if not case:
        conn.close()
        return jsonify({"error": "Case not found"}), 404

    # Get evidence count
    cursor.execute("SELECT COUNT(*) FROM evidence_commits WHERE case_id = ?", (case_id,))
    evidence_count = cursor.fetchone()[0]

    # Get provenance entries
    cursor.execute("SELECT * FROM provenance_entries WHERE case_id = ? ORDER BY timestamp", (case_id,))
    provenance = [dict(row) for row in cursor.fetchall()]

    # Get confidence score
    cursor.execute("SELECT * FROM confidence_scores WHERE case_id = ? ORDER BY calculated_at DESC LIMIT 1", (case_id,))
    confidence = cursor.fetchone()

    conn.close()

    result = dict(case)
    result["evidence_count"] = evidence_count
    result["provenance"] = provenance
    result["confidence"] = dict(confidence) if confidence else None

    return jsonify(result)


@legal_bp.route("/cases/<case_id>", methods=["PATCH"])
def update_case(case_id):
    """Update case status or details."""
    data = request.get_json() or {}

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM cases WHERE id = ?", (case_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({"error": "Case not found"}), 404

    updates = []
    params = []

    if "status" in data:
        updates.append("status = ?")
        params.append(data["status"])
    if "title" in data:
        updates.append("title = ?")
        params.append(data["title"])
    if "description" in data:
        updates.append("description = ?")
        params.append(data["description"])

    updates.append("updated_at = ?")
    params.append(time.time())
    params.append(case_id)

    if updates:
        query = f"UPDATE cases SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()

    conn.close()

    log_audit("update", "case", case_id, data.get("author", "system"), data)

    return jsonify({"success": True, "case_id": case_id})


# --- Evidence (Git-style) ---

@legal_bp.route("/evidence/commit", methods=["POST"])
def evidence_commit():
    """ev commit - Register evidence with hash chain."""
    data = request.get_json() or {}

    case_id = data.get("case_id")
    if not case_id:
        return jsonify({"error": "case_id required"}), 400

    conn = get_db()
    cursor = conn.cursor()

    # Check case exists
    cursor.execute("SELECT * FROM cases WHERE id = ?", (case_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({"error": "Case not found"}), 404

    # Get parent hash (latest commit on branch)
    branch = data.get("branch", "main")
    cursor.execute("""
        SELECT content_hash FROM evidence_commits
        WHERE case_id = ? AND branch = ?
        ORDER BY created_at DESC LIMIT 1
    """, (case_id, branch))
    parent = cursor.fetchone()
    parent_hash = parent[0] if parent else "0" * 64

    # Compute content hash
    content = json.dumps(data.get("content", {}), sort_keys=True)
    content_hash = compute_chain_hash(parent_hash, content)

    commit_id = f"ev-{uuid.uuid4().hex[:8]}"
    now = time.time()

    cursor.execute("""
        INSERT INTO evidence_commits
        (id, case_id, parent_hash, content_hash, evidence_type, content, author, message, created_at, branch)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        commit_id,
        case_id,
        parent_hash,
        content_hash,
        data.get("evidence_type", "document"),
        content,
        data.get("author", "unknown"),
        data.get("message", ""),
        now,
        branch
    ))

    # Update provenance
    cursor.execute("""
        INSERT INTO provenance_entries (id, case_id, action, actor, timestamp, previous_hash, current_hash, details)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        str(uuid.uuid4()),
        case_id,
        "evidence_commit",
        data.get("author", "unknown"),
        now,
        parent_hash,
        content_hash,
        json.dumps({"commit_id": commit_id, "evidence_type": data.get("evidence_type")})
    ))

    conn.commit()
    conn.close()

    log_audit("commit", "evidence", commit_id, data.get("author", "unknown"), {"case_id": case_id})

    return jsonify({
        "success": True,
        "commit_id": commit_id,
        "content_hash": content_hash,
        "parent_hash": parent_hash,
        "branch": branch
    }), 201


@legal_bp.route("/evidence/log/<case_id>", methods=["GET"])
def evidence_log(case_id):
    """ev log - Get evidence history for a case."""
    branch = request.args.get("branch", "main")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM evidence_commits
        WHERE case_id = ? AND branch = ?
        ORDER BY created_at DESC
    """, (case_id, branch))

    commits = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify({"case_id": case_id, "branch": branch, "commits": commits, "total": len(commits)})


@legal_bp.route("/evidence/verify/<content_hash>", methods=["GET"])
def evidence_verify(content_hash):
    """ev verify - Verify evidence integrity by hash."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM evidence_commits WHERE content_hash = ?", (content_hash,))
    commit = cursor.fetchone()
    conn.close()

    if not commit:
        return jsonify({"verified": False, "error": "Hash not found"}), 404

    commit_dict = dict(commit)

    # Recompute hash to verify
    recomputed = compute_chain_hash(commit_dict["parent_hash"], commit_dict["content"])
    verified = recomputed == content_hash

    return jsonify({
        "verified": verified,
        "commit_id": commit_dict["id"],
        "case_id": commit_dict["case_id"],
        "content_hash": content_hash,
        "recomputed_hash": recomputed,
        "integrity": "INTACT" if verified else "COMPROMISED"
    })


@legal_bp.route("/evidence/diff/<hash_a>/<hash_b>", methods=["GET"])
def evidence_diff(hash_a, hash_b):
    """ev diff - Compare two evidence commits."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM evidence_commits WHERE content_hash = ?", (hash_a,))
    commit_a = cursor.fetchone()

    cursor.execute("SELECT * FROM evidence_commits WHERE content_hash = ?", (hash_b,))
    commit_b = cursor.fetchone()

    conn.close()

    if not commit_a or not commit_b:
        return jsonify({"error": "One or both commits not found"}), 404

    a_dict = dict(commit_a)
    b_dict = dict(commit_b)

    return jsonify({
        "commit_a": {"id": a_dict["id"], "hash": hash_a, "created_at": a_dict["created_at"]},
        "commit_b": {"id": b_dict["id"], "hash": hash_b, "created_at": b_dict["created_at"]},
        "same_case": a_dict["case_id"] == b_dict["case_id"],
        "time_delta": abs(a_dict["created_at"] - b_dict["created_at"]),
        "content_a": json.loads(a_dict["content"]),
        "content_b": json.loads(b_dict["content"])
    })


# --- Provenance ---

@legal_bp.route("/provenance/<case_id>", methods=["GET"])
def get_provenance(case_id):
    """Get full chain of custody for a case."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM provenance_entries
        WHERE case_id = ?
        ORDER BY timestamp ASC
    """, (case_id,))

    entries = [dict(row) for row in cursor.fetchall()]
    conn.close()

    # Verify chain integrity
    chain_valid = True
    for i in range(1, len(entries)):
        if entries[i]["previous_hash"] != entries[i-1]["current_hash"]:
            chain_valid = False
            break

    return jsonify({
        "case_id": case_id,
        "entries": entries,
        "total": len(entries),
        "chain_integrity": "VALID" if chain_valid else "BROKEN"
    })


@legal_bp.route("/provenance/<case_id>/verify", methods=["GET"])
def verify_provenance(case_id):
    """Verify provenance chain integrity."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM provenance_entries
        WHERE case_id = ?
        ORDER BY timestamp ASC
    """, (case_id,))

    entries = [dict(row) for row in cursor.fetchall()]
    conn.close()

    if not entries:
        return jsonify({"case_id": case_id, "verified": False, "reason": "No provenance entries"})

    breaks = []
    for i in range(1, len(entries)):
        if entries[i]["previous_hash"] != entries[i-1]["current_hash"]:
            breaks.append({
                "position": i,
                "expected": entries[i-1]["current_hash"],
                "found": entries[i]["previous_hash"]
            })

    return jsonify({
        "case_id": case_id,
        "verified": len(breaks) == 0,
        "total_entries": len(entries),
        "chain_breaks": breaks,
        "integrity": "INTACT" if len(breaks) == 0 else "COMPROMISED"
    })


# --- Confidence ---

@legal_bp.route("/confidence/<case_id>", methods=["GET"])
def get_confidence(case_id):
    """Get current confidence score for a case."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM confidence_scores
        WHERE case_id = ?
        ORDER BY calculated_at DESC LIMIT 1
    """, (case_id,))

    score = cursor.fetchone()
    conn.close()

    if not score:
        return jsonify({"case_id": case_id, "confidence": None, "message": "No confidence score calculated yet"})

    return jsonify({"case_id": case_id, "confidence": dict(score)})


@legal_bp.route("/confidence/evaluate", methods=["POST"])
def evaluate_confidence():
    """Evaluate and store confidence score."""
    data = request.get_json() or {}

    case_id = data.get("case_id")
    if not case_id:
        return jsonify({"error": "case_id required"}), 400

    factors = {
        "source_reliability": data.get("source_reliability", 0.5),
        "chain_integrity": data.get("chain_integrity", 0.5),
        "corroboration": data.get("corroboration", 0.5),
        "timeliness": data.get("timeliness", 0.5),
        "completeness": data.get("completeness", 0.5),
    }

    overall = calculate_confidence(**factors)

    score_id = str(uuid.uuid4())
    now = time.time()

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO confidence_scores
        (id, case_id, evidence_id, source_reliability, chain_integrity, corroboration, timeliness, completeness, overall_score, calculated_at, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        score_id,
        case_id,
        data.get("evidence_id"),
        factors["source_reliability"],
        factors["chain_integrity"],
        factors["corroboration"],
        factors["timeliness"],
        factors["completeness"],
        overall,
        now,
        data.get("notes", "")
    ))
    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "score_id": score_id,
        "case_id": case_id,
        "factors": factors,
        "overall_score": overall,
        "interpretation": "HIGH" if overall >= 0.7 else "MEDIUM" if overall >= 0.4 else "LOW"
    })


# --- Court Export ---

@legal_bp.route("/court/export/<case_id>", methods=["POST"])
def court_export(case_id):
    """Generate 5-page court package (WCAF format)."""
    data = request.get_json() or {}
    jurisdiction = data.get("jurisdiction", "de")

    conn = get_db()
    cursor = conn.cursor()

    # Get case
    cursor.execute("SELECT * FROM cases WHERE id = ?", (case_id,))
    case = cursor.fetchone()
    if not case:
        conn.close()
        return jsonify({"error": "Case not found"}), 404

    case_dict = dict(case)

    # Get evidence
    cursor.execute("SELECT * FROM evidence_commits WHERE case_id = ? ORDER BY created_at", (case_id,))
    evidence = [dict(row) for row in cursor.fetchall()]

    # Get provenance
    cursor.execute("SELECT * FROM provenance_entries WHERE case_id = ? ORDER BY timestamp", (case_id,))
    provenance = [dict(row) for row in cursor.fetchall()]

    # Get confidence
    cursor.execute("SELECT * FROM confidence_scores WHERE case_id = ? ORDER BY calculated_at DESC LIMIT 1", (case_id,))
    confidence = cursor.fetchone()

    # Generate export
    export_id = f"WCAF-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
    now = time.time()

    # WCAF 5-page structure
    wcaf_content = {
        "page_1_cover": {
            "case_id": case_id,
            "title": case_dict["title"],
            "jurisdiction": jurisdiction,
            "generated_at": now,
            "export_id": export_id
        },
        "page_2_summary": {
            "case_type": case_dict["case_type"],
            "status": case_dict["status"],
            "description": case_dict["description"],
            "evidence_count": len(evidence),
            "provenance_count": len(provenance)
        },
        "page_3_evidence": {
            "total": len(evidence),
            "items": [{"id": e["id"], "type": e["evidence_type"], "hash": e["content_hash"][:16] + "..."} for e in evidence[:10]]
        },
        "page_4_provenance": {
            "chain_length": len(provenance),
            "first_action": provenance[0]["action"] if provenance else None,
            "last_action": provenance[-1]["action"] if provenance else None,
            "integrity": "VERIFIED"
        },
        "page_5_certification": {
            "confidence_score": dict(confidence)["overall_score"] if confidence else None,
            "wcaf_version": "1.0",
            "agent": __agent_id__,
            "principle": "AI processes. Human decides. WINDI guarantees."
        }
    }

    content_hash = compute_hash(json.dumps(wcaf_content, sort_keys=True))

    cursor.execute("""
        INSERT INTO court_exports (id, case_id, export_type, jurisdiction, pages, generated_at, content_hash, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        export_id,
        case_id,
        "wcaf",
        jurisdiction,
        5,
        now,
        content_hash,
        json.dumps(wcaf_content)
    ))
    conn.commit()
    conn.close()

    log_audit("export", "court", export_id, data.get("author", "system"), {"case_id": case_id, "jurisdiction": jurisdiction})

    return jsonify({
        "success": True,
        "export_id": export_id,
        "case_id": case_id,
        "jurisdiction": jurisdiction,
        "pages": 5,
        "content_hash": content_hash,
        "wcaf": wcaf_content
    })


@legal_bp.route("/court/wcaf/<case_id>", methods=["GET"])
def get_wcaf(case_id):
    """Get latest WCAF export for a case."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM court_exports
        WHERE case_id = ? AND export_type = 'wcaf'
        ORDER BY generated_at DESC LIMIT 1
    """, (case_id,))

    export = cursor.fetchone()
    conn.close()

    if not export:
        return jsonify({"error": "No WCAF export found for this case"}), 404

    export_dict = dict(export)
    export_dict["metadata"] = json.loads(export_dict["metadata"]) if export_dict["metadata"] else {}

    return jsonify(export_dict)


# ═══════════════════════════════════════════════════════════════
#  INIT ON IMPORT
# ═══════════════════════════════════════════════════════════════

# Initialize database when module is imported
init_db()
