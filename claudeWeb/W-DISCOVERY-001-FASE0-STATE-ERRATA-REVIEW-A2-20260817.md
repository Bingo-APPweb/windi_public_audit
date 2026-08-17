# W-DISCOVERY-001-FASE0-STATE-ERRATA-REVIEW-A2
**Tipo:** APPEND-ONLY sobre REVIEW-A1 (preservado intocado)
**Data:** 2026-08-17
**Origem:** Revisão do Codex desktop — DOCUMENTARY PASS WITH MINOR PRECISION FIXES
**Executor:** CCode (Opus 4.5)
**Doutrina:** §268 · Propose≠Execute
**Estado:** NOT SEALED — aguarda decisão I9

O A1 (`194eb931...b7f52`) permanece válido. Este A2 corrige 4 pontos de precisão terminológica.

---

## Disposição 1 — Claim "verificável": Precisão Epistémica

A frase do A1 Disposição 4 ("O claim não é falso") é **SUPERSEDED**.

**Redacção corrigida:**

> O claim não foi demonstrado falso, mas permanece não verificado e não provado.

Isto preserva a honestidade epistémica: ausência de falsidade demonstrada ≠ verdade provada.

---

## Disposição 2 — Proveniência: Escopo de "alteracoes_strato"

A declaração do A1 (`alteracoes_strato: nenhuma`) é **PRECISADA**.

**Escopo correcto:**

```yaml
alteracoes_strato_auditoria_codex: nenhuma
  # O Codex desktop operou em modo read-only

alteracoes_strato_ccode_sessao:
  - 6 correcções de claims aplicadas (documentadas em Corrections Executed)
  - 9 documentos criados em /home/windi/claudeWeb/
```

A declaração original refere-se exclusivamente à auditoria read-only do Codex. As alterações do CCode estão documentadas separadamente.

---

## Disposição 3 — Payload vs Envelope

O A1 e Supplement v2 não distinguem explicitamente payload de envelope. **Clarificação:**

| Conceito | Conteúdo | Bytes | Contagem |
|----------|----------|-------|----------|
| **Payload manifestado** | 9 ficheiros (v0.2 + A5 + A6 + auditorias + erratas) | 71,501 | INCLUÍDO |
| **Envelope** | Evidence Supplement v2 | 4,000 | EXCLUÍDO da contagem |

O Supplement v2 (`608d463c...e9087`) é o manifesto que lista os 9 ficheiros. Ele não se conta a si próprio.

---

## Disposição 4 — Terminologia: "Final" → "Consolidado"

A expressão do Supplement v2 ("Inventário Final") é **SUPERSEDED**.

**Redacção corrigida:**

> Inventário Consolidado desta Revisão

"Final" implica encerramento definitivo. "Consolidado desta Revisão" preserva a natureza append-only e a possibilidade de futuras erratas.

---

## Linhagem Actualizada

```
Fase 0 State Errata (c656495d...)
└── REVIEW-A1 (194eb931...)
    └── REVIEW-A2 ← este documento
        └── (pronto para decisão I9)
```

---

## Estado Preservado

| Campo | Valor |
|-------|-------|
| Gate D-SPEC | ELIGIBLE |
| Gate F1 | **BLOCKED** |
| Build | **NOT AUTHORIZED** |
| Seal/Receipt | **NONE** |
| Commit | **NONE** |

---

## Declaração

```yaml
proposed_by: CCode (Opus 4.5)
authority: pending Human Dragon
payload: 9 ficheiros · 71,501 bytes
envelope: Evidence Supplement v2 · 4,000 bytes · 608d463c...e9087
```

---

*"WINDI sabe corrigir-se sem reescrever-se."* — §268

OM SHANTI
