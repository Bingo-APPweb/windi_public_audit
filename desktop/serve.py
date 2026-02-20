#!/usr/bin/env python3
"""WINDI Desktop — Static Server with Health Endpoint"""
import http.server
import socketserver
import os
import sys
import json
from datetime import datetime

PORT = int(os.environ.get("PORT", 8100))
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class DesktopHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            health = {
                "service": "windi-desktop",
                "status": "operational",
                "version": "1.0.0",
                "port": PORT,
                "path": "/desktop/",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "pages": {
                    "landing": "index.html",
                    "suite": "suite.html",
                    "sealing": "sealing.html",
                    "warroom": "warroom.html"
                },
                "wallet_integration": True,
                "principle": "AI processes. Human decides. WINDI guarantees."
            }
            self.wfile.write(json.dumps(health, indent=2).encode())
            return
        super().do_GET()

    def log_message(self, format, *args):
        sys.stdout.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {args[0]}\n")
        sys.stdout.flush()

if __name__ == "__main__":
    with socketserver.TCPServer(("0.0.0.0", PORT), DesktopHandler) as httpd:
        print(f"WINDI Desktop serving on port {PORT}")
        print(f"Directory: {DIRECTORY}")
        print(f"Health: http://localhost:{PORT}/health")
        httpd.serve_forever()
