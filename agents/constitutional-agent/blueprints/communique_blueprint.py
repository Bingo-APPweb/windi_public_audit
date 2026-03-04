"""
WINDI Communique Engine v2.0.0 - Flask Blueprint
=================================================

Domain extension for the Constitutional Agent (Sandbox Core).
Integrates as /communique/* endpoints on :8091.

Migrated from standalone BaseHTTPRequestHandler to Flask Blueprint.
Database preserved: /opt/windi/communique/data/communiques.db (55 docs)

Features:
- Full CRUD for communiques
- ISP template resolution
- Dragon AI draft generation
- Canvas InDesign-style editing
- Ledger integration (query + write)
- Multimedia evidence support

Principle: "AI processes. Human decides. WINDI guarantees."

Version: 2.0.0
Sealed: W-COMM-001
"""

import hashlib
import json
import os
import re
import sqlite3
import unicodedata
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests
from flask import Blueprint, jsonify, request, Response

__version__ = "2.0.0"
__agent_id__ = "W-COMM-001"
__agent_name__ = "Communique"

# Database path - PRESERVED from original location
DB_PATH = "/opt/windi/communique/data/communiques.db"
PUBLISHED_DIR = "/opt/windi/communique/published"
ISP_PROFILE_PATH = "/opt/windi/isp/communique/profile.json"

# External services
DRAGON_URL = "http://localhost:8108"
LEDGER_URL = "http://localhost:8101"
EXPORT_URL = "http://localhost:8103"

# ===================================================================
#  DOCUMENT TYPE ROUTING (Document Intelligence Hub)
# ===================================================================

SUPPORTED_DOC_TYPES = [
    "communique",
    "letter",
    "email",
    "invoice",
    "contract",
    "report",
    "presentation",
    "spreadsheet",
]

RENDERERS = {
    "communique":    {"renderer": "renderer_communique",    "status": "live",   "port": 8091},
    "letter":        {"renderer": "renderer_letter",        "status": "stub",   "port": None},
    "email":         {"renderer": "renderer_email",         "status": "stub",   "port": None},
    "invoice":       {"renderer": "renderer_invoice",       "status": "live",   "port": 8103},  # Export Engine
    "contract":      {"renderer": "renderer_contract",      "status": "stub",   "port": None},
    "report":        {"renderer": "renderer_report",        "status": "stub",   "port": None},
    "presentation":  {"renderer": "renderer_presentation",  "status": "stub",   "port": None},
    "spreadsheet":   {"renderer": "renderer_spreadsheet",   "status": "stub",   "port": None},
}


def resolve_renderer(doc_type: str) -> dict:
    """Resolve renderer for document type."""
    return RENDERERS.get(doc_type, RENDERERS["communique"])


def is_valid_doc_type(doc_type: str) -> bool:
    """Check if doc_type is supported."""
    return doc_type in SUPPORTED_DOC_TYPES


# ===================================================================
#  BLUEPRINT
# ===================================================================

communique_bp = Blueprint("communique", __name__, url_prefix="/communique")


# ===================================================================
#  DATABASE FUNCTIONS
# ===================================================================

