#!/bin/bash
# Fix: correct the redirect pattern
# Run with: sudo bash /home/windi/fix-nginx-verify-docs.sh

NGINX_CONF="/etc/nginx/sites-enabled/windi-domain.com"

echo "🔧 Fixing redirect pattern..."

# Replace the broken redirect with correct one
sed -i 's|location \^~ /verify-public/docs/ {|location ~ ^/verify-public/docs/(.*)$ {|' "$NGINX_CONF"
sed -i 's|return 301 /verify-public/web/docs/\$request_uri;|return 301 /verify-public/web/docs/$1;|' "$NGINX_CONF"

echo "🧪 Testing nginx..."
nginx -t

if [ $? -eq 0 ]; then
    echo "🔄 Reloading nginx..."
    systemctl reload nginx
    echo "✅ Fixed!"
else
    echo "❌ Failed!"
fi
