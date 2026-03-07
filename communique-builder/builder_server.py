"""
WINDI Communiqué Builder — v2.1.0
Port: 8115 | Path: /builder/
"AI processes. Human decides. WINDI guarantees."
"""

import os
import json
import uuid
import hashlib
import datetime
import urllib.request
import urllib.error
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

PORT           = int(os.getenv("PORT", 8115))
COMMUNIQUE_URL = os.getenv("COMMUNIQUE_ENGINE_URL", "http://127.0.0.1:8105")
LEDGER_URL     = os.getenv("LEDGER_URL",             "http://127.0.0.1:8101")
STATIC_DIR     = Path(__file__).parent / "static"
VERSION        = "2.1.0"

# SMTP Configuration (Strato)
SMTP_HOST      = os.getenv("SMTP_HOST", "smtp.strato.de")
SMTP_PORT      = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER      = os.getenv("SMTP_USER", "info@a4desk.de")
SMTP_PASS      = os.getenv("SMTP_PASS", "")


# ── helpers ──────────────────────────────────────────────────────────────────

def _json(body: dict, status: int = 200) -> tuple:
    data = json.dumps(body, ensure_ascii=False, default=str).encode()
    return status, "application/json", data


def _proxy_post(url: str, payload: dict) -> dict:
    """Fire-and-forget JSON POST, return response dict."""
    raw = json.dumps(payload).encode()
    req = urllib.request.Request(
        url, data=raw,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}


# ── request handler ───────────────────────────────────────────────────────────

class BuilderHandler(SimpleHTTPRequestHandler):

    def log_message(self, fmt, *args):
        ts = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        print(f"[{ts}] {fmt % args}")

    # ── routing ──
    def do_GET(self):
        path = self.path.split("?")[0].rstrip("/") or "/"

        routes = {
            "/health":            self._health,
            "/builder/health":    self._health,
            "/builder/api/info":  self._info,
        }

        if path in routes:
            routes[path]()
        elif path in ("/builder", "/builder/", "/"):
            self._serve_index()
        elif path.startswith("/builder/static/"):
            rel = path[len("/builder/static/"):]
            self._serve_static(rel)
        else:
            self._404()

    def do_POST(self):
        path = self.path.split("?")[0].rstrip("/")
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}

        routes = {
            "/builder/api/preview":    (self._preview,    body),
            "/builder/api/publish":    (self._publish,    body),
            "/builder/api/draft":      (self._draft,      body),
            "/builder/api/distribute": (self._distribute, body),
        }

        if path in routes:
            fn, b = routes[path]
            fn(b)
        else:
            self._404()

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    # ── handlers ──

    def _health(self):
        status, ct, data = _json({
            "status":  "healthy",
            "service": "windi-communique-builder",
            "version": VERSION,
            "port":    PORT,
            "ts":      datetime.datetime.utcnow().isoformat() + "Z",
            "deps": {
                "communique_engine": COMMUNIQUE_URL,
                "ledger":            LEDGER_URL,
            }
        })
        self._respond(status, ct, data)

    def _info(self):
        status, ct, data = _json({
            "builder":  f"WINDI Communiqué Builder v{VERSION}",
            "engine":   COMMUNIQUE_URL,
            "ledger":   LEDGER_URL,
            "doc_types": ["communique", "communiqué"],
            "principle": "AI processes. Human decides. WINDI guarantees.",
        })
        self._respond(status, ct, data)

    def _preview(self, body: dict):
        """Generate preview — calls communiqué engine."""
        result = _proxy_post(f"{COMMUNIQUE_URL}/api/preview", body)
        status, ct, data = _json(result)
        self._respond(status, ct, data)

    def _draft(self, body: dict):
        """Save draft locally (in-memory, no ledger seal)."""
        draft_id = f"DRAFT-{uuid.uuid4().hex[:8].upper()}"
        content  = json.dumps(body, sort_keys=True)
        h        = hashlib.sha256(content.encode()).hexdigest()[:16]
        status, ct, data = _json({
            "draft_id":  draft_id,
            "hash":      h,
            "ts":        datetime.datetime.utcnow().isoformat() + "Z",
            "status":    "draft_saved",
            "note":      "Draft is ephemeral — publish to seal in Ledger.",
        })
        self._respond(status, ct, data)

    def _publish(self, body: dict):
        """Publish → Engine → Ledger seal. Human already approved."""
        # 1. Send to Communiqué Engine for rendering
        engine_payload = {
            "title_de":    body.get("title", ""),
            "body_de":     body.get("body", ""),
            "author_name": body.get("sender", ""),
            "author_role": body.get("sender_role", "CGO"),
            "recipient":   body.get("recipient", ""),
            "governance_level": body.get("governance_level", "MEDIUM"),
        }
        render_result = _proxy_post(f"{COMMUNIQUE_URL}/api/communique/create", engine_payload)
        if "error" in render_result:
            status, ct, data = _json({"error": render_result["error"], "step": "engine"}, 502)
            self._respond(status, ct, data)
            return

        # 2. Seal in Forensic Ledger
        receipt_id = f"COM-BUILDER-{datetime.datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        content_h  = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
        ledger_payload = {
            "id":               receipt_id,
            "actor":            body.get("sender", "builder"),
            "app":              "communique-builder",
            "doc_name":         body.get("title", "Communiqué"),
            "doc_type":         "communique",
            "governance_level": body.get("governance_level", "MEDIUM"),
            "hash":             content_h,
            "metadata": {
                "builder_version": VERSION,
                "recipient":       body.get("recipient", ""),
                "tags":            body.get("tags", []),
            }
        }
        ledger_result = _proxy_post(f"{LEDGER_URL}/api/receipts", ledger_payload)

        status, ct, data = _json({
            "status":       "published",
            "receipt_id":   receipt_id,
            "hash":         content_h,
            "engine":       render_result,
            "ledger":       ledger_result,
            "verify_url":   f"https://windi-domain.com/verify-public/?id={receipt_id}",
            "ts":           datetime.datetime.utcnow().isoformat() + "Z",
        })
        self._respond(status, ct, data)

    def _distribute(self, body: dict):
        """Distribute document via Email/SMTP. Human approved."""
        channel = body.get("channel", "email")
        recipients = body.get("recipients", [])
        title = body.get("title", "WINDI Communiqué")
        content = body.get("body", "")
        sender_name = body.get("sender", "WINDI System")
        receipt_id = body.get("receipt_id", "")

        if not recipients:
            status, ct, data = _json({"error": "No recipients provided"}, 400)
            self._respond(status, ct, data)
            return

        if channel != "email":
            status, ct, data = _json({"error": f"Channel '{channel}' not yet supported"}, 400)
            self._respond(status, ct, data)
            return

        if not SMTP_PASS:
            status, ct, data = _json({"error": "SMTP not configured (missing SMTP_PASS)"}, 500)
            self._respond(status, ct, data)
            return

        # Build email
        results = []
        for recipient in recipients:
            try:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = f"[WINDI] {title}"
                msg["From"] = f"{sender_name} <{SMTP_USER}>"
                msg["To"] = recipient

                # Plain text version
                text_body = f"""
WINDI Communiqué
================
{title}

{content}

---
Receipt ID: {receipt_id}
Verify: https://windi-domain.com/verify-public/?id={receipt_id}

"AI processes. Human decides. WINDI guarantees."
                """.strip()

                # HTML version
                html_body = f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: 'Segoe UI', sans-serif; background: #0d1117; color: #c9d1d9; padding: 20px;">
  <div style="max-width: 600px; margin: 0 auto; background: #161b22; border-radius: 8px; padding: 24px; border: 1px solid #30363d;">
    <h1 style="color: #58a6ff; margin-top: 0;">{title}</h1>
    <div style="white-space: pre-wrap; line-height: 1.6;">{content}</div>
    <hr style="border: none; border-top: 1px solid #30363d; margin: 20px 0;">
    <p style="font-size: 12px; color: #8b949e;">
      Receipt ID: <code style="background: #21262d; padding: 2px 6px; border-radius: 4px;">{receipt_id}</code><br>
      <a href="https://windi-domain.com/verify-public/?id={receipt_id}" style="color: #58a6ff;">Verify Document</a>
    </p>
    <p style="font-size: 11px; color: #6e7681; font-style: italic;">
      "AI processes. Human decides. WINDI guarantees."
    </p>
  </div>
