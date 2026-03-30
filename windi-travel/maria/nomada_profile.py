"""
nomada_profile.py — MARIA Memory Layer
───────────────────────────────────────
Stores and retrieves nomada preferences per DID.
"MARIA remembers, but never intrudes."

Database: maria_memory.db (SQLite)
Schema:
  - nomadas:     did, lang, created_at
  - preferences: did, key, value, updated_at
  - interactions: did, request_id, intent_type, place, rating, timestamp

Invariants:
  I1 — No PII stored (only DID + preferences)
  I11 — Interactions can be sealed in Ledger

Author: Liga IA+H · Kempten 2026
"""

import sqlite3
import os
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import logging

log = logging.getLogger("w-maria-memory")

# ── Database Path ────────────────────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), "maria_memory.db")


def get_connection() -> sqlite3.Connection:
    """Get SQLite connection with row factory."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database schema if not exists."""
    conn = get_connection()
    c = conn.cursor()

    # Nomadas — base profile
    c.execute("""
        CREATE TABLE IF NOT EXISTS nomadas (
            did TEXT PRIMARY KEY,
            lang TEXT DEFAULT 'EN',
            name TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Preferences — key-value store per DID
    c.execute("""
        CREATE TABLE IF NOT EXISTS preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            did TEXT NOT NULL,
            key TEXT NOT NULL,
            value TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(did, key)
        )
    """)

    # Interactions — history of MARIA recommendations
    c.execute("""
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            did TEXT NOT NULL,
            request_id TEXT NOT NULL,
            intent_type TEXT,
            place_name TEXT,
            rating INTEGER,
            feedback TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Indexes for performance
    c.execute("CREATE INDEX IF NOT EXISTS idx_interactions_did ON interactions(did)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_preferences_did ON preferences(did)")

    conn.commit()
    conn.close()
    log.info(f"[MARIA Memory] Database initialized: {DB_PATH}")


# ── Nomada Profile ───────────────────────────────────────────────────────────

def get_or_create_nomada(did: str, lang: str = "EN", name: str = None) -> Dict[str, Any]:
    """
    Get nomada profile or create if not exists.
    Returns dict with profile data.
    """
    if not did:
        return {"did": None, "lang": lang, "name": None, "is_new": True}

    conn = get_connection()
    c = conn.cursor()

    # Try to get existing
    c.execute("SELECT * FROM nomadas WHERE did = ?", (did,))
    row = c.fetchone()

    if row:
        conn.close()
        return {
            "did": row["did"],
            "lang": row["lang"],
            "name": row["name"],
            "created_at": row["created_at"],
            "is_new": False
        }

    # Create new nomada
    created_at = datetime.now(timezone.utc).isoformat()
    c.execute(
        "INSERT INTO nomadas (did, lang, name, created_at) VALUES (?, ?, ?, ?)",
        (did, lang, name, created_at)
    )
    conn.commit()
    conn.close()

    log.info(f"[MARIA Memory] New nomada created: {did[:8]}...")
    return {
        "did": did,
        "lang": lang,
        "name": name,
        "created_at": created_at,
        "is_new": True
    }


def update_nomada_lang(did: str, lang: str):
    """Update nomada's preferred language."""
    if not did:
        return
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE nomadas SET lang = ? WHERE did = ?", (lang, did))
    conn.commit()
    conn.close()


# ── Preferences ──────────────────────────────────────────────────────────────

def set_preference(did: str, key: str, value: Any):
    """Set a preference for a nomada."""
    if not did:
        return
    conn = get_connection()
    c = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()
    val_str = json.dumps(value) if not isinstance(value, str) else value
    c.execute("""
        INSERT INTO preferences (did, key, value, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(did, key) DO UPDATE SET value = ?, updated_at = ?
    """, (did, key, val_str, now, val_str, now))
    conn.commit()
    conn.close()


def get_preference(did: str, key: str, default: Any = None) -> Any:
    """Get a preference value."""
    if not did:
        return default
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT value FROM preferences WHERE did = ? AND key = ?", (did, key))
    row = c.fetchone()
    conn.close()
    if row:
        try:
            return json.loads(row["value"])
        except:
            return row["value"]
    return default


def get_all_preferences(did: str) -> Dict[str, Any]:
    """Get all preferences for a nomada."""
    if not did:
        return {}
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT key, value FROM preferences WHERE did = ?", (did,))
    rows = c.fetchall()
    conn.close()
    prefs = {}
    for row in rows:
        try:
            prefs[row["key"]] = json.loads(row["value"])
        except:
            prefs[row["key"]] = row["value"]
    return prefs


# ── Interactions ─────────────────────────────────────────────────────────────

def log_interaction(
    did: str,
    request_id: str,
    intent_type: str,
    place_name: str,
    rating: int = None,
    feedback: str = None
):
    """Log an interaction for memory and learning."""
    if not did:
        return
    conn = get_connection()
    c = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()
    c.execute("""
        INSERT INTO interactions (did, request_id, intent_type, place_name, rating, feedback, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (did, request_id, intent_type, place_name, rating, feedback, now))
    conn.commit()
    conn.close()


def get_recent_interactions(did: str, limit: int = 10) -> list:
    """Get recent interactions for context."""
    if not did:
        return []
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT intent_type, place_name, rating, timestamp
        FROM interactions
        WHERE did = ?
        ORDER BY timestamp DESC
        LIMIT ?
    """, (did, limit))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_favorite_types(did: str) -> list:
    """Get most frequent intent types for a nomada."""
    if not did:
        return []
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT intent_type, COUNT(*) as count
        FROM interactions
        WHERE did = ? AND rating >= 4
        GROUP BY intent_type
        ORDER BY count DESC
        LIMIT 3
    """, (did,))
    rows = c.fetchall()
    conn.close()
    return [row["intent_type"] for row in rows]


# ── Context Enrichment ───────────────────────────────────────────────────────

def enrich_context_with_memory(did: str, context: dict) -> dict:
    """
    Enrich context with nomada's memory.
    Used by booking_router to personalize recommendations.
    """
    if not did:
        return context

    profile = get_or_create_nomada(did)
    recent = get_recent_interactions(did, limit=5)
    favorites = get_favorite_types(did)
    prefs = get_all_preferences(did)

    context["nomada"] = {
        "is_new": profile.get("is_new", True),
        "name": profile.get("name"),
        "preferred_lang": profile.get("lang", "EN"),
        "recent_visits": len(recent),
        "favorites": favorites,
        "quiet_preference": prefs.get("quiet", False),
        "family_mode": prefs.get("family", False),
    }

    # Add recent places to avoid repetition
    if recent:
        context["nomada"]["recent_places"] = [r["place_name"] for r in recent[:3]]

    return context


# ── Initialize on import ─────────────────────────────────────────────────────
init_db()
