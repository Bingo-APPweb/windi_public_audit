#!/usr/bin/env python3
"""
WINDI Maestro Agent v1.0.0 — Governance Orchestrator
=====================================================
Third Institutional Pillar: RESOLUTION

Routes governance findings to resolution channels, tracks SLA compliance,
escalates breaches, and closes governance cycles with forensic proof.

Principle: AI processes. Human decides. WINDI guarantees.

Governance Cycle:
    Finding Detected → Sentinela (detect) → Maestro (route)
    → Human (decide) → Maestro (close) → Forensic Ledger

NON-Capabilities (Constitutional Constraints):
    - Does NOT decide resolution (Human decides — I1)
    - Does NOT validate compliance (Sentinela's domain)
    - Does NOT modify ISP profiles (ISP Manager's domain)

Version: 1.1.0 (with DecisionRouter, SLAGuardian, ResolutionAssembler)
Created: 2026-02-08
Author: WINDI Publishing House / Three Dragons Protocol
"""

import json
import os
import sys
import hashlib
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

# ============================================================================
# CONFIGURATION
# ============================================================================

VERSION = "1.2.0"
AGENT_ID = "windi://agent/core/maestro"
CODENAME = "Maestro"
PILLAR = "RESOLUTION"

# Base paths
AGENT_BASE = Path("/opt/windi/agents/maestro")
AGENTS_ROOT = Path("/opt/windi/agents")
ISP_LIBRARY = Path("/opt/windi/isp")
ENGINE_PATH = Path("/opt/windi/engine")

# Output directories
RESOLUTIONS_DIR = AGENT_BASE / "resolutions"
ESCALATIONS_DIR = AGENT_BASE / "escalations"
RECEIPTS_DIR = AGENT_BASE / "receipts"
REPORTS_DIR = AGENT_BASE / "reports"
STATE_DIR = AGENT_BASE / "state"

# Peer agent paths
SENTINELA_FINDINGS = AGENTS_ROOT / "sentinela" / "findings"
SENTINELA_RECEIPTS = AGENTS_ROOT / "sentinela" / "receipts"
ISP_MANAGER_ALERTS = AGENTS_ROOT / "isp-manager" / "alerts"

# SLA Configuration (from capsule.json)
SLA_ACKNOWLEDGE = {
    "R0": timedelta(hours=48), "R1": timedelta(hours=48),
    "R2": timedelta(hours=24), "R3": timedelta(hours=24),
    "R4": timedelta(hours=4),  "R5": timedelta(hours=1),
}
SLA_RESOLVE = {
    "R0": timedelta(days=30), "R1": timedelta(days=30),
    "R2": timedelta(days=14), "R3": timedelta(days=14),
    "R4": timedelta(days=7),  "R5": timedelta(days=2),
}

ESCALATION_THRESHOLD_PCT = 0.80  # Warn at 80% of resolve SLA


# ============================================================================
# FORENSIC RECEIPT GENERATOR
# ============================================================================

class ForensicReceipt:
    """Generates immutable forensic receipts for every Maestro action."""

    @staticmethod
    def generate(action: str, details: Dict, finding_id: str = None) -> Dict:
        timestamp = datetime.now(timezone.utc).isoformat()
        payload = json.dumps({
            "agent_id": AGENT_ID,
            "action": action,
            "finding_id": finding_id,
            "details": details,
            "timestamp": timestamp,
        }, sort_keys=True)

        receipt = {
            "receipt_id": f"MAESTRO-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{hashlib.sha256(payload.encode()).hexdigest()[:8]}",
            "agent_id": AGENT_ID,
            "version": VERSION,
            "action": action,
            "finding_id": finding_id,
            "details": details,
            "timestamp": timestamp,
            "integrity_hash": hashlib.sha256(payload.encode()).hexdigest(),
            "invariante_i9": True,
            "auto_apply": False,
        }
        return receipt

    @staticmethod
    def save(receipt: Dict):
        RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
        filename = f"{receipt['receipt_id']}.json"
        filepath = RECEIPTS_DIR / filename
        with open(filepath, 'w') as f:
            json.dump(receipt, f, indent=2, ensure_ascii=False)
        return filepath


# ============================================================================
# GOVERNANCE CYCLE STATE
# ============================================================================

