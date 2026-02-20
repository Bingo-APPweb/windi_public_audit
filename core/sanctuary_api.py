#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║  WINDI SKILL-SANCTUARY API — Port 8093                          ║
║  "O Cockpit do Santuário"                                        ║
║                                                                  ║
║  REST API that exposes the Skill-Loader Core to human            ║
║  Controllers via web dashboard and direct API calls.             ║
║                                                                  ║
║  Endpoints:                                                      ║
║    GET  /api/sanctuary/status     — Sanctuary health             ║
║    GET  /api/sanctuary/skills     — List all baptized skills     ║
║    POST /api/sanctuary/scan       — Scan a document (SGE)        ║
║    POST /api/sanctuary/audit      — Audit against I1-I9          ║
║    GET  /api/sanctuary/receipts   — List consumption receipts    ║
║    GET  /api/sanctuary/receipt/:id — Single receipt detail        ║
║    GET  /                         — Dashboard UI                 ║
║                                                                  ║
║  Princípio: "IA processa. Humano decide. WINDI garante."        ║
╚══════════════════════════════════════════════════════════════════╝
"""

import json
import os
import sys
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

# Add core to path
CORE_PATH = Path("/opt/windi/core")
sys.path.insert(0, str(CORE_PATH))

from skill_loader_core import SkillLoaderCore

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────
PORT = 8093
HOST = "0.0.0.0"
RECEIPT_DIR = Path("/opt/windi/receipts/skills")
DASHBOARD_HTML = Path(__file__).parent / "windi_public_dashboard.html"
ADMIN_HTML = Path(__file__).parent / "sanctuary_dashboard.html"

# ─────────────────────────────────────────────
# GLOBAL LOADER INSTANCE
# ─────────────────────────────────────────────
loader = None


def get_loader():
    """Get or initialize the global SkillLoaderCore."""
    global loader
    if loader is None or not loader._initialized:
        loader = SkillLoaderCore()
        loader.initialize()
    return loader


# ─────────────────────────────────────────────
# REQUEST HANDLER
# ─────────────────────────────────────────────

class SanctuaryHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler for the Skill-Sanctuary API."""

    def log_message(self, format, *args):
        """Custom log format."""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [SANCTUARY-API] {args[0]}")

    def _send_json(self, data, status=200):
        """Send a JSON response."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        body = json.dumps(data, indent=2, ensure_ascii=False, default=str)
        self.wfile.write(body.encode("utf-8"))

    def _send_html(self, html_content, status=200):
        """Send an HTML response."""
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html_content.encode("utf-8"))

    def _read_body(self):
        """Read and parse JSON request body."""
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return {}
        body = self.rfile.read(content_length)
        return json.loads(body.decode("utf-8"))

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        """Handle GET requests."""
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        params = parse_qs(parsed.query)

        try:
            if path == "/admin":
                self._serve_admin()
            elif path == "" or path == "/":
                self._serve_dashboard()
            elif path == "/api/sanctuary/status":
                self._handle_status()
            elif path == "/api/sanctuary/skills":
                domain = params.get("domain", [None])[0]
                self._handle_list_skills(domain)
            elif path == "/api/sanctuary/receipts":
                self._handle_list_receipts()
            elif path.startswith("/api/sanctuary/receipt/"):
                receipt_id = path.split("/")[-1]
                self._handle_get_receipt(receipt_id)
            else:
                self._send_json({"error": "Not found", "path": path}, 404)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def do_POST(self):
        """Handle POST requests."""
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        try:
            body = self._read_body()

            if path == "/api/sanctuary/scan":
                self._handle_scan(body)
            elif path == "/api/sanctuary/quick-scan":
                self._handle_quick_scan(body)
            elif path == "/api/sanctuary/audit":
                self._handle_audit(body)
            elif path == "/api/sanctuary/dsgvo-check":
                self._handle_dsgvo_check(body)
            else:
                self._send_json({"error": "Not found"}, 404)
        except json.JSONDecodeError:
            self._send_json({"error": "Invalid JSON body"}, 400)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    # ─── ENDPOINT HANDLERS ───

    def _serve_dashboard(self):
        """Serve the Sanctuary Dashboard HTML."""
        if DASHBOARD_HTML.exists():
            html = DASHBOARD_HTML.read_text(encoding="utf-8")
        else:
            html = self._fallback_dashboard()
        self._send_html(html)

    def _handle_status(self):
        """GET /api/sanctuary/status"""
        ldr = get_loader()
        status = ldr.get_status()

        # Add receipt count
        receipt_count = 0
        if RECEIPT_DIR.exists():
            receipt_count = len(list(RECEIPT_DIR.glob("SKR-*.json")))
        status["receipts_generated"] = receipt_count

        self._send_json(status)

    def _handle_list_skills(self, domain=None):
        """GET /api/sanctuary/skills"""
        ldr = get_loader()
        skills = ldr.list_skills(domain=domain)
        self._send_json({
            "total": len(skills),
            "skills": skills
        })

    def _handle_scan(self, body):
        """POST /api/sanctuary/scan — Full 6-layer SGE deep scan."""
        content = body.get("content", "")
        if not content:
            self._send_json({"error": "Missing 'content' field"}, 400)
            return

        ldr = get_loader()
        result = ldr.consume_skill(
            skill_id="sge_deep_scanner",
            function_name="deep_scan",
            args={
                "content": content,
                "document_type": body.get("document_type", "contract"),
                "document_id": body.get("document_id", "API-SCAN"),
                "scan_mode": body.get("scan_mode", "full"),
                "focus_layers": body.get("focus_layers"),
            },
            agent_id=body.get("agent_id", "api-user"),
            input_summary=body.get("summary", "API scan request")
        )
        self._send_json(result)

    def _handle_quick_scan(self, body):
        """POST /api/sanctuary/quick-scan — 2-layer triage."""
        content = body.get("content", "")
        if not content:
            self._send_json({"error": "Missing 'content' field"}, 400)
            return

        ldr = get_loader()
        result = ldr.consume_skill(
            skill_id="sge_deep_scanner",
            function_name="quick_scan",
            args={
                "content": content,
                "document_type": body.get("document_type", "generic"),
            },
            agent_id=body.get("agent_id", "api-user"),
            input_summary="Quick scan via API"
        )
        self._send_json(result)

    def _handle_audit(self, body):
        """POST /api/sanctuary/audit — I1-I9 invariant audit."""
        content = body.get("content", "")
        if not content:
            self._send_json({"error": "Missing 'content' field"}, 400)
            return

        ldr = get_loader()
        result = ldr.consume_skill(
            skill_id="invariant_auditor",
            function_name="audit_document",
            args={
                "content": content,
                "document_type": body.get("document_type", "generic"),
                "strict_mode": body.get("strict_mode", True),
            },
            agent_id=body.get("agent_id", "api-user"),
            input_summary="I1-I9 Audit via API"
        )
        self._send_json(result)

    def _handle_dsgvo_check(self, body):
        """POST /api/sanctuary/dsgvo-check — Focused DSGVO article check."""
        content = body.get("content", "")
        if not content:
            self._send_json({"error": "Missing 'content' field"}, 400)
            return

        ldr = get_loader()
        result = ldr.consume_skill(
            skill_id="sge_deep_scanner",
            function_name="scan_dsgvo_compliance",
            args={
                "content": content,
                "check_type": body.get("check_type", "art_13"),
            },
            agent_id=body.get("agent_id", "api-user"),
            input_summary=f"DSGVO {body.get('check_type', 'art_13')} check via API"
        )
        self._send_json(result)

    def _handle_list_receipts(self):
        """GET /api/sanctuary/receipts"""
        receipts = []
        if RECEIPT_DIR.exists():
            for rf in sorted(RECEIPT_DIR.glob("SKR-*.json"), reverse=True)[:50]:
                try:
                    data = json.loads(rf.read_text(encoding="utf-8"))
                    receipts.append({
                        "receipt_id": data.get("receipt_id"),
                        "skill_name": data.get("skill_name"),
                        "consumed_at": data.get("consumed_at"),
                        "domain": data.get("domain"),
                        "i9_status": data.get("i9_status"),
                        "execution_ms": data.get("execution_ms"),
                    })
                except Exception:
                    pass
        self._send_json({"total": len(receipts), "receipts": receipts})

    def _handle_get_receipt(self, receipt_id):
        """GET /api/sanctuary/receipt/:id"""
        receipt_file = RECEIPT_DIR / f"{receipt_id}.json"
        if not receipt_file.exists():
            # Try searching
            for rf in RECEIPT_DIR.glob("*.json"):
                if receipt_id in rf.name:
                    receipt_file = rf
                    break
        if receipt_file.exists():
            data = json.loads(receipt_file.read_text(encoding="utf-8"))
            self._send_json(data)
        else:
            self._send_json({"error": f"Receipt not found: {receipt_id}"}, 404)

    def _serve_admin(self):
        if ADMIN_HTML.exists():
            self._send_html(ADMIN_HTML.read_text(encoding="utf-8"))
        else:
            self._send_html("<h1>Admin not found</h1>", 404)

    def _fallback_dashboard(self):
        """Minimal fallback if dashboard HTML file is missing."""
        return """<!DOCTYPE html><html><head><title>WINDI Sanctuary</title></head>
        <body style="background:#0a0a0a;color:#d4af37;font-family:monospace;padding:40px">
        <h1>🏛️ WINDI Skill-Sanctuary</h1>
        <p>Dashboard file not found. API is operational.</p>
        <p>Try: <a href="/api/sanctuary/status" style="color:#d4af37">/api/sanctuary/status</a></p>
        </body></html>"""


# ─────────────────────────────────────────────
# SERVER STARTUP
# ─────────────────────────────────────────────

def main():
    """Start the Sanctuary API server."""
    print(f"""
╔══════════════════════════════════════════════════════╗
║  🏛️ WINDI SKILL-SANCTUARY API                        ║
║  Port: {PORT}                                          ║
║  Dashboard: http://localhost:{PORT}/                   ║
║  API Base:  http://localhost:{PORT}/api/sanctuary/     ║
║                                                      ║
║  "IA processa. Humano decide. WINDI garante."        ║
╚══════════════════════════════════════════════════════╝
""")

    # Pre-initialize the loader
    get_loader()

    server = HTTPServer((HOST, PORT), SanctuaryHandler)
    print(f"[SANCTUARY-API] Listening on {HOST}:{PORT}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[SANCTUARY-API] Shutting down...")
        if loader:
            loader.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
