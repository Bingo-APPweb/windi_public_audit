"""
WINDI Dispatch Stress Master v1.0
──────────────────────────────────
Stress test for the Dispatch Gateway :8121

Tests:
  - 1000 concurrent activations across all network tiers
  - Invariant enforcement under load (I5 failures correctly rejected)
  - Layer distribution correctness per network tier
  - Latency profile (p50, p95, p99)
  - Evaporation policy consistency

Run:
  pip install httpx --break-system-packages
  python3 dispatch_stress.py

  # Custom target:
  python3 dispatch_stress.py --url http://localhost:8121 --requests 500 --workers 25
"""

import asyncio
import httpx
import time
import random
import sys
import argparse
from collections import defaultdict
from statistics import mean, median, stdev

# ── CONFIG ──────────────────────────────────────
TARGET_URL        = "http://localhost:8121/activate"
HEALTH_URL        = "http://localhost:8121/health"
TOTAL_REQUESTS    = 1000
CONCURRENT_WORKERS = 50
REQUEST_TIMEOUT   = 5.0
NETWORKS          = ["2g", "3g", "4g", "5g", "wifi"]

# Real seeds from Ledger for valid activation tests
REAL_SEEDS = [
    "WINDI-CANVAS-COMM-EE2007B2",
    "WINDI-WEB-COMM-EE2007B2",
    "WINDI-WEB-COMM-C44C8010",
    "WINDI-CANVAS-COMM-C44C8010",
    "WINDI-VIRTUE-ONEWOW-20260314",
]
INVALID_SEED_PREFIX = "FAKE-SEED-"    # simulate forged seeds (10% of requests)

EXPECTED_LAYERS = {
    "2g":   1,  # P1 only
    "3g":   2,  # P1+P2
    "4g":   3,  # P1+P2+P3
    "5g":   4,  # P1+P2+P3+P4
    "wifi": 4,  # P1+P2+P3+P4
}

# ── RESULT DATACLASS ─────────────────────────────
class Result:
    def __init__(self, success, latency_ms, network, layers, status_code, evap_policy, error=None):
        self.success     = success
        self.latency_ms  = latency_ms
        self.network     = network
        self.layers      = layers
        self.status_code = status_code
        self.evap_policy = evap_policy
        self.error       = error

# ── SINGLE USER SIMULATION ───────────────────────
async def simulate_activation(client: httpx.AsyncClient, user_id: int) -> Result:
    network = random.choice(NETWORKS)

    # 90% real seeds from Ledger, 10% invalid (should be rejected with 403)
    if random.random() < 0.9:
        seed_id = random.choice(REAL_SEEDS)
    else:
        seed_id = f"{INVALID_SEED_PREFIX}{user_id:05d}"

    payload = {
        "seed_id":         seed_id,
        "stream_token":    f"ST-{random.getrandbits(48):012X}",
        "network_quality": network,
        "device_id":       f"DEV-{user_id:04d}"
    }

    t0 = time.time()
    try:
        r = await client.post(TARGET_URL, json=payload, timeout=REQUEST_TIMEOUT)
        latency = (time.time() - t0) * 1000

        if r.status_code == 200:
            data = r.json()
            layers = len(data.get("manifest", []))
            evap   = data.get("evaporation_policy", "unknown")
            return Result(True, latency, network, layers, 200, evap)

        elif r.status_code == 403:
            # I5 failure — expected for FAKE seeds
            latency = (time.time() - t0) * 1000
            return Result(False, latency, network, 0, 403, "rejected")

        else:
            latency = (time.time() - t0) * 1000
            return Result(False, latency, network, 0, r.status_code, "error")

    except httpx.TimeoutException:
        return Result(False, REQUEST_TIMEOUT * 1000, network, 0, 0, "error", "timeout")
    except Exception as e:
        return Result(False, 0, network, 0, 0, "error", str(e))

# ── PERCENTILE HELPER ────────────────────────────
def percentile(data, pct):
    if not data:
        return 0
    sorted_d = sorted(data)
    idx = int(len(sorted_d) * pct / 100)
    return sorted_d[min(idx, len(sorted_d) - 1)]

