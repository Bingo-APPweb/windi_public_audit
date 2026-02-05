"""
WINDI Deutsche Bahn Governance Simulator v1.0

Generates 1,000 realistic governance telemetry signals
simulating the document flow patterns of a large railway company
with known structural governance problems.

Case: Deutsche Bahn AG
- Revenue: €26.2B
- Loss 2024: -€1.8B
- Debt: €32.6B
- Core problem: Cannot track where approved resources go

"Flow is Truth. Content is Sovereign."
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import random
import sys
import time
import urllib.request
from typing import Any, Dict, List

# Add parent path for emitter import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "emitters", "python"))
from windi_emitter import WindiEmitter, WindiEmitterConfig, build_doc_vector_bytes, salt_local_id

# ─── DB Organizational Topology (Anonymized via Hash) ────────────

DB_DOMAINS = [
    "fernverkehr",           # Long-distance rail
    "regio",                 # Regional rail
    "cargo",                 # DB Cargo
    "netze",                 # Infrastructure (DB Netz)
    "schenker",              # Logistics (being sold)
    "station-service",       # Station management
    "systemtechnik",         # Engineering
    "energie",               # Energy supply
    "konzernleitung",        # Corporate HQ
    "finanzen",              # Finance
    "einkauf",               # Procurement
    "personal",              # HR
    "recht",                 # Legal
    "it-services",           # IT
    "sicherheit",            # Safety/Security
]

# Document archetypes representing DB's governance flows
DOC_TYPES = {
    "PROCUREMENT_CONTRACT":   {"type_id": 1, "impact_band": 4, "role_id": 10},
    "BUDGET_APPROVAL":        {"type_id": 2, "impact_band": 5, "role_id": 20},
    "MAINTENANCE_ORDER":      {"type_id": 3, "impact_band": 3, "role_id": 30},
    "INVESTMENT_PROPOSAL":    {"type_id": 4, "impact_band": 5, "role_id": 40},
    "COMPLIANCE_REPORT":      {"type_id": 5, "impact_band": 3, "role_id": 50},
    "CHANGE_REQUEST":         {"type_id": 6, "impact_band": 2, "role_id": 60},
    "VENDOR_EVALUATION":      {"type_id": 7, "impact_band": 3, "role_id": 70},
    "SAFETY_CLEARANCE":       {"type_id": 8, "impact_band": 4, "role_id": 80},
    "BOARD_RESOLUTION":       {"type_id": 9, "impact_band": 5, "role_id": 90},
    "INTERNAL_AUDIT":         {"type_id": 10, "impact_band": 4, "role_id": 100},
}

# Lifecycle states
STATES = {"draft": 1, "pending": 2, "approved": 3, "active": 4, "closed": 5, "escalated": 6}

# ─── Scenario Patterns (DB's known governance failures) ──────────

# Each scenario defines probability distributions for signals
# These model the STRUCTURAL problems, not content

SCENARIOS = {
    "bottleneck_leadership": {
        "description": "CEO/Board decisions concentrate too many approvals",
        "weight": 0.20,
        "signals": [
            {"code": "ID-CONC", "shelf": "S1", "weight_range": (70, 95), "events": ["APPROVAL_REQUESTED", "APPROVED"]},
            {"code": "ID-CENT", "shelf": "S1", "weight_range": (60, 85), "events": ["STATE_TRANSITION"]},
        ],
        "domains": ["konzernleitung", "finanzen"],
    },
    "procurement_opacity": {
        "description": "Contracts approved without clear delivery tracking",
        "weight": 0.25,
        "signals": [
            {"code": "IMP-GRAV", "shelf": "S2", "weight_range": (65, 90), "events": ["APPROVED", "APPROVAL_OVERRIDDEN"]},
            {"code": "IMP-SKEW", "shelf": "S2", "weight_range": (50, 75), "events": ["DOC_CREATED", "APPROVED"]},
            {"code": "DEC-OVR", "shelf": "S5", "weight_range": (75, 95), "events": ["APPROVAL_OVERRIDDEN"]},
        ],
        "domains": ["einkauf", "cargo", "netze"],
    },
    "infrastructure_deadlock": {
        "description": "Maintenance orders blocked by cross-department dependencies",
        "weight": 0.20,
        "signals": [
            {"code": "DOM-FRIC", "shelf": "S3", "weight_range": (70, 90), "events": ["DEPENDENCY_BLOCKING", "DEADLINE_EXCEEDED"]},
            {"code": "DOM-LOOP", "shelf": "S3", "weight_range": (55, 80), "events": ["STATE_TRANSITION", "APPROVAL_REQUESTED"]},
            {"code": "REL-NODE", "shelf": "S7", "weight_range": (75, 95), "events": ["DEPENDENCY_BLOCKING"]},
            {"code": "REL-DEPTH", "shelf": "S7", "weight_range": (60, 85), "events": ["DEPENDENCY_LINKED"]},
        ],
        "domains": ["netze", "systemtechnik", "sicherheit"],
    },
    "compliance_overload": {
        "description": "Excessive bureaucratic layers slow down critical safety decisions",
        "weight": 0.15,
        "signals": [
            {"code": "GOV-DENS", "shelf": "S4", "weight_range": (60, 85), "events": ["APPROVAL_REQUESTED", "STATE_TRANSITION"]},
            {"code": "GOV-STACK", "shelf": "S4", "weight_range": (70, 90), "events": ["REJECTED", "APPROVAL_REQUESTED"]},
            {"code": "TMP-STALL", "shelf": "S6", "weight_range": (65, 88), "events": ["DEADLINE_EXCEEDED"]},
        ],
        "domains": ["sicherheit", "recht", "regio", "fernverkehr"],
    },
    "quarter_end_rush": {
        "description": "Spike in approvals before reporting deadlines",
        "weight": 0.10,
        "signals": [
            {"code": "TMP-SPIKE", "shelf": "S6", "weight_range": (80, 98), "events": ["APPROVED", "APPROVAL_OVERRIDDEN"]},
            {"code": "DEC-INTU", "shelf": "S5", "weight_range": (60, 80), "events": ["APPROVED"]},
        ],
        "domains": ["finanzen", "konzernleitung", "einkauf"],
    },
    "schenker_divestiture": {
        "description": "Schenker sale creating governance gaps in logistics chain",
        "weight": 0.10,
        "signals": [
            {"code": "REL-DEPTH", "shelf": "S7", "weight_range": (70, 92), "events": ["DEPENDENCY_LINKED", "STATE_TRANSITION"]},
            {"code": "DOM-FRIC", "shelf": "S3", "weight_range": (65, 88), "events": ["DEPENDENCY_BLOCKING"]},
            {"code": "ID-CENT", "shelf": "S1", "weight_range": (55, 78), "events": ["APPROVAL_REQUESTED"]},
        ],
        "domains": ["schenker", "cargo", "konzernleitung"],
    },
}


def _generate_signal(
    emitter: WindiEmitter,
    csalt_b64: str,
    scenario_key: str,
    signal_def: Dict,
    domain: str,
    base_ts: int,
    offset_ms: int,
) -> Dict[str, Any]:
    """Generate a single telemetry signal from scenario definition."""

    # Pick random doc type weighted by scenario
    doc_key = random.choice(list(DOC_TYPES.keys()))
    doc_info = DOC_TYPES[doc_key]

    # Build doc vector (no content, only structural metadata)
    state_key = random.choice(list(STATES.keys()))
    local_id = f"DB-{scenario_key[:4].upper()}-{random.randint(10000, 99999)}"
    salted_id = salt_local_id(csalt_b64, local_id)

    doc_vec = build_doc_vector_bytes(
        doc_type_id=doc_info["type_id"],
        issuer_role_id=doc_info["role_id"],
        impact_band_id=doc_info["impact_band"],
        lifecycle_state_id=STATES[state_key],
        local_doc_id_salted=salted_id,
    )

    # Weight with some jitter
    w_min, w_max = signal_def["weight_range"]
    weight = min(100, max(0, random.randint(w_min, w_max) + random.randint(-5, 5)))

    # Event
    event = random.choice(signal_def["events"])

    # Context flags
    flags = 0
    if weight > 75:
        flags |= 1  # is_high_risk_flow
    if domain in ["konzernleitung", "finanzen"]:
        flags |= 2  # is_cross_domain (HQ touches everything)
    if event == "APPROVAL_OVERRIDDEN":
        flags |= 4  # has_human_override
    if scenario_key == "quarter_end_rush":
        flags |= 8  # is_end_of_month_window

    # Timestamp with realistic spread
    ts = base_ts + offset_ms

    packet = emitter.emit(
        shelf=signal_def["shelf"],
        code=signal_def["code"],
        weight=weight,
        domain_id=domain,
        doc_vector_bytes=doc_vec,
        event=event,
        ctx_window=random.choice(["5m", "15m", "1h", "24h"]),
        ctx_flags=flags,
        ts_ms=ts,
    )

    return packet


def generate_db_simulation(n_signals: int = 1000, seed: int = 42) -> List[Dict[str, Any]]:
    """
    Generate n_signals governance telemetry packets simulating
    Deutsche Bahn's document flow patterns.
    """
    random.seed(seed)

    # Client keys (would be generated per-client in production)
    csalt = base64.b64encode(os.urandom(32)).decode()
    hmac_key = base64.b64encode(os.urandom(32)).decode()

    cfg = WindiEmitterConfig(
        client_id="deutsche-bahn-ag-simulation",
        key_id="db-sim-key-001",
        csalt_b64=csalt,
        hmac_key_b64=hmac_key,
    )
    emitter = WindiEmitter(cfg)

    # Simulate 30 days of document flow
    base_ts = int(time.time() * 1000) - (30 * 24 * 3600 * 1000)
    time_span_ms = 30 * 24 * 3600 * 1000

    # Build weighted scenario pool
    scenario_pool = []
    for key, scenario in SCENARIOS.items():
        count = int(n_signals * scenario["weight"])
        for _ in range(count):
            scenario_pool.append((key, scenario))

    # Fill remaining
    while len(scenario_pool) < n_signals:
        key = random.choice(list(SCENARIOS.keys()))
        scenario_pool.append((key, SCENARIOS[key]))

    random.shuffle(scenario_pool)

    packets = []
    for i, (scenario_key, scenario) in enumerate(scenario_pool[:n_signals]):
        signal_def = random.choice(scenario["signals"])
        domain = random.choice(scenario["domains"])
        offset = int((i / n_signals) * time_span_ms) + random.randint(-3600000, 3600000)
        offset = max(0, min(time_span_ms, offset))

        pkt = _generate_signal(emitter, csalt, scenario_key, signal_def, domain, base_ts, offset)
        packets.append(pkt)

    # Sort by timestamp for realistic ordering
    packets.sort(key=lambda p: p["header"]["ts"])

    return packets, cfg, csalt, hmac_key


def run_simulation_to_bridge(
    bridge_url: str = "http://localhost:8090",
    n_signals: int = 1000,
    batch_size: int = 50,
):
    """Generate signals and send them to the Bridge API."""
    print(f"╔══════════════════════════════════════════════╗")
    print(f"║  WINDI Deutsche Bahn Simulator v1.0          ║")
    print(f"║  Generating {n_signals} governance signals           ║")
    print(f"╚══════════════════════════════════════════════╝")

    packets, cfg, csalt, hmac_key = generate_db_simulation(n_signals)

    # Register client with bridge
    print(f"\n→ Registering client with Bridge...")
    reg_data = json.dumps({
        "client_id_hash": base64.b64encode(
            hashlib.sha256(cfg.client_id.encode()).digest()
        ).decode(),
        "key_id": cfg.key_id,
        "hmac_key_b64": hmac_key,
    }).encode()

    req = urllib.request.Request(
        f"{bridge_url}/api/v1/register",
        data=reg_data,
        headers={"Content-Type": "application/json"},
    )
    try:
        resp = urllib.request.urlopen(req)
        print(f"  ✓ Registered: {json.loads(resp.read())}")
    except Exception as e:
        print(f"  ✗ Registration failed: {e}")
        return

    # Send in batches
    total_accepted = 0
    total_rejected = 0

    for batch_start in range(0, len(packets), batch_size):
        batch = packets[batch_start:batch_start + batch_size]
        batch_data = json.dumps({"packets": batch}).encode()

        req = urllib.request.Request(
            f"{bridge_url}/api/v1/telemetry/batch",
            data=batch_data,
            headers={"Content-Type": "application/json"},
        )
        try:
            resp = urllib.request.urlopen(req)
            result = json.loads(resp.read())
            total_accepted += result["accepted"]
            total_rejected += result["rejected"]
            pct = int(((batch_start + len(batch)) / len(packets)) * 100)
            bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
            print(f"\r  [{bar}] {pct}% — ✓{total_accepted} ✗{total_rejected}", end="", flush=True)
        except Exception as e:
            print(f"\n  ✗ Batch error at {batch_start}: {e}")

    print(f"\n\n═══ SIMULATION COMPLETE ═══")
    print(f"  Total sent:     {len(packets)}")
    print(f"  Accepted:       {total_accepted}")
    print(f"  Rejected:       {total_rejected}")
    print(f"  Success rate:   {total_accepted/len(packets)*100:.1f}%")

    # Fetch dashboard state
    try:
        req = urllib.request.Request(f"{bridge_url}/api/v1/dashboard")
        resp = urllib.request.urlopen(req)
        dashboard = json.loads(resp.read())
        print(f"\n═══ DASHBOARD STATE ═══")
        print(f"  Avg Weight:     {dashboard['totals']['avg_weight']}")
        print(f"  By Shelf:       {json.dumps(dashboard['by_shelf'], indent=2)}")
        print(f"  Hotspots:")
        for h in dashboard.get("hotspots", []):
            print(f"    🔥 {h['code']} ({h['signal_name']}) w={h['weight']} [{h['event']}]")
    except Exception as e:
        print(f"  Dashboard fetch failed: {e}")


def export_simulation_json(path: str = "db_simulation_1000.json", n_signals: int = 1000):
    """Export simulation data as JSON for offline use."""
    packets, cfg, csalt, hmac_key = generate_db_simulation(n_signals)

    export = {
        "meta": {
            "simulator": "WINDI DB Governance Simulator v1.0",
            "signals": len(packets),
            "client_id": cfg.client_id,
            "key_id": cfg.key_id,
            "hmac_key_b64": hmac_key,
            "csalt_b64": csalt,
            "generated_at": int(time.time() * 1000),
        },
        "packets": packets,
    }

    with open(path, "w") as f:
        json.dump(export, f, indent=2)

    print(f"Exported {len(packets)} signals to {path}")
    return path


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="WINDI DB Governance Simulator")
    parser.add_argument("--mode", choices=["bridge", "export"], default="export")
    parser.add_argument("--signals", type=int, default=1000)
    parser.add_argument("--bridge-url", default="http://localhost:8090")
    parser.add_argument("--output", default="db_simulation_1000.json")
    args = parser.parse_args()

    if args.mode == "bridge":
        run_simulation_to_bridge(args.bridge_url, args.signals)
    else:
        export_simulation_json(args.output, args.signals)
