#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
WINDI Clone 1 — Sovereign Editor v2.0
Porta: 8092
Funcao: Frontend que PROXIA /api/* para HUB (:8085)

O Clone NAO tem banco proprio.
O Clone e o ROSTO bonito do HUB.

AI processes. Human decides. WINDI guarantees.
═══════════════════════════════════════════════════════════════════════════════
"""
from flask import Flask, send_from_directory, request, Response, jsonify
from flask_cors import CORS
import requests
import tempfile
import io

import os

app = Flask(__name__)
CORS(app)

HUB_URL = "http://localhost:8085"
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

# ══════════════════════════════════════════════════════════════════════════════
# FRONTEND
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    """Serve the Sovereign Editor"""
    return send_from_directory(STATIC_DIR, "editor.html")

@app.route("/static/<path:filename>")
def static_files(filename):
    """Serve static assets"""
    return send_from_directory(STATIC_DIR, filename)

# ══════════════════════════════════════════════════════════════════════════════
# API PROXY → HUB :8085
# ══════════════════════════════════════════════════════════════════════════════


# ═══ WINDI FILE EXTRACT — PDF/DOCX text extraction ═══
@app.route("/api/extract", methods=["POST"])
def extract_text():
    """Extract text from uploaded PDF/DOCX files for analysis"""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    f = request.files['file']
    filename = f.filename.lower() if f.filename else ''

    try:
        if filename.endswith('.pdf'):
            try:
                import PyPDF2
                reader = PyPDF2.PdfReader(io.BytesIO(f.read()))
                text = '\n'.join(page.extract_text() or '' for page in reader.pages)
            except ImportError:
                return jsonify({"error": "PDF support not installed. Run: pip install PyPDF2 --break-system-packages"}), 500

        elif filename.endswith('.docx') or filename.endswith('.doc'):
            try:
                import docx
                doc = docx.Document(io.BytesIO(f.read()))
                text = '\n'.join(para.text for para in doc.paragraphs if para.text.strip())
            except ImportError:
                return jsonify({"error": "DOCX support not installed"}), 500

        elif filename.endswith('.txt') or filename.endswith('.md') or filename.endswith('.rtf'):
            text = f.read().decode('utf-8', errors='replace')

        else:
            return jsonify({"error": f"Unsupported format: {filename}"}), 400

        text = text.strip()
        if not text:
            return jsonify({"error": "No text could be extracted from file"}), 400

        return jsonify({
            "success": True,
            "text": text,
            "filename": f.filename,
            "chars": len(text),
            "source": "windi-extract"
        })

    except Exception as e:
        return jsonify({"error": f"Extraction failed: {str(e)}"}), 500

@app.route("/api/<path:subpath>", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
def proxy_to_hub(subpath):
    """Proxy ALL /api/* calls to HUB"""
    url = f"{HUB_URL}/api/{subpath}"

    # Forward query params
    if request.query_string:
        url += f"?{request.query_string.decode()}"

    # Handle CORS preflight
    if request.method == "OPTIONS":
        return Response("", status=200, headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Session-ID",
        })

    # Forward request to HUB
    try:
        # Build headers to forward
        forward_headers = {}
        for key, value in request.headers:
            key_lower = key.lower()
            if key_lower not in ("host", "content-length", "connection"):
                forward_headers[key] = value

        resp = requests.request(
            method=request.method,
            url=url,
            headers=forward_headers,
            data=request.get_data(),
            cookies=request.cookies,
            timeout=30,
            allow_redirects=False
        )

        # Build response headers
        excluded = {"content-encoding", "transfer-encoding", "connection"}
        headers = {k: v for k, v in resp.headers.items() if k.lower() not in excluded}
        headers["Access-Control-Allow-Origin"] = "*"

        return Response(resp.content, status=resp.status_code, headers=headers)

    except requests.exceptions.ConnectionError:
        return jsonify({
            "error": "HUB_UNREACHABLE",
            "message": "Central HUB is not responding"
        }), 503

    except requests.exceptions.Timeout:
        return jsonify({
            "error": "HUB_TIMEOUT",
            "message": "Request to HUB timed out"
        }), 504

    except Exception as e:
        return jsonify({
            "error": "PROXY_ERROR",
            "message": str(e)
        }), 500

# ══════════════════════════════════════════════════════════════════════════════
# HEALTH
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/health")
def health():
    """Health check with HUB connectivity"""
    hub_ok = False
    hub_info = None

    try:
        r = requests.get(f"{HUB_URL}/api/health", timeout=5)
        hub_ok = r.status_code == 200
        if hub_ok:
            hub_info = r.json()
    except:
        pass

    return jsonify({
        "service": "windi-clone-1",
        "name": "Sovereign Editor",
        "status": "operational" if hub_ok else "degraded",
        "hub_connected": hub_ok,
        "hub_url": HUB_URL,
        "hub_info": hub_info,
        "port": 8092
    })

# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("  WINDI Clone 1 — Sovereign Editor")
    print("=" * 70)
    print(f"  Editor:     http://0.0.0.0:8092")
    print(f"  HUB Proxy:  {HUB_URL}")
    print("  AI processes. Human decides. WINDI guarantees.")
    print("=" * 70)

    app.run(host="0.0.0.0", port=8092, debug=False)
