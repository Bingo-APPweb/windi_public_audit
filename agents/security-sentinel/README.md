# W-SEC-001 Security Sentinel

**Port:** 8144
**Status:** MVP
**Version:** 1.0.0

> **"WAF bloqueia. W-SEC entende. Ledger prova."**

## Mission

Security Evidence Architecture for WINDI Core.

W-SEC-001 is the intelligence layer that:
- Detects security events from multiple sensors
- Correlates related events into incidents
- Classifies severity and confidence
- Anchors high-value incidents to the Forensic Ledger

## Principle

**Not every suspicious event deserves a seal.**
**Every seal must arise from correlated evidence.**

## Quick Start

```bash
# Install dependencies
cd /opt/windi/agents/security-sentinel
pip install -r requirements.txt

# Run
python app.py
# or
uvicorn app:app --host 0.0.0.0 --port 8144
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/sec/events` | Ingest single event |
| POST | `/sec/events/batch` | Ingest batch of events |
| GET | `/sec/incidents` | List incidents |
| GET | `/sec/incidents/{id}` | Get incident details |
| GET | `/sec/incidents/{id}/events` | Get incident events |
| POST | `/sec/incidents/{id}/seal` | Seal and anchor to ledger |
| POST | `/sec/incidents/{id}/close` | Close with resolution |
| POST | `/sec/incidents/{id}/investigate` | Mark as investigating |
| GET | `/health` | Health check |
| GET | `/metrics` | Basic metrics |

## Smoke Test

```bash
# 1. Send test event
curl -X POST http://127.0.0.1:8144/sec/events \
  -H "Content-Type: application/json" \
  -d '{
    "event_id":"sec_evt_test_001",
    "timestamp":"2026-04-08T12:00:00Z",
    "source":"constitutional-agent",
    "sensor":"rate_limiter",
    "event_type":"rate_limit_exceeded",
    "severity":"medium",
    "confidence":0.85,
    "actor":{"ip":"203.0.113.10","session_id":"sess_1","user_agent":"curl/8.5.0"},
    "target":{"service":"w-gateway-001","endpoint":"/gateway/call","method":"POST"},
    "threat":{"family":"abuse","vector":"api_flood"}
  }'

# Expected: incident_id created

# 2. Send similar event (should correlate)
curl -X POST http://127.0.0.1:8144/sec/events \
  -H "Content-Type: application/json" \
  -d '{
    "event_id":"sec_evt_test_002",
    "timestamp":"2026-04-08T12:00:30Z",
    "source":"constitutional-agent",
    "sensor":"rate_limiter",
    "event_type":"rate_limit_exceeded",
    "severity":"medium",
    "confidence":0.85,
    "actor":{"ip":"203.0.113.10","session_id":"sess_1","user_agent":"curl/8.5.0"},
    "target":{"service":"w-gateway-001","endpoint":"/gateway/call","method":"POST"},
    "threat":{"family":"abuse","vector":"api_flood"}
  }'

# Expected: correlated: true (same incident)

# 3. List incidents
curl http://127.0.0.1:8144/sec/incidents

# 4. Seal incident
curl -X POST http://127.0.0.1:8144/sec/incidents/{incident_id}/seal

# Expected: ledger_receipt_id
```

## Integration with Sensors

### From security.py (rate limiter)

```python
from sensors import rate_limit_event
import httpx

async def on_rate_limit_exceeded(ip, session_id, user_agent, endpoint, count):
    evt = rate_limit_event(
        ip=ip,
        session_id=session_id,
        user_agent=user_agent,
        service="constitutional-agent",
        endpoint=endpoint,
        method="POST",
        count=count,
        window_seconds=60,
    )

    async with httpx.AsyncClient() as client:
        await client.post(
            "http://127.0.0.1:8144/sec/events",
            json=evt.model_dump(mode="json")
        )
```

### From constitutional_gate.py (invariant violation)

```python
from sensors import constitutional_violation_event
import httpx

async def on_invariant_violation(ip, did, session_id, endpoint, invariant, action):
    evt = constitutional_violation_event(
        ip=ip,
        did=did,
        session_id=session_id,
        service="constitutional-agent",
        endpoint=endpoint,
        invariant=invariant,
        action_attempted=action,
    )

    async with httpx.AsyncClient() as client:
        await client.post(
            "http://127.0.0.1:8144/sec/events",
            json=evt.model_dump(mode="json")
        )
```

## Severity Escalation

| Condition | Effect |
|-----------|--------|
| event_count >= 25 | +1 severity level |
| event_count >= 100 | +2 severity levels |
| Critical endpoint hit | +1 severity level |
| High-priority event type | +1 severity level |

## Event Types

| Type | Base Severity | Family |
|------|---------------|--------|
| `rate_limit_exceeded` | medium | abuse |
| `token_invalid` | low | intrusion |
| `token_replay_detected` | high | intrusion |
| `forbidden_endpoint_access` | high | intrusion |
| `device_binding_mismatch` | medium | intrusion |
| `constitutional_violation_attempt` | high | tampering |
| `merkle_integrity_failed` | critical | tampering |
| `seal_forgery_attempt` | critical | tampering |

## Architecture

```
[Sensors]
    ↓
POST /sec/events
    ↓
[Correlation Engine]
    ↓
SEC-INCIDENT created/updated
    ↓
POST /sec/incidents/{id}/seal
    ↓
[Ledger Client]
    ↓
Forensic Ledger :8101
```

## Invariants

- **I9**: Human approval required for response actions
- **I11**: Sealed incidents become permanent evidence

## Files

```
/opt/windi/agents/security-sentinel/
├── app.py              # FastAPI application
├── config.py           # Configuration
├── schemas.py          # Data models
├── storage.py          # In-memory storage (MVP)
├── security_sentinel.py # Core engine
├── correlation.py      # Correlation logic
├── classifiers.py      # Severity/action classifiers
├── canonicalize.py     # Hash computation
├── ledger_client.py    # Forensic Ledger integration
├── maestro_client.py   # Maestro case integration
├── sensors.py          # Event factory helpers
├── requirements.txt    # Dependencies
└── README.md           # This file
```

## Roadmap

### Phase A (MVP) ✅
- FastAPI on :8144
- Event ingestion
- In-memory correlation
- Ledger anchoring

### Phase B
- SQLite persistence
- Retry queue
- Maestro integration
- Suppressions/allowlist

### Phase C
- Correlation rules engine
- Multi-sensor scoring
- IP reputation
- Operator console

---

*W-SEC-001 · WINDI Security Evidence Architecture*
*"Detectar ≠ acusar. Registrar ≠ identificar. Selar ≠ publicar tudo."*
