"""
W-CANVAS-OBS-001 — Sovereign System Observability Layer
WINDI Publishing House | Kempten, Bavaria

Provides unified observability state from WSG + CIA sources.
Enables real-time dashboard rendering and state sealing.

Invariants:
O1 — Data comes only from internal sources (WSG/CIA)
O2 — Mapping is declarative (recipe), not hardcode
O3 — Visualization separated from collection
O4 — Snapshot always sealable
O5 — No mandatory external dependency

Version: 1.0.0
Date: 21-03-2026
"""

import os
import json
import hashlib
import httpx
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from flask import Blueprint, request, jsonify

logger = logging.getLogger("W-CANVAS-OBS-001")

obs_bp = Blueprint("obs", __name__, url_prefix="/obs")

# ── Config ──────────────────────────────────────────────────────
LEDGER_BASE = os.getenv("LEDGER_URL", "http://127.0.0.1:8101")
WSG_ENDPOINTS = [
    {"name": "Dragon Hub", "url": "http://127.0.0.1:8108/health", "critical": True},
    {"name": "Forensic Ledger", "url": "http://127.0.0.1:8101/health", "critical": True},
    {"name": "Sandbox Core", "url": "http://127.0.0.1:8091/health", "critical": True},
    {"name": "Desktop GEN7", "url": "http://127.0.0.1:8119/health", "critical": False},
    {"name": "Wallet Service", "url": "http://127.0.0.1:8099/health", "critical": False},
    {"name": "Dispatch Gateway", "url": "http://127.0.0.1:8121/health", "critical": False},
    {"name": "Lead Admin", "url": "http://127.0.0.1:8096/health", "critical": False},
    {"name": "Canvas Engine", "url": "http://127.0.0.1:8091/canvas/status", "critical": False},
]

# ── State Cache ─────────────────────────────────────────────────
_state_cache = {
    "last_update": None,
    "data": None,
    "ttl_seconds": 10
}


def collect_wsg_state() -> Dict[str, Any]:
    """Collect real-time state from WSG endpoints."""
    services_up = 0
    services_down = 0
    latencies = []
    service_status = []

    for svc in WSG_ENDPOINTS:
        try:
            start = datetime.now(timezone.utc)
            resp = httpx.get(svc["url"], timeout=3.0)
            latency = (datetime.now(timezone.utc) - start).total_seconds() * 1000

            if resp.status_code == 200:
                services_up += 1
                latencies.append(latency)
                service_status.append({
                    "name": svc["name"],
                    "status": "online",
                    "latency_ms": round(latency, 1),
                    "critical": svc["critical"]
                })
            else:
                services_down += 1
                service_status.append({
                    "name": svc["name"],
                    "status": "error",
                    "code": resp.status_code,
                    "critical": svc["critical"]
                })
        except Exception as e:
            services_down += 1
            service_status.append({
                "name": svc["name"],
                "status": "offline",
                "error": str(e)[:50],
                "critical": svc["critical"]
            })

    avg_latency = round(sum(latencies) / len(latencies), 1) if latencies else 0
    health = "green" if services_down == 0 else ("yellow" if services_down < 3 else "red")

    return {
        "services_up": services_up,
        "services_down": services_down,
        "services_total": len(WSG_ENDPOINTS),
        "latency_ms": avg_latency,
        "health": health,
        "services": service_status
    }


def collect_cia_state() -> Dict[str, Any]:
    """Collect CIA metrics (sovereignty, engine mix, etc.)."""
    # Read from sovereignty gate stats if available
    stats_path = "/opt/windi/agents/constitutional-agent/data/canvas_stats.json"

    local_calls = 0
    external_calls = 0
    tokens_saved = 0

    try:
        if os.path.exists(stats_path):
            with open(stats_path, "r") as f:
                stats = json.load(f)
                local_calls = stats.get("local_calls", 0)
                external_calls = stats.get("external_calls", 0)
                tokens_saved = stats.get("tokens_saved", 0)
    except Exception as e:
        logger.warning(f"Could not read canvas stats: {e}")

    total_calls = local_calls + external_calls
    sovereignty_score = round(local_calls / total_calls, 2) if total_calls > 0 else 1.0

    return {
        "mode": "SOVEREIGN" if sovereignty_score >= 0.8 else "HYBRID",
        "engine_mix": {
            "A": round(local_calls / total_calls, 2) if total_calls > 0 else 1.0,
            "B": round(external_calls / total_calls, 2) if total_calls > 0 else 0.0
        },
        "local_vs_external": {
            "local": local_calls,
            "external": external_calls
        },
        "tokens_saved": tokens_saved,
        "sovereignty_score": sovereignty_score
    }


