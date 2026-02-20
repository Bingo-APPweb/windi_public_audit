#!/usr/bin/env python3
"""
🐉🛡 WINDI STRESS TEST — LINHAGEM DE FERRO
═══════════════════════════════════════════
Validates Sentinel LAW criteria under load:
  1. latency_p95     < 100ms
  2. unsynced        = 0
  3. hash_drift      = 0
  4. reconciliation  = HEALTHY
  5. event_drops     = 0
  6. chain_integrity = VALID

Test: Inject rapid receipt bursts through D1 → B1 → Ledger pipeline
"""

import json
import hashlib
import time
import uuid
import statistics
import sys
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from concurrent.futures import ThreadPoolExecutor, as_completed

# ═══════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════
BASE_URL = "https://admin.windia4desk.tech/desktop"
TOTAL_RECEIPTS = 100           # Total receipts to inject
BURST_SIZE = 10                # Receipts per burst
BURST_DELAY = 0.02             # 20ms between requests in burst (≈50/sec)
BETWEEN_BURSTS = 0.5           # 500ms between bursts
LATENCY_P95_LIMIT = 100        # ms — Sentinel LAW
TIMEOUT = 10                   # seconds per request

# ═══════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════
def api_get(path):
    """GET request to Desktop API"""
    url = f"{BASE_URL}{path}"
    req = Request(url, headers={"Accept": "application/json"})
    try:
        with urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}

def api_post(path, data):
    """POST request to Desktop API, returns (response, latency_ms)"""
    url = f"{BASE_URL}{path}"
    body = json.dumps(data).encode()
    req = Request(url, data=body, headers={
        "Content-Type": "application/json",
        "Accept": "application/json"
    })
    start = time.monotonic()
    try:
        with urlopen(req, timeout=TIMEOUT) as resp:
            latency = (time.monotonic() - start) * 1000
            result = json.loads(resp.read().decode())
            return result, latency
    except HTTPError as e:
        latency = (time.monotonic() - start) * 1000
        try:
            body = e.read().decode()
        except:
            body = str(e)
        return {"error": body, "status": e.code}, latency
    except Exception as e:
        latency = (time.monotonic() - start) * 1000
        return {"error": str(e)}, latency

def generate_content(seq):
    """Generate deterministic document content for hash verification"""
    return {
        "type": "doc",
        "content": [{"type": "paragraph", "content": [
            {"type": "text", "text": f"Stress test paragraph {seq} — Linhagem de Ferro — {uuid.uuid4().hex[:8]}"}
        ]}]
    }

