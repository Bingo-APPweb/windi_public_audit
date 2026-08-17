# W-DISCOVERY-001-FASE0-STATE-ERRATA-20260817
**Tipo:** APPEND-ONLY sobre CLAIM-LANGUAGE-AUDIT + Evidence Pack
**Data:** 2026-08-17
**Origem:** Revisão da Testemunha Cloud (auditoria read-only directa ao STRATO)
**Executor:** CCode (Opus 4.5)
**Doutrina:** §268 · DOCUMENTED≠ACTIVE · Propose≠Execute
**Estado:** NOT SEALED — aguarda revisão I9

---

## Resumo Executivo

A avaliação anterior "5 COMPLETE · 1 PARTIAL" está **SUPERSEDED**.

| Item | Estado Anterior | Estado Corrigido |
|------|-----------------|------------------|
| #1 Ledger idempotency | COMPLETE | **AUDITED / FAIL** |
| #2 Silent-except sweep | COMPLETE | **PARTIAL** |
| #3 Claim-language | COMPLETE (críticos resolvidos) | **COMPLETE WITH FINDINGS** |
| #4 §265 M2 overlap | COMPLETE | **NOT AUDITED VALIDLY** |
| #5 Portas vs matriz | COMPLETE | COMPLETE |
| #6 Playground/Percurso | PARTIAL | PARTIAL |

**Gate F1:** Permanece **BLOQUEADO**

---

## ERRATA #1 — Item #1: Ledger Idempotency = AUDITED / FAIL

### Achado

O relatório exploratório afirmou "INSERT OR IGNORE", mas o código real usa SELECT seguido de INSERT comum.

**Ficheiro:** `/opt/windi/suite-docs/forensic_ledger.py:154-173`
```python
# §299 FIX: Check if receipt already exists
existing = con.execute(
    "SELECT id, content_hash FROM receipts WHERE id = ?",
    (r["id"],)
).fetchone()

if existing:
    return False  # Not created, already existed

# Insert new receipt (append-only)
con.execute("""
    INSERT INTO receipts(...) VALUES (...)
""", ...)
```

**Problema:** O comportamento no Ledger é idempotente (não sobrescreve), mas:

**Ficheiro:** `/opt/windi/suite-docs/windi_forensic_api.py:979-993`
```python
upsert_receipt(receipt)  # ← RETORNO IGNORADO

print(f"[FORENSIC] ◆ Cartaz Seal: {receipt['id']} ...")
self._json(201, {
    "ok": True,
    "sealed": True,  # ← SEMPRE True
    "receipt_id": receipt["id"],
    ...
})
```

**Violação:** A API ignora o retorno de `upsert_receipt()` e sempre declara `201, sealed: true`, mesmo quando o receipt já existia. Isto é enganador.

### Estado Corrigido

```
Item #1: AUDITED / FAIL
Motivo: API declara sucesso em duplicados sem indicar idempotência
```

### Proposta de Correcção (NÃO IMPLEMENTAR SEM I9)

```python
created = upsert_receipt(receipt)
if created:
    self._json(201, {"ok": True, "sealed": True, "created": True, ...})
else:
    self._json(200, {"ok": True, "sealed": True, "created": False,
                     "note": "Receipt already existed (idempotent)", ...})
```

---

## ERRATA #2 — Item #2: Silent-Except Sweep = PARTIAL

### Achado

O inventário CLAIM-CONTAINMENT-001-INVENTORY.md corrigiu um `except` crítico em `forensic_blueprint.py:852`, mas admite explicitamente que:

- Nem todos os callers foram auditados
- Frontend ficou fora do escopo
- Não houve varredura AST completa

### Estado Corrigido

```
Item #2: PARTIAL
Motivo: Callers, frontend e AST integral não auditados
```

### Trabalho Pendente

1. Auditoria de todos os callers de `upsert_receipt()`
2. Varredura AST de `except Exception` em todo `/opt/windi/`
3. Auditoria de error handling em frontend (JavaScript)

---

## ERRATA #3 — Item #3: Claim-Language = COMPLETE WITH FINDINGS

### Achado 3.1: Contagem Incorrecta

A contagem anterior (7 críticos, 11 altos, 2 médios, 8 válidos) está **SUPERSEDED**.

**Contagem corrigida:**

| Classificação | Quantidade |
|---------------|------------|
| CRÍTICOS | 8 |
| ALTO RISCO | 9 |
| MÉDIO RISCO | 2 |
| VÁLIDOS | 9 |
| **TOTAL** | **28** |

### Achado 3.2: Claim Aberto em memory/index.html

**Ficheiro:** `/opt/windi/landing-pmg/static/memory/index.html:628-630`
```html
<span lang="pt" class="active">Tu selas ao enviar. Hash imutável, hora UTC — verificável sem revelar o original.</span>
<span lang="de">Du versiegelst beim Senden. Unveränderlicher Hash, UTC-Zeit — verifizierbar ohne das Original preiszugeben.</span>
<span lang="en">Seal on sending. Immutable hash, UTC time — verifiable without revealing the original.</span>
```

**Violação:** "Seal on sending" implica sealing automático sem gate I9.

**Estado:** ABERTO — não corrigido na execução anterior.

### Achado 3.3: Reclassificação de Achado Interno

**Ficheiro:** `/opt/windi/hios/cinema/obras/w-hios-forensic-unit/production/cena00/CENA00-MONTAGEM-CANDIDATO.json`

Este ficheiro é **interno** (não servido publicamente). Deve ser reclassificado de "superfície pública" para "achado interno".

