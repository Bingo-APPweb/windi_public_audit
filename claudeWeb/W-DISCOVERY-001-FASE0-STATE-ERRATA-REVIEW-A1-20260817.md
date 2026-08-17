# W-DISCOVERY-001-FASE0-STATE-ERRATA-REVIEW-A1
**Tipo:** APPEND-ONLY sobre W-DISCOVERY-001-FASE0-STATE-ERRATA-20260817 (preservado intocado)
**Data:** 2026-08-17
**Origem:** Revisão do Codex desktop com acesso read-only directo ao STRATO
**Executor:** CCode (Opus 4.5)
**Doutrina:** §268 · Propose≠Execute
**Estado:** NOT SEALED — aguarda revisão I9

A Errata original (`c656495d...ad75a`) permanece válida. Este A1 corrige 4 pontos de precisão.

---

## Disposição 1 — Proveniência Corrigida

A declaração da Errata original ("Origem: Revisão da Testemunha Cloud") é **SUPERSEDED**.

**Proveniência correcta:**

```yaml
origem: Codex desktop
método: auditoria read-only directa ao STRATO
acesso: leitura de ficheiros em /opt/windi/
alterações_strato: nenhuma
```

A Testemunha Cloud não participou desta auditoria. O Codex desktop leu directamente os ficheiros do servidor via acesso autorizado.

---

## Disposição 2 — §265 M3: Definição Corrigida

A descrição da Errata original ("M3 mede CBP POST success rate") é **SUPERSEDED** por imprecisão.

**Definição correcta de §265 M3 (Continuity Drift):**

```yaml
métrica: M3
nome: Continuity Drift
mede: tempo desde o último receipt versus ciclo/sprint declarado
detecta:
  - sessões sem fecho
  - gaps de continuidade
  - CBPs órfãos (gerados mas não ancorados)
exemplo_empírico: CBP POST falho foi caso latente detectado
nota: o exemplo não é a definição
```

**Crosswalk parcial actualizado:**

| §265 | Nome | Mede | Sentinel Equivalente |
|------|------|------|---------------------|
| M1 | Sealed-Laws Drift | CLAUDE.md laws ↔ Ledger receipts | PENDING |
| M2 | Service Health Drift | declared LIVE vs ss/systemctl | PENDING |
| M3 | Continuity Drift | tempo desde último receipt vs ciclo | PENDING |

---

## Disposição 3 — Contrato de Idempotência: Especificação Completa

A proposta de correcção na Errata original é **EXPANDIDA** para cobrir todos os casos.

### 3.1 Semântica de Resposta

| Condição | Código HTTP | Resposta | Semântica |
|----------|-------------|----------|-----------|
| ID novo | 201 | `created: true` | Receipt criado |
| Mesmo ID + mesmo content_hash | 200 | `created: false, status: "IDEMPOTENT_REPLAY"` | Retry seguro |
| Mesmo ID + content_hash diferente | 409 | `error: "ID_CONTENT_CONFLICT"` | Colisão de conteúdo |

### 3.2 Resposta Sempre Devolve Hash Armazenado

```json
{
  "ok": true,
  "sealed": true,
  "created": false,
  "status": "IDEMPOTENT_REPLAY",
  "receipt_id": "WINDI-XXX-...",
  "stored_content_hash": "sha256:...",
  "submitted_content_hash": "sha256:...",
  "match": true
}
```

### 3.3 Inserção Atómica

O padrão actual SELECT → INSERT é **vulnerável a race condition**:

```
Thread A: SELECT (não existe)
Thread B: SELECT (não existe)
Thread A: INSERT (sucesso)
Thread B: INSERT (falha ou duplicado)
```

**Especificação correcta:**

```sql
-- Opção A: INSERT OR IGNORE + verificação
INSERT OR IGNORE INTO receipts (...) VALUES (...);
SELECT * FROM receipts WHERE id = ?;
-- Comparar content_hash para determinar REPLAY vs CONFLICT

-- Opção B: Transação com EXCLUSIVE lock
BEGIN EXCLUSIVE;
SELECT ... WHERE id = ?;
IF NOT EXISTS: INSERT ...;
COMMIT;
```

