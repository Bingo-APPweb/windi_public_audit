#!/bin/bash
# Patch nginx to add /wallet/ UI route
# Run: sudo bash /opt/windi/patch-nginx-wallet.sh

set -e

CONF="/etc/nginx/sites-enabled/windi-domain.com"
BACKUP="/opt/windi/nginx-backup-wallet-$(date +%Y%m%d_%H%M%S).conf"

echo "[1/4] Backup..."
cp "$CONF" "$BACKUP"
echo "      → $BACKUP"

echo "[2/4] Adding /wallet/ UI route..."
sed -i '/location \^~ \/api\/wallet\/ {/,/^    }$/{
    /^    }$/a\
\
    # ── Wallet UI (:8099) ─────────────────────────────────\
    location ^~ /wallet/ {\
        proxy_pass http://windi_wallet/;\
        proxy_http_version 1.1;\
        proxy_set_header Host $host;\
        proxy_set_header X-Real-IP $remote_addr;\
    }
}' "$CONF"

echo "[3/4] Testing nginx config..."
nginx -t

echo "[4/4] Reloading nginx..."
systemctl reload nginx

echo ""
echo "✅ /wallet/ route added"
echo "   Test: curl -s https://windi-domain.com/wallet/ | head -5"
