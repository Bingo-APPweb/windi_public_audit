#!/usr/bin/env python3
"""
WINDI Agent Palette v0.4.0 — Cognitive Document Agent
Port: 8108
"80% local. 20% LLM. 100% governado."

Serves:
  GET  /health          → Service health
  GET  /api/tiers       → Tier definitions
  GET  /api/engine      → Engine capabilities
  GET  /                → Agent Suite UI (React SPA)
  POST /api/generate    → Process document intent (backend mirror)
  POST /api/wisdom/candidate    → Submit wisdom candidate (Part 2A)
  GET  /api/wisdom/stats        → Wisdom pipeline stats
  POST /api/multimodal/ocr      → OCR image (Part 2B)
  POST /api/multimodal/verify-url → Verify URL
  GET  /api/multimodal/capabilities → Multimodal capabilities
"""

import json
import hashlib
import os
import re
import time
import sqlite3
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timezone
from pathlib import Path

# WINDI Document Renderer Integration
import sys as _sys
_sys.path.insert(0, str(Path(__file__).parent / "renderer"))
try:
    from render_api import route_render_api
    HAS_RENDERER = True
    print("[Palette] Document Renderer: LOADED")
except ImportError as _e:
    HAS_RENDERER = False
    print(f"[Palette] Document Renderer: NOT AVAILABLE ({_e})")

# Part 2A: Wisdom Engine
try:
    from wisdom_engine import route_wisdom_api
    HAS_WISDOM = True
    print("[Palette] Wisdom Engine: LOADED")
except ImportError as _e:
    HAS_WISDOM = False
    print(f"[Palette] Wisdom Engine: NOT AVAILABLE ({_e})")

# Part 2B: Multimodal Engine
try:
    from multimodal_engine import route_multimodal_api
    HAS_MULTIMODAL = True
    print("[Palette] Multimodal Engine: LOADED")
except ImportError as _e:
    HAS_MULTIMODAL = False
    print(f"[Palette] Multimodal Engine: NOT AVAILABLE ({_e})")

PORT = int(os.environ.get("WINDI_PALETTE_PORT", 8108))
VERSION = "0.4.0"
BASE_DIR = Path(__file__).parent
UI_FILE = BASE_DIR / "ui" / "index.html"
GOVERNANCE_FILE = BASE_DIR / "ui" / "governance.html"
LOG_DIR = Path("/opt/windi/logs")
DATA_DIR = Path("/opt/windi/data")

# ── Tier definitions ─────────────────────────────────────────
TIERS = {
    "FREE": {"label":"Personal","llm":False,"sge_max":2,"ledger":False,"vault":False,"max_docs":5,
             "types":["letter","memo","note","email"],"formats":["docx"]},
    "MED":  {"label":"Organization","llm":True,"llm_budget":2000,"sge_max":5,"ledger":True,"vault":False,"max_docs":50,
             "types":["letter","memo","note","email","report","contract","invoice","protocol","analysis","presentation"],"formats":["docx","pdf","xlsx","pptx"]},
    "HIGH": {"label":"Governance","llm":True,"llm_budget":8000,"sge_max":5,"ledger":True,"vault":True,"max_docs":500,
             "types":["letter","memo","note","email","report","contract","invoice","protocol","analysis","presentation","security_advisory","governance_decision","communique","certificate"],
             "formats":["docx","pdf","xlsx","pptx","jmpg"]},
}

# ── Stats tracking ───────────────────────────────────────────
stats = {"requests": 0, "docs_generated": 0, "start_time": datetime.now(timezone.utc).isoformat()}


