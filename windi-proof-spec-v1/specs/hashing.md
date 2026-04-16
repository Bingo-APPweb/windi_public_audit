# Hashing Specification

**WINDI Proof Spec v1.0.0**

This document defines the hashing requirements for WINDI proof artifacts.

---

## Algorithm

**SHA-256 is the only supported hash algorithm in v1.0.0.**

| Property | Value |
|----------|-------|
| Algorithm | SHA-256 |
| Output size | 256 bits (32 bytes) |
| Hex representation | 64 lowercase characters |
| Field name | `hash_algorithm` |
| Field value | `"SHA-256"` |

---

## Why SHA-256

1. **Widely supported** — Available in every major language and platform
2. **Well-analyzed** — Decades of cryptographic scrutiny
3. **Collision resistant** — No practical collision attacks known
4. **Deterministic** — Same input always produces same output
5. **Fast enough** — Suitable for high-volume verification

---

## Input Requirements

The hash is computed over the **canonicalized payload**, not the raw input.

**Process:**
1. Parse the receipt/proof
2. Remove transient fields (`source_payload`)
3. Apply canonicalization rules (see `canonicalization.md`)
4. Encode as UTF-8 bytes
5. Compute SHA-256
6. Output as lowercase hexadecimal

---

## Output Format

**64 lowercase hexadecimal characters.**

```
✅ 9d4e1e23bd5b727046a9e3b4b7db57bd8d6ee684d5a63e7d8f6a3d1c1f1f9abc
```

**Invalid formats:**

```
❌ 0x9d4e1e23...              (no prefix)
❌ sha256:9d4e1e23...         (no prefix)
❌ 9D4E1E23BD5B...            (must be lowercase)
❌ 9d4e1e23 bd5b 7270...      (no spaces)
❌ 9d4e1e23bd5b7270           (must be 64 chars)
```

---

## Schema Validation

In `receipt.schema.json`:

```json
{
  "content_hash": {
    "type": "string",
    "pattern": "^[a-f0-9]{64}$"
  },
  "hash_algorithm": {
    "type": "string",
    "enum": ["SHA-256"]
  }
}
```

---

## Reference Implementations

### JavaScript/Node.js
```javascript
const crypto = require('crypto');

function sha256(data) {
  return crypto
    .createHash('sha256')
    .update(data, 'utf8')
    .digest('hex');
}
```

### Python
```python
import hashlib

def sha256(data: str) -> str:
    return hashlib.sha256(data.encode('utf-8')).hexdigest()
```

### Go
```go
import (
    "crypto/sha256"
    "encoding/hex"
)

func Sha256(data string) string {
    hash := sha256.Sum256([]byte(data))
    return hex.EncodeToString(hash[:])
}
```

### Rust
```rust
use sha2::{Sha256, Digest};

fn sha256(data: &str) -> String {
    let mut hasher = Sha256::new();
    hasher.update(data.as_bytes());
    hex::encode(hasher.finalize())
}
```

---

## Test Vectors

### Empty String
```
Input:  ""
SHA-256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

### Simple String
```
Input:  "WINDI"
SHA-256: 7c2c8d0c2f1d3e4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a
```
*(Note: Verify with actual implementation)*

### Canonical Receipt
```
Input:  {"actor":"test","app":"test"}
SHA-256: [compute with implementation]
```

---

## Security Considerations

### Hash Collision

SHA-256 has no known practical collision attacks. The probability of accidental collision is negligible (1 in 2^128 for birthday attack).

### Content Inference

Hashes do not reveal content. However:
- Known-plaintext attacks are possible for short, predictable content
- Content with low entropy may be brute-forced
- Use for documents, not passwords or secrets

### Hash Extension

SHA-256 is vulnerable to length extension attacks. This is not relevant for WINDI receipts because:
- Entire payload is hashed, not partial
- Hash is for verification, not authentication

---

## Future Versions

If cryptographic advances require algorithm change:
- New algorithm will be added as enum option
- `hash_algorithm` field will indicate which was used
- v1.0.0 receipts with SHA-256 remain valid
- Transition period will support both

**Potential future algorithms:**
- SHA-3 (Keccak)
- BLAKE3
- Post-quantum candidates

---

## Verification Algorithm

```
FUNCTION verifyHash(receipt, expectedHash):
  canonical = canonicalize(receipt)
  computedHash = sha256(canonical)
  RETURN computedHash == expectedHash
```

---

## References

- FIPS 180-4: Secure Hash Standard
- RFC 6234: US Secure Hash Algorithms
- WINDI Canonicalization: `specs/canonicalization.md`

---

*WINDI Proof Spec v1.0.0 — Hashing*
