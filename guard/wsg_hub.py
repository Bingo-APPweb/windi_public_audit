#!/usr/bin/env python3
"""
WINDI Surface Guard v0.2.0 — Hub Controller
"Observar. Registrar. CURAR. Dissuadir."

Orchestrates all WSG modules as a unified daemon.

Constitutional Principle:
"WSG não toma decisões. WSG preserva decisões já tomadas."

I9 Safe: WSG operates within SEALED parameters.
Does not escalate autonomy. Heals within constitutional envelope.

Author: WINDI Publishing House
Version: 0.2.0
Date: 10 Feb 2026
"""

import os
import sys
import json
import time
import signal
import logging
import threading
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
import http.server
import socketserver


# ═══════════════════════════════════════════════════════════════════════════════
# IMPORTS — WSG Modules
# ═══════════════════════════════════════════════════════════════════════════════

try:
    from .wsg_health_monitor import ServiceHealthMonitor
    from .wsg_link_checker import LinkIntegrityChecker
    from .wsg_css_guard import CSSDriftDetector
    from .wsg_i18n_guard import I18nConsistencyGuard
except ImportError:
    # Running standalone
    from wsg_health_monitor import ServiceHealthMonitor
    from wsg_link_checker import LinkIntegrityChecker
    from wsg_css_guard import CSSDriftDetector
    from wsg_i18n_guard import I18nConsistencyGuard


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

WSG_CONFIG = {
    "version": "0.3.0",
    "codename": "CIA Integration",

    # Module schedules
    "health_interval_seconds": 60,
    "link_check_hour": 3,      # 03:00 daily
    "css_audit_hour": 4,       # 04:00 daily
    "i18n_audit_day": 0,       # Monday (0 = Monday, 6 = Sunday)
    "i18n_audit_hour": 5,      # 05:00 weekly

    # Pages to monitor (WINDI One Tree Domain)
    "pages_to_scan": [
        "https://windi-domain.com/desktop/",
        "https://windi-domain.com/keys/",
        "https://windi-domain.com/pioneer/",
        "https://windi-domain.com/verify-public/",
        "https://windi-domain.com/how-it-works/",
    ],

    # API settings — Port 8113 (8094 = Forensic Validation, 8095 = TSIL)
    "api_port": 8113,
    "api_host": "0.0.0.0",

    # Reports
    "reports_dir": "/opt/windi/guard/reports",
}


# ═══════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class WSGStatus:
    """Current status of WSG Hub."""
    version: str
    uptime_seconds: float
    health_monitor: Dict[str, Any]
    last_link_scan: Optional[str]
    last_css_audit: Optional[str]
    last_i18n_audit: Optional[str]
    heal_count: int
    alert_count: int


# ═══════════════════════════════════════════════════════════════════════════════
# SIMPLE SCHEDULER
# ═══════════════════════════════════════════════════════════════════════════════

