# WINDI Phase 3: Hub ↔ Node Federation Layer

## Overview

Phase 3 implements the **Node Identity & Attestation System**, the foundation for WINDI federation. This allows independent WINDI Nodes to cryptographically identify themselves to the a4Desk Hub.

```
┌─────────────────────────────────────────────────────────────────┐
│                        a4Desk Hub (Strato)                       │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              hub-node-registry (:8070)                      │ │
│  │  • Node Registration    • Attestation Verification         │ │
│  │  • Certificate Issuance • Public Key Registry              │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ Ed25519 Signed Attestations
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
   ┌─────────┐          ┌─────────┐          ┌─────────┐
   │ Node A  │          │ Node B  │          │ Node C  │
   │ (Bank)  │          │ (Gov)   │          │ (Corp)  │
   └─────────┘          └─────────┘          └─────────┘
```

## Architecture

### Node Identity Model

- **Node ID Format**: `node:<org>-<location>-<instance>`
  - Example: `node:deutschebank-frankfurt-01`
- **Keypair**: Ed25519 (32-byte public key, 64-byte secret key)
- **Storage**: Keys stored at Hub in PostgreSQL, locally in JSON files

### Attestation Flow

1. **Node generates keypair** (Ed25519)
2. **Node registers** with Hub (sends public key)
3. **Node creates attestation** payload with timestamp
4. **Node signs** attestation with secret key
5. **Hub verifies** signature and timestamp freshness
6. **Hub issues** signed certificate

### Security Features

- All signatures use Ed25519
- Canonical JSON before signing (sorted keys, no whitespace)
- Replay protection: 5-minute attestation window
- Certificate expiration: 1 year (configurable)

## Folder Structure

```
/opt/windi/phase3/
├── docker-compose.yml           # Full stack deployment
├── README.md                    # This file
│
├── hub-node-registry/           # Hub microservice
│   ├── Dockerfile
│   ├── package.json
│   ├── src/
│   │   └── server.js            # Express server
│   └── sql/
│       └── 001_schema.sql       # PostgreSQL schema
│
├── windi-node-identity-client/  # Node.js client library
│   ├── package.json
│   └── src/
│       └── index.js             # WindiNodeIdentity class
│
└── examples/
    ├── register-node.js         # Full registration example
    └── curl-example.sh          # cURL demonstration
```

## API Endpoints

### Hub Node Registry (:8070)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Service health check |
| GET | `/hub/public-key` | Get Hub's public key |
| POST | `/nodes/register` | Register a new node |
| POST | `/nodes/attest` | Submit attestation, get certificate |
| GET | `/nodes/:node_id` | Get node details |
| GET | `/nodes/:node_id/certificate` | Get node's certificate |
| GET | `/nodes/:node_id/events` | Get node event history |
| GET | `/nodes` | List all nodes |

## Quick Start

### 1. Start with Docker Compose

```bash
cd /opt/windi/phase3
docker-compose up -d

# Check health
curl http://localhost:8070/health
```

### 2. Register a Node (Node.js)

```bash
cd /opt/windi/phase3/examples
npm install --prefix ../windi-node-identity-client

NODE_ID=node:myorg-berlin-01 \
NODE_DOMAIN=windi.myorg.de \
HUB_URL=http://localhost:8070 \
node register-node.js
```

### 3. Manual Registration (cURL)

```bash
# Register
curl -X POST http://localhost:8070/nodes/register \
  -H "Content-Type: application/json" \
  -d '{
    "node_id": "node:myorg-berlin-01",
    "domain": "windi.myorg.de",
    "public_key": "BASE64_ED25519_PUBLIC_KEY",
    "roles": ["verifier"]
  }'

# Attest (requires signed payload)
curl -X POST http://localhost:8070/nodes/attest \
  -H "Content-Type: application/json" \
  -d '{
    "node_id": "node:myorg-berlin-01",
    "attestation": {
      "node_id": "node:myorg-berlin-01",
      "domain": "windi.myorg.de",
      "roles": ["verifier"],
      "timestamp": "2026-02-08T12:00:00Z"
    },
    "signature": "BASE64_SIGNATURE"
  }'
```

## Database Schema

### Tables

- **nodes**: Node identities and certificates
- **attestation_history**: All attestation attempts
- **node_events**: Audit log of node lifecycle events
- **hub_signing_keys**: Hub's own keypairs

### Node Status Values

- `PENDING`: Registered but not attested
- `ACTIVE`: Attested and operational
- `SUSPENDED`: Temporarily disabled
- `REVOKED`: Permanently revoked

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Service port | `8070` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://windi:windi@localhost:5432/windi_hub` |
| `HUB_SIGNING_KEY` | Base64 Ed25519 seed (32 bytes) | Auto-generated |

## Certificate Format

```json
{
  "version": "1.0",
  "node_id": "node:deutschebank-frankfurt-01",
  "domain": "windi.deutschebank.de",
  "public_key": "BASE64...",
  "public_key_fingerprint": "abc123...",
  "roles": ["verifier", "anchor_publisher"],
  "status": "ACTIVE",
  "issued_at": "2026-02-08T12:00:00Z",
  "expires_at": "2027-02-08T12:00:00Z",
  "issuer": {
    "hub_id": "windi-hub-primary",
    "public_key": "BASE64..."
  },
  "hub_signature": "BASE64..."
}
```

## Integration Points

This federation layer enables:

- **Issuer Registry Sync**: Nodes can publish/consume issuer updates
- **Anchor Federation**: Distributed transparency anchoring
- **Governance Permissions**: Role-based access control
- **Cross-Node Verification**: Verify documents across nodes

## Next Steps (Phase 3+)

1. **Sync Protocol**: Real-time issuer registry synchronization
2. **Anchor Federation**: Multi-node transparency anchoring
3. **Governance Mesh**: Distributed policy enforcement
4. **Node Discovery**: Automatic node discovery via DNS

---

**Principle**: AI processes. Human decides. WINDI guarantees.

**Invariante I9**: Zero auto_apply. All federation actions require human approval.
