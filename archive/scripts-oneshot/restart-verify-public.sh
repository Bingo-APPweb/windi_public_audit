#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# WINDI-LAW Smoke Test Fix — B4: Restart verify-public service
# Run with: sudo bash /home/windi/restart-verify-public.sh
# ═══════════════════════════════════════════════════════════════

echo "🔄 Restarting windi-verify-public service..."
systemctl restart windi-verify-public

sleep 2

echo "📊 Service status:"
systemctl status windi-verify-public --no-pager -l | head -15

echo ""
echo "🧪 Testing endpoint..."
sleep 1
curl -s http://localhost:8114/health 2>/dev/null && echo "" || echo "⚠️ Service not responding yet"

echo ""
echo "✅ Done!"