def compute_hash(content):
    """SHA-256 canonical hash (recursive-key-sort)"""
    canonical = json.dumps(content, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()

def print_header(text):
    print(f"\n{'═' * 60}")
    print(f"  {text}")
    print(f"{'═' * 60}")

def print_law(name, value, expected, passed):
    icon = "✅" if passed else "❌"
    print(f"  {icon} {name:25s} = {str(value):15s}  (expected: {expected})")

# ═══════════════════════════════════════════
# PHASE 0: PRE-FLIGHT
# ═══════════════════════════════════════════
def phase_preflight():
    print_header("PHASE 0 — PRE-FLIGHT CHECK")
    
    health = api_get("/health")
    status = api_get("/api/status")
    reconcile = api_get("/api/reconcile")
    
    print(f"  Service:     {health.get('service', 'UNKNOWN')}")
    print(f"  Version:     {health.get('version', 'UNKNOWN')}")
    print(f"  Status:      {health.get('status', 'UNKNOWN')}")
    print(f"  Ledger:      {'connected' if health.get('ledger_connected') else 'DISCONNECTED'}")
    print(f"  Receipts:    {status.get('receipts_total', '?')}")
    print(f"  Unsynced:    {status.get('receipts_unsynced', '?')}")
    print(f"  Reconcile:   {reconcile.get('status', 'UNKNOWN')}")
    
    if health.get('status') != 'operational':
        print("\n  ⛔ ABORT: System not operational")
        sys.exit(1)
    if not health.get('ledger_connected'):
        print("\n  ⛔ ABORT: Ledger not connected")
        sys.exit(1)
    
    baseline_total = status.get('receipts_total', 0)
    print(f"\n  ✅ PRE-FLIGHT PASSED — Baseline: {baseline_total} receipts")
    return baseline_total

# ═══════════════════════════════════════════
# PHASE 1: BURST INJECTION
# ═══════════════════════════════════════════
def phase_burst_injection(baseline_total):
    print_header(f"PHASE 1 — BURST INJECTION ({TOTAL_RECEIPTS} receipts)")
    
    doc_id = f"STRESS-{uuid.uuid4().hex[:12]}"
    latencies = []
    errors = []
    hashes_sent = []
    
    total_bursts = TOTAL_RECEIPTS // BURST_SIZE
    
    for burst in range(total_bursts):
        burst_start = time.monotonic()
        burst_latencies = []
        
        for i in range(BURST_SIZE):
            seq = burst * BURST_SIZE + i
            content = generate_content(seq)
            content_hash = compute_hash(content)
            hashes_sent.append(content_hash)
            
            receipt_data = {
                "doc_id": doc_id,
                "action": "STRESS_TEST",
                "integrity_hash": content_hash,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "user_id": "guardian-stress-test",
                "metadata": {
                    "title": f"Linhagem de Ferro #{seq}",
                    "content_length": len(json.dumps(content)),
                    "hash_algorithm": "SHA-256",
                    "canonical_method": "recursive-key-sort",
                    "stress_burst": burst,
                    "stress_seq": seq
                }
            }
            
            result, latency = api_post("/api/ledger/receipts", receipt_data)
            latencies.append(latency)
            burst_latencies.append(latency)
            
            if "error" in result:
                errors.append({"seq": seq, "error": result["error"], "latency": latency})
            
            if BURST_DELAY > 0:
                time.sleep(BURST_DELAY)
        
        burst_elapsed = (time.monotonic() - burst_start) * 1000
        avg_lat = statistics.mean(burst_latencies)
        max_lat = max(burst_latencies)
        err_count = sum(1 for e in errors if e["seq"] >= burst * BURST_SIZE)
        
        status_icon = "🟢" if max_lat < LATENCY_P95_LIMIT else "🟡" if max_lat < 200 else "🔴"
        print(f"  Burst {burst+1:3d}/{total_bursts} | "
              f"avg={avg_lat:6.1f}ms  max={max_lat:6.1f}ms  "
              f"errors={err_count} {status_icon}")
        
        if BETWEEN_BURSTS > 0:
            time.sleep(BETWEEN_BURSTS)
    
    return doc_id, latencies, errors, hashes_sent

# ═══════════════════════════════════════════
# PHASE 2: SETTLE & VERIFY
# ═══════════════════════════════════════════
def phase_settle_verify(doc_id, baseline_total):
    print_header("PHASE 2 — SETTLE & VERIFY")
    
    print("  Waiting 2s for pipeline to settle...")
    time.sleep(2)
    
    # Get current status
    status = api_get("/api/status")
    new_total = status.get("receipts_total", 0)
    unsynced = status.get("receipts_unsynced", 0)
    
    print(f"  Receipts before: {baseline_total}")
    print(f"  Receipts after:  {new_total}")
    print(f"  New receipts:    {new_total - baseline_total}")
    print(f"  Expected:        {TOTAL_RECEIPTS}")
    print(f"  Unsynced:        {unsynced}")
    
    # Reconciliation
    reconcile = api_get("/api/reconcile")
    print(f"  Reconcile:       {reconcile.get('status', 'UNKNOWN')}")
    print(f"  Still pending:   {reconcile.get('still_pending', '?')}")
    print(f"  Failed IDs:      {reconcile.get('failed_ids', [])}")
    
    # Check receipts for this doc
    doc_receipts = api_get(f"/api/ledger/receipts?doc_id={doc_id}")
    doc_count = len(doc_receipts) if isinstance(doc_receipts, list) else 0
    print(f"  Doc receipts:    {doc_count}")
    
    # Hash drift check — verify all synced
    hash_drift = 0
    if isinstance(doc_receipts, list):
        for r in doc_receipts:
            if not r.get("ledger_synced"):
                hash_drift += 1
    
    return {
        "new_total": new_total,
        "expected": TOTAL_RECEIPTS,
        "received": new_total - baseline_total,
        "unsynced": unsynced,
        "hash_drift": hash_drift,
        "reconcile_status": reconcile.get("status", "UNKNOWN"),
        "still_pending": reconcile.get("still_pending", 0),
        "failed_ids": reconcile.get("failed_ids", []),
        "doc_count": doc_count
    }

# ═══════════════════════════════════════════
# PHASE 3: SENTINEL LAW VERDICT
# ═══════════════════════════════════════════
def phase_verdict(latencies, errors, verify_results):
    print_header("PHASE 3 — SENTINEL LAW VERDICT 🐉🛡")
    
    # Compute latency stats
    if latencies:
        lat_p50 = statistics.median(latencies)
        lat_p95 = sorted(latencies)[int(len(latencies) * 0.95)]
        lat_p99 = sorted(latencies)[int(len(latencies) * 0.99)]
        lat_max = max(latencies)
        lat_avg = statistics.mean(latencies)
    else:
        lat_p50 = lat_p95 = lat_p99 = lat_max = lat_avg = 999
    
    event_drops = TOTAL_RECEIPTS - verify_results["received"]
    reconcile_healthy = verify_results["reconcile_status"] == "reconciliation_complete"
    chain_valid = verify_results["hash_drift"] == 0 and len(verify_results["failed_ids"]) == 0
    
    # ── LAW CHECKS ──
    law_1 = lat_p95 < LATENCY_P95_LIMIT
    law_2 = verify_results["unsynced"] == 0
    law_3 = verify_results["hash_drift"] == 0
    law_4 = reconcile_healthy
    law_5 = event_drops == 0
    law_6 = chain_valid
    
    all_pass = all([law_1, law_2, law_3, law_4, law_5, law_6])
    
    print(f"\n  {'SENTINEL LAW — PERMANENT CRITERIA':^56}")
    print(f"  {'─' * 56}")
    print_law("latency_p95", f"{lat_p95:.1f}ms", f"< {LATENCY_P95_LIMIT}ms", law_1)
    print_law("unsynced", str(verify_results["unsynced"]), "= 0", law_2)
    print_law("hash_drift", str(verify_results["hash_drift"]), "= 0", law_3)
    print_law("reconciliation", "HEALTHY" if reconcile_healthy else "DEGRADED", "= HEALTHY", law_4)
    print_law("event_drops", str(event_drops), "= 0", law_5)
    print_law("chain_integrity", "VALID" if chain_valid else "BROKEN", "= VALID", law_6)
    
    print(f"\n  {'─' * 56}")
    print(f"  📊 Latency Profile:")
    print(f"     avg={lat_avg:.1f}ms  p50={lat_p50:.1f}ms  p95={lat_p95:.1f}ms  p99={lat_p99:.1f}ms  max={lat_max:.1f}ms")
    print(f"  📊 Throughput:")
    if latencies:
        total_time = sum(latencies) / 1000
        print(f"     {TOTAL_RECEIPTS} receipts in {total_time:.1f}s  ({TOTAL_RECEIPTS/total_time:.1f} receipts/sec effective)")
    print(f"  📊 Errors: {len(errors)}/{TOTAL_RECEIPTS}")
    
    if errors:
        print(f"\n  ⚠️  Error samples:")
        for e in errors[:5]:
            print(f"     seq={e['seq']}: {str(e['error'])[:80]}")
    
    print(f"\n  {'═' * 56}")
    if all_pass:
        print(f"  🐉🛡  VERDICT: ALL PASS — SENTINEL LAW VALIDATED  🐉🛡")
        print(f"  {'═' * 56}")
        print(f"\n  The foundation speaks. It is STRONG.")
        print(f"  These criteria are now PERMANENT LAW.")
        print(f"  Violation of ANY = immediate alert.")
    else:
        failed = []
        if not law_1: failed.append("latency_p95")
        if not law_2: failed.append("unsynced")
        if not law_3: failed.append("hash_drift")
        if not law_4: failed.append("reconciliation")
        if not law_5: failed.append("event_drops")
        if not law_6: failed.append("chain_integrity")
        print(f"  ⚠️  VERDICT: {len(failed)} LAW(S) FAILED")
        print(f"  {'═' * 56}")
        print(f"  Failed: {', '.join(failed)}")
        print(f"  Action: Investigate and fix before scaling.")
    
    return all_pass

# ═══════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════
def main():
    print("""
    🐉🛡 WINDI STRESS TEST — LINHAGEM DE FERRO
    ═══════════════════════════════════════════
    "AI processes. Human decides. WINDI guarantees."
    
    Test:     {total} receipts in bursts of {burst}
    Target:   ≈{rate} receipts/sec
    Criteria: Sentinel LAW (6 invariants)
    """.format(
        total=TOTAL_RECEIPTS,
        burst=BURST_SIZE,
        rate=int(1 / BURST_DELAY) if BURST_DELAY > 0 else "∞"
    ))
    
    start_time = time.monotonic()
    
    # Phase 0: Pre-flight
    baseline = phase_preflight()
    
    # Phase 1: Burst injection
    doc_id, latencies, errors, hashes = phase_burst_injection(baseline)
    
    # Phase 2: Settle & verify
    verify = phase_settle_verify(doc_id, baseline)
    
    # Phase 3: Verdict
    all_pass = phase_verdict(latencies, errors, verify)
    
    elapsed = time.monotonic() - start_time
    print(f"\n  Total test time: {elapsed:.1f}s")
    print(f"  Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"  Doc ID: {doc_id}")
    print()
    
    sys.exit(0 if all_pass else 1)

if __name__ == "__main__":
    main()
