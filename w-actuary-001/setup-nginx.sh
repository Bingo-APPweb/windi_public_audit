#!/bin/bash
# W-ACTUARY-001 nginx setup script
# Run with: sudo bash /opt/windi/w-actuary-001/setup-nginx.sh

set -e

NGINX_CONF="/etc/nginx/sites-available/windi-domain.com"

echo "📊 W-ACTUARY-001 nginx setup"
echo "──────────────────────────────"

# Check if already configured
if grep -q "windi_actuary" "$NGINX_CONF"; then
    echo "✓ Upstream already exists"
else
    echo "Adding upstream..."
    sed -i '/upstream windi_dragon.*8108/a upstream windi_actuary      { server 127.0.0.1:8015 max_fails=3 fail_timeout=30s; keepalive 8;  }' "$NGINX_CONF"
    echo "✓ Upstream added"
fi

# Check if location exists
if grep -q "/actuary/" "$NGINX_CONF"; then
    echo "✓ Location already exists"
else
    echo "Adding location block..."
    # Add after /api/receipts/ block
    sed -i '/location \^~ \/api\/receipts\//,/}/a\
\
    # ── W-Actuary-001 (:8015) — Verifiable Actuarial Intelligence ─\
    location ^~ /actuary/ {\
        proxy_pass http://windi_actuary/;\
        proxy_http_version 1.1;\
    }' "$NGINX_CONF"
    echo "✓ Location added"
fi

# Test nginx config
echo "Testing nginx configuration..."
nginx -t

# Reload
echo "Reloading nginx..."
systemctl reload nginx

echo "──────────────────────────────"
echo "✓ W-ACTUARY-001 exposed at https://windi-domain.com/actuary/"
echo ""
echo "Test endpoints:"
echo "  /actuary/health"
echo "  /actuary/receipts"
echo "  /actuary/demo/full-flow/{receipt_id}"
