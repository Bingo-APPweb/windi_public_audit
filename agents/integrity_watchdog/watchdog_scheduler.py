#!/usr/bin/env python3
"""
WINDI Integrity Watchdog Scheduler v1.0.0 — Three Dragons Protocol
===================================================================

Scheduling and dead-man switch for continuous integrity verification.
If the Watchdog stops watching, someone needs to know.

Author: WINDI Publishing House / Three Dragons Protocol
"""

import json
import os
import glob
import argparse
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional

# Import the main engine
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from watchdog_engine import IntegrityWatchdog


class WatchdogScheduler:
    """
    Scheduler for Integrity Watchdog with dead-man switch capability.

    Features:
    - Periodic execution every N hours
    - Event-triggered execution
    - Dead-man switch: alerts if no check in 12 hours
    """

    def __init__(self, watchdog: IntegrityWatchdog = None):
        """
        Initialize scheduler.

        Args:
            watchdog: IntegrityWatchdog instance (created if not provided)
        """
        self.watchdog = watchdog or IntegrityWatchdog()
        self.base_path = '/opt/windi/agents/integrity_watchdog'
        self.state_file = os.path.join(self.base_path, 'scheduler_state.json')
        self.dead_man_path = os.path.join(self.base_path, 'alerts', 'dead_man')

        os.makedirs(self.dead_man_path, exist_ok=True)

        self.state = self._load_state()

    def _load_state(self) -> Dict:
        """Load scheduler state from file."""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

        return {
            "last_check_utc": None,
            "total_checks": 0,
            "last_status": None,
            "daemon_started_utc": None,
            "daemon_pid": None
        }

    def _save_state(self) -> None:
        """Save scheduler state to file."""
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)

    def run_periodic(self, interval_hours: int = 6, max_iterations: int = None) -> None:
        """
        Execute full_check periodically.

        Args:
            interval_hours: Hours between checks
            max_iterations: Maximum number of iterations (None = infinite)
        """
        self.state["daemon_started_utc"] = datetime.now(timezone.utc).isoformat()
        self.state["daemon_pid"] = os.getpid()
        self._save_state()

        print(f"Watchdog scheduler started. Interval: {interval_hours}h")
        print(f"PID: {os.getpid()}")

        iterations = 0
        while max_iterations is None or iterations < max_iterations:
            try:
                # Run check
                print(f"\n[{datetime.now(timezone.utc).isoformat()}] Running full check...")
                results = self.watchdog.run_full_check()
                self.watchdog.save_report(results)

                # Update state
                self.state["last_check_utc"] = results["timestamp_utc"]
                self.state["last_status"] = results["overall_status"]
                self.state["total_checks"] = self.state.get("total_checks", 0) + 1
                self._save_state()

                print(f"Check complete: {results['overall_status']}")

                iterations += 1

                if max_iterations is None or iterations < max_iterations:
                    # Sleep until next check
                    print(f"Next check in {interval_hours} hours...")
                    time.sleep(interval_hours * 3600)

            except KeyboardInterrupt:
                print("\nScheduler stopped by user.")
                break
            except Exception as e:
                print(f"Error during check: {e}")
                # Still sleep to avoid tight error loop
                time.sleep(60)

        self.state["daemon_started_utc"] = None
        self.state["daemon_pid"] = None
        self._save_state()

    def run_on_event(self, event_type: str) -> Dict:
        """
        Trigger check based on external event.

        Args:
            event_type: Type of event (cycle_close, new_submission, etc.)

        Returns:
            Check results
        """
        print(f"Event-triggered check: {event_type}")
        results = self.watchdog.run_full_check()
        self.watchdog.save_report(results)

        self.state["last_check_utc"] = results["timestamp_utc"]
        self.state["last_status"] = results["overall_status"]
        self.state["total_checks"] = self.state.get("total_checks", 0) + 1
        self._save_state()

        return results

    def dead_man_switch(self, max_hours: int = 12) -> Dict:
        """
        Check if the last verification report is within threshold.

        If NO check in the last N hours, generate CRITICAL alert.

        Args:
            max_hours: Maximum hours without a check before alert

        Returns:
            Status dictionary
        """
        now = datetime.now(timezone.utc)
        threshold = now - timedelta(hours=max_hours)

        # Find most recent check report
        reports = sorted(
            glob.glob(os.path.join(self.watchdog.reports_path, "CHK-*.json")),
            reverse=True
        )

        status = {
            "check_utc": now.isoformat(),
            "threshold_hours": max_hours,
            "watchdog_alive": True,
            "last_check_utc": None,
            "hours_since_last": None,
            "alert_generated": False
        }

        if not reports:
            # No reports at all
            status["watchdog_alive"] = False
            status["reason"] = "No verification reports found"
        else:
            # Check most recent report
            try:
                with open(reports[0], 'r', encoding='utf-8') as f:
                    last_report = json.load(f)

                last_check_str = last_report.get("timestamp_utc", "")
                if last_check_str:
                    last_check = datetime.fromisoformat(last_check_str.replace('Z', '+00:00'))
                    status["last_check_utc"] = last_check_str
                    status["hours_since_last"] = round((now - last_check).total_seconds() / 3600, 2)

                    if last_check < threshold:
                        status["watchdog_alive"] = False
                        status["reason"] = f"No check in {status['hours_since_last']} hours (threshold: {max_hours}h)"

            except (json.JSONDecodeError, IOError, ValueError) as e:
                status["watchdog_alive"] = False
                status["reason"] = f"Could not read last report: {e}"

        # Generate alert if watchdog is not alive
        if not status["watchdog_alive"]:
            status["alert_generated"] = True
            alert = {
                "agent": "integrity-watchdog",
                "alert_type": "DEAD_MAN_SWITCH",
                "timestamp": now.isoformat(),
                "severity": "CRITICAL",
                "description": "Integrity Watchdog has stopped — no verification in threshold period",
                "details": status,
                "action_required": "IMMEDIATE_HUMAN_ATTENTION",
                "message": "The dragon watcher has fallen. Who watches now?"
            }

            alert_file = os.path.join(
                self.dead_man_path,
                f"dead_man_{now.strftime('%Y%m%d_%H%M%S')}.json"
            )

            with open(alert_file, 'w', encoding='utf-8') as f:
                json.dump(alert, f, indent=2, ensure_ascii=False)

            print(f"CRITICAL: Dead-man switch triggered! Alert saved to {alert_file}")

        return status

    def get_status(self) -> Dict:
        """
        Return current scheduler status.

        Returns:
            Status dictionary
        """
        # Refresh state
        self.state = self._load_state()

        # Get recent check info
        reports = sorted(
            glob.glob(os.path.join(self.watchdog.reports_path, "CHK-*.json")),
            reverse=True
        )

        status = {
            "scheduler_state": self.state,
            "reports_count": len(reports),
            "most_recent_report": reports[0] if reports else None,
            "daemon_running": self.state.get("daemon_pid") is not None,
            "watchdog_version": self.watchdog.manifest.get("version", "unknown")
        }

        # Check if daemon is actually running
        if status["daemon_running"]:
            pid = self.state.get("daemon_pid")
            try:
                # Check if process exists
                os.kill(pid, 0)
            except (OSError, TypeError):
                status["daemon_running"] = False
                status["daemon_note"] = "PID recorded but process not found"

        return status


