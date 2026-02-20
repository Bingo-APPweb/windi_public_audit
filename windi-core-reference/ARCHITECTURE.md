# WINDI Architecture

## Overview

WINDI provides cryptographic document verification for financial institutions without exposing sensitive document content.

## System Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         WINDI Data Flow                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────────────────┐  │
│  │ Document │───▶│  Reader SDK  │───▶│   Verification API       │  │
│  │  (PDF)   │    │  (SHA-256)   │    │   POST /verify           │  │
│  └──────────┘    └──────────────┘    └────────────┬─────────────┘  │
│                                                    │                 │
│                                                    ▼                 │
│                                      ┌──────────────────────────┐   │
│                                      │    Policy Engine         │   │
│                                      │    (ALLOW/HOLD/BLOCK)    │   │
│                                      └────────────┬─────────────┘   │
│                                                    │                 │
│                         ┌──────────────────────────┼──────────────┐ │
│                         │                          │              │ │
│                         ▼                          ▼              ▼ │
│              ┌──────────────────┐    ┌──────────────────────────┐  │
│              │  Bank Core       │    │   Forensics Engine       │  │
│              │  (Execute/Hold)  │    │   (Audit Trail)          │  │
│              └──────────────────┘    └──────────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Reader SDK (`windi-reader-sdk`)

**Role:** Client-side document processing

**Functions:**
- Compute SHA-256 hash of document
- Canonicalize fields (IBAN, amount, currency)
- Call Verification API
- No document content leaves client

**Key APIs:**
```javascript
client.verify({ document_id, document_hash, issuer_key_id })
Hash.sha256UrnFromFile(path)
Canon.canonIBAN(iban)
```

### 2. Verification API (`windi-verification-api`)

**Role:** Backend verification service

**Functions:**
- Validate hash format
- Check issuer registry
- Verify signature chain
- Return trust level and risk flags

**Endpoints:**
```
POST /verify      — Verify by hash
POST /verify/wvc  — Verify by WVC code
GET  /health      — Health check
```

**Response:**
```json
{
  "verdict": "VALID",
  "integrity": "INTACT",
  "trust_level": "HIGH",
  "issuer_status": "TRUSTED",
  "risk_flags": []
}
```

### 3. Policy Engine (`windi-policy-engine`)

**Role:** Risk-based decision making

**Functions:**
- Apply configurable rules
- Evaluate verification result + context
- Return decision with reason codes

**Rules:**
| Rule | Triggers | Decision |
|------|----------|----------|
| `tamperedOrInvalidSig` | Tampered document | BLOCK |
| `ibanMismatch` | IBAN differs from expected | BLOCK |
| `highValueLowTrust` | High amount + trust < HIGH | HOLD |
| `issuerUnknown` | Unknown issuer | HOLD |

### 4. Forensics Engine (`windi-forensics-engine`)

**Role:** Audit trail and non-repudiation

**Functions:**
- Append-only event log
- Hash chain (prev_hash → event_hash)
- Institutional attestation
- Bundle export for audit

**Event Types:**
```
VERIFY_CALLED → VERIFY_RESULT → POLICY_DECISION → PAYMENT_ACTION
```

### 5. Proof Spec (`windi-proof-spec`)

**Role:** Cryptographic standards

**Defines:**
- ProofSet JSON Schema
- Canonicalization rules
- Shelf definitions
- Hash algorithm (SHA-256)
- WVC QR format

### 6. WCAF Toolkit (`windi-wcaf-toolkit`)

**Role:** Auditor tools

**Commands:**
```bash
wcaf verify   <bundle.json>
wcaf timeline <bundle.json>
wcaf replay   <bundle.json>
wcaf export   <bundle.json>
```

## Data Contracts

### Verification Request
```json
{
  "document_id": "windi:doc:inv-2026-001",
  "document_hash": "sha256:abc123...",
  "issuer_key_id": "windi:key:bank-de",
  "proof_level": "L2"
}
```

### Policy Input
```json
{
  "verification": { "verdict": "VALID", "trust_level": "HIGH", ... },
  "doc": { "iban": "DE89370400440532013000" },
  "context": { "expected_iban": "...", "amount": 50000 }
}
```

### WCAF Event
```json
{
  "event_id": "uuid",
  "ts": "2026-02-08T12:00:00Z",
  "document_id": "INV-2025-0001",
  "type": "POLICY_DECISION",
  "payload": { "decision": "ALLOW", "policy_version": "bank-v3.2" },
  "prev_hash": "abc123...",
  "event_hash": "def456...",
  "schema_version": "wcaf-1.0"
}
```

## Security Model

1. **No Content Transmission** — Only hashes cross system boundaries
2. **Hash Chain Integrity** — Tamper-evident audit log
3. **Institutional Signatures** — RSA/Ed25519 attestation
4. **Append-Only Storage** — No UPDATE/DELETE on forensics tables
5. **Key Rotation Ready** — key_id supports versioned keys

## Deployment Topology

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Bank Zone     │     │   WINDI Zone    │     │   Audit Zone    │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│ Reader SDK      │────▶│ Verification API│────▶│ Forensics DB    │
│ Policy Engine   │     │ (public API)    │     │ (append-only)   │
│ Bank Core       │     └─────────────────┘     │ WCAF Toolkit    │
└─────────────────┘                             └─────────────────┘
```
