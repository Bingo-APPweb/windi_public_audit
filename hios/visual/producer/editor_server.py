#!/usr/bin/env python3
"""
WINDI Cinema Editor — Backend Server
Guarda alterações do editor para o Claude poder ver.
Port: 8197
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

DATA_FILE = "/opt/windi/hios/visual/producer/editor_state.json"

def load_state():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return None

def save_state(data):
    data['saved_at'] = datetime.now().isoformat()
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

@app.route('/api/editor/state', methods=['GET'])
def get_state():
    """Claude usa isto para ver o estado actual"""
    state = load_state()
    if state:
        return jsonify(state)
    return jsonify({"error": "Nenhuma edição guardada ainda"}), 404

@app.route('/api/editor/state', methods=['POST'])
def save_state_endpoint():
    """Editor envia alterações para aqui"""
    data = request.json
    save_state(data)
    return jsonify({"status": "ok", "saved_at": data.get('saved_at')})

@app.route('/api/editor/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "windi-cinema-editor"})

if __name__ == '__main__':
    print("🎬 WINDI Cinema Editor Server")
    print("   Port: 8197")
    print("   State: " + DATA_FILE)
    app.run(host='127.0.0.1', port=8197, debug=False)
