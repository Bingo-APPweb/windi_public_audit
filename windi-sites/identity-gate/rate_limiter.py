"""
§246-D4 · DID-Based Rate Limiter
Sovereign Capacity Governance — Not Just Anti-Spam

Liga IA+H · Kempten, Bavaria · 2026-05-07

Constitutional Principles:
- DID-first (no domain fallback)
- Fail-closed (DB error = REJECT)
- PHO override receipt-bound
- T7e never bypassable
- ALLOW/DEFER/REJECT semantic distinction

"Throughput without governance becomes invisible delegation."
"""

import os
import sqlite3
import time
import hashlib
import logging
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List, Tuple
from threading import Lock

log = logging.getLogger("windi.rate_limiter")

# ═══════════════════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════════════════

DB_PATH = os.environ.get("RATE_LIMIT_DB", "/opt/windi/data/mail_rate_limits.db")
LEDGER_URL = os.environ.get("LEDGER_URL", "http://localhost:8101")

# Window definitions (seconds)
WINDOW_BURST = 60          # 1 minute
WINDOW_HOURLY = 3600       # 1 hour
WINDOW_DAILY = 86400       # 24 hours

# Tier limits: (burst, hourly, daily)
TIER_LIMITS = {
    "LOW":  (5, 20, 50),
    "MED":  (15, 100, 500),
    "HIGH": (50, 500, 2000),
}

DEFAULT_TIER = "LOW"

# PHO Override constraints
MAX_OVERRIDE_MULTIPLIER = 10  # Max 10x tier limit
MAX_OVERRIDE_HOURS = 72       # Max 72 hours


# ═══════════════════════════════════════════════════════════════════════════════
# Result Types — ALLOW/DEFER/REJECT Semantic Distinction
# ═══════════════════════════════════════════════════════════════════════════════

class RateLimitAction(Enum):
    """
    Three-state result with constitutional semantics:

    ALLOW  = Proceed normally
    DEFER  = Temporary throttling, recoverable continuity
    REJECT = Constitutional rupture, permanent until reset/intervention
    """
    ALLOW = "allow"
    DEFER = "defer"
    REJECT = "reject"


@dataclass
class RateLimitResult:
    """
    Result of rate limit check with full context for receipts.
    """
    action: RateLimitAction
    reason: str
    window: Optional[str] = None        # 'burst' | 'hourly' | 'daily' | None
    count: int = 0                      # Current count in window
    limit: int = 0                      # Tier limit for window
    tier: str = DEFAULT_TIER
    retry_after: int = 0                # Seconds until retry allowed
    constitutional: bool = False        # True if REJECT is constitutional/abuse
    receipt_type: str = "RATE_LIMIT_ALLOW"

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["action"] = self.action.value
        return d


# ═══════════════════════════════════════════════════════════════════════════════
# Database Schema — Future-Proof for DID Reputation
# ═══════════════════════════════════════════════════════════════════════════════

