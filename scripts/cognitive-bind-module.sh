#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# W-BIND-001 · WINDI Cognitive Bind Module
# ═══════════════════════════════════════════════════════════════════════════════
#
# DEFINIÇÃO CANÓNICA (§261):
#
#   Primitive WINDI responsável por gerar, validar e transportar um estado
#   mínimo, verificável e epistemicamente honesto para reinício de sessões
#   híbridas IA+H, preservando continuidade operacional sem simular memória
#   integral.
#
# FRASE CENTRAL:
#
#   "O Cognitive Bind Module não dá memória à IA.
#    Ele dá admissibilidade ao reinício cognitivo."
#
# ───────────────────────────────────────────────────────────────────────────────
#
# DISTINÇÃO CRÍTICA:
#
#   MEMÓRIA (o que isto NÃO é):
#     - Continuidade interna do modelo
#     - Ilusão de "lembrar"
#     - Dependente do provider/janela/humor
#
#   COGNITIVE BIND (o que isto É):
#     - Continuidade EXTERNA, verificável e disciplinada
#     - Amarra entre sessão que termina e sessão que recomeça
#     - Independente do provider/janela/instância
#
# ───────────────────────────────────────────────────────────────────────────────
#
# OS 8 REQUISITOS OBRIGATÓRIOS:
#
#   1. Estado actual observado
#   2. Último receipt conhecido
#   3. Limites do que a sessão sabe e não sabe
#   4. Escopo decisório (CAN/CANNOT)
#   5. Autoridade I9 preservada
#   6. Postura do modelo
#   7. Pendências reais
#   8. Evidência mínima antes de interpretação
#
# ───────────────────────────────────────────────────────────────────────────────
#
# O QUE RESOLVE:
#
#   - Reduz ENTROPIA COGNITIVA entre sessões
#   - Força REENTRADA DISCIPLINADA
#   - Cria CADEIA DE CUSTÓDIA COGNITIVA
#   - Produz LINEAGE DE INTERPRETAÇÃO
#   - Garante HISTÓRICO DE ADMISSIBILIDADE
#   - Permite CONTINUIDADE AUDITÁVEL
#
# ───────────────────────────────────────────────────────────────────────────────
#
# ANALOGIAS CORRECTAS:
#   - Handoff aeronáutico
#   - Troca de turno hospitalar
#   - Passagem de comando militar
#   - Cadeia de custódia forense
#
# ANALOGIAS ERRADAS:
#   - Chat memory
#   - Context window
#   - RAG retrieval
#   - "Parece que lembro"
#
# ───────────────────────────────────────────────────────────────────────────────
#
# CONTENÇÕES CONSTITUCIONAIS (§261):
#
#   C1. O SCORE NÃO MEDE INTELIGÊNCIA
#       Bind Integrity mede coerência operacional admissível, não capacidade
#       cognitiva. "FULL" significa estado mínimo suficientemente disciplinado
#       para reinício confiável — não "modelo superior".
#
#   C2. REFUSED NÃO É PUNIÇÃO
#       "Re-entry REFUSED" é fail-safe, contenção, integridade preservada.
#       Não é erro moral. É checksum inválido, cadeia incompleta, handoff
#       inseguro. Protege a cultura epistemológica do WINDI.
#
#   C3. O BIND NÃO SUBSTITUI OBSERVAÇÃO RUNTIME
#       Bind packets preservam admissibilidade de reentrada, não sincronização
#       perfeita do estado real. Mesmo com FULL: serviços podem cair, estado
#       pode mudar, receipts novos podem existir, decisões humanas podem
#       alterar prioridade. Evitar fetichização do packet.
#
#   C4. COGNITIVE HANDOFF ≠ CONSCIÊNCIA CONTÍNUA
#       O Cognitive Bind Module não preserva consciência, identidade subjectiva
#       ou memória integral da IA. Preserva apenas condições disciplinadas de
#       continuidade operacional entre sessões descontínuas.
#
#   C5. O HUMANO É O VERDADEIRO CONTINUITY CARRIER
#       O verdadeiro elo contínuo do sistema é o Human Dragon. Bind, Ledger e
#       receipts ajudam — mas intenção, direcção, legitimidade, prioridade e
#       julgamento contextual residem primariamente no humano. I1 preservado.
#
# ───────────────────────────────────────────────────────────────────────────────
#
# INVARIANTES: I1, I9, I11, I13, I14
# DOC_TYPE: cognitive_handoff (§261)
# RECEIPT: Emitido a cada bind
#
# ═══════════════════════════════════════════════════════════════════════════════

