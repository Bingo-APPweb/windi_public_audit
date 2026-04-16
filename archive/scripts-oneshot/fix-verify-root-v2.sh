#!/bin/bash
# Fix verify-public root route - v2
# Move backup out of sites-enabled

set -e

echo "=== Fix: Moving backup out of sites-enabled ==="

# Move backup to home
mv /etc/nginx/sites-enabled/windi-domain.com.bak.* /home/windi/ 2>/dev/null || true

echo "[1/2] Testing nginx config..."
nginx -t

echo "[2/2] Reloading nginx..."
systemctl reload nginx

echo ""
echo "=== DONE ==="
echo "Test: curl -I https://windi-domain.com/verify-public/"
