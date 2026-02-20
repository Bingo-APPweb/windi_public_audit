# WINDI Proof Specification

Part of the **WINDI** (Worldwide Infrastructure for Non-repudiable Document Integrity) ecosystem.

This repository defines the cryptographic proof structure used in the WINDI ecosystem.

## Purpose

It ensures that document integrity proofs are:

- **Deterministic** — Same input always produces same output
- **Interoperable** — Works across all WINDI-compatible systems
- **Privacy-preserving** — No raw sensitive data in proofs

## Scope

This specification standardizes:

| Component | Description |
|-----------|-------------|
| Canonicalization | Deterministic field normalization rules |
| ProofSet | Structured proof container schema |
| Hash Generation | Algorithm and encoding standards |
| WVC Format | WINDI Verification Code QR payload |

## Resulting Flow

```
Document → Canonicalization → Hash → ProofSet → Signature → QR Code
```

## Repository Structure

```
windi-proof-spec/
├── spec/
│   ├── proofset-schema.json      # JSON Schema for ProofSet
│   ├── canonicalization-spec.md  # Normalization rules
│   ├── shelf-definitions.md      # Proof shelf types
│   ├── hash-algorithms.md        # Hash algorithm spec
│   └── wvc-qr-format.md          # QR code payload format
├── test-vectors/
│   ├── test-vectors.json         # Test cases
│   └── verify-test-vectors.js    # Validation script
└── examples/
    ├── example-proofset.json     # Sample ProofSet
    ├── example-canonicalized.txt # Canonicalized output
    └── example-wvc.json          # Sample WVC payload
```

## Quick Reference

### ProofSet Structure

```json
{
  "document_hash": "sha256:abc123...",
  "proof_shelves": {
    "payto_hash": "sha256:...",
    "amount_hash": "sha256:...",
    "currency_hash": "sha256:...",
    "structure_hash": "sha256:..."
  }
}
```

### Canonicalization Example

```
PAYTO|IBAN|DE89370400440532013000
AMOUNT|DEC|1000.00
CURRENCY|ISO4217|EUR
```

### Hash Format

```
Algorithm: SHA-256
Encoding:  UTF-8
Output:    lowercase hex
Prefix:    "sha256:"
```

## Position in the WINDI Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    WINDI Ecosystem                       │
├─────────────────────────────────────────────────────────┤
│  windi-reader-sdk        — Client verification           │
│  windi-policy-engine     — Risk decisions                │
│  windi-proof-spec ◄───── YOU ARE HERE                   │
│  windi-verification-api  — Backend API                   │
│  windi-forensics-engine  — Audit trail                   │
│  windi-wcaf-toolkit      — Compliance tools              │
│  windi-core-reference    — Architecture docs             │
└─────────────────────────────────────────────────────────┘
```

## Related Repositories

- [windi-reader-sdk](https://github.com/Bingo-APPweb/windi-reader-sdk) — Client SDK
- [windi-verification-api](https://github.com/Bingo-APPweb/windi-verification-api) — API
- [windi-core-reference](https://github.com/Bingo-APPweb/windi-core-reference) — Architecture

## Security

See [SECURITY.md](SECURITY.md) for vulnerability reporting.

## License

Apache 2.0 — See [LICENSE](LICENSE)
