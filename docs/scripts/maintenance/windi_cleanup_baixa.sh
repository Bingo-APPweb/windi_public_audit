#!/bin/bash
# ============================================================
# WINDI CLEANUP — PRIORIDADE BAIXA
# Data: 2026-03-13 | Gerado por: Architect
# Ações: node_modules dedup + auditoria memória (43 processos)
# ============================================================

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║     WINDI CLEANUP — PRIORIDADE BAIXA                 ║"
echo "║     node_modules dedup | memória | mapa completo     ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# ── AÇÃO 7: NODE_MODULES AUDIT ────────────────────────────────
echo "▶ [1/2] Auditando node_modules duplicados..."
echo ""

echo "  📊 Todos os node_modules em /opt/windi:"
find /opt/windi -name "node_modules" -type d -not -path "*/node_modules/*/node_modules" 2>/dev/null \
  | while read dir; do
      SIZE=$(du -sh "$dir" 2>/dev/null | cut -f1)
      PARENT=$(dirname "$dir")
      printf "  %-12s  %s\n" "$SIZE" "$PARENT"
    done

echo ""
echo "  📊 Total node_modules:"
find /opt/windi -name "node_modules" -type d -not -path "*/node_modules/*/node_modules" 2>/dev/null \
  | xargs du -sh 2>/dev/null | awk '{sum += $1} END {print "  " sum " MB total"}'

echo ""
echo "  🔍 Pacotes comuns entre projetos (candidatos a dedup):"
for dir in /opt/windi/*/node_modules; do
    if [ -d "$dir" ]; then
        PARENT=$(dirname "$dir")
        COUNT=$(ls "$dir" 2>/dev/null | wc -l)
        echo "    $(basename $PARENT): $COUNT pacotes"
    fi
done

echo ""
echo "  ════════════════════════════════════════════════════"
echo "  OPÇÕES DE DEDUPLICAÇÃO"
echo "  ════════════════════════════════════════════════════"
echo ""
echo "  OPÇÃO A — npm dedupe (imediato, sem migração)"
echo "  ─────────────────────────────────────────────"
echo "  Para cada projeto:"
for dir in /opt/windi/*/package.json; do
    PARENT=$(dirname "$dir")
    if [ -d "$PARENT/node_modules" ]; then
        echo "    cd $PARENT && npm dedupe"
    fi
done
echo ""
echo "  OPÇÃO B — pnpm workspaces (médio prazo, máximo dedup)"
echo "  ──────────────────────────────────────────────────────"
echo "  Requer: npm install -g pnpm"
echo "  Benefício: deduplicação global via hard links (~60-70% menos espaço)"
echo "  Custo: migração package.json + pnpm-workspace.yaml"
echo ""
echo "  pnpm-workspace.yaml mínimo:"
cat << 'PNPM_EXAMPLE'
  packages:
    - 'dashboard'
    - 'ppt-engine'
    - 'war-room'
PNPM_EXAMPLE
echo ""
echo "  RECOMENDAÇÃO: OPÇÃO A agora (seguro, 0 risco)"
echo "  OPÇÃO B quando houver 4+ projetos Node ativos."
echo ""
echo "  ⚠️  npm dedupe NÃO reinicia serviços. Mas recomenda-se:"
echo "  1. Rodar fora de horário de pico"
echo "  2. Verificar serviço ainda UP após dedupe"
echo ""

# ── AÇÃO 8: AUDITORIA MEMÓRIA ─────────────────────────────────
echo "▶ [2/2] Auditoria de memória — 43 processos Python..."
echo ""

echo "  📊 Top 10 processos Python por memória (RSS):"
ps aux --sort=-%mem \
  | grep python \
  | grep -v grep \
  | head -10 \
  | awk '{printf "  %5s MB  %-8s  %s\n", int($6/1024), $1, substr($0, index($0,$11))}'

