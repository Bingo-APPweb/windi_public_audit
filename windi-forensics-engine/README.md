# windi-forensics-engine

Audit trail e replay determinístico para o WINDI — **nível prova pericial**.

Part of the **WINDI** (Worldwide Infrastructure for Non-repudiable Document Integrity) ecosystem.

## Features

| Feature | Status |
|---------|--------|
| Append-only event log | ✅ |
| Hash chain (prev_hash → event_hash) | ✅ |
| verifyChain() tampering detection | ✅ |
| replay() state reconstruction | ✅ |
| MemoryStore adapter | ✅ |
| **PostgresStore adapter** | ✅ |
| **Institutional attestation (signed head)** | ✅ |
| **WCAF Bundle export (portable audit)** | ✅ |
| **Bundle signature verification** | ✅ |

## Installation

```bash
npm install windi-forensics-engine
```

## Quick Start

```js
const { createForensics, EventTypes } = require("windi-forensics-engine");
const crypto = require("crypto");

// Generate institutional keys (in production, use HSM/KMS)
const { publicKey, privateKey } = crypto.generateKeyPairSync("rsa", {
  modulusLength: 2048,
  publicKeyEncoding: { type: "spki", format: "pem" },
  privateKeyEncoding: { type: "pkcs8", format: "pem" }
});

const fx = createForensics({
  keyId: "windi-root-2026",
  privateKey,
  publicKey
});

// Append events
await fx.appendEvent({
  document_id: "INV-2025-0001",
  type: EventTypes.VERIFY_RESULT,
  payload: { verdict: "VALID", trust_level: "HIGH" },
  actor: { system: "verification-api", instance_id: "api-1" }
});

await fx.appendEvent({
  document_id: "INV-2025-0001",
  type: EventTypes.POLICY_DECISION,
  payload: { decision: "ALLOW", policy_version: "bank-v3.2" },
  actor: { system: "policy-engine", instance_id: "pe-1" }
});

// Export audit bundle (with attestation and signature)
const bundle = await fx.exportAuditBundle("INV-2025-0001");
console.log(JSON.stringify(bundle, null, 2));
```

## Event Types

| Type | Description |
|------|-------------|
| `VERIFY_CALLED` | Verification API was called |
| `VERIFY_RESULT` | Verification result received |
| `POLICY_DECISION` | Policy engine decision (include `policy_version`) |
| `PAYMENT_ACTION` | Payment executed/held/blocked |
| `NOTE` | Manual annotation |

## WCAF Event Structure

```json
{
  "event_id": "uuid",
  "ts": "2026-02-08T12:00:00Z",
  "document_id": "INV-2025-0001",
  "type": "POLICY_DECISION",
  "actor": {
    "system": "policy-engine",
    "instance_id": "pe-1"
  },
  "payload": {
    "decision": "ALLOW",
    "policy_version": "bank-v3.2"
  },
  "prev_hash": "abc123...",
  "event_hash": "def456...",
  "schema_version": "wcaf-1.0"
}
```

## Institutional Attestation

Create cryptographic proof that the chain state was certified by the WINDI operator:

```js
const attestation = await fx.createAttestation({
  document_id: "INV-2025-0001"
});

// Verify attestation
const isValid = fx.verifyAttestation(attestation);
```

### Attestation Structure

```json
{
  "document_id": "INV-2025-0001",
  "head_event_hash": "abc123...",
  "attested_at": "2026-02-08T12:45:22Z",
  "signature_alg": "RSA-SHA256",
  "signature": "base64...",
  "key_id": "windi-root-2026",
  "schema_version": "wcaf-attestation-1.0"
}
```

## WCAF Bundle Export

Create a portable, self-contained audit package:

```js
const timeline = await fx.getTimeline({ document_id: "INV-2025-0001" });
const bundle = fx.createBundle({ timeline, attestation });

// Or use the convenience method (includes attestation + signature)
const fullBundle = await fx.exportAuditBundle("INV-2025-0001");

// Verify bundle
const result = fx.verifyBundle(fullBundle);
console.log(result.ok); // true
```

### Bundle Structure

```json
{
  "bundle_version": "wcaf-bundle-1.0",
  "document_id": "INV-2025-0001",
  "created_at": "2026-02-08T13:00:00Z",

  "timeline": [ /* events */ ],

  "chain_verification": {
    "verified": true,
    "head_event_hash": "...",
    "event_count": 3
  },

  "attestation": {
    "attested_at": "...",
    "head_event_hash": "...",
    "signature_alg": "RSA-SHA256",
    "signature": "...",
    "key_id": "windi-root-2026"
  },

  "bundle_signature": {
    "alg": "RSA-SHA256",
    "key_id": "windi-root-2026",
    "signature": "...",
    "signed_hash": "..."
  }
}
```

## PostgreSQL Storage

For production use:

```js
const { Pool } = require("pg");
const { createForensics, PostgresStore } = require("windi-forensics-engine");

const pool = new Pool({ connectionString: process.env.DATABASE_URL });
const store = new PostgresStore(pool);

const fx = createForensics({ store, keyId: "...", privateKey: "..." });
```

### SQL Schema

See `sql/001_wcaf_schema.sql` for the complete schema including:

- `wcaf_events` — Append-only event table with UPDATE/DELETE prevention
- `wcaf_attestations` — Institutional signatures
- `wcaf_chain_heads` — View for latest event per document
- `wcaf_verify_chain()` — Server-side chain verification function

## Testing

```bash
npm test
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  WINDI Forensics Engine                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  appendEvent() ──────────────────────────────────────┐      │
│       │                                               │      │
│       ▼                                               ▼      │
│  ┌─────────┐    ┌─────────────┐    ┌──────────────────────┐ │
│  │ Events  │───▶│ Hash Chain  │───▶│ Attestation (signed) │ │
│  │ (WCAF)  │    │ prev→hash   │    │ head_event_hash      │ │
│  └─────────┘    └─────────────┘    └──────────────────────┘ │
│       │                                       │              │
│       ▼                                       ▼              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                    WCAF Bundle                          ││
│  │  timeline + chain_verification + attestation + signature││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
│  Storage Adapters:                                           │
│  ┌──────────────┐  ┌──────────────┐                         │
│  │ MemoryStore  │  │ PostgresStore│                         │
│  │ (testing)    │  │ (production) │                         │
│  └──────────────┘  └──────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

## What This Proves

| Layer | What It Proves |
|-------|----------------|
| Hash Chain | Technical integrity (no tampering) |
| verifyChain() | Chain continuity |
| Attestation | Institutional authorship |
| Bundle Signature | Complete package integrity |
| policy_version | Which rules produced the decision |
| schema_version | Future compatibility |

## License

Apache 2.0 — See [LICENSE](LICENSE)
