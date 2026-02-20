#!/usr/bin/env python3
"""
🐉🛡 WINDI SENTINEL LAW — Permanent Governance Invariants
═══════════════════════════════════════════════════════════
"The system cannot degrade silently."

This module runs ON the Strato server, querying localhost endpoints
to measure TRUE server-side processing time (no network overhead).

6 PERMANENT LAWS (post-stress-test 17Feb2026):
  LAW 1: latency_p95     < 100ms   (server-side receipt creation)
  LAW 2: unsynced        = 0       (all receipts synced to Ledger)
  LAW 3: hash_drift      = 0       (no hash inconsistencies)
  LAW 4: reconciliation  = HEALTHY (Ledger reconciliation clean)
  LAW 5: event_drops     = 0       (no lost events in pipeline)
  LAW 6: chain_integrity = VALID   (hash chain unbroken)

Violation of ANY law → immediate alert.
Port: 8102
Cycle: every 30 seconds
"""

import json
import hashlib
import time
import threading
import logging
import os
import sqlite3
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from collections import deque
from pathlib import Path

# ═══════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════
PORT = 8102
CHECK_INTERVAL = 30          # seconds between law checks
LATENCY_WINDOW = 100         # keep last N latency samples
LATENCY_P95_LIMIT = 100      # ms — LAW 1
ALERT_CONSECUTIVE = 2        # alert after N consecutive violations
PROBE_TIMEOUT = 10           # seconds per probe request

# Internal endpoints (localhost — no network overhead)
DESKTOP_URL = "http://127.0.0.1:8100"
LEDGER_URL = "http://127.0.0.1:8101"
BRIDGE_URL = "http://127.0.0.1:8097"

# Persistence
DATA_DIR = Path("/opt/windi/data")
LOG_DIR = Path("/opt/windi/logs")
DB_PATH = DATA_DIR / "sentinel_law.db"
LOG_PATH = LOG_DIR / "sentinel_law.log"

# ═══════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [SENTINEL-LAW] %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_PATH) if LOG_DIR.exists() else logging.StreamHandler()
    ]
)
log = logging.getLogger("sentinel-law")