class GovernanceCycleState:
    """
    Manages the state of governance resolution cycles.
    
    State transitions:
        OPEN → ACKNOWLEDGED → IN_PROGRESS → RESOLVED → CLOSED
                                          → ESCALATED → RESOLVED → CLOSED
    
    Uses SQLite for persistent state (file-based, no server needed).
    """

    VALID_STATUSES = [
        "OPEN", "ACKNOWLEDGED", "IN_PROGRESS",
        "RESOLVED", "ESCALATED", "CLOSED"
    ]

    def __init__(self, db_path: Path = None):
        self.db_path = db_path or (STATE_DIR / "maestro_state.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS governance_cycles (
                    finding_id TEXT PRIMARY KEY,
                    source_agent TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    category TEXT DEFAULT '',
                    summary TEXT DEFAULT '',
                    status TEXT DEFAULT 'OPEN',
                    assigned_to TEXT DEFAULT '',
                    resolution_note TEXT DEFAULT '',
                    sla_acknowledge_deadline TEXT,
                    sla_resolve_deadline TEXT,
                    created_at TEXT NOT NULL,
                    acknowledged_at TEXT,
                    resolved_at TEXT,
                    closed_at TEXT,
                    escalated_at TEXT,
                    escalation_count INTEGER DEFAULT 0,
                    receipt_chain TEXT DEFAULT '[]'
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cycle_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    finding_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    event_data TEXT DEFAULT '{}',
                    timestamp TEXT NOT NULL,
                    receipt_id TEXT,
                    FOREIGN KEY (finding_id) REFERENCES governance_cycles(finding_id)
                )
            """)
            conn.commit()

    def register_finding(self, finding: Dict) -> Dict:
        """Register a new finding from Sentinela and open a governance cycle."""
        finding_id = finding.get("finding_id", f"FND-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}")
        severity = finding.get("severity", "R2")
        now = datetime.now(timezone.utc)

        ack_deadline = now + SLA_ACKNOWLEDGE.get(severity, timedelta(hours=24))
        resolve_deadline = now + SLA_RESOLVE.get(severity, timedelta(days=14))

        with sqlite3.connect(str(self.db_path)) as conn:
            try:
                conn.execute("""
                    INSERT INTO governance_cycles 
                    (finding_id, source_agent, severity, category, summary, status,
                     sla_acknowledge_deadline, sla_resolve_deadline, created_at)
                    VALUES (?, ?, ?, ?, ?, 'OPEN', ?, ?, ?)
                """, (
                    finding_id,
                    finding.get("source_agent", "sentinela"),
                    severity,
                    finding.get("category", ""),
                    finding.get("summary", ""),
                    ack_deadline.isoformat(),
                    resolve_deadline.isoformat(),
                    now.isoformat(),
                ))
                conn.execute("""
                    INSERT INTO cycle_events (finding_id, event_type, event_data, timestamp)
                    VALUES (?, 'REGISTERED', ?, ?)
                """, (finding_id, json.dumps(finding), now.isoformat()))
                conn.commit()
            except sqlite3.IntegrityError:
                return {"error": f"Finding {finding_id} already registered", "finding_id": finding_id}

        # Determine routing channel
        channel = self._determine_channel(severity)

        result = {
            "finding_id": finding_id,
            "status": "OPEN",
            "severity": severity,
            "routed_to": channel,
            "sla_acknowledge": ack_deadline.isoformat(),
            "sla_resolve": resolve_deadline.isoformat(),
            "action_required": "HUMAN_ACKNOWLEDGE",
            "auto_apply": False,
        }

        # Generate receipt
        receipt = ForensicReceipt.generate("ROUTE_FINDING", result, finding_id)
        ForensicReceipt.save(receipt)
        self._append_receipt(finding_id, receipt["receipt_id"])

        return result

    def acknowledge(self, finding_id: str, acknowledged_by: str) -> Dict:
        """Record human acknowledgment of a finding."""
        now = datetime.now(timezone.utc)
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute(
                "SELECT status, severity FROM governance_cycles WHERE finding_id = ?",
                (finding_id,)
            )
            row = cursor.fetchone()
            if not row:
                return {"error": f"Finding {finding_id} not found"}
            if row[0] not in ("OPEN", "ESCALATED"):
                return {"error": f"Finding {finding_id} is {row[0]}, cannot acknowledge"}

            conn.execute("""
                UPDATE governance_cycles 
                SET status = 'ACKNOWLEDGED', acknowledged_at = ?, assigned_to = ?
                WHERE finding_id = ?
            """, (now.isoformat(), acknowledged_by, finding_id))
            conn.execute("""
                INSERT INTO cycle_events (finding_id, event_type, event_data, timestamp)
                VALUES (?, 'ACKNOWLEDGED', ?, ?)
            """, (finding_id, json.dumps({"by": acknowledged_by}), now.isoformat()))
            conn.commit()

        result = {
            "finding_id": finding_id,
            "status": "ACKNOWLEDGED",
            "acknowledged_by": acknowledged_by,
            "timestamp": now.isoformat(),
            "auto_apply": False,
        }
        receipt = ForensicReceipt.generate("ACKNOWLEDGE", result, finding_id)
        ForensicReceipt.save(receipt)
        self._append_receipt(finding_id, receipt["receipt_id"])
        return result

    def resolve(self, finding_id: str, resolution_note: str, resolved_by: str) -> Dict:
        """Record human resolution decision. Maestro does NOT decide — only records."""
        now = datetime.now(timezone.utc)
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute(
                "SELECT status FROM governance_cycles WHERE finding_id = ?",
                (finding_id,)
            )
            row = cursor.fetchone()
            if not row:
                return {"error": f"Finding {finding_id} not found"}
            if row[0] not in ("ACKNOWLEDGED", "IN_PROGRESS", "ESCALATED"):
                return {"error": f"Finding {finding_id} is {row[0]}, cannot resolve"}

            conn.execute("""
                UPDATE governance_cycles 
                SET status = 'RESOLVED', resolution_note = ?, resolved_at = ?, assigned_to = ?
                WHERE finding_id = ?
            """, (resolution_note, now.isoformat(), resolved_by, finding_id))
            conn.execute("""
                INSERT INTO cycle_events (finding_id, event_type, event_data, timestamp)
                VALUES (?, 'RESOLVED', ?, ?)
            """, (finding_id, json.dumps({
                "by": resolved_by, "note": resolution_note
            }), now.isoformat()))
            conn.commit()

        result = {
            "finding_id": finding_id,
            "status": "RESOLVED",
            "resolved_by": resolved_by,
            "resolution_note": resolution_note,
            "timestamp": now.isoformat(),
            "auto_apply": False,
        }
        receipt = ForensicReceipt.generate("RESOLVE", result, finding_id)
        ForensicReceipt.save(receipt)
        self._append_receipt(finding_id, receipt["receipt_id"])
        return result

    def close_cycle(self, finding_id: str, closed_by: str) -> Dict:
        """Close a governance cycle after resolution is verified."""
        now = datetime.now(timezone.utc)
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute(
                "SELECT status, severity, created_at, resolved_at, receipt_chain FROM governance_cycles WHERE finding_id = ?",
                (finding_id,)
            )
            row = cursor.fetchone()
            if not row:
                return {"error": f"Finding {finding_id} not found"}
            if row[0] != "RESOLVED":
                return {"error": f"Finding {finding_id} is {row[0]}, must be RESOLVED to close"}

            conn.execute("""
                UPDATE governance_cycles SET status = 'CLOSED', closed_at = ?
                WHERE finding_id = ?
            """, (now.isoformat(), finding_id))
            conn.execute("""
                INSERT INTO cycle_events (finding_id, event_type, event_data, timestamp)
                VALUES (?, 'CLOSED', ?, ?)
            """, (finding_id, json.dumps({"by": closed_by}), now.isoformat()))
            conn.commit()

        # Calculate cycle duration
        created = datetime.fromisoformat(row[2])
        cycle_duration = (now - created).total_seconds() / 3600  # hours

        result = {
            "finding_id": finding_id,
            "status": "CLOSED",
            "severity": row[1],
            "closed_by": closed_by,
            "cycle_duration_hours": round(cycle_duration, 2),
            "receipt_chain": json.loads(row[4]) if row[4] else [],
            "timestamp": now.isoformat(),
            "governance_cycle": "COMPLETE",
            "auto_apply": False,
        }
        receipt = ForensicReceipt.generate("CLOSE_CYCLE", result, finding_id)
        ForensicReceipt.save(receipt)
        self._append_receipt(finding_id, receipt["receipt_id"])
        return result

    def check_sla(self) -> Dict:
        """Check all open cycles for SLA compliance. Returns alerts."""
        now = datetime.now(timezone.utc)
        alerts = {"breached_acknowledge": [], "breached_resolve": [], "warning_resolve": [], "healthy": 0}

        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute("""
                SELECT finding_id, severity, status, 
                       sla_acknowledge_deadline, sla_resolve_deadline, escalation_count
                FROM governance_cycles 
                WHERE status NOT IN ('RESOLVED', 'CLOSED')
            """)
            for row in cursor.fetchall():
                fid, severity, status, ack_dl, res_dl, esc_count = row
                ack_deadline = datetime.fromisoformat(ack_dl) if ack_dl else None
                res_deadline = datetime.fromisoformat(res_dl) if res_dl else None

                # Check acknowledge SLA
                if status == "OPEN" and ack_deadline and now > ack_deadline:
                    alerts["breached_acknowledge"].append({
                        "finding_id": fid,
                        "severity": severity,
                        "deadline": ack_dl,
                        "overdue_hours": round((now - ack_deadline).total_seconds() / 3600, 2),
                    })
                # Check resolve SLA warning (80% threshold)
                elif status in ("ACKNOWLEDGED", "IN_PROGRESS") and res_deadline:
                    remaining = (res_deadline - now).total_seconds()
                    total = SLA_RESOLVE.get(severity, timedelta(days=14)).total_seconds()
                    if remaining <= 0:
                        alerts["breached_resolve"].append({
                            "finding_id": fid,
                            "severity": severity,
                            "deadline": res_dl,
                            "overdue_hours": round(abs(remaining) / 3600, 2),
                        })
                    elif remaining / total <= (1 - ESCALATION_THRESHOLD_PCT):
                        alerts["warning_resolve"].append({
                            "finding_id": fid,
                            "severity": severity,
                            "deadline": res_dl,
                            "remaining_hours": round(remaining / 3600, 2),
                            "threshold_pct": f"{ESCALATION_THRESHOLD_PCT * 100}%",
                        })
                    else:
                        alerts["healthy"] += 1
                else:
                    alerts["healthy"] += 1

        # Generate receipt for SLA check
        total_issues = (len(alerts["breached_acknowledge"]) +
                       len(alerts["breached_resolve"]) +
                       len(alerts["warning_resolve"]))
        receipt = ForensicReceipt.generate("SLA_CHECK", {
            "total_open": alerts["healthy"] + total_issues,
            "breached": len(alerts["breached_acknowledge"]) + len(alerts["breached_resolve"]),
            "warnings": len(alerts["warning_resolve"]),
            "healthy": alerts["healthy"],
        })
        ForensicReceipt.save(receipt)

        alerts["summary"] = {
            "total_open_cycles": alerts["healthy"] + total_issues,
            "sla_breaches": len(alerts["breached_acknowledge"]) + len(alerts["breached_resolve"]),
            "sla_warnings": len(alerts["warning_resolve"]),
            "healthy_cycles": alerts["healthy"],
            "checked_at": now.isoformat(),
            "auto_apply": False,
        }
        return alerts

    def escalate(self, finding_id: str, reason: str) -> Dict:
        """Escalate a finding. This is NOTIFICATION only — never autonomous action (I9)."""
        now = datetime.now(timezone.utc)
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute(
                "SELECT status, severity, escalation_count FROM governance_cycles WHERE finding_id = ?",
                (finding_id,)
            )
            row = cursor.fetchone()
            if not row:
                return {"error": f"Finding {finding_id} not found"}

            new_count = (row[2] or 0) + 1
            conn.execute("""
                UPDATE governance_cycles 
                SET status = 'ESCALATED', escalated_at = ?, escalation_count = ?
                WHERE finding_id = ?
            """, (now.isoformat(), new_count, finding_id))
            conn.execute("""
                INSERT INTO cycle_events (finding_id, event_type, event_data, timestamp)
                VALUES (?, 'ESCALATED', ?, ?)
            """, (finding_id, json.dumps({
                "reason": reason, "escalation_number": new_count
            }), now.isoformat()))
            conn.commit()

        result = {
            "finding_id": finding_id,
            "status": "ESCALATED",
            "severity": row[1],
            "reason": reason,
            "escalation_number": new_count,
            "action_required": "HUMAN_DECISION_URGENT",
            "timestamp": now.isoformat(),
            "auto_apply": False,
        }

        # Save escalation file
        ESCALATIONS_DIR.mkdir(parents=True, exist_ok=True)
        esc_file = ESCALATIONS_DIR / f"ESC-{finding_id}-{now.strftime('%Y%m%d%H%M%S')}.json"
        with open(esc_file, 'w') as f:
            json.dump(result, f, indent=2)

        receipt = ForensicReceipt.generate("ESCALATE", result, finding_id)
        ForensicReceipt.save(receipt)
        self._append_receipt(finding_id, receipt["receipt_id"])
        return result

    def get_dashboard(self) -> Dict:
        """Generate dashboard data for the Command Center."""
        with sqlite3.connect(str(self.db_path)) as conn:
            # Status distribution
            cursor = conn.execute("""
                SELECT status, COUNT(*) FROM governance_cycles GROUP BY status
            """)
            status_counts = dict(cursor.fetchall())

            # Severity distribution (open only)
            cursor = conn.execute("""
                SELECT severity, COUNT(*) FROM governance_cycles 
                WHERE status NOT IN ('RESOLVED', 'CLOSED')
                GROUP BY severity
            """)
            open_by_severity = dict(cursor.fetchall())

            # Recent events
            cursor = conn.execute("""
                SELECT finding_id, event_type, timestamp 
                FROM cycle_events 
                ORDER BY timestamp DESC LIMIT 20
            """)
            recent_events = [
                {"finding_id": r[0], "event": r[1], "timestamp": r[2]}
                for r in cursor.fetchall()
            ]

            # SLA metrics
            cursor = conn.execute("""
                SELECT COUNT(*) FROM governance_cycles
                WHERE status = 'CLOSED' AND resolved_at IS NOT NULL
            """)
            total_closed = cursor.fetchone()[0]

            cursor = conn.execute("""
                SELECT AVG(
                    JULIANDAY(resolved_at) - JULIANDAY(created_at)
                ) * 24 
                FROM governance_cycles 
                WHERE status = 'CLOSED' AND resolved_at IS NOT NULL
            """)
            avg_resolution_hours = cursor.fetchone()[0]

        return {
            "agent_id": AGENT_ID,
            "pillar": PILLAR,
            "status_distribution": status_counts,
            "open_by_severity": open_by_severity,
            "total_closed_cycles": total_closed,
            "avg_resolution_hours": round(avg_resolution_hours, 2) if avg_resolution_hours else None,
            "recent_events": recent_events,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "auto_apply": False,
        }

    def get_finding(self, finding_id: str) -> Optional[Dict]:
        """Get full details of a specific governance cycle."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM governance_cycles WHERE finding_id = ?", (finding_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            
            cycle = dict(row)
            
            # Get events
            cursor = conn.execute(
                "SELECT event_type, event_data, timestamp, receipt_id FROM cycle_events WHERE finding_id = ? ORDER BY timestamp",
                (finding_id,)
            )
            cycle["events"] = [
                {"type": r[0], "data": json.loads(r[1]) if r[1] else {}, "timestamp": r[2], "receipt": r[3]}
                for r in cursor.fetchall()
            ]
            return cycle

    def _determine_channel(self, severity: str) -> str:
        """Determine routing channel based on severity. Institutional (R0-R3) vs Alert (R4-R5)."""
        if severity in ("R4", "R5"):
            return "ALERT_CHANNEL"
        return "INSTITUTIONAL_CHANNEL"

    def _append_receipt(self, finding_id: str, receipt_id: str):
        """Append receipt to the finding's receipt chain."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute(
                "SELECT receipt_chain FROM governance_cycles WHERE finding_id = ?",
                (finding_id,)
            )
            row = cursor.fetchone()
            if row:
                chain = json.loads(row[0]) if row[0] else []
                chain.append(receipt_id)
                conn.execute(
                    "UPDATE governance_cycles SET receipt_chain = ? WHERE finding_id = ?",
                    (json.dumps(chain), finding_id)
                )
                conn.commit()


# ============================================================================
# FINDING INGESTION — Reads from Sentinela & ISP Manager
# ============================================================================

class FindingIngestor:
    """Scans peer agent output directories for new findings to process."""

    @staticmethod
    def scan_sentinela_findings() -> List[Dict]:
        """Read unprocessed findings from Sentinela."""
        findings = []
        if not SENTINELA_FINDINGS.exists():
            return findings
        
        for fpath in sorted(SENTINELA_FINDINGS.glob("*.json")):
            try:
                with open(fpath) as f:
                    finding = json.load(f)
                finding["_source_file"] = str(fpath)
                finding["source_agent"] = "sentinela"
                findings.append(finding)
            except (json.JSONDecodeError, IOError) as e:
                findings.append({
                    "finding_id": fpath.stem,
                    "source_agent": "sentinela",
                    "severity": "R2",
                    "category": "PARSE_ERROR",
                    "summary": f"Could not parse finding file: {e}",
                    "_source_file": str(fpath),
                })
        return findings

    @staticmethod
    def scan_isp_manager_alerts() -> List[Dict]:
        """Read alerts from ISP Manager as potential findings."""
        alerts = []
        if not ISP_MANAGER_ALERTS.exists():
            return alerts

        for fpath in sorted(ISP_MANAGER_ALERTS.glob("*.json")):
            try:
                with open(fpath) as f:
                    alert = json.load(f)
                # Convert ISP Manager alert format to finding format
                alert["source_agent"] = "isp-manager"
                if "finding_id" not in alert:
                    alert["finding_id"] = f"ISP-{fpath.stem}"
                alerts.append(alert)
            except (json.JSONDecodeError, IOError):
                pass
        return alerts


# ============================================================================
# MAIN AGENT CLASS
# ============================================================================

class MaestroAgent:
    """
    WINDI Maestro Agent — Governance Orchestrator.
    
    Third Pillar: RESOLUTION
    
    Internal Modules:
        DecisionRouter      — Routes findings to human stakeholders
        SLAGuardian         — Monitors SLA compliance
        ResolutionAssembler — Creates DecisionPackages for human review
    
    Commands:
        status          — Show agent status and health
        dashboard       — Generate dashboard for Command Center
        ingest          — Scan peer agents and register new findings
        check_sla       — Check all open cycles for SLA compliance
        acknowledge     — Record human acknowledgment
        resolve         — Record human resolution decision
        close           — Close a resolved governance cycle
        escalate        — Escalate a finding
        find            — Get details of a specific finding
        report          — Generate governance cycle report
        route           — Route a finding through DecisionRouter
        sla_report      — Generate SLA compliance report
        package         — Assemble DecisionPackage for a finding
        deadlines       — Show approaching deadlines
    """

    def __init__(self):
        self.state = GovernanceCycleState()
        self.ingestor = FindingIngestor()
        self._ensure_dirs()
        
        # Initialize modules (lazy — they work even without peer agents)
        self._router = None
        self._sla_guardian = None
        self._assembler = None
        self._conflict_protocol = None

    def _ensure_dirs(self):
        for d in [RESOLUTIONS_DIR, ESCALATIONS_DIR, RECEIPTS_DIR, REPORTS_DIR, STATE_DIR]:
            d.mkdir(parents=True, exist_ok=True)

    @property
    def router(self):
        if self._router is None:
            # Import here to allow standalone operation
            try:
                sys.path.insert(0, str(AGENT_BASE))
                from modules.decision_router import DecisionRouter
                self._router = DecisionRouter(isp_library_path=ISP_LIBRARY)
            except ImportError:
                self._router = None
        return self._router

    @property
    def sla_guardian(self):
        if self._sla_guardian is None:
            try:
                sys.path.insert(0, str(AGENT_BASE))
                from modules.sla_guardian import SLAGuardian
                self._sla_guardian = SLAGuardian(state_db_path=self.state.db_path)
            except ImportError:
                self._sla_guardian = None
        return self._sla_guardian

    @property
    def assembler(self):
        if self._assembler is None:
            try:
                sys.path.insert(0, str(AGENT_BASE))
                from modules.resolution_assembler import ResolutionAssembler
                self._assembler = ResolutionAssembler(state_db_path=self.state.db_path)
            except ImportError:
                self._assembler = None
        return self._assembler

    @property
    def conflict_protocol(self):
        if self._conflict_protocol is None:
            try:
                sys.path.insert(0, str(AGENT_BASE))
                from modules.conflict_protocol import InstitutionalConflictProtocol
                self._conflict_protocol = InstitutionalConflictProtocol(state_db_path=self.state.db_path)
            except ImportError:
                self._conflict_protocol = None
        return self._conflict_protocol

    def status(self) -> Dict:
        """Show agent status and ecosystem health."""
        manifest_path = AGENT_BASE / "manifest.json"
        manifest = {}
        if manifest_path.exists():
            with open(manifest_path) as f:
                manifest = json.load(f)

        # Check peer agents
        peers = {
            "sentinela": (AGENTS_ROOT / "sentinela" / "manifest.json").exists(),
            "isp-manager": (AGENTS_ROOT / "isp-manager" / "manifest.json").exists(),
        }

        # Check modules
        modules = {
            "decision_router": self.router is not None,
            "sla_guardian": self.sla_guardian is not None,
            "resolution_assembler": self.assembler is not None,
            "conflict_protocol": self.conflict_protocol is not None,
        }

        # Count state
        with sqlite3.connect(str(self.state.db_path)) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM governance_cycles")
            total_cycles = cursor.fetchone()[0]
            cursor = conn.execute(
                "SELECT COUNT(*) FROM governance_cycles WHERE status NOT IN ('RESOLVED', 'CLOSED')"
            )
            open_cycles = cursor.fetchone()[0]

        return {
            "agent_id": AGENT_ID,
            "codename": CODENAME,
            "pillar": PILLAR,
            "version": VERSION,
            "status": "ACTIVE",
            "execution_mode": "human-mediated",
            "invariants": ["I1-I9"],
            "peer_agents": peers,
            "modules": modules,
            "cycles": {
                "total": total_cycles,
                "open": open_cycles,
                "closed": total_cycles - open_cycles,
            },
            "paths": {
                "agent_base": str(AGENT_BASE),
                "state_db": str(self.state.db_path),
                "state_db_exists": self.state.db_path.exists(),
                "sentinela_findings": str(SENTINELA_FINDINGS),
                "sentinela_available": SENTINELA_FINDINGS.exists(),
                "isp_manager_alerts": str(ISP_MANAGER_ALERTS),
                "isp_manager_available": ISP_MANAGER_ALERTS.exists(),
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "auto_apply": False,
        }

    def route_finding(self, finding: Dict) -> Dict:
        """Route a finding using the DecisionRouter module."""
        if not self.router:
            return {"error": "DecisionRouter module not available", "auto_apply": False}
        
        routing = self.router.route(finding)
        
        # Generate receipt
        receipt = ForensicReceipt.generate("ROUTE_VIA_ROUTER", routing, finding.get("finding_id"))
        ForensicReceipt.save(receipt)
        
        return routing

    def sla_report(self) -> Dict:
        """Generate SLA compliance report using SLAGuardian module."""
        if not self.sla_guardian:
            return {"error": "SLAGuardian module not available", "auto_apply": False}
        
        return self.sla_guardian.generate_compliance_report()

    def get_deadlines(self, hours: int = 24) -> List[Dict]:
        """Get approaching deadlines using SLAGuardian module."""
        if not self.sla_guardian:
            return [{"error": "SLAGuardian module not available"}]
        
        return self.sla_guardian.get_approaching_deadlines(hours)

    def build_package(self, finding_id: str) -> Dict:
        """Build a DecisionPackage using ResolutionAssembler module."""
        if not self.assembler:
            return {"error": "ResolutionAssembler module not available", "auto_apply": False}
        
        # Get routing decision if router is available
        routing = None
        if self.router:
            finding_data = self.state.get_finding(finding_id)
            if finding_data:
                routing = self.router.route(finding_data)
        
        package = self.assembler.assemble(finding_id, routing)
        
        # Save package
        RESOLUTIONS_DIR.mkdir(parents=True, exist_ok=True)
        pkg_file = RESOLUTIONS_DIR / f"PKG-{finding_id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.json"
        with open(pkg_file, 'w') as f:
            json.dump(package, f, indent=2, ensure_ascii=False)
        
        # Generate receipt
        receipt = ForensicReceipt.generate("ASSEMBLE_PACKAGE", {
            "finding_id": finding_id,
            "package_file": str(pkg_file),
            "integrity_hash": package.get("integrity_hash", "N/A"),
        }, finding_id)
        ForensicReceipt.save(receipt)
        
        package["_saved_to"] = str(pkg_file)
        return package

    def detect_conflicts(self) -> Dict:
        """Detect institutional conflicts between pillar outputs."""
        if not self.conflict_protocol:
            return {"error": "ConflictProtocol module not available", "auto_apply": False}
        
        # Scan both pillars
        sentinela_findings = self.ingestor.scan_sentinela_findings()
        isp_alerts = self.ingestor.scan_isp_manager_alerts()
        
        conflicts = self.conflict_protocol.detect(sentinela_findings, isp_alerts)
        
        registered = []
        for c in conflicts:
            reg = self.conflict_protocol.register(c)
            registered.append(reg)
        
        receipt = ForensicReceipt.generate("DETECT_CONFLICTS", {
            "sentinela_scanned": len(sentinela_findings),
            "isp_scanned": len(isp_alerts),
            "conflicts_detected": len(conflicts),
            "conflicts_registered": len(registered),
        })
        ForensicReceipt.save(receipt)
        
        return {
            "scanned": {"sentinela": len(sentinela_findings), "isp_manager": len(isp_alerts)},
            "conflicts_detected": len(conflicts),
            "registered": registered,
            "auto_apply": False,
        }

    def package_conflict(self, conflict_id: str) -> Dict:
        """Build a ConflictPackage for human review."""
        if not self.conflict_protocol:
            return {"error": "ConflictProtocol module not available", "auto_apply": False}
        
        conflict = self.conflict_protocol.get_conflict(conflict_id)
        if not conflict:
            return {"error": f"Conflict {conflict_id} not found"}
        
        return self.conflict_protocol.package(conflict)

    def adjudicate_conflict(self, conflict_id: str, decision: str,
                             rationale: str, decided_by: str) -> Dict:
        """Record human adjudication of a conflict."""
        if not self.conflict_protocol:
            return {"error": "ConflictProtocol module not available", "auto_apply": False}
        
        result = self.conflict_protocol.adjudicate(conflict_id, decision, rationale, decided_by)
        
        receipt = ForensicReceipt.generate("ADJUDICATE_CONFLICT", {
            "conflict_id": conflict_id,
            "decision": decision,
            "decided_by": decided_by,
        })
        ForensicReceipt.save(receipt)
        
        return result

    def seal_conflict(self, conflict_id: str, sealed_by: str) -> Dict:
        """Seal a resolved conflict in the Forensic Ledger."""
        if not self.conflict_protocol:
            return {"error": "ConflictProtocol module not available", "auto_apply": False}
        
        result = self.conflict_protocol.seal(conflict_id, sealed_by)
        
        receipt = ForensicReceipt.generate("SEAL_CONFLICT", {
            "conflict_id": conflict_id,
            "sealed_by": sealed_by,
            "integrity_hash": result.get("integrity_hash", "N/A"),
        })
        ForensicReceipt.save(receipt)
        
        return result

    def list_conflicts(self, status: str = None) -> Dict:
        """List institutional conflicts."""
        if not self.conflict_protocol:
            return {"error": "ConflictProtocol module not available", "auto_apply": False}
        
        conflicts = self.conflict_protocol.list_conflicts(status)
        return {
            "total": len(conflicts),
            "filter": status or "ALL",
            "conflicts": conflicts,
            "auto_apply": False,
        }

    def ingest(self) -> Dict:
        """Scan peer agent outputs and register new findings."""
        sentinela_findings = self.ingestor.scan_sentinela_findings()
        isp_alerts = self.ingestor.scan_isp_manager_alerts()

        all_findings = sentinela_findings + isp_alerts
        results = {"registered": [], "already_exists": [], "errors": []}

        for finding in all_findings:
            result = self.state.register_finding(finding)
            if "error" in result:
                if "already registered" in result["error"]:
                    results["already_exists"].append(result["finding_id"])
                else:
                    results["errors"].append(result)
            else:
                results["registered"].append(result)

        summary = {
            "scanned_sources": {
                "sentinela_findings": len(sentinela_findings),
                "isp_manager_alerts": len(isp_alerts),
            },
            "new_registered": len(results["registered"]),
            "already_existed": len(results["already_exists"]),
            "errors": len(results["errors"]),
            "registered_details": results["registered"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "auto_apply": False,
        }

        receipt = ForensicReceipt.generate("INGEST", summary)
        ForensicReceipt.save(receipt)
        return summary

    def report(self) -> Dict:
        """Generate comprehensive governance cycle report."""
        dashboard = self.state.get_dashboard()
        sla_check = self.state.check_sla()

        report = {
            "report_type": "GOVERNANCE_CYCLE_REPORT",
            "agent_id": AGENT_ID,
            "dashboard": dashboard,
            "sla_status": sla_check["summary"],
            "sla_breaches": {
                "acknowledge": sla_check["breached_acknowledge"],
                "resolve": sla_check["breached_resolve"],
            },
            "sla_warnings": sla_check["warning_resolve"],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "auto_apply": False,
        }

        # Save report
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        report_file = REPORTS_DIR / f"cycle_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        receipt = ForensicReceipt.generate("REPORT", {
            "report_file": str(report_file),
            "open_cycles": dashboard["status_distribution"],
        })
        ForensicReceipt.save(receipt)

        report["report_file"] = str(report_file)
        return report


# ============================================================================
# CLI INTERFACE
# ============================================================================

def print_json(data: Any):
    print(json.dumps(data, indent=2, ensure_ascii=False))



def main():
    if len(sys.argv) < 2:
        print(f"""
═══════════════════════════════════════════════════════════
  🎼 WINDI Maestro Agent v{VERSION} — Governance Orchestrator
  Pillar: {PILLAR}
  Modules: DecisionRouter | SLAGuardian | ResolutionAssembler | ConflictProtocol
  "AI processes. Human decides. WINDI guarantees."
═══════════════════════════════════════════════════════════

Core Commands:
  status                                   Show agent status + modules
  dashboard                                Dashboard for Command Center
  ingest                                   Scan peers & register new findings
  check_sla                                Check SLA compliance
  report                                   Generate governance cycle report

Governance Cycle:
  acknowledge --finding-id <id> --by <n>   Acknowledge finding
  resolve --finding-id <id> --by <n> --note <t>  Record resolution
  close --finding-id <id> --by <n>         Close cycle
  escalate --finding-id <id> --reason <t>  Escalate finding
  find --finding-id <id>                   Get finding details

Module Commands:
  route --finding-id <id>                  Route finding (DecisionRouter)
  sla_report                               SLA compliance report (SLAGuardian)
  deadlines [--hours N]                    Approaching deadlines (default 24h)
  package --finding-id <id>                Build DecisionPackage (Assembler)

Conflict Protocol:
  conflicts [--status <s>]                 List institutional conflicts
  detect_conflicts                         Scan for pillar divergences
  conflict_package --conflict-id <id>      Build ConflictPackage for human
  adjudicate --conflict-id <id> --decision <d> --rationale <r> --by <n>
  seal_conflict --conflict-id <id> --by <n>  Seal in Forensic Ledger
""")
        return

    agent = MaestroAgent()
    cmd = sys.argv[1]

    def get_arg(flag):
        try:
            idx = sys.argv.index(flag)
            return sys.argv[idx + 1]
        except (ValueError, IndexError):
            return None

    if cmd == "status":
        print_json(agent.status())
    elif cmd == "dashboard":
        print_json(agent.state.get_dashboard())
    elif cmd == "ingest":
        print_json(agent.ingest())
    elif cmd == "check_sla":
        print_json(agent.state.check_sla())
    elif cmd == "acknowledge":
        fid, by = get_arg("--finding-id"), get_arg("--by")
        if not fid or not by:
            print("Usage: maestro_agent.py acknowledge --finding-id <id> --by <name>"); sys.exit(1)
        print_json(agent.state.acknowledge(fid, by))
    elif cmd == "resolve":
        fid, by, note = get_arg("--finding-id"), get_arg("--by"), get_arg("--note")
        if not fid or not by or not note:
            print("Usage: maestro_agent.py resolve --finding-id <id> --by <name> --note <text>"); sys.exit(1)
        print_json(agent.state.resolve(fid, note, by))
    elif cmd == "close":
        fid, by = get_arg("--finding-id"), get_arg("--by")
        if not fid or not by:
            print("Usage: maestro_agent.py close --finding-id <id> --by <name>"); sys.exit(1)
        print_json(agent.state.close_cycle(fid, by))
    elif cmd == "escalate":
        fid, reason = get_arg("--finding-id"), get_arg("--reason")
        if not fid or not reason:
            print("Usage: maestro_agent.py escalate --finding-id <id> --reason <text>"); sys.exit(1)
        print_json(agent.state.escalate(fid, reason))
    elif cmd == "find":
        fid = get_arg("--finding-id")
        if not fid:
            print("Usage: maestro_agent.py find --finding-id <id>"); sys.exit(1)
        result = agent.state.get_finding(fid)
        print_json(result if result else {"error": f"Finding {fid} not found"})
    elif cmd == "report":
        print_json(agent.report())
    # Module commands
    elif cmd == "route":
        fid = get_arg("--finding-id")
        if not fid:
            print("Usage: maestro_agent.py route --finding-id <id>"); sys.exit(1)
        finding_data = agent.state.get_finding(fid)
        if not finding_data:
            print(json.dumps({"error": f"Finding {fid} not found"})); sys.exit(1)
        print_json(agent.route_finding(finding_data))
    elif cmd == "sla_report":
        print_json(agent.sla_report())
    elif cmd == "deadlines":
        hours = int(get_arg("--hours") or "24")
        print_json({"approaching_deadlines": agent.get_deadlines(hours), "lookahead_hours": hours})
    elif cmd == "package":
        fid = get_arg("--finding-id")
        if not fid:
            print("Usage: maestro_agent.py package --finding-id <id>"); sys.exit(1)
        print_json(agent.build_package(fid))
    # Conflict Protocol commands
    elif cmd == "conflicts":
        status_filter = get_arg("--status")
        print_json(agent.list_conflicts(status_filter))
    elif cmd == "detect_conflicts":
        print_json(agent.detect_conflicts())
    elif cmd == "conflict_package":
        cid = get_arg("--conflict-id")
        if not cid:
            print("Usage: maestro_agent.py conflict_package --conflict-id <id>"); sys.exit(1)
        print_json(agent.package_conflict(cid))
    elif cmd == "adjudicate":
        cid = get_arg("--conflict-id")
        decision = get_arg("--decision")
        rationale = get_arg("--rationale")
        by = get_arg("--by")
        if not all([cid, decision, rationale, by]):
            print("Usage: maestro_agent.py adjudicate --conflict-id <id> --decision <d> --rationale <r> --by <n>"); sys.exit(1)
        print_json(agent.adjudicate_conflict(cid, decision, rationale, by))
    elif cmd == "seal_conflict":
        cid = get_arg("--conflict-id")
        by = get_arg("--by")
        if not cid or not by:
            print("Usage: maestro_agent.py seal_conflict --conflict-id <id> --by <n>"); sys.exit(1)
        print_json(agent.seal_conflict(cid, by))
    else:
        print(f"Unknown command: {cmd}"); sys.exit(1)


if __name__ == "__main__":
    main()
