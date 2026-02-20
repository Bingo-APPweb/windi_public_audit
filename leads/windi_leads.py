#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════
  WINDI Lead Capture API v1.0.0
  Port 8096 · Zero Dependencies · Forensic-Grade

  "Cada lead é uma semente. O jardim cresce com disciplina."

  Three Dragons Protocol v1.1 · I1-I9 Active
═══════════════════════════════════════════════════════════════════

  Endpoints:
    POST /api/leads          — Capture new lead
    GET  /api/leads/count    — Lead count (authenticated)
    GET  /api/leads/export   — Export leads CSV (authenticated)
    GET  /health             — Health check

  Storage:
    /opt/windi/leads/leads.jsonl        — Append-only lead ledger
    /opt/windi/leads/leads_daily.csv    — Daily CSV export

  Security:
    - CORS restricted to a4desk.de domains
    - Admin endpoints require WINDI_LEADS_SECRET
    - Rate limiting per IP (10 leads/hour)
    - Input sanitization
    - Hash chain integrity (same as Schnittstelle)
"""

import json
import hashlib
import secrets
import os
import sys
import csv
import io
import re
from datetime import datetime, timezone, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from collections import defaultdict
import logging

# ── Configuration ──
VERSION = "1.0.0"
PORT = 8096
WINDI_BASE = Path("/opt/windi")
LEADS_DIR = WINDI_BASE / "leads"
LEADS_FILE = LEADS_DIR / "leads.jsonl"
LEADS_CSV = LEADS_DIR / "leads_daily.csv"

# Environment
ENV_LEADS_SECRET = "WINDI_LEADS_SECRET"  # For admin endpoints
ENV_CORS_ORIGINS = "WINDI_LEADS_CORS"    # Comma-separated allowed origins

# Defaults
DEFAULT_CORS = "https://a4desk.de,https://www.a4desk.de,http://localhost:8085,https://clone.windia4desk.tech"
RATE_LIMIT_PER_HOUR = 10
MAX_FIELD_LENGTH = 500

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [LEADS] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("windi-leads")

BANNER = f"""
╔═══════════════════════════════════════════════════════════════════╗
║   WINDI LEAD CAPTURE API v{VERSION}                                 ║
║   Port {PORT} · "Cada lead é uma semente."                        ║
║   Three Dragons Protocol v1.1 · I1-I9 Active                   ║
╚═══════════════════════════════════════════════════════════════════╝
"""


# ═══════════════════════════════════════════════════════════════════
# LEAD LEDGER — Append-only JSONL with hash chain
# ═══════════════════════════════════════════════════════════════════

class LeadLedger:
    """Forensic-grade lead storage with hash chain integrity."""

    def __init__(self):
        LEADS_DIR.mkdir(parents=True, exist_ok=True)

    def _get_last_hash(self) -> str:
        if not LEADS_FILE.exists() or LEADS_FILE.stat().st_size == 0:
            return "GENESIS"
        with open(LEADS_FILE, "r") as f:
            lines = f.readlines()
            if not lines:
                return "GENESIS"
            try:
                last = json.loads(lines[-1].strip())
                return last.get("hash", "GENESIS")
            except (json.JSONDecodeError, IndexError):
                return "GENESIS"

    def append(self, lead_data: dict) -> dict:
        prev_hash = self._get_last_hash()
        entry = {
            "id": f"LEAD-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(4)}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": lead_data,
            "prev_hash": prev_hash,
        }
        # Compute hash
        raw = json.dumps(entry, sort_keys=True, ensure_ascii=False)
        entry["hash"] = hashlib.sha256(raw.encode()).hexdigest()

        # Append
        with open(LEADS_FILE, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        return entry

    def count(self) -> int:
        if not LEADS_FILE.exists():
            return 0
        with open(LEADS_FILE, "r") as f:
            return sum(1 for line in f if line.strip())

    def get_all(self) -> list:
        if not LEADS_FILE.exists():
            return []
        leads = []
        with open(LEADS_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        leads.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return leads

    def verify_chain(self) -> dict:
        leads = self.get_all()
        if not leads:
            return {"status": "EMPTY", "entries": 0}

        for i, entry in enumerate(leads):
            expected_prev = "GENESIS" if i == 0 else leads[i - 1].get("hash")
            if entry.get("prev_hash") != expected_prev:
                return {
                    "status": "BROKEN",
                    "entries": len(leads),
                    "broken_at": i,
                }
        return {
            "status": "INTACT",
            "entries": len(leads),
            "last_hash": leads[-1].get("hash", "?")[:16],
        }

    def export_csv(self) -> str:
        leads = self.get_all()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "timestamp", "name", "email", "company", "interest", "source", "hash"])
        for lead in leads:
            d = lead.get("data", {})
            writer.writerow([
                lead.get("id", ""),
                lead.get("timestamp", ""),
                d.get("name", ""),
                d.get("email", ""),
                d.get("company", ""),
                d.get("interest", ""),
                d.get("source", ""),
                lead.get("hash", "")[:16],
            ])
        return output.getvalue()


# ═══════════════════════════════════════════════════════════════════
# RATE LIMITER — Per-IP, in-memory
# ═══════════════════════════════════════════════════════════════════

class RateLimiter:
    def __init__(self, max_per_hour: int = RATE_LIMIT_PER_HOUR):
        self.max = max_per_hour
        self.requests = defaultdict(list)

    def check(self, ip: str) -> bool:
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=1)
        # Clean old entries
        self.requests[ip] = [t for t in self.requests[ip] if t > cutoff]
        if len(self.requests[ip]) >= self.max:
            return False
        self.requests[ip].append(now)
        return True


# ═══════════════════════════════════════════════════════════════════
# INPUT VALIDATION
# ═══════════════════════════════════════════════════════════════════

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")

def sanitize(value: str, max_len: int = MAX_FIELD_LENGTH) -> str:
    if not isinstance(value, str):
        return ""
    # Strip control characters, limit length
    cleaned = "".join(c for c in value if c.isprintable() or c in "\n\t")
    return cleaned.strip()[:max_len]

def validate_lead(data: dict) -> tuple:
    """Returns (is_valid, cleaned_data_or_error)."""
    name = sanitize(data.get("name", ""))
    email = sanitize(data.get("email", ""))
    company = sanitize(data.get("company", ""))
    interest = sanitize(data.get("interest", ""))

    if not name:
        return False, "Name is required"
    if not email:
        return False, "Email is required"
    if not EMAIL_REGEX.match(email):
        return False, "Invalid email format"
    if interest and interest not in ("free", "pro", "enterprise", "partner"):
        interest = "other"

    return True, {
        "name": name,
        "email": email,
        "company": company,
        "interest": interest,
        "source": sanitize(data.get("source", "landing-page")),
    }


# ═══════════════════════════════════════════════════════════════════
# HTTP HANDLER
# ═══════════════════════════════════════════════════════════════════

class LeadHandler(BaseHTTPRequestHandler):
    ledger = LeadLedger()
    limiter = RateLimiter()
    admin_secret = os.environ.get(ENV_LEADS_SECRET, "")

    # Allowed CORS origins
    cors_origins = set(
        os.environ.get(ENV_CORS_ORIGINS, DEFAULT_CORS).split(",")
    )

    def log_message(self, format, *args):
        logger.info(f"{self.client_address[0]} — {format % args}")

    def _get_origin(self) -> str:
        return self.headers.get("Origin", "")

    def _cors_headers(self) -> dict:
        origin = self._get_origin()
        headers = {
            "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Max-Age": "86400",
        }
        if origin in self.cors_origins or not origin:
            headers["Access-Control-Allow-Origin"] = origin or "*"
        else:
            # Reject unknown origins
            headers["Access-Control-Allow-Origin"] = "null"
        return headers

    def _respond(self, code: int, body: dict, content_type: str = "application/json"):
        self.send_response(code)
        cors = self._cors_headers()
        for k, v in cors.items():
            self.send_header(k, v)
        self.send_header("Content-Type", content_type)
        self.send_header("X-WINDI-Service", "Lead-Capture")
        self.end_headers()
        if content_type == "application/json":
            self.wfile.write(json.dumps(body, ensure_ascii=False, indent=2).encode())
        elif content_type == "text/csv":
            self.wfile.write(body.encode() if isinstance(body, str) else json.dumps(body).encode())

    def _check_admin(self) -> bool:
        if not self.admin_secret:
            return False
        auth = self.headers.get("Authorization", "")
        return auth == f"Bearer {self.admin_secret}"

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(204)
        cors = self._cors_headers()
        for k, v in cors.items():
            self.send_header(k, v)
        self.end_headers()

    def do_POST(self):
        if self.path == "/api/leads":
            self._handle_new_lead()
        else:
            self._respond(404, {"error": "Not found"})

    def do_GET(self):
        if self.path == "/health":
            chain = self.ledger.verify_chain()
            self._respond(200, {
                "service": "WINDI_LEAD_CAPTURE",
                "version": VERSION,
                "status": "RUNNING",
                "port": PORT,
                "leads_count": self.ledger.count(),
                "chain": chain,
                "cors_origins": list(self.cors_origins),
                "rate_limit": f"{RATE_LIMIT_PER_HOUR}/hour",
                "admin_configured": bool(self.admin_secret),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        elif self.path == "/api/leads/count":
            if not self._check_admin():
                self._respond(401, {"error": "Unauthorized. Set Authorization: Bearer $WINDI_LEADS_SECRET"})
                return
            self._respond(200, {
                "count": self.ledger.count(),
                "chain": self.ledger.verify_chain(),
            })

        elif self.path == "/api/leads/export":
            if not self._check_admin():
                self._respond(401, {"error": "Unauthorized"})
                return
            csv_data = self.ledger.export_csv()
            self.send_response(200)
            cors = self._cors_headers()
            for k, v in cors.items():
                self.send_header(k, v)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Disposition", f"attachment; filename=windi-leads-{datetime.now().strftime('%Y%m%d')}.csv")
            self.end_headers()
            self.wfile.write(csv_data.encode("utf-8"))

        else:
            self._respond(404, {"error": "Not found"})

    def _handle_new_lead(self):
        ip = self.client_address[0]

        # Rate limiting
        if not self.limiter.check(ip):
            logger.warning(f"Rate limited: {ip}")
            self._respond(429, {
                "error": "Too many requests. Please try again later.",
                "retry_after": "3600",
            })
            return

        # Read body
        length = int(self.headers.get("Content-Length", 0))
        if length > 10000:  # 10KB max
            self._respond(413, {"error": "Payload too large"})
            return

        try:
            raw = self.rfile.read(length)
            data = json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._respond(400, {"error": "Invalid JSON"})
            return

        # Validate
        valid, result = validate_lead(data)
        if not valid:
            self._respond(422, {"error": result})
            return

        # Add metadata
        result["ip_hash"] = hashlib.sha256(ip.encode()).hexdigest()[:16]  # Privacy: hash IP
        result["user_agent"] = self.headers.get("User-Agent", "unknown")[:200]
        result["referrer"] = self.headers.get("Referer", "direct")[:500]
        result["lang"] = data.get("lang", "de")

        # Store
        entry = self.ledger.append(result)

        logger.info(
            f"✓ New lead: {result['name']} <{result['email']}> "
            f"interest={result['interest']} → {entry['id']}"
        )

        self._respond(201, {
            "status": "received",
            "lead_id": entry["id"],
            "message": "Thank you! We'll be in touch.",
            "timestamp": entry["timestamp"],
        })


# ═══════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════

HELP = """
  Usage: python3 windi_leads.py <command>

  ── Server ─────────────────────────────────────────────
  start             Start API server on port 8096
  health            Show health status

  ── Admin ──────────────────────────────────────────────
  count             Count total leads
  export            Export leads as CSV to stdout
  list              List all leads (JSON)
  verify            Verify hash chain integrity

  ── Environment ────────────────────────────────────────
  WINDI_LEADS_SECRET    Admin API key (for count/export endpoints)
  WINDI_LEADS_CORS      Comma-separated CORS origins
