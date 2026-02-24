#!/usr/bin/env python3
"""Simple HTTP server for A4 Desk Landing page."""
import http.server
import socketserver
import os

PORT = 8086
DIRECTORY = "/opt/windi/a4desk-landing"

os.chdir(DIRECTORY)

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def log_message(self, format, *args):
        pass  # Suppress logs

with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
    print(f"A4 Desk Landing serving on :{PORT}")
    httpd.serve_forever()
