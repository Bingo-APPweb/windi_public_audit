#!/usr/bin/env python3
"""
WINDI Auditor Demo — Isolation Score Live
==========================================
Shows real-time multi-tenant isolation metrics.

Usage:
    python3 demo_isolation_score.py
    python3 demo_isolation_score.py --tenant siemens-pilot

26 February 2026 — WINDI Governance Institute
"""

import sys
import json
import urllib.request
from datetime import datetime, timezone

LEDGER_URL = "http://127.0.0.1:8101"
CUTOVER_TIMESTAMP = 1772198399

def get_json(url):
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e)}

def calculate_isolation_score(receipts):
    """Calculate isolation score (0-100) based on tenant compliance."""
    if not receipts:
        return 100, {}

    total = 0
    with_tenant = 0
    with_hash = 0
    conflicts = 0
    legacy = 0

    tenant_map = {}  # com_id -> set of tenant_ids

    for r in receipts:
        meta = r.get("metadata", {})
        created_at = r.get("created_at", 0)
        tenant_id = meta.get("tenant_id")
        metadata_hash = meta.get("metadata_hash")
        com_id = meta.get("references", {}).get("com_id", "")

        # Skip non-tenant-relevant receipts
        if meta.get("segregation_mode") != "forensic" and meta.get("context") != "multi-tenant-isolation":
            continue

        total += 1

        # Legacy check
        if created_at < CUTOVER_TIMESTAMP:
            legacy += 1
            continue

        if tenant_id:
            with_tenant += 1
        if metadata_hash:
            with_hash += 1

        # Track conflicts
        if com_id and tenant_id:
            tenant_map.setdefault(com_id, set()).add(tenant_id)

    # Count conflicts
    for tenants in tenant_map.values():
        if len(tenants) > 1:
            conflicts += 1

    # Calculate score
    post_cutover = total - legacy
    if post_cutover == 0:
        score = 100
    else:
        tenant_coverage = (with_tenant / post_cutover) * 40 if post_cutover > 0 else 40
        hash_coverage = (with_hash / post_cutover) * 30 if post_cutover > 0 else 30
        conflict_penalty = min(conflicts * 10, 30)
        score = min(100, max(0, tenant_coverage + hash_coverage + 30 - conflict_penalty))

    details = {
        "total_receipts": total,
        "legacy_exempt": legacy,
        "post_cutover": post_cutover,
        "with_tenant_id": with_tenant,
        "with_metadata_hash": with_hash,
        "conflicts": conflicts
    }

    return round(score), details

def main():
    tenant_filter = None
    for arg in sys.argv[1:]:
        if not arg.startswith("-"):
            tenant_filter = arg

    print()
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║        WINDI ISOLATION SCORE — LIVE AUDITOR VIEW             ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print()

    # Fetch receipts
    data = get_json(f"{LEDGER_URL}/api/receipts?limit=1000")
    if "error" in data:
        print(f"  ⚠️  Ledger API: {data['error']}")
        print()
        return

    receipts = data.get("receipts", [])

    # Filter by tenant if specified
    if tenant_filter:
        receipts = [r for r in receipts if r.get("metadata", {}).get("tenant_id") == tenant_filter]
        print(f"  Tenant Filter: {tenant_filter}")
        print()

    # Calculate score
    score, details = calculate_isolation_score(receipts)

    # Display
    print(f"  ┌─────────────────────────────────────┐")
    print(f"  │  ISOLATION SCORE                    │")
    print(f"  │                                     │")

    # Score visualization
    bar_filled = int(score / 5)
    bar_empty = 20 - bar_filled
    bar = "█" * bar_filled + "░" * bar_empty

    if score >= 90:
        status = "🟢 EXCELLENT"
    elif score >= 70:
        status = "🟡 GOOD"
    elif score >= 50:
        status = "🟠 FAIR"
    else:
        status = "🔴 CRITICAL"

    print(f"  │     {bar}  {score}/100  │")
    print(f"  │                                     │")
    print(f"  │     Status: {status:20}   │")
    print(f"  └─────────────────────────────────────┘")
    print()

    # Details
    print("  METRICS")
    print("  ───────────────────────────────────────")
    print(f"  Total isolation receipts:    {details['total_receipts']:>6}")
    print(f"  Legacy exempt (pre-cutover): {details['legacy_exempt']:>6}")
    print(f"  Post-cutover receipts:       {details['post_cutover']:>6}")
    print(f"  With tenant_id:              {details['with_tenant_id']:>6}")
    print(f"  With metadata_hash:          {details['with_metadata_hash']:>6}")
    print(f"  Cross-tenant conflicts:      {details['conflicts']:>6}")
    print()

    # Auditor statement
    print("  AUDITOR STATEMENT")
    print("  ───────────────────────────────────────")
    if score >= 90 and details['conflicts'] == 0:
        print("  ✅ Multi-tenant isolation VERIFIED")
        print("     No cross-tenant conflicts detected.")
        print("     All post-cutover receipts compliant.")
    elif details['conflicts'] > 0:
        print(f"  ⚠️  {details['conflicts']} cross-tenant conflicts detected")
        print("     Requires investigation.")
    else:
        print("  ⚠️  Partial compliance")
        print("     Some receipts missing tenant metadata.")
    print()

    print("  Timestamp:", datetime.now(timezone.utc).isoformat())
    print()

if __name__ == "__main__":
    main()
