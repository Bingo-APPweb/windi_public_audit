#!/usr/bin/env python3
"""WINDI Master Arbeit — Static file server with health endpoint."""
import http.server
import socketserver
import os
import json

PORT = 8084
DIR = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "service": "windi-masterarbeit",
                "version": "1.0.0",
                "status": "operational",
                "port": PORT
            }).encode())
            return
        return super().do_GET()

os.chdir(DIR)
print(f"\n  WINDI Master Arbeit: http://87.106.29.233:{PORT}")
print(f"  Health: http://127.0.0.1:{PORT}/health\n")
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    httpd.serve_forever()
