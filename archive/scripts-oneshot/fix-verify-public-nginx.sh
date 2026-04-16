#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# Fix /verify-public/ nginx path
# Run with: sudo bash /home/windi/fix-verify-public-nginx.sh
# ═══════════════════════════════════════════════════════════════

NGINX_CONF="/etc/nginx/sites-enabled/windi-domain.com"

echo "🔧 Adding /verify-public/web/ location to nginx..."

# Check if already exists
if grep -q "location /verify-public/web/" "$NGINX_CONF"; then
    echo "✅ Already exists"
    exit 0
fi

# Add after the viewer location using awk
awk '
/location \/verify-public\/viewer\/ \{/,/^\s*\}$/ {
    print
    if (/^\s*\}$/) {
        print ""
        print "    # ── Verify Public Web (static) ──────────────────────────"
        print "    location /verify-public/web/ {"
        print "        alias /opt/windi/verify-public/web/;"
        print "        index index.html;"
        print "        try_files $uri $uri/ =404;"
        print "        add_header Cache-Control \"public, max-age=3600\";"
        print "        add_header X-WINDI-Service \"verify-public-web\" always;"
        print "    }"
        print ""
        print "    # ── Verify Public Root redirect ────────────────────────"
        print "    location = /verify-public/ {"
        print "        return 301 /verify-public/web/;"
        print "    }"
        print "    location = /verify-public {"
        print "        return 301 /verify-public/web/;"
        print "    }"
    }
    next
}
{ print }
' "$NGINX_CONF" > /tmp/nginx-verify-fix.conf

mv /tmp/nginx-verify-fix.conf "$NGINX_CONF"

echo "🧪 Testing nginx..."
nginx -t

echo "🔄 Reloading nginx..."
systemctl reload nginx

echo "✅ Done!"
echo "📍 Test: curl https://windi-domain.com/verify-public/"