class SimpleScheduler:
    """
    Simple task scheduler for WSG.

    Supports:
    - Interval-based tasks (every N seconds)
    - Daily tasks (at specific hour)
    - Weekly tasks (on specific day at specific hour)
    """

    def __init__(self):
        self.tasks: List[Dict[str, Any]] = []
        self.running = False
        self.logger = logging.getLogger("WSG.Scheduler")

    def every_seconds(self, seconds: int, func, name: str = ""):
        """Schedule task to run every N seconds."""
        self.tasks.append({
            "type": "interval",
            "interval": seconds,
            "func": func,
            "name": name or func.__name__,
            "last_run": 0,
        })

    def daily_at(self, hour: int, func, name: str = ""):
        """Schedule task to run daily at specific hour."""
        self.tasks.append({
            "type": "daily",
            "hour": hour,
            "func": func,
            "name": name or func.__name__,
            "last_run": None,
        })

    def weekly_at(self, day: int, hour: int, func, name: str = ""):
        """Schedule task to run weekly on specific day at specific hour."""
        self.tasks.append({
            "type": "weekly",
            "day": day,  # 0 = Monday
            "hour": hour,
            "func": func,
            "name": name or func.__name__,
            "last_run": None,
        })

    def _should_run(self, task: Dict[str, Any]) -> bool:
        """Check if task should run now."""
        now = time.time()
        now_dt = datetime.now()

        if task["type"] == "interval":
            return (now - task["last_run"]) >= task["interval"]

        elif task["type"] == "daily":
            if task["last_run"] is None:
                return now_dt.hour == task["hour"]
            last_dt = datetime.fromisoformat(task["last_run"])
            return (now_dt.date() > last_dt.date() and now_dt.hour >= task["hour"])

        elif task["type"] == "weekly":
            if task["last_run"] is None:
                return now_dt.weekday() == task["day"] and now_dt.hour == task["hour"]
            last_dt = datetime.fromisoformat(task["last_run"])
            days_since = (now_dt - last_dt).days
            return (days_since >= 7 or
                    (now_dt.weekday() == task["day"] and
                     now_dt.hour >= task["hour"] and
                     last_dt.date() < now_dt.date()))

        return False

    def run(self):
        """Run scheduler loop."""
        self.running = True
        self.logger.info("Scheduler started")

        while self.running:
            for task in self.tasks:
                if self._should_run(task):
                    try:
                        self.logger.info(f"Running task: {task['name']}")
                        task["func"]()

                        if task["type"] == "interval":
                            task["last_run"] = time.time()
                        else:
                            task["last_run"] = datetime.now().isoformat()

                    except Exception as e:
                        self.logger.error(f"Task {task['name']} failed: {e}")

            time.sleep(1)

    def stop(self):
        """Stop scheduler."""
        self.running = False
        self.logger.info("Scheduler stopped")


# ═══════════════════════════════════════════════════════════════════════════════
# WSG HUB API HANDLER
# ═══════════════════════════════════════════════════════════════════════════════

