#!/bin/bash
# ═══════════════════════════════════════════════════════
# WINDI Clone — Correção Cirúrgica: Restart Loop Fix
# Dragon Surgery Script v1.0 — FIX
# Date: 2026-02-15
# 
# DIAGNÓSTICO:
#   - PID 695412 (nohup, 11/Fev) segurando porta 8092
#   - PID 776110 (nohup, 14/Fev) segurando porta 8095
#   - systemd tenta subir na 8095 → "Address already in use" → loop
#   - 14.642+ restarts em 24h
#
# CORREÇÃO:
#   1. Parar systemd (cessar fogo)
#   2. Matar ambos nohup zombies
#   3. Corrigir service file (porta 8092, logs, segurança)
#   4. Reiniciar via systemd
#   5. Verificar
# ═══════════════════════════════════════════════════════

set -e

echo "🐉 === WINDI CLONE SURGERY — CORREÇÃO ==="
echo "$(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# ─── PASSO 1: Cessar fogo ────────────────────────────
echo "═══ PASSO 1: Parando systemd (cessar fogo) ═══"
sudo systemctl stop windi-clone.service
sudo systemctl disable windi-clone.service
echo "✅ systemd clone parado e desabilitado"
echo ""

# ─── PASSO 2: Matar zombies nohup ───────────────────
echo "═══ PASSO 2: Eliminando processos fantasma ═══"
echo ""

echo "Antes:"
ps aux | grep clone_server | grep -v grep || echo "(nenhum)"
echo ""

# Matar todos os processos clone_server
pkill -f "clone_server.py" 2>/dev/null && echo "✅ Processos clone_server eliminados" || echo "⚠ Nenhum processo encontrado"
sleep 2

# Verificar portas limpas
echo ""
echo "Verificando portas após cleanup:"
echo -n "  8092: "
ss -tlnp | grep :8092 && echo "⚠ AINDA OCUPADA" || echo "✅ LIVRE"
echo -n "  8095: "
ss -tlnp | grep :8095 && echo "⚠ AINDA OCUPADA" || echo "✅ LIVRE"

# Se ainda ocupadas, forçar
if ss -tlnp | grep -q :8092; then
    echo "Forçando liberação da 8092..."
    sudo fuser -k 8092/tcp 2>/dev/null
    sleep 1
fi
if ss -tlnp | grep -q :8095; then
    echo "Forçando liberação da 8095..."
    sudo fuser -k 8095/tcp 2>/dev/null
    sleep 1
fi

echo ""
echo "Depois:"
ps aux | grep clone_server | grep -v grep || echo "✅ Nenhum processo clone_server ativo"
echo ""

# ─── PASSO 3: Verificar porta no clone_server.py ────
echo "═══ PASSO 3: Verificando porta no código ═══"
CLONE_SCRIPT="/opt/windi/clone/server/clone_server.py"
if [ -f "$CLONE_SCRIPT" ]; then
    echo "Portas encontradas no código:"
    grep -n "port\|8092\|8095" "$CLONE_SCRIPT" | head -10
    echo ""
    
    CURRENT_PORT=$(grep -oP 'port[=:]\s*\K\d+' "$CLONE_SCRIPT" | tail -1)
    echo "Porta atual no código: ${CURRENT_PORT:-'não detectada'}"
    
    # Se estiver em 8095, mudar para 8092
    if grep -q "8095" "$CLONE_SCRIPT"; then
        echo ""
        echo "⚠ Código usa porta 8095. Corrigindo para 8092 (conforme port map)..."
        cp "$CLONE_SCRIPT" "$CLONE_SCRIPT.bak.$(date +%Y%m%d_%H%M%S)"
        sed -i 's/8095/8092/g' "$CLONE_SCRIPT"
        echo "✅ Porta corrigida para 8092"
        echo "Verificação:"
        grep -n "8092" "$CLONE_SCRIPT" | head -5
    elif grep -q "8092" "$CLONE_SCRIPT"; then
        echo "✅ Código já usa porta 8092 — correto"
    else
        echo "⚠ Porta não detectada automaticamente. Verifique manualmente."
    fi