SCHEMA_SQL = """
-- Rate counters (D4.4)
CREATE TABLE IF NOT EXISTS rate_counters (
    did TEXT NOT NULL,
    window TEXT NOT NULL,           -- 'burst' | 'hourly' | 'daily'
    window_start INTEGER NOT NULL,  -- Unix timestamp of window start
    count INTEGER DEFAULT 0,
    PRIMARY KEY (did, window, window_start)
);

CREATE INDEX IF NOT EXISTS idx_rate_counters_did ON rate_counters(did);
CREATE INDEX IF NOT EXISTS idx_rate_counters_window ON rate_counters(window, window_start);

-- Rate overrides (D4.9)
CREATE TABLE IF NOT EXISTS rate_overrides (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    did TEXT NOT NULL,
    window TEXT NOT NULL,           -- 'burst' | 'hourly' | 'daily'
    new_limit INTEGER NOT NULL,
    created_at INTEGER NOT NULL,
    expires_at INTEGER NOT NULL,
    pho_actor TEXT NOT NULL,        -- DID or email of PHO
    reason TEXT NOT NULL,
    receipt_id TEXT,                -- Ledger receipt for audit
    status TEXT DEFAULT 'active',   -- 'active' | 'expired' | 'revoked'
    UNIQUE(did, window, created_at)
);

CREATE INDEX IF NOT EXISTS idx_rate_overrides_did ON rate_overrides(did);
CREATE INDEX IF NOT EXISTS idx_rate_overrides_expires ON rate_overrides(expires_at);

-- DID Reputation (future-proof, D4 does not populate)
-- Schema ready for future sprint W-MAILBOX-REPUTATION-001
CREATE TABLE IF NOT EXISTS did_reputation (
    did TEXT PRIMARY KEY,
    trust_score REAL DEFAULT 0.5,       -- 0.0 to 1.0
    governance_tier TEXT DEFAULT 'LOW', -- LOW | MED | HIGH
    anomaly_flags TEXT DEFAULT '[]',    -- JSON array of flags
    last_violation_at INTEGER,          -- Unix timestamp
    total_violations INTEGER DEFAULT 0,
    total_emails_sent INTEGER DEFAULT 0,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

-- Rate events log (for audit trail)
CREATE TABLE IF NOT EXISTS rate_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    did TEXT NOT NULL,
    event_type TEXT NOT NULL,       -- ALLOW | DEFER | REJECT | OVERRIDE | BOUNCE_STORM
    window TEXT,
    count_at_event INTEGER,
    limit_at_event INTEGER,
    tier TEXT,
    retry_after INTEGER,
    constitutional INTEGER DEFAULT 0,
    reason TEXT,
    receipt_id TEXT,
    created_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_rate_events_did ON rate_events(did);
CREATE INDEX IF NOT EXISTS idx_rate_events_type ON rate_events(event_type);
CREATE INDEX IF NOT EXISTS idx_rate_events_created ON rate_events(created_at);
"""


# ═══════════════════════════════════════════════════════════════════════════════
# Rate Limiter Class
# ═══════════════════════════════════════════════════════════════════════════════