class WSGAPIHandler(http.server.BaseHTTPRequestHandler):
    """HTTP API handler for WSG Hub."""

    hub: 'WSGHub' = None  # Set by WSGHub

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass

    def _send_json(self, data: Any, status: int = 200):
        """Send JSON response."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, ensure_ascii=False, default=str).encode())

    def do_GET(self):
        """Handle GET requests."""
        if self.path == "/api/wsg/status":
            status = self.hub.get_status()
            self._send_json(asdict(status))

        elif self.path == "/api/wsg/health":
            health = self.hub.health_monitor.get_status_summary()
            self._send_json(health)

        elif self.path == "/api/wsg/report":
            report = self.hub.get_latest_report()
            self._send_json(report)

        elif self.path == "/api/wsg/heal-log":
            heals = self.hub.get_heal_log()
            self._send_json(heals)

        elif self.path == "/":
            self._send_json({
                "service": "WSG Hub",
                "version": WSG_CONFIG["version"],
                "endpoints": [
                    "/api/wsg/status",
                    "/api/wsg/health",
                    "/api/wsg/report",
                    "/api/wsg/heal-log",
                ],
            })

        else:
            self._send_json({"error": "Not found"}, 404)


# ═══════════════════════════════════════════════════════════════════════════════
# WSG HUB CONTROLLER
# ═══════════════════════════════════════════════════════════════════════════════

class WSGHub:
    """
    WINDI Surface Guard Hub Controller — Orchestrates all WSG modules.

    Runs as daemon on HUB with:
    - Health Monitor: Every 60 seconds
    - Link Checker: Daily at 03:00
    - CSS Guard: Daily at 04:00 (+ on-deploy hook)
    - i18n Guard: Weekly on Monday at 05:00

    API endpoints:
    - GET /api/wsg/status → status of all modules
    - GET /api/wsg/health → current health check results
    - GET /api/wsg/report → latest full report
    - GET /api/wsg/heal-log → history of repairs
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        log_level: int = logging.INFO,
    ):
        self.config = config or WSG_CONFIG
        self.start_time = time.time()
        self.heal_count = 0
        self.alert_count = 0

        # Setup logging
        self.logger = logging.getLogger("WSG.Hub")
        self.logger.setLevel(log_level)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(
                "[%(asctime)s] WSG-HUB %(levelname)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            ))
            self.logger.addHandler(handler)

        # Initialize modules
        reports_dir = self.config.get("reports_dir", "/opt/windi/guard/reports")
        os.makedirs(reports_dir, exist_ok=True)

        self.health_monitor = ServiceHealthMonitor(
            reports_dir=reports_dir,
            log_level=log_level,
        )

        self.link_checker = LinkIntegrityChecker(
            pages=self.config.get("pages_to_scan"),
            reports_dir=reports_dir,
            log_level=log_level,
        )

        self.css_guard = CSSDriftDetector(
            reports_dir=reports_dir,
            log_level=log_level,
        )

        self.i18n_guard = I18nConsistencyGuard(
            reports_dir=reports_dir,
            log_level=log_level,
        )

        # Scheduler
        self.scheduler = SimpleScheduler()

        # Last run timestamps
        self.last_link_scan: Optional[str] = None
        self.last_css_audit: Optional[str] = None
        self.last_i18n_audit: Optional[str] = None

        # API server
        self.api_server: Optional[socketserver.TCPServer] = None

    def _run_health_check(self):
        """Run health check cycle."""
        results = self.health_monitor.check_all()

        # Count heals
        for receipt in self.health_monitor.receipts:
            if receipt.result == "success":
                self.heal_count += 1

    def _run_link_check(self):
        """Run link integrity check."""
        self.logger.info("Starting daily link integrity scan...")
        report = self.link_checker.scan_all()
        self.last_link_scan = datetime.now(timezone.utc).isoformat()

        if report.broken_count > 0:
            self.alert_count += 1
            self.logger.warning(f"Link scan found {report.broken_count} broken links")

    def _run_css_audit(self):
        """Run CSS drift audit."""
        self.logger.info("Starting CSS drift audit...")
        pages = self.config.get("pages_to_scan", [])
        report = self.css_guard.audit_all(pages)
        self.last_css_audit = datetime.now(timezone.utc).isoformat()

        if report.total_drift_count > 0:
            self.alert_count += 1
            self.logger.warning(f"CSS audit found {report.total_drift_count} drifts")

    def _run_i18n_audit(self):
        """Run i18n consistency audit."""
        self.logger.info("Starting weekly i18n audit...")
        pages = self.config.get("pages_to_scan", [])
        report = self.i18n_guard.audit_all(pages)
        self.last_i18n_audit = datetime.now(timezone.utc).isoformat()

        if report.incomplete_count > 0:
            self.alert_count += 1
            self.logger.warning(f"i18n audit found {report.incomplete_count} incomplete elements")

    def get_status(self) -> WSGStatus:
        """Get current WSG status."""
        return WSGStatus(
            version=self.config.get("version", "0.2.0"),
            uptime_seconds=round(time.time() - self.start_time, 1),
            health_monitor={
                "services_monitored": len(self.health_monitor.services),
                "failure_counts": dict(self.health_monitor.failure_counts),
            },
            last_link_scan=self.last_link_scan,
            last_css_audit=self.last_css_audit,
            last_i18n_audit=self.last_i18n_audit,
            heal_count=self.heal_count,
            alert_count=self.alert_count,
        )

    def get_latest_report(self) -> Dict[str, Any]:
        """Get latest combined report."""
        reports_dir = self.config.get("reports_dir", "/opt/windi/guard/reports")

        def load_latest(prefix: str) -> Optional[Dict]:
            try:
                files = sorted([f for f in os.listdir(reports_dir) if f.startswith(prefix)], reverse=True)
                if files:
                    with open(os.path.join(reports_dir, files[0]), 'r') as f:
                        return json.load(f)
            except Exception:
                pass
            return None

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "link_integrity": load_latest("link_integrity_"),
            "css_audit": load_latest("css_audit_"),
            "i18n_audit": load_latest("i18n_audit_"),
        }

    def get_heal_log(self) -> List[Dict[str, Any]]:
        """Get history of WSG heal receipts."""
        return [r.to_dict() for r in self.health_monitor.receipts[-100:]]

    def _start_api_server(self):
        """Start API server in background thread."""
        WSGAPIHandler.hub = self

        port = self.config.get("api_port", 8094)
        host = self.config.get("api_host", "0.0.0.0")

        try:
            self.api_server = socketserver.TCPServer((host, port), WSGAPIHandler)
            self.logger.info(f"WSG API server started on {host}:{port}")

            api_thread = threading.Thread(target=self.api_server.serve_forever, daemon=True)
            api_thread.start()
        except Exception as e:
            self.logger.error(f"Failed to start API server: {e}")

    def run(self):
        """
        Run WSG Hub as daemon.

        Schedule:
        - Health: every 60 seconds
        - Links: daily at 03:00
        - CSS: daily at 04:00
        - i18n: weekly Monday at 05:00
        """
        self.logger.info("=" * 60)
        self.logger.info("WINDI Surface Guard v0.2.0 — Infrastructure Healer")
        self.logger.info("\"Observar. Registrar. CURAR. Dissuadir.\"")
        self.logger.info("=" * 60)

        # Setup signal handlers
        def signal_handler(signum, frame):
            self.logger.info("Shutdown signal received")
            self.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Schedule tasks
        health_interval = self.config.get("health_interval_seconds", 60)
        self.scheduler.every_seconds(health_interval, self._run_health_check, "HealthMonitor")

        link_hour = self.config.get("link_check_hour", 3)
        self.scheduler.daily_at(link_hour, self._run_link_check, "LinkChecker")

        css_hour = self.config.get("css_audit_hour", 4)
        self.scheduler.daily_at(css_hour, self._run_css_audit, "CSSGuard")

        i18n_day = self.config.get("i18n_audit_day", 0)
        i18n_hour = self.config.get("i18n_audit_hour", 5)
        self.scheduler.weekly_at(i18n_day, i18n_hour, self._run_i18n_audit, "I18nGuard")

        # Start API server
        self._start_api_server()

        # Run initial health check
        self.logger.info("Running initial health check...")
        self._run_health_check()

        # Start scheduler
        self.logger.info("Scheduler started. Press Ctrl+C to stop.")
        self.scheduler.run()

    def stop(self):
        """Stop WSG Hub."""
        self.logger.info("Stopping WSG Hub...")
        self.scheduler.stop()
        if self.api_server:
            self.api_server.shutdown()
        self.logger.info("WSG Hub stopped")


