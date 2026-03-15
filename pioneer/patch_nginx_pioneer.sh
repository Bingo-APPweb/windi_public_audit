#!/bin/bash
# WINDI Pioneer nginx patch — 2026-03-15
# Substitui proxy :8120 (morto) por alias estático

set -e

NGINX_CONF="/etc/nginx/sites-enabled/windi-domain.com"
BACKUP_DIR="/opt/windi/backups"
BACKUP_FILE="${BACKUP_DIR}/nginx_windi_$(date +%Y%m%d_%H%M).conf"

echo "═══════════════════════════════════════════════════════════════"
echo "  WINDI Pioneer — nginx patch"
echo "═══════════════════════════════════════════════════════════════"

# 1. Backup
echo "[1/4] Backup..."
mkdir -p "$BACKUP_DIR"
cp "$NGINX_CONF" "$BACKUP_FILE"
echo "      ✅ $BACKUP_FILE"

# 2. Patch
echo "[2/4] Aplicando patch..."
python3 << 'PYEOF'
import re

conf_path = "/etc/nginx/sites-enabled/windi-domain.com"

with open(conf_path, 'r') as f:
    content = f.read()

old_block = '''    # ── Pioneer Program Landing (:8120) ────────────────────
    location /pioneer/ {
        proxy_pass http://windi_pioneer/pioneer/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 30s;
        proxy_connect_timeout 10s;
    }
    location /api/pioneer/ {
        proxy_pass http://windi_pioneer/api/pioneer/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    # ── END Pioneer Program ────────────────────────────────'''

new_block = '''    # ── Pioneer Pages — HTML estático ────────────────────────
    location /pioneer/florianopolis/ {
        alias /opt/windi/pioneer/florianopolis/;
        index index.html;
        try_files $uri $uri/ =404;
        add_header Cache-Control "public, max-age=3600";
    }

    location /pioneer/ {
        alias /opt/windi/pioneer/;
        index index.html;
        try_files $uri $uri/ =404;
        add_header Cache-Control "public, max-age=3600";
    }
    # ── END Pioneer Pages ──────────────────────────────────'''

if old_block in content:
    content = content.replace(old_block, new_block)
    with open(conf_path, 'w') as f:
        f.write(content)
    print("      ✅ Patch aplicado")
else:
    print("      ❌ Bloco não encontrado — verificar manualmente")
    exit(1)
PYEOF

# 3. Test
echo "[3/4] Testando nginx..."
nginx -t
echo "      ✅ nginx test passed"

# 4. Reload
echo "[4/4] Recarregando nginx..."
systemctl reload nginx
echo "      ✅ nginx reloaded"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  ✅ PATCH COMPLETO"
echo "  /pioneer/              → alias estático"
echo "  /pioneer/florianopolis/ → certificado trilíngue"
echo "═══════════════════════════════════════════════════════════════"
