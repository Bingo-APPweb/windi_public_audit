#!/bin/bash
# W-ACTUARY-001 nginx rate limiting
# Run with: sudo bash /opt/windi/w-actuary-001/nginx-ratelimit.sh

set -e

NGINX_CONF="/etc/nginx/sites-available/windi-domain.com"

echo "🛡️ W-ACTUARY-001 rate limiting setup"
echo "──────────────────────────────"

# Check if rate limit zone already exists
if grep -q "zone=actuary" "$NGINX_CONF"; then
    echo "✓ Rate limit zone already configured"
else
    echo "Adding rate limit zone..."
    # Add after the first 'server {' line in http context (before server blocks)
    # We need to add it in the http context, which is in nginx.conf

    # Check nginx.conf for existing zone
    if grep -q "zone=actuary" /etc/nginx/nginx.conf; then
        echo "✓ Rate limit zone exists in nginx.conf"
    else
        echo "Adding rate limit zone to nginx.conf..."
        sudo sed -i '/http {/a\    # W-ACTUARY-001 rate limiting\n    limit_req_zone $binary_remote_addr zone=actuary:10m rate=10r/s;' /etc/nginx/nginx.conf
        echo "✓ Rate limit zone added"
    fi
fi

# Update actuary API location with rate limiting
echo "Updating actuary API location..."
sed -i '/location \^~ \/actuary\/api\//,/}/c\
    # API Backend (:8015) with rate limiting\
    location ^~ /actuary/api/ {\
        limit_req zone=actuary burst=20 nodelay;\
        limit_req_status 429;\
        proxy_pass http://windi_actuary/;\
        proxy_http_version 1.1;\
        proxy_set_header Host $host;\
        proxy_set_header X-Real-IP $remote_addr;\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\
    }' "$NGINX_CONF"

# Test
echo "Testing nginx..."
/usr/sbin/nginx -t

# Reload
echo "Reloading nginx..."
systemctl reload nginx

echo "──────────────────────────────"
echo "✓ Rate limiting configured (10r/s, burst 20)"