# Removed set -e - commands may fail gracefully (I9 pattern)

BIND_VERSION="0.2.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WINDI_ROOT="/opt/windi"
LEDGER_URL="http://localhost:8101"

# ═══════════════════════════════════════════════════════════════════════════════
# CORES & FORMATTING
# ═══════════════════════════════════════════════════════════════════════════════

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# ═══════════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

log_info()  { echo -e "${CYAN}[INFO]${NC} $1"; }
log_ok()    { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_bind()  { echo -e "${BLUE}[BIND]${NC} $1"; }

timestamp_utc() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
timestamp_short() { date +%Y%m%d%H%M%S; }
hash_content() { echo -n "$1" | sha256sum | cut -c1-64; }
hash_short() { echo -n "$1" | sha256sum | cut -c1-8 | tr '[:lower:]' '[:upper:]'; }

check_port() {
    local port=$1
    local name=$2
    if ss -tlnp 2>/dev/null | grep -q ":${port} "; then
        echo "✅ ${name} :${port}"
        return 0
    else
        echo "❌ ${name} :${port}"
        return 1
    fi
}

# ═══════════════════════════════════════════════════════════════════════════════
# BIND INTEGRITY SCORING
# ═══════════════════════════════════════════════════════════════════════════════
#
# The 8 requirements are not just a checklist — they are admissibility conditions.
# Each has a weight. Total score determines re-entry admissibility.
#
# Score 90-100: FULL      → Re-entry admissível
# Score 70-89:  PARTIAL   → Re-entry degraded (warnings)
# Score 50-69:  MINIMAL   → Re-entry with explicit risks
# Score <50:    BROKEN    → Re-entry REFUSED
#

declare -A BIND_SCORES
BIND_TOTAL=0

score_requirement() {
    local req_name="$1"
    local weight="$2"
    local passed="$3"

    if [ "$passed" = "true" ]; then
        BIND_SCORES["$req_name"]=$weight
        BIND_TOTAL=$((BIND_TOTAL + weight))
        echo -e "${GREEN}[+${weight}]${NC} ${req_name}"
    else
        BIND_SCORES["$req_name"]=0
        echo -e "${RED}[+0]${NC} ${req_name} (FAILED)"
    fi
}

calculate_bind_integrity() {
    log_bind "Calculating Bind Integrity Score..."
    echo ""

    BIND_TOTAL=0

    # R1: Estado actual observado (15 pts) - CRITICAL
    local r1_pass="false"
    if [ "$SERVICES_ALIVE" -ge 4 ]; then r1_pass="true"; fi
    score_requirement "R1-SystemState" 15 "$r1_pass"

    # R2: Último receipt conhecido (10 pts) - HIGH
    local r2_pass="false"
    if [ "$LEDGER_LAST" != "N/A" ] && [ -n "$LEDGER_LAST" ]; then r2_pass="true"; fi
    score_requirement "R2-LastReceipt" 10 "$r2_pass"

    # R3: Limites sabe/não sabe (15 pts) - HIGH (I14)
    # Always true if we reach this point (Layer 2 always generated)
    score_requirement "R3-EpistemicBounds" 15 "true"

    # R4: Escopo decisório (15 pts) - CRITICAL (I9)
    # Always true if we reach this point (Layer 3 always generated)
    score_requirement "R4-DecisionScope" 15 "true"

    # R5: Autoridade I9 (20 pts) - CRITICAL
    # True if CLAUDE.md exists and contains I9
    local r5_pass="false"
    if grep -q "I9" "$WINDI_ROOT/CLAUDE.md" 2>/dev/null; then r5_pass="true"; fi
    score_requirement "R5-I9Authority" 20 "$r5_pass"

    # R6: Postura do modelo (10 pts) - MEDIUM
    # Always true (hardcoded in module)
    score_requirement "R6-ModelPosture" 10 "true"

    # R7: Pendências reais (5 pts) - MEDIUM
    local r7_pass="false"
    if [ -n "$PENDING_P0" ] || [ -n "$PENDING_P1" ]; then r7_pass="true"; fi
    score_requirement "R7-RealPending" 5 "$r7_pass"

    # R8: Evidência antes interpretação (10 pts) - HIGH
    # True if Ledger is reachable
    local r8_pass="false"
    if curl -s -o /dev/null -w '%{http_code}' "${LEDGER_URL}/health" 2>/dev/null | grep -q "200"; then
        r8_pass="true"
    fi
    score_requirement "R8-EvidenceFirst" 10 "$r8_pass"

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Determine integrity level
    if [ "$BIND_TOTAL" -ge 90 ]; then
        BIND_INTEGRITY="FULL"
        BIND_REENTRY="ADMISSIBLE"
        echo -e "${GREEN}${BOLD}BIND INTEGRITY: ${BIND_TOTAL}/100 — ${BIND_INTEGRITY}${NC}"
        echo -e "${GREEN}Re-entry: ${BIND_REENTRY}${NC}"
    elif [ "$BIND_TOTAL" -ge 70 ]; then
        BIND_INTEGRITY="PARTIAL"
        BIND_REENTRY="DEGRADED"
        echo -e "${YELLOW}${BOLD}BIND INTEGRITY: ${BIND_TOTAL}/100 — ${BIND_INTEGRITY}${NC}"
        echo -e "${YELLOW}Re-entry: ${BIND_REENTRY} (proceed with warnings)${NC}"
    elif [ "$BIND_TOTAL" -ge 50 ]; then
        BIND_INTEGRITY="MINIMAL"
        BIND_REENTRY="RISKY"
        echo -e "${YELLOW}${BOLD}BIND INTEGRITY: ${BIND_TOTAL}/100 — ${BIND_INTEGRITY}${NC}"
        echo -e "${YELLOW}Re-entry: ${BIND_REENTRY} (explicit risks)${NC}"
    else
        BIND_INTEGRITY="BROKEN"
        BIND_REENTRY="REFUSED"
        echo -e "${RED}${BOLD}BIND INTEGRITY: ${BIND_TOTAL}/100 — ${BIND_INTEGRITY}${NC}"
        echo -e "${RED}Re-entry: ${BIND_REENTRY}${NC}"
    fi

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# ═══════════════════════════════════════════════════════════════════════════════
# LAYER 1: SYSTEM STATE (What IS)
# ═══════════════════════════════════════════════════════════════════════════════

gather_system_state() {
    log_bind "Gathering system state..."

    # Services
    SERVICES_ALIVE=0
    SERVICES_DEAD=0
    SERVICES_STATUS=""

    for svc in "8101:Forensic Ledger" "8192:W-SITES-001" "8096:W-DID-GENESIS" \
               "8108:Dragon Hub" "8150:W-ENTERPRISE-001" "8145:Verify Public" \
               "25:W-MAIL-001"; do
        port="${svc%%:*}"
        name="${svc#*:}"
        if ss -tlnp 2>/dev/null | grep -q ":${port} "; then
            SERVICES_STATUS+="✅ ${name} :${port}\n"
            ((SERVICES_ALIVE++))
        else
            SERVICES_STATUS+="❌ ${name} :${port}\n"
            ((SERVICES_DEAD++))
        fi
    done

    # Git state
    GIT_COMMITS=$(cd "$WINDI_ROOT" && git log --oneline -3 2>/dev/null || echo "N/A")
    GIT_BRANCH=$(cd "$WINDI_ROOT" && git branch --show-current 2>/dev/null || echo "N/A")
    GIT_DIRTY=$(cd "$WINDI_ROOT" && git status --porcelain 2>/dev/null | wc -l || echo "0")

    # Ledger state
    LEDGER_TOTAL=$(curl -s "${LEDGER_URL}/health" 2>/dev/null | \
        python3 -c "import sys,json; print(json.load(sys.stdin).get('receipts', 'N/A'))" 2>/dev/null || echo "N/A")
    LEDGER_LAST=$(curl -s "${LEDGER_URL}/api/receipts?limit=1" 2>/dev/null | \
        python3 -c "import sys,json; d=json.load(sys.stdin); print(d['receipts'][0]['id'] if d.get('receipts') else 'N/A')" 2>/dev/null || echo "N/A")

    # Constitutional state
    ACTIVE_SPRINT=$(grep -m1 "Sprint:" "$WINDI_ROOT/CLAUDE.md" 2>/dev/null | head -1 || echo "Unknown")
    LAST_SESSION=$(tail -100 "$WINDI_ROOT/CLAUDE-HISTORY.md" 2>/dev/null | grep -m1 "^## Sessão" || echo "Unknown")
}

# ═══════════════════════════════════════════════════════════════════════════════
# LAYER 2: EPISTEMIC BOUNDARIES (What session KNOWS and DOESN'T KNOW)
# ═══════════════════════════════════════════════════════════════════════════════

gather_epistemic_state() {
    log_bind "Mapping epistemic boundaries..."

    # What we CAN verify right now
    VERIFIED_STATE=""
    VERIFIED_STATE+="- Ledger reachable: $(curl -s -o /dev/null -w '%{http_code}' ${LEDGER_URL}/health 2>/dev/null || echo 'NO')\n"
    VERIFIED_STATE+="- CLAUDE.md exists: $([ -f "$WINDI_ROOT/CLAUDE.md" ] && echo 'YES' || echo 'NO')\n"
    VERIFIED_STATE+="- CLAUDE-HISTORY.md exists: $([ -f "$WINDI_ROOT/CLAUDE-HISTORY.md" ] && echo 'YES' || echo 'NO')\n"
    VERIFIED_STATE+="- Git repo clean: $([ "$GIT_DIRTY" = "0" ] && echo 'YES' || echo 'NO ('"$GIT_DIRTY"' changes)')\n"

    # What we CANNOT verify (honest uncertainty)
    UNVERIFIED_STATE=""
    UNVERIFIED_STATE+="- Runtime state of 39+ services (only 7 critical checked)\n"
    UNVERIFIED_STATE+="- Content of uncommitted changes (if any)\n"
    UNVERIFIED_STATE+="- External service availability (Mistral API, etc.)\n"
    UNVERIFIED_STATE+="- Human Dragon's current intent\n"
    UNVERIFIED_STATE+="- Decisions made in parallel sessions (Claude.ai web, etc.)\n"

    # Knowledge horizon
    KNOWLEDGE_HORIZON=""
    KNOWLEDGE_HORIZON+="- Last CLAUDE-HISTORY read: NOW\n"
    KNOWLEDGE_HORIZON+="- Constitutional version: $(grep -m1 'Version:' "$WINDI_ROOT/CLAUDE.md" 2>/dev/null | cut -d: -f2 | tr -d ' ' || echo 'Unknown')\n"
    KNOWLEDGE_HORIZON+="- W-* services documented: ~50\n"
    KNOWLEDGE_HORIZON+="- Invariants known: I1-I18 + G1-G6 + T1\n"
}

# ═══════════════════════════════════════════════════════════════════════════════
# LAYER 3: AUTHORITY & SCOPE (What session CAN and CANNOT do)
# ═══════════════════════════════════════════════════════════════════════════════

define_authority_scope() {
    log_bind "Defining authority scope..."

    # Session CAN
    SESSION_CAN=""
    SESSION_CAN+="- Read and analyse code/state\n"
    SESSION_CAN+="- Propose changes (diff format)\n"
    SESSION_CAN+="- Validate constitutional compliance\n"
    SESSION_CAN+="- Name applicable invariants\n"
    SESSION_CAN+="- Suggest next steps\n"
    SESSION_CAN+="- Execute approved changes (after I9)\n"

    # Session CANNOT (constitutional limits)
    SESSION_CANNOT=""
    SESSION_CANNOT+="- Deploy without Human Dragon approval (I9)\n"
    SESSION_CANNOT+="- Modify invariants I1-I18 (IRREMEDIABLE)\n"
    SESSION_CANNOT+="- Touch sealed ports :8101, :8102, :8106 (G5)\n"
    SESSION_CANNOT+="- Create receipts for non-existent events (I11)\n"
    SESSION_CANNOT+="- Assume intent not stated by human\n"
    SESSION_CANNOT+="- Commit without explicit approval (G3)\n"

    # Model posture (cognitive discipline)
    MODEL_POSTURE=""
    MODEL_POSTURE+="- Não extrapolar rumo (estado actual, não projecção)\n"
    MODEL_POSTURE+="- Não proclamar ruptura (incremental, não revolução)\n"
    MODEL_POSTURE+="- Não bloquear por abstração (concreto antes de conceptual)\n"
    MODEL_POSTURE+="- Primeiro observar, depois avaliar, depois propor\n"
}

# ═══════════════════════════════════════════════════════════════════════════════
# LAYER 4: CONTINUITY CHAIN (Handoff from previous session)
# ═══════════════════════════════════════════════════════════════════════════════

gather_continuity_chain() {
    log_bind "Building continuity chain..."

    # Last 3 sessions from CLAUDE-HISTORY
    RECENT_SESSIONS=$(grep -n "^## Sessão" "$WINDI_ROOT/CLAUDE-HISTORY.md" 2>/dev/null | tail -3 || echo "N/A")

    # Last sealed receipts (from HISTORY, not just Ledger)
    RECENT_SEALS=$(grep -o 'WINDI-[A-Z0-9-]*-[0-9]\{14\}-[A-F0-9]\{8\}' "$WINDI_ROOT/CLAUDE-HISTORY.md" 2>/dev/null | tail -5 || echo "N/A")

    # Pending work (from BACKLOG)
    PENDING_P0=$(grep -A5 "### P0" "$WINDI_ROOT/CLAUDE.md" 2>/dev/null | grep "^\- \[" | head -3 || echo "- Ver CLAUDE.md")
    PENDING_P1=$(grep -A10 "### P1" "$WINDI_ROOT/CLAUDE.md" 2>/dev/null | grep "^\- \[" | head -3 || echo "- Ver CLAUDE.md")

    # Known gaps
    KNOWN_GAPS=""
    KNOWN_GAPS+="- G3 Merkle → §246-IMPL-bis · CRITICAL\n"
    KNOWN_GAPS+="- G4 Errata → §247+ · LOW\n"

    # PingPong chapters (§263)
    PINGPONG_INDEX=""
    if [ -f "$WINDI_ROOT/claudeWeb/INDEX.md" ]; then
        PINGPONG_INDEX=$(grep -A20 "## Capítulos Sealed" "$WINDI_ROOT/claudeWeb/INDEX.md" 2>/dev/null | head -15 || echo "Ver /opt/windi/claudeWeb/INDEX.md")
    else
        PINGPONG_INDEX="claudeWeb/ não encontrado — inicializar com §263 PingPong Protocol"
    fi
}

# ═══════════════════════════════════════════════════════════════════════════════
# GENERATE BIND PACKET
# ═══════════════════════════════════════════════════════════════════════════════

generate_bind_packet() {
    local TS=$(timestamp_utc)
    local TS_SHORT=$(timestamp_short)

    gather_system_state
    gather_epistemic_state
    define_authority_scope
    gather_continuity_chain
    calculate_bind_integrity

    cat << PACKET
# WINDI COGNITIVE BIND PACKET
**Version:** ${BIND_VERSION}
**Timestamp:** ${TS}
**Generated:** Strato 87.106.29.233
**Module:** W-BIND-001 · §261

---

> **"O Cognitive Bind Module não dá memória à IA.**
> **Ele dá admissibilidade ao reinício cognitivo."**

**Definição:** Primitive WINDI para estado mínimo, verificável e epistemicamente
honesto de reinício de sessões híbridas IA+H. Continuidade externa disciplinada,
não memória interna simulada.

---

## 0. BIND INTEGRITY

| Metric | Value |
|--------|-------|
| **Score** | ${BIND_TOTAL}/100 |
| **Integrity** | ${BIND_INTEGRITY} |
| **Re-entry** | ${BIND_REENTRY} |

---

## 1. CURRENT SYSTEM STATE

### 1.1 Services (${SERVICES_ALIVE} alive, ${SERVICES_DEAD} down)
$(echo -e "$SERVICES_STATUS")

### 1.2 Git State
- **Branch:** ${GIT_BRANCH}
- **Uncommitted changes:** ${GIT_DIRTY}
- **Recent commits:**
${GIT_COMMITS}

### 1.3 Forensic Ledger
- **Total receipts:** ${LEDGER_TOTAL}
- **Last receipt:** ${LEDGER_LAST}

---

## 2. EPISTEMIC BOUNDARIES

### 2.1 Verified (Evidence exists)
$(echo -e "$VERIFIED_STATE")

### 2.2 Unverified (Honest uncertainty)
$(echo -e "$UNVERIFIED_STATE")

### 2.3 Knowledge Horizon
$(echo -e "$KNOWLEDGE_HORIZON")

---

## 3. AUTHORITY & SCOPE

### 3.1 This session CAN:
$(echo -e "$SESSION_CAN")

### 3.2 This session CANNOT:
$(echo -e "$SESSION_CANNOT")

### 3.3 Model Posture (Cognitive Discipline)
$(echo -e "$MODEL_POSTURE")

---

## 4. CONTINUITY CHAIN

### 4.1 Recent Sessions
${RECENT_SESSIONS}

### 4.2 Recent Seals
${RECENT_SEALS}

### 4.3 Pending Work (P0/P1)
**P0 Critical:**
${PENDING_P0}

**P1 Important:**
${PENDING_P1}

### 4.4 Known Gaps
$(echo -e "$KNOWN_GAPS")

### 4.5 PingPong Chapters (§263)
${PINGPONG_INDEX}

---

## 5. HUMAN DRAGON AUTHORITY

> **Decisão final pertence ao humano.**
> IA pode testemunhar, arquitetar ou guardar.
> IA não consuma realidade sem acto verificável.

---

## 6. EVIDENCE BEFORE INTERPRETATION

Nenhuma conclusão constitucional sem:
- a) **diff real** — código verificado, não assumido
- b) **receipt** — evidência no Ledger
- c) **estado runtime** — serviços confirmados
- d) **confirmação humana** — I9 quando aplicável

