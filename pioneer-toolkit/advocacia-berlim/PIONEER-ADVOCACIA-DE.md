# WINDI Pioneer · Sector Advocacia
## Berlin · Deutschland · Deutsch / English

---

## Das Problem, das WINDI für Sie löst
## The Problem WINDI solves for you

Anwälte arbeiten täglich mit Dokumenten, deren Echtheit
angefochten werden kann. Ein Screenshot ist kein Beweis.
Eine E-Mail kann gefälscht sein. Ein PDF hat kein Datum.

Lawyers work daily with documents whose authenticity
can be challenged. A screenshot is not evidence.
An email can be forged. A PDF has no verifiable timestamp.

**Mit WINDI / With WINDI:**
Jedes Dokument erhält einen forensischen Hash,
der vor einem deutschen Gericht standhält (ZPO-konform).

Every document receives a forensic hash
that holds up in German court (ZPO-compliant).

---

## Schritt 1 / Step 1 — API Key erhalten / Get API Key

```bash
./shared/get_api_key.sh "Kanzlei Berlin" NODAL
```

Oder manuell / Or manually:

```bash
curl -X POST https://windi-domain.com/api-keys/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Kanzlei Berlin Pioneer",
    "tier": "NODAL",
    "description": "Anwaltskanzlei Berlin — Pioneer Program"
  }'
```

---

## Schritt 2 / Step 2 — Dokument atomisieren / Atomize document

```bash
python3 atomize_advocacia.py vertrag.pdf
```

---

## Was der Richter sieht / What the judge sees

```
┌─────────────────────────────────────────────────┐
│  WINDI · VERIFIZIERT / VERIFIED                 │
│                                                 │
│  Kanzlei:    Berlin Pioneer                     │
│  Datum:      15 Mar 2026 · 14:32 UTC            │
│  Schema:     LEGAL                              │
│  Compliance: ZPO, eIDAS                         │
│  Hash:       a7b3c9d2...                        │
│                                                 │
│  Dieses Dokument ist authentisch                │
│  und wurde nicht verändert.                     │
│                                                 │
│  This document is authentic                     │
│  and has not been altered.                      │
└─────────────────────────────────────────────────┘
```

---

## Anwendungsfälle / Use Cases

| Situation | Was atomisieren | Wert |
|-----------|----------------|------|
| Beweissicherung | Screenshot, Foto | Datum + Hash = Beweis |
| Vertragsabschluss | PDF Unterzeichnet | Zeitstempel irrefutável |
| Gutachten | Expertendokument | Verfälschungsschutz |
| Mandantenkommunikation | E-Mail Export | Nachweisbar zugestellt |

---

## Invariante I5 — ZPO-Relevanz

Der SHA-256 Hash des Dokuments wird im WINDI Forensic Ledger
permanent gespeichert. Jede nachträgliche Änderung des Dokuments
erzeugt einen anderen Hash — die Fälschung wird sofort erkennbar.

**Konform mit:**
- ZPO §§ 415-444 (Urkundenbeweis)
- eIDAS Regulation (EU 910/2014)
- GDPR Art. 5(1)(f) (Integrität)

---

## Support

- Email: pioneer@windi-domain.com
- Sector: ADVOCACIA_BERLIM
- Tier: NODAL

*"AI processes. Human decides. WINDI guarantees."*
