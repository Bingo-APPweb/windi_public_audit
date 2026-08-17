# W-DISCOVERY-001-REVIEW-A5 — Errata de Conformidade
**Tipo:** APPEND-ONLY sobre W-DISCOVERY-001 v0.2 CANDIDATE (preservado intocado)
**Data:** 2026-08-16
**Origem:** Revisão de conformidade da Testemunha Cloud — veredicto ERRATA REQUIRED
**Revisor:** Guardian (Claude.ai web)
**Executor do append:** CCode (Opus 4.5)
**Doutrina:** §268 · Propose≠Execute · DOCUMENTED≠ACTIVE
**Estado:** NOT SEALED — selagem exclusivamente Human Dragon

A v0.2 permanece válida como arquitectura normativa. Este A5 corrige sete disposições de evidência, proveniência e classificação antes do Gate D-SPEC.

---

## Disposição 1 — Protocolo ≠ Receipt

A frase do §9 da v0.2 ("protocolo [...] congelado como receipt") é **SUPERSEDED**. Redacção corrigida conforme A2-Disp.3:

> **"FREMDE-PROTOCOL-001 é um objecto versionado e hasheado, congelado antes dos testes. Um receipt regista o acto de congelamento: versão, hash, data, escopo e autorização aplicável."**

Preserva-se: protocolo ≠ receipt · regra ≠ prova da existência da regra · congelamento ≠ validação dos resultados.

---

## Disposição 2 — Tabela B: Classificação de Uso

A Tabela B do §10 da v0.2 não classifica se cada claim é DEPENDENCY ou REFERENCE (A3-Disp.2). Redacção corrigida:

| # | Claim | Evidência | Estado | **Uso** |
|---|-------|-----------|--------|---------|
| 1 | Playground vivo em :8120 | curl + health | SERVICE_HEALTH_VERIFIED | **DEPENDENCY** |
| 2 | Certificados WPO-{UUIDv7} emitidos | — | REFERENCED / NOT VERIFIED | **REFERENCE** |
| 3 | Tríade SELADO/PLAYGROUND-ORIGIN/NÃO-VERIFICÁVEL | — | REFERENCED / NOT VERIFIED | **DEPENDENCY** (se usado no demonstrador) |
| 4 | Verify "parcialmente vivo" em :8114 | curl + /health | SERVICE_HEALTH_VERIFIED | **DEPENDENCY** |
| 5 | W-QA-SECTOR-001 como primeiro tijolo | — | REFERENCED / NOT VERIFIED | **REFERENCE** |
| 6 | Tiers P/M/G e PAYG existentes | — | REFERENCED / NOT VERIFIED | **REFERENCE** |
| 7 | Percurso mobile S1/S3 | Fase 2 scope | REFERENCED (plano futuro) | **REFERENCE** |

**Regra reforçada:** Claims DEPENDENCY devem ser verificados antes do Gate BUILD. Claims REFERENCE podem permanecer NOT VERIFIED sem bloquear a construção.

---

## Disposição 3 — VERIFIED → SERVICE_HEALTH_VERIFIED

As classificações "VERIFIED" para Playground :8120 e Verify :8114 são **SUPERSEDED** por excesso de escopo. Redacção corrigida:

> **SERVICE_HEALTH_VERIFIED — endpoint /health respondeu 200; não verifica fluxo completo, tríade comportamental ou Caso Zero.**

Esta classificação aplica-se aos claims #1 e #4 da Tabela B.

---

## Disposição 4 — Fase 0: PARTIAL / NOT COMPLETE

A declaração da v0.2 §20 ("Fase 0 concluída ✅") é **SUPERSEDED**. O relatório FASE0-AUDIT-REPORT-20260815.md regista:

| Item do Escopo | Resultado |
|----------------|-----------|
| Ledger idempotency | NOT AUDITED |
| §265 M2 overlap | NOT AUDITED |
| Silent-except sweep | PASS (sem triagem semântica integral) |
| Claim-language inventory | PARCIAL (apenas llms.txt) |
| Percurso tab | Ficheiro isolado verificado |

Redacção corrigida:

> **Fase 0 do HANDOFF-CLAIM-CONTAINMENT-001: PARTIAL / NOT COMPLETE**
>
> Itens auditados: 4 de 6
> Itens NOT AUDITED: 2 (Ledger idempotency, §265 M2)
> Estado: Gate F1 permanece **BLOQUEADO** até conclusão integral ou decisão explícita de waiver

---

## Disposição 5 — Separação de Evidência: Auditoria vs Restarts

