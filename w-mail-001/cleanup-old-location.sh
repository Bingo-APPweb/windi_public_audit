#!/bin/bash
# Remove obsolete /mail/ location from windi-domain.com
# (Now using dedicated mail.windisites.de subdomain)

set -e

NGINX_CONF="/etc/nginx/sites-enabled/windi-domain.com"
BACKUP="/opt/windi/backups/nginx/windi-domain.com.cleanup-mail-$(date +%Y%m%d_%H%M%S)"

echo "Cleaning up obsolete /mail/ location from windi-domain.com..."

# Backup
cp "$NGINX_CONF" "$BACKUP"
echo "✅ Backup: $BACKUP"

# Remove /mail/ location block (lines 306-318 approximately)
sed -i '/# W-MAIL-001 — SnappyMail WebUI (:8200)/,/^    }$/d' "$NGINX_CONF"

echo "✅ Obsolete location removed"

# Test
nginx -t && systemctl reload nginx

echo "✅ Cleanup complete — /mail/ removed from windi-domain.com"
echo "   SnappyMail now exclusively at: https://mail.windisites.de/"
