# WINDI Verification API

**WINDI Proof Interface Layer (WPIL) — Independent verification of WINDI proof artifacts.**

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Spec](https://img.shields.io/badge/spec-windi--proof--spec%20v1.0.0-green)
![License](https://img.shields.io/badge/license-Apache%202.0-blue)

---

## Purpose

> **"You do not need to trust WINDI to verify WINDI."**

This API enables independent verification of WINDI proof artifacts without requiring access to or trust in the originating WINDI system.

It acts as the **WPIL Entry Point** — the layer where external systems connect to verify WINDI receipts.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    External System                       │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│           WINDI Verification API (WPIL)                  │
│                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │   Level 1   │  │   Level 2   │  │   Level 3   │      │
│  │   Schema    │→ │    Hash     │→ │   Ledger    │      │
│  │ Validation  │  │Verification │  │Confirmation │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
│                                                          │
└─────────────────────────┬───────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              WINDI Verify Public (:8145)                 │
│                   (Optional)                             │
└─────────────────────────────────────────────────────────┘
```

---

## Verification Levels

| Level | Name | What It Does |
|-------|------|--------------|
| **1** | Schema Validation | Validates receipt structure against `windi-proof-spec v1.0.0` |
| **2** | Hash Verification | Validates `content_hash` format (64 hex chars, SHA-256) |
| **3** | Ledger Confirmation | Confirms receipt exists in WINDI Forensic Ledger |

---

## API Endpoints

### `GET /`

Service information.

### `GET /health`

Health check (Living Tree compatible).

```json
{
  "status": "healthy",
  "service": "windi-verification-api",
  "role": "WPIL",
  "version": "1.0.0",
  "spec_version": "1.0.0"
}
```

### `POST /verify`

Verify a single receipt.

**Request:**
```json
{
  "receipt": {
    "spec_version": "1.0.0",
    "receipt_id": "WINDI-LAW-20260410094726-289EE95D",
    "issued_at": "2026-04-10T09:47:26Z",
    "actor": "did:windi:dragon-001",
    "app": "windi-law",
    "content_hash": "9d4e1e23bd5b727046a9e3b4b7db57bd8d6ee684d5a63e7d8f6a3d1c1f1f9abc",
    "hash_algorithm": "SHA-256",
    "governance_level": "HIGH",
    "verify_url": "https://windi-domain.com/verify/WINDI-LAW-20260410094726-289EE95D",
    "human_approved": true,
    "invariants": ["I9", "I11"]
  }
}
```

**Response:**
```json
{
  "verified": true,
  "receipt_id": "WINDI-LAW-20260410094726-289EE95D",
  "timestamp": "2026-04-16T12:00:00Z",
  "levels": {
    "schema": "VALID",
    "hash": "MATCH",
    "ledger": "CONFIRMED"
  },
  "governance_status": {
    "level": "HIGH",
    "human_approved": true,
    "policy_decision": null,
    "invariants": ["I9", "I11"]
  },
  "warnings": [],
  "errors": [],
  "verifier": {
    "name": "WINDI Verification API",
    "version": "1.0.0",
    "spec_version": "1.0.0",
    "role": "WPIL"
  }
}
```

### `POST /verify/batch`

Verify multiple receipts.

**Request:**
```json
{
  "receipts": [
    { "spec_version": "1.0.0", "receipt_id": "...", ... },
    { "spec_version": "1.0.0", "receipt_id": "...", ... }
  ]
}
```

**Response:**
```json
{
  "verified": true,
  "timestamp": "2026-04-16T12:00:00Z",
  "summary": {
    "total": 2,
    "verified": 2,
    "failed": 0
  },
  "results": [...]
}
```

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `4000` | Server port |
| `HOST` | `0.0.0.0` | Server host |
| `WINDI_VERIFY_URL` | `https://windi-domain.com/verify-public/api/verify` | WINDI Ledger verification endpoint |
| `WPIL_MODE` | `relay` | Mode: `relay` (local+remote) or `local` |
| `WPIL_SKIP_REMOTE` | `false` | Skip remote verification |
| `LOG_LEVEL` | `info` | Log level: `debug`, `info`, `warn`, `error` |

---

## Running

### Local Development

```bash
npm install
npm start
```

### Docker

```bash
docker build -t windi-verification-api .
docker run -p 4000:4000 windi-verification-api
```

### Production

```bash
PORT=4000 WINDI_VERIFY_URL=https://windi-domain.com/verify-public/api/verify npm start
```

---

## Invariants Alignment

This API respects WINDI Constitutional Invariants:

| Invariant | Relevance |
|-----------|-----------|
| **I9** | Checks `human_approved` for HIGH governance receipts |
| **I11** | Validates evidence hash format and permanence |
| **I14** | Validates `actor` and `app` are not placeholders |

---

## WINDI Ecosystem Position

```
┌─────────────────────────────────────────────────────────┐
│                    WINDI Ecosystem                       │
├─────────────────────────────────────────────────────────┤
│  windi-proof-spec      ◄── Canonical schema             │
│  windi-verification-api ◄── YOU ARE HERE (WPIL)        │
│  windi-reader-sdk      ◄── Client SDK                   │
│  windi-policy-engine   ◄── Decision layer               │
│  windi-forensics-engine◄── Audit trail                  │
│  windi-wcaf-toolkit    ◄── Auditor tools                │
└─────────────────────────────────────────────────────────┘
```

---

## Security

- No sensitive data processed
- Cryptographic integrity by design
- Deterministic verification
- Auditability and compliance readiness

See [SECURITY.md](SECURITY.md) for responsible disclosure.

---

## License

Apache 2.0 — See [LICENSE](LICENSE)

---

**WINDI Verification API v1.0.0** — *WPIL Entry Point*

> "AI processes. Human decides. WINDI guarantees."
