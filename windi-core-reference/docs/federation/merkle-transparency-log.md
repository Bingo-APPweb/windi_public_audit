# WINDI Merkle Transparency Log (CT-style)

## Purpose
The WINDI Merkle Transparency Log provides **public, append-only, cryptographic transparency** for `combined_root_hash` anchors emitted by WINDI nodes and/or the Hub.

It enables any third party to verify that:
- a specific `combined_root_hash` **was published**,
- at or before a specific time,
- in a log that is **append-only** (with consistency proofs),
- with **compact verification proofs** (inclusion proofs).

This design follows CT-style principles (RFC 6962 family):
- leaf hashing uses prefix `0x00`,
- node hashing uses prefix `0x01`,
- periodic Signed Tree Heads (STH) are signed by the log operator.

---

## Terminology
- **Leaf payload**: canonical JSON describing an anchor entry (e.g. `combined_root_hash`, `node_id`, `ts`).
- **Leaf hash**: `SHA256(0x00 || canonical_json(leaf_payload))`
- **Node hash**: `SHA256(0x01 || left_hash || right_hash)`
- **Merkle root**: root hash over `tree_size` leaves.
- **STH (Signed Tree Head)**: signed statement of `(tree_size, timestamp, root_hash)` by the log operator.
- **Inclusion proof**: audit path proving a leaf is included in a tree of size `tree_size`.
- **Consistency proof**: proof that a newer tree is an append-only extension of an older tree.

---

## Threat Model

### In scope (what this log protects against)
1. **Post-publication tampering**
   - Once a leaf is included in an STH, an attacker cannot change/remove it without breaking proofs or consistency.

2. **Backdating / "we published it earlier"**
   - The log provides public ordering and a signed STH timestamp; publication can be audited externally.

3. **Silent edits to internal state**
   - If a system tries to rewrite history after anchoring, the evidence can be checked against the public log.

4. **Split-view attacks (targeted log views)** — *only when monitors/pinning are used*
   - With STH pinning and consistency verification, clients can detect log rollback or divergent views.

### Out of scope (what this log does NOT protect against)
1. **Dishonest log operator before publication**
   - If the operator never publishes an anchor, the log cannot prove it existed.

2. **Compromised log signing key**
   - A compromised key can sign fraudulent STHs. Mitigation: key rotation, keyset history, multi-party monitoring.

3. **Incorrect `combined_root_hash` generation**
   - The log only proves publication of the hash; correctness of that hash is validated by WINDI bundle verification (WCAF chain, signatures).

4. **Time accuracy**
   - `timestamp` in STH is asserted by the operator. Stronger guarantees can be achieved by anchoring STHs to an external timestamping system.

---

## Security Properties

### What is proven
Given:
- `combined_root_hash`
- `leaf_index` (or discovered via lookup)
- `STH` (tree_size, root_hash, timestamp, signature)
- `inclusion proof` for that `leaf_index` and `tree_size`
- log operator public key

A verifier can prove:
1. The `combined_root_hash` corresponds to a leaf committed into the Merkle tree of size `tree_size`.
2. The tree root for that `tree_size` matches the signed `STH`.
3. Therefore, the `combined_root_hash` was included in the log **no later than** `STH.timestamp` (assuming operator timestamp honesty).

With **consistency proofs** between consecutive STHs, a verifier can additionally prove:
4. The log is append-only over time (no rollback, no rewriting).

