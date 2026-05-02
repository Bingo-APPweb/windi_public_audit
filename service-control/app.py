"""
W-SERVICE-CONTROL — WINDI Service Control Panel v2.1.0
Sovereign Service Management with I9 Human Gate + Double Receipt Ledger

Port: 8170
Invariants: I1, I9, I11

§227 Update: Added support for:
- W-MAIL-001 (Docker) — Email Sovereign
- W-OLLAMA-001 (Remote) — Galho B / Server Gêmeo

Liga IA+H · Kempten, Bavaria · 2026
"""

import subprocess
import json
import hashlib
import requests
import time
from datetime import datetime, timezone
from flask import Flask, jsonify, request, render_template_string
from functools import wraps

app = Flask(__name__)

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

PORT = 8170
VERSION = "2.1.0"  # §227 Galho B + W-MAIL-001
LEDGER_URL = "http://localhost:8101"

# Tiers for service protection
TIER_SEALED = "SEALED"      # No restart via UI - requires terminal
TIER_CRITICAL = "CRITICAL"  # Dual confirmation + double receipt
TIER_STANDARD = "STANDARD"  # Single confirmation + double receipt

# Services to monitor (systemd service names)
WINDI_SERVICES = [
    # Core Infrastructure - SEALED (G5 Protected)
    {"name": "windi-suite-docs", "port": 8101, "display": "Forensic Ledger", "category": "core", "tier": TIER_SEALED, "url": "/ledger/"},
    {"name": "windi-law", "port": 8122, "display": "WINDI-LAW", "category": "agents", "tier": TIER_SEALED, "url": "/law/"},

    # Core Infrastructure - CRITICAL
    {"name": "windi-dragon-chat", "port": 8108, "display": "Dragon Hub", "category": "core", "tier": TIER_CRITICAL, "url": "/desktop/"},
    {"name": "windi-desktop-gen7", "port": 8119, "display": "Desktop GEN7", "category": "core", "tier": TIER_CRITICAL, "url": "/desktop/"},
    {"name": "windi-governance", "port": 8080, "display": "Governance API", "category": "core", "tier": TIER_CRITICAL, "url": ""},

    # Agents - STANDARD
    {"name": "windi-travel", "port": 8126, "display": "WINDI Travel", "category": "agents", "tier": TIER_STANDARD, "url": "/travel/"},
    {"name": "windi-nomad-bot", "port": 8127, "display": "W-NOMAD-001", "category": "agents", "tier": TIER_STANDARD, "url": "https://t.me/windi_nomad_bot"},
    {"name": "windi-vd-cut", "port": 8128, "display": "W-VD-CUT-001", "category": "agents", "tier": TIER_STANDARD, "url": "/vd-cut/"},
    {"name": "windi-joe", "port": 8129, "display": "W-JOE-001", "category": "agents", "tier": TIER_STANDARD, "url": "/joe/"},
    {"name": "windi-vd-mass", "port": 8131, "display": "W-VD-MASS-001", "category": "agents", "tier": TIER_STANDARD, "nohup": True, "url": "/vd-mass/"},
    {"name": "windi-jmpg", "port": 8132, "display": "W-JMPG-001", "category": "agents", "tier": TIER_STANDARD, "url": ""},
    {"name": "windi-social", "port": 8133, "display": "W-SOCIAL-001", "category": "agents", "tier": TIER_STANDARD, "nohup": True, "url": "/social/"},

    # Dashboards - STANDARD
    {"name": "windi-udb", "port": 8140, "display": "UDB God View", "category": "dashboards", "tier": TIER_STANDARD, "nohup": True, "url": "/udb/"},
    {"name": "windi-intent-cmd", "port": 8141, "display": "W-INTENT-CMD", "category": "dashboards", "tier": TIER_STANDARD, "url": ""},
    {"name": "windi-fediverse", "port": 8142, "display": "W-FEDIVERSE-001", "category": "dashboards", "tier": TIER_STANDARD, "url": "/fediverse/"},
    {"name": "windi-bridge", "port": 8143, "display": "W-BRIDGE-001", "category": "dashboards", "tier": TIER_STANDARD, "url": "/watch/"},
    {"name": "windi-sec-001", "port": 8144, "display": "W-SEC-001", "category": "dashboards", "tier": TIER_STANDARD, "url": "/sec/"},
    {"name": "windi-verify-public", "port": 8114, "display": "Verify Public", "category": "dashboards", "tier": TIER_STANDARD, "url": "/verify-public/"},
    {"name": "windi-enterprise", "port": 8150, "display": "W-Enterprise-001", "category": "dashboards", "tier": TIER_STANDARD, "url": "/enterprise/"},
    {"name": "windi-lab", "port": 8151, "display": "W-LAB-001", "category": "dashboards", "tier": TIER_STANDARD, "nohup": True, "url": "/lab/"},
    {"name": "windi-cost", "port": 8152, "display": "W-COST-001", "category": "dashboards", "tier": TIER_STANDARD, "nohup": True, "url": "/cost/"},
    {"name": "windi-cache", "port": 8160, "display": "W-CACHE-001", "category": "dashboards", "tier": TIER_STANDARD, "nohup": True, "url": "/wcache/noir"},
    {"name": "windi-travel-map", "port": 8153, "display": "W-TRAVEL-MAP", "category": "dashboards", "tier": TIER_STANDARD, "nohup": True, "url": "/travel/map/"},
    {"name": "windi-academy", "port": 8180, "display": "W-ACADEMY-001", "category": "dashboards", "tier": TIER_STANDARD, "nohup": True, "url": "/academy/"},

    # Support - STANDARD
    {"name": "windi-leads", "port": 8096, "display": "DID Genesis", "category": "support", "tier": TIER_STANDARD, "url": "", "nohup": True},  # §186 uvicorn restart
    {"name": "windi-wallet", "port": 8095, "display": "Wallet Service", "category": "support", "tier": TIER_STANDARD, "url": "/wallet/"},
    {"name": "windi-communique", "port": 8105, "display": "Communiqué Engine", "category": "support", "tier": TIER_STANDARD, "url": ""},
    {"name": "windi-dispatch", "port": 8106, "display": "Dispatch Gateway", "category": "support", "tier": TIER_STANDARD, "url": ""},

    # Special (nohup)
    {"name": "sandbox-core", "port": 8091, "display": "Sandbox Core", "category": "core", "tier": TIER_CRITICAL, "nohup": True, "url": ""},

    # §224-226 W-MAIL-001 — Email Sovereign (Docker)
    {"name": "windi-mail", "port": 8888, "display": "W-MAIL-001 Email", "category": "support", "tier": TIER_CRITICAL, "docker": True, "url": "https://mail.windisites.de/"},

    # §227 W-OLLAMA-001 — Galho B / Server Gêmeo (Remote)
    {"name": "windi-ollama", "port": 11434, "display": "W-OLLAMA-001 Galho B", "category": "infra", "tier": TIER_STANDARD, "remote": True, "remote_host": "85.215.131.0", "url": ""},
]