</body>
</html>
                """.strip()

                msg.attach(MIMEText(text_body, "plain", "utf-8"))
                msg.attach(MIMEText(html_body, "html", "utf-8"))

                # Send via SMTP SSL
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
                    server.login(SMTP_USER, SMTP_PASS)
                    server.sendmail(SMTP_USER, recipient, msg.as_string())

                results.append({"recipient": recipient, "status": "sent"})
                print(f"[DISTRIBUTE] Email sent to {recipient}")

            except Exception as e:
                results.append({"recipient": recipient, "status": "failed", "error": str(e)})
                print(f"[DISTRIBUTE] Failed to send to {recipient}: {e}")

        # Log to Forensic Ledger
        dist_id = f"DIST-{datetime.datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        ledger_payload = {
            "id":               dist_id,
            "actor":            sender_name,
            "app":              "communique-builder",
            "doc_name":         f"Distribution: {title}",
            "doc_type":         "distribution",
            "governance_level": "MEDIUM",
            "hash":             hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest(),
            "metadata": {
                "channel":     channel,
                "recipients":  len(recipients),
                "receipt_id":  receipt_id,
            }
        }
        ledger_result = _proxy_post(f"{LEDGER_URL}/api/receipts", ledger_payload)

        sent_count = sum(1 for r in results if r["status"] == "sent")
        status, ct, data = _json({
            "status":       "distributed",
            "dist_id":      dist_id,
            "channel":      channel,
            "sent":         sent_count,
            "total":        len(recipients),
            "results":      results,
            "ledger":       ledger_result,
            "ts":           datetime.datetime.utcnow().isoformat() + "Z",
        })
        self._respond(status, ct, data)

    def _serve_index(self):
        idx = STATIC_DIR / "index.html"
        if not idx.exists():
            self._404(); return
        data = idx.read_bytes()
        self._respond(200, "text/html; charset=utf-8", data)

    def _serve_static(self, rel: str):
        f = STATIC_DIR / rel
        if not f.exists() or not f.is_file():
            self._404(); return
        ext = f.suffix.lower()
        ct  = {".css": "text/css", ".js": "application/javascript",
               ".png": "image/png", ".svg": "image/svg+xml",
               ".ico": "image/x-icon"}.get(ext, "application/octet-stream")
        self._respond(200, ct, f.read_bytes())

    def _404(self):
        status, ct, data = _json({"error": "Not found"}, 404)
        self._respond(status, ct, data)

    def _respond(self, status: int, ct: str, data: bytes):
        self.send_response(status)
        self.send_header("Content-Type", ct)
        self.send_header("Content-Length", str(len(data)))
        self._cors()
        self.end_headers()
        self.wfile.write(data)

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")


# ── main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"[WINDI] Communiqué Builder v{VERSION} → :{PORT}")
    print(f"[WINDI] Static: {STATIC_DIR}")
    print(f"[WINDI] Engine: {COMMUNIQUE_URL}")
    print(f"[WINDI] Ledger: {LEDGER_URL}")
    srv = HTTPServer(("0.0.0.0", PORT), BuilderHandler)
    srv.serve_forever()
