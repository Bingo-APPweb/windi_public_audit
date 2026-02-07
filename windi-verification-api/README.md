# WINDI Verification API

Part of the **WINDI** (Worldwide Infrastructure for Non-repudiable Document Integrity) ecosystem.

This repository provides the **Document and Chain Verification Endpoints** component of the WINDI trust and verification architecture.

## Purpose

This module enables secure, verifiable, and privacy-preserving document integrity workflows for institutional and financial environments.

The Verification API provides:
- Document hash verification endpoints
- Virtue Receipt validation
- Chain integrity checks
- Real-time governance status queries
- Batch verification for bulk operations

## Position in the WINDI Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    WINDI Ecosystem                       │
├─────────────────────────────────────────────────────────┤
│  windi-reader-sdk                                        │
│  windi-policy-engine                                     │
│  windi-proof-spec                                        │
│  windi-verification-api ◄── YOU ARE HERE                │
│  windi-forensics-engine                                  │
│  windi-wcaf-toolkit                                      │
│  windi-core-reference                                    │
└─────────────────────────────────────────────────────────┘
```

See: https://github.com/Bingo-APPweb/windi-core-reference

## Security Principles

- No sensitive data processing
- Cryptographic integrity by design
- Deterministic verification
- Auditability and compliance readiness

## Status

Early public technical release — interfaces may evolve.

## License

Apache 2.0 — See [LICENSE](LICENSE)
