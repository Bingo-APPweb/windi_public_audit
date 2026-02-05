"""
WINDI Medium Registry v1.0
Lightweight institutional registry for MEDIUM-level documents.

Design philosophy:
- LOW = No registration (free flow)
- MEDIUM = Institutional Registry (lightweight traceability)
- HIGH = Forensic Registry (full submission chain with REG- IDs)

MEDIUM Registry captures:
- Date, ISP, Level, Identity Governance, Short Hash
- NO Submission ID (reserved for HIGH)
- NO full forensic chain
- YES institutional traceability
"""

import sqlite3
import json
import hashlib
import os
from datetime import datetime, timezone
from typing import Optional


MEDIUM_REGISTRY_DB = os.environ.get(
    "WINDI_MEDIUM_REGISTRY_DB",
    "/opt/windi/forensic/medium_registry.db"
)


class MediumRegistry:
    """Lightweight registry for MEDIUM governance documents."""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or MEDIUM_REGISTRY_DB
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize the medium registry database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS medium_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_id TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL,
                isp_name TEXT,
                isp_version TEXT,
                governance_level TEXT DEFAULT 'MEDIUM',
                institution_id TEXT,
                institution_name TEXT,
                institution_type TEXT,
                institution_country TEXT,
                identity_license_status TEXT,
                disclaimer_included BOOLEAN DEFAULT 1,
                logo_used BOOLEAN DEFAULT 0,
                document_type TEXT,
                policy_version TEXT,
                content_hash_short TEXT NOT NULL,
                metadata_json TEXT,
                notes TEXT
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_medium_date
            ON medium_entries(created_at)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_medium_isp
            ON medium_entries(isp_name)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_medium_institution
            ON medium_entries(institution_id)
        """)

        conn.commit()
        conn.close()

    def _generate_entry_id(self) -> str:
        """Generate lightweight entry ID (not REG- which is reserved for HIGH)."""
        now = datetime.now(timezone.utc)
        return f"MED-{now.strftime('%Y%m%d')}-{now.strftime('%H%M%S%f')[:10]}"

    def _compute_short_hash(self, content: str) -> str:
        """Compute short hash (8 chars) for lightweight verification."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:8]

    def register(
        self,
        content: str,
        isp_name: str = None,
        isp_version: str = None,
        institution_id: str = None,
        institution_name: str = None,
        institution_type: str = None,
        institution_country: str = None,
        identity_license_status: str = None,
        disclaimer_included: bool = True,
        logo_used: bool = False,
        document_type: str = None,
        policy_version: str = None,
        metadata: dict = None,
        notes: str = None
    ) -> dict:
        """Register a MEDIUM document in the lightweight registry."""
        entry_id = self._generate_entry_id()
        content_hash = self._compute_short_hash(content)
        now = datetime.now(timezone.utc).isoformat()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO medium_entries (
                    entry_id, created_at, isp_name, isp_version,
                    governance_level, institution_id, institution_name,
                    institution_type, institution_country,
                    identity_license_status, disclaimer_included, logo_used,
                    document_type, policy_version, content_hash_short,
                    metadata_json, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry_id, now, isp_name, isp_version,
                "MEDIUM", institution_id, institution_name,
                institution_type, institution_country,
                identity_license_status, disclaimer_included, logo_used,
                document_type, policy_version, content_hash,
                json.dumps(metadata) if metadata else None, notes
            ))
            conn.commit()

            return {
                "success": True,
                "entry_id": entry_id,
                "content_hash_short": content_hash,
                "created_at": now,
                "governance_level": "MEDIUM",
                "identity_governance": {
                    "institution": institution_name,
                    "license_status": identity_license_status,
                    "disclaimer": disclaimer_included,
                    "logo": logo_used
                }
            }
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def lookup(self, entry_id: str) -> Optional[dict]:
        """Look up a registry entry."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM medium_entries WHERE entry_id = ?", (entry_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def verify_content(self, entry_id: str, content: str) -> dict:
        """Verify content matches the registered hash."""
        entry = self.lookup(entry_id)
        if not entry:
            return {"valid": False, "error": "Entry not found"}

        current_hash = self._compute_short_hash(content)
        matches = current_hash == entry["content_hash_short"]

        return {
            "valid": matches,
            "entry_id": entry_id,
            "registered_hash": entry["content_hash_short"],
            "current_hash": current_hash,
            "message": "Content verified" if matches else "Content has been modified"
        }

    def list_entries(
        self,
        isp_name: str = None,
        institution_id: str = None,
        since: str = None,
        limit: int = 50
    ) -> list:
        """List registry entries with optional filters."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        conditions = []
        params = []

        if isp_name:
            conditions.append("isp_name = ?")
            params.append(isp_name)
        if institution_id:
            conditions.append("institution_id = ?")
            params.append(institution_id)
        if since:
            conditions.append("created_at >= ?")
            params.append(since)

        where = " AND ".join(conditions) if conditions else "1=1"
        cursor.execute(
            f"SELECT * FROM medium_entries WHERE {where} ORDER BY created_at DESC LIMIT ?",
            params + [limit]
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_stats(self) -> dict:
        """Registry statistics for dashboard."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM medium_entries")
        total = cursor.fetchone()[0]

        cursor.execute("""
            SELECT isp_name, COUNT(*) FROM medium_entries
            WHERE isp_name IS NOT NULL GROUP BY isp_name
        """)
        by_isp = {r[0]: r[1] for r in cursor.fetchall()}

        cursor.execute("""
            SELECT institution_name, COUNT(*) FROM medium_entries
            WHERE institution_name IS NOT NULL GROUP BY institution_name
            ORDER BY COUNT(*) DESC LIMIT 10
        """)
        by_institution = {r[0]: r[1] for r in cursor.fetchall()}

        cursor.execute("""
            SELECT identity_license_status, COUNT(*) FROM medium_entries
            WHERE identity_license_status IS NOT NULL GROUP BY identity_license_status
        """)
        by_license = {r[0]: r[1] for r in cursor.fetchall()}

        cursor.execute("""
            SELECT document_type, COUNT(*) FROM medium_entries
            WHERE document_type IS NOT NULL GROUP BY document_type
        """)
        by_doc_type = {r[0]: r[1] for r in cursor.fetchall()}

        conn.close()

        return {
            "total_entries": total,
            "by_isp": by_isp,
            "by_institution": by_institution,
            "by_license_status": by_license,
            "by_document_type": by_doc_type
        }

    def generate_governance_statement(self, entry_id: str) -> Optional[dict]:
        """
        Generate a Governance Statement (Proof of Governance) for a MEDIUM entry.
        This is NOT a forensic certificate. It is an institutional governance attestation.
        """
        entry = self.lookup(entry_id)
        if not entry:
            return None

        statement = {
            "type": "WINDI Governance Statement",
            "level": "MEDIUM",
            "entry_id": entry["entry_id"],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "institution": entry.get("institution_name", "Not specified"),
            "identity_governance": {
                "mode": "institutional_simulation",
                "license_status": entry.get("identity_license_status", "unknown"),
                "disclaimer_included": bool(entry.get("disclaimer_included", True)),
                "logo_used": bool(entry.get("logo_used", False))
            },
            "policy_version": entry.get("policy_version", "unknown"),
            "content_hash": entry.get("content_hash_short", ""),
            "isp": entry.get("isp_name", "none"),
            "statement": {
                "de": (
                    "Dieses Dokument wurde unter WINDI-Governance der Stufe MEDIUM erstellt. "
                    "Es simuliert institutionelle Identität und enthält die entsprechenden Haftungsausschlüsse."
                ),
                "en": (
                    "This document was created under WINDI MEDIUM governance. "
                    "It simulates institutional identity and includes appropriate disclaimers."
                ),
                "pt": (
                    "Este documento foi criado sob governança WINDI nível MEDIUM. "
                    "Simula identidade institucional e inclui os disclaimers apropriados."
                )
            }
        }

        statement_json = json.dumps(statement, sort_keys=True)
        statement["statement_hash"] = hashlib.sha256(
            statement_json.encode("utf-8")
        ).hexdigest()[:12]

        return statement


if __name__ == "__main__":
    db_path = os.path.join(os.path.dirname(__file__), "..", "forensic", "medium_registry_test.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    registry = MediumRegistry(db_path=db_path)

    print("=" * 60)
    print("WINDI Medium Registry v1.0 - Test")
    print("=" * 60)

    result = registry.register(
        content="Sehr geehrte Deutsche Bahn, hiermit teilen wir Ihnen mit...",
        isp_name="Deutsche Bahn",
        isp_version="1.0",
        institution_id="INST-DE-DB-001",
        institution_name="Deutsche Bahn AG",
        institution_type="public_enterprise",
        institution_country="DE",
        identity_license_status="model_only",
        document_type="institutional_letter",
        policy_version="WINDI-GOV-2.1.0",
        metadata={"template": "carta_institucional", "lang": "de"}
    )
    print(f"Registration: {json.dumps(result, indent=2)}")

    if result["success"]:
        stmt = registry.generate_governance_statement(result["entry_id"])
        print(f"\nGovernance Statement:\n{json.dumps(stmt, indent=2)}")

        verify = registry.verify_content(
            result["entry_id"],
            "Sehr geehrte Deutsche Bahn, hiermit teilen wir Ihnen mit..."
        )
        print(f"\nVerification: {verify}")

    stats = registry.get_stats()
    print(f"\nStats: {json.dumps(stats, indent=2)}")

    os.remove(db_path)
    print("\nTest DB cleaned up.")
