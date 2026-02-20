#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════
 WINDI Sentinel Bridge API v1.0
 Port: 8098
 Purpose: Ponte entre o Sentinel Daemon e o Meisterwerk Dashboard
 
 "O Sentinel observa. A Bridge traduz. O Ministro decide."
 
 Architecture:
   sentinel.py (daemon) → writes state → /opt/windi/data/sentinel_state.json
   sentinel_bridge.py (API) → reads state → serves JSON via HTTP
   Meisterwerk Dashboard → fetches /sentinel/api/status → renders SovereignPulse
   
 Deployment:
   Port 8098 | systemd: windi-sentinel-bridge
   nginx: /sentinel/ → http://127.0.0.1:8098/
═══════════════════════════════════════════════════════════════
"""

import json
import os
import time
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from flask import Flask, jsonify, Response
from functools import wraps

# ─── Configuration ────────────────────────────────────────────

APP_NAME = "WINDI Sentinel Bridge"
VERSION = "1.0.0"
PORT = 8098

# Sentinel writes its state here (updated every cycle ~78ms, but we read on demand)
SENTINEL_STATE_FILE = "/opt/windi/data/sentinel_state.json"
SENTINEL_HISTORY_FILE = "/opt/windi/data/sentinel_history.json"
SENTINEL_INCIDENTS_FILE = "/opt/windi/data/sentinel_incidents.json"

# Fallback: if Sentinel hasn't written state yet, probe services directly
SERVICE_PROBES = {
    "governance":  {"port": 8080, "path": "/health",     "critical": True},
    "babel":       {"port": 8085, "path": "/health",     "critical": True},
    "cortex":      {"port": 8089, "path": "/health",     "critical": False},
    "warroom":     {"port": 8090, "path": "/war-room/",  "critical": False},
    "clone":       {"port": 8092, "path": "/health",     "critical": False},
    "forensic":    {"port": 8094, "path": "/health",     "critical": False},
    "bridge":      {"port": 8097, "path": "/health",     "critical": True},
    "brain":       {"port": None, "systemd": "windi-brain",       "critical": False},
    "sentinel":    {"port": None, "systemd": "windi-sentinel",    "critical": True},
}

# Escalation thresholds (mirrors Sentinel daemon config)
ESCALATION_RULES = {
    "NOMINAL":  {"max_degraded": 0, "max_warning": 0, "max_critical": 0},
    "DEGRADED": {"max_degraded": 2, "max_warning": 0, "max_critical": 0},
    "WARNING":  {"max_degraded": 99, "max_warning": 2, "max_critical": 0},
    "CRITICAL": {"max_degraded": 99, "max_warning": 99, "max_critical": 1},
}

# ─── Flask App ────────────────────────────────────────────────

app = Flask(__name__)


def cors_headers(f):
    """Add CORS headers for dashboard consumption."""
    @wraps(f)
    def decorated(*args, **kwargs):
        response = f(*args, **kwargs)
        if isinstance(response, Response):
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response
    return decorated


# ─── State Reading ────────────────────────────────────────────


def normalize_sentinel_state(raw_state):
    """
    Normalize actual Sentinel daemon output to Bridge expected format.
    Sentinel writes: {services: {"windi-governance": {last_status, current_level, ...}}, ...}
    Bridge expects:  {status, services: {"governance": {status, port, critical, ...}}, summary, ...}
    """
    services = raw_state.get('services', {})
    
    # Known service metadata
    svc_meta = {
        "windi-governance": {"port": 8080, "critical": True, "name": "governance"},
        "windi-babel":      {"port": 8085, "critical": True, "name": "babel"},
        "windi-landing":    {"port": 8086, "critical": False, "name": "landing"},
        "windi-cortex":     {"port": 8089, "critical": False, "name": "cortex"},
        "windi-warroom":    {"port": 8090, "critical": False, "name": "warroom"},
        "windi-clone":      {"port": 8092, "critical": False, "name": "clone"},
        "windi-bridge":     {"port": 8097, "critical": True, "name": "bridge"},
        "windi-brain":      {"port": None, "critical": False, "name": "brain"},
        "windi-gateway":    {"port": None, "critical": True, "name": "gateway"},
    }
    
    normalized_services = {}
    for svc_id, svc_data in services.items():
        meta = svc_meta.get(svc_id, {"port": None, "critical": False, "name": svc_id.replace("windi-", "")})
        status = svc_data.get("last_status", "unknown")
        level = svc_data.get("current_level", "UNKNOWN")
        
        # Map current_level to status if last_status is missing
        if status == "unknown" and level:
            status = {"OK": "healthy", "DEGRADED": "degraded", "WARNING": "warning", "CRITICAL": "critical"}.get(level, "unknown")
        
        normalized_services[meta["name"]] = {
            "id": meta["name"],
            "status": status,
            "latency_ms": None,  # Sentinel doesn't track latency per-service yet
            "port": meta["port"],
            "critical": meta["critical"],
            "checked_at": svc_data.get("last_checked"),
            "consecutive_ok": svc_data.get("consecutive_successes", 0),
            "consecutive_fail": svc_data.get("consecutive_failures", 0),
            "total_checks": svc_data.get("total_checks", 0),
        }
    
    # Calculate summary
    all_statuses = [s["status"] for s in normalized_services.values()]
    healthy = all_statuses.count("healthy")
    degraded = all_statuses.count("degraded")
    warning = all_statuses.count("warning")
    critical = all_statuses.count("critical")
    total = len(all_statuses)
    
    # Overall status
    if critical > 0:
        overall = "CRITICAL"
    elif warning > 0:
        overall = "WARNING"
    elif degraded > 0:
        overall = "DEGRADED"
    else:
        overall = "NOMINAL"
    
    return {
        "status": overall,
        "services": normalized_services,
        "summary": {
            "total": total,
            "healthy": healthy,
            "degraded": degraded,
            "warning": warning,
            "critical": critical,
            "avg_latency_ms": 0,
        },
        "timestamp": raw_state.get("last_check", raw_state.get("started_at")),
        "cycle_ms": raw_state.get("cycle_ms"),
        "total_checks": raw_state.get("total_checks", 0),
        "started_at": raw_state.get("started_at"),
    }

def read_sentinel_state():
    """
    Read current Sentinel state from the daemon's state file.
    Falls back to direct probing if state file is stale or missing.
    """
    state = None
    source = "unknown"
    
    # Try reading Sentinel's own state file first
    if os.path.exists(SENTINEL_STATE_FILE):
        try:
            with open(SENTINEL_STATE_FILE, 'r') as f:
                state = json.load(f)
            
            # Check if state is fresh (less than 120 seconds old)
            if 'timestamp' in state:
                state_time = datetime.fromisoformat(state['timestamp'])
                age = (datetime.now(timezone.utc) - state_time).total_seconds()
                if age < 120:
                    source = "sentinel_daemon"
                else:
                    state = None  # Stale, fall back to probing
                    source = "probe_fallback"
        except (json.JSONDecodeError, KeyError, ValueError):
            state = None
            source = "probe_fallback"
    
    # Fallback: probe services directly
    if state is None:
        state = probe_services_directly()
        source = "direct_probe"
    
    # Normalize if this is raw Sentinel daemon format
    if 'status' not in state and 'services' in state:
        svc_sample = next(iter(state.get('services', {}).values()), {})
        if isinstance(svc_sample, dict) and 'current_level' in svc_sample:
            state = normalize_sentinel_state(state)
            source = "sentinel_daemon_normalized"
    
    state['_source'] = source
    state['_bridge_version'] = VERSION
    state['_served_at'] = datetime.now(timezone.utc).isoformat()
    
    return state


def probe_services_directly():
    """
    Direct service probing when Sentinel state file is unavailable.
    This is the fallback — the Sentinel daemon is the authoritative source.
    """
    import subprocess
    import socket
    
    services = {}
    
    for name, config in SERVICE_PROBES.items():
        svc = {
            "id": name,
            "status": "unknown",
            "latency_ms": None,
            "port": config.get("port"),
            "critical": config.get("critical", False),
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }
        
        if config.get("port"):
            # TCP probe
            start = time.time()
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex(('127.0.0.1', config['port']))
                elapsed = (time.time() - start) * 1000
                sock.close()
                
                if result == 0:
                    svc['status'] = 'healthy'
                    svc['latency_ms'] = round(elapsed, 1)
                    
                    # Check for degraded (high latency)
                    if elapsed > 200:
                        svc['status'] = 'degraded'
                    elif elapsed > 1000:
                        svc['status'] = 'warning'
                else:
                    svc['status'] = 'critical'
                    svc['latency_ms'] = None
            except Exception:
                svc['status'] = 'critical'
                svc['latency_ms'] = None
        
        elif config.get("systemd"):
            # systemd unit check
            try:
                result = subprocess.run(
                    ['systemctl', 'is-active', config['systemd']],
                    capture_output=True, text=True, timeout=5
                )
                if result.stdout.strip() == 'active':
                    svc['status'] = 'healthy'
                    svc['latency_ms'] = 0
                else:
                    svc['status'] = 'critical'
            except Exception:
                svc['status'] = 'unknown'
        
        services[name] = svc
    
    # Calculate overall state
    statuses = [s['status'] for s in services.values()]
    critical_count = statuses.count('critical')
    warning_count = statuses.count('warning')
    degraded_count = statuses.count('degraded')
    healthy_count = statuses.count('healthy')
    total = len(statuses)
    
    # Determine escalation level
    if critical_count > 0:
        overall = "CRITICAL"
    elif warning_count > 0:
        overall = "WARNING"
    elif degraded_count > 0:
        overall = "DEGRADED"
    else:
        overall = "NOMINAL"
    
    avg_latency = 0
    latencies = [s['latency_ms'] for s in services.values() if s['latency_ms'] is not None]
    if latencies:
        avg_latency = round(sum(latencies) / len(latencies), 1)
    
    return {
        "status": overall,
        "services": services,
        "summary": {
            "total": total,
            "healthy": healthy_count,
            "degraded": degraded_count,
            "warning": warning_count,
            "critical": critical_count,
            "avg_latency_ms": avg_latency,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cycle_ms": None,  # Only Sentinel daemon knows this
    }


def read_incidents():
    """Read recent incidents from Sentinel's incident log."""
    if os.path.exists(SENTINEL_INCIDENTS_FILE):
        try:
            with open(SENTINEL_INCIDENTS_FILE, 'r') as f:
                incidents = json.load(f)
            # Return last 20 incidents
            return incidents[-20:] if isinstance(incidents, list) else []
        except (json.JSONDecodeError, KeyError):
            return []
    return []


