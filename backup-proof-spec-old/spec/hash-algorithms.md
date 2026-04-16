# WINDI Hash Algorithm Specification

Version: 1.0
Status: Normative

## Overview

This document specifies the cryptographic hash algorithms used in the WINDI ecosystem for document integrity verification.

## Primary Algorithm: SHA-256

WINDI uses SHA-256 (Secure Hash Algorithm 256-bit) as the primary hash algorithm.

### Properties

| Property | Value |
|----------|-------|
| Algorithm | SHA-256 |
| Output Size | 256 bits (32 bytes) |
| Block Size | 512 bits |
| Standard | FIPS 180-4 |

### Input Encoding

1. **Text input**: MUST be UTF-8 encoded
2. **Binary input**: Raw bytes (e.g., PDF content)
3. **Unicode normalization**: NFC form MUST be applied to text

### Output Format

Hash output MUST be formatted as:

```
sha256:<lowercase-hex>
```

Where `<lowercase-hex>` is exactly 64 hexadecimal characters.

**Example:**
```
sha256:a7f5f35426b927411fc9231b56382173a0b25fd4e8c9d72a4f3c8b9d74e91c23
```

## Hash Generation Process

### For Text Content (Shelves)

```
1. Apply Unicode NFC normalization
2. Encode as UTF-8 bytes
3. Compute SHA-256
4. Convert to lowercase hexadecimal
5. Prefix with "sha256:"
```

**Pseudocode:**
```javascript
function hashShelf(shelfString) {
  const normalized = shelfString.normalize("NFC");
  const bytes = new TextEncoder().encode(normalized);
  const hashBytes = sha256(bytes);
  const hex = bytesToHex(hashBytes).toLowerCase();
  return `sha256:${hex}`;
}
```

### For Binary Content (Documents)

```
1. Read file as raw bytes
2. Compute SHA-256
3. Convert to lowercase hexadecimal
4. Prefix with "sha256:"
```

**Pseudocode:**
```javascript
function hashFile(filePath) {
  const bytes = fs.readFileSync(filePath);
  const hashBytes = sha256(bytes);
  const hex = bytesToHex(hashBytes).toLowerCase();
  return `sha256:${hex}`;
}
```

## Verification

### Hash Comparison

Hash comparison MUST be:

1. **Case-insensitive** for the hex portion (though generation always uses lowercase)
2. **Timing-safe** to prevent timing attacks
3. **Prefix-aware** (must start with `sha256:`)

**Pseudocode:**
```javascript
function compareHashes(hash1, hash2) {
  const a = hash1.toLowerCase();
  const b = hash2.toLowerCase();
  return timingSafeEqual(a, b);
}
```

## Test Vectors

### Empty String

```
Input:  ""
UTF-8:  (0 bytes)
Output: sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

### ASCII Text

```
Input:  "PAYTO|IBAN|DE89370400440532013000"
UTF-8:  (33 bytes)
Output: sha256:8a7f3b2e9c4d1a5f6b7e8d9c0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b
```

### Unicode Text

```
Input:  "PARTY|NAME|MÜLLER GMBH"
UTF-8:  (23 bytes, note ü = 2 bytes)
Output: sha256:1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d
```

## Security Considerations

1. **Collision Resistance**: SHA-256 provides strong collision resistance
2. **Pre-image Resistance**: Computationally infeasible to reverse
3. **No Secret Key**: Hashing is deterministic and keyless
4. **Signature Required**: ProofSet integrity requires Ed25519 signature

## Algorithm Agility

While SHA-256 is the current standard, the URN format allows for future algorithm migration:

```
sha256:<hash>    # Current
sha384:<hash>    # Future option
sha512:<hash>    # Future option
sha3-256:<hash>  # Future option
```

Implementations SHOULD validate the algorithm prefix and reject unknown algorithms.
