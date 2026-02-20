# WINDI Verification API

## Overview

The WINDI Verification API is the core backend service for document integrity verification in the WINDI ecosystem.

## Endpoints

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "WINDI Verification API running"
}
```

### POST /verify

Validates document integrity using the WINDI ProofSet.

#### Request Body
```json
{
  "document_id": "windi:doc:abc123",
  "document_hash": "sha256:a7f5f35426b927411fc9231b56382173a0b25fd4e8c9d72a4f3c8b9d74e91c23",
  "proof_shelves": {
    "payto_hash": "sha256:7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069",
    "amount_hash": "sha256:2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae"
  }
}
```

#### Response
```json
{
  "verdict": "VALID",
  "integrity": "INTACT",
  "trust_level": "L2",
  "issuer_status": "TRUSTED",
  "checks": {
    "schema_valid": true
  },
  "risk_flags": []
}
```

## Running Locally

```bash
npm install
npm start
```

Server runs on port 4000 by default. Set `PORT` environment variable to change.

## Testing

```bash
# Health check
curl http://localhost:4000/health

# Verify document
curl -X POST http://localhost:4000/verify \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "windi:doc:test-001",
    "document_hash": "sha256:a7f5f35426b927411fc9231b56382173a0b25fd4e8c9d72a4f3c8b9d74e91c23",
    "proof_shelves": {}
  }'
```

## Architecture

```
┌─────────────────────────────────────────────────┐
│              WINDI Verification API              │
├─────────────────────────────────────────────────┤
│  routes/verify.js      → HTTP endpoint           │
│  services/             → Business logic          │
│  validation/           → ProofSet schema check   │
│  utils/                → Logging utilities       │
└─────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────┐
│           windi-proof-spec                       │
│           (ProofSet JSON Schema)                 │
└─────────────────────────────────────────────────┘
```

## Related Repositories

- [windi-proof-spec](https://github.com/Bingo-APPweb/windi-proof-spec) — ProofSet schema
- [windi-reader-sdk](https://github.com/Bingo-APPweb/windi-reader-sdk) — Client SDK
