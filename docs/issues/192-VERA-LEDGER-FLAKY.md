# §192 — VERA→Ledger Connection Flaky

**Status:** OPEN  
**Priority:** P2  
**Discovered:** 19 Apr 2026, during §191 audit  
**Affects:** W-ENTERPRISE-001 (:8150) → Forensic Ledger (:8101)

---

## Problem

During §191-B verification, the VERA seal-opinion endpoint occasionally fails to POST to the Ledger even with a valid DID. The error returned is:

```json
{
  "status": "seal_aborted",
  "ledger_error": "unknown",
  "retry_hint": {...}
}
```

The §191-B fix correctly returns HTTP 502 instead of the misleading `sealed_local`, but the root cause of the connection failure remains undiagnosed.

---

## Observed Behaviour

| Test | DID | Expected | Actual |
|------|-----|----------|--------|
| T2 (§191-B) | `did:windi:dragon-001` (valid) | `ledger_confirmed: true` | `ledger_error: "unknown"` |

The Ledger itself was healthy (verified via direct curl to :8101).

---

## Suspected Causes

1. **Timeout** — VERA POST to Ledger may timeout under load
2. **Connection pool exhaustion** — httpx/aiohttp connection not released
3. **Race condition** — Concurrent requests causing rejection
4. **Payload size** — Large vera_response exceeding limits

---

## Diagnostic Steps

```bash
# 1. Watch VERA logs during seal
journalctl -u windi-enterprise -f | grep -i ledger

# 2. Monitor Ledger connections
watch -n1 'ss -tlnp | grep 8101'

# 3. Test minimal payload
curl -X POST http://localhost:8150/vera/seal-opinion \
  -H "Content-Type: application/json" \
  -d '{"question":"x","vera_response":"y","officer_id":"did:windi:dragon-001"}'
```

---

## Proposed Fix

1. Add retry with exponential backoff in `vera_agent.py`
2. Log full Ledger response on failure
3. Add circuit breaker if Ledger fails >3x in 60s

---

## Files

- `/opt/windi/w-enterprise-001/vera_agent.py`

---

## Related

- §191-B: `WINDI-191-B-GATE-HARDENING-20260419`

---

**Opened:** 19 April 2026 · Liga IA+H
