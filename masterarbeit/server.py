#!/usr/bin/env python3
import http.server, socketserver, os
PORT = 8084
DIR = os.path.dirname(os.path.abspath(__file__))
class H(http.server.SimpleHTTPRequestHandler):
    def __init__(s, *a, **k): super().__init__(*a, directory=DIR, **k)
os.chdir(DIR)
print(f"\n  WINDI Master Arbeit: http://87.106.29.233:{PORT}\n")
with socketserver.TCPServer(("", PORT), H) as httpd: httpd.serve_forever()
