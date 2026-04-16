#!/bin/bash
# Fix duplicate /cost/ route
set -e

CONF="/etc/nginx/sites-enabled/windi-domain.com"
BACKUP="/home/windi/nginx-backup-cost-fix-$(date +%Y%m%d_%H%M%S).conf"

cp "$CONF" "$BACKUP"
echo "Backup: $BACKUP"

# Remove lines 206-212 (second duplicate block including comment and blank line)
sed -i '206,212d' "$CONF"

nginx -t && systemctl reload nginx
echo "Fixed and reloaded"
