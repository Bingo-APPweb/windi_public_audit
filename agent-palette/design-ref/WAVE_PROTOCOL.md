# WINDI Capacity Governance — Wave Protocol v1.0

> "A porteira antes do cavalo. Controla a admissão, nunca chegas à ruptura."
> — Guardian Dragon, 2026-02-25

## Protocol Overview

The Wave Protocol governs WINDI's controlled growth through capacity tiers. Each wave represents a stability checkpoint — not a calendar date, but a proven operational threshold.

## Wave Definitions

| Wave | Limit | Tier | Description | Stability Requirement |
|------|-------|------|-------------|----------------------|
| **Wave 0** | 10 | Internal | Founding team, core testers | Initial deployment |
| **Wave 1** | 50 | Beta | Invite-only, trusted partners | 14 days stable from Wave 0 |
| **Wave 2** | 200 | Controlled | Free tier with waitlist | 14 days stable from Wave 1 |
| **Wave 3** | 500 | Open | Free tier, open registration | 14 days stable from Wave 2 |
| **Wave 4** | 1000+ | Scale | PostgreSQL migration trigger | Infrastructure upgrade |

## Stability Criteria (14-Day Rule)

A wave is considered **stable** when ALL conditions hold for 14 consecutive days:

```
STABLE = (
    sentinel_incidents == 0 AND
    sqlite_locks == 0 AND
    cpu_avg < 60% AND
    memory_avg < 70% AND
    api_latency_p95 < 500ms AND
    ledger_sync_failures == 0
)
```

**Important**: Calendar days do NOT count. Only operational days meeting ALL criteria.

## Current Status

```
Wave:     0 (Internal)
Limit:    10
Current:  10 humans
Status:   AT CAPACITY
Next:     Wave 1 (50) — awaiting 14-day stability window
```

## Genesis Integration

The `genesis.js` module checks wave capacity before showing the Baptism Ritual:

```javascript
// Endpoint: GET /api/wallet/health
// Response includes: { "humans": 10, ... }

const WAVE_CONFIG = {
  current_wave: 0,
  wave_limits: [10, 50, 200, 500, 1000],
  waitlist_enabled: true,
};

// If humans >= wave_limits[current_wave], show waitlist
```

### Behavior Matrix

| Condition | Genesis Action |
|-----------|----------------|
| `humans < limit` | Show Baptism Ritual |
| `humans >= limit` | Show Waitlist Message |
| `humans >= limit` + invite_code | Allow Baptism (Wave 1+) |

## Waitlist Messages (Trilingual)

### Portuguese
```
O Ledger está em fase de crescimento controlado.
Estás na lista de espera — serás notificado quando houver vagas.
Wave actual: 0 (Interno) | Próxima: Wave 1 (Beta)
```

### German
```
Das Ledger befindet sich in kontrollierter Wachstumsphase.
Du bist auf der Warteliste — wir benachrichtigen dich, wenn Plätze frei werden.
Aktuelle Wave: 0 (Intern) | Nächste: Wave 1 (Beta)
```

### English
```
The Ledger is in controlled growth phase.
You're on the waitlist — we'll notify you when spots open.
Current Wave: 0 (Internal) | Next: Wave 1 (Beta)
```

## Rate Limits by Tier

| Tier | Requests/min | Documents/day | Ledger seals/day |
|------|--------------|---------------|------------------|
| PERSONAL | 30 | 10 | 5 |
| ORGANIZATION | 100 | 100 | 50 |
| GOVERNANCE | 300 | unlimited | unlimited |

## PostgreSQL Migration Triggers (Wave 4)

When ANY of these conditions occur, PostgreSQL migration becomes mandatory:

```
MIGRATE_TRIGGER = (
    humans >= 800 OR
    sqlite_file_size > 500MB OR
    concurrent_writes > 50/sec OR
    query_latency_p99 > 200ms
)
```

## Sentinel Integration

The Sentinel monitors wave stability metrics:

```yaml
wave_monitoring:
  check_interval: 60s
  metrics:
    - sqlite_locks
    - cpu_percent
    - memory_percent
    - api_latency
    - ledger_sync_status

  alerts:
    - type: wave_stability_breach
      condition: "any metric exceeds threshold"
      action: reset_stability_counter

    - type: wave_capacity_reached
      condition: "humans >= wave_limit"
      action: notify_guardian
```

## Invite Code System (Wave 1+)

Starting from Wave 1, invite codes allow controlled expansion:

```
Code Format: WINDI-W1-XXXX-XXXX
Validity:    7 days
Uses:        1 (single use)
Generator:   Guardian Dragon only (I9)
```

## Decision Authority

| Decision | Authority | Protocol |
|----------|-----------|----------|
| Open next wave | Guardian Dragon | I9 approval required |
| Issue invite code | Guardian Dragon | Logged in Decision Journal |
| Emergency capacity increase | Guardian + Architect | Dual approval |
| PostgreSQL migration | All Three Dragons | Unanimous consensus |

## Changelog

- **v1.0** (2026-02-25): Initial protocol — Guardian Dragon directive

---

**Three Dragons Protocol**
- Guardian Dragon protects the gates
- Architect Dragon builds the infrastructure
- Witness Dragon observes and validates

*"AI processes. Human decides. WINDI guarantees."*
