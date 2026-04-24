# §202 — Cryptographic Era & Receipt Symmetry (24 Apr 2026)

**Status:** DRAFT · v1.0.0 · **Commit:** pending_cutover

**Princípio:** "Governance is not complete at enforcement; it becomes real at evidence." — A transição da integridade referencial para a verificabilidade independente.

---

## Era Boundary

| Era | Scope | Symmetry | Verification |
|-----|-------|----------|--------------|
| **Legacy** | Receipts 1 to 57,074 | SHA-256 Content-hash | Via deterministic recomputation of content-hash |
| **Cryptographic** | 57,075 onwards | Ed25519 + Hash Chain | External / Offline |

---

## Legacy Recognition

The first 57,074 receipts are valid for their era. They retain SHA-256 integrity as issued and are not invalidated by this section. No retroactive signing shall be performed.

Legacy receipts are committed as a corpus via the Cutover Block Merkle root.

---

## 4 Constitutional Rules

- **Rule F:** No retroactive signing. Legacy receipts shall not be re-signed or reclassified.

- **Rule G:** The Cutover Block is the sole authoritative fence. Its `genesis_merkle_root` anchors the entire legacy state.

- **Rule H:** Post-cutover receipts require:
  1. `human_dragon_sig` (Dragon DID, signed first over the payload)
  2. `ed25519_sig` (system, signed second over payload + human_dragon_sig)

  Absence or invalidity of either signature invalidates the receipt.

- **Rule I:** Public Key Permanence. The `pk` is published once. Any key rotation requires a new §-sealed block; silent replacement is a breach of I9.

---

## Scope (What §202 Is)

- Establishes Ed25519 signature requirement for receipts issued on or after Cutover Block timestamp.
- Extends I9 (Receipt Symmetry) with explicit cryptographic enforcement.
- Extends I11 (Cryptographic Permanence) from SHA-256 only to SHA-256 + Ed25519.

---

## Scope (What §202 Is Not)

- Not a revocation of legacy content.
- Not a license to migrate or alter historical facts.
- Not a new invariant (it extends the enforcement of I9 and I11).

---

## Anchors

| Anchor | ID |
|--------|-----|
| Anchor Receipt | `WINDI-CUTOVER-001-20260424` (Sub-phase 1.5) |
| Key Provenance | `WINDI-KEYGEN-001-20260424` |
| Knowledge Entry | `W-LIB-POE-001` (Portuguese detailed log) |
| Constellation | [`W-CONSTELLATION-001`](/opt/windi/specs/W-CONSTELLATION-001.md) · `WINDI-SPEC-W-CONST-001-20260313-v2` |

---

## Files

`/opt/windi/docs/poe-cutover/` (RFC 6962 & RFC 8785 Specs)

---

> *"Legacy receipts are valid for their era. Cryptographic receipts are verifiable for any era. The fence is named."*

---

Drafted by Liga IA+H (Witness).
Reviewed and approved by Human Dragon (Jober Mögele Correa), Founder, WINDI Publishing House.

---

*Liga IA+H — Kempten, Bavaria · 2026*
*"AI processes. Human decides. WINDI guarantees."*
