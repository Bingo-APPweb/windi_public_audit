#!/usr/bin/env python3
"""
WINDI SLA Sentinel Agent v1.0.0 — Three Dragons Protocol
=========================================================

Real-time SLA monitoring with preemptive alerting.
Advisory-only. Human-mediated. Mathematically precise.

"O Guardião do Tempo"

Author: WINDI Publishing House / Three Dragons Protocol
License: Proprietary — WINDI Governance Framework
"""

import json
import argparse
import os
import glob
import sqlite3
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any


class SLASentinel:
    """
    WINDI SLA Sentinel Agent v1.0.0

    Real-time SLA monitoring with preemptive alerting.
    Advisory-only. Human-mediated. Mathematically precise.

    Alert levels:
    - GREEN: < 50% elapsed
    - YELLOW: 50-74% elapsed
    - ORANGE: 75-89% elapsed
    - RED: >= 90% elapsed
    - BLACK: Breached
    """

    def __init__(self, config_path: str = '/opt/windi/agents/sla_sentinel/manifest.json'):
        """
        Initialize the SLA Sentinel.

        Args:
            config_path: Path to manifest.json
        """
        self.config_path = config_path
        self.base_path = os.path.dirname(config_path)

        # Load configuration
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                self.manifest = json.load(f)
        else:
            self.manifest = {"agent_id": "sla-sentinel", "version": "1.0.0"}

        # Define paths
        self.maestro_db = '/opt/windi/agents/maestro/state/maestro_state.db'
        self.definitions_path = os.path.join(self.base_path, 'sla_definitions.json')
        self.monitors_path = os.path.join(self.base_path, 'monitors')
        self.escalations_path = os.path.join(self.base_path, 'escalations', 'pending')
        self.logs_path = os.path.join(self.base_path, 'logs')

        # Ensure directories exist
        for path in [self.monitors_path, self.escalations_path, self.logs_path]:
            os.makedirs(path, exist_ok=True)

        # Load SLA definitions
        self.sla_rules = self._load_sla_definitions()

    def _load_sla_definitions(self) -> Dict[str, Dict]:
        """Load SLA rules from definitions file."""
        rules = {}

        if os.path.exists(self.definitions_path):
            try:
                with open(self.definitions_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for rule in data.get("sla_rules", []):
                        severity = rule.get("severity", "")
                        if severity:
                            rules[severity] = rule
            except (json.JSONDecodeError, IOError):
                pass

        # Default rules if not loaded
        if not rules:
            rules = {
                "R5": {"max_acknowledge_minutes": 5, "max_resolve_minutes": 15},
                "R4": {"max_acknowledge_minutes": 15, "max_resolve_minutes": 30},
                "R3": {"max_acknowledge_minutes": 30, "max_resolve_minutes": 120},
                "R2": {"max_acknowledge_minutes": 60, "max_resolve_minutes": 480},
                "R1": {"max_acknowledge_minutes": 240, "max_resolve_minutes": 1440},
                "R0": {"max_acknowledge_minutes": 1440, "max_resolve_minutes": 4320}
            }

        return rules

    def _load_active_findings(self) -> List[Dict]:
        """Load active findings from Maestro database."""
        findings = []

        if os.path.exists(self.maestro_db):
            try:
                conn = sqlite3.connect(self.maestro_db)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT * FROM governance_cycles
                    WHERE status NOT IN ('CLOSED', 'CANCELLED')
                    ORDER BY created_at ASC
                """)

                for row in cursor.fetchall():
                    findings.append(dict(row))

                conn.close()
            except Exception as e:
                print(f"Warning: Could not load Maestro data: {e}")

        return findings

    def check_all_active(self) -> Dict[str, Any]:
        """
        Check SLA status of all active findings.

        Returns:
            sla_status_report dictionary
        """
        now = datetime.now(timezone.utc)

        report = {
            "check_timestamp_utc": now.isoformat(),
            "active_findings": 0,
            "statuses": [],
            "overall_health": "GREEN",
            "alerts_generated": 0,
            "summary": {
                "green": 0,
                "yellow": 0,
                "orange": 0,
                "red": 0,
                "black": 0
            }
        }

        findings = self._load_active_findings()
        report["active_findings"] = len(findings)

        if not findings:
            report["overall_health"] = "ALL_CLEAR"
            return report

        for finding in findings:
            status = self.calculate_sla_status(finding)
            report["statuses"].append(status)

            # Track summary
            level = status.get("alert_level", "GREEN").lower()
            if level in report["summary"]:
                report["summary"][level] += 1

            # Generate alert if >= YELLOW
            if level in ["yellow", "orange", "red", "black"]:
                self.generate_alert(
                    finding_id=status["finding_id"],
                    severity=status["severity"],
                    alert_level=status["alert_level"],
                    time_remaining_min=status.get("time_remaining_minutes", 0)
                )
                report["alerts_generated"] += 1

        # Determine overall health
        if report["summary"]["black"] > 0:
            report["overall_health"] = "BLACK"
        elif report["summary"]["red"] > 0:
            report["overall_health"] = "RED"
        elif report["summary"]["orange"] > 0:
            report["overall_health"] = "ORANGE"
        elif report["summary"]["yellow"] > 0:
            report["overall_health"] = "YELLOW"
        else:
            report["overall_health"] = "GREEN"

        return report

    def check_single(self, finding_id: str) -> Optional[Dict]:
        """Check SLA status of a specific finding."""
        findings = self._load_active_findings()

        for finding in findings:
            if finding.get("finding_id") == finding_id:
                return self.calculate_sla_status(finding)

        return {"error": f"Finding {finding_id} not found or not active"}

    def calculate_sla_status(self, finding: Dict) -> Dict:
        """
        Calculate SLA status for a finding.

        Determines: elapsed_minutes, sla_limit, percentage, alert_level, time_remaining.
        """
        now = datetime.now(timezone.utc)

        finding_id = finding.get("finding_id", "unknown")
        severity = finding.get("severity", "R3")
        status = finding.get("status", "OPEN")
        created_at = finding.get("created_at", "")
        acknowledged_at = finding.get("acknowledged_at")
        resolved_at = finding.get("resolved_at")

        # Get SLA rules for this severity
        rules = self.sla_rules.get(severity, self.sla_rules.get("R3", {}))

        result = {
            "finding_id": finding_id,
            "severity": severity,
            "current_status": status,
            "stage": "UNKNOWN",
            "elapsed_minutes": 0,
            "sla_limit_minutes": 0,
            "elapsed_percentage": 0,
            "alert_level": "GREEN",
            "time_remaining_minutes": 0
        }

        if not created_at:
            return result

        try:
            created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        except ValueError:
            return result

        # Determine current stage and calculate
        if status in ["OPEN", "ROUTED"] and not acknowledged_at:
            # Stage: Waiting for acknowledgment
            result["stage"] = "ACKNOWLEDGE"
            sla_limit = rules.get("max_acknowledge_minutes", 60)
            elapsed = (now - created).total_seconds() / 60

        elif status == "ACKNOWLEDGED" or (acknowledged_at and not resolved_at):
            # Stage: Waiting for resolution
            result["stage"] = "RESOLVE"
            sla_limit = rules.get("max_resolve_minutes", 480)
            try:
                ack_time = datetime.fromisoformat(acknowledged_at.replace('Z', '+00:00'))
                elapsed = (now - ack_time).total_seconds() / 60
            except (ValueError, TypeError):
                elapsed = (now - created).total_seconds() / 60

        elif status == "RESOLVED" or resolved_at:
            # Stage: Waiting for close
            result["stage"] = "CLOSE"
            sla_limit = rules.get("max_close_minutes", 240)
            try:
                res_time = datetime.fromisoformat(resolved_at.replace('Z', '+00:00'))
                elapsed = (now - res_time).total_seconds() / 60
            except (ValueError, TypeError):
                elapsed = 0

        else:
            return result

        result["elapsed_minutes"] = round(elapsed, 2)
        result["sla_limit_minutes"] = sla_limit
        result["elapsed_percentage"] = round((elapsed / sla_limit) * 100, 1) if sla_limit > 0 else 0
        result["time_remaining_minutes"] = round(max(0, sla_limit - elapsed), 2)

        # Determine alert level
        pct = result["elapsed_percentage"]
        if pct >= 100:
            result["alert_level"] = "BLACK"
        elif pct >= 90:
            result["alert_level"] = "RED"
        elif pct >= 75:
            result["alert_level"] = "ORANGE"
        elif pct >= 50:
            result["alert_level"] = "YELLOW"
        else:
            result["alert_level"] = "GREEN"

        return result

    def generate_alert(self, finding_id: str, severity: str, alert_level: str, time_remaining_min: float) -> None:
        """
        Generate preemptive alert.

        Message is human-readable with clear time remaining.
        """
        now = datetime.now(timezone.utc)

        # Create human-readable message
        if alert_level == "BLACK":
            message = f"SLA BREACH: Finding {finding_id} ({severity}) has exceeded SLA deadline"
        elif alert_level == "RED":
            message = f"CRITICAL: Finding {finding_id} ({severity}) has {time_remaining_min:.0f} minutes before SLA breach"
        elif alert_level == "ORANGE":
            message = f"WARNING: Finding {finding_id} ({severity}) has {time_remaining_min:.0f} minutes before SLA breach"
        else:
            message = f"ATTENTION: Finding {finding_id} ({severity}) is at 50%+ SLA elapsed ({time_remaining_min:.0f} min remaining)"

        alert = {
            "agent": "sla-sentinel",
            "timestamp": now.isoformat(),
            "finding_id": finding_id,
            "severity": severity,
            "alert_level": alert_level,
            "time_remaining_minutes": round(time_remaining_min, 2),
            "message": message,
            "action_required": "HUMAN_ATTENTION_RECOMMENDED"
        }

        alert_file = os.path.join(
            self.escalations_path,
            f"sla_{now.strftime('%Y%m%d_%H%M%S')}_{finding_id}_{alert_level}.json"
        )

        with open(alert_file, 'w', encoding='utf-8') as f:
            json.dump(alert, f, indent=2, ensure_ascii=False)

    def get_queue_forecast(self) -> Dict:
        """
        Forecast: given current queue and avg resolution time, how many at risk?

        Returns:
            Forecast dictionary with at_risk count and bottleneck stage
        """
        findings = self._load_active_findings()

        if not findings:
            return {
                "at_risk": 0,
                "estimated_breaches": 0,
                "bottleneck_stage": None,
                "queue_size": 0
            }

        at_risk = 0
        by_stage = {"ACKNOWLEDGE": 0, "RESOLVE": 0, "CLOSE": 0}

        for finding in findings:
            status = self.calculate_sla_status(finding)
            if status.get("alert_level") in ["ORANGE", "RED", "BLACK"]:
                at_risk += 1
            stage = status.get("stage", "UNKNOWN")
            if stage in by_stage:
                by_stage[stage] += 1

        # Find bottleneck
        bottleneck = max(by_stage.items(), key=lambda x: x[1])[0] if by_stage else None

        return {
            "at_risk": at_risk,
            "estimated_breaches": sum(1 for f in findings if self.calculate_sla_status(f).get("alert_level") in ["RED", "BLACK"]),
            "bottleneck_stage": bottleneck,
            "queue_size": len(findings),
            "by_stage": by_stage
        }

    def save_status_report(self, report: Dict) -> str:
        """Save status report to monitors directory."""
        now = datetime.now(timezone.utc)
        path = os.path.join(self.monitors_path, f"sla_status_{now.strftime('%Y%m%d_%H%M%S')}.json")

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        return path

    def get_dashboard_data(self) -> Dict:
        """
        Get data formatted for Command Center dashboard.

        Returns:
            Dashboard-ready dictionary
        """
        report = self.check_all_active()
        forecast = self.get_queue_forecast()

        return {
            "timestamp": report["check_timestamp_utc"],
            "active_count": report["active_findings"],
            "overall_health": report["overall_health"],
            "health_color": self._get_health_color(report["overall_health"]),
            "summary": report["summary"],
            "at_risk": forecast["at_risk"],
            "bottleneck": forecast["bottleneck_stage"],
            "alerts_pending": report["alerts_generated"]
        }

    def _get_health_color(self, health: str) -> str:
        """Get display color for health status."""
        colors = {
            "ALL_CLEAR": "#4ade80",
            "GREEN": "#4ade80",
            "YELLOW": "#facc15",
            "ORANGE": "#fb923c",
            "RED": "#ef4444",
            "BLACK": "#1a1a1a"
        }
        return colors.get(health, "#a0a0a0")

    def get_definitions(self) -> Dict:
        """Return current SLA definitions."""
        return {
            "version": "1.0.0",
            "rules": self.sla_rules
        }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="WINDI SLA Sentinel v1.0.0 — Three Dragons Protocol",
        epilog="O Guardião do Tempo"
    )
    parser.add_argument("--check", action="store_true", help="Check all active findings")
    parser.add_argument("--finding", type=str, metavar="ID", help="Check specific finding")
    parser.add_argument("--forecast", action="store_true", help="Queue forecast")
    parser.add_argument("--dashboard", action="store_true", help="Dashboard data")
    parser.add_argument("--definitions", action="store_true", help="Show SLA definitions")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")

    args = parser.parse_args()

    sentinel = SLASentinel()

    if args.check:
        report = sentinel.check_all_active()
        path = sentinel.save_status_report(report)

        if args.json:
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            print("=" * 60)
            print("   WINDI SLA SENTINEL — Status Report")
            print("=" * 60)
            print(f"   Timestamp: {report['check_timestamp_utc']}")
            print(f"   Active Findings: {report['active_findings']}")
            print(f"   Overall Health: {report['overall_health']}")
            print()
            print("   SUMMARY:")
            for level, count in report["summary"].items():
                icon = {"green": "🟢", "yellow": "🟡", "orange": "🟠", "red": "🔴", "black": "⬛"}.get(level, "⚪")
                print(f"     {icon} {level.upper()}: {count}")
            print()
            if report["statuses"]:
                print("   DETAILS:")
                for s in report["statuses"][:10]:  # Limit display
                    print(f"     {s['finding_id']} | {s['severity']} | {s['stage']} | {s['alert_level']} | {s['time_remaining_minutes']:.0f}min left")
            print()
            print(f"   Alerts Generated: {report['alerts_generated']}")
            print(f"   Report saved: {path}")
            print("=" * 60)

    elif args.finding:
        result = sentinel.check_single(args.finding)
        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"Finding: {result.get('finding_id', args.finding)}")
            print(f"Status: {result.get('current_status', 'N/A')}")
            print(f"Stage: {result.get('stage', 'N/A')}")
            print(f"Alert Level: {result.get('alert_level', 'N/A')}")
            print(f"Time Remaining: {result.get('time_remaining_minutes', 0):.0f} minutes")

    elif args.forecast:
        forecast = sentinel.get_queue_forecast()
        if args.json:
            print(json.dumps(forecast, indent=2, ensure_ascii=False))
        else:
            print(f"Queue Size: {forecast['queue_size']}")
            print(f"At Risk: {forecast['at_risk']}")
            print(f"Estimated Breaches: {forecast['estimated_breaches']}")
            print(f"Bottleneck: {forecast['bottleneck_stage'] or 'None'}")

    elif args.dashboard:
        data = sentinel.get_dashboard_data()
        if args.json:
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"Health: {data['overall_health']} ({data['health_color']})")
            print(f"Active: {data['active_count']}")
            print(f"At Risk: {data['at_risk']}")

    elif args.definitions:
        defs = sentinel.get_definitions()
        if args.json:
            print(json.dumps(defs, indent=2, ensure_ascii=False))
        else:
            print("SLA Definitions:")
            for sev, rules in defs["rules"].items():
                print(f"  {sev}: ACK {rules.get('max_acknowledge_minutes', '?')}min, RESOLVE {rules.get('max_resolve_minutes', '?')}min")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
