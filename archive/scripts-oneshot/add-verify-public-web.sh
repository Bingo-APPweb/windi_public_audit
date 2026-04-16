#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# Add /verify-public/web/ to nginx (correct placement)
# Run with: sudo bash /home/windi/add-verify-public-web.sh
# ═══════════════════════════════════════════════════════════════

NGINX_CONF="/etc/nginx/sites-enabled/windi-domain.com"

echo "🔧 Adding /verify-public/web/ location..."

# Check if already exists
if grep -q "location /verify-public/web/" "$NGINX_CONF"; then
    echo "✅ Already exists"
    nginx -t && systemctl reload nginx
    exit 0
fi

# Insert after JMPG Viewer block (line 213) using sed
# Find the line with "add_header X-WINDI-Service \"jmpg-viewer\"" and add after it
sed -i '/add_header X-WINDI-Service "jmpg-viewer" always;/a\
    }\
\
    # ── Verify Public Web (static) ──────────────────────────\
    location /verify-public/web/ {\
        alias /opt/windi/verify-public/web/;\
        index index.html;\
        try_files $uri $uri/ =404;\
        add_header Cache-Control "public, max-age=3600";\
        add_header X-WINDI-Service "verify-public-web" always;' "$NGINX_CONF"

# Remove the duplicate closing brace that was left
sed -i '213d' "$NGINX_CONF"

echo "🧪 Testing nginx..."
nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Config OK"
    echo "🔄 Reloading nginx..."
    systemctl reload nginx
    echo "✅ Done!"
    echo "📍 Test: curl https://windi-domain.com/verify-public/web/"
else
    echo "❌ Config error - please check manually"
fi
