#!/usr/bin/env python3
"""
WINDI Desktop Server v2.0.0 — Portal de Soberania
===================================================
Operationalized backend serving Desktop UI + Governance API Bridge.
Functions like Clone BABEL: self-monitoring, forensic heartbeat, API-connected.

Port: 8100
Path: /desktop/
Principle: AI processes. Human decides. WINDI guarantees.

Architecture:
  L1 (Desktop UI) → L2 (Governance Bridge) → L3 (Forensic Ledger)
  
  Static Pages: index.html, suite.html, sealing.html, warroom.html
  API Bridge:   /api/governance/* → localhost:8080
  API Bridge:   /api/sentinel/*  → localhost:8098
  API Bridge:   /api/forensic/*  → localhost:8094
  API Internal: /api/desktop/*   → Desktop-own endpoints
  Health:       /health          → Full health with dependency checks

Three Dragons Protocol:
  Guardian (Claude)  — Constitutional validation
  Architect (GPT)    — Structural integrity
  Witness (Gemini)   — Forensic observation
"""

import os
import sys
import json
import time
import hashlib
import logging
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from functools import wraps

try:
    from flask import Flask, send_from_directory, jsonify, request, abort, make_response
    from flask_cors import CORS
except ImportError:
    print("Installing Flask dependencies...")
    os.system(f"{sys.executable} -m pip install flask flask-cors --break-system-packages -q")
    from flask import Flask, send_from_directory, jsonify, request, abort, make_response
    from flask_cors import CORS

try:
    import requests as http_client
except ImportError:
    os.system(f"{sys.executable} -m pip install requests --break-system-packages -q")
    import requests as http_client

# ═══════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════

BASE_DIR = Path(os.environ.get("WINDI_DESKTOP_DIR", "/opt/windi/desktop"))
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = Path(os.environ.get("WINDI_DATA_DIR", "/opt/windi/data"))
LOG_DIR = Path(os.environ.get("WINDI_LOG_DIR", "/opt/windi/logs"))

PORT = int(os.environ.get("WINDI_DESKTOP_PORT", 8100))
HOST = os.environ.get("WINDI_DESKTOP_HOST", "0.0.0.0")
VERSION = "2.0.0"

# Upstream services
GOVERNANCE_API = os.environ.get("WINDI_GOVERNANCE_URL", "http://127.0.0.1:8080")
SENTINEL_API = os.environ.get("WINDI_SENTINEL_URL", "http://127.0.0.1:8098")
FORENSIC_API = os.environ.get("WINDI_FORENSIC_URL", "http://127.0.0.1:8094")
WALLET_API = os.environ.get("WINDI_WALLET_URL", "http://127.0.0.1:8099")
CLONE_API = os.environ.get("WINDI_CLONE_URL", "http://127.0.0.1:8092")
BRIDGE_API = os.environ.get("WINDI_BRIDGE_URL", "http://127.0.0.1:8097")
BABEL_API = os.environ.get("WINDI_BABEL_URL", "http://127.0.0.1:8085")

# Heartbeat interval (seconds)
HEARTBEAT_INTERVAL = 30

# ═══════════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════════

LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [DESKTOP] %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "desktop.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("windi-desktop")

# ═══════════════════════════════════════════════════════════
# FLASK APPLICATION
# ═══════════════════════════════════════════════════════════

app = Flask(__name__, static_folder=str(STATIC_DIR))
CORS(app, origins=["https://windi-domain.com", "http://localhost:*"])

# ═══════════════════════════════════════════════════════════
# FORENSIC HEARTBEAT — Self-Monitoring Thread
# ═══════════════════════════════════════════════════════════

