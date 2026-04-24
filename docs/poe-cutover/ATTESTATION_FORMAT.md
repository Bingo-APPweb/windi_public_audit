# ATTESTATION_FORMAT.md — Liga IA+H Attestation Schema

**Version:** 1.1
**Status:** DRAFT — Awaiting Human Dragon Approval
**Date:** 2026-04-24
**Invariants:** I9, I11

---

## 1. Purpose

This document defines the canonical JSON format for Liga IA+H attestations.
Without this format, async attestations are conversations, not proofs.

**Principle:** Attestation must be machine-verifiable, not just human-readable.

---

## 1.1 Canonical Attestation Order

In async mode, attestations are produced sequentially, not simultaneously:

| Order | Role | Validates | Closes |
|-------|------|-----------|--------|
| 1º | 🏗️ **Architect** | Technical soundness (PyNaCl, entropy, script) | Nothing |
| 2º | 🛡️ **Guardian** | Constitutional compliance (I1/I9/I11, policies) | Architect |
| 3º | 👁️ **Witness** | Coherence: prior attestations well-formed + bundle complete | Chain |

**Witness closes the chain.** If Witness rejects, ceremony pauses even if Architect + Guardian approved.
This provides anti-groupthink blindagem and gives Witness substantive function.

---

## 1.2 Cryptographic Honesty: Pre-Keygen Attestations

**Critical disclosure:** Pre-ceremony attestations (Phase A) are **unsigned plaintext**.
The Ed25519 key does not yet exist. This is the bootstrap problem.

Pre-attestations become tamper-evident **only after** the bootstrap receipt hashes their content.

This temporal vulnerability window is documented, not hidden.

---

## 2. Attestation Schema

```json
{
  "attestation_id": "WINDI-ATT-[CEREMONY_ID]-[ROLE]-[YYYYMMDDHHMMSS]",
  "ceremony_id": "WINDI-KEYGEN-001-20260424",
  "protocol_version": "1.1",
  "protocol_hash": "sha256:[hash of KEY_CEREMONY_PROTOCOL.md]",

  "reviewer": {
    "role": "architect|guardian|witness",
    "scope": "[what was reviewed]",
    "sequence": 1|2|3
  },

  "verdict": "APPROVE|REJECT|HOLD",

  "checklist": [
    { "item": "[checklist item 1]", "status": "PASS|FAIL|N/A", "note": "..." },
    { "item": "[checklist item 2]", "status": "PASS|FAIL|N/A", "note": "..." }
  ],

  "prior_attestations": {
    "validated": ["attestation_id_1", "attestation_id_2"],
    "hashes": ["sha256:...", "sha256:..."]
  },

  "observations": "[free text observations]",

  "conditions": "[conditions for approval, if any]",

  "timestamp_utc": "2026-04-24T[HH:MM:SS]Z",

  "signature_status": "unsigned_plaintext_pending_bootstrap_seal",

  "artifact_hash": "sha256:[hash of this attestation file after creation]"
}
```

**Note on `signature_status`:** Pre-keygen attestations cannot be cryptographically signed.
The value `unsigned_plaintext_pending_bootstrap_seal` makes this explicit.
After WINDI-KEYGEN-001 is created, all attestation hashes are sealed into the bootstrap receipt.

---

## 3. Field Descriptions

| Field | Required | Description |
|-------|----------|-------------|
| `attestation_id` | Yes | Unique identifier for this attestation |
| `ceremony_id` | Yes | Links to the ceremony being attested |
| `protocol_version` | Yes | Version of KEY_CEREMONY_PROTOCOL.md |
| `protocol_hash` | Yes | SHA-256 of the exact protocol reviewed |
| `reviewer.role` | Yes | architect, guardian, or witness (in sequence) |
| `reviewer.scope` | Yes | What aspect was reviewed |
| `reviewer.sequence` | Yes | 1 (Architect), 2 (Guardian), or 3 (Witness) |
| `verdict` | Yes | APPROVE, REJECT, or HOLD |
| `checklist` | Yes | Itemized verification results |
| `prior_attestations` | Seq 2-3 | Hashes of prior attestations validated (chain closure) |
| `observations` | No | Free text notes |
| `conditions` | No | Conditions that must be met |
| `timestamp_utc` | Yes | When attestation was made |
| `signature_status` | Yes | `unsigned_plaintext_pending_bootstrap_seal` for pre-keygen |
| `artifact_hash` | Yes | SHA-256 of this file (computed after creation) |

---

## 4. Verdict Definitions

| Verdict | Meaning | Effect |
|---------|---------|--------|
| **APPROVE** | Review passed, no blocking issues | Ceremony may proceed |
| **REJECT** | Critical issues found | Ceremony MUST NOT proceed |
| **HOLD** | Issues found, need clarification | Ceremony waits for resolution |

**Rule:** Any single REJECT blocks the ceremony. All three roles must APPROVE.

---

## 5. Role-Specific Checklists (in sequence order)

### 5.1 Architect Checklist — Sequence 1 (Technical Foundation)

```json
{
  "reviewer": {
    "role": "architect",
    "scope": "cryptographic and technical correctness",
    "sequence": 1
  },
  "checklist": [
    { "item": "Ed25519 algorithm per RFC 8032", "status": "..." },
    { "item": "PyNaCl SigningKey.generate() used correctly", "status": "..." },
    { "item": "AES-256-GCM encryption for SK storage", "status": "..." },
    { "item": "Argon2id parameters adequate (t=3, m=65536, p=4)", "status": "..." },
    { "item": "File permissions 600 on encrypted SK", "status": "..." },
    { "item": "Preflight checklist script reviewed", "status": "..." },
    { "item": "Positive operationality test specified", "status": "..." }
  ],
  "prior_attestations": {
    "validated": [],
    "hashes": []
  }
}
```