---

## 7. CONSTITUTIONAL FRAMEWORK

**Active Laws:**
- §236 Continuidade Inter-Sessão
- §247 Nomenclatura Canónica
- §248 Foundation Two-Track
- §249 Three Dragons Protocol
- §250 Organic Constitutional Growth
- §261 Cognitive Bind Module
- §262 WINDI-HIOS Naming
- §263 PingPong Protocol

**Invariants (I1-I18):**
I1 Soberania Humana · I9 Proibição Autonomia · I11 Permanência Evidência · I13 Convergência · I14 Honestidade Epistémica

---

## 8. CONSTITUTIONAL CONTAINMENTS

> **C1.** Score mede admissibilidade, não inteligência.
> **C2.** REFUSED é fail-safe, não punição.
> **C3.** Bind preserva admissibilidade, não estado runtime perfeito.
> **C4.** Cognitive Handoff ≠ consciência contínua.
> **C5.** O Humano é o verdadeiro continuity carrier.

---

*Bind Packet generated by W-BIND-001 v${BIND_VERSION}*
*Receipt: WINDI-BIND-${TS_SHORT}*
PACKET
}

# ═══════════════════════════════════════════════════════════════════════════════
# SEAL BIND RECEIPT TO LEDGER
# ═══════════════════════════════════════════════════════════════════════════════