def main():
    """Main entry point for CLI usage."""
    parser = argparse.ArgumentParser(
        description="WINDI Integrity Watchdog Scheduler v1.0.0",
        epilog="If the Watchdog stops, the dead-man switch alerts."
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run as continuous service in foreground"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=6,
        help="Hours between checks in daemon mode (default: 6)"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Execute one check and exit"
    )
    parser.add_argument(
        "--dead-man-check",
        action="store_true",
        help="Check if watchdog is alive (dead-man switch)"
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=12,
        help="Hours threshold for dead-man switch (default: 12)"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show scheduler status"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format"
    )

    args = parser.parse_args()

    scheduler = WatchdogScheduler()

    if args.daemon:
        scheduler.run_periodic(interval_hours=args.interval)

    elif args.once:
        results = scheduler.run_on_event("manual_trigger")
        if args.json:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            print(f"Check complete: {results['overall_status']}")
            print(f"Check ID: {results['check_id']}")

    elif args.dead_man_check:
        status = scheduler.dead_man_switch(max_hours=args.threshold)
        if args.json:
            print(json.dumps(status, indent=2, ensure_ascii=False))
        else:
            if status["watchdog_alive"]:
                print(f"✅ Watchdog ALIVE")
                print(f"   Last check: {status['last_check_utc']}")
                print(f"   Hours since: {status['hours_since_last']}")
            else:
                print(f"❌ WATCHDOG DOWN!")
                print(f"   Reason: {status.get('reason', 'Unknown')}")
                print(f"   Alert generated: {status['alert_generated']}")

    elif args.status:
        status = scheduler.get_status()
        if args.json:
            print(json.dumps(status, indent=2, ensure_ascii=False))
        else:
            print("=" * 50)
            print("   WATCHDOG SCHEDULER STATUS")
            print("=" * 50)
            print(f"   Daemon running: {status['daemon_running']}")
            print(f"   Total reports: {status['reports_count']}")
            print(f"   Total checks: {status['scheduler_state'].get('total_checks', 0)}")
            print(f"   Last check: {status['scheduler_state'].get('last_check_utc', 'Never')}")
            print(f"   Last status: {status['scheduler_state'].get('last_status', 'N/A')}")
            print("=" * 50)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
