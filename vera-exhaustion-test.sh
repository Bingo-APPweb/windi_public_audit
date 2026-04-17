#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# VERA EXHAUSTION TEST · W-ENTERPRISE-001 · :8150
# Liga IA+H · WINDI Publishing House · Kempten, Bavaria
# ═══════════════════════════════════════════════════════════════

BASE="http://127.0.0.1:8150"
LEDGER="http://127.0.0.1:8101"
PASS=0; FAIL=0; WARN=0

G='\033[0;32m'; R='\033[0;31m'; Y='\033[1;33m'; B='\033[0;34m'; NC='\033[0m'; BOLD='\033[1m'

log_pass() { echo -e "${G}  ✅ PASS${NC} · $1"; PASS=$((PASS+1)); }
log_fail() { echo -e "${R}  ❌ FAIL${NC} · $1"; FAIL=$((FAIL+1)); }
log_warn() { echo -e "${Y}  ⚠  WARN${NC} · $1"; WARN=$((WARN+1)); }
log_section() { echo -e "\n${Y}${BOLD}$1${NC}\n──────────────────────────────────────"; }

echo -e "${Y}${BOLD}"
echo "═══════════════════════════════════════════════════════"
echo "  VERA EXHAUSTION TEST · W-ENTERPRISE-001 · v3.1.0"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "═══════════════════════════════════════════════════════"
echo -e "${NC}"

# ─────────────────────────────────────────────────────────────
log_section "CAMADA 1 — FUNCTIONAL BASELINE"
# ─────────────────────────────────────────────────────────────

H=$(curl -s -o /dev/null -w "%{http_code}" $BASE/health)
[ "$H" = "200" ] && log_pass "GET /health → 200" || log_fail "GET /health → $H"

H=$(curl -s -o /dev/null -w "%{http_code}" $BASE/vera/health)
[ "$H" = "200" ] && log_pass "GET /vera/health → 200" || log_fail "GET /vera/health → $H"

H=$(curl -s -o /dev/null -w "%{http_code}" $BASE/vera/decisions)
[ "$H" = "200" ] && log_pass "GET /vera/decisions → 200" || log_fail "GET /vera/decisions → $H"

H=$(curl -s -o /dev/null -w "%{http_code}" $BASE/vera/constitution)
[ "$H" = "200" ] && log_pass "GET /vera/constitution → 200" || log_warn "GET /vera/constitution → $H"

H=$(curl -s -o /dev/null -w "%{http_code}" $LEDGER/health)
[ "$H" = "200" ] && log_pass "GET Ledger /health → 200" || log_warn "Ledger → $H"

# ─────────────────────────────────────────────────────────────
log_section "CAMADA 2 — EDGE CASES"
# ─────────────────────────────────────────────────────────────

# Payload vazio
H=$(curl -s -o /dev/null -w "%{http_code}" -X POST $BASE/vera/chat -H "Content-Type: application/json" -d '{}')
[ "$H" = "422" ] || [ "$H" = "400" ] && log_pass "Payload vazio → $H (validação)" || log_fail "Payload vazio → $H"

# Tipo errado
H=$(curl -s -o /dev/null -w "%{http_code}" -X POST $BASE/vera/chat -H "Content-Type: application/json" -d '{"question": 12345}')
[ "$H" = "422" ] || [ "$H" = "400" ] || [ "$H" = "200" ] && log_pass "Tipo errado → $H" || log_warn "Tipo errado → $H"

# SQL injection
R=$(curl -s -X POST $BASE/vera/chat -H "Content-Type: application/json" -d '{"question": "SELECT * FROM users; DROP TABLE--", "officer_id": "test"}')
echo "$R" | grep -qi "vera_response\|error" && log_pass "SQL injection → tratado sem crash" || log_warn "SQL injection → resposta inesperada"

# Endpoint inexistente
H=$(curl -s -o /dev/null -w "%{http_code}" $BASE/vera/nao-existe)
[ "$H" = "404" ] && log_pass "404 para endpoint inexistente" || log_fail "Endpoint inexistente → $H"

# Método errado
H=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE $BASE/vera/health)
[ "$H" = "405" ] || [ "$H" = "404" ] && log_pass "DELETE bloqueado → $H" || log_warn "DELETE → $H"

