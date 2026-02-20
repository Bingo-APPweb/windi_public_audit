#!/usr/bin/env python3
"""
WINDI Maestro — SLAGuardian Module v1.0.0
==========================================
"O Relógio da Governança"

Monitors governance cycle SLAs, detects approaching deadlines,
triggers escalation alerts, and generates SLA compliance reports.

Principle: Time is governance. A finding without a deadline is a finding without consequence.

SLA Tiers by Severity:
    ┌──────────┬──────────────┬──────────────┐
    │ Severity │ Acknowledge  │   Resolve    │
    ├──────────┼──────────────┼──────────────┤
    │  R0-R1   │    48 hours  │   30 days    │
    │  R2-R3   │    24 hours  │   14 days    │
    │  R4      │     4 hours  │    7 days    │
    │  R5      │     1 hour   │   48 hours   │
    └──────────┴──────────────┴──────────────┘

Escalation Triggers:
    ⚠️  WARNING:  80% of resolve SLA consumed
    🔴 BREACH:   SLA deadline passed
    ⚫ CRITICAL:  2x SLA exceeded (severe negligence)

Version: 1.0.0
Created: 2026-02-08
Author: WINDI Publishing House / Three Dragons Protocol
"""

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from enum import Enum


# ============================================================================
# SLA CONFIGURATION
# ============================================================================

class SLATier(Enum):
    """SLA tiers mapped to risk severity levels."""
    CRITICAL = "CRITICAL"   # R5
    HIGH = "HIGH"           # R4
    MEDIUM = "MEDIUM"       # R2-R3
    LOW = "LOW"             # R0-R1


# Acknowledge SLA (time to first human response)
SLA_ACKNOWLEDGE = {
    "R0": timedelta(hours=48),
    "R1": timedelta(hours=48),
    "R2": timedelta(hours=24),
    "R3": timedelta(hours=24),
    "R4": timedelta(hours=4),
    "R5": timedelta(hours=1),
}

# Resolve SLA (time to resolution decision)
SLA_RESOLVE = {
    "R0": timedelta(days=30),
    "R1": timedelta(days=30),
    "R2": timedelta(days=14),
    "R3": timedelta(days=14),
    "R4": timedelta(days=7),
    "R5": timedelta(days=2),
}

# Escalation thresholds
WARNING_THRESHOLD = 0.80   # 80% of SLA consumed → warning
SEVERE_MULTIPLIER = 2.0    # 2x SLA exceeded → severe negligence flag


# ============================================================================
# SLA STATUS CLASSIFICATION
# ============================================================================

class SLAStatus(Enum):
    HEALTHY = "HEALTHY"           # Within SLA, plenty of time
    WARNING = "WARNING"           # 80%+ of SLA consumed
    BREACHED = "BREACHED"         # Past deadline
    SEVERE = "SEVERE"             # 2x past deadline
    NOT_APPLICABLE = "N/A"        # Finding in terminal state


# ============================================================================
# SLA GUARDIAN
# ============================================================================

