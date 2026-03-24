# WINDI-LAW — Risk Matrix v1.0
# Documento: risk-matrix.md
# Status: CANONICAL · Selavel no Ledger
# Data: 2026-03-24 · Liga IA+H

---

## Principio

Diferentes tipos de entidade tem diferentes perfis de risco.
A matriz abaixo guia o Human Dragon na avaliacao do nivel de
due diligence necessario antes de verificar uma identidade.

---

## Matriz de Risco por Tipo de Entidade

### BAIXO RISCO — law_firm / individual

| Factor                  | Indicador                                    |
|-------------------------|----------------------------------------------|
| Email                   | Dominio proprio (ex: @mustermann-law.de)     |
| NIF/VAT                 | Formato DE/AT/CH/PT valido                   |
| Nome                    | Coerente com tipo de entidade                |
| Jurisdicao              | DE, AT, CH, PT, EU — known jurisdictions     |
| Due diligence necessario| Criterios standard (verification-criteria)  |

**Decisao tipica:** Verificar apos checklist completo.

---

### MEDIO RISCO — corporation / individual fora da EU

| Factor                  | Indicador                                    |
|-------------------------|----------------------------------------------|
| Email                   | Dominio corporativo mas nao juridico         |
| Pais                    | Fora da EU mas com framework legal conhecido |
| Actividade              | Nao claramente juridica                      |
| Due diligence necessario| Verificar NIF/VAT externamente              |

**Decisao tipica:** Verificar com nota de observacao no audit-log.

---

### ALTO RISCO — entidades nao identificaveis

| Factor                  | Indicador                                    |
|-------------------------|----------------------------------------------|
| Email                   | Gmail / Hotmail / Yahoo                      |
| Nome                    | Generico ("Legal Solutions", "Law Corp")     |
| NIF/VAT                 | Ausente ou formato invalido                  |
| Pais                    | Jurisdicao desconhecida ou offshore          |
| Due diligence necessario| Contacto directo necessario                 |

**Decisao tipica:** Manter PROVISIONAL ate clarificacao.
Se sem resposta em 7 dias → REFUSED.

---

### RED FLAG — Recusa imediata

| Condicao                                    | Accao            |
|---------------------------------------------|------------------|
| Mesmo NIF/VAT ja existe no sistema          | REFUSED          |
| Mesmo email ja existe no sistema            | REFUSED          |
| Nome identico a entidade ja verificada      | Investigar       |
| Padrao de registo automatizado (bot)        | SUSPENDED        |
| Entidade em lista de sancoes conhecida      | REFUSED + log    |

---

## Jurisdicoes Suportadas e Nivel de Confianca

| Jurisdicao  | Framework      | Confianca | Notas                    |
|-------------|----------------|-----------|--------------------------|
| DE          | ZPO · BGB      | *****     | Jurisdicao primaria      |
| AT          | ABGB           | *****     | Plena compatibilidade    |
| CH          | OR             | ****      | Nao EU mas solido        |
| PT          | CC · CPC       | *****     | Jurisdicao primaria      |
| BR          | Marco Civil    | ****      | Liga IA+H origin         |
| EU          | eIDAS · GDPR   | *****     | Framework regulatorio    |
| INT         | UNCITRAL       | ***       | Verificacao reforcada    |

---
Liga IA+H · Kempten, Bavaria · 2026
"AI processes. Human decides. WINDI guarantees."
