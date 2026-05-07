"""
§246-Phase5a — Mailbox Provisioning Layer (API + DB)

"The mailbox that PROVES existence. Not the mailbox that only TRANSMITS."
↑ Honored at Phase 5b (mail system integration). Phase 5a covers
  the sovereign data plane: DID-binding, lifecycle events, audit trail.

Phase 5a (this module): API + SQLite + Ledger receipts.
Phase 5b (pending):     Postfix/Dovecot integration. Until 5b lands,
                        _configure_mail_system() is a stub. Commercial
                        tiers MUST NOT advertise functional mailboxes
                        before 5b ships.

Constitutional Foundation:
- Every mailbox is DID-bound (sovereign ownership)
- Two-phase atomic provisioning (PRE → POST)
- 11 lifecycle events tracked in Ledger
- Quota/tier management per identity

Invariants: I1, I9, I11, I12, I14
Receipt: F8881FCA (D3 Architectural Seal)
Implementation Receipt: 2C3DD7CA (Phase 5a)
"""

import sqlite3
import hashlib
import os
import subprocess
import requests
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any, List


# ═══════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════

DB_PATH = "/opt/windi/data/mailbox_provisioning.db"
LEDGER_URL = "http://127.0.0.1:8101/api/receipts"
POSTFIX_VIRTUAL = "/etc/postfix/virtual"
DOVECOT_PASSWD = "/etc/dovecot/users"

# Tiers and their quotas (MB)
TIER_QUOTAS = {
    "FREE":   100,    # 100 MB
    "LOW":    500,    # 500 MB
    "MED":    2048,   # 2 GB
    "HIGH":   10240,  # 10 GB
    "PHO":    51200,  # 50 GB (Privileged Human Operator)
}


# ═══════════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════════

class MailboxStatus(Enum):
    """Mailbox lifecycle states."""
    PENDING = "pending"           # PRE phase initiated
    ACTIVE = "active"             # POST phase completed
    SUSPENDED = "suspended"       # Temporarily disabled
    REVOKED = "revoked"           # Permanently disabled
    LEGAL_HOLD = "legal_hold"     # Cannot modify/delete


class MailboxEvent(Enum):
    """11 lifecycle events (D3 spec)."""
    PROVISION_PRE = "provision_pre"       # 1. PRE phase started
    PROVISION_POST = "provision_post"     # 2. POST phase completed
    QUOTA_WARNING = "quota_warning"       # 3. Soft quota threshold (80%)
    QUOTA_EXCEEDED = "quota_exceeded"     # 4. Hard quota hit
    TIER_UPGRADE = "tier_upgrade"         # 5. Quota increased
    TIER_DOWNGRADE = "tier_downgrade"     # 6. Quota decreased (with retention)
    SUSPEND = "suspend"                   # 7. Temporary suspension
    RESTORE = "restore"                   # 8. Restored from suspension
    REVOKE = "revoke"                     # 9. Permanent revocation
    LEGAL_HOLD = "legal_hold"             # 10. Legal hold applied
    SLUG_RENAME = "slug_rename"           # 11. Email address changed


# ═══════════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class MailboxResult:
    """Result of mailbox operations."""
    success: bool
    email: str
    status: MailboxStatus
    message: str
    receipt_id: Optional[str] = None
    quota_mb: Optional[int] = None
    used_mb: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "email": self.email,
            "status": self.status.value if isinstance(self.status, MailboxStatus) else self.status,
            "message": self.message,
            "receipt_id": self.receipt_id,
            "quota_mb": self.quota_mb,
            "used_mb": self.used_mb
        }


@dataclass
class MailboxInfo:
    """Complete mailbox information."""
    email: str
    wallet_id: str
    slug: str
    domain: str
    tier: str
    quota_mb: int
    used_mb: float
    status: MailboxStatus
    created_at: str
    updated_at: str
    provision_receipt_id: Optional[str] = None
    legal_hold_receipt_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "email": self.email,
            "wallet_id": self.wallet_id,
            "slug": self.slug,
            "domain": self.domain,
            "tier": self.tier,
            "quota_mb": self.quota_mb,
            "used_mb": self.used_mb,
            "status": self.status.value if isinstance(self.status, MailboxStatus) else self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "provision_receipt_id": self.provision_receipt_id,
            "legal_hold_receipt_id": self.legal_hold_receipt_id
        }


