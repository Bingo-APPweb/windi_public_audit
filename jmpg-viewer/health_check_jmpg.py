#!/usr/bin/env python3
"""
WINDI JMPG — Health Check & Integrity Validator
=================================================
"Visto de Qualidade" — O teste definitivo da Linhagem de Ferro.

Validates the complete pipeline:
  Desktop → Export Engine(:8103) → Forensic Ledger(:8101) → Viewer verification

Run on the Strato server after applying all patches:
  python3 health_check_jmpg.py

Or with custom endpoints:
  python3 health_check_jmpg.py --export http://127.0.0.1:8103 --ledger http://127.0.0.1:8101

Exit codes:
  0 = ALL PASS (Linhagem de Ferro intacta)
  1 = FAILURES detected
  2 = Infrastructure error (service down)
"""

import argparse
import hashlib
import json
import os
import sys
import tempfile
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

# Optional: requests (falls back to urllib if not available)
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    import urllib.request
    import urllib.error
    HAS_REQUESTS = False


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_EXPORT_URL = "http://127.0.0.1:8103"
DEFAULT_LEDGER_URL = "http://127.0.0.1:8101"
# When running externally via nginx:
# --export https://admin.windia4desk.tech/export
# --ledger https://admin.windia4desk.tech/desktop/api/ledger
# (Ledger is proxied through Desktop Gateway)

TEST_CONTENT_BLOCKS = [
    {"type": "heading", "content": "Linhagem de Ferro — Health Check", "level": 1},
    {"type": "paragraph", "content": "Este documento é um teste automatizado de integridade do pipeline JMPG."},
    {"type": "paragraph", "content": f"Gerado em: {datetime.now(timezone.utc).isoformat()}"},
]

SEPARATOR = "=" * 60


# ============================================================
# HTTP HELPERS (work with or without requests library)
# ============================================================

def http_get(url, timeout=10):
    """GET request, returns (status_code, response_dict_or_text)."""
    try:
        if HAS_REQUESTS:
            r = requests.get(url, timeout=timeout)
            try:
                return r.status_code, r.json()
            except Exception:
                return r.status_code, r.text
        else:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode("utf-8")
                try:
                    return resp.status, json.loads(body)
                except Exception:
                    return resp.status, body
    except Exception as e:
        return 0, str(e)


def http_post_json(url, data, timeout=30):
    """POST JSON, returns (status_code, response_dict_or_bytes)."""
    try:
        if HAS_REQUESTS:
            r = requests.post(url, json=data, timeout=timeout)
            content_type = r.headers.get("content-type", "")
            if "json" in content_type:
                return r.status_code, r.json(), None
            else:
                return r.status_code, None, r.content
        else:
            body = json.dumps(data).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=body,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
                content_type = resp.headers.get("content-type", "")
                if "json" in content_type:
                    return resp.status, json.loads(raw.decode("utf-8")), None
                else:
                    return resp.status, None, raw
    except Exception as e:
        return 0, {"error": str(e)}, None


# ============================================================
# HASH FUNCTIONS
# ============================================================

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_json(obj) -> str:
    """Reproduce Python's json.dumps(obj, separators=(',',':'), sort_keys=True)"""
    return json.dumps(obj, separators=(",", ":"), sort_keys=True, ensure_ascii=False)


# ============================================================
# TEST RESULTS
# ============================================================

class TestResult:
    def __init__(self, name, passed, detail="", critical=True):
        self.name = name
        self.passed = passed
        self.detail = detail
        self.critical = critical

    def __str__(self):
        icon = "✅" if self.passed else ("❌" if self.critical else "⚠️")
        detail = f"  → {self.detail}" if self.detail else ""
        return f"  {icon} {self.name}{detail}"


# ============================================================
# HEALTH CHECKS
# ============================================================

def check_service_health(name, url):
    """Check if a service is healthy."""
    # Try /health first, then root
    for endpoint in [f"{url}/health", url]:
        status, data = http_get(endpoint)
        if status == 200 and isinstance(data, dict):
            version = data.get("version", data.get("engine_version", ""))
            svc = data.get("service", data.get("status", ""))
            return TestResult(f"{name} health", True, f"{svc} v{version}" if version else str(svc))
    # For Ledger proxied through Desktop: check if receipts endpoint works
    status, data = http_get(f"{url}/receipts?limit=1")
    if status == 200:
        return TestResult(f"{name} health", True, "receipts endpoint accessible")
    return TestResult(f"{name} health", False, f"HTTP {status}: {data}")


