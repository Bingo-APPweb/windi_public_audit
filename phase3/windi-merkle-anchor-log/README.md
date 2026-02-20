# windi-merkle-anchor-log

Public append-only Merkle Transparency Log (CT-style) for WINDI combined_root_hash anchors.

## Features

- RFC6962-style Merkle tree with domain separation (0x00 leaf, 0x01 node)
- Ed25519 signed tree heads (STH)
- Inclusion proofs for any leaf
- Consistency proofs between tree sizes
- Canonical JSON for deterministic hashing

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | (required) |
| `PORT` | Server port | 4051 |
| `LOG_SIGNING_KEY_PATH` | Path to Ed25519 private key PEM | (required) |
| `LOG_KEY_ID` | Key identifier for STH | hub-log-2026 |
| `LOG_PUBLIC_KEY_PEM` | Public key PEM (for /hub/public-key) | (optional) |

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/anchors` | Append anchor `{ combined_root_hash, node_id? }` |
| GET | `/sth` | Get current Signed Tree Head |
| GET | `/lookup?combined_root_hash=...` | Find leaf by hash |
| GET | `/proof/inclusion?leaf_index=&tree_size=` | Get inclusion proof |
| GET | `/proof/consistency?old_size=&new_size=` | Get consistency proof |
| GET | `/leaves?start=&limit=` | List leaves (paginated) |
| GET | `/hub/public-key` | Get log's public key |
| GET | `/health` | Health check |

## Quick Start

1. Apply schema:
```bash
psql $DATABASE_URL -f sql/001_schema.sql
```

2. Generate Ed25519 key:
```bash
openssl genpkey -algorithm ED25519 -out log_signing_key.pem
openssl pkey -in log_signing_key.pem -pubout -out log_signing_key.pub
```

3. Start server:
```bash
export DATABASE_URL='postgres://windi:windi@localhost:5432/windi'
export LOG_SIGNING_KEY_PATH='./log_signing_key.pem'
export LOG_KEY_ID='hub-log-2026'
export LOG_PUBLIC_KEY_PEM="$(cat log_signing_key.pub)"
npm start
```

4. Test:
```bash
# Add anchor
curl -X POST http://localhost:4051/anchors \
  -H "content-type: application/json" \
  -d '{"combined_root_hash":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}'

# Get STH
curl http://localhost:4051/sth

# Lookup
curl "http://localhost:4051/lookup?combined_root_hash=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"

# Inclusion proof
curl "http://localhost:4051/proof/inclusion?leaf_index=0&tree_size=1"
```

## Docker

```bash
docker build -t windi-merkle-anchor-log .
docker run -p 4051:4051 \
  -e DATABASE_URL=... \
  -e LOG_SIGNING_KEY_PATH=/run/secrets/key.pem \
  -v ./log_signing_key.pem:/run/secrets/key.pem:ro \
  windi-merkle-anchor-log
```

## Notes

- MVP recomputes root/proofs from stored leaves up to tree_size
- For large scale, add `merkle_nodes` caching layer
- Leaf indices are 0-based in API (1-based BIGSERIAL in DB)

## License

MIT - WINDI Project