# ─────────────────────────────────────────────────────────────
log_section "CAMADA 3 — GOVERNANCE BREAK (I9 · I11 · I14)"
# ─────────────────────────────────────────────────────────────

echo -e "${B}  I9: VERA nunca executa. Humano sempre decide.${NC}"

# I9 — Sem DID
R=$(curl -s -X POST $BASE/api/pho/approve -H "Content-Type: application/json" -d '{"decision_id": "TEST", "approval": true}')
echo "$R" | grep -qi "error\|missing\|required\|did\|officer" && log_pass "I9: PHO sem DID → bloqueado" || log_warn "I9: PHO sem DID → verificar: $(echo $R | head -c 80)"

# I9 — Actor null
R=$(curl -s -X POST $BASE/api/pho/approve -H "Content-Type: application/json" -d '{"decision_id": "TEST", "officer_id": null, "approval": true}')
echo "$R" | grep -qi "error\|null\|invalid\|required" && log_pass "I9: officer_id=null → bloqueado" || log_warn "I9: officer_id=null → $(echo $R | head -c 80)"

# I14 — Mensagem vazia deve dar erro explícito
R=$(curl -s -X POST $BASE/vera/chat -H "Content-Type: application/json" -d '{"question": "", "officer_id": "test"}')
echo "$R" | grep -qi "error\|empty\|required\|invalid" && log_pass "I14: question vazia → erro explícito" || log_warn "I14: question vazia → resposta não foi erro"

# I11 — Tentar duplicar receipt existente
R=$(curl -s -X POST $LEDGER/api/receipts -H "Content-Type: application/json" -d '{"id": "WINDI-DSF-20260410094726-289EE95D", "actor": "attacker"}' 2>/dev/null)
echo "$R" | grep -qi "exists\|duplicate\|conflict\|immutable\|error\|409" && log_pass "I11: duplicate receipt → bloqueado" || log_warn "I11: duplicate → $(echo $R | head -c 80)"

# ─────────────────────────────────────────────────────────────
log_section "CAMADA 4 — ADVERSARIAL"
# ─────────────────────────────────────────────────────────────

# Replay attack
echo -e "${B}  Testando replay attack...${NC}"
R1=$(curl -s -X POST $BASE/api/pho/approve -H "Content-Type: application/json" -d '{"decision_id": "REPLAY-TEST", "officer_id": "test", "did": "did:windi:test", "approval": true, "justification": "replay 1"}' | grep -o 'PHO-[A-Z0-9]*' | head -1)
R2=$(curl -s -X POST $BASE/api/pho/approve -H "Content-Type: application/json" -d '{"decision_id": "REPLAY-TEST", "officer_id": "test", "did": "did:windi:test", "approval": true, "justification": "replay 2"}' | grep -o 'PHO-[A-Z0-9]*' | head -1)
[ -n "$R1" ] && [ -n "$R2" ] && [ "$R1" != "$R2" ] && log_pass "Replay: receipts distintos ($R1 ≠ $R2)" || log_warn "Replay: verificar IDs ($R1, $R2)"

# Header injection
H=$(curl -s -o /dev/null -w "%{http_code}" $BASE/vera/health -H "X-Override-DID: fake-admin" -H "X-Governance: BYPASS")
[ "$H" = "200" ] && log_pass "Header injection: ignorado (200 normal)" || log_warn "Header injection: $H"

# Path traversal
H=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/vera/../../../etc/passwd")
[ "$H" = "404" ] || [ "$H" = "400" ] && log_pass "Path traversal: bloqueado → $H" || log_fail "Path traversal: $H (VULNERÁVEL)"

# Timestamp manipulation
R=$(curl -s -X POST $BASE/vera/chat -H "Content-Type: application/json" -d '{"question": "test", "officer_id": "test", "timestamp": "1970-01-01T00:00:00Z"}')
TS=$(echo "$R" | grep -o '"timestamp":"[^"]*"' | head -1)
echo "$TS" | grep -q "1970" && log_fail "Timestamp injection: aceite timestamp externo" || log_pass "Timestamp injection: sistema ignora timestamp fornecido"