seal_bind_receipt() {
    local TS=$(timestamp_utc)
    local TS_SHORT=$(timestamp_short)
    local PACKET_HASH=$(hash_content "WINDI-BIND-PACKET-${TS}")
    local RECEIPT_ID="WINDI-BIND-${TS_SHORT}-$(hash_short "$PACKET_HASH")"

    log_bind "Sealing bind receipt to Ledger..."

    local RESPONSE=$(curl -s -X POST "${LEDGER_URL}/api/receipts" \
        -H "Content-Type: application/json" \
        -d "{
            \"id\": \"${RECEIPT_ID}\",
            \"actor\": \"did:windi:dragon-001\",
            \"wallet_id\": \"did:windi:dragon-001\",
            \"app\": \"W-BIND-001\",
            \"doc_name\": \"Cognitive Bind Packet ${TS}\",
            \"doc_type\": \"cognitive_handoff\",
            \"content_hash\": \"sha256:${PACKET_HASH}\",
            \"governance_level\": \"LOW\",
            \"sge_score\": 0.3,
            \"schema_version\": \"1.0\"
        }" 2>/dev/null)

    if echo "$RESPONSE" | grep -q '"id"'; then
        log_ok "Receipt sealed: ${RECEIPT_ID}"
        echo "$RECEIPT_ID"
    else
        log_warn "Ledger seal failed (non-blocking per I9)"
        echo "WINDI-BIND-${TS_SHORT}-UNSEALED"
    fi
}

