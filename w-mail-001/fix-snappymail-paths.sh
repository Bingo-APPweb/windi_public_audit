#!/bin/bash
# Fix SnappyMail path generation by adding X-Forwarded-Prefix header

set -e

NGINX_CONF="/etc/nginx/sites-enabled/windi-domain.com"
BACKUP="/opt/windi/backups/nginx/windi-domain.com.snappymail-fix-$(date +%Y%m%d_%H%M%S)"

echo "═══════════════════════════════════════════════════════════════"
echo "Fixing SnappyMail path generation"
echo "═══════════════════════════════════════════════════════════════"

# Backup
cp "$NGINX_CONF" "$BACKUP"
echo "✅ Backup: $BACKUP"

# Add X-Forwarded-Prefix header to mail location
echo "Adding X-Forwarded-Prefix header..."

sed -i '/location \^~ \/mail\/ {/,/}/ {
    /add_header X-WINDI-Service/a\        proxy_set_header X-Forwarded-Prefix /mail;
}' "$NGINX_CONF"

echo "✅ Header added"

# Test
nginx -t
if [ $? -ne 0 ]; then
  echo "❌ Config invalid - restoring backup"
  cp "$BACKUP" "$NGINX_CONF"
  exit 1
fi

# Reload
systemctl reload nginx
echo "✅ nginx reloaded"

echo ""
echo "Try accessing: https://windi-domain.com/mail/"
echo "If still failing, SnappyMail may need base path config in container."
