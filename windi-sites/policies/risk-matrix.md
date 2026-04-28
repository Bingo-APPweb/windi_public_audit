# WINDI-SITES — Risk Matrix v1.0
# Status: CANONICAL · Trilingual (DE | EN | PT)
# Date: 2026-03-24 · Liga IA+H

---

# 🇩🇪 DEUTSCH

## Prinzip

Verschiedene Entitätstypen haben unterschiedliche Risikoprofile.
Die folgende Matrix leitet den Human Dragon bei der Bewertung des erforderlichen
Due-Diligence-Niveaus vor der Verifizierung einer Identität.

---

## Risikomatrix nach Entitätstyp

### 🟢 NIEDRIGES RISIKO — law_firm / individual

| Faktor                  | Indikator                                    |
|-------------------------|----------------------------------------------|
| E-Mail                  | Eigene Domain (z.B. @mustermann-law.de)      |
| USt-IdNr.               | Gültiges DE/AT/CH/PT Format                  |
| Name                    | Kohärent mit Entitätstyp                     |
| Gerichtsbarkeit         | DE, AT, CH, PT, EU — bekannte Jurisdiktionen |
| Erforderliche Prüfung   | Standardkriterien (verification-criteria)    |

**Typische Entscheidung:** Verifizieren nach vollständiger Checkliste.

---

### 🟡 MITTLERES RISIKO — corporation / individual außerhalb der EU

| Faktor                  | Indikator                                    |
|-------------------------|----------------------------------------------|
| E-Mail                  | Unternehmens- aber nicht juristische Domain  |
| Land                    | Außerhalb der EU aber bekanntes Rechtssystem |
| Aktivität               | Nicht eindeutig juristisch                   |
| Erforderliche Prüfung   | USt-IdNr. extern verifizieren               |

**Typische Entscheidung:** Verifizieren mit Beobachtungsnotiz im Audit-Log.

---

### 🔴 HOHES RISIKO — nicht identifizierbare Entitäten

| Faktor                  | Indikator                                    |
|-------------------------|----------------------------------------------|
| E-Mail                  | Gmail / Hotmail / Yahoo                      |
| Name                    | Generisch ("Legal Solutions", "Law Corp")    |
| USt-IdNr.               | Fehlend oder ungültiges Format               |
| Land                    | Unbekannte oder Offshore-Gerichtsbarkeit     |
| Erforderliche Prüfung   | Direkter Kontakt erforderlich               |

**Typische Entscheidung:** PROVISIONAL belassen bis Klärung.
Bei keiner Antwort innerhalb von 7 Tagen → REFUSED.

---

### ⛔ RED FLAG — Sofortige Ablehnung

| Bedingung                                   | Aktion           |
|---------------------------------------------|------------------|
| Gleiche USt-IdNr. existiert bereits         | REFUSED          |
| Gleiche E-Mail existiert bereits            | REFUSED          |
| Identischer Name wie verifizierte Entität   | Untersuchen      |
| Automatisiertes Registrierungsmuster (Bot)  | SUSPENDED        |
| Entität auf bekannter Sanktionsliste        | REFUSED + Log    |

---

## Unterstützte Gerichtsbarkeiten

| Land | Rahmenwerk     | Vertrauen | Notizen                  |
|------|----------------|-----------|--------------------------|
| 🇩🇪 DE | ZPO · BGB      | ★★★★★     | Primäre Gerichtsbarkeit  |
| 🇦🇹 AT | ABGB           | ★★★★★     | Volle Kompatibilität     |
| 🇨🇭 CH | OR             | ★★★★☆     | Nicht EU aber solide     |
| 🇵🇹 PT | CC · CPC       | ★★★★★     | Primäre Gerichtsbarkeit  |
| 🇧🇷 BR | Marco Civil    | ★★★★☆     | Liga IA+H Ursprung       |
| 🇪🇺 EU | eIDAS · GDPR   | ★★★★★     | Regulatorischer Rahmen   |
| 🌍 INT | UNCITRAL       | ★★★☆☆     | Verstärkte Verifizierung |

---

# 🇬🇧 ENGLISH

## Principle

Different entity types have different risk profiles.
The matrix below guides the Human Dragon in assessing the level of
due diligence required before verifying an identity.

---

## Risk Matrix by Entity Type

### 🟢 LOW RISK — law_firm / individual

| Factor                  | Indicator                                    |
|-------------------------|----------------------------------------------|
| Email                   | Own domain (e.g. @mustermann-law.de)         |
| VAT/Tax ID              | Valid DE/AT/CH/PT format                     |
| Name                    | Coherent with entity type                    |
| Jurisdiction            | DE, AT, CH, PT, EU — known jurisdictions     |
| Due diligence required  | Standard criteria (verification-criteria)    |

**Typical decision:** Verify after complete checklist.

---

### 🟡 MEDIUM RISK — corporation / individual outside EU

| Factor                  | Indicator                                    |
|-------------------------|----------------------------------------------|
| Email                   | Corporate but not legal domain               |
| Country                 | Outside EU but known legal framework         |
| Activity                | Not clearly legal                            |
| Due diligence required  | Verify VAT externally                        |

**Typical decision:** Verify with observation note in audit-log.

