#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════
  WINDI JMPG Viewer Server v1.0.0
  Port: 8104
  Pattern: BaseHTTPRequestHandler (WINDI Standard)
  
  Serves the JMPG Viewer (HTML5 universal viewer for .jmpg files)
  Integrates with:
    - Forensic Ledger (:8101) for hash verification
    - Wallet (:8099) for signature validation
    - Export Engine (:8103) for .jmpg generation
    
  "AI processes. Human decides. WINDI guarantees."
═══════════════════════════════════════════════════════════════
"""

import os
import sys
import json
import time
import hashlib
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timezone
from pathlib import Path

# ── Configuration ──
PORT = int(os.environ.get("JMPG_PORT", 8104))
HOST = "0.0.0.0"
VERSION = "1.0.0"
SERVICE_NAME = "WINDI JMPG Viewer"

# Paths
BASE_DIR = Path(__file__).parent
VIEWER_HTML = BASE_DIR / "viewer.html"
SAMPLES_DIR = BASE_DIR / "samples"

# Sibling services
LEDGER_URL = os.environ.get("LEDGER_URL", "http://127.0.0.1:8101")
WALLET_URL = os.environ.get("WALLET_URL", "http://127.0.0.1:8099")
EXPORT_URL = os.environ.get("EXPORT_URL", "http://127.0.0.1:8103")

# ── Stats ──
STATS = {
    "start_time": None,
    "requests_served": 0,
    "jmpg_verified": 0,
    "last_request": None
}


class JMPGViewerHandler(BaseHTTPRequestHandler):
    """Handler for JMPG Viewer service."""

    def log_message(self, format, *args):
        """Custom log format matching WINDI pattern."""
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        sys.stdout.write(f"[{ts}] JMPG-VIEWER {format % args}\n")
        sys.stdout.flush()

    def _send_json(self, code, data):
        """Send JSON response."""
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, code, html_bytes):
        """Send HTML response."""
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(html_bytes)))
        self._cors_headers()
        self.end_headers()
        self.wfile.write(html_bytes)

    def _cors_headers(self):
        """Add CORS headers for cross-origin access."""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    def do_GET(self):
        """Route GET requests."""
        STATS["requests_served"] += 1
        STATS["last_request"] = datetime.now(timezone.utc).isoformat()

        path = self.path.split("?")[0].rstrip("/") or "/"

        routes = {
            "/":            self._handle_viewer,
            "/health":      self._handle_health,
            "/api/status":  self._handle_status,
            "/api/schema":  self._handle_schema,
            "/api/verify":  self._handle_verify_info,
        }

        handler = routes.get(path)
        if handler:
            handler()
        else:
            self._send_json(404, {"error": "Not found", "path": path})

    def do_POST(self):
        """Route POST requests."""
        STATS["requests_served"] += 1
        STATS["last_request"] = datetime.now(timezone.utc).isoformat()

        path = self.path.split("?")[0].rstrip("/")

        if path == "/api/verify":
            self._handle_verify_hash()
        else:
            self._send_json(404, {"error": "Not found", "path": path})

    # ── Route Handlers ──

    def _handle_viewer(self):
        """Serve the JMPG viewer HTML."""
        if VIEWER_HTML.exists():
            html = VIEWER_HTML.read_bytes()
            self._send_html(200, html)
        else:
            self._send_html(503, b"<h1>Viewer HTML not found</h1>")

    def _handle_health(self):
        """Health check — matches WINDI Sentinel LAW expectations."""
        uptime = 0
        if STATS["start_time"]:
            uptime = int(time.time() - STATS["start_time"])

        self._send_json(200, {
            "service": SERVICE_NAME,
            "version": VERSION,
            "status": "healthy",
            "port": PORT,
            "uptime_seconds": uptime,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "viewer_available": VIEWER_HTML.exists(),
            "zero_knowledge": True
        })

    def _handle_status(self):
        """Detailed status with sibling service connectivity."""
        siblings = {}
        for name, url in [("ledger", LEDGER_URL), ("wallet", WALLET_URL), ("export", EXPORT_URL)]:
            try:
                req = urllib.request.urlopen(f"{url}/health", timeout=2)
                siblings[name] = {"status": "reachable", "code": req.getcode()}
            except Exception as e:
                siblings[name] = {"status": "unreachable", "error": str(e)[:80]}

        self._send_json(200, {
            "service": SERVICE_NAME,
            "version": VERSION,
            "port": PORT,
            "stats": STATS,
            "siblings": siblings,
            "architecture": {
                "pattern": "BaseHTTPRequestHandler",
                "zero_knowledge": True,
                "format": "JMPG-1.0",
                "principle": "AI processes. Human decides. WINDI guarantees."
            }
        })

    def _handle_schema(self):
        """Return the JMPG manifest JSON schema."""
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "https://windi.example/schema/jmpg/manifest-1.0.json",
            "title": "JMPG Manifest v1.0",
            "description": "Joint Media Protocol for Governance — Manifest Schema",
            "type": "object",
            "required": ["format", "package_id", "kind", "title", "created_at",
                         "entrypoints", "author", "governance"],
            "properties": {
                "format": {"const": "JMPG-1.0"},
                "package_id": {"type": "string", "pattern": "^JMPG-\\d{8}-\\d{4}$"},
                "kind": {"enum": ["COMMUNIQUE", "JOURNALINE", "REPORT", "BRIEF",
                                  "FIELD_REPORT", "ALERT", "INSTRUCTION"]},
                "title": {"type": "string", "maxLength": 256},
                "created_at": {"type": "string", "format": "date-time"},
                "language": {"type": "string"},
                "author": {
                    "type": "object",
                    "required": ["wallet_id"],
                    "properties": {
                        "wallet_id": {"type": "string"},
                        "display_name": {"type": "string"}
                    }
                },
                "governance": {
                    "type": "object",
                    "required": ["content_hash_sha256", "ledger_ref"],
                    "properties": {
                        "content_hash_sha256": {"type": "string", "pattern": "^sha256:[a-f0-9]{64}$"},
                        "ledger_ref": {"type": "object"},
                        "sge": {"type": "object"},
                        "virtue_receipt_ref": {"type": "string"},
                        "sentinel_law": {"type": "object"}
                    }
                }
            }
        }
        self._send_json(200, schema)

    def _handle_verify_info(self):
        """GET /api/verify — info about the verification endpoint."""
        self._send_json(200, {
            "endpoint": "POST /api/verify",
            "description": "Verify a .jmpg package hash against the Forensic Ledger",
            "body": {
                "package_hash": "sha256:...",
                "receipt_id": "VR-..."
            },
            "note": "Zero-Knowledge: only hashes are transmitted, never content."
        })

    def _handle_verify_hash(self):
        """POST /api/verify — verify hash against Ledger (:8101)."""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)
        except Exception as e:
            self._send_json(400, {"error": f"Invalid JSON: {e}"})
            return

        package_hash = data.get("package_hash", "")
        receipt_id = data.get("receipt_id", "")

        if not package_hash:
            self._send_json(400, {"error": "package_hash required"})
            return

        # Try to verify against Forensic Ledger
        verification = {
            "package_hash": package_hash,
            "receipt_id": receipt_id,
            "verified_at": datetime.now(timezone.utc).isoformat(),
            "ledger_status": "PENDING"
        }

        try:
            # Query Ledger for matching receipt
            ledger_url = f"{LEDGER_URL}/api/receipts"
            req = urllib.request.urlopen(ledger_url, timeout=3)
            ledger_data = json.loads(req.read())

            # Search for matching hash in receipts
            receipts = ledger_data if isinstance(ledger_data, list) else ledger_data.get("receipts", [])
            match_found = False
            for r in receipts:
                r_hash = r.get("content_hash", r.get("package_hash_sha256", ""))
                if package_hash.replace("sha256:", "") in r_hash:
                    match_found = True
                    verification["ledger_status"] = "VERIFIED"
                    verification["ledger_entry"] = r.get("receipt_id", r.get("id", ""))
                    break

            if not match_found:
                verification["ledger_status"] = "NOT_FOUND"
                verification["note"] = "Hash not found in Forensic Ledger. Package may be unregistered."

        except Exception as e:
            verification["ledger_status"] = "LEDGER_UNREACHABLE"
            verification["error"] = str(e)[:100]

        STATS["jmpg_verified"] += 1
        self._send_json(200, verification)


def main():
    """Start JMPG Viewer server."""
    STATS["start_time"] = time.time()

    # Ensure samples directory exists
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 62)
    print(f"  {SERVICE_NAME} v{VERSION}")
    print(f"  Port: {PORT}")
    print(f"  Viewer: {'OK' if VIEWER_HTML.exists() else 'MISSING'}")
    print(f"  Pattern: BaseHTTPRequestHandler (WINDI Standard)")
    print(f"  Zero-Knowledge: YES")
    print("=" * 62)
    print(f"  Endpoints:")
    print(f"    GET  /            → JMPG Viewer (HTML5)")
    print(f"    GET  /health      → Health check")
    print(f"    GET  /api/status  → Detailed status + siblings")
    print(f"    GET  /api/schema  → JMPG manifest JSON schema")
    print(f"    POST /api/verify  → Verify hash vs Ledger (:8101)")
    print("=" * 62)
    print()

    server = HTTPServer((HOST, PORT), JMPGViewerHandler)
    print(f"[READY] Listening on {HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[STOP] Shutting down.")
        server.server_close()


if __name__ == "__main__":
    main()
