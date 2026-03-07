"""
WINDI Communiqué Builder — v1.0.0
Port: 8115 | Path: /builder/
"AI processes. Human decides. WINDI guarantees."
"""

import os
import json
import uuid
import hashlib
import datetime
import urllib.request
import urllib.error
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

PORT         = int(os.getenv("PORT", 8115))
COMMUNIQUE_URL = os.getenv("COMMUNIQUE_ENGINE_URL", "http://127.0.0.1:8105")
LEDGER_URL     = os.getenv("LEDGER_URL",             "http://127.0.0.1:8101")
STATIC_DIR     = Path(__file__).parent / "static"
VERSION        = "1.0.0"


# ── helpers ──────────────────────────────────────────────────────────────────

def _json(body: dict, status: int = 200) -> tuple:
    data = json.dumps(body, ensure_ascii=False, default=str).encode()
    return status, "application/json", data


def _proxy_post(url: str, payload: dict) -> dict:
    """Fire-and-forget JSON POST, return response dict."""
    raw = json.dumps(payload).encode()
    req = urllib.request.Request(
        url, data=raw,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}


# ── request handler ───────────────────────────────────────────────────────────

class BuilderHandler(SimpleHTTPRequestHandler):

    def log_message(self, fmt, *args):
        ts = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        print(f"[{ts}] {fmt % args}")

    # ── routing ──
    def do_GET(self):
        path = self.path.split("?")[0].rstrip("/") or "/"

        routes = {
            "/health":            self._health,
            "/builder/health":    self._health,
            "/builder/api/info":  self._info,
        }

        if path in routes:
            routes[path]()
        elif path in ("/builder", "/builder/", "/"):
            self._serve_index()
        elif path.startswith("/builder/static/"):
            rel = path[len("/builder/static/"):]
            self._serve_static(rel)
        else:
            self._404()

    def do_POST(self):
        path = self.path.split("?")[0].rstrip("/")
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}

        routes = {
            "/builder/api/preview":  (self._preview, body),
            "/builder/api/publish":  (self._publish, body),
            "/builder/api/draft":    (self._draft,   body),
        }

        if path in routes:
            fn, b = routes[path]
            fn(b)
        else:
            self._404()

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    # ── handlers ──

    def _health(self):
        status, ct, data = _json({
            "status":  "healthy",
            "service": "windi-communique-builder",
            "version": VERSION,
            "port":    PORT,
            "ts":      datetime.datetime.utcnow().isoformat() + "Z",
            "deps": {
                "communique_engine": COMMUNIQUE_URL,
                "ledger":            LEDGER_URL,
            }
        })
        self._respond(status, ct, data)

    def _info(self):
        status, ct, data = _json({
            "builder":  f"WINDI Communiqué Builder v{VERSION}",
            "engine":   COMMUNIQUE_URL,
            "ledger":   LEDGER_URL,
            "doc_types": ["communique", "communiqué"],
            "principle": "AI processes. Human decides. WINDI guarantees.",
        })
        self._respond(status, ct, data)

    def _preview(self, body: dict):
        """Generate preview — calls communiqué engine."""
        result = _proxy_post(f"{COMMUNIQUE_URL}/api/preview", body)
        status, ct, data = _json(result)
        self._respond(status, ct, data)

    def _draft(self, body: dict):
        """Save draft locally (in-memory, no ledger seal)."""
        draft_id = f"DRAFT-{uuid.uuid4().hex[:8].upper()}"
        content  = json.dumps(body, sort_keys=True)
        h        = hashlib.sha256(content.encode()).hexdigest()[:16]
        status, ct, data = _json({
            "draft_id":  draft_id,
            "hash":      h,
            "ts":        datetime.datetime.utcnow().isoformat() + "Z",
            "status":    "draft_saved",
            "note":      "Draft is ephemeral — publish to seal in Ledger.",
        })
        self._respond(status, ct, data)

    def _publish(self, body: dict):
        """Publish → Engine → Ledger seal. Human already approved."""
        # 1. Send to Communiqué Engine for rendering
        engine_payload = {
            "title_de":    body.get("title", ""),
            "body_de":     body.get("body", ""),
            "author_name": body.get("sender", ""),
            "author_role": body.get("sender_role", "CGO"),
            "recipient":   body.get("recipient", ""),
            "governance_level": body.get("governance_level", "MEDIUM"),
        }
        render_result = _proxy_post(f"{COMMUNIQUE_URL}/api/communique/create", engine_payload)
        if "error" in render_result:
            status, ct, data = _json({"error": render_result["error"], "step": "engine"}, 502)
            self._respond(status, ct, data)
            return

        # 2. Seal in Forensic Ledger
        receipt_id = f"COM-BUILDER-{datetime.datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        content_h  = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
        ledger_payload = {
            "id":               receipt_id,
            "actor":            body.get("sender", "builder"),
            "app":              "communique-builder",
            "doc_name":         body.get("title", "Communiqué"),
            "doc_type":         "communique",
            "governance_level": body.get("governance_level", "MEDIUM"),
            "hash":             content_h,
            "metadata": {
                "builder_version": VERSION,
                "recipient":       body.get("recipient", ""),
                "tags":            body.get("tags", []),
            }
        }
        ledger_result = _proxy_post(f"{LEDGER_URL}/api/receipts", ledger_payload)

        status, ct, data = _json({
            "status":       "published",
            "receipt_id":   receipt_id,
            "hash":         content_h,
            "engine":       render_result,
            "ledger":       ledger_result,
            "verify_url":   f"https://windi-domain.com/verify-public/?id={receipt_id}",
            "ts":           datetime.datetime.utcnow().isoformat() + "Z",
        })
        self._respond(status, ct, data)

    def _serve_index(self):
        idx = STATIC_DIR / "index.html"
        if not idx.exists():
            self._404(); return
        data = idx.read_bytes()
        self._respond(200, "text/html; charset=utf-8", data)

    def _serve_static(self, rel: str):
        f = STATIC_DIR / rel
        if not f.exists() or not f.is_file():
            self._404(); return
        ext = f.suffix.lower()
        ct  = {".css": "text/css", ".js": "application/javascript",
               ".png": "image/png", ".svg": "image/svg+xml",
               ".ico": "image/x-icon"}.get(ext, "application/octet-stream")
        self._respond(200, ct, f.read_bytes())

    def _404(self):
        status, ct, data = _json({"error": "Not found"}, 404)
        self._respond(status, ct, data)

    def _respond(self, status: int, ct: str, data: bytes):
        self.send_response(status)
        self.send_header("Content-Type", ct)
        self.send_header("Content-Length", str(len(data)))
        self._cors()
        self.end_headers()
        self.wfile.write(data)

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")


# ── main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"[WINDI] Communiqué Builder v{VERSION} → :{PORT}")
    print(f"[WINDI] Static: {STATIC_DIR}")
    print(f"[WINDI] Engine: {COMMUNIQUE_URL}")
    print(f"[WINDI] Ledger: {LEDGER_URL}")
    srv = HTTPServer(("0.0.0.0", PORT), BuilderHandler)
    srv.serve_forever()
