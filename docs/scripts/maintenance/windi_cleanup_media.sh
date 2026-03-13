#!/bin/bash
# ============================================================
# WINDI CLEANUP — PRIORIDADE MÉDIA
# Data: 2026-03-13 | Gerado por: Architect
# Ações: Comprimir snapshot 78MB + git gc + serviços mortos
# ============================================================

set -e
echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║     WINDI CLEANUP — PRIORIDADE MÉDIA                 ║"
echo "║     Snapshot compress | git gc | serviços mortos     ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# ── AÇÃO 4: COMPRIMIR SNAPSHOT ────────────────────────────────
echo "▶ [1/3] Comprimindo ledger_snapshot_20260305..."

SNAPSHOT_DIR="/opt/windi/backups/ledger_snapshot_20260305_060802"
SNAPSHOT_TAR="/opt/windi/backups/ledger_snapshot_20260305.tar.gz"

if [ -d "$SNAPSHOT_DIR" ]; then
    BEFORE=$(du -sh "$SNAPSHOT_DIR" | cut -f1)
    echo "  📁 Diretório encontrado: $SNAPSHOT_DIR ($BEFORE)"
    echo "  🗜️  Comprimindo → $SNAPSHOT_TAR"
    echo "  ⏳ Aguarde (78MB pode levar ~10s)..."

    cd /opt/windi/backups
    tar -czf ledger_snapshot_20260305.tar.gz ledger_snapshot_20260305_060802/

    if [ -f "$SNAPSHOT_TAR" ]; then
        AFTER=$(du -sh "$SNAPSHOT_TAR" | cut -f1)
        echo "  ✅ .tar.gz criado: $AFTER"
        echo ""
        echo "  ⚠️  CONFIRMAÇÃO — remover diretório original?"
        echo "     De: $BEFORE → Para: $AFTER"
        read -p "  Remover $SNAPSHOT_DIR? [s/N] " CONFIRM_SNAP
        if [[ "$CONFIRM_SNAP" =~ ^[Ss]$ ]]; then
            rm -rf "$SNAPSHOT_DIR"
            echo "  ✅ Diretório removido. Espaço recuperado."
        else
            echo "  ⏩ Diretório mantido. .tar.gz também mantido."
        fi
    else
        echo "  ❌ ERRO: .tar.gz não foi criado. Diretório preservado."
    fi
elif [ -f "$SNAPSHOT_TAR" ]; then
    echo "  ✅ Snapshot já comprimido: $SNAPSHOT_TAR"
    du -sh "$SNAPSHOT_TAR"
else
    echo "  🔍 Buscando snapshot em /opt/windi/backups/..."
    ls -lh /opt/windi/backups/ 2>/dev/null
    echo "  ⚠️  Path não encontrado. Verifique acima e ajuste manualmente."
fi

echo ""

# ── AÇÃO 5: GIT GC ────────────────────────────────────────────
echo "▶ [2/3] Executando git gc --aggressive em /opt/windi..."

if [ -d "/opt/windi/.git" ]; then
    echo "  📊 Git objects antes:"
    du -sh /opt/windi/.git/objects 2>/dev/null

    echo "  ⏳ git gc --aggressive (pode levar 1-2 min)..."
    cd /opt/windi
    git gc --aggressive --prune=now 2>&1 | tail -5

    echo ""
    echo "  📊 Git objects depois:"
    du -sh /opt/windi/.git/objects 2>/dev/null
    echo "  ✅ git gc concluído."
else
    echo "  ⚠️  /opt/windi não é um repositório git."
    echo "  🔍 Procurando repos git em /opt/windi/..."
    find /opt/windi -maxdepth 2 -name ".git" -type d 2>/dev/null | while read gitdir; do
        REPO=$(dirname "$gitdir")
        SIZE=$(du -sh "$gitdir/objects" 2>/dev/null | cut -f1)
        echo "     📁 $REPO (objects: $SIZE)"
    done
    echo ""
    echo "  Cole o path correto e execute:"
    echo "  cd /opt/windi/<repo> && git gc --aggressive --prune=now"
fi

echo ""

# ── AÇÃO 6: AUDITORIA SERVIÇOS MORTOS ────────────────────────
echo "▶ [3/3] Auditando serviços DEAD/NOT-FOUND..."

DEAD_SERVICES=(
    "windi-distribution-engine"
    "windi-guard"
    "windi-jmpg-export"
    "windi-preview-cleaner"
    "windi-forensic-ledger"
)

echo "  Estado atual:"
echo ""
printf "  %-35s %-15s %-30s\n" "SERVIÇO" "ESTADO" "UNIT FILE"
printf "  %-35s %-15s %-30s\n" "-------" "------" "---------"

for svc in "${DEAD_SERVICES[@]}"; do
    STATUS=$(systemctl is-active "$svc" 2>/dev/null || echo "not-found")
    UNIT_FILE=$(systemctl show "$svc" --property=FragmentPath 2>/dev/null | cut -d= -f2)
    if [ -z "$UNIT_FILE" ]; then
        UNIT_FILE="(sem unit file)"
    fi
    printf "  %-35s %-15s %-30s\n" "$svc" "$STATUS" "$UNIT_FILE"
done

echo ""
echo "  📋 RECOMENDAÇÃO POR SERVIÇO:"
echo ""
echo "  windi-distribution-engine → Verificar se foi substituído pelo Communiqué Engine (:8105)"
echo "  windi-guard               → Verificar se função foi absorvida pelo Constitutional Agent (:8091)"
echo "  windi-jmpg-export         → JMPG Viewer (:8104) está healthy — pode ser legacy"
echo "  windi-preview-cleaner     → Verificar cronjob alternativo"
echo "  windi-forensic-ledger     → Forensic Ledger (:8101) roda em outro processo — unit órfão?"
echo ""
echo "  ⚠️  NÃO removendo unit files automaticamente."
echo "  Para remover um serviço morto (após confirmar irrelevância):"
echo ""
echo "  sudo systemctl disable windi-<nome>"
echo "  sudo rm /etc/systemd/system/windi-<nome>.service"
echo "  sudo systemctl daemon-reload"
echo ""

# ── RELATÓRIO FINAL ───────────────────────────────────────────
echo "╔══════════════════════════════════════════════════════╗"
echo "║     RELATÓRIO PÓS PRIORIDADE MÉDIA                   ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
echo "📊 Disco total /opt/windi:"
du -sh /opt/windi 2>/dev/null

echo ""
echo "📦 Backups:"
du -sh /opt/windi/backups/* 2>/dev/null | sort -rh

echo ""
echo "📁 Logs top 5 (pós-logrotate):"
du -sh /opt/windi/logs/*.log 2>/dev/null | sort -rh | head -5

echo ""
echo "┌─────────────────────────────────────────┬────────────┐"
echo "│ Economia Total Estimada (P.Alta+P.Média) │   ~650 MB  │"
echo "└─────────────────────────────────────────┴────────────┘"
echo ""
echo "📌 PENDENTE (do sudo manual):"
echo "   sudo tee /etc/logrotate.d/windi + sudo logrotate -f → ~500 MB"
echo ""
echo "✅ Prioridade Média concluída."
echo "📌 Próximo opcional: node_modules dedup (pnpm workspaces) — P.Baixa"
echo ""
echo "OM SHANTI 🐉"
