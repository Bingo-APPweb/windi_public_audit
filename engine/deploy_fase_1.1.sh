#!/bin/bash
# ============================================================
# WINDI Phase 1.1 — Deploy /api/governance/health endpoint
# Date: 02 Feb 2026
# Principle: Zero-Violence Deployment
# ============================================================
# 
# What this does:
#   1. Backs up current governance_api_minimal.py
#   2. Deploys updated version with /health endpoint
#   3. Verifies syntax before starting
#   4. Restarts the API on port 8083
#   5. Runs 3 verification tests
#
# Rollback: If anything fails, the backup is at:
#   /opt/windi/backups/fase_1.1_backup/governance_api_minimal.py.bak
# ============================================================

set -e  # Stop on first error

echo "============================================"
echo "  WINDI Phase 1.1 — Deploy Script"
echo "  $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "============================================"
echo ""

# --- Step 0: Pre-flight check ---
echo "[0/5] Pre-flight check..."
if ! ss -tulnp | grep -q ":8083"; then
    echo "  WARNING: Port 8083 not currently active"
    echo "  (This is OK if the API was stopped)"
else
    echo "  OK: Port 8083 is active"
fi
echo ""

# --- Step 1: Backup ---
echo "[1/5] Creating backup..."
BACKUP_DIR="/opt/windi/backups/fase_1.1_backup"
mkdir -p "$BACKUP_DIR"
if [ -f /opt/windi/engine/governance_api_minimal.py ]; then
    cp /opt/windi/engine/governance_api_minimal.py "$BACKUP_DIR/governance_api_minimal.py.bak"
    echo "  Backup saved: $BACKUP_DIR/governance_api_minimal.py.bak"
else
    echo "  WARNING: Original file not found (first deploy?)"
fi
echo ""

# --- Step 2: Deploy new file ---
echo "[2/5] Writing updated governance_api_minimal.py..."
python3 << 'PYEOF'
content = '''\
"""
WINDI Governance API - Evolution Minimal
Phase 1.1: HTTP heartbeat + Engine health bridge.

Port map (01 Feb 2026):
  8080 = windi_governance_api (complete)
  8081 = brain.trust_bus (uvicorn)
  8082 = windi_gateway
  8083 = THIS (evolution minimal)
  8084 = masterarbeit/server
  8085 = BABEL (a4desk_tiptap_babel)
  8086 = app.py
  8889 = windi_cortex

Phase history:
  1.0 = Pure heartbeat, zero engine deps (01 Feb 2026)
  1.1 = /health endpoint bridges engine via GovernanceHealthCheck (02 Feb 2026)
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import sys
import os
from datetime import datetime, timezone

HOST = "0.0.0.0"
PORT = 8083
VERSION = "1.1-health"

# --- Engine bridge (isolated) ---

def get_engine_health():
    """
    Bridge to GovernanceHealthCheck.quick_status().
    Wrapped in try/except so engine failure never kills the API.
    """
    try:
        engine_dir = os.path.dirname(os.path.abspath(__file__))
        if engine_dir not in sys.path:
            sys.path.insert(0, engine_dir)

        from governance_health import GovernanceHealthCheck
        health = GovernanceHealthCheck()
        return health.quick_status()
    except ImportError as e:
        return {
            "engine_status": "import_error",
            "error": f"Cannot import GovernanceHealthCheck: {e}"
        }
    except Exception as e:
        return {
            "engine_status": "error",
            "error": str(e)
        }


# --- HTTP Handler ---

class GovernanceHandler(BaseHTTPRequestHandler):

    def _set_headers(self, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("X-WINDI-Version", VERSION)
        self.end_headers()

    def do_GET(self):
        if self.path == "/api/governance/status":
            response = {
                "status": "UP",
                "service": "WINDI Governance API",
                "version": VERSION,
                "checked_at": datetime.now(timezone.utc).isoformat()
            }
            self._set_headers(200)
            self.wfile.write(json.dumps(response, indent=2).encode())

        elif self.path == "/api/governance/health":
            engine_report = get_engine_health()
            response = {
                "status": "UP",
                "version": VERSION,
                "checked_at": datetime.now(timezone.utc).isoformat(),
                "engine": engine_report
            }
            self._set_headers(200)
            self.wfile.write(json.dumps(response, indent=2).encode())

        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({
                "error": "Not found",
                "available": [
                    "/api/governance/status",
                    "/api/governance/health"
                ]
            }).encode())

    def log_message(self, format, *args):
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        print(f"[{timestamp}] {args[0]}")


def run():
    server = HTTPServer((HOST, PORT), GovernanceHandler)
    print(f"WINDI Governance API ({VERSION}) running on port {PORT}")
    print(f"Endpoints:")
    print(f"  GET /api/governance/status  (pure heartbeat)")
    print(f"  GET /api/governance/health  (engine bridge)")
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    server.serve_forever()


if __name__ == "__main__":
    run()
'''

