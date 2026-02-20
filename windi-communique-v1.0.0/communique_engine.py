#!/usr/bin/env python3
"""
WINDI Communiqué Engine — Main Server
=======================================
Port: 8105
Stack: BaseHTTPRequestHandler + SQLite
Principle: "AI processes. Human decides. WINDI guarantees."

Endpoints:
  INTERNAL (localhost):
    POST /api/communique/create
    GET  /api/communique/{id}
    PUT  /api/communique/{id}
    POST /api/communique/{id}/review
    POST /api/communique/{id}/publish
    POST /api/communique/{id}/archive
    POST /api/communique/{id}/revoke
    GET  /api/communique/list
    GET  /api/communique/stats

  PUBLIC:
    GET  /communique/{id}           → HTML page
    GET  /communique/{id}/verify    → JSON verification
    GET  /communique/{id}/pdf       → PDF download
    GET  /communique/feed           → HTML feed
    GET  /communique/feed.json      → JSON feed
    GET  /health                    → Health check
"""

import json
import os
import re
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timezone
from urllib.parse import urlparse, parse_qs

# Add current dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import communique_db as db
from communique_publisher import publish_communique, compute_content_hash, verify_in_ledger
from communique_renderer import render_communique_page, render_feed_page, render_verify_page

PORT = int(os.environ.get("COMMUNIQUE_PORT", 8105))
VERSION = "1.0.0"
SERVICE_NAME = "windi-communique"


