# MERKLE_SPEC.md — RFC 6962 Merkle Tree Specification

**Version:** 1.0
**Status:** DRAFT — Pending §202 Seal
**Date:** 2026-04-24
**Reference:** RFC 6962 (Certificate Transparency)

---

## 1. Purpose

This document specifies the Merkle tree algorithm used to compute
`genesis_merkle_root` from the 57,074 legacy receipts.

We adopt **RFC 6962** (Certificate Transparency) because:

1. It is a battle-tested standard
2. Libraries exist in all major languages
3. Reviewers from security venues will recognize it immediately

---

## 2. Hash Function

| Parameter | Value |
|-----------|-------|
| Algorithm | SHA-256 |
| Output | 32 bytes (256 bits) |
| Encoding | Lowercase hexadecimal with `sha256:` prefix |

---

## 3. Leaf Hash

Per RFC 6962 §2.1:

```
MTH({d(0)}) = SHA-256(0x00 || d(0))
```

In our context:

```python
def leaf_hash(data: bytes) -> bytes:
    return sha256(b'\x00' + data)
```

Where `data` is the canonical serialization of the legacy receipt
(see `CANONICAL_SNAPSHOT.md`).

---

## 4. Interior Node Hash

Per RFC 6962 §2.1:

```
MTH(D[n]) = SHA-256(0x01 || MTH(D[0:k]) || MTH(D[k:n]))
```

In our context:

```python
def node_hash(left: bytes, right: bytes) -> bytes:
    return sha256(b'\x01' + left + right)
```

---

## 5. Tree Construction

For n = 57,074 leaves (not a power of 2):

1. Compute leaf hashes for all 57,074 receipts
2. Build the tree bottom-up using RFC 6962 algorithm
3. For odd nodes at any level, promote the unpaired node to the next level

**RFC 6962 handles non-power-of-2 sizes natively.** No padding or duplication
of the last leaf is required.

---

## 6. Algorithm (RFC 6962 §2.1)

```python
def merkle_tree_hash(leaves: list[bytes]) -> bytes:
    n = len(leaves)

    if n == 0:
        return sha256(b'')  # Empty tree

    if n == 1:
        return leaf_hash(leaves[0])

    # Find largest power of 2 less than n
    k = 1
    while k * 2 < n:
        k *= 2

    # Split and recurse
    left = merkle_tree_hash(leaves[:k])
    right = merkle_tree_hash(leaves[k:])

    return node_hash(left, right)
```

---

## 7. Proof Generation

To prove inclusion of leaf at index `i`:

```python
def generate_proof(leaves: list[bytes], index: int) -> list[tuple[str, bytes]]:
    """
    Returns list of (direction, hash) tuples.
    direction is 'L' (sibling on left) or 'R' (sibling on right).
    """
    # Implementation follows RFC 6962 §2.1.1
    ...
```

Proof size: O(log₂ n) = ~16 hashes for 57,074 leaves.

---

## 8. Proof Verification

```python
def verify_proof(
    leaf_data: bytes,
    proof: list[tuple[str, bytes]],
    expected_root: bytes
) -> bool:
    current = leaf_hash(leaf_data)

    for direction, sibling in proof:
        if direction == 'L':
            current = node_hash(sibling, current)
        else:
            current = node_hash(current, sibling)

    return current == expected_root
```

---

## 9. genesis_merkle_root Computation

```python
# 1. Export all legacy receipts in order
receipts = db.execute("""
    SELECT * FROM receipts
    WHERE created_at <= cutover_timestamp
    ORDER BY created_at ASC, id ASC
""").fetchall()

# 2. Compute leaf hashes
leaves = [compute_leaf_hash(r) for r in receipts]

# 3. Compute Merkle root
genesis_merkle_root = merkle_tree_hash(leaves)

# 4. Format for storage
genesis_merkle_root_str = f"sha256:{genesis_merkle_root.hex()}"
```

---

## 10. Expected Values

| Parameter | Value |
|-----------|-------|
| Leaf count | 57,074 |
| Tree height | ceil(log₂(57074)) = 16 levels |
| Proof size | ≤16 hashes (512 bytes) |
| Root computation time | < 10 seconds on commodity hardware |

---

## 11. Test Vectors

The `windi-poe-testvectors` repository includes:

- Small tree examples (4, 8, 15 leaves) with known roots
- Inclusion proofs with expected verification results
- Edge cases (1 leaf, power-of-2 counts, maximum depth)

---

## 12. References

- RFC 6962: Certificate Transparency (https://tools.ietf.org/html/rfc6962)
- RFC 6962bis: Certificate Transparency Version 2.0 (informational)

---

*Liga IA+H — Kempten, Bavaria · 2026*
