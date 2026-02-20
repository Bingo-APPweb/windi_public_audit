#!/usr/bin/env python3
"""
WINDI Sentinel LAW v2.0 — Hardened
===================================
Origin: Stress Test Linhagem de Ferro — 17 Feb 2026
Hardened: 19 Feb 2026

Improvements over v1.0:
  1. SELF-PROBE ISOLATION: Sentinel's own probes cannot block the system
  2. ESCALATION TIERS: GREEN → YELLOW → ORANGE → RED → BLACK
  3. HUMAN INTERVENTION PROTOCOL: Propose → Authorize → Execute → Audit
  4. STALE PROBE DETECTION: Auto-detect orphaned probes from Sentinel itself
  5. ALERT CHANNELS: Structured alerts with severity for future SMTP/webhook

Principle: "The system cannot degrade silently."
Invariant I9: "No AI system may escalate its own autonomy level."
"""

import json
import time
import hashlib
import sqlite3
import threading
import traceback
import statistics
from datetime import datetime, timezone, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.request import urlopen, Request
from urllib.error import URLError
from collections import deque

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

PORT = 8102
CHECK_INTERVAL_S = 30
LATENCY_P95_LIMIT_MS = 100
LATENCY_WINDOW = 100  # rolling window of samples

# Escalation thresholds (consecutive violations before escalation)
ESCALATION_THRESHOLDS = {
    "GREEN":  0,   # 0 consecutive violations = healthy
    "YELLOW": 3,   # 3 consecutive violations = attention
    "ORANGE": 10,  # 10 = action recommended
    "RED":    30,  # 30 = breach imminent (~15 min at 30s cycles)
    "BLACK":  60,  # 60 = breach confirmed (~30 min)
}

# Self-probe isolation: max age before a probe is considered stale
SELF_PROBE_MAX_AGE_S = 120  # 2 minutes = 4 cycles

# Endpoints to monitor
ENDPOINTS = {
    "desktop": "http://127.0.0.1:8100",
    "ledger":  "http://127.0.0.1:8101",
    "bridge":  "http://127.0.0.1:8097",
}

DB_PATH = "/opt/windi/data/sentinel_law.db"
LOG_PATH = "/opt/windi/logs/sentinel_law.log"

# ═══════════════════════════════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════════════════════════════

