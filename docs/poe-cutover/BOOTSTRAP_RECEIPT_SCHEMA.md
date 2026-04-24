# BOOTSTRAP_RECEIPT_SCHEMA.md — WINDI-KEYGEN-001 Complete Schema

**Version:** 1.0
**Status:** DRAFT — Awaiting Human Dragon Approval
**Date:** 2026-04-24
**Type:** Key Provenance Block

---

## 1. Purpose

This document defines the complete JSON schema for `WINDI-KEYGEN-001-20260424`,
the bootstrap receipt that anchors the entire WINDI Cryptographic Era.

**Architectural insight:** This receipt is signed by the key it attests — the bootstrap moment.
This self-attestation is explicitly acknowledged, not hidden.

---

## 2. Complete Schema

```json
{
  "receipt_id": "WINDI-KEYGEN-001-20260424",
  "type": "key_provenance_block",
  "timestamp_utc": "2026-04-24T[HH:MM:SS]Z",
  "protocol_version": "1.1",

  "ceremony": {
    "pk": "base64:[32 bytes Ed25519 public key]",
    "pk_fingerprint": "sha256:[64 hex chars]",
    "algorithm": "Ed25519-RFC8032",
    "library": "PyNaCl",
    "library_version": "[version from preflight]",
    "generator_did": "did:windi:dragon-001",
    "entropy_source": "os.urandom(32) via PyNaCl SigningKey.generate()",
    "location": "Kempten, Bavaria, Deutschland",
    "environment": "Strato VPS (87.106.29.233)"
  },

  "preflight": {
    "log_hash": "sha256:[hash of preflight_log_YYYYMMDDHHMMSS.txt]",
    "log_path": "/opt/windi/docs/poe-cutover/artifacts/preflight_log_20260424HHMMSS.txt",
    "all_checks_passed": true,
    "entropy_bits": "[value from preflight]",
    "timestamp_utc": "2026-04-24T[HH:MM:SS]Z"
  },

  "attestations": {
    "sequence": ["architect", "guardian", "witness"],
    "architect": {
      "attestation_id": "WINDI-ATT-KEYGEN-001-ARCHITECT-20260424HHMMSS",
      "verdict": "APPROVE",
      "hash": "sha256:[hash of attestation file]"
    },
    "guardian": {
      "attestation_id": "WINDI-ATT-KEYGEN-001-GUARDIAN-20260424HHMMSS",
      "verdict": "APPROVE",
      "hash": "sha256:[hash of attestation file]"
    },
    "witness": {
      "attestation_id": "WINDI-ATT-KEYGEN-001-WITNESS-20260424HHMMSS",
      "verdict": "APPROVE",
      "hash": "sha256:[hash of attestation file]",
      "closes_chain": true
    }
  },

  "loss_acceptance": {
    "artifact_type": "physical_handwritten_declaration",
    "photo_hash": "sha256:[hash of photograph]",
    "photo_path": "/opt/windi/docs/poe-cutover/artifacts/loss_acceptance_20260424.jpg",
    "language": "pt-BR",
    "signer": "Jober Mögele Correa",
    "role": "Human Dragon",
    "date": "2026-04-24"
  },

  "operationality_proof": {
    "test_message": "WINDI-KEYGEN-001 operational @ 2026-04-24T[HH:MM:SS]Z",
    "signature": "[hex signature]",
    "verified": true,
    "timestamp_utc": "2026-04-24T[HH:MM:SS]Z"
  },

  "bootstrap_anchors": {
    "github_commit": "[commit hash after publication]",
    "github_repo": "windi-publishing/windi-verifier",
    "github_branch": "main",
    "zenodo_doi": "[DOI after registration]",
    "zenodo_url": "[URL after registration]"
  },

  "bootstrap_disclosure": "This receipt is signed by the key it attests. Self-attestation is acknowledged. Trust is established through: (1) public anchoring of the public key in GitHub and Zenodo, (2) the attestation chain from Architect → Guardian → Witness, (3) the physical loss acceptance artifact, (4) the preflight environmental audit. Third parties can verify by obtaining pk from bootstrap_anchors and verifying ed25519_sig.",

  "protocol_artifacts": {
    "KEY_CEREMONY_PROTOCOL_hash": "sha256:[hash]",
    "ATTESTATION_FORMAT_hash": "sha256:[hash]",
    "PASSPHRASE_POLICY_hash": "sha256:[hash]",
    "PREFLIGHT_CHECKLIST_hash": "sha256:[hash]"
  },

  "governance": {
    "human_dragon_did": "did:windi:dragon-001",
    "human_dragon_sig": "base64:[signature over all above fields]",
    "approval_timestamp_utc": "2026-04-24T[HH:MM:SS]Z",
    "invariants": ["I1", "I9", "I11"]
  },

  "ed25519_sig": "base64:[signature over (all above + human_dragon_sig)]"
}
```