**Impacto:** Reduz críticos públicos, mas não elimina o problema (ficheiro ainda contém `receipt_generated: false`).

### Estado Corrigido

```
Item #3: COMPLETE WITH FINDINGS
Motivo: 8 críticos identificados, 1 ainda aberto (memory/index.html)
Nota: Não declarar "0 críticos"
```

---

## ERRATA #4 — Item #4: §265 M2 = NOT AUDITED VALIDLY

### Achado

A avaliação anterior associou métricas por número, não por significado:

| §265 | Sentinel LAW | Semântica Real |
|------|--------------|----------------|
| M1 (Sealed-Laws Drift) | LAW1? | §265 M1 mede CLAUDE.md ↔ Ledger |
| M2 (Service Health Drift) | LAW2? | §265 M2 mede declarados LIVE vs ss/systemctl |
| M3 (Continuity Drift) | LAW3? | §265 M3 mede CBP POST success |

**Problema:** Sentinel LAW mede coisas diferentes:
- LAW1: Latency P95 < 100ms
- LAW2: Unsynced receipts = 0
- LAW3: Hash drift = 0

**Estas não são as mesmas métricas.**

### Estado Corrigido

```
Item #4: NOT AUDITED VALIDLY
Motivo: Associação por número, não por significado semântico
```

### Trabalho Pendente

Produzir crosswalk semântico real:

| §265 Métrica | Definição | Sentinel Equivalente | Estado |
|--------------|-----------|---------------------|--------|
| M1 | CLAUDE.md laws ↔ Ledger receipts | ? | PENDING |
| M2 | declared LIVE services vs reality | ? | PENDING |
| M3 | CBP POST success rate | ? | PENDING |

---

## ERRATA #5 — Item #6: Playground/Percurso = PARTIAL (Classificar, Não Corrigir)

### Achado 5.1: Código Já Popula panelDiff

A afirmação "tab vazia" está **desactualizada**.

**Ficheiro:** `/opt/windi/artifacts/playground.html:2280-2281`
```javascript
// Render project with canonical hash in panelDiff (Percurso)
renderProject(result.project, result.verification_state, currentProjectHash, payloadVersion);
```

**Ficheiro:** `/opt/windi/artifacts/playground.html:2308`
```javascript
function renderProject(project, verificationState, contentHash, payloadVersion) {
```

O código existe e é chamado após `/api/project`. O placeholder "Em breve" pode ser fallback, não estado permanente.

### Achado 5.2: Ordem Original

A ordem no handoff era: **"classificar (provável S1/S3), NÃO corrigir"**

**Acção correcta:** Testar o fluxo mobile actual, não construir microserviço novo.

### Estado Corrigido

```
Item #6: PARTIAL
Motivo: Fluxo mobile não testado; classificação pendente
```

### Trabalho Pendente (NÃO IMPLEMENTAR)

1. Testar fluxo: `/api/project` → `renderProject()` → `panelDiff`
2. Verificar comportamento em mobile
3. Classificar:
   - Visão actual: IMPLEMENTED ou STUB?
   - Histórico de iterações: ABSENT → REFERENCE-DEFERRED?
   - Severidade: S1 ou S3?

---

## Estado Consolidado da Fase 0

| # | Item | Estado | Bloqueia F1? |
|---|------|--------|--------------|
| 1 | Ledger idempotency | **AUDITED / FAIL** | **SIM** |
| 2 | Silent-except sweep | **PARTIAL** | **SIM** |
| 3 | Claim-language inventory | **COMPLETE WITH FINDINGS** | NÃO (findings documentados) |
| 4 | §265 M2 overlap | **NOT AUDITED VALIDLY** | **SIM** |
| 5 | Portas vs matriz | COMPLETE | NÃO |
| 6 | Playground/Percurso | **PARTIAL** | **SIM** |

**Resumo:** 1 COMPLETE · 1 COMPLETE WITH FINDINGS · 4 BLOQUEANTES
**Gate F1:** **BLOQUEADO**

---

## Correcções Aplicadas (Preservadas)

As 6 correcções de claims executadas anteriormente permanecem válidas:

| Ficheiro | Hash HTTPS = Disco? | Estado |
|----------|---------------------|--------|
| identity/index.html | ✅ | APPLIED |
| enterprise/index.html | ✅ | APPLIED |
| witness-thesis/index.html | ✅ | APPLIED |
| README.md | ✅ | APPLIED |
| gabi-test/index.html (banner) | ✅ PÚBLICO | APPLIED |

---

## Pacote D-SPEC

O pacote D-SPEC (v0.2 + A5 + A6) permanece identificável pelos hashes originais:

| Artefacto | SHA-256 |
|-----------|---------|
| v0.2-CANDIDATE | `9ce1d6da947baf8ff9d57414a8465647aef43749814fc06fce3224edb4af1d20` |
| REVIEW-A5 | `688a821fd0f8ebc911387f6403c22f49a64c428ead22d5b9b4157061157b312c` |
| REVIEW-A6 | `b610dde7c12408719cddf0f47da5f74e6bd07951f70dd375f501afd24160032b` |

**Não é necessário refazer o pacote.** A norma está elegível; a capacidade operacional (Fase 0) está bloqueada.

---

## Declaração

- Aprovação da especificação (Gate D-SPEC) ≠ autorização de build
- Gate F1 permanece bloqueado até Fase 0 COMPLETE
- Nenhuma implementação autorizada sem novo I9
- Esta errata não altera documentos históricos — apenas os supersede

---

*"WINDI sabe corrigir-se sem reescrever-se."* — §268

OM SHANTI
