#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# 🐉 WINDI Orchestrator — Hardened Deploy Script v1.1.0
# ═══════════════════════════════════════════════════════════════
# Safe deployment with:
#   - PID file management (clean start/stop)
#   - Readiness loop (no fragile sleep)
#   - Port conflict handling (graceful, not random kill)
#   - Log rotation ready
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

PORT=8109
APPDIR=/opt/windi/orchestrator
LOGDIR=/opt/windi/logs
PIDFILE=$APPDIR/orchestrator.pid

echo "═══════════════════════════════════════════════════════════"
echo "🐉 WINDI Orchestrator v1.1.0 — Hardened Deployment"
echo "═══════════════════════════════════════════════════════════"

# ── Step 1: Ensure directories ──
echo ""
echo ">>> Step 1: Ensuring directories..."
mkdir -p "$APPDIR" "$LOGDIR"
echo "✅ Directories ready"

# ── Step 2: Check port availability ──
echo ""
echo ">>> Step 2: Checking port ${PORT}..."
if ss -ltnp 2>/dev/null | grep -q ":${PORT} "; then
    echo "⚠️  Port ${PORT} in use. Attempting graceful stop via PID file..."
    if [ -f "$PIDFILE" ]; then
        OLD_PID=$(cat "$PIDFILE")
        if kill -0 "$OLD_PID" 2>/dev/null; then
            echo "   Sending SIGTERM to PID $OLD_PID..."
            kill "$OLD_PID" 2>/dev/null || true
            # Wait up to 5 seconds for graceful shutdown
            for i in {1..10}; do
                if ! kill -0 "$OLD_PID" 2>/dev/null; then
                    break
                fi
                sleep 0.5
            done
        fi
        rm -f "$PIDFILE"
    fi

    # Check if port is still in use
    sleep 1
    if ss -ltnp 2>/dev/null | grep -q ":${PORT} "; then
        echo "❌ Port ${PORT} still in use after graceful stop attempt."
        echo "   Owner process:"
        ss -ltnp 2>/dev/null | grep ":${PORT} " || true
        echo ""
        echo "   Manual resolution required. Run: fuser -k ${PORT}/tcp"
        exit 1
    fi
fi
echo "✅ Port ${PORT} available"

# ── Step 3: Start orchestrator ──
echo ""
echo ">>> Step 3: Starting orchestrator..."
cd "$APPDIR"
nohup python3 "$APPDIR/windi_orchestrator.py" >> "$LOGDIR/orchestrator.log" 2>&1 &
NEW_PID=$!
echo "$NEW_PID" > "$PIDFILE"
echo "   PID: $NEW_PID"

# ── Step 4: Readiness loop (max 30 attempts, 0.3s each = 9s timeout) ──
echo ""
echo ">>> Step 4: Waiting for readiness..."
READY=false
for i in {1..30}; do
    if curl -fsS "http://localhost:${PORT}/health" >/dev/null 2>&1; then
        READY=true
        break
    fi
    sleep 0.3
done

if [ "$READY" != "true" ]; then
    echo "❌ Orchestrator failed to start within 9 seconds."
    echo "   Check logs: tail -50 $LOGDIR/orchestrator.log"
    exit 1
fi

# ── Step 5: Health check ──
echo ""
echo ">>> Step 5: Health check..."
HEALTH=$(curl -fsS "http://localhost:${PORT}/health")
echo "$HEALTH" | python3 -m json.tool

# Verify API key
API_OK=$(echo "$HEALTH" | python3 -c "import sys,json; print(json.load(sys.stdin).get('dragon',{}).get('api_key_configured',False))" 2>/dev/null || echo "False")
if [ "$API_OK" != "True" ]; then
    echo ""
    echo "⚠️  WARNING: Dragon API key NOT configured — LLM calls will fail"
    echo "   Set ANTHROPIC_API_KEY in /opt/windi/.env"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "🐉 Orchestrator LIVE on :${PORT}"
echo "   PID: $(cat "$PIDFILE")"
echo "   Log: $LOGDIR/orchestrator.log"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Endpoints:"
echo "  GET  http://localhost:${PORT}/health     — Health check"
echo "  POST http://localhost:${PORT}/generate   — Dragon-only (no save)"
echo "  POST http://localhost:${PORT}/orchestrate — Full pipeline"
echo ""
echo "To stop:"
echo "  kill \$(cat $PIDFILE)"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "🐉 ULTIMATE TEST (I9-compliant)"
echo "═══════════════════════════════════════════════════════════"
echo ""
cat << 'TESTCMD'
curl -s -X POST http://localhost:8109/orchestrate \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "bafin-demo",
    "prompt": "Generate a Governance Decision documenting the WINDI Sovereignty Test from 26 February 2026.",
    "facts_verified": {
      "test_date": "26 February 2026",
      "test_result": "Complete governance cycle executed with zero new code",
      "receipts": ["GC-PALETTE-EN-20260226141511", "WB-PALETTE-GENESIS-20260226141505"],
      "regulations": ["EU AI Act Article 14", "BaFin MaRisk AT 7.2"]
    },
    "author_name": "WINDI Governance Institute",
    "author_role": "Architect Dragon",
    "actor": "JMPG-CGO",
    "auto_publish": true,
    "human_ack": "I_APPROVE_PUBLISH"
  }' | python3 -m json.tool
TESTCMD
echo ""