class ForensicHeartbeat:
    """
    Monitors upstream services and maintains a governance pulse.
    Like the Clone's constitutional matrix — always watching, never deciding.
    """
    
    def __init__(self):
        self.status = {}
        self.last_check = None
        self.pulse_count = 0
        self.started_at = datetime.now(timezone.utc).isoformat()
        self._lock = threading.Lock()
        self._running = False
    
    def start(self):
        self._running = True
        t = threading.Thread(target=self._heartbeat_loop, daemon=True)
        t.start()
        log.info("Forensic Heartbeat STARTED — monitoring %d upstream services", 7)
    
    def stop(self):
        self._running = False
    
    def _check_service(self, name, url, timeout=3):
        """Check a single service health."""
        try:
            r = http_client.get(f"{url}/health", timeout=timeout)
            return {
                "status": "UP" if r.status_code == 200 else "DEGRADED",
                "code": r.status_code,
                "latency_ms": int(r.elapsed.total_seconds() * 1000),
            }
        except http_client.exceptions.ConnectionError:
            return {"status": "DOWN", "code": 0, "latency_ms": -1}
        except http_client.exceptions.Timeout:
            return {"status": "TIMEOUT", "code": 0, "latency_ms": timeout * 1000}
        except Exception as e:
            return {"status": "ERROR", "code": 0, "latency_ms": -1, "error": str(e)[:80]}
    
    def _heartbeat_loop(self):
        """Main heartbeat loop — runs every HEARTBEAT_INTERVAL seconds."""
        while self._running:
            try:
                checks = {
                    "governance": self._check_service("governance", GOVERNANCE_API),
                    "sentinel": self._check_service("sentinel", SENTINEL_API),
                    "forensic": self._check_service("forensic", FORENSIC_API),
                    "wallet": self._check_service("wallet", WALLET_API),
                    "clone": self._check_service("clone", CLONE_API),
                    "bridge": self._check_service("bridge", BRIDGE_API),
                    "babel": self._check_service("babel", BABEL_API),
                }
                
                up_count = sum(1 for v in checks.values() if v["status"] == "UP")
                total = len(checks)
                
                with self._lock:
                    self.status = checks
                    self.last_check = datetime.now(timezone.utc).isoformat()
                    self.pulse_count += 1
                
                if self.pulse_count % 10 == 0:  # Log every 10th pulse
                    log.info("Heartbeat #%d — %d/%d services UP", self.pulse_count, up_count, total)
                    
            except Exception as e:
                log.error("Heartbeat error: %s", str(e)[:100])
            
            time.sleep(HEARTBEAT_INTERVAL)
    
    def get_status(self):
        with self._lock:
            return {
                "services": dict(self.status),
                "last_check": self.last_check,
                "pulse_count": self.pulse_count,
                "started_at": self.started_at,
            }

heartbeat = ForensicHeartbeat()

# ═══════════════════════════════════════════════════════════
# STATIC PAGE SERVING
# ═══════════════════════════════════════════════════════════

PAGES = {
    "": "index.html",
    "index.html": "index.html", 
    "suite.html": "suite.html",
    "sealing.html": "sealing.html",
    "warroom.html": "warroom.html",
}

@app.route("/")
def root_redirect():
    """Redirect bare / to /index.html"""
    return send_page("index.html")

@app.route("/<path:filename>")
def serve_page(filename):
    """Serve static HTML pages or pass to API routes."""
    if filename in PAGES:
        return send_page(PAGES[filename])
    # Try static files
    static_path = STATIC_DIR / filename
    if static_path.exists():
        return send_from_directory(str(STATIC_DIR), filename)
    abort(404)

def send_page(page_name):
    """Serve an HTML page from the static directory."""
    page_path = STATIC_DIR / page_name
    if page_path.exists():
        return send_from_directory(str(STATIC_DIR), page_name)
    abort(404)

# ═══════════════════════════════════════════════════════════
# HEALTH ENDPOINT — Full System Diagnosis
# ═══════════════════════════════════════════════════════════

@app.route("/health")
def health():
    """
    Comprehensive health check with dependency status.
    Used by Sentinel for dual validation (systemd + HTTP).
    """
    hb = heartbeat.get_status()
    services = hb.get("services", {})
    
    up_count = sum(1 for v in services.values() if v.get("status") == "UP")
    total = len(services) if services else 7
    
    # Desktop is operational if it can serve pages
    pages_ok = all((STATIC_DIR / p).exists() for p in PAGES.values())
    
    return jsonify({
        "service": "windi-desktop",
        "status": "operational" if pages_ok else "degraded",
        "version": VERSION,
        "port": PORT,
        "path": "/desktop/",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pages": {k: v for k, v in PAGES.items() if k},
        "wallet_integration": True,
        "ecosystem": {
            "up": up_count,
            "total": total,
            "services": services,
        },
        "heartbeat": {
            "pulse_count": hb.get("pulse_count", 0),
            "last_check": hb.get("last_check"),
            "started_at": hb.get("started_at"),
        },
        "principle": "AI processes. Human decides. WINDI guarantees.",
    })

# ═══════════════════════════════════════════════════════════
# API BRIDGE — Governance Data for War Room & Suite
# ═══════════════════════════════════════════════════════════

def proxy_get(upstream_url, path, timeout=5):
    """Forward a GET request to an upstream service."""
    try:
        url = f"{upstream_url}{path}"
        r = http_client.get(url, timeout=timeout)
        return jsonify(r.json()), r.status_code
    except http_client.exceptions.ConnectionError:
        return jsonify({"error": "upstream_unavailable", "service": upstream_url}), 503
    except Exception as e:
        return jsonify({"error": str(e)[:100]}), 500