def read_history():
    """Read health history for timeline visualization."""
    if os.path.exists(SENTINEL_HISTORY_FILE):
        try:
            with open(SENTINEL_HISTORY_FILE, 'r') as f:
                history = json.load(f)
            # Return last 100 data points
            return history[-100:] if isinstance(history, list) else []
        except (json.JSONDecodeError, KeyError):
            return []
    return []


# ─── Minister Abstraction Layer ───────────────────────────────

def abstract_for_minister(state):
    """
    Translate raw Sentinel state into Minister-level abstraction.
    The Minister never sees ports, latencies, or technical details.
    He sees: impact, decisions affected, and recommended actions.
    
    "O Ministro não precisa saber que o porto 8080 caiu.
     Ele precisa saber que 3 decisões estão bloqueadas."
    """
    status = state.get('status', 'NOMINAL')
    summary = state.get('summary', {})
    services = state.get('services', {})
    
    # Determine which critical services are down
    critical_down = []
    for name, svc in services.items():
        if isinstance(svc, dict) and svc.get('critical') and svc.get('status') in ('critical', 'warning'):
            critical_down.append(name)
    
    # Minister-level translation
    minister = {
        "pulse": _minister_pulse(status),
        "label": _minister_label(status),
        "message": _minister_message(status, critical_down),
        "feeling": _minister_feeling(status),
        "action_required": status in ("WARNING", "CRITICAL"),
        "decisions_affected": _decisions_affected(status, critical_down),
        "confidence": _governance_confidence(summary),
        "timestamp": state.get('timestamp'),
    }
    
    return minister


