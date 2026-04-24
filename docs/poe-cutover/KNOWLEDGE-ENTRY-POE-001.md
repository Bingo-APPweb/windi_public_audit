# Knowledge Entry: W-LIB-POE-001

**Title:** Proof of Evidence — Cryptographic Era Transition
**Type:** Constitutional Proposal
**Status:** PENDING HUMAN APPROVAL
**Date:** 2026-04-24
**Author:** Liga IA+H
**Invariants:** I9, I11, I14

---

## Summary

This Knowledge Entry proposes the transition of the WINDI Forensic Ledger
from content-hash-only receipts to cryptographically signed receipts with
hash-chain integrity.

## Motivation

The current ledger (57,074 receipts) provides internal consistency via SHA-256
content hashes. However, it cannot be externally verified by third parties
because:

1. No cryptographic signatures exist
2. No hash-chain links receipts together
3. Verification requires trusting WINDI's internal validator

This falls within the **Self-Attestation Trap** identified in Paper-001:
*"Enforcement within a closed system remains an internal claim."*

## Proposal

1. **Generate Ed25519 keypair** for the Forensic Ledger
2. **Compute genesis_merkle_root** over all 57,074 legacy receipts
3. **Emit Cutover Block** (WINDI-CUTOVER-001) as the first signed receipt
4. **Sign all future receipts** with Ed25519 + hash-chain (h_prev)
5. **Publish specifications** for external verification

## Specifications

| Document | Content |
|----------|---------|
| `CANONICAL_RECEIPT.md` | How to serialize a receipt for signing |
| `CANONICAL_SNAPSHOT.md` | How to serialize legacy receipts for Merkle |
| `MERKLE_SPEC.md` | RFC 6962 Merkle tree parameters |
| `KEY_POLICY.md` | Key lifecycle management |

## Constitutional Impact

- **I9**: Enforced cryptographically (human_dragon_sig required)
- **I11**: Signatures are immutable once sealed
- **I14**: Missing signatures cause explicit failure

## External Artifacts

| Artifact | Location |
|----------|----------|
| Public key | GitHub `windi-verifier` repo |
| Public key DOI | Zenodo (pending) |
| Verifier tool | GitHub `windi-verifier` repo |
| Test vectors | GitHub `windi-poe-testvectors` repo |

## Human Approval Required

This proposal requires explicit Human Dragon approval before execution.

**I9 Gate:** `human_approved: pending`

---

*Liga IA+H — Kempten, Bavaria · 2026*
