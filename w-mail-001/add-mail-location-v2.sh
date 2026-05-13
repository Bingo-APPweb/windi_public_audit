#!/bin/bash
# Add W-MAIL-001 location block AFTER /sites/ closing brace (line 300)

set -e

NGINX_CONF="/etc/nginx/sites-enabled/windi-domain.com"
BACKUP="/opt/windi/backups/nginx/windi-domain.com.pre-mail-v2-$(date +%Y%m%d_%H%M%S)"

echo "═══════════════════════════════════════════════════════════════"
echo "Adding W-MAIL-001 location block (v2 - correct placement)"
echo "═══════════════════════════════════════════════════════════════"

# Backup
echo "[1/4] Creating backup..."
cp "$NGINX_CONF" "$BACKUP"
echo "✅ Backup: $BACKUP"

# Add location block AFTER line 300 (closing brace of /sites/)
echo "[2/4] Adding location /mail/ block after /sites/..."

sed -i '300a\
\
    # ══════════════════════════════════════════════════════════\
    # W-MAIL-001 — SnappyMail WebUI (:8200)\
    # ══════════════════════════════════════════════════════════\
\
    location ^~ /mail/ {\
        proxy_pass http://127.0.0.1:8200/;\
        proxy_http_version 1.1;\
        proxy_set_header Host $host;\
        proxy_set_header X-Real-IP $remote_addr;\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\
        proxy_set_header X-Forwarded-Proto $scheme;\
        add_header X-WINDI-Service "w-mail-001" always;\
    }' "$NGINX_CONF"

echo "✅ Location block added after line 300"

# Test
echo "[3/4] Testing nginx configuration..."
nginx -t

if [ $? -ne 0 ]; then
  echo "❌ nginx config invalid - restoring backup"
  cp "$BACKUP" "$NGINX_CONF"
  exit 1
fi

echo "✅ nginx config valid"

# Reload
echo "[4/4] Reloading nginx..."
systemctl reload nginx
echo "✅ nginx reloaded"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ W-MAIL-001 SnappyMail Proxy Active"
echo ""
echo "Test:"
echo "  curl -I https://windi-domain.com/mail/"
echo ""
echo "Access:"
echo "  https://windi-domain.com/mail/"
echo "  Login: postmaster@windisites.de"
echo "  Password: (from /opt/windi/w-mail-001/config/.admin-password)"
echo "═══════════════════════════════════════════════════════════════"
