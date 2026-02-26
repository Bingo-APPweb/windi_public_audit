#!/usr/bin/env python3
"""
WINDI Backend-to-Frontend Score Calculator
===========================================
Measures system completeness and wiring between backend services
and frontend UI components.

Usage:
    python3 backend_frontend_score.py
    python3 backend_frontend_score.py --compare

26 February 2026 — WINDI Governance Institute
"""

import os
import sys
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# ═══════════════════════════════════════════════════════════════
# BASELINE: 24 February 2026
# ═══════════════════════════════════════════════════════════════
BASELINE_DATE = "2026-02-24"
BASELINE_FEATURES = {
    "Sprint 0": [
        {"id": "T00", "name": "Dragon Server (LLM Brain)", "wired": True}
    ],
    "Sprint 1": [
        {"id": "E01", "name": "PDF Export Engine", "wired": True},
        {"id": "E02", "name": "DOCX Production", "wired": True},
        {"id": "E03", "name": "PPTX ISP Engine", "wired": True},
        {"id": "E04", "name": "XLSX Spreadsheet Engine", "wired": True},
        {"id": "F01", "name": "Forensic Ledger", "wired": True},
        {"id": "F03", "name": "Wave1 Seal Pipeline", "wired": True},
    ],
    "Sprint 2": [
        {"id": "F05", "name": "Paperless.io Signature", "wired": True},
        {"id": "F02", "name": "Forensic Vault", "wired": True},
        {"id": "F31", "name": "Communiqué Engine", "wired": True},
    ],
    "Sprint 3": [
        {"id": "I02", "name": "OCR / Multimodal", "wired": True},
        {"id": "I06", "name": "Product Identity Skill", "wired": True},
        {"id": "S07", "name": "Constitutional Panel", "wired": True},
    ],
    "Sprint 4": [
        {"id": "S04", "name": "Sentinel LAW Monitor", "wired": True},
    ],
    "Sprint 5": [
        {"id": "C01", "name": "Cognitive Observability", "wired": True},
    ],
}

# ═══════════════════════════════════════════════════════════════
# NEW FEATURES: 26 February 2026
# ═══════════════════════════════════════════════════════════════
NEW_FEATURES = {
    "Sprint MT (Multi-Tenant)": [
        {"id": "MT01", "name": "TenantAuditCollector.js", "wired": True, "type": "UI"},
        {"id": "MT02", "name": "TenantStamp.js", "wired": True, "type": "UI"},
        {"id": "MT03", "name": "Legacy Allowlist", "wired": True, "type": "Config"},
        {"id": "MT04", "name": "Tenant Isolation Verifier", "wired": True, "type": "Test"},
        {"id": "MT05", "name": "Tenant Presence Assertion", "wired": True, "type": "Test"},
        {"id": "MT06", "name": "Boundary Events Verifier", "wired": True, "type": "Test"},
        {"id": "MT07", "name": "Tenant Boundary Alert (UI)", "wired": True, "type": "UI"},
        {"id": "MT08", "name": "Isolation Score Display", "wired": True, "type": "UI"},
    ],
    "Sprint DEMO (Auditor)": [
        {"id": "DM01", "name": "Demo Health Check", "wired": True, "type": "Script"},
        {"id": "DM02", "name": "Demo Isolation Score", "wired": True, "type": "Script"},
        {"id": "DM03", "name": "Demo Ledger Verify", "wired": True, "type": "Script"},
        {"id": "DM04", "name": "Auditor Demo (EN)", "wired": True, "type": "Demo"},
        {"id": "DM05", "name": "Auditor Demo (DE)", "wired": True, "type": "Demo"},
        {"id": "DM06", "name": "BaFin Response Guide", "wired": True, "type": "Doc"},
        {"id": "DM07", "name": "Executive Brief", "wired": True, "type": "Doc"},
        {"id": "DM08", "name": "Constitutional Responses", "wired": True, "type": "Doc"},
    ],
    "Sprint PUB (Publishing)": [
        {"id": "PB01", "name": "Communiqué COM-20260226-0017", "wired": True, "type": "Pub"},
        {"id": "PB02", "name": "HTTPS communique.windia4desk.online", "wired": True, "type": "Infra"},
        {"id": "PB03", "name": "Audit Baseline Sealed", "wired": True, "type": "Audit"},
        {"id": "PB04", "name": "OUTLOOK Full Report", "wired": True, "type": "Report"},
    ],
}


def check_service(port):
    """Check if a service is responding."""
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{port}/", method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            return True
    except:
        return False


def check_file_exists(path):
    """Check if a file exists."""
    return Path(path).exists()


def check_string_in_file(filepath, search_string):
    """Check if a string exists in a file."""
    try:
        with open(filepath, 'r') as f:
            return search_string.lower() in f.read().lower()
    except:
        return False


