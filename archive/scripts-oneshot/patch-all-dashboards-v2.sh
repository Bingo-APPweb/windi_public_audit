#!/bin/bash
# WINDI Portal Full Dashboard Patch v2
# Adds all missing dashboard routes to nginx
# Run with: sudo bash patch-all-dashboards-v2.sh

set -e

NGINX_CONF="/etc/nginx/sites-enabled/windi-domain.com"
BACKUP="/home/windi/nginx-backup-full-dashboards-$(date +%Y%m%d_%H%M%S).conf"

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║         WINDI PORTAL - FULL DASHBOARD NGINX PATCH v2               ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

echo "=== Step 1: Backing up nginx config ==="
cp "$NGINX_CONF" "$BACKUP"
echo "Backup: $BACKUP"

echo ""
echo "=== Step 2: Finding insertion point ==="
# Find the line number where we'll insert (before "location /wcache/")
LINE_NUM=$(grep -n "location /wcache/" "$NGINX_CONF" | head -1 | cut -d: -f1)
echo "Inserting before line $LINE_NUM (location /wcache/)"

echo ""
echo "=== Step 3: Creating patched config ==="

# Split the file and insert new routes
head -n $((LINE_NUM - 1)) "$NGINX_CONF" > /tmp/nginx_part1.conf

cat >> /tmp/nginx_part1.conf << 'ROUTES'

    # ═══════════════════════════════════════════════════════════════════
    # WINDI DASHBOARDS · Agent Interfaces
    # Added by patch-all-dashboards-v2.sh · 13 Apr 2026
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

    # Audit Dashboard
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

tail -n +$LINE_NUM "$NGINX_CONF" >> /tmp/nginx_part1.conf

echo ""
echo "=== Step 4: Fix fediverse route ==="
sed -i 's|proxy_pass http://127.0.0.1:8142/fediverse/;|proxy_pass http://127.0.0.1:8142/;|g' /tmp/nginx_part1.conf

echo ""
echo "=== Step 5: Testing new config ==="
cp /tmp/nginx_part1.conf "$NGINX_CONF"

if nginx -t; then
    echo "✅ nginx config OK"
else
    echo "❌ nginx config ERROR - restoring backup"
    cp "$BACKUP" "$NGINX_CONF"
    rm -f /tmp/nginx_part1.conf
    exit 1
fi

echo ""
echo "=== Step 6: Reloading nginx ==="
systemctl reload nginx

echo ""
echo "=== Step 7: Testing new routes ==="
sleep 2

test_url() {
    local name=$1
    local url=$2
    local status=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "ERR")
    if [ "$status" == "200" ]; then
        printf "  ✅ %-12s %s → %s\n" "$name" "$status" "$url"
    else
        printf "  ❌ %-12s %s → %s\n" "$name" "$status" "$url"
    fi
}

echo ""
test_url "legal" "https://windi-domain.com/legal/"
test_url "notary" "https://windi-domain.com/notary/"
test_url "audit-dash" "https://windi-domain.com/audit-dash/"
test_url "sec" "https://windi-domain.com/sec/"
test_url "joe-dash" "https://windi-domain.com/joe-dash/"
test_url "vd-cut" "https://windi-domain.com/vd-cut/"
test_url "vd-mass" "https://windi-domain.com/vd-mass/"
test_url "ledger" "https://windi-domain.com/ledger/"
test_url "watch" "https://windi-domain.com/watch/"
test_url "fediverse" "https://windi-domain.com/fediverse/"

echo ""
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║                    ✅ PATCH COMPLETE                               ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Backup saved to: $BACKUP"

rm -f /tmp/nginx_part1.conf