def init_db():
    """Initialize SQLite with history + proposals tables."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # History table (same as v1)
    c.execute("""
        CREATE TABLE IF NOT EXISTS law_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            cycle_id INTEGER NOT NULL,
            latency_p50_ms REAL,
            latency_p95_ms REAL,
            latency_p99_ms REAL,
            receipts_total INTEGER,
            receipts_unsynced INTEGER,
            hash_drift INTEGER,
            event_drops INTEGER,
            reconciliation_status TEXT,
            chain_integrity TEXT,
            all_pass INTEGER,
            escalation_level TEXT DEFAULT 'GREEN'
        )
    """)

    # Alerts table (same as v1, extended with escalation)
    c.execute("""
        CREATE TABLE IF NOT EXISTS law_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            cycle_id INTEGER NOT NULL,
            law_name TEXT NOT NULL,
            expected TEXT,
            actual TEXT,
            resolved INTEGER DEFAULT 0,
            resolved_at TEXT,
            escalation_level TEXT DEFAULT 'YELLOW'
        )
    """)

    # NEW: Action Proposals table (Human Intervention Protocol)
    c.execute("""
        CREATE TABLE IF NOT EXISTS action_proposals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            cycle_id INTEGER NOT NULL,
            proposal_type TEXT NOT NULL,
            description TEXT NOT NULL,
            impact_level TEXT NOT NULL,
            target_service TEXT,
            proposed_action TEXT NOT NULL,
            status TEXT DEFAULT 'PENDING',
            authorized_by TEXT,
            authorized_at TEXT,
            executed_at TEXT,
            ledger_receipt_id TEXT,
            escalation_level TEXT DEFAULT 'YELLOW'
        )
    """)

    # NEW: Stale probes tracking
    c.execute("""
        CREATE TABLE IF NOT EXISTS stale_probes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            probe_receipt_id TEXT,
            age_seconds REAL,
            action_taken TEXT DEFAULT 'ISOLATED',
            cycle_id INTEGER
        )
    """)

    # Add escalation_level column to law_history if missing (migration)
    try:
        c.execute("SELECT escalation_level FROM law_history LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE law_history ADD COLUMN escalation_level TEXT DEFAULT 'GREEN'")

    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════════════════════
# ESCALATION ENGINE
# ═══════════════════════════════════════════════════════════════

class EscalationEngine:
    """
    Tracks consecutive violations per LAW and determines escalation level.

    GREEN  → 0 consecutive violations (healthy)
    YELLOW → 3+ (attention recommended)
    ORANGE → 10+ (action recommended)
    RED    → 30+ (breach imminent, ~15min)
    BLACK  → 60+ (breach confirmed, ~30min)
    """

    def __init__(self):
        self.consecutive_violations = {}  # law_name → count
        self.current_level = "GREEN"
        self.level_changed_at = datetime.now(timezone.utc)
        self.level_history = []

    def record_result(self, law_name: str, passed: bool):
        """Record a check result and update escalation state."""
        if passed:
            if law_name in self.consecutive_violations:
                del self.consecutive_violations[law_name]
        else:
            self.consecutive_violations[law_name] = \
                self.consecutive_violations.get(law_name, 0) + 1

    def compute_level(self) -> str:
        """Determine current escalation level from worst violation streak."""
        if not self.consecutive_violations:
            new_level = "GREEN"
        else:
            max_streak = max(self.consecutive_violations.values())
            if max_streak >= ESCALATION_THRESHOLDS["BLACK"]:
                new_level = "BLACK"
            elif max_streak >= ESCALATION_THRESHOLDS["RED"]:
                new_level = "RED"
            elif max_streak >= ESCALATION_THRESHOLDS["ORANGE"]:
                new_level = "ORANGE"
            elif max_streak >= ESCALATION_THRESHOLDS["YELLOW"]:
                new_level = "YELLOW"
            else:
                new_level = "GREEN"

        if new_level != self.current_level:
            self.level_history.append({
                "from": self.current_level,
                "to": new_level,
                "at": datetime.now(timezone.utc).isoformat(),
                "streaks": dict(self.consecutive_violations),
            })
            self.current_level = new_level
            self.level_changed_at = datetime.now(timezone.utc)

        return self.current_level

    def get_status(self) -> dict:
        return {
            "level": self.current_level,
            "since": self.level_changed_at.isoformat(),
            "consecutive_violations": dict(self.consecutive_violations),
            "thresholds": ESCALATION_THRESHOLDS,
            "recent_transitions": self.level_history[-10:],
        }


# ═══════════════════════════════════════════════════════════════
# SELF-PROBE ISOLATION
# ═══════════════════════════════════════════════════════════════

class SelfProbeIsolator:
    """
    Detects and isolates stale probes created by Sentinel itself.

    The orphaned probe incident (1410 cycles in LAW2 failure) happened
    because a Sentinel probe receipt failed to sync and the LAW check
    kept detecting it as "unsynced". This isolator:

    1. Tracks which receipt IDs were created by Sentinel probes
    2. If a probe is older than SELF_PROBE_MAX_AGE_S and unsynced,
       it's marked as ISOLATED (excluded from LAW2 count)
    3. Logs isolation events for forensic audit
    """

    def __init__(self):
        self.active_probes = {}  # receipt_id → creation_timestamp
        self.isolated_count = 0

    def register_probe(self, receipt_id: str):
        """Register a new probe receipt ID."""
        self.active_probes[receipt_id] = time.time()

    def clear_probe(self, receipt_id: str):
        """Mark a probe as successfully synced."""
        self.active_probes.pop(receipt_id, None)

    def check_stale_probes(self) -> list:
        """Return list of stale (orphaned) probe IDs."""
        now = time.time()
        stale = []
        for rid, created_at in list(self.active_probes.items()):
            age = now - created_at
            if age > SELF_PROBE_MAX_AGE_S:
                stale.append({
                    "receipt_id": rid,
                    "age_seconds": round(age, 1),
                })
                # Remove from active tracking
                del self.active_probes[rid]
                self.isolated_count += 1
        return stale

    def get_isolation_adjustment(self, unsynced_count: int,
                                  unsynced_ids: list = None) -> int:
        """
        Adjust unsynced count by removing Sentinel's own stale probes.
        Returns the adjusted count that should be used for LAW2.
        """
        if unsynced_ids is None:
            return unsynced_count

        # Count how many unsynced IDs belong to our probes
        sentinel_unsynced = sum(
            1 for uid in unsynced_ids
            if uid in self.active_probes
        )

        adjusted = max(0, unsynced_count - sentinel_unsynced)
        return adjusted

    def get_status(self) -> dict:
        return {
            "active_probes": len(self.active_probes),
            "isolated_total": self.isolated_count,
            "max_age_s": SELF_PROBE_MAX_AGE_S,
        }


# ═══════════════════════════════════════════════════════════════
# HUMAN INTERVENTION PROTOCOL
# ═══════════════════════════════════════════════════════════════

class HumanInterventionProtocol:
    """
    Implements the Nível 2 Protocol:

    1. Detection: Sentinel identifies an issue
    2. Proposal: Generates an Action Proposal (NOT auto-execute)
    3. Human Authorization: Waits for explicit human approval
    4. Audited Execution: If approved, logs to Forensic Ledger

    Respects I9: No auto-remediation. Ever.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.pending_proposals = []

    def propose_action(self, cycle_id: int, proposal_type: str,
                       description: str, impact_level: str,
                       target_service: str, proposed_action: str,
                       escalation_level: str = "YELLOW") -> dict:
        """
        Create an action proposal for human review.

        proposal_type: "restart", "investigate", "escalate", "isolate"
        impact_level: "LOW", "MEDIUM", "HIGH", "CRITICAL"
        """
        now = datetime.now(timezone.utc).isoformat()

        proposal = {
            "timestamp": now,
            "cycle_id": cycle_id,
            "proposal_type": proposal_type,
            "description": description,
            "impact_level": impact_level,
            "target_service": target_service,
            "proposed_action": proposed_action,
            "status": "PENDING",
            "escalation_level": escalation_level,
        }

        # Persist to DB
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            INSERT INTO action_proposals
            (timestamp, cycle_id, proposal_type, description, impact_level,
             target_service, proposed_action, status, escalation_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'PENDING', ?)
        """, (now, cycle_id, proposal_type, description, impact_level,
              target_service, proposed_action, escalation_level))
        proposal["id"] = c.lastrowid
        conn.commit()
        conn.close()

        self.pending_proposals.append(proposal)
        return proposal

    def authorize(self, proposal_id: int, authorized_by: str = "Human Dragon") -> dict:
        """
        Authorize a pending proposal. This is called via API by the human.
        Returns the updated proposal. Does NOT auto-execute.
        """
        now = datetime.now(timezone.utc).isoformat()
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            UPDATE action_proposals
            SET status = 'AUTHORIZED', authorized_by = ?, authorized_at = ?
            WHERE id = ? AND status = 'PENDING'
        """, (authorized_by, now, proposal_id))

        if c.rowcount == 0:
            conn.close()
            return {"error": "Proposal not found or already processed"}

        conn.commit()
        conn.close()

        return {
            "id": proposal_id,
            "status": "AUTHORIZED",
            "authorized_by": authorized_by,
            "authorized_at": now,
            "note": "Proposal authorized. Human must execute or delegate."
        }

    def reject(self, proposal_id: int, reason: str = "") -> dict:
        """Reject a proposal."""
        now = datetime.now(timezone.utc).isoformat()
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            UPDATE action_proposals
            SET status = 'REJECTED', authorized_by = ?, authorized_at = ?
            WHERE id = ? AND status = 'PENDING'
        """, (f"REJECTED: {reason}", now, proposal_id))
        conn.commit()
        conn.close()
        return {"id": proposal_id, "status": "REJECTED", "reason": reason}

    def get_pending(self) -> list:
        """Get all pending proposals."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("""
            SELECT * FROM action_proposals
            WHERE status = 'PENDING'
            ORDER BY timestamp DESC
        """)
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows

    def get_all(self, limit: int = 50) -> list:
        """Get all proposals (any status)."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("""
            SELECT * FROM action_proposals
            ORDER BY timestamp DESC LIMIT ?
        """, (limit,))
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows


# ═══════════════════════════════════════════════════════════════
# LAW CHECKER (enhanced v2)
# ═══════════════════════════════════════════════════════════════

class SentinelLAW:
    """The 6 immutable laws of WINDI system health."""

    def __init__(self):
        self.latency_samples = deque(maxlen=LATENCY_WINDOW)
        self.cycle_id = 0
        self.total_checks = 0
        self.total_violations = 0
        self.total_alerts = 0
        self.started_at = datetime.now(timezone.utc)
        self.last_result = None

        # v2 components
        self.escalation = EscalationEngine()
        self.isolator = SelfProbeIsolator()
        self.hip = HumanInterventionProtocol(DB_PATH)

        # Track if we already proposed action for current escalation
        self._last_proposal_level = "GREEN"

    def _fetch_json(self, url: str, timeout: int = 5) -> dict:
        """Fetch JSON from a URL with timeout."""
        try:
            req = Request(url)
            with urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode())
        except Exception:
            return {}

    def _probe_latency(self) -> float:
        """Send a probe receipt via Desktop gateway (like v1) and measure round-trip time."""
        now = datetime.now(timezone.utc).isoformat()
        probe_hash = hashlib.sha256(
            f"sentinel-law-probe-{self.cycle_id}-{time.time()}".encode()
        ).hexdigest()

        # Use same format as v1.0 — Desktop gateway handles Ledger translation
        probe_receipt = {
            "doc_id": "SENTINEL-LAW-PROBE",
            "action": "LAW_PROBE",
            "integrity_hash": probe_hash,
            "timestamp": now,
            "user_id": "sentinel-law-v2",
            "metadata": {
                "cycle_id": self.cycle_id,
                "purpose": "latency_measurement",
                "hash_algorithm": "SHA-256",
                "sentinel_version": "2.0.0-hardened"
            }
        }

        start = time.time()
        try:
            data = json.dumps(probe_receipt).encode()
            req = Request(
                f"{ENDPOINTS['desktop']}/api/ledger/receipts",
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urlopen(req, timeout=5) as resp:
                result = json.loads(resp.read().decode())
                elapsed_ms = (time.time() - start) * 1000

                # Register probe for isolation tracking
                receipt_id = result.get("receipt_id", "")
                if receipt_id:
                    self.isolator.register_probe(receipt_id)

                return elapsed_ms
        except Exception:
            return -1

    def check_all(self) -> dict:
        """Run all 6 LAW checks with v2 hardening."""
        self.cycle_id += 1
        self.total_checks += 1
        now = datetime.now(timezone.utc)

        # ── Check stale probes FIRST (self-probe isolation) ──
        stale = self.isolator.check_stale_probes()
        if stale:
            self._log_stale_probes(stale)

        # ── LAW 1: Latency P95 < 100ms ──
        probe_ms = self._probe_latency()
        if probe_ms > 0:
            self.latency_samples.append(probe_ms)

        samples = list(self.latency_samples)
        if len(samples) >= 5:
            sorted_s = sorted(samples)
            p50 = sorted_s[len(sorted_s) // 2]
            p95_idx = int(len(sorted_s) * 0.95)
            p95 = sorted_s[min(p95_idx, len(sorted_s) - 1)]
            p99_idx = int(len(sorted_s) * 0.99)
            p99 = sorted_s[min(p99_idx, len(sorted_s) - 1)]
        else:
            p50 = p95 = p99 = probe_ms if probe_ms > 0 else 0

        law1_pass = p95 < LATENCY_P95_LIMIT_MS

        # ── LAW 2: Unsynced = 0 (with self-probe isolation) ──
        d1_status = self._fetch_json(f"{ENDPOINTS['desktop']}/api/status")
        raw_unsynced = d1_status.get("unsynced_receipts", 0)
        unsynced_ids = d1_status.get("unsynced_receipt_ids", [])

        # ISOLATION: subtract Sentinel's own stale probes
        adjusted_unsynced = self.isolator.get_isolation_adjustment(
            raw_unsynced, unsynced_ids
        )
        law2_pass = adjusted_unsynced == 0

        # ── LAW 3: Hash drift = 0 ──
        hash_drift = 0
        receipts = d1_status.get("recent_receipts", [])[:20]
        for r in receipts:
            if r.get("ledger_synced") is False:
                hash_drift += 1
        law3_pass = hash_drift == 0

        # ── LAW 4: Reconciliation = HEALTHY ──
        recon = self._fetch_json(f"{ENDPOINTS['desktop']}/api/reconcile")
        recon_status = recon.get("status", "unknown")
        recon_healthy = recon_status in ("reconciliation_complete", "HEALTHY", "healthy")
        still_pending = recon.get("still_pending", 0)
        law4_pass = recon_healthy

        # ── LAW 5: Event drops = 0 ──
        event_drops = 0
        if probe_ms < 0:
            event_drops = 1
        law5_pass = event_drops == 0

        # ── LAW 6: Chain integrity = VALID ──
        bridge = self._fetch_json(f"{ENDPOINTS['bridge']}/health")
        chain_intact = bridge.get("chain_intact", False)
        law6_pass = chain_intact is True

        # ── Aggregate ──
        laws = {
            "LAW1": {
                "name": "latency_p95",
                "value": f"{p95:.1f}ms",
                "raw_value": p95,
                "expected": "< 100ms",
                "passed": law1_pass,
                "detail": {
                    "probe_latency": f"{probe_ms:.1f}ms" if probe_ms > 0 else "FAILED",
                    "p50": f"{p50:.1f}ms",
                    "p95": f"{p95:.1f}ms",
                    "p99": f"{p99:.1f}ms",
                    "samples": len(samples),
                },
            },
            "LAW2": {
                "name": "unsynced",
                "value": str(adjusted_unsynced),
                "raw_value": adjusted_unsynced,
                "expected": "= 0",
                "passed": law2_pass,
                "detail": {
                    "receipts_total": d1_status.get("total_receipts", 0),
                    "raw_unsynced": raw_unsynced,
                    "isolated_sentinel_probes": raw_unsynced - adjusted_unsynced,
                },
            },
            "LAW3": {
                "name": "hash_drift",
                "value": str(hash_drift),
                "raw_value": hash_drift,
                "expected": "= 0",
                "passed": law3_pass,
                "detail": {"checked_receipts": len(receipts)},
            },
            "LAW4": {
                "name": "reconciliation",
                "value": "HEALTHY" if recon_healthy else recon_status,
                "raw_value": recon_status,
                "expected": "= HEALTHY",
                "passed": law4_pass,
                "detail": {
                    "status": recon_status,
                    "still_pending": still_pending,
                    "failed_ids": recon.get("failed_ids", []),
                },
            },
            "LAW5": {
                "name": "event_drops",
                "value": str(event_drops),
                "raw_value": event_drops,
                "expected": "= 0",
                "passed": law5_pass,
                "detail": {"probe_delivered": probe_ms > 0},
            },
            "LAW6": {
                "name": "chain_integrity",
                "value": "VALID" if chain_intact else "BROKEN",
                "raw_value": chain_intact,
                "expected": "= VALID",
                "passed": law6_pass,
                "detail": {
                    "chain_intact": chain_intact,
                    "chain_entries": bridge.get("chain_entries", 0),
                },
            },
        }

        all_pass = all(l["passed"] for l in laws.values())
        violations = [k for k, v in laws.items() if not v["passed"]]

        # ── Update escalation engine ──
        for law_key, law_data in laws.items():
            self.escalation.record_result(law_data["name"], law_data["passed"])
        escalation_level = self.escalation.compute_level()

        # ── Generate proposals at escalation boundaries ──
        if escalation_level != "GREEN" and escalation_level != self._last_proposal_level:
            self._generate_proposal(escalation_level, violations, laws)
            self._last_proposal_level = escalation_level
        elif escalation_level == "GREEN":
            self._last_proposal_level = "GREEN"

        # ── Track violations ──
        if not all_pass:
            self.total_violations += 1

        # ── Persist to DB ──
        self._save_history(now, p50, p95, p99, laws, all_pass, escalation_level)
        if violations:
            self._save_alerts(now, violations, laws, escalation_level)

        # ── Build result ──
        result = {
            "cycle_id": self.cycle_id,
            "timestamp": now.isoformat(),
            "all_pass": all_pass,
            "violations": violations,
            "laws": laws,
            "escalation": {
                "level": escalation_level,
                "since": self.escalation.level_changed_at.isoformat(),
                "streaks": dict(self.escalation.consecutive_violations),
            },
            "self_probe_isolation": {
                "stale_detected": len(stale),
                "stale_probes": stale,
                "active_probes": len(self.isolator.active_probes),
                "total_isolated": self.isolator.isolated_count,
            },
            "alerts": [],
            "latency_profile": {
                "p50": f"{p50:.1f}ms",
                "p95": f"{p95:.1f}ms",
                "p99": f"{p99:.1f}ms",
                "samples": len(samples),
            },
        }

        self.last_result = result
        return result

    def _generate_proposal(self, level: str, violations: list, laws: dict):
        """Generate human intervention proposal based on escalation level."""
        violated_details = []
        for v in violations:
            law = laws[v]
            violated_details.append(
                f"{v} ({law['name']}): got {law['value']}, expected {law['expected']}"
            )

        description = (
            f"Escalation to {level}. Violations: {', '.join(violated_details)}"
        )

        # Determine proposal type based on level
        if level in ("YELLOW", "ORANGE"):
            proposal_type = "investigate"
            proposed_action = (
                "Investigate the failing LAW checks. Check service logs and "
                "recent deployments for root cause."
            )
            impact = "LOW" if level == "YELLOW" else "MEDIUM"
        elif level == "RED":
            proposal_type = "escalate"
            proposed_action = (
                "System approaching SLA breach. Recommend immediate investigation. "
                "Consider service restart if root cause is identified."
            )
            impact = "HIGH"
        else:  # BLACK
            proposal_type = "restart"
            proposed_action = (
                "SLA BREACHED. Propose targeted restart of affected services "
                "after human review of logs."
            )
            impact = "CRITICAL"

        self.hip.propose_action(
            cycle_id=self.cycle_id,
            proposal_type=proposal_type,
            description=description,
            impact_level=impact,
            target_service=", ".join(violations),
            proposed_action=proposed_action,
            escalation_level=level,
        )

    def _log_stale_probes(self, stale: list):
        """Log stale probe isolations to DB."""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        for s in stale:
            c.execute("""
                INSERT INTO stale_probes (timestamp, probe_receipt_id, age_seconds,
                                          action_taken, cycle_id)
                VALUES (?, ?, ?, 'ISOLATED', ?)
            """, (datetime.now(timezone.utc).isoformat(),
                  s["receipt_id"], s["age_seconds"], self.cycle_id))
        conn.commit()
        conn.close()

    def _save_history(self, now, p50, p95, p99, laws, all_pass, level):
        """Save check result to history."""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            INSERT INTO law_history
            (timestamp, cycle_id, latency_p50_ms, latency_p95_ms, latency_p99_ms,
             receipts_total, receipts_unsynced, hash_drift, event_drops,
             reconciliation_status, chain_integrity, all_pass, escalation_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            now.isoformat(), self.cycle_id, p50, p95, p99,
            laws["LAW2"]["detail"].get("receipts_total", 0),
            laws["LAW2"]["raw_value"],
            laws["LAW3"]["raw_value"],
            laws["LAW5"]["raw_value"],
            laws["LAW4"]["raw_value"],
            laws["LAW6"]["value"],
            1 if all_pass else 0,
            level,
        ))
        conn.commit()
        conn.close()

    def _save_alerts(self, now, violations, laws, level):
        """Save alerts for violations."""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        for v in violations:
            law = laws[v]
            c.execute("""
                INSERT INTO law_alerts
                (timestamp, cycle_id, law_name, expected, actual, escalation_level)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (now.isoformat(), self.cycle_id,
                  law["name"], law["expected"], law["value"], level))
            self.total_alerts += 1
        conn.commit()
        conn.close()


