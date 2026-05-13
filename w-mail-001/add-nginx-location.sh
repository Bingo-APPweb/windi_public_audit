#!/bin/bash
# Add W-MAIL-001 location block to nginx config

set -e

NGINX_CONF="/etc/nginx/sites-enabled/windi-domain.com"
BACKUP="/opt/windi/backups/nginx/windi-domain.com.pre-mail-$(date +%Y%m%d_%H%M%S)"

echo "═══════════════════════════════════════════════════════════════"
echo "Adding W-MAIL-001 location block to nginx config"
echo "═══════════════════════════════════════════════════════════════"

# Backup current config
echo "[1/4] Creating backup..."
cp "$NGINX_CONF" "$BACKUP"
echo "✅ Backup: $BACKUP"

# Add location block after /sites/ location
echo "[2/4] Adding location /mail/ block..."

# Find line number of /sites/ location closing brace
LINE_NUM=$(grep -n "location \^~ /sites/" "$NGINX_CONF" | cut -d: -f1)

if [ -z "$LINE_NUM" ]; then
  echo "❌ Could not find /sites/ location block"
  exit 1
fi

# Add location block after /sites/ closing brace
sed -i "${LINE_NUM}a\\
\\
    # ══════════════════════════════════════════════════════════\\
    # W-MAIL-001 — SnappyMail WebUI (:8200)\\
    # ══════════════════════════════════════════════════════════\\
\\
    location ^~ /mail/ {\\
        proxy_pass http://127.0.0.1:8200/;\\
        proxy_http_version 1.1;\\
        proxy_set_header Host \$host;\\
        proxy_set_header X-Real-IP \$remote_addr;\\
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;\\
        proxy_set_header X-Forwarded-Proto \$scheme;\\
        add_header X-WINDI-Service \"w-mail-001\" always;\\
    }" "$NGINX_CONF"

echo "✅ Location block added"

# Test nginx config
echo "[3/4] Testing nginx configuration..."
nginx -t

if [ $? -eq 0 ]; then
  echo "✅ nginx config valid"
else
  echo "❌ nginx config invalid - restoring backup"
  cp "$BACKUP" "$NGINX_CONF"
  exit 1
fi

# Reload nginx
echo "[4/4] Reloading nginx..."
systemctl reload nginx
echo "✅ nginx reloaded"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ W-MAIL-001 SnappyMail Proxy Active"
echo ""
echo "Test access:"
echo "  curl -I https://windi-domain.com/mail/"
echo ""
echo "WebUI:"
echo "  https://windi-domain.com/mail/"
echo "═══════════════════════════════════════════════════════════════"
