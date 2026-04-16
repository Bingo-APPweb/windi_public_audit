"""
W-SERVICE-CONTROL — WINDI Service Control Panel
Sovereign Service Management with I9 Human Gate

Port: 8170
Invariants: I1, I9, I11

Liga IA+H · Kempten, Bavaria · 2026
"""

import subprocess
import json
import hashlib
import requests
from datetime import datetime, timezone
from flask import Flask, jsonify, request, render_template_string
from functools import wraps

app = Flask(__name__)

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

PORT = 8170
VERSION = "1.0.0"
LEDGER_URL = "http://localhost:8101"

# Services to monitor (systemd service names)
WINDI_SERVICES = [
    # Core Infrastructure
    {"name": "windi-suite-docs", "port": 8101, "display": "Forensic Ledger", "category": "core", "sealed": True, "url": "/ledger/"},
    {"name": "windi-dragon-chat", "port": 8108, "display": "Dragon Hub", "category": "core", "url": "/desktop/"},
    {"name": "windi-desktop-gen7", "port": 8119, "display": "Desktop GEN7", "category": "core", "url": "/desktop/"},
    {"name": "windi-governance", "port": 8080, "display": "Governance API", "category": "core", "url": "/governance/"},

    # Agents
    {"name": "windi-law", "port": 8122, "display": "WINDI-LAW", "category": "agents", "sealed": True, "url": "/law/"},
    {"name": "windi-travel", "port": 8126, "display": "WINDI Travel", "category": "agents", "url": "/travel/"},
    {"name": "windi-nomad-bot", "port": 8127, "display": "W-NOMAD-001", "category": "agents", "url": "https://t.me/windi_nomad_bot"},
    {"name": "windi-vd-cut", "port": 8128, "display": "W-VD-CUT-001", "category": "agents", "url": "/vdcut-dash/"},
    {"name": "windi-joe", "port": 8129, "display": "W-JOE-001", "category": "agents", "url": "/joe-dash/"},
    {"name": "windi-vd-mass", "port": 8131, "display": "W-VD-MASS-001", "category": "agents", "url": "/vdmass-dash/"},
    {"name": "windi-jmpg", "port": 8132, "display": "W-JMPG-001", "category": "agents", "url": "/comm/"},

    # Dashboards
    {"name": "windi-udb", "port": 8140, "display": "UDB God View", "category": "dashboards", "nohup": True, "url": "/udb/"},
    {"name": "windi-intent-cmd", "port": 8141, "display": "W-INTENT-CMD", "category": "dashboards", "url": "/intent/"},
    {"name": "windi-fediverse", "port": 8142, "display": "W-FEDIVERSE-001", "category": "dashboards", "url": "/fediverse/"},
    {"name": "windi-bridge", "port": 8143, "display": "W-BRIDGE-001", "category": "dashboards", "url": "/watch/"},
    {"name": "windi-sec-001", "port": 8144, "display": "W-SEC-001", "category": "dashboards", "url": "/sec-dash/"},
    {"name": "windi-verify-public", "port": 8145, "display": "Verify Public", "category": "dashboards", "url": "/verify-public/"},
    {"name": "windi-enterprise", "port": 8150, "display": "W-Enterprise-001", "category": "dashboards", "url": "/enterprise/"},
    {"name": "windi-cache", "port": 8160, "display": "W-CACHE-001", "category": "dashboards", "nohup": True, "url": "/wcache/noir"},
    {"name": "windi-cost", "port": 8152, "display": "W-COST-001", "category": "dashboards", "nohup": True, "url": "/cost/"},
    {"name": "windi-lab", "port": 8151, "display": "W-LAB-001", "category": "dashboards", "url": "/lab/"},
    {"name": "windi-social", "port": 8133, "display": "W-SOCIAL-001", "category": "agents", "url": "/social/"},

    # Support
    {"name": "windi-leads", "port": 8096, "display": "DID Genesis", "category": "support", "url": "/genesis/"},
    {"name": "windi-wallet", "port": 8095, "display": "Wallet Service", "category": "support", "url": "/wallet/"},
    {"name": "windi-communique", "port": 8105, "display": "Communiqué Engine", "category": "support", "url": "/communique/"},
    {"name": "windi-dispatch", "port": 8106, "display": "Dispatch Gateway", "category": "support", "url": "/dispatch/"},

    # Special (nohup)
    {"name": "sandbox-core", "port": 8091, "display": "Sandbox Core", "category": "core", "nohup": True, "url": "/agents/"},
]

# Health check endpoints by port
HEALTH_ENDPOINTS = {
    8091: "/health",
    8096: "/health",
    8101: "/health",
    8108: "/health",
    8119: "/health",
    8122: "/health",
    8126: "/health",
    8127: "/health",
    8128: "/vd-cut/health",
    8129: "/health",
    8131: "/health",
    8132: "/health",
    8140: "/health",
    8141: "/health",
    8142: "/health",
    8143: "/health",
    8144: "/health",
    8145: "/health",
    8150: "/health",
    8160: "/health",
    8152: "/health",
    8151: "/health",
    8133: "/health",
}

# ═══════════════════════════════════════════════════════════════
# SUBSYSTEMS — Module-level Health Monitoring (SVG Sentinel)
# ═══════════════════════════════════════════════════════════════

