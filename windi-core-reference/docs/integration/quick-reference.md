# WINDI Verifier Quick Reference

## API Endpoint

```
POST https://api.windi.systems/verify
```

## Request

```json
{
  "document_hash": "sha256-hex-64-chars",
  "proof": {
    "issuer_id": "string",
    "signature": "base64",
    "signed_at": "ISO-8601",
    "public_key_id": "string"
  },
  "context": {
    "transaction_value": number,
    "currency": "string",
    "iban": "string"
  },
  "locale": "en|de|pt"
}
```

## Response

```json
{
  "decision": "ALLOW|HOLD|BLOCK",
  "trust_level": "LOW|MEDIUM|HIGH",
  "reason_codes": ["string"],
  "reasons": ["localized string"],
  "request_id": "string"
}
```

## Decisions

| Decision | Action |
|----------|--------|
| `ALLOW` | Proceed |
| `HOLD` | Manual review |
| `BLOCK` | Reject |

## Trust Levels

| Level | Issuer Status |
|-------|---------------|
| `LOW` | Unknown/Applied |
| `MEDIUM` | Registered |
| `HIGH` | Trusted |

## Common Reason Codes

| Code | Meaning |
|------|---------|
| `SIGNATURE_INVALID` | Bad signature |
| `ISSUER_UNKNOWN` | Unknown issuer |
| `ISSUER_SUSPENDED` | Issuer suspended |
| `HASH_MISMATCH` | Document altered |
| `HIGH_VALUE_LOW_TRUST` | Risk threshold |

## Quick Start

```javascript
// Hash document locally
const hash = crypto.createHash("sha256")
  .update(fs.readFileSync("doc.pdf"))
  .digest("hex");

// Call WINDI API
const res = await fetch("https://api.windi.systems/verify", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ document_hash: hash, proof, locale: "en" })
});

const { decision, reasons } = await res.json();
```

## Environment Variables

```bash
WINDI_API_URL=https://api.windi.systems
WINDI_API_KEY=your-api-key
```
