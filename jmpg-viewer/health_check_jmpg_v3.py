#!/usr/bin/env python3
"""
🐉 WINDI JMPG — VISTO DE QUALIDADE v3.1
Linhagem de Ferro (Dual-Hash + Determinism-Aware)

v3.1 — Corrected for actual Export Engine API:
  - Export returns binary ZIP (.jmpg), not JSON
  - receipt.json is INSIDE the .jmpg ZIP
  - bundle_hash = SHA-256 of the entire .jmpg file
  - bundle_hash sealed in Ledger post-ZIP
  - Determinism variance (timestamps) = INFO, not WARNING

"AI processes. Human decides. WINDI guarantees."
"""

import json
import hashlib
import os
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# ── Config ──────────────────────────────────────────────────
EXPORT_ENGINE = os.getenv("EXPORT_URL", "http://127.0.0.1:8103")
LEDGER_URL    = os.getenv("LEDGER_URL", "http://127.0.0.1:8101")
SENTINEL_URL  = os.getenv("SENTINEL_URL", "http://127.0.0.1:8102")
TIMEOUT       = 10

# ── Helpers ─────────────────────────────────────────────────
class CheckResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.infos = 0
        self.warn_msgs = []
        self.fail_msgs = []
        self.info_msgs = []

    def ok(self, msg):
        self.passed += 1
        print(f"  ✅ {msg}")

    def fail(self, msg):
        self.failed += 1
        self.fail_msgs.append(msg)
        print(f"  ❌ {msg}")

    def warn(self, msg):
        self.warnings += 1
        self.warn_msgs.append(msg)
        print(f"  ⚠️  {msg}")

    def info(self, msg):
        self.infos += 1
        self.info_msgs.append(msg)
        print(f"  ℹ️  {msg}")

    @property
    def total(self):
        return self.passed + self.failed + self.warnings + self.infos


def http_get_json(url, timeout=TIMEOUT):
    """HTTP GET -> (status_code, parsed_json_or_None, raw_body)."""
    try:
        req = Request(url, method="GET")
        with urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            try:
                return resp.status, json.loads(body), body
            except json.JSONDecodeError:
                return resp.status, None, body
    except HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        try:
            return e.code, json.loads(body), body
        except Exception:
            return e.code, None, body
    except Exception as e:
        return 0, None, str(e)


def http_post_binary(url, json_body, timeout=TIMEOUT):
    """HTTP POST JSON -> (status_code, raw_bytes, headers_dict)."""
    try:
        payload = json.dumps(json_body).encode("utf-8")
        req = Request(url, data=payload, method="POST")
        req.add_header("Content-Type", "application/json")
        with urlopen(req, timeout=timeout) as resp:
            headers = {k.lower(): v for k, v in resp.getheaders()}
            return resp.status, resp.read(), headers
    except HTTPError as e:
        body = e.read() if e.fp else b""
        return e.code, body, {}
    except Exception as e:
        return 0, str(e).encode(), {}


def http_post_json(url, json_body, timeout=TIMEOUT):
    """HTTP POST JSON -> (status_code, parsed_json_or_None)."""
    try:
        payload = json.dumps(json_body).encode("utf-8")
        req = Request(url, data=payload, method="POST")
        req.add_header("Content-Type", "application/json")
        with urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            try:
                return resp.status, json.loads(body)
            except json.JSONDecodeError:
                return resp.status, None
    except HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, None
    except Exception as e:
        return 0, None


def sha256_bytes(data):
    """SHA-256 of raw bytes."""
    return hashlib.sha256(data).hexdigest()


# ── Phases ──────────────────────────────────────────────────

