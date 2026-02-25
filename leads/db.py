"""
WINDI ID Genesis — Database Layer (SQLite)
Three Dragons Protocol v1.1 · I1-I9 Active

Schema designed for:
- Lead capture + status tracking
- WINDI ID provisioning
- PII separation (revocable fields vs. immutable governance fields)
- DSGVO Art.17 compliance: PII can be NULLed, governance hashes remain
"""
import sqlite3
import os
from datetime import datetime, timezone
from config import DB_PATH

def get_db():
    """Get database connection with Turbo PRAGMAs for high throughput."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Turbo PRAGMAs - Autarquia Máxima
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-8000")       # 8MB cache
    conn.execute("PRAGMA mmap_size=268435456")    # 256MB mmap
    conn.execute("PRAGMA busy_timeout=5000")      # 5s timeout
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    """Initialize database schema."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db()
    conn.executescript("""
        -- ═══ LEADS TABLE ═══
        -- PII fields (name, email, company) are revocable under DSGVO
        -- Governance fields (lead_id, windi_id, status, timestamps) are immutable
        CREATE TABLE IF NOT EXISTS leads (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id         TEXT UNIQUE NOT NULL,
            name            TEXT,           -- PII: revocable
            email           TEXT,           -- PII: revocable
            company         TEXT,           -- PII: revocable
            interest        TEXT DEFAULT 'free',
            source          TEXT DEFAULT 'landing',
            lang            TEXT DEFAULT 'de',
            status          TEXT DEFAULT 'PENDING',
            -- WINDI ID fields (populated on APPROVE)
            windi_id        TEXT UNIQUE,
            activation_token TEXT UNIQUE,
            public_key      TEXT,           -- stored on ACTIVATE
            key_fingerprint TEXT,           -- stored on ACTIVATE
            key_type        TEXT DEFAULT 'non-custodial',
            -- Timestamps
            created_at      TEXT NOT NULL,
            approved_at     TEXT,
            activated_at    TEXT,
            revoked_at      TEXT,
            -- Metadata
            approved_by     TEXT,
            ip_address      TEXT,
            notes           TEXT
        );

        -- ═══ RATE LIMITING ═══
        CREATE TABLE IF NOT EXISTS rate_limits (
            ip_address      TEXT NOT NULL,
            endpoint        TEXT NOT NULL,
            timestamp       TEXT NOT NULL
        );

        -- ═══ INDEXES ═══
        CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
        CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);
        CREATE INDEX IF NOT EXISTS idx_leads_windi_id ON leads(windi_id);
        CREATE INDEX IF NOT EXISTS idx_leads_token ON leads(activation_token);
        CREATE INDEX IF NOT EXISTS idx_rate_ip ON rate_limits(ip_address, endpoint);
    """)
    conn.commit()
    conn.close()

# ── CRUD Operations ──

def create_lead(lead_id: str, name: str, email: str, company: str = "",
                interest: str = "free", source: str = "landing",
                lang: str = "de", ip_address: str = "") -> dict:
    """Create a new lead with PENDING status."""
    conn = get_db()
    now = datetime.now(timezone.utc).isoformat()
    try:
        conn.execute("""
            INSERT INTO leads (lead_id, name, email, company, interest, source, lang,
                              status, created_at, ip_address)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'PENDING', ?, ?)
        """, (lead_id, name, email, company, interest, source, lang, now, ip_address))
        conn.commit()
        return {"lead_id": lead_id, "status": "PENDING", "created_at": now}
    except sqlite3.IntegrityError:
        return {"error": "Lead already exists", "lead_id": lead_id}
    finally:
        conn.close()

