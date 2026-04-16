#!/bin/bash
# Patch nginx to add /travel/map/ route for W-TRAVEL-MAP-001
# Usage: sudo bash patch-nginx.sh

set -e

NGINX_CONF="/etc/nginx/sites-enabled/windi-domain.com"
BACKUP="/tmp/nginx-backup-travel-map-$(date +%Y%m%d_%H%M%S).conf"
SNIPPET="/opt/windi/windi-travel/map-comparator/deploy-windi-travel-map/nginx-snippet.conf"

# Backup
cp "$NGINX_CONF" "$BACKUP"
echo "Backup: $BACKUP"

# Check if already patched
if grep -q "W-TRAVEL-MAP-001" "$NGINX_CONF"; then
    echo "Already patched. Exiting."
    exit 0
fi

# Insert before "# ═══ WINDI TRAVEL :8126 ═══"
sed -i '/# ═══ WINDI TRAVEL :8126 ═══/r '"$SNIPPET" "$NGINX_CONF"
# Move the inserted block BEFORE the marker line
sed -i '/# ═══ W-TRAVEL-MAP-001/,/^    }$/{ H; d }; /# ═══ WINDI TRAVEL :8126 ═══/{ x; p; x }' "$NGINX_CONF"

# Alternative simpler approach - just insert before the line
sed -i "s|    # ═══ WINDI TRAVEL :8126 ═══|$(cat $SNIPPET)\n\n    # ═══ WINDI TRAVEL :8126 ═══|" "$BACKUP"
cp "$BACKUP" "$NGINX_CONF"

# Test
nginx -t
if [ $? -eq 0 ]; then
    systemctl reload nginx
    echo "Done! /travel/map/ now routes to :8153"
else
    echo "nginx -t failed! Restoring backup..."
    cp "$BACKUP" "$NGINX_CONF"
    exit 1
fi
