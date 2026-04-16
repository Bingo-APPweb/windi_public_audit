#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# WINDI-LAW Smoke Test — Complete Fix v2
# Run with: sudo bash /home/windi/fix-smoke-test-v2.sh
# ═══════════════════════════════════════════════════════════════

set -e

echo "═══════════════════════════════════════════════════════════════"
echo "WINDI-LAW Smoke Test Fix v2"
echo "═══════════════════════════════════════════════════════════════"

# ─── STEP 1: Fix nginx (remove stray backup from sites-enabled) ───
echo ""
echo "🔧 STEP 1: Fixing nginx..."

# Move backup files out of sites-enabled
if ls /etc/nginx/sites-enabled/*.bak* 1>/dev/null 2>&1; then
    echo "   Moving backup files out of sites-enabled..."
    mv /etc/nginx/sites-enabled/*.bak* /tmp/
    echo "   ✅ Backup files moved to /tmp/"
fi

# Check if /api/verify/ already exists in config
if grep -q "location.*api/verify" /etc/nginx/sites-enabled/windi-domain.com 2>/dev/null; then
    echo "   ✅ /api/verify/ location already exists"
else
    echo "   Adding /api/verify/ location..."
    # Insert after /api/receipts/ block using awk (more reliable than sed)
    awk '
    /location \^~ \/api\/receipts\/ \{/ { in_receipts=1 }
    in_receipts && /^    \}$/ {
        print
        print ""
        print "    # ── Forensic Ledger Verify API ───────────────────────────"
        print "    location ^~ /api/verify/ {"
        print "        proxy_pass http://windi_ledger/api/verify/;"
        print "        proxy_http_version 1.1;"
        print "    }"
        in_receipts=0
        next
    }
    { print }
    ' /etc/nginx/sites-enabled/windi-domain.com > /tmp/nginx-windi-new.conf

    mv /tmp/nginx-windi-new.conf /etc/nginx/sites-enabled/windi-domain.com
    echo "   ✅ /api/verify/ location added"
fi

echo "   Testing nginx config..."
nginx -t

echo "   Reloading nginx..."
systemctl reload nginx
echo "   ✅ Nginx reloaded"

# ─── STEP 2: Install httpx ───────────────────────────────────────
echo ""
echo "🔧 STEP 2: Installing httpx..."

pip3 install httpx==0.27.0 --quiet 2>/dev/null || pip install httpx==0.27.0 --quiet
echo "   ✅ httpx installed"

# Verify installation
python3 -c "import httpx; print('   httpx version:', httpx.__version__)"

# ─── STEP 3: Restart verify-public service ───────────────────────
echo ""
echo "🔧 STEP 3: Restarting verify-public service..."

systemctl restart windi-verify-public
sleep 3

# Check status
if systemctl is-active --quiet windi-verify-public; then
    echo "   ✅ windi-verify-public is running"
else
    echo "   ⚠️ windi-verify-public failed to start"
    echo "   Checking logs..."
    journalctl -u windi-verify-public -n 10 --no-pager
fi

# ─── STEP 4: Quick verification ──────────────────────────────────
echo ""
echo "🧪 STEP 4: Quick verification..."

# Test nginx /api/verify/ endpoint
echo "   Testing /api/verify/ endpoint..."
VERIFY_RESULT=$(curl -s "https://windi-domain.com/api/verify/WINDI-LAW-SMOKE-1774544561" 2>/dev/null)
if echo "$VERIFY_RESULT" | grep -q "ok"; then
    echo "   ✅ /api/verify/ working!"
    echo "   $VERIFY_RESULT" | head -3
else
    echo "   ⚠️ /api/verify/ not working yet"
    echo "   Response: $VERIFY_RESULT"
fi

# Test verify-public health if running on 8114
echo ""
echo "   Testing verify-public health (port 8114)..."
HEALTH=$(curl -s http://localhost:8114/health 2>/dev/null || echo "not responding")
echo "   Health: $HEALTH"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ COMPLETE!"
echo ""
echo "Next: Run smoke test to verify 7/7 PASS"
echo "═══════════════════════════════════════════════════════════════"
