#!/usr/bin/env python3
"""
WSG v0.2.0 — Service Health Monitor
"Observar. Registrar. CURAR. Dissuadir."

Module 1: Monitors critical endpoints and auto-repairs downed services.

Constitutional Alignment:
- Auto-restart is NOT autonomy escalation (I9 safe)
- It's operational maintenance (like systemd watchdog)
- Operates within SEALED parameters defined by human

Author: WINDI Publishing House
Version: 0.2.0
Date: 10 Feb 2026
"""

import os
import json
import time
import hashlib
import subprocess
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict
from enum import Enum
import urllib.request
import urllib.error

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

WSG_MONITORED_SERVICES: Dict[str, Dict[str, Any]] = {
    # ═══════════════════════════════════════════════════════════════════════════════
    # WINDI NERVOUS SYSTEM — Updated 21 Mar 2026
    # Ports aligned with CLAUDE.md §13 Mapa de Portas
    # ═══════════════════════════════════════════════════════════════════════════════
    "sandbox_core": {
        "url": "http://localhost:8091/health",
        "process": "sandbox_core.py",
        "restart_cmd": None,  # Manual — nohup per CLAUDE.md Rule 10
        "critical": True,
        "timeout": 10,
        "max_failures": 3,
    },
    "dragon_hub": {
        "url": "http://localhost:8108/health",
        "process": "dragon_hub.py",
        "restart_cmd": None,  # Manual — API key protected
        "critical": True,
        "timeout": 10,
        "max_failures": 3,
    },
    "desktop_gen7": {
        "url": "http://localhost:8119/health",
        "process": "gen7_server.py",
        "restart_cmd": None,  # Manual — systemd
        "critical": True,
        "timeout": 10,
        "max_failures": 3,
    },
    "forensic_ledger": {
        "url": "http://localhost:8101/health",
        "process": "forensic_ledger.py",
        "restart_cmd": None,  # SEALED PORT — NEVER auto-restart
        "critical": True,
        "timeout": 10,
        "max_failures": 3,
    },
    "verify_public": {
        "url": "http://localhost:8114/health",
        "process": "verify_public.py",
        "restart_cmd": None,  # SEALED PORT
        "critical": False,
        "timeout": 10,
        "max_failures": 3,
    },
    "dispatch_gateway": {
        "url": "http://localhost:8121/health",
        "process": "dispatch_gateway.py",
        "restart_cmd": None,  # Manual
        "critical": False,
        "timeout": 10,
        "max_failures": 3,
    },
    "wallet_service": {
        "url": "http://localhost:8099/health",
        "process": "wallet_service.py",
        "restart_cmd": None,  # Manual
        "critical": False,
        "timeout": 10,
        "max_failures": 3,
    },
    "lead_admin": {
        "url": "http://localhost:8096/health",
        "process": "lead_admin.py",
        "restart_cmd": None,  # systemd — env secured
        "critical": False,
        "timeout": 10,
        "max_failures": 3,
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

class ServiceStatus(Enum):
    """Service health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"
    RESTARTING = "restarting"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a single health check."""
    service: str
    status: ServiceStatus
    response_time_ms: float
    http_status: Optional[int] = None
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class WSGHealReceipt:
    """
    WSG-HEAL Receipt — Virtue Receipt for each repair action.
    Immutable record of infrastructure healing.
    """
    receipt_id: str
    type: str = "WSG-HEAL"
    subtype: str = ""
    service: str = ""
    reason: str = ""
    action: str = ""
    result: str = ""
    downtime_seconds: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    hash: str = ""

    def __post_init__(self):
        """Calculate receipt hash after initialization."""
        if not self.hash:
            self.hash = self._calculate_hash()

    def _calculate_hash(self) -> str:
        """Calculate SHA-256 hash of receipt contents."""
        content = f"{self.receipt_id}|{self.type}|{self.subtype}|{self.service}|{self.reason}|{self.action}|{self.result}|{self.timestamp}"
        return f"sha256:{hashlib.sha256(content.encode()).hexdigest()[:16]}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


# ═══════════════════════════════════════════════════════════════════════════════
# SERVICE HEALTH MONITOR
# ═══════════════════════════════════════════════════════════════════════════════

class ServiceHealthMonitor:
    """
    WSG Service Health Monitor — Auto-healing for WINDI services.

    Cycle:
    1. Ping each service every 60s
    2. If 3 consecutive failures → AUTO-RESTART (if restart_cmd != None)
    3. If restart fails → ALERT in Forensic Ledger + log
    4. If critical=True and restart fails 2x → ESCALATE (email/notification)
    5. Generate WSG-HEAL Receipt for each repair
    """

    def __init__(
        self,
        services: Optional[Dict[str, Dict[str, Any]]] = None,
        reports_dir: str = "/opt/windi/guard/reports",
        log_level: int = logging.INFO,
    ):
        self.services = services or WSG_MONITORED_SERVICES
        self.reports_dir = reports_dir
        self.failure_counts: Dict[str, int] = {name: 0 for name in self.services}
        self.restart_attempts: Dict[str, int] = {name: 0 for name in self.services}
        self.receipts: List[WSGHealReceipt] = []

        # Setup logging
        self.logger = logging.getLogger("WSG.HealthMonitor")
        self.logger.setLevel(log_level)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(
                "[%(asctime)s] WSG-HEALTH %(levelname)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            ))
            self.logger.addHandler(handler)

        # Ensure reports directory exists
        os.makedirs(self.reports_dir, exist_ok=True)

    def check_service(self, name: str) -> HealthCheckResult:
        """
        Perform health check on a single service.

        Args:
            name: Service name from WSG_MONITORED_SERVICES

        Returns:
            HealthCheckResult with status and metrics
        """
        config = self.services.get(name)
        if not config:
            return HealthCheckResult(
                service=name,
                status=ServiceStatus.UNKNOWN,
                response_time_ms=0,
                error=f"Service '{name}' not configured"
            )

        url = config["url"]
        timeout = config.get("timeout", 10)

        start_time = time.time()

        try:
            req = urllib.request.Request(url, method="GET")
            req.add_header("User-Agent", "WSG-HealthMonitor/0.2.0")

            with urllib.request.urlopen(req, timeout=timeout) as response:
                response_time = (time.time() - start_time) * 1000
                http_status = response.status

                # Determine status based on response
                if 200 <= http_status < 300:
                    status = ServiceStatus.HEALTHY
                elif 500 <= http_status < 600:
                    status = ServiceStatus.DOWN
                else:
                    status = ServiceStatus.DEGRADED

                return HealthCheckResult(
                    service=name,
                    status=status,
                    response_time_ms=round(response_time, 2),
                    http_status=http_status,
                )

        except urllib.error.HTTPError as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service=name,
                status=ServiceStatus.DOWN if e.code >= 500 else ServiceStatus.DEGRADED,
                response_time_ms=round(response_time, 2),
                http_status=e.code,
                error=f"HTTP {e.code}: {e.reason}"
            )

        except urllib.error.URLError as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service=name,
                status=ServiceStatus.DOWN,
                response_time_ms=round(response_time, 2),
                error=f"Connection failed: {str(e.reason)}"
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                service=name,
                status=ServiceStatus.UNKNOWN,
                response_time_ms=round(response_time, 2),
                error=f"Unexpected error: {str(e)}"
            )

    def restart_service(self, name: str) -> WSGHealReceipt:
        """
        Attempt to restart a failed service.

        Args:
            name: Service name to restart

        Returns:
            WSGHealReceipt documenting the restart attempt
        """
        config = self.services.get(name, {})
        restart_cmd = config.get("restart_cmd")

        if not restart_cmd:
            self.logger.warning(f"No restart command for {name} — manual intervention required")
            return WSGHealReceipt(
                receipt_id=f"WSG-HEAL-{int(time.time())}-{name[:4].upper()}",
                subtype="SERVICE_RESTART_SKIPPED",
                service=name,
                reason="No restart command configured",
                action="none",
                result="skipped",
                metadata={"requires_manual": True}
            )

        start_time = time.time()
        self.restart_attempts[name] = self.restart_attempts.get(name, 0) + 1

        self.logger.info(f"Attempting restart of {name} (attempt #{self.restart_attempts[name]})")

        try:
            # Execute restart command
            result = subprocess.run(
                restart_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )

            # Wait briefly for service to start
            time.sleep(2)

            # Verify service is back up
            check = self.check_service(name)
            downtime = time.time() - start_time

            if check.status == ServiceStatus.HEALTHY:
                self.logger.info(f"✅ {name} restarted successfully (downtime: {downtime:.1f}s)")
                self.failure_counts[name] = 0
                self.restart_attempts[name] = 0

                receipt = WSGHealReceipt(
                    receipt_id=f"WSG-HEAL-{int(time.time())}-{name[:4].upper()}",
                    subtype="SERVICE_RESTART",
                    service=name,
                    reason=f"{self.failure_counts.get(name, 0)} consecutive health check failures",
                    action="auto_restart",
                    result="success",
                    downtime_seconds=round(downtime, 2),
                    metadata={
                        "restart_cmd": restart_cmd,
                        "attempt": self.restart_attempts.get(name, 1),
                    }
                )
            else:
                self.logger.error(f"❌ {name} restart failed — service still unhealthy")
                receipt = WSGHealReceipt(
                    receipt_id=f"WSG-HEAL-{int(time.time())}-{name[:4].upper()}",
                    subtype="SERVICE_RESTART",
                    service=name,
                    reason=f"Restart attempt #{self.restart_attempts[name]}",
                    action="auto_restart",
                    result="failed",
                    downtime_seconds=round(downtime, 2),
                    metadata={
                        "restart_cmd": restart_cmd,
                        "attempt": self.restart_attempts[name],
                        "post_restart_status": check.status.value,
                        "error": check.error,
                    }
                )

        except subprocess.TimeoutExpired:
            downtime = time.time() - start_time
            self.logger.error(f"❌ {name} restart timed out")
            receipt = WSGHealReceipt(
                receipt_id=f"WSG-HEAL-{int(time.time())}-{name[:4].upper()}",
                subtype="SERVICE_RESTART",
                service=name,
                reason="Restart command timed out",
                action="auto_restart",
                result="timeout",
                downtime_seconds=round(downtime, 2),
            )

        except Exception as e:
            downtime = time.time() - start_time
            self.logger.error(f"❌ {name} restart error: {e}")
            receipt = WSGHealReceipt(
                receipt_id=f"WSG-HEAL-{int(time.time())}-{name[:4].upper()}",
                subtype="SERVICE_RESTART",
                service=name,
                reason=str(e),
                action="auto_restart",
                result="error",
                downtime_seconds=round(downtime, 2),
            )

        # Store receipt
        self.receipts.append(receipt)
        self._save_receipt(receipt)

        return receipt

    def check_all(self) -> Dict[str, HealthCheckResult]:
        """
        Check all configured services and auto-heal if needed.

        Returns:
            Dictionary of service names to their health check results
        """
        results: Dict[str, HealthCheckResult] = {}

        for name, config in self.services.items():
            result = self.check_service(name)
            results[name] = result

            max_failures = config.get("max_failures", 3)

            if result.status in (ServiceStatus.DOWN, ServiceStatus.UNKNOWN):
                self.failure_counts[name] = self.failure_counts.get(name, 0) + 1
                self.logger.warning(
                    f"⚠️ {name} unhealthy (failure {self.failure_counts[name]}/{max_failures}): {result.error}"
                )

                # Auto-restart if threshold reached
                if self.failure_counts[name] >= max_failures:
                    self.logger.warning(f"🔧 {name} reached failure threshold — initiating auto-restart")
                    self.restart_service(name)

                    # Check for escalation (critical service, multiple restart failures)
                    if config.get("critical") and self.restart_attempts.get(name, 0) >= 2:
                        self._escalate(name)
            else:
                # Reset failure count on healthy check
                if self.failure_counts.get(name, 0) > 0:
                    self.logger.info(f"✅ {name} recovered after {self.failure_counts[name]} failures")
                self.failure_counts[name] = 0

        return results

    def _escalate(self, name: str) -> None:
        """
        Escalate critical service failure for human intervention.

        Args:
            name: Service name requiring escalation
        """
        self.logger.critical(
            f"🚨 ESCALATION: Critical service {name} failed to restart after "
            f"{self.restart_attempts[name]} attempts — HUMAN INTERVENTION REQUIRED"
        )

        # Create escalation receipt
        receipt = WSGHealReceipt(
            receipt_id=f"WSG-ESC-{int(time.time())}-{name[:4].upper()}",
            subtype="ESCALATION",
            service=name,
            reason=f"Critical service failed {self.restart_attempts[name]} restart attempts",
            action="escalate",
            result="pending_human",
            metadata={
                "critical": True,
                "restart_attempts": self.restart_attempts[name],
                "requires": "human_intervention",
            }
        )

        self.receipts.append(receipt)
        self._save_receipt(receipt)

        # TODO: Send notification (email, Slack, etc.)

    def _save_receipt(self, receipt: WSGHealReceipt) -> None:
        """Save receipt to reports directory."""
        filename = f"{receipt.receipt_id}.json"
        filepath = os.path.join(self.reports_dir, filename)

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(receipt.to_json())
            self.logger.debug(f"Receipt saved: {filepath}")
        except Exception as e:
            self.logger.error(f"Failed to save receipt: {e}")

    def get_status_summary(self) -> Dict[str, Any]:
        """
        Get summary of all service statuses.

        Returns:
            Dictionary with service statuses and overall health
        """
        results = self.check_all()

        healthy = sum(1 for r in results.values() if r.status == ServiceStatus.HEALTHY)
        degraded = sum(1 for r in results.values() if r.status == ServiceStatus.DEGRADED)
        down = sum(1 for r in results.values() if r.status == ServiceStatus.DOWN)

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_services": len(results),
            "healthy": healthy,
            "degraded": degraded,
            "down": down,
            "overall": "healthy" if down == 0 and degraded == 0 else ("degraded" if down == 0 else "critical"),
            "services": {
                name: {
                    "status": r.status.value,
                    "response_time_ms": r.response_time_ms,
                    "failure_count": self.failure_counts.get(name, 0),
                    "error": r.error,
                }
                for name, r in results.items()
            },
            "recent_heals": len(self.receipts),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Run health monitor as standalone CLI."""
    import argparse

    parser = argparse.ArgumentParser(
        description="WSG Service Health Monitor v0.2.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python wsg_health_monitor.py --check-all
  python wsg_health_monitor.py --check governance_api
  python wsg_health_monitor.py --daemon --interval 60
        """
    )

    parser.add_argument("--check-all", action="store_true", help="Check all services once")
    parser.add_argument("--check", type=str, help="Check specific service")
    parser.add_argument("--restart", type=str, help="Manually restart service")
    parser.add_argument("--status", action="store_true", help="Show status summary")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    parser.add_argument("--interval", type=int, default=60, help="Check interval in seconds (daemon mode)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    monitor = ServiceHealthMonitor(log_level=log_level)

    if args.check_all:
        results = monitor.check_all()
        for name, result in results.items():
            status_icon = "✅" if result.status == ServiceStatus.HEALTHY else "❌"
            print(f"{status_icon} {name}: {result.status.value} ({result.response_time_ms}ms)")
            if result.error:
                print(f"   └─ {result.error}")

    elif args.check:
        result = monitor.check_service(args.check)
        status_icon = "✅" if result.status == ServiceStatus.HEALTHY else "❌"
        print(f"{status_icon} {args.check}: {result.status.value} ({result.response_time_ms}ms)")
        if result.error:
            print(f"   └─ {result.error}")

    elif args.restart:
        receipt = monitor.restart_service(args.restart)
        print(f"Restart result: {receipt.result}")
        print(receipt.to_json())

    elif args.status:
        summary = monitor.get_status_summary()
        print(json.dumps(summary, indent=2))

    elif args.daemon:
        print(f"WSG Health Monitor starting (interval: {args.interval}s)")
        print("Press Ctrl+C to stop")
        try:
            while True:
                monitor.check_all()
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\nWSG Health Monitor stopped")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
