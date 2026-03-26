#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# WINDI Travel — Nginx Patch Script
# Adiciona bloco /travel/ ao windi-domain.com
# ═══════════════════════════════════════════════════════════════

set -e

NGINX_CONF="/etc/nginx/sites-enabled/windi-domain.com"
BACKUP="/opt/windi/backups/nginx-pre-travel-$(date +%Y%m%d_%H%M%S).conf"

echo "═══════════════════════════════════════════════════════════"
echo "WINDI Travel — Nginx Patch"
echo "═══════════════════════════════════════════════════════════"

# 1. Verificar se /travel/ já existe
if grep -q "location.*\/travel\/" "$NGINX_CONF"; then
    echo "✅ /travel/ já está configurado — nada a fazer"
    exit 0
fi

# 2. Backup
echo "[1/4] Backup..."
sudo cp "$NGINX_CONF" "$BACKUP"
echo "      → $BACKUP"

# 3. Criar bloco temporário
TRAVEL_BLOCK='
    # ═══ WINDI TRAVEL :8126 ═══
    location ^~ /travel/ {
        proxy_pass http://127.0.0.1:8126/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
'

# 4. Encontrar linha após /law/ block e inserir
echo "[2/4] Adicionando bloco /travel/..."

# Encontrar o número da linha onde /law/ termina (procura o } após location ^~ /law/)
LAW_LINE=$(grep -n "location \^~ /law/" "$NGINX_CONF" | head -1 | cut -d: -f1)

if [ -z "$LAW_LINE" ]; then
    echo "❌ Bloco /law/ não encontrado — a adicionar antes do primeiro location"
    # Fallback: adicionar antes do primeiro location
    sudo sed -i "/location \/ {/i\\
    # ═══ WINDI TRAVEL :8126 ═══\\
    location ^~ /travel/ {\\
        proxy_pass http://127.0.0.1:8126/;\\
        proxy_http_version 1.1;\\
        proxy_set_header Host \$host;\\
        proxy_set_header X-Real-IP \$remote_addr;\\
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;\\
        proxy_set_header X-Forwarded-Proto \$scheme;\\
    }\\
" "$NGINX_CONF"
else
    # Encontrar o } que fecha o bloco /law/ (próximo } após LAW_LINE)
    END_LINE=$(tail -n +$LAW_LINE "$NGINX_CONF" | grep -n "^[[:space:]]*}" | head -1 | cut -d: -f1)
    INSERT_LINE=$((LAW_LINE + END_LINE))

    echo "      Inserindo após linha $INSERT_LINE"

    sudo sed -i "${INSERT_LINE}a\\
\\
    # ═══ WINDI TRAVEL :8126 ═══\\
    location ^~ /travel/ {\\
        proxy_pass http://127.0.0.1:8126/;\\
        proxy_http_version 1.1;\\
        proxy_set_header Host \$host;\\
        proxy_set_header X-Real-IP \$remote_addr;\\
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;\\
        proxy_set_header X-Forwarded-Proto \$scheme;\\
    }" "$NGINX_CONF"
fi

# 5. Testar nginx
echo "[3/4] Testando nginx..."
if sudo nginx -t; then
    echo "      ✅ nginx -t OK"
else
    echo "      ❌ nginx -t FALHOU — restaurando backup"
    sudo cp "$BACKUP" "$NGINX_CONF"
    exit 1
fi

# 6. Reload
echo "[4/4] Recarregando nginx..."
sudo systemctl reload nginx

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "✅ PATCH COMPLETO"
echo "═══════════════════════════════════════════════════════════"
echo "Verificar: curl -s http://localhost:8126/health"
echo "Gate:      https://windi-domain.com/travel/gate"
echo "═══════════════════════════════════════════════════════════"