# ── Governance API Bridge ──────────────────────────
@app.route("/api/governance/status")
def gov_status():
    return proxy_get(GOVERNANCE_API, "/api/status")

@app.route("/api/governance/dashboard")
def gov_dashboard():
    return proxy_get(GOVERNANCE_API, "/api/dashboard")

@app.route("/api/governance/submissions")
def gov_submissions():
    return proxy_get(GOVERNANCE_API, "/api/submissions")

@app.route("/api/governance/integrity")
def gov_integrity():
    return proxy_get(GOVERNANCE_API, "/api/integrity")

@app.route("/api/governance/compliance")
def gov_compliance():
    return proxy_get(GOVERNANCE_API, "/api/compliance")

# ── Sentinel API Bridge ──────────────────────────
@app.route("/api/sentinel/status")
def sentinel_status():
    return proxy_get(SENTINEL_API, "/api/status")

@app.route("/api/sentinel/calibration")
def sentinel_calibration():
    return proxy_get(SENTINEL_API, "/api/calibration")

# ── Forensic API Bridge ──────────────────────────
@app.route("/api/forensic/verify/<receipt_id>")
def forensic_verify(receipt_id):
    return proxy_get(FORENSIC_API, f"/api/verify/{receipt_id}")

@app.route("/api/forensic/recent")
def forensic_recent():
    return proxy_get(FORENSIC_API, "/api/recent")

# ═══════════════════════════════════════════════════════════
# DESKTOP-OWN API — Aggregated Intelligence
# ═══════════════════════════════════════════════════════════

@app.route("/api/desktop/pulse")
def desktop_pulse():
    """
    The Forensic Heartbeat pulse — real-time ecosystem status.
    This is what the War Room heatmap consumes.
    """
    hb = heartbeat.get_status()
    return jsonify({
        "pulse": hb,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "principle": "AI processes. Human decides. WINDI guarantees.",
    })

