"""
WINDI Governance Event Log v1.0
Central logging of all governance decisions, identity detections, and level changes.

Purpose:
- Auditoria interna (internal audit trail)
- Melhoria de regras (rule improvement feedback)
- Prova de diligência (proof of diligence)

Storage: SQLite for structured queries + JSON export capability.
"""

import sqlite3
import json
import os
import hashlib
from datetime import datetime, timezone
from typing import Optional


EVENT_LOG_DB = os.environ.get(
    "WINDI_EVENT_LOG_DB",
    "/opt/windi/forensic/governance_events.db"
)


class GovernanceEventLog:
    """Central governance event logging system."""

    EVENT_TYPES = [
        "level_assigned",
        "level_upgraded",
        "level_downgrade_blocked",
        "identity_detected",
        "identity_license_checked",
        "document_submitted",
        "document_approved",
        "document_blocked",
        "advisor_triggered",
        "policy_version_changed",
        "isp_loaded",
        "isp_created",
        "health_check",
        "registry_entry_created",
        "integrity_verified",
        "integrity_failed"
    ]

    def __init__(self, db_path: str = None):
        self.db_path = db_path or EVENT_LOG_DB
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize the event log database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS governance_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT UNIQUE NOT NULL,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                document_id TEXT,
                governance_level TEXT,
                isp_name TEXT,
                institution_id TEXT,
                institution_name TEXT,
                identity_license_status TEXT,
                action_taken TEXT NOT NULL,
                reason TEXT,
                details_json TEXT,
                policy_version TEXT,
                event_hash TEXT NOT NULL,
                previous_hash TEXT
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_timestamp
            ON governance_events(timestamp)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_type
            ON governance_events(event_type)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_document
            ON governance_events(document_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_institution
            ON governance_events(institution_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_level
            ON governance_events(governance_level)
        """)

        conn.commit()
        conn.close()

    def _get_last_hash(self) -> str:
        """Get the hash of the last event for chain integrity."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT event_hash FROM governance_events ORDER BY id DESC LIMIT 1"
        )
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else "GENESIS"

    def _compute_event_hash(self, event_data: dict, previous_hash: str) -> str:
        """Compute SHA-256 hash for event chain integrity."""
        payload = json.dumps(event_data, sort_keys=True) + previous_hash
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

    def _generate_event_id(self, event_type: str) -> str:
        """Generate unique event ID."""
        now = datetime.now(timezone.utc)
        ts = now.strftime("%Y%m%d%H%M%S%f")[:18]
        prefix = event_type.upper()[:4]
        return f"EVT-{prefix}-{ts}"

    def log_event(
        self,
        event_type: str,
        action_taken: str,
        document_id: str = None,
        governance_level: str = None,
        isp_name: str = None,
        institution_id: str = None,
        institution_name: str = None,
        identity_license_status: str = None,
        reason: str = None,
        details: dict = None,
        policy_version: str = None
    ) -> dict:
        """Log a governance event."""
        if event_type not in self.EVENT_TYPES:
            return {"success": False, "error": f"Unknown event type: {event_type}"}

        now = datetime.now(timezone.utc).isoformat()
        event_id = self._generate_event_id(event_type)
        previous_hash = self._get_last_hash()

        event_data = {
            "event_id": event_id,
            "timestamp": now,
            "event_type": event_type,
            "document_id": document_id,
            "governance_level": governance_level,
            "action_taken": action_taken,
            "policy_version": policy_version
        }

        event_hash = self._compute_event_hash(event_data, previous_hash)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO governance_events (
                    event_id, timestamp, event_type, document_id,
                    governance_level, isp_name, institution_id, institution_name,
                    identity_license_status, action_taken, reason,
                    details_json, policy_version, event_hash, previous_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_id, now, event_type, document_id,
                governance_level, isp_name, institution_id, institution_name,
                identity_license_status, action_taken, reason,
                json.dumps(details) if details else None,
                policy_version, event_hash, previous_hash
            ))
            conn.commit()

            return {
                "success": True,
                "event_id": event_id,
                "event_hash": event_hash,
                "timestamp": now
            }
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def query_events(
        self,
        event_type: str = None,
        document_id: str = None,
        institution_id: str = None,
        governance_level: str = None,
        since: str = None,
        until: str = None,
        limit: int = 100
    ) -> list:
        """Query events with filters."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        conditions = []
        params = []

        if event_type:
            conditions.append("event_type = ?")
            params.append(event_type)
        if document_id:
            conditions.append("document_id = ?")
            params.append(document_id)
        if institution_id:
            conditions.append("institution_id = ?")
            params.append(institution_id)
        if governance_level:
            conditions.append("governance_level = ?")
            params.append(governance_level)
        if since:
            conditions.append("timestamp >= ?")
            params.append(since)
        if until:
            conditions.append("timestamp <= ?")
            params.append(until)

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        query = f"""
            SELECT * FROM governance_events
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT ?
        """
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_event_stats(self) -> dict:
        """Get aggregate statistics for dashboard."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM governance_events")
        total = cursor.fetchone()[0]

        cursor.execute("""
            SELECT event_type, COUNT(*) as count
            FROM governance_events
            GROUP BY event_type
            ORDER BY count DESC
        """)
        by_type = {row[0]: row[1] for row in cursor.fetchall()}

        cursor.execute("""
            SELECT governance_level, COUNT(*) as count
            FROM governance_events
            WHERE governance_level IS NOT NULL
            GROUP BY governance_level
        """)
        by_level = {row[0]: row[1] for row in cursor.fetchall()}

        cursor.execute("""
            SELECT institution_name, COUNT(*) as count
            FROM governance_events
            WHERE institution_name IS NOT NULL
            GROUP BY institution_name
            ORDER BY count DESC
            LIMIT 10
        """)
        top_institutions = {row[0]: row[1] for row in cursor.fetchall()}

        cursor.execute("""
            SELECT COUNT(*) FROM governance_events
            WHERE action_taken = 'blocked'
        """)
        blocked_count = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM governance_events
            WHERE event_type = 'level_upgraded'
        """)
        upgrades = cursor.fetchone()[0]

        cursor.execute("""
            SELECT MIN(timestamp), MAX(timestamp) FROM governance_events
        """)
        time_range = cursor.fetchone()

        conn.close()

        return {
            "total_events": total,
            "events_by_type": by_type,
            "events_by_level": by_level,
            "top_institutions": top_institutions,
            "blocked_count": blocked_count,
            "upgrade_count": upgrades,
            "earliest_event": time_range[0],
            "latest_event": time_range[1]
        }

    def verify_chain_integrity(self) -> dict:
        """Verify the hash chain integrity of the event log."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM governance_events ORDER BY id ASC")
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return {"valid": True, "events_checked": 0, "message": "Empty log"}

        expected_previous = "GENESIS"
        broken_at = None

        for row in rows:
            row_dict = dict(row)
            if row_dict["previous_hash"] != expected_previous:
                broken_at = row_dict["event_id"]
                break
            expected_previous = row_dict["event_hash"]

        return {
            "valid": broken_at is None,
            "events_checked": len(rows),
            "broken_at": broken_at,
            "message": "Chain intact" if broken_at is None else f"Chain broken at {broken_at}"
        }

    def export_json(self, filepath: str = None, limit: int = 1000) -> str:
        """Export events as JSON for backup or analysis."""
        events = self.query_events(limit=limit)
        output = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "total_events": len(events),
            "events": events
        }
        if filepath:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(output, f, indent=2, ensure_ascii=False)
            return filepath
        return json.dumps(output, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    db_path = os.path.join(os.path.dirname(__file__), "..", "forensic", "governance_events_test.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    log = GovernanceEventLog(db_path=db_path)

    print("=" * 60)
    print("WINDI Governance Event Log v1.0 - Test")
    print("=" * 60)

    r1 = log.log_event(
        event_type="identity_detected",
        action_taken="detected",
        institution_id="INST-DE-DB-001",
        institution_name="Deutsche Bahn AG",
        governance_level="LOW",
        reason="Automatic detection in document text",
        policy_version="WINDI-GOV-2.1.0"
    )
    print(f"Event 1: {r1}")

    r2 = log.log_event(
        event_type="level_upgraded",
        action_taken="upgraded",
        document_id="DOC-TEST-001",
        institution_id="INST-DE-DB-001",
        institution_name="Deutsche Bahn AG",
        governance_level="MEDIUM",
        identity_license_status="model_only",
        reason="Real institution detected, auto-upgrade LOW->MEDIUM",
        policy_version="WINDI-GOV-2.1.0"
    )
    print(f"Event 2: {r2}")

    r3 = log.log_event(
        event_type="advisor_triggered",
        action_taken="user_notified",
        document_id="DOC-TEST-001",
        governance_level="MEDIUM",
        reason="Governance Advisor recommended MEDIUM for Deutsche Bahn document",
        policy_version="WINDI-GOV-2.1.0"
    )
    print(f"Event 3: {r3}")

    stats = log.get_event_stats()
    print(f"\nStats: {json.dumps(stats, indent=2)}")

    integrity = log.verify_chain_integrity()
    print(f"\nChain Integrity: {integrity}")

    os.remove(db_path)
    print("\nTest DB cleaned up.")
