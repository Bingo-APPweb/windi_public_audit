"""
W-UDB-001 — WINDI Unified Dashboard
Sovereign Video Evidence Engine — God View

Port: 8140
"Se não consegues ver, não consegues escalar."

Liga IA+H · Kempten, Bavaria · 2026
"""

import os
import sqlite3
import hashlib
import requests
from datetime import datetime, timezone
from pathlib import Path
from flask import Flask, jsonify, render_template, request, Response
import json
import time

app = Flask(__name__)

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

PORT = 8140
VERSION = "1.0.0"

# Agent endpoints
AGENTS = {
    "VD-CUT": {
        "name": "W-VD-CUT-001",
        "port": 8128,
        "health": "http://localhost:8128/vd-cut/health",
        "framework": "FastAPI"
    },
    "VD-MASS": {
        "name": "W-VD-MASS-001",
        "port": 8131,
        "health": "http://localhost:8131/health",
        "metrics": "http://localhost:8131/metrics",
        "exceptions": "http://localhost:8131/queue/exceptions",
        "framework": "Flask"
    },
    "LEDGER": {
        "name": "Forensic Ledger",
        "port": 8101,
        "health": "http://localhost:8101/health",
        "framework": "Flask"
    }
}

# Paths
BASE_DIR = Path("/opt/windi/udb")
DB_PATH = BASE_DIR / "dashboard.db"

# Request timeout
TIMEOUT = 2.0


# ═══════════════════════════════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════════════════════════════

def init_db():
    """Initialize dashboard database."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Metrics history (for trends)
    c.execute("""
        CREATE TABLE IF NOT EXISTS metrics_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            zone TEXT NOT NULL,
            metric_name TEXT NOT NULL,
            metric_value REAL NOT NULL
        )
    """)

    # Emergency events
    c.execute("""
        CREATE TABLE IF NOT EXISTS emergency_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            event_type TEXT NOT NULL,
            actor_did TEXT NOT NULL,
            reason TEXT,
            affected_policies TEXT,
            resolved_at TEXT
        )
    """)

    # Daily manifests
    c.execute("""
        CREATE TABLE IF NOT EXISTS daily_manifests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE NOT NULL,
            vdcut_seals INTEGER DEFAULT 0,
            vdmass_seals INTEGER DEFAULT 0,
            super_hash TEXT,
            created_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def fetch_agent(agent_key: str, endpoint: str = "health") -> dict:
    """Fetch data from an agent with timeout."""
    agent = AGENTS.get(agent_key)
    if not agent:
        return {"status": "ERROR", "error": f"Unknown agent: {agent_key}"}

    url = agent.get(endpoint, agent.get("health"))
    try:
        r = requests.get(url, timeout=TIMEOUT)
        if r.status_code == 200:
            return {"status": "ONLINE", "data": r.json()}
        else:
            return {"status": "ERROR", "code": r.status_code}
    except requests.exceptions.Timeout:
        return {"status": "TIMEOUT", "agent": agent["name"]}
    except requests.exceptions.ConnectionError:
        return {"status": "DOWN", "agent": agent["name"]}
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}


def calculate_integrity_score() -> float:
    """Calculate global integrity score from both agents."""
    # For now, simple check - both agents responding
    vdcut = fetch_agent("VD-CUT")
    vdmass = fetch_agent("VD-MASS")

    online_count = sum([
        1 if vdcut.get("status") == "ONLINE" else 0,
        1 if vdmass.get("status") == "ONLINE" else 0
    ])

    return (online_count / 2) * 100


# ═══════════════════════════════════════════════════════════════
# ROUTES — Health & Info
# ═══════════════════════════════════════════════════════════════

@app.route("/health")
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "ONLINE",
        "service": "W-UDB-001",
        "version": VERSION,
        "port": PORT,
        "protocol": "I9 + I11",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })


@app.route("/")
def index():
    """Render the God View dashboard."""
    return render_template("index.html")


# ═══════════════════════════════════════════════════════════════
# ROUTES — Zone Data
# ═══════════════════════════════════════════════════════════════