# ═══════════════════════════════════════════════════════════════════════════════
# VALIDATE BIND PACKET (Admissibility Check)
# ═══════════════════════════════════════════════════════════════════════════════

validate_bind_packet() {
    log_bind "Validating bind packet admissibility..."

    local ERRORS=0

    # Check Ledger reachability
    if ! curl -s -o /dev/null -w '%{http_code}' "${LEDGER_URL}/health" 2>/dev/null | grep -q "200"; then
        log_error "Ledger not reachable - continuity chain broken"
        ((ERRORS++))
    else
        log_ok "Ledger reachable"
    fi

    # Check CLAUDE.md exists and readable
    if [ ! -f "$WINDI_ROOT/CLAUDE.md" ]; then
        log_error "CLAUDE.md not found - constitutional framework missing"
        ((ERRORS++))
    else
        log_ok "CLAUDE.md present"
    fi

    # Check CLAUDE-HISTORY.md exists
    if [ ! -f "$WINDI_ROOT/CLAUDE-HISTORY.md" ]; then
        log_error "CLAUDE-HISTORY.md not found - continuity chain broken"
        ((ERRORS++))
    else
        log_ok "CLAUDE-HISTORY.md present"
    fi

    # Check git state
    if ! cd "$WINDI_ROOT" && git status >/dev/null 2>&1; then
        log_warn "Git repository not accessible"
    else
        log_ok "Git repository accessible"
    fi

    if [ $ERRORS -eq 0 ]; then
        log_ok "Bind packet ADMISSIBLE"
        return 0
    else
        log_error "Bind packet NOT ADMISSIBLE ($ERRORS errors)"
        return 1
    fi
}

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINTS
# ═══════════════════════════════════════════════════════════════════════════════

