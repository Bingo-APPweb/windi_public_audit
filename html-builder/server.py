#!/usr/bin/env python3
"""
WINDI HTML Builder Server v3.0
Port: 8117
Pattern: BaseHTTPRequestHandler (WINDI standard)
"AI processes. Human decides. WINDI guarantees."
"""
import http.server
import socketserver
import os
from pathlib import Path

PORT = 8117
BASE_DIR = Path(__file__).parent
UI_FILE = BASE_DIR / "ui" / "index.html"

class WINDIHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Serve index.html for all routes (SPA)
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.send_header("X-WINDI-Service", "html-builder-v3")
        self.end_headers()
        with open(UI_FILE, "rb") as f:
            self.wfile.write(f.read())

    def log_message(self, format, *args):
        pass  # Silent — logs via nohup redirect

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), WINDIHandler) as httpd:
        print(f"[WINDI HTML Builder v3.0] Listening on :{PORT}")
        httpd.serve_forever()
