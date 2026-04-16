#!/bin/bash
# WINDI Portal Full Dashboard Patch
# Adds all missing dashboard routes to nginx
# Run with: sudo bash patch-all-dashboards.sh

set -e

NGINX_CONF="/etc/nginx/sites-enabled/windi-domain.com"
BACKUP="/home/windi/nginx-backup-full-dashboards-$(date +%Y%m%d_%H%M%S).conf"

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║         WINDI PORTAL - FULL DASHBOARD NGINX PATCH                  ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

echo "=== Step 1: Backing up nginx config ==="
cp "$NGINX_CONF" "$BACKUP"
echo "Backup: $BACKUP"

echo ""
echo "=== Step 2: Adding dashboard routes ==="

# Create a temp file with the new routes
cat > /tmp/dashboard_routes.conf << 'ROUTES'

    # ═══════════════════════════════════════════════════════════════════
    # WINDI DASHBOARDS · Agent Interfaces
    # Added by patch-all-dashboards.sh
    # ═══════════════════════════════════════════════════════════════════

    # Legal Dashboard
    location /legal/ {
        alias /opt/windi/legal-dashboard/;
        index index.html;
        try_files $uri $uri/ /legal/index.html;
    }
    location = /legal { return 301 /legal/; }

    # Notary Dashboard
    location /notary/ {
        alias /opt/windi/notary-dashboard/;
        index index.html;
        try_files $uri $uri/ /notary/index.html;
    }
    location = /notary { return 301 /notary/; }

    # Audit Dashboard (using /audit-dash/ to avoid conflict with existing /audit/ proxy)
    location /audit-dash/ {
        alias /opt/windi/audit-dashboard/;
        index index.html;
        try_files $uri $uri/ /audit-dash/index.html;
    }
    location = /audit-dash { return 301 /audit-dash/; }

    # W-SEC-001 Security Sentinel Dashboard
    location /sec/ {
        alias /opt/windi/sec-dashboard/;
        index index.html;
        try_files $uri $uri/ /sec/index.html;
    }
    location = /sec { return 301 /sec/; }

    # W-JOE-001 Story Graph Dashboard
    location /joe-dash/ {
        alias /opt/windi/joe-dashboard/;
        index index.html;
        try_files $uri $uri/ /joe-dash/index.html;
    }
    location = /joe-dash { return 301 /joe-dash/; }

    # W-VD-CUT-001 Forensic Video Cutter Dashboard
    location /vd-cut/ {
        alias /opt/windi/vdcut-dashboard/;
        index index.html;
        try_files $uri $uri/ /vd-cut/index.html;
    }
    location = /vd-cut { return 301 /vd-cut/; }

    # W-VD-MASS-001 Batch Video Processing Dashboard
    location /vd-mass/ {
        alias /opt/windi/vdmass-dashboard/;
        index index.html;
        try_files $uri $uri/ /vd-mass/index.html;
    }
    location = /vd-mass { return 301 /vd-mass/; }

    # Forensic Ledger Info Page
    location /ledger/ {
        alias /opt/windi/ledger-info/;
        index index.html;
        try_files $uri $uri/ /ledger/index.html;
    }
    location = /ledger { return 301 /ledger/; }

    # Watch Info Page (Bridge)
    location /watch/ {
        alias /opt/windi/watch-info/;
        index index.html;
        try_files $uri $uri/ /watch/index.html;
    }

    # ═══════════════════════════════════════════════════════════════════
ROUTES

# Insert the routes before "location /wcache/"
sed -i '/location \/wcache\// {
    r /tmp/dashboard_routes.conf
    N
}' "$NGINX_CONF"

echo ""
echo "=== Step 3: Fix fediverse route ==="
# Change from: proxy_pass http://127.0.0.1:8142/fediverse/;
# To: proxy_pass http://127.0.0.1:8142/;
sed -i 's|proxy_pass http://127.0.0.1:8142/fediverse/;|proxy_pass http://127.0.0.1:8142/;|g' "$NGINX_CONF"

echo ""
echo "=== Step 4: Testing nginx config ==="
if nginx -t; then
    echo "✅ nginx config OK"
else
    echo "❌ nginx config ERROR - restoring backup"
    cp "$BACKUP" "$NGINX_CONF"
    exit 1
fi

echo ""
echo "=== Step 5: Reloading nginx ==="
systemctl reload nginx

echo ""
echo "=== Step 6: Testing new routes ==="
sleep 2

declare -A ROUTES=(
    ["legal"]="https://windi-domain.com/legal/"
    ["notary"]="https://windi-domain.com/notary/"
    ["audit-dash"]="https://windi-domain.com/audit-dash/"
    ["sec"]="https://windi-domain.com/sec/"
    ["joe-dash"]="https://windi-domain.com/joe-dash/"
    ["vd-cut"]="https://windi-domain.com/vd-cut/"
    ["vd-mass"]="https://windi-domain.com/vd-mass/"
    ["fediverse"]="https://windi-domain.com/fediverse/"
    ["ledger"]="https://windi-domain.com/ledger/"
    ["watch"]="https://windi-domain.com/watch/"
)

echo "┌──────────────┬────────┬─────────────────────────────────────┐"
echo "│ Service      │ Status │ URL                                 │"
echo "├──────────────┼────────┼─────────────────────────────────────┤"

for name in "${!ROUTES[@]}"; do
    url="${ROUTES[$name]}"
    status=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "ERR")
    if [ "$status" == "200" ]; then
        printf "│ %-12s │ ✅ %s │ %-35s │\n" "$name" "$status" "$url"
    else
        printf "│ %-12s │ ❌ %s │ %-35s │\n" "$name" "$status" "$url"
    fi
done

echo "└──────────────┴────────┴─────────────────────────────────────┘"

echo ""
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║                    ✅ PATCH COMPLETE                               ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""
echo "New Dashboard URLs:"
echo "  • https://windi-domain.com/legal/"
echo "  • https://windi-domain.com/notary/"
echo "  • https://windi-domain.com/audit-dash/"
echo "  • https://windi-domain.com/sec/"
echo "  • https://windi-domain.com/joe-dash/"
echo "  • https://windi-domain.com/vd-cut/"
echo "  • https://windi-domain.com/vd-mass/"
echo "  • https://windi-domain.com/ledger/"
echo "  • https://windi-domain.com/watch/"
echo "  • https://windi-domain.com/fediverse/ (fixed)"
echo ""
echo "Backup saved to: $BACKUP"

rm -f /tmp/dashboard_routes.conf
