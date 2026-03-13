#!/bin/bash
# ============================================================
# WINDI — INVESTIGAÇÃO PIDs SUSPEITOS
# PIDs: 620886 (sanctuary_api.py) + 687305 (forensic_validate_handwritten.py)
# Princípio: READ FIRST. Nunca kill sem confirmar.
# ============================================================

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║  INVESTIGAÇÃO PIDs SUSPEITOS                        ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

investigate_pid() {
    local PID=$1
    local LABEL=$2

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  🔍 PID $PID — $LABEL"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # Verificar se PID ainda existe
    if ! kill -0 "$PID" 2>/dev/null; then
        echo "  ⚠️  PID $PID não existe mais (já morreu ou foi reciclado)"
        echo ""
        # Tentar encontrar por nome do script
        NAME=$(echo "$LABEL" | sed 's/.*(\(.*\))/\1/' || echo "$LABEL")
        echo "  🔍 Buscando por nome do processo..."
        ps aux | grep -v grep | grep "$NAME" | head -5 || echo "  Não encontrado."
        echo ""
        return
    fi

    # Processo completo
    echo "  📋 Processo completo:"
    ps aux | grep "^[^ ]* *$PID " | grep -v grep

    echo ""

    # Uptime do processo
    echo "  ⏱️  Tempo rodando:"
    ps -p "$PID" -o pid,etime,cmd --no-headers 2>/dev/null || echo "  N/A"

    echo ""

    # Porta(s) que o PID ocupa
    echo "  🔌 Portas abertas por este PID:"
    PORT_INFO=$(ss -tlnp 2>/dev/null | grep "pid=$PID,")
    if [ -n "$PORT_INFO" ]; then
        echo "$PORT_INFO" | awk '{print "    " $0}'
    else
        echo "  ⚠️  Sem porta aberta — não está servindo requests"
        echo "  → Candidato a zumbi/script em loop"
    fi

    echo ""

    # Arquivo sendo executado
    echo "  📁 Script/arquivo executado:"
    ls -la /proc/$PID/exe 2>/dev/null | awk '{print "  " $NF}' || echo "  N/A"

    echo ""

    # Working directory
    echo "  📂 Working directory:"
    ls -la /proc/$PID/cwd 2>/dev/null | awk '{print "  " $NF}' || echo "  N/A"

    echo ""

    # Chamado por quem (parent PID)
    echo "  👆 Parent process:"
    PPID=$(ps -p "$PID" -o ppid --no-headers 2>/dev/null | tr -d ' ')
    if [ -n "$PPID" ] && [ "$PPID" != "0" ]; then
        ps aux | grep "^[^ ]* *$PPID " | grep -v grep | awk '{print "  PPID=" $2 " CMD=" substr($0, index($0,$11))}'
    else
        echo "  PPID não encontrado"
    fi

    echo ""

    # Uso de CPU nos últimos momentos
    echo "  📊 CPU/MEM atual:"
    ps -p "$PID" -o pid,%cpu,%mem,vsz,rss --no-headers 2>/dev/null \
        | awk '{printf "  CPU: %s%%  MEM: %s%%  VSZ: %s KB  RSS: %s KB\n", $2, $3, $4, $5}'

    echo ""

    # Verifica se há systemd unit associada
    echo "  🔧 Serviço systemd associado:"
    systemctl status "$PID" 2>/dev/null | head -3 || echo "  Nenhum (nohup ou script avulso)"

    echo ""
}

# ── PID 1: sanctuary_api.py ───────────────────────────────────
investigate_pid 620886 "sanctuary_api.py"

# ── PID 2: forensic_validate_handwritten.py ──────────────────
investigate_pid 687305 "forensic_validate_handwritten.py"

# ── VEREDICTO ─────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║  MATRIZ DE DECISÃO                                   ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
echo "  Para cada PID, o veredicto baseia-se em:"
echo ""
echo "  🔴 KILL seguro se:"
echo "     - Sem porta aberta (não serve requests)"
echo "     - Working dir em path descontinuado/legacy"
echo "     - Parent = bash/nohup sem systemd"
echo "     - Uptime longo sem actividade conhecida"
echo ""
echo "  🟡 INVESTIGAR MAIS se:"
echo "     - Porta aberta mas não documentada"
echo "     - Parent é o constitutional-agent"
echo ""
echo "  ✅ MANTER se:"
echo "     - Porta conhecida e activa"
echo "     - Chamado por serviço systemd"
echo ""
echo "  ─────────────────────────────────────────────────────"
echo "  COMANDO DE KILL (só executar após veredicto HUMANO):"
echo ""
echo "  # sanctuary_api.py"
echo "  kill 620886 && echo 'sanctuary_api killed'"
echo ""
echo "  # forensic_validate_handwritten.py"
echo "  kill 687305 && echo 'forensic_validate killed'"
echo ""
echo "  # Confirmar que não voltaram:"
echo "  sleep 3 && ps aux | grep -E 'sanctuary|forensic_validate' | grep -v grep"
echo ""
echo "OM SHANTI 🐉"