def _minister_pulse(status):
    """Pulse color for the SovereignPulse component."""
    return {
        "NOMINAL": "green",
        "DEGRADED": "gold", 
        "WARNING": "amber",
        "CRITICAL": "red",
    }.get(status, "gray")


def _minister_label(status):
    """German label for the Minister."""
    return {
        "NOMINAL": "STABIL",
        "DEGRADED": "BEOBACHTUNG",
        "WARNING": "AUFMERKSAMKEIT",
        "CRITICAL": "HANDLUNG ERFORDERLICH",
    }.get(status, "UNBEKANNT")


def _minister_message(status, critical_down):
    """Human-readable message — no technical jargon."""
    if status == "NOMINAL":
        return "Alle Systeme arbeiten einwandfrei. Volle Entscheidungsfähigkeit."
    elif status == "DEGRADED":
        return "Ein Dienst zeigt leichte Verzögerung. Kein Einfluss auf Ihre Entscheidungen."
    elif status == "WARNING":
        return "Erhöhte Aufmerksamkeit. Architektur-Team beobachtet aktiv. Entscheidungsfähigkeit erhalten."
    elif status == "CRITICAL":
        if "governance" in critical_down:
            return "Governance-Pipeline unterbrochen. Einige Entscheidungen können offline bestätigt werden. Wiederherstellung läuft."
        else:
            services_de = ", ".join(critical_down)
            return f"Systemkomponente betroffen ({services_de}). Architektur-Team arbeitet an Wiederherstellung."
    return "Systemstatus wird ermittelt."