def get_db():
    """Get database connection with WAL mode."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA busy_timeout=5000")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Initialize database schema (preserves existing data)."""
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS communiques (
            id              TEXT PRIMARY KEY,
            title_de        TEXT NOT NULL,
            title_en        TEXT,
            title_pt        TEXT,
            body_de         TEXT NOT NULL,
            body_en         TEXT,
            body_pt         TEXT,
            category        TEXT NOT NULL CHECK(category IN ('LAUNCH','UPDATE','ALERT','GOVERNANCE','REPORT')),
            impact_level    TEXT DEFAULT 'MED' CHECK(impact_level IN ('LOW','MED','HIGH','CRIT')),
            status          TEXT DEFAULT 'DRAFT' CHECK(status IN ('DRAFT','REVIEW','PUBLISHED','ARCHIVED','REVOKED')),
            author_role     TEXT NOT NULL,
            author_name     TEXT NOT NULL,
            approved_by     TEXT,
            approval_date   TEXT,
            content_hash    TEXT,
            bundle_hash     TEXT,
            ledger_id       TEXT,
            receipt_id      TEXT,
            version         INTEGER DEFAULT 1,
            tags            TEXT DEFAULT '[]',
            related_docs    TEXT DEFAULT '[]',
            isp_template    TEXT,
            created_at      TEXT NOT NULL,
            published_at    TEXT,
            updated_at      TEXT NOT NULL,
            archived_at     TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_communiques_status ON communiques(status);
        CREATE INDEX IF NOT EXISTS idx_communiques_category ON communiques(category);
        CREATE INDEX IF NOT EXISTS idx_communiques_published ON communiques(published_at);

        CREATE TABLE IF NOT EXISTS communique_audit (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            com_id      TEXT NOT NULL,
            action      TEXT NOT NULL,
            old_status  TEXT,
            new_status  TEXT,
            actor       TEXT NOT NULL,
            details     TEXT,
            timestamp   TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_audit_com ON communique_audit(com_id);
    """)
    conn.commit()

    # Migration: add isp_template column if missing
    cursor = conn.execute("PRAGMA table_info(communiques)")
    columns = [row[1] for row in cursor.fetchall()]
    if "isp_template" not in columns:
        conn.execute("ALTER TABLE communiques ADD COLUMN isp_template TEXT DEFAULT NULL")
        conn.commit()

    # Migration: add doc_type column if missing (Document Intelligence Hub)
    cursor = conn.execute("PRAGMA table_info(communiques)")
    columns = [row[1] for row in cursor.fetchall()]
    if "doc_type" not in columns:
        conn.execute("ALTER TABLE communiques ADD COLUMN doc_type TEXT DEFAULT 'communique'")
        conn.commit()
        # Backfill existing rows
        conn.execute("UPDATE communiques SET doc_type = 'communique' WHERE doc_type IS NULL")
        conn.commit()

    conn.close()


def now_iso():
    """Current UTC timestamp in ISO 8601."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_text(text):
    """Unicode NFC normalization for canonical hashing."""
    if text is None:
        return None
    return unicodedata.normalize("NFC", text.strip())


def generate_id():
    """Generate communique ID: COM-YYYYMMDD-XXXX."""
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    prefix = f"COM-{today}-"
    conn = get_db()
    row = conn.execute(
        "SELECT id FROM communiques WHERE id LIKE ? ORDER BY id DESC LIMIT 1",
        (f"{prefix}%",)
    ).fetchone()
    conn.close()

    if row:
        seq = int(row["id"].split("-")[-1]) + 1
    else:
        seq = 1
    return f"{prefix}{seq:04d}"


def compute_content_hash(com: dict) -> str:
    """Compute SHA-256 hash of communique content fields."""
    fields = ["title_de", "title_en", "title_pt", "body_de", "body_en", "body_pt",
              "category", "impact_level", "author_name", "author_role"]
    canonical = "|".join(str(com.get(f, "") or "") for f in fields)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ===================================================================
#  ISP RESOLVER (inline from original)
# ===================================================================

_cached_profile = None
_cached_mtime = 0


def _load_isp_profile():
    """Load ISP communique profile with caching."""
    global _cached_profile, _cached_mtime

    if not os.path.exists(ISP_PROFILE_PATH):
        return None

    mtime = os.path.getmtime(ISP_PROFILE_PATH)
    if _cached_profile and mtime == _cached_mtime:
        return _cached_profile

    with open(ISP_PROFILE_PATH, "r", encoding="utf-8") as f:
        _cached_profile = json.load(f)
        _cached_mtime = mtime

    return _cached_profile


def get_isp_templates():
    """Return list of ISP templates."""
    profile = _load_isp_profile()
    if not profile:
        return []

    templates = []
    for t in profile.get("templates", []):
        templates.append({
            "id": t["id"],
            "code": t["code"],
            "name_de": t["name_de"],
            "name_en": t["name_en"],
            "name_pt": t["name_pt"],
            "description_en": t["description_en"],
            "governance_level": t["governance_level"],
            "requires_review": t["requires_review"],
            "requires_seal": t["requires_seal"],
            "sge_keywords": t["sge_keywords"],
            "form_fields_count": len(t.get("form_fields", [])),
        })
    return templates


def resolve_isp(body_text: str, title_text: str = "") -> dict:
    """Match text against ISP template keywords."""
    profile = _load_isp_profile()
    if not profile:
        return {"suggestions": [], "best_match": None, "resolver_version": "1.0.0"}

    resolver_config = profile.get("resolver", {})
    auto_threshold = resolver_config.get("thresholds", {}).get("auto_apply", 100)
    suggest_threshold = resolver_config.get("thresholds", {}).get("human_confirms", 70)

    combined_text = f"{title_text} {body_text}".lower()
    suggestions = []

    for t in profile.get("templates", []):
        keywords = t.get("sge_keywords", [])
        if not keywords:
            continue

        matched = []
        for kw in keywords:
            pattern = re.escape(kw.lower())
            if re.search(r'\b' + pattern + r'\b', combined_text):
                matched.append(kw)

        total = len(keywords)
        score = (len(matched) / total * 100) if total > 0 else 0

        if score > 0:
            action = "manual"
            if score >= auto_threshold:
                action = "auto_apply"
            elif score >= suggest_threshold:
                action = "suggest"

            suggestions.append({
                "template_id": t["id"],
                "code": t["code"],
                "name_en": t["name_en"],
                "name_de": t["name_de"],
                "score": round(score, 1),
                "matched_keywords": matched,
                "total_keywords": total,
                "action": action,
            })

    suggestions.sort(key=lambda x: x["score"], reverse=True)
    best = suggestions[0] if suggestions and suggestions[0]["score"] >= suggest_threshold else None

    return {
        "suggestions": suggestions,
        "best_match": best,
        "resolver_version": resolver_config.get("version", "1.0.0"),
    }


def get_isp_status():
    """Return ISP status for health endpoint."""
    profile = _load_isp_profile()
    connected = profile is not None
    template_count = len(profile.get("templates", [])) if profile else 0
    resolver_version = profile.get("resolver", {}).get("version", "1.0.0") if profile else "0.0.0"

    return {
        "isp_connected": connected,
        "templates_loaded": template_count,
        "resolver_version": resolver_version,
    }


# ===================================================================
#  HEALTH & STATUS
# ===================================================================

@communique_bp.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    conn = get_db()
    stats = {}
    for status in ["DRAFT", "REVIEW", "PUBLISHED", "ARCHIVED", "REVOKED"]:
        row = conn.execute("SELECT COUNT(*) as c FROM communiques WHERE status = ?", (status,)).fetchone()
        stats[status.lower()] = row["c"]
    stats["total"] = sum(stats.values())
    conn.close()

    return jsonify({
        "status": "GREEN",
        "agent": __agent_id__,
        "name": __agent_name__,
        "version": __version__,
        "database": DB_PATH,
        "stats": stats,
        "isp": get_isp_status(),
        "integrations": {
            "dragon": DRAGON_URL,
            "ledger": LEDGER_URL,
            "export": EXPORT_URL,
        },
        "principle": "AI processes. Human decides. WINDI guarantees.",
        "timestamp": now_iso(),
    })


@communique_bp.route("/status", methods=["GET"])
def status():
    """Detailed status including external service checks."""
    dragon_ok = False
    ledger_ok = False

    try:
        r = requests.get(f"{DRAGON_URL}/health", timeout=2)
        dragon_ok = r.status_code == 200
    except:
        pass

    try:
        r = requests.get(f"{LEDGER_URL}/health", timeout=2)
        ledger_ok = r.status_code == 200
    except:
        pass

    return jsonify({
        "agent": __agent_id__,
        "version": __version__,
        "services": {
            "dragon": {"url": DRAGON_URL, "healthy": dragon_ok},
            "ledger": {"url": LEDGER_URL, "healthy": ledger_ok},
        },
        "isp": get_isp_status(),
        "timestamp": now_iso(),
    })


# ===================================================================
#  DOCUMENT TYPES (Document Intelligence Hub)
# ===================================================================

@communique_bp.route("/doc-types", methods=["GET"])
def doc_types():
    """List supported document types and their renderer status."""
    doc_type_list = []
    for dt in SUPPORTED_DOC_TYPES:
        info = RENDERERS.get(dt, {})
        doc_type_list.append({
            "type": dt,
            "renderer": info.get("renderer", f"renderer_{dt}"),
            "status": info.get("status", "stub"),
            "port": info.get("port"),
        })

    return jsonify({
        "agent": __agent_id__,
        "version": __version__,
        "doc_types": doc_type_list,
        "total": len(doc_type_list),
        "live_count": sum(1 for d in doc_type_list if d["status"] == "live"),
        "stub_count": sum(1 for d in doc_type_list if d["status"] == "stub"),
        "principle": "1 agent + N ISPs + N renderers = clean architecture",
    })


# ===================================================================
#  CRUD COMMUNIQUES
# ===================================================================

@communique_bp.route("/create", methods=["POST"])
def create():
    """Create a new document in DRAFT status (Document Intelligence Hub)."""
    data = request.get_json() or {}

    if not data.get("title_de") or not data.get("body_de"):
        return jsonify({"error": "title_de and body_de required"}), 400
    if not data.get("author_name") or not data.get("author_role"):
        return jsonify({"error": "author_name and author_role required"}), 400

    # Document type routing (default: communique for retrocompatibility)
    doc_type = data.get("doc_type", "communique")
    if not is_valid_doc_type(doc_type):
        return jsonify({
            "error": f"Invalid doc_type: {doc_type}",
            "supported": SUPPORTED_DOC_TYPES
        }), 400

    renderer_info = resolve_renderer(doc_type)

    # ISP Resolver
    isp_suggestion = None
    if not data.get("isp_template"):
        isp_result = resolve_isp(
            body_text=data.get("body_de", "") + " " + data.get("body_en", ""),
            title_text=data.get("title_de", "") + " " + data.get("title_en", "")
        )
        if isp_result.get("best_match"):
            best = isp_result["best_match"]
            if best["action"] == "auto_apply":
                data["isp_template"] = best["template_id"]
            isp_suggestion = isp_result

    com_id = generate_id()
    ts = now_iso()

    conn = get_db()
    conn.execute("""
        INSERT INTO communiques (
            id, title_de, title_en, title_pt,
            body_de, body_en, body_pt,
            category, impact_level, status,
            author_role, author_name,
            tags, related_docs, isp_template,
            doc_type, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'DRAFT', ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        com_id,
        normalize_text(data.get("title_de", "")),
        normalize_text(data.get("title_en")),
        normalize_text(data.get("title_pt")),
        normalize_text(data.get("body_de", "")),
        normalize_text(data.get("body_en")),
        normalize_text(data.get("body_pt")),
        data.get("category", "UPDATE"),
        data.get("impact_level", "MED"),
        data.get("author_role", ""),
        data.get("author_name", ""),
        json.dumps(data.get("tags", [])),
        json.dumps(data.get("related_docs", [])),
        data.get("isp_template"),
        doc_type,
        ts, ts
    ))

    # Audit log
    conn.execute("""
        INSERT INTO communique_audit (com_id, action, old_status, new_status, actor, details, timestamp)
        VALUES (?, 'CREATE', NULL, 'DRAFT', ?, ?, ?)
    """, (com_id, data.get("author_name", "system"), f"doc_type={doc_type}", ts))

    conn.commit()
    conn.close()

    result = {
        "id": com_id,
        "status": "DRAFT",
        "doc_type": doc_type,
        "renderer": renderer_info,
        "created_at": ts
    }
    if isp_suggestion:
        result["isp_resolver"] = isp_suggestion

    return jsonify(result), 201


@communique_bp.route("/list", methods=["GET"])
def list_communiques():
    """List communiques with optional filters."""
    status_filter = request.args.get("status")
    category = request.args.get("category")
    limit = int(request.args.get("limit", 20))
    offset = int(request.args.get("offset", 0))

    conn = get_db()
    query = "SELECT * FROM communiques WHERE 1=1"
    params = []

    if status_filter:
        query += " AND status = ?"
        params.append(status_filter)
    if category:
        query += " AND category = ?"
        params.append(category)

    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = conn.execute(query, params).fetchall()
    conn.close()

    return jsonify({
        "communiques": [dict(r) for r in rows],
        "count": len(rows)
    })


@communique_bp.route("/<com_id>", methods=["GET"])
def get_communique(com_id):
    """Get a single communique by ID."""
    conn = get_db()
    row = conn.execute("SELECT * FROM communiques WHERE id = ?", (com_id,)).fetchone()

    if not row:
        conn.close()
        return jsonify({"error": "Not found"}), 404

    com = dict(row)

    # Include audit trail
    audit = conn.execute(
        "SELECT * FROM communique_audit WHERE com_id = ? ORDER BY timestamp ASC",
        (com_id,)
    ).fetchall()
    com["audit_trail"] = [dict(a) for a in audit]

    conn.close()
    return jsonify(com)


@communique_bp.route("/<com_id>", methods=["PUT", "PATCH"])
def update_communique(com_id):
    """Update a communique. Only allowed for DRAFT or REVIEW status."""
    data = request.get_json() or {}

    conn = get_db()
    row = conn.execute("SELECT status FROM communiques WHERE id = ?", (com_id,)).fetchone()

    if not row:
        conn.close()
        return jsonify({"error": "Communique not found"}), 404

    if row["status"] in ("PUBLISHED", "ARCHIVED", "REVOKED"):
        conn.close()
        return jsonify({"error": f"Cannot modify communique in {row['status']} status. Immutability enforced."}), 403

    ts = now_iso()
    updates = []
    values = []

    for field in ["title_de", "title_en", "title_pt", "body_de", "body_en", "body_pt",
                  "category", "impact_level", "tags", "related_docs", "isp_template"]:
        if field in data:
            val = data[field]
            if field in ("tags", "related_docs") and isinstance(val, list):
                val = json.dumps(val)
            elif field.startswith("title_") or field.startswith("body_"):
                val = normalize_text(val)
            updates.append(f"{field} = ?")
            values.append(val)

    if updates:
        updates.append("updated_at = ?")
        values.append(ts)
        updates.append("version = version + 1")
        values.append(com_id)

        conn.execute(
            f"UPDATE communiques SET {', '.join(updates)} WHERE id = ?",
            values
        )
        conn.commit()

    conn.close()
    return jsonify({"id": com_id, "updated_at": ts})


@communique_bp.route("/<com_id>/review", methods=["POST", "PATCH"])
def review(com_id):
    """Transition DRAFT -> REVIEW."""
    data = request.get_json() or {}
    actor = data.get("actor", "system")

    result = _transition_status(com_id, "REVIEW", actor)
    if "error" in result:
        return jsonify(result), result.get("code", 400)
    return jsonify(result)


@communique_bp.route("/<com_id>/publish", methods=["POST"])
def publish(com_id):
    """Transition REVIEW -> PUBLISHED with full crypto sealing."""
    data = request.get_json() or {}
    actor = data.get("approved_by", data.get("actor", "system"))

    conn = get_db()
    row = conn.execute("SELECT * FROM communiques WHERE id = ?", (com_id,)).fetchone()

    if not row:
        conn.close()
        return jsonify({"error": "Not found"}), 404

    com = dict(row)

    if com["status"] != "REVIEW":
        conn.close()
        return jsonify({"error": f"Cannot publish from {com['status']}. Must be in REVIEW."}), 400

    conn.close()

    # Transition status
    result = _transition_status(com_id, "PUBLISHED", actor)
    if "error" in result:
        return jsonify(result), result.get("code", 400)

    # Compute content hash
    content_hash = compute_content_hash(com)

    # Publish to Ledger
    ledger_id = None
    receipt_id = None
    try:
        ledger_payload = {
            "type": "communique_publish",
            "source": "communique",
            "source_id": com_id,
            "content_hash": content_hash,
            "category": com.get("category"),
            "impact_level": com.get("impact_level"),
            "author": actor,
        }
        r = requests.post(f"{LEDGER_URL}/ingest", json=ledger_payload, timeout=5)
        if r.status_code == 200:
            ledger_data = r.json()
            ledger_id = ledger_data.get("ledger_id") or ledger_data.get("verification_id")
            receipt_id = ledger_data.get("receipt_id") or ledger_data.get("id")
    except Exception as e:
        pass  # Ledger failure should not block publish

    # Update crypto fields
    conn = get_db()
    conn.execute("""
        UPDATE communiques SET content_hash=?, ledger_id=?, receipt_id=?, updated_at=?
        WHERE id = ?
    """, (content_hash, ledger_id, receipt_id, now_iso(), com_id))
    conn.commit()
    conn.close()

    return jsonify({
        "id": com_id,
        "status": "PUBLISHED",
        "content_hash": content_hash,
        "ledger_id": ledger_id,
        "receipt_id": receipt_id,
        "timestamp": result.get("timestamp")
    })


@communique_bp.route("/<com_id>/archive", methods=["POST"])
def archive(com_id):
    """Transition PUBLISHED -> ARCHIVED."""
    data = request.get_json() or {}
    actor = data.get("actor", "system")
    reason = data.get("reason", "Archived by operator")

    result = _transition_status(com_id, "ARCHIVED", actor, reason)
    if "error" in result:
        return jsonify(result), result.get("code", 400)
    return jsonify(result)


@communique_bp.route("/<com_id>/revoke", methods=["POST"])
def revoke(com_id):
    """Transition PUBLISHED -> REVOKED (requires reason)."""
    data = request.get_json() or {}
    actor = data.get("actor", "system")
    reason = data.get("reason")

    if not reason:
        return jsonify({"error": "Reason required for revocation"}), 400

    result = _transition_status(com_id, "REVOKED", actor, reason)
    if "error" in result:
        return jsonify(result), result.get("code", 400)
    return jsonify(result)


def _transition_status(com_id: str, new_status: str, actor: str, details: str = None) -> dict:
    """Transition communique status with audit trail."""
    valid_transitions = {
        "DRAFT": ["REVIEW"],
        "REVIEW": ["DRAFT", "PUBLISHED"],
        "PUBLISHED": ["ARCHIVED", "REVOKED"],
        "ARCHIVED": [],
        "REVOKED": [],
    }

    conn = get_db()
    row = conn.execute("SELECT status FROM communiques WHERE id = ?", (com_id,)).fetchone()

    if not row:
        conn.close()
        return {"error": "Communique not found", "code": 404}

    old_status = row["status"]
    if new_status not in valid_transitions.get(old_status, []):
        conn.close()
        return {"error": f"Invalid transition: {old_status} -> {new_status}", "code": 400}

    ts = now_iso()
    update_fields = {"status": new_status, "updated_at": ts}

    if new_status == "PUBLISHED":
        update_fields["published_at"] = ts
        update_fields["approved_by"] = actor
        update_fields["approval_date"] = ts
    elif new_status in ("ARCHIVED", "REVOKED"):
        update_fields["archived_at"] = ts

    set_clause = ", ".join(f"{k} = ?" for k in update_fields)
    values = list(update_fields.values()) + [com_id]
    conn.execute(f"UPDATE communiques SET {set_clause} WHERE id = ?", values)

    # Audit
    conn.execute("""
        INSERT INTO communique_audit (com_id, action, old_status, new_status, actor, details, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (com_id, f"TRANSITION_{new_status}", old_status, new_status, actor, details, ts))

    conn.commit()
    conn.close()

    return {"id": com_id, "old_status": old_status, "new_status": new_status, "timestamp": ts}


@communique_bp.route("/<com_id>/verify", methods=["GET"])
def verify(com_id):
    """Public verification endpoint."""
    conn = get_db()
    row = conn.execute("SELECT * FROM communiques WHERE id = ?", (com_id,)).fetchone()

    if not row:
        conn.close()
        return jsonify({"error": "Not found", "verified": False}), 404

    com = dict(row)
    conn.close()

    if com["status"] not in ("PUBLISHED", "ARCHIVED", "REVOKED"):
        return jsonify({"error": "Not published", "verified": False}), 400

    # Recompute hash
    current_hash = compute_content_hash(com)
    hash_match = current_hash == com.get("content_hash")

    # Check Ledger
    ledger_verified = False
    ledger_status = "unknown"
    if com.get("receipt_id"):
        try:
            r = requests.get(f"{LEDGER_URL}/receipt/{com['receipt_id']}", timeout=3)
            if r.status_code == 200:
                receipt = r.json()
                receipt = receipt.get("receipt", receipt)
                ledger_status = receipt.get("status", "unknown")
                ledger_verified = ledger_status == "sealed"
        except:
            pass

    return jsonify({
        "communique_id": com_id,
        "verified": hash_match and ledger_verified,
        "content_hash_match": hash_match,
        "content_hash_stored": com.get("content_hash"),
        "content_hash_computed": current_hash,
        "bundle_hash": com.get("bundle_hash"),
        "ledger_verified": ledger_verified,
        "ledger_status": ledger_status,
        "receipt_id": com.get("receipt_id"),
        "status": com.get("status"),
        "published_at": com.get("published_at"),
        "verification_timestamp": now_iso()
    })


# ===================================================================
#  ISP TEMPLATES
# ===================================================================

@communique_bp.route("/templates", methods=["GET"])
def templates():
    """List ISP templates."""
    templates = get_isp_templates()
    profile = _load_isp_profile()

    profile_info = None
    if profile:
        profile_info = {
            "profile_id": profile["isp_profile"]["id"],
            "name": profile["isp_profile"]["name"],
            "version": profile["isp_profile"]["version"],
        }

    return jsonify({
        "profile": profile_info,
        "templates": templates,
        "count": len(templates),
    })


@communique_bp.route("/templates/<template_id>", methods=["GET"])
def template_detail(template_id):
    """Get single ISP template detail."""
    profile = _load_isp_profile()
    if not profile:
        return jsonify({"error": "ISP not available"}), 501

    for t in profile.get("templates", []):
        if t["id"] == template_id or t["code"] == template_id:
            return jsonify(t)

    return jsonify({"error": "Template not found"}), 404


# ===================================================================
#  DRAGON INTEGRATION (NEW)
# ===================================================================

@communique_bp.route("/draft/ai", methods=["POST"])
def draft_ai():
    """Generate draft via Dragon AI integration."""
    data = request.get_json() or {}

    prompt = data.get("prompt")
    if not prompt:
        return jsonify({"error": "prompt required"}), 400

    isp_template = data.get("isp_template")
    category = data.get("category", "UPDATE")
    author_name = data.get("author_name", "Dragon AI")
    author_role = data.get("author_role", "AI Assistant")

    # Call Dragon
    try:
        dragon_payload = {
            "prompt": f"Generate a WINDI communique about: {prompt}. "
                      f"Include trilingual content (German primary, English, Portuguese). "
                      f"Format as JSON with keys: title_de, title_en, title_pt, body_de, body_en, body_pt",
            "dragon": "architect",
            "format": "json"
        }

        r = requests.post(f"{DRAGON_URL}/dragon", json=dragon_payload, timeout=30)

        if r.status_code != 200:
            return jsonify({"error": "Dragon request failed", "status": r.status_code}), 502

        dragon_response = r.json()
        content = dragon_response.get("response", dragon_response.get("content", {}))

        # Parse if string
        if isinstance(content, str):
            try:
                content = json.loads(content)
            except:
                content = {"body_de": content, "title_de": prompt[:50]}

    except requests.Timeout:
        return jsonify({"error": "Dragon timeout"}), 504
    except Exception as e:
        return jsonify({"error": f"Dragon error: {str(e)}"}), 502

    # Create draft with Dragon content
    draft_data = {
        "title_de": content.get("title_de", prompt[:50]),
        "title_en": content.get("title_en"),
        "title_pt": content.get("title_pt"),
        "body_de": content.get("body_de", ""),
        "body_en": content.get("body_en"),
        "body_pt": content.get("body_pt"),
        "category": category,
        "author_name": author_name,
        "author_role": author_role,
        "isp_template": isp_template,
        "tags": ["ai-generated"],
    }

    # Create the draft
    com_id = generate_id()
    ts = now_iso()

    conn = get_db()
    conn.execute("""
        INSERT INTO communiques (
            id, title_de, title_en, title_pt,
            body_de, body_en, body_pt,
            category, impact_level, status,
            author_role, author_name,
            tags, related_docs, isp_template,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'MED', 'DRAFT', ?, ?, ?, '[]', ?, ?, ?)
    """, (
        com_id,
        normalize_text(draft_data.get("title_de", "")),
        normalize_text(draft_data.get("title_en")),
        normalize_text(draft_data.get("title_pt")),
        normalize_text(draft_data.get("body_de", "")),
        normalize_text(draft_data.get("body_en")),
        normalize_text(draft_data.get("body_pt")),
        category,
        author_role,
        author_name,
        json.dumps(draft_data.get("tags", [])),
        isp_template,
        ts, ts
    ))

    conn.execute("""
        INSERT INTO communique_audit (com_id, action, old_status, new_status, actor, details, timestamp)
        VALUES (?, 'CREATE_AI', NULL, 'DRAFT', ?, ?, ?)
    """, (com_id, "Dragon AI", f"Prompt: {prompt[:100]}", ts))

    conn.commit()
    conn.close()

    return jsonify({
        "id": com_id,
        "status": "DRAFT",
        "created_at": ts,
        "dragon_generated": True,
        "content": draft_data,
    }), 201


# ===================================================================
#  CANVAS (NEW)
# ===================================================================

@communique_bp.route("/<com_id>/canvas", methods=["GET"])
def canvas_get(com_id):
    """Get communique data formatted for Canvas editor."""
    conn = get_db()
    row = conn.execute("SELECT * FROM communiques WHERE id = ?", (com_id,)).fetchone()

    if not row:
        conn.close()
        return jsonify({"error": "Not found"}), 404

    com = dict(row)
    conn.close()

    # Canvas format with layout info
    canvas_data = {
        "id": com_id,
        "status": com["status"],
        "editable": com["status"] in ("DRAFT", "REVIEW"),
        "layout": {
            "template": com.get("isp_template") or "default",
            "languages": ["de", "en", "pt"],
        },
        "content": {
            "de": {
                "title": com.get("title_de", ""),
                "body": com.get("body_de", ""),
            },
            "en": {
                "title": com.get("title_en", ""),
                "body": com.get("body_en", ""),
            },
            "pt": {
                "title": com.get("title_pt", ""),
                "body": com.get("body_pt", ""),
            },
        },
        "metadata": {
            "category": com.get("category"),
            "impact_level": com.get("impact_level"),
            "author_name": com.get("author_name"),
            "author_role": com.get("author_role"),
            "version": com.get("version"),
            "created_at": com.get("created_at"),
            "updated_at": com.get("updated_at"),
        },
    }

    return jsonify(canvas_data)


@communique_bp.route("/<com_id>/canvas/save", methods=["POST"])
def canvas_save(com_id):
    """Save Canvas editor changes."""
    data = request.get_json() or {}

    conn = get_db()
    row = conn.execute("SELECT status FROM communiques WHERE id = ?", (com_id,)).fetchone()

    if not row:
        conn.close()
        return jsonify({"error": "Not found"}), 404

    if row["status"] not in ("DRAFT", "REVIEW"):
        conn.close()
        return jsonify({"error": f"Cannot edit in {row['status']} status"}), 403

    ts = now_iso()

    # Extract content from canvas format
    content = data.get("content", {})
    updates = {
        "title_de": content.get("de", {}).get("title"),
        "title_en": content.get("en", {}).get("title"),
        "title_pt": content.get("pt", {}).get("title"),
        "body_de": content.get("de", {}).get("body"),
        "body_en": content.get("en", {}).get("body"),
        "body_pt": content.get("pt", {}).get("body"),
    }

    # Build update query
    set_parts = []
    values = []
    for k, v in updates.items():
        if v is not None:
            set_parts.append(f"{k} = ?")
            values.append(normalize_text(v))

    if set_parts:
        set_parts.append("updated_at = ?")
        values.append(ts)
        set_parts.append("version = version + 1")
        values.append(com_id)

        conn.execute(
            f"UPDATE communiques SET {', '.join(set_parts)} WHERE id = ?",
            values
        )

        conn.execute("""
            INSERT INTO communique_audit (com_id, action, old_status, new_status, actor, details, timestamp)
            VALUES (?, 'CANVAS_EDIT', ?, ?, ?, ?, ?)
        """, (com_id, row["status"], row["status"], data.get("editor", "Canvas"), "Canvas save", ts))

        conn.commit()

    conn.close()

    return jsonify({
        "id": com_id,
        "saved": True,
        "updated_at": ts,
    })


# ===================================================================
#  FEED (COMPATIBILITY)
# ===================================================================

@communique_bp.route("/feed.json", methods=["GET"])
def feed_json():
    """Public JSON feed of published communiques."""
    conn = get_db()
    rows = conn.execute("""
        SELECT id, title_de, title_en, title_pt, category, impact_level,
               author_name, author_role, content_hash, receipt_id,
               published_at, created_at
        FROM communiques
        WHERE status = 'PUBLISHED'
        ORDER BY published_at DESC
        LIMIT 20
    """).fetchall()
    conn.close()

    return jsonify({
        "feed": "WINDI Communique Feed",
        "version": __version__,
        "count": len(rows),
        "communiques": [dict(r) for r in rows],
        "generated_at": now_iso()
    })


# ===================================================================
#  EXPORT
# ===================================================================

@communique_bp.route("/<com_id>/export", methods=["POST"])
def export(com_id):
    """Export communique via Export Engine."""
    data = request.get_json() or {}
    format_type = data.get("format", "pdf")

    conn = get_db()
    row = conn.execute("SELECT * FROM communiques WHERE id = ?", (com_id,)).fetchone()

    if not row:
        conn.close()
        return jsonify({"error": "Not found"}), 404

    com = dict(row)
    conn.close()

    if com["status"] not in ("PUBLISHED", "ARCHIVED"):
        return jsonify({"error": "Only published/archived can be exported"}), 400

    # Call Export Engine
    try:
        export_payload = {
            "source": "communique",
            "source_id": com_id,
            "format": format_type,
            "content": {
                "title": com.get("title_de"),
                "body": com.get("body_de"),
                "category": com.get("category"),
                "author": com.get("author_name"),
            }
        }

        r = requests.post(f"{EXPORT_URL}/export", json=export_payload, timeout=30)

        if r.status_code == 200:
            return jsonify(r.json())
        else:
            return jsonify({"error": "Export failed", "status": r.status_code}), 502

    except Exception as e:
        return jsonify({"error": f"Export error: {str(e)}"}), 502


# ===================================================================
#  LEDGER QUERY (NEW)
# ===================================================================

@communique_bp.route("/ledger/query", methods=["GET"])
def ledger_query():
    """Query Ledger for communique receipts."""
    limit = int(request.args.get("limit", 10))

    try:
        r = requests.get(
            f"{LEDGER_URL}/search",
            params={"source": "communique", "limit": limit},
            timeout=5
        )

        if r.status_code == 200:
            return jsonify(r.json())
        else:
            return jsonify({"error": "Ledger query failed"}), 502

    except Exception as e:
        return jsonify({"error": f"Ledger error: {str(e)}"}), 502


# ===================================================================
#  INITIALIZE
# ===================================================================

# Initialize database on import
init_db()
