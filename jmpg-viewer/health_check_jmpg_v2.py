#!/usr/bin/env python3
"""
WINDI JMPG — Health Check v2 (Dual-Hash Aware)
================================================
Queries Forensic Ledger DIRECTLY on :8101 (not via Desktop Gateway).
Validates bundle_hash + content_hash + /api/verify endpoint.

Run:  python3 health_check_jmpg_v2.py
"""

import hashlib
import json
import os
import sys
import tempfile
import time
import zipfile
from datetime import datetime, timezone

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    import urllib.request
    import urllib.error
    HAS_REQUESTS = False

EXPORT_URL = "http://127.0.0.1:8103"
LEDGER_URL = "http://127.0.0.1:8101"  # Direct to Forensic Ledger!
SEP = "=" * 60


def http_get(url, timeout=10):
    try:
        if HAS_REQUESTS:
            r = requests.get(url, timeout=timeout)
            try:
                return r.status_code, r.json()
            except:
                return r.status_code, r.text
        else:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode("utf-8")
                try:
                    return resp.status, json.loads(body)
                except:
                    return resp.status, body
    except Exception as e:
        return 0, str(e)


def http_post(url, data, timeout=30):
    try:
        body = json.dumps(data).encode("utf-8")
        if HAS_REQUESTS:
            r = requests.post(url, json=data, timeout=timeout)
            ct = r.headers.get("content-type", "")
            if "json" in ct:
                return r.status_code, r.json(), None
            return r.status_code, None, r.content
        else:
            req = urllib.request.Request(
                url, data=body,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
                ct = resp.headers.get("content-type", "")
                if "json" in ct:
                    return resp.status, json.loads(raw.decode()), None
                return resp.status, None, raw
    except Exception as e:
        return 0, {"error": str(e)}, None


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(obj) -> str:
    return json.dumps(obj, separators=(",", ":"), sort_keys=True, ensure_ascii=False)


class R:
    """Test result."""
    def __init__(self, name, ok, detail="", critical=True):
        self.name, self.ok, self.detail, self.critical = name, ok, detail, critical

    def __str__(self):
        icon = "✅" if self.ok else ("❌" if self.critical else "⚠️")
        d = f"  → {self.detail}" if self.detail else ""
        return f"  {icon} {self.name}{d}"


def main():
    print(f"""
{SEP}
  🐉 WINDI JMPG — VISTO DE QUALIDADE v2
  Linhagem de Ferro (Dual-Hash Aware)
{SEP}
  Export Engine: {EXPORT_URL}
  Forensic Ledger: {LEDGER_URL} (DIRECT)
  Timestamp: {datetime.now(timezone.utc).isoformat()}
{SEP}
""")

    results = []

    # ── Phase 1: Health ──
    print("📡 Phase 1: Service Health")

    for name, url in [
        ("Export Engine (:8103)", EXPORT_URL),
        ("Forensic Ledger (:8101)", LEDGER_URL),
    ]:
        s, d = http_get(f"{url}/health")
        if s == 200 and isinstance(d, dict):
            v = d.get("version", "?")
            svc = d.get("service", "OK")
            r = R(f"{name}", True, f"{svc} v{v}")
        else:
            r = R(f"{name}", False, f"HTTP {s}")
        results.append(r)
        print(r)

    # Sentinel LAW
    s, d = http_get("http://127.0.0.1:8102/health")
    if s == 200 and isinstance(d, dict):
        r = R("Sentinel LAW (:8102)", d.get("all_laws_pass", False),
              f"Cycle #{d.get('cycle_id','?')}, alerts={d.get('active_alerts','?')}")
    else:
        r = R("Sentinel LAW (:8102)", False, "Unreachable", critical=False)
    results.append(r)
    print(r)

    # Abort if critical down
    if any(not r.ok and r.critical for r in results):
        print("\n❌ Critical services down.")
        sys.exit(2)

    # ── Phase 2: /api/verify endpoint ──
    print(f"\n🔍 Phase 2: Verify Endpoint")

    s, d = http_get(f"{LEDGER_URL}/api/verify/NONEXISTENT-TEST")
    if s == 404 and isinstance(d, dict) and d.get("error") == "not_found":
        r = R("/api/verify returns 404 for unknown", True, "Correct behavior")
    elif s == 404:
        r = R("/api/verify endpoint", False, "Endpoint not found — patch not applied", critical=False)
    else:
        r = R("/api/verify endpoint", False, f"Unexpected HTTP {s}", critical=False)
    results.append(r)
    print(r)

    # ── Phase 3: seal-bundle endpoint ──
    s2, d2 = http_get(f"{LEDGER_URL}/health")  # just to confirm it's up
    s3, d3, _ = http_post(
        f"{LEDGER_URL}/api/receipts/NONEXISTENT-TEST/seal-bundle",
        {"bundle_hash": "test", "bundle_size": 0}
    )
    if s3 == 404:
        r = R("seal-bundle returns 404 for unknown", True, "Correct behavior")
    elif s3 == 0:
        r = R("seal-bundle endpoint", False, "Not responding — patch not applied", critical=False)
    else:
        r = R("seal-bundle endpoint", True, f"HTTP {s3}")
    results.append(r)
    print(r)

    # ── Phase 4: Full pipeline ──
    print(f"\n📦 Phase 3: Full Export Pipeline")

    blocks = [
        {"type": "heading", "content": "Dual-Hash Health Check", "level": 1},
        {"type": "paragraph", "content": f"Test at {datetime.now(timezone.utc).isoformat()}"},
    ]

    print("  📦 Exporting test .jmpg...")
    s, json_r, raw = http_post(f"{EXPORT_URL}/api/export/jmpg", {
        "template": "comunicado",
        "title": "Dual-Hash Health Check",
        "language": "de",
        "author": "health-check-v2",
        "content_blocks": blocks,
    })

    if s != 200 or raw is None:
        results.append(R("Export .jmpg", False, f"HTTP {s}: {json_r}"))
        _summary(results)
        return

    results.append(R("Export .jmpg", True, f"{len(raw)} bytes"))

    # Bundle hash
    local_bundle_hash = sha256(raw)
    results.append(R("Bundle hash", True, f"{local_bundle_hash[:20]}..."))

    # Extract
    tmp = tempfile.NamedTemporaryFile(suffix=".jmpg", delete=False)
    tmp.write(raw)
    tmp.close()

    try:
        with zipfile.ZipFile(tmp.name, "r") as zf:
            manifest = json.loads(zf.read("manifest.json"))
            content = json.loads(zf.read("content.json"))
            receipt = json.loads(zf.read("receipt.json"))

        receipt_id = manifest.get("governance", {}).get("receipt_id") or manifest.get("package_id")
        results.append(R("Receipt ID", bool(receipt_id), receipt_id or "MISSING"))

        # Content hash verification
        local_content_hash = sha256(canonical_json(content.get("blocks", [])).encode("utf-8"))
        manifest_ch = manifest.get("content_hash")
        ch_match = local_content_hash == manifest_ch
        results.append(R("Content hash (recalc vs manifest)", ch_match,
                        f"{local_content_hash[:16]}... {'==' if ch_match else '!='} {(manifest_ch or '?')[:16]}..."))

        # ── Check Forensic Ledger for receipt ──
        print(f"\n  🔍 Checking Ledger for: {receipt_id}")

        # Direct lookup on :8101
        s, d = http_get(f"{LEDGER_URL}/api/receipts/{receipt_id}")
        if s == 200 and isinstance(d, dict) and d.get("ok"):
            ledger_receipt = d.get("receipt", {})
            results.append(R("Receipt in Forensic Ledger", True,
                            f"Found! governance={ledger_receipt.get('governance_level')}"))

            # Check content_hash match
            ledger_ch = ledger_receipt.get("content_hash", "")
            ch_ledger_match = local_content_hash == ledger_ch
            results.append(R("Content hash (local vs Ledger)", ch_ledger_match,
                            f"{local_content_hash[:16]}... {'==' if ch_ledger_match else '!='} {ledger_ch[:16]}..."))

            # Check bundle_hash
            ledger_bh = ledger_receipt.get("bundle_hash")
            if ledger_bh:
                bh_match = local_bundle_hash == ledger_bh
                results.append(R("Bundle hash (local vs Ledger)", bh_match,
                                f"{local_bundle_hash[:16]}... {'==' if bh_match else '!='} {ledger_bh[:16]}..."))

                # Check size
                ledger_size = ledger_receipt.get("bundle_size")
                if ledger_size:
                    size_match = len(raw) == ledger_size
                    results.append(R("Bundle size match", size_match,
                                    f"local={len(raw)} ledger={ledger_size}"))
            else:
                results.append(R("Bundle hash in Ledger", False,
                                "NULL — Export Engine patch not yet sending bundle_hash",
                                critical=False))
        else:
            results.append(R("Receipt in Forensic Ledger", False,
                            f"HTTP {s}: {d}"))

        # ── /api/verify test ──
        s, d = http_get(f"{LEDGER_URL}/api/verify/{receipt_id}")
        if s == 200 and isinstance(d, dict) and d.get("ok"):
            results.append(R("/api/verify for real receipt", True,
                            f"content_hash={d.get('content_hash','?')[:12]}... bundle_hash={'present' if d.get('bundle_hash') else 'null'}"))
        elif s == 404 and "not_found" in str(d):
            # Endpoint exists but receipt not found (might be in different format)
            results.append(R("/api/verify", False,
                            f"Receipt not found via verify (check ID format)", critical=False))
        else:
            results.append(R("/api/verify", False,
                            f"HTTP {s}", critical=False))

        # Determinism test
        print("\n  🔬 Determinism test...")
        _, _, raw2 = http_post(f"{EXPORT_URL}/api/export/jmpg", {
            "template": "comunicado", "title": "Dual-Hash Health Check",
            "language": "de", "author": "health-check-v2", "content_blocks": blocks,
        })
        if raw2:
            with zipfile.ZipFile(tempfile.NamedTemporaryFile(suffix=".jmpg").name, "w"):
                pass
            tmp2 = tempfile.NamedTemporaryFile(suffix=".jmpg", delete=False)
            tmp2.write(raw2)
            tmp2.close()
            with zipfile.ZipFile(tmp2.name) as zf2:
                c2 = json.loads(zf2.read("content.json"))
            ch2 = sha256(canonical_json(c2.get("blocks", [])).encode("utf-8"))
            results.append(R("Content hash determinism", local_content_hash == ch2))
            bh2 = sha256(raw2)
            results.append(R("Bundle hash determinism",
                            local_bundle_hash == bh2,
                            "IDENTICAL" if local_bundle_hash == bh2 else "DIFFERS (timestamps)",
                            critical=False))
            os.unlink(tmp2.name)

    finally:
        os.unlink(tmp.name)

    _summary(results)


def _summary(results):
    total = len(results)
    passed = sum(1 for r in results if r.ok)
    crit_fail = [r for r in results if not r.ok and r.critical]
    warnings = [r for r in results if not r.ok and not r.critical]

    print(f"\n{SEP}")
    print("  📊 SUMMARY")
    print(SEP)
    print(f"\n  Total:    {total}")
    print(f"  Passed:   {passed} ✅")
    print(f"  Critical: {len(crit_fail)} ❌")
    print(f"  Warnings: {len(warnings)} ⚠️")

    if crit_fail:
        print(f"\n  ❌ CRITICAL:")
        for r in crit_fail:
            print(f"     • {r.name}: {r.detail}")
    if warnings:
        print(f"\n  ⚠️  WARNINGS:")
        for r in warnings:
            print(f"     • {r.name}: {r.detail}")

    print(f"\n{SEP}")
    if not crit_fail and not warnings:
        print("  🟢 LINHAGEM DE FERRO: INTACTA")
        print("  Dual-hash verified. Pipeline sealed.")
    elif not crit_fail:
        print("  🟡 LINHAGEM DE FERRO: PARCIAL")
        print("  Core OK. Pending patches noted above.")
    else:
        print("  🔴 LINHAGEM DE FERRO: QUEBRADA")
        print("  Critical failures. Apply patches and re-run.")
    print(SEP)
    print(f"\n  \"AI processes. Human decides. WINDI guarantees.\"")

    sys.exit(1 if crit_fail else 0)


if __name__ == "__main__":
    main()