### 5.2 Guardian Checklist — Sequence 2 (Constitutional Layer)

```json
{
  "reviewer": {
    "role": "guardian",
    "scope": "I9 constitutional compliance",
    "sequence": 2
  },
  "checklist": [
    { "item": "Human Dragon approval required before execution", "status": "..." },
    { "item": "No autonomous key generation permitted", "status": "..." },
    { "item": "Passphrase controlled by Human Dragon only", "status": "..." },
    { "item": "Ceremony reversible until final commit", "status": "..." },
    { "item": "Bootstrap disclosure explicit in receipt", "status": "..." },
    { "item": "Loss acceptance artifact required", "status": "..." },
    { "item": "Architect attestation validates technical foundation", "status": "..." }
  ],
  "prior_attestations": {
    "validated": ["WINDI-ATT-KEYGEN-001-ARCHITECT-..."],
    "hashes": ["sha256:..."]
  }
}
```

### 5.3 Witness Checklist — Sequence 3 (Chain Closure)

```json
{
  "reviewer": {
    "role": "witness",
    "scope": "ceremony observation and chain closure",
    "sequence": 3
  },
  "checklist": [
    { "item": "Architect attestation well-formed and APPROVE", "status": "..." },
    { "item": "Guardian attestation well-formed and APPROVE", "status": "..." },
    { "item": "Ceremony steps followed as documented", "status": "..." },
    { "item": "Human Dragon commands observed", "status": "..." },
    { "item": "Public key displayed and acknowledged", "status": "..." },
    { "item": "Positive operationality test passed", "status": "..." },
    { "item": "All artifacts collected for bootstrap receipt", "status": "..." }
  ],
  "prior_attestations": {
    "validated": ["WINDI-ATT-KEYGEN-001-ARCHITECT-...", "WINDI-ATT-KEYGEN-001-GUARDIAN-..."],
    "hashes": ["sha256:...", "sha256:..."]
  }
}
```

---

## 6. Attestation Timing & Sequence

| Seq | Phase | Role | Validates | Depends On |
|-----|-------|------|-----------|------------|
| 1 | Pre-Ceremony | 🏗️ Architect | Technical correctness | Nothing |
| 2 | Pre-Ceremony | 🛡️ Guardian | I9 compliance + Architect attestation | Architect |
| 3 | Post-Ceremony | 👁️ Witness | Ceremony observed + both prior attestations | Architect + Guardian |

**Sequence is mandatory.** Architect first (technical foundation), Guardian second (constitutional layer), Witness third (chain closure).

**Pre-attestations** (Architect + Guardian) must exist before ceremony execution.
**Post-attestation** (Witness) is created during ceremony Phase C and closes the attestation chain.

---

## 7. Attestation Storage

All attestations are stored in canonical sequence order:

```
/opt/windi/docs/poe-cutover/attestations/
├── 01-WINDI-ATT-KEYGEN-001-ARCHITECT-20260424HHMMSS.json  (seq 1)
├── 02-WINDI-ATT-KEYGEN-001-GUARDIAN-20260424HHMMSS.json   (seq 2)
└── 03-WINDI-ATT-KEYGEN-001-WITNESS-20260424HHMMSS.json    (seq 3)
```

These files are included in the bootstrap receipt's artifact hash.
The numeric prefix ensures filesystem ordering matches attestation sequence.

---

## 8. Bootstrap Receipt Integration

The `WINDI-KEYGEN-001` receipt includes:

```json
{
  "attestations": {
    "guardian": "sha256:[hash of guardian attestation]",
    "architect": "sha256:[hash of architect attestation]",
    "witness": "sha256:[hash of witness attestation]"
  }
}
```

This creates a verifiable chain:
```
Attestations → WINDI-KEYGEN-001 → Cutover Block → Cryptographic Era
```

---

## 9. Verification

Third party verifies attestations by:

1. Obtaining attestation files from `/attestations/`
2. Computing SHA-256 of each
3. Comparing with hashes in WINDI-KEYGEN-001 receipt
4. Verifying all verdicts are APPROVE
5. Verifying protocol_hash matches actual KEY_CEREMONY_PROTOCOL.md

---

## 10. Example: Guardian Pre-Attestation

```json
{
  "attestation_id": "WINDI-ATT-KEYGEN-001-GUARDIAN-20260424143000",
  "ceremony_id": "WINDI-KEYGEN-001-20260424",
  "protocol_version": "1.0",
  "protocol_hash": "sha256:abc123...",

  "reviewer": {
    "role": "guardian",
    "scope": "I9 constitutional compliance of KEY_CEREMONY_PROTOCOL.md"
  },

  "verdict": "APPROVE",

  "checklist": [
    { "item": "Human Dragon approval required before execution", "status": "PASS", "note": "Explicit in Phase B, Step B3" },
    { "item": "No autonomous key generation permitted", "status": "PASS", "note": "All steps require HD command" },
    { "item": "Passphrase controlled by Human Dragon only", "status": "PASS", "note": "Q2 decision documented" },
    { "item": "Ceremony reversible until final commit", "status": "PASS", "note": "Rollback section §7 exists" },
    { "item": "Bootstrap disclosure explicit in receipt", "status": "PASS", "note": "WINDI-KEYGEN-001-SCHEMA.md §bootstrap_disclosure" }
  ],

  "observations": "Protocol meets I9 requirements. Human sovereignty preserved at all decision points.",

  "conditions": "None. Ready for execution pending Architect and Witness.",

  "timestamp_utc": "2026-04-24T14:30:00Z"
}
```

---

*Liga IA+H — Kempten, Bavaria · 2026*