### 3.4 Rotas Afectadas

Todas as rotas que chamam `upsert_receipt()` devem respeitar o retorno:

- `/api/receipts` (POST)
- `/api/ledger/seal`
- Qualquer outra rota de sealing

### 3.5 Testes Propostos (NÃO IMPLEMENTAR)

```python
def test_idempotent_replay():
    """Mesmo ID + mesmo hash = 200 IDEMPOTENT_REPLAY"""

def test_content_conflict():
    """Mesmo ID + hash diferente = 409 ID_CONTENT_CONFLICT"""

def test_concurrent_insert():
    """Duas threads simultâneas = uma 201, outra 200 ou 409"""

def test_response_includes_stored_hash():
    """Resposta sempre inclui hash armazenado"""
```

**Estado:** Especificação pronta. Implementação requer I9 explícito.

---

## Disposição 4 — Claims Abertos: Inventário Preciso

A declaração da Errata original ("1 crítico ainda aberto") é **SUPERSEDED** por imprecisão.

### Inventário Completo de Achados Abertos

| # | Tipo | Localização | Claim | Estado |
|---|------|-------------|-------|--------|
| 1 | **CRÍTICO PÚBLICO** | `/opt/windi/landing-pmg/static/memory/index.html:630` | "Seal on sending" | ABERTO |
| 2 | **INTERNO** | `/opt/windi/hios/cinema/.../CENA00-MONTAGEM-CANDIDATO.json` | `receipt_generated: false` | ABERTO (interno) |
| 3 | **HIGH/UNVERIFIED** | `/opt/windi/landing-pmg/static/enterprise/index.html:461` | "operador verificável" | CORRIGIDO mas UNVERIFIED |

### Nota sobre "operador verificável"

A correcção aplicada mudou "certificado" → "verificável". Isto resolve a violação I9 (não há processo de certificação), mas:

- "verificável" implica que existe um processo de verificação
- Enquanto não existir processo verificável real, permanece **HIGH/UNVERIFIED**
- O claim não é falso, mas também não é provado

### Estado do Item #3

```
Item #3: COMPLETE WITH FINDINGS
Findings:
  - 1 crítico público aberto (memory/index.html)
  - 1 achado interno aberto (CENA00 JSON)
  - 1 claim HIGH/UNVERIFIED (enterprise "verificável")
```

---

## Linhagem Actualizada

```
W-DISCOVERY-001-FASE0-STATE-ERRATA-20260817 (c656495d...ad75a)
└── REVIEW-A1 ← este documento
    └── (pronto para revisão I9)
```

---

## Estado Consolidado (Errata + A1)

| # | Item | Estado | Bloqueia F1? |
|---|------|--------|--------------|
| 1 | Ledger idempotency | **AUDITED / FAIL** (spec completa em A1) | **SIM** |
| 2 | Silent-except sweep | **PARTIAL** | **SIM** |
| 3 | Claim-language inventory | **COMPLETE WITH FINDINGS** (3 achados) | NÃO |
| 4 | §265 M2 overlap | **NOT AUDITED VALIDLY** (M3 corrigido) | **SIM** |
| 5 | Portas vs matriz | COMPLETE | NÃO |
| 6 | Playground/Percurso | **PARTIAL** | **SIM** |

**Gate F1:** BLOQUEADO

---

## Declaração

```yaml
proposed_by: CCode (Opus 4.5)
authority: pending Human Dragon
origem_da_revisao: Codex desktop (read-only STRATO)
alteracoes_strato: nenhuma
```

- Aprovação da especificação ≠ autorização de build
- Gate F1 permanece BLOQUEADO
- Nenhuma implementação sem I9 explícito
- Nenhum seal, receipt, commit ou promoção de gate

---

*"WINDI sabe corrigir-se sem reescrever-se."* — §268

OM SHANTI
