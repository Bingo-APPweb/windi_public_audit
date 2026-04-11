"""
W-DEV-API-001 Database Schema
SQLite with WAL mode for concurrent reads
"""

import sqlite3
import os
from datetime import datetime, timezone

DB_PATH = os.environ.get("WDEV_DB_PATH", "/opt/windi/data/wdev_api.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    """Initialize all tables"""
    conn = get_conn()

    # ── API Keys ─────────────────────────────────────────
    # Stores hashed keys only (SHA-256)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            key_id          TEXT PRIMARY KEY,
            key_hash        TEXT NOT NULL UNIQUE,
            environment     TEXT DEFAULT 'live',
            tier            TEXT DEFAULT 'SEED',
            status          TEXT DEFAULT 'pending_approval',
            scopes          TEXT DEFAULT '["seal:create","verify:read"]',
            owner_email     TEXT,
            owner_name      TEXT,
            owner_did       TEXT,
            note            TEXT,
            approved_by     TEXT,
            approved_at     TEXT,
            last_used_at    TEXT,
            request_count   INTEGER DEFAULT 0,
            created_at      TEXT NOT NULL,
            expires_at      TEXT
        )
    """)

    # ── Artifacts ────────────────────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS artifacts (
            artifact_id     TEXT PRIMARY KEY,
            type            TEXT NOT NULL,
            title           TEXT,
            did             TEXT NOT NULL,
            mime_type       TEXT,
            sha256          TEXT NOT NULL,
            size_bytes      INTEGER,
            storage_key     TEXT,
            status          TEXT DEFAULT 'created',
            metadata        TEXT,
            created_by_key  TEXT,
            created_at      TEXT NOT NULL,
            FOREIGN KEY (created_by_key) REFERENCES api_keys(key_id)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_artifacts_sha256 ON artifacts(sha256)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_artifacts_did ON artifacts(did)")

    # ── Seals ────────────────────────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS seals (
            seal_id             TEXT PRIMARY KEY,
            artifact_id         TEXT NOT NULL,
            did                 TEXT NOT NULL,
            seal_type           TEXT DEFAULT 'evidence',
            status              TEXT DEFAULT 'pending',
            confirmed_by_human  INTEGER DEFAULT 0,
            ledger_entry_id     TEXT,
            receipt_id          TEXT,
            verify_url          TEXT,
            metadata            TEXT,
            sealed_at           TEXT,
            created_by_key      TEXT,
            created_at          TEXT NOT NULL,
            FOREIGN KEY (artifact_id) REFERENCES artifacts(artifact_id),
            FOREIGN KEY (created_by_key) REFERENCES api_keys(key_id)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_seals_receipt ON seals(receipt_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_seals_artifact ON seals(artifact_id)")

    # ── Receipts (denormalized for fast lookup) ──────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS receipts (
            receipt_id      TEXT PRIMARY KEY,
            artifact_id     TEXT,
            seal_id         TEXT,
            ledger_entry_id TEXT,
            did             TEXT,
            sha256          TEXT,
            verify_url      TEXT,
            status          TEXT DEFAULT 'valid',
            created_at      TEXT NOT NULL,
            FOREIGN KEY (artifact_id) REFERENCES artifacts(artifact_id),
            FOREIGN KEY (seal_id) REFERENCES seals(seal_id)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_receipts_sha256 ON receipts(sha256)")

    # ── Idempotency Keys ─────────────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS idempotency_keys (
            idempotency_key TEXT PRIMARY KEY,
            key_id          TEXT NOT NULL,
            endpoint        TEXT NOT NULL,
            response        TEXT,
            created_at      TEXT NOT NULL,
            expires_at      TEXT NOT NULL
        )
    """)

    # ── Audit Log ────────────────────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp       TEXT NOT NULL,
            key_id          TEXT,
            endpoint        TEXT,
            method          TEXT,
            request_id      TEXT,
            status_code     INTEGER,
            ip_address      TEXT,
            user_agent      TEXT,
            response_time   REAL
        )
    """)

    # ── Key Requests (pending approval) ──────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS key_requests (
            request_id      TEXT PRIMARY KEY,
            email           TEXT NOT NULL,
            name            TEXT,
            company         TEXT,
            use_case        TEXT,
            tier_requested  TEXT DEFAULT 'SEED',
            status          TEXT DEFAULT 'pending',
            reviewed_by     TEXT,
            reviewed_at     TEXT,
            key_id          TEXT,
            created_at      TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()
    print(f"[W-DEV-API-001] DB initialized: {DB_PATH}")

def now_iso():
    return datetime.now(timezone.utc).isoformat()

if __name__ == "__main__":
    init_db()
