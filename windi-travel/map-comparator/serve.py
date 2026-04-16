#!/usr/bin/env python3
"""
Simple HTTP server for WINDI Travel Map Comparator
Port: 8180
Usage: python3 serve.py

Access:
  - http://localhost:8180/01-svg-curado.html
  - http://localhost:8180/02-leaflet-osm.html
  - http://localhost:8180/03-maplibre-gl.html
  - http://localhost:8180/ (index)
"""

import http.server
import socketserver
import os

PORT = 8180
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

os.chdir(DIRECTORY)

Handler = http.server.SimpleHTTPRequestHandler

# Generate simple index
INDEX_HTML = """<!DOCTYPE html>
<html lang="pt">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>WINDI Travel · Comparador de Mapas</title>
<style>
  body{font-family:system-ui;background:#F5F0E0;color:#2A2520;padding:40px;max-width:600px;margin:0 auto}
  h1{font-size:24px;border-bottom:2px solid #8B6914;padding-bottom:12px}
  ul{list-style:none;padding:0}
  li{margin:16px 0}
  a{display:block;padding:16px 20px;background:#FAF6EA;border:1px solid #C4B896;text-decoration:none;color:#2A2520;font-weight:600}
  a:hover{background:#8B6914;color:#FAF6EA;border-color:#8B6914}
  .num{color:#8B6914;margin-right:12px}
</style>
</head>
<body>
<h1>Comparador de Mapas · Bayern Süd</h1>
<ul>
<li><a href="01-svg-curado.html"><span class="num">01</span>SVG Curado — Ilustração Editorial</a></li>
<li><a href="02-leaflet-osm.html"><span class="num">02</span>Leaflet + OSM — Tema KLAR</a></li>
<li><a href="03-maplibre-gl.html"><span class="num">03</span>MapLibre GL — Cinematográfico</a></li>
</ul>
<p style="margin-top:40px;font-size:12px;color:#5C5548">WINDI Travel · I16 Creator Cartographic Sovereignty</p>
</body>
</html>
"""

with open(os.path.join(DIRECTORY, "index.html"), "w") as f:
    f.write(INDEX_HTML)

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"🗺️  WINDI Travel Map Comparator")
    print(f"📍 Serving at http://localhost:{PORT}")
    print(f"📁 Directory: {DIRECTORY}")
    print()
    print("Maps:")
    print(f"  http://localhost:{PORT}/01-svg-curado.html")
    print(f"  http://localhost:{PORT}/02-leaflet-osm.html")
    print(f"  http://localhost:{PORT}/03-maplibre-gl.html")
    print()
    print("Press Ctrl+C to stop")
    httpd.serve_forever()