with open("/opt/windi/engine/governance_api_minimal.py", "w") as f:
    f.write(content)

print(f"  FILE WRITTEN OK ({len(content.strip().splitlines())} lines)")
PYEOF
echo ""

# --- Step 3: Syntax verification ---
echo "[3/5] Verifying syntax..."
python3 -c "import py_compile; py_compile.compile('/opt/windi/engine/governance_api_minimal.py', doraise=True); print('  SYNTAX OK')"
echo ""

# --- Step 4: Restart API ---
echo "[4/5] Restarting API on port 8083..."
pkill -f governance_api_minimal.py 2>/dev/null || echo "  (no previous process to kill)"
sleep 1
cd /opt/windi/engine
nohup python3 governance_api_minimal.py > /tmp/windi_api_minimal.log 2>&1 &
NEW_PID=$!
echo "  New PID: $NEW_PID"
sleep 2

# Check if process survived
if ps -p $NEW_PID > /dev/null 2>&1; then
    echo "  Process alive: YES"
else
    echo "  ERROR: Process died immediately!"
    echo "  Log:"
    cat /tmp/windi_api_minimal.log
    echo ""
    echo "  ROLLBACK: cp $BACKUP_DIR/governance_api_minimal.py.bak /opt/windi/engine/governance_api_minimal.py"
    exit 1
fi
echo ""

# --- Step 5: Verification tests ---
echo "[5/5] Running verification tests..."
echo ""

echo "  TEST 1: Heartbeat (/status) — must show UP, no engine dependency"
echo "  -------"
RESULT1=$(curl -s http://localhost:8083/api/governance/status)
echo "  $RESULT1" | python3 -m json.tool 2>/dev/null || echo "  $RESULT1"
echo ""

echo "  TEST 2: Engine health (/health) — must show UP + engine report"
echo "  -------"
RESULT2=$(curl -s http://localhost:8083/api/governance/health)
echo "  $RESULT2" | python3 -m json.tool 2>/dev/null || echo "  $RESULT2"
echo ""

echo "  TEST 3: 404 handling — must list both endpoints"
echo "  -------"
RESULT3=$(curl -s http://localhost:8083/anything-else)
echo "  $RESULT3" | python3 -m json.tool 2>/dev/null || echo "  $RESULT3"
echo ""

# --- Summary ---
echo "============================================"
echo "  PHASE 1.1 DEPLOYMENT SUMMARY"
echo "============================================"
echo "  Version: 1.1-health"
echo "  Port: 8083"
echo "  PID: $NEW_PID"
echo "  Backup: $BACKUP_DIR/"
echo ""
echo "  Endpoints:"
echo "    /api/governance/status  → pure heartbeat (no engine)"
echo "    /api/governance/health  → engine bridge (GovernanceHealthCheck)"
echo ""
echo "  Success criteria:"
echo "    [check /status output above — must be UP]"
echo "    [check /health output above — must show engine data]"
echo "    [if engine fails, /status must still be UP]"
echo ""
echo "  Next: Phase 1.2 — /api/governance/detect (POST)"
echo "============================================"
