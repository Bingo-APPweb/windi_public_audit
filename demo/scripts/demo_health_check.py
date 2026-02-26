#!/usr/bin/env python3
"""
WINDI Auditor Demo — System Health Check
=========================================
Quick verification that all critical systems are operational.
Run this BEFORE the demo to ensure everything works.

Usage:
    python3 demo_health_check.py

26 February 2026 — WINDI Governance Institute
"""

import json
import urllib.request
from datetime import datetime, timezone

SERVICES = [
    {"name": "Forensic Ledger", "port": 8101, "endpoint": "/api/receipts?limit=1", "critical": True},
    {"name": "Orchestrator", "port": 8104, "endpoint": "/", "critical": True},
    {"name": "Communiqué Engine", "port": 8105, "endpoint": "/api/communique/list", "critical": True},
    {"name": "Dragon Server", "port": 8106, "endpoint": "/health", "critical": True},
    {"name": "Forensic API", "port": 8094, "endpoint": "/health", "critical": False},
    {"name": "Vault Service", "port": 8107, "endpoint": "/health", "critical": False},
    {"name": "Sentinel LAW", "port": 8103, "endpoint": "/health", "critical": False},
]

def check_service(service):
    """Check if a service is responding."""
    url = f"http://127.0.0.1:{service['port']}{service['endpoint']}"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return {"status": "UP", "code": resp.status}
    except urllib.error.HTTPError as e:
        # Some services return 404 for root but are still up
        if e.code in [404, 405]:
            return {"status": "UP", "code": e.code}
        return {"status": "DOWN", "error": str(e)}
    except Exception as e:
        return {"status": "DOWN", "error": str(e)}

def main():
    print()
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║        WINDI DEMO — PRE-FLIGHT HEALTH CHECK                  ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print()

    all_ok = True
    critical_ok = True

    print("  SERVICE STATUS")
    print("  ───────────────────────────────────────")

    for service in SERVICES:
        result = check_service(service)
        is_critical = service.get("critical", False)
        marker = "🔴" if is_critical else "⚪"

        if result["status"] == "UP":
            print(f"  {marker} ✅ {service['name']:20} (:{service['port']})")
        else:
            print(f"  {marker} ❌ {service['name']:20} (:{service['port']}) — {result.get('error', 'DOWN')}")
            all_ok = False
            if is_critical:
                critical_ok = False

    print()
    print("  ───────────────────────────────────────")

    if all_ok:
        print("  ✅ ALL SYSTEMS OPERATIONAL")
        print("     Demo ready to proceed.")
    elif critical_ok:
        print("  ⚠️  NON-CRITICAL SERVICES DOWN")
        print("     Demo can proceed with limited functionality.")
    else:
        print("  ❌ CRITICAL SERVICES DOWN")
        print("     Demo NOT recommended. Fix issues first.")

    print()
    print("  Timestamp:", datetime.now(timezone.utc).isoformat())
    print()

    # Return exit code
    return 0 if critical_ok else 1

if __name__ == "__main__":
    exit(main())
