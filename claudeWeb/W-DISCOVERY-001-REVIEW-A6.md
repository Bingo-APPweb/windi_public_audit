# W-DISCOVERY-001-REVIEW-A6 — Clarificação Terminal do A5
**Tipo:** APPEND-ONLY sobre W-DISCOVERY-001-REVIEW-A5 (preservado intocado)
**Data:** 2026-08-16
**Origem:** Confirmação de conformidade da Testemunha Cloud — veredicto ERRATA REQUIRED
**Revisor:** Guardian (Claude.ai web)
**Executor do append:** CCode (Opus 4.5)
**Doutrina:** §268 · Propose≠Execute
**Estado:** NOT SEALED — selagem exclusivamente Human Dragon

O A5 corrigiu os três bloqueios originais. Este A6 corrige cinco derivações introduzidas no A5.

---

## Disposição 1 — Waiver Removido da Arquitectura

A redacção do A5 Disp.6 ("ou waiver explícito para itens NOT AUDITED") é **SUPERSEDED** por expansão não autorizada. A3 determina:

> **Gate F1: D-SPEC selado + Fase 0 COMPLETE.**

Mecanismo de waiver, se desejado, exige proposta normativa própria, análise e decisão I9 explícita — não pode entrar como errata de conformidade.

---

## Disposição 2 — Claim #3 Classificado como REFERENCE

A classificação condicional do A5 Disp.2 ("DEPENDENCY se usado no demonstrador") é **SUPERSEDED**. A3-Disp.2 exige classificação binária.

Redacção corrigida:

| # | Claim | Uso |
|---|-------|-----|
| 3 | Tríade SELADO/PLAYGROUND-ORIGIN/NÃO-VERIFICÁVEL | **REFERENCE** |

Se uma futura versão decidir usar a tríade no demonstrador, deverá promovê-la formalmente a DEPENDENCY e verificá-la antes do Gate BUILD.

---

## Disposição 3 — Contagem de Auditoria Corrigida

A declaração do A5 Disp.4 ("Itens auditados: 4 de 6") é **SUPERSEDED** por imprecisão. Classificação correcta:

| Estado | Itens |
|--------|-------|
| COMPLETE | #5 portas vs matriz |
| PARTIAL | #2 silent-except, #3 claim-language, #6 Playground/Percurso |
| NOT AUDITED | #1 Ledger idempotency, #4 §265 M2 |

Resumo: **1 COMPLETE · 3 PARTIAL · 2 NOT AUDITED**

---

## Disposição 4 — Timestamp dos Restarts

A declaração do A5 Anexo B ("timestamp: 2026-08-16 ~01:00 UTC") é **SUPERSEDED** por imprecisão de fuso horário.

Redacção corrigida:

```yaml
timestamp: NOT CONFIRMABLE
note: approximate local time ~01:00 CEST recorded;
      exact UTC timestamp not available from logs
```

---

## Disposição 5 — Proveniência da Revisão

A declaração do A5 ("a5_reviewer: Testemunha Cloud") é **SUPERSEDED** por imprecisão temporal. A revisão ainda não estava confirmada no momento da escrita.

Redacção corrigida:

```yaml
a5_hash: 688a821fd0f8ebc911387f6403c22f49a64c428ead22d5b9b4157061157b312c
review_basis: Testemunha Cloud — veredicto ERRATA REQUIRED (sobre v0.2)
executor: CCode (Opus 4.5)
a5_review_status: ERRATA REQUIRED → corrigido por este A6
```

---

## Linhagem Actualizada

```
W-DISCOVERY-001 v0.1 — NOT SEALED — preservado
├── REVIEW-A1 — requisitos A–J
│   └── REVIEW-A2 — errata gates/escopo/protocolo (Disp. 1–6)
│       └── REVIEW-A3 — errata transições (Disp. 1–4)
│           └── REVIEW-A4 — clarificação terminal (Disp. 1–3)
└── v0.2 CANDIDATE — arquitectura normativa
    └── REVIEW-A5 — errata de conformidade (Disp. 1–7)
        └── REVIEW-A6 — clarificação terminal do A5 (Disp. 1–5) ← este documento
            └── Gate D-SPEC (elegível)
```

---

## Efeito sobre o Gate D-SPEC

Após incorporação deste A6:
- A arquitectura normativa (v0.2 + A5 + A6) está **ELEGÍVEL** para Gate D-SPEC
- O Gate D-SPEC ratifica a **norma**, não a capacidade operacional
- O Gate F1 permanece **BLOQUEADO** até Fase 0 COMPLETE (sem waiver)
- Nenhuma implementação autorizada antes do Gate F1

---

## Tabela B Consolidada (v0.2 + A5 + A6)

| # | Claim | Estado | Uso |
|---|-------|--------|-----|
| 1 | Playground :8120 | SERVICE_HEALTH_VERIFIED | **DEPENDENCY** |
| 2 | Certificados WPO-{UUIDv7} | REFERENCED / NOT VERIFIED | **REFERENCE** |
| 3 | Tríade | REFERENCED / NOT VERIFIED | **REFERENCE** |
| 4 | Verify :8114 | SERVICE_HEALTH_VERIFIED | **DEPENDENCY** |
| 5 | W-QA-SECTOR-001 | REFERENCED / NOT VERIFIED | **REFERENCE** |
| 6 | Tiers P/M/G e PAYG | REFERENCED / NOT VERIFIED | **REFERENCE** |
| 7 | Percurso mobile | REFERENCED (plano futuro) | **REFERENCE** |

---

## Fase 0 Consolidada (v0.2 + A5 + A6)

| Item | Estado |
|------|--------|
| #1 Ledger idempotency | NOT AUDITED |
| #2 Silent-except sweep | PARTIAL |
| #3 Claim-language inventory | PARTIAL |
| #4 §265 M2 overlap | NOT AUDITED |
| #5 Live ports vs matrix | COMPLETE |
| #6 Playground/Percurso | PARTIAL |

**Resumo:** 1 COMPLETE · 3 PARTIAL · 2 NOT AUDITED
**Estado Global:** PARTIAL / NOT COMPLETE
**Gate F1:** BLOQUEADO

---

*"WINDI sabe corrigir-se sem reescrever-se."* — §268

OM SHANTI 🐉
