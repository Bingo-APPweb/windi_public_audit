#!/usr/bin/env python3
"""
WINDI Governance Hub — Agent Collector v1.0.0
==============================================

Collects heartbeat and state from all 8 constellation agents.
Read-only. Zero-knowledge. Aggregation only.

The Hub NEVER decides. The Hub displays, routes, registers.
Human decides via Hub. Maestro registers. Ledger seals.

Three Dragons Protocol — Guardian Approved.
"""

import json
import hashlib
import argparse
import os
import glob
import subprocess
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any


class HubCollector:
    """
    Collects status from all 8 agents and produces unified hub_state.json.
    NEVER modifies agent state. Read-only aggregation.
    """

    AGENT_REGISTRY = {
        "sentinela": {
            "name": "Sentinela",
            "shelf": "detection",
            "icon": "🔍",
            "version": "1.0.0",
            "manifest_path": "/opt/windi/agents/compliance/manifest.json",
            "status_path": "/opt/windi/engine/sentinela_status.json",
            "description": "Compliance verification agent"
        },
        "pulse-agent": {
            "name": "Pulse Agent",
            "shelf": "detection",
            "icon": "💓",
            "version": "1.0.0",
            "manifest_path": "/opt/windi/agents/pulse_agent/manifest.json",
            "engine_path": "/opt/windi/agents/pulse_agent/pulse_engine.py",
            "baselines_path": "/opt/windi/agents/pulse_agent/baselines/",
            "patterns_path": "/opt/windi/agents/pulse_agent/patterns/",
            "description": "Predictive pattern analysis"
        },
        "sla-sentinel": {
            "name": "SLA Sentinel",
            "shelf": "detection",
            "icon": "⏱️",
            "version": "1.0.0",
            "manifest_path": "/opt/windi/agents/sla_sentinel/manifest.json",
            "engine_path": "/opt/windi/agents/sla_sentinel/sla_engine.py",
            "definitions_path": "/opt/windi/agents/sla_sentinel/sla_definitions.json",
            "description": "Real-time SLA monitoring"
        },
        "maestro": {
            "name": "Maestro",
            "shelf": "orchestration",
            "icon": "🎼",
            "version": "1.2.0",
            "manifest_path": "/opt/windi/agents/maestro/manifest.json",
            "engine_path": "/opt/windi/agents/maestro/maestro_agent.py",
            "state_db": "/opt/windi/agents/maestro/state/maestro_state.db",
            "description": "Governance cycle orchestration"
        },
        "onboarding-agent": {
            "name": "Onboarding Agent",
            "shelf": "orchestration",
            "icon": "🚀",
            "version": "1.0.0",
            "manifest_path": "/opt/windi/agents/onboarding_agent/manifest.json",
            "engine_path": "/opt/windi/agents/onboarding_agent/onboarding_engine.py",
            "intake_path": "/opt/windi/agents/onboarding_agent/intake/",
            "description": "Client/ISP provisioning pipeline"
        },
        "isp-manager": {
            "name": "ISP Manager",
            "shelf": "verification",
            "icon": "📋",
            "version": "1.0.1",
            "manifest_path": "/opt/windi/agents/isp-manager/manifest.json",
            "scanner_path": "/opt/windi/isp_scanner_v1.1.py",
            "audit_dashboard": "/static/audit_dashboard.html",
            "isp_path": "/opt/windi/isp/",
            "description": "ISP profile lifecycle management"
        },
        "integrity-watchdog": {
            "name": "Integrity Watchdog",
            "shelf": "verification",
            "icon": "🐕",
            "version": "1.0.0",
            "manifest_path": "/opt/windi/agents/integrity_watchdog/manifest.json",
            "engine_path": "/opt/windi/agents/integrity_watchdog/watchdog_engine.py",
            "reports_path": "/opt/windi/agents/integrity_watchdog/reports/",
            "description": "Forensic ledger integrity verification"
        },
        "report-agent": {
            "name": "Report Agent",
            "shelf": "meta_governance",
            "icon": "📊",
            "version": "1.0.0",
            "engine_path": "/opt/windi/engine/cycle_report_generator.py",
            "reports_path": "/opt/windi/reports/",
            "description": "Governance cycle report generation"
        }
    }

    def __init__(self):
        self.state_path = "/opt/windi/hub/cache/hub_state.json"
        self.log_path = "/opt/windi/hub/logs/collector.log"
        self.constellation_path = "/opt/windi/agents/CONSTELLATION.json"

        # Ensure directories exist
        os.makedirs(os.path.dirname(self.state_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

    def collect_all(self) -> Dict[str, Any]:
        """
        Collect state from all 8 agents.
        Returns complete hub_state.json.
        """
        now = datetime.now(timezone.utc)

        hub_state = {
            "hub_version": "1.0.0",
            "collected_utc": now.isoformat(),
            "constellation_hash": self._get_constellation_hash(),
            "constellation_status": "OPERATIONAL",
            "agents_total": 8,
            "agents_responding": 0,
            "agents_silent": 0,
            "shelves": {
                "detection": [],
                "orchestration": [],
                "verification": [],
                "meta_governance": []
            },
            "modules": {
                "constellation_registry": {},
                "live_queue": {},
                "forensic_health": {},
                "predictive_signals": {},
                "reports_seals": {},
                "state_viewer": {}
            },
            "alerts_summary": {
                "critical": 0,
                "high": 0,
                "warning": 0,
                "info": 0
            }
        }

        # Collect from each agent
        for agent_id, config in self.AGENT_REGISTRY.items():
            heartbeat = self._get_heartbeat(agent_id, config)
            hub_state["shelves"][config["shelf"]].append(heartbeat)

            if heartbeat["status"] != "SILENT":
                hub_state["agents_responding"] += 1
            else:
                hub_state["agents_silent"] += 1

        # Populate modules
        self._populate_constellation_registry(hub_state)
        self._populate_live_queue(hub_state)
        self._populate_forensic_health(hub_state)
        self._populate_predictive_signals(hub_state)
        self._populate_reports_seals(hub_state)
        self._populate_state_viewer(hub_state)

        # Determine overall status
        if hub_state["agents_silent"] == 0:
            hub_state["constellation_status"] = "OPERATIONAL"
        elif hub_state["agents_silent"] <= 2:
            hub_state["constellation_status"] = "DEGRADED"
        else:
            hub_state["constellation_status"] = "CRITICAL"

        # Count alerts from all agents
        self._count_alerts(hub_state)

        self._save_state(hub_state)
        self._log(f"Collected state: {hub_state['agents_responding']}/{hub_state['agents_total']} responding, status: {hub_state['constellation_status']}")

        return hub_state

    def _get_constellation_hash(self) -> str:
        """Get truncated hash from CONSTELLATION.json."""
        if os.path.exists(self.constellation_path):
            try:
                with open(self.constellation_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                content = json.dumps(data, sort_keys=True)
                return hashlib.sha256(content.encode()).hexdigest()[:8]
            except Exception:
                pass
        return "unknown"

    def _get_heartbeat(self, agent_id: str, config: Dict) -> Dict:
        """
        Generate heartbeat for an agent.
        Returns: {agent_id, name, icon, shelf, version, status, last_check_utc, advisory_only: true}
        """
        heartbeat = {
            "agent_id": agent_id,
            "name": config["name"],
            "icon": config["icon"],
            "shelf": config["shelf"],
            "version": config.get("version", "1.0.0"),
            "status": "SILENT",
            "last_check_utc": None,
            "advisory_only": True,
            "description": config["description"],
            "metrics": {}
        }

        # Check if manifest exists
        manifest_path = config.get("manifest_path", "")
        if manifest_path and os.path.exists(manifest_path):
            heartbeat["status"] = "OPERATIONAL"
            heartbeat["last_check_utc"] = datetime.now(timezone.utc).isoformat()

            try:
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                    heartbeat["version"] = manifest.get("version", heartbeat["version"])
            except Exception:
                pass

        # Check engine file exists
        engine_path = config.get("engine_path", "")
        if engine_path and os.path.exists(engine_path):
            heartbeat["status"] = "OPERATIONAL"
            heartbeat["last_check_utc"] = datetime.now(timezone.utc).isoformat()

        # Get specific metrics per agent type
        heartbeat["metrics"] = self._get_agent_metrics(agent_id, config)

        return heartbeat

    def _get_agent_metrics(self, agent_id: str, config: Dict) -> Dict:
        """Get specific metrics for each agent type."""
        metrics = {}

        try:
            if agent_id == "pulse-agent":
                # Get latest analysis
                patterns_path = config.get("patterns_path", "")
                if patterns_path and os.path.exists(patterns_path):
                    analyses = sorted(glob.glob(os.path.join(patterns_path, "PLS-*.json")), reverse=True)
                    if analyses:
                        with open(analyses[0], 'r') as f:
                            data = json.load(f)
                        metrics["rhythm_status"] = data.get("rhythm_status", "UNKNOWN")
                        metrics["patterns_count"] = len(data.get("patterns_detected", []))
                        metrics["confidence"] = data.get("confidence", "LOW")

            elif agent_id == "sla-sentinel":
                # Get definitions
                defs_path = config.get("definitions_path", "")
                if defs_path and os.path.exists(defs_path):
                    metrics["definitions_loaded"] = True

            elif agent_id == "integrity-watchdog":
                # Get latest check
                reports_path = config.get("reports_path", "")
                if reports_path and os.path.exists(reports_path):
                    reports = sorted(glob.glob(os.path.join(reports_path, "CHK-*.json")), reverse=True)
                    if reports:
                        with open(reports[0], 'r') as f:
                            data = json.load(f)
                        metrics["overall_status"] = data.get("overall_status", "UNKNOWN")
                        metrics["anomalies_count"] = len(data.get("anomalies", []))
                        metrics["last_check"] = data.get("timestamp_utc", "")

            elif agent_id == "report-agent":
                # Count reports
                reports_path = config.get("reports_path", "")
                if reports_path and os.path.exists(reports_path):
                    reports = glob.glob(os.path.join(reports_path, "**/*.json"), recursive=True)
                    metrics["reports_count"] = len(reports)

            elif agent_id == "isp-manager":
                # Count ISP profiles
                isp_path = config.get("isp_path", "")
                if isp_path and os.path.exists(isp_path):
                    profiles = [d for d in os.listdir(isp_path) if os.path.isdir(os.path.join(isp_path, d))]
                    metrics["profiles_count"] = len(profiles)

            elif agent_id == "maestro":
                # Get active cases
                import sqlite3
                db_path = config.get("state_db", "")
                if db_path and os.path.exists(db_path):
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM governance_cycles WHERE status != 'CLOSED'")
                    metrics["active_cases"] = cursor.fetchone()[0]
                    cursor.execute("SELECT COUNT(*) FROM governance_cycles WHERE status = 'CLOSED'")
                    metrics["closed_cases"] = cursor.fetchone()[0]
                    conn.close()

            elif agent_id == "onboarding-agent":
                # Count onboardings
                intake_path = config.get("intake_path", "")
                if intake_path and os.path.exists(intake_path):
                    onboardings = glob.glob(os.path.join(intake_path, "ONB-*.json"))
                    metrics["onboardings_count"] = len(onboardings)

        except Exception as e:
            metrics["error"] = str(e)[:50]

        return metrics

    def _populate_constellation_registry(self, hub_state: Dict) -> None:
        """Module 1: Agent list with versions, status, heartbeats."""
        registry = {
            "constellation_hash": hub_state["constellation_hash"],
            "agents": [],
            "three_pillars": {
                "CREATION": "isp-manager",
                "VERIFICATION": "sentinela",
                "RESOLUTION": "maestro"
            }
        }

        for shelf, agents in hub_state["shelves"].items():
            for agent in agents:
                registry["agents"].append({
                    "id": agent["agent_id"],
                    "name": agent["name"],
                    "icon": agent["icon"],
                    "shelf": shelf,
                    "version": agent["version"],
                    "status": agent["status"]
                })

        hub_state["modules"]["constellation_registry"] = registry

    def _populate_live_queue(self, hub_state: Dict) -> None:
        """Module 2: Live Governance Queue from Maestro + SLA Sentinel."""
        queue = {
            "active_cases": [],
            "sla_status": "ALL_CLEAR",
            "critical_flags": [],
            "total_active": 0,
            "total_pending_ack": 0
        }

        # Get cases from Maestro
        maestro_db = "/opt/windi/agents/maestro/state/maestro_state.db"
        if os.path.exists(maestro_db):
            try:
                import sqlite3
                conn = sqlite3.connect(maestro_db)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT finding_id, severity, status, created_at, acknowledged_at
                    FROM governance_cycles
                    WHERE status NOT IN ('CLOSED', 'CANCELLED')
                    ORDER BY created_at DESC
                    LIMIT 10
                """)

                for row in cursor.fetchall():
                    queue["active_cases"].append({
                        "finding_id": row["finding_id"],
                        "severity": row["severity"],
                        "status": row["status"],
                        "created_at": row["created_at"],
                        "acknowledged": row["acknowledged_at"] is not None
                    })
                    queue["total_active"] += 1
                    if row["status"] in ["OPEN", "ROUTED"] and not row["acknowledged_at"]:
                        queue["total_pending_ack"] += 1

                conn.close()
            except Exception:
                pass

        # Get SLA status from monitors
        sla_monitors = glob.glob("/opt/windi/agents/sla_sentinel/monitors/sla_status_*.json")
        if sla_monitors:
            try:
                with open(sorted(sla_monitors, reverse=True)[0], 'r') as f:
                    sla_data = json.load(f)
                queue["sla_status"] = sla_data.get("overall_health", "UNKNOWN")
            except Exception:
                pass

        # Get critical flags from agent alerts
        for agent_path in ["/opt/windi/agents/pulse_agent/alerts/pending/",
                          "/opt/windi/agents/integrity_watchdog/alerts/pending/"]:
            if os.path.exists(agent_path):
                for alert_file in glob.glob(os.path.join(agent_path, "*.json"))[:5]:
                    try:
                        with open(alert_file, 'r') as f:
                            alert = json.load(f)
                        if alert.get("severity") in ["HIGH", "CRITICAL"]:
                            queue["critical_flags"].append({
                                "agent": alert.get("agent", "unknown"),
                                "severity": alert.get("severity", "WARNING"),
                                "message": alert.get("description", alert.get("message", ""))[:100]
                            })
                    except Exception:
                        pass

        hub_state["modules"]["live_queue"] = queue

    def _populate_forensic_health(self, hub_state: Dict) -> None:
        """Module 3: Forensic Health from Integrity Watchdog."""
        forensic = {
            "status": "UNKNOWN",
            "last_check_utc": None,
            "checks": {
                "hash_chain": False,
                "receipt_completeness": False,
                "temporal_consistency": False,
                "merkle_integrity": False,
                "cross_references": False
            },
            "anomalies_count": 0,
            "merkle_root_truncated": None,
            "dead_man_alive": False
        }

        reports_path = "/opt/windi/agents/integrity_watchdog/reports/"
        if os.path.exists(reports_path):
            reports = sorted(glob.glob(os.path.join(reports_path, "CHK-*.json")), reverse=True)
            if reports:
                try:
                    with open(reports[0], 'r') as f:
                        data = json.load(f)

                    forensic["status"] = data.get("overall_status", "UNKNOWN")
                    forensic["last_check_utc"] = data.get("timestamp_utc", "")
                    forensic["anomalies_count"] = len(data.get("anomalies", []))

                    # Parse checks
                    for check in data.get("checks_performed", []):
                        check_name = check.get("name", "").replace("_", "_")
                        if check_name in forensic["checks"]:
                            forensic["checks"][check_name] = check.get("status") == "PASS"

                    # Check if watchdog is alive (last check < 12 hours)
                    if forensic["last_check_utc"]:
                        last_check = datetime.fromisoformat(forensic["last_check_utc"].replace('Z', '+00:00'))
                        hours_ago = (datetime.now(timezone.utc) - last_check).total_seconds() / 3600
                        forensic["dead_man_alive"] = hours_ago < 12

                except Exception:
                    pass

        # Get Merkle root from ledger
        ledger_path = "/opt/windi/data/forensic_ledger.json"
        if os.path.exists(ledger_path):
            try:
                with open(ledger_path, 'r') as f:
                    ledger = json.load(f)
                root = ledger.get("merkle_root", "")
                if root:
                    forensic["merkle_root_truncated"] = root[:8]
            except Exception:
                pass

        hub_state["modules"]["forensic_health"] = forensic

    def _populate_predictive_signals(self, hub_state: Dict) -> None:
        """Module 4: Predictive Signals from Pulse Agent."""
        signals = {
            "rhythm_status": "UNKNOWN",
            "patterns_detected": [],
            "confidence": "LOW",
            "last_analysis_utc": None,
            "data_points": 0
        }

        patterns_path = "/opt/windi/agents/pulse_agent/patterns/"
        if os.path.exists(patterns_path):
            analyses = sorted(glob.glob(os.path.join(patterns_path, "PLS-*.json")), reverse=True)
            if analyses:
                try:
                    with open(analyses[0], 'r') as f:
                        data = json.load(f)

                    signals["rhythm_status"] = data.get("rhythm_status", "UNKNOWN")
                    signals["confidence"] = data.get("confidence", "LOW")
                    signals["last_analysis_utc"] = data.get("timestamp_utc", "")
                    signals["data_points"] = data.get("data_points_analyzed", 0)

                    for pattern in data.get("patterns_detected", [])[:5]:
                        signals["patterns_detected"].append({
                            "type": pattern.get("pattern_type", ""),
                            "severity": pattern.get("severity", ""),
                            "description": pattern.get("description", "")[:100]
                        })

                except Exception:
                    pass

        hub_state["modules"]["predictive_signals"] = signals

    def _populate_reports_seals(self, hub_state: Dict) -> None:
        """Module 5: Reports & Seals from Report Agent."""
        reports = {
            "sealed_reports": [],
            "total_count": 0,
            "latest_cycle_id": None
        }

        reports_path = "/opt/windi/reports/"
        if os.path.exists(reports_path):
            report_files = glob.glob(os.path.join(reports_path, "**/*.json"), recursive=True)

            for rf in sorted(report_files, reverse=True)[:10]:
                try:
                    with open(rf, 'r') as f:
                        data = json.load(f)

                    if "seal" in data and data["seal"].get("report_seal_hash"):
                        reports["sealed_reports"].append({
                            "cycle_id": data.get("cycle_id", ""),
                            "generated_utc": data.get("report_generated_utc", ""),
                            "findings_count": data.get("executive_summary", {}).get("total_findings", 0),
                            "seal_hash_truncated": data["seal"]["report_seal_hash"][:8],
                            "file_path": rf
                        })
                        reports["total_count"] += 1

                        if not reports["latest_cycle_id"]:
                            reports["latest_cycle_id"] = data.get("cycle_id", "")

                except Exception:
                    pass

        hub_state["modules"]["reports_seals"] = reports

    def _populate_state_viewer(self, hub_state: Dict) -> None:
        """Module 6: State Viewer - read-only snapshot."""
        state_viewer = {
            "snapshot_utc": hub_state["collected_utc"],
            "constellation_status": hub_state["constellation_status"],
            "agents_responding": hub_state["agents_responding"],
            "agents_total": hub_state["agents_total"],
            "recent_events": []
        }

        # Collect recent events from event log
        events_log = "/opt/windi/hub/logs/events.jsonl"
        if os.path.exists(events_log):
            try:
                with open(events_log, 'r') as f:
                    lines = f.readlines()[-10:]
                for line in reversed(lines):
                    try:
                        event = json.loads(line.strip())
                        state_viewer["recent_events"].append({
                            "timestamp": event.get("timestamp", ""),
                            "agent": event.get("agent", ""),
                            "type": event.get("type", ""),
                            "message": event.get("message", "")[:50]
                        })
                    except Exception:
                        pass
            except Exception:
                pass

        hub_state["modules"]["state_viewer"] = state_viewer

    def _count_alerts(self, hub_state: Dict) -> None:
        """Count alerts from all agent alert directories."""
        alert_dirs = [
            "/opt/windi/agents/pulse_agent/alerts/pending/",
            "/opt/windi/agents/integrity_watchdog/alerts/pending/",
            "/opt/windi/agents/integrity_watchdog/alerts/dead_man/",
            "/opt/windi/agents/sla_sentinel/escalations/pending/"
        ]

        for alert_dir in alert_dirs:
            if os.path.exists(alert_dir):
                for alert_file in glob.glob(os.path.join(alert_dir, "*.json")):
                    try:
                        with open(alert_file, 'r') as f:
                            alert = json.load(f)
                        severity = alert.get("severity", "INFO").upper()
                        if severity == "CRITICAL":
                            hub_state["alerts_summary"]["critical"] += 1
                        elif severity == "HIGH":
                            hub_state["alerts_summary"]["high"] += 1
                        elif severity == "WARNING":
                            hub_state["alerts_summary"]["warning"] += 1
                        else:
                            hub_state["alerts_summary"]["info"] += 1
                    except Exception:
                        pass

    def _save_state(self, hub_state: Dict) -> None:
        """Save hub_state.json to cache."""
        with open(self.state_path, 'w', encoding='utf-8') as f:
            json.dump(hub_state, f, indent=2, ensure_ascii=False)

    def _log(self, message: str) -> None:
        """Log collector activity."""
        timestamp = datetime.now(timezone.utc).isoformat()
        log_line = f"[{timestamp}] {message}\n"
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(log_line)

    def get_heartbeat(self, agent_id: str) -> Optional[Dict]:
        """Get heartbeat for a single agent."""
        if agent_id in self.AGENT_REGISTRY:
            return self._get_heartbeat(agent_id, self.AGENT_REGISTRY[agent_id])
        return None

    def get_module(self, module_name: str) -> Optional[Dict]:
        """Get data for a specific module."""
        # Load cached state
        if os.path.exists(self.state_path):
            with open(self.state_path, 'r') as f:
                state = json.load(f)
            return state.get("modules", {}).get(module_name)
        return None

    def get_all_alerts(self) -> List[Dict]:
        """Get all pending alerts from all agents."""
        alerts = []
        alert_dirs = [
            ("/opt/windi/agents/pulse_agent/alerts/pending/", "pulse-agent"),
            ("/opt/windi/agents/integrity_watchdog/alerts/pending/", "integrity-watchdog"),
            ("/opt/windi/agents/integrity_watchdog/alerts/dead_man/", "integrity-watchdog"),
            ("/opt/windi/agents/sla_sentinel/escalations/pending/", "sla-sentinel")
        ]

        for alert_dir, agent in alert_dirs:
            if os.path.exists(alert_dir):
                for alert_file in glob.glob(os.path.join(alert_dir, "*.json")):
                    try:
                        with open(alert_file, 'r') as f:
                            alert = json.load(f)
                        alert["agent_origin"] = agent
                        alert["file_path"] = alert_file
                        alerts.append(alert)
                    except Exception:
                        pass

        # Sort by severity
        severity_order = {"CRITICAL": 0, "HIGH": 1, "WARNING": 2, "INFO": 3}
        alerts.sort(key=lambda x: severity_order.get(x.get("severity", "INFO").upper(), 4))

        return alerts

    def get_event_envelope(self, event_type: str, severity: str, refs: Dict, timestamps: Dict) -> Dict:
        """Generate standardized event envelope for the Hub."""
        return {
            "type": event_type,
            "severity": severity,
            "refs": refs,  # Hash-only references
            "timestamps": timestamps,
            "generated_utc": datetime.now(timezone.utc).isoformat()
        }


def main():
    """Main entry point for CLI usage."""
    parser = argparse.ArgumentParser(
        description="WINDI Governance Hub Collector v1.0.0 — Three Dragons Protocol",
        epilog="The Hub displays, routes, registers. The Hub NEVER decides."
    )
    parser.add_argument("--collect", action="store_true", help="Execute full collection from all agents")
    parser.add_argument("--agent", type=str, metavar="AGENT_ID", help="Collect from specific agent")
    parser.add_argument("--module", type=str, choices=["registry", "queue", "forensic", "predictive", "reports", "state"],
                       help="Get specific module data")
    parser.add_argument("--alerts", action="store_true", help="Get all pending alerts")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--summary", action="store_true", help="Show human-readable summary")

    args = parser.parse_args()

    collector = HubCollector()

    if args.collect:
        state = collector.collect_all()

        if args.json:
            print(json.dumps(state, indent=2, ensure_ascii=False))
        elif args.summary:
            print("=" * 60)
            print("   WINDI GOVERNANCE HUB — Collection Summary")
            print("=" * 60)
            print(f"   Collected: {state['collected_utc']}")
            print(f"   Constellation Status: {state['constellation_status']}")
            print(f"   Agents: {state['agents_responding']}/{state['agents_total']} responding")
            print(f"   Constellation Hash: {state['constellation_hash']}")
            print()
            print("   SHELVES:")
            for shelf, agents in state["shelves"].items():
                print(f"     {shelf.upper()}:")
                for a in agents:
                    status_icon = "🟢" if a["status"] == "OPERATIONAL" else "🔴"
                    print(f"       {status_icon} {a['icon']} {a['name']} v{a['version']}")
            print()
            print("   ALERTS:")
            print(f"     Critical: {state['alerts_summary']['critical']}")
            print(f"     High: {state['alerts_summary']['high']}")
            print(f"     Warning: {state['alerts_summary']['warning']}")
            print("=" * 60)
        else:
            print(f"Collected: {state['agents_responding']}/{state['agents_total']} agents, status: {state['constellation_status']}")

    elif args.agent:
        heartbeat = collector.get_heartbeat(args.agent)
        if heartbeat:
            if args.json:
                print(json.dumps(heartbeat, indent=2, ensure_ascii=False))
            else:
                print(f"{heartbeat['icon']} {heartbeat['name']} v{heartbeat['version']}")
                print(f"  Status: {heartbeat['status']}")
                print(f"  Shelf: {heartbeat['shelf']}")
                if heartbeat.get("metrics"):
                    print(f"  Metrics: {heartbeat['metrics']}")
        else:
            print(f"Agent not found: {args.agent}")

    elif args.module:
        module_map = {
            "registry": "constellation_registry",
            "queue": "live_queue",
            "forensic": "forensic_health",
            "predictive": "predictive_signals",
            "reports": "reports_seals",
            "state": "state_viewer"
        }
        data = collector.get_module(module_map.get(args.module, args.module))
        if data:
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"Module not found or cache empty. Run --collect first.")

    elif args.alerts:
        alerts = collector.get_all_alerts()
        if args.json:
            print(json.dumps(alerts, indent=2, ensure_ascii=False))
        else:
            print(f"Pending alerts: {len(alerts)}")
            for a in alerts[:10]:
                print(f"  [{a.get('severity', 'INFO')}] {a.get('agent_origin', 'unknown')}: {a.get('message', a.get('description', ''))[:60]}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
