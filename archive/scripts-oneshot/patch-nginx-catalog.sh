#!/bin/bash
# Patch nginx para adicionar rota /catalog/
# Execução: sudo bash /home/windi/patch-nginx-catalog.sh

set -e

NGINX_CONF="/etc/nginx/sites-enabled/windi-domain.com"
BACKUP="/etc/nginx/sites-enabled/windi-domain.com.bak-catalog-$(date +%Y%m%d_%H%M%S)"

echo "=== WINDI Catalog Nginx Patch ==="
echo ""

# Backup
cp "$NGINX_CONF" "$BACKUP"
echo "✓ Backup: $BACKUP"

# Verificar se já existe
if grep -q "windi-catalog" "$NGINX_CONF"; then
    echo "⚠ Rota /catalog/ já existe"
    exit 0
fi

# Adicionar rota após nomad-upload
sed -i '/add_header X-WINDI-Service "nomad-upload-pwa" always;/a\
    }\
\
    # ═══ WINDI Catalog (Maio 2026) ═══\
    location = /catalog/ {\
        alias /opt/windi/nomad-pwa/;\
        try_files catalog.html =404;\
        add_header Cache-Control "no-cache";\
        add_header X-WINDI-Service "windi-catalog" always;' "$NGINX_CONF"

# Corrigir a chaveta extra
sed -i '/X-WINDI-Service "nomad-upload-pwa"/,/X-WINDI-Service "windi-catalog"/{/^    }$/d}' "$NGINX_CONF"

echo "✓ Rota /catalog/ adicionada"

# Testar configuração
echo ""
echo "Testando nginx..."
nginx -t

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Configuração válida"
    echo ""
    echo "Recarregando nginx..."
    systemctl reload nginx
    echo "✓ Nginx recarregado"
    echo ""
    echo "=== DEPLOY COMPLETO ==="
    echo "URL: https://windi-domain.com/catalog/"
else
    echo "❌ Erro na configuração. Restaurando backup..."
    cp "$BACKUP" "$NGINX_CONF"
    exit 1
fi