O Anexo da v0.2 mistura resultados da auditoria read-only (22:39 UTC) com restarts posteriores. Estrutura corrigida:

### Anexo A — Evidência Fase 0 (2026-08-15 22:39 UTC)
```yaml
executor: CCode (Opus 4.5)
mode: READ-ONLY
status: PARTIAL
```

**Portas DOWN no momento da auditoria:**
| Porta | Serviço | Estado Auditoria |
|-------|---------|------------------|
| :8140 | W-UDB-001 | DOWN |
| :8143 | W-BRIDGE-001 | DOWN (DOCUMENTED≠IMPLEMENTED) |
| :8151 | W-LAB-001 | DOWN |
| :8160 | W-CACHE-001 | DOWN |
| :8180 | W-ACADEMY-001 | DOWN |

### Anexo B — Mudanças Operacionais Posteriores (sob autorização separada)
```yaml
executor: CCode (Opus 4.5)
authority: Human Dragon I9 (comando explícito)
timestamp: 2026-08-16 ~01:00 UTC
```

**Serviços iniciados via nohup:**
| Porta | Serviço | Estado | Durabilidade |
|-------|---------|--------|--------------|
| :8140 | W-UDB-001 | ONLINE_AD_HOC | nohup (não systemd) |
| :8151 | W-LAB-001 | ONLINE_AD_HOC | nohup (não systemd) |
| :8160 | W-CACHE-001 | ONLINE_AD_HOC | nohup (não systemd) |
| :8180 | W-ACADEMY-001 | ONLINE_AD_HOC | nohup (não systemd) |

**Nota:** ONLINE_AD_HOC ≠ DURABLE. Estes serviços não sobrevivem a reboot do servidor sem intervenção manual.

**W-BRIDGE :8143:** Permanece DOWN — DOCUMENTED≠IMPLEMENTED, fora do Caso Zero.

---

## Disposição 6 — Gate F1 Bloqueado

A pré-condição do Gate F1 na v0.2 §11 ("Fase 0 concluída ✅") é **SUPERSEDED**. Redacção corrigida:

> **Gate F1: D-SPEC selado + Fase 0 COMPLETE (ou waiver explícito para itens NOT AUDITED)**

Opções para desbloquear F1:
1. Completar auditoria dos itens pendentes (Ledger idempotency, §265 M2)
2. Waiver I9 explícito declarando que os itens NOT AUDITED não são bloqueantes para F1

---

## Disposição 7 — "WINDI guarantees" Nota de Escopo

O achado F0-002 do relatório (llms.txt contém "WINDI guarantees") requer tratamento antes de qualquer superfície Discovery. Redacção obrigatória:

> **A expressão "WINDI guarantees" na superfície pública deve ser acompanhada de nota de escopo que explicite:**
> - O que exactamente é garantido (integridade criptográfica, não resultado)
> - O que NÃO é garantido (aconselhamento profissional, responsabilidade por decisões)
> - Limites territoriais e regulatórios aplicáveis

Esta nota é pré-condição do Gate PUBLIC, não do Gate D-SPEC.

---

## Linhagem Actualizada

```
W-DISCOVERY-001 v0.1 — NOT SEALED — preservado
├── REVIEW-A1 — requisitos A–J
│   └── REVIEW-A2 — errata gates/escopo/protocolo (Disp. 1–6)
│       └── REVIEW-A3 — errata transições (Disp. 1–4)
│           └── REVIEW-A4 — clarificação terminal (Disp. 1–3)
└── v0.2 CANDIDATE — arquitectura normativa
    └── REVIEW-A5 — errata de conformidade (Disp. 1–7) ← este documento
        └── (futura) v0.2.1 CANDIDATE ou Gate D-SPEC
```

---

## Efeito sobre o Gate D-SPEC

Após incorporação deste A5:
- A arquitectura normativa (v0.2 + A5) está **ELEGÍVEL** para Gate D-SPEC
- O Gate D-SPEC ratifica a **norma**, não a capacidade operacional
- O Gate F1 permanece **BLOQUEADO** até Fase 0 COMPLETE ou waiver

A selagem do D-SPEC não autoriza execução. Nenhum código, página ou serviço Discovery criado antes do Gate F1.

---

## Hashes de Referência

```yaml
v0.2_hash: cf4e225c...d26a8ee (434 linhas)
fase0_hash: 376ed8e3...d75291d (207 linhas)
a5_author: CCode (Opus 4.5)
a5_reviewer: Testemunha Cloud (Guardian)
```

---

*"WINDI sabe corrigir-se sem reescrever-se."* — §268

OM SHANTI 🐉
