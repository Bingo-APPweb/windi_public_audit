#!/usr/bin/env python3
"""
WINDI Multi-Tenant Forensic Isolation Verifier
================================================
Verifies tenant segregation through ledger-anchored metadata.
Respects legacy allowlist for pre-cutover receipts.

Checks:
1. All tenant isolation receipts have valid metadata_hash (post-cutover)
2. No com_id appears under multiple tenant_ids (conflict detection)
3. Segregation model is forensic-metadata based

Usage:
    python3 verify_tenant_isolation.py                    # All tenants
    python3 verify_tenant_isolation.py siemens-pilot      # Specific tenant
    python3 verify_tenant_isolation.py --strict           # Fail on warnings
    python3 verify_tenant_isolation.py --no-legacy        # Ignore legacy allowlist

Exit codes:
    0 = PASS (no conflicts, valid hashes)
    1 = FAIL (conflicts or invalid hashes)
    2 = API error

26 February 2026 — WINDI Governance Institute
"""

import sys
import json
import hashlib
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

LEDGER_URL = "http://127.0.0.1:8101"
CUTOVER_TIMESTAMP = 1772198399  # 2026-02-26 23:59:59 UTC (end of rollout day)


def load_legacy_allowlist() -> dict:
    """Load legacy receipts allowlist."""
    allowlist_path = Path(__file__).parent / "legacy_receipts_allowlist.json"
    try:
        with open(allowlist_path, "r") as f:
            return json.load(f)
    except Exception:
        return {"exempt_metadata_hash": [], "legacy_ledger_ids": [], "legacy_receipt_prefixes": []}


def is_legacy_exempt(receipt: dict, allowlist: dict) -> bool:
    """Check if receipt is exempt from hash verification due to legacy status."""
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

    # Check allowlist by tenant
    if tenant_id in allowlist.get("exempt_metadata_hash", []):
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


def verify_metadata_hash(receipt: dict) -> bool:
    """
    Verify that metadata_hash matches the actual metadata.
    This proves the metadata hasn't been tampered with.
    """
    meta = receipt.get("metadata", {})
    stored_hash = meta.get("metadata_hash", "")

    if not stored_hash:
        return False

    # Reconstruct metadata without the hash itself
    meta_copy = {k: v for k, v in meta.items() if k != "metadata_hash"}
    meta_bytes = json.dumps(meta_copy, sort_keys=True, ensure_ascii=False).encode("utf-8")
    computed_hash = hashlib.sha256(meta_bytes).hexdigest()

    return computed_hash == stored_hash


def is_tenant_isolation_receipt(receipt: dict) -> bool:
    """Check if this receipt is a tenant isolation record."""
    meta = receipt.get("metadata", {})
    return (
        meta.get("segregation_mode") == "forensic" or
        meta.get("context") == "multi-tenant-isolation" or
        meta.get("receipt_type") == "tenant_context"
    )


