#!/usr/bin/env python3
"""
WINDI Landing Page Server v1.0.0
Port: 8107
Serves the P/M/G tier selection landing page.
"AI processes. Human decides. WINDI guarantees."
"""

import os
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

PORT = int(os.environ.get("LANDING_PORT", 8107))
VERSION = "1.0.0"
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


class LandingHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        print(f"[{ts}] LANDING {args[0]}")

    def do_GET(self):
        path = urlparse(self.path).path.rstrip("/")

        if path in ("", "/", "/index.html"):
            self._serve_file("index.html", "text/html")
        elif path == "/health":
            self._send_json({
                "service": "WINDI Landing P/M/G",
                "version": VERSION,
                "status": "healthy",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        else:
            # Try to serve static file
            rel = path.lstrip("/")
            filepath = os.path.join(STATIC_DIR, rel)

            # WS-7: Handle directory paths → index.html
            if os.path.isdir(filepath):
                index_path = os.path.join(filepath, "index.html")
                if os.path.isfile(index_path):
                    self._serve_file(os.path.join(rel, "index.html"), "text/html")
                    return

            if os.path.isfile(filepath):
                ct = "text/html"
                if filepath.endswith(".css"): ct = "text/css"
                elif filepath.endswith(".js"): ct = "application/javascript"
                elif filepath.endswith(".svg"): ct = "image/svg+xml"
                elif filepath.endswith(".png"): ct = "image/png"
                elif filepath.endswith(".ico"): ct = "image/x-icon"
                self._serve_file(rel, ct)
            else:
                self._send_json({"error": "Not found"}, 404)

    def _serve_file(self, filename, content_type):
        filepath = os.path.join(STATIC_DIR, filename)
        try:
            with open(filepath, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", f"{content_type}; charset=utf-8")
            self.send_header("Cache-Control", "public, max-age=300")
            self.end_headers()
            self.wfile.write(data)
        except FileNotFoundError:
            self._send_json({"error": "File not found"}, 404)

    def _send_json(self, data, status=200):
        import json
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())


def main():
    print(f"""
╔══════════════════════════════════════════════╗
║  🛡 WINDI Landing Page v{VERSION}               ║
║  Port: {PORT}                                  ║
║  Static: {STATIC_DIR}
║  "Choose your level of sovereignty."         ║
╚══════════════════════════════════════════════╝
    """)

    if not os.path.exists(os.path.join(STATIC_DIR, "index.html")):
        print(f"⚠️  WARNING: {STATIC_DIR}/index.html not found!")

    server = HTTPServer(("0.0.0.0", PORT), LandingHandler)
    print(f"[LANDING] Listening on http://0.0.0.0:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[LANDING] Shutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()
