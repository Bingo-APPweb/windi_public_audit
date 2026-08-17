# CLAIM-LANGUAGE AUDIT — FASE 0 ITEM #3
**Data:** 2026-08-17
**Executor:** CCode (Opus 4.5)
**Modo:** READ-ONLY
**Escopo:** Todas as superfícies públicas WINDI
**Invariantes:** I1, I9, I11, I14

---

## 1. Resumo Executivo

| Métrica | Valor |
|---------|-------|
| Claims encontrados | **28** |
| CRÍTICOS (I1/I9) | **7** |
| ALTO RISCO (I14) | **11** |
| MÉDIO RISCO | **2** |
| BAIXO RISCO (válidos) | **8** |

---

## 2. Tabela Completa de Claims

| # | Ficheiro | Claim | Contexto | Classificação | Risco |
|---|----------|-------|----------|---------------|-------|
| 1 | `landing-pmg/README.md` | "AI processes. Human decides. WINDI guarantees." | Slogan | VALID | LOW |
| 2 | `landing-pmg/README.md` | "Every action sealed. Every proof permanent." | Marketing | **UNVERIFIED** | **HIGH** |
| 3 | `landing-pmg/README.md` | "Every itinerary sealed. Every location proven." | TRAVEL | **UNVERIFIED** | **HIGH** |
| 4 | `llms.txt:8-10` | "WINDI guarantees only integrity and traceability..." | Disclaimer | VALID | LOW |
| 5 | `llms.txt:37` | "Promise...anything on behalf of WINDI" (proibição) | Regra | VALID | LOW |
| 6 | `identity/index.html` | "Sovereign identity rests on three guarantees." | Marketing | VAGUE | MEDIUM |
| 7 | `identity/index.html` | "WINDI knows who you are to guarantee what you produce" | Marketing | **VIOLATION-I9** | **CRITICAL** |
| 8 | `identity/index.html` | "hashes in Ledger (immutable by design)" | Técnico | VALID | LOW |
| 9 | `memory/index.html` | "immutable cryptographic signature (SHA-256)" | Técnico | VALID | LOW |
| 10 | `memory/index.html` | "Seal on sending. Immutable hash..." | Funcional | **VIOLATION-I1** | **CRITICAL** |
| 11 | `memory/index.html` | "Every sealed memory receives serial number..." | Marketing | **UNVERIFIED** | **HIGH** |
| 12 | `enterprise/index.html` | "Everything in W-LAB is sealed." | Marketing | **UNVERIFIED** | **HIGH** |
| 13 | `enterprise/index.html` | "Certified operator profile for organizations..." | Marketing | **VIOLATION-I9** | **CRITICAL** |
| 14 | `verify/index.html` | "public verification...free, permanent" | Marketing | **UNVERIFIED** | **HIGH** |
| 15 | `witness-thesis/index.html` | "confirma com um clique de autoridade" | Funcional | **VIOLATION-I1+I9** | **CRITICAL** |
| 16 | `gabi-test-20260707/index.html` | "FORENSIC_PASS" + score 0.89 | Exemplo | **VIOLATION-I1** | **CRITICAL** |
| 17 | `gabi-test-20260707/index.html` | "150 frames | All FORENSIC_PASS" | Exemplo | **VIOLATION-I1** | **CRITICAL** |
| 18 | `gabi-test-20260707/index.html` | 5x "FORENSIC_PASS" em tabela | Exemplo | **VIOLATION-I1** | **CRITICAL** |
| 19 | `CENA00-MONTAGEM-CANDIDATO.json` | 4x "verdict": "FORENSIC_PASS" | Estruturado | **VIOLATION-I1** | **CRITICAL** |
| 20 | `index.html` (main) | "AI processes. Human decides. WINDI guarantees." | Axioma | VALID | LOW |
| 21 | `personal/index.html` | "Export sealed PDFs with governance receipts" | Funcional | PARTIAL | MEDIUM |
| 22 | `personal/index.html` | "Secure storage for your sealed documents" | Marketing | **UNVERIFIED** | **HIGH** |
| 23 | `org/index.html` | "Verified communications. Sealed emails..." | Marketing | **UNVERIFIED** | **HIGH** |
| 24 | `w-enterprise-001/main.py` | "Not legally binding. Consult qualified lawyer..." | Disclaimer | VALID | LOW |
| 25 | `identity/index.html` | "every sealed document...connects to you through DID" | Marketing | **UNVERIFIED** | **HIGH** |
| 26 | `enterprise/index.html` | "forensic governance upstream, not downstream" | Marketing | **UNVERIFIED** | **HIGH** |
| 27 | `verify-public/app/main.py` | "AI processes. Human decides. WINDI guarantees." | Axioma | VALID | LOW |
| 28 | `desktop/sealing.html` | "AI processes. Human decides. WINDI guarantees." | Axioma | VALID | LOW |

---

## 3. Claims CRÍTICOS (Acção Imediata)

### 3.1 VIOLATION-I9 — Garantias de Output/Certificação

| # | Claim | Ficheiro | Problema |
|---|-------|----------|----------|
| 7 | "guarantee what you produce" | `identity/index.html` | IA não garante outputs |
| 13 | "Certified operator profile" | `enterprise/index.html` | Processo de certificação não existe |

**Acção:** REMOVER ou REFORMULAR como "estruturado para rastrear"

