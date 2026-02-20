#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║  WINDI SENTINEL v1.0.0 — The Shield of the Dragon              ║
║  Bloco E: Observability & Protective Monitoring                 ║
║                                                                  ║
║  "Resiliência sem vigilância é apenas sorte organizada."         ║
║                                                                  ║
║  The Sentinel monitors all WINDI services with semantic          ║
║  intelligence — each service is checked at its own health        ║
║  endpoint, not a generic ping. It detects degradation before     ║
║  failure, alerts before crisis, and records incidents in the     ║
║  Forensic Ledger for institutional memory.                       ║
║                                                                  ║
║  Decision Authority: Jober Mögele Correa (Human Dragon)          ║
║  Protocol: Three Dragons — Guardian/Architect/Witness             ║
║  Principle: AI processes. Human decides. WINDI guarantees.       ║
╚══════════════════════════════════════════════════════════════════╝
"""

import json
import hashlib
import subprocess
import socket
import time
import sys
import os
import signal
import logging
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from typing import Optional

# ─────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────

WINDI_BASE = os.environ.get("WINDI_BASE", "/opt/windi")
SENTINEL_VERSION = "1.0.0"
SENTINEL_CODENAME = "Shield of the Dragon"

# Timing
CHECK_INTERVAL_SECONDS = int(os.environ.get("SENTINEL_INTERVAL", "60"))
HTTP_TIMEOUT_SECONDS = int(os.environ.get("SENTINEL_TIMEOUT", "8"))

# Thresholds (conservative — avoid noise)
WARN_THRESHOLD = int(os.environ.get("SENTINEL_WARN", "2"))     # consecutive failures → WARNING
ALERT_THRESHOLD = int(os.environ.get("SENTINEL_ALERT", "5"))   # consecutive failures → ALERT
CRITICAL_THRESHOLD = int(os.environ.get("SENTINEL_CRIT", "10"))  # consecutive failures → CRITICAL

# Paths
LOG_DIR = f"{WINDI_BASE}/logs"
DATA_DIR = f"{WINDI_BASE}/data"
SENTINEL_LOG = f"{LOG_DIR}/sentinel.log"
SENTINEL_STATE_FILE = f"{DATA_DIR}/sentinel_state.json"
FORENSIC_LEDGER_PATH = f"{DATA_DIR}/forensic_ledger.json"
INCIDENT_LOG_PATH = f"{DATA_DIR}/sentinel_incidents.json"

# Forensic API (for future integration when windi-forensic awakens)
FORENSIC_API_HOST = "127.0.0.1"
FORENSIC_API_PORT = 8094

# ─────────────────────────────────────────────────────────
# SERVICE REGISTRY — Semantic Health Map
# Each service has its own "pulse point" — the Sentinel
# knows exactly where to listen for each heartbeat.
# ─────────────────────────────────────────────────────────

SERVICE_REGISTRY = [
    {
        "name": "windi-governance",
        "display": "Governance API",
        "systemd_unit": "windi-governance.service",
        "port": 8080,
        "health_endpoint": "/api/status",
        "health_method": "http",
        "critical": True,
        "description": "Core governance engine — the constitutional heart",
    },
    {
        "name": "windi-babel",
        "display": "BABEL Editor",
        "systemd_unit": "windi-babel.service",
        "port": 8085,
        "health_endpoint": "/",
        "health_method": "http",
        "expected_status": [200, 301, 302],
        "critical": True,
        "description": "A4 Desk document editor — where humans work",
    },
    {
        "name": "windi-landing",
        "display": "A4 Desk Landing",
        "systemd_unit": "windi-landing.service",
        "port": 8086,
        "health_endpoint": "/",
        "health_method": "http",
        "expected_status": [200, 301, 302],
        "critical": False,
        "description": "Landing page and static content",
    },
    {
        "name": "windi-cortex",
        "display": "Cortex",
        "systemd_unit": "windi-cortex.service",
        "port": 8889,
        "health_endpoint": "/health",
        "health_method": "http",
        "critical": False,
        "description": "Metacognition engine — system self-awareness (legacy port 8889)",
    },
    {
        "name": "windi-warroom",
        "display": "War Room",
        "systemd_unit": "windi-warroom.service",
        "port": 8090,
        "health_endpoint": "/",
        "health_method": "http",
        "expected_status": [200, 301, 302, 304, 404],
        "critical": False,
        "description": "Dashboard and briefing center",
    },
    {
        "name": "windi-clone",
        "display": "Clone",
        "systemd_unit": "windi-clone.service",
        "port": 8092,
        "health_endpoint": "/health",
        "health_method": "http",
        "critical": False,
        "description": "Clone territory — constitutional node",
    },
    # DORMANT — re-enable when windi-forensic is deployed (Bloco B5)
    # {
    #     "name": "windi-forensic",
    #     "display": "Forensic API",
    #     "systemd_unit": "windi-forensic.service",
    #     "port": 8094,
    #     "health_endpoint": "/health",
    #     "health_method": "http",
    #     "critical": False,
    #     "description": "Forensic validation and ledger API",
    # },
    {
        "name": "windi-wallet",
        "display": "Sovereign Wallet",
        "systemd_unit": "windi-wallet.service",
        "port": 8099,
        "health_endpoint": "/api/wallet/health",
        "health_method": "http",
        "critical": False,
        "description": "Sovereign Identity Wallet — O Espelho",
    },
    {
        "name": "windi-bridge",
        "display": "Command Bridge",
        "systemd_unit": "windi-bridge.service",
        "port": 8097,
        "health_endpoint": "/health",
        "health_method": "http",
        "critical": True,
        "description": "Sign flow and I9 Gate — sovereignty enforcement",
    },
    {
        "name": "windi-brain",
        "display": "Brain Core",
        "systemd_unit": "windi-brain.service",
        "port": None,
        "health_endpoint": None,
        "health_method": "systemd",
        "critical": True,
        "description": "Brain core runtime — no network port",
    },
    {
        "name": "windi-gateway",
        "display": "Gateway",
        "systemd_unit": "windi-gateway.service",
        "port": None,
        "health_endpoint": None,
        "health_method": "systemd",
        "critical": True,
        "description": "Constitutional firewall — no network port",
    },
]

# ─────────────────────────────────────────────────────────
# LOGGING SETUP
# ─────────────────────────────────────────────────────────

def setup_logging():
    """Configure dual logging: file + stdout for journald."""
    Path(LOG_DIR).mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("sentinel")
    logger.setLevel(logging.INFO)

    # File handler
    fh = logging.FileHandler(SENTINEL_LOG, encoding="utf-8")
    fh.setLevel(logging.INFO)

    # Stdout handler — only when NOT running under systemd
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)

    fmt = logging.Formatter(
        "%(asctime)s [SENTINEL] %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    fh.setFormatter(fmt)
    sh.setFormatter(fmt)

    logger.addHandler(fh)
    # Only add stdout if not under systemd (avoids duplicate lines)
    if not os.environ.get("INVOCATION_ID"):  # systemd sets this
        logger.addHandler(sh)

    return logger


log = setup_logging()

# ─────────────────────────────────────────────────────────
# HEALTH CHECK FUNCTIONS
# ─────────────────────────────────────────────────────────

def check_http_health(host: str, port: int, path: str,
                      expected_status: list = None,
                      timeout: int = HTTP_TIMEOUT_SECONDS) -> dict:
    """
    Check service health via HTTP endpoint.
    Returns status dict with success, status_code, response_time.
    """
    if expected_status is None:
        expected_status = [200]

    url = f"http://{host}:{port}{path}"
    result = {
        "method": "http",
        "url": url,
        "success": False,
        "status_code": None,
        "response_time_ms": None,
        "error": None,
    }

    start = time.monotonic()
    try:
        req = Request(url, method="GET")
        req.add_header("User-Agent", f"WINDI-Sentinel/{SENTINEL_VERSION}")
        with urlopen(req, timeout=timeout) as resp:
            result["status_code"] = resp.status
            result["success"] = resp.status in expected_status
            result["response_time_ms"] = round((time.monotonic() - start) * 1000, 1)
    except HTTPError as e:
        result["status_code"] = e.code
        result["success"] = e.code in expected_status
        result["response_time_ms"] = round((time.monotonic() - start) * 1000, 1)
        if not result["success"]:
            result["error"] = f"HTTP {e.code}: {e.reason}"
    except URLError as e:
        result["error"] = f"Connection failed: {e.reason}"
        result["response_time_ms"] = round((time.monotonic() - start) * 1000, 1)
    except socket.timeout:
        result["error"] = f"Timeout after {timeout}s"
        result["response_time_ms"] = timeout * 1000
    except Exception as e:
        result["error"] = str(e)
        result["response_time_ms"] = round((time.monotonic() - start) * 1000, 1)

    return result


def check_systemd_health(unit_name: str) -> dict:
    """
    Check service health via systemd status.
    For services without network ports (brain, gateway).
    """
    result = {
        "method": "systemd",
        "unit": unit_name,
        "success": False,
        "active_state": None,
        "sub_state": None,
        "pid": None,
        "error": None,
    }

    try:
        proc = subprocess.run(
            ["systemctl", "show", unit_name,
             "--property=ActiveState,SubState,MainPID"],
            capture_output=True, text=True, timeout=10
        )
        if proc.returncode == 0:
            for line in proc.stdout.strip().split("\n"):
                if "=" in line:
                    key, val = line.split("=", 1)
                    if key == "ActiveState":
                        result["active_state"] = val
                        result["success"] = val == "active"
                    elif key == "SubState":
                        result["sub_state"] = val
                    elif key == "MainPID":
                        result["pid"] = int(val) if val != "0" else None
        else:
            result["error"] = f"systemctl returned {proc.returncode}"
    except subprocess.TimeoutExpired:
        result["error"] = "systemctl timeout"
    except Exception as e:
        result["error"] = str(e)

    return result


def check_port_listening(port: int) -> bool:
    """Quick TCP check if port is listening."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            return s.connect_ex(("127.0.0.1", port)) == 0
    except Exception:
        return False


