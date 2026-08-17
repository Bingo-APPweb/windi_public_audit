# W-DISCOVERY-001 — EVIDENCE SUPPLEMENT
**Data:** 2026-08-17
**Tipo:** Manifesto read-only com hashes completos
**Executor:** CCode (Opus 4.5)
**proposed_by:** CCode
**authority:** pending Human Dragon

---

## Declaração de Autoria

Este documento foi **proposto** pelo CCode. Nenhuma aprovação I9 foi concedida.

- Aprovação da especificação ≠ autorização de build
- Gate F1 permanece BLOQUEADO
- Nenhuma implementação autorizada sem I9 explícito

---

## Manifesto do Pacote Completo

### Pacote D-SPEC (Normativo)

| # | Artefacto | Caminho | Bytes | SHA-256 |
|---|-----------|---------|-------|---------|
| 1 | v0.2-CANDIDATE | `/home/windi/claudeWeb/W-DISCOVERY-001-v0.2-CANDIDATE.md` | 17,923 | `9ce1d6da947baf8ff9d57414a8465647aef43749814fc06fce3224edb4af1d20` |
| 2 | REVIEW-A5 | `/home/windi/claudeWeb/W-DISCOVERY-001-REVIEW-A5.md` | 7,090 | `688a821fd0f8ebc911387f6403c22f49a64c428ead22d5b9b4157061157b312c` |
| 3 | REVIEW-A6 | `/home/windi/claudeWeb/W-DISCOVERY-001-REVIEW-A6.md` | 4,726 | `b610dde7c12408719cddf0f47da5f74e6bd07951f70dd375f501afd24160032b` |

### Artefactos de Auditoria (Sessão 2026-08-17)

| # | Artefacto | Caminho | Bytes | SHA-256 |
|---|-----------|---------|-------|---------|
| 4 | Evidence Pack | `/home/windi/claudeWeb/W-DISCOVERY-001-EVIDENCE-PACK-20260817.md` | 5,478 | `70436c9aa4efcc8b39bd70c9171bdebc4699e934465ed71c4b98ec99c2196f40` |
| 5 | Claim Audit | `/home/windi/claudeWeb/CLAIM-LANGUAGE-AUDIT-FASE0-ITEM3-20260817.md` | 8,519 | `878433a898e1c4e869af3e2ad87542f691c9e6f9910cc5d2e5523747c6e33e5a` |
| 6 | Corrections Proposal | `/home/windi/claudeWeb/CLAIM-CORRECTIONS-PROPOSAL-20260817.md` | 8,743 | `bc58b44841f02d333755cebd866595a7b2d7751efbd11f40b8b2b8f893d7ec3a` |
| 7 | Corrections Executed | `/home/windi/claudeWeb/CLAIM-CORRECTIONS-EXECUTED-20260817.md` | 3,600 | `ef8c0c4b0d002d61d18b0e944e9438739bdac3b3823362f67ffbd71d512f6834` |
| 8 | Fase 0 State Errata | `/home/windi/claudeWeb/W-DISCOVERY-001-FASE0-STATE-ERRATA-20260817.md` | 9,061 | `c656495d6e396c3ce63e805c47c7e9163fc2eb4479f166031f22a8c2517ad75a` |

**Total:** 65,140 bytes em 8 ficheiros

---

## Ordem de Leitura

1. **v0.2-CANDIDATE** — Arquitectura normativa (incorpora A1–A4)
2. **REVIEW-A5** — Errata de conformidade
3. **REVIEW-A6** — Clarificação terminal
4. **Evidence Pack** — Identificação do pacote
5. **Claim Audit** — 28 claims inventariados
6. **Corrections Proposal** — 6 correcções propostas
7. **Corrections Executed** — 6 correcções aplicadas
8. **Fase 0 State Errata** — Correcção do estado dos itens #1-#6

---

## Estado Corrigido da Fase 0

| # | Item | Estado | Bloqueia F1? |
|---|------|--------|--------------|
| 1 | Ledger idempotency | **AUDITED / FAIL** | **SIM** |
| 2 | Silent-except sweep | **PARTIAL** | **SIM** |
| 3 | Claim-language inventory | **COMPLETE WITH FINDINGS** | NÃO |
| 4 | §265 M2 overlap | **NOT AUDITED VALIDLY** | **SIM** |
| 5 | Portas vs matriz | COMPLETE | NÃO |
| 6 | Playground/Percurso | **PARTIAL** | **SIM** |

**Resumo:** 1 COMPLETE · 1 COMPLETE WITH FINDINGS · 4 BLOQUEANTES
**Gate F1:** **BLOQUEADO**

---

## Correcções Aplicadas no STRATO

| Ficheiro | Alteração | Verificado |
|----------|-----------|------------|
| `/opt/windi/landing-pmg/static/identity/index.html` | "garantir" → "rastrear proveniência" | ✅ |
| `/opt/windi/landing-pmg/static/enterprise/index.html` | "certificado" → "verificável" | ✅ |
| `/opt/windi/pages/witness-thesis/index.html` | "um clique" → "revê e confirma" | ✅ |
| `/opt/windi/landing-pmg/README.md:5` | "Every action" → "Approved actions" | ✅ |
| `/opt/windi/landing-pmg/README.md:14` | "Every itinerary" → "Approved itineraries" | ✅ |
| `/opt/windi/landing-pmg/static/hios-review/gabi-test-20260707/index.html` | + Banner "DIAGNOSTIC TEST ONLY" | ✅ |

---

## Claims Ainda Abertos

| Ficheiro | Claim | Estado |
|----------|-------|--------|
| `/opt/windi/landing-pmg/static/memory/index.html:630` | "Seal on sending" | **ABERTO** |

---

## Trabalho Pendente (NÃO AUTORIZADO)

| Item | Trabalho | Estado |
|------|----------|--------|
| #1 | Corrigir API para distinguir created vs existed | PROPOSTO |
| #2 | Auditoria AST completa + frontend | PENDENTE |
| #4 | Crosswalk semântico §265 ↔ Sentinel LAW | PENDENTE |
| #6 | Testar fluxo mobile + classificar | PENDENTE |

---

## Verificação de Integridade

```bash
sha256sum /home/windi/claudeWeb/W-DISCOVERY-001-*.md \
          /home/windi/claudeWeb/CLAIM-*.md
```

---

*proposed_by: CCode (Opus 4.5)*
*authority: pending Human Dragon*
*"WINDI sabe corrigir-se sem reescrever-se."* — §268

OM SHANTI