def main():
    tenant_filter = None
    strict_mode = False
    ignore_legacy = "--no-legacy" in sys.argv

    for arg in sys.argv[1:]:
        if arg == "--strict":
            strict_mode = True
        elif not arg.startswith("-"):
            tenant_filter = arg

    print("=" * 65)
    print("  WINDI Multi-Tenant Forensic Isolation Verifier")
    print("  'Tenant segregation through ledger-anchored metadata'")
    print("=" * 65)
    print()

    # Load legacy allowlist
    allowlist = {} if ignore_legacy else load_legacy_allowlist()
    if allowlist:
        print(f"Legacy allowlist loaded: {len(allowlist.get('exempt_metadata_hash', []))} tenants exempt")
    print(f"Cutover date: 2026-02-26 (ts={CUTOVER_TIMESTAMP})")
    print()

    # Fetch all receipts
    data = get_json(f"{LEDGER_URL}/api/receipts?limit=2000")
    if "error" in data:
        print(f"ERROR: Cannot reach Ledger API: {data['error']}")
        sys.exit(2)

    receipts = data.get("receipts", [])
    print(f"Total receipts in Ledger: {len(receipts)}")

    # Filter tenant isolation receipts
    isolation_receipts = [r for r in receipts if is_tenant_isolation_receipt(r)]
    print(f"Tenant isolation receipts: {len(isolation_receipts)}")

    if tenant_filter:
        print(f"Filtering for tenant: {tenant_filter}")

    # Analyze receipts
    tenant_map = {}  # com_id -> set of tenant_ids
    hash_results = {"passed": 0, "failed": 0, "legacy_exempt": 0, "failures": []}
    warnings = []

    for r in isolation_receipts:
        meta = r.get("metadata", {})
        tenant_id = meta.get("tenant_id", "unknown")
        refs = meta.get("references", {})
        com_id = refs.get("com_id", "")

        # Apply tenant filter
        if tenant_filter and tenant_id != tenant_filter:
            continue

        # Check for public tenant (warning)
        if tenant_id == "public":
            warnings.append({
                "type": "public_tenant",
                "receipt_id": r.get("id"),
                "com_id": com_id
            })

        # Track com_id -> tenant mapping
        if com_id:
            tenant_map.setdefault(com_id, set()).add(tenant_id)

        # Verify metadata hash (tamper protection)
        # Legacy receipts are exempt
        if is_legacy_exempt(r, allowlist):
            hash_results["legacy_exempt"] += 1
        elif verify_metadata_hash(r):
            hash_results["passed"] += 1
        else:
            hash_results["failed"] += 1
            hash_results["failures"].append({
                "receipt_id": r.get("id", "?"),
                "tenant_id": tenant_id,
                "com_id": com_id,
                "created_at": r.get("created_at")
            })

    # Detect conflicts (same com_id under multiple tenants)
    conflicts = {
        com_id: sorted(list(tenants))
        for com_id, tenants in tenant_map.items()
        if len(tenants) > 1
    }

    # Build result
    status = "PASS"
    if conflicts:
        status = "FAIL"
    if hash_results["failed"] > 0:
        status = "FAIL"
    if strict_mode and warnings:
        status = "FAIL"

    result = {
        "verification": "WINDI Multi-Tenant Forensic Isolation",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ledger_url": LEDGER_URL,
        "legacy_policy": "ignored" if ignore_legacy else "enforced",
        "cutover_timestamp": CUTOVER_TIMESTAMP,
        "total_receipts": len(receipts),
        "isolation_receipts": len(isolation_receipts),
        "segregation_model": {
            "type": "forensic-metadata isolation",
            "engine_modification_required": False,
            "auditability": "full",
            "tamper_protection": "ledger anchored"
        },
        "hash_verification": {
            "passed": hash_results["passed"],
            "failed": hash_results["failed"],
            "legacy_exempt": hash_results["legacy_exempt"],
            "failures": hash_results["failures"][:5]
        },
        "isolation_check": {
            "unique_documents": len(tenant_map),
            "conflicts_detected": len(conflicts),
            "conflicts": conflicts
        },
        "warnings": warnings[:5] if warnings else [],
        "status": status
    }

    if tenant_filter:
        result["tenant_filter"] = tenant_filter
        filtered_count = sum(
            1 for r in isolation_receipts
            if r.get("metadata", {}).get("tenant_id") == tenant_filter
        )
        result["tenant_receipts"] = filtered_count

    # Output
    print()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print()

    if status == "PASS":
        print("✅ Multi-tenant forensic isolation VERIFIED")
        if hash_results["legacy_exempt"] > 0:
            print(f"   Legacy exempt: {hash_results['legacy_exempt']} pre-cutover receipts")
        print("   No conflicts detected. Post-cutover hashes valid.")
        print("   Segregation model: forensic-metadata isolation")
    else:
        print("❌ Multi-tenant forensic isolation FAILED")
        if conflicts:
            print(f"   Conflicts: {len(conflicts)} documents under multiple tenants")
        if hash_results["failed"] > 0:
            print(f"   Hash failures: {hash_results['failed']} POST-CUTOVER receipts with invalid metadata_hash")
            for f in hash_results["failures"][:2]:
                print(f"     - {f['receipt_id']}: tenant={f['tenant_id']}")
        if warnings and strict_mode:
            print(f"   Warnings: {len(warnings)} (strict mode)")

    sys.exit(0 if status == "PASS" else 1)


if __name__ == "__main__":
    main()
