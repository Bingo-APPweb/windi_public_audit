# W-KEYS-001 — Quick Reference

**Version**: 1.1.0
**Status**: LIVE
**Date**: 2026-03-13

---

## Tier Rate Limits

| Tier | RPM | RPD | Badge | Trust Boost |
|------|-----|-----|-------|-------------|
| SEED | 10 | 100 | BRONZE | 0% |
| NODAL | 60 | 1,000 | SILVER | +8% |
| SOVEREIGN | 300 | 10,000 | GOLD | +15% |
| ORACLE | ∞ | ∞ | PLATINUM | +20% |

---

## Key Format

```
Production: wnd_live_{32_hex_chars}
Sandbox:    wnd_test_{32_hex_chars}
Key ID:     wk_{24_hex_chars}
```

**Example**: `wnd_live_ad6d4f4a0c939db60b7aacbf7eae43d2`

---

## Endpoints

| Method | Path | Purpose | Auth |
|--------|------|---------|------|
| GET | `/api-keys/health` | Health check | - |
| GET | `/api-keys/tiers` | List tiers | - |
| POST | `/api-keys/request` | Request key | - |
| POST | `/api-keys/{id}/approve` | Approve (I9) | - |
| POST | `/api-keys/{id}/rotate` | Rotate key | - |
| POST | `/api-keys/{id}/revoke` | Revoke key | - |
| GET | `/api-keys/list` | List keys | - |
| GET | `/api-keys/{id}/usage` | Usage stats | - |
| GET | `/api-keys/validate` | Internal auth | Key |

---

## Quick Examples

### 1. Request a Key
```bash
curl -X POST https://windi-domain.com/api-keys/request \
  -H "Content-Type: application/json" \
  -d '{
    "wallet_id": "wal_pioneer_abc123",
    "name": "My API Key",
    "scopes": ["propagation:read"],
    "tier": "NODAL"
  }'
```

### 2. Approve Key (I9)
```bash
curl -X POST https://windi-domain.com/api-keys/{key_id}/approve \
  -H "Content-Type: application/json" \
  -d '{"approved_by": "Human Dragon"}'
# → Returns API key ONCE. Save it!
```

### 3. Use the Key
```bash
curl https://windi-domain.com/api/receipts \
  -H "X-WINDI-API-Key: wnd_live_..."
```

### 4. Rotate Key
```bash
curl -X POST https://windi-domain.com/api-keys/{key_id}/rotate \
  -H "Content-Type: application/json" \
  -d '{"rotated_by": "Human Dragon"}'
# Old key valid for 24h grace period
```

### 5. Check Usage
```bash
curl https://windi-domain.com/api-keys/{key_id}/usage
```

---

## Scopes

| Scope | Description |
|-------|-------------|
| `ledger:read` | Read Forensic Ledger receipts |
| `ledger:write` | Create Forensic Ledger receipts |
| `verify:read` | Verify documents |
| `propagation:read` | Read propagation stats |
| `propagation:write` | Record propagation events |
| `communique:read` | Read messages |
| `communique:write` | Send messages |
| `all` | Full access |

---

## Key Lifecycle

```
                    ┌─────────────┐
                    │   REQUEST   │
                    └──────┬──────┘
                           │
                           ▼
                  ┌────────────────┐
                  │ pending_approval│
                  └────────┬───────┘
                           │ Human approval (I9)
                           ▼
                    ┌──────────┐
           ┌────────│  active  │────────┐
           │        └──────────┘        │
           │              │             │
     Rotate│              │Revoke    Expire
           ▼              ▼             ▼
    ┌──────────┐   ┌──────────┐  ┌──────────┐
    │ rotating │   │ revoked  │  │ expired  │
    └──────────┘   └──────────┘  └──────────┘
         │
         │ 24h grace
         ▼
    ┌──────────┐
    │ expired  │
    └──────────┘
```

---

## Constitutional Compliance

| Invariant | Implementation |
|-----------|----------------|
| **I9** | Key activation requires human approval |
| **I5** | All operations logged in audit table |
| **I6** | Hash-chained audit trail |
| **I10** | Key lifecycle sealed in Forensic Ledger |

---

## Files

| File | Purpose |
|------|---------|
| `/opt/windi/specs/w-keys-001-openapi.yaml` | OpenAPI 3.1 spec |
| `/opt/windi/specs/w-keys-001-schemas.json` | JSON Schema definitions |
| `/opt/windi/agents/constitutional-agent/blueprints/api_keys_blueprint.py` | Implementation |
| `/opt/windi/data/api_keys.db` | SQLite database |

---

*W-KEYS-001 · WINDI Publishing House · Kempten, Bavaria*
