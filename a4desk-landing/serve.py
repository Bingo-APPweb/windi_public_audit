#!/usr/bin/env python3
"""WINDI A4 Desk Landing — Static file server with health endpoint."""
import http.server
import socketserver
import os
import json

PORT = 8086
DIRECTORY = "/opt/windi/a4desk-landing"

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "service": "windi-a4desk-landing",
                "version": "1.0.0",
                "status": "operational",
                "port": PORT
            }).encode())
            return
        return super().do_GET()

    def log_message(self, format, *args):
        pass  # Suppress logs

os.chdir(DIRECTORY)
print(f"A4 Desk Landing serving on :{PORT}")
print(f"Health: http://127.0.0.1:{PORT}/health")
with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
    httpd.serve_forever()