### What is NOT proven
- That the underlying document is valid (that's WINDI verification / WCAF chain).
- That the issuer is trusted (that's issuer registry + policy).
- That the timestamp is globally accurate (only that the operator signed it).
- That the log is globally consistent unless monitors/pinning exist.

---

## Data Model

### Leaf payload (canonical JSON)
Minimum recommended fields:
```json
{
  "combined_root_hash": "<64 hex>",
  "node_id": "node:<...>",     // optional but recommended
  "ts": "ISO-8601 timestamp"   // server time of log append
}
```

### Leaf hash
```
leaf_hash = SHA256(0x00 || canonical_json(leaf_payload))
```

### Node hash
```
node_hash = SHA256(0x01 || left_hash || right_hash)
```

---

## API Endpoints

### Append anchor
```
POST /anchors
```
Body:
```json
{
  "combined_root_hash": "<64 hex>",
  "node_id": "node:<...>"      // optional
}
```

Response (recommended):
```json
{
  "leaf_index": 42,
  "leaf_hash": "<hex>",
  "sth": { ... }               // optional depending on emission policy
}
```

### Current STH
```
GET /sth
```
Response:
```json
{
  "tree_size": 12345,
  "timestamp": "ISO-8601",
  "root_hash": "<hex>",
  "signature_alg": "Ed25519",
  "signature": "<base64>",
  "key_id": "hub-log-2026"
}
```

### STH history
```
GET /sth/history?limit=...
```

### Lookup by combined_root_hash
```
GET /lookup?combined_root_hash=<hex>
```
Response:
```json
{
  "found": true,
  "leaf_index": 42,
  "leaf_hash": "<hex>",
  "ts": "ISO-8601",
  "node_id": "node:..."
}
```

### Inclusion proof
```
GET /proof/inclusion?leaf_index=<n>&tree_size=<m>
```
Response:
```json
{
  "leaf_index": 42,
  "tree_size": 12345,
  "audit_path": ["<hex>", "<hex>", ...]
}
```

### Consistency proof
```
GET /proof/consistency?old_size=<n>&new_size=<m>
```
Response:
```json
{
  "old_size": 8000,
  "new_size": 12345,
  "consistency_path": ["<hex>", "<hex>", ...]
}
```

### Convenience verification bundle
```
GET /verify/:combined_root_hash
```
Recommended response:
```json
{
  "lookup": { ... },
  "sth": { ... },
  "inclusion_proof": { ... }
}
```

### Public key
```
GET /pubkey
```
Response:
```json
{
  "key_id": "hub-log-2026",
  "algorithm": "Ed25519",
  "public_key_pem": "-----BEGIN PUBLIC KEY-----..."
}
```

---

## Verification Algorithms (Client)

### Verify STH signature
Input: `sth`, `log_public_key`
1. canonicalize JSON `{tree_size, timestamp, root_hash}`
2. verify Ed25519 signature over canonical JSON bytes

### Verify inclusion proof
Input: `leaf_payload`, `audit_path`, `leaf_index`, `tree_size`, `sth.root_hash`
1. Compute `leaf_hash = SHA256(0x00 || canonical_json(leaf_payload))`
2. Combine with `audit_path` according to `leaf_index` position to reconstruct root
3. Check reconstructed root equals `sth.root_hash`

### Verify consistency proof
Input: `old_sth`, `new_sth`, `consistency_path`
1. verify that root of `old_size` is consistent as prefix of `new_size`
2. detect rollback/split-view when pinned STHs diverge

---

## STH Lifecycle

### Emission policy
Recommended options:
- Emit STH every N appends (e.g. 100)
- Emit STH every T minutes (e.g. 1 min)
- Emit STH on-demand when requested (less ideal)

### Client pinning (recommended)
Clients should persist:
- last seen `sth.tree_size`
- last seen `sth.root_hash`
- last seen `sth.timestamp`
- `key_id`

On next verification:
1. fetch new STH
2. require `new.tree_size >= pinned.tree_size`
3. require consistency proof `pinned → new` verifies
4. if fails, flag potential rollback/split-view

---

## Operational Recommendations

- Publish STHs in `/sth/history` for monitoring.
- Support multiple `key_id` with rotation and a `keyset.json` (Phase 3B.2+).
- Encourage third-party monitors to:
  - fetch STH periodically,
  - verify consistency chain,
  - gossip STHs across parties.

---

## Compatibility Notes

- Core WINDI codes remain language-neutral.
- Human-readable content belongs to i18n packs; transparency log stores only cryptographic anchors.