def phase1_service_health(r):
    """Phase 1: Service Health — are all 3 services alive?"""
    print("\n📡 Phase 1: Service Health")

    # Export Engine
    code, data, _ = http_get_json(f"{EXPORT_ENGINE}/health")
    if code == 200 and data:
        name = data.get("service", "?")
        ver = data.get("version", "?")
        r.ok(f"Export Engine (:8103)  -> {name} v{ver}")
    elif code == 200:
        r.ok("Export Engine (:8103)  -> UP")
    else:
        r.fail(f"Export Engine (:8103)  -> DOWN (HTTP {code})")

    # Forensic Ledger
    code, data, _ = http_get_json(f"{LEDGER_URL}/health")
    if code == 200 and data:
        name = data.get("service", "?")
        ver = data.get("version", "?")
        r.ok(f"Forensic Ledger (:8101)  -> {name} v{ver}")
    elif code == 200:
        r.ok("Forensic Ledger (:8101)  -> UP")
    else:
        r.fail(f"Forensic Ledger (:8101)  -> DOWN (HTTP {code})")

    # Sentinel LAW
    code, data, _ = http_get_json(f"{SENTINEL_URL}/health")
    if code == 200 and data:
        cycle = data.get("cycle", "?")
        alerts = data.get("alerts", "?")
        r.ok(f"Sentinel LAW (:8102)  -> Cycle #{cycle}, alerts={alerts}")
    elif code == 200:
        r.ok("Sentinel LAW (:8102)  -> UP")
    else:
        r.fail(f"Sentinel LAW (:8102)  -> DOWN (HTTP {code})")


def phase2_verify_endpoints(r):
    """Phase 2: Verify dual-hash endpoints respond correctly."""
    print("\n🔍 Phase 2: Verify Endpoints")

    # /api/verify/<unknown> should return 404
    code, _, _ = http_get_json(f"{LEDGER_URL}/api/verify/NONEXISTENT-ID-12345")
    if code == 404:
        r.ok("/api/verify returns 404 for unknown  -> Correct")
    else:
        r.fail(f"/api/verify returned HTTP {code} for unknown")

    # /api/receipts/<unknown>/seal-bundle should return 404
    code, _ = http_post_json(
        f"{LEDGER_URL}/api/receipts/NONEXISTENT-ID-12345/seal-bundle",
        {"bundle_hash": "test", "bundle_size": 0}
    )
    if code == 404:
        r.ok("seal-bundle returns 404 for unknown  -> Correct")
    else:
        r.fail(f"seal-bundle returned HTTP {code} for unknown")


def export_jmpg(label="test"):
    """
    Export a .jmpg via the Export Engine.
    Returns: (jmpg_bytes, receipt_json, content_hash, error_string)
    The Export Engine returns a binary ZIP — receipt.json is inside it.
    """
    payload = {
        "content_blocks": [
            {
                "type": "paragraph",
                "text": f"WINDI Health Check v3.1 [{label}] {datetime.now(timezone.utc).isoformat()}"
            }
        ],
        "metadata": {
            "title": "Health Check v3.1",
            "author": "WINDI Sentinel",
            "doc_type": "APPROVAL",
            "impact_level": "LOW"
        }
    }

    code, raw_bytes, headers = http_post_binary(
        f"{EXPORT_ENGINE}/api/export/jmpg", payload
    )

    if code != 200:
        err_msg = raw_bytes.decode("utf-8", errors="replace")[:200]
        return None, None, None, f"HTTP {code}: {err_msg}"

    # Write to temp file to validate as ZIP
    try:
        with tempfile.NamedTemporaryFile(suffix=".jmpg", delete=False) as tmp:
            tmp.write(raw_bytes)
            tmp_path = tmp.name

        if not zipfile.is_zipfile(tmp_path):
            os.unlink(tmp_path)
            return None, None, None, "Response is not a valid ZIP file"

        with zipfile.ZipFile(tmp_path, "r") as z:
            receipt_json = json.loads(z.read("receipt.json"))
            manifest_json = json.loads(z.read("manifest.json"))

        content_hash = (
            receipt_json.get("content_hash")
            or manifest_json.get("content_hash", "")
        )
        os.unlink(tmp_path)
        return raw_bytes, receipt_json, content_hash, None

    except Exception as e:
        return None, None, None, f"Parse error: {e}"