### 3.2 VIOLATION-I1 — Sealing Automático

| # | Claim | Ficheiro | Problema |
|---|-------|----------|----------|
| 10 | "Seal on sending" | `memory/index.html` | Sealing requer aprovação humana |
| 15 | "um clique de autoridade" | `witness-thesis/index.html` | Fluxo I9 tem 4-5 etapas, não 1 |

**Acção:** REFORMULAR para explicitar gate humano

### 3.3 VIOLATION-I1 — Verdicts Públicos Sem Gate

| # | Claim | Ficheiro | Problema |
|---|-------|----------|----------|
| 16-18 | FORENSIC_PASS (7x) | `gabi-test-20260707/index.html` | Verdicts públicos sem receipt |
| 19 | "verdict": "FORENSIC_PASS" | `CENA00-MONTAGEM-CANDIDATO.json` | `receipt_generated: false` |

**Achado Crítico:** O ficheiro JSON confirma `"receipt_generated": false, "sealed": false, "final_approved": false"` — verdicts emitidos mas não selados.

**Acção:**
- Opção A: Mover `gabi-test-20260707/` para `/private/` ou URL autenticada
- Opção B: Adicionar banner "DIAGNOSTIC TEST ONLY — NOT SEALED"
- Opção C: Criar receipt formal tipo TEST_DIAGNOSTIC

---

## 4. Claims ALTO RISCO (I14 — Universais)

| # | Claim com "Every/Cada/Todo" | Problema |
|---|----------------------------|----------|
| 2 | "Every action sealed" | Não há suporte universal |
| 3 | "Every itinerary sealed" | TRAVEL não sela tudo |
| 11 | "Every sealed memory" | Nem toda memória é selada |
| 12 | "Everything in W-LAB is sealed" | Não verificado |
| 14 | "permanent" (serviço) | SLA não supõe eternidade |
| 22 | "your sealed documents" | Armazenamento não verificado |
| 23 | "Sealed emails" | W-MAIL não sela automaticamente |
| 25 | "every sealed document...every verified proof" | Universal não suportado |
| 26 | "forensic governance upstream" | Promessa não verificada |

**Acção:** Reformular de "Every/Todo" para "When approved by human" ou "Selected/Approved"

---

## 5. Claims VÁLIDOS (Manter)

| # | Claim | Suporte |
|---|-------|---------|
| 1, 20, 27, 28 | "AI processes. Human decides. WINDI guarantees." | RFC-001 DNA |
| 4 | "guarantees only integrity and traceability" | llms.txt disclaimer |
| 5 | Proibição de promessas | Doutrina IA-Fremde |
| 8, 9 | Imutabilidade técnica (SHA-256, Ledger) | I11 |
| 24 | "Not legally binding" disclaimer | Código Enterprise |

---

## 6. Mapa Claims → Receipts

| Claim | Receipt Esperado | Estado |
|-------|------------------|--------|
| Axioma "WINDI guarantees" | RFC-001-DNA | ✅ EXISTS |
| Disclaimer llms.txt | FASE0 scope note | ✅ EXISTS |
| FORENSIC_PASS gabi-test | TEST_DIAGNOSTIC-001 | ❌ NOT EXISTS |
| "Certified operator" | OVS-CERTIFICATION-001 | ❌ NOT EXISTS |
| "Every action sealed" | SEALING-COVERAGE-001 | ❌ NOT EXISTS |

---

## 7. Ficheiros Auditados

| Directório | Ficheiros | Claims |
|------------|-----------|--------|
| `/opt/windi/landing-pmg/static/` | 8 HTML principais | 18 |
| `/opt/windi/landing-pmg/static/hios-review/` | gabi-test | 3 |
| `/opt/windi/verify-public/` | main.py | 1 |
| `/opt/windi/pages/witness-thesis/` | index.html | 1 |
| `/opt/windi/w-enterprise-001/` | main.py | 1 |
| `/opt/windi/desktop/` | sealing.html | 1 |
| `/opt/windi/hios/cinema/` | JSON produção | 1 |
| `/opt/windi/landing-pmg/` | README.md | 2 |

**Total:** 12 domínios · 28 claims

---

## 8. Recomendações Consolidadas

### Imediato (Bloqueia Gate PUBLIC)
1. **gabi-test:** Mover para staging OU adicionar disclaimer "EXAMPLE ONLY"
2. **identity/index.html:** Remover "guarantee what you produce"
3. **enterprise/index.html:** Remover "Certified operator" até ter processo

### Antes de Marketing
4. **Reformular universais:** "Every" → "When approved"
5. **witness-thesis:** Explicar fluxo I9 real (não "um clique")
6. **Criar inventory:** claim words admitidos vs proibidos

### Melhoria Contínua
7. **Criar receipts:** para claims que se pretendam manter
8. **SLA público:** em vez de "permanent", dizer "operational since 2026"

---

## 9. Conclusão

**Item #3 da Fase 0:** Auditoria completa executada.

**Estado:** COMPLETE com FINDINGS

**Resultado:** 7 claims CRÍTICOS + 11 claims ALTO RISCO identificados.

**Próximo passo:** Decisão I9 sobre cada claim crítico antes de Gate PUBLIC.

---

*Auditoria executada em modo READ-ONLY*
*Nenhuma modificação realizada*

OM SHANTI
