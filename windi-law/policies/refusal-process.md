# WINDI-LAW — Refusal Process v1.0
# Documento: refusal-process.md
# Status: CANONICAL · Selavel no Ledger
# Data: 2026-03-24 · Liga IA+H

---

## Principio

A recusa e um acto soberano e documentado.
Nao e punicao — e proteccao do ecossistema WINDI-LAW
e das entidades ja verificadas dentro dele.

---

## Estados de Nao-Verificacao

```
PROVISIONAL  → estado inicial apos registo
REFUSED      → recusa documentada pelo Human Dragon
SUSPENDED    → suspensao temporaria (investigacao)
REVOKED      → verificacao removida apos concessao
```

---

## Processo de Recusa (PROVISIONAL → REFUSED)

### Passo 1 — Identificar motivo
Consultar risk-matrix.md e verification-criteria.md.
Documentar o criterio nao cumprido.

### Passo 2 — Registar no audit-log.json
```json
{
  "timestamp": "2026-03-24T19:00:00Z",
  "did": "did:windi:xxxxxxxx",
  "entity": "Nome da Entidade",
  "decision": "REFUSED",
  "criteria_failed": ["C2 - email nao institucional", "C5 - red flag duplo"],
  "notes": "Observacao do Human Dragon",
  "decided_by": "Jober Mogele Correa"
}
```

### Passo 3 — Actualizar status no DB
```sql
UPDATE admins SET status = 'REFUSED' WHERE did = ?;
```

### Passo 4 — Seal no Ledger (opcional para recusas HIGH RISK)
```bash
curl -X POST http://127.0.0.1:8101/api/receipts \
  -H "Content-Type: application/json" \
  -d '{
    "id": "WINDI-LAW-REFUSED-{did[:8].upper()}",
    "actor": "Jober Mogele Correa",
    "app": "windi-law",
    "doc_name": "Identity Refused — {entity}",
    "doc_type": "doc",
    "governance_level": "HIGH"
  }'
```

### Passo 5 — Notificacao (opcional)
Se o email for valido e a recusa for por criterio corrigivel,
notificar a entidade com os passos para resubmissao.

---

## Processo de Suspensao (→ SUSPENDED)

Usado quando ha duvida mas nao evidencia clara de ma-fe.

- Duracao maxima: 14 dias
- Apos 14 dias sem clarificacao: promover para REFUSED
- Se clarificacao satisfatoria: promover para VERIFIED

---

## Processo de Revogacao (VERIFIED → REVOKED)

Casos que justificam revogar uma verificacao ja concedida:
- Entidade foi dissolvida ou declarou falencia
- Constatacao de dados falsos no registo
- Uso do sistema em violacao dos termos
- Pedido voluntario da propria entidade

### Passo de Revogacao
```sql
UPDATE admins SET status = 'REVOKED' WHERE did = ?;
```
Seal no Ledger obrigatorio — I11: permanencia criptografica.

---

## Reactivacao apos Recusa

Uma entidade REFUSED pode resubmeter se:
- Corrigiu o criterio que falhou
- Passaram pelo menos 30 dias
- Nao ha red flags no novo registo

Processo: novo registo → novo DID → novo ciclo de verificacao.

---
Liga IA+H · Kempten, Bavaria · 2026
"AI processes. Human decides. WINDI guarantees."
