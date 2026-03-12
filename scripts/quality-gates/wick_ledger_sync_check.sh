#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# WINDI Quality Gate: WICK → Ledger Sync Integrity
# W-SPEC-WICK-LEDGER-SYNC-001 — Section 5.2
#
# Verifica que todos os artifacts públicos no WICK Evidence Graph
# estão sincronizados com o Forensic Ledger.
#
# Exit codes:
#   0 = OK (todos sincronizados)
#   1 = FAIL (gap detectado, CI deve falhar)
#   2 = ERROR (DB inacessível)
#
# Uso:
#   bash wick_ledger_sync_check.sh          # Apenas verifica
#   bash wick_ledger_sync_check.sh --fix    # Verifica e corrige
#
# Autor: Human Dragon + Architect
# Data: 13.03.2026
# SPEC: W-SPEC-WICK-LEDGER-SYNC-001
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

# ── Configuração ──
WICK_DB="/opt/windi/agents/constitutional-agent/data/wick_agent.db"
LEDGER_DB="/opt/windi/data/forensic_ledger.sqlite3"
RESYNC_SCRIPT="/opt/windi/agents/constitutional-agent/tools/resync_public.py"
WICK_APP_NAME="wick-evidence-graph"  # app name usado no sync_to_ledger()

# ── Cores ──
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ── Funções ──
log_ok()   { echo -e "${GREEN}✓${NC} $1"; }
log_fail() { echo -e "${RED}✗${NC} $1"; }
log_warn() { echo -e "${YELLOW}⚠${NC} $1"; }
log_info() { echo -e "  $1"; }

header() {
    echo "═══════════════════════════════════════════════════════════════"
    echo "  WINDI Quality Gate: WICK → Ledger Sync"
    echo "  W-SPEC-WICK-LEDGER-SYNC-001"
    echo "═══════════════════════════════════════════════════════════════"
}

# ── Verifica DBs existem ──
check_databases() {
    if [[ ! -f "$WICK_DB" ]]; then
        log_fail "WICK DB não encontrado: $WICK_DB"
        exit 2
    fi
    if [[ ! -f "$LEDGER_DB" ]]; then
        log_fail "Ledger DB não encontrado: $LEDGER_DB"
        exit 2
    fi
    log_ok "Databases acessíveis"
}

# ── Conta artifacts ──
count_wick_public() {
    sqlite3 "$WICK_DB" "SELECT COUNT(*) FROM artifacts WHERE visibility='public'" 2>/dev/null
}

count_ledger_wick() {
    # Conta receipts com app='wick-evidence-graph' OU app='windi-wick'
    sqlite3 "$LEDGER_DB" "SELECT COUNT(*) FROM receipts WHERE app='$WICK_APP_NAME' OR app='windi-wick'" 2>/dev/null
}

# ── Lista IDs em falta ──
find_missing_ids() {
    # Retorna IDs que estão no WICK como public mas não no Ledger
    sqlite3 "$WICK_DB" "SELECT id FROM artifacts WHERE visibility='public'" 2>/dev/null | while read -r id; do
        EXISTS=$(sqlite3 "$LEDGER_DB" "SELECT COUNT(*) FROM receipts WHERE id='$id'" 2>/dev/null)
        if [[ "$EXISTS" -eq 0 ]]; then
            echo "$id"
        fi
    done
}

# ── Main ──
main() {
    local AUTO_FIX=false

    # Parse args
    if [[ "${1:-}" == "--fix" ]]; then
        AUTO_FIX=true
    fi

    header
    echo ""

    # Step 1: Verifica DBs
    check_databases

    # Step 2: Conta
    WICK_COUNT=$(count_wick_public)
    LEDGER_COUNT=$(count_ledger_wick)

    log_info "WICK public artifacts:  $WICK_COUNT"
    log_info "Ledger WICK receipts:   $LEDGER_COUNT"
    echo ""

    # Step 3: Verifica cada artifact público tem entrada no Ledger
    MISSING=$(find_missing_ids)
    if [[ -z "$MISSING" ]]; then
        MISSING_COUNT=0
    else
        MISSING_COUNT=$(echo "$MISSING" | wc -l | tr -d ' ')
    fi

    if [[ "$MISSING_COUNT" -eq 0 ]]; then
        log_ok "Sync OK — todos os $WICK_COUNT artifacts públicos estão no Ledger"
        echo ""
        echo "═══════════════════════════════════════════════════════════════"
        echo -e "  Status: ${GREEN}PASS${NC}"
        echo "═══════════════════════════════════════════════════════════════"
        exit 0
    fi

    # Step 4: Gap detectado
    log_fail "Gap detectado: $MISSING_COUNT artifacts públicos não estão no Ledger"
    echo ""

    # Lista IDs em falta
    log_warn "Artifacts em falta:"
    echo "$MISSING" | while read -r id; do
        [[ -n "$id" ]] && log_info "  - $id"
    done
    echo ""

    # Step 5: Auto-fix se pedido
    if [[ "$AUTO_FIX" == true ]]; then
        log_warn "Auto-fix activado — executando resync..."
        echo ""

        if [[ -f "$RESYNC_SCRIPT" ]]; then
            python3 "$RESYNC_SCRIPT"

            # Re-verifica
            echo ""
            MISSING_AFTER=$(find_missing_ids)
            if [[ -z "$MISSING_AFTER" ]]; then
                MISSING_COUNT_AFTER=0
            else
                MISSING_COUNT_AFTER=$(echo "$MISSING_AFTER" | wc -l | tr -d ' ')
            fi
            if [[ "$MISSING_COUNT_AFTER" -eq 0 ]]; then
                log_ok "Resync bem-sucedido — todos os $WICK_COUNT artifacts no Ledger"
                echo ""
                echo "═══════════════════════════════════════════════════════════════"
                echo -e "  Status: ${GREEN}PASS${NC} (após auto-fix)"
                echo "═══════════════════════════════════════════════════════════════"
                exit 0
            else
                log_fail "Resync falhou — ainda faltam $MISSING_COUNT_AFTER artifacts"
            fi
        else
            log_fail "Resync script não encontrado: $RESYNC_SCRIPT"
        fi
    fi

    # Step 6: Falha
    echo "═══════════════════════════════════════════════════════════════"
    echo -e "  Status: ${RED}FAIL${NC}"
    echo "  Gap: $MISSING_COUNT artifacts públicos não verificáveis"
    echo ""
    echo "  Para corrigir:"
    echo "    python3 $RESYNC_SCRIPT"
    echo "  Ou:"
    echo "    bash $0 --fix"
    echo "═══════════════════════════════════════════════════════════════"
    exit 1
}

main "$@"