def get_lead_by_id(lead_id: str) -> dict | None:
    conn = get_db()
    row = conn.execute("SELECT * FROM leads WHERE lead_id = ?", (lead_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_lead_by_token(token: str) -> dict | None:
    conn = get_db()
    row = conn.execute("SELECT * FROM leads WHERE activation_token = ?", (token,)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_leads_by_status(status: str = None) -> list:
    conn = get_db()
    if status:
        rows = conn.execute(
            "SELECT * FROM leads WHERE status = ? ORDER BY created_at DESC", (status,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM leads ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def approve_lead(lead_id: str, windi_id: str, activation_token: str,
                 approved_by: str = "admin") -> bool:
    """
    I9-GUARDED: This function MUST only be called after explicit human approval.
    Sets status to APPROVED and generates WINDI ID + activation token.
    """
    conn = get_db()
    now = datetime.now(timezone.utc).isoformat()
    cursor = conn.execute("""
        UPDATE leads
        SET status = 'APPROVED',
            windi_id = ?,
            activation_token = ?,
            approved_at = ?,
            approved_by = ?
        WHERE lead_id = ? AND status = 'PENDING'
    """, (windi_id, activation_token, now, approved_by, lead_id))
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success

def activate_lead(token: str, public_key: str, key_fingerprint: str) -> dict | None:
    """Activate a lead: store public key, mark as ACTIVE."""
    conn = get_db()
    now = datetime.now(timezone.utc).isoformat()
    cursor = conn.execute("""
        UPDATE leads
        SET status = 'ACTIVE',
            public_key = ?,
            key_fingerprint = ?,
            activated_at = ?
        WHERE activation_token = ? AND status = 'APPROVED'
    """, (public_key, key_fingerprint, now, token))
    conn.commit()
    if cursor.rowcount > 0:
        lead = get_lead_by_token(token)
        conn.close()
        return lead
    conn.close()
    return None

def revoke_lead(lead_id: str) -> bool:
    """
    DSGVO-compliant revocation: NULL PII fields, keep governance data.
    The hash chain in the ledger remains intact (hashes are not PII).
    """
    conn = get_db()
    now = datetime.now(timezone.utc).isoformat()
    cursor = conn.execute("""
        UPDATE leads
        SET status = 'REVOKED',
            name = NULL,
            email = NULL,
            company = NULL,
            public_key = NULL,
            activation_token = NULL,
            revoked_at = ?,
            notes = COALESCE(notes, '') || ' [REVOKED: PII cleared per DSGVO Art.17]'
        WHERE lead_id = ? AND status != 'REVOKED'
    """, (now, lead_id))
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success

def get_lead_stats() -> dict:
    conn = get_db()
    rows = conn.execute("""
        SELECT status, COUNT(*) as count FROM leads GROUP BY status
    """).fetchall()
    conn.close()
    stats = {r["status"]: r["count"] for r in rows}
    stats["total"] = sum(stats.values())
    return stats

# ── Rate Limiting ──

def check_rate_limit(ip: str, endpoint: str, max_per_hour: int = 10) -> bool:
    """Returns True if request is allowed, False if rate limited."""
    conn = get_db()
    one_hour_ago = datetime.now(timezone.utc).replace(
        minute=0, second=0, microsecond=0
    ).isoformat()
    count = conn.execute("""
        SELECT COUNT(*) FROM rate_limits
        WHERE ip_address = ? AND endpoint = ? AND timestamp > ?
    """, (ip, endpoint, one_hour_ago)).fetchone()[0]
    if count >= max_per_hour:
        conn.close()
        return False
    conn.execute("""
        INSERT INTO rate_limits (ip_address, endpoint, timestamp)
        VALUES (?, ?, ?)
    """, (ip, endpoint, datetime.now(timezone.utc).isoformat()))
    conn.commit()
    conn.close()
    return True

def cleanup_rate_limits():
    """Remove old rate limit entries."""
    conn = get_db()
    two_hours_ago = datetime.now(timezone.utc).isoformat()[:13] + ":00:00+00:00"
    conn.execute("DELETE FROM rate_limits WHERE timestamp < ?", (two_hours_ago,))
    conn.commit()
    conn.close()

# Initialize on import
init_db()