class SLAGuardian:
    """
    Monitors governance cycle SLAs and generates escalation alerts.
    
    The Guardian tracks two SLA types per finding:
    1. Acknowledge SLA: Time for human to acknowledge finding
    2. Resolve SLA: Time for human to make resolution decision
    
    The Guardian NEVER:
    - Auto-resolves findings
    - Changes finding status
    - Makes decisions about resolution
    
    The Guardian ONLY:
    - Measures time elapsed vs deadlines
    - Classifies SLA health status
    - Generates structured alerts for escalation
    - Produces compliance reports
    """

    def __init__(self, state_db_path: Path = None):
        self.db_path = state_db_path or Path("/opt/windi/agents/maestro/state/maestro_state.db")

    def check_all(self) -> Dict:
        """
        Full SLA health check across all open governance cycles.
        
        Returns structured report with:
        - Per-finding SLA status
        - Aggregate health metrics
        - Escalation recommendations (never auto-applied)
        """
        now = datetime.now(timezone.utc)
        
        findings = self._get_open_findings()
        
        results = {
            "checked_at": now.isoformat(),
            "total_open": len(findings),
            "findings": [],
            "escalation_queue": [],
            "metrics": {
                "healthy": 0,
                "warning": 0,
                "breached": 0,
                "severe": 0,
            },
            "auto_apply": False,
        }
        
        for finding in findings:
            assessment = self._assess_finding(finding, now)
            results["findings"].append(assessment)
            
            # Count by status
            worst_status = assessment["worst_status"]
            if worst_status == SLAStatus.HEALTHY.value:
                results["metrics"]["healthy"] += 1
            elif worst_status == SLAStatus.WARNING.value:
                results["metrics"]["warning"] += 1
            elif worst_status == SLAStatus.BREACHED.value:
                results["metrics"]["breached"] += 1
            elif worst_status == SLAStatus.SEVERE.value:
                results["metrics"]["severe"] += 1
            
            # Queue for escalation if needed
            if worst_status in (SLAStatus.BREACHED.value, SLAStatus.SEVERE.value):
                results["escalation_queue"].append({
                    "finding_id": assessment["finding_id"],
                    "severity": assessment["severity"],
                    "status": worst_status,
                    "reason": assessment["escalation_reason"],
                    "recommended_action": "ESCALATE",
                    "auto_apply": False,  # I9
                })
        
        # Calculate SLA compliance rate
        total = results["total_open"]
        if total > 0:
            compliant = results["metrics"]["healthy"] + results["metrics"]["warning"]
            results["metrics"]["sla_compliance_rate"] = round(compliant / total * 100, 1)
        else:
            results["metrics"]["sla_compliance_rate"] = 100.0
        
        return results

    def check_finding(self, finding_id: str) -> Dict:
        """Check SLA status for a specific finding."""
        now = datetime.now(timezone.utc)
        finding = self._get_finding(finding_id)
        
        if not finding:
            return {"error": f"Finding {finding_id} not found", "finding_id": finding_id}
        
        return self._assess_finding(finding, now)

    def get_approaching_deadlines(self, hours_ahead: int = 24) -> List[Dict]:
        """Get findings with deadlines approaching within the next N hours."""
        now = datetime.now(timezone.utc)
        cutoff = now + timedelta(hours=hours_ahead)
        
        findings = self._get_open_findings()
        approaching = []
        
        for finding in findings:
            fid = finding["finding_id"]
            severity = finding["severity"]
            status = finding["status"]
            
            # Check acknowledge deadline
            if status == "OPEN" and finding.get("sla_acknowledge_deadline"):
                ack_dl = datetime.fromisoformat(finding["sla_acknowledge_deadline"])
                if now < ack_dl <= cutoff:
                    remaining = (ack_dl - now).total_seconds() / 3600
                    approaching.append({
                        "finding_id": fid,
                        "severity": severity,
                        "sla_type": "ACKNOWLEDGE",
                        "deadline": finding["sla_acknowledge_deadline"],
                        "remaining_hours": round(remaining, 2),
                        "urgency": "HIGH" if remaining < 4 else "MEDIUM",
                    })
            
            # Check resolve deadline
            if status in ("ACKNOWLEDGED", "IN_PROGRESS") and finding.get("sla_resolve_deadline"):
                res_dl = datetime.fromisoformat(finding["sla_resolve_deadline"])
                if now < res_dl <= cutoff:
                    remaining = (res_dl - now).total_seconds() / 3600
                    approaching.append({
                        "finding_id": fid,
                        "severity": severity,
                        "sla_type": "RESOLVE",
                        "deadline": finding["sla_resolve_deadline"],
                        "remaining_hours": round(remaining, 2),
                        "urgency": "HIGH" if remaining < 8 else "MEDIUM",
                    })
        
        # Sort by remaining time (most urgent first)
        approaching.sort(key=lambda x: x["remaining_hours"])
        return approaching

    def generate_compliance_report(self) -> Dict:
        """
        Generate SLA compliance report for the Command Center dashboard.
        
        Includes:
        - Overall compliance rate
        - Per-severity breakdown
        - Historical trend (last 30 days of closed cycles)
        - Current hotspots
        """
        now = datetime.now(timezone.utc)
        
        # Current open cycle health
        current_health = self.check_all()
        
        # Historical: closed cycles and their SLA performance
        historical = self._get_historical_sla_performance()
        
        # Per-severity breakdown of open findings
        severity_breakdown = self._get_severity_breakdown()
        
        report = {
            "report_type": "SLA_COMPLIANCE",
            "generated_at": now.isoformat(),
            "current_state": {
                "total_open": current_health["total_open"],
                "compliance_rate": current_health["metrics"]["sla_compliance_rate"],
                "healthy": current_health["metrics"]["healthy"],
                "warning": current_health["metrics"]["warning"],
                "breached": current_health["metrics"]["breached"],
                "severe": current_health["metrics"]["severe"],
            },
            "severity_breakdown": severity_breakdown,
            "historical_performance": historical,
            "escalation_queue_size": len(current_health["escalation_queue"]),
            "approaching_deadlines": len(self.get_approaching_deadlines(24)),
            "auto_apply": False,
        }
        
        # Health grade (A-F)
        rate = current_health["metrics"]["sla_compliance_rate"]
        if rate >= 95:
            report["grade"] = "A"
        elif rate >= 85:
            report["grade"] = "B"
        elif rate >= 70:
            report["grade"] = "C"
        elif rate >= 50:
            report["grade"] = "D"
        else:
            report["grade"] = "F"
        
        return report

    # ── Internal assessment ────────────────────────────────────────────

    def _assess_finding(self, finding: Dict, now: datetime) -> Dict:
        """Assess SLA status for a single finding."""
        fid = finding["finding_id"]
        severity = finding["severity"]
        status = finding["status"]
        
        ack_status = SLAStatus.NOT_APPLICABLE
        ack_detail = {}
        resolve_status = SLAStatus.NOT_APPLICABLE
        resolve_detail = {}
        escalation_reason = None
        
        # Assess acknowledge SLA
        if status == "OPEN" and finding.get("sla_acknowledge_deadline"):
            ack_dl = datetime.fromisoformat(finding["sla_acknowledge_deadline"])
            ack_status, ack_detail = self._assess_deadline(now, ack_dl, severity, "ACKNOWLEDGE")
            if ack_status in (SLAStatus.BREACHED, SLAStatus.SEVERE):
                escalation_reason = f"Acknowledge SLA {ack_status.value}: {ack_detail.get('overdue', 'unknown')}"
        
        # Assess resolve SLA
        if status in ("OPEN", "ACKNOWLEDGED", "IN_PROGRESS", "ESCALATED"):
            if finding.get("sla_resolve_deadline"):
                res_dl = datetime.fromisoformat(finding["sla_resolve_deadline"])
                resolve_status, resolve_detail = self._assess_deadline(now, res_dl, severity, "RESOLVE")
                if resolve_status in (SLAStatus.BREACHED, SLAStatus.SEVERE):
                    escalation_reason = f"Resolve SLA {resolve_status.value}: {resolve_detail.get('overdue', 'unknown')}"
        
        # Determine worst status
        status_priority = {
            SLAStatus.NOT_APPLICABLE: 0,
            SLAStatus.HEALTHY: 1,
            SLAStatus.WARNING: 2,
            SLAStatus.BREACHED: 3,
            SLAStatus.SEVERE: 4,
        }
        worst = max(
            [ack_status, resolve_status],
            key=lambda s: status_priority.get(s, 0)
        )
        
        return {
            "finding_id": fid,
            "severity": severity,
            "current_status": status,
            "acknowledge_sla": {
                "status": ack_status.value,
                **ack_detail,
            },
            "resolve_sla": {
                "status": resolve_status.value,
                **resolve_detail,
            },
            "worst_status": worst.value,
            "escalation_reason": escalation_reason,
            "auto_apply": False,
        }

    def _assess_deadline(self, now: datetime, deadline: datetime, severity: str, sla_type: str) -> Tuple[SLAStatus, Dict]:
        """Assess a single deadline and return status + details."""
        if now > deadline:
            overdue = now - deadline
            overdue_hours = overdue.total_seconds() / 3600
            
            # Check severe threshold (2x SLA)
            sla_duration = (SLA_ACKNOWLEDGE if sla_type == "ACKNOWLEDGE" else SLA_RESOLVE).get(severity, timedelta(days=14))
            severe_threshold = sla_duration * SEVERE_MULTIPLIER
            
            if overdue >= severe_threshold:
                return SLAStatus.SEVERE, {
                    "overdue": f"{overdue_hours:.1f}h overdue",
                    "overdue_hours": round(overdue_hours, 2),
                    "deadline": deadline.isoformat(),
                    "severity_flag": "NEGLIGENCE",
                }
            else:
                return SLAStatus.BREACHED, {
                    "overdue": f"{overdue_hours:.1f}h overdue",
                    "overdue_hours": round(overdue_hours, 2),
                    "deadline": deadline.isoformat(),
                }
        else:
            remaining = (deadline - now).total_seconds()
            sla_duration = (SLA_ACKNOWLEDGE if sla_type == "ACKNOWLEDGE" else SLA_RESOLVE).get(severity, timedelta(days=14))
            total_seconds = sla_duration.total_seconds()
            consumed_pct = 1 - (remaining / total_seconds) if total_seconds > 0 else 0
            
            if consumed_pct >= WARNING_THRESHOLD:
                return SLAStatus.WARNING, {
                    "remaining_hours": round(remaining / 3600, 2),
                    "consumed_pct": round(consumed_pct * 100, 1),
                    "deadline": deadline.isoformat(),
                }
            else:
                return SLAStatus.HEALTHY, {
                    "remaining_hours": round(remaining / 3600, 2),
                    "consumed_pct": round(consumed_pct * 100, 1),
                    "deadline": deadline.isoformat(),
                }

    # ── Database queries ───────────────────────────────────────────────

    def _get_open_findings(self) -> List[Dict]:
        if not self.db_path.exists():
            return []
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM governance_cycles 
                WHERE status NOT IN ('RESOLVED', 'CLOSED')
                ORDER BY 
                    CASE severity 
                        WHEN 'R5' THEN 1 WHEN 'R4' THEN 2 
                        WHEN 'R3' THEN 3 WHEN 'R2' THEN 4 
                        WHEN 'R1' THEN 5 WHEN 'R0' THEN 6 
                    END
            """)
            return [dict(row) for row in cursor.fetchall()]

    def _get_finding(self, finding_id: str) -> Optional[Dict]:
        if not self.db_path.exists():
            return None
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM governance_cycles WHERE finding_id = ?", (finding_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def _get_historical_sla_performance(self) -> Dict:
        """Get SLA performance of closed cycles (last 30 days)."""
        if not self.db_path.exists():
            return {"total_closed": 0, "within_sla": 0, "breached_sla": 0}
        
        cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute("""
                SELECT severity, created_at, resolved_at, sla_resolve_deadline
                FROM governance_cycles 
                WHERE status = 'CLOSED' AND closed_at > ?
            """, (cutoff,))
            
            within = 0
            breached = 0
            for row in cursor.fetchall():
                if row[2] and row[3]:  # resolved_at and sla_resolve_deadline exist
                    resolved = datetime.fromisoformat(row[2])
                    deadline = datetime.fromisoformat(row[3])
                    if resolved <= deadline:
                        within += 1
                    else:
                        breached += 1
            
            return {
                "period": "last_30_days",
                "total_closed": within + breached,
                "within_sla": within,
                "breached_sla": breached,
                "compliance_rate": round(within / (within + breached) * 100, 1) if (within + breached) > 0 else 100.0,
            }

    def _get_severity_breakdown(self) -> Dict:
        """Get open finding counts by severity."""
        if not self.db_path.exists():
            return {}
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute("""
                SELECT severity, COUNT(*), 
                       MIN(sla_resolve_deadline) as earliest_deadline
                FROM governance_cycles 
                WHERE status NOT IN ('RESOLVED', 'CLOSED')
                GROUP BY severity
            """)
            return {
                row[0]: {"count": row[1], "earliest_deadline": row[2]}
                for row in cursor.fetchall()
            }