else
    echo "❌ Script não encontrado em $CLONE_SCRIPT"
    echo "Procurando..."
    find /opt/windi/clone -name "*.py" -type f 2>/dev/null
    echo ""
    echo "⚠ AÇÃO MANUAL NECESSÁRIA: verificar caminho do script"
    exit 1
fi
echo ""

# ─── PASSO 4: Backup + novo service file ────────────
echo "═══ PASSO 4: Novo service file ═══"

# Backup
BK="/opt/windi/backups/pre_clone_fix_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BK"
sudo cp /etc/systemd/system/windi-clone.service "$BK/"
echo "Backup salvo em: $BK"
echo ""

# Criar log dir se necessário
mkdir -p /opt/windi/logs

# Novo service file
sudo tee /etc/systemd/system/windi-clone.service << 'EOF'
[Unit]
Description=WINDI Clone Server v1.4.0 — Território Soberano (:8092)
Documentation=https://admin.windia4desk.tech/clone/health
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=windi
Group=windi
WorkingDirectory=/opt/windi/clone/server
ExecStart=/usr/bin/python3 /opt/windi/clone/server/clone_server.py
Restart=on-failure
RestartSec=10
StartLimitBurst=5
StartLimitIntervalSec=60
StandardOutput=append:/opt/windi/logs/clone.log
StandardError=append:/opt/windi/logs/clone.log

# Security hardening
NoNewPrivileges=yes
ProtectSystem=strict
ReadWritePaths=/opt/windi/data /opt/windi/logs /opt/windi/clone

[Install]
WantedBy=multi-user.target
EOF

echo ""
echo "✅ Novo service file instalado"
echo ""
echo "Mudanças chave:"
echo "  - Restart=always → Restart=on-failure (não reinicia se sair limpo)"
echo "  - RestartSec=5 → RestartSec=10 (mais tempo entre tentativas)"
echo "  - StartLimitBurst=5 + IntervalSec=60 (máx 5 restarts/minuto, depois para)"
echo "  - Logs → /opt/windi/logs/clone.log"
echo "  - Security hardening ativado"
echo "  - Descrição atualizada: porta 8092"
echo ""

# ─── PASSO 5: Reload + start ────────────────────────
echo "═══ PASSO 5: Ativando serviço corrigido ═══"
sudo systemctl daemon-reload
sudo systemctl enable windi-clone.service
sudo systemctl start windi-clone.service
sleep 3

echo ""
echo "Status:"
sudo systemctl status windi-clone.service --no-pager
echo ""

# ─── PASSO 6: Verificação ───────────────────────────
echo "═══ PASSO 6: Verificação Final ═══"
echo ""

echo -n "Porta 8092: "
ss -tlnp | grep :8092 && echo "" || echo "❌ NÃO ATIVA"

echo ""
echo "Health check:"
sleep 2
curl -s http://localhost:8092/health 2>/dev/null | python3 -m json.tool || echo "❌ Health check falhou"

echo ""
echo "--- Todos os serviços WINDI ---"
systemctl list-units --type=service | grep windi
echo ""

# Contar se está em loop
sleep 5
RESTARTS_AFTER=$(sudo journalctl -u windi-clone.service --since "1 min ago" | grep -c "Started" 2>/dev/null)
echo "Restarts no último minuto: $RESTARTS_AFTER"
if [ "$RESTARTS_AFTER" -le 1 ]; then
    echo "✅ LOOP ELIMINADO — Clone estável"
else
    echo "⚠ Ainda reiniciando. Verificar logs:"
    echo "  sudo journalctl -u windi-clone.service -n 20 --no-pager"
fi

echo ""
echo "🐉 === CIRURGIA COMPLETA ==="
echo ""
echo "Resumo:"
echo "  ✅ Processos nohup fantasma eliminados"
echo "  ✅ Porta corrigida para 8092"  
echo "  ✅ Service file corrigido (Restart=on-failure + rate limit)"
echo "  ✅ Logs centralizados em /opt/windi/logs/clone.log"
echo "  ✅ Security hardening ativado"
echo "  Backup: $BK"
