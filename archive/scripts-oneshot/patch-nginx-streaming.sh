#!/bin/bash
# §137 — Nginx Streaming Patch for WINDI-LAW
# Execute: sudo bash /home/windi/patch-nginx-streaming.sh

set -e

NGINX_CONF="/etc/nginx/sites-enabled/windi-domain.com"
BACKUP="${NGINX_CONF}.bak_$(date +%Y%m%d_%H%M%S)"

echo "=== §137 Nginx Streaming Patch ==="
echo "Backup: $BACKUP"
cp "$NGINX_CONF" "$BACKUP"

# Adicionar o location de streaming ANTES do location /law/ genérico
sed -i '/# ── WINDI-LAW Identity Gate (:8122) — W-GATE-001/i\
    # ── §137 WINDI-LAW Streaming (SSE) ─────────────────────────\
    location ^~ /law/ai-draft/stream {\
        proxy_pass http://127.0.0.1:8122/ai-draft/stream;\
        proxy_http_version 1.1;\
        proxy_set_header Host $host;\
        proxy_set_header X-Real-IP $remote_addr;\
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\
        proxy_set_header X-Forwarded-Proto $scheme;\
        # SSE critical settings\
        proxy_buffering off;\
        proxy_cache off;\
        proxy_read_timeout 120s;\
        chunked_transfer_encoding on;\
    }\
' "$NGINX_CONF"

echo "Testing nginx config..."
nginx -t

echo "Reloading nginx..."
systemctl reload nginx

echo "✅ §137 Nginx Streaming patch applied!"
echo "Test with: curl -N https://windi-domain.com/law/ai-draft/stream ..."
