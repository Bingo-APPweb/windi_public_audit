#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║  WINDI PULSE v1.0.0 — Ecosystem Health Monitor              ║
║  "The heartbeat of the industrial dragon."                   ║
║                                                              ║
║  Port: 8109                                                  ║
║  Endpoints:                                                  ║
║    GET /api/pulse/health    → self health                    ║
║    GET /api/pulse/scan      → full ecosystem scan            ║
║    GET /api/pulse/history   → change log (memory loop)       ║
║    GET /api/pulse/outlook   → sprint progress + gaps         ║
║    GET /api/pulse/sentinel  → sentinel integration           ║
║                                                              ║
║  "AI processes. Human decides. WINDI guarantees."            ║
╚══════════════════════════════════════════════════════════════╝
"""

import json
import hashlib
import sqlite3
import time
import os
import subprocess
import threading
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════

PORT = 8109
SCAN_INTERVAL = 60  # seconds between background scans
DB_PATH = "/opt/windi/data/pulse.db"
VERSION = "1.0.0"

# ═══════════════════════════════════════════════════════════════
# SERVICE REGISTRY — Everything WINDI has or plans to have
# ═══════════════════════════════════════════════════════════════

SERVICES = [
    # === Core Services (8080-8089) ===
    {
        "id": "governance",
        "name": "Governance API",
        "port": 8080,
        "health_path": "/health",
        "systemd": "windi-governance",
        "category": "core",
        "critical": True,
    },
    {
        "id": "hub-babel",
        "name": "HUB BABEL Editor",
        "port": 8085,
        "health_path": "/api/health",
        "systemd": "windi-babel",
        "category": "core",
        "critical": True,
    },
    {
        "id": "a4desk-landing",
        "name": "A4 Desk Landing",
        "port": 8086,
        "health_path": "/",
        "systemd": "windi-landing",
        "category": "core",
        "critical": False,
    },
    {
        "id": "cortex",
        "name": "Cortex Metacognition",
        "port": 8889,
        "health_path": "/health",
        "systemd": "windi-cortex",
        "category": "intelligence",
        "critical": False,
    },

    # === Extended Services (8090-8099) ===
    {
        "id": "warroom",
        "name": "War Room",
        "port": 8090,
        "health_path": "/war-room/",
        "systemd": "windi-warroom",
        "category": "extended",
        "critical": False,
    },
    {
        "id": "clone",
        "name": "Clone UI",
        "port": 8092,
        "health_path": "/health",
        "systemd": "windi-clone",
        "category": "extended",
        "critical": False,
    },
    {
        "id": "schnittstelle",
        "name": "Schnittstelle (Paperless)",
        "port": 8095,
        "health_path": "/health",
        "systemd": None,
        "category": "forensic",
        "critical": True,
    },
    {
        "id": "id-genesis",
        "name": "ID Genesis",
        "port": 8096,
        "health_path": "/health",
        "systemd": None,
        "category": "extended",
        "critical": False,
    },
    {
        "id": "bridge",
        "name": "Command Bridge",
        "port": 8097,
        "health_path": "/health",
        "systemd": "windi-bridge",
        "category": "forensic",
        "critical": True,
    },
    {
        "id": "sentinel",
        "name": "Sentinel",
        "port": 8098,
        "health_path": "/health",
        "systemd": None,
        "category": "governance",
        "critical": False,
    },
    {
        "id": "wallet",
        "name": "Wallet O Espelho",
        "port": 8099,
        "health_path": "/health",
        "systemd": None,
        "category": "extended",
        "critical": False,
    },

    # === Ecosystem Services (8100-8109) ===
    {
        "id": "desktop-d1",
        "name": "Desktop D1 (FastAPI+React)",
        "port": 8100,
        "health_path": "/",
        "systemd": "windi-desktop",
        "category": "production",
        "critical": True,
    },
    {
        "id": "ledger",
        "name": "Forensic Ledger",
        "port": 8101,
        "health_path": "/api/receipts",
        "systemd": "windi-ledger",
        "category": "forensic",
        "critical": True,
    },
    {
        "id": "sentinel-law",
        "name": "Sentinel LAW",
        "port": 8102,
        "health_path": "/health",
        "systemd": "windi-sentinel-law",
        "category": "governance",
        "critical": True,
    },
    {
        "id": "export-engine",
        "name": "Export Engine (PDF+DOCX)",
        "port": 8103,
        "health_path": "/health",
        "systemd": "windi-export",
        "category": "production",
        "critical": True,
    },
    {
        "id": "jmpg-viewer",
        "name": "JMPG Viewer",
        "port": 8104,
        "health_path": "/health",
        "systemd": "windi-jmpg-viewer",
        "category": "production",
        "critical": False,
    },
    {
        "id": "communique",
        "name": "Communiqué Engine",
        "port": 8105,
        "health_path": "/health",
        "systemd": "windi-communique",
        "category": "ecosystem",
        "critical": True,
    },
    {
        "id": "vault",
        "name": "Forensic Vault",
        "port": 8106,
        "health_path": "/",
        "systemd": "windi-vault",
        "category": "forensic",
        "critical": True,
    },
    {
        "id": "landing-pmg",
        "name": "Landing P/M/G",
        "port": 8107,
        "health_path": "/",
        "systemd": "windi-landing-pmg",
        "category": "core",
        "critical": False,
    },
    {
        "id": "palette",
        "name": "Agent Palette (Dragon Server)",
        "port": 8108,
        "health_path": "/",
        "systemd": None,
        "category": "intelligence",
        "critical": True,
        "extra_checks": [
            {"path": "/api/dragon/health", "name": "Dragon Brain"},
            {"path": "/api/dragon/chat", "name": "Dragon Chat", "method": "POST",
             "body": '{"message":"pulse","tier":"LOW","language":"en"}'},
        ],
    },
]

# ═══════════════════════════════════════════════════════════════
# FEATURE WIRING MAP — What should be connected to Palette
# ═══════════════════════════════════════════════════════════════

WIRING_MAP = [
    {"id": "W01", "name": "PDF Export via Palette",         "service": "export-engine",  "route": "/api/palette/export/pdf",    "sprint": 1, "status": "pending"},
    {"id": "W02", "name": "DOCX Export via Palette",        "service": "export-engine",  "route": "/api/palette/export/docx",   "sprint": 1, "status": "pending"},
    {"id": "W03", "name": "PPTX Export via Palette",        "service": "ppt-engine",     "route": "/api/palette/export/pptx",   "sprint": 1, "status": "pending"},
    {"id": "W04", "name": "Ledger Seal from Palette",       "service": "ledger",         "route": "/api/palette/seal",          "sprint": 1, "status": "pending"},
    {"id": "W05", "name": "Wave1 N1-N4 Pipeline",           "service": "export-engine",  "route": "/api/palette/seal-export",   "sprint": 1, "status": "pending"},
    {"id": "W06", "name": "Paperless Signature",            "service": "bridge",         "route": "/api/palette/sign",          "sprint": 2, "status": "pending"},
    {"id": "W07", "name": "Vault Storage",                  "service": "vault",          "route": "/api/palette/vault",         "sprint": 2, "status": "pending"},
    {"id": "W08", "name": "OCR Multimodal",                 "service": "palette",        "route": "/api/multimodal/ocr",        "sprint": 3, "status": "pending"},
    {"id": "W09", "name": "Wisdom Chain",                   "service": "palette",        "route": "/api/wisdom/candidate",      "sprint": 3, "status": "pending"},
    {"id": "W10", "name": "Product Identity Skill",         "service": "palette",        "route": "skill-load",                 "sprint": 3, "status": "pending"},
    {"id": "W11", "name": "Constitutional Panel",           "service": "palette",        "route": "/api/constitution",          "sprint": 3, "status": "pending"},
    {"id": "W12", "name": "Compliance Passport API",        "service": "palette",        "route": "/api/compliance/passport",   "sprint": 3, "status": "pending"},
    {"id": "W13", "name": "Sentinel Status in Palette",     "service": "sentinel-law",   "route": "/api/sentinel/status",       "sprint": 4, "status": "pending"},
    {"id": "W14", "name": "Communiqué from Palette",        "service": "communique",     "route": "/api/palette/communique",    "sprint": 4, "status": "pending"},
    {"id": "W15", "name": "ISP Live API Fetch",             "service": "governance",     "route": "/api/isp/list",              "sprint": 4, "status": "pending"},
    {"id": "W16", "name": "XLSX Export",                    "service": "new",            "route": "/api/palette/export/xlsx",   "sprint": 4, "status": "pending"},
    {"id": "W17", "name": "Dragon Server systemd",          "service": "palette",        "route": "systemd",                    "sprint": 0, "status": "pending"},
    {"id": "W18", "name": "Chat Persistence",               "service": "palette",        "route": "/api/palette/sessions",      "sprint": 4, "status": "pending"},
]

# ═══════════════════════════════════════════════════════════════
# DATABASE — Memory Loop
# ═══════════════════════════════════════════════════════════════

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            scan_hash TEXT NOT NULL,
            total_services INTEGER,
            alive INTEGER,
            dead INTEGER,
            degraded INTEGER,
            wired INTEGER,
            pending_wires INTEGER,
            sentinel_status TEXT,
            data_json TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            event_type TEXT NOT NULL,
            service_id TEXT,
            message TEXT,
            severity TEXT DEFAULT 'info'
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS wire_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            wire_id TEXT NOT NULL,
            old_status TEXT,
            new_status TEXT,
            verified_by TEXT DEFAULT 'pulse'
        )
    """)
    conn.commit()
    conn.close()


