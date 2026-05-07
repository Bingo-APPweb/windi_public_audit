"""
§246-D2-bis + Phase 4 · Slug Reservation System
Namespace Sovereignty — Not Just UX

Liga IA+H · Kempten, Bavaria · 2026-05-07

Constitutional Principles:
- Slug = institutional entity (DID-bound, lineage-aware, auditable)
- Expiry explicit (reserve → renew → expire → release)
- Rename preserves lineage (slug changes, DID + receipts remain)
- Events generate receipts (reserve, renew, release, transfer)
- No silent collision (explicit, verifiable, receipt-aware)

"Namespace sovereignty is the foundation of public institutional identity."
"""

import os
import re
import sqlite3
import hashlib
import logging
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum

log = logging.getLogger("windi.slug_reservation")

# ═══════════════════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════════════════

DB_PATH = os.environ.get("SITES_DB", "/opt/windi/windi-sites/identity-gate/windi_sites_identity.db")
LEDGER_URL = os.environ.get("LEDGER_URL", "http://localhost:8101")

# TTL configuration (D2-bis spec)
RESERVATION_TTL_DAYS = 7          # Soft TTL, renewable
RESERVATION_CAP_DAYS = 30         # Hard cap, non-renewable
OWNERSHIP_INDEFINITE = 36500      # ~100 years (effectively permanent)

# Slug validation
SLUG_MIN_LENGTH = 3
SLUG_MAX_LENGTH = 32
SLUG_PATTERN = re.compile(r'^[a-z0-9][a-z0-9\-]*[a-z0-9]$|^[a-z0-9]$')

# Reserved/blacklisted slugs (D2-bis §B + Guardian expansion 07 Mai 2026)
# 55 terms: RFC 2142 compliance, anti-phishing, WINDI brand protection
RESERVED_SLUGS = frozenset([
    # System/Infrastructure
    'admin', 'administrator', 'root', 'system', 'windi', 'windisites',
    'support', 'help', 'info', 'contact', 'team', 'staff',
    'billing', 'sales', 'account', 'accounts',
    # RFC 2142 - Mandatory mailbox names
    'postmaster', 'hostmaster', 'webmaster', 'abuse',
    # Email special
    'noreply', 'no-reply', 'welcome', 'mailer-daemon', 'bounce',
    'security', 'ssl', 'ftp', 'mail', 'dmarc',
    # Email protocols/autodiscovery (anti-phishing)
    'smtp', 'imap', 'pop', 'pop3', 'webmail',
    'autoconfig', 'autodiscover', 'mta-sts',
    # Network services
    'sftp', 'ssh', 'vpn', 'ns1', 'ns2', 'dns',
    # Legal/compliance
    'legal', 'compliance', 'privacy', 'gdpr', 'dsgvo', 'impressum',
    # Reserved namespaces
    'api', 'app', 'www', 'cdn', 'static', 'assets', 'media',
    'test', 'demo', 'staging', 'dev', 'prod', 'beta', 'alpha',
    # WINDI brand/governance protection
    'guardian', 'architect', 'witness', 'dragon',
    'ledger', 'vault', 'sentinel', 'did', 'cortex', 'genesis',
])


# ═══════════════════════════════════════════════════════════════════════════════
# Result Types
# ═══════════════════════════════════════════════════════════════════════════════

class SlugStatus(Enum):
    """Lifecycle states for slug reservations."""
    AVAILABLE = "available"       # Not reserved, not owned
    RESERVED = "reserved"         # Reserved by workbench token, pending DID
    PROMOTED = "promoted"         # Owned by DID, namespace sovereign
    EXPIRED = "expired"           # Reservation expired, pending cleanup
    BLACKLISTED = "blacklisted"   # System reserved, never available


