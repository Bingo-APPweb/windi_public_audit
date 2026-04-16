# Canonicalization Specification

**WINDI Proof Spec v1.0.0**

This document defines the deterministic canonicalization rules for WINDI proof artifacts. Following these rules ensures that identical content always produces identical hashes, enabling independent verification.

---

## Purpose

Canonicalization removes ambiguity from serialization. Without it, semantically identical data could produce different hashes due to:
- Key ordering differences
- Whitespace variations
- Number formatting inconsistencies
- Character encoding differences

---

## Core Rules

### Rule 1: UTF-8 Encoding

**All text MUST be encoded as UTF-8.**

- No BOM (Byte Order Mark)
- No alternative encodings (Latin-1, UTF-16, etc.)
- Invalid UTF-8 sequences cause verification failure

```
✅ UTF-8 encoded
❌ Latin-1 encoded
❌ UTF-16 encoded
```

---

### Rule 2: Lexicographic Key Ordering

**Object keys MUST be serialized in lexicographic (alphabetical) order.**

Before canonicalization:
```json
{
  "name": "document.pdf",
  "actor": "did:windi:dragon-001",
  "hash": "abc123"
}
```

After canonicalization:
```json
{"actor":"did:windi:dragon-001","hash":"abc123","name":"document.pdf"}
```

**Implementation:**
```javascript
// JavaScript example
JSON.stringify(obj, Object.keys(obj).sort());
```

---

### Rule 3: No Whitespace

**Canonical form has no insignificant whitespace.**

- No spaces after colons
- No spaces after commas
- No newlines
- No indentation

```
✅ {"key":"value","array":[1,2,3]}
❌ { "key": "value", "array": [1, 2, 3] }
❌ {
     "key": "value"
   }
```

---

### Rule 4: Array Order Preserved

**Arrays MUST preserve their original order.**

- Do NOT sort array elements
- Order is semantically significant
- Only object keys are reordered, not arrays

```json
// Original
{"items": ["c", "a", "b"]}

// Canonical (unchanged order)
{"items":["c","a","b"]}
```

---

### Rule 5: Number Normalization

**Numbers MUST be in JSON-standard normalized form.**

| Input | Canonical |
|-------|-----------|
| `1.0` | `1` |
| `1.00` | `1` |
| `1e0` | `1` |
| `1E+2` | `100` |
| `0.5` | `0.5` |
| `-0` | `0` |

**Rules:**
- No trailing zeros after decimal
- No unnecessary decimal point
- No exponential notation for representable integers
- Negative zero becomes zero

---

### Rule 6: String Escaping

**Strings use minimal JSON escaping.**

Only escape:
- `"` → `\"`
- `\` → `\\`
- Control characters (U+0000 to U+001F) → `\uXXXX`

Do NOT escape:
- Forward slash `/` (optional in JSON, not escaped)
- Non-ASCII Unicode (serialize as UTF-8, not `\uXXXX`)

```
✅ "path/to/file"
❌ "path\/to\/file"

✅ "München"
❌ "M\u00FCnchen"
```

---

### Rule 7: Boolean and Null Literals

**Use lowercase literals exactly as specified.**

```
✅ true
✅ false
✅ null

❌ True
❌ FALSE
❌ NULL
```

---

### Rule 8: Exclude Transient Fields

**Fields marked as transient are excluded from hash computation.**

In the WINDI receipt schema, the following field is transient:
- `source_payload` — internal compatibility data, not part of canonical hash

**Process:**
1. Remove transient fields from object
2. Apply canonicalization rules
3. Compute hash

```javascript
// Pseudo-code
function canonicalize(receipt) {
  const copy = { ...receipt };
  delete copy.source_payload;  // transient
  return JSON.stringify(copy, Object.keys(copy).sort());
}
```

---

## Canonicalization Algorithm

```
FUNCTION canonicalize(value):
  IF value is null:
    RETURN "null"

  IF value is boolean:
    RETURN value ? "true" : "false"

  IF value is number:
    RETURN normalizeNumber(value)

  IF value is string:
    RETURN '"' + escapeString(value) + '"'

  IF value is array:
    elements = []
    FOR each item in value:
      elements.append(canonicalize(item))
    RETURN '[' + join(elements, ',') + ']'

  IF value is object:
    pairs = []
    keys = sortLexicographically(value.keys())
    FOR each key in keys:
      IF key is not transient:
        pairs.append('"' + key + '":' + canonicalize(value[key]))
    RETURN '{' + join(pairs, ',') + '}'
