# WINDI-TRAVEL — Refusal Process v1.0
# Status: CANONICAL · Trilingual (DE | EN | PT)
# Date: 2026-03-24 · Liga IA+H

---

# 🇩🇪 DEUTSCH

## Grundprinzip

Die Ablehnung ist ein souveräner und dokumentierter Akt.
Es ist keine Bestrafung — es ist der Schutz des WINDI-TRAVEL-Ökosystems
und der bereits verifizierten Entitäten darin.

---

## Nicht-Verifizierungs-Zustände

```
PROVISIONAL  → Ausgangszustand nach Registrierung
REFUSED      → Dokumentierte Ablehnung durch Human Dragon
SUSPENDED    → Vorübergehende Sperrung (Untersuchung)
REVOKED      → Verifizierung nach Erteilung entzogen
```

---

## Ablehnungsprozess (PROVISIONAL → REFUSED)

### Schritt 1 — Grund identifizieren
Konsultiere risk-matrix.md und verification-criteria.md.
Dokumentiere das nicht erfüllte Kriterium.

### Schritt 2 — Im audit-log.json registrieren
```json
{
  "timestamp": "2026-03-24T19:00:00Z",
  "did": "did:windi:xxxxxxxx",
  "entity": "Name der Entität",
  "decision": "REFUSED",
  "criteria_failed": ["C2 - keine institutionelle E-Mail", "C5 - Red Flag doppelt"],
  "notes": "Beobachtung des Human Dragon",
  "decided_by": "Jober Mogele Correa"
}
```

### Schritt 3 — Status in der DB aktualisieren
```sql
UPDATE admins SET status = 'REFUSED' WHERE did = ?;
```

### Schritt 4 — Im Ledger versiegeln (optional für HIGH RISK Ablehnungen)
```bash
curl -X POST http://127.0.0.1:8101/api/receipts \
  -H "Content-Type: application/json" \
  -d '{
    "id": "WINDI-TRAVEL-REFUSED-{did[:8].upper()}",
    "actor": "Jober Mogele Correa",
    "app": "windi-travel",
    "doc_name": "Identität abgelehnt — {entity}",
    "doc_type": "doc",
    "governance_level": "HIGH"
  }'
```

### Schritt 5 — Benachrichtigung (optional)
Wenn die E-Mail gültig ist und die Ablehnung auf ein korrigierbares Kriterium zurückzuführen ist,
benachrichtige die Entität mit den Schritten zur erneuten Einreichung.

---

## Suspendierungsprozess (→ SUSPENDED)

Verwendet, wenn Zweifel bestehen, aber keine klaren Beweise für böswilliges Verhalten.

- Maximale Dauer: 14 Tage
- Nach 14 Tagen ohne Klärung: Hochstufen zu REFUSED
- Bei zufriedenstellender Klärung: Hochstufen zu VERIFIED

---

## Widerrufsprozess (VERIFIED → REVOKED)

Fälle, die den Widerruf einer bereits erteilten Verifizierung rechtfertigen:
- Entität wurde aufgelöst oder hat Insolvenz angemeldet
- Feststellung falscher Daten bei der Registrierung
- Nutzung des Systems unter Verletzung der Bedingungen
- Freiwilliger Antrag der Entität selbst

### Widerrufsschritt
```sql
UPDATE admins SET status = 'REVOKED' WHERE did = ?;
```
Versiegelung im Ledger obligatorisch — I11: kryptographische Permanenz.

---

## Reaktivierung nach Ablehnung

Eine REFUSED-Entität kann erneut einreichen, wenn:
- Das fehlgeschlagene Kriterium korrigiert wurde
- Mindestens 30 Tage vergangen sind
- Keine Red Flags bei der neuen Registrierung vorhanden sind

Prozess: Neue Registrierung → Neue DID → Neuer Verifizierungszyklus.

---

# 🇬🇧 ENGLISH

## Foundational Principle

Refusal is a sovereign and documented act.
It is not punishment — it is protection of the WINDI-TRAVEL ecosystem
and the entities already verified within it.

---

## Non-Verification States

```
PROVISIONAL  → Initial state after registration
REFUSED      → Documented refusal by Human Dragon
SUSPENDED    → Temporary suspension (investigation)
REVOKED      → Verification removed after being granted
```

---

## Refusal Process (PROVISIONAL → REFUSED)

### Step 1 — Identify reason
Consult risk-matrix.md and verification-criteria.md.
Document the criterion not met.

### Step 2 — Register in audit-log.json
```json
{
  "timestamp": "2026-03-24T19:00:00Z",
  "did": "did:windi:xxxxxxxx",
  "entity": "Entity Name",
  "decision": "REFUSED",
  "criteria_failed": ["C2 - non-institutional email", "C5 - duplicate red flag"],
  "notes": "Human Dragon observation",
  "decided_by": "Jober Mogele Correa"
}
```

