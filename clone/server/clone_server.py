#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════
CLONE-A4DESK-WINDI — Servidor Autônomo
Porta 8092 · Território Soberano
═══════════════════════════════════════════════════════════════

Museum of the Future (5 Phases):
  1. Hello World
  2. Genesis Museum
  3. Cryptographic Gallery
  4. DNA Transparency Panel
  5. Sovereign Editor Preview

IA processa · Humano decide · WINDI garante
═══════════════════════════════════════════════════════════════
"""

import os
from flask import Flask, send_from_directory, redirect, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')
MUSEUM_DIR = os.path.join(STATIC_DIR, 'museum')

# ═══════════════════════════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════════════════════════

@app.route('/')
def index():
    """Landing page → Museum"""
    return redirect('/museum')


@app.route('/health')
def health():
    """Health check"""
    return jsonify({
        'service': 'clone-a4Desk-WINDI',
        'status': 'healthy',
        'territory': 'sovereign',
        'port': 8092,
        'components': ['museum', 'onboarding'],
        'principle': 'IA processa · Humano decide · WINDI garante'
    })


@app.route('/museum')
def museum_index():
    """Museum of the Future - Entry point"""
    return send_from_directory(MUSEUM_DIR, 'index.html')


@app.route('/museum/<path:filename>')
def museum_static(filename):
    """Serve museum static files (components, assets)"""
    return send_from_directory(MUSEUM_DIR, filename)


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("═" * 60)
    print("  clone-a4Desk-WINDI · Servidor Autônomo")
    print("  Porta 8092 · Território Soberano")
    print("═" * 60)
    print(f"  Museum: {MUSEUM_DIR}")
    print(f"  URL: http://0.0.0.0:8092")
    print("  IA processa · Humano decide · WINDI garante")
    print("═" * 60)

    app.run(host='0.0.0.0', port=8092, debug=False)
