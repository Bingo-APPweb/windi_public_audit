#!/bin/bash
# Add timeouts to /desktop-gen7/ location block

set -e

NGINX_CONF="/etc/nginx/sites-enabled/windi-domain.com"
BACKUP_DIR="/opt/windi/backups/nginx"
BACKUP_FILE="${BACKUP_DIR}/windi-domain.com.bak.$(date +%Y%m%d%H%M%S)"

echo "[1/3] Creating backup..."
sudo mkdir -p "$BACKUP_DIR"
sudo cp "$NGINX_CONF" "$BACKUP_FILE"
echo "      ✅ Backup: $BACKUP_FILE"

echo "[2/3] Adding timeouts to /desktop-gen7/ block..."
sudo sed -i '/location \^~ \/desktop-gen7\//,/^    }/ {
    /proxy_set_header X-Forwarded-Proto/a\
        proxy_read_timeout 60s;\
        proxy_connect_timeout 10s;
}' "$NGINX_CONF"
echo "      ✅ Timeouts added"

echo "[3/3] Testing nginx..."
if sudo nginx -t; then
    echo "      ✅ nginx test passed"
    sudo systemctl reload nginx
    echo "      ✅ nginx reloaded"
else
    echo "      ❌ nginx test FAILED - restoring backup"
    sudo cp "$BACKUP_FILE" "$NGINX_CONF"
    exit 1
fi

echo ""
echo "Verification:"
grep -A 12 "desktop-gen7" /etc/nginx/sites-enabled/windi-domain.com
