#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
WINDI Distribution Engine v1.0.0
═══════════════════════════════════════════════════════════════════════════════
Port: 8116 | Path: /distribute/
The Sovereign Message Carrier — WINDI Publishing House

"AI processes. Human decides. WINDI guarantees."

Features:
  • Centralized SMTP (noreply@a4desk.de) — User needs NO technical knowledge
  • Quota management per tier (FREE: 10, STARTER: 100, PRO: 1000, ENTERPRISE: ∞)
  • Distribution Ledger — Every send is sealed and auditable
  • Reply-To preservation — Responses go to the original sender
  • Anti-spam governance — Content hashed, reputation protected

═══════════════════════════════════════════════════════════════════════════════
"""

import os
import json
import uuid
import hashlib
import sqlite3
import smtplib
import ssl
import datetime
import urllib.request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, formatdate
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Optional, Dict, Tuple

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

PORT            = int(os.getenv("PORT", 8116))
VERSION         = "1.0.0"
DB_PATH         = os.getenv("DIST_DB_PATH", "/opt/windi/data/distribution.db")
LEDGER_URL      = os.getenv("LEDGER_URL", "http://127.0.0.1:8101")
ID_GENESIS_URL  = os.getenv("ID_GENESIS_URL", "http://127.0.0.1:8096")

# SMTP Configuration (Centralized — WINDI Notary)
SMTP_HOST       = os.getenv("SMTP_HOST", "smtp.strato.de")
SMTP_PORT       = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER       = os.getenv("SMTP_USER", "info@a4desk.de")
SMTP_PASS       = os.getenv("SMTP_PASS", "")
SMTP_FROM_NAME  = "WINDI Publishing House"
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "noreply@a4desk.de")

# Tier Quotas
TIER_QUOTAS = {
    "FREE":       10,
    "STARTER":    100,
    "PRO":        1000,
    "ENTERPRISE": 999999,  # Effectively unlimited
}

# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE SETUP
# ═══════════════════════════════════════════════════════════════════════════════

def init_db():
    """Initialize distribution database with required tables."""
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Distribution Ledger — Every send is recorded
    cur.execute("""
        CREATE TABLE IF NOT EXISTS distribution_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dist_id TEXT UNIQUE NOT NULL,
            user_id TEXT,
            user_email TEXT,
            user_name TEXT,
            recipient_email TEXT NOT NULL,
            receipt_id TEXT,
            doc_title TEXT,
            content_hash TEXT,
            status TEXT DEFAULT 'sent',
            tier_at_time TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT
        )
    """)

    # Quota Tracking
    cur.execute("""
        CREATE TABLE IF NOT EXISTS distribution_quotas (
            user_id TEXT PRIMARY KEY,
            user_email TEXT,
            tier TEXT DEFAULT 'FREE',
            monthly_limit INTEGER DEFAULT 10,
            used_this_month INTEGER DEFAULT 0,
            reset_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print(f"[WINDI] Database initialized: {DB_PATH}")


def get_db():
    """Get database connection."""
    return sqlite3.connect(DB_PATH)


# ═══════════════════════════════════════════════════════════════════════════════
# QUOTA MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def get_or_create_quota(user_id: str, user_email: str, tier: str = "FREE") -> Dict:
    """Get or create quota for a user."""
    conn = get_db()
    cur = conn.cursor()

    # Check if quota exists
    cur.execute("SELECT * FROM distribution_quotas WHERE user_id = ?", (user_id,))
    row = cur.fetchone()

    today = datetime.date.today()

    if row:
        # Check if we need to reset (new month)
        reset_date = datetime.datetime.strptime(row[5], "%Y-%m-%d").date() if row[5] else today
        if today >= reset_date:
            # Reset quota for new month
            new_reset = (today.replace(day=1) + datetime.timedelta(days=32)).replace(day=1)
            cur.execute("""
                UPDATE distribution_quotas
                SET used_this_month = 0, reset_date = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (new_reset.isoformat(), user_id))
            conn.commit()
            used = 0
        else:
            used = row[4]

        quota = {
            "user_id": row[0],
            "user_email": row[1],
            "tier": row[2],
            "monthly_limit": row[3],
            "used_this_month": used,
            "reset_date": row[5],
        }
    else:
        # Create new quota
        monthly_limit = TIER_QUOTAS.get(tier.upper(), 10)
        reset_date = (today.replace(day=1) + datetime.timedelta(days=32)).replace(day=1)

        cur.execute("""
            INSERT INTO distribution_quotas (user_id, user_email, tier, monthly_limit, used_this_month, reset_date)
            VALUES (?, ?, ?, ?, 0, ?)
        """, (user_id, user_email, tier.upper(), monthly_limit, reset_date.isoformat()))
        conn.commit()

        quota = {
            "user_id": user_id,
            "user_email": user_email,
            "tier": tier.upper(),
            "monthly_limit": monthly_limit,
            "used_this_month": 0,
            "reset_date": reset_date.isoformat(),
        }

    conn.close()
    return quota


def increment_quota(user_id: str) -> bool:
    """Increment used quota for a user."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        UPDATE distribution_quotas
        SET used_this_month = used_this_month + 1, updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
    """, (user_id,))
    conn.commit()
    conn.close()
    return True


def record_distribution(dist_id: str, user_id: str, user_email: str, user_name: str,
                        recipient: str, receipt_id: str, doc_title: str,
                        content_hash: str, tier: str, metadata: dict = None) -> bool:
    """Record a distribution in the ledger."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO distribution_ledger
        (dist_id, user_id, user_email, user_name, recipient_email, receipt_id, doc_title, content_hash, tier_at_time, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (dist_id, user_id, user_email, user_name, recipient, receipt_id, doc_title,
          content_hash, tier, json.dumps(metadata or {})))
    conn.commit()
    conn.close()
    return True


# ═══════════════════════════════════════════════════════════════════════════════
# EMAIL TEMPLATES
# ═══════════════════════════════════════════════════════════════════════════════

def build_email_html(title: str, body: str, sender_name: str, receipt_id: str, verify_url: str) -> str:
    """Build beautiful HTML email with WINDI branding."""
    return f"""
<!DOCTYPE html>
<html lang="pt">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background:#0E0D0B;font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;">
  <div style="max-width:600px;margin:0 auto;padding:24px;">

    <!-- Header -->
    <div style="background:#1A1814;border-radius:12px 12px 0 0;padding:20px 24px;border-bottom:2px solid #C9A84C;">
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td>
            <div style="display:inline-block;width:36px;height:36px;background:#C9A84C;border-radius:8px;text-align:center;line-height:36px;font-size:18px;">⚓</div>
          </td>
          <td style="padding-left:12px;">
            <div style="color:#F5F0E0;font-size:16px;font-weight:700;">WINDI Publishing House</div>
            <div style="color:#6B6158;font-size:11px;font-family:monospace;">VERIFIED DOCUMENT DELIVERY</div>
          </td>
        </tr>
      </table>
    </div>

    <!-- Content -->
    <div style="background:#1A1814;padding:28px 24px;border-left:1px solid #2E2A24;border-right:1px solid #2E2A24;">

      <!-- Sender Badge -->
      <div style="background:#252018;border-radius:8px;padding:12px 16px;margin-bottom:20px;border-left:3px solid #C9A84C;">
        <div style="color:#6B6158;font-size:10px;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:4px;">Enviado por</div>
        <div style="color:#F5F0E0;font-size:14px;font-weight:600;">{sender_name}</div>
      </div>

      <!-- Document Title -->
      <h1 style="color:#C9A84C;font-size:22px;font-weight:700;margin:0 0 16px 0;line-height:1.3;">
        {title}
      </h1>

      <!-- Document Body -->
      <div style="color:#c9d1d9;font-size:14px;line-height:1.7;white-space:pre-wrap;">
{body}
      </div>

    </div>

    <!-- Footer: Verification -->
    <div style="background:#161410;border-radius:0 0 12px 12px;padding:20px 24px;border:1px solid #2E2A24;border-top:none;">

      <!-- Receipt ID -->
      <div style="background:#0E0D0B;border-radius:8px;padding:12px 16px;margin-bottom:16px;border:1px solid #2E2A24;">
        <table width="100%" cellpadding="0" cellspacing="0">
          <tr>
            <td style="color:#6B6158;font-size:11px;">Receipt ID</td>
            <td style="text-align:right;">
              <code style="color:#C9A84C;font-size:12px;font-family:monospace;">{receipt_id}</code>
            </td>
          </tr>
        </table>
      </div>

      <!-- Verify Button -->
      <a href="{verify_url}" style="display:block;background:#C9A84C;color:#0E0D0B;text-decoration:none;text-align:center;padding:14px 20px;border-radius:8px;font-weight:700;font-size:13px;">
        🔍 Verificar Autenticidade
      </a>

      <!-- Tagline -->
      <div style="text-align:center;margin-top:20px;padding-top:16px;border-top:1px solid #2E2A24;">
        <div style="color:#6B6158;font-size:10px;font-style:italic;">
          "AI processes. Human decides. WINDI guarantees."
        </div>
        <div style="color:#3D3830;font-size:9px;margin-top:6px;font-family:monospace;">
          WINDI Publishing House v{VERSION} | Sovereign Document Delivery
        </div>
      </div>

    </div>

  </div>
</body>
</html>
"""


def build_email_text(title: str, body: str, sender_name: str, receipt_id: str, verify_url: str) -> str:
    """Build plain text version of email."""
    return f"""
════════════════════════════════════════════════════════════
WINDI PUBLISHING HOUSE — VERIFIED DOCUMENT
════════════════════════════════════════════════════════════

Enviado por: {sender_name}

────────────────────────────────────────────────────────────
{title}
────────────────────────────────────────────────────────────

{body}

────────────────────────────────────────────────────────────
Receipt ID: {receipt_id}
Verificar:  {verify_url}

"AI processes. Human decides. WINDI guarantees."
════════════════════════════════════════════════════════════
"""


# ═══════════════════════════════════════════════════════════════════════════════
# SMTP SENDER
# ═══════════════════════════════════════════════════════════════════════════════

def send_email(recipient: str, subject: str, html_body: str, text_body: str,
               reply_to: str = None) -> Tuple[bool, str]:
    """Send email via centralized WINDI SMTP."""
    if not SMTP_PASS:
        return False, "SMTP not configured"

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[WINDI] {subject}"
        msg["From"] = formataddr((SMTP_FROM_NAME, SMTP_FROM_EMAIL))
        msg["To"] = recipient
        msg["Date"] = formatdate(localtime=True)

        if reply_to:
            msg["Reply-To"] = reply_to

        # Add headers for deliverability
        msg["X-Mailer"] = f"WINDI-Publishing-House/{VERSION}"
        msg["X-Priority"] = "3"

        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        # Send via SSL
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_FROM_EMAIL, recipient, msg.as_string())

        return True, "sent"

    except Exception as e:
        return False, str(e)


# ═══════════════════════════════════════════════════════════════════════════════
# FORENSIC LEDGER INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

def seal_in_ledger(dist_id: str, user_email: str, recipient: str, doc_title: str,
                   content_hash: str, metadata: dict = None) -> dict:
    """Seal distribution record in Forensic Ledger."""
    payload = {
        "id": dist_id,
        "actor": user_email,
        "app": "windi-distribution-engine",
        "doc_name": f"Distribution: {doc_title}",
        "doc_type": "communique",
        "governance_level": "MEDIUM",
        "content_hash": content_hash,
        "sge_score": 0.85,
        "metadata": {
            "recipient": recipient,
            "engine_version": VERSION,
            **(metadata or {})
        }
    }

    try:
        raw = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{LEDGER_URL}/api/receipts",
            data=raw,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════════
# HTTP HANDLER
# ═══════════════════════════════════════════════════════════════════════════════

def _json_response(body: dict, status: int = 200) -> Tuple[int, str, bytes]:
    data = json.dumps(body, ensure_ascii=False, default=str).encode()
    return status, "application/json", data


class DistributionHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        ts = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        print(f"[{ts}] {fmt % args}")

    def _respond(self, status: int, content_type: str, data: bytes):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0].rstrip("/") or "/"

        if path in ("/health", "/distribute/health"):
            self._handle_health()
        elif path in ("/distribute/api/quota", "/api/quota"):
            self._handle_quota_check()
        elif path in ("/distribute/api/stats", "/api/stats"):
            self._handle_stats()
        else:
            status, ct, data = _json_response({"error": "Not found"}, 404)
            self._respond(status, ct, data)

    def do_POST(self):
        path = self.path.split("?")[0].rstrip("/")
        length = int(self.headers.get("Content-Length", 0))

        # Bug fix: Capture JSON parsing errors gracefully
        try:
            raw = self.rfile.read(length) if length else b"{}"
            body = json.loads(raw)
        except Exception as e:
            self._respond(400, "application/json", json.dumps({"error": f"Invalid JSON: {str(e)}"}).encode())
            return

        if path in ("/distribute/api/send", "/api/send"):
            self._handle_send(body)
        elif path in ("/distribute/api/quota/upgrade", "/api/quota/upgrade"):
            self._handle_quota_upgrade(body)
        else:
            status, ct, data = _json_response({"error": "Not found"}, 404)
            self._respond(status, ct, data)

    # ── Handlers ──

    def _handle_health(self):
        status, ct, data = _json_response({
            "status": "healthy",
            "service": "windi-distribution-engine",
            "version": VERSION,
            "port": PORT,
            "ts": datetime.datetime.utcnow().isoformat() + "Z",
            "smtp_configured": bool(SMTP_PASS),
            "deps": {
                "ledger": LEDGER_URL,
                "id_genesis": ID_GENESIS_URL,
            }
        })
        self._respond(status, ct, data)

    def _handle_quota_check(self):
        """Check quota for a user (via query params)."""
        from urllib.parse import urlparse, parse_qs
        query = parse_qs(urlparse(self.path).query)

        user_id = query.get("user_id", ["anonymous"])[0]
        user_email = query.get("email", ["anonymous@windi.local"])[0]
        tier = query.get("tier", ["FREE"])[0]

        quota = get_or_create_quota(user_id, user_email, tier)
        quota["remaining"] = quota["monthly_limit"] - quota["used_this_month"]

        status, ct, data = _json_response(quota)
        self._respond(status, ct, data)

    def _handle_stats(self):
        """Get distribution statistics."""
        conn = get_db()
        cur = conn.cursor()

        # Total distributions
        cur.execute("SELECT COUNT(*) FROM distribution_ledger")
        total = cur.fetchone()[0]

        # Today's distributions
        today = datetime.date.today().isoformat()
        cur.execute("SELECT COUNT(*) FROM distribution_ledger WHERE DATE(sent_at) = ?", (today,))
        today_count = cur.fetchone()[0]

        # Unique users
        cur.execute("SELECT COUNT(DISTINCT user_id) FROM distribution_ledger")
        unique_users = cur.fetchone()[0]

        conn.close()

        status, ct, data = _json_response({
            "total_distributions": total,
            "today": today_count,
            "unique_users": unique_users,
            "version": VERSION,
        })
        self._respond(status, ct, data)

    def _handle_send(self, body: dict):
        """Main distribution endpoint — The Heart of Publishing House."""

        # Extract fields
        user_id = body.get("user_id", "anonymous")
        user_email = body.get("user_email", "anonymous@windi.local")
        user_name = body.get("user_name", "WINDI User")
        tier = body.get("tier", "FREE")

        recipient = body.get("recipient", "").strip()
        recipients = body.get("recipients", [])

        # Support single recipient or list
        if recipient and not recipients:
            recipients = [recipient]

        title = body.get("title", "WINDI Document")
        content = body.get("body", body.get("content", ""))
        receipt_id = body.get("receipt_id", "")

        # Validation
        if not recipients:
            status, ct, data = _json_response({"error": "No recipients provided"}, 400)
            self._respond(status, ct, data)
            return

        if not content:
            status, ct, data = _json_response({"error": "No content provided"}, 400)
            self._respond(status, ct, data)
            return

        # Check quota
        quota = get_or_create_quota(user_id, user_email, tier)
        remaining = quota["monthly_limit"] - quota["used_this_month"]

        if remaining < len(recipients):
            status, ct, data = _json_response({
                "error": "Quota exceeded",
                "quota": quota,
                "requested": len(recipients),
                "remaining": remaining,
                "upgrade_hint": "Upgrade your tier for more sends: FREE→STARTER→PRO→ENTERPRISE"
            }, 403)
            self._respond(status, ct, data)
            return

        # Generate distribution ID
        dist_id = f"DIST-{datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8].upper()}"
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        verify_url = f"https://windi-domain.com/verify-public/?id={receipt_id or dist_id}"

        # Build email
        html_body = build_email_html(title, content, user_name, receipt_id or dist_id, verify_url)
        text_body = build_email_text(title, content, user_name, receipt_id or dist_id, verify_url)

        # Send to all recipients
        results = []
        for r in recipients:
            r = r.strip()
            if not r or "@" not in r:
                results.append({"recipient": r, "status": "invalid", "error": "Invalid email"})
                continue

            success, msg = send_email(
                recipient=r,
                subject=title,
                html_body=html_body,
                text_body=text_body,
                reply_to=user_email if user_email != "anonymous@windi.local" else None
            )

            if success:
                # Record in local ledger
                record_distribution(
                    dist_id=f"{dist_id}-{len(results)}",
                    user_id=user_id,
                    user_email=user_email,
                    user_name=user_name,
                    recipient=r,
                    receipt_id=receipt_id,
                    doc_title=title,
                    content_hash=content_hash,
                    tier=tier
                )
                increment_quota(user_id)
                results.append({"recipient": r, "status": "sent"})
                print(f"[DISTRIBUTE] ✓ Sent to {r}")
            else:
                results.append({"recipient": r, "status": "failed", "error": msg})
                print(f"[DISTRIBUTE] ✗ Failed: {r} — {msg}")

        # Seal in Forensic Ledger
        # Use receipt_id if provided (from Communiqué), otherwise use dist_id
        seal_id = receipt_id if receipt_id else dist_id
        ledger_result = seal_in_ledger(
            dist_id=seal_id,
            user_email=user_email,
            recipient=", ".join(recipients),
            doc_title=title,
            content_hash=content_hash,
            metadata={"recipients_count": len(recipients), "tier": tier, "dist_id": dist_id}
        )

        # Calculate results
        sent_count = sum(1 for r in results if r["status"] == "sent")

        # Updated quota
        new_quota = get_or_create_quota(user_id, user_email, tier)

        status, ct, data = _json_response({
            "status": "distributed" if sent_count > 0 else "failed",
            "dist_id": dist_id,
            "sent": sent_count,
            "total": len(recipients),
            "results": results,
            "quota": {
                "used": new_quota["used_this_month"],
                "limit": new_quota["monthly_limit"],
                "remaining": new_quota["monthly_limit"] - new_quota["used_this_month"],
                "tier": new_quota["tier"],
            },
            "ledger": ledger_result,
            "ts": datetime.datetime.utcnow().isoformat() + "Z",
        })
        self._respond(status, ct, data)

    def _handle_quota_upgrade(self, body: dict):
        """Upgrade user tier (admin endpoint)."""
        user_id = body.get("user_id")
        new_tier = body.get("tier", "STARTER").upper()

        if not user_id:
            status, ct, data = _json_response({"error": "user_id required"}, 400)
            self._respond(status, ct, data)
            return

        if new_tier not in TIER_QUOTAS:
            status, ct, data = _json_response({"error": f"Invalid tier. Valid: {list(TIER_QUOTAS.keys())}"}, 400)
            self._respond(status, ct, data)
            return

        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            UPDATE distribution_quotas
            SET tier = ?, monthly_limit = ?, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (new_tier, TIER_QUOTAS[new_tier], user_id))
        conn.commit()
        conn.close()

        status, ct, data = _json_response({
            "status": "upgraded",
            "user_id": user_id,
            "new_tier": new_tier,
            "new_limit": TIER_QUOTAS[new_tier],
        })
        self._respond(status, ct, data)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print(f"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║  WINDI DISTRIBUTION ENGINE v{VERSION}                                            ║
║  The Sovereign Message Carrier — Publishing House                             ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║  Port:       {PORT}                                                              ║
║  SMTP:       {SMTP_HOST}:{SMTP_PORT}                                               ║
║  Ledger:     {LEDGER_URL}                                        ║
║  Database:   {DB_PATH}                              ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║  Tiers:      FREE(10) | STARTER(100) | PRO(1000) | ENTERPRISE(∞)              ║
╚═══════════════════════════════════════════════════════════════════════════════╝
    """)

    print("[WINDI] Initializing database...")
    init_db()

    print(f"[WINDI] Starting HTTP server on :{PORT}")
    print("[WINDI] \"AI processes. Human decides. WINDI guarantees.\"")

    server = HTTPServer(("0.0.0.0", PORT), DistributionHandler)
    server.serve_forever()