# Health check endpoints by port
HEALTH_ENDPOINTS = {
    8091: "/health",
    8096: "/api/genesis/health",  # §186 DID-Genesis correct endpoint
    8101: "/health",
    8108: "/health",
    8114: "/health",
    8119: "/health",
    8122: "/health",
    8126: "/health",
    8127: "/health",
    8128: "/vd-cut/health",
    8129: "/health",
    8131: "/health",
    8132: "/comm/health",
    8133: "/social/health",
    8140: "/health",
    8141: "/health",
    8142: "/health",
    8143: "/health",
    8144: "/health",
    8150: "/health",
    8151: "/health",
    8152: "/health",
    8153: "/health",
    8160: "/health",
    8180: "/health",
    8888: "/",  # §224-226 W-MAIL-001 SnappyMail webmail
    11434: "/api/tags",  # §227 W-OLLAMA-001 Ollama API
}

# Remote services (Galho B)
REMOTE_HOSTS = {
    "windi-ollama": "85.215.131.0",
}

# Nohup service paths (for manual restart)
NOHUP_PATHS = {
    "windi-vd-mass": "/opt/windi/vd-mass",
    "windi-jmpg": "/opt/windi/comm",
    "windi-social": "/opt/windi/w-social-001",
    "windi-lab": "/opt/windi/w-lab-001",
    "windi-cost": "/opt/windi/w-cost-001",
    "windi-cache": "/opt/windi/w-cache-001",
    "windi-travel-map": "/opt/windi/windi-travel/map-comparator/deploy-windi-travel-map",
    "windi-udb": "/opt/windi/udb",
    "sandbox-core": "/opt/windi/agents/constitutional-agent",
    "windi-academy": "/opt/windi/w-academy-001",
    "windi-leads": "/opt/windi/did-genesis",  # §186 DID-Genesis restart fix
}

# Nohup main files
NOHUP_MAIN_FILES = {
    "windi-vd-mass": "app.py",
    "windi-jmpg": "jmpg_server.py",
    "windi-social": "app.py",
    "windi-lab": "app.py",
    "windi-cost": "app.py",
    "windi-cache": "app.py",
    "windi-travel-map": "server.py",
    "windi-udb": "app.py",
    "sandbox-core": "agent.py",
    "windi-academy": "app.py",
    "windi-leads": "did_genesis.py",  # §186 uvicorn did_genesis:app
}

# §186 Custom startup commands (for uvicorn services)
NOHUP_COMMANDS = {
    "windi-leads": "python3 -m uvicorn did_genesis:app --host 0.0.0.0 --port 8096",
}

# ═══════════════════════════════════════════════════════════════
# SUBSYSTEMS — Module-level Health Monitoring (SVG Sentinel)
# ═══════════════════════════════════════════════════════════════