# ─────────────────────────────────────────────────────────
# STATE MANAGEMENT
# ─────────────────────────────────────────────────────────

class SentinelState:
    """
    Persistent state tracking for the Sentinel.
    Tracks consecutive failures per service and overall system health.
    """

    def __init__(self, state_file: str = SENTINEL_STATE_FILE):
        self.state_file = state_file
        self.state = self._load()

    def _load(self) -> dict:
        """Load state from file or initialize fresh."""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, "r") as f:
                    return json.load(f)
        except Exception as e:
            log.warning(f"Could not load state: {e}. Starting fresh.")

        return {
            "version": SENTINEL_VERSION,
            "started_at": self._now(),
            "last_check": None,
            "total_checks": 0,
            "services": {},
        }

    def _save(self):
        """Persist state to file."""
        try:
            Path(self.state_file).parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, "w") as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            log.error(f"Could not save state: {e}")

    def _now(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    def record_check(self, service_name: str, success: bool, details: dict):
        """Record a health check result for a service."""
        if service_name not in self.state["services"]:
            self.state["services"][service_name] = {
                "consecutive_failures": 0,
                "consecutive_successes": 0,
                "total_checks": 0,
                "total_failures": 0,
                "last_status": None,
                "last_checked": None,
                "last_failure": None,
                "last_recovery": None,
                "current_level": "OK",
            }

        svc = self.state["services"][service_name]
        svc["total_checks"] += 1
        svc["last_checked"] = self._now()
        svc["last_status"] = "healthy" if success else "unhealthy"

        if success:
            was_failing = svc["consecutive_failures"] > 0
            svc["consecutive_failures"] = 0
            svc["consecutive_successes"] += 1

            if was_failing:
                svc["last_recovery"] = self._now()
                old_level = svc["current_level"]
                svc["current_level"] = "OK"
                log.info(f"  🟢 {service_name} RECOVERED (was {old_level})")
                return {"event": "recovery", "from_level": old_level}
            else:
                svc["current_level"] = "OK"
        else:
            svc["consecutive_failures"] += 1
            svc["consecutive_successes"] = 0
            svc["total_failures"] += 1
            svc["last_failure"] = self._now()

            # Determine severity level
            failures = svc["consecutive_failures"]
            old_level = svc["current_level"]

            if failures >= CRITICAL_THRESHOLD:
                svc["current_level"] = "CRITICAL"
            elif failures >= ALERT_THRESHOLD:
                svc["current_level"] = "ALERT"
            elif failures >= WARN_THRESHOLD:
                svc["current_level"] = "WARNING"
            else:
                svc["current_level"] = "DEGRADED"

            # Only log on level transitions or first failure
            new_level = svc["current_level"]
            if new_level != old_level or failures == 1:
                return {"event": "escalation", "level": new_level,
                        "failures": failures, "from_level": old_level}

        return None

    def get_summary(self) -> dict:
        """Get overall system health summary."""
        healthy = 0
        degraded = 0
        warning = 0
        alert = 0
        critical = 0

        for name, svc in self.state["services"].items():
            level = svc.get("current_level", "OK")
            if level == "OK":
                healthy += 1
            elif level == "DEGRADED":
                degraded += 1
            elif level == "WARNING":
                warning += 1
            elif level == "ALERT":
                alert += 1
            elif level == "CRITICAL":
                critical += 1

        total = len(self.state["services"])

        # Overall system status
        if critical > 0:
            system_status = "CRITICAL"
        elif alert > 0:
            system_status = "ALERT"
        elif warning > 0:
            system_status = "WARNING"
        elif degraded > 0:
            system_status = "DEGRADED"
        else:
            system_status = "OPERATIONAL"

        return {
            "system_status": system_status,
            "total_services": total,
            "healthy": healthy,
            "degraded": degraded,
            "warning": warning,
            "alert": alert,
            "critical": critical,
            "timestamp": self._now(),
        }

    def finalize_cycle(self):
        """Save state after a complete check cycle."""
        self.state["last_check"] = self._now()
        self.state["total_checks"] += 1
        self._save()


# ─────────────────────────────────────────────────────────
# INCIDENT RECORDING
# ─────────────────────────────────────────────────────────

def record_incident(service_name: str, event: dict, check_details: dict,
                    service_config: dict):
    """
    Record a significant event (escalation or recovery) in the incident log.
    Also attempts to register in the Forensic Ledger.
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    incident = {
        "incident_id": f"SENTINEL-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{service_name}",
        "timestamp": now,
        "service": service_name,
        "display_name": service_config.get("display", service_name),
        "critical_service": service_config.get("critical", False),
        "event_type": event.get("event"),
        "level": event.get("level", event.get("from_level", "OK")),
        "consecutive_failures": event.get("failures", 0),
        "check_details": {
            k: v for k, v in check_details.items()
            if k != "response_body"  # don't store response bodies
        },
        "classification": {
            "doc_type": "SENTINEL_EVENT",
            "category": "INFRA_LEGACY",
            "sub_category": "OBSERVABILITY",
        },
    }

    # Write to incident log
    try:
        incidents_path = Path(INCIDENT_LOG_PATH)
        incidents_path.parent.mkdir(parents=True, exist_ok=True)

        if incidents_path.exists():
            with open(incidents_path, "r") as f:
                incidents = json.load(f)
        else:
            incidents = {"entries": []}

        incidents["entries"].append(incident)

        # Keep last 1000 incidents (rolling window)
        if len(incidents["entries"]) > 1000:
            incidents["entries"] = incidents["entries"][-1000:]

        with open(incidents_path, "w") as f:
            json.dump(incidents, f, indent=2, ensure_ascii=False)

    except Exception as e:
        log.error(f"Could not write incident log: {e}")

    # Attempt Forensic Ledger registration (non-blocking)
    try:
        if check_port_listening(FORENSIC_API_PORT):
            req = Request(
                f"http://{FORENSIC_API_HOST}:{FORENSIC_API_PORT}/api/register",
                data=json.dumps(incident).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urlopen(req, timeout=5) as resp:
                if resp.status in [200, 201]:
                    log.info(f"  📡 Incident registered in Forensic API")
    except Exception:
        pass  # Non-blocking — forensic registration is best-effort


# ─────────────────────────────────────────────────────────
# MAIN CHECK CYCLE
# ─────────────────────────────────────────────────────────

def run_check_cycle(state: SentinelState) -> dict:
    """
    Execute one complete health check cycle across all services.
    Returns summary of the cycle.
    """
    cycle_start = time.monotonic()
    events = []

    for svc in SERVICE_REGISTRY:
        name = svc["name"]

        # Choose health check method
        if svc["health_method"] == "http" and svc["port"]:
            expected = svc.get("expected_status", [200])
            check = check_http_health(
                "127.0.0.1", svc["port"], svc["health_endpoint"],
                expected_status=expected
            )
            success = check["success"]

            # Additional: verify systemd is active too
            systemd_check = check_systemd_health(svc["systemd_unit"])
            if not systemd_check["success"]:
                success = False
                check["systemd_active"] = False
                check["error"] = (check.get("error") or "") + " [systemd inactive]"
            else:
                check["systemd_active"] = True

        elif svc["health_method"] == "systemd":
            check = check_systemd_health(svc["systemd_unit"])
            success = check["success"]

        else:
            check = {"method": "skip", "error": "No health method defined"}
            success = False

        # Record result
        event = state.record_check(name, success, check)

        # Log status with appropriate icon
        if success:
            icon = "✅"
            status_str = f"healthy ({check.get('response_time_ms', '-')}ms)" \
                if check.get("response_time_ms") else "healthy"
        else:
            svc_state = state.state["services"].get(name, {})
            level = svc_state.get("current_level", "DEGRADED")
            level_icons = {
                "DEGRADED": "🟡",
                "WARNING": "🟠",
                "ALERT": "🔴",
                "CRITICAL": "⚫",
            }
            icon = level_icons.get(level, "❌")
            fails = svc_state.get("consecutive_failures", 1)
            err = check.get("error", "unknown")
            status_str = f"{level} (fail #{fails}: {err})"

        port_str = f":{svc['port']}" if svc['port'] else " sys"
        log.info(f"  {icon} {name:<24} {port_str:<6} {status_str}")

        # Handle significant events
        if event:
            events.append({"service": name, "event": event, "check": check})
            if event["event"] == "escalation":
                level = event["level"]
                if level in ("WARNING", "ALERT", "CRITICAL"):
                    log.warning(
                        f"  ⚡ {name} escalated to {level} "
                        f"(fail #{event['failures']})"
                    )
                    record_incident(name, event, check, svc)
            elif event["event"] == "recovery":
                log.info(f"  🟢 {name} recovered from {event['from_level']}")
                record_incident(name, event, check, svc)

    # Cycle summary
    cycle_time = round((time.monotonic() - cycle_start) * 1000, 1)
    summary = state.get_summary()
    summary["cycle_time_ms"] = cycle_time
    summary["events_count"] = len(events)

    return summary


# ─────────────────────────────────────────────────────────
# SENTINEL MAIN LOOP
# ─────────────────────────────────────────────────────────

class SentinelDaemon:
    """
    The Sentinel daemon — runs continuously, checking all services
    at regular intervals. Handles graceful shutdown.
    """

    def __init__(self):
        self.running = True
        self.state = SentinelState()
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

    def _handle_signal(self, signum, frame):
        sig_name = signal.Signals(signum).name
        log.info(f"Received {sig_name} — shutting down gracefully...")
        self.running = False

    def run(self):
        """Main daemon loop."""
        log.info("=" * 64)
        log.info(f"  WINDI SENTINEL v{SENTINEL_VERSION} — {SENTINEL_CODENAME}")
        log.info(f"  Monitoring {len(SERVICE_REGISTRY)} services")
        log.info(f"  Interval: {CHECK_INTERVAL_SECONDS}s")
        log.info(f"  Thresholds: WARN={WARN_THRESHOLD} "
                 f"ALERT={ALERT_THRESHOLD} CRIT={CRITICAL_THRESHOLD}")
        log.info(f"  State file: {SENTINEL_STATE_FILE}")
        log.info(f"  Incident log: {INCIDENT_LOG_PATH}")
        log.info(f"  The shield is raised. 🛡️")
        log.info("=" * 64)

        cycle_count = 0

        while self.running:
            cycle_count += 1
            log.info(f"─── Cycle #{cycle_count} "
                     f"({datetime.now().strftime('%H:%M:%S')}) ───")

            try:
                summary = run_check_cycle(self.state)
                self.state.finalize_cycle()

                # Log cycle summary
                status = summary["system_status"]
                status_icons = {
                    "OPERATIONAL": "🟢",
                    "DEGRADED": "🟡",
                    "WARNING": "🟠",
                    "ALERT": "🔴",
                    "CRITICAL": "⚫",
                }
                icon = status_icons.get(status, "❓")

                log.info(
                    f"  {icon} System: {status} | "
                    f"{summary['healthy']}/{summary['total_services']} healthy | "
                    f"cycle: {summary['cycle_time_ms']}ms"
                )

                if summary["events_count"] > 0:
                    log.info(f"  ⚡ {summary['events_count']} event(s) in this cycle")

            except Exception as e:
                log.error(f"  ❌ Check cycle failed: {e}")

            # Sleep with interruptibility
            for _ in range(CHECK_INTERVAL_SECONDS):
                if not self.running:
                    break
                time.sleep(1)

        # Graceful shutdown
        log.info("─── Sentinel shutting down ───")
        self.state.finalize_cycle()
        log.info("  State saved. Shield lowered. Sentinel rests. 🛡️")


# ─────────────────────────────────────────────────────────
# CLI: SINGLE CHECK MODE (for testing)
# ─────────────────────────────────────────────────────────

def run_single_check():
    """Run a single check cycle and exit. Useful for testing."""
    state = SentinelState()

    print()
    print("╔══════════════════════════════════════════════════════════════════╗")
    print(f"║  WINDI SENTINEL v{SENTINEL_VERSION} — Single Check Mode              ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print()

    summary = run_check_cycle(state)
    state.finalize_cycle()

    print()
    status = summary["system_status"]
    print(f"  System Status: {status}")
    print(f"  Healthy: {summary['healthy']}/{summary['total_services']}")
    print(f"  Cycle time: {summary['cycle_time_ms']}ms")

    if summary.get("warning", 0) + summary.get("alert", 0) + summary.get("critical", 0) > 0:
        print()
        print("  ⚠️  Services with issues:")
        for name, svc in state.state["services"].items():
            if svc["current_level"] != "OK":
                print(f"     {svc['current_level']}: {name} "
                      f"(fails: {svc['consecutive_failures']})")

    print()
    return 0 if status == "OPERATIONAL" else 1


# ─────────────────────────────────────────────────────────
# CLI: STATUS MODE (quick view)
# ─────────────────────────────────────────────────────────

def show_status():
    """Show current Sentinel state without running a new check."""
    state = SentinelState()

    if not state.state.get("services"):
        print("  No Sentinel data yet. Run a check first.")
        return 1

    print()
    print("╔══════════════════════════════════════════════════════════════════╗")
    print(f"║  WINDI SENTINEL v{SENTINEL_VERSION} — Current State                  ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print()

    summary = state.get_summary()

    status_icons = {
        "OPERATIONAL": "🟢", "DEGRADED": "🟡",
        "WARNING": "🟠", "ALERT": "🔴", "CRITICAL": "⚫",
    }

    print(f"  System: {status_icons.get(summary['system_status'], '?')} "
          f"{summary['system_status']}")
    print(f"  Last check: {state.state.get('last_check', 'never')}")
    print(f"  Total cycles: {state.state.get('total_checks', 0)}")
    print()

    for name, svc in state.state["services"].items():
        level = svc.get("current_level", "?")
        icon = "✅" if level == "OK" else status_icons.get(level, "❓")
        fails = svc.get("consecutive_failures", 0)
        last = svc.get("last_checked", "never")
        extra = f" (fails: {fails})" if fails > 0 else ""
        print(f"  {icon} {name:<24} {level:<10}{extra}")

    print()
    return 0


# ─────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────

def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "check":
            return run_single_check()
        elif cmd == "status":
            return show_status()
        elif cmd == "serve":
            daemon = SentinelDaemon()
            daemon.run()
            return 0
        else:
            print(f"Usage: {sys.argv[0]} [check|status|serve]")
            print("  check  — Run one check cycle and exit")
            print("  status — Show current state")
            print("  serve  — Run as daemon (for systemd)")
            return 1
    else:
        # Default: daemon mode
        daemon = SentinelDaemon()
        daemon.run()
        return 0


if __name__ == "__main__":
    sys.exit(main())