@dataclass
class SlugCheckResult:
    """Result of slug availability check."""
    slug: str
    status: SlugStatus
    available: bool
    message: str
    reserved_by: Optional[str] = None   # workbench_token hash or DID
    expires_at: Optional[str] = None    # ISO timestamp
    suggestions: List[str] = None       # Alternative slugs if unavailable

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        d["suggestions"] = self.suggestions or []
        return d


@dataclass
class SlugReservationResult:
    """Result of slug reservation operation."""
    success: bool
    slug: str
    status: SlugStatus
    message: str
    workbench_token: Optional[str] = None
    expires_at: Optional[str] = None
    receipt_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        return d


# ═══════════════════════════════════════════════════════════════════════════════
# Database Schema
# ═══════════════════════════════════════════════════════════════════════════════

SCHEMA_SQL = """
-- Slug reservations (D2-bis §G enhanced for Phase 4)
CREATE TABLE IF NOT EXISTS slug_reservations (
    slug TEXT PRIMARY KEY,
    workbench_token TEXT NOT NULL,      -- Reservation token (anonymous phase)
    wallet_id TEXT,                     -- DID after promotion (ownership phase)
    reserved_at TEXT NOT NULL,          -- ISO timestamp
    last_renewed_at TEXT NOT NULL,      -- ISO timestamp
    expires_soft TEXT NOT NULL,         -- TTL renewal window (7d)
    expires_hard TEXT NOT NULL,         -- Cap absolute (30d from reserved_at)
    demo_sent_to_hash TEXT,             -- Hash of email for anti-abuse
    status TEXT DEFAULT 'reserved',     -- reserved/promoted/expired
    -- Phase 4 enhancements: Lineage & audit
    parent_receipt_id TEXT,             -- Chain lineage
    promotion_receipt_id TEXT,          -- Receipt when promoted to ownership
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_slug_reservations_status ON slug_reservations(status);
CREATE INDEX IF NOT EXISTS idx_slug_reservations_wallet ON slug_reservations(wallet_id);
CREATE INDEX IF NOT EXISTS idx_slug_reservations_expires ON slug_reservations(expires_soft);

-- Slug events log (Phase 4: receipt-aware lifecycle)
CREATE TABLE IF NOT EXISTS slug_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL,
    event_type TEXT NOT NULL,           -- RESERVE | RENEW | PROMOTE | EXPIRE | RELEASE | TRANSFER | RENAME
    actor TEXT,                         -- workbench_token or wallet_id
    details TEXT,                       -- JSON with event-specific data
    receipt_id TEXT,                    -- Ledger receipt for audit
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_slug_events_slug ON slug_events(slug);
CREATE INDEX IF NOT EXISTS idx_slug_events_type ON slug_events(event_type);

-- Slug rename history (Phase 4: lineage preservation)
CREATE TABLE IF NOT EXISTS slug_rename_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    old_slug TEXT NOT NULL,
    new_slug TEXT NOT NULL,
    wallet_id TEXT NOT NULL,            -- DID owner
    renamed_at TEXT NOT NULL,
    receipt_id TEXT,
    reason TEXT
);

CREATE INDEX IF NOT EXISTS idx_slug_rename_wallet ON slug_rename_history(wallet_id);
"""


# ═══════════════════════════════════════════════════════════════════════════════
# Slug Reservation Manager
# ═══════════════════════════════════════════════════════════════════════════════

