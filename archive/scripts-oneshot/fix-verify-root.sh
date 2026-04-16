#!/bin/bash
# Fix verify-public root route
# Date: 2026-04-01
# Purpose: Add /verify-public/ route to serve index.html

set -e

NGINX_CONF="/etc/nginx/sites-enabled/windi-domain.com"
BACKUP="/etc/nginx/sites-enabled/windi-domain.com.bak.$(date +%Y%m%d_%H%M%S)"

echo "=== WINDI Verify Public Root Fix ==="
echo ""

# Backup
echo "[1/4] Creating backup..."
cp "$NGINX_CONF" "$BACKUP"
echo "      Backup: $BACKUP"

# Insert new route before line 226 (before Verify Public API comment)
echo "[2/4] Adding /verify-public/ root route..."

sed -i '225a\
\
    # ── Verify Public Root ──────────────────────────\
    location = /verify-public/ {\
        alias /opt/windi/verify-public/web/;\
        index index.html;\
        try_files /index.html =404;\
        add_header Cache-Control "public, max-age=3600";\
        add_header X-WINDI-Service "verify-public-root" always;\
    }' "$NGINX_CONF"

# Test nginx config
echo "[3/4] Testing nginx config..."
nginx -t

# Reload nginx
echo "[4/4] Reloading nginx..."
systemctl reload nginx

echo ""
echo "=== DONE ==="
echo "Test: curl -I https://windi-domain.com/verify-public/"