### Step 3 — Update status in DB
```sql
UPDATE admins SET status = 'REFUSED' WHERE did = ?;
```

### Step 4 — Seal in Ledger (optional for HIGH RISK refusals)
```bash
curl -X POST http://127.0.0.1:8101/api/receipts \
  -H "Content-Type: application/json" \
  -d '{
    "id": "WINDI-TRAVEL-REFUSED-{did[:8].upper()}",
    "actor": "Jober Mogele Correa",
    "app": "windi-travel",
    "doc_name": "Identity Refused — {entity}",
    "doc_type": "doc",
    "governance_level": "HIGH"
  }'
```

### Step 5 — Notification (optional)
If the email is valid and the refusal is due to a correctable criterion,
notify the entity with steps for resubmission.

---

## Suspension Process (→ SUSPENDED)

Used when there is doubt but no clear evidence of bad faith.

- Maximum duration: 14 days
- After 14 days without clarification: promote to REFUSED
- If satisfactory clarification: promote to VERIFIED

---

## Revocation Process (VERIFIED → REVOKED)

Cases that justify revoking an already granted verification:
- Entity was dissolved or declared bankruptcy
- Discovery of false data in registration
- Use of the system in violation of terms
- Voluntary request from the entity itself

### Revocation Step
```sql
UPDATE admins SET status = 'REVOKED' WHERE did = ?;
```
Seal in Ledger mandatory — I11: cryptographic permanence.

---

## Reactivation after Refusal

A REFUSED entity can resubmit if:
- The failed criterion has been corrected
- At least 30 days have passed
- No red flags in the new registration

Process: New registration → New DID → New verification cycle.

---

# 🇵🇹 PORTUGUÊS

## Princípio Fundacional

A recusa é um acto soberano e documentado.
Não é punição — é protecção do ecossistema WINDI-TRAVEL
e das entidades já verificadas dentro dele.

---

## Estados de Não-Verificação

```
PROVISIONAL  → Estado inicial após registo
REFUSED      → Recusa documentada pelo Human Dragon
SUSPENDED    → Suspensão temporária (investigação)
REVOKED      → Verificação removida após concessão
```

---

## Processo de Recusa (PROVISIONAL → REFUSED)

### Passo 1 — Identificar motivo
Consultar risk-matrix.md e verification-criteria.md.
Documentar o critério não cumprido.

### Passo 2 — Registar no audit-log.json
```json
{
  "timestamp": "2026-03-24T19:00:00Z",
  "did": "did:windi:xxxxxxxx",
  "entity": "Nome da Entidade",
  "decision": "REFUSED",
  "criteria_failed": ["C2 - email não institucional", "C5 - red flag duplo"],
  "notes": "Observação do Human Dragon",
  "decided_by": "Jober Mogele Correa"
}
```

### Passo 3 — Actualizar status no DB
```sql
UPDATE admins SET status = 'REFUSED' WHERE did = ?;
```

### Passo 4 — Selar no Ledger (opcional para recusas HIGH RISK)
```bash
curl -X POST http://127.0.0.1:8101/api/receipts \
  -H "Content-Type: application/json" \
  -d '{
    "id": "WINDI-TRAVEL-REFUSED-{did[:8].upper()}",
    "actor": "Jober Mogele Correa",
    "app": "windi-travel",
    "doc_name": "Identidade Recusada — {entity}",
    "doc_type": "doc",
    "governance_level": "HIGH"
  }'
```

### Passo 5 — Notificação (opcional)
Se o email for válido e a recusa for por critério corrigível,
notificar a entidade com os passos para resubmissão.

---

## Processo de Suspensão (→ SUSPENDED)

Usado quando há dúvida mas não evidência clara de má-fé.

- Duração máxima: 14 dias
- Após 14 dias sem clarificação: promover para REFUSED
- Se clarificação satisfatória: promover para VERIFIED

---

## Processo de Revogação (VERIFIED → REVOKED)

Casos que justificam revogar uma verificação já concedida:
- Entidade foi dissolvida ou declarou falência
- Constatação de dados falsos no registo
- Uso do sistema em violação dos termos
- Pedido voluntário da própria entidade

### Passo de Revogação
```sql
UPDATE admins SET status = 'REVOKED' WHERE did = ?;
```
Selo no Ledger obrigatório — I11: permanência criptográfica.

---

## Reactivação após Recusa

Uma entidade REFUSED pode resubmeter se:
- Corrigiu o critério que falhou
- Passaram pelo menos 30 dias
- Não há red flags no novo registo

Processo: Novo registo → Nova DID → Novo ciclo de verificação.

---

Liga IA+H · Kempten, Bavaria · 2026
"AI processes. Human decides. WINDI guarantees."
