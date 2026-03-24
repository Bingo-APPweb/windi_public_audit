# WINDI-LAW — Verification Criteria v1.0
# Documento: verification-criteria.md
# Status: CANONICAL · Selavel no Ledger
# Data: 2026-03-24 · Liga IA+H

---

## Principio Fundacional

> "Verification is not requested. It is granted."

A verificacao no WINDI-LAW nao e um direito automatico.
E uma decisao soberana do Human Dragon, baseada em criterios objectivos
e documentados. O sistema e fail-closed — o estado default e PROVISIONAL.

---

## Criterios de Verificacao (PROVISIONAL → VERIFIED)

### Criterio 1 — Entidade Legitima
- [ ] Nome legal corresponde a entidade registada
- [ ] Pais declarado e consistente com o identificador fiscal
- [ ] NIF/VAT tem formato valido para o pais indicado
- [ ] Tipo de entidade (law_firm / corporation / individual) e coerente

### Criterio 2 — Responsavel Legal Identificavel
- [ ] Nome completo do admin e real e verificavel
- [ ] Email institucional (nao gmail/hotmail/yahoo para law_firm)
- [ ] Email e entidade pertencem ao mesmo dominio (preferencial)

### Criterio 3 — Consentimentos Completos
- [ ] consent_ledger = 1 (aceita registo no Ledger)
- [ ] consent_ai = 1 (compreende que IA nao decide)
- [ ] eu_ai_act_art14 = 1 (supervisao humana confirmada)

### Criterio 4 — DID Gerado Correctamente
- [ ] DID no formato did:windi:{uuid-v4}
- [ ] Fingerprint SHA-256 presente
- [ ] Public key Ed25519 registada

### Criterio 5 — Sem Red Flags
- [ ] Email nao consta em listas de spam conhecidas
- [ ] Entidade nao tem nome generico/suspeito (ex: "Test Company")
- [ ] Nao ha duplicados no sistema (mesmo email ou NIF)

---

## Tabela de Decisao

| Criterios cumpridos | Decisao          | Accao                    |
|---------------------|------------------|--------------------------|
| 5/5                 | VERIFICAR         | POST /law/admin/verify/  |
| 4/5 (C5 em falta)   | VERIFICAR com nota| Registar observacao      |
| 3/5 ou menos        | RECUSAR           | Ver refusal-process.md   |
| Red flag activo     | SUSPENDER         | UPDATE status=SUSPENDED  |

---

## Periodicidade de Revisao

- Novos registos: avaliar em ate 48h
- Revisao de contas VERIFIED: semestral
- Contas PROVISIONAL sem actividade >30 dias: notificar ou arquivar

---

## Registo de Decisao

Cada decisao deve ser registada em audit-log.json com:
- timestamp
- did
- decisao (VERIFIED / REFUSED / SUSPENDED)
- criterios cumpridos (lista)
- observacoes do Human Dragon

---
Liga IA+H · Kempten, Bavaria · 2026
"AI processes. Human decides. WINDI guarantees."
