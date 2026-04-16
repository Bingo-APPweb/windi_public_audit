#!/bin/bash
# WINDI Portal Dashboards - nginx patch
# Adds routes for legal, notary, audit dashboards
# Run with: sudo bash patch-portal-dashboards.sh

set -e

NGINX_CONF="/etc/nginx/sites-enabled/windi-domain.com"
BACKUP="/home/windi/nginx-backup-dashboards-$(date +%Y%m%d_%H%M%S).conf"

echo "=== Backing up nginx config ==="
cp "$NGINX_CONF" "$BACKUP"
echo "Backup: $BACKUP"

echo "=== Adding dashboard routes ==="

# Find the line with "location = /portal {" and insert before it
sed -i '/location = \/portal {/i\
\
    # WINDI DASHBOARDS · Agent Interfaces\
    # ═══════════════════════════════════════════════\
\
    location /legal/ {\
        alias /opt/windi/legal-dashboard/;\
        index index.html;\
        try_files $uri $uri/ /legal/index.html;\
    }\
\
    location = /legal {\
        return 301 /legal/;\
    }\
\
    location /notary/ {\
        alias /opt/windi/notary-dashboard/;\
        index index.html;\
        try_files $uri $uri/ /notary/index.html;\
    }\
\
    location = /notary {\
        return 301 /notary/;\
    }\
\
    location /audit-dash/ {\
        alias /opt/windi/audit-dashboard/;\
        index index.html;\
        try_files $uri $uri/ /audit-dash/index.html;\
    }\
\
    location = /audit-dash {\
        return 301 /audit-dash/;\
    }\
' "$NGINX_CONF"

echo "=== Testing nginx config ==="
nginx -t

echo "=== Reloading nginx ==="
systemctl reload nginx

echo "=== Testing new routes ==="
echo -n "legal: "; curl -s -o /dev/null -w "%{http_code}" https://windi-domain.com/legal/
echo ""
echo -n "notary: "; curl -s -o /dev/null -w "%{http_code}" https://windi-domain.com/notary/
echo ""
echo -n "audit-dash: "; curl -s -o /dev/null -w "%{http_code}" https://windi-domain.com/audit-dash/
echo ""

echo ""
echo "✅ Dashboard routes added!"
echo ""
echo "URLs:"
echo "  https://windi-domain.com/legal/"
echo "  https://windi-domain.com/notary/"
echo "  https://windi-domain.com/audit-dash/"