# ═══════════════════════════════════════════════════════════════
# HTTP SERVER
# ═══════════════════════════════════════════════════════════════

sentinel = SentinelLAW()


class SentinelHandler(BaseHTTPRequestHandler):
    """HTTP API for Sentinel LAW v2."""

    def log_message(self, format, *args):
        pass  # Suppress default logging

    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())

    def do_GET(self):
        path = self.path.split("?")[0]
        query = {}
        if "?" in self.path:
            for param in self.path.split("?")[1].split("&"):
                if "=" in param:
                    k, v = param.split("=", 1)
                    query[k] = v

        # ── Health ──
        if path == "/health":
            self._json({
                "service": "WINDI Sentinel LAW",
                "version": "2.0.0-hardened",
                "status": "enforcing",
                "all_laws_pass": sentinel.last_result["all_pass"] if sentinel.last_result else None,
                "escalation_level": sentinel.escalation.current_level,
                "active_alerts": len(sentinel.hip.get_pending()),
                "cycle_id": sentinel.cycle_id,
                "port": PORT,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "principle": "The system cannot degrade silently.",
            })

        # ── Full status ──
        elif path == "/api/law/status":
            self._json({
                "service": "WINDI Sentinel LAW",
                "version": "2.0.0-hardened",
                "status": "enforcing",
                "started_at": sentinel.started_at.isoformat(),
                "cycle_id": sentinel.cycle_id,
                "total_checks": sentinel.total_checks,
                "total_violations": sentinel.total_violations,
                "total_alerts": sentinel.total_alerts,
                "active_alerts": sentinel.hip.get_pending(),
                "escalation": sentinel.escalation.get_status(),
                "self_probe_isolation": sentinel.isolator.get_status(),
                "consecutive_violations": dict(sentinel.escalation.consecutive_violations),
                "last_check": sentinel.last_result["timestamp"] if sentinel.last_result else None,
                "last_result": sentinel.last_result,
                "config": {
                    "check_interval_s": CHECK_INTERVAL_S,
                    "latency_p95_limit_ms": LATENCY_P95_LIMIT_MS,
                    "alert_threshold": ESCALATION_THRESHOLDS["YELLOW"],
                    "latency_window": LATENCY_WINDOW,
                    "escalation_thresholds": ESCALATION_THRESHOLDS,
                    "self_probe_max_age_s": SELF_PROBE_MAX_AGE_S,
                },
                "endpoints_monitored": ENDPOINTS,
                "principle": "Violation of ANY law = immediate alert.",
                "origin": "Stress Test Linhagem de Ferro — 17 Feb 2026, Hardened 19 Feb 2026",
            })

        # ── Manual check trigger ──
        elif path == "/api/law/check":
            result = sentinel.check_all()
            self._json(result)

        # ── Escalation status ──
        elif path == "/api/law/escalation":
            self._json(sentinel.escalation.get_status())

        # ── Action proposals (Human Intervention Protocol) ──
        elif path == "/api/law/proposals":
            status_filter = query.get("status", "all")
            if status_filter == "pending":
                self._json({"proposals": sentinel.hip.get_pending()})
            else:
                limit = int(query.get("limit", "50"))
                self._json({"proposals": sentinel.hip.get_all(limit)})

        # ── Self-probe isolation status ──
        elif path == "/api/law/isolation":
            self._json(sentinel.isolator.get_status())

        # ── History ──
        elif path == "/api/law/history":
            limit = int(query.get("limit", "50"))
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("""
                SELECT * FROM law_history ORDER BY id DESC LIMIT ?
            """, (limit,))
            rows = [dict(r) for r in c.fetchall()]
            conn.close()
            self._json({"history": rows})

        # ── Alerts ──
        elif path == "/api/law/alerts":
            active_only = query.get("active", "false") == "true"
            limit = int(query.get("limit", "50"))
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            if active_only:
                c.execute("""
                    SELECT * FROM law_alerts WHERE resolved = 0
                    ORDER BY id DESC LIMIT ?
                """, (limit,))
            else:
                c.execute("""
                    SELECT * FROM law_alerts ORDER BY id DESC LIMIT ?
                """, (limit,))
            rows = [dict(r) for r in c.fetchall()]
            conn.close()
            self._json({"alerts": rows})

        # ── Config ──
        elif path == "/api/law/config":
            self._json({
                "laws": {
                    "LAW1": {"name": "latency_p95", "limit": "< 100ms", "source": "localhost receipt probe"},
                    "LAW2": {"name": "unsynced", "limit": "= 0", "source": "D1 /api/status (with self-probe isolation)"},
                    "LAW3": {"name": "hash_drift", "limit": "= 0", "source": "D1 receipt ledger_synced field"},
                    "LAW4": {"name": "reconciliation", "limit": "= HEALTHY", "source": "D1 /api/reconcile"},
                    "LAW5": {"name": "event_drops", "limit": "= 0", "source": "probe receipt delivery verification"},
                    "LAW6": {"name": "chain_integrity", "limit": "= VALID", "source": "Bridge /health chain_intact"},
                },
                "check_interval_s": CHECK_INTERVAL_S,
                "escalation_thresholds": ESCALATION_THRESHOLDS,
                "self_probe_isolation": {
                    "enabled": True,
                    "max_age_s": SELF_PROBE_MAX_AGE_S,
                    "description": "Sentinel's own stale probes are excluded from LAW2 count",
                },
                "human_intervention": {
                    "enabled": True,
                    "auto_remediation": False,
                    "invariant_i9": "No AI system may escalate its own autonomy level",
                    "description": "Proposals require human authorization via API",
                },
                "latency_window": LATENCY_WINDOW,
                "endpoints_monitored": ENDPOINTS,
                "principle": "Violation of ANY law = immediate alert.",
                "origin": "Stress Test Linhagem de Ferro — 17 Feb 2026, Hardened 19 Feb 2026",
            })

        else:
            self._json({
                "error": "Not found",
                "available": [
                    "/health",
                    "/api/law/status",
                    "/api/law/check",
                    "/api/law/escalation",
                    "/api/law/proposals",
                    "/api/law/proposals?status=pending",
                    "/api/law/isolation",
                    "/api/law/history",
                    "/api/law/alerts",
                    "/api/law/config",
                ],
            }, 404)

    def do_POST(self):
        path = self.path.split("?")[0]
        content_len = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(content_len)) if content_len > 0 else {}

        # ── Authorize a proposal ──
        if path == "/api/law/proposals/authorize":
            proposal_id = body.get("proposal_id")
            authorized_by = body.get("authorized_by", "Human Dragon")
            if not proposal_id:
                self._json({"error": "proposal_id required"}, 400)
                return
            result = sentinel.hip.authorize(proposal_id, authorized_by)
            self._json(result)

        # ── Reject a proposal ──
        elif path == "/api/law/proposals/reject":
            proposal_id = body.get("proposal_id")
            reason = body.get("reason", "")
            if not proposal_id:
                self._json({"error": "proposal_id required"}, 400)
                return
            result = sentinel.hip.reject(proposal_id, reason)
            self._json(result)

        else:
            self._json({"error": "Not found"}, 404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


# ═══════════════════════════════════════════════════════════════
# BACKGROUND CHECKER
# ═══════════════════════════════════════════════════════════════

def background_checker():
    """Run LAW checks every CHECK_INTERVAL_S."""
    while True:
        try:
            result = sentinel.check_all()
            level = result["escalation"]["level"]
            status = "ALL PASS" if result["all_pass"] else f"VIOLATIONS: {result['violations']}"

            # Color indicator for escalation
            level_icons = {
                "GREEN": "[GREEN]", "YELLOW": "[YELLOW]",
                "ORANGE": "[ORANGE]", "RED": "[RED]", "BLACK": "[BLACK]"
            }
            icon = level_icons.get(level, "[?]")

            with open(LOG_PATH, "a") as f:
                f.write(
                    f"[{result['timestamp']}] Cycle {result['cycle_id']} "
                    f"{icon} {level} | {status} | "
                    f"p95={result['latency_profile']['p95']} | "
                    f"isolated={result['self_probe_isolation']['stale_detected']}\n"
                )
        except Exception as e:
            with open(LOG_PATH, "a") as f:
                f.write(f"[ERROR] {datetime.now(timezone.utc).isoformat()} {e}\n")
                traceback.print_exc(file=f)

        time.sleep(CHECK_INTERVAL_S)


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    init_db()

    print(f"WINDI Sentinel LAW v2.0 — Hardened")
    print(f"   Port: {PORT}")
    print(f"   Check interval: {CHECK_INTERVAL_S}s")
    print(f"   Escalation: GREEN->YELLOW->ORANGE->RED->BLACK")
    print(f"   Self-probe isolation: ENABLED (max age {SELF_PROBE_MAX_AGE_S}s)")
    print(f"   Human Intervention Protocol: ENABLED (I9 compliant)")
    print(f"   Principle: The system cannot degrade silently.")
    print()

    # Start background checker
    checker = threading.Thread(target=background_checker, daemon=True)
    checker.start()

    # Start HTTP server
    server = HTTPServer(("0.0.0.0", PORT), SentinelHandler)
    print(f"Sentinel LAW v2.0 listening on :{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nSentinel LAW shutting down.")
        server.shutdown()