class SlugManager:
    """
    Namespace sovereignty manager for slug reservations.

    Features:
    - Slug validation (length, pattern, blacklist)
    - Reservation with TTL (7d soft, 30d hard cap)
    - Renewal within soft TTL
    - Promotion to ownership (DID-bound)
    - Rename with lineage preservation
    - Event logging with receipts
    - No silent collision
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize database with schema."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.executescript(SCHEMA_SQL)
            conn.commit()
            conn.close()
            log.info(f"[SLUG] Slug manager DB initialized")
        except Exception as e:
            log.error(f"[SLUG] Failed to init DB: {e}")

    def _conn(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path, timeout=5.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _now_iso(self) -> str:
        """Current UTC timestamp in ISO format."""
        return datetime.now(timezone.utc).isoformat()

    def _generate_receipt_id(self, event_type: str, slug: str) -> str:
        """Generate receipt ID for slug event."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        hash_input = f"SLUG-{event_type}-{slug}-{timestamp}"
        hash8 = hashlib.sha256(hash_input.encode()).hexdigest()[:8].upper()
        return f"WINDI-SLUG-{event_type.upper()}-{timestamp}-{hash8}"

    def _log_event(
        self,
        conn: sqlite3.Connection,
        slug: str,
        event_type: str,
        actor: str = None,
        details: str = None,
        receipt_id: str = None
    ):
        """Log slug event for audit trail."""
        conn.execute(
            "INSERT INTO slug_events (slug, event_type, actor, details, receipt_id, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (slug, event_type, actor, details, receipt_id, self._now_iso())
        )

    def _emit_receipt(self, event_type: str, slug: str, metadata: Dict) -> Optional[str]:
        """Emit receipt to Forensic Ledger."""
        try:
            import requests

            receipt_id = self._generate_receipt_id(event_type, slug)

            # Actor must be valid DID or email for Ledger API
            actor = metadata.get("actor", "system@windi-domain.com")
            if not actor.startswith("did:") and "@" not in actor:
                actor = "system@windi-domain.com"

            payload = {
                "id": receipt_id,
                "actor": actor,
                "app": "w-sites-001-slug-manager",
                "action": f"SLUG_{event_type.upper()}",
                "doc_type": "audit-bundle",
                "doc_name": f"Slug {event_type}: {slug}",
                "governance_level": "MEDIUM",
                "sge_score": 0.6,
                "content_hash": f"sha256:{hashlib.sha256(str(metadata).encode()).hexdigest()}",
                "metadata": metadata
            }

            if metadata.get("parent_receipt_id"):
                payload["parent_receipt_id"] = metadata["parent_receipt_id"]

            resp = requests.post(
                f"{LEDGER_URL}/api/receipts",
                json=payload,
                timeout=3
            )

            if resp.status_code == 201:
                log.info(f"[SLUG] Receipt emitted: {receipt_id}")
                return receipt_id
            else:
                log.warning(f"[SLUG] Receipt failed: {resp.status_code}")
                return None

        except Exception as e:
            log.warning(f"[SLUG] Receipt emission failed (non-blocking): {e}")
            return None

    # ═══════════════════════════════════════════════════════════════════════
    # Validation
    # ═══════════════════════════════════════════════════════════════════════

    def validate_slug(self, slug: str) -> Tuple[bool, str]:
        """
        Validate slug format.

        Returns:
            (valid, message)
        """
        if not slug:
            return False, "Slug is required"

        slug = slug.lower().strip()

        if len(slug) < SLUG_MIN_LENGTH:
            return False, f"Slug must be at least {SLUG_MIN_LENGTH} characters"

        if len(slug) > SLUG_MAX_LENGTH:
            return False, f"Slug must be at most {SLUG_MAX_LENGTH} characters"

        if not SLUG_PATTERN.match(slug):
            return False, "Slug must contain only lowercase letters, numbers, and hyphens"

        if slug in RESERVED_SLUGS:
            return False, f"Slug '{slug}' is reserved for system use"

        return True, "Valid"

    def _generate_suggestions(self, slug: str, count: int = 3) -> List[str]:
        """Generate alternative slug suggestions."""
        suggestions = []
        base = slug.rstrip('0123456789')

        for i in range(1, count + 10):
            candidate = f"{base}{i}"
            if self.check_availability(candidate).available:
                suggestions.append(candidate)
                if len(suggestions) >= count:
                    break

        return suggestions

    # ═══════════════════════════════════════════════════════════════════════
    # Availability Check
    # ═══════════════════════════════════════════════════════════════════════

    def check_availability(self, slug: str) -> SlugCheckResult:
        """
        Check if slug is available for reservation.

        Returns detailed status with suggestions if unavailable.
        """
        slug = slug.lower().strip()

        # Validate format
        valid, msg = self.validate_slug(slug)
        if not valid:
            return SlugCheckResult(
                slug=slug,
                status=SlugStatus.BLACKLISTED if slug in RESERVED_SLUGS else SlugStatus.AVAILABLE,
                available=False,
                message=msg
            )

        # Check system blacklist
        if slug in RESERVED_SLUGS:
            return SlugCheckResult(
                slug=slug,
                status=SlugStatus.BLACKLISTED,
                available=False,
                message=f"'{slug}' is reserved for system use",
                suggestions=self._generate_suggestions(slug)
            )

        try:
            conn = self._conn()
            try:
                row = conn.execute(
                    "SELECT slug, status, workbench_token, wallet_id, expires_soft "
                    "FROM slug_reservations WHERE slug = ?",
                    (slug,)
                ).fetchone()

                if not row:
                    return SlugCheckResult(
                        slug=slug,
                        status=SlugStatus.AVAILABLE,
                        available=True,
                        message="Available"
                    )

                status = row["status"]
                expires_soft = row["expires_soft"]
                now = self._now_iso()

                # Check if expired
                if status == "reserved" and expires_soft < now:
                    # Expired, clean up and return available
                    conn.execute(
                        "UPDATE slug_reservations SET status = 'expired' WHERE slug = ?",
                        (slug,)
                    )
                    conn.commit()
                    return SlugCheckResult(
                        slug=slug,
                        status=SlugStatus.AVAILABLE,
                        available=True,
                        message="Available (previous reservation expired)"
                    )

                if status == "promoted":
                    # Owned by DID
                    return SlugCheckResult(
                        slug=slug,
                        status=SlugStatus.PROMOTED,
                        available=False,
                        message=f"'{slug}' is owned",
                        reserved_by=row["wallet_id"][:20] + "..." if row["wallet_id"] else None,
                        suggestions=self._generate_suggestions(slug)
                    )

                if status == "reserved":
                    return SlugCheckResult(
                        slug=slug,
                        status=SlugStatus.RESERVED,
                        available=False,
                        message=f"'{slug}' is reserved",
                        reserved_by=hashlib.sha256(row["workbench_token"].encode()).hexdigest()[:8],
                        expires_at=expires_soft,
                        suggestions=self._generate_suggestions(slug)
                    )

                # Expired or unknown status
                return SlugCheckResult(
                    slug=slug,
                    status=SlugStatus.AVAILABLE,
                    available=True,
                    message="Available"
                )

            finally:
                conn.close()

        except Exception as e:
            log.error(f"[SLUG] Availability check failed: {e}")
            # Fail-safe: treat as unavailable to prevent collision
            return SlugCheckResult(
                slug=slug,
                status=SlugStatus.RESERVED,
                available=False,
                message=f"Availability check failed: {str(e)[:50]}"
            )

    # ═══════════════════════════════════════════════════════════════════════
    # Reserve
    # ═══════════════════════════════════════════════════════════════════════

    def reserve(
        self,
        slug: str,
        workbench_token: str,
        parent_receipt_id: str = None
    ) -> SlugReservationResult:
        """
        Reserve a slug for a workbench session.

        TTL: 7 days soft (renewable), 30 days hard cap
        """
        slug = slug.lower().strip()

        # Check availability
        check = self.check_availability(slug)
        if not check.available:
            return SlugReservationResult(
                success=False,
                slug=slug,
                status=check.status,
                message=check.message
            )

        try:
            conn = self._conn()
            try:
                now = datetime.now(timezone.utc)
                now_iso = now.isoformat()
                expires_soft = (now + timedelta(days=RESERVATION_TTL_DAYS)).isoformat()
                expires_hard = (now + timedelta(days=RESERVATION_CAP_DAYS)).isoformat()

                # Insert reservation
                conn.execute(
                    "INSERT OR REPLACE INTO slug_reservations "
                    "(slug, workbench_token, reserved_at, last_renewed_at, "
                    "expires_soft, expires_hard, status, parent_receipt_id, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, 'reserved', ?, ?, ?)",
                    (slug, workbench_token, now_iso, now_iso,
                     expires_soft, expires_hard, parent_receipt_id, now_iso, now_iso)
                )

                # Emit receipt
                receipt_id = self._emit_receipt("RESERVE", slug, {
                    "slug": slug,
                    "actor": "slug-reservation@windi-domain.com",
                    "workbench_token_prefix": workbench_token[:8],
                    "expires_soft": expires_soft,
                    "expires_hard": expires_hard,
                    "parent_receipt_id": parent_receipt_id
                })

                # Log event
                self._log_event(
                    conn, slug, "RESERVE",
                    actor=workbench_token,
                    details=f'{{"expires_soft":"{expires_soft}"}}',
                    receipt_id=receipt_id
                )

                conn.commit()

                log.info(f"[SLUG] Reserved: {slug} for token {workbench_token[:8]}...")

                return SlugReservationResult(
                    success=True,
                    slug=slug,
                    status=SlugStatus.RESERVED,
                    message="Slug reserved successfully",
                    workbench_token=workbench_token,
                    expires_at=expires_soft,
                    receipt_id=receipt_id
                )

            finally:
                conn.close()

        except Exception as e:
            log.error(f"[SLUG] Reserve failed: {e}")
            return SlugReservationResult(
                success=False,
                slug=slug,
                status=SlugStatus.AVAILABLE,
                message=f"Reservation failed: {str(e)[:50]}"
            )

    # ═══════════════════════════════════════════════════════════════════════
    # Renew
    # ═══════════════════════════════════════════════════════════════════════

    def renew(self, slug: str, workbench_token: str) -> SlugReservationResult:
        """
        Renew a slug reservation (extend soft TTL, cannot exceed hard cap).
        """
        slug = slug.lower().strip()

        try:
            conn = self._conn()
            try:
                row = conn.execute(
                    "SELECT * FROM slug_reservations WHERE slug = ? AND workbench_token = ?",
                    (slug, workbench_token)
                ).fetchone()

                if not row:
                    return SlugReservationResult(
                        success=False,
                        slug=slug,
                        status=SlugStatus.AVAILABLE,
                        message="Reservation not found or token mismatch"
                    )

                if row["status"] != "reserved":
                    return SlugReservationResult(
                        success=False,
                        slug=slug,
                        status=SlugStatus(row["status"]),
                        message=f"Cannot renew: status is {row['status']}"
                    )

                now = datetime.now(timezone.utc)
                now_iso = now.isoformat()
                expires_hard = row["expires_hard"]

                # Cannot extend beyond hard cap
                new_expires_soft = min(
                    (now + timedelta(days=RESERVATION_TTL_DAYS)).isoformat(),
                    expires_hard
                )

                if new_expires_soft <= row["expires_soft"]:
                    return SlugReservationResult(
                        success=False,
                        slug=slug,
                        status=SlugStatus.RESERVED,
                        message="Cannot renew: hard cap reached",
                        expires_at=row["expires_soft"]
                    )

                # Update reservation
                conn.execute(
                    "UPDATE slug_reservations SET last_renewed_at = ?, expires_soft = ?, updated_at = ? "
                    "WHERE slug = ?",
                    (now_iso, new_expires_soft, now_iso, slug)
                )

                # Emit receipt
                receipt_id = self._emit_receipt("RENEW", slug, {
                    "slug": slug,
                    "actor": "slug-reservation@windi-domain.com",
                    "workbench_token_prefix": workbench_token[:8],
                    "new_expires_soft": new_expires_soft,
                    "expires_hard": expires_hard
                })

                # Log event
                self._log_event(
                    conn, slug, "RENEW",
                    actor=workbench_token,
                    details=f'{{"new_expires_soft":"{new_expires_soft}"}}',
                    receipt_id=receipt_id
                )

                conn.commit()

                log.info(f"[SLUG] Renewed: {slug}")

                return SlugReservationResult(
                    success=True,
                    slug=slug,
                    status=SlugStatus.RESERVED,
                    message="Reservation renewed",
                    workbench_token=workbench_token,
                    expires_at=new_expires_soft,
                    receipt_id=receipt_id
                )

            finally:
                conn.close()

        except Exception as e:
            log.error(f"[SLUG] Renew failed: {e}")
            return SlugReservationResult(
                success=False,
                slug=slug,
                status=SlugStatus.RESERVED,
                message=f"Renewal failed: {str(e)[:50]}"
            )

    # ═══════════════════════════════════════════════════════════════════════
    # Promote (Reservation → Ownership)
    # ═══════════════════════════════════════════════════════════════════════

    def promote(
        self,
        slug: str,
        workbench_token: str,
        wallet_id: str,
        parent_receipt_id: str = None
    ) -> SlugReservationResult:
        """
        Promote slug reservation to ownership (DID-bound).

        This is the transition from anonymous reservation to sovereign ownership.
        """
        slug = slug.lower().strip()

        if not wallet_id or not wallet_id.startswith("did:"):
            return SlugReservationResult(
                success=False,
                slug=slug,
                status=SlugStatus.RESERVED,
                message="Valid DID required for promotion"
            )

        try:
            conn = self._conn()
            try:
                row = conn.execute(
                    "SELECT * FROM slug_reservations WHERE slug = ? AND workbench_token = ?",
                    (slug, workbench_token)
                ).fetchone()

                if not row:
                    return SlugReservationResult(
                        success=False,
                        slug=slug,
                        status=SlugStatus.AVAILABLE,
                        message="Reservation not found or token mismatch"
                    )

                if row["status"] != "reserved":
                    return SlugReservationResult(
                        success=False,
                        slug=slug,
                        status=SlugStatus(row["status"]),
                        message=f"Cannot promote: status is {row['status']}"
                    )

                now = datetime.now(timezone.utc)
                now_iso = now.isoformat()

                # Emit receipt BEFORE promotion (audit trail)
                receipt_id = self._emit_receipt("PROMOTE", slug, {
                    "slug": slug,
                    "actor": wallet_id,
                    "from_workbench_token": workbench_token[:8] + "...",
                    "to_wallet_id": wallet_id,
                    "reserved_at": row["reserved_at"],
                    "promoted_at": now_iso,
                    "parent_receipt_id": parent_receipt_id or row["parent_receipt_id"]
                })

                # Update to promoted status
                conn.execute(
                    "UPDATE slug_reservations SET "
                    "wallet_id = ?, status = 'promoted', "
                    "promotion_receipt_id = ?, updated_at = ? "
                    "WHERE slug = ?",
                    (wallet_id, receipt_id, now_iso, slug)
                )

                # Log event
                self._log_event(
                    conn, slug, "PROMOTE",
                    actor=wallet_id,
                    details=f'{{"wallet_id":"{wallet_id}"}}',
                    receipt_id=receipt_id
                )

                conn.commit()

                log.info(f"[SLUG] Promoted: {slug} → {wallet_id[:20]}...")

                return SlugReservationResult(
                    success=True,
                    slug=slug,
                    status=SlugStatus.PROMOTED,
                    message="Slug promoted to ownership",
                    workbench_token=workbench_token,
                    receipt_id=receipt_id
                )

            finally:
                conn.close()

        except Exception as e:
            log.error(f"[SLUG] Promote failed: {e}")
            return SlugReservationResult(
                success=False,
                slug=slug,
                status=SlugStatus.RESERVED,
                message=f"Promotion failed: {str(e)[:50]}"
            )

    # ═══════════════════════════════════════════════════════════════════════
    # Rename (Lineage Preservation)
    # ═══════════════════════════════════════════════════════════════════════

    def rename(
        self,
        old_slug: str,
        new_slug: str,
        wallet_id: str,
        reason: str = None
    ) -> SlugReservationResult:
        """
        Rename a slug while preserving lineage.

        Critical: DID and receipts remain, only slug changes.
        Old slug becomes available, new slug becomes owned.
        """
        old_slug = old_slug.lower().strip()
        new_slug = new_slug.lower().strip()

        # Validate new slug
        valid, msg = self.validate_slug(new_slug)
        if not valid:
            return SlugReservationResult(
                success=False,
                slug=old_slug,
                status=SlugStatus.PROMOTED,
                message=f"New slug invalid: {msg}"
            )

        # Check new slug availability
        check = self.check_availability(new_slug)
        if not check.available:
            return SlugReservationResult(
                success=False,
                slug=old_slug,
                status=SlugStatus.PROMOTED,
                message=f"New slug unavailable: {check.message}"
            )

        try:
            conn = self._conn()
            try:
                # Verify ownership of old slug
                row = conn.execute(
                    "SELECT * FROM slug_reservations WHERE slug = ? AND wallet_id = ? AND status = 'promoted'",
                    (old_slug, wallet_id)
                ).fetchone()

                if not row:
                    return SlugReservationResult(
                        success=False,
                        slug=old_slug,
                        status=SlugStatus.AVAILABLE,
                        message="Slug not owned by this DID"
                    )

                now = datetime.now(timezone.utc)
                now_iso = now.isoformat()

                # Emit receipt for rename
                receipt_id = self._emit_receipt("RENAME", new_slug, {
                    "old_slug": old_slug,
                    "new_slug": new_slug,
                    "actor": wallet_id,
                    "reason": reason,
                    "renamed_at": now_iso,
                    "parent_receipt_id": row["promotion_receipt_id"]
                })

                # Record rename history (lineage preservation)
                conn.execute(
                    "INSERT INTO slug_rename_history "
                    "(old_slug, new_slug, wallet_id, renamed_at, receipt_id, reason) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (old_slug, new_slug, wallet_id, now_iso, receipt_id, reason)
                )

                # Update slug in reservation
                conn.execute(
                    "UPDATE slug_reservations SET slug = ?, updated_at = ? WHERE slug = ?",
                    (new_slug, now_iso, old_slug)
                )

                # Log events for both old and new
                self._log_event(
                    conn, old_slug, "RENAME_FROM",
                    actor=wallet_id,
                    details=f'{{"new_slug":"{new_slug}"}}',
                    receipt_id=receipt_id
                )
                self._log_event(
                    conn, new_slug, "RENAME_TO",
                    actor=wallet_id,
                    details=f'{{"old_slug":"{old_slug}"}}',
                    receipt_id=receipt_id
                )

                conn.commit()

                log.info(f"[SLUG] Renamed: {old_slug} → {new_slug} by {wallet_id[:20]}...")

                return SlugReservationResult(
                    success=True,
                    slug=new_slug,
                    status=SlugStatus.PROMOTED,
                    message=f"Renamed from {old_slug} to {new_slug}",
                    receipt_id=receipt_id
                )

            finally:
                conn.close()

        except Exception as e:
            log.error(f"[SLUG] Rename failed: {e}")
            return SlugReservationResult(
                success=False,
                slug=old_slug,
                status=SlugStatus.PROMOTED,
                message=f"Rename failed: {str(e)[:50]}"
            )

    # ═══════════════════════════════════════════════════════════════════════
    # Cleanup & Maintenance
    # ═══════════════════════════════════════════════════════════════════════

    def cleanup_expired(self) -> Dict[str, Any]:
        """
        Cleanup expired reservations.

        Returns aggregate receipt for purged slugs.
        """
        try:
            conn = self._conn()
            try:
                now_iso = self._now_iso()

                # Find expired reservations
                expired = conn.execute(
                    "SELECT slug, workbench_token FROM slug_reservations "
                    "WHERE status = 'reserved' AND expires_soft < ?",
                    (now_iso,)
                ).fetchall()

                if not expired:
                    return {"purged": 0, "slugs": []}

                slugs = [row["slug"] for row in expired]

                # Update status to expired
                conn.execute(
                    "UPDATE slug_reservations SET status = 'expired', updated_at = ? "
                    "WHERE status = 'reserved' AND expires_soft < ?",
                    (now_iso, now_iso)
                )

                # Emit aggregate receipt
                receipt_id = self._emit_receipt("PURGE", "aggregate", {
                    "count": len(slugs),
                    "slugs_purged": len(slugs),  # Count only, not actual slugs (privacy)
                    "purged_at": now_iso
                })

                # Log aggregate event
                self._log_event(
                    conn, "AGGREGATE", "PURGE",
                    details=f'{{"count":{len(slugs)}}}',
                    receipt_id=receipt_id
                )

                conn.commit()

                log.info(f"[SLUG] Purged {len(slugs)} expired reservations")

                return {
                    "purged": len(slugs),
                    "slugs": slugs,
                    "receipt_id": receipt_id
                }

            finally:
                conn.close()

        except Exception as e:
            log.error(f"[SLUG] Cleanup failed: {e}")
            return {"error": str(e)}

    def get_reservation(self, slug: str) -> Optional[Dict[str, Any]]:
        """Get reservation details for a slug."""
        slug = slug.lower().strip()

        try:
            conn = self._conn()
            try:
                row = conn.execute(
                    "SELECT * FROM slug_reservations WHERE slug = ?",
                    (slug,)
                ).fetchone()

                if not row:
                    return None

                return dict(row)

            finally:
                conn.close()

        except Exception as e:
            log.error(f"[SLUG] Get reservation failed: {e}")
            return None

    def get_by_wallet(self, wallet_id: str) -> List[Dict[str, Any]]:
        """Get all slugs owned by a wallet/DID."""
        try:
            conn = self._conn()
            try:
                rows = conn.execute(
                    "SELECT * FROM slug_reservations WHERE wallet_id = ? AND status = 'promoted'",
                    (wallet_id,)
                ).fetchall()

                return [dict(row) for row in rows]

            finally:
                conn.close()

        except Exception as e:
            log.error(f"[SLUG] Get by wallet failed: {e}")
            return []


# ═══════════════════════════════════════════════════════════════════════════════
# Singleton Instance
# ═══════════════════════════════════════════════════════════════════════════════

_manager: Optional[SlugManager] = None


def get_slug_manager() -> SlugManager:
    """Get or create slug manager singleton."""
    global _manager
    if _manager is None:
        _manager = SlugManager()
    return _manager


# Convenience functions
def check_slug(slug: str) -> SlugCheckResult:
    return get_slug_manager().check_availability(slug)


def reserve_slug(slug: str, workbench_token: str, parent_receipt_id: str = None) -> SlugReservationResult:
    return get_slug_manager().reserve(slug, workbench_token, parent_receipt_id)


def renew_slug(slug: str, workbench_token: str) -> SlugReservationResult:
    return get_slug_manager().renew(slug, workbench_token)


def promote_slug(slug: str, workbench_token: str, wallet_id: str, parent_receipt_id: str = None) -> SlugReservationResult:
    return get_slug_manager().promote(slug, workbench_token, wallet_id, parent_receipt_id)


def rename_slug(old_slug: str, new_slug: str, wallet_id: str, reason: str = None) -> SlugReservationResult:
    return get_slug_manager().rename(old_slug, new_slug, wallet_id, reason)