# ═══════════════════════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Run WSG Hub as standalone CLI."""
    import argparse

    parser = argparse.ArgumentParser(
        description="WSG Hub Controller v0.2.0 — Infrastructure Healer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python wsg_hub.py --daemon                    # Run as daemon
  python wsg_hub.py --health-check              # Run single health check
  python wsg_hub.py --full-audit                # Run all audits now
  python wsg_hub.py --status                    # Show current status
        """
    )

    parser.add_argument("--daemon", action="store_true", help="Run as daemon (default)")
    parser.add_argument("--health-check", action="store_true", help="Run single health check")
    parser.add_argument("--full-audit", action="store_true", help="Run all audits now")
    parser.add_argument("--status", action="store_true", help="Show current status")
    parser.add_argument("--port", type=int, default=None, help="API port (default: from WSG_CONFIG)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO

    config = WSG_CONFIG.copy()
    if args.port is not None:
        config["api_port"] = args.port

    hub = WSGHub(config=config, log_level=log_level)

    if args.health_check:
        print("Running health check...")
        hub._run_health_check()
        status = hub.health_monitor.get_status_summary()
        print(json.dumps(status, indent=2))

    elif args.full_audit:
        print("Running full audit suite...")
        hub._run_health_check()
        hub._run_link_check()
        hub._run_css_audit()
        hub._run_i18n_audit()
        print("Full audit complete. Check /opt/windi/guard/reports/")

    elif args.status:
        # Quick status check
        status = hub.get_status()
        print(f"\nWSG Hub Status v{status.version}")
        print(f"  Uptime: {status.uptime_seconds}s")
        print(f"  Services: {status.health_monitor['services_monitored']}")
        print(f"  Heals: {status.heal_count}")
        print(f"  Alerts: {status.alert_count}")

    else:
        # Default: run as daemon
        hub.run()


if __name__ == "__main__":
    main()
