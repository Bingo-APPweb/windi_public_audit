# WINDI-KEYGEN-001 — Key Provenance Block Schema

**Version:** 1.0
**Status:** DRAFT — Pending §202 Seal
**Date:** 2026-04-24
**Type:** key_provenance_block

---

## Purpose

This document defines the schema for the `WINDI-KEYGEN-001` receipt,
which serves as the cryptographic birth certificate for the Forensic
Ledger Ed25519 keypair.

---

## Schema

```json
{
  "receipt_id": "WINDI-KEYGEN-001-20260424",
  "type": "key_provenance_block",
  "timestamp_utc": "2026-04-24T[HH:MM:SS]Z",

  "ceremony": {
    "pk": "base64:[32 bytes Ed25519 public key]",
    "pk_fingerprint": "sha256:[64 hex chars]",
    "algorithm": "Ed25519-RFC8032",
    "generator_did": "did:windi:dragon-001",
    "entropy_source": "Python secrets.token_bytes(32)",
    "location": "Kempten, Bavaria, Deutschland",
    "witnessed_by": [
      "Guardian (Constitutional Protection)",
      "Architect (Technical Validation)",
      "Witness (Observation and Record)"
    ]
  },

  "bootstrap_anchors": {
    "github_commit": "[commit hash, pending]",
    "github_repo": "windi-publishing/windi-verifier",
    "zenodo_doi": "[DOI, pending]",
    "zenodo_url": "[URL, pending]"
  },

  "bootstrap_disclosure": "This receipt is signed by the key it attests. Self-attestation is acknowledged. Trust is established through public anchoring of the public key in multiple independent repositories (GitHub, Zenodo) that are outside WINDI's unilateral control.",

  "governance": {
    "human_dragon_did": "did:windi:dragon-001",
    "human_dragon_sig": "base64:[signature over ceremony + bootstrap_anchors + bootstrap_disclosure]",
    "approval_timestamp_utc": "2026-04-24T[HH:MM:SS]Z",
    "invariants": ["I9", "I11"]
  },

  "ed25519_sig": "base64:[signature over all above fields]"
}
```

---

## Field Descriptions

### ceremony

| Field | Description |
|-------|-------------|
| `pk` | The Ed25519 public key in base64 encoding |
| `pk_fingerprint` | SHA-256 hash of the raw public key bytes |
| `algorithm` | Signature algorithm identifier |
| `generator_did` | DID of the human who initiated generation |
| `entropy_source` | Description of randomness source |
| `location` | Physical location of ceremony |
| `witnessed_by` | List of Liga IA+H witnesses |

### bootstrap_anchors

| Field | Description |
|-------|-------------|
| `github_commit` | Git commit hash containing pk |
| `github_repo` | Repository path |
| `zenodo_doi` | Digital Object Identifier |
| `zenodo_url` | Direct URL to Zenodo record |

### bootstrap_disclosure

Plain text acknowledgment that this receipt is self-attesting.
This field exists specifically to make the bootstrap problem visible
rather than hidden.

### governance

| Field | Description |
|-------|-------------|
| `human_dragon_did` | DID of approving human |
| `human_dragon_sig` | Human's signature (signs before system) |
| `approval_timestamp_utc` | When human approved |
| `invariants` | Constitutional invariants enforced |

### ed25519_sig

System signature over the entire payload (excluding this field).
This signature uses the key being attested — the bootstrap moment.

---

## Signature Order

```
1. Construct payload without signatures
2. Human Dragon signs → human_dragon_sig
3. Add human_dragon_sig to payload
4. System signs (payload + human_dragon_sig) → ed25519_sig
5. Final receipt complete
```

---

## Verification

A third party verifies WINDI-KEYGEN-001 by:

1. Obtaining pk from bootstrap_anchors (GitHub or Zenodo)
2. Verifying ed25519_sig against pk
3. Verifying human_dragon_sig against known Human Dragon public key
4. Confirming bootstrap_anchors point to matching pk

If all pass, the key provenance is established.

---

## Connection to Cutover Block

The Cutover Block (WINDI-CUTOVER-001) references this receipt:

```json
{
  "cryptographic_era": {
    "key_provenance_receipt_id": "WINDI-KEYGEN-001-20260424",
    ...
  }
}
```

This creates a verifiable link from the Cutover Block back to the
key's birth certificate.

---

*Liga IA+H — Kempten, Bavaria · 2026*