SUBSYSTEMS = {
    "windi-law": [
        {
            "id": "ai-draft",
            "display": "AI Draft",
            "endpoint": "/ai-draft/health",
            "port": 8122,
            "critical": True,
            "description": "LLM document generation"
        },
        {
            "id": "identity-gate",
            "display": "Identity Gate",
            "endpoint": "/health",
            "port": 8122,
            "critical": True,
            "description": "DID authentication"
        },
        {
            "id": "dragon-law",
            "display": "Dragon Law",
            "endpoint": "/dragon/health",
            "port": 8122,
            "critical": False,
            "description": "Dragon Shadow Forest integration"
        }
    ],
    "windi-travel": [
        {
            "id": "identity-gate",
            "display": "Identity Gate",
            "endpoint": "/health",
            "port": 8126,
            "critical": True,
            "description": "DID wallet authentication"
        },
        {
            "id": "workspace",
            "display": "Workspace",
            "endpoint": "/workspace/",
            "port": 8126,
            "critical": True,
            "description": "Travel workspace UI"
        }
    ],
    "windi-lab": [
        {
            "id": "clear",
            "display": "Dilemas de Geleia",
            "endpoint": "/api/clear/stats",
            "port": 8151,
            "critical": False,
            "description": "Cognitive training module"
        }
    ]
}

# ═══════════════════════════════════════════════════════════════
# I9 GATE — Human Approval Required
# ═══════════════════════════════════════════════════════════════

def require_i9_gate(f):
    """Decorator requiring human DID for service control actions."""
    @wraps(f)
    def decorated(*args, **kwargs):
        data = request.get_json() or {}
        actor_did = data.get("actor_did")

        if not actor_did:
            return jsonify({
                "error": "I9_VIOLATION",
                "message": "Human approval required. Provide actor_did.",
                "invariant": "I9"
            }), 403

        # Validate DID format
        if not actor_did.startswith("did:windi:"):
            return jsonify({
                "error": "INVALID_DID",
                "message": "DID must start with did:windi:",
                "invariant": "I9"
            }), 400

        return f(*args, **kwargs)
    return decorated

# ═══════════════════════════════════════════════════════════════
# SERVICE STATUS FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def get_systemd_status(service_name):
    """Get systemd service status."""
    try:
        result = subprocess.run(
            ["systemctl", "is-active", service_name],
            capture_output=True, text=True, timeout=5
        )
        status = result.stdout.strip()
        return status if status else "unknown"
    except Exception as e:
        return "error"

def get_port_status(port):
    """Check if port is listening."""
    try:
        result = subprocess.run(
            ["ss", "-tlnp"],
            capture_output=True, text=True, timeout=5
        )
        return f":{port}" in result.stdout
    except:
        return False

def check_health_endpoint(port):
    """Check service health endpoint."""
    endpoint = HEALTH_ENDPOINTS.get(port, "/health")
    try:
        r = requests.get(f"http://localhost:{port}{endpoint}", timeout=2)
        if r.status_code == 200:
            return {"status": "healthy", "data": r.json() if r.headers.get('content-type', '').startswith('application/json') else {}}
        return {"status": "unhealthy", "code": r.status_code}
    except requests.exceptions.ConnectionError:
        return {"status": "offline", "error": "connection_refused"}
    except Exception as e:
        return {"status": "error", "error": str(e)[:50]}

