# WINDI DeepDOCFakes — Document Security Division

## Mission

Guarantee that a document is not merely well-formatted, but **verifiably legitimate in its institutional origin**.

> "We don't protect the appearance of the document.  
> We protect the institutional existence of it."

## Threat Model

**Document Deepfake Risk**: AI systems can generate documents that perfectly replicate institutional communication — letterheads, tone, terminology, formatting — without any institutional authorization. This creates a new category of fraud: **institutional identity forgery without malicious code**.

```
Before WINDI:  "This PDF looks real"
After  WINDI:  "This document is verifiably generated within 
                a governed institutional system"
```

A deepfake copies **text and layout**.  
It cannot copy **structural governance markers** because:
1. The canonical field order is system-internal
2. The hash chain includes server identity and timestamp
3. The governance context is not visible in the document
4. The provenance ID is generated at creation time

## Architecture

```
/opt/windi/engine/deepdocfakes/
├── __init__.py              — Package definition & exports
├── structural_hash.py       — Canonical structural fingerprinting
├── provenance_engine.py     — Digital birth certificate generation
├── verify_engine.py         — VALID | UNKNOWN | TAMPERED verification
├── deepfake_risk.py         — Resilience scoring (0-100)
├── pdf_metadata_embed.py    — XMP/custom metadata for PDFs
├── registry_provenance.py   — Registry management & audit
└── README.md                — This file

/opt/windi/provenance/
├── records/                 — Provenance record JSON files
└── index.json               — Fast lookup index
```

## Invariants

1. **Every HIGH document MUST have a provenance record** — no exceptions
2. **Structural hashes are deterministic** — same input always produces same hash
3. **Provenance records are immutable** — once written, never modified
4. **Verification is stateless** — any party with the hash can verify
5. **Jurisdiction is bound** — all records tied to German infrastructure

## Protocol: WINDI-SOF-v1

**S**ecure **O**rigin **F**ramework, version 1.

### Provenance Record Structure

```json
{
  "provenance_id": "WINDI-PROV-XXXXXXXXXXXX",
  "submission_id": "REG-20260202-0001",
  "governance_context": {
    "level": "HIGH",
    "isp_profile": "bafin",
    "policy_version": "2.2.0"
  },
  "cryptographic_proof": {
    "structural_hash": "sha256...",
    "provenance_hash": "sha256...",
    "hash_chain": "abcd1234→efgh5678"
  },
  "deepfake_resilience": {
    "score": 100,
    "rating": "MAXIMUM — Forensic-grade provenance"
  }
}
```

### Verification Protocol

```
POST /api/verify
  Input:  { submission_id, decision_payload }
  Output: { status: VALID | UNKNOWN | TAMPERED, checks: {...} }
```

### Resilience Scoring

| Score  | Rating  | Typical Level |
|--------|---------|---------------|
| 85-100 | MAXIMUM | HIGH + all features |
| 60-84  | HIGH    | HIGH standard / MEDIUM + identity |
| 40-59  | MEDIUM  | MEDIUM standard |
| 20-39  | LOW     | LOW with provenance |
| 0-19   | MINIMAL | LOW without provenance |

## Governance Level Policy

| Feature | HIGH | MEDIUM | LOW |
|---------|------|--------|-----|
| Provenance record | **Required** | Optional | — |
| Registry entry | **Required** | Optional | — |
| Structural hash | Strict | Strict | Basic |
| PDF metadata embed | Yes | Yes | No |
| Verify endpoint | Yes | Yes | No |
| Forensic ledger | Yes | — | — |
| Tamper evidence | Yes | — | — |
| Four-eyes principle | Yes | — | — |

## EU AI Act Alignment

- **Article 12** — Record-Keeping: provenance records provide complete audit trail
- **Article 14** — Human Oversight: four-eyes principle in HIGH governance
- **Article 50** — Transparency: identity governance prevents misleading AI content

## Three Dragons Contribution

| Dragon | Role | Contribution |
|--------|------|-------------|
| Guardian (Claude) | Core engine, scoring, verification | `provenance_engine.py`, `verify_engine.py`, `deepfake_risk.py` |
| Architect (GPT) | Modular structure, API contracts, threat model | Package design, `structural_hash.py`, endpoint spec |
| Witness (Gemini) | Future: independent verification attestation | Planned: cross-validation protocol |

## Version

- Module: WINDI DeepDOCFakes v1.0.0
- Protocol: WINDI-SOF-v1
- Date: 02 February 2026
- Division: Document Security Division
- Publisher: WINDI Publishing House — Kempten (Allgäu), Bavaria, Germany
