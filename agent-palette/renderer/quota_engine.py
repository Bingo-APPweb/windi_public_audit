#!/usr/bin/env python3
"""WINDI Quota Engine v1.0.0"""

import sqlite3, time, hashlib, json, threading
from pathlib import Path
from datetime import datetime, date
from typing import Dict, Tuple, Optional
from collections import defaultdict

TIERS = {
    "ANON": {"renders_per_day": 3, "max_file_mb": 2, "max_pages": 5, "max_slides": 3,
             "formats": ["pdf", "docx"], "requests_per_min": 10, "renders_per_min": 1},
    "FREE": {"renders_per_day": 10, "max_file_mb": 5, "max_pages": 15, "max_slides": 5,
             "formats": ["pdf", "docx", "xlsx", "pptx"], "requests_per_min": 30, "renders_per_min": 3},
    "PRO":  {"renders_per_day": 200, "max_file_mb": 25, "max_pages": 100, "max_slides": 50,
             "formats": ["pdf", "docx", "xlsx", "pptx"], "requests_per_min": 60, "renders_per_min": 10},
}

class RateLimiter:
    def __init__(self):
        self._requests = defaultdict(list)
        self._renders = defaultdict(list)
        self._lock = threading.Lock()

    def _clean(self, ts, secs=60):
        cutoff = time.time() - secs
        return [t for t in ts if t > cutoff]

    def check_rate(self, ident, tier, is_render=False):
        cfg = TIERS.get(tier, TIERS["ANON"])
        with self._lock:
            now = time.time()
            self._requests[ident] = self._clean(self._requests[ident])
            self._renders[ident] = self._clean(self._renders[ident])
            if len(self._requests[ident]) >= cfg["requests_per_min"]:
                return False, "rate_limit_requests", 30
            if is_render and len(self._renders[ident]) >= cfg["renders_per_min"]:
                return False, "rate_limit_renders", 30
            self._requests[ident].append(now)
            if is_render:
                self._renders[ident].append(now)
            return True, None, 0

_rate_limiter = RateLimiter()

class QuotaEngine:
    def __init__(self, db_path="/opt/windi/data/quota.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS quota_usage (
                id INTEGER PRIMARY KEY, identifier TEXT NOT NULL, tier TEXT DEFAULT 'ANON',
                date TEXT NOT NULL, renders_today INTEGER DEFAULT 0, bytes_today INTEGER DEFAULT 0,
                last_render_at TEXT, UNIQUE(identifier, date))""")
            conn.commit()

    def _get_id(self, ip, acct=None):
        if acct and acct != "anonymous":
            return f"acct:{acct}"
        return f"anon:{hashlib.sha256(ip.encode()).hexdigest()[:16]}"

    def check_quota(self, ip, acct, tier, fmt, size=0):
        cfg = TIERS.get(tier, TIERS["ANON"])
        ident = self._get_id(ip, acct)
        today = date.today().isoformat()
        if fmt.lower() not in cfg["formats"]:
            return {"allowed": False, "reason": "format_not_allowed",
                    "message": f"Format '{fmt}' not available on {tier}", "allowed_formats": cfg["formats"]}
        rate_ok, rate_reason, retry = _rate_limiter.check_rate(ident, tier, True)
        if not rate_ok:
            return {"allowed": False, "reason": rate_reason, "retry_after": retry}
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT renders_today FROM quota_usage WHERE identifier=? AND date=?",
                              (ident, today)).fetchone()
            used = row[0] if row else 0
            limit = cfg["renders_per_day"]
            if used >= limit:
                return {"allowed": False, "reason": "quota_exhausted", "used": used, "limit": limit,
                        "message": f"Daily limit reached ({used}/{limit})", "reset_at": f"{today}T24:00:00Z"}
            return {"allowed": True, "remaining": limit - used - 1, "used": used, "limit": limit}

    def record_render(self, ip, acct, tier, size=0):
        ident = self._get_id(ip, acct)
        today = date.today().isoformat()
        now = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""INSERT INTO quota_usage (identifier,tier,date,renders_today,bytes_today,last_render_at)
                VALUES (?,?,?,1,?,?) ON CONFLICT(identifier,date) DO UPDATE SET
                renders_today=renders_today+1, bytes_today=bytes_today+?, last_render_at=?""",
                (ident, tier, today, size, now, size, now))
            conn.commit()
        return {"recorded": True}

    def get_status(self, ip, acct, tier):
        cfg = TIERS.get(tier, TIERS["ANON"])
        ident = self._get_id(ip, acct)
        today = date.today().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT renders_today,bytes_today FROM quota_usage WHERE identifier=? AND date=?",
                              (ident, today)).fetchone()
        used = row[0] if row else 0
        return {"tier": tier, "renders_today": used, "limit": cfg["renders_per_day"],
                "remaining": cfg["renders_per_day"] - used, "formats": cfg["formats"]}

_engine = None
def get_quota_engine():
    global _engine
    if not _engine:
        _engine = QuotaEngine()
    return _engine

def route_quota_api(handler, method, path):
    if not path.startswith("/api/quota/") and not path.startswith("/api/dragon/quota/"):
        return False
    path = path.replace("/api/dragon", "/api")
    engine = get_quota_engine()

    def send(data, status=200):
        body = json.dumps(data).encode()
        handler.send_response(status)
        handler.send_header("Content-Type", "application/json")
        handler.send_header("Content-Length", str(len(body)))
        handler.end_headers()
        handler.wfile.write(body)

    def get_ip():
        fwd = handler.headers.get("X-Forwarded-For", "")
        return fwd.split(",")[0].strip() if fwd else handler.client_address[0]

    if method == "GET" and path == "/api/quota/status":
        tier = handler.headers.get("X-WINDI-Tier", "ANON").upper()
        send(engine.get_status(get_ip(), None, tier))
        return True

    if method == "POST" and path == "/api/quota/check":
        clen = int(handler.headers.get("Content-Length", 0))
        body = json.loads(handler.rfile.read(clen)) if clen else {}
        tier = body.get("tier", "ANON").upper()
        fmt = body.get("format", "docx")
        result = engine.check_quota(get_ip(), body.get("account_id"), tier, fmt)
        send(result, 200 if result["allowed"] else 429)
        return True

    return False