SUBSYSTEMS = {
    "windi-law": [
        {"id": "ai-draft", "display": "AI Draft", "endpoint": "/ai-draft/health", "port": 8122, "critical": True, "description": "LLM document generation"},
        {"id": "identity-gate", "display": "Identity Gate", "endpoint": "/health", "port": 8122, "critical": True, "description": "DID authentication"},
        {"id": "dragon-law", "display": "Dragon Law", "endpoint": "/dragon/health", "port": 8122, "critical": False, "description": "Dragon Shadow Forest integration"}
    ],
    "windi-travel": [
        {"id": "identity-gate", "display": "Identity Gate", "endpoint": "/health", "port": 8126, "critical": True, "description": "DID wallet authentication"},
        {"id": "workspace", "display": "Workspace", "endpoint": "/workspace/", "port": 8126, "critical": True, "description": "Travel workspace UI"}
    ],
    "windi-lab": [
        {"id": "clear", "display": "Dilemas de Geleia", "endpoint": "/api/clear/stats", "port": 8151, "critical": False, "description": "Cognitive training module"}
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

def check_health_endpoint(port, remote_host=None):
    """Check service health endpoint (supports local and remote services)."""
    endpoint = HEALTH_ENDPOINTS.get(port, "/health")
    host = remote_host if remote_host else "localhost"
    try:
        r = requests.get(f"http://{host}:{port}{endpoint}", timeout=5)
        if r.status_code == 200:
            try:
                return {"status": "healthy", "data": r.json(), "host": host}
            except:
                return {"status": "healthy", "data": {}, "host": host}
        return {"status": "unhealthy", "code": r.status_code, "host": host}
    except requests.exceptions.ConnectionError:
        return {"status": "offline", "error": "connection_refused", "host": host}
    except requests.exceptions.Timeout:
        return {"status": "timeout", "error": "timeout", "host": host}
    except Exception as e:
        return {"status": "error", "error": str(e)[:50], "host": host}

def check_docker_service(container_name_prefix):
    """Check if Docker container is running."""
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", f"name={container_name_prefix}", "--format", "{{.Status}}"],
            capture_output=True, text=True, timeout=5
        )
        status = result.stdout.strip()
        if "Up" in status:
            return {"status": "running", "docker_status": status}
        elif status:
            return {"status": "stopped", "docker_status": status}
        else:
            return {"status": "not_found", "docker_status": "container not found"}
    except Exception as e:
        return {"status": "error", "error": str(e)[:50]}

def get_full_service_status(service):
    """Get comprehensive status for a service."""
    name = service["name"]
    port = service.get("port")
    is_nohup = service.get("nohup", False)
    is_docker = service.get("docker", False)
    is_remote = service.get("remote", False)
    remote_host = service.get("remote_host")
    tier = service.get("tier", TIER_STANDARD)

    # Systemd status (skip for nohup/docker/remote services)
    if is_nohup:
        systemd = "nohup"
    elif is_docker:
        systemd = "docker"
    elif is_remote:
        systemd = "remote"
    else:
        systemd = get_systemd_status(name)

    # Port status (skip for remote services)
    if is_remote:
        port_active = True  # Assume remote is reachable, let health check determine
    else:
        port_active = get_port_status(port) if port else False

    # Health check
    if is_docker:
        # For Docker services, check both container and port
        docker_status = check_docker_service("mailserver")
        if docker_status["status"] == "running":
            health = check_health_endpoint(port) if port else {"status": "healthy", "docker": True}
        else:
            health = {"status": "offline", "docker_status": docker_status}
    elif is_remote and remote_host:
        # For remote services (Galho B), check remote health
        health = check_health_endpoint(port, remote_host=remote_host)
    elif port and port_active:
        health = check_health_endpoint(port)
    else:
        health = {"status": "offline"}

    # Determine overall status
    if health["status"] == "healthy":
        overall = "online"
    elif health["status"] == "running":  # Docker running
        overall = "online"
    elif port_active and not is_remote:
        overall = "degraded"
    elif systemd == "active" or systemd == "nohup":
        overall = "starting"
    elif is_remote and health["status"] == "timeout":
        overall = "degraded"
    else:
        overall = "offline"

    # Check for subsystems
    has_subsystems = name in SUBSYSTEMS

    return {
        "service": name,
        "display": service["display"],
        "port": port,
        "category": service.get("category", "other"),
        "tier": tier,
        "sealed": tier == TIER_SEALED,
        "nohup": is_nohup,
        "docker": is_docker,
        "remote": is_remote,
        "remote_host": remote_host,
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
        return {"id": subsystem["id"], "display": subsystem["display"], "status": "offline", "critical": subsystem.get("critical", False), "description": subsystem.get("description", ""), "error": "connection_refused"}
    except requests.exceptions.Timeout:
        return {"id": subsystem["id"], "display": subsystem["display"], "status": "blocked", "critical": subsystem.get("critical", False), "description": subsystem.get("description", ""), "error": "timeout"}
    except Exception as e:
        return {"id": subsystem["id"], "display": subsystem["display"], "status": "error", "critical": subsystem.get("critical", False), "description": subsystem.get("description", ""), "error": str(e)[:50]}

def get_all_subsystems_status(service_name):
    """Get status of all subsystems for a service."""
    if service_name not in SUBSYSTEMS:
        return {"service": service_name, "subsystems": [], "has_critical_failure": False}

    subsystems = []
    has_critical_failure = False

    for sub in SUBSYSTEMS[service_name]:
        status = check_subsystem_health(service_name, sub)
        subsystems.append(status)
        if status["critical"] and status["status"] not in ["online"]:
            has_critical_failure = True

    return {
        "service": service_name,
        "subsystems": subsystems,
        "has_critical_failure": has_critical_failure,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# ═══════════════════════════════════════════════════════════════
# LEDGER INTEGRATION (I11) — Double Receipt System
# ═══════════════════════════════════════════════════════════════

def generate_receipt_id(action, service_name, actor_did):
    """Generate a unique receipt ID."""
    ts = datetime.now().strftime('%Y%m%d%H%M%S')
    hash_input = f"{action}{service_name}{actor_did}{ts}"
    short_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:8].upper()
    return f"WINDI-SVC-{ts}-{short_hash}"

def seal_to_ledger(receipt_data):
    """Seal receipt to Forensic Ledger (I11)."""
    try:
        r = requests.post(f"{LEDGER_URL}/api/receipts", json=receipt_data, timeout=5)
        return r.status_code in [200, 201]
    except:
        return False

def create_restart_initiated_receipt(service_name, actor_did, tier, pre_health):
    """Create Receipt 1: restart_initiated."""
    receipt_id = generate_receipt_id("RESTART_INIT", service_name, actor_did)

    receipt = {
        "id": receipt_id,  # §191: Ledger requires 'id' not 'receipt_id'
        "actor": actor_did,
        "app": "service-control",
        "doc_name": f"Restart Initiated: {service_name}",
        "doc_type": "service-restart-initiated",
        "governance_level": "HIGH" if tier == TIER_CRITICAL else "MEDIUM",
        "sge_score": 0.85 if tier == TIER_CRITICAL else 0.70,  # §191: Required field
        "content_hash": f"sha256:{hashlib.sha256(json.dumps({'service': service_name, 'action': 'restart_initiated', 'tier': tier, 'pre_health': pre_health}, sort_keys=True).encode()).hexdigest()}",
        "invariants": ["I9", "I11"],
        "stage": "C6",
        "metadata": {
            "service": service_name,
            "tier": tier,
            "action": "restart_initiated",
            "pre_health": pre_health
        },
        "sealed_at": datetime.now(timezone.utc).isoformat()
    }

    sealed = seal_to_ledger(receipt)
    return receipt_id if sealed else None, receipt

def create_restart_completed_receipt(service_name, actor_did, tier, parent_receipt_id, post_health, success):
    """Create Receipt 2: restart_completed (linked to Receipt 1)."""
    receipt_id = generate_receipt_id("RESTART_DONE", service_name, actor_did)

    receipt = {
        "id": receipt_id,  # §191: Ledger requires 'id' not 'receipt_id'
        "parent_receipt_id": parent_receipt_id,  # Chain link!
        "actor": actor_did,
        "app": "service-control",
        "doc_name": f"Restart {'Completed' if success else 'Failed'}: {service_name}",
        "doc_type": "service-restart-completed",
        "governance_level": "HIGH" if tier == TIER_CRITICAL else "MEDIUM",
        "sge_score": 0.90 if success else 0.50,  # §191: Required field
        "content_hash": f"sha256:{hashlib.sha256(json.dumps({'service': service_name, 'action': 'restart_completed', 'success': success, 'post_health': post_health}, sort_keys=True).encode()).hexdigest()}",
        "invariants": ["I9", "I11"],
        "stage": "C6",
        "metadata": {
            "service": service_name,
            "tier": tier,
            "action": "restart_completed",
            "success": success,
            "post_health": post_health,
            "parent_receipt_id": parent_receipt_id
        },
        "sealed_at": datetime.now(timezone.utc).isoformat()
    }

    sealed = seal_to_ledger(receipt)
    return receipt_id if sealed else None, receipt

# ═══════════════════════════════════════════════════════════════
# RESTART EXECUTION
# ═══════════════════════════════════════════════════════════════

def restart_systemd_service(service_name):
    """Restart a systemd service."""
    try:
        # Try without sudo first (if running as root or with permissions)
        result = subprocess.run(
            ["systemctl", "restart", service_name],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return True, "success"

        # Fallback: try with sudo
        result = subprocess.run(
            ["sudo", "systemctl", "restart", service_name],
            capture_output=True, text=True, timeout=30
        )
        return result.returncode == 0, result.stderr if result.returncode != 0 else "success"
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except Exception as e:
        return False, str(e)

def restart_nohup_service(service_name, port):
    """Restart a nohup service by killing existing process and starting new one."""
    path = NOHUP_PATHS.get(service_name)
    main_file = NOHUP_MAIN_FILES.get(service_name, "app.py")
    custom_cmd = NOHUP_COMMANDS.get(service_name)  # §186 Custom uvicorn commands

    if not path:
        return False, f"No path configured for {service_name}"

    try:
        # Kill existing process on port
        subprocess.run(["fuser", "-k", f"{port}/tcp"], capture_output=True, timeout=5)
        time.sleep(1)

        # Start new process (use custom command if available)
        log_file = f"/tmp/{service_name}.log"
        if custom_cmd:
            cmd = f"cd {path} && nohup {custom_cmd} > {log_file} 2>&1 &"
        else:
            cmd = f"cd {path} && nohup python3 {main_file} > {log_file} 2>&1 &"
        subprocess.run(cmd, shell=True, timeout=5)

        # Wait for service to start
        time.sleep(3)

        # Verify port is listening
        if get_port_status(port):
            return True, "success"
        else:
            return False, "service did not start"
    except Exception as e:
        return False, str(e)

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
        "features": ["double_receipt", "tier_protection", "i9_ceremony"],
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

@app.route("/api/services")
def list_services():
    """List all services with current status."""
    services = []

    for svc in WINDI_SERVICES:
        status = get_full_service_status(svc)
        services.append(status)

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
    """
    Restart a service with I9 ceremony and double receipt (I11).

    Flow:
    1. Validate DID and tier
    2. Pre-restart health check
    3. Seal Receipt 1 (restart_initiated)
    4. Execute restart
    5. Post-restart health check
    6. Seal Receipt 2 (restart_completed) with parent_receipt_id
    """
    data = request.get_json() or {}
    actor_did = data.get("actor_did")
    reason = data.get("reason", "Manual restart via Control Panel")

    # Find service
    svc = next((s for s in WINDI_SERVICES if s["name"] == service_name), None)
    if not svc:
        return jsonify({"error": "Service not found"}), 404

    tier = svc.get("tier", TIER_STANDARD)
    is_nohup = svc.get("nohup", False)
    port = svc.get("port")

    # Check if SEALED (blocked)
    if tier == TIER_SEALED:
        return jsonify({
            "error": "SEALED_SERVICE",
            "message": f"{svc['display']} is a SEALED service. Restart blocked via UI.",
            "invariant": "G5",
            "tier": tier
        }), 403

    # Pre-restart health check
    pre_health = check_health_endpoint(port) if port else {"status": "unknown"}

    # === RECEIPT 1: restart_initiated ===
    receipt1_id, receipt1 = create_restart_initiated_receipt(
        service_name, actor_did, tier, pre_health
    )

    if not receipt1_id:
        return jsonify({
            "error": "LEDGER_FAILED",
            "message": "Failed to seal restart_initiated receipt to Ledger",
            "invariant": "I11"
        }), 500

    # === EXECUTE RESTART ===
    if is_nohup:
        success, error = restart_nohup_service(service_name, port)
    else:
        success, error = restart_systemd_service(service_name)

    # Wait for service to stabilize
    time.sleep(2)

    # Post-restart health check
    post_health = check_health_endpoint(port) if port else {"status": "unknown"}

    # Determine actual success based on health
    actual_success = success and post_health.get("status") == "healthy"

    # === RECEIPT 2: restart_completed (linked to Receipt 1) ===
    receipt2_id, receipt2 = create_restart_completed_receipt(
        service_name, actor_did, tier, receipt1_id, post_health, actual_success
    )

    return jsonify({
        "status": "RESTART_COMPLETED" if actual_success else "RESTART_FAILED",
        "service": service_name,
        "tier": tier,
        "success": actual_success,
        "receipts": {
            "initiated": {
                "receipt_id": receipt1_id,
                "action": "restart_initiated",
                "pre_health": pre_health
            },
            "completed": {
                "receipt_id": receipt2_id,
                "action": "restart_completed",
                "parent_receipt_id": receipt1_id,
                "post_health": post_health,
                "success": actual_success
            }
        },
        "message": f"Restart {'successful' if actual_success else 'failed'}: {svc['display']}",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

@app.route("/api/services/<service_name>/stop", methods=["POST"])
@require_i9_gate
def stop_service(service_name):
    """Stop a service (requires I9 human approval)."""
    data = request.get_json() or {}
    actor_did = data.get("actor_did")

    svc = next((s for s in WINDI_SERVICES if s["name"] == service_name), None)
    if not svc:
        return jsonify({"error": "Service not found"}), 404

    tier = svc.get("tier", TIER_STANDARD)
    if tier == TIER_SEALED:
        return jsonify({
            "error": "SEALED_SERVICE",
            "message": f"{svc['display']} is SEALED. Cannot be stopped via Control Panel.",
            "invariant": "G5"
        }), 403

    is_nohup = svc.get("nohup", False)
    port = svc.get("port")

    try:
        if is_nohup:
            subprocess.run(["fuser", "-k", f"{port}/tcp"], capture_output=True, timeout=5)
            success = True
        else:
            result = subprocess.run(
                ["systemctl", "stop", service_name],
                capture_output=True, text=True, timeout=30
            )
            success = result.returncode == 0

        # Seal to ledger
        receipt_id = generate_receipt_id("STOP", service_name, actor_did)
        seal_to_ledger({
            "receipt_id": receipt_id,
            "actor": actor_did,
            "app": "service-control",
            "doc_name": f"Service Stop: {service_name}",
            "doc_type": "service-stop",
            "governance_level": "HIGH",
            "invariants": ["I9", "I11"],
            "stage": "C6",
            "sealed_at": datetime.now(timezone.utc).isoformat()
        })

        return jsonify({
            "status": "STOPPED" if success else "STOP_FAILED",
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

    is_nohup = svc.get("nohup", False)
    port = svc.get("port")

    try:
        if is_nohup:
            success, _ = restart_nohup_service(service_name, port)
        else:
            result = subprocess.run(
                ["systemctl", "start", service_name],
                capture_output=True, text=True, timeout=30
            )
            success = result.returncode == 0

        receipt_id = generate_receipt_id("START", service_name, actor_did)
        seal_to_ledger({
            "receipt_id": receipt_id,
            "actor": actor_did,
            "app": "service-control",
            "doc_name": f"Service Start: {service_name}",
            "doc_type": "service-start",
            "governance_level": "MEDIUM",
            "invariants": ["I9", "I11"],
            "stage": "C6",
            "sealed_at": datetime.now(timezone.utc).isoformat()
        })

        return jsonify({
            "status": "STARTED" if success else "START_FAILED",
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

    is_nohup = svc.get("nohup", False)

    try:
        if is_nohup:
            # Read from log file
            log_file = f"/tmp/{service_name}.log"
            result = subprocess.run(
                ["tail", "-n", str(min(lines, 200)), log_file],
                capture_output=True, text=True, timeout=10
            )
            logs = result.stdout if result.returncode == 0 else "No logs available"
        else:
            result = subprocess.run(
                ["journalctl", "-u", service_name, "-n", str(min(lines, 200)), "--no-pager"],
                capture_output=True, text=True, timeout=10
            )
            logs = result.stdout

        return jsonify({
            "service": service_name,
            "logs": logs,
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
# HTML TEMPLATE — New UI with Tier-based Restart + Double Receipt
# ═══════════════════════════════════════════════════════════════

DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="en" data-theme="noir">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WINDI Service Control Panel</title>
    <style>
        :root {
            --bg: #ffffff;
            --bg-secondary: #f5f5f3;
            --bg-card: #ffffff;
            --text: #1a1a18;
            --text-dim: #6b6b67;
            --border: rgba(0,0,0,0.12);
            --border-strong: rgba(0,0,0,0.22);
            --gold: #8B7424;
            --green: #3B6D11;
            --green-bg: #EAF3DE;
            --red: #A32D2D;
            --red-bg: #FCEBEB;
            --yellow: #BA7517;
            --yellow-bg: #FAEEDA;
            --blue: #1D5AA8;
            --font-mono: 'Courier New', monospace;
        }

        [data-theme="noir"] {
            --bg: #1c1c1a;
            --bg-secondary: #252523;
            --bg-card: #252523;
            --text: #f0ede8;
            --text-dim: #9a9790;
            --border: rgba(255,255,255,0.1);
            --border-strong: rgba(255,255,255,0.18);
            --gold: #C9A84C;
            --green: #90c739;
            --green-bg: rgba(144,199,57,0.15);
            --red: #E24B4A;
            --red-bg: rgba(226,75,74,0.15);
            --yellow: #F5A623;
            --yellow-bg: rgba(245,166,35,0.15);
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            background: var(--bg-secondary);
            color: var(--text);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            font-size: 16px;
            line-height: 1.7;
            min-height: 100vh;
            padding: 2rem;
        }

        .page { max-width: 900px; margin: 0 auto; }

        button {
            background: transparent;
            border: 0.5px solid var(--border-strong);
            border-radius: 8px;
            color: var(--text);
            cursor: pointer;
            font-family: inherit;
            font-size: 13px;
            padding: 6px 14px;
            transition: all 0.15s;
        }
        button:hover { background: var(--bg-secondary); border-color: var(--gold); }
        button:active { transform: scale(0.98); }
        button:disabled { opacity: 0.4; cursor: not-allowed; }

        .header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1.5rem;
        }
        .header-title {
            font-size: 13px;
            color: var(--text-dim);
            font-family: var(--font-mono);
            letter-spacing: 0.05em;
        }
        .header-main {
            font-size: 18px;
            font-weight: 500;
            color: var(--text);
        }
        .header-status {
            display: flex;
            gap: 8px;
            align-items: center;
        }
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--green);
        }
        .status-text {
            font-size: 13px;
            color: var(--text-dim);
        }

        .legend {
            display: flex;
            gap: 12px;
            margin-bottom: 1.5rem;
            flex-wrap: wrap;
        }
        .legend-item {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 12px;
            color: var(--text-dim);
        }
        .legend-dot {
            width: 10px;
            height: 10px;
            border-radius: 2px;
        }
        .legend-dot.sealed { background: var(--red); }
        .legend-dot.critical { background: var(--yellow); }
        .legend-dot.standard { background: var(--green); }
        .legend-sep {
            width: 1px;
            background: var(--border);
        }

        #services-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .service-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: var(--bg-card);
            border: 0.5px solid var(--border);
            border-radius: 8px;
            padding: 12px 16px;
            gap: 12px;
        }
        .service-row:hover { border-color: var(--border-strong); }

        .service-info {
            display: flex;
            align-items: center;
            gap: 12px;
            flex: 1;
            min-width: 0;
        }
        .service-status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            flex-shrink: 0;
        }
        .service-status-dot.online { background: var(--green); animation: pulse 2.5s ease-in-out infinite; }
        .service-status-dot.offline { background: var(--red); }
        .service-status-dot.degraded { background: var(--yellow); }
        .service-status-dot.starting { background: var(--blue); animation: pulse 1s ease-in-out infinite; }

        @keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.4; } }
        @keyframes spin { to { transform: rotate(360deg); } }

        .service-details { flex: 1; min-width: 0; }
        .service-name { font-size: 14px; font-weight: 500; color: var(--text); }
        .service-port { font-size: 12px; color: var(--text-dim); font-family: var(--font-mono); }

        .tier-badge {
            font-size: 11px;
            padding: 3px 8px;
            border-radius: 4px;
            white-space: nowrap;
            flex-shrink: 0;
        }
        .tier-badge.sealed { background: var(--red-bg); color: var(--red); }
        .tier-badge.critical { background: var(--yellow-bg); color: var(--yellow); }
        .tier-badge.standard { background: var(--green-bg); color: var(--green); }

        .btn-blocked {
            font-size: 12px;
            color: var(--text-dim);
            padding: 6px 12px;
            border: 0.5px solid var(--border);
            border-radius: 8px;
            opacity: 0.5;
            cursor: not-allowed;
        }

        /* Modal */
        #modal-overlay {
            display: none;
            margin-top: 1.5rem;
        }
        #modal-overlay.active { display: block; }

        .modal-card {
            background: var(--bg-card);
            border: 0.5px solid var(--border-strong);
            border-radius: 12px;
            padding: 1.25rem;
        }
        .modal-header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 1rem;
        }
        .modal-tier-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
        }
        .modal-title {
            font-size: 15px;
            font-weight: 500;
            color: var(--text);
        }
        .modal-body {
            font-size: 13px;
            color: var(--text-dim);
            margin-bottom: 1rem;
            line-height: 1.6;
        }

        .receipt-box {
            background: var(--bg-secondary);
            border-radius: 8px;
            padding: 0.75rem 1rem;
            margin-bottom: 1rem;
            font-size: 12px;
            font-family: var(--font-mono);
            color: var(--text-dim);
        }
        .receipt-box .label {
            color: var(--text);
            margin-bottom: 4px;
        }
        .receipt-box.success {
            border: 0.5px solid var(--green);
        }
        .receipt-box .receipt-label {
            color: var(--text-dim);
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 6px;
        }
        .receipt-box .receipt-id {
            color: var(--text);
            margin-bottom: 2px;
        }

        .dual-note {
            font-size: 12px;
            color: var(--yellow);
            margin-bottom: 1rem;
            padding: 8px 12px;
            border-left: 2px solid var(--yellow);
            background: var(--yellow-bg);
        }

        .modal-actions {
            display: flex;
            gap: 8px;
        }
        .modal-actions button { flex: 1; }
        .btn-confirm { border-color: var(--gold); color: var(--gold); }

        .spinner {
            width: 14px;
            height: 14px;
            border: 2px solid var(--border);
            border-top-color: var(--text-dim);
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            display: inline-block;
        }

        .chain-arrow {
            text-align: center;
            font-size: 11px;
            color: var(--text-dim);
            font-family: var(--font-mono);
            margin: 8px 0;
        }

        .controls {
            display: flex;
            gap: 8px;
            align-items: center;
        }
        select {
            background: var(--bg-card);
            border: 1px solid var(--border);
            color: var(--text);
            padding: 6px 10px;
            border-radius: 6px;
            font-family: inherit;
            font-size: 13px;
        }
    </style>
</head>
<body>
<div class="page">

<div class="header">
    <div>
        <div class="header-title">WINDI INSTITUTE · SERVICE CONTROL</div>
        <div class="header-main">Service Control Panel v2.1 · §227</div>
    </div>
    <div class="controls">
        <select id="lang-toggle" onchange="setLang(this.value)">
            <option value="de">DE</option>
            <option value="en" selected>EN</option>
            <option value="pt">PT</option>
        </select>
        <button onclick="toggleTheme()" title="Toggle Theme">☀</button>
        <div class="header-status">
            <div class="status-dot"></div>
            <span class="status-text" id="active-count">— / — active</span>
        </div>
    </div>
</div>

<div class="legend">
    <div class="legend-item">
        <div class="legend-dot sealed"></div> SEALED — no restart
    </div>
    <div class="legend-sep"></div>
    <div class="legend-item">
        <div class="legend-dot critical"></div> CRITICAL — dual receipt
    </div>
    <div class="legend-sep"></div>
    <div class="legend-item">
        <div class="legend-dot standard"></div> STANDARD — single confirm
    </div>
    <div class="legend-sep"></div>
    <div class="legend-item">
        <span style="font-size:11px;padding:2px 6px;border-radius:3px;background:var(--blue);color:white">REMOTE</span> Galho B
    </div>
    <div class="legend-sep"></div>
    <div class="legend-item">
        <span style="font-size:11px;padding:2px 6px;border-radius:3px;background:#0db7ed;color:white">DOCKER</span>
    </div>
</div>

<div id="services-list"></div>

<div id="modal-overlay">
    <div class="modal-card">
        <div class="modal-header">
            <div id="modal-tier-dot" class="modal-tier-dot"></div>
            <div class="modal-title" id="modal-title">Confirmar restart</div>
        </div>
        <div class="modal-body" id="modal-body"></div>

        <div id="step1">
            <div class="receipt-box">
                <div class="label">I9 — confirmação humana obrigatória</div>
                <div>Acção: restart_initiated</div>
                <div id="modal-svc-name">target: —</div>
                <div id="modal-ts">timestamp: —</div>
            </div>
            <div id="dual-note" class="dual-note" style="display:none">
                Serviço crítico — confirmação dupla activada. O segundo receipt será gerado após restart completo.
            </div>
            <div class="modal-actions">
                <button onclick="cancelRestart()">Cancelar</button>
                <button onclick="confirmRestart()" class="btn-confirm">Confirmar restart ↗</button>
            </div>
        </div>

        <div id="step2" style="display:none">
            <div class="receipt-box">
                <div class="receipt-label">Receipt 1 — início</div>
                <div class="receipt-id" id="receipt1-id"></div>
                <div>action: restart_initiated</div>
                <div>status: sealed ✓</div>
            </div>
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:1rem">
                <div class="spinner"></div>
                <span style="font-size:13px;color:var(--text-dim)">Restarting service…</span>
            </div>
        </div>

        <div id="step3" style="display:none">
            <div class="receipt-box">
                <div class="receipt-label">Receipt 1 — início</div>
                <div class="receipt-id" id="r1-id"></div>
                <div>action: restart_initiated · sealed ✓</div>
            </div>
            <div class="chain-arrow">↓ parent_receipt_id chain</div>
            <div class="receipt-box success">
                <div class="receipt-label" style="color:var(--green)">Receipt 2 — conclusão</div>
                <div class="receipt-id" id="r2-id"></div>
                <div>action: restart_completed · sealed ✓</div>
                <div id="r2-health"></div>
            </div>
            <button onclick="closeModal()" style="width:100%;margin-top:1rem">Fechar</button>
        </div>

        <div id="step-error" style="display:none">
            <div class="receipt-box" style="border-color:var(--red)">
                <div class="receipt-label" style="color:var(--red)">Restart Failed</div>
                <div id="error-msg" style="color:var(--red)"></div>
            </div>
            <button onclick="closeModal()" style="width:100%;margin-top:1rem">Fechar</button>
        </div>
    </div>
</div>

</div>

<script>
const API_BASE = window.location.pathname.replace(/\\/$/, '');
const TIER_COLOR = {SEALED:'#A32D2D', CRITICAL:'#BA7517', STANDARD:'#3B6D11'};
const TIER_COLOR_NOIR = {SEALED:'#E24B4A', CRITICAL:'#F5A623', STANDARD:'#90c739'};

let services = [];
let currentSvc = null;
let currentDID = 'did:windi:dragon-001';

// I18N
const i18n = {
    en: { restart: 'restart ↗', blocked: 'blocked', online: 'running', offline: 'stopped' },
    de: { restart: 'neustart ↗', blocked: 'blockiert', online: 'läuft', offline: 'gestoppt' },
    pt: { restart: 'reiniciar ↗', blocked: 'bloqueado', online: 'executando', offline: 'parado' }
};
let lang = localStorage.getItem('windi-lang') || 'en';
function t(key) { return i18n[lang]?.[key] || key; }
function setLang(l) { lang = l; localStorage.setItem('windi-lang', l); render(); }

// Theme
function toggleTheme() {
    const html = document.documentElement;
    const current = html.getAttribute('data-theme');
    const next = current === 'noir' ? 'light' : 'noir';
    html.setAttribute('data-theme', next);
    localStorage.setItem('windi-theme', next);
}
const savedTheme = localStorage.getItem('windi-theme') || 'noir';
document.documentElement.setAttribute('data-theme', savedTheme);

function nowStr() { return new Date().toISOString().replace('T',' ').substr(0,19)+' UTC'; }

async function loadServices() {
    try {
        const r = await fetch(API_BASE + '/api/services');
        const data = await r.json();
        services = data.services;
        const active = services.filter(s => s.overall === 'online').length;
        document.getElementById('active-count').textContent = active + ' / ' + services.length + ' active';
        render();
    } catch(e) {
        console.error('Failed to load services:', e);
    }
}

function render() {
    const list = document.getElementById('services-list');
    list.innerHTML = '';

    services.forEach(svc => {
        const tier = svc.tier || 'STANDARD';
        const blocked = tier === 'SEALED';
        const isOnline = svc.overall === 'online';
        const statusText = isOnline ? t('online') : t('offline');
        const isDocker = svc.docker || false;
        const isRemote = svc.remote || false;
        const remoteHost = svc.remote_host || '';

        // Build port display with host info
        let portDisplay = `:${svc.port} · ${statusText}`;
        if (isRemote && remoteHost) {
            portDisplay = `${remoteHost}:${svc.port} · ${statusText}`;
        }

        // Build type badges
        let typeBadges = '';
        if (isDocker) {
            typeBadges += '<span style="font-size:10px;padding:2px 5px;border-radius:3px;background:#0db7ed;color:white;margin-left:6px">DOCKER</span>';
        }
        if (isRemote) {
            typeBadges += '<span style="font-size:10px;padding:2px 5px;border-radius:3px;background:#1D5AA8;color:white;margin-left:6px">GALHO B</span>';
        }

        const row = document.createElement('div');
        row.className = 'service-row';
        row.innerHTML = `
            <div class="service-info">
                <div class="service-status-dot ${svc.overall}"></div>
                <div class="service-details">
                    <div class="service-name">${svc.display}${typeBadges}</div>
                    <div class="service-port">${portDisplay}</div>
                </div>
                <div class="tier-badge ${tier.toLowerCase()}">${tier}</div>
            </div>
            <div>
                ${blocked || isRemote
                    ? `<div class="btn-blocked">${isRemote ? 'remote' : t('blocked')}</div>`
                    : `<button onclick="openModal('${svc.service}')">${t('restart')}</button>`
                }
            </div>
        `;
        list.appendChild(row);
    });
}

function openModal(serviceName) {
    currentSvc = services.find(s => s.service === serviceName);
    if (!currentSvc) return;

    const tier = currentSvc.tier || 'STANDARD';
    const isNoir = document.documentElement.getAttribute('data-theme') === 'noir';
    const colors = isNoir ? TIER_COLOR_NOIR : TIER_COLOR;

    document.getElementById('modal-overlay').classList.add('active');
    document.getElementById('step1').style.display = 'block';
    document.getElementById('step2').style.display = 'none';
    document.getElementById('step3').style.display = 'none';
    document.getElementById('step-error').style.display = 'none';

    document.getElementById('modal-tier-dot').style.background = colors[tier];
    document.getElementById('modal-title').textContent = 'Confirmar restart — ' + currentSvc.display;
    document.getElementById('modal-body').textContent = tier === 'CRITICAL'
        ? 'Serviço crítico. O restart será registado em dois receipts encadeados (início + conclusão).'
        : 'Confirmação I9 necessária. A acção será selada no ledger com receipt auditável.';
    document.getElementById('modal-svc-name').textContent = 'target: ' + currentSvc.service;
    document.getElementById('modal-ts').textContent = 'timestamp: ' + nowStr();
    document.getElementById('dual-note').style.display = tier === 'CRITICAL' ? 'block' : 'none';

    document.getElementById('modal-overlay').scrollIntoView({behavior:'smooth', block:'nearest'});
}

function cancelRestart() {
    document.getElementById('modal-overlay').classList.remove('active');
    currentSvc = null;
}

async function confirmRestart() {
    if (!currentSvc) return;

    // Show step 2 (loading)
    document.getElementById('step1').style.display = 'none';
    document.getElementById('step2').style.display = 'block';
    document.getElementById('receipt1-id').textContent = 'Generating...';

    try {
        const r = await fetch(`${API_BASE}/api/services/${currentSvc.service}/restart`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                actor_did: currentDID,
                reason: 'Manual restart via Control Panel v2.0'
            })
        });

        const data = await r.json();

        if (r.ok && data.receipts) {
            // Show step 3 (success)
            document.getElementById('step2').style.display = 'none';
            document.getElementById('step3').style.display = 'block';

            document.getElementById('r1-id').textContent = data.receipts.initiated.receipt_id;
            document.getElementById('r2-id').textContent = data.receipts.completed.receipt_id;

            const health = data.receipts.completed.post_health?.status || 'unknown';
            document.getElementById('r2-health').textContent = `health: ${health} · port ${currentSvc.port}`;

            // Reload services
            setTimeout(loadServices, 1000);
        } else {
            // Show error
            document.getElementById('step2').style.display = 'none';
            document.getElementById('step-error').style.display = 'block';
            document.getElementById('error-msg').textContent = data.message || data.error || 'Restart failed';
        }
    } catch(e) {
        document.getElementById('step2').style.display = 'none';
        document.getElementById('step-error').style.display = 'block';
        document.getElementById('error-msg').textContent = 'Network error: ' + e.message;
    }
}

function closeModal() {
    document.getElementById('modal-overlay').classList.remove('active');
    currentSvc = null;
}

// Init
loadServices();
setInterval(loadServices, 30000);
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
║   W-SERVICE-CONTROL v2.1.0 — §227 Galho B Update             ║
║   Port: {PORT}                                                 ║
║   Invariants: I1, I9, I11                                    ║
║   Features: Tier Protection · Docker · Remote · Dual Receipt ║
║   New: W-MAIL-001 (Docker) · W-OLLAMA-001 (Galho B)          ║
║   "Se não consegues controlar, não consegues escalar."       ║
╚══════════════════════════════════════════════════════════════╝
    """)
    app.run(host="0.0.0.0", port=PORT, debug=False)
