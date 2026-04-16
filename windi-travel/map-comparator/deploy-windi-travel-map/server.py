#!/usr/bin/env python3
"""
W-TRAVEL-MAP-001 — WINDI Travel Map Comparator Service
Port: 8153
Invariants: I9, I11, I16

Berlin Pitch Demo — Bayern Süd Cartographic Sovereignty
"""

import os
from flask import Flask, send_from_directory, redirect, jsonify

app = Flask(__name__)

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAPS_DIR = os.path.dirname(BASE_DIR)  # Parent: map-comparator/

# Map files
MAPS = {
    "01-svg-curado": "01-svg-curado.html",
    "02-leaflet-osm": "02-leaflet-osm.html",
    "03-maplibre-gl": "03-maplibre-gl.html",
    "03-v2-berlin-pitch": "03-v2-berlin-pitch.html",
}

@app.route("/health")
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "W-TRAVEL-MAP-001",
        "port": 8153,
        "invariants": ["I9", "I11", "I16"]
    })

@app.route("/api/info")
def api_info():
    """Service information."""
    return jsonify({
        "service": "W-TRAVEL-MAP-001",
        "version": "1.0.0",
        "description": "WINDI Travel Map Comparator — Bayern Süd",
        "maps": list(MAPS.keys()),
        "pitch_url": "/travel/map/berlin-pitch",
        "invariants": {
            "I9": "Human Approval Gate",
            "I11": "Cryptographic Evidence Permanence",
            "I16": "Creator Cartographic Sovereignty"
        }
    })

@app.route("/")
def index():
    """Serve comparator index."""
    return send_from_directory(MAPS_DIR, "index.html")

@app.route("/berlin-pitch")
def berlin_pitch():
    """Redirect to the Berlin Pitch map (v2)."""
    return redirect("/travel/map/03-v2-berlin-pitch")

@app.route("/<map_name>")
def serve_map(map_name):
    """Serve individual map files."""
    # Handle .html extension
    if map_name.endswith(".html"):
        map_name = map_name[:-5]

    if map_name in MAPS:
        return send_from_directory(MAPS_DIR, MAPS[map_name])

    # Fallback: try as-is
    filename = f"{map_name}.html"
    if os.path.exists(os.path.join(MAPS_DIR, filename)):
        return send_from_directory(MAPS_DIR, filename)

    return jsonify({"error": "Map not found", "available": list(MAPS.keys())}), 404

@app.route("/static/<path:filename>")
def serve_static(filename):
    """Serve static assets if any."""
    static_dir = os.path.join(MAPS_DIR, "static")
    if os.path.exists(static_dir):
        return send_from_directory(static_dir, filename)
    return jsonify({"error": "Static file not found"}), 404

if __name__ == "__main__":
    print("W-TRAVEL-MAP-001 — WINDI Travel Map Comparator")
    print("Port: 8153")
    print("Maps:", list(MAPS.keys()))
    app.run(host="127.0.0.1", port=8153, debug=False)
