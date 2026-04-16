#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# WINDI-LAW Smoke Test Fix — B3: Add /api/verify/ to nginx
# Run with: sudo bash /home/windi/patch-nginx-verify.sh
# ═══════════════════════════════════════════════════════════════

set -e

NGINX_CONF="/etc/nginx/sites-enabled/windi-domain.com"
BACKUP="${NGINX_CONF}.bak-$(date +%Y%m%d_%H%M%S)"

echo "📦 Creating backup: $BACKUP"
cp "$NGINX_CONF" "$BACKUP"

echo "🔧 Adding /api/verify/ location..."

# Insert after /api/receipts/ block
sed -i '/location \^~ \/api\/receipts\/ {/,/^    }$/{
    /^    }$/a\
\
    # ── Forensic Ledger Verify API ───────────────────────────\
    location ^~ /api/verify/ {\
        proxy_pass http://windi_ledger/api/verify/;\
        proxy_http_version 1.1;\
    }
}' "$NGINX_CONF"

echo "🧪 Testing nginx config..."
nginx -t

echo "🔄 Reloading nginx..."
systemctl reload nginx

echo "✅ Done! /api/verify/ is now exposed."
echo "📍 Test: curl https://windi-domain.com/api/verify/WINDI-LAW-SMOKE-1774544561"