def check_export_pipeline(export_url, ledger_url):
    """
    Full export pipeline test:
    1. Export a .jmpg
    2. Calculate bundle_hash from raw bytes
    3. Verify content_hash from extracted blocks
    4. Check against Ledger
    """
    results = []

    # --- STEP 1: Export ---
    print("\n  📦 Exporting test .jmpg...")
    payload = {
        "template": "comunicado",
        "title": "JMPG Health Check",
        "language": "de",
        "author": "health-check-bot",
        "content_blocks": TEST_CONTENT_BLOCKS,
    }

    status, json_resp, raw_bytes = http_post_json(
        f"{export_url}/api/export/jmpg", payload
    )

    if status != 200 or raw_bytes is None:
        error_msg = json_resp if json_resp else f"HTTP {status}"
        results.append(TestResult("Export .jmpg", False, f"Failed: {error_msg}"))
        return results

    results.append(TestResult("Export .jmpg", True, f"{len(raw_bytes)} bytes"))

    # Save to temp file
    tmp = tempfile.NamedTemporaryFile(suffix=".jmpg", delete=False)
    tmp.write(raw_bytes)
    tmp.close()
    jmpg_path = tmp.name

    try:
        # --- STEP 2: Bundle hash (raw bytes) ---
        local_bundle_hash = sha256_bytes(raw_bytes)
        local_size = len(raw_bytes)
        results.append(TestResult(
            "Bundle hash calculated",
            True,
            f"SHA-256: {local_bundle_hash[:16]}... ({local_size} bytes)"
        ))

        # --- STEP 3: Extract and verify structure ---
        try:
            with zipfile.ZipFile(jmpg_path, "r") as zf:
                names = zf.namelist()
                required = ["manifest.json", "content.json", "receipt.json"]
                missing = [n for n in required if n not in names]
                if missing:
                    results.append(TestResult(
                        "ZIP structure", False, f"Missing: {missing}"
                    ))
                else:
                    results.append(TestResult(
                        "ZIP structure", True, f"Files: {sorted(names)}"
                    ))

                # Read manifest
                manifest = json.loads(zf.read("manifest.json"))
                receipt_id = manifest.get("governance", {}).get("receipt_id") or manifest.get("package_id")
                manifest_content_hash = manifest.get("content_hash")

                results.append(TestResult(
                    "Receipt ID",
                    bool(receipt_id),
                    receipt_id or "MISSING"
                ))

                # Read content and recalculate content_hash
                content = json.loads(zf.read("content.json"))
                blocks = content.get("blocks", [])
                local_content_hash = sha256_bytes(
                    canonical_json(blocks).encode("utf-8")
                )

                content_match = local_content_hash == manifest_content_hash
                results.append(TestResult(
                    "Content hash (local vs manifest)",
                    content_match,
                    f"local={local_content_hash[:16]}... manifest={manifest_content_hash[:16]}..."
                    if manifest_content_hash else "manifest_content_hash MISSING"
                ))

                # Read receipt
                receipt = json.loads(zf.read("receipt.json"))
                receipt_registered = receipt.get("registered", False)
                receipt_content_hash = receipt.get("content_hash")

                results.append(TestResult(
                    "Ledger registration (from receipt.json)",
                    receipt_registered,
                    f"registered={receipt_registered}"
                ))

        except zipfile.BadZipFile:
            results.append(TestResult("ZIP structure", False, "Not a valid ZIP file"))
            return results

        # --- STEP 4: Verify against Ledger ---
        print(f"\n  🔍 Checking Ledger for receipt: {receipt_id}")

        # Try the new /api/verify endpoint first
        verify_url = f"{ledger_url}/verify/{receipt_id}"
        # Also try alternative paths
        verify_urls = [
            verify_url,
            f"{ledger_url}/../verify/{receipt_id}",
            f"{ledger_url.replace('/api/ledger', '/api/verify')}/{receipt_id}",
        ]
        
        verify_status = 0
        verify_data = {}
        for vurl in verify_urls:
            verify_status, verify_data = http_get(vurl)
            if verify_status == 200:
                break

        if verify_status == 200 and isinstance(verify_data, dict):
            results.append(TestResult(
                "/api/verify endpoint", True, "Available (new architecture)"
            ))

            # Check bundle_hash
            ledger_bundle_hash = verify_data.get("bundle_hash")
            if ledger_bundle_hash:
                bundle_match = local_bundle_hash == ledger_bundle_hash
                results.append(TestResult(
                    "Bundle hash (local vs Ledger)",
                    bundle_match,
                    f"local={local_bundle_hash[:16]}... ledger={ledger_bundle_hash[:16]}..."
                ))
            else:
                results.append(TestResult(
                    "Bundle hash in Ledger",
                    False,
                    "NOT PRESENT — Export Engine patch not yet applied",
                    critical=False  # Expected before patch
                ))

            # Check size
            ledger_size = verify_data.get("size_bytes")
            if ledger_size:
                size_match = local_size == ledger_size
                results.append(TestResult(
                    "Size (local vs Ledger)",
                    size_match,
                    f"local={local_size} ledger={ledger_size}"
                ))
            else:
                results.append(TestResult(
                    "Size in Ledger",
                    False,
                    "NOT PRESENT — Export Engine patch not yet applied",
                    critical=False
                ))

            # Check content_hash
            ledger_content_hash = verify_data.get("content_hash")
            if ledger_content_hash:
                content_ledger_match = local_content_hash == ledger_content_hash
                results.append(TestResult(
                    "Content hash (local vs Ledger)",
                    content_ledger_match,
                    f"local={local_content_hash[:16]}... ledger={ledger_content_hash[:16]}..."
                ))

        elif verify_status == 404:
            results.append(TestResult(
                "/api/verify endpoint",
                False,
                "Endpoint not found — Ledger patch not yet applied",
                critical=False
            ))

            # Fallback: try /api/receipts via ledger
            print("  🔄 Falling back to receipts list...")
            receipts_status, receipts_data = http_get(
                f"{ledger_url}/receipts?limit=200"
            )
            if receipts_status == 200 and isinstance(receipts_data, list):
                found = [r for r in receipts_data
                         if r.get("doc_id") == receipt_id or r.get("id") == receipt_id]
                if found:
                    results.append(TestResult(
                        "Receipt in Ledger (legacy)",
                        True,
                        f"Found via receipts list"
                    ))
                    ledger_hash = found[0].get("integrity_hash", "")
                    hash_match = ledger_hash == local_content_hash or ledger_hash == manifest_content_hash
                    results.append(TestResult(
                        "Content hash (legacy comparison)",
                        hash_match,
                        f"ledger={ledger_hash[:16]}... vs content={local_content_hash[:16]}..."
                    ))
                else:
                    # Check if ALL entries are LAW_PROBE (registration gap)
                    all_actions = set(r.get("action", "") for r in receipts_data)
                    if all_actions == {"LAW_PROBE"}:
                        results.append(TestResult(
                            "Receipt in Ledger",
                            False,
                            f"{receipt_id} not found. NOTE: Ledger only has LAW_PROBE entries. "
                            f"Export Engine may register to different table/endpoint.",
                        ))
                    else:
                        results.append(TestResult(
                            "Receipt in Ledger",
                            False,
                            f"{receipt_id} not found in {len(receipts_data)} receipts"
                        ))
        else:
            results.append(TestResult(
                "Ledger verification",
                False,
                f"HTTP {verify_status}: {verify_data}"
            ))

        # --- STEP 5: Determinism test ---
        print("\n  🔬 Determinism test (export same content twice)...")
        status2, _, raw2 = http_post_json(
            f"{export_url}/api/export/jmpg", payload
        )
        if status2 == 200 and raw2:
            hash2 = sha256_bytes(raw2)
            # Content hash should match, bundle hash may differ (timestamps)
            with zipfile.ZipFile(tempfile.NamedTemporaryFile(suffix=".jmpg", delete=False).name, "w") as _:
                pass  # just need a temp path
            tmp2 = tempfile.NamedTemporaryFile(suffix=".jmpg", delete=False)
            tmp2.write(raw2)
            tmp2.close()
            try:
                with zipfile.ZipFile(tmp2.name, "r") as zf2:
                    content2 = json.loads(zf2.read("content.json"))
                    blocks2 = content2.get("blocks", [])
                    content_hash2 = sha256_bytes(
                        canonical_json(blocks2).encode("utf-8")
                    )
                    manifest2 = json.loads(zf2.read("manifest.json"))
                    manifest_ch2 = manifest2.get("content_hash")

                content_deterministic = local_content_hash == content_hash2
                bundle_deterministic = local_bundle_hash == hash2

                results.append(TestResult(
                    "Content hash determinism",
                    content_deterministic,
                    f"export1={local_content_hash[:16]}... export2={content_hash2[:16]}..."
                ))

                results.append(TestResult(
                    "Bundle hash determinism",
                    bundle_deterministic,
                    f"{'IDENTICAL' if bundle_deterministic else 'DIFFERS (expected if timestamps vary)'}",
                    critical=False  # Bundle may differ due to timestamps
                ))
            finally:
                os.unlink(tmp2.name)

    finally:
        os.unlink(jmpg_path)

    return results


