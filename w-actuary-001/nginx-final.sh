#!/bin/bash
# W-ACTUARY-001 nginx final config (static frontend + API)
# Run with: sudo bash /opt/windi/w-actuary-001/nginx-final.sh

set -e

NGINX_CONF="/etc/nginx/sites-available/windi-domain.com"
BACKUP="$NGINX_CONF.bak.$(date +%Y%m%d%H%M%S)"

echo "🚀 W-ACTUARY-001 nginx final setup"
echo "──────────────────────────────"

# Backup
cp "$NGINX_CONF" "$BACKUP"
echo "✓ Backup: $BACKUP"

# Replace actuary block (lines 226-230) with new config
echo "Updating actuary configuration..."
sed -i '226,230c\
    # ── W-Actuary-001 — Verifiable Actuarial Intelligence ─────────────\
    # API Backend (:8015)\
    location ^~ /actuary/api/ {\
        proxy_pass http://windi_actuary/;\
        proxy_http_version 1.1;\
        proxy_set_header Host $host;\
        proxy_set_header X-Real-IP $remote_addr;\
    }\
    \
    # Static Frontend\
    location /actuary/ {\
        alias /opt/windi/w-actuary-001/frontend/;\
        index index.html;\
        try_files $uri $uri/ /actuary/index.html;\
        add_header X-WINDI-Service "w-actuary-001" always;\
    }' "$NGINX_CONF"

# Test
echo "Testing nginx..."
/usr/sbin/nginx -t

# Reload
echo "Reloading nginx..."
systemctl reload nginx

echo "──────────────────────────────"
echo "✓ W-ACTUARY-001 configured"
echo ""
echo "URLs:"
echo "  UI:  https://windi-domain.com/actuary/"
echo "  API: https://windi-domain.com/actuary/api/health"
