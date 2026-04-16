#!/bin/bash
# Add /api/briefing route to nginx
# Run with: sudo bash /home/windi/patch-nginx-briefing.sh

NGINX_CONF="/etc/nginx/sites-enabled/windi-domain.com"
BACKUP="/home/windi/nginx-backup-briefing-$(date +%Y%m%d_%H%M%S).conf"

echo "═══════════════════════════════════════════════════════════"
echo "  WINDI Nginx Patch — /api/briefing Route"
echo "═══════════════════════════════════════════════════════════"

cp "$NGINX_CONF" "$BACKUP"
echo "📦 Backup: $BACKUP"

# Add briefing route before /api/dragon/ line
sed -i '/location.*\/api\/dragon\//i\    # ── Briefing Aggregator (:8123) ────────────────────────────\n    location = /api/briefing {\n        proxy_pass http://127.0.0.1:8123/api/briefing;\n        proxy_http_version 1.1;\n        proxy_set_header Host $host;\n        proxy_set_header X-Real-IP $remote_addr;\n    }\n' "$NGINX_CONF"

echo "🧪 Testing nginx..."
nginx -t

if [ $? -eq 0 ]; then
    echo "🔄 Reloading nginx..."
    systemctl reload nginx
    echo "✅ /api/briefing → :8123"
else
    echo "❌ Failed! Restoring..."
    cp "$BACKUP" "$NGINX_CONF"
fi