---

## 3. Field Hierarchy

```
WINDI-KEYGEN-001
├── ceremony           → Key generation details
├── preflight          → Environment validation
├── attestations       → Liga IA+H chain (Architect → Guardian → Witness)
├── loss_acceptance    → Physical artifact
├── operationality_proof → Positive test (B12)
├── bootstrap_anchors  → External publication links
├── bootstrap_disclosure → Explicit self-attestation acknowledgment
├── protocol_artifacts → Hashes of all protocol documents
├── governance         → Human Dragon signature
└── ed25519_sig        → System signature (THE BOOTSTRAP MOMENT)
```

---

## 4. Signature Order

```
1. Assemble all fields except governance.human_dragon_sig and ed25519_sig
2. Canonicalize to RFC 8785 JSON
3. Human Dragon signs → human_dragon_sig
4. Add human_dragon_sig to payload
5. System signs (payload + human_dragon_sig) → ed25519_sig
6. Receipt complete
```

**The bootstrap moment is step 5:** The newly created key signs its own birth certificate.

---

## 5. Artifact Hash Computation

Before ceremony, compute hashes of all fixed artifacts:

```bash
cd /opt/windi/docs/poe-cutover/

# Protocol documents
sha256sum KEY_CEREMONY_PROTOCOL.md
sha256sum ATTESTATION_FORMAT.md
sha256sum PASSPHRASE_POLICY.md
sha256sum PREFLIGHT_CHECKLIST.sh

# These go into protocol_artifacts section
```

---

## 6. Content Hash (for Forensic Ledger)

The `content_hash` for Forensic Ledger storage is computed over the entire
receipt (excluding `ed25519_sig`) using RFC 8785 canonicalization:

```python
import json
import hashlib

def compute_content_hash(receipt: dict) -> str:
    # Remove ed25519_sig for content hash
    payload = {k: v for k, v in receipt.items() if k != "ed25519_sig"}
    # RFC 8785 canonicalization
    canonical = json.dumps(payload, sort_keys=True, separators=(',', ':'))
    return "sha256:" + hashlib.sha256(canonical.encode()).hexdigest()
```

---

## 7. Verification by Third Party

```python
from nacl.signing import VerifyKey
from nacl.encoding import Base64Encoder
import json

def verify_bootstrap_receipt(receipt: dict, pk_base64: str) -> bool:
    """Verify WINDI-KEYGEN-001 bootstrap receipt."""

    # 1. Load public key from external source (GitHub/Zenodo)
    verify_key = VerifyKey(pk_base64, encoder=Base64Encoder)

    # 2. Extract and decode ed25519_sig
    sig = base64.b64decode(receipt["ed25519_sig"])

    # 3. Reconstruct signed payload
    payload = {k: v for k, v in receipt.items() if k != "ed25519_sig"}
    canonical = json.dumps(payload, sort_keys=True, separators=(',', ':'))

    # 4. Verify signature
    try:
        verify_key.verify(canonical.encode(), sig)
        return True
    except:
        return False

# Additional checks:
# - Verify all attestation hashes match actual files
# - Verify operationality_proof signature
# - Verify loss_acceptance.photo_hash matches photo
# - Verify all verdicts are APPROVE
# - Verify pk_fingerprint matches SHA256(pk)
```

---

## 8. Connection to Cutover Block

`WINDI-CUTOVER-001-20260424` references this receipt:

```json
{
  "cryptographic_era": {
    "key_provenance_receipt_id": "WINDI-KEYGEN-001-20260424",
    "pk": "[same pk as in KEYGEN-001]",
    "pk_fingerprint": "[same fingerprint]"
  }
}
```

This creates the verifiable chain:

```
WINDI-KEYGEN-001 (key birth)
       ↓
WINDI-CUTOVER-001 (era boundary)
       ↓
All future receipts (Ed25519 signed)
```

---

## 9. OsmosisBuffer Gamma Entry

> *"O primeiro receipt que importa é o primeiro que pode ser verificado
> por alguém que não confia em ti."*

This is WINDI-KEYGEN-001. The first receipt that matters is the first receipt
that can be verified by someone who doesn't trust you.

---

*Liga IA+H — Kempten, Bavaria · 2026*
