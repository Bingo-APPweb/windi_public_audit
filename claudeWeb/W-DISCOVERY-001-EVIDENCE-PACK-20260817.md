# W-DISCOVERY-001 — EVIDENCE PACK
**Tipo:** READ-ONLY · Prova do pacote candidato
**Data:** 2026-08-17
**Executor:** CCode (Opus 4.5)
**Autoridade:** Nenhuma decisão executada — apenas observação
**Doutrina:** §268 · Propose≠Execute · DOCUMENTED≠ACTIVE

---

## 1. Manifesto do Pacote

O pacote candidato para Gate D-SPEC é composto por três artefactos, na seguinte ordem de leitura:

| Ordem | Artefacto | Função |
|-------|-----------|--------|
| 1 | W-DISCOVERY-001-v0.2-CANDIDATE.md | Arquitectura normativa consolidada (incorpora A1–A4) |
| 2 | W-DISCOVERY-001-REVIEW-A5.md | Errata de conformidade (7 disposições) |
| 3 | W-DISCOVERY-001-REVIEW-A6.md | Clarificação terminal do A5 (5 disposições) |

**Regra de leitura:** v0.2 é a base; A5 aplica errata sobre v0.2; A6 aplica errata sobre A5.

---

## 2. Hashes e Metadados

| Artefacto | SHA-256 | Linhas | Última Modificação |
|-----------|---------|--------|-------------------|
| v0.2-CANDIDATE | `9ce1d6da947baf8ff9d57414a8465647aef43749814fc06fce3224edb4af1d20` | 450 | 2026-08-16 10:47:02 CEST |
| REVIEW-A5 | `688a821fd0f8ebc911387f6403c22f49a64c428ead22d5b9b4157061157b312c` | 179 | 2026-08-16 01:47:03 CEST |
| REVIEW-A6 | `b610dde7c12408719cddf0f47da5f74e6bd07951f70dd375f501afd24160032b` | 140 | 2026-08-16 01:51:13 CEST |

**Caminhos no STRATO:**
```
/home/windi/claudeWeb/W-DISCOVERY-001-v0.2-CANDIDATE.md
/home/windi/claudeWeb/W-DISCOVERY-001-REVIEW-A5.md
/home/windi/claudeWeb/W-DISCOVERY-001-REVIEW-A6.md
```

---

## 3. Linhagem Documental

```
W-DISCOVERY-001 v0.1 — base teórica (não materializada como ficheiro separado)
├── REVIEW-A1 — requisitos A–J (incorporado na v0.2)
│   └── REVIEW-A2 — errata gates/escopo/protocolo (incorporado na v0.2)
│       └── REVIEW-A3 — errata transições (incorporado na v0.2)
│           └── REVIEW-A4 — clarificação terminal (incorporado na v0.2)
└── v0.2 CANDIDATE ← 9ce1d6da...
    └── REVIEW-A5 ← 688a821f...
        └── REVIEW-A6 ← b610dde7...
            └── Gate D-SPEC (NÃO DECIDIDO)
```

---

## 4. Estado da Fase 0 — Corrigido

Conforme A6-Disp.1, o mecanismo de waiver foi **removido** da arquitectura. Todos os itens pendentes bloqueiam o Gate F1.

| # | Item do Escopo | Resultado | Estado | Bloqueia F1? |
|---|----------------|-----------|--------|--------------|
| 1 | Ledger idempotency | Código não localizado | **NOT AUDITED** | **SIM** |
| 2 | Silent-except sweep | Sem triagem semântica integral | **PARTIAL** | **SIM** |
| 3 | Claim-language inventory | Apenas llms.txt verificado | **PARTIAL** | **SIM** |
| 4 | §265 M2 overlap | Scripts não localizados | **NOT AUDITED** | **SIM** |
| 5 | Live ports vs matrix | 25/30 LIVE, 5 DOWN | **COMPLETE** | NÃO |
| 6 | Playground/Percurso | Tab não implementado | **PARTIAL** | **SIM** |

**Resumo:** 1 COMPLETE · 3 PARTIAL · 2 NOT AUDITED
**Itens pendentes:** #1, #2, #3, #4, #6 (5 de 6)
**Estado Global:** **PARTIAL / NOT COMPLETE**
**Gate F1:** **BLOQUEADO** (sem opção de waiver)

---

## 5. Estado dos Gates

| Gate | Pré-condição | Estado | Decisão |
|------|--------------|--------|---------|
| **D-SPEC** | Pacote normativo completo | ELEGÍVEL (prova pendente) | **NÃO DECIDIDO** |
| **F1** | D-SPEC selado + Fase 0 COMPLETE | **BLOQUEADO** | N/A |
| **BUILD** | F1 + claims-dependência verificados | PENDENTE F1 | N/A |
| **FREMDE** | BUILD concluída + protocolo congelado | PENDENTE BUILD | N/A |
| **PUBLIC** | FREMDE satisfeito + I9 | PENDENTE FREMDE | N/A |
| **COMMERCIAL** | PUBLIC + 7 gates legais | PENDENTE PUBLIC | N/A |

---

## 6. Tabela B — Claims

| # | Claim | Estado | Uso |
|---|-------|--------|-----|
| 1 | Playground :8120 | SERVICE_HEALTH_VERIFIED | **DEPENDENCY** |
| 2 | Certificados WPO-{UUIDv7} | NOT VERIFIED | REFERENCE |
| 3 | Tríade SELADO/PLAYGROUND-ORIGIN/NÃO-VERIFICÁVEL | NOT VERIFIED | REFERENCE |
| 4 | Verify :8114 | SERVICE_HEALTH_VERIFIED | **DEPENDENCY** |
| 5 | W-QA-SECTOR-001 | NOT VERIFIED | REFERENCE |
| 6 | Tiers P/M/G e PAYG | NOT VERIFIED | REFERENCE |
| 7 | Percurso mobile S1/S3 | REFERENCED (plano) | REFERENCE |

---

## 7. Matriz de Conformidade — Resumo

### Requisitos A–J (A1): 10/10 CONFORME
### Disposições A2: 6/6 CONFORME
### Disposições A3: 4/4 CONFORME
### Disposições A4: 3/3 CONFORME
### Disposições A5: 7/7 INCORPORADAS
### Disposições A6: 5/5 CONFORME

**Conformidade documental:** PROVÁVEL
**Pacote pronto para decisão D-SPEC:** **AINDA NÃO PROVADO**

---

## 8. O Que Este Evidence Pack NÃO Faz

- NÃO sela nenhum documento
- NÃO emite receipts
- NÃO altera runtime
- NÃO faz commits
- NÃO aprova gates
- NÃO oferece opção de waiver (A6-Disp.1 proíbe)
- NÃO substitui decisão I9

---

## 9. Próximo Passo Correcto

Para avançar ao Gate D-SPEC, o Human Dragon deve:

1. **Verificar** se os hashes correspondem aos ficheiros pretendidos
2. **Decidir** se a conformidade documental está provada
3. **Selar** o Gate D-SPEC (se aprovado)

O Gate F1 permanece **BLOQUEADO** até:
- Item #1 (Ledger idempotency) — AUDITED ou COMPLETE
- Item #2 (Silent-except sweep) — COMPLETE
- Item #3 (Claim-language inventory) — COMPLETE
- Item #4 (§265 M2 overlap) — AUDITED ou COMPLETE
- Item #6 (Playground/Percurso) — COMPLETE

Não existe atalho. A6-Disp.1 removeu o mecanismo de waiver.

---

*"WINDI sabe corrigir-se sem reescrever-se."* — §268

OM SHANTI