def get_obs_state(force_refresh: bool = False) -> Dict[str, Any]:
    """Get unified observability state with caching."""
    start_time = datetime.now(timezone.utc)

    # Check cache
    if not force_refresh and _state_cache["data"]:
        if _state_cache["last_update"]:
            age = (start_time - _state_cache["last_update"]).total_seconds()
            if age < _state_cache["ttl_seconds"]:
                cached = _state_cache["data"].copy()
                cached["meta"]["from_cache"] = True
                cached["meta"]["cache_age_ms"] = round(age * 1000)
                return cached

    # Collect fresh state
    wsg = collect_wsg_state()
    cia = collect_cia_state()

    # Calculate execution time
    exec_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

    # Derive metrics
    uptime_ratio = round(wsg["services_up"] / wsg["services_total"], 2)

    # Determine sovereignty label
    sov_score = cia["sovereignty_score"]
    if sov_score >= 0.95:
        sov_label = "LOCAL"
    elif sov_score >= 0.7:
        sov_label = "HYBRID"
    else:
        sov_label = "EXTERNAL"

    state = {
        "timestamp": start_time.isoformat(),
        "agent": "W-CANVAS-OBS-001",
        "version": "1.0.0",
        "wsg": wsg,
        "cia": cia,
        "derived": {
            "sovereignty_score": cia["sovereignty_score"],
            "uptime_ratio": uptime_ratio,
            "health_status": wsg["health"],
            "operational_mode": cia["mode"]
        },
        "meta": {
            "execution_time_ms": round(exec_time, 1),
            "data_freshness": "realtime",
            "sovereignty": sov_label,
            "from_cache": False,
            "external_dependencies": 0
        }
    }

    # Update cache
    _state_cache["data"] = state
    _state_cache["last_update"] = start_time

    return state


# ═══════════════════════════════════════════════════════════════
# API Endpoints
# ═══════════════════════════════════════════════════════════════

@obs_bp.route("/state", methods=["GET"])
def get_state():
    """Get unified observability state."""
    force = request.args.get("force", "false").lower() == "true"
    state = get_obs_state(force_refresh=force)
    return jsonify(state)


@obs_bp.route("/health", methods=["GET"])
def health():
    """OBS health check."""
    return jsonify({
        "agent": "W-CANVAS-OBS-001",
        "status": "healthy",
        "cache_ttl": _state_cache["ttl_seconds"]
    })


@obs_bp.route("/wsg", methods=["GET"])
def get_wsg():
    """Get WSG state only."""
    return jsonify(collect_wsg_state())


@obs_bp.route("/cia", methods=["GET"])
def get_cia():
    """Get CIA state only."""
    return jsonify(collect_cia_state())


@obs_bp.route("/seal", methods=["POST"])
def seal_state():
    """Seal current state to Forensic Ledger."""
    state = get_obs_state(force_refresh=True)

    # Create state hash
    state_json = json.dumps(state, sort_keys=True)
    state_hash = hashlib.sha256(state_json.encode()).hexdigest()

    # Prepare receipt
    receipt_id = f"WINDI-OBS-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    try:
        ledger_payload = {
            "receipt_id": receipt_id,
            "actor": request.json.get("wallet_id", "system"),
            "app": "canvas-obs",
            "doc_name": "System State Snapshot",
            "doc_type": "obs_snapshot",
            "content_hash": state_hash,
            "invariants": ["O1", "O4"],
            "stage": "C6",
            "metadata": {
                "timestamp": state["timestamp"],
                "services_up": state["wsg"]["services_up"],
                "sovereignty_score": state["derived"]["sovereignty_score"],
                "health_status": state["derived"]["health_status"]
            }
        }

        resp = httpx.post(f"{LEDGER_BASE}/api/receipts", json=ledger_payload, timeout=5.0)

        if resp.status_code in (200, 201):
            return jsonify({
                "success": True,
                "receipt_id": receipt_id,
                "state_hash": state_hash,
                "sealed_at": state["timestamp"],
                "verify_url": f"https://windi-domain.com/verify-public/?id={receipt_id}"
            })
        else:
            return jsonify({
                "success": False,
                "error": f"Ledger returned {resp.status_code}"
            }), 500

    except Exception as e:
        logger.exception("Failed to seal state")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@obs_bp.route("/report", methods=["GET"])
def sovereignty_report():
    """Generate sovereignty report (last 24h)."""
    state = get_obs_state()
    cia = state["cia"]
    wsg = state["wsg"]

    total = cia["local_vs_external"]["local"] + cia["local_vs_external"]["external"]

    return jsonify({
        "period": "24h",
        "generated_at": state["timestamp"],
        "requests_total": total,
        "local_executed": cia["local_vs_external"]["local"],
        "external_calls": cia["local_vs_external"]["external"],
        "tokens_saved": cia["tokens_saved"],
        "sovereignty_score": cia["sovereignty_score"],
        "uptime": state["derived"]["uptime_ratio"],
        "health": wsg["health"],
        "services": {
            "up": wsg["services_up"],
            "down": wsg["services_down"],
            "total": wsg["services_total"]
        }
    })
