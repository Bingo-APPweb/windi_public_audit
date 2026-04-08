#!/bin/bash
# W-SEC-001 — nginx patch script
# Run with: sudo bash /opt/windi/agents/security-sentinel/nginx-patch.sh

NGINX_CONF="/etc/nginx/sites-enabled/windi-domain.com"
BACKUP="/tmp/windi-domain.com.backup-sec-$(date +%Y%m%d_%H%M%S)"

echo "🔒 W-SEC-001 nginx patch"
echo "========================"

# Backup
cp "$NGINX_CONF" "$BACKUP"
echo "✅ Backup: $BACKUP"

# Check if route already exists
if grep -q "location /sec/" "$NGINX_CONF"; then
    echo "⚠️  Route /sec/ already exists"
    exit 0
fi

# Find insertion point (after END W-UDB-001)
LINE=$(grep -n "END W-UDB-001" "$NGINX_CONF" | head -1 | cut -d: -f1)

if [ -z "$LINE" ]; then
    echo "❌ Could not find insertion point (END W-UDB-001)"
    exit 1
fi

# Insert after that line
sed -i "${LINE}a\\
\\
    # ── W-SEC-001 Security Sentinel (:8144) ───────────────────\\
    location /sec/ {\\
        proxy_pass http://127.0.0.1:8144/;\\
        proxy_http_version 1.1;\\
        proxy_set_header Host \$host;\\
        proxy_set_header X-Real-IP \$remote_addr;\\
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;\\
        proxy_set_header X-Forwarded-Proto \$scheme;\\
        proxy_read_timeout 86400s;\\
        proxy_connect_timeout 10s;\\
        # SSE support\\
        proxy_buffering off;\\
        proxy_cache off;\\
        chunked_transfer_encoding off;\\
    }\\
    # ═══ END W-SEC-001 ═══" "$NGINX_CONF"

echo "✅ Route /sec/ added"

# Test nginx config
nginx -t
if [ $? -eq 0 ]; then
    echo "✅ nginx config valid"
    nginx -s reload
    echo "✅ nginx reloaded"
    echo ""
    echo "🎯 Dashboard available at:"
    echo "   https://windi-domain.com/sec/dashboard/"
else
    echo "❌ nginx config invalid — restoring backup"
    cp "$BACKUP" "$NGINX_CONF"
    exit 1
fi