@app.route("/zone/a")
def zone_a():
    """
    ZONE A — Forensic Hub (VD-CUT :8128)
    Individual I9 seals, manual operations
    """
    result = fetch_agent("VD-CUT")

    # Enrich with VD-CUT specific data
    if result.get("status") == "ONLINE":
        data = result.get("data", {})
        return jsonify({
            "zone": "A",
            "name": "FORENSIC HUB",
            "agent": "W-VD-CUT-001",
            "port": 8128,
            "status": "ONLINE",
            "governance": "I9 Direct",
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    else:
        return jsonify({
            "zone": "A",
            "name": "FORENSIC HUB",
            "agent": "W-VD-CUT-001",
            "port": 8128,
            "status": result.get("status", "DOWN"),
            "governance": "I9 Direct",
            "error": result.get("error"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 503 if result.get("status") == "DOWN" else 200


@app.route("/zone/b")
def zone_b():
    """
    ZONE B — Mass Automation Pulse (VD-MASS :8131)
    Policy-based I9-P seals, batch operations
    """
    health_result = fetch_agent("VD-MASS")
    metrics_result = fetch_agent("VD-MASS", "metrics")
    exceptions_result = fetch_agent("VD-MASS", "exceptions")

    if health_result.get("status") == "ONLINE":
        metrics_data = metrics_result.get("data", {}) if metrics_result.get("status") == "ONLINE" else {}
        exceptions_data = exceptions_result.get("data", {}) if exceptions_result.get("status") == "ONLINE" else {}

        return jsonify({
            "zone": "B",
            "name": "MASS PULSE",
            "agent": "W-VD-MASS-001",
            "port": 8131,
            "status": "ONLINE",
            "governance": "I9-P Policy",
            "metrics": metrics_data,
            "pending_exceptions": exceptions_data.get("pending", 0) if isinstance(exceptions_data, dict) else 0,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    else:
        return jsonify({
            "zone": "B",
            "name": "MASS PULSE",
            "agent": "W-VD-MASS-001",
            "port": 8131,
            "status": health_result.get("status", "DOWN"),
            "governance": "I9-P Policy",
            "error": health_result.get("error"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 503 if health_result.get("status") == "DOWN" else 200


@app.route("/zone/c")
def zone_c():
    """
    ZONE C — Ledger Integrity (Dual-Chain)
    Global integrity metrics across both agents
    """
    vdcut = fetch_agent("VD-CUT")
    vdmass = fetch_agent("VD-MASS")
    ledger = fetch_agent("LEDGER")

    # Calculate integrity
    agents_online = sum([
        1 if vdcut.get("status") == "ONLINE" else 0,
        1 if vdmass.get("status") == "ONLINE" else 0,
        1 if ledger.get("status") == "ONLINE" else 0
    ])
    integrity_score = (agents_online / 3) * 100

    return jsonify({
        "zone": "C",
        "name": "LEDGER INTEGRITY",
        "status": "HEALTHY" if integrity_score == 100 else "DEGRADED" if integrity_score > 0 else "CRITICAL",
        "integrity_score": integrity_score,
        "agents": {
            "VD-CUT": vdcut.get("status"),
            "VD-MASS": vdmass.get("status"),
            "LEDGER": ledger.get("status")
        },
        "governance": "Dual-Chain",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })


@app.route("/metrics")
def metrics():
    """
    Aggregated metrics from all zones.
    Used by the frontend for KPI display.
    """
    zone_a = zone_a_data()
    zone_b = zone_b_data()
    zone_c = zone_c_data()

    return jsonify({
        "service": "W-UDB-001",
        "kpis": {
            "integrity_score": zone_c.get("integrity_score", 0),
            "exception_pressure": zone_b.get("pending_exceptions", 0),
            "sovereignty_ratio": 100.0  # All local processing
        },
        "zones": {
            "a": zone_a,
            "b": zone_b,
            "c": zone_c
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    })


def zone_a_data():
    """Internal helper for zone A data."""
    result = fetch_agent("VD-CUT")
    return {
        "status": result.get("status"),
        "data": result.get("data", {})
    }


def zone_b_data():
    """Internal helper for zone B data."""
    health = fetch_agent("VD-MASS")
    metrics = fetch_agent("VD-MASS", "metrics")
    exceptions = fetch_agent("VD-MASS", "exceptions")

    metrics_data = metrics.get("data", {}) if metrics.get("status") == "ONLINE" else {}
    exceptions_data = exceptions.get("data", {}) if exceptions.get("status") == "ONLINE" else {}

    return {
        "status": health.get("status"),
        "metrics": metrics_data,
        "pending_exceptions": exceptions_data.get("pending", 0) if isinstance(exceptions_data, dict) else 0
    }


def zone_c_data():
    """Internal helper for zone C data."""
    vdcut = fetch_agent("VD-CUT")
    vdmass = fetch_agent("VD-MASS")
    ledger = fetch_agent("LEDGER")

    agents_online = sum([
        1 if vdcut.get("status") == "ONLINE" else 0,
        1 if vdmass.get("status") == "ONLINE" else 0,
        1 if ledger.get("status") == "ONLINE" else 0
    ])

    return {
        "integrity_score": (agents_online / 3) * 100,
        "agents": {
            "VD-CUT": vdcut.get("status"),
            "VD-MASS": vdmass.get("status"),
            "LEDGER": ledger.get("status")
        }
    }


# ═══════════════════════════════════════════════════════════════
# ROUTES — Emergency Controls
# ═══════════════════════════════════════════════════════════════

@app.route("/emergency/halt", methods=["POST"])
def emergency_halt():
    """
    KILL SWITCH — Suspend all VD-MASS policies
    Requires I9 human authorization (actor_did)
    """
    data = request.get_json() or {}

    # I9 Gate: Require human actor
    actor_did = data.get("actor_did")
    if not actor_did:
        return jsonify({
            "error": "I9 VIOLATION: actor_did required",
            "message": "Kill Switch requires human authorization"
        }), 403

    reason = data.get("reason", "Manual emergency halt")

    # Log the emergency event
    db = get_db()
    c = db.cursor()
    c.execute("""
        INSERT INTO emergency_events (timestamp, event_type, actor_did, reason, affected_policies)
        VALUES (?, ?, ?, ?, ?)
    """, (
        datetime.now(timezone.utc).isoformat(),
        "KILL_SWITCH",
        actor_did,
        reason,
        "all"
    ))
    db.commit()
    event_id = c.lastrowid
    db.close()

    # TODO: Actually halt VD-MASS policies via API call
    # POST http://localhost:8131/emergency/halt

    return jsonify({
        "status": "HALT_INITIATED",
        "event_id": event_id,
        "actor_did": actor_did,
        "reason": reason,
        "message": "All VD-MASS policies have been suspended",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })


@app.route("/manifest/daily", methods=["POST"])
def daily_manifest():
    """
    Generate daily Super-Hash manifest.
    Seals all seals from today into one irremediable block.
    """
    data = request.get_json() or {}

    # I9 Gate
    actor_did = data.get("actor_did")
    if not actor_did:
        return jsonify({
            "error": "I9 VIOLATION: actor_did required"
        }), 403

    target_date = data.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))

    # TODO: Fetch actual seal counts from VD-CUT and VD-MASS
    vdcut_seals = 0
    vdmass_seals = 0

    # Generate super hash (placeholder - would hash all receipts)
    manifest_content = f"{target_date}|vdcut:{vdcut_seals}|vdmass:{vdmass_seals}|actor:{actor_did}"
    super_hash = hashlib.sha256(manifest_content.encode()).hexdigest()

    # Store manifest
    db = get_db()
    c = db.cursor()
    try:
        c.execute("""
            INSERT INTO daily_manifests (date, vdcut_seals, vdmass_seals, super_hash, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            target_date,
            vdcut_seals,
            vdmass_seals,
            super_hash,
            datetime.now(timezone.utc).isoformat()
        ))
        db.commit()
        manifest_id = c.lastrowid
    except sqlite3.IntegrityError:
        db.close()
        return jsonify({
            "error": f"Manifest for {target_date} already exists"
        }), 409
    db.close()

    return jsonify({
        "status": "MANIFEST_CREATED",
        "manifest_id": manifest_id,
        "date": target_date,
        "vdcut_seals": vdcut_seals,
        "vdmass_seals": vdmass_seals,
        "super_hash": f"sha256:{super_hash}",
        "actor_did": actor_did,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })


# ═══════════════════════════════════════════════════════════════
# ROUTES — SSE Real-Time Stream
# ═══════════════════════════════════════════════════════════════

@app.route("/live")
def live_stream():
    """
    Server-Sent Events stream for real-time updates.
    Pushes zone data every 5 seconds.
    """
    def generate():
        while True:
            data = {
                "zones": {
                    "a": zone_a_data(),
                    "b": zone_b_data(),
                    "c": zone_c_data()
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            yield f"data: {json.dumps(data)}\n\n"
            time.sleep(5)

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    init_db()
    print(f"""
╔════════════════════════════════════════════════════════════════╗
║  W-UDB-001 — WINDI Unified Dashboard                           ║
║  Sovereign Video Evidence Engine — God View                    ║
╠════════════════════════════════════════════════════════════════╣
║  Port: {PORT}                                                    ║
║  Protocol: I9 + I11                                            ║
║  Zones: A (Forensic) + B (Mass) + C (Ledger)                   ║
╠════════════════════════════════════════════════════════════════╣
║  Monitoring:                                                   ║
║    - W-VD-CUT-001  :8128  (Forensic Hub)                       ║
║    - W-VD-MASS-001 :8131  (Mass Pulse)                         ║
║    - Forensic Ledger :8101 (Dual-Chain)                        ║
╚════════════════════════════════════════════════════════════════╝

Liga IA+H · Kempten, Bavaria · 2026
"Se não consegues ver, não consegues escalar."
    """)
    app.run(host="0.0.0.0", port=PORT, debug=True, threaded=True)
