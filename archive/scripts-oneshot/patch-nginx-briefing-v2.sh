#!/bin/bash
# Add /api/briefing route to nginx (v2 - safer)
# Run with: sudo bash /home/windi/patch-nginx-briefing-v2.sh

NGINX_CONF="/etc/nginx/sites-enabled/windi-domain.com"
BACKUP="/home/windi/nginx-backup-briefing-$(date +%Y%m%d_%H%M%S).conf"

echo "═══════════════════════════════════════════════════════════"
echo "  WINDI Nginx Patch — /api/briefing Route (v2)"
echo "═══════════════════════════════════════════════════════════"

# Check if already exists
if grep -q "api/briefing" "$NGINX_CONF"; then
    echo "⚠️  /api/briefing already exists in config"
    grep -n "briefing" "$NGINX_CONF"
    exit 0
fi

cp "$NGINX_CONF" "$BACKUP"
echo "📦 Backup: $BACKUP"

# Find line number of /api/dragon/ and insert before it
LINE=$(grep -n "location.*\/api\/dragon\/" "$NGINX_CONF" | head -1 | cut -d: -f1)

if [ -z "$LINE" ]; then
    echo "❌ Could not find /api/dragon/ location"
    exit 1
fi

echo "📍 Inserting before line $LINE"

# Create temp file with the new content
head -n $((LINE-1)) "$NGINX_CONF" > /tmp/nginx_new.conf
cat >> /tmp/nginx_new.conf << 'EOF'
    # ── Briefing Aggregator (:8123) ────────────────────────────
    location = /api/briefing {
        proxy_pass http://127.0.0.1:8123/api/briefing;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

EOF
tail -n +$LINE "$NGINX_CONF" >> /tmp/nginx_new.conf

cp /tmp/nginx_new.conf "$NGINX_CONF"

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