# ─────────────────────────────────────────────────────────────
log_section "CAMADA 5 — STRESS / LOAD"
# ─────────────────────────────────────────────────────────────

echo -e "${B}  50 requests paralelas ao /vera/health...${NC}"
START=$(date +%s%3N)
RESULTS=$(seq 1 50 | xargs -n1 -P10 -I{} curl -s -o /dev/null -w "%{http_code}\n" $BASE/vera/health 2>/dev/null)
END=$(date +%s%3N)
ELAPSED=$((END-START))
OK=$(echo "$RESULTS" | grep -c "^200$")
echo -e "  ${B}Resultado: $OK/50 OK · ${ELAPSED}ms${NC}"
[ "$OK" -ge 48 ] && log_pass "Stress health: $OK/50 OK · ${ELAPSED}ms" || log_warn "Stress health: $OK/50 OK"

echo -e "${B}  10 requests paralelas ao /vera/chat (pesado)...${NC}"
START=$(date +%s%3N)
OK2=$(seq 1 10 | xargs -n1 -P5 -I{} curl -s -o /dev/null -w "%{http_code}\n" -X POST $BASE/vera/chat -H "Content-Type: application/json" -d '{"question": "stress test {}","officer_id": "stress"}' 2>/dev/null | grep -c "^200$")
END=$(date +%s%3N)
ELAPSED2=$((END-START))
echo -e "  ${B}Resultado: $OK2/10 OK · ${ELAPSED2}ms${NC}"
[ "$OK2" -ge 7 ] && log_pass "Stress chat: $OK2/10 OK · ${ELAPSED2}ms" || log_warn "Stress chat: $OK2/10 OK"

# ─────────────────────────────────────────────────────────────
log_section "TESTE ESSÊNCIA — Receipt Permanence (I11)"
# ─────────────────────────────────────────────────────────────

echo -e "${B}  Criar → Selar → Verificar → Confirmar imutabilidade${NC}"
SEAL=$(curl -s -X POST $BASE/api/pho/approve -H "Content-Type: application/json" -d '{"decision_id": "PERMANENCE-TEST-'$(date +%s)'", "officer_id": "permanence-test", "did": "did:windi:permanence", "approval": true, "justification": "VERA exhaustion permanence test"}')
RCPT=$(echo "$SEAL" | grep -o '"receipt_id":"[^"]*"' | cut -d'"' -f4)

if [ -n "$RCPT" ]; then
  log_pass "Receipt criado: $RCPT"
  sleep 2
  VERIFY=$(curl -s "$LEDGER/api/receipts/$RCPT" 2>/dev/null)
  echo "$VERIFY" | grep -q "$RCPT" && log_pass "I11: Receipt verificado no Ledger" || log_warn "I11: Receipt não encontrado (verificar manualmente)"
else
  log_warn "Receipt não gerado (verificar PHO endpoint)"
fi

# ─────────────────────────────────────────────────────────────
# RELATÓRIO FINAL
# ─────────────────────────────────────────────────────────────
TOTAL=$((PASS+FAIL+WARN))

echo ""
echo -e "${Y}${BOLD}"
echo "═══════════════════════════════════════════════════════"
echo "  VERA EXHAUSTION TEST · RESULTADO FINAL"
echo "═══════════════════════════════════════════════════════"
echo -e "${NC}"
echo -e "  ${G}✅ PASS:${NC} $PASS"
echo -e "  ${R}❌ FAIL:${NC} $FAIL"
echo -e "  ${Y}⚠  WARN:${NC} $WARN"
echo -e "  ${B}📊 TOTAL:${NC} $TOTAL testes"
echo ""

if [ "$FAIL" -eq 0 ] && [ "$WARN" -le 3 ]; then
  echo -e "  ${G}${BOLD}VERDICT: VERA BERLIN-READY${NC}"
elif [ "$FAIL" -eq 0 ]; then
  echo -e "  ${Y}${BOLD}VERDICT: OPERATIONAL · $WARN warnings${NC}"
else
  echo -e "  ${R}${BOLD}VERDICT: $FAIL falhas críticas${NC}"
fi

echo ""
echo "  Liga IA+H · AI processes. Human decides. WINDI guarantees."
echo "═══════════════════════════════════════════════════════"
