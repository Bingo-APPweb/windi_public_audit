#!/bin/bash
# ═══════════════════════════════════════════════
# W-CACHE-001 · NGINX ROUTE PATCH
# Adds /wcache/ route for NOIR dashboard
# ═══════════════════════════════════════════════

set -e

NGINX_CONF="/etc/nginx/sites-enabled/windi-domain.com"
BACKUP="/tmp/nginx-backup-wcache-$(date +%Y%m%d_%H%M%S).conf"

echo "🔵 W-CACHE-001 nginx patch"
echo "─────────────────────────────"

# Check if already patched
if grep -q "location /wcache" "$NGINX_CONF"; then
    echo "✅ Already patched - /wcache route exists"
    exit 0
fi

# Backup
echo "📦 Creating backup: $BACKUP"
sudo cp "$NGINX_CONF" "$BACKUP"

echo "📝 Adding W-CACHE-001 routes..."

# Create patch file
cat > /tmp/wcache-patch.txt << 'EOF'

    # ═══════════════════════════════════════════════
    # W-CACHE-001 · NOIR Dashboard · Port 8160
    # ═══════════════════════════════════════════════

    location /wcache/ {
        proxy_pass http://127.0.0.1:8160/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /wcache/api/ {
        proxy_pass http://127.0.0.1:8160/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location = /wcache {
        return 301 /wcache/noir;
    }

    location = /wcache/noir {
        proxy_pass http://127.0.0.1:8160/noir;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }
EOF

# Insert before enterprise location block
sudo sed -i "/location \/enterprise\//r /tmp/wcache-patch.txt" "$NGINX_CONF"

# Test nginx config
echo "🔍 Testing nginx configuration..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Nginx config OK - reloading..."
    sudo systemctl reload nginx
    echo ""
    echo "═══════════════════════════════════════════════"
    echo "✅ W-CACHE-001 NOIR Dashboard available at:"
    echo "   https://windi-domain.com/wcache/noir"
    echo ""
    echo "   API: https://windi-domain.com/wcache/api/cache/v1/"
    echo "═══════════════════════════════════════════════"
else
    echo "❌ Nginx config FAILED - rolling back..."
    sudo cp "$BACKUP" "$NGINX_CONF"
    echo "Restored from backup"
    exit 1
fi
