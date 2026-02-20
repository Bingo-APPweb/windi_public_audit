# windi-policy-engine

Motor de decisão de risco do WINDI.

Part of the **WINDI** (Worldwide Infrastructure for Non-repudiable Document Integrity) ecosystem.

## Overview

The Policy Engine receives verification results and payment context, then returns a risk-based decision (ALLOW/HOLD/BLOCK) with detailed reason codes.

## Installation

```bash
npm install windi-policy-engine
```

## Usage

```js
const { simpleDecision } = require("windi-policy-engine");

const result = simpleDecision({
  verification: {
    verdict: "VALID",
    integrity: "INTACT",
    signature: "VALID",
    trust_level: "HIGH",
    issuer_status: "TRUSTED",
    risk_flags: []
  },
  doc: {
    iban: "DE89370400440532013000"
  },
  context: {
    expected_iban: "DE89370400440532013000",
    amount: 50000
  }
});

console.log(result);
// {
//   decision: "ALLOW",
//   score: 0,
//   reason_codes: [],
//   required_actions: [],
//   applied_rules: []
// }
```

## Input

| Field | Description |
|-------|-------------|
| `verification` | Result from WINDI Verification API (`/verify`) |
| `doc` | Extracted document fields (iban, amount, supplier, etc.) |
| `context` | Payment context (expected_iban, amount, currency, etc.) |
| `policy` | Optional policy overrides |

## Output

| Field | Description |
|-------|-------------|
| `decision` | `ALLOW`, `HOLD`, or `BLOCK` |
| `score` | Risk score 0-100 |
| `reason_codes` | Standardized reason codes |
| `required_actions` | Recommended actions for the bank/ERP |
| `applied_rules` | Details of which rules fired |

## Built-in Rules

| Rule | Triggers | Decision |
|------|----------|----------|
| `tamperedOrInvalidSig` | Document tampered or signature invalid | BLOCK |
| `ibanMismatch` | IBAN in document differs from expected | BLOCK |
| `flagsFromVerification` | Maps risk_flags to decisions | Configurable |
| `highValueLowTrust` | High amount + trust < HIGH | HOLD |
| `issuerUnknown` | Issuer not in trusted registry | HOLD |

## Reason Codes

| Code | Description |
|------|-------------|
| `DOC_TAMPERED` | Document integrity compromised |
| `SIGNATURE_INVALID` | Digital signature verification failed |
| `VERIFICATION_INVALID` | Verification API returned INVALID |
| `IBAN_MISMATCH` | IBAN differs from registered value |
| `HIGH_VALUE_LOW_TRUST` | Transaction exceeds threshold without HIGH trust |
| `ISSUER_UNKNOWN` | Document issuer not in trusted registry |
| `VERIFY_FLAG:*` | Mapped from verification risk_flags |

## Custom Policies

```js
const { simpleDecision } = require("windi-policy-engine");

const customPolicy = {
  policy_id: "my-bank-policy-v2",
  high_value_threshold: 25000,
  risk_flag_map: {
    "DOC_NOT_FOUND": "BLOCK",
    "ISSUER_NOT_FOUND": "HOLD"
  },
  default_decision: "ALLOW"
};

const result = simpleDecision({
  verification,
  doc,
  context,
  policy: customPolicy
});
```

## Testing

```bash
npm test
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    WINDI Policy Engine                       │
├─────────────────────────────────────────────────────────────┤
│  Input:                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ verification│  │    doc      │  │      context        │  │
│  │  (from API) │  │ (extracted) │  │ (payment metadata)  │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
│         │                │                     │             │
│         └────────────────┴─────────────────────┘             │
│                          │                                   │
│                          ▼                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                    Rule Engine                         │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐  │  │
│  │  │ tampered    │ │ iban        │ │ highValue       │  │  │
│  │  │ OrInvalid   │ │ Mismatch    │ │ LowTrust        │  │  │
│  │  └─────────────┘ └─────────────┘ └─────────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
│                          │                                   │
│                          ▼                                   │
│  Output: { decision, score, reason_codes, required_actions } │
└─────────────────────────────────────────────────────────────┘
```

## Position in the WINDI Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    WINDI Ecosystem                       │
├─────────────────────────────────────────────────────────┤
│  windi-reader-sdk        — Client SDK                    │
│  windi-policy-engine ◄── YOU ARE HERE                   │
│  windi-proof-spec        — Proof specification           │
│  windi-verification-api  — Backend API                   │
│  windi-forensics-engine  — Audit trail                   │
│  windi-wcaf-toolkit      — Compliance tools              │
│  windi-core-reference    — Architecture docs             │
└─────────────────────────────────────────────────────────┘
```

## Related Repositories

- [windi-verification-api](https://github.com/Bingo-APPweb/windi-verification-api) — Verification API
- [windi-reader-sdk](https://github.com/Bingo-APPweb/windi-reader-sdk) — Client SDK
- [windi-proof-spec](https://github.com/Bingo-APPweb/windi-proof-spec) — Proof specification

## License

Apache 2.0 — See [LICENSE](LICENSE)