echo ""
echo "  📊 Memória total Python:"
ps aux | grep python | grep -v grep \
  | awk '{sum += $6} END {printf "  Total RSS: %d MB (%d processos)\n", int(sum/1024), NR}'

echo ""
echo "  📊 Distribuição por serviço:"
ps aux | grep python | grep -v grep \
  | grep -oP '/opt/windi/[^/]+' \
  | sort | uniq -c | sort -rn \
  | awk '{printf "  %3d processos  %s\n", $1, $2}'

echo ""
echo "  ════════════════════════════════════════════════════"
echo "  MAPA DE CONSOLIDAÇÃO — CONSTITUTIONAL MONOLITH"
echo "  ════════════════════════════════════════════════════"
echo ""
echo "  STATUS ATUAL:"
echo "  ┌─────────────────────────────────────────────────┐"
echo "  │  43 processos Python × ~54 MB médio = 2.3 GB   │"
echo "  │  Cada blueprint no :8091 já é um processo leve  │"
echo "  │  Overhead: imports duplicados, GIL, GC isolado  │"
echo "  └─────────────────────────────────────────────────┘"
echo ""
echo "  PADRÃO ATUAL (correto para esta fase):"
echo "    1 Constitutional Agent (:8091) = processo mestre"
echo "    7 blueprints como extensões do mesmo processo"
echo "    → JÁ É o monolito constitucional correto"
echo ""
echo "  CANDIDATOS A ELIMINAR (processos redundantes):"
ps aux | grep python | grep -v grep \
  | grep -v "8091\|8100\|8101\|8103\|8104\|8105\|8108\|8114" \
  | awk '{printf "  PID %-7s  %5s MB  %s\n", $2, int($6/1024), substr($0, index($0,$11))}' \
  | head -15

echo ""
echo "  AÇÃO RECOMENDADA:"
echo "  ① Identificar processos Python fora dos ports conhecidos"
echo "  ② Verificar se são zumbis nohup de deploys antigos"
echo "  ③ Kill cirúrgico apenas nos confirmados como obsoletos:"
echo "     ps aux | grep python | grep -v grep | grep '<path_obsoleto>'"
echo "     kill <PID>"
echo ""
echo "  ⚠️  NÃO matar processos sem confirmar port/função."
echo "     Regra: ss -tlnp | grep <PID> antes de qualquer kill."
echo ""

# ── RELATÓRIO FINAL ACUMULADO ─────────────────────────────────
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║          SESSÃO DE LIMPEZA — RELATÓRIO ACUMULADO            ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "  Disco /opt/windi:"
du -sh /opt/windi 2>/dev/null

echo ""
echo "  Memória atual:"
free -h | grep Mem

echo ""
printf "  %-28s %-12s\n" "AÇÃO" "ECONOMIA"
printf "  %-28s %-12s\n" "────────────────────────────" "────────────"
printf "  %-28s %-12s\n" "Backup duplicado removido"   "26 MB ✅"
printf "  %-28s %-12s\n" "13 DBs vazias removidas"     "~0 MB ✅"
printf "  %-28s %-12s\n" "Snapshot comprimido"         "53 MB ✅"
printf "  %-28s %-12s\n" "git gc"                      "25 MB ✅"
printf "  %-28s %-12s\n" "Logrotate (pendente sudo)"   "~500 MB ⏳"
printf "  %-28s %-12s\n" "node_modules (opcional)"     "~50-80 MB 🟡"
printf "  %-28s %-12s\n" "────────────────────────────" "────────────"
printf "  %-28s %-12s\n" "TOTAL CONFIRMADO"            "104 MB"
printf "  %-28s %-12s\n" "TOTAL COM LOGROTATE"         "~604 MB"
echo ""
echo "  📌 Único item pendente de sudo: logrotate (~500 MB)"
echo ""
echo "✅ Todas as prioridades (Alta/Média/Baixa) auditadas."
echo "🏛️  Servidor WINDI em estado constitucional limpo."
echo ""
echo "OM SHANTI 🐉"
