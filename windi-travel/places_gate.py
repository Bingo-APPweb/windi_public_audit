"""
places_gate.py — Places Sovereignty Gate v1.0
═══════════════════════════════════════════════
"O que não medimos, não controlamos."

Gate de soberania para Google Places API.
Nunca chamar Places directamente — sempre via gate.

Features:
  - Tier-based rate limiting (FREE=0, MED=1, HIGH=3, TRAVEL=5)
  - Field restrictions (only allowed fields)
  - SQLite cache with TTL per place type
  - Ledger logging for each call
  - Cache-first strategy → sovereignty grows over time

Invariants:
  I1  — No PII stored (only place data)
  I10 — Graceful fallback if Places unavailable
  I11 — Every external call logged in Ledger

Author: Liga IA+H · Kempten 2026
"""

import os
import json
import time
import hashlib
import sqlite3
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

import httpx

log = logging.getLogger("w-places-gate")

# ══════════════════════════════════════════════════════════════════════════════
# Configuration
# ══════════════════════════════════════════════════════════════════════════════

# KEY lives ONLY in .env — NEVER in code, NEVER in git
GOOGLE_PLACES_KEY = os.getenv("GOOGLE_PLACES_KEY", "")
GOOGLE_PLACES_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"

# Ledger for audit trail
LEDGER_URL = os.getenv("LEDGER_URL", "http://localhost:8101/api/receipts")

# Cache database
CACHE_DB_PATH = os.path.join(os.path.dirname(__file__), "places_cache.db")

# ══════════════════════════════════════════════════════════════════════════════
# Tier Limits — calls per request
# ══════════════════════════════════════════════════════════════════════════════

TIER_LIMITS = {
    "FREE": 0,      # No external calls — cache only
    "MED": 1,       # 1 call per request
    "HIGH": 3,      # 3 calls per request
    "TRAVEL": 5,    # 5 calls per request (premium nomads)
    "INTERNAL": 10, # Internal testing
}

# ══════════════════════════════════════════════════════════════════════════════
# Allowed Fields — data minimization
# ══════════════════════════════════════════════════════════════════════════════

ALLOWED_FIELDS = {
    "name",
    "formatted_address",
    "vicinity",
    "geometry",
    "types",
    "opening_hours",
    "rating",
    "user_ratings_total",
    "place_id",
}

# ══════════════════════════════════════════════════════════════════════════════
# Cache TTL per place type (in days)
# ══════════════════════════════════════════════════════════════════════════════

CACHE_TTL_DAYS = {
    "airport": 365,
    "train_station": 365,
    "bus_station": 180,
    "hotel": 30,
    "lodging": 30,
    "restaurant": 7,
    "cafe": 7,
    "bar": 7,
    "museum": 90,
    "tourist_attraction": 90,
    "park": 90,
    "default": 14,
}

# ══════════════════════════════════════════════════════════════════════════════
# Database Setup
# ══════════════════════════════════════════════════════════════════════════════