class RateLimiter:
    """
    DID-based rate limiter with sovereign capacity governance.

    Features:
    - Three windows: burst (1min), hourly (1h), daily (24h)
    - Three tiers: LOW, MED, HIGH with configurable limits
    - ALLOW/DEFER/REJECT semantic distinction
    - PHO override with receipts
    - Fail-closed: DB error = REJECT (constitutional)
    - Future-proof schema for DID reputation
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._lock = Lock()
        self._init_db()

    def _init_db(self):
        """Initialize database with schema."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.executescript(SCHEMA_SQL)
            conn.commit()
            conn.close()
            log.info(f"[D4] Rate limiter DB initialized: {self.db_path}")
        except Exception as e:
            log.error(f"[D4] Failed to init DB: {e}")
            # Fail-closed: will reject all requests if DB not available

    def _conn(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path, timeout=5.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _get_window_start(self, window: str) -> int:
        """Get the start timestamp for a window (discrete, not sliding)."""
        now = int(time.time())

        if window == "burst":
            # Start of current minute
            return now - (now % WINDOW_BURST)
        elif window == "hourly":
            # Start of current hour
            return now - (now % WINDOW_HOURLY)
        elif window == "daily":
            # Midnight UTC of current day
            dt = datetime.now(timezone.utc)
            midnight = dt.replace(hour=0, minute=0, second=0, microsecond=0)
            return int(midnight.timestamp())
        else:
            return now

    def _get_tier_limit(self, tier: str, window: str) -> int:
        """Get limit for tier and window."""
        limits = TIER_LIMITS.get(tier.upper(), TIER_LIMITS[DEFAULT_TIER])
        idx = {"burst": 0, "hourly": 1, "daily": 2}.get(window, 0)
        return limits[idx]

    def _get_count(self, conn: sqlite3.Connection, did: str, window: str, window_start: int) -> int:
        """Get current count for DID in window."""
        row = conn.execute(
            "SELECT COALESCE(SUM(count), 0) as total FROM rate_counters "
            "WHERE did = ? AND window = ? AND window_start >= ?",
            (did, window, window_start)
        ).fetchone()
        return row["total"] if row else 0

    def _increment_count(self, conn: sqlite3.Connection, did: str, window: str, window_start: int):
        """Increment count for DID in window (atomic)."""
        conn.execute(
            "INSERT INTO rate_counters (did, window, window_start, count) "
            "VALUES (?, ?, ?, 1) "
            "ON CONFLICT (did, window, window_start) DO UPDATE SET count = count + 1",
            (did, window, window_start)
        )

    def _get_active_override(self, conn: sqlite3.Connection, did: str, window: str) -> Optional[Dict]:
        """Get active override for DID and window."""
        now = int(time.time())
        row = conn.execute(
            "SELECT * FROM rate_overrides "
            "WHERE did = ? AND window = ? AND expires_at > ? AND status = 'active' "
            "ORDER BY created_at DESC LIMIT 1",
            (did, window, now)
        ).fetchone()
        return dict(row) if row else None

    def _seconds_until_midnight_utc(self) -> int:
        """Calculate seconds until midnight UTC (for daily REJECT retry_after)."""
        now = datetime.now(timezone.utc)
        midnight = (now + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        return int((midnight - now).total_seconds())

    def _log_event(self, conn: sqlite3.Connection, result: RateLimitResult, did: str, receipt_id: str = None):
        """Log rate event for audit trail."""
        conn.execute(
            "INSERT INTO rate_events "
            "(did, event_type, window, count_at_event, limit_at_event, tier, "
            "retry_after, constitutional, reason, receipt_id, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                did,
                result.action.value.upper(),
                result.window,
                result.count,
                result.limit,
                result.tier,
                result.retry_after,
                1 if result.constitutional else 0,
                result.reason,
                receipt_id,
                int(time.time())
            )
        )

    def check_rate(self, did: str, tier: str = DEFAULT_TIER) -> RateLimitResult:
        """
        Check rate limit for DID.

        Returns:
            RateLimitResult with action (ALLOW/DEFER/REJECT), reason, and context

        Fail-closed: Any error results in REJECT with constitutional=True
        """
        if not did:
            return RateLimitResult(
                action=RateLimitAction.REJECT,
                reason="missing_did",
                constitutional=True,
                receipt_type="RATE_LIMIT_REJECT"
            )

        tier = tier.upper() if tier else DEFAULT_TIER
        if tier not in TIER_LIMITS:
            tier = DEFAULT_TIER

        try:
            with self._lock:
                conn = self._conn()
                try:
                    # Check each window in order: burst -> hourly -> daily
                    for window, window_seconds, retry_base in [
                        ("burst", WINDOW_BURST, 60),
                        ("hourly", WINDOW_HOURLY, 1800),
                        ("daily", WINDOW_DAILY, None)  # Special: midnight UTC
                    ]:
                        window_start = self._get_window_start(window)
                        count = self._get_count(conn, did, window, window_start)

                        # Check for active override
                        override = self._get_active_override(conn, did, window)
                        if override:
                            limit = override["new_limit"]
                        else:
                            limit = self._get_tier_limit(tier, window)

                        if count >= limit:
                            # Limit exceeded
                            if window == "daily":
                                # Daily = REJECT (constitutional rupture until midnight)
                                result = RateLimitResult(
                                    action=RateLimitAction.REJECT,
                                    reason="daily_quota_exhausted",
                                    window=window,
                                    count=count,
                                    limit=limit,
                                    tier=tier,
                                    retry_after=self._seconds_until_midnight_utc(),
                                    constitutional=False,  # Recoverable at midnight
                                    receipt_type="RATE_LIMIT_REJECT"
                                )
                            else:
                                # Burst/hourly = DEFER (temporary throttling)
                                result = RateLimitResult(
                                    action=RateLimitAction.DEFER,
                                    reason=f"{window}_limit_reached",
                                    window=window,
                                    count=count,
                                    limit=limit,
                                    tier=tier,
                                    retry_after=retry_base,
                                    constitutional=False,
                                    receipt_type="RATE_LIMIT_DEFER"
                                )

                            self._log_event(conn, result, did)
                            conn.commit()
                            return result

                    # All windows OK - increment counters and allow
                    now_ts = int(time.time())
                    for window in ["burst", "hourly", "daily"]:
                        window_start = self._get_window_start(window)
                        self._increment_count(conn, did, window, window_start)

                    conn.commit()

                    return RateLimitResult(
                        action=RateLimitAction.ALLOW,
                        reason="within_limits",
                        tier=tier,
                        receipt_type="RATE_LIMIT_ALLOW"
                    )

                finally:
                    conn.close()

        except Exception as e:
            # Fail-closed: DB error = REJECT (constitutional)
            log.error(f"[D4] Rate check failed for {did}: {e}")
            return RateLimitResult(
                action=RateLimitAction.REJECT,
                reason=f"db_error: {str(e)[:50]}",
                constitutional=True,
                receipt_type="RATE_LIMIT_REJECT"
            )

    def apply_override(
        self,
        did: str,
        window: str,
        new_limit: int,
        duration_hours: int,
        pho_actor: str,
        reason: str,
        tier: str = DEFAULT_TIER
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Apply PHO override for DID.

        Args:
            did: Target DID
            window: 'burst' | 'hourly' | 'daily'
            new_limit: New limit (max 10x tier)
            duration_hours: Hours until expiry (max 72)
            pho_actor: DID/email of PHO applying override
            reason: Justification
            tier: Current tier (for max limit calculation)

        Returns:
            (success, message, receipt_id)
        """
        tier = tier.upper() if tier else DEFAULT_TIER
        base_limit = self._get_tier_limit(tier, window)
        max_limit = base_limit * MAX_OVERRIDE_MULTIPLIER

        # Validate constraints
        if new_limit > max_limit:
            return False, f"new_limit exceeds max ({max_limit})", None

        if duration_hours > MAX_OVERRIDE_HOURS:
            return False, f"duration exceeds max ({MAX_OVERRIDE_HOURS}h)", None

        if window not in ["burst", "hourly", "daily"]:
            return False, f"invalid window: {window}", None

        try:
            now = int(time.time())
            expires_at = now + (duration_hours * 3600)

            # Generate receipt ID
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
            hash_input = f"OVERRIDE-{did}-{window}-{timestamp}"
            hash8 = hashlib.sha256(hash_input.encode()).hexdigest()[:8].upper()
            receipt_id = f"WINDI-MAILBOX-RATE-OVERRIDE-{timestamp}-{hash8}"

            with self._lock:
                conn = self._conn()
                try:
                    # Insert override
                    conn.execute(
                        "INSERT INTO rate_overrides "
                        "(did, window, new_limit, created_at, expires_at, pho_actor, reason, receipt_id, status) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active')",
                        (did, window, new_limit, now, expires_at, pho_actor, reason, receipt_id)
                    )

                    # Log event
                    result = RateLimitResult(
                        action=RateLimitAction.ALLOW,
                        reason="pho_override_applied",
                        window=window,
                        limit=new_limit,
                        tier=tier,
                        receipt_type="RATE_LIMIT_OVERRIDE"
                    )
                    self._log_event(conn, result, did, receipt_id)

                    conn.commit()

                    log.info(f"[D4] PHO override applied: {did} {window}={new_limit} by {pho_actor}")
                    return True, "override_applied", receipt_id

                finally:
                    conn.close()

        except Exception as e:
            log.error(f"[D4] Override failed: {e}")
            return False, f"db_error: {str(e)[:50]}", None

    def get_status(self, did: str, tier: str = DEFAULT_TIER) -> Dict[str, Any]:
        """Get current rate limit status for DID."""
        tier = tier.upper() if tier else DEFAULT_TIER

        try:
            conn = self._conn()
            try:
                status = {
                    "did": did,
                    "tier": tier,
                    "windows": {},
                    "overrides": [],
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

                for window in ["burst", "hourly", "daily"]:
                    window_start = self._get_window_start(window)
                    count = self._get_count(conn, did, window, window_start)

                    override = self._get_active_override(conn, did, window)
                    if override:
                        limit = override["new_limit"]
                        status["overrides"].append({
                            "window": window,
                            "new_limit": limit,
                            "expires_at": override["expires_at"],
                            "pho_actor": override["pho_actor"]
                        })
                    else:
                        limit = self._get_tier_limit(tier, window)

                    status["windows"][window] = {
                        "count": count,
                        "limit": limit,
                        "remaining": max(0, limit - count),
                        "window_start": window_start
                    }

                return status

            finally:
                conn.close()

        except Exception as e:
            return {"error": str(e), "did": did}

    def cleanup_old_records(self, max_age_seconds: int = 86400):
        """
        Cleanup old rate counters and expire overrides.
        Should be called periodically (e.g., every 5 minutes).
        """
        try:
            cutoff = int(time.time()) - max_age_seconds
            now = int(time.time())

            conn = self._conn()
            try:
                # Delete old counters
                deleted_counters = conn.execute(
                    "DELETE FROM rate_counters WHERE window_start < ?",
                    (cutoff,)
                ).rowcount

                # Expire old overrides
                expired_overrides = conn.execute(
                    "UPDATE rate_overrides SET status = 'expired' "
                    "WHERE expires_at < ? AND status = 'active'",
                    (now,)
                ).rowcount

                conn.commit()

                if deleted_counters > 0 or expired_overrides > 0:
                    log.info(f"[D4] Cleanup: {deleted_counters} counters, {expired_overrides} overrides expired")

                return {"deleted_counters": deleted_counters, "expired_overrides": expired_overrides}

            finally:
                conn.close()

        except Exception as e:
            log.error(f"[D4] Cleanup failed: {e}")
            return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════════
# Singleton Instance
# ═══════════════════════════════════════════════════════════════════════════════

_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get or create rate limiter singleton."""
    global _limiter
    if _limiter is None:
        _limiter = RateLimiter()
    return _limiter


def check_rate(did: str, tier: str = DEFAULT_TIER) -> RateLimitResult:
    """Convenience function to check rate limit."""
    return get_rate_limiter().check_rate(did, tier)


def get_rate_status(did: str, tier: str = DEFAULT_TIER) -> Dict[str, Any]:
    """Convenience function to get rate status."""
    return get_rate_limiter().get_status(did, tier)


# ═══════════════════════════════════════════════════════════════════════════════
# Ledger Integration (Receipt Emission)
# ═══════════════════════════════════════════════════════════════════════════════

def emit_rate_receipt(
    result: RateLimitResult,
    did: str,
    parent_receipt_id: str = None
) -> Optional[str]:
    """
    Emit rate limit event to Forensic Ledger.

    Only emits for DEFER/REJECT (not ALLOW to avoid noise).
    Returns receipt_id if successful.
    """
    if result.action == RateLimitAction.ALLOW:
        return None  # Don't spam ledger with ALLOW events

    try:
        import requests

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        hash_input = f"RATE-{result.receipt_type}-{did}-{timestamp}"
        hash8 = hashlib.sha256(hash_input.encode()).hexdigest()[:8].upper()
        receipt_id = f"WINDI-MAILBOX-RATE-{result.action.value.upper()}-{timestamp}-{hash8}"

        payload = {
            "id": receipt_id,
            "actor": did,
            "app": "w-sites-001-rate-limiter",
            "action": result.receipt_type,
            "doc_type": "audit-bundle",
            "doc_name": f"Rate Limit {result.action.value.upper()}: {did}",
            "governance_level": "HIGH" if result.constitutional else "MEDIUM",
            "sge_score": 0.7 if result.constitutional else 0.5,
            "content_hash": f"sha256:{hashlib.sha256(str(result.to_dict()).encode()).hexdigest()}",
            "metadata": {
                **result.to_dict(),
                "did": did,
                "timestamp": timestamp
            }
        }

        if parent_receipt_id:
            payload["parent_receipt_id"] = parent_receipt_id

        resp = requests.post(
            f"{LEDGER_URL}/api/receipts",
            json=payload,
            timeout=3
        )

        if resp.status_code == 201:
            log.info(f"[D4] Receipt emitted: {receipt_id}")
            return receipt_id
        else:
            log.warning(f"[D4] Receipt failed: {resp.status_code} {resp.text[:100]}")
            return None

    except Exception as e:
        log.warning(f"[D4] Receipt emission failed (non-blocking): {e}")
        return None
