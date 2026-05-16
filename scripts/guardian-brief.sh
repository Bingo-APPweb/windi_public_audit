#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# WINDI Guardian Brief Generator
# ═══════════════════════════════════════════════════════════════════
# Gera brief curado para início de sessão Guardian (Claude.ai web)
# Human Dragon executa, copia output, cola no primeiro turno
#
# Limite duro: 100 linhas / 8KB
# Receipt: emitido a cada execução
# ═══════════════════════════════════════════════════════════════════

set -e

TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
TS_SHORT=$(date +%Y%m%d%H%M%S)

# ─── Funções auxiliares ───

check_port() {
    local port=$1
    local name=$2
    if ss -tlnp 2>/dev/null | grep -q ":${port} "; then
        echo "✅ ${name} :${port}"
    else
        echo "❌ ${name} :${port}"
    fi
}

# ─── Recolha de dados ───

# Sprint actual (do CLAUDE.md)
SPRINT_LINE=$(grep -m1 "Sprint:" /opt/windi/CLAUDE.md 2>/dev/null | head -1 || echo "Sprint: desconhecido")

# Último receipt
LAST_RECEIPT=$(curl -s "http://localhost:8101/api/receipts?limit=1" 2>/dev/null | \
    python3 -c "import sys,json; d=json.load(sys.stdin); print(d['receipts'][0]['id'] if d.get('receipts') else 'N/A')" 2>/dev/null || echo "N/A")

# Total receipts
TOTAL_RECEIPTS=$(curl -s "http://localhost:8101/health" 2>/dev/null | \
    python3 -c "import sys,json; print(json.load(sys.stdin).get('receipts', 'N/A'))" 2>/dev/null || echo "N/A")

# Última entrada CLAUDE-HISTORY (últimas 30 linhas relevantes)
LAST_SESSION=$(tail -50 /opt/windi/CLAUDE-HISTORY.md 2>/dev/null | grep -A2 "^## Sessão" | tail -3 || echo "N/A")

# Próximo passo (do CLAUDE-HISTORY)
NEXT_STEP=$(grep -A1 "Próximo" /opt/windi/CLAUDE-HISTORY.md 2>/dev/null | tail -2 | head -1 || echo "Ver CLAUDE-HISTORY.md")

# Gaps conhecidos (do CLAUDE.md BACKLOG)
GAPS=$(grep -A10 "### P0" /opt/windi/CLAUDE.md 2>/dev/null | grep "^\- \[" | head -3 || echo "- Ver CLAUDE.md BACKLOG")

# ─── Gerar Brief ───

cat << BRIEF
# WINDI COGNITIVE BIND PACKET
**Timestamp:** ${TS}
**Gerado em:** Strato 87.106.29.233

---

## Current System State

### Serviços Vivos
$(check_port 8101 "Forensic Ledger")
$(check_port 8192 "W-SITES-001")
$(check_port 8096 "W-DID-GENESIS")
$(check_port 8108 "Dragon Hub")
$(check_port 8150 "W-ENTERPRISE-001")
$(check_port 8114 "Verify Public")
$(check_port 25 "W-MAIL-001 SMTP")

### Últimos Commits
$(cd /opt/windi && git log --oneline -3 2>/dev/null || echo "N/A")

### Receipts Selados
- **Total:** ${TOTAL_RECEIPTS}
- **Último:** ${LAST_RECEIPT}

### Endpoints Relevantes
- Ledger: http://localhost:8101/api/receipts
- Verify: https://windi-domain.com/verify-public/
- Sites: https://windisites.de/

### Pendências Reais
${GAPS}
- **G3 Merkle** → §246-IMPL-bis · CRITICAL · prazo 7 dias
- **G4 Errata** → §247+ · LOW

---

## Session Scope

### O que esta sessão PODE decidir:
- Revisão de arquitectura proposta
- Validação constitucional de diffs
- Nomeação de invariantes aplicáveis
- Proposta de próximos passos

### O que esta sessão NÃO PODE decidir:
- Deploy sem approval I9
- Alteração de invariantes (I1-I18)
- Modificação de portas SEALED (:8101, :8102, :8106)
- Commits sem confirmação Human Dragon

---

## Evidence Before Interpretation

Nenhuma conclusão constitucional sem:
- a) **diff real** — código verificado, não assumido
- b) **receipt** — evidência no Ledger
- c) **estado runtime** — serviços confirmados via ss/curl
- d) **confirmação humana** — I9 quando aplicável

---

## Model Posture

- **Não extrapolar rumo** — estado actual, não projecção
- **Não proclamar ruptura** — mudança incremental, não revolução
- **Não bloquear por abstração** — concreto antes de conceptual
- **Primeiro observar, depois avaliar, depois propor**

---

## Human Dragon Authority

> Decisão final pertence ao humano.
> IA pode testemunhar, arquitetar ou guardar.
> IA não consuma realidade sem acto verificável.

---

## Sprint Actual
${SPRINT_LINE}

## Leis Constitucionais Activas
§236 Continuidade · §246 Sprint 1 (CLOSED) · §247 Nomenclatura · §248 Foundation · §249 Three Dragons · §250 Organic Growth

## Última Sessão
${LAST_SESSION}

## Próximo Passo Herdado
${NEXT_STEP}

## O Que Esta Sessão NÃO Sabe
- W-TRAVEL-001 blueprint draft (em /opt/windi/archive/) — não revisto
- Mecanismo de sync de skills para Claude.ai — não investigado
- Estado detalhado dos 39 serviços — só 7 críticos listados acima

---
*Brief gerado por /opt/windi/scripts/guardian-brief.sh*
*Receipt: WINDI-GUARDIAN-BRIEF-${TS_SHORT}*
BRIEF

# ─── Emitir Receipt ───

BRIEF_HASH=$(cat << BRIEF | sha256sum | cut -c1-64
# WINDI STATE BRIEF - ${TS}
BRIEF
)

curl -s -X POST http://localhost:8101/api/receipts \
  -H "Content-Type: application/json" \
  -d "{
    \"id\": \"WINDI-GUARDIAN-BRIEF-${TS_SHORT}-$(echo ${BRIEF_HASH} | cut -c1-8 | tr '[:lower:]' '[:upper:]')\",
    \"actor\": \"did:windi:dragon-001\",
    \"wallet_id\": \"did:windi:dragon-001\",
    \"app\": \"W-GUARDIAN-BRIEF\",
    \"doc_name\": \"Guardian Brief ${TS}\",
    \"doc_type\": \"infrastructure_event\",
    \"content_hash\": \"sha256:${BRIEF_HASH}\",
    \"governance_level\": \"LOW\",
    \"sge_score\": 0.3,
    \"schema_version\": \"1.0\"
  }" > /dev/null 2>&1

echo ""
echo "# Receipt emitido: WINDI-GUARDIAN-BRIEF-${TS_SHORT}"
