#!/bin/bash
# ============================================================
# WINDI CLEANUP — PRIORIDADE ALTA
# Data: 2026-03-13 | Gerado por: Architect
# Princípio: READ FIRST → PROPOSE → EXECUTE
# ============================================================

set -e
echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║     WINDI CLEANUP — PRIORIDADE ALTA                  ║"
echo "║     3 ações: Logrotate | Backup dup | DBs vazias     ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# ── AÇÃO 1: LOGROTATE ────────────────────────────────────────
echo "▶ [1/3] Configurando logrotate para /opt/windi/logs/..."

# Verificar estado atual
echo "  📊 Tamanho atual dos logs:"
du -sh /opt/windi/logs/*.log 2>/dev/null | sort -rh | head -10

# Criar config logrotate
sudo tee /etc/logrotate.d/windi > /dev/null << 'EOF'
/opt/windi/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    size 50M
    copytruncate
    dateext
    dateformat -%Y%m%d
}
EOF

echo "  ✅ Config criada: /etc/logrotate.d/windi"

# Forçar rotação agora nos logs críticos (>100MB)
echo "  🔄 Rotacionando logs grandes imediatamente..."
sudo logrotate -f /etc/logrotate.d/windi 2>/dev/null && echo "  ✅ Rotação executada" || echo "  ⚠️  Rotação adiada (será automática amanhã)"

# Verificar resultado
echo "  📊 Tamanho após rotação:"
du -sh /opt/windi/logs/*.log 2>/dev/null | sort -rh | head -10

echo ""

# ── AÇÃO 2: REMOVER BACKUP DUPLICADO ─────────────────────────
echo "▶ [2/3] Verificando backup duplicado forensic_ledger..."

SQLITE_ORIG="/opt/windi/backups/forensic_ledger_20260305_143541.sqlite3"
GZ_FILE=$(ls /opt/windi/backups/forensic_ledger*.gz 2>/dev/null | head -1)

echo "  📁 Original: $SQLITE_ORIG"
echo "  📦 Comprimido: $GZ_FILE"

if [ -f "$SQLITE_ORIG" ] && [ -f "$GZ_FILE" ]; then
    ORIG_SIZE=$(du -sh "$SQLITE_ORIG" | cut -f1)
    GZ_SIZE=$(du -sh "$GZ_FILE" | cut -f1)
    echo ""
    echo "  ⚠️  CONFIRMAÇÃO NECESSÁRIA:"
    echo "     Original ($ORIG_SIZE): $SQLITE_ORIG"
    echo "     .gz mantido ($GZ_SIZE): $GZ_FILE"
    echo ""
    read -p "  Remover original? [s/N] " CONFIRM_SQLITE
    if [[ "$CONFIRM_SQLITE" =~ ^[Ss]$ ]]; then
        rm "$SQLITE_ORIG"
        echo "  ✅ Original removido. .gz preservado."
        echo "  💾 Espaço liberado: ~$ORIG_SIZE"
    else
        echo "  ⏩ Pulado."
    fi
elif [ ! -f "$SQLITE_ORIG" ]; then
    echo "  ✅ Original já removido (ou path diferente)."
    echo "  📋 Listando backups existentes:"
    ls -lh /opt/windi/backups/ 2>/dev/null
else
    echo "  ⚠️  .gz não encontrado — NÃO removendo original (segurança)."
    echo "  📋 Estado atual dos backups:"
    ls -lh /opt/windi/backups/ 2>/dev/null
fi

echo ""

# ── AÇÃO 3: REMOVER DBs VAZIAS ────────────────────────────────
echo "▶ [3/3] Identificando e removendo databases vazias..."

echo "  🔍 DBs com 0 bytes encontradas:"
EMPTY_DBS=$(find /opt/windi -name "*.db" -size 0 2>/dev/null)

if [ -z "$EMPTY_DBS" ]; then
    echo "  ✅ Nenhuma DB vazia encontrada."
else
    echo "$EMPTY_DBS" | while read db; do
        echo "     - $db"
    done
    echo ""
    echo "  ⚠️  CONFIRMAÇÃO NECESSÁRIA:"
    echo "     Serão removidas: $(echo "$EMPTY_DBS" | wc -l) arquivos"
    read -p "  Remover todas? [s/N] " CONFIRM_DBS
    if [[ "$CONFIRM_DBS" =~ ^[Ss]$ ]]; then
        echo "$EMPTY_DBS" | while read db; do
            rm "$db"
            echo "  🗑️  Removido: $db"
        done
        echo "  ✅ DBs vazias removidas."
    else
        echo "  ⏩ Pulado."
    fi
fi

echo ""

# ── RELATÓRIO FINAL ───────────────────────────────────────────
echo "╔══════════════════════════════════════════════════════╗"
echo "║     RELATÓRIO PÓS-LIMPEZA                            ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
echo "📊 Disco atual:"
df -h /opt/windi 2>/dev/null || df -h /

echo ""
echo "📁 Logs top 5:"
du -sh /opt/windi/logs/*.log 2>/dev/null | sort -rh | head -5

echo ""
echo "📦 Backups:"
du -sh /opt/windi/backups/* 2>/dev/null | sort -rh

echo ""
echo "✅ Limpeza Prioridade Alta concluída."
echo "📌 Próximo: Prioridade Média (comprimir snapshot + git gc)"
echo ""
echo "OM SHANTI 🐉"
