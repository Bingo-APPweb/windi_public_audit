# WINDI-SITES — Verification Criteria v1.0
# Status: CANONICAL · Trilingual (DE | EN | PT)
# Date: 2026-03-24 · Liga IA+H

---

# 🇩🇪 DEUTSCH

## Grundprinzip

> "Verifizierung wird nicht angefordert. Sie wird gewährt."

Die Verifizierung bei WINDI-SITES ist kein automatisches Recht.
Es ist eine souveräne Entscheidung des Human Dragon, basierend auf objektiven
und dokumentierten Kriterien. Das System ist fail-closed — der Standardzustand ist PROVISIONAL.

---

## Verifizierungskriterien (PROVISIONAL → VERIFIED)

### Kriterium 1 — Legitime Entität
- [ ] Rechtlicher Name entspricht einer registrierten Entität
- [ ] Angegebenes Land stimmt mit der Steuer-ID überein
- [ ] USt-IdNr. hat gültiges Format für das angegebene Land
- [ ] Entitätstyp (law_firm / corporation / individual) ist kohärent

### Kriterium 2 — Identifizierbarer Rechtsverantwortlicher
- [ ] Vollständiger Name des Admins ist real und verifizierbar
- [ ] Institutionelle E-Mail (nicht gmail/hotmail/yahoo für law_firm)
- [ ] E-Mail und Entität gehören zur gleichen Domain (bevorzugt)

### Kriterium 3 — Vollständige Einwilligungen
- [ ] consent_ledger = 1 (akzeptiert Registrierung im Ledger)
- [ ] consent_ai = 1 (versteht, dass KI nicht entscheidet)
- [ ] eu_ai_act_art14 = 1 (menschliche Aufsicht bestätigt)

### Kriterium 4 — DID Korrekt Generiert
- [ ] DID im Format did:windi:{uuid-v4}
- [ ] SHA-256 Fingerprint vorhanden
- [ ] Ed25519 Public Key registriert

### Kriterium 5 — Keine Red Flags
- [ ] E-Mail nicht in bekannten Spam-Listen
- [ ] Entität hat keinen generischen/verdächtigen Namen
- [ ] Keine Duplikate im System (gleiche E-Mail oder USt-IdNr.)

---

## Entscheidungstabelle

| Erfüllte Kriterien | Entscheidung      | Aktion                   |
|--------------------|-------------------|--------------------------|
| 5/5                | VERIFIZIEREN      | POST /law/admin/verify/  |
| 4/5 (K5 fehlt)     | VERIFIZIEREN+Notiz| Beobachtung registrieren |
| 3/5 oder weniger   | ABLEHNEN          | Siehe refusal-process.md |
| Red Flag aktiv     | SUSPENDIEREN      | UPDATE status=SUSPENDED  |

---

## Überprüfungsrhythmus

- Neue Registrierungen: innerhalb von 48h bewerten
- Überprüfung von VERIFIED-Konten: halbjährlich
- PROVISIONAL-Konten ohne Aktivität >30 Tage: benachrichtigen oder archivieren

---

# 🇬🇧 ENGLISH

## Foundational Principle

> "Verification is not requested. It is granted."

Verification at WINDI-SITES is not an automatic right.
It is a sovereign decision by the Human Dragon, based on objective
and documented criteria. The system is fail-closed — the default state is PROVISIONAL.

---

## Verification Criteria (PROVISIONAL → VERIFIED)

### Criterion 1 — Legitimate Entity
- [ ] Legal name corresponds to a registered entity
- [ ] Declared country is consistent with tax identifier
- [ ] VAT/Tax ID has valid format for the indicated country
- [ ] Entity type (law_firm / corporation / individual) is coherent

### Criterion 2 — Identifiable Legal Representative
- [ ] Admin's full name is real and verifiable
- [ ] Institutional email (not gmail/hotmail/yahoo for law_firm)
- [ ] Email and entity belong to the same domain (preferred)

### Criterion 3 — Complete Consents
- [ ] consent_ledger = 1 (accepts registration in Ledger)
- [ ] consent_ai = 1 (understands that AI does not decide)
- [ ] eu_ai_act_art14 = 1 (human oversight confirmed)

### Criterion 4 — DID Correctly Generated
- [ ] DID in format did:windi:{uuid-v4}
- [ ] SHA-256 Fingerprint present
- [ ] Ed25519 Public Key registered

### Criterion 5 — No Red Flags
- [ ] Email not in known spam lists
- [ ] Entity does not have generic/suspicious name
- [ ] No duplicates in system (same email or VAT)

---

## Decision Table

| Criteria Met | Decision         | Action                   |
|--------------|------------------|--------------------------|
| 5/5          | VERIFY           | POST /law/admin/verify/  |
| 4/5 (C5 missing) | VERIFY+Note  | Register observation     |
| 3/5 or less  | REFUSE           | See refusal-process.md   |
| Red flag active | SUSPEND       | UPDATE status=SUSPENDED  |

---

## Review Schedule

- New registrations: evaluate within 48h
- Review of VERIFIED accounts: semi-annually
- PROVISIONAL accounts without activity >30 days: notify or archive

---

# 🇵🇹 PORTUGUÊS

## Princípio Fundacional

> "A verificação não é solicitada. É concedida."

A verificação no WINDI-SITES não é um direito automático.
É uma decisão soberana do Human Dragon, baseada em critérios objectivos
e documentados. O sistema é fail-closed — o estado default é PROVISIONAL.

---

## Critérios de Verificação (PROVISIONAL → VERIFIED)

### Critério 1 — Entidade Legítima
- [ ] Nome legal corresponde a entidade registada
- [ ] País declarado é consistente com o identificador fiscal
- [ ] NIF/VAT tem formato válido para o país indicado
- [ ] Tipo de entidade (law_firm / corporation / individual) é coerente

### Critério 2 — Responsável Legal Identificável
- [ ] Nome completo do admin é real e verificável
- [ ] Email institucional (não gmail/hotmail/yahoo para law_firm)
- [ ] Email e entidade pertencem ao mesmo domínio (preferencial)

### Critério 3 — Consentimentos Completos
- [ ] consent_ledger = 1 (aceita registo no Ledger)
- [ ] consent_ai = 1 (compreende que IA não decide)
- [ ] eu_ai_act_art14 = 1 (supervisão humana confirmada)

### Critério 4 — DID Gerado Correctamente
- [ ] DID no formato did:windi:{uuid-v4}
- [ ] Fingerprint SHA-256 presente
- [ ] Public key Ed25519 registada

### Critério 5 — Sem Red Flags
- [ ] Email não consta em listas de spam conhecidas
- [ ] Entidade não tem nome genérico/suspeito
- [ ] Não há duplicados no sistema (mesmo email ou NIF)

---

## Tabela de Decisão

| Critérios cumpridos | Decisão           | Acção                    |
|---------------------|-------------------|--------------------------|
| 5/5                 | VERIFICAR         | POST /law/admin/verify/  |
| 4/5 (C5 em falta)   | VERIFICAR+Nota    | Registar observação      |
| 3/5 ou menos        | RECUSAR           | Ver refusal-process.md   |
| Red flag activo     | SUSPENDER         | UPDATE status=SUSPENDED  |

---

## Periodicidade de Revisão

- Novos registos: avaliar em até 48h
- Revisão de contas VERIFIED: semestral
- Contas PROVISIONAL sem actividade >30 dias: notificar ou arquivar

---

Liga IA+H · Kempten, Bavaria · 2026
"AI processes. Human decides. WINDI guarantees."
