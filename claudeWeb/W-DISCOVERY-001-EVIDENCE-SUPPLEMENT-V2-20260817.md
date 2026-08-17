# W-DISCOVERY-001 — EVIDENCE SUPPLEMENT v2
**Data:** 2026-08-17
**Tipo:** Manifesto read-only com hashes completos (actualizado)
**Executor:** CCode (Opus 4.5)
**proposed_by:** CCode
**authority:** pending Human Dragon

---

## Actualização

Este documento supersede `W-DISCOVERY-001-EVIDENCE-SUPPLEMENT-20260817.md` (`acb84577...d76db`).

Adiciona: `W-DISCOVERY-001-FASE0-STATE-ERRATA-REVIEW-A1-20260817.md`

---

## Manifesto Completo

### Pacote D-SPEC (Normativo)

| # | Artefacto | Bytes | SHA-256 |
|---|-----------|-------|---------|
| 1 | v0.2-CANDIDATE | 17,923 | `9ce1d6da947baf8ff9d57414a8465647aef43749814fc06fce3224edb4af1d20` |
| 2 | REVIEW-A5 | 7,090 | `688a821fd0f8ebc911387f6403c22f49a64c428ead22d5b9b4157061157b312c` |
| 3 | REVIEW-A6 | 4,726 | `b610dde7c12408719cddf0f47da5f74e6bd07951f70dd375f501afd24160032b` |

### Artefactos de Auditoria (Sessão 2026-08-17)

| # | Artefacto | Bytes | SHA-256 |
|---|-----------|-------|---------|
| 4 | Evidence Pack | 5,478 | `70436c9aa4efcc8b39bd70c9171bdebc4699e934465ed71c4b98ec99c2196f40` |
| 5 | Claim Audit | 8,519 | `878433a898e1c4e869af3e2ad87542f691c9e6f9910cc5d2e5523747c6e33e5a` |
| 6 | Corrections Proposal | 8,743 | `bc58b44841f02d333755cebd866595a7b2d7751efbd11f40b8b2b8f893d7ec3a` |
| 7 | Corrections Executed | 3,600 | `ef8c0c4b0d002d61d18b0e944e9438739bdac3b3823362f67ffbd71d512f6834` |
| 8 | Fase 0 State Errata | 9,061 | `c656495d6e396c3ce63e805c47c7e9163fc2eb4479f166031f22a8c2517ad75a` |
| 9 | **Errata REVIEW-A1** | 6,361 | `194eb931e5a79b3448707a859e839d35eb0d8416df3f18e04bc3073e033b7f52` |

**Total:** 71,501 bytes em 9 ficheiros

---

## Linhagem Documental

```
W-DISCOVERY-001 v0.2 CANDIDATE (9ce1d6da...)
├── REVIEW-A5 (688a821f...)
│   └── REVIEW-A6 (b610dde7...)
│       └── Evidence Pack (70436c9a...)
│           └── Claim Audit (878433a8...)
│               └── Corrections Proposal (bc58b448...)
│                   └── Corrections Executed (ef8c0c4b...)
│                       └── Fase 0 State Errata (c656495d...)
│                           └── Errata REVIEW-A1 (194eb931...) ← NOVO
```

---

## Estado Consolidado da Fase 0

| # | Item | Estado | Bloqueia F1? |
|---|------|--------|--------------|
| 1 | Ledger idempotency | **AUDITED / FAIL** | **SIM** |
| 2 | Silent-except sweep | **PARTIAL** | **SIM** |
| 3 | Claim-language inventory | **COMPLETE WITH FINDINGS** | NÃO |
| 4 | §265 M2 overlap | **NOT AUDITED VALIDLY** | **SIM** |
| 5 | Portas vs matriz | COMPLETE | NÃO |
| 6 | Playground/Percurso | **PARTIAL** | **SIM** |

**Gate F1:** BLOQUEADO (4 itens bloqueantes)

---

## Correcções no A1

| Disposição | Correcção |
|------------|-----------|
| 1 | Proveniência: Codex desktop (não Testemunha Cloud) |
| 2 | §265 M3: tempo vs ciclo (não CBP POST success) |
| 3 | Idempotência: 200/409/201 + inserção atómica |
| 4 | Claims: 1 crítico + 1 interno + 1 HIGH/UNVERIFIED |

---

## Claims Abertos (Inventário Final)

| # | Tipo | Localização | Estado |
|---|------|-------------|--------|
| 1 | CRÍTICO PÚBLICO | `memory/index.html:630` | ABERTO |
| 2 | INTERNO | `CENA00-MONTAGEM-CANDIDATO.json` | ABERTO |
| 3 | HIGH/UNVERIFIED | `enterprise/index.html:461` | CORRIGIDO mas não provado |

---

## Declaração

```yaml
proposed_by: CCode (Opus 4.5)
authority: pending Human Dragon
origem_da_revisao: Codex desktop (read-only STRATO)
alteracoes_strato: 6 correcções de claims aplicadas
build_autorizado: NÃO
seal_emitido: NÃO
commit_feito: NÃO
gate_promovido: NÃO
```

---

## Pronto para Revisão I9

O pacote documental está completo:
- Norma (v0.2 + A5 + A6) elegível para Gate D-SPEC
- Fase 0 com estado honesto (4 bloqueantes identificados)
- Correcções de claims aplicadas (6)
- Especificação de idempotência completa
- Proveniência e métricas corrigidas

**Próximo passo:** Decisão I9 do Human Dragon

---

*"WINDI sabe corrigir-se sem reescrever-se."* — §268

OM SHANTI
