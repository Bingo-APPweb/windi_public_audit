#!/usr/bin/env python3
"""
WINDI Tenant Presence Assertion Test
=====================================
Ensures no institutional receipt is created without tenant_id.
Respects legacy allowlist for pre-cutover receipts.

This test is designed for CI/CD pipelines and cron jobs.
Exit code 0 = PASS, Exit code 2 = FAIL (missing tenant)

Usage:
    python3 assert_tenant_presence.py
    python3 assert_tenant_presence.py --strict       # Fail on any receipt without tenant
    python3 assert_tenant_presence.py --no-legacy    # Ignore legacy allowlist

26 February 2026 — WINDI Governance Institute
"""

import sys
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

LEDGER_URL = "http://127.0.0.1:8101"
CUTOVER_TIMESTAMP = 1772198399  # 2026-02-26 23:59:59 UTC (end of rollout day)

# Governance levels that require tenant_id
INSTITUTIONAL_LEVELS = {"HIGH", "GOLD", "MEDIUM"}


def load_legacy_allowlist() -> dict:
    """Load legacy receipts allowlist."""
    allowlist_path = Path(__file__).parent / "legacy_receipts_allowlist.json"
    try:
        with open(allowlist_path, "r") as f:
            return json.load(f)
    except Exception:
        return {"exempt_missing_tenant_id": [], "legacy_ledger_ids": [], "legacy_receipt_prefixes": []}


def is_legacy_exempt(receipt: dict, allowlist: dict) -> bool:
    """Check if receipt is exempt due to legacy status."""
    receipt_id = receipt.get("id", "")
    created_at = receipt.get("created_at", 0)
    meta = receipt.get("metadata", {})
    tenant_id = meta.get("tenant_id", "")

    # Pre-cutover receipts are legacy
    if created_at < CUTOVER_TIMESTAMP:
        return True

    # Check allowlist by ledger ID
    if receipt_id in allowlist.get("legacy_ledger_ids", []):
        return True

    # Check allowlist by tenant prefix
    if tenant_id in allowlist.get("exempt_missing_tenant_id", []):
        return True

    # Check allowlist by receipt prefix
    for prefix in allowlist.get("legacy_receipt_prefixes", []):
        if receipt_id.startswith(prefix):
            return True

    return False


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
    ignore_legacy = "--no-legacy" in sys.argv

    print("=" * 60)
    print("  WINDI Tenant Presence Assertion Test")
    print("=" * 60)
    print()

    # Load legacy allowlist
    allowlist = {} if ignore_legacy else load_legacy_allowlist()
    if allowlist:
        print(f"Legacy allowlist loaded: {len(allowlist.get('legacy_ledger_ids', []))} IDs, "
              f"{len(allowlist.get('exempt_missing_tenant_id', []))} tenants exempt")
    print(f"Cutover date: 2026-02-26 (ts={CUTOVER_TIMESTAMP})")
    print()

    # Fetch receipts
    data = get_json(f"{LEDGER_URL}/api/receipts?limit=2000")
    if "error" in data:
        print(f"ERROR: Cannot reach Ledger API: {data['error']}")
        sys.exit(2)

    receipts = data.get("receipts", [])
    print(f"Total receipts: {len(receipts)}")

    # Check for missing tenant_id
    missing = []
    legacy_exempt = []
    checked = 0
    by_level = {}

    for r in receipts:
        governance_level = r.get("governance_level", "")
        meta = r.get("metadata", {})
        tenant_id = meta.get("tenant_id")

        # Track by governance level
        by_level.setdefault(governance_level, {"total": 0, "with_tenant": 0, "legacy": 0})
        by_level[governance_level]["total"] += 1
        if tenant_id:
            by_level[governance_level]["with_tenant"] += 1

        # Check institutional receipts
        if governance_level in INSTITUTIONAL_LEVELS:
            checked += 1
            if not tenant_id:
                # Check if legacy exempt
                if is_legacy_exempt(r, allowlist):
                    by_level[governance_level]["legacy"] += 1
                    legacy_exempt.append({
                        "id": r.get("id", "?"),
                        "doc_name": r.get("doc_name", "?")[:40],
                        "reason": "pre-cutover" if r.get("created_at", 0) < CUTOVER_TIMESTAMP else "allowlist"
                    })
                else:
                    missing.append({
                        "id": r.get("id", "?"),
                        "doc_name": r.get("doc_name", "?")[:50],
                        "governance_level": governance_level,
                        "app": r.get("app", "?"),
                        "created_at": r.get("created_at")
                    })

        # Strict mode: check ALL receipts (ignores legacy)
        if strict_mode and not tenant_id and not is_legacy_exempt(r, allowlist):
            entry = {
                "id": r.get("id", "?"),
                "doc_name": r.get("doc_name", "?")[:50],
                "governance_level": governance_level or "NONE",
                "app": r.get("app", "?")
            }
            if entry not in missing:
                missing.append(entry)

    # Build result
    result = {
        "test": "Tenant Presence Assertion",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": "strict" if strict_mode else "institutional",
        "legacy_policy": "ignored" if ignore_legacy else "enforced",
        "cutover_timestamp": CUTOVER_TIMESTAMP,
        "total_receipts": len(receipts),
        "institutional_checked": checked,
        "legacy_exempt_count": len(legacy_exempt),
        "missing_tenant_count": len(missing),
        "missing_tenant_samples": missing[:5],
        "legacy_exempt_samples": legacy_exempt[:3],
        "by_governance_level": by_level,
        "status": "PASS" if not missing else "FAIL"
    }

    print()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print()

    if result["status"] == "PASS":
        if legacy_exempt:
            print(f"✅ PASS: All post-cutover receipts have tenant_id ({len(legacy_exempt)} legacy exempt)")
        else:
            print("✅ PASS: All institutional receipts have tenant_id")
        sys.exit(0)
    else:
        print(f"❌ FAIL: {len(missing)} post-cutover receipts missing tenant_id")
        print("   These are NEW receipts that should have tenant_id.")
        for m in missing[:3]:
            print(f"   - {m['id']}: {m['doc_name']}")
        sys.exit(2)


if __name__ == "__main__":
    main()
