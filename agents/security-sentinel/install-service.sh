#!/bin/bash
# W-SEC-001 — Install systemd service
# Run with: sudo bash install-service.sh

set -e

echo "🛡️ Installing W-SEC-001 Security Sentinel..."

# Ensure log directory exists
mkdir -p /opt/windi/logs/security
chown windi:windi /opt/windi/logs/security

# Copy service file
cp /opt/windi/agents/security-sentinel/windi-sec-001.service /etc/systemd/system/

# Reload systemd
systemctl daemon-reload

# Enable and start
systemctl enable windi-sec-001.service
systemctl start windi-sec-001.service

# Wait and verify
sleep 3

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
systemctl status windi-sec-001.service --no-pager
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo "🧪 Testing endpoints..."
curl -s http://127.0.0.1:8144/health | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'✅ Service: {data[\"service\"]} v{data[\"version\"]}')
print(f'✅ Telegram: {data[\"webhooks\"][\"telegram_configured\"]}')
"

echo ""
echo "🎉 W-SEC-001 installed successfully!"
echo ""
echo "Commands:"
echo "  systemctl status windi-sec-001"
echo "  journalctl -u windi-sec-001 -f"
echo "  tail -f /opt/windi/logs/security/w-sec-001.log"