```

---

## Hash Computation

After canonicalization, compute SHA-256:

```
FUNCTION computeContentHash(receipt):
  canonical = canonicalize(receipt)
  bytes = encodeUTF8(canonical)
  hash = SHA256(bytes)
  RETURN hexEncode(hash)  // 64 lowercase hex characters
```

**Output format:**
- 64 hexadecimal characters
- Lowercase only
- No prefix (no `0x`, no `sha256:`)

```
✅ 9d4e1e23bd5b727046a9e3b4b7db57bd8d6ee684d5a63e7d8f6a3d1c1f1f9abc
❌ 0x9d4e1e23bd5b727046a9e3b4b7db57bd8d6ee684d5a63e7d8f6a3d1c1f1f9abc
❌ SHA256:9d4e1e23...
❌ 9D4E1E23BD5B727046A9E3B4B7DB57BD8D6EE684D5A63E7D8F6A3D1C1F1F9ABC
```

---

## Test Vector

**Input receipt:**
```json
{
  "spec_version": "1.0.0",
  "receipt_id": "TEST-001",
  "issued_at": "2026-04-10T12:00:00Z",
  "actor": "did:windi:test",
  "app": "test-app",
  "content_hash": "0000000000000000000000000000000000000000000000000000000000000000",
  "hash_algorithm": "SHA-256",
  "governance_level": "MED",
  "verify_url": "https://example.com/verify/TEST-001"
}
```

**Canonical form:**
```
{"actor":"did:windi:test","app":"test-app","content_hash":"0000000000000000000000000000000000000000000000000000000000000000","governance_level":"MED","hash_algorithm":"SHA-256","issued_at":"2026-04-10T12:00:00Z","receipt_id":"TEST-001","spec_version":"1.0.0","verify_url":"https://example.com/verify/TEST-001"}
```

**SHA-256 of canonical form:**
```
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

*(Note: This is an example. Actual hash depends on exact byte sequence.)*

---

## Implementation Notes

### JavaScript/TypeScript
```typescript
function canonicalize(obj: any): string {
  if (obj === null) return 'null';
  if (typeof obj === 'boolean') return obj.toString();
  if (typeof obj === 'number') return JSON.stringify(obj);
  if (typeof obj === 'string') return JSON.stringify(obj);
  if (Array.isArray(obj)) {
    return '[' + obj.map(canonicalize).join(',') + ']';
  }
  const keys = Object.keys(obj).filter(k => k !== 'source_payload').sort();
  const pairs = keys.map(k => `"${k}":${canonicalize(obj[k])}`);
  return '{' + pairs.join(',') + '}';
}
```

### Python
```python
import json
import hashlib

def canonicalize(obj):
    if obj is None:
        return 'null'
    if isinstance(obj, bool):
        return 'true' if obj else 'false'
    if isinstance(obj, (int, float)):
        return json.dumps(obj)
    if isinstance(obj, str):
        return json.dumps(obj)
    if isinstance(obj, list):
        return '[' + ','.join(canonicalize(x) for x in obj) + ']'
    if isinstance(obj, dict):
        keys = sorted(k for k in obj.keys() if k != 'source_payload')
        pairs = [f'"{k}":{canonicalize(obj[k])}' for k in keys]
        return '{' + ','.join(pairs) + '}'

def compute_hash(receipt):
    canonical = canonicalize(receipt)
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()
```

---

## References

- RFC 8785: JSON Canonicalization Scheme (JCS)
- WINDI Proof Spec: `schemas/receipt.schema.json`
- Hashing Specification: `specs/hashing.md`

---

*WINDI Proof Spec v1.0.0 — Canonicalization*