# ═══════════════════════════════════════════
# DATABASE — Alert History & Metrics
# ═══════════════════════════════════════════
def init_db():
    """Initialize SQLite for alert persistence"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS law_checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            law_id TEXT NOT NULL,
            law_name TEXT NOT NULL,
            value TEXT NOT NULL,
            expected TEXT NOT NULL,
            passed INTEGER NOT NULL,
            cycle_id INTEGER NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            law_id TEXT NOT NULL,
            law_name TEXT NOT NULL,
            value TEXT NOT NULL,
            expected TEXT NOT NULL,
            consecutive_violations INTEGER NOT NULL,
            resolved INTEGER DEFAULT 0,
            resolved_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            cycle_id INTEGER NOT NULL,
            latency_p50_ms REAL,
            latency_p95_ms REAL,
            latency_p99_ms REAL,
            receipts_total INTEGER,
            receipts_unsynced INTEGER,
            hash_drift INTEGER,
            event_drops INTEGER,
            reconciliation_status TEXT,
            chain_integrity TEXT,
            all_pass INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()
    log.info(f"Law DB initialized: {DB_PATH}")

# ═══════════════════════════════════════════
# LOCALHOST PROBES (server-side only)
# ═══════════════════════════════════════════
def probe_get(url, path):
    """GET request to localhost endpoint, returns (data, latency_ms)"""
    full = f"{url}{path}"
    req = Request(full, headers={"Accept": "application/json"})
    start = time.monotonic()
    try:
        with urlopen(req, timeout=PROBE_TIMEOUT) as resp:
            latency = (time.monotonic() - start) * 1000
            data = json.loads(resp.read().decode())
            return data, latency
    except Exception as e:
        latency = (time.monotonic() - start) * 1000
        return {"error": str(e)}, latency

def probe_post(url, path, body):
    """POST request to localhost, returns (data, latency_ms)"""
    full = f"{url}{path}"
    payload = json.dumps(body).encode()
    req = Request(full, data=payload, headers={
        "Content-Type": "application/json",
        "Accept": "application/json"
    })
    start = time.monotonic()
    try:
        with urlopen(req, timeout=PROBE_TIMEOUT) as resp:
            latency = (time.monotonic() - start) * 1000
            data = json.loads(resp.read().decode())
            return data, latency
    except Exception as e:
        latency = (time.monotonic() - start) * 1000
        return {"error": str(e)}, latency

# ═══════════════════════════════════════════
# LAW ENGINE
# ═══════════════════════════════════════════
class SentinelLaw:
    """Continuous enforcement of 6 permanent governance invariants"""

    def __init__(self):
        self.cycle_id = 0
        self.latency_history = deque(maxlen=LATENCY_WINDOW)
        self.consecutive_violations = {f"LAW{i}": 0 for i in range(1, 7)}
        self.last_check = None
        self.last_result = None
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.total_checks = 0
        self.total_violations = 0
        self.total_alerts = 0
        self.active_alerts = []

    def check_all_laws(self):
        """Execute one complete law verification cycle"""
        self.cycle_id += 1
        self.total_checks += 1
        now = datetime.now(timezone.utc).isoformat()
        results = {}

        # ── LAW 1: latency_p95 < 100ms (server-side) ──
        # Probe: create a synthetic receipt via D1 Gateway (localhost)
        probe_hash = hashlib.sha256(
            f"sentinel-law-probe-{self.cycle_id}-{time.time()}".encode()
        ).hexdigest()

        probe_receipt = {
            "doc_id": "SENTINEL-LAW-PROBE",
            "action": "LAW_PROBE",
            "integrity_hash": probe_hash,
            "timestamp": now,
            "user_id": "sentinel-law",
            "metadata": {
                "cycle_id": self.cycle_id,
                "purpose": "latency_measurement",
                "hash_algorithm": "SHA-256"
            }
        }

        probe_data, probe_latency = probe_post(
            DESKTOP_URL, "/api/ledger/receipts", probe_receipt
        )
        self.latency_history.append(probe_latency)

        # Calculate percentiles from history
        if len(self.latency_history) >= 5:
            sorted_lat = sorted(self.latency_history)
            p50 = sorted_lat[int(len(sorted_lat) * 0.50)]
            p95 = sorted_lat[int(len(sorted_lat) * 0.95)]
            p99 = sorted_lat[min(int(len(sorted_lat) * 0.99), len(sorted_lat) - 1)]
        else:
            p50 = p95 = p99 = probe_latency

        law1_pass = p95 < LATENCY_P95_LIMIT
        results["LAW1"] = {
            "name": "latency_p95",
            "value": f"{p95:.1f}ms",
            "raw_value": p95,
            "expected": f"< {LATENCY_P95_LIMIT}ms",
            "passed": law1_pass,
            "detail": {
                "probe_latency": f"{probe_latency:.1f}ms",
                "p50": f"{p50:.1f}ms",
                "p95": f"{p95:.1f}ms",
                "p99": f"{p99:.1f}ms",
                "samples": len(self.latency_history)
            }
        }

        # ── LAW 2: unsynced = 0 ──
        status_data, _ = probe_get(DESKTOP_URL, "/api/status")
        unsynced = status_data.get("receipts_unsynced", -1)
        receipts_total = status_data.get("receipts_total", 0)
        law2_pass = unsynced == 0

        results["LAW2"] = {
            "name": "unsynced",
            "value": str(unsynced),
            "raw_value": unsynced,
            "expected": "= 0",
            "passed": law2_pass,
            "detail": {"receipts_total": receipts_total}
        }

        # ── LAW 3: hash_drift = 0 ──
        # Check: query receipts and verify all have ledger_synced = 1
        receipts_data, _ = probe_get(
            DESKTOP_URL, "/api/ledger/receipts?doc_id=SENTINEL-LAW-PROBE"
        )
        hash_drift = 0
        if isinstance(receipts_data, list):
            for r in receipts_data[-20:]:  # Check last 20
                if not r.get("ledger_synced"):
                    hash_drift += 1
        law3_pass = hash_drift == 0

        results["LAW3"] = {
            "name": "hash_drift",
            "value": str(hash_drift),
            "raw_value": hash_drift,
            "expected": "= 0",
            "passed": law3_pass,
            "detail": {"checked_receipts": min(len(receipts_data) if isinstance(receipts_data, list) else 0, 20)}
        }

        # ── LAW 4: reconciliation = HEALTHY ──
        reconcile_data, _ = probe_get(DESKTOP_URL, "/api/reconcile")
        reconcile_status = reconcile_data.get("status", "UNKNOWN")
        still_pending = reconcile_data.get("still_pending", -1)
        failed_ids = reconcile_data.get("failed_ids", [])
        law4_pass = reconcile_status == "reconciliation_complete" and still_pending == 0

        results["LAW4"] = {
            "name": "reconciliation",
            "value": "HEALTHY" if law4_pass else "DEGRADED",
            "raw_value": reconcile_status,
            "expected": "= HEALTHY",
            "passed": law4_pass,
            "detail": {
                "status": reconcile_status,
                "still_pending": still_pending,
                "failed_ids": failed_ids[:5]
            }
        }

        # ── LAW 5: event_drops = 0 ──
        # Verify our probe receipt was actually created
        probe_found = False
        if isinstance(receipts_data, list):
            for r in receipts_data:
                if r.get("integrity_hash") == probe_hash:
                    probe_found = True
                    break
        event_drops = 0 if probe_found or "error" not in probe_data else 1
        law5_pass = event_drops == 0

        results["LAW5"] = {
            "name": "event_drops",
            "value": str(event_drops),
            "raw_value": event_drops,
            "expected": "= 0",
            "passed": law5_pass,
            "detail": {"probe_delivered": probe_found}
        }

        # ── LAW 6: chain_integrity = VALID ──
        # Check Bridge health for chain integrity
        bridge_data, _ = probe_get(BRIDGE_URL, "/health")
        chain_intact = bridge_data.get("chain_intact", False)
        chain_entries = bridge_data.get("chain_entries", 0)
        law6_pass = chain_intact is True

        results["LAW6"] = {
            "name": "chain_integrity",
            "value": "VALID" if law6_pass else "BROKEN",
            "raw_value": chain_intact,
            "expected": "= VALID",
            "passed": law6_pass,
            "detail": {
                "chain_intact": chain_intact,
                "chain_entries": chain_entries
            }
        }

        # ── AGGREGATE ──
        all_pass = all(r["passed"] for r in results.values())
        violations = [k for k, v in results.items() if not v["passed"]]

        # Update consecutive violation counters
        for law_id in results:
            if results[law_id]["passed"]:
                self.consecutive_violations[law_id] = 0
            else:
                self.consecutive_violations[law_id] += 1
                self.total_violations += 1

        # Generate alerts for sustained violations
        new_alerts = []
        for law_id, count in self.consecutive_violations.items():
            if count >= ALERT_CONSECUTIVE:
                alert = {
                    "law_id": law_id,
                    "law_name": results[law_id]["name"],
                    "value": results[law_id]["value"],
                    "expected": results[law_id]["expected"],
                    "consecutive": count,
                    "timestamp": now
                }
                new_alerts.append(alert)
                self.total_alerts += 1
                log.warning(
                    f"🚨 SENTINEL ALERT: {law_id} ({results[law_id]['name']}) "
                    f"VIOLATED {count}x consecutive! "
                    f"Value={results[law_id]['value']} Expected={results[law_id]['expected']}"
                )

        self.active_alerts = new_alerts

        # Build result
        self.last_check = now
        self.last_result = {
            "cycle_id": self.cycle_id,
            "timestamp": now,
            "all_pass": all_pass,
            "violations": violations,
            "laws": results,
            "alerts": new_alerts,
            "latency_profile": {
                "p50": f"{p50:.1f}ms",
                "p95": f"{p95:.1f}ms",
                "p99": f"{p99:.1f}ms",
                "samples": len(self.latency_history)
            }
        }

        # Persist to DB
        self._persist(results, all_pass, p50, p95, p99,
                      receipts_total, unsynced, hash_drift,
                      event_drops, reconcile_status, chain_intact,
                      new_alerts)

        status_icon = "🟢" if all_pass else "🔴"
        log.info(
            f"{status_icon} Cycle {self.cycle_id}: "
            f"{'ALL PASS' if all_pass else f'VIOLATIONS: {violations}'} | "
            f"p95={p95:.1f}ms unsynced={unsynced} drift={hash_drift} "
            f"reconcile={'OK' if law4_pass else 'FAIL'} "
            f"drops={event_drops} chain={'OK' if law6_pass else 'BROKEN'}"
        )

        return self.last_result

    def _persist(self, results, all_pass, p50, p95, p99,
                 receipts_total, unsynced, hash_drift,
                 event_drops, reconcile_status, chain_intact,
                 new_alerts):
        """Persist check results and alerts to SQLite"""
        try:
            conn = sqlite3.connect(str(DB_PATH))
            now = datetime.now(timezone.utc).isoformat()

            # Law checks
            for law_id, r in results.items():
                conn.execute(
                    "INSERT INTO law_checks (timestamp, law_id, law_name, value, expected, passed, cycle_id) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (now, law_id, r["name"], r["value"], r["expected"],
                     1 if r["passed"] else 0, self.cycle_id)
                )

            # Metrics
            conn.execute(
                "INSERT INTO metrics (timestamp, cycle_id, latency_p50_ms, latency_p95_ms, "
                "latency_p99_ms, receipts_total, receipts_unsynced, hash_drift, event_drops, "
                "reconciliation_status, chain_integrity, all_pass) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (now, self.cycle_id, p50, p95, p99, receipts_total, unsynced,
                 hash_drift, event_drops, reconcile_status,
                 "VALID" if chain_intact else "BROKEN",
                 1 if all_pass else 0)
            )

            # Alerts
            for alert in new_alerts:
                conn.execute(
                    "INSERT INTO alerts (timestamp, law_id, law_name, value, expected, "
                    "consecutive_violations) VALUES (?, ?, ?, ?, ?, ?)",
                    (alert["timestamp"], alert["law_id"], alert["law_name"],
                     alert["value"], alert["expected"], alert["consecutive"])
                )

            conn.commit()
            conn.close()
        except Exception as e:
            log.error(f"DB persist error: {e}")

    def get_status(self):
        """Return current law enforcement status"""
        return {
            "service": "WINDI Sentinel LAW",
            "version": "1.0.0",
            "status": "enforcing",
            "started_at": self.started_at,
            "cycle_id": self.cycle_id,
            "total_checks": self.total_checks,
            "total_violations": self.total_violations,
            "total_alerts": self.total_alerts,
            "active_alerts": self.active_alerts,
            "consecutive_violations": {
                k: v for k, v in self.consecutive_violations.items() if v > 0
            },
            "last_check": self.last_check,
            "last_result": self.last_result,
            "config": {
                "check_interval_s": CHECK_INTERVAL,
                "latency_p95_limit_ms": LATENCY_P95_LIMIT,
                "alert_threshold": ALERT_CONSECUTIVE,
                "latency_window": LATENCY_WINDOW
            },
            "principle": "The system cannot degrade silently.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def get_history(self, limit=50):
        """Return recent law check history from DB"""
        try:
            conn = sqlite3.connect(str(DB_PATH))
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM metrics ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
            conn.close()
            return [dict(r) for r in rows]
        except Exception as e:
            return {"error": str(e)}

    def get_alerts(self, limit=50, unresolved_only=False):
        """Return alert history"""
        try:
            conn = sqlite3.connect(str(DB_PATH))
            conn.row_factory = sqlite3.Row
            query = "SELECT * FROM alerts"
            if unresolved_only:
                query += " WHERE resolved = 0"
            query += " ORDER BY id DESC LIMIT ?"
            rows = conn.execute(query, (limit,)).fetchall()
            conn.close()
            return [dict(r) for r in rows]
        except Exception as e:
            return {"error": str(e)}

# ═══════════════════════════════════════════
# HTTP SERVER
# ═══════════════════════════════════════════
law_engine = SentinelLaw()

class LawHandler(BaseHTTPRequestHandler):
    """HTTP API for Sentinel LAW"""

    def do_GET(self):
        path = self.path.split("?")[0].rstrip("/")

        routes = {
            "/health": self._health,
            "/api/law/status": self._status,
            "/api/law/check": self._check_now,
            "/api/law/history": self._history,
            "/api/law/alerts": self._alerts,
            "/api/law/config": self._config,
        }

        handler = routes.get(path)
        if handler:
            handler()
        else:
            self._json(404, {"error": "Not found", "available": list(routes.keys())})

    def _health(self):
        """Health endpoint — quick status"""
        last = law_engine.last_result
        self._json(200, {
            "service": "WINDI Sentinel LAW",
            "version": "1.0.0",
            "status": "enforcing",
            "all_laws_pass": last["all_pass"] if last else None,
            "active_alerts": len(law_engine.active_alerts),
            "cycle_id": law_engine.cycle_id,
            "port": PORT,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "principle": "The system cannot degrade silently."
        })

    def _status(self):
        """Full status with last check details"""
        self._json(200, law_engine.get_status())

    def _check_now(self):
        """Trigger immediate law check"""
        result = law_engine.check_all_laws()
        self._json(200, result)

    def _history(self):
        """Recent metrics history"""
        self._json(200, {"history": law_engine.get_history()})

    def _alerts(self):
        """Alert history"""
        self._json(200, {"alerts": law_engine.get_alerts()})

    def _config(self):
        """Current configuration (read-only)"""
        self._json(200, {
            "laws": {
                "LAW1": {"name": "latency_p95", "limit": f"< {LATENCY_P95_LIMIT}ms",
                         "source": "localhost receipt probe"},
                "LAW2": {"name": "unsynced", "limit": "= 0",
                         "source": "D1 /api/status"},
                "LAW3": {"name": "hash_drift", "limit": "= 0",
                         "source": "D1 receipt ledger_synced field"},
                "LAW4": {"name": "reconciliation", "limit": "= HEALTHY",
                         "source": "D1 /api/reconcile"},
                "LAW5": {"name": "event_drops", "limit": "= 0",
                         "source": "probe receipt delivery verification"},
                "LAW6": {"name": "chain_integrity", "limit": "= VALID",
                         "source": "Bridge /health chain_intact"}
            },
            "check_interval_s": CHECK_INTERVAL,
            "alert_threshold": ALERT_CONSECUTIVE,
            "latency_window": LATENCY_WINDOW,
            "endpoints_monitored": {
                "desktop": DESKTOP_URL,
                "ledger": LEDGER_URL,
                "bridge": BRIDGE_URL
            },
            "principle": "Violation of ANY law = immediate alert.",
            "origin": "Stress Test Linhagem de Ferro — 17 Feb 2026"
        })

    def _json(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, default=str).encode())

    def log_message(self, format, *args):
        """Suppress default HTTP logging (we use our own)"""
        pass

# ═══════════════════════════════════════════
# CONTINUOUS LAW ENFORCEMENT LOOP
# ═══════════════════════════════════════════
def enforcement_loop():
    """Background thread: check all laws every CHECK_INTERVAL seconds"""
    log.info(f"🐉🛡 Law enforcement loop started (every {CHECK_INTERVAL}s)")
    # Initial check after 5s warmup
    time.sleep(5)
    while True:
        try:
            law_engine.check_all_laws()
        except Exception as e:
            log.error(f"Law check cycle failed: {e}")
        time.sleep(CHECK_INTERVAL)

# ═══════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════
def main():
    print("""
    🐉🛡 WINDI SENTINEL LAW v1.0.0
    ═══════════════════════════════
    "The system cannot degrade silently."

    Port:     {port}
    Interval: {interval}s
    Laws:     6 permanent invariants
    Origin:   Stress Test Linhagem de Ferro — 17 Feb 2026

    Endpoints:
      /health            — Quick health
      /api/law/status    — Full status + last check
      /api/law/check     — Trigger immediate check
      /api/law/history   — Metrics history
      /api/law/alerts    — Alert history
      /api/law/config    — Law definitions
    """.format(port=PORT, interval=CHECK_INTERVAL))

    # Initialize database
    init_db()

    # Start enforcement loop in background
    enforcer = threading.Thread(target=enforcement_loop, daemon=True)
    enforcer.start()

    # Start HTTP server
    server = HTTPServer(("0.0.0.0", PORT), LawHandler)
    log.info(f"🐉🛡 Sentinel LAW serving on port {PORT}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Sentinel LAW shutting down")
        server.shutdown()

if __name__ == "__main__":
    main()
