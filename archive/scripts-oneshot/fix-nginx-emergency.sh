#!/bin/bash
# Emergency fix - remove misplaced locations
NGINX_CONF="/etc/nginx/sites-enabled/windi-domain.com"

echo "🚨 Emergency nginx fix..."

# Remove lines 497-512 (the misplaced locations)
sed -i '497,512d' "$NGINX_CONF"

echo "🧪 Testing nginx..."
nginx -t && echo "✅ Config OK" || echo "❌ Still broken"

echo "🔄 Reloading nginx..."
systemctl reload nginx && echo "✅ Nginx reloaded" || echo "❌ Reload failed"