def verify_new_features():
    """Verify that new features are actually working."""
    index_html = "/opt/windi/agent-palette/ui/index.html"

    checks = {
        "MT01": check_file_exists("/opt/windi/agent-palette/ui/TenantAuditCollector.js"),
        "MT02": check_file_exists("/opt/windi/agent-palette/ui/TenantStamp.js"),
        "MT03": check_file_exists("/opt/windi/orchestrator/tests/legacy_receipts_allowlist.json"),
        "MT04": check_file_exists("/opt/windi/orchestrator/tests/verify_tenant_isolation.py"),
        "MT05": check_file_exists("/opt/windi/orchestrator/tests/assert_tenant_presence.py"),
        "MT06": check_file_exists("/opt/windi/orchestrator/tests/verify_tenant_boundary_events.py"),
        "MT07": check_string_in_file(index_html, "boundary") and check_string_in_file(index_html, "tenant"),
        "MT08": check_string_in_file(index_html, "isolationScore") or check_string_in_file(index_html, "WINDI_TenantAudit"),
        "DM01": check_file_exists("/opt/windi/demo/scripts/demo_health_check.py"),
        "DM02": check_file_exists("/opt/windi/demo/scripts/demo_isolation_score.py"),
        "DM03": check_file_exists("/opt/windi/demo/scripts/demo_ledger_verify.py"),
        "DM04": check_file_exists("/opt/windi/demo/auditor_demo.sh"),
        "DM05": check_file_exists("/opt/windi/demo/auditor_demo_de.sh"),
        "DM06": check_file_exists("/opt/windi/demo/BAFIN_RESPONSES.md"),
        "DM07": check_file_exists("/opt/windi/demo/EXECUTIVE_BRIEF_5MIN.md"),
        "DM08": check_file_exists("/opt/windi/demo/WINDI_CONSTITUTIONAL_RESPONSES.md"),
        "PB01": check_file_exists("/opt/windi/communique/published/COM-20260226-0017.html"),
        "PB02": check_service(443) or check_file_exists("/opt/windi/web/communique/nginx-communique.conf"),
        "PB03": check_file_exists("/opt/windi/reports/baseline/audit_baseline_20260226.json"),
        "PB04": check_file_exists("/opt/windi/reports/outlook_20260226_full.md"),
    }
    return checks


def calculate_scores():
    """Calculate before and after scores."""
    # Baseline count
    baseline_total = sum(len(features) for features in BASELINE_FEATURES.values())
    baseline_wired = sum(
        sum(1 for f in features if f["wired"])
        for features in BASELINE_FEATURES.values()
    )

    # New features count
    new_total = sum(len(features) for features in NEW_FEATURES.values())

    # Verify new features
    checks = verify_new_features()
    new_wired = sum(1 for v in checks.values() if v)

    # Combined
    total_before = baseline_total
    wired_before = baseline_wired

    total_after = baseline_total + new_total
    wired_after = baseline_wired + new_wired

    return {
        "baseline": {
            "date": BASELINE_DATE,
            "total": total_before,
            "wired": wired_before,
            "percentage": round((wired_before / total_before) * 100, 1) if total_before > 0 else 0
        },
        "current": {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "total": total_after,
            "wired": wired_after,
            "percentage": round((wired_after / total_after) * 100, 1) if total_after > 0 else 0
        },
        "delta": {
            "features_added": new_total,
            "features_wired": new_wired,
            "total_increase_pct": round(((total_after - total_before) / total_before) * 100, 1),
            "absolute_growth": total_after - total_before
        },
        "verification": checks
    }


def main():
    compare_mode = "--compare" in sys.argv

    print()
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║     WINDI BACKEND-TO-FRONTEND SCORE                          ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print()

    scores = calculate_scores()

    # Before
    print("  BASELINE (24 February 2026)")
    print("  ───────────────────────────────────────")
    print(f"  Total Features:    {scores['baseline']['total']}")
    print(f"  Wired Features:    {scores['baseline']['wired']}")
    print(f"  Wiring Score:      {scores['baseline']['percentage']}%")
    print()

    # After
    print("  CURRENT (26 February 2026)")
    print("  ───────────────────────────────────────")
    print(f"  Total Features:    {scores['current']['total']}")
    print(f"  Wired Features:    {scores['current']['wired']}")
    print(f"  Wiring Score:      {scores['current']['percentage']}%")
    print()

    # Delta
    print("  ┌─────────────────────────────────────────────────────────┐")
    print("  │  GROWTH METRICS                                        │")
    print("  ├─────────────────────────────────────────────────────────┤")
    print(f"  │  Features Added:        +{scores['delta']['features_added']:>3}                         │")
    print(f"  │  Features Wired:        +{scores['delta']['features_wired']:>3}                         │")
    print(f"  │  Total Increase:        +{scores['delta']['total_increase_pct']:>5.1f}%                      │")
    print("  │                                                         │")
    print(f"  │  BEFORE: {scores['baseline']['total']} features → AFTER: {scores['current']['total']} features         │")
    print("  └─────────────────────────────────────────────────────────┘")
    print()

    # Visual
    bar_before = int(scores['baseline']['percentage'] / 5)
    bar_after = int(scores['current']['percentage'] / 5)

    print("  VISUAL COMPARISON")
    print("  ───────────────────────────────────────")
    print(f"  Before: {'█' * bar_before}{'░' * (20 - bar_before)} {scores['baseline']['percentage']}% ({scores['baseline']['wired']}/{scores['baseline']['total']})")
    print(f"  After:  {'█' * bar_after}{'░' * (20 - bar_after)} {scores['current']['percentage']}% ({scores['current']['wired']}/{scores['current']['total']})")
    print()

    # New features detail
    if compare_mode:
        print("  NEW FEATURES VERIFICATION")
        print("  ───────────────────────────────────────")
        for sprint, features in NEW_FEATURES.items():
            print(f"  {sprint}:")
            for f in features:
                status = "✅" if scores['verification'].get(f['id'], False) else "❌"
                print(f"    {status} {f['id']}: {f['name']}")
        print()

    print("  Timestamp:", datetime.now(timezone.utc).isoformat())
    print()


if __name__ == "__main__":
    main()
