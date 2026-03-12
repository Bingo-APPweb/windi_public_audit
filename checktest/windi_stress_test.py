#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║     WINDI PLATFORM STRESS TEST — Concurrent User Simulation  ║
║     Usage: python3 windi_stress_test.py [20|50|100]          ║
║     Run on Strato server — measures real performance          ║
╚══════════════════════════════════════════════════════════════╝
"""

import sys
import time
import threading
import urllib.request
import urllib.error
import json
import statistics
from datetime import datetime
from collections import defaultdict

# ── TEST CONFIGURATION ──────────────────────────────────────────

CRITICAL_ENDPOINTS = [
    ("Landing PMG",         "http://localhost:8107/",                       "GET",  None, 200),
    ("Verify Public",       "http://localhost:8114/verify-public/",         "GET",  None, 200),
    ("Forensic Ledger",     "http://localhost:8101/health",                 "GET",  None, 200),
    ("Forensic Vault",      "http://localhost:8106/health",                 "GET",  None, 200),
    ("Sentinel LAW",        "http://localhost:8102/health",                 "GET",  None, 200),
    ("Dragon Hub",          "http://localhost:8108/health",                 "GET",  None, 200),
    ("Wallet API",          "http://localhost:8099/health",                 "GET",  None, 200),
]

PIPELINE_ENDPOINTS = [
    ("Export Engine",       "http://localhost:8103/health",                 "GET",  None, 200),
    ("Communiqué Engine",   "http://localhost:8105/health",                 "GET",  None, 200),
    ("Desktop",             "http://localhost:8100/health",                 "GET",  None, 200),
    ("JMPG Viewer",         "http://localhost:8104/health",                 "GET",  None, 200),
]

AGENT_ENDPOINTS = [
    ("W-LEGAL-001",         "http://localhost:8091/legal/health",           "GET",  None, 200),
    ("W-NOTARY-001",        "http://localhost:8091/notary/health",          "GET",  None, 200),
    ("W-AUDIT-001",         "http://localhost:8091/audit/health",           "GET",  None, 200),
    ("Grove Arena",         "http://localhost:8091/grove/health",           "GET",  None, 200),
]

VERIFY_FLOW = [
    ("Verify I11 Receipt",  "http://localhost:8114/verify-public/?id=WINDI-I11-CONSTITUTIONAL-20260305", "GET", None, 200),
    ("Ledger Verify API",   "http://localhost:8101/api/verify/WINDI-I11-CONSTITUTIONAL-20260305",       "GET", None, 200),
]

ALL_ENDPOINTS = CRITICAL_ENDPOINTS + PIPELINE_ENDPOINTS + AGENT_ENDPOINTS + VERIFY_FLOW

# ── RESULT TRACKING ─────────────────────────────────────────────

class ResultTracker:
    def __init__(self):
        self.lock = threading.Lock()
        self.results = defaultdict(lambda: {
            "success": 0, "fail": 0, "times": [], "errors": []
        })

    def record(self, name, success, elapsed, error=None):
        with self.lock:
            r = self.results[name]
            r["times"].append(elapsed)
            if success:
                r["success"] += 1
            else:
                r["fail"] += 1
                if error:
                    r["errors"].append(error)

    def summary(self):
        return dict(self.results)

    def clear(self):
        with self.lock:
            self.results.clear()

tracker = ResultTracker()

# ── SINGLE REQUEST ───────────────────────────────────────────────

def make_request(name, url, method="GET", body=None, expected_code=200):
    start = time.time()
    try:
        headers = {"Content-Type": "application/json", "User-Agent": "WINDI-StressTest/1.0"}
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=10) as resp:
            elapsed = (time.time() - start) * 1000  # ms
            code = resp.getcode()
            success = (code == expected_code)
            tracker.record(name, success, elapsed, f"HTTP {code}" if not success else None)
    except urllib.error.HTTPError as e:
        elapsed = (time.time() - start) * 1000
        tracker.record(name, False, elapsed, f"HTTP {e.code}")
    except urllib.error.URLError as e:
        elapsed = (time.time() - start) * 1000
        tracker.record(name, False, elapsed, f"URLError: {e.reason}")
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        tracker.record(name, False, elapsed, str(e)[:60])

# ── SIMULATED USER SESSION ───────────────────────────────────────

def simulate_user(user_id, rounds=3):
    import random

    flow = []
    flow.extend(CRITICAL_ENDPOINTS[:3])
    flow.extend(random.sample(PIPELINE_ENDPOINTS, min(2, len(PIPELINE_ENDPOINTS))))
    flow.extend(VERIFY_FLOW)

    for _ in range(rounds):
        for name, url, method, body, expected in flow:
            make_request(name, url, method, body, expected)
            time.sleep(random.uniform(0.05, 0.2))

# ── STRESS TEST RUNNER ───────────────────────────────────────────

def run_stress_test(num_users, rounds=3):
    print(f"\n{'═'*60}")
    print(f"  🔥 STRESS TEST: {num_users} CONCURRENT USERS ({rounds} rounds each)")
    print(f"  Started: {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'═'*60}\n")

    threads = []
    start_time = time.time()

    for i in range(num_users):
        t = threading.Thread(target=simulate_user, args=(i, rounds), daemon=True)
        threads.append(t)

    for t in threads:
        t.start()

    for t in threads:
        t.join(timeout=120)

    total_time = time.time() - start_time

    print(f"  ⏱️  Total wall time: {total_time:.2f}s")
    print(f"  👥 Users: {num_users}  Rounds: {rounds}")
    print(f"\n{'─'*60}")
    print(f"  {'ENDPOINT':<30} {'OK':>5} {'FAIL':>5} {'AVG':>8} {'P95':>8} {'STATUS'}")
    print(f"{'─'*60}")

    summary = tracker.summary()
    total_reqs = 0
    total_ok = 0
    critical_failures = []

    for name, url, method, body, expected in ALL_ENDPOINTS:
        if name not in summary:
            continue

        r = summary[name]
        ok = r["success"]
        fail = r["fail"]
        total = ok + fail
        total_reqs += total
        total_ok += ok

        if total == 0:
            continue

        times = r["times"]
        avg_ms = statistics.mean(times) if times else 0
        p95_ms = sorted(times)[int(len(times) * 0.95)] if len(times) > 1 else times[0] if times else 0

        success_rate = (ok / total * 100) if total > 0 else 0

        if success_rate >= 99:
            status = "🟢 EXCELLENT"
        elif success_rate >= 95:
            status = "🟡 GOOD"
        elif success_rate >= 85:
            status = "🟠 DEGRADED"
        else:
            status = "🔴 FAILING"
            for name2, url2, _, _, _ in CRITICAL_ENDPOINTS:
                if name2 == name:
                    critical_failures.append(name)

        if p95_ms < 200:
            lat_str = f"{p95_ms:>6.0f}ms"
        elif p95_ms < 500:
            lat_str = f"{p95_ms:>6.0f}ms⚠"
        else:
            lat_str = f"{p95_ms:>6.0f}ms🔴"

        print(f"  {name:<30} {ok:>5} {fail:>5} {avg_ms:>6.0f}ms {lat_str} {status}")

        if r["errors"] and fail > 0:
            unique_errors = list(set(r["errors"][:3]))
            for e in unique_errors:
                print(f"    ↳ Error: {e}")

    print(f"\n{'═'*60}")
    print(f"  FINAL VERDICT — {num_users} USERS")
    print(f"{'─'*60}")

    overall_rate = (total_ok / total_reqs * 100) if total_reqs > 0 else 0
    print(f"  Total requests:  {total_reqs}")
    print(f"  Success rate:    {overall_rate:.1f}%")
    print(f"  Wall time:       {total_time:.2f}s")
    print(f"  Throughput:      {total_reqs/total_time:.1f} req/s")

    if overall_rate >= 99 and not critical_failures:
        print(f"\n  🐉 VERDICT: PLATFORM READY ✅")
        print(f"     {num_users} users → sustained without degradation")
        verdict = "READY"
    elif overall_rate >= 95 and not critical_failures:
        print(f"\n  🟡 VERDICT: ACCEPTABLE — minor tuning recommended")
        print(f"     Acceptable for launch with monitoring")
        verdict = "ACCEPTABLE"
    elif critical_failures:
        print(f"\n  🔴 VERDICT: CRITICAL FAILURES — NOT READY")
        print(f"     Critical services failing: {', '.join(critical_failures)}")
        verdict = "NOT_READY"
    else:
        print(f"\n  🟠 VERDICT: DEGRADED — needs investigation")
        verdict = "DEGRADED"

    print(f"{'═'*60}\n")
    return verdict, overall_rate

# ── BASELINE SNAPSHOT ────────────────────────────────────────────

def run_baseline():
    print("\n" + "═"*60)
    print("  📊 BASELINE CHECK (1 user, single pass)")
    print("═"*60)

    results = {}
    for name, url, method, body, expected in ALL_ENDPOINTS:
        start = time.time()
        try:
            req = urllib.request.Request(url, method=method)
            with urllib.request.urlopen(req, timeout=10) as resp:
                elapsed = (time.time() - start) * 1000
                code = resp.getcode()
                ok = (code == expected)
                results[name] = {"ok": ok, "code": code, "ms": elapsed}
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            results[name] = {"ok": False, "code": 0, "ms": elapsed, "err": str(e)[:50]}

    ok_count = sum(1 for r in results.values() if r["ok"])
    print(f"\n  {'ENDPOINT':<35} {'HTTP':>5} {'TIME':>8} {'STATUS'}")
    print("  " + "─"*58)
    for name, r in results.items():
        status = "✅" if r["ok"] else "❌"
        err = f"  ({r.get('err', '')})" if not r["ok"] else ""
        print(f"  {name:<35} {r['code']:>5} {r['ms']:>6.0f}ms {status}{err}")

    print(f"\n  Baseline: {ok_count}/{len(results)} endpoints OK")
    print("═"*60)
    return ok_count, len(results)

# ── MAIN ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    LEVELS = [20, 50, 100]
    if len(sys.argv) > 1:
        try:
            level_arg = int(sys.argv[1])
            LEVELS = [level_arg]
        except ValueError:
            pass

    print("""