# ═══════════════════════════════════════════════════════════════════════════
# MAILBOX MANAGER
# ═══════════════════════════════════════════════════════════════════════════

class MailboxManager:
    """
    §246-D3: Sovereign Mailbox Manager.

    Two-phase atomic provisioning:
    - PRE: Create records, reserve namespace
    - POST: Configure mail system, activate

    If PRE succeeds but POST fails → rollback to PENDING, retry possible.
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_db(self):
        """Initialize database schema."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = self._conn()
        try:
            # Mailboxes table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS mailboxes (
                    email TEXT PRIMARY KEY,
                    wallet_id TEXT NOT NULL,
                    slug TEXT NOT NULL,
                    domain TEXT NOT NULL DEFAULT 'windisites.de',
                    tier TEXT NOT NULL DEFAULT 'FREE',
                    quota_mb INTEGER NOT NULL DEFAULT 100,
                    used_mb REAL NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'pending',
                    provision_receipt_id TEXT,
                    legal_hold_receipt_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(slug, domain)
                )
            """)

            # Events table (audit trail)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS mailbox_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    metadata TEXT,
                    receipt_id TEXT,
                    event_at TEXT NOT NULL,
                    FOREIGN KEY (email) REFERENCES mailboxes(email)
                )
            """)

            # Indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_mailboxes_wallet ON mailboxes(wallet_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_mailboxes_status ON mailboxes(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_email ON mailbox_events(email)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON mailbox_events(event_type)")

            conn.commit()
        finally:
            conn.close()

    # ═══════════════════════════════════════════════════════════════════════
    # Receipt Emission
    # ═══════════════════════════════════════════════════════════════════════

    def _emit_receipt(
        self,
        event: str,
        email: str,
        metadata: Dict[str, Any]
    ) -> Optional[str]:
        """Emit receipt to Forensic Ledger."""
        try:
            now = datetime.now(timezone.utc)
            ts = now.strftime("%Y%m%d%H%M%S")
            content = f"MAILBOX-{event}-{email}-{ts}"
            hash8 = hashlib.sha256(content.encode()).hexdigest()[:8].upper()
            receipt_id = f"WINDI-MAILBOX-{event}-{ts}-{hash8}"

            actor = metadata.get("actor", "system@windi-domain.com")
            if not actor.startswith("did:") and "@" not in actor:
                actor = "system@windi-domain.com"

            payload = {
                "id": receipt_id,
                "actor": actor,
                "app": "w-mail-001",
                "doc_name": f"Mailbox {event}: {email}",
                "doc_type": "audit-bundle",
                "governance_level": "HIGH",
                "content_hash": f"sha256:{hashlib.sha256(content.encode()).hexdigest()}",
                "metadata": {
                    "event": event,
                    "email": email,
                    **metadata
                },
                "sge_score": 0.95,
                "invariants": ["I1", "I9", "I11", "I14"]
            }

            resp = requests.post(LEDGER_URL, json=payload, timeout=5)
            if resp.ok:
                return receipt_id
        except Exception as e:
            print(f"[MAILBOX] Receipt emission failed: {e}")
        return None

    def _log_event(
        self,
        email: str,
        event_type: MailboxEvent,
        actor: str,
        metadata: Dict[str, Any],
        receipt_id: Optional[str] = None
    ):
        """Log event to local database."""
        conn = self._conn()
        try:
            import json
            conn.execute("""
                INSERT INTO mailbox_events (email, event_type, actor, metadata, receipt_id, event_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                email,
                event_type.value,
                actor,
                json.dumps(metadata),
                receipt_id,
                datetime.now(timezone.utc).isoformat()
            ))
            conn.commit()
        finally:
            conn.close()

    # ═══════════════════════════════════════════════════════════════════════
    # PRE Phase: Reserve namespace, create records
    # ═══════════════════════════════════════════════════════════════════════

    def provision_pre(
        self,
        slug: str,
        wallet_id: str,
        domain: str = "windisites.de",
        tier: str = "FREE",
        actor: str = "system@windi-domain.com"
    ) -> MailboxResult:
        """
        PRE phase of mailbox provisioning.

        Creates database record with status=PENDING.
        Does NOT configure mail system yet.
        """
        slug = slug.lower().strip()
        email = f"{slug}@{domain}"

        # Validate DID
        if not wallet_id or not wallet_id.startswith("did:"):
            return MailboxResult(
                success=False,
                email=email,
                status=MailboxStatus.PENDING,
                message="Valid DID required (wallet_id must start with did:)"
            )

        # Validate tier
        if tier not in TIER_QUOTAS:
            return MailboxResult(
                success=False,
                email=email,
                status=MailboxStatus.PENDING,
                message=f"Invalid tier: {tier}. Valid: {list(TIER_QUOTAS.keys())}"
            )

        quota_mb = TIER_QUOTAS[tier]
        now = datetime.now(timezone.utc).isoformat()

        conn = self._conn()
        try:
            # Check existing
            existing = conn.execute(
                "SELECT * FROM mailboxes WHERE email = ?",
                (email,)
            ).fetchone()

            if existing:
                return MailboxResult(
                    success=False,
                    email=email,
                    status=MailboxStatus(existing["status"]),
                    message=f"Email '{email}' already exists"
                )

            # Emit PRE receipt
            receipt_id = self._emit_receipt("PROVISION-PRE", email, {
                "actor": actor,
                "wallet_id": wallet_id,
                "slug": slug,
                "domain": domain,
                "tier": tier,
                "quota_mb": quota_mb,
                "phase": "PRE"
            })

            # Create record
            conn.execute("""
                INSERT INTO mailboxes
                (email, wallet_id, slug, domain, tier, quota_mb, used_mb, status, provision_receipt_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 0, 'pending', ?, ?, ?)
            """, (email, wallet_id, slug, domain, tier, quota_mb, receipt_id, now, now))

            conn.commit()

            # Log event
            self._log_event(email, MailboxEvent.PROVISION_PRE, actor, {
                "wallet_id": wallet_id,
                "tier": tier,
                "quota_mb": quota_mb
            }, receipt_id)

            return MailboxResult(
                success=True,
                email=email,
                status=MailboxStatus.PENDING,
                message="PRE phase complete. Ready for POST phase.",
                receipt_id=receipt_id,
                quota_mb=quota_mb
            )

        except sqlite3.IntegrityError:
            return MailboxResult(
                success=False,
                email=email,
                status=MailboxStatus.PENDING,
                message=f"Slug '{slug}' already taken on {domain}"
            )
        finally:
            conn.close()

    # ═══════════════════════════════════════════════════════════════════════
    # POST Phase: Configure mail system, activate
    # ═══════════════════════════════════════════════════════════════════════

    def provision_post(
        self,
        email: str,
        password_hash: Optional[str] = None,
        actor: str = "system@windi-domain.com"
    ) -> MailboxResult:
        """
        POST phase of mailbox provisioning.

        Configures mail system:
        1. Adds to Postfix virtual map
        2. Adds to Dovecot users
        3. Activates mailbox

        If this fails, mailbox remains PENDING (retry possible).
        """
        conn = self._conn()
        try:
            row = conn.execute(
                "SELECT * FROM mailboxes WHERE email = ?",
                (email,)
            ).fetchone()

            if not row:
                return MailboxResult(
                    success=False,
                    email=email,
                    status=MailboxStatus.PENDING,
                    message="Mailbox not found. Run PRE phase first."
                )

            if row["status"] != "pending":
                return MailboxResult(
                    success=False,
                    email=email,
                    status=MailboxStatus(row["status"]),
                    message=f"Cannot POST: status is {row['status']}, expected pending"
                )

            # Generate password hash if not provided
            if not password_hash:
                import secrets
                temp_password = secrets.token_urlsafe(16)
                password_hash = self._hash_password(temp_password)

            # Configure mail system (atomic: all or nothing)
            config_success = self._configure_mail_system(
                email=email,
                password_hash=password_hash,
                quota_mb=row["quota_mb"]
            )

            if not config_success:
                return MailboxResult(
                    success=False,
                    email=email,
                    status=MailboxStatus.PENDING,
                    message="Mail system configuration failed. PRE preserved, retry possible."
                )

            # Emit POST receipt
            receipt_id = self._emit_receipt("PROVISION-POST", email, {
                "actor": actor,
                "wallet_id": row["wallet_id"],
                "slug": row["slug"],
                "domain": row["domain"],
                "tier": row["tier"],
                "quota_mb": row["quota_mb"],
                "phase": "POST",
                "pre_receipt_id": row["provision_receipt_id"]
            })

            # Activate
            now = datetime.now(timezone.utc).isoformat()
            conn.execute("""
                UPDATE mailboxes
                SET status = 'active', provision_receipt_id = ?, updated_at = ?
                WHERE email = ?
            """, (receipt_id, now, email))

            conn.commit()

            # Log event
            self._log_event(email, MailboxEvent.PROVISION_POST, actor, {
                "wallet_id": row["wallet_id"],
                "tier": row["tier"],
                "phase": "POST"
            }, receipt_id)

            return MailboxResult(
                success=True,
                email=email,
                status=MailboxStatus.ACTIVE,
                message="Mailbox provisioned and active",
                receipt_id=receipt_id,
                quota_mb=row["quota_mb"]
            )

        finally:
            conn.close()

    def _hash_password(self, password: str) -> str:
        """Generate Dovecot-compatible password hash."""
        try:
            result = subprocess.run(
                ["doveadm", "pw", "-s", "SHA512-CRYPT", "-p", password],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        # Fallback: simple SHA512
        import crypt
        return crypt.crypt(password, crypt.mksalt(crypt.METHOD_SHA512))

    def _configure_mail_system(
        self,
        email: str,
        password_hash: str,
        quota_mb: int
    ) -> bool:
        """
        Configure Postfix/Dovecot for mailbox.

        §246-Phase5b SCAFFOLD PENDING
        =============================
        Real Postfix/Dovecot integration lands in Phase 5b.
        Until then this is intentionally a no-op that returns True
        so the API + DB lifecycle can be exercised end-to-end.

        DO NOT remove this comment without sealing Phase 5b first.

        Production implementation would use:
        - Postfix virtual_mailbox_maps (SQL backend)
        - Dovecot SQL passdb/userdb
        - Maildir creation with proper permissions
        """
        # §246-Phase5b SCAFFOLD PENDING
        # This stub allows Phase 5a (API + DB layer) to function.
        # Emails sent to this address will get 550 user unknown
        # until Phase 5b integrates with actual mail system.
        print(f"[MAILBOX] Phase5b stub: {email}, quota={quota_mb}MB")
        return True

    # ═══════════════════════════════════════════════════════════════════════
    # Lifecycle Operations
    # ═══════════════════════════════════════════════════════════════════════

    def get_mailbox(self, email: str) -> Optional[MailboxInfo]:
        """Get mailbox information."""
        conn = self._conn()
        try:
            row = conn.execute(
                "SELECT * FROM mailboxes WHERE email = ?",
                (email,)
            ).fetchone()

            if not row:
                return None

            return MailboxInfo(
                email=row["email"],
                wallet_id=row["wallet_id"],
                slug=row["slug"],
                domain=row["domain"],
                tier=row["tier"],
                quota_mb=row["quota_mb"],
                used_mb=row["used_mb"],
                status=MailboxStatus(row["status"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                provision_receipt_id=row["provision_receipt_id"],
                legal_hold_receipt_id=row["legal_hold_receipt_id"]
            )
        finally:
            conn.close()

    def get_mailboxes_by_wallet(self, wallet_id: str) -> List[MailboxInfo]:
        """Get all mailboxes for a wallet/DID."""
        conn = self._conn()
        try:
            rows = conn.execute(
                "SELECT * FROM mailboxes WHERE wallet_id = ? ORDER BY created_at DESC",
                (wallet_id,)
            ).fetchall()

            return [
                MailboxInfo(
                    email=row["email"],
                    wallet_id=row["wallet_id"],
                    slug=row["slug"],
                    domain=row["domain"],
                    tier=row["tier"],
                    quota_mb=row["quota_mb"],
                    used_mb=row["used_mb"],
                    status=MailboxStatus(row["status"]),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    provision_receipt_id=row["provision_receipt_id"],
                    legal_hold_receipt_id=row["legal_hold_receipt_id"]
                )
                for row in rows
            ]
        finally:
            conn.close()

    def suspend(
        self,
        email: str,
        reason: str,
        actor: str = "system@windi-domain.com"
    ) -> MailboxResult:
        """Suspend mailbox (temporary)."""
        conn = self._conn()
        try:
            row = conn.execute(
                "SELECT * FROM mailboxes WHERE email = ?",
                (email,)
            ).fetchone()

            if not row:
                return MailboxResult(
                    success=False,
                    email=email,
                    status=MailboxStatus.PENDING,
                    message="Mailbox not found"
                )

            if row["status"] == "legal_hold":
                return MailboxResult(
                    success=False,
                    email=email,
                    status=MailboxStatus.LEGAL_HOLD,
                    message="Cannot suspend: under legal hold"
                )

            receipt_id = self._emit_receipt("SUSPEND", email, {
                "actor": actor,
                "reason": reason,
                "previous_status": row["status"]
            })

            now = datetime.now(timezone.utc).isoformat()
            conn.execute("""
                UPDATE mailboxes SET status = 'suspended', updated_at = ?
                WHERE email = ?
            """, (now, email))
            conn.commit()

            self._log_event(email, MailboxEvent.SUSPEND, actor, {
                "reason": reason
            }, receipt_id)

            return MailboxResult(
                success=True,
                email=email,
                status=MailboxStatus.SUSPENDED,
                message="Mailbox suspended",
                receipt_id=receipt_id
            )
        finally:
            conn.close()

    def restore(
        self,
        email: str,
        actor: str = "system@windi-domain.com"
    ) -> MailboxResult:
        """Restore suspended mailbox."""
        conn = self._conn()
        try:
            row = conn.execute(
                "SELECT * FROM mailboxes WHERE email = ?",
                (email,)
            ).fetchone()

            if not row:
                return MailboxResult(
                    success=False,
                    email=email,
                    status=MailboxStatus.PENDING,
                    message="Mailbox not found"
                )

            if row["status"] != "suspended":
                return MailboxResult(
                    success=False,
                    email=email,
                    status=MailboxStatus(row["status"]),
                    message=f"Cannot restore: status is {row['status']}, expected suspended"
                )

            receipt_id = self._emit_receipt("RESTORE", email, {
                "actor": actor
            })

            now = datetime.now(timezone.utc).isoformat()
            conn.execute("""
                UPDATE mailboxes SET status = 'active', updated_at = ?
                WHERE email = ?
            """, (now, email))
            conn.commit()

            self._log_event(email, MailboxEvent.RESTORE, actor, {}, receipt_id)

            return MailboxResult(
                success=True,
                email=email,
                status=MailboxStatus.ACTIVE,
                message="Mailbox restored",
                receipt_id=receipt_id
            )
        finally:
            conn.close()

    def revoke(
        self,
        email: str,
        reason: str,
        actor: str = "system@windi-domain.com"
    ) -> MailboxResult:
        """Permanently revoke mailbox (IRREMEDIABLE)."""
        conn = self._conn()
        try:
            row = conn.execute(
                "SELECT * FROM mailboxes WHERE email = ?",
                (email,)
            ).fetchone()

            if not row:
                return MailboxResult(
                    success=False,
                    email=email,
                    status=MailboxStatus.PENDING,
                    message="Mailbox not found"
                )

            if row["status"] == "legal_hold":
                return MailboxResult(
                    success=False,
                    email=email,
                    status=MailboxStatus.LEGAL_HOLD,
                    message="Cannot revoke: under legal hold"
                )

            receipt_id = self._emit_receipt("REVOKE", email, {
                "actor": actor,
                "reason": reason,
                "previous_status": row["status"],
                "irremediable": True
            })

            now = datetime.now(timezone.utc).isoformat()
            conn.execute("""
                UPDATE mailboxes SET status = 'revoked', updated_at = ?
                WHERE email = ?
            """, (now, email))
            conn.commit()

            self._log_event(email, MailboxEvent.REVOKE, actor, {
                "reason": reason,
                "irremediable": True
            }, receipt_id)

            return MailboxResult(
                success=True,
                email=email,
                status=MailboxStatus.REVOKED,
                message="Mailbox permanently revoked (IRREMEDIABLE)",
                receipt_id=receipt_id
            )
        finally:
            conn.close()

    def apply_legal_hold(
        self,
        email: str,
        case_reference: str,
        actor: str = "system@windi-domain.com"
    ) -> MailboxResult:
        """Apply legal hold (freezes mailbox, prevents modification/deletion)."""
        conn = self._conn()
        try:
            row = conn.execute(
                "SELECT * FROM mailboxes WHERE email = ?",
                (email,)
            ).fetchone()

            if not row:
                return MailboxResult(
                    success=False,
                    email=email,
                    status=MailboxStatus.PENDING,
                    message="Mailbox not found"
                )

            receipt_id = self._emit_receipt("LEGAL-HOLD", email, {
                "actor": actor,
                "case_reference": case_reference,
                "previous_status": row["status"]
            })

            now = datetime.now(timezone.utc).isoformat()
            conn.execute("""
                UPDATE mailboxes
                SET status = 'legal_hold', legal_hold_receipt_id = ?, updated_at = ?
                WHERE email = ?
            """, (receipt_id, now, email))
            conn.commit()

            self._log_event(email, MailboxEvent.LEGAL_HOLD, actor, {
                "case_reference": case_reference
            }, receipt_id)

            return MailboxResult(
                success=True,
                email=email,
                status=MailboxStatus.LEGAL_HOLD,
                message=f"Legal hold applied. Case: {case_reference}",
                receipt_id=receipt_id
            )
        finally:
            conn.close()

    def update_tier(
        self,
        email: str,
        new_tier: str,
        actor: str = "system@windi-domain.com"
    ) -> MailboxResult:
        """Change mailbox tier (upgrade or downgrade)."""
        if new_tier not in TIER_QUOTAS:
            return MailboxResult(
                success=False,
                email=email,
                status=MailboxStatus.PENDING,
                message=f"Invalid tier: {new_tier}"
            )

        conn = self._conn()
        try:
            row = conn.execute(
                "SELECT * FROM mailboxes WHERE email = ?",
                (email,)
            ).fetchone()

            if not row:
                return MailboxResult(
                    success=False,
                    email=email,
                    status=MailboxStatus.PENDING,
                    message="Mailbox not found"
                )

            if row["status"] == "legal_hold":
                return MailboxResult(
                    success=False,
                    email=email,
                    status=MailboxStatus.LEGAL_HOLD,
                    message="Cannot change tier: under legal hold"
                )

            old_tier = row["tier"]
            old_quota = row["quota_mb"]
            new_quota = TIER_QUOTAS[new_tier]

            is_upgrade = new_quota > old_quota
            event_type = MailboxEvent.TIER_UPGRADE if is_upgrade else MailboxEvent.TIER_DOWNGRADE

            receipt_id = self._emit_receipt(
                "TIER-UPGRADE" if is_upgrade else "TIER-DOWNGRADE",
                email,
                {
                    "actor": actor,
                    "old_tier": old_tier,
                    "new_tier": new_tier,
                    "old_quota_mb": old_quota,
                    "new_quota_mb": new_quota
                }
            )

            now = datetime.now(timezone.utc).isoformat()
            conn.execute("""
                UPDATE mailboxes
                SET tier = ?, quota_mb = ?, updated_at = ?
                WHERE email = ?
            """, (new_tier, new_quota, now, email))
            conn.commit()

            self._log_event(email, event_type, actor, {
                "old_tier": old_tier,
                "new_tier": new_tier,
                "old_quota_mb": old_quota,
                "new_quota_mb": new_quota
            }, receipt_id)

            action = "upgraded" if is_upgrade else "downgraded"
            return MailboxResult(
                success=True,
                email=email,
                status=MailboxStatus(row["status"]),
                message=f"Tier {action}: {old_tier} → {new_tier} ({old_quota}MB → {new_quota}MB)",
                receipt_id=receipt_id,
                quota_mb=new_quota
            )
        finally:
            conn.close()

    def check_quota(self, email: str) -> MailboxResult:
        """Check quota status and emit warning if needed."""
        conn = self._conn()
        try:
            row = conn.execute(
                "SELECT * FROM mailboxes WHERE email = ?",
                (email,)
            ).fetchone()

            if not row:
                return MailboxResult(
                    success=False,
                    email=email,
                    status=MailboxStatus.PENDING,
                    message="Mailbox not found"
                )

            used = row["used_mb"]
            quota = row["quota_mb"]
            percent = (used / quota * 100) if quota > 0 else 0

            if percent >= 100:
                # Emit quota exceeded event
                receipt_id = self._emit_receipt("QUOTA-EXCEEDED", email, {
                    "used_mb": used,
                    "quota_mb": quota,
                    "percent": percent
                })
                self._log_event(email, MailboxEvent.QUOTA_EXCEEDED, "system", {
                    "used_mb": used,
                    "quota_mb": quota
                }, receipt_id)

                return MailboxResult(
                    success=True,
                    email=email,
                    status=MailboxStatus(row["status"]),
                    message=f"QUOTA EXCEEDED: {used:.1f}MB / {quota}MB ({percent:.1f}%)",
                    receipt_id=receipt_id,
                    quota_mb=quota,
                    used_mb=used
                )

            elif percent >= 80:
                # Emit warning
                receipt_id = self._emit_receipt("QUOTA-WARNING", email, {
                    "used_mb": used,
                    "quota_mb": quota,
                    "percent": percent
                })
                self._log_event(email, MailboxEvent.QUOTA_WARNING, "system", {
                    "used_mb": used,
                    "quota_mb": quota
                }, receipt_id)

                return MailboxResult(
                    success=True,
                    email=email,
                    status=MailboxStatus(row["status"]),
                    message=f"QUOTA WARNING: {used:.1f}MB / {quota}MB ({percent:.1f}%)",
                    receipt_id=receipt_id,
                    quota_mb=quota,
                    used_mb=used
                )

            return MailboxResult(
                success=True,
                email=email,
                status=MailboxStatus(row["status"]),
                message=f"OK: {used:.1f}MB / {quota}MB ({percent:.1f}%)",
                quota_mb=quota,
                used_mb=used
            )
        finally:
            conn.close()


# ═══════════════════════════════════════════════════════════════════════════
# SINGLETON + HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

_manager: Optional[MailboxManager] = None

def get_mailbox_manager() -> MailboxManager:
    """Get singleton mailbox manager."""
    global _manager
    if _manager is None:
        _manager = MailboxManager()
    return _manager

def provision_mailbox_pre(
    slug: str,
    wallet_id: str,
    domain: str = "windisites.de",
    tier: str = "FREE",
    actor: str = "system@windi-domain.com"
) -> MailboxResult:
    """Convenience wrapper for PRE phase."""
    return get_mailbox_manager().provision_pre(slug, wallet_id, domain, tier, actor)

def provision_mailbox_post(
    email: str,
    password_hash: Optional[str] = None,
    actor: str = "system@windi-domain.com"
) -> MailboxResult:
    """Convenience wrapper for POST phase."""
    return get_mailbox_manager().provision_post(email, password_hash, actor)

def get_mailbox(email: str) -> Optional[MailboxInfo]:
    """Get mailbox info."""
    return get_mailbox_manager().get_mailbox(email)

def get_mailboxes_by_wallet(wallet_id: str) -> List[MailboxInfo]:
    """Get all mailboxes for wallet."""
    return get_mailbox_manager().get_mailboxes_by_wallet(wallet_id)
