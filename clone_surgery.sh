#!/bin/bash
# ═══════════════════════════════════════════════════════
# WINDI Clone — Operação Cirúrgica: Restart Loop Fix
# Dragon Surgery Script v1.0
# Date: 2026-02-15
# ═══════════════════════════════════════════════════════

echo "🐉 === WINDI CLONE SURGERY — DIAGNÓSTICO ==="
echo "$(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# ─── PASSO 1: Snapshot do estado atual ───────────────
echo "═══ PASSO 1: Estado Atual ═══"
echo ""
echo "--- Uptime ---"
uptime
echo ""

echo "--- systemd services ---"
systemctl list-units --type=service | grep windi
echo ""

echo "--- Porta 8092 ---"
ss -tlnp | grep 8092
echo ""

# ─── PASSO 2: Service file (a verdade) ──────────────
echo "═══ PASSO 2: Service File (Verbatim) ═══"
echo ""
cat /etc/systemd/system/windi-clone.service
echo ""

# ─── PASSO 3: Journal logs (últimas 50 linhas) ──────
echo "═══ PASSO 3: Journal do Clone (últimas 50) ═══"
echo ""
sudo journalctl -u windi-clone.service -n 50 --no-pager 2>&1
echo ""

# ─── PASSO 4: Restart count ─────────────────────────
echo "═══ PASSO 4: Contagem de Restarts ═══"
echo ""
echo "Restarts nas últimas 24h:"
sudo journalctl -u windi-clone.service --since "24h ago" | grep -c "Started\|Stopped\|Main process exited" 2>&1
echo ""
echo "Últimas 10 transições:"
sudo journalctl -u windi-clone.service --since "24h ago" | grep -E "Started|Stopped|Main process exited|Deactivated|Failed" | tail -10
echo ""

# ─── PASSO 5: Log direto do clone ───────────────────
echo "═══ PASSO 5: Clone App Log ═══"
echo ""
if [ -f /opt/windi/logs/clone.log ]; then
    echo "Últimas 20 linhas de /opt/windi/logs/clone.log:"
    tail -20 /opt/windi/logs/clone.log
else
    echo "Arquivo /opt/windi/logs/clone.log não encontrado."
    echo "Procurando logs alternativos..."
    ls -la /opt/windi/clone/*.log 2>/dev/null || echo "Nenhum log local encontrado."
fi
echo ""

# ─── PASSO 6: Verificar o script principal ──────────
echo "═══ PASSO 6: Clone Entry Point ═══"
echo ""
echo "Conteúdo de /opt/windi/clone/ :"
ls -la /opt/windi/clone/*.py /opt/windi/clone/*.sh 2>/dev/null
echo ""
echo "Primeira e última linhas do script principal:"
for f in /opt/windi/clone/clone_server.py /opt/windi/clone/app.py /opt/windi/clone/main.py /opt/windi/clone/server.py; do
    if [ -f "$f" ]; then
        echo "--- $f ---"
        head -5 "$f"
        echo "..."
        tail -10 "$f"
        echo ""
    fi
done
echo ""

# ─── PASSO 7: Processos nohup fantasma ─────────────
echo "═══ PASSO 7: Processos Fantasma ═══"
echo ""
echo "Processos com 'clone' no nome:"
ps aux | grep -i clone | grep -v grep
echo ""
echo "Processos na porta 8092:"
sudo fuser 8092/tcp 2>&1 || echo "fuser não disponível ou porta livre"
echo ""

echo "🐉 === FIM DO DIAGNÓSTICO ==="
echo ""
echo "Copie TODA a saída acima e cole no chat."
echo "Com isso, faço a correção cirúrgica exata."