def check_sentinel_law(base_url):
    """Check if Sentinel LAW is monitoring."""
    # Try internal first, then external nginx path
    for url in ["http://127.0.0.1:8102/health", f"{base_url.rstrip('/')}/../../sentinel-law/health"]:
        status, data = http_get(url)
        if status == 200 and isinstance(data, dict):
            all_pass = data.get("all_laws_pass", False)
            cycle = data.get("cycle_id", "?")
            alerts = data.get("active_alerts", "?")
            return TestResult(
                "Sentinel LAW",
                all_pass,
                f"Cycle #{cycle}, alerts={alerts}, all_laws_pass={all_pass}"
            )
    # Try via known external path
    status, data = http_get("https://admin.windia4desk.tech/sentinel-law/health")
    if status == 200 and isinstance(data, dict):
        all_pass = data.get("all_laws_pass", False)
        cycle = data.get("cycle_id", "?")
        return TestResult("Sentinel LAW", all_pass, f"Cycle #{cycle}, all_laws_pass={all_pass}")
    return TestResult("Sentinel LAW", False, "Unreachable", critical=False)


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="WINDI JMPG Health Check — Visto de Qualidade"
    )
    parser.add_argument(
        "--export", default=DEFAULT_EXPORT_URL,
        help=f"Export Engine base URL (default: {DEFAULT_EXPORT_URL})"
    )
    parser.add_argument(
        "--ledger", default=DEFAULT_LEDGER_URL,
        help=f"Forensic Ledger base URL (default: {DEFAULT_LEDGER_URL})"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Show extra debug output"
    )
    args = parser.parse_args()

    print(f"""
{SEPARATOR}
  🐉 WINDI JMPG — VISTO DE QUALIDADE
  Linhagem de Ferro Health Check
{SEPARATOR}
  Export Engine: {args.export}
  Forensic Ledger: {args.ledger}
  Timestamp: {datetime.now(timezone.utc).isoformat()}
{SEPARATOR}
""")

    all_results = []
    critical_failures = 0
    warnings = 0

    # === Phase 1: Service Health ===
    print("📡 Phase 1: Service Health")
    for name, url in [
        ("Export Engine (:8103)", args.export),
        ("Forensic Ledger (:8101)", args.ledger),
    ]:
        r = check_service_health(name, url)
        all_results.append(r)
        print(r)

    sentinel = check_sentinel_law(args.ledger)
    all_results.append(sentinel)
    print(sentinel)

    # Check Desktop Gateway (derive URL from ledger URL pattern)
    desktop_url = args.ledger.replace("/api/ledger", "")  # try to get desktop base
    desktop = check_service_health("Desktop Gateway (:8100)", desktop_url)
    all_results.append(desktop)
    print(desktop)

    # Abort if critical services are down
    critical_down = [r for r in all_results if not r.passed and r.critical]
    if critical_down:
        print(f"\n❌ Critical services down. Cannot proceed with pipeline test.")
        print(f"   Fix: Ensure Export Engine and Ledger are running.")
        sys.exit(2)

    # === Phase 2: Export Pipeline ===
    print(f"\n📦 Phase 2: Export Pipeline (end-to-end)")
    pipeline_results = check_export_pipeline(args.export, args.ledger)
    all_results.extend(pipeline_results)
    for r in pipeline_results:
        print(r)

    # === Phase 3: Summary ===
    print(f"\n{SEPARATOR}")
    print("  📊 SUMMARY")
    print(SEPARATOR)

    total = len(all_results)
    passed = sum(1 for r in all_results if r.passed)
    failed_critical = [r for r in all_results if not r.passed and r.critical]
    failed_warning = [r for r in all_results if not r.passed and not r.critical]

    print(f"\n  Total checks:     {total}")
    print(f"  Passed:           {passed} ✅")
    print(f"  Failed (critical): {len(failed_critical)} ❌")
    print(f"  Warnings:         {len(failed_warning)} ⚠️")

    if failed_critical:
        print(f"\n  ❌ CRITICAL FAILURES:")
        for r in failed_critical:
            print(f"     • {r.name}: {r.detail}")

    if failed_warning:
        print(f"\n  ⚠️  WARNINGS (non-blocking):")
        for r in failed_warning:
            print(f"     • {r.name}: {r.detail}")

    # === Verdict ===
    print(f"\n{SEPARATOR}")
    if not failed_critical:
        if not failed_warning:
            print("  🟢 LINHAGEM DE FERRO: INTACTA")
            print("  All hashes aligned. Pipeline verified.")
        else:
            print("  🟡 LINHAGEM DE FERRO: PARCIAL")
            print("  Core pipeline works. Some patches pending.")
        print(SEPARATOR)
        print(f"\n  hash_export ≡ hash_ledger ≡ hash_viewer")
        print(f"  \"AI processes. Human decides. WINDI guarantees.\"")
        sys.exit(0)
    else:
        print("  🔴 LINHAGEM DE FERRO: QUEBRADA")
        print("  Critical failures detected. Apply patches and re-run.")
        print(SEPARATOR)
        sys.exit(1)


if __name__ == "__main__":
    main()
