#!/usr/bin/env python3
"""
WINDI Communiqué Engine — Database Module
==========================================
SQLite operations for communiqué management.
Implements immutability lock for PUBLISHED status.

Port: 8105
Principle: "AI processes. Human decides. WINDI guarantees."
"""

import sqlite3
import json
import os
import unicodedata
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "communiques.db")


def get_db():
    """Get database connection with WAL mode."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Initialize database schema."""
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

            -- Governance
            author_role     TEXT NOT NULL,
            author_name     TEXT NOT NULL,
            approved_by     TEXT,
            approval_date   TEXT,

            -- Cryptography (filled on publish)
            content_hash    TEXT,
            bundle_hash     TEXT,
            ledger_id       TEXT,
            receipt_id      TEXT,

            -- Metadata
            version         INTEGER DEFAULT 1,
            tags            TEXT DEFAULT '[]',
            related_docs    TEXT DEFAULT '[]',

            -- Timestamps
            created_at      TEXT NOT NULL,
            published_at    TEXT,
            updated_at      TEXT NOT NULL,
            archived_at     TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_communiques_status ON communiques(status);
        CREATE INDEX IF NOT EXISTS idx_communiques_category ON communiques(category);
        CREATE INDEX IF NOT EXISTS idx_communiques_published ON communiques(published_at);

        -- Audit log for all state transitions
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
    conn.close()

    # Migration: add isp_template column if missing
    _migrate_isp_template()


def _migrate_isp_template():
    """Add isp_template column to communiques table if it does not exist."""
    conn = get_db()
    cursor = conn.execute("PRAGMA table_info(communiques)")
    columns = [row[1] for row in cursor.fetchall()]
    if "isp_template" not in columns:
        conn.execute("ALTER TABLE communiques ADD COLUMN isp_template TEXT DEFAULT NULL")
        conn.commit()
        print("[communique_db] Migration: added isp_template column")
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
    """Generate communiqué ID: COM-YYYYMMDD-XXXX."""
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


def create_communique(data):
    """Create a new communiqué in DRAFT status."""
    com_id = generate_id()
    ts = now_iso()

    conn = get_db()
    conn.execute("""
        INSERT INTO communiques (
            id, title_de, title_en, title_pt,
            body_de, body_en, body_pt,
            category, impact_level, status,
            author_role, author_name,
            tags, related_docs,
            isp_template,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'DRAFT', ?, ?, ?, ?, ?, ?, ?)
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
        ts, ts
    ))

    # Audit log
    conn.execute("""
        INSERT INTO communique_audit (com_id, action, old_status, new_status, actor, timestamp)
        VALUES (?, 'CREATE', NULL, 'DRAFT', ?, ?)
    """, (com_id, data.get("author_name", "system"), ts))

    conn.commit()
    conn.close()

    return {"id": com_id, "status": "DRAFT", "created_at": ts}


def get_communique(com_id):
    """Get a single communiqué by ID."""
    conn = get_db()
    row = conn.execute("SELECT * FROM communiques WHERE id = ?", (com_id,)).fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def update_communique(com_id, data):
    """
    Update a communiqué. ONLY allowed if status is DRAFT or REVIEW.
    PUBLISHED/ARCHIVED/REVOKED are IMMUTABLE.
    """
    conn = get_db()
    row = conn.execute("SELECT status FROM communiques WHERE id = ?", (com_id,)).fetchone()
    if not row:
        conn.close()
        return {"error": "Communiqué not found", "code": 404}

    if row["status"] in ("PUBLISHED", "ARCHIVED", "REVOKED"):
        conn.close()
        return {"error": f"Cannot modify communiqué in {row['status']} status. Immutability enforced.", "code": 403}

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
    return {"id": com_id, "updated_at": ts}


def transition_status(com_id, new_status, actor, details=None):
    """
    Transition communiqué status with audit trail.
    Enforces valid transitions.
    """
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
        return {"error": "Communiqué not found", "code": 404}

    old_status = row["status"]
    if new_status not in valid_transitions.get(old_status, []):
        conn.close()
        return {"error": f"Invalid transition: {old_status} → {new_status}", "code": 400}

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


def set_crypto_fields(com_id, content_hash, bundle_hash=None, ledger_id=None, receipt_id=None):
    """Set cryptographic fields on publish. Only works for PUBLISHED status."""
    conn = get_db()
    row = conn.execute("SELECT status FROM communiques WHERE id = ?", (com_id,)).fetchone()
    if not row or row["status"] != "PUBLISHED":
        conn.close()
        return {"error": "Can only set crypto fields on PUBLISHED communiqués"}

    conn.execute("""
        UPDATE communiques SET content_hash=?, bundle_hash=?, ledger_id=?, receipt_id=?, updated_at=?
        WHERE id = ?
    """, (content_hash, bundle_hash, ledger_id, receipt_id, now_iso(), com_id))
    conn.commit()
    conn.close()
    return {"id": com_id, "sealed": True}


def list_communiques(status=None, category=None, limit=20, offset=0):
    """List communiqués with optional filters."""
    conn = get_db()
    query = "SELECT * FROM communiques WHERE 1=1"
    params = []

    if status:
        query += " AND status = ?"
        params.append(status)
    if category:
        query += " AND category = ?"
        params.append(category)

    query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def list_published(limit=20):
    """List published communiqués for public feed."""
    conn = get_db()
    rows = conn.execute("""
        SELECT id, title_de, title_en, title_pt, category, impact_level,
               author_name, author_role, content_hash, receipt_id,
               published_at, created_at
        FROM communiques
        WHERE status = 'PUBLISHED'
        ORDER BY published_at DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_audit_trail(com_id):
    """Get full audit trail for a communiqué."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM communique_audit WHERE com_id = ? ORDER BY timestamp ASC",
        (com_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_stats():
    """Get communiqué statistics."""
    conn = get_db()
    stats = {}
    for status in ["DRAFT", "REVIEW", "PUBLISHED", "ARCHIVED", "REVOKED"]:
        row = conn.execute("SELECT COUNT(*) as c FROM communiques WHERE status = ?", (status,)).fetchone()
        stats[status.lower()] = row["c"]
    stats["total"] = sum(stats.values())
    conn.close()
    return stats


# Initialize on import
init_db()
