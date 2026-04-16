# Changelog

All notable changes to this project will be documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] — 2026-02-08

### Added
- **ProofSet Schema** (`spec/proofset-schema.json`)
  - JSON Schema for cryptographic proof container
  - Document hash validation pattern
  - Proof shelves structure
  - Issuer and signature fields
- **Canonicalization Specification** (`spec/canonicalization-spec.md`)
  - IBAN normalization rules
  - Amount format detection and normalization
  - Currency symbol mapping to ISO 4217
  - Date format conversion to ISO 8601
  - Shelf format: `TYPE|SUBTYPE|VALUE`
- **Shelf Definitions** (`spec/shelf-definitions.md`)
  - PAYTO, AMOUNT, CURRENCY, DATE, REF, PARTY, TEXT, STRUCT
  - Custom shelf support with X- prefix
- **Hash Algorithm Specification** (`spec/hash-algorithms.md`)
  - SHA-256 as primary algorithm
  - UTF-8 encoding requirements
  - URN format: `sha256:<hex>`
- **WVC QR Format** (`spec/wvc-qr-format.md`)
  - Binary payload structure (48 bytes)
  - Base32 encoding
  - QR code generation guidelines
- **Test Vectors** (`test-vectors/`)
  - Canonicalization test cases
  - Hash generation validation
  - ProofSet schema validation
  - Verification script
- **Examples**
  - Complete ProofSet JSON
  - Canonicalization walkthrough
  - WVC payload example

## [0.1.0] — 2026-02-07

### Added
- Repository initialized
- Documentation structure created
- Architecture alignment with WINDI ecosystem
