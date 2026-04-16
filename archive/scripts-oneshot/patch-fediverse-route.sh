#!/bin/bash
# WINDI Fediverse - fix nginx route
# Corrects /fediverse/ to point to root of :8142
# Run with: sudo bash patch-fediverse-route.sh

set -e

NGINX_CONF="/etc/nginx/sites-enabled/windi-domain.com"
BACKUP="/home/windi/nginx-backup-fediverse-fix-$(date +%Y%m%d_%H%M%S).conf"

echo "=== Backing up nginx config ==="
cp "$NGINX_CONF" "$BACKUP"
echo "Backup: $BACKUP"

echo "=== Fixing fediverse route ==="
# Change from: proxy_pass http://127.0.0.1:8142/fediverse/;
# To: proxy_pass http://127.0.0.1:8142/;

sed -i 's|proxy_pass http://127.0.0.1:8142/fediverse/;|proxy_pass http://127.0.0.1:8142/;|g' "$NGINX_CONF"

echo "=== Testing nginx config ==="
nginx -t

echo "=== Reloading nginx ==="
systemctl reload nginx

echo "=== Testing fediverse ==="
echo -n "fediverse: "; curl -s https://windi-domain.com/fediverse/ | head -c 100
echo ""

echo ""
echo "✅ Fediverse route fixed!"