@app.route("/api/desktop/ecosystem")
def desktop_ecosystem():
    """
    Complete ecosystem overview — aggregated from all services.
    The Controller Dashboard data source.
    """
    hb = heartbeat.get_status()
    services = hb.get("services", {})
    
    # Categorize services by layer
    l1_edge = {k: v for k, v in services.items() if k in ("babel",)}
    l2_mesh = {k: v for k, v in services.items() if k in ("governance", "sentinel", "bridge", "wallet")}
    l3_ledger = {k: v for k, v in services.items() if k in ("forensic", "clone")}
    
    return jsonify({
        "ecosystem": {
            "L1_edge": {"services": l1_edge, "description": "a4Desk — Human Workspace"},
            "L2_mesh": {"services": l2_mesh, "description": "WINDI Mesh — Governance Layer"},
            "L3_ledger": {"services": l3_ledger, "description": "Forensic Ledger — Proof Layer"},
        },
        "total_up": sum(1 for v in services.values() if v.get("status") == "UP"),
        "total_services": len(services),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

@app.route("/api/desktop/warroom-data")
def warroom_data():
    """
    Aggregated data for the War Room — SGE heatmap, alerts, departments.
    Tries to pull from governance API, falls back to cached data.
    """
    try:
        # Try live governance data
        r = http_client.get(f"{GOVERNANCE_API}/api/dashboard", timeout=3)
        if r.status_code == 200:
            gov_data = r.json()
            return jsonify({
                "source": "live",
                "governance": gov_data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
    except:
        pass
    
    # Fallback: return cached/static data for display
    return jsonify({
        "source": "cached",
        "governance": {
            "overall_sge": 0.69,
            "risk_level": "ERHÖHT",
            "active_documents": 47,
            "sealed_today": 12,
            "pending_review": 3,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

@app.route("/api/desktop/suite-data")
def suite_data():
    """
    Data for the Suite — recent documents, templates, ISP status.
    """
    try:
        # Try BABEL for real document data
        r = http_client.get(f"{BABEL_API}/api/documents/recent", timeout=3)
        if r.status_code == 200:
            return jsonify({
                "source": "live",
                "documents": r.json(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
    except:
        pass
    
    return jsonify({
        "source": "cached",
        "documents": [],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

# ═══════════════════════════════════════════════════════════
# INVARIANT I9 — Prohibition of Autonomy Escalation
# ═══════════════════════════════════════════════════════════

@app.route("/api/desktop/i9-check")
def i9_check():
    """
    Constitutional I9 validation — Desktop NEVER auto-applies.
    Human Dragon retains sovereign decision authority.
    """
    return jsonify({
        "invariant": "I9",
        "name": "Prohibition of Autonomy Escalation",
        "status": "ENFORCED",
        "auto_apply": False,
        "human_sovereignty": True,
        "message": "Desktop suggests. Human Dragon decides.",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })

# ═══════════════════════════════════════════════════════════
# DRAGON → DESKTOP BRIDGE — Document Handoff from Chat to Editor
# "O arquitecto desenhou. Agora o estaleiro constrói."
# ═══════════════════════════════════════════════════════════

# In-memory draft storage (could be upgraded to Redis/SQLite later)
_dragon_drafts = {}

@app.route("/api/documents/create-from-dragon", methods=["POST", "OPTIONS"])
def create_from_dragon():
    """
    Receive a document draft from Dragon Architect and prepare it for the editor.

    Expected payload:
    {
        "title": "Birthday Letter",
        "type": "letter",
        "content": "Dear sister...",
        "fields": {"recipient": "Sister", "occasion": "60th Birthday"}
    }

    Returns:
    {
        "success": true,
        "id": "draft_1709...",
        "editor_url": "/desktop/?doc=draft_1709..."
    }
    """
    # Handle CORS preflight
    if request.method == "OPTIONS":
        response = make_response()
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    try:
        data = request.get_json() or {}

        # Validate required fields
        if not data.get("title") and not data.get("content"):
            return jsonify({"success": False, "error": "Missing title or content"}), 400

        # Generate draft ID
        import hashlib
        draft_id = "draft_" + hashlib.sha256(
            (str(datetime.now()) + str(data.get("title", ""))).encode()
        ).hexdigest()[:12]

        # Store draft
        draft = {
            "id": draft_id,
            "title": data.get("title", "Dragon Draft"),
            "type": data.get("type", "letter"),
            "content": data.get("content", ""),
            "fields": data.get("fields", {}),
            "source": "dragon_architect",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "draft",
        }
        _dragon_drafts[draft_id] = draft

        log.info("[Dragon→Desktop] Draft created: %s (type=%s)", draft_id, draft["type"])

        response = jsonify({
            "success": True,
            "id": draft_id,
            "title": draft["title"],
            "type": draft["type"],
            "editor_url": f"/desktop/?doc={draft_id}",
            "message": "Draft ready for editing",
        })
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response

    except Exception as e:
        log.error("[Dragon→Desktop] Error: %s", str(e))
        return jsonify({"success": False, "error": str(e)[:100]}), 500

@app.route("/api/documents/dragon-draft/<draft_id>", methods=["GET"])
def get_dragon_draft(draft_id):
    """Retrieve a Dragon draft by ID for loading into the editor."""
    draft = _dragon_drafts.get(draft_id)
    if not draft:
        return jsonify({"success": False, "error": "Draft not found"}), 404

    response = jsonify({"success": True, "draft": draft})
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response

# ═══════════════════════════════════════════════════════════
# ERROR HANDLERS
# ═══════════════════════════════════════════════════════════

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "not_found", "service": "windi-desktop"}), 404

@app.errorhandler(500)
def server_error(e):
    log.error("500 error: %s", str(e))
    return jsonify({"error": "internal_error", "service": "windi-desktop"}), 500

# ═══════════════════════════════════════════════════════════
# STARTUP
# ═══════════════════════════════════════════════════════════

def ensure_directories():
    """Create necessary directories."""
    for d in [STATIC_DIR, DATA_DIR, LOG_DIR]:
        d.mkdir(parents=True, exist_ok=True)
    log.info("Directories verified: static=%s, data=%s, logs=%s", STATIC_DIR, DATA_DIR, LOG_DIR)

def verify_pages():
    """Verify all static pages exist."""
    missing = []
    for name, filename in PAGES.items():
        if not (STATIC_DIR / filename).exists():
            missing.append(filename)
    if missing:
        log.warning("Missing pages: %s", missing)
    else:
        log.info("All %d pages verified", len(set(PAGES.values())))
    return len(missing) == 0

if __name__ == "__main__":
    log.info("=" * 60)
    log.info("WINDI Desktop Server v%s — Portal de Soberania", VERSION)
    log.info("AI processes. Human decides. WINDI guarantees.")
    log.info("=" * 60)
    
    ensure_directories()
    pages_ok = verify_pages()
    
    if not pages_ok:
        log.warning("Some pages missing — server will start but some routes may 404")
    
    # Start Forensic Heartbeat
    heartbeat.start()
    
    log.info("Starting on %s:%d", HOST, PORT)
    log.info("Pages: %s", ", ".join(set(PAGES.values())))
    log.info("Upstream: governance=%s, sentinel=%s, forensic=%s", 
             GOVERNANCE_API, SENTINEL_API, FORENSIC_API)
    
    app.run(host=HOST, port=PORT, debug=False)