def get_full_service_status(service):
    """Get comprehensive status for a service."""
    name = service["name"]
    port = service.get("port")
    is_nohup = service.get("nohup", False)

    # Systemd status (skip for nohup services)
    if is_nohup:
        systemd = "nohup"
    else:
        systemd = get_systemd_status(name)

    # Port status
    port_active = get_port_status(port) if port else False

    # Health check
    health = check_health_endpoint(port) if port and port_active else {"status": "offline"}

    # Determine overall status
    if health["status"] == "healthy":
        overall = "online"
    elif port_active:
        overall = "degraded"
    elif systemd == "active" or systemd == "nohup":
        overall = "starting"
    else:
        overall = "offline"

    # Check for subsystems
    has_subsystems = name in SUBSYSTEMS

    return {
        "service": name,
        "display": service["display"],
        "port": port,
        "category": service.get("category", "other"),
        "sealed": service.get("sealed", False),
        "nohup": is_nohup,
        "url": service.get("url", ""),
        "systemd": systemd,
        "port_active": port_active,
        "health": health,
        "overall": overall,
        "has_subsystems": has_subsystems,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# ═══════════════════════════════════════════════════════════════
# SUBSYSTEM HEALTH FUNCTIONS (SVG Sentinel)
# ═══════════════════════════════════════════════════════════════

def check_subsystem_health(service_name, subsystem):
    """Check health of a specific subsystem module."""
    port = subsystem["port"]
    endpoint = subsystem["endpoint"]

    try:
        r = requests.get(f"http://localhost:{port}{endpoint}", timeout=3, allow_redirects=False)
        # 200-399 = healthy (includes redirects and auth challenges)
        if 200 <= r.status_code < 400:
            return {
                "id": subsystem["id"],
                "display": subsystem["display"],
                "status": "online",
                "critical": subsystem.get("critical", False),
                "description": subsystem.get("description", ""),
                "response_time_ms": r.elapsed.total_seconds() * 1000
            }
        return {
            "id": subsystem["id"],
            "display": subsystem["display"],
            "status": "degraded",
            "critical": subsystem.get("critical", False),
            "description": subsystem.get("description", ""),
            "status_code": r.status_code
        }
    except requests.exceptions.ConnectionError:
        return {
            "id": subsystem["id"],
            "display": subsystem["display"],
            "status": "offline",
            "critical": subsystem.get("critical", False),
            "description": subsystem.get("description", ""),
            "error": "connection_refused"
        }
    except requests.exceptions.Timeout:
        return {
            "id": subsystem["id"],
            "display": subsystem["display"],
            "status": "blocked",
            "critical": subsystem.get("critical", False),
            "description": subsystem.get("description", ""),
            "error": "timeout"
        }
    except Exception as e:
        return {
            "id": subsystem["id"],
            "display": subsystem["display"],
            "status": "error",
            "critical": subsystem.get("critical", False),
            "description": subsystem.get("description", ""),
            "error": str(e)[:50]
        }

def get_all_subsystems_status(service_name):
    """Get status of all subsystems for a service."""
    if service_name not in SUBSYSTEMS:
        return {"service": service_name, "subsystems": [], "has_critical_failure": False}

    subsystems = []
    has_critical_failure = False

    for sub in SUBSYSTEMS[service_name]:
        status = check_subsystem_health(service_name, sub)
        subsystems.append(status)

        # Track critical failures
        if status["critical"] and status["status"] not in ["online"]:
            has_critical_failure = True

    return {
        "service": service_name,
        "subsystems": subsystems,
        "has_critical_failure": has_critical_failure,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# ═══════════════════════════════════════════════════════════════
# LEDGER INTEGRATION (I11)
# ═══════════════════════════════════════════════════════════════

def seal_action(action, service_name, actor_did, result):
    """Seal service control action to Forensic Ledger."""
    receipt = {
        "receipt_id": f"WINDI-SVC-{datetime.now().strftime('%Y%m%d%H%M%S')}-{hashlib.sha256(f'{action}{service_name}{actor_did}'.encode()).hexdigest()[:8].upper()}",
        "actor": actor_did,
        "app": "service-control",
        "doc_name": f"Service {action}: {service_name}",
        "doc_type": "service-action",
        "governance_level": "HIGH",
        "content_hash": f"sha256:{hashlib.sha256(json.dumps(result, sort_keys=True).encode()).hexdigest()}",
        "invariants": ["I9", "I11"],
        "stage": "C6",
        "sealed_at": datetime.now(timezone.utc).isoformat()
    }

    try:
        r = requests.post(f"{LEDGER_URL}/api/receipts", json=receipt, timeout=5)
        return receipt["receipt_id"] if r.status_code in [200, 201] else None
    except:
        return None

# ═══════════════════════════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@app.route("/health")
def health():
    return jsonify({
        "service": "W-SERVICE-CONTROL",
        "version": VERSION,
        "port": PORT,
        "status": "ONLINE",
        "invariants": ["I1", "I9", "I11"],
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

@app.route("/api/services")
def list_services():
    """List all services with current status."""
    services = []

    for svc in WINDI_SERVICES:
        status = get_full_service_status(svc)
        services.append(status)

    # Count by status
    counts = {
        "online": len([s for s in services if s["overall"] == "online"]),
        "degraded": len([s for s in services if s["overall"] == "degraded"]),
        "starting": len([s for s in services if s["overall"] == "starting"]),
        "offline": len([s for s in services if s["overall"] == "offline"]),
        "total": len(services)
    }

    return jsonify({
        "services": services,
        "counts": counts,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

@app.route("/api/services/<service_name>")
def get_service(service_name):
    """Get single service status."""
    svc = next((s for s in WINDI_SERVICES if s["name"] == service_name), None)
    if not svc:
        return jsonify({"error": "Service not found"}), 404

    return jsonify(get_full_service_status(svc))

@app.route("/api/services/<service_name>/restart", methods=["POST"])
@require_i9_gate
def restart_service(service_name):
    """Restart a service (requires I9 human approval)."""
    data = request.get_json() or {}
    actor_did = data.get("actor_did")
    reason = data.get("reason", "Manual restart via Control Panel")

    # Find service
    svc = next((s for s in WINDI_SERVICES if s["name"] == service_name), None)
    if not svc:
        return jsonify({"error": "Service not found"}), 404

    # Check if sealed (protected)
    if svc.get("sealed"):
        return jsonify({
            "error": "SEALED_SERVICE",
            "message": f"{svc['display']} is a SEALED service. Restart requires additional approval.",
            "invariant": "G5"
        }), 403

    # Check if nohup (different restart method)
    if svc.get("nohup"):
        return jsonify({
            "error": "NOHUP_SERVICE",
            "message": f"{svc['display']} runs via nohup, not systemd. Manual restart required.",
            "suggestion": f"cd /opt/windi/{service_name.replace('windi-', '')} && ./start.sh"
        }), 400

    # Execute restart
    try:
        result = subprocess.run(
            ["sudo", "systemctl", "restart", service_name],
            capture_output=True, text=True, timeout=30
        )

        success = result.returncode == 0

        action_result = {
            "action": "restart",
            "service": service_name,
            "success": success,
            "actor_did": actor_did,
            "reason": reason,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # Seal to Ledger (I11)
        receipt_id = seal_action("RESTART", service_name, actor_did, action_result)
        action_result["receipt_id"] = receipt_id

        if success:
            return jsonify({
                "status": "RESTART_INITIATED",
                "service": service_name,
                "receipt_id": receipt_id,
                "message": f"{svc['display']} restart initiated successfully",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        else:
            return jsonify({
                "status": "RESTART_FAILED",
                "service": service_name,
                "error": result.stderr,
                "receipt_id": receipt_id
            }), 500

    except subprocess.TimeoutExpired:
        return jsonify({"error": "Restart timed out"}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/services/<service_name>/stop", methods=["POST"])
@require_i9_gate
def stop_service(service_name):
    """Stop a service (requires I9 human approval)."""
    data = request.get_json() or {}
    actor_did = data.get("actor_did")

    svc = next((s for s in WINDI_SERVICES if s["name"] == service_name), None)
    if not svc:
        return jsonify({"error": "Service not found"}), 404

    if svc.get("sealed"):
        return jsonify({
            "error": "SEALED_SERVICE",
            "message": f"{svc['display']} is SEALED. Cannot be stopped via Control Panel.",
            "invariant": "G5"
        }), 403

    try:
        result = subprocess.run(
            ["sudo", "systemctl", "stop", service_name],
            capture_output=True, text=True, timeout=30
        )

        receipt_id = seal_action("STOP", service_name, actor_did, {"success": result.returncode == 0})

        return jsonify({
            "status": "STOPPED" if result.returncode == 0 else "STOP_FAILED",
            "service": service_name,
            "receipt_id": receipt_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/services/<service_name>/start", methods=["POST"])
@require_i9_gate
def start_service(service_name):
    """Start a service (requires I9 human approval)."""
    data = request.get_json() or {}
    actor_did = data.get("actor_did")

    svc = next((s for s in WINDI_SERVICES if s["name"] == service_name), None)
    if not svc:
        return jsonify({"error": "Service not found"}), 404

    try:
        result = subprocess.run(
            ["sudo", "systemctl", "start", service_name],
            capture_output=True, text=True, timeout=30
        )

        receipt_id = seal_action("START", service_name, actor_did, {"success": result.returncode == 0})

        return jsonify({
            "status": "STARTED" if result.returncode == 0 else "START_FAILED",
            "service": service_name,
            "receipt_id": receipt_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/services/<service_name>/logs")
def get_logs(service_name):
    """Get recent logs for a service."""
    lines = request.args.get("lines", 50, type=int)

    svc = next((s for s in WINDI_SERVICES if s["name"] == service_name), None)
    if not svc:
        return jsonify({"error": "Service not found"}), 404

    try:
        result = subprocess.run(
            ["journalctl", "-u", service_name, "-n", str(min(lines, 200)), "--no-pager"],
            capture_output=True, text=True, timeout=10
        )

        return jsonify({
            "service": service_name,
            "logs": result.stdout,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ═══════════════════════════════════════════════════════════════
# SUBSYSTEM ENDPOINTS (SVG Sentinel API)
# ═══════════════════════════════════════════════════════════════

@app.route("/api/subsystems")
def list_all_subsystems():
    """List all services that have subsystems configured."""
    return jsonify({
        "services_with_subsystems": list(SUBSYSTEMS.keys()),
        "total_subsystems": sum(len(subs) for subs in SUBSYSTEMS.values()),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

@app.route("/api/subsystems/<service_name>")
def get_subsystems(service_name):
    """Get subsystem status for a specific service (SVG Sentinel)."""
    if service_name not in SUBSYSTEMS:
        return jsonify({
            "error": "NO_SUBSYSTEMS",
            "message": f"Service {service_name} has no subsystems configured",
            "available": list(SUBSYSTEMS.keys())
        }), 404

    return jsonify(get_all_subsystems_status(service_name))

@app.route("/api/subsystems/<service_name>/<subsystem_id>")
def get_single_subsystem(service_name, subsystem_id):
    """Get status of a specific subsystem module."""
    if service_name not in SUBSYSTEMS:
        return jsonify({"error": "Service not found"}), 404

    subsystem = next((s for s in SUBSYSTEMS[service_name] if s["id"] == subsystem_id), None)
    if not subsystem:
        return jsonify({"error": "Subsystem not found"}), 404

    return jsonify(check_subsystem_health(service_name, subsystem))

# ═══════════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════════

@app.route("/")
def dashboard():
    return render_template_string(DASHBOARD_HTML)

@app.route("/noir")
def dashboard_noir():
    return render_template_string(DASHBOARD_HTML)

@app.route("/did-architecture")
def did_architecture():
    """§173 DID Architecture Diagram Page"""
    try:
        with open("/opt/windi/service-control/static/did-architecture.html", "r") as f:
            return f.read()
    except Exception as e:
        return f"Error loading page: {e}", 500

# ═══════════════════════════════════════════════════════════════
# HTML TEMPLATE
# ═══════════════════════════════════════════════════════════════

DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="en" data-theme="noir">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WINDI Service Control Panel</title>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0A0A10;
            --bg-card: #12121A;
            --gold: #C9A84C;
            --gold-dim: #8B7424;
            --text: #E8E6E1;
            --text-dim: #9A9890;
            --border: #1A1A24;
            --green: #4ADE80;
            --red: #F87171;
            --yellow: #FACC15;
            --blue: #60A5FA;
        }
        [data-theme="klar"] {
            --bg: #FAFAF8;
            --bg-card: #FFFFFF;
            --gold: #8B7424;
            --gold-dim: #6B5A1C;
            --text: #1A1A1A;
            --text-dim: #5A5A5A;
            --border: #E0DED8;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'JetBrains Mono', monospace;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
        }
        .header {
            background: var(--bg-card);
            border-bottom: 1px solid var(--border);
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .logo { color: var(--gold); font-size: 1.5rem; font-weight: 700; }
        .logo-sub { color: var(--text-dim); font-weight: 400; font-size: 0.9rem; margin-left: 0.5rem; }
        .controls { display: flex; gap: 1rem; align-items: center; }
        .btn-theme {
            background: transparent;
            border: 1px solid var(--border);
            color: var(--gold);
            padding: 0.5rem;
            cursor: pointer;
            border-radius: 4px;
            font-size: 1.2rem;
        }
        select {
            background: var(--bg-card);
            border: 1px solid var(--border);
            color: var(--text);
            padding: 0.5rem;
            border-radius: 4px;
            font-family: inherit;
        }
        .main { padding: 2rem; max-width: 1600px; margin: 0 auto; }

        /* DID Banner */
        .did-banner {
            background: linear-gradient(135deg, var(--bg-card) 0%, rgba(201,168,76,0.1) 100%);
            border: 1px solid var(--gold-dim);
            border-radius: 8px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        .did-banner.connected { border-color: var(--green); }
        .did-input {
            flex: 1;
            background: var(--bg);
            border: 1px solid var(--border);
            color: var(--text);
            padding: 0.75rem 1rem;
            border-radius: 4px;
            font-family: inherit;
        }
        .btn-connect {
            background: var(--gold);
            color: var(--bg);
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 4px;
            cursor: pointer;
            font-weight: 600;
            font-family: inherit;
        }
        .btn-connect:hover { background: var(--gold-dim); }

        /* Stats */
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }
        .stat-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1rem;
            text-align: center;
        }
        .stat-value { font-size: 2rem; font-weight: 700; color: var(--gold); }
        .stat-label { color: var(--text-dim); font-size: 0.75rem; text-transform: uppercase; }
        .stat-card.online .stat-value { color: var(--green); }
        .stat-card.offline .stat-value { color: var(--red); }
        .stat-card.degraded .stat-value { color: var(--yellow); }

        /* Category */
        .category { margin-bottom: 2rem; }
        .category-title {
            color: var(--gold);
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid var(--border);
        }

        /* Service Grid */
        .services-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 1rem;
        }
        .service-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1rem;
            transition: border-color 0.2s;
        }
        .service-card:hover { border-color: var(--gold-dim); }
        .service-card.online { border-left: 3px solid var(--green); }
        .service-card.offline { border-left: 3px solid var(--red); }
        .service-card.degraded { border-left: 3px solid var(--yellow); }
        .service-card.starting { border-left: 3px solid var(--blue); }

        .service-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem; }
        .service-name { font-weight: 600; color: var(--text); }
        .service-port { color: var(--text-dim); font-size: 0.8rem; }
        .service-status {
            font-size: 0.7rem;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            text-transform: uppercase;
            font-weight: 600;
        }
        .service-status.online { background: rgba(74,222,128,0.2); color: var(--green); }
        .service-status.offline { background: rgba(248,113,113,0.2); color: var(--red); }
        .service-status.degraded { background: rgba(250,204,21,0.2); color: var(--yellow); }
        .service-status.starting { background: rgba(96,165,250,0.2); color: var(--blue); }

        .service-meta { display: flex; gap: 0.5rem; margin-bottom: 0.75rem; flex-wrap: wrap; }
        .badge {
            font-size: 0.65rem;
            padding: 0.2rem 0.4rem;
            border-radius: 3px;
            background: var(--border);
            color: var(--text-dim);
        }
        .badge.sealed { background: rgba(201,168,76,0.2); color: var(--gold); }
        .badge.nohup { background: rgba(96,165,250,0.2); color: var(--blue); }

        .service-actions { display: flex; gap: 0.5rem; margin-top: 0.75rem; }
        .btn-action {
            flex: 1;
            padding: 0.5rem;
            border: 1px solid var(--border);
            background: transparent;
            color: var(--text);
            border-radius: 4px;
            cursor: pointer;
            font-family: inherit;
            font-size: 0.75rem;
            transition: all 0.2s;
        }
        .btn-action:hover { border-color: var(--gold); color: var(--gold); }
        .btn-action:disabled { opacity: 0.5; cursor: not-allowed; }
        .btn-action.open { border-color: var(--blue); color: var(--blue); text-decoration: none; text-align: center; }
        .btn-action.open:hover { background: var(--blue); color: var(--bg); }
        .btn-action.restart:hover { border-color: var(--yellow); color: var(--yellow); }
        .btn-action.stop:hover { border-color: var(--red); color: var(--red); }
        .btn-action.start:hover { border-color: var(--green); color: var(--green); }

        /* Logs Modal */
        .modal {
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.8);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }
        .modal.active { display: flex; }
        .modal-content {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            width: 90%;
            max-width: 800px;
            max-height: 80vh;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }
        .modal-header {
            padding: 1rem;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .modal-title { color: var(--gold); font-weight: 600; }
        .modal-close {
            background: transparent;
            border: none;
            color: var(--text-dim);
            font-size: 1.5rem;
            cursor: pointer;
        }
        .modal-body {
            padding: 1rem;
            overflow-y: auto;
            flex: 1;
        }
        .logs-content {
            font-size: 0.75rem;
            line-height: 1.6;
            white-space: pre-wrap;
            word-break: break-all;
            color: var(--text-dim);
        }

        /* Toast */
        .toast {
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1rem 1.5rem;
            display: none;
            z-index: 1001;
        }
        .toast.success { border-color: var(--green); }
        .toast.error { border-color: var(--red); }
        .toast.active { display: block; }

        /* I18N */
        .i18n { display: none; }

        /* Loading */
        .loading { opacity: 0.5; pointer-events: none; }
        @keyframes spin { to { transform: rotate(360deg); } }
        .spinner { animation: spin 1s linear infinite; display: inline-block; }

        /* Subsystems (SVG Sentinel) */
        .subsystems {
            margin-top: 0.75rem;
            padding-top: 0.75rem;
            border-top: 1px dashed var(--border);
        }
        .subsystems-title {
            font-size: 0.65rem;
            color: var(--text-dim);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.5rem;
        }
        .subsystem-row {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.3rem 0;
        }
        .sentinel-svg {
            width: 16px;
            height: 16px;
            flex-shrink: 0;
        }
        .sentinel-svg.online { color: var(--green); }
        .sentinel-svg.offline { color: var(--red); }
        .sentinel-svg.degraded { color: var(--yellow); }
        .sentinel-svg.blocked { color: var(--red); animation: pulse 1.5s infinite; }
        .sentinel-svg.error { color: var(--red); }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.4; }
        }
        .subsystem-name {
            font-size: 0.75rem;
            color: var(--text);
            flex: 1;
        }
        .subsystem-name.critical::after {
            content: " ★";
            color: var(--gold);
        }
        .subsystem-status {
            font-size: 0.65rem;
            color: var(--text-dim);
        }
        .subsystem-expand {
            background: transparent;
            border: 1px solid var(--border);
            color: var(--text-dim);
            padding: 0.2rem 0.4rem;
            border-radius: 3px;
            font-size: 0.65rem;
            cursor: pointer;
        }
        .subsystem-expand:hover {
            border-color: var(--gold);
            color: var(--gold);
        }
        .subsystem-alert {
            background: rgba(248,113,113,0.1);
            border: 1px solid var(--red);
            border-radius: 4px;
            padding: 0.5rem;
            margin-top: 0.5rem;
            font-size: 0.7rem;
            color: var(--red);
        }
    </style>
</head>
<body>
    <header class="header">
        <div>
            <span class="logo">WINDI<span class="logo-sub">Service Control</span></span>
        </div>
        <div class="controls">
            <select id="lang-toggle" onchange="setLang(this.value)">
                <option value="de">DE</option>
                <option value="en" selected>EN</option>
                <option value="pt">PT</option>
            </select>
            <button class="btn-theme" onclick="toggleTheme()" title="Toggle Theme">☀</button>
        </div>
    </header>

    <main class="main">
        <!-- DID Banner -->
        <div class="did-banner" id="did-banner">
            <span>🪪</span>
            <input type="text" class="did-input" id="did-input" placeholder="did:windi:your-identifier" />
            <button class="btn-connect" onclick="connectDID()" data-i18n="connect">Connect</button>
        </div>

        <!-- Stats -->
        <div class="stats" id="stats">
            <div class="stat-card online">
                <div class="stat-value" id="stat-online">--</div>
                <div class="stat-label" data-i18n="online">Online</div>
            </div>
            <div class="stat-card degraded">
                <div class="stat-value" id="stat-degraded">--</div>
                <div class="stat-label" data-i18n="degraded">Degraded</div>
            </div>
            <div class="stat-card offline">
                <div class="stat-value" id="stat-offline">--</div>
                <div class="stat-label" data-i18n="offline">Offline</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="stat-total">--</div>
                <div class="stat-label" data-i18n="total">Total</div>
            </div>
        </div>

        <!-- Services by Category -->
        <div id="services-container"></div>
    </main>

    <!-- Logs Modal -->
    <div class="modal" id="logs-modal">
        <div class="modal-content">
            <div class="modal-header">
                <span class="modal-title" id="logs-title">Logs</span>
                <button class="modal-close" onclick="closeModal()">&times;</button>
            </div>
            <div class="modal-body">
                <pre class="logs-content" id="logs-content"></pre>
            </div>
        </div>
    </div>

    <!-- Toast -->
    <div class="toast" id="toast"></div>

    <script>
        // State
        let currentDID = null;
        let services = [];

        // I18N
        const i18n = {
            en: {
                connect: "Connect", disconnect: "Disconnect", online: "Online", offline: "Offline",
                degraded: "Degraded", total: "Total", restart: "Restart", stop: "Stop", start: "Start",
                logs: "Logs", core: "Core Infrastructure", agents: "Agents", dashboards: "Dashboards",
                support: "Support Services", other: "Other", restartSuccess: "Restart initiated",
                restartFailed: "Restart failed", noDidWarning: "Connect DID to control services",
                sealed: "SEALED", nohup: "NOHUP", open: "Open"
            },
            de: {
                connect: "Verbinden", disconnect: "Trennen", online: "Online", offline: "Offline",
                degraded: "Eingeschränkt", total: "Gesamt", restart: "Neustart", stop: "Stoppen", start: "Starten",
                logs: "Logs", core: "Kerninfrastruktur", agents: "Agenten", dashboards: "Dashboards",
                support: "Support-Dienste", other: "Andere", restartSuccess: "Neustart eingeleitet",
                restartFailed: "Neustart fehlgeschlagen", noDidWarning: "DID verbinden um Dienste zu steuern",
                sealed: "VERSIEGELT", nohup: "NOHUP", open: "Öffnen"
            },
            pt: {
                connect: "Conectar", disconnect: "Desconectar", online: "Online", offline: "Offline",
                degraded: "Degradado", total: "Total", restart: "Reiniciar", stop: "Parar", start: "Iniciar",
                logs: "Logs", core: "Infraestrutura Core", agents: "Agentes", dashboards: "Dashboards",
                support: "Serviços de Suporte", other: "Outros", restartSuccess: "Reinício iniciado",
                restartFailed: "Reinício falhou", noDidWarning: "Conecte DID para controlar serviços",
                sealed: "SELADO", nohup: "NOHUP", open: "Abrir"
            }
        };
        let lang = localStorage.getItem('windi-lang') || 'en';

        function t(key) { return i18n[lang][key] || key; }

        function setLang(l) {
            lang = l;
            localStorage.setItem('windi-lang', l);
            document.querySelectorAll('[data-i18n]').forEach(el => {
                el.textContent = t(el.dataset.i18n);
            });
            renderServices();
        }

        // Theme
        function toggleTheme() {
            const html = document.documentElement;
            const current = html.getAttribute('data-theme');
            const next = current === 'noir' ? 'klar' : 'noir';
            html.setAttribute('data-theme', next);
            localStorage.setItem('windi-theme', next);
        }

        // Init theme
        const savedTheme = localStorage.getItem('windi-theme') || 'noir';
        document.documentElement.setAttribute('data-theme', savedTheme);

        // DID
        function connectDID() {
            const input = document.getElementById('did-input');
            const banner = document.getElementById('did-banner');
            const btn = banner.querySelector('.btn-connect');

            if (currentDID) {
                currentDID = null;
                sessionStorage.removeItem('windi_control_did');
                input.value = FOUNDER_DID;  // Reset to founder DID
                input.disabled = false;
                btn.textContent = t('connect');
                banner.classList.remove('connected');
                showToast(t('disconnect'), 'success');
            } else {
                const did = input.value.trim();
                if (!did.startsWith('did:windi:')) {
                    showToast('DID must start with did:windi:', 'error');
                    return;
                }
                currentDID = did;
                sessionStorage.setItem('windi_control_did', did);
                input.disabled = true;
                btn.textContent = t('disconnect');
                banner.classList.add('connected');
                // Show tier badge for founder
                const tierBadge = did === 'did:windi:dragon-001' ? ' [ORACLE/Founder]' : '';
                showToast('DID connected: ' + did + tierBadge, 'success');
            }
            renderServices();
        }

        // Restore DID from session or localStorage
        const FOUNDER_DID = 'did:windi:dragon-001';
        const savedDID = sessionStorage.getItem('windi_control_did') || localStorage.getItem('windi_default_did');
        const didInput = document.getElementById('did-input');

        if (savedDID) {
            didInput.value = savedDID;
            connectDID();
        } else {
            // Auto-fill with founder DID for convenience
            didInput.value = FOUNDER_DID;
            didInput.placeholder = FOUNDER_DID + ' (founder)';
        }

        // Toast
        function showToast(msg, type = 'success') {
            const toast = document.getElementById('toast');
            toast.textContent = msg;
            toast.className = 'toast active ' + type;
            setTimeout(() => toast.classList.remove('active'), 3000);
        }

        // Load Services
        // Base path for API calls (handles /svc-control/ prefix)
        const API_BASE = window.location.pathname.replace(/\/$/, '');

        async function loadServices() {
            try {
                const r = await fetch(API_BASE + '/api/services');
                const data = await r.json();
                services = data.services;

                document.getElementById('stat-online').textContent = data.counts.online;
                document.getElementById('stat-degraded').textContent = data.counts.degraded;
                document.getElementById('stat-offline').textContent = data.counts.offline;
                document.getElementById('stat-total').textContent = data.counts.total;

                renderServices();

                // Load subsystems for services that have them (SVG Sentinel)
                for (const svc of services) {
                    if (svc.has_subsystems) {
                        const containerId = `subsystems-${svc.service.replace(/[^a-z0-9]/gi, '-')}`;
                        loadSubsystems(svc.service, containerId);
                    }
                }
            } catch (e) {
                console.error('Failed to load services:', e);
            }
        }

        // Render Services
        function renderServices() {
            const container = document.getElementById('services-container');
            const categories = ['core', 'agents', 'dashboards', 'support', 'other'];

            let html = '';
            for (const cat of categories) {
                const catServices = services.filter(s => s.category === cat);
                if (catServices.length === 0) continue;

                html += `<div class="category">
                    <h2 class="category-title">${t(cat)}</h2>
                    <div class="services-grid">`;

                for (const svc of catServices) {
                    const canControl = currentDID && !svc.sealed && !svc.nohup;
                    const subsystemId = `subsystems-${svc.service.replace(/[^a-z0-9]/gi, '-')}`;
                    html += `
                        <div class="service-card ${svc.overall}">
                            <div class="service-header">
                                <div>
                                    <div class="service-name">${svc.display}</div>
                                    <div class="service-port">:${svc.port} · ${svc.service}</div>
                                </div>
                                <span class="service-status ${svc.overall}">${svc.overall}</span>
                            </div>
                            <div class="service-meta">
                                ${svc.sealed ? `<span class="badge sealed">${t('sealed')}</span>` : ''}
                                ${svc.nohup ? `<span class="badge nohup">${t('nohup')}</span>` : ''}
                                ${svc.has_subsystems ? `<span class="badge" style="background:rgba(201,168,76,0.2);color:var(--gold);">SENTINEL</span>` : ''}
                                <span class="badge">${svc.systemd}</span>
                            </div>
                            ${svc.has_subsystems ? `<div class="subsystems" id="${subsystemId}"></div>` : ''}
                            <div class="service-actions">
                                ${svc.url ? `
                                    <a href="${svc.url}" target="_blank" class="btn-action open">
                                        🔗 ${t('open')}
                                    </a>
                                ` : ''}
                                <button class="btn-action restart" onclick="restartService('${svc.service}')" ${canControl ? '' : 'disabled'}>
                                    ↻ ${t('restart')}
                                </button>
                                ${svc.overall === 'online' ? `
                                    <button class="btn-action stop" onclick="stopService('${svc.service}')" ${canControl ? '' : 'disabled'}>
                                        ⬛ ${t('stop')}
                                    </button>
                                ` : `
                                    <button class="btn-action start" onclick="startService('${svc.service}')" ${canControl ? '' : 'disabled'}>
                                        ▶ ${t('start')}
                                    </button>
                                `}
                                <button class="btn-action" onclick="showLogs('${svc.service}')">
                                    📋 ${t('logs')}
                                </button>
                            </div>
                        </div>`;
                }
                html += '</div></div>';
            }
            container.innerHTML = html;
        }

        // Actions
        async function restartService(name) {
            if (!currentDID) { showToast(t('noDidWarning'), 'error'); return; }
            try {
                const r = await fetch(`${API_BASE}/api/services/${name}/restart`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({actor_did: currentDID, reason: 'Manual restart via Control Panel'})
                });
                const data = await r.json();
                if (r.ok) {
                    showToast(`${t('restartSuccess')}: ${name}`, 'success');
                    setTimeout(loadServices, 2000);
                } else {
                    showToast(data.message || data.error, 'error');
                }
            } catch (e) {
                showToast(t('restartFailed'), 'error');
            }
        }

        async function stopService(name) {
            if (!currentDID) { showToast(t('noDidWarning'), 'error'); return; }
            try {
                const r = await fetch(`${API_BASE}/api/services/${name}/stop`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({actor_did: currentDID})
                });
                if (r.ok) {
                    showToast('Service stopped: ' + name, 'success');
                    setTimeout(loadServices, 2000);
                }
            } catch (e) {
                showToast('Stop failed', 'error');
            }
        }

        async function startService(name) {
            if (!currentDID) { showToast(t('noDidWarning'), 'error'); return; }
            try {
                const r = await fetch(`${API_BASE}/api/services/${name}/start`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({actor_did: currentDID})
                });
                if (r.ok) {
                    showToast('Service started: ' + name, 'success');
                    setTimeout(loadServices, 2000);
                }
            } catch (e) {
                showToast('Start failed', 'error');
            }
        }

        // Logs Modal
        async function showLogs(name) {
            const modal = document.getElementById('logs-modal');
            const title = document.getElementById('logs-title');
            const content = document.getElementById('logs-content');

            title.textContent = `Logs: ${name}`;
            content.textContent = 'Loading...';
            modal.classList.add('active');

            try {
                const r = await fetch(`${API_BASE}/api/services/${name}/logs?lines=100`);
                const data = await r.json();
                content.textContent = data.logs || 'No logs available';
            } catch (e) {
                content.textContent = 'Failed to load logs';
            }
        }

        function closeModal() {
            document.getElementById('logs-modal').classList.remove('active');
        }

        // SVG Sentinel Icons
        const SENTINEL_SVGS = {
            online: `<svg class="sentinel-svg online" viewBox="0 0 16 16" fill="currentColor">
                <circle cx="8" cy="8" r="6" fill="currentColor"/>
            </svg>`,
            offline: `<svg class="sentinel-svg offline" viewBox="0 0 16 16" fill="currentColor">
                <circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="2" fill="none"/>
                <line x1="5" y1="5" x2="11" y2="11" stroke="currentColor" stroke-width="2"/>
            </svg>`,
            degraded: `<svg class="sentinel-svg degraded" viewBox="0 0 16 16" fill="currentColor">
                <polygon points="8,2 14,14 2,14" fill="currentColor"/>
                <text x="8" y="12" font-size="8" fill="var(--bg)" text-anchor="middle">!</text>
            </svg>`,
            blocked: `<svg class="sentinel-svg blocked" viewBox="0 0 16 16" fill="currentColor">
                <circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="2" fill="none"/>
                <line x1="4" y1="8" x2="12" y2="8" stroke="currentColor" stroke-width="2"/>
            </svg>`,
            error: `<svg class="sentinel-svg error" viewBox="0 0 16 16" fill="currentColor">
                <circle cx="8" cy="8" r="6" fill="currentColor"/>
                <text x="8" y="11" font-size="8" fill="var(--bg)" text-anchor="middle">?</text>
            </svg>`
        };

        // Load subsystems for a service
        async function loadSubsystems(serviceName, containerId) {
            const container = document.getElementById(containerId);
            if (!container) return;

            container.innerHTML = '<div class="subsystems-title">Loading subsystems...</div>';

            try {
                const r = await fetch(`${API_BASE}/api/subsystems/${serviceName}`);
                if (!r.ok) {
                    container.innerHTML = '';
                    return;
                }
                const data = await r.json();
                renderSubsystems(data, container);
            } catch (e) {
                container.innerHTML = `<div class="subsystem-alert">Failed to load subsystems</div>`;
            }
        }

        // Render subsystems in container
        function renderSubsystems(data, container) {
            if (!data.subsystems || data.subsystems.length === 0) {
                container.innerHTML = '';
                return;
            }

            let html = `<div class="subsystems-title">Subsystems (${data.subsystems.length})</div>`;

            for (const sub of data.subsystems) {
                const icon = SENTINEL_SVGS[sub.status] || SENTINEL_SVGS.error;
                const criticalClass = sub.critical ? 'critical' : '';
                const respTime = sub.response_time_ms ? ` · ${sub.response_time_ms.toFixed(0)}ms` : '';

                html += `
                    <div class="subsystem-row">
                        ${icon}
                        <span class="subsystem-name ${criticalClass}" title="${sub.description}">${sub.display}</span>
                        <span class="subsystem-status">${sub.status}${respTime}</span>
                    </div>`;
            }

            if (data.has_critical_failure) {
                html += `<div class="subsystem-alert">⚠️ Critical subsystem failure detected</div>`;
            }

            container.innerHTML = html;
        }

        // Init
        loadServices();
        setInterval(loadServices, 30000); // Refresh every 30s
        setLang(lang);
    </script>
</body>
</html>
'''

# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║   W-SERVICE-CONTROL — WINDI Service Control Panel            ║
║   Port: {PORT}                                                 ║
║   Invariants: I1, I9, I11                                    ║
║   "Se não consegues controlar, não consegues escalar."       ║
╚══════════════════════════════════════════════════════════════╝
    """)
    app.run(host="0.0.0.0", port=PORT, debug=False)
