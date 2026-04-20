#!/bin/bash
# W-ACTUARY-001 nginx fix script
# Run with: sudo bash /opt/windi/w-actuary-001/fix-nginx.sh

set -e

NGINX_CONF="/etc/nginx/sites-available/windi-domain.com"
BACKUP="/etc/nginx/sites-available/windi-domain.com.bak.$(date +%Y%m%d%H%M%S)"

echo "🔧 W-ACTUARY-001 nginx fix"
echo "──────────────────────────────"

# Backup
cp "$NGINX_CONF" "$BACKUP"
echo "✓ Backup created: $BACKUP"

# Remove all broken actuary blocks (lines containing actuary location)
echo "Removing broken actuary blocks..."
sed -i '/# ── W-Actuary-001 (:8015)/,/^    }/d' "$NGINX_CONF"

# Fix the broken /api/receipts/ block - reconstruct it
echo "Fixing /api/receipts/ block..."
sed -i '/location \^~ \/api\/receipts\/ {$/,/^    }$/c\
    location ^~ /api/receipts/ {\
        proxy_pass http://windi_ledger/api/receipts/;\
        proxy_http_version 1.1;\
    }' "$NGINX_CONF" 2>/dev/null || true

# Add actuary location BEFORE the catch-all "location /"
echo "Adding actuary location in correct position..."
sed -i '/^    location \/ {$/i\
    # ── W-Actuary-001 (:8015) — Verifiable Actuarial Intelligence ─────\
    location ^~ /actuary/ {\
        proxy_pass http://windi_actuary/;\
        proxy_http_version 1.1;\
    }\
' "$NGINX_CONF"

# Test nginx config
echo "Testing nginx configuration..."
nginx -t

# Reload
echo "Reloading nginx..."
systemctl reload nginx

echo "──────────────────────────────"
echo "✓ nginx fixed and reloaded"
echo ""
echo "Test: curl https://windi-domain.com/actuary/health"
