#!/bin/bash
# ══════════════════════════════════════════════════════════════
# Fix: /law/ shows JSON → redirect to /law/landing/
# Run with: sudo bash /home/windi/patch-nginx-law-redirect.sh
# ══════════════════════════════════════════════════════════════

NGINX_CONF="/etc/nginx/sites-enabled/windi-domain.com"
BACKUP="/home/windi/nginx-backup-law-redirect-$(date +%Y%m%d_%H%M%S).conf"

echo "═══════════════════════════════════════════════════════════"
echo "  WINDI Nginx Patch — /law/ Redirect"
echo "═══════════════════════════════════════════════════════════"

echo ""
echo "📦 Creating backup..."
cp "$NGINX_CONF" "$BACKUP"

echo "🔧 Adding redirect rule..."

# Add redirect before the catch-all /law/ proxy
# Find: location /law/ { proxy_pass
# Add before: location = /law/ { return 301 /law/landing/; }

sed -i '/location \/law\/ { proxy_pass/i\    # Redirect /law/ to landing page\n    location = /law/ { return 301 /law/landing/; }' "$NGINX_CONF"

echo ""
echo "🧪 Testing nginx config..."
nginx -t

if [ $? -eq 0 ]; then
    echo ""
    echo "🔄 Reloading nginx..."
    systemctl reload nginx
    echo ""
    echo "✅ Done! /law/ now redirects to /law/landing/"
else
    echo ""
    echo "❌ Config test failed! Restoring backup..."
    cp "$BACKUP" "$NGINX_CONF"
    echo "Restored from: $BACKUP"
fi