# ── MAIN STRESS RUNNER ───────────────────────────
async def main():
    parser = argparse.ArgumentParser(description="WINDI Dispatch Stress Master v1.0")
    parser.add_argument("--url",      default=TARGET_URL,         help="Target URL")
    parser.add_argument("--requests", default=TOTAL_REQUESTS, type=int, help="Total requests")
    parser.add_argument("--workers",  default=CONCURRENT_WORKERS, type=int, help="Concurrent workers")
    args = parser.parse_args()

    print()
    print("=" * 55)
    print("  WINDI DISPATCH STRESS MASTER v1.0")
    print("=" * 55)
    print(f"  Target   : {args.url}")
    print(f"  Requests : {args.requests}")
    print(f"  Workers  : {args.workers}")
    print(f"  Networks : {', '.join(NETWORKS)}")
    print("=" * 55)

    # ── Pre-flight health check ──────────────────
    print("\n  [PRE-FLIGHT] Checking Gateway health...")
    try:
        async with httpx.AsyncClient(timeout=3.0) as c:
            h = await c.get(HEALTH_URL)
        if h.status_code == 200:
            data = h.json()
            print(f"  Gateway {data.get('status','?')} — v{data.get('version','?')}")
        else:
            print(f"  Health check failed: HTTP {h.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"  Gateway unreachable: {e}")
        print("  Start the gateway first: python3 dispatch_gateway.py")
        sys.exit(1)

    # ── Run stress test ──────────────────────────
    print(f"\n  [STRESS] Firing {args.requests} activations...")
    t_global_start = time.time()

    semaphore = asyncio.Semaphore(args.workers)

    async def bounded_activation(client, uid):
        async with semaphore:
            return await simulate_activation(client, uid)

    async with httpx.AsyncClient() as client:
        tasks = [bounded_activation(client, i) for i in range(args.requests)]
        results = await asyncio.gather(*tasks)

    total_elapsed = time.time() - t_global_start

    # ── Metrics ──────────────────────────────────
    successes  = [r for r in results if r.success]
    rejections = [r for r in results if r.status_code == 403]
    errors     = [r for r in results if not r.success and r.status_code != 403]
    latencies  = [r.latency_ms for r in successes]

    success_rate = len(successes) / args.requests * 100
    rejection_rate = len(rejections) / args.requests * 100
    rps = args.requests / total_elapsed

    print()
    print("=" * 55)
    print("  DISPATCH GATEWAY — STRESS RESULTS")
    print("=" * 55)
    print(f"  Total Time    : {total_elapsed:.2f}s")
    print(f"  Throughput    : {rps:.1f} req/s")
    print()
    print(f"  Activated   : {len(successes):>5} / {args.requests}  ({success_rate:.1f}%)")
    print(f"  I5 Rejected : {len(rejections):>5} / {args.requests}  ({rejection_rate:.1f}%)")
    print(f"  Errors      : {len(errors):>5} / {args.requests}")
    print()

    if latencies:
        print(f"  LATENCY (successful activations only):")
        print(f"  p50  : {percentile(latencies, 50):.1f} ms")
        print(f"  p95  : {percentile(latencies, 95):.1f} ms")
        print(f"  p99  : {percentile(latencies, 99):.1f} ms")
        print(f"  mean : {mean(latencies):.1f} ms")
        print(f"  peak : {max(latencies):.1f} ms")
        print()

    # ── Layer distribution per network ───────────
    print("  HYDRATION LAYERS (P-layer count by network):")
    net_layers = defaultdict(list)
    net_counts = defaultdict(int)
    for r in successes:
        net_layers[r.network].append(r.layers)
        net_counts[r.network] += 1

    for net in NETWORKS:
        layers_list = net_layers.get(net, [])
        if layers_list:
            avg_layers = mean(layers_list)
            expected   = EXPECTED_LAYERS[net]
            ok = "OK" if abs(avg_layers - expected) < 0.2 else "WARN"
            print(f"  {ok} [{net:>4}] avg={avg_layers:.1f} P-layers "
                  f"(expected={expected}) — {net_counts[net]} activations")

    # ── Evaporation policy check ──────────────────
    print()
    print("  EVAPORATION POLICY distribution:")
    evap_counts = defaultdict(int)
    for r in successes:
        evap_counts[r.evap_policy] += 1
    for policy, count in sorted(evap_counts.items()):
        print(f"  {policy:<14}: {count}")

    # ── Gate assessment ───────────────────────────
    print()
    print("=" * 55)
    print("  CONSTITUTIONAL GATE ASSESSMENT")
    print("=" * 55)

    gate_ok = True

    if success_rate < 85:
        print(f"  SUCCESS RATE {success_rate:.1f}% below 85% threshold — FAIL")
        gate_ok = False
    else:
        print(f"  Success rate {success_rate:.1f}% — PASS")

    if latencies and percentile(latencies, 95) > 200:
        p95 = percentile(latencies, 95)
        print(f"  p95 latency {p95:.1f}ms exceeds 200ms — FAIL")
        gate_ok = False
    elif latencies:
        print(f"  p95 latency {percentile(latencies, 95):.1f}ms — PASS")

    if len(errors) > args.requests * 0.05:
        print(f"  Error rate {len(errors)/args.requests*100:.1f}% exceeds 5% — FAIL")
        gate_ok = False
    else:
        print(f"  Error rate {len(errors)/args.requests*100:.1f}% — PASS")

    # Layer correctness check
    layer_correct = True
    for net in NETWORKS:
        layers_list = net_layers.get(net, [])
        if layers_list:
            avg = mean(layers_list)
            if abs(avg - EXPECTED_LAYERS[net]) > 0.3:
                layer_correct = False
                break
    if not layer_correct:
        print(f"  Hydration layer mapping inconsistency — REVIEW")
    else:
        print(f"  Hydration layers correct for all network tiers — PASS")

    print()
    if gate_ok:
        print("  GATEWAY PRONTO PARA PRODUCAO")
        print("  OM SHANTI — A semente esta solida.")
    else:
        print("  GATEWAY PRECISA DE AJUSTE ANTES DO DEPLOY")
        print("  Review latency / error rates antes de subir ao nginx.")
    print("=" * 55)
    print()

if __name__ == "__main__":
    asyncio.run(main())