def _minister_feeling(status):
    """What the Minister should feel — emotional engineering."""
    return {
        "NOMINAL": "Orientiert. Ruhig. Souverän.",
        "DEGRADED": "Informiert. Keine Handlung nötig.",
        "WARNING": "Aufmerksam. Entscheidungsfähig.",
        "CRITICAL": "Ernst. Fokussiert. Handlungsbereit.",
    }.get(status, "Abwartend.")


def _decisions_affected(status, critical_down):
    """How many decisions are impacted — this is what matters to the Minister."""
    if status in ("NOMINAL", "DEGRADED"):
        return {"blocked": 0, "delayed": 0, "available": "all"}
    elif status == "WARNING":
        return {"blocked": 0, "delayed": 1, "available": "most"}
    elif status == "CRITICAL":
        if "governance" in critical_down:
            return {"blocked": 1, "delayed": 2, "available": "limited"}
        return {"blocked": 0, "delayed": 1, "available": "most"}
    return {"blocked": 0, "delayed": 0, "available": "unknown"}


def _governance_confidence(summary):
    """Governance confidence percentage for the integrity gauge."""
    total = summary.get('total', 9)
    healthy = summary.get('healthy', 0)
    critical = summary.get('critical', 0)
    
    if total == 0:
        return 0
    
    base = (healthy / total) * 100
    # Critical services have outsized impact on confidence
    penalty = critical * 5
    
    return max(0, min(100, round(base - penalty)))


# ─── API Routes ───────────────────────────────────────────────

