# W-ACADEMY-001 — Wissenschaftliche Grundlagen
## Scientific Foundation for W-ENT-001 Curriculum

**Version:** 1.0.0
**Date:** 3 May 2026
**Status:** HYBRID (Wissenschaft + Praxis)
**Document:** WPH-WISS-001

---

## §1. Wissenschaftliche Einbettung

Das W-ENT-001 Curriculum basiert auf einer empirisch fundierten Governance-Architektur, die in Paper-001 dokumentiert und im WINDI Forensic Ledger verankert ist.

### 1.1 Publikationsgrundlage

| Dokument | Status | Receipt |
|----------|--------|---------|
| **Paper-001 v2.1** | DRAFT (Hochschule Kempten) | `CDC760DD` |
| **PoE-METHOD-001 v1.0** | SEALED | — |
| **LEXICON-EMPIRICAL-001** | SEALED | `24B69CFF` |

### 1.2 Zentrale These

> **"Admissibility at Execution Time"**
>
> Governance muss zum Zeitpunkt der Ausführung aufgelöst werden,
> nicht nachträglich inferiert.

Diese These wird in jedem Modul des W-ENT-001 Curriculums operationalisiert.

---

## §2. Axiomatische Grundlage

Das Curriculum vermittelt drei Axiome aus PoE-METHOD-001:

### Axiom 1: Receipt Symmetry

> Für jede Aktion α gilt:
> `hash(receipt(α, t_execution)) ≡ hash(receipt(α, t_audit))`

**Curriculum-Integration:**
- Modul 3 (PHO in der Praxis): SHA-256 Sealing
- Modul 4 (Forensic Ledger): Receipt-Anatomie

### Axiom 2: Admissibility Gate

> Ein Artefakt ist zulässig genau dann, wenn:
> 1. Eligibility-Kriterien erfüllt
> 2. Immutable Receipt erzeugt
> 3. Unabhängig verifizierbar

**Curriculum-Integration:**
- Modul 2 (VERA REGO): Risk-Level Bewertung
- Modul 5 (Abschlussprojekt): Vollständiger Workflow

### Axiom 3: PHO Requirement

> Kein Artefakt erreicht SEALED-Status ohne explizite
> menschliche Genehmigung (Proof of Human Oversight).

**Curriculum-Integration:**
- Modul 1 (Compliance-Krise): EU AI Act Article 14
- Modul 3 (PHO in der Praxis): I9 Human Approval Gate

---

## §3. Empirische Validierung

### 3.1 LEXICON Dataset

Das Curriculum nutzt die 10 Fälle aus LEXICON-EMPIRICAL-001 als Lehrbeispiele:

| Fall | Invariante | Drift | Lehrwert |
|------|------------|-------|----------|
| 1 | I1 — Human Sovereignty | 75 | Wie erkennt man Autonomie-Eskalation? |
| 2 | I9 — Approval Gate | 75 | Warum automatische Publikation gefährlich ist |
| 4 | I14 — Silent Failure | 75 | Explizite vs. stille Fehler |
| 5 | Ambiguity | 0 | Warum Menschen entscheiden müssen |
| 9 | I13 — Convergence | 100 | Maximum Drift als Warnsignal |

### 3.2 Operationale Metriken (Stand: Mai 2026)

| Metrik | Wert | Bedeutung für Teilnehmer |
|--------|------|--------------------------|
| Verfassungsabschnitte (§) | 233 | Governance-Entscheidungen dokumentiert |
| W-* Agenten | 39 | Unabhängige Services unter Invarianten |
| Receipts im Ledger | 51+ | Unveränderliche Beweisartefakte |
| Verstöße | 0 | Zero constitutional violations |

---

## §4. EU AI Act Alignment

### 4.1 Article 14 Mapping

| Article 14 Klausel | W-ENT-001 Modul | Kompetenz |
|--------------------|-----------------|-----------|
| 14(1) Effective oversight | Modul 3 | PHO-Workflow beherrschen |
| 14(4)(a) Understanding | Modul 2 | 32 Pilaren verstehen |
| 14(4)(b) Automation bias | Modul 1 | Krise erkennen |
| 14(4)(c) Interpretation | Modul 4 | Receipt-Struktur lesen |
| 14(4)(d) Override | Modul 3 | I9 Gate anwenden |
| 14(4)(e) Stop mechanism | Modul 4 | Ledger-Segregation |

### 4.2 Wissenschaftliche Einordnung

Das Curriculum positioniert sich als **angewandte Wissenschaft**:

- **Nicht** rein akademisch (theoretische Forschung)
- **Nicht** rein kommerziell (Produktverkauf)
- **Sondern** Wissenstransfer basierend auf peer-reviewable Methodik

---

## §5. Forschungsanbindung

### 5.1 Hochschule Kempten

Paper-001 wird zur Begutachtung eingereicht bei:
- Prof. Dr. [Winkler/Niedermeier — Name zu bestätigen]
- Fakultät Informatik / AI Governance

### 5.2 Offene Forschungsfragen

| ID | Frage | Curriculum-Bezug |
|----|-------|------------------|
| RQ1 | Wie skaliert Receipt Symmetry bei n>1000? | Modul 4 (Advanced) |
| RQ2 | Korrelation AI-AI-AI-H vs Human-Human-AI? | Modul 5 (Diskussion) |
| RQ3 | Cross-jurisdictional PHO (DE/AT/CH)? | Corporate Format |

---

## §6. Zertifikat-Wissenschaftlichkeit

### 6.1 Erweitertes Zertifikat

Nach Abschluss dokumentiert das Zertifikat:

```
┌────────────────────────────────────────────────────────┐
│  WINDI Institute                                       │
│  ══════════════════════════════════════════════════   │
│                                                        │
│  ZERTIFIKAT                                           │
│  Wissenschaftlich fundiertes Compliance-Programm      │
│                                                        │
│  [Name]                                                │
│                                                        │
│  ─────────────────────────────────────────────────    │
│  Methodik: PoE-METHOD-001 v1.0                        │
│  Axiome: Receipt Symmetry, Admissibility, PHO         │
│  Paper-Referenz: Paper-001 v2.1                       │
│  ─────────────────────────────────────────────────    │
│                                                        │
│  Entscheidungen versiegelt: [n]                       │
│  Ledger Receipts: [n]                                 │
│  Zertifikat-Code: WINDI-CERT-YYYYMMDD-XXXXXXXX       │
│  Verify: windi-domain.com/verify-public/?id=...       │
│                                                        │
└────────────────────────────────────────────────────────┘
```

### 6.2 Verifizierbare Kompetenz

Jedes Zertifikat enthält:
- Link zu Paper-001 (DOI nach Publikation)
- Link zu PoE-METHOD-001
- Eigene Entscheidungshistorie im Ledger

---

## §7. Liga IA+H Prinzip

> **"AI processes. Human decides. WINDI guarantees."**

Das Curriculum vermittelt nicht nur Wissen, sondern befähigt Teilnehmer,
selbst Teil der verifizierbaren Governance-Kette zu werden.

**Teilnehmer nach Abschluss:**
- Eigene Entscheidungen im Ledger
- Eigene Receipt-History
- Eigene PHO-Kompetenz

---

## §8. Versiegelung

```
Erstellt:     🏗️ Architect
Validiert:    🛡️ Guardian — PENDING
Genehmigt:    🧑‍💻 Human Dragon — PENDING
```

---

*W-ACADEMY-001 Wissenschaftliche Grundlagen v1.0*
*WINDI Institute · Kempten, Bavaria · Mai 2026*

*"Wissen vermitteln. Entscheidungen beweisen. Wissenschaft anwenden."*