def init_cache_db():
    """Initialize SQLite cache database."""
    conn = sqlite3.connect(CACHE_DB_PATH, check_same_thread=False)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS places_cache (
            cache_key TEXT PRIMARY KEY,
            place_type TEXT,
            lat REAL,
            lng REAL,
            data TEXT,
            created_at TEXT,
            expires_at TEXT,
            hit_count INTEGER DEFAULT 0
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS call_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            actor TEXT,
            place_type TEXT,
            lat REAL,
            lng REAL,
            cache_hit INTEGER,
            results_count INTEGER,
            ledger_receipt TEXT
        )
    """)

    c.execute("CREATE INDEX IF NOT EXISTS idx_cache_key ON places_cache(cache_key)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_expires ON places_cache(expires_at)")

    conn.commit()
    conn.close()
    log.info(f"[Places Gate] Cache DB initialized: {CACHE_DB_PATH}")


def get_cache_connection() -> sqlite3.Connection:
    """Get SQLite connection."""
    conn = sqlite3.connect(CACHE_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


# ══════════════════════════════════════════════════════════════════════════════
# Cache Operations
# ══════════════════════════════════════════════════════════════════════════════

def make_cache_key(lat: float, lng: float, place_type: str) -> str:
    """Generate cache key from location + type."""
    # Round to ~100m precision for cache grouping
    lat_r = round(lat, 3)
    lng_r = round(lng, 3)
    raw = f"{lat_r}:{lng_r}:{place_type}"
    return hashlib.md5(raw.encode()).hexdigest()[:16]


def get_ttl_days(place_type: str) -> int:
    """Get TTL in days for a place type."""
    return CACHE_TTL_DAYS.get(place_type, CACHE_TTL_DAYS["default"])


def cache_get(cache_key: str) -> Optional[List[dict]]:
    """Get cached places if valid."""
    conn = get_cache_connection()
    c = conn.cursor()

    now = datetime.now(timezone.utc).isoformat()
    c.execute("""
        SELECT data, hit_count FROM places_cache
        WHERE cache_key = ? AND expires_at > ?
    """, (cache_key, now))

    row = c.fetchone()
    if row:
        # Increment hit count
        c.execute("""
            UPDATE places_cache SET hit_count = hit_count + 1
            WHERE cache_key = ?
        """, (cache_key,))
        conn.commit()
        conn.close()

        log.info(f"[Places Gate] Cache HIT: {cache_key} (hits: {row['hit_count'] + 1})")
        return json.loads(row["data"])

    conn.close()
    return None


def cache_set(cache_key: str, place_type: str, lat: float, lng: float, data: List[dict]):
    """Store places in cache."""
    from datetime import timedelta

    conn = get_cache_connection()
    c = conn.cursor()

    now = datetime.now(timezone.utc)
    ttl_days = get_ttl_days(place_type)
    expires = (now + timedelta(days=ttl_days)).isoformat()

    c.execute("""
        INSERT OR REPLACE INTO places_cache
        (cache_key, place_type, lat, lng, data, created_at, expires_at, hit_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, 0)
    """, (cache_key, place_type, lat, lng, json.dumps(data), now.isoformat(), expires))

    conn.commit()
    conn.close()
    log.info(f"[Places Gate] Cache SET: {cache_key} (TTL: {ttl_days} days)")


# ══════════════════════════════════════════════════════════════════════════════
# Field Filtering
# ══════════════════════════════════════════════════════════════════════════════

def filter_place_fields(place: dict) -> dict:
    """Filter place data to allowed fields only."""
    filtered = {}
    for key in ALLOWED_FIELDS:
        if key in place:
            value = place[key]
            # Special handling for nested objects
            if key == "geometry" and isinstance(value, dict):
                filtered["geometry"] = {"location": value.get("location", {})}
            elif key == "opening_hours" and isinstance(value, dict):
                filtered["opening_hours"] = {"open_now": value.get("open_now")}
            else:
                filtered[key] = value
    return filtered


# ══════════════════════════════════════════════════════════════════════════════
# Ledger Logging
# ══════════════════════════════════════════════════════════════════════════════

async def log_to_ledger(
    actor: str,
    place_type: str,
    lat: float,
    lng: float,
    cache_hit: bool,
    results_count: int
) -> Optional[str]:
    """Log Places call to Forensic Ledger."""
    receipt_id = f"WINDI-PLACES-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    payload = {
        "id": receipt_id,
        "actor": actor,
        "app": "windi-travel",
        "doc_name": f"Places Query · {place_type}",
        "doc_type": "api_call",
        "governance_level": "MEDIUM",
        "content_hash": hashlib.sha256(
            f"{lat}:{lng}:{place_type}:{cache_hit}".encode()
        ).hexdigest(),
        "sge_score": 95,
        "note": json.dumps({
            "place_type": place_type,
            "location": f"{round(lat,2)},{round(lng,2)}",
            "cache_hit": cache_hit,
            "results_count": results_count,
            "sovereign_delta": 1 if not cache_hit else 0,
        }),
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.post(LEDGER_URL, json=payload)
            if r.status_code in (200, 201):
                log.info(f"[Places Gate] Ledger sealed: {receipt_id}")
                return receipt_id
    except Exception as e:
        log.warning(f"[Places Gate] Ledger seal failed (non-blocking): {e}")

    return None


def log_call_locally(
    actor: str,
    place_type: str,
    lat: float,
    lng: float,
    cache_hit: bool,
    results_count: int,
    ledger_receipt: str = None
):
    """Log call to local database for analytics."""
    conn = get_cache_connection()
    c = conn.cursor()

    c.execute("""
        INSERT INTO call_log
        (timestamp, actor, place_type, lat, lng, cache_hit, results_count, ledger_receipt)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now(timezone.utc).isoformat(),
        actor,
        place_type,
        lat, lng,
        1 if cache_hit else 0,
        results_count,
        ledger_receipt
    ))

    conn.commit()
    conn.close()


# ══════════════════════════════════════════════════════════════════════════════
# Main Gate Function
# ══════════════════════════════════════════════════════════════════════════════