---

### 🔴 HIGH RISK — non-identifiable entities

| Factor                  | Indicator                                    |
|-------------------------|----------------------------------------------|
| Email                   | Gmail / Hotmail / Yahoo                      |
| Name                    | Generic ("Legal Solutions", "Law Corp")      |
| VAT/Tax ID              | Missing or invalid format                    |
| Country                 | Unknown or offshore jurisdiction             |
| Due diligence required  | Direct contact required                      |

**Typical decision:** Keep PROVISIONAL until clarification.
If no response within 7 days → REFUSED.

---

### ⛔ RED FLAG — Immediate Refusal

| Condition                                   | Action           |
|---------------------------------------------|------------------|
| Same VAT/Tax ID already exists              | REFUSED          |
| Same email already exists                   | REFUSED          |
| Identical name to verified entity           | Investigate      |
| Automated registration pattern (bot)        | SUSPENDED        |
| Entity on known sanctions list              | REFUSED + Log    |

---

## Supported Jurisdictions

| Country | Framework      | Trust     | Notes                    |
|---------|----------------|-----------|--------------------------|
| 🇩🇪 DE   | ZPO · BGB      | ★★★★★     | Primary jurisdiction     |
| 🇦🇹 AT   | ABGB           | ★★★★★     | Full compatibility       |
| 🇨🇭 CH   | OR             | ★★★★☆     | Not EU but solid         |
| 🇵🇹 PT   | CC · CPC       | ★★★★★     | Primary jurisdiction     |
| 🇧🇷 BR   | Marco Civil    | ★★★★☆     | Liga IA+H origin         |
| 🇪🇺 EU   | eIDAS · GDPR   | ★★★★★     | Regulatory framework     |
| 🌍 INT   | UNCITRAL       | ★★★☆☆     | Enhanced verification    |

---

# 🇵🇹 PORTUGUÊS

## Princípio

Diferentes tipos de entidade têm diferentes perfis de risco.
A matriz abaixo guia o Human Dragon na avaliação do nível de
due diligence necessário antes de verificar uma identidade.

---

## Matriz de Risco por Tipo de Entidade

### 🟢 BAIXO RISCO — law_firm / individual

| Factor                  | Indicador                                    |
|-------------------------|----------------------------------------------|
| Email                   | Domínio próprio (ex: @mustermann-law.de)     |
| NIF/VAT                 | Formato DE/AT/CH/PT válido                   |
| Nome                    | Coerente com tipo de entidade                |
| Jurisdição              | DE, AT, CH, PT, EU — jurisdições conhecidas  |
| Due diligence necessário| Critérios standard (verification-criteria)   |

**Decisão típica:** Verificar após checklist completo.

---

### 🟡 MÉDIO RISCO — corporation / individual fora da EU

| Factor                  | Indicador                                    |
|-------------------------|----------------------------------------------|
| Email                   | Domínio corporativo mas não jurídico         |
| País                    | Fora da EU mas com framework legal conhecido |
| Actividade              | Não claramente jurídica                      |
| Due diligence necessário| Verificar NIF/VAT externamente               |

**Decisão típica:** Verificar com nota de observação no audit-log.

---

### 🔴 ALTO RISCO — entidades não identificáveis

| Factor                  | Indicador                                    |
|-------------------------|----------------------------------------------|
| Email                   | Gmail / Hotmail / Yahoo                      |
| Nome                    | Genérico ("Legal Solutions", "Law Corp")     |
| NIF/VAT                 | Ausente ou formato inválido                  |
| País                    | Jurisdição desconhecida ou offshore          |
| Due diligence necessário| Contacto directo necessário                  |

**Decisão típica:** Manter PROVISIONAL até clarificação.
Se sem resposta em 7 dias → REFUSED.

---

### ⛔ RED FLAG — Recusa imediata

| Condição                                    | Acção            |
|---------------------------------------------|------------------|
| Mesmo NIF/VAT já existe no sistema          | REFUSED          |
| Mesmo email já existe no sistema            | REFUSED          |
| Nome idêntico a entidade já verificada      | Investigar       |
| Padrão de registo automatizado (bot)        | SUSPENDED        |
| Entidade em lista de sanções conhecida      | REFUSED + log    |

---

## Jurisdições Suportadas

| País    | Framework      | Confiança | Notas                    |
|---------|----------------|-----------|--------------------------|
| 🇩🇪 DE   | ZPO · BGB      | ★★★★★     | Jurisdição primária      |
| 🇦🇹 AT   | ABGB           | ★★★★★     | Plena compatibilidade    |
| 🇨🇭 CH   | OR             | ★★★★☆     | Não EU mas sólido        |
| 🇵🇹 PT   | CC · CPC       | ★★★★★     | Jurisdição primária      |
| 🇧🇷 BR   | Marco Civil    | ★★★★☆     | Liga IA+H origin         |
| 🇪🇺 EU   | eIDAS · GDPR   | ★★★★★     | Framework regulatório    |
| 🌍 INT   | UNCITRAL       | ★★★☆☆     | Verificação reforçada    |

---

Liga IA+H · Kempten, Bavaria · 2026
"AI processes. Human decides. WINDI guarantees."