class PaletteHandler(BaseHTTPRequestHandler):
    """WINDI Agent Palette HTTP Handler"""

    def log_message(self, format, *args):
        """Suppress default logging to stderr"""
        pass

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))

    def _send_html(self, html, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def _normalize_path(self, path):
        """Handle nginx prefix stripping"""
        for prefix in ["/palette"]:
            if path.startswith(prefix):
                path = path[len(prefix):] or "/"
        return path

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path = self._normalize_path(self.path.split("?")[0])
        if HAS_RENDERER and route_render_api(self, "GET", path):
            return
        if HAS_WISDOM and route_wisdom_api(self, "GET", path):
            return
        if HAS_MULTIMODAL and route_multimodal_api(self, "GET", path):
            return
        stats["requests"] += 1

        if path == "/health":
            self._send_json({
                "service": "WINDI Agent Palette",
                "version": VERSION,
                "status": "healthy",
                "port": PORT,
                "engine": {
                    "doc_types": 14,
                    "isp_templates": 13,
                    "sge_layers": "7 + cross-correlation",
                    "languages": ["DE", "EN", "PT"],
                },
                "modules": {
                    "renderer": HAS_RENDERER,
                    "wisdom": HAS_WISDOM,
                    "multimodal": HAS_MULTIMODAL,
                },
                "stats": stats,
                "uptime_since": stats["start_time"],
            })

        elif path == "/api/tiers":
            self._send_json({"tiers": TIERS, "version": VERSION})

        elif path == "/api/engine":
            self._send_json({
                "version": VERSION,
                "capabilities": {
                    "intent_parser": "v2 — regex + keyword + entity extraction",
                    "isp_resolver": "13 sealed templates (6 COM + 7 GEN)",
                    "sge": "7-layer + cross-correlation",
                    "entity_extraction": ["email", "person", "org", "money", "date", "mention"],
                    "languages": {"de": "Deutsch", "en": "English", "pt": "Português"},
                    "doc_types": 14,
                    "conversation_memory": "last 10 intents",
                },
                "pipeline": [
                    {"layer": "L1", "name": "IntentParser v2", "location": "local", "latency": "<5ms"},
                    {"layer": "L2", "name": "Entity Extractor", "location": "local", "latency": "<2ms"},
                    {"layer": "L3", "name": "ISP Resolver", "location": "local", "latency": "<3ms"},
                    {"layer": "L4", "name": "DocGenerator", "location": "local", "latency": "<10ms"},
                    {"layer": "L5", "name": "SGE v2 (7-layer)", "location": "edge", "latency": "<8ms"},
                    {"layer": "L6", "name": "Ledger Seal", "location": ":8101", "latency": "~20ms"},
                    {"layer": "L7", "name": "Vault Broadcast", "location": ":8106", "latency": "~15ms"},
                ],
                "principle": "KI verarbeitet. Mensch entscheidet. WINDI garantiert.",
            })

        elif path == "/" or path == "/index.html":
            if UI_FILE.exists():
                self._send_html(UI_FILE.read_text(encoding="utf-8"))
            else:
                self._send_html(self._fallback_ui())

        elif path == "/governance" or path == "/governance/":
            if GOVERNANCE_FILE.exists():
                self._send_html(GOVERNANCE_FILE.read_text(encoding="utf-8"))
            else:
                self._send_json({"error": "Governance dashboard not found"}, 404)

        else:
            self._send_json({"error": "Not found", "path": path}, 404)

    def do_POST(self):
        path = self._normalize_path(self.path.split("?")[0])
        if HAS_RENDERER and route_render_api(self, "POST", path):
            return
        if HAS_WISDOM and route_wisdom_api(self, "POST", path):
            return
        if HAS_MULTIMODAL and route_multimodal_api(self, "POST", path):
            return
        stats["requests"] += 1

        if path == "/api/generate":
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length)) if length > 0 else {}
                prompt = body.get("prompt", "")
                tier = body.get("tier", "FREE")

                if not prompt:
                    self._send_json({"error": "Missing 'prompt' field"}, 400)
                    return

                if tier not in TIERS:
                    self._send_json({"error": f"Invalid tier: {tier}"}, 400)
                    return

                # Process intent (server-side mirror of client engine)
                result = {
                    "status": "received",
                    "prompt": prompt,
                    "tier": tier,
                    "note": "Full processing runs client-side in v0.3.0. Server endpoint reserved for future LLM integration.",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                stats["docs_generated"] += 1
                self._send_json(result)

            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        else:
            self._send_json({"error": "Not found"}, 404)

    def _fallback_ui(self):
        return """<!DOCTYPE html>
<html><head><title>WINDI Agent Palette</title></head>
<body style="background:#08080D;color:#E2E2EA;font-family:system-ui;display:flex;align-items:center;justify-content:center;height:100vh;margin:0">
<div style="text-align:center">
<h1 style="color:#D4A843">🐉 WINDI Agent Palette v""" + VERSION + """</h1>
<p>UI file not found. Place index.html in ./ui/</p>
<p><a href="/health" style="color:#D4A843">/health</a> · <a href="/api/engine" style="color:#D4A843">/api/engine</a></p>
</div></body></html>"""


def main():
    os.makedirs(LOG_DIR, exist_ok=True)
    server = HTTPServer(("0.0.0.0", PORT), PaletteHandler)
    print(f"🐉 WINDI Agent Palette v{VERSION} running on :{PORT}")
    print(f"   14 doc types · 13 ISP templates · 7-layer SGE")
    print(f"   Modules: Renderer={'✓' if HAS_RENDERER else '✗'} Wisdom={'✓' if HAS_WISDOM else '✗'} Multimodal={'✓' if HAS_MULTIMODAL else '✗'}")
    print(f"   Health: http://localhost:{PORT}/health")
    print(f"   UI:     http://localhost:{PORT}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🐉 Palette stopped.")
        server.server_close()


if __name__ == "__main__":
    main()