"""

def main():
    print(BANNER)

    if len(sys.argv) < 2:
        print(HELP)
        return

    cmd = sys.argv[1].lower().replace("-", "_")
    ledger = LeadLedger()

    if cmd == "start":
        print(f"  Starting Lead Capture API on port {PORT}...")
        print(f"  CORS origins: {os.environ.get(ENV_CORS_ORIGINS, DEFAULT_CORS)}")
        print(f"  Admin secret: {'SET' if os.environ.get(ENV_LEADS_SECRET) else 'NOT SET (admin endpoints disabled)'}")
        print(f"  Leads stored: {ledger.count()}")
        print(f"  Rate limit: {RATE_LIMIT_PER_HOUR} leads/hour/IP")
        print()

        server = HTTPServer(("0.0.0.0", PORT), LeadHandler)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n  Shutting down...")
            server.shutdown()

    elif cmd == "health":
        chain = ledger.verify_chain()
        health = {
            "service": "WINDI_LEAD_CAPTURE",
            "version": VERSION,
            "leads_count": ledger.count(),
            "chain": chain,
            "storage": str(LEADS_FILE),
        }
        print(json.dumps(health, indent=2))

    elif cmd == "count":
        print(f"  Total leads: {ledger.count()}")

    elif cmd == "export":
        print(ledger.export_csv())

    elif cmd == "list":
        leads = ledger.get_all()
        for lead in leads:
            d = lead.get("data", {})
            print(f"  {lead['id']} | {d.get('name', '?')} | {d.get('email', '?')} | {d.get('interest', '?')} | {lead['timestamp'][:19]}")
        print(f"\n  Total: {len(leads)} leads")

    elif cmd == "verify":
        result = ledger.verify_chain()
        print(json.dumps(result, indent=2))
        if result["status"] == "INTACT":
            print(f"\n  ✓ Chain INTACT — {result['entries']} entries verified")
        elif result["status"] == "EMPTY":
            print("\n  ○ Ledger empty — no leads yet")
        else:
            print(f"\n  ✗ Chain BROKEN at entry {result.get('broken_at')}")

    else:
        print(f"  Unknown command: {cmd}")
        print(HELP)


if __name__ == "__main__":
    main()
