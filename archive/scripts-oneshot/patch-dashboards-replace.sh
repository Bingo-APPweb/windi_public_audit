#!/bin/bash
# WINDI Portal - Replace API routes with Dashboard routes
# Run with: sudo bash patch-dashboards-replace.sh

set -e

NGINX_CONF="/etc/nginx/sites-enabled/windi-domain.com"
BACKUP="/home/windi/nginx-backup-replace-$(date +%Y%m%d_%H%M%S).conf"

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║       WINDI PORTAL - REPLACE API ROUTES WITH DASHBOARDS            ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

echo "=== Step 1: Backup ==="
cp "$NGINX_CONF" "$BACKUP"
echo "Backup: $BACKUP"

echo ""
echo "=== Step 2: Replacing routes ==="

# Function to replace a proxy route with a static alias route
replace_route() {
    local path=$1
    local alias_path=$2
    local file=$3

    # Create the new route block
    local new_block="location /${path}/ {
        alias ${alias_path}/;
        index index.html;
        try_files \$uri \$uri/ /${path}/index.html;
    }
    location = /${path} { return 301 /${path}/; }"

    echo "  Replacing /${path}/ → ${alias_path}/"
}

# For now, let's do targeted sed replacements

# 1. Legal: /legal/ → static
echo "  [1/10] Replacing /legal/"
sed -i '/location \^~ \/legal\/ {/,/}/ {
    s|proxy_pass http://127.0.0.1:8091/legal/;|alias /opt/windi/legal-dashboard/;\n        index index.html;\n        try_files $uri $uri/ /legal/index.html;|
    /proxy_http_version/d
    /proxy_set_header/d
    /proxy_read_timeout/d
}' "$NGINX_CONF"

# 2. Notary: /notary/ → static
echo "  [2/10] Replacing /notary/"
sed -i '/location \^~ \/notary\/ {/,/}/ {
    s|proxy_pass http://127.0.0.1:8091/notary/;|alias /opt/windi/notary-dashboard/;\n        index index.html;\n        try_files $uri $uri/ /notary/index.html;|
    /proxy_http_version/d
    /proxy_set_header/d
    /proxy_read_timeout/d
}' "$NGINX_CONF"

# 3. Sec: /sec/ → static
echo "  [3/10] Replacing /sec/"
sed -i '/location \/sec\/ {/,/}/ {
    s|proxy_pass http://127.0.0.1:8144/;|alias /opt/windi/sec-dashboard/;\n        index index.html;\n        try_files $uri $uri/ /sec/index.html;|
    /proxy_http_version/d
    /proxy_set_header/d
    /proxy_read_timeout/d
}' "$NGINX_CONF"

# 4. VD-CUT: /vd-cut/ → static
echo "  [4/10] Replacing /vd-cut/"
sed -i '/location \^~ \/vd-cut\/ {/,/}/ {
    s|proxy_pass http://127.0.0.1:8128/vd-cut/;|alias /opt/windi/vdcut-dashboard/;\n        index index.html;\n        try_files $uri $uri/ /vd-cut/index.html;|
    /proxy_http_version/d
    /proxy_set_header/d
    /proxy_read_timeout/d
}' "$NGINX_CONF"

# 5. VD-MASS: /vd-mass/ → static
echo "  [5/10] Replacing /vd-mass/"
sed -i '/location \/vd-mass\/ {/,/}/ {
    s|proxy_pass http://127.0.0.1:8131/;|alias /opt/windi/vdmass-dashboard/;\n        index index.html;\n        try_files $uri $uri/ /vd-mass/index.html;|
    /proxy_http_version/d
    /proxy_set_header/d
    /proxy_read_timeout/d
}' "$NGINX_CONF"

# 6. Joe: /joe/ → /joe-dash/ static (needs new route)
echo "  [6/10] Replacing /joe/"
sed -i '/location \^~ \/joe\/ {/,/}/ {
    s|proxy_pass http://127.0.0.1:8129/joe/;|alias /opt/windi/joe-dashboard/;\n        index index.html;\n        try_files $uri $uri/ /joe/index.html;|
    /proxy_http_version/d
    /proxy_set_header/d
    /proxy_read_timeout/d
}' "$NGINX_CONF"

# 7. Watch: /watch/ → static
echo "  [7/10] Replacing /watch/"
sed -i '/location \/watch\/ {/,/}/ {
    s|proxy_pass http://127.0.0.1:8143/watch/;|alias /opt/windi/watch-info/;\n        index index.html;\n        try_files $uri $uri/ /watch/index.html;|
    /proxy_http_version/d
    /proxy_set_header/d
    /proxy_read_timeout/d
}' "$NGINX_CONF"

# 8. Fediverse: fix the proxy path
echo "  [8/10] Fixing /fediverse/"
sed -i 's|proxy_pass http://127.0.0.1:8142/fediverse/;|proxy_pass http://127.0.0.1:8142/;|g' "$NGINX_CONF"

# 9 & 10: Ledger and audit-dash need NEW routes (insert before wcache)
echo "  [9/10] Adding /ledger/ route"
echo "  [10/10] Adding /audit-dash/ route"

# Find wcache line and insert new routes before it
LINE_NUM=$(grep -n "location /wcache/" "$NGINX_CONF" | head -1 | cut -d: -f1)

if [ -n "$LINE_NUM" ]; then
    head -n $((LINE_NUM - 1)) "$NGINX_CONF" > /tmp/nginx_temp.conf

    cat >> /tmp/nginx_temp.conf << 'NEWROUTES'

    # Forensic Ledger Info Page
    location /ledger/ {
        alias /opt/windi/ledger-info/;
        index index.html;
        try_files $uri $uri/ /ledger/index.html;
    }
    location = /ledger { return 301 /ledger/; }

    # Audit Dashboard
    location /audit-dash/ {
        alias /opt/windi/audit-dashboard/;
        index index.html;
        try_files $uri $uri/ /audit-dash/index.html;
    }
    location = /audit-dash { return 301 /audit-dash/; }

NEWROUTES

    tail -n +$LINE_NUM "$NGINX_CONF" >> /tmp/nginx_temp.conf
    mv /tmp/nginx_temp.conf "$NGINX_CONF"
fi

echo ""
echo "=== Step 3: Testing nginx config ==="
if nginx -t; then
    echo "✅ nginx config OK"
else
    echo "❌ nginx config ERROR - restoring backup"
    cp "$BACKUP" "$NGINX_CONF"
    exit 1
fi

echo ""
echo "=== Step 4: Reloading nginx ==="
systemctl reload nginx

echo ""
echo "=== Step 5: Testing routes ==="
sleep 2

for route in legal notary sec vd-cut vd-mass joe watch fediverse ledger audit-dash; do
    status=$(curl -s -o /dev/null -w "%{http_code}" "https://windi-domain.com/${route}/" 2>/dev/null || echo "ERR")
    if [ "$status" == "200" ]; then
        printf "  ✅ %-12s %s\n" "/${route}/" "$status"
    else
        printf "  ❌ %-12s %s\n" "/${route}/" "$status"
    fi
done

echo ""
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║                    ✅ PATCH COMPLETE                               ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo "Backup: $BACKUP"