def phase3_full_pipeline(r):
    """Phase 3: Full Export Pipeline — export, hash, verify against Ledger."""
    print("\n📦 Phase 3: Full Export Pipeline")

    # ── Step 1: Export ──────────────────────────────────────
    print("  📦 Exporting test .jmpg...")
    jmpg_bytes, receipt, content_hash, err = export_jmpg("primary")

    if err:
        r.fail(f"Export failed: {err}")
        return

    receipt_id = receipt.get("receipt_id", "")
    registered = receipt.get("registered", False)

    if receipt_id and registered:
        r.ok(f"Export created: {receipt_id}")
    elif receipt_id:
        r.warn(f"Export created but not registered: {receipt_id}")
    else:
        r.fail("Export response missing receipt_id")
        return

    # ── Step 2: Compute bundle hash (SHA-256 of entire .jmpg) ──
    bundle_hash_local = sha256_bytes(jmpg_bytes)
    bundle_size_local = len(jmpg_bytes)
    r.ok(f"Bundle hash (local): {bundle_hash_local[:20]}... ({bundle_size_local} bytes)")

    if content_hash:
        r.ok(f"Content hash: {content_hash[:20]}...")
    else:
        r.warn("Content hash not found in receipt")

    # ── Step 3: Verify against Ledger ───────────────────────
    print(f"  🔍 Checking Ledger for: {receipt_id}")
    code, data, _ = http_get_json(f"{LEDGER_URL}/api/receipts/{receipt_id}")

    if code != 200 or not data:
        r.fail(f"Ledger lookup failed for {receipt_id} (HTTP {code})")
        return

    ledger_receipt = data.get("receipt", data)
    ledger_content_hash = ledger_receipt.get("content_hash", "")
    ledger_bundle_hash = ledger_receipt.get("bundle_hash", "")
    ledger_bundle_size = ledger_receipt.get("bundle_size", 0)
    ledger_status = ledger_receipt.get("status", "")

    # Content hash: Export vs Ledger
    if ledger_content_hash and content_hash:
        if ledger_content_hash == content_hash:
            r.ok("Content hash (Export == Ledger)  MATCH")
        else:
            r.fail(
                f"Content hash MISMATCH: "
                f"export={content_hash[:16]}... vs ledger={ledger_content_hash[:16]}..."
            )
    else:
        r.warn("Content hash comparison skipped (missing data)")

    # Bundle hash: Local SHA-256 vs Ledger — THE KEY INTEGRITY CHECK
    if ledger_bundle_hash:
        if ledger_bundle_hash == bundle_hash_local:
            r.ok("Bundle hash (Local == Ledger)  MATCH  <- INTEGRITY SEALED")
        else:
            r.fail(
                f"Bundle hash MISMATCH: "
                f"local={bundle_hash_local[:16]}... vs ledger={ledger_bundle_hash[:16]}..."
            )
    else:
        r.fail("Bundle hash NOT found in Ledger (seal-bundle may not have run)")

    # Bundle size
    if ledger_bundle_size and ledger_bundle_size == bundle_size_local:
        r.ok(f"Bundle size (Local == Ledger)  MATCH  ({bundle_size_local} bytes)")
    elif ledger_bundle_size:
        r.warn(
            f"Bundle size differs: local={bundle_size_local} vs ledger={ledger_bundle_size}"
        )

    # Status
    if ledger_status == "sealed":
        r.ok(f"Ledger status: {ledger_status}")
    elif ledger_status:
        r.warn(f"Ledger status: {ledger_status} (expected: sealed)")
    else:
        r.info("Ledger status field not present")

    # ── Step 4: /api/verify endpoint ────────────────────────
    code, data, _ = http_get_json(f"{LEDGER_URL}/api/verify/{receipt_id}")
    if code == 200:
        verified = data.get("verified", False) if data else False
        if verified:
            r.ok(f"/api/verify/{receipt_id}  -> VERIFIED")
        else:
            r.info(f"/api/verify returned 200 but verified={verified}")
    else:
        r.info(f"/api/verify returned HTTP {code}")

    # ── Step 5: Determinism test (INFO only) ────────────────
    print("  🔬 Determinism test (informational)...")
    jmpg_bytes2, _, _, err2 = export_jmpg("determinism")

    if err2:
        r.info(f"Second export failed, skipping determinism: {err2}")
    else:
        bundle_hash2 = sha256_bytes(jmpg_bytes2)
        if bundle_hash_local == bundle_hash2:
            r.ok("Bundle hash determinism: IDENTICAL across exports")
        else:
            # EXPECTED behavior — timestamps in ZIP metadata differ per export
            # NOT a defect: each export seals its unique hash in the Ledger
            r.info("Bundle hash varies across exports (timestamps by design)")

    # ── Step 6: ZIP structural integrity ────────────────────
    try:
        with tempfile.NamedTemporaryFile(suffix=".jmpg", delete=False) as tmp:
            tmp.write(jmpg_bytes)
            tmp_path = tmp.name
        with zipfile.ZipFile(tmp_path, "r") as z:
            names = set(z.namelist())
            required = {"manifest.json", "content.json", "receipt.json", "hash.txt"}
            missing = required - names
        os.unlink(tmp_path)

        if not missing:
            r.ok(f"ZIP structure: all required files present ({len(names)} total)")
        else:
            r.warn(f"ZIP missing: {', '.join(sorted(missing))}")
    except Exception as e:
        r.warn(f"ZIP structure check failed: {e}")