@app.route('/health')
@cors_headers
def health():
    """Health check for this bridge service."""
    return jsonify({
        "service": APP_NAME,
        "version": VERSION,
        "status": "healthy",
        "port": PORT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "principle": "KI verarbeitet. Mensch entscheidet. WINDI garantiert.",
    })


@app.route('/api/status')
@cors_headers
def get_status():
    """
    Full Sentinel status — for Architektur and Operation layers.
    Returns raw service data with technical details.
    """
    state = read_sentinel_state()
    return jsonify(state)


@app.route('/api/minister')
@cors_headers
def get_minister_view():
    """
    Minister-abstracted view — no technical details.
    This is what the SovereignPulse component consumes.
    
    The Minister sees impact, not implementation.
    """
    state = read_sentinel_state()
    minister = abstract_for_minister(state)
    return jsonify(minister)


@app.route('/api/services')
@cors_headers
def get_services():
    """Individual service details — for Architektur layer."""
    state = read_sentinel_state()
    services = state.get('services', {})
    return jsonify({
        "services": services,
        "summary": state.get('summary', {}),
        "timestamp": state.get('timestamp'),
    })


@app.route('/api/incidents')
@cors_headers
def get_incidents():
    """Recent incidents — for Architektur and Operation layers."""
    incidents = read_incidents()
    return jsonify({
        "incidents": incidents,
        "count": len(incidents),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@app.route('/api/history')
@cors_headers
def get_history():
    """Health history for pulse visualization."""
    history = read_history()
    return jsonify({
        "history": history,
        "count": len(history),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@app.route('/api/escalation')
@cors_headers
def get_escalation():
    """
    Current escalation state with timeline.
    Combines current status with recent history to show progression.
    """
    state = read_sentinel_state()
    incidents = read_incidents()
    
    # Build escalation timeline from recent incidents
    timeline = []
    for inc in incidents[-10:]:
        timeline.append({
            "timestamp": inc.get('timestamp'),
            "from_status": inc.get('from_status'),
            "to_status": inc.get('to_status'),
            "trigger": inc.get('trigger'),
            "service": inc.get('service'),
        })
    
    return jsonify({
        "current_status": state.get('status', 'NOMINAL'),
        "timeline": timeline,
        "minister_view": abstract_for_minister(state),
        "summary": state.get('summary', {}),
        "timestamp": state.get('timestamp'),
    })


# ─── Foundation B2 Integration ────────────────────────────────

@app.route('/api/foundation')
@cors_headers
def get_foundation():
    """
    Foundation B2 status — the cryptographic identity.
    Read from the sealed foundation record.
    """
    foundation_file = "/opt/windi/data/foundation_b2.json"
    
    if os.path.exists(foundation_file):
        try:
            with open(foundation_file, 'r') as f:
                foundation = json.load(f)
            return jsonify({
                "sealed": True,
                "record": foundation,
                "integrity": "VERIFIED",
            })
        except Exception:
            pass
    
    return jsonify({
        "sealed": False,
        "record": None,
        "integrity": "UNKNOWN",
    })


# ─── Entry Point ──────────────────────────────────────────────

if __name__ == '__main__':
    print(f"""
╔══════════════════════════════════════════════════════╗
║  {APP_NAME} v{VERSION}                          ║
║  Port: {PORT}                                        ║
║  "O Sentinel observa. A Bridge traduz."              ║
║  Endpoints:                                          ║
║    /health          — Bridge health check            ║
║    /api/status      — Full Sentinel state             ║
║    /api/minister    — Minister-abstracted view        ║
║    /api/services    — Individual service details      ║
║    /api/incidents   — Recent incidents                ║
║    /api/history     — Health history for pulse         ║
║    /api/escalation  — Escalation timeline             ║
║    /api/foundation  — Foundation B2 status            ║
╚══════════════════════════════════════════════════════╝
    """)
    app.run(host='0.0.0.0', port=PORT, debug=False)
