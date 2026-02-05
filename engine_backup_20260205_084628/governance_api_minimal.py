"""
WINDI Governance API - Evolution Minimal
Phase 1.2: Identity detection + Governance Advisor via HTTP.

Port map (01 Feb 2026):
  8080 = windi_governance_api (complete)
  8081 = brain.trust_bus (uvicorn)
  8082 = windi_gateway
  8083 = THIS (evolution minimal)
  8084 = masterarbeit/server
  8085 = BABEL (a4desk_tiptap_babel)
  8086 = app.py
  8889 = windi_cortex

Phase history:
  1.0 = Pure heartbeat, zero engine deps (01 Feb 2026)
  1.1 = /health endpoint bridges engine via GovernanceHealthCheck (01 Feb 2026)
  1.2 = /detect + /recommend POST endpoints via IdentityDetector (02 Feb 2026)
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import sys
import os
from datetime import datetime, timezone

HOST = "0.0.0.0"
PORT = 8083
VERSION = "1.2-detect"

IDENTITY_DIR_PATH = os.environ.get(
    "WINDI_IDENTITY_DIR",
    "/opt/windi/config/identity_directory.json"
)

# --- Engine bridges (isolated) ---

def get_engine_health():
    """Bridge to GovernanceHealthCheck.quick_status()."""
    try:
        engine_dir = os.path.dirname(os.path.abspath(__file__))
        if engine_dir not in sys.path:
            sys.path.insert(0, engine_dir)
        from governance_health import GovernanceHealthCheck
        health = GovernanceHealthCheck()
        return health.quick_status()
    except ImportError as e:
        return {"engine_status": "import_error", "error": str(e)}
    except Exception as e:
        return {"engine_status": "error", "error": str(e)}


def get_detector():
    """Lazy loader for IdentityDetector. Returns (detector, error_or_None)."""
    try:
        engine_dir = os.path.dirname(os.path.abspath(__file__))
        if engine_dir not in sys.path:
            sys.path.insert(0, engine_dir)
        from identity_detector import IdentityDetector
        detector = IdentityDetector(directory_path=IDENTITY_DIR_PATH)
        return detector, None
    except ImportError as e:
        return None, {"error": "import_error", "detail": f"Cannot import IdentityDetector: {e}"}
    except Exception as e:
        return None, {"error": "init_error", "detail": str(e)}


def do_detect(text):
    """Bridge to IdentityDetector.scan_text()."""
    detector, err = get_detector()
    if err:
        return {"detections": [], "count": 0, "error": err}
    try:
        detections = detector.scan_text(text)
        return {"detections": detections, "count": len(detections)}
    except Exception as e:
        return {"detections": [], "count": 0, "error": {"error": "scan_error", "detail": str(e)}}


def do_recommend(text, current_level="LOW"):
    """Bridge to IdentityDetector.get_governance_recommendation()."""
    detector, err = get_detector()
    if err:
        return {"action": "error", "current_level": current_level, "recommended_level": current_level, "error": err}
    try:
        return detector.get_governance_recommendation(text, current_level)
    except Exception as e:
        return {"action": "error", "current_level": current_level, "recommended_level": current_level, "error": {"error": "recommend_error", "detail": str(e)}}


# --- HTTP Handler ---

ENDPOINTS = {
    "GET": ["/api/governance/status", "/api/governance/health"],
    "POST": ["/api/governance/detect", "/api/governance/recommend"]
}


class GovernanceHandler(BaseHTTPRequestHandler):

    def _set_headers(self, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("X-WINDI-Version", VERSION)
        self.end_headers()

    def _read_body(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return {}
        raw = self.rfile.read(content_length)
        try:
            return json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            return {"_parse_error": str(e)}

    def _send_json(self, data, code=200):
        self._set_headers(code)
        self.wfile.write(json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8"))

    def do_GET(self):
        if self.path == "/api/governance/status":
            self._send_json({
                "status": "UP",
                "service": "WINDI Governance API",
                "version": VERSION,
                "checked_at": datetime.now(timezone.utc).isoformat()
            })
        elif self.path == "/api/governance/health":
            self._send_json({
                "status": "UP",
                "version": VERSION,
                "checked_at": datetime.now(timezone.utc).isoformat(),
                "engine": get_engine_health()
            })
        else:
            self._send_json({"error": "Not found", "available": ENDPOINTS}, 404)

    def do_POST(self):
        body = self._read_body()
        if "_parse_error" in body:
            self._send_json({"error": "Invalid JSON", "detail": body["_parse_error"]}, 400)
            return

        if self.path == "/api/governance/detect":
            text = body.get("text", "")
            if not text:
                self._send_json({"error": "Missing text field", "usage": "POST {text: ...}"}, 400)
                return
            self._send_json(do_detect(text))

        elif self.path == "/api/governance/recommend":
            text = body.get("text", "")
            current_level = body.get("current_level", "LOW")
            if not text:
                self._send_json({"error": "Missing text field", "usage": "POST {text: ..., current_level: LOW}"}, 400)
                return
            if current_level not in ("LOW", "MEDIUM", "HIGH"):
                self._send_json({"error": "Invalid current_level", "valid": ["LOW","MEDIUM","HIGH"]}, 400)
                return
            self._send_json(do_recommend(text, current_level))

        else:
            self._send_json({"error": "Not found", "available": ENDPOINTS}, 404)

    def log_message(self, format, *args):
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        print(f"[{timestamp}] {args[0]}")


def run():
    server = HTTPServer((HOST, PORT), GovernanceHandler)
    print(f"WINDI Governance API ({VERSION}) running on port {PORT}")
    print(f"Endpoints:")
    print(f"  GET  /api/governance/status     (pure heartbeat)")
    print(f"  GET  /api/governance/health     (engine bridge)")
    print(f"  POST /api/governance/detect     (identity detection)")
    print(f"  POST /api/governance/recommend  (governance advisor)")
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    server.serve_forever()


if __name__ == "__main__":
    run()