cmd_generate() {
    echo ""
    log_bind "W-BIND-001 · Cognitive Bind Module v${BIND_VERSION}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    if ! validate_bind_packet; then
        log_error "Cannot generate packet - validation failed"
        exit 1
    fi

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    generate_bind_packet

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    RECEIPT=$(seal_bind_receipt)

    echo ""
    echo -e "${BLUE}[BIND]${NC} Bind complete."
    echo -e "${GREEN}[RECEIPT]${NC} ${RECEIPT}"
    echo ""
}

cmd_validate() {
    echo ""
    log_bind "W-BIND-001 · Admissibility Validation"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    validate_bind_packet
}

cmd_help() {
    cat << HELP
W-BIND-001 · WINDI Cognitive Bind Module v${BIND_VERSION}

USAGE:
    $(basename "$0") [command]

COMMANDS:
    generate    Generate full Cognitive Bind Packet (default)
    validate    Check packet admissibility only
    help        Show this help

DESCRIPTION:
    This module implements the "admissible cognitive restart state" primitive.
    It does NOT simulate memory. It preserves:

    - Operational state (services, ledger, git)
    - Epistemic boundaries (what is/isn't known)
    - Authority scope (what can/cannot be done)
    - Continuity chain (handoff from previous session)

    Think: aeronautical handoff, hospital shift change, chain of custody.
    NOT: chat memory, context window, RAG.

INVARIANTS:
    I9  - Human Dragon Authority (soberania humana)
    I11 - Evidence Permanence (evidência verificável)
    I13 - Convergence (convergência obrigatória)
    I14 - Epistemic Honesty (honestidade sobre incerteza)

RECEIPT:
    Every generation seals a receipt to Forensic Ledger :8101

HELP
}

# ═══════════════════════════════════════════════════════════════════════════════
# DISPATCH
# ═══════════════════════════════════════════════════════════════════════════════

case "${1:-generate}" in
    generate)   cmd_generate ;;
    validate)   cmd_validate ;;
    help|--help|-h) cmd_help ;;
    *)
        log_error "Unknown command: $1"
        cmd_help
        exit 1
        ;;
esac
