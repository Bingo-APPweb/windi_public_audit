# CANONICAL_SNAPSHOT.md — Legacy Receipt Serialization for Merkle Tree

**Version:** 1.0
**Status:** DRAFT — Pending §202 Seal
**Date:** 2026-04-24
**Invariants:** I11, I14

---

## 1. Purpose

This document specifies the **canonical form** for serializing legacy receipts
(receipts 1 through 57,074) when computing the `genesis_merkle_root`.

Legacy receipts were created before the Cryptographic Era and do not have
Ed25519 signatures. This specification defines how to hash them consistently
for inclusion in the Merkle tree.

---

## 2. Legacy Receipt Canonical Form

Each legacy receipt is serialized using RFC 8785 (JCS) with these fields
in lexicographic order:

```json
{
  "actor": "string",
  "app": "string",
  "content_hash": "sha256:hex",
  "created_at": integer (unix epoch),
  "doc_name": "string",
  "doc_type": "string",
  "governance_level": "string",
  "id": "string (receipt_id)",
  "sge_score": number,
  "status": "string"
}
```

**Fields EXCLUDED** (not available or not relevant for integrity):

- `ed25519_pub`, `ed25519_sig`, `merkle_root` (always NULL in legacy)
- `metadata_json` (variable structure, not suitable for canonical form)
- `tags_json`, `flags_json` (operational, not integrity-critical)
- `bundle_hash`, `bundle_size` (optional, post-creation)

---

## 3. Leaf Hash Computation

Each legacy receipt becomes a Merkle leaf:

```python
def compute_leaf_hash(receipt: dict) -> bytes:
    canonical_fields = {
        "actor": receipt["actor"],
        "app": receipt["app"],
        "content_hash": receipt["content_hash"],
        "created_at": receipt["created_at"],
        "doc_name": receipt["doc_name"],
        "doc_type": receipt["doc_type"],
        "governance_level": receipt["governance_level"],
        "id": receipt["id"],
        "sge_score": receipt["sge_score"],
        "status": receipt["status"]
    }
    canonical = jcs_serialize(canonical_fields)  # RFC 8785
    return sha256(canonical)
```

---

## 4. Ordering

Leaves are ordered by:

```sql
ORDER BY created_at ASC, id ASC
```

The secondary sort by `id` ensures deterministic ordering when multiple
receipts have identical `created_at` timestamps.

---

## 5. Null Handling

If any canonical field is NULL in the database:

| Field | Null Handling |
|-------|---------------|
| `actor` | Use literal string `"null"` |
| `sge_score` | Use `0.0` |
| Others | Use empty string `""` |

This ensures deterministic serialization even for incomplete legacy data.

---

## 6. Merkle Tree Construction

See `MERKLE_SPEC.md` for the RFC 6962 Merkle tree algorithm applied
to the ordered leaf hashes.

---

## 7. Verification

To verify that a specific legacy receipt is included in `genesis_merkle_root`:

1. Compute the leaf hash using this specification
2. Obtain the Merkle proof (sibling hashes along the path)
3. Recompute the root using the proof
4. Compare with `genesis_merkle_root` in the Cutover Block

This allows O(log n) verification of any single legacy receipt's inclusion
without processing all 57,074 receipts.

---

## 8. Implementation Notes

- Export legacy receipts: `SELECT * FROM receipts ORDER BY created_at ASC, id ASC`
- Use consistent JSON library (Python `json` with `sort_keys=True` approximates JCS)
- For production, use proper JCS library (`json-canonicalize`)

---

*Liga IA+H — Kempten, Bavaria · 2026*
