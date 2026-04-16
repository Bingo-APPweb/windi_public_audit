#!/bin/bash
# Add redirect /verify-public/docs/ → /verify-public/web/docs/
# Run with: sudo bash /home/windi/patch-nginx-verify-docs.sh

NGINX_CONF="/etc/nginx/sites-enabled/windi-domain.com"
BACKUP="/home/windi/nginx-backup-verify-docs-$(date +%Y%m%d_%H%M%S).conf"

echo "═══════════════════════════════════════════════════════════"
echo "  WINDI Nginx Patch — /verify-public/docs/ Redirect"
echo "═══════════════════════════════════════════════════════════"

# Check if already exists
if grep -q "verify-public/docs/" "$NGINX_CONF"; then
    echo "⚠️  Route already exists"
    grep -n "verify-public/docs" "$NGINX_CONF"
    exit 0
fi

cp "$NGINX_CONF" "$BACKUP"
echo "📦 Backup: $BACKUP"

# Find verify-public/web/ line and insert redirect before it
LINE=$(grep -n "location /verify-public/web/" "$NGINX_CONF" | head -1 | cut -d: -f1)

if [ -z "$LINE" ]; then
    echo "❌ Could not find /verify-public/web/ location"
    exit 1
fi

echo "📍 Inserting before line $LINE"

head -n $((LINE-1)) "$NGINX_CONF" > /tmp/nginx_new.conf
cat >> /tmp/nginx_new.conf << 'EOF'
      # Redirect /verify-public/docs/ → /verify-public/web/docs/
      location ^~ /verify-public/docs/ {
          return 301 /verify-public/web/docs/$request_uri;
      }

EOF
tail -n +$LINE "$NGINX_CONF" >> /tmp/nginx_new.conf

cp /tmp/nginx_new.conf "$NGINX_CONF"

echo "🧪 Testing nginx..."
nginx -t

if [ $? -eq 0 ]; then
    echo "🔄 Reloading nginx..."
    systemctl reload nginx
    echo "✅ /verify-public/docs/ → /verify-public/web/docs/"
else
    echo "❌ Failed! Restoring..."
    cp "$BACKUP" "$NGINX_CONF"
fi
