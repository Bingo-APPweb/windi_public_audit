#!/usr/bin/env python3
"""
WINDI Tenant Boundary Event Verifier
=====================================
Checks the Ledger for any tenant boundary crossing events or conflicts.

This script is designed for:
- CI/CD pipelines (exit code 0 = pass, 2 = fail)
- Auditor review sessions
- Production monitoring

Usage:
    python3 verify_tenant_boundary_events.py
    python3 verify_tenant_boundary_events.py --strict    # Fail on any boundary alert
    python3 verify_tenant_boundary_events.py --tenant <id>  # Filter by tenant

26 February 2026 — WINDI Governance Institute
"""

import sys
import json
import urllib.request
from datetime import datetime, timezone
from collections import defaultdict

LEDGER_URL = "http://127.0.0.1:8101"


def get_json(url: str) -> dict:
    """GET request helper."""
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e)}


def main():
    strict_mode = "--strict" in sys.argv
    filter_tenant = None

    # Parse --tenant <id> argument
    for i, arg in enumerate(sys.argv):
        if arg == "--tenant" and i + 1 < len(sys.argv):
            filter_tenant = sys.argv[i + 1]

    print("=" * 70)
    print("  WINDI Tenant Boundary Event Verifier")
    print("=" * 70)
    print()

    # Fetch all receipts
    data = get_json(f"{LEDGER_URL}/api/receipts?limit=5000")
    if "error" in data:
        print(f"ERROR: Cannot reach Ledger API: {data['error']}")
        sys.exit(2)

    receipts = data.get("receipts", [])
    print(f"Total receipts scanned: {len(receipts)}")

    # Track documents by com_id to detect conflicts
    doc_tenant_map = defaultdict(set)  # com_id -> set of tenant_ids
    boundary_events = []
    conflicts = []

    for r in receipts:
        meta = r.get("metadata", {})
        tenant_id = meta.get("tenant_id")

        if filter_tenant and tenant_id != filter_tenant:
            continue

        # Check for tenant context receipts (boundary alerts)
        receipt_type = meta.get("receipt_type")
        if receipt_type == "tenant_boundary_alert":
            boundary_events.append({
                "id": r.get("id"),
                "from_tenant": meta.get("from_tenant"),
                "to_tenant": meta.get("to_tenant"),
                "timestamp": r.get("created_at"),
                "reason": meta.get("reason", "Unknown")
            })

        # Track com_id to tenant mapping for conflict detection
        com_id = meta.get("com_id") or r.get("isp_context", "").split(":")[-1]
        if com_id and tenant_id:
            doc_tenant_map[com_id].add(tenant_id)

    # Detect conflicts (same com_id with multiple tenants)
    for com_id, tenants in doc_tenant_map.items():
        if len(tenants) > 1:
            conflicts.append({
                "com_id": com_id,
                "tenants": list(tenants),
                "severity": "CRITICAL"
            })

    # Build result
    result = {
        "test": "Tenant Boundary Event Verification",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": "strict" if strict_mode else "standard",
        "filter_tenant": filter_tenant,
        "total_receipts": len(receipts),
        "boundary_events": len(boundary_events),
        "boundary_samples": boundary_events[:5],
        "conflicts_detected": len(conflicts),
        "conflict_details": conflicts[:5],
        "unique_documents_tracked": len(doc_tenant_map),
        "status": "PASS"
    }

    # Determine pass/fail
    if conflicts:
        result["status"] = "FAIL"
        result["failure_reason"] = f"{len(conflicts)} cross-tenant conflicts detected"
    elif strict_mode and boundary_events:
        result["status"] = "FAIL"
        result["failure_reason"] = f"{len(boundary_events)} boundary events in strict mode"

    print()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print()

    # Summary output
    if result["status"] == "PASS":
        print("✅ PASS: No tenant isolation violations detected")
        if boundary_events:
            print(f"   ℹ️  {len(boundary_events)} boundary events logged (within tolerance)")
        sys.exit(0)
    else:
        print(f"❌ FAIL: {result['failure_reason']}")
        if conflicts:
            print("   CONFLICTS:")
            for c in conflicts[:3]:
                print(f"     - {c['com_id']}: tenants={c['tenants']}")
        if boundary_events:
            print("   BOUNDARY EVENTS:")
            for e in boundary_events[:3]:
                print(f"     - {e['from_tenant']} → {e['to_tenant']} at {e['timestamp']}")
        sys.exit(2)


if __name__ == "__main__":
    main()
