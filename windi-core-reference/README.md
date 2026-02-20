# WINDI Core Reference

**The Single Source of Truth** for the WINDI ecosystem.

Part of the **WINDI** (Worldwide Infrastructure for Non-repudiable Document Integrity) ecosystem.

## Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture and data flow |
| [TRUST_MODEL.md](TRUST_MODEL.md) | Trust levels and verification tiers |
| [WCAF_FORMAT.md](WCAF_FORMAT.md) | WINDI Chain Audit Format specification |
| [I18N_MODEL.md](I18N_MODEL.md) | Internationalization strategy |
| [ROADMAP.md](ROADMAP.md) | Development milestones |

## WINDI Ecosystem

```
┌─────────────────────────────────────────────────────────┐
│                    WINDI Ecosystem                       │
├─────────────────────────────────────────────────────────┤
│  windi-reader-sdk        — Client SDK for verification   │
│  windi-policy-engine     — Risk decision engine          │
│  windi-proof-spec        — Cryptographic proof schema    │
│  windi-verification-api  — Backend verification API      │
│  windi-forensics-engine  — Audit trail and replay        │
│  windi-wcaf-toolkit      — Auditor CLI tools             │
│  windi-core-reference ◄── YOU ARE HERE                  │
└─────────────────────────────────────────────────────────┘
```

## Core Principles

> **"AI processes. Human decides. WINDI guarantees."**

1. **Human Sovereignty** — AI advises, humans make final decisions
2. **Cryptographic Integrity** — Every document verifiable by hash
3. **Privacy by Design** — Only hashes transmitted, never content
4. **Institutional Trust** — Governance for regulated environments
5. **Non-Repudiation** — Complete audit trail with institutional signatures

## Quick Reference

### Verification Flow

```
Document → SDK (hash) → /verify API → Policy Engine → Decision
                              ↓
                        Forensics Log
```

### Trust Levels

| Level | Meaning |
|-------|---------|
| `LOW` | Integrity or signature problem, or unknown issuer |
| `MEDIUM` | Signature valid, issuer REGISTERED |
| `HIGH` | Signature valid, issuer TRUSTED |

### Decision Outcomes

| Decision | Action |
|----------|--------|
| `ALLOW` | Payment proceeds |
| `HOLD` | Manual review required |
| `BLOCK` | Payment rejected |

## Related Repositories

- [windi-reader-sdk](https://github.com/Bingo-APPweb/windi-reader-sdk)
- [windi-verification-api](https://github.com/Bingo-APPweb/windi-verification-api)
- [windi-policy-engine](https://github.com/Bingo-APPweb/windi-policy-engine)
- [windi-forensics-engine](https://github.com/Bingo-APPweb/windi-forensics-engine)
- [windi-proof-spec](https://github.com/Bingo-APPweb/windi-proof-spec)
- [windi-wcaf-toolkit](https://github.com/Bingo-APPweb/windi-wcaf-toolkit)

## License

Apache 2.0 — See [LICENSE](LICENSE)