# ── Main ────────────────────────────────────────────────────

def main():
    now = datetime.now(timezone.utc).isoformat()
    sep = "=" * 60

    print(sep)
    print("  🐉 WINDI JMPG — VISTO DE QUALIDADE v3.1")
    print("  Linhagem de Ferro (Dual-Hash + Determinism-Aware)")
    print(sep)
    print(f"  Export Engine: {EXPORT_ENGINE}")
    print(f"  Forensic Ledger: {LEDGER_URL} (DIRECT)")
    print(f"  Timestamp: {now}")
    print(sep)

    r = CheckResult()

    phase1_service_health(r)
    phase2_verify_endpoints(r)
    phase3_full_pipeline(r)

    # ── Summary ─────────────────────────────────────────────
    print(f"\n{sep}")
    print("  📊 SUMMARY")
    print(sep)
    print(f"  Total:    {r.total}")
    print(f"  Passed:   {r.passed} ✅")
    print(f"  Critical: {r.failed} ❌")
    print(f"  Warnings: {r.warnings} ⚠️")
    print(f"  Info:     {r.infos} ℹ️")

    if r.fail_msgs:
        print("\n  ❌ FAILURES:")
        for m in r.fail_msgs:
            print(f"     • {m}")

    if r.warn_msgs:
        print("\n  ⚠️  WARNINGS:")
        for m in r.warn_msgs:
            print(f"     • {m}")

    if r.info_msgs:
        print("\n  ℹ️  NOTES (by design):")
        for m in r.info_msgs:
            print(f"     • {m}")

    # ── Verdict ─────────────────────────────────────────────
    # GREEN:  Zero failures + zero warnings (infos are OK)
    # YELLOW: Zero failures + some warnings
    # RED:    Any failures
    print(f"\n{sep}")

    if r.failed > 0:
        print("  🔴 LINHAGEM DE FERRO: COMPROMETIDA")
        print("  Critical failures detected. Investigate immediately.")
    elif r.warnings > 0:
        print("  🟡 LINHAGEM DE FERRO: PARCIAL")
        print("  Core OK. Review warnings above.")
    else:
        print("  🟢 LINHAGEM DE FERRO: INTACTA")
        print("  Dual-hash integrity verified end-to-end.")
        print("  Every export seals its unique hash in the Ledger.")

    print(sep)
    print('  "AI processes. Human decides. WINDI guarantees."')
    print()

    return 1 if r.failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