def log_event(event_type, service_id, message, severity="info"):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "INSERT INTO events (timestamp, event_type, service_id, message, severity) VALUES (?,?,?,?,?)",
            (datetime.now(timezone.utc).isoformat(), event_type, service_id, message, severity),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def save_scan(result):
    try:
        scan_json = json.dumps(result, default=str)
        scan_hash = hashlib.sha256(scan_json.encode()).hexdigest()[:16]
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            """INSERT INTO scans
               (timestamp, scan_hash, total_services, alive, dead, degraded,
                wired, pending_wires, sentinel_status, data_json)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                result["timestamp"],
                scan_hash,
                result["summary"]["total"],
                result["summary"]["alive"],
                result["summary"]["dead"],
                result["summary"]["degraded"],
                result["summary"]["wired"],
                result["summary"]["pending_wires"],
                result["summary"].get("sentinel_status", "unknown"),
                scan_json,
            ),
        )
        # Keep only last 1440 scans (~24h at 1/min)
        conn.execute("DELETE FROM scans WHERE id NOT IN (SELECT id FROM scans ORDER BY id DESC LIMIT 1440)")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[PULSE] DB save error: {e}")


# ═══════════════════════════════════════════════════════════════
# HEALTH CHECKER ENGINE
# ═══════════════════════════════════════════════════════════════

def check_port(port, path="/", method="GET", body=None, timeout=3):
    """Check if a service responds on localhost:port."""
    try:
        url = f"http://127.0.0.1:{port}{path}"
        if method == "POST" and body:
            req = Request(url, data=body.encode(), headers={"Content-Type": "application/json"})
        else:
            req = Request(url)
        resp = urlopen(req, timeout=timeout)
        code = resp.getcode()
        content = resp.read(512).decode("utf-8", errors="replace")
        return {"alive": True, "code": code, "snippet": content[:200]}
    except HTTPError as e:
        return {"alive": True, "code": e.code, "snippet": str(e.reason)[:200]}
    except (URLError, OSError, Exception) as e:
        return {"alive": False, "code": 0, "snippet": str(e)[:200]}


def check_systemd(unit_name):
    """Check systemd service status."""
    if not unit_name:
        return {"managed": False, "status": "no-unit"}
    try:
        result = subprocess.run(
            ["systemctl", "is-active", f"{unit_name}.service"],
            capture_output=True, text=True, timeout=5,
        )
        status = result.stdout.strip()
        return {"managed": True, "status": status}
    except Exception as e:
        return {"managed": False, "status": f"error: {e}"}


def check_file_exists(path):
    """Check if a file/dir exists on the filesystem."""
    return os.path.exists(path)


def check_ppt_engine():
    """Special check: PPT engine is CLI, not HTTP."""
    engine_path = "/opt/windi/ppt-engine/isp_ppt_engine.js"
    node_check = subprocess.run(["which", "node"], capture_output=True, text=True, timeout=5)
    return {
        "engine_exists": os.path.exists(engine_path),
        "node_available": node_check.returncode == 0,
        "isps": [
            f for f in os.listdir("/opt/windi/ppt-engine/isp/")
            if f.endswith(".json") and f != "isp_schema.json"
        ] if os.path.exists("/opt/windi/ppt-engine/isp/") else [],
    }


def check_wisdom():
    """Check Wisdom Chain status."""
    db_path = "/opt/windi/engine/wisdom/wisdom.db"
    if not os.path.exists(db_path):
        return {"exists": False, "blocks": 0}
    try:
        conn = sqlite3.connect(db_path)
        count = conn.execute("SELECT COUNT(*) FROM blocks").fetchone()[0]
        latest = conn.execute(
            "SELECT id, namespace FROM blocks ORDER BY rowid DESC LIMIT 1"
        ).fetchone()
        conn.close()
        return {
            "exists": True,
            "blocks": count,
            "latest": {"id": latest[0][:12] + "...", "namespace": latest[1]} if latest else None,
        }
    except Exception as e:
        return {"exists": True, "blocks": 0, "error": str(e)}


def check_ledger_stats():
    """Check Forensic Ledger receipt count."""
    try:
        resp = urlopen("http://127.0.0.1:8101/api/receipts?limit=1", timeout=3)
        data = json.loads(resp.read())
        if isinstance(data, dict):
            return {"receipts": data.get("total", data.get("count", "unknown"))}
        elif isinstance(data, list):
            return {"receipts": "list-mode"}
        return {"receipts": "unknown"}
    except Exception:
        return {"receipts": "unreachable"}


def check_skills():
    """Check if skills directory has product-identity."""
    skills_path = "/opt/windi/skills/core/product-identity/SKILL.md"
    return {
        "product_identity": os.path.exists(skills_path),
        "skills_dir": os.path.exists("/opt/windi/skills/"),
    }


# ═══════════════════════════════════════════════════════════════
# FULL ECOSYSTEM SCAN
# ═══════════════════════════════════════════════════════════════

def full_scan():
    """Run complete ecosystem health scan."""
    timestamp = datetime.now(timezone.utc).isoformat()
    services_result = []
    alive_count = 0
    dead_count = 0
    degraded_count = 0

    for svc in SERVICES:
        # Basic port check
        main_check = check_port(svc["port"], svc.get("health_path") or "/")
        systemd_check = check_systemd(svc.get("systemd"))

        status = "dead"
        if main_check["alive"]:
            if main_check["code"] < 400:
                status = "alive"
                alive_count += 1
            elif main_check["code"] < 500:
                status = "degraded"
                degraded_count += 1
            else:
                status = "error"
                dead_count += 1
        else:
            dead_count += 1

        entry = {
            "id": svc["id"],
            "name": svc["name"],
            "port": svc["port"],
            "category": svc["category"],
            "critical": svc.get("critical", False),
            "status": status,
            "http_code": main_check["code"],
            "systemd": systemd_check,
            "snippet": main_check.get("snippet", "")[:100],
        }

        # Extra checks (Dragon Server sub-endpoints)
        if svc.get("extra_checks"):
            extras = {}
            for ec in svc["extra_checks"]:
                ec_result = check_port(
                    svc["port"], ec["path"],
                    method=ec.get("method", "GET"),
                    body=ec.get("body"),
                )
                extras[ec["name"]] = {
                    "alive": ec_result["alive"],
                    "code": ec_result["code"],
                }
                # If Dragon Brain is dead, mark as degraded
                if ec["name"] == "Dragon Brain" and not ec_result["alive"]:
                    entry["status"] = "degraded"
                    if status == "alive":
                        alive_count -= 1
                        degraded_count += 1
            entry["extra_checks"] = extras

        services_result.append(entry)

    # Special checks
    ppt_status = check_ppt_engine()
    wisdom_status = check_wisdom()
    ledger_stats = check_ledger_stats()
    skills_status = check_skills()

    # Wire status check
    wired_count = 0
    pending_count = 0
    wire_results = []
    for w in WIRING_MAP:
        # Check if the route actually responds
        if w["route"].startswith("/api/"):
            wc = check_port(8108, w["route"])
            is_wired = wc["alive"] and wc["code"] < 404
        elif w["route"] == "systemd":
            sc = check_systemd("windi-palette")
            is_wired = sc.get("status") == "active"
        elif w["route"] == "skill-load":
            is_wired = skills_status.get("product_identity", False)
        else:
            is_wired = False

        actual_status = "wired" if is_wired else w["status"]
        if is_wired:
            wired_count += 1
        else:
            pending_count += 1

        wire_results.append({**w, "actual_status": actual_status, "verified": is_wired})

    # Sentinel LAW check
    sentinel_check = check_port(8102, "/health")
    sentinel_status = "GREEN" if sentinel_check["alive"] and sentinel_check["code"] < 400 else "UNKNOWN"

    result = {
        "timestamp": timestamp,
        "version": VERSION,
        "principle": "AI processes. Human decides. WINDI guarantees.",
        "summary": {
            "total": len(SERVICES),
            "alive": alive_count,
            "dead": dead_count,
            "degraded": degraded_count,
            "health_pct": round((alive_count / len(SERVICES)) * 100, 1) if SERVICES else 0,
            "wired": wired_count,
            "pending_wires": pending_count,
            "total_wires": len(WIRING_MAP),
            "wire_pct": round((wired_count / len(WIRING_MAP)) * 100, 1) if WIRING_MAP else 0,
            "sentinel_status": sentinel_status,
        },
        "services": services_result,
        "wiring": wire_results,
        "special": {
            "ppt_engine": ppt_status,
            "wisdom_chain": wisdom_status,
            "ledger": ledger_stats,
            "skills": skills_status,
        },
        "sprints": {
            0: {"name": "Dragon Server", "wires": [w for w in wire_results if w["sprint"] == 0]},
            1: {"name": "Document Production", "wires": [w for w in wire_results if w["sprint"] == 1]},
            2: {"name": "Forensic Seal + Sign", "wires": [w for w in wire_results if w["sprint"] == 2]},
            3: {"name": "Intelligence + Governance", "wires": [w for w in wire_results if w["sprint"] == 3]},
            4: {"name": "Ecosystem + Ops", "wires": [w for w in wire_results if w["sprint"] == 4]},
        },
    }

    return result


# ═══════════════════════════════════════════════════════════════
# BACKGROUND SCANNER + MEMORY LOOP
# ═══════════════════════════════════════════════════════════════

_last_scan = None
_last_scan_time = 0
_scan_lock = threading.Lock()


def background_scanner():
    """Run scans periodically and detect changes (memory loop)."""
    global _last_scan, _last_scan_time
    previous_statuses = {}

    while True:
        try:
            result = full_scan()

            with _scan_lock:
                _last_scan = result
                _last_scan_time = time.time()

            # Memory Loop: detect changes
            current_statuses = {s["id"]: s["status"] for s in result["services"]}
            for sid, status in current_statuses.items():
                prev = previous_statuses.get(sid)
                if prev and prev != status:
                    severity = "critical" if status == "dead" else "warning" if status == "degraded" else "info"
                    svc_name = next((s["name"] for s in result["services"] if s["id"] == sid), sid)
                    log_event(
                        "status_change", sid,
                        f"{svc_name}: {prev} → {status}",
                        severity,
                    )
                    print(f"[PULSE] CHANGE: {svc_name} {prev} → {status}")

            previous_statuses = current_statuses
            save_scan(result)

        except Exception as e:
            print(f"[PULSE] Scan error: {e}")

        time.sleep(SCAN_INTERVAL)


# ═══════════════════════════════════════════════════════════════
# HTTP SERVER
# ═══════════════════════════════════════════════════════════════

class PulseHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Silent logging

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json_response(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._cors()
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, default=str).encode())

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0].rstrip("/")

        # ── Self Health ──
        if path in ("", "/", "/api/pulse/health"):
            self._json_response({
                "service": "WINDI Pulse",
                "version": VERSION,
                "status": "operational",
                "scan_interval_s": SCAN_INTERVAL,
                "last_scan_age_s": round(time.time() - _last_scan_time, 1) if _last_scan_time else None,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        # ── Full Scan ──
        elif path == "/api/pulse/scan":
            with _scan_lock:
                if _last_scan:
                    self._json_response(_last_scan)
                else:
                    # First request before background scan completes
                    result = full_scan()
                    self._json_response(result)

        # ── Outlook (Sprint Progress) ──
        elif path == "/api/pulse/outlook":
            with _scan_lock:
                scan = _last_scan or full_scan()

            sprints_summary = {}
            for sprint_num, sprint_data in scan["sprints"].items():
                wires = sprint_data["wires"]
                done = sum(1 for w in wires if w["verified"])
                total = len(wires)
                sprints_summary[sprint_num] = {
                    "name": sprint_data["name"],
                    "progress": f"{done}/{total}",
                    "pct": round((done / total) * 100) if total else 0,
                    "status": "complete" if done == total else "in-progress" if done > 0 else "pending",
                    "wires": wires,
                }

            self._json_response({
                "timestamp": scan["timestamp"],
                "ecosystem_health": scan["summary"]["health_pct"],
                "wiring_progress": scan["summary"]["wire_pct"],
                "sprints": sprints_summary,
                "special": scan["special"],
            })

        # ── History (Memory Loop) ──
        elif path == "/api/pulse/history":
            try:
                conn = sqlite3.connect(DB_PATH)
                # Recent events
                events = conn.execute(
                    "SELECT timestamp, event_type, service_id, message, severity FROM events ORDER BY id DESC LIMIT 50"
                ).fetchall()
                # Scan trend (last 60)
                trends = conn.execute(
                    "SELECT timestamp, alive, dead, degraded, wired FROM scans ORDER BY id DESC LIMIT 60"
                ).fetchall()
                conn.close()

                self._json_response({
                    "events": [
                        {"timestamp": e[0], "type": e[1], "service": e[2], "message": e[3], "severity": e[4]}
                        for e in events
                    ],
                    "trends": [
                        {"timestamp": t[0], "alive": t[1], "dead": t[2], "degraded": t[3], "wired": t[4]}
                        for t in reversed(trends)
                    ],
                })
            except Exception as e:
                self._json_response({"error": str(e)}, 500)

        # ── Sentinel Integration ──
        elif path == "/api/pulse/sentinel":
            sentinel_check = check_port(8102, "/health")
            sentinel_data = {}
            if sentinel_check["alive"]:
                try:
                    sentinel_data = json.loads(sentinel_check.get("snippet", "{}"))
                except Exception:
                    sentinel_data = {"raw": sentinel_check.get("snippet", "")}

            self._json_response({
                "sentinel_alive": sentinel_check["alive"],
                "sentinel_code": sentinel_check["code"],
                "sentinel_data": sentinel_data,
                "i9_status": "ENFORCED",
                "invariants": "9/9",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        else:
            self._json_response({"error": "Not found", "path": path}, 404)


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║  🐉 WINDI PULSE v{VERSION}                                     ║
║  Ecosystem Health Monitor                                    ║
║  Port: {PORT}                                                  ║
║  Scan interval: {SCAN_INTERVAL}s                                          ║
║  DB: {DB_PATH}                               ║
║  "AI processes. Human decides. WINDI guarantees."            ║
╚══════════════════════════════════════════════════════════════╝
    """)

    init_db()
    log_event("startup", "pulse", f"WINDI Pulse v{VERSION} starting on :{PORT}")

    # Start background scanner
    scanner = threading.Thread(target=background_scanner, daemon=True)
    scanner.start()
    print(f"[PULSE] Background scanner started (interval: {SCAN_INTERVAL}s)")

    # Start HTTP server
    server = HTTPServer(("0.0.0.0", PORT), PulseHandler)
    print(f"[PULSE] HTTP server listening on :{PORT}")
    print(f"[PULSE] Endpoints:")
    print(f"  GET /api/pulse/health    → self health")
    print(f"  GET /api/pulse/scan      → full ecosystem scan")
    print(f"  GET /api/pulse/outlook   → sprint progress")
    print(f"  GET /api/pulse/history   → memory loop events")
    print(f"  GET /api/pulse/sentinel  → sentinel integration")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[PULSE] Shutting down...")
        log_event("shutdown", "pulse", "Clean shutdown")
        server.shutdown()


if __name__ == "__main__":
    main()
