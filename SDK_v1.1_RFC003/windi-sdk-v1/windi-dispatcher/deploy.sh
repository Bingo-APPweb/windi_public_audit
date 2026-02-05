#!/bin/bash
# ═══════════════════════════════════════════════════════
# WINDI Sovereign Dispatcher — Deploy Script
# Target: Strato 87.106.29.233
# ═══════════════════════════════════════════════════════
#
# Usage:
#   1. Upload dispatcher/ folder to /opt/windi/dispatcher/
#   2. Copy .env.example to .env and fill SMTP credentials
#   3. Run: bash deploy.sh
#
# ═══════════════════════════════════════════════════════

set -e

DEPLOY_DIR="/opt/windi/dispatcher"
LOG_FILE="/var/log/windi-dispatch.log"

echo "🐉 WINDI Dispatcher — Deploy"
echo "════════════════════════════"

# 1. Install dependencies
echo "📦 Installing dependencies..."
cd "$DEPLOY_DIR"
npm install --production

# 2. Check .env
if [ ! -f .env ]; then
    echo "⚠️  No .env found. Copying from .env.example..."
    cp .env.example .env
    echo "❗ IMPORTANT: Edit .env with your SMTP credentials before running!"
    echo "   nano $DEPLOY_DIR/.env"
    exit 1
fi

# 3. Create log file
touch "$LOG_FILE"
chmod 644 "$LOG_FILE"

# 4. Test run
echo ""
echo "🧪 Running test..."
node test-dispatch.js

# 5. Setup cron (09:00 CET, weekdays)
echo ""
echo "⏰ Setting up cron job..."

CRON_CMD="0 8 * * 1-5 cd $DEPLOY_DIR && /usr/bin/node run.js >> $LOG_FILE 2>&1"
# Note: Server likely UTC, so 8 UTC = 9 CET (winter) / 10 CEST (summer)
# Adjust if server uses Europe/Berlin timezone

# Check if cron already exists
if crontab -l 2>/dev/null | grep -q "windi.*run.js"; then
    echo "   Cron already exists — skipping"
else
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
    echo "   ✅ Cron installed: $CRON_CMD"
fi

echo ""
echo "════════════════════════════"
echo "✅ Deploy complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env with SMTP credentials"
echo "  2. Test: node test-dispatch.js"
echo "  3. Manual dispatch: node run.js"
echo "  4. Or via API: curl -X POST http://localhost:8090/api/dispatch -H 'Content-Type: application/json' -d '{\"recipient\":\"your@email.com\"}'"
echo ""
echo "Logs: tail -f $LOG_FILE"
echo "🐉 AI processes. Human decides. WINDI guarantees."
