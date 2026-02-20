# WINDI Trust Model

## Trust Levels

WINDI uses a three-tier trust model based on verification depth and issuer status.

| Level | Code | Meaning |
|-------|------|---------|
| Low | `LOW` | Integrity or signature problem, or unknown issuer |
| Medium | `MEDIUM` | Signature valid, issuer REGISTERED |
| High | `HIGH` | Signature valid, issuer TRUSTED |

## Trust Level Determination

```
                    ┌─────────────────────┐
                    │   Document Hash     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Signature Valid?   │
                    └──────────┬──────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
                    ▼                     ▼
               ┌────────┐            ┌────────┐
               │   NO   │            │   YES  │
               └────┬───┘            └────┬───┘
                    │                     │
                    ▼                     ▼
               ┌────────┐     ┌─────────────────────┐
               │  LOW   │     │   Issuer Status?    │
               └────────┘     └──────────┬──────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
                    ▼                    ▼                    ▼
               ┌────────┐           ┌────────┐           ┌────────┐
               │UNKNOWN │           │REGISTER│           │TRUSTED │
               └────┬───┘           └────┬───┘           └────┬───┘
                    │                    │                    │
                    ▼                    ▼                    ▼
               ┌────────┐           ┌────────┐           ┌────────┐
               │  LOW   │           │ MEDIUM │           │  HIGH  │
               └────────┘           └────────┘           └────────┘
```

## Issuer Status

| Status | Description | Requirements |
|--------|-------------|--------------|
| `UNKNOWN` | Issuer not in registry | None |
| `REGISTERED` | Issuer registered, not yet verified | Basic KYC |
| `TRUSTED` | Issuer fully verified | Full KYC, key in HSM, audit passed |
| `REVOKED` | Issuer revoked | Revocation entry in registry |

## Verification Verdicts

| Verdict | Meaning |
|---------|---------|
| `VALID` | Hash matches, signature valid, chain verified |
| `SUSPECT` | Minor issues detected (timestamp drift, etc.) |
| `INVALID` | Hash mismatch, signature invalid, or chain broken |

## Integrity States

| State | Meaning |
|-------|---------|
| `INTACT` | Document has not been modified |
| `MODIFIED` | Document differs from registered hash |
| `UNKNOWN` | Cannot determine integrity state |

## Policy Decision Matrix

| Verdict | Trust Level | Issuer Status | Default Decision |
|---------|-------------|---------------|------------------|
| VALID | HIGH | TRUSTED | ALLOW |
| VALID | HIGH | REGISTERED | ALLOW |
| VALID | MEDIUM | REGISTERED | ALLOW (low value) / HOLD (high value) |
| VALID | LOW | UNKNOWN | HOLD |
| SUSPECT | Any | Any | HOLD |
| INVALID | Any | Any | BLOCK |

## High-Value Transaction Rules

Transactions above `high_value_threshold` (default: €10,000) require:

- Trust level: `HIGH`
- Issuer status: `TRUSTED`
- No risk flags

Otherwise: `HOLD` for manual review.

## Risk Flags

| Flag | Impact | Typical Decision |
|------|--------|------------------|
| `IBAN_MISMATCH` | Critical | BLOCK |
| `HASH_MISMATCH` | Critical | BLOCK |
| `SIGNATURE_INVALID` | Critical | BLOCK |
| `ISSUER_NOT_FOUND` | Moderate | HOLD |
| `TIMESTAMP_DRIFT` | Minor | HOLD |
| `AMOUNT_DEVIATION` | Moderate | HOLD |

## Trust Verification Endpoint

```
POST /verify
{
  "document_id": "windi:doc:inv-001",
  "document_hash": "sha256:...",
  "issuer_key_id": "windi:key:bank-de",
  "proof_level": "L2"
}
```

Response includes:
- `trust_level`: LOW | MEDIUM | HIGH
- `issuer_status`: UNKNOWN | REGISTERED | TRUSTED | REVOKED
- `verdict`: VALID | SUSPECT | INVALID
- `risk_flags`: Array of detected issues
