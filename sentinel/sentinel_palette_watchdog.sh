#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
# SENTINEL WATCHDOG — Agent Palette v0.7.1-D Protection
# ═══════════════════════════════════════════════════════════════════════
# Deploy: cp sentinel_palette_watchdog.sh /opt/windi/sentinel/
# Run:    bash /opt/windi/sentinel/sentinel_palette_watchdog.sh
# Cron:   */5 * * * * /opt/windi/sentinel/sentinel_palette_watchdog.sh >> /opt/windi/logs/sentinel_palette.log 2>&1
# ═══════════════════════════════════════════════════════════════════════

set -euo pipefail

EXPECTED_VERSION="0.7.1-D"
EXPECTED_HASH="85c0a18ef227d723c399b505538fe7068ed6b0f3d78203e98f673e2840ed73db"
UI_FILE="/opt/windi/agent-palette/ui/index.html"
BACKUP_DIR="/opt/windi/backups/palette"
LOG="/opt/windi/logs/sentinel_palette.log"
ALERT_FILE="/opt/windi/sentinel/palette_alert.flag"

TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)

mkdir -p "$BACKUP_DIR" "$(dirname $LOG)" "$(dirname $ALERT_FILE)"

# ── 1. File exists ──
if [ ! -f "$UI_FILE" ]; then
    echo "[$TS] ❌ CRITICAL: UI file missing: $UI_FILE"
    touch "$ALERT_FILE"
    exit 1
fi

# ── 2. Version check ──
CURRENT_VERSION=$(grep -o 'const V = "[^"]*"' "$UI_FILE" | grep -o '"[^"]*"' | tr -d '"')
if [ "$CURRENT_VERSION" != "$EXPECTED_VERSION" ]; then
    echo "[$TS] ⚠️  VERSION DRIFT: expected=$EXPECTED_VERSION got=$CURRENT_VERSION"
    touch "$ALERT_FILE"
fi

# ── 3. Hash integrity ──
CURRENT_HASH=$(sha256sum "$UI_FILE" | cut -d' ' -f1)
if [ "$CURRENT_HASH" != "$EXPECTED_HASH" ]; then
    echo "[$TS] ⚠️  HASH DRIFT: file modified since seal"
    echo "  Expected: $EXPECTED_HASH"
    echo "  Current:  $CURRENT_HASH"
    # Don't alert on hash drift alone — updates are expected
    # But log it for forensic trail
fi

# ── 4. Critical functions present ──
CRITICAL_FUNCTIONS=("extractInvoiceFields" "renderDocTemplate" "parseIntent" "validateInvariants" "runSGE" "genReceipt" "applyLayer7" "resolveFormat")
MISSING=0
for fn in "${CRITICAL_FUNCTIONS[@]}"; do
    if ! grep -q "$fn" "$UI_FILE"; then
        echo "[$TS] ❌ MISSING FUNCTION: $fn"
        MISSING=$((MISSING + 1))
    fi
done

if [ $MISSING -gt 0 ]; then
    echo "[$TS] ❌ CRITICAL: $MISSING core functions missing — restoring backup"
    # Auto-restore from latest backup
    LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/index.html.*.bak 2>/dev/null | head -1)
    if [ -n "$LATEST_BACKUP" ]; then
        cp "$LATEST_BACKUP" "$UI_FILE"
        echo "[$TS] 🔄 RESTORED from: $LATEST_BACKUP"
    fi
    touch "$ALERT_FILE"
    exit 1
fi

# ── 5. Brand safety ──
BRAND_LEAKS=$(grep -c "Claude\|GPT\|Gemini\|OpenAI\|Anthropic" "$UI_FILE" 2>/dev/null || true)
if [ "$BRAND_LEAKS" != "0" ]; then
    echo "[$TS] ❌ BRAND LEAK: $BRAND_LEAKS references found"
    touch "$ALERT_FILE"
fi

# ── 6. Service alive ──
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:8108/ 2>/dev/null || echo "000")
if [ "$HTTP_CODE" != "200" ]; then
    echo "[$TS] ❌ SERVICE DOWN: HTTP $HTTP_CODE on port 8108"
    # Auto-restart
    PID=$(ss -tlnp | grep 8108 | grep -oP 'pid=\K\d+' || echo "")
    if [ -n "$PID" ]; then
        kill "$PID" 2>/dev/null
        sleep 2
    fi
    cd /opt/windi/agent-palette
    nohup python3 agent_palette_server.py > /dev/null 2>&1 &
    sleep 2
    NEW_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:8108/ 2>/dev/null || echo "000")
    echo "[$TS] 🔄 RESTARTED: now HTTP $NEW_CODE"
    touch "$ALERT_FILE"
fi

# ── 7. Render API test ──
RENDER_RESP=$(curl -s --max-time 10 -X POST http://localhost:8108/api/dragon/render \
    -H "Content-Type: application/json" \
    -d '{"text":"sentinel-probe","userInput":"Rechnung für Sentinel GmbH, 1x Probe zu €100","intent":{"doc_type":"invoice","language":"de","entities":{"org":["Sentinel GmbH"],"money":["€100"]}},"tier":"FREE","sge":null,"receipt":null}' 2>/dev/null)
RENDER_OK=$(echo "$RENDER_RESP" | python3 -c "import sys,json;print(json.load(sys.stdin).get('success',False))" 2>/dev/null || echo "False")
if [ "$RENDER_OK" != "True" ]; then
    echo "[$TS] ❌ RENDER API FAILED"
    touch "$ALERT_FILE"
fi

# ── 8. Create sealed backup (daily) ──
TODAY=$(date +%Y%m%d)
DAILY_BACKUP="$BACKUP_DIR/index.html.${TODAY}.sealed"
if [ ! -f "$DAILY_BACKUP" ]; then
    cp "$UI_FILE" "$DAILY_BACKUP"
    chmod 444 "$DAILY_BACKUP"  # Read-only seal
    echo "[$TS] 🔒 Daily sealed backup: $DAILY_BACKUP"
fi

# ── RESULT ──
if [ ! -f "$ALERT_FILE" ] || [ "$(find "$ALERT_FILE" -mmin +60 2>/dev/null)" ]; then
    # No recent alerts
    rm -f "$ALERT_FILE"
    echo "[$TS] ✅ SENTINEL GREEN — v$CURRENT_VERSION — all checks passed"
else
    echo "[$TS] 🟡 SENTINEL ALERT — check logs above"
fi