class CommuniqueHandler(BaseHTTPRequestHandler):
    """HTTP request handler for WINDI Communiqué Engine."""

    def log_message(self, format, *args):
        """Custom logging with timestamp."""
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        sys.stderr.write(f"[{ts}] [{SERVICE_NAME}] {format % args}\n")

    def send_json(self, data, status=200):
        """Send JSON response."""
        body = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, html, status=200):
        """Send HTML response."""
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, filepath, content_type, filename=None):
        """Send file response."""
        if not os.path.exists(filepath):
            self.send_json({"error": "File not found"}, 404)
            return
        with open(filepath, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", len(data))
        if filename:
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.end_headers()
        self.wfile.write(data)

    def read_body(self):
        """Read and parse JSON request body."""
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    # ─── ROUTING ──────────────────────────────────────────────

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        params = parse_qs(parsed.query)

        # Health
        if path == "/health":
            return self._handle_health()

        # Public feed
        if path == "/communique/feed":
            return self._handle_feed_html()
        if path == "/communique/feed.json":
            return self._handle_feed_json()

        # Public communiqué page
        m = re.match(r"^/communique/(COM-\d{8}-\d{4})$", path)
        if m:
            return self._handle_public_page(m.group(1))

        # Public verify
        m = re.match(r"^/communique/(COM-\d{8}-\d{4})/verify$", path)
        if m:
            return self._handle_verify(m.group(1))

        # Public PDF download
        m = re.match(r"^/communique/(COM-\d{8}-\d{4})/pdf$", path)
        if m:
            return self._handle_pdf_download(m.group(1))

        # API: get single
        m = re.match(r"^/api/communique/(COM-\d{8}-\d{4})$", path)
        if m:
            return self._handle_api_get(m.group(1))

        # API: list
        if path == "/api/communique/list":
            return self._handle_api_list(params)

        # API: stats
        if path == "/api/communique/stats":
            return self._handle_api_stats()

        # Static files
        if path.startswith("/static/"):
            return self._handle_static(path)

        self.send_json({"error": "Not found"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        # Create
        if path == "/api/communique/create":
            return self._handle_create()

        # Review
        m = re.match(r"^/api/communique/(COM-\d{8}-\d{4})/review$", path)
        if m:
            return self._handle_review(m.group(1))

        # Publish
        m = re.match(r"^/api/communique/(COM-\d{8}-\d{4})/publish$", path)
        if m:
            return self._handle_publish(m.group(1))

        # Archive
        m = re.match(r"^/api/communique/(COM-\d{8}-\d{4})/archive$", path)
        if m:
            return self._handle_archive(m.group(1))

        # Revoke
        m = re.match(r"^/api/communique/(COM-\d{8}-\d{4})/revoke$", path)
        if m:
            return self._handle_revoke(m.group(1))

        self.send_json({"error": "Not found"}, 404)

    def do_PUT(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        m = re.match(r"^/api/communique/(COM-\d{8}-\d{4})$", path)
        if m:
            return self._handle_update(m.group(1))

        self.send_json({"error": "Not found"}, 404)

    def do_OPTIONS(self):
        """CORS preflight."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    # ─── HEALTH ───────────────────────────────────────────────

    def _handle_health(self):
        stats = db.get_stats()
        self.send_json({
            "service": SERVICE_NAME,
            "version": VERSION,
            "status": "operational",
            "port": PORT,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "stats": stats,
            "principle": "AI processes. Human decides. WINDI guarantees."
        })

    # ─── API HANDLERS ─────────────────────────────────────────

    def _handle_create(self):
        try:
            data = self.read_body()
            if not data.get("title_de") or not data.get("body_de"):
                return self.send_json({"error": "title_de and body_de required"}, 400)
            if not data.get("author_name") or not data.get("author_role"):
                return self.send_json({"error": "author_name and author_role required"}, 400)

            result = db.create_communique(data)
            self.send_json(result, 201)
        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    def _handle_api_get(self, com_id):
        com = db.get_communique(com_id)
        if not com:
            return self.send_json({"error": "Not found"}, 404)
        # Include audit trail
        com["audit_trail"] = db.get_audit_trail(com_id)
        self.send_json(com)

    def _handle_update(self, com_id):
        try:
            data = self.read_body()
            result = db.update_communique(com_id, data)
            if "error" in result:
                return self.send_json(result, result.get("code", 400))
            self.send_json(result)
        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    def _handle_review(self, com_id):
        try:
            data = self.read_body()
            actor = data.get("actor", "system")
            result = db.transition_status(com_id, "REVIEW", actor)
            if "error" in result:
                return self.send_json(result, result.get("code", 400))
            self.send_json(result)
        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    def _handle_publish(self, com_id):
        """
        THE CRITICAL ENDPOINT.
        Transitions REVIEW → PUBLISHED with full crypto sealing.
        """
        try:
            data = self.read_body()
            actor = data.get("approved_by", data.get("actor", "system"))

            # Get current communiqué
            com = db.get_communique(com_id)
            if not com:
                return self.send_json({"error": "Not found"}, 404)
            if com["status"] != "REVIEW":
                return self.send_json({"error": f"Cannot publish from {com['status']}. Must be in REVIEW."}, 400)

            # 1. Transition to PUBLISHED
            transition = db.transition_status(com_id, "PUBLISHED", actor)
            if "error" in transition:
                return self.send_json(transition, transition.get("code", 400))

            # 2. Refresh communiqué with updated timestamps
            com = db.get_communique(com_id)

            # 3. Full publish workflow (hash + PDF + Ledger)
            pub_result = publish_communique(com, actor)

            # 4. Set crypto fields in DB
            if pub_result.get("success"):
                db.set_crypto_fields(
                    com_id,
                    content_hash=pub_result.get("content_hash"),
                    bundle_hash=pub_result.get("bundle_hash"),
                    ledger_id=pub_result.get("ledger_id"),
                    receipt_id=pub_result.get("receipt_id")
                )

            self.send_json({
                "id": com_id,
                "status": "PUBLISHED",
                "publish_result": pub_result,
                "timestamp": transition.get("timestamp")
            })

        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    def _handle_archive(self, com_id):
        try:
            data = self.read_body()
            actor = data.get("actor", "system")
            details = data.get("reason", "Archived by operator")
            result = db.transition_status(com_id, "ARCHIVED", actor, details)
            if "error" in result:
                return self.send_json(result, result.get("code", 400))
            self.send_json(result)
        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    def _handle_revoke(self, com_id):
        try:
            data = self.read_body()
            actor = data.get("actor", "system")
            details = data.get("reason")
            if not details:
                return self.send_json({"error": "Reason required for revocation"}, 400)
            result = db.transition_status(com_id, "REVOKED", actor, details)
            if "error" in result:
                return self.send_json(result, result.get("code", 400))
            self.send_json(result)
        except Exception as e:
            self.send_json({"error": str(e)}, 500)

    def _handle_api_list(self, params):
        status = params.get("status", [None])[0]
        category = params.get("category", [None])[0]
        limit = int(params.get("limit", [20])[0])
        offset = int(params.get("offset", [0])[0])
        result = db.list_communiques(status=status, category=category, limit=limit, offset=offset)
        self.send_json({"communiques": result, "count": len(result)})

    def _handle_api_stats(self):
        self.send_json(db.get_stats())

    # ─── PUBLIC HANDLERS ──────────────────────────────────────

    def _handle_public_page(self, com_id):
        """Render public HTML page for a communiqué."""
        com = db.get_communique(com_id)
        if not com or com["status"] not in ("PUBLISHED", "ARCHIVED", "REVOKED"):
            return self.send_html("<h1>Communiqué not found</h1>", 404)
        html = render_communique_page(com)
        self.send_html(html)

    def _handle_verify(self, com_id):
        """Public verification endpoint."""
        com = db.get_communique(com_id)
        if not com:
            return self.send_json({"error": "Not found", "verified": False}, 404)

        if com["status"] not in ("PUBLISHED", "ARCHIVED", "REVOKED"):
            return self.send_json({"error": "Not published", "verified": False}, 400)

        # Recompute hash from current DB content
        current_hash = compute_content_hash(com)
        hash_match = current_hash == com.get("content_hash")

        # Check Ledger if receipt exists
        ledger_verified = False
        ledger_status = "unknown"
        if com.get("receipt_id"):
            ledger_check = verify_in_ledger(com["receipt_id"])
            if ledger_check.get("success"):
                receipt = ledger_check.get("receipt", {})
                ledger_status = receipt.get("status", "unknown")
                ledger_verified = ledger_status == "sealed"

        self.send_json({
            "communique_id": com_id,
            "verified": hash_match and ledger_verified,
            "content_hash_match": hash_match,
            "content_hash_stored": com.get("content_hash"),
            "content_hash_computed": current_hash,
            "bundle_hash": com.get("bundle_hash"),
            "ledger_verified": ledger_verified,
            "ledger_status": ledger_status,
            "receipt_id": com.get("receipt_id"),
            "status": com.get("status"),
            "published_at": com.get("published_at"),
            "category": com.get("category"),
            "impact_level": com.get("impact_level"),
            "verification_timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        })

    def _handle_pdf_download(self, com_id):
        """Download published PDF."""
        com = db.get_communique(com_id)
        if not com or com["status"] not in ("PUBLISHED", "ARCHIVED"):
            return self.send_json({"error": "Not available"}, 404)

        pdf_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "published", com_id, "communique.pdf"
        )
        self.send_file(pdf_path, "application/pdf", f"{com_id}.pdf")

    def _handle_feed_html(self):
        """Public HTML feed of published communiqués."""
        communiques = db.list_published(limit=20)
        html = render_feed_page(communiques)
        self.send_html(html)

    def _handle_feed_json(self):
        """Public JSON feed."""
        communiques = db.list_published(limit=20)
        self.send_json({
            "feed": "WINDI Communiqué Feed",
            "version": VERSION,
            "count": len(communiques),
            "communiques": communiques,
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        })

    def _handle_static(self, path):
        """Serve static files."""
        static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
        filename = path.replace("/static/", "", 1)
        filepath = os.path.join(static_dir, filename)

        if not os.path.exists(filepath):
            return self.send_json({"error": "Not found"}, 404)

        ct = "text/plain"
        if filename.endswith(".css"):
            ct = "text/css"
        elif filename.endswith(".js"):
            ct = "application/javascript"
        self.send_file(filepath, ct)


def main():
    print("=" * 60)
    print(f"  🛡️  WINDI Communiqué Engine v{VERSION}")
    print(f"  Port: {PORT}")
    print(f"  Service: {SERVICE_NAME}")
    print(f"  DB: {db.DB_PATH}")
    print(f"  Principle: AI processes. Human decides. WINDI guarantees.")
    print("=" * 60)

    server = HTTPServer(("0.0.0.0", PORT), CommuniqueHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"\n[{SERVICE_NAME}] Shutting down gracefully...")
        server.server_close()


if __name__ == "__main__":
    main()