async def search_places_sovereign(
    place_type: str,
    lat: float,
    lng: float,
    lang: str = "en",
    tier: str = "MED",
    actor: str = "anonymous"
) -> Dict[str, Any]:
    """
    Sovereign Places Search — cache-first, audit-always.

    Returns:
        {
            "places": [...],
            "cache_hit": bool,
            "sovereign_mode": bool,
            "ledger_receipt": str or None
        }
    """
    # Check tier limit
    max_calls = TIER_LIMITS.get(tier.upper(), 0)
    if max_calls == 0 and tier.upper() == "FREE":
        # FREE tier: cache only, no external calls
        pass

    # Generate cache key
    cache_key = make_cache_key(lat, lng, place_type)

    # Try cache first
    cached = cache_get(cache_key)
    if cached is not None:
        # Cache HIT — zero external calls
        receipt = await log_to_ledger(actor, place_type, lat, lng, True, len(cached))
        log_call_locally(actor, place_type, lat, lng, True, len(cached), receipt)

        return {
            "places": cached,
            "cache_hit": True,
            "sovereign_mode": True,  # Data from local cache
            "ledger_receipt": receipt,
        }

    # Cache MISS — check if we can make external call
    if max_calls == 0:
        # No external calls allowed for this tier
        log.info(f"[Places Gate] Tier {tier} cannot make external calls")
        return {
            "places": [],
            "cache_hit": False,
            "sovereign_mode": True,  # Forced sovereignty
            "ledger_receipt": None,
        }

    # Make external call to Google Places
    if not GOOGLE_PLACES_KEY:
        log.warning("[Places Gate] No GOOGLE_PLACES_KEY configured")
        return {
            "places": [],
            "cache_hit": False,
            "sovereign_mode": True,
            "ledger_receipt": None,
        }

    lang_code = {"PT": "pt", "DE": "de", "EN": "en"}.get(lang.upper(), "en")

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(
                GOOGLE_PLACES_URL,
                params={
                    "location": f"{lat},{lng}",
                    "rankby": "distance",
                    "type": place_type,
                    "language": lang_code,
                    "key": GOOGLE_PLACES_KEY,
                }
            )

            if r.status_code != 200:
                log.warning(f"[Places Gate] Google API error: {r.status_code}")
                return {
                    "places": [],
                    "cache_hit": False,
                    "sovereign_mode": True,
                    "ledger_receipt": None,
                }

            results = r.json().get("results", [])[:5]

            # Filter to allowed fields only
            filtered = [filter_place_fields(p) for p in results]

            # Store in cache
            cache_set(cache_key, place_type, lat, lng, filtered)

            # Log to Ledger
            receipt = await log_to_ledger(actor, place_type, lat, lng, False, len(filtered))
            log_call_locally(actor, place_type, lat, lng, False, len(filtered), receipt)

            log.info(f"[Places Gate] External call: {len(filtered)} results → cached")

            return {
                "places": filtered,
                "cache_hit": False,
                "sovereign_mode": False,  # Used external API
                "ledger_receipt": receipt,
            }

    except Exception as e:
        log.warning(f"[Places Gate] External call failed: {e}")
        return {
            "places": [],
            "cache_hit": False,
            "sovereign_mode": True,  # Fallback to sovereignty
            "ledger_receipt": None,
        }


# ══════════════════════════════════════════════════════════════════════════════
# Analytics
# ══════════════════════════════════════════════════════════════════════════════

def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    conn = get_cache_connection()
    c = conn.cursor()

    # Total cached places
    c.execute("SELECT COUNT(*) as total FROM places_cache")
    total = c.fetchone()["total"]

    # Total hits
    c.execute("SELECT SUM(hit_count) as hits FROM places_cache")
    hits = c.fetchone()["hits"] or 0

    # Call log stats
    c.execute("SELECT COUNT(*) as calls, SUM(cache_hit) as cache_hits FROM call_log")
    row = c.fetchone()
    total_calls = row["calls"] or 0
    cache_hits = row["cache_hits"] or 0

    # Top cached locations
    c.execute("""
        SELECT place_type, COUNT(*) as count
        FROM places_cache
        GROUP BY place_type
        ORDER BY count DESC
        LIMIT 5
    """)
    top_types = [{"type": r["place_type"], "count": r["count"]} for r in c.fetchall()]

    conn.close()

    hit_rate = (cache_hits / total_calls * 100) if total_calls > 0 else 0

    return {
        "total_cached_queries": total,
        "total_cache_hits": hits,
        "total_api_calls": total_calls,
        "cache_hit_rate": f"{hit_rate:.1f}%",
        "sovereignty_score": f"{hit_rate:.0f}%",
        "top_place_types": top_types,
    }


# ══════════════════════════════════════════════════════════════════════════════
# Initialize on import
# ══════════════════════════════════════════════════════════════════════════════

init_cache_db()