╔══════════════════════════════════════════════════════════════╗
║         WINDI STRESS TEST — Pioneer Program Readiness        ║
║         "A plataforma aguenta os primeiros 100?"             ║
╚══════════════════════════════════════════════════════════════╝""")
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Targets: {LEVELS} concurrent users")

    ok_baseline, total_baseline = run_baseline()

    if ok_baseline < total_baseline * 0.7:
        print("\n  ⛔ Too many services down for stress test.")
        print("  Run windi_audit.sh first and fix failures.")
        sys.exit(1)

    print(f"\n  ✅ Baseline OK ({ok_baseline}/{total_baseline}) — starting stress tests...")
    time.sleep(2)

    verdicts = {}
    for level in LEVELS:
        tracker.clear()
        verdict, rate = run_stress_test(level, rounds=3)
        verdicts[level] = {"verdict": verdict, "rate": rate}
        if level != LEVELS[-1]:
            print("  ⏳ Cooldown 5s...")
            time.sleep(5)

    print("\n" + "═"*60)
    print("  🏁 STRESS TEST COMPLETE — SUMMARY")
    print("═"*60)
    print(f"\n  {'USERS':<10} {'RATE':>8} {'VERDICT'}")
    print("  " + "─"*40)
    for level, result in verdicts.items():
        emoji = "🟢" if result["verdict"] == "READY" else \
                "🟡" if result["verdict"] == "ACCEPTABLE" else \
                "🟠" if result["verdict"] == "DEGRADED" else "🔴"
        print(f"  {level:<10} {result['rate']:>7.1f}% {emoji} {result['verdict']}")

    print()
    all_ready = all(v["verdict"] in ["READY", "ACCEPTABLE"] for v in verdicts.values())
    if all_ready:
        print("  🐉 PLATFORM CLEARED FOR PIONEER PROGRAM LAUNCH")
        print()
        print("  Next step: LinkedIn Convocation Post")
    else:
        failing = [str(k) for k,v in verdicts.items() if v["verdict"] not in ["READY","ACCEPTABLE"]]
        print(f"  ⚠️  Platform needs fixes before launch")
        print(f"  Failed at: {', '.join(failing)} users")
        print()
        print("  Next step: Fix failures, re-run stress test")

    print("═"*60)

    # Save report
    report = {
        "date": datetime.now().isoformat(),
        "baseline": {"ok": ok_baseline, "total": total_baseline},
        "stress_tests": verdicts
    }
    report_file = f"/opt/windi/checktest/stress_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\n  📄 Report saved: {report_file}")
    except Exception as e:
        print(f"\n  ⚠️  Could not save report: {e}")
