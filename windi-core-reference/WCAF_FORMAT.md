# WINDI Chain Audit Format (WCAF)

## Overview

WCAF is the standard format for WINDI forensic event logs. It provides:

- Append-only event chain
- Hash-based integrity verification
- Institutional attestation
- Portable audit bundles

## Event Structure

```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "ts": "2026-02-08T12:00:00.000Z",
  "document_id": "INV-2025-0001",
  "type": "VERIFY_RESULT",
  "actor": {
    "system": "verification-api",
    "instance_id": "api-1"
  },
  "payload": {
    "verdict": "VALID",
    "integrity": "INTACT",
    "trust_level": "HIGH"
  },
  "prev_hash": "GENESIS",
  "event_hash": "abc123def456...",
  "schema_version": "wcaf-1.0"
}
```

## Event Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event_id` | UUID | Yes | Unique event identifier |
| `ts` | ISO 8601 | Yes | Event timestamp |
| `document_id` | String | Yes | Document being tracked |
| `type` | String | Yes | Event type (see below) |
| `actor` | Object | No | System that generated event |
| `payload` | Object | Yes | Event-specific data |
| `prev_hash` | Hex(64) | Yes | Hash of previous event or "GENESIS" |
| `event_hash` | Hex(64) | Yes | SHA-256 of canonicalized event |
| `schema_version` | String | Yes | WCAF schema version |

## Event Types

| Type | Description | Typical Payload |
|------|-------------|-----------------|
| `VERIFY_CALLED` | Verification API called | `{ document_hash, issuer_key_id }` |
| `VERIFY_RESULT` | Verification completed | `{ verdict, integrity, trust_level }` |
| `POLICY_DECISION` | Policy engine decision | `{ decision, reason_codes, policy_version }` |
| `PAYMENT_ACTION` | Payment system action | `{ action, ticket, executed_at }` |
| `NOTE` | Manual annotation | `{ author, text }` |

## Hash Chain

Events form a hash chain:

```
GENESIS → event_hash[0] → event_hash[1] → event_hash[2] → ...
           ↑                 ↑                 ↑
         prev_hash[1]    prev_hash[2]     prev_hash[3]
```

### Hash Computation

1. Create event core (all fields except `event_hash`)
2. Canonicalize to stable JSON (sorted keys, no undefined)
3. Compute SHA-256
4. Store as lowercase hex

```javascript
event_hash = sha256(stableStringify(eventCore))
```

## Attestation

Institutional signature over chain head:

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

### Signature Payload

```json
{
  "document_id": "INV-2025-0001",
  "head_event_hash": "abc123...",
  "attested_at": "2026-02-08T12:45:22Z",
  "schema_version": "wcaf-attestation-1.0"
}
```

Signature = Sign(SHA256(stableStringify(payload)), privateKey)

## Bundle Format

Portable audit package:

```json
{
  "bundle_version": "wcaf-bundle-1.0",
  "document_id": "INV-2025-0001",
  "created_at": "2026-02-08T13:00:00Z",

  "timeline": [
    { /* event 1 */ },
    { /* event 2 */ },
    { /* event 3 */ }
  ],

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

## Verification

### Chain Verification

```javascript
function verifyChain(timeline) {
  let prev = "GENESIS";
  for (const event of timeline) {
    if (event.prev_hash !== prev) return false;
    const recomputed = sha256(stableStringify(eventWithoutHash(event)));
    if (recomputed !== event.event_hash) return false;
    prev = event.event_hash;
  }
  return true;
}
```

### Attestation Verification

```javascript
function verifyAttestation(attestation, publicKey) {
  const payload = {
    document_id: attestation.document_id,
    head_event_hash: attestation.head_event_hash,
    attested_at: attestation.attested_at,
    schema_version: attestation.schema_version
  };
  return verify(sha256(stableStringify(payload)), attestation.signature, publicKey);
}
```

## SQL Storage

See `windi-forensics-engine/sql/001_wcaf_schema.sql` for:

- `wcaf_events` — Append-only event table
- `wcaf_attestations` — Institutional signatures
- `wcaf_chain_heads` — View for latest event per document
- `wcaf_verify_chain()` — Server-side chain verification

## Version History

| Version | Date | Changes |
|---------|------|---------|
| `wcaf-1.0` | 2026-02-08 | Initial release |
