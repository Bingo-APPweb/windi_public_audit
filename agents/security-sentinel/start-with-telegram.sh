#!/bin/bash
# W-SEC-001 — Start with Telegram Webhooks
# Usage: ./start-with-telegram.sh <BOT_TOKEN> <CHAT_ID>

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: ./start-with-telegram.sh <BOT_TOKEN> <CHAT_ID>"
    echo ""
    echo "Example:"
    echo "  ./start-with-telegram.sh '1234567890:ABCdef...' '-1001234567890'"
    exit 1
fi

BOT_TOKEN="$1"
CHAT_ID="$2"

# Stop existing instance
echo "🔴 Stopping existing instance..."
pkill -f "uvicorn app:app.*8144" 2>/dev/null
sleep 2

# Export environment variables
export SEC_TELEGRAM_BOT_TOKEN="$BOT_TOKEN"
export SEC_TELEGRAM_CHAT_ID="$CHAT_ID"
export SEC_TELEGRAM_ENABLED="true"

# Start service
echo "🟢 Starting W-SEC-001 with Telegram enabled..."
cd /opt/windi/agents/security-sentinel

nohup python3 -m uvicorn app:app --host 0.0.0.0 --port 8144 >> /opt/windi/logs/security/w-sec-001.log 2>&1 &

sleep 3

# Verify
echo ""
echo "Checking health..."
curl -s http://127.0.0.1:8144/health | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"✅ Service: {data['service']} v{data['version']}\")
print(f\"✅ Port: {data['port']}\")
print(f\"✅ Telegram configured: {data['webhooks']['telegram_configured']}\")
"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "To test, run:"
echo "  curl -X POST http://127.0.0.1:8144/sec/webhooks/test"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
