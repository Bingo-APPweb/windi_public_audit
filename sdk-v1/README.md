# WINDI SDK v1.0 — Governance Telemetry System

> **AI processes. Human decides. WINDI guarantees.**

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     WINDI SYSTEM v1.0                        │
│                                                              │
│  ┌──────────┐    ┌──────────┐    ┌───────────┐              │
│  │  a4Desk   │    │  Bridge  │    │ Dashboard │              │
│  │  (Edge)   │───▶│  (Core)  │───▶│ (Monitor) │              │
│  │           │    │          │    │           │              │
│  │ Emitter   │    │ Validate │    │ ECG Pulse │              │
│  │ Hash+Sign │    │ Decode   │    │ Shelf HP  │              │
│  │ Zero-Know │    │ Aggregate│    │ Hotspots  │              │
│  └──────────┘    └──────────┘    └───────────┘              │
│       ▲               ▲               ▲                      │
│       │               │               │                      │
│  RFC-001/002    HMAC Verify      Signal Feed                │
│  Micro-Signals  Anti-Replay      Live Render                │
│                                                              │
│  ════════════════════════════════════════════                │
│  Flow is Truth. Content is Sovereign.                        │
│  Documents carry signals, never content.                     │
└─────────────────────────────────────────────────────────────┘
```

## Components

| Component | Path | Description |
|-----------|------|-------------|
| **Schemas** | `/schemas/` | RFC-002 JSON Schema + example payload |
| **Registry** | `/registry/` | Micro-Signal binary code registry |
| **Emitters** | `/emitters/` | Python + TypeScript reference emitters |
| **Bridge API** | `/bridge/` | Telemetry receiver with HMAC validation |
| **Simulator** | `/simulator/` | Deutsche Bahn 1000-signal generator |
| **Dashboard** | `/dashboard/` | Real-time governance monitor (HTML) |
| **Docs** | `/docs/` | RFC documents and guides |

## Quick Start

### 1. Start the Bridge API
```bash
cd bridge
python windi_bridge.py
# Listening on 0.0.0.0:8090
```

### 2. Run the DB Simulation
```bash
# Send 1000 signals to Bridge
cd simulator
python db_simulator.py --mode bridge --signals 1000

# Or export to JSON
python db_simulator.py --mode export --output db_sim.json
```

### 3. Open the Dashboard
```bash
# Serve dashboard (Bridge must be running)
cd dashboard
python -m http.server 8091
# Open http://localhost:8091
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | System health check |
| GET | `/api/v1/dashboard` | Full dashboard state |
| GET | `/api/v1/shelf/{S1-S7}` | Shelf detail signals |
| GET | `/api/v1/registry` | Signal code registry |
| POST | `/api/v1/telemetry` | Ingest single packet |
| POST | `/api/v1/telemetry/batch` | Ingest batch packets |
| POST | `/api/v1/register` | Register client HMAC key |

## Security Model (Zero-Knowledge)

```
Client (a4Desk) holds:        WINDI Core receives:
─────────────────────         ──────────────────────
✓ Document content            ✗ Document content
✓ Domain names                ✗ Domain names
✓ Personal data               ✗ Personal data
✓ CSALT (secret)              ✓ HMAC signature
✓ HMAC key                    ✓ Hashed domain
                              ✓ Hashed doc fingerprint
                              ✓ Shelf + Code + Weight
                              ✓ Event + Context flags
```

## RFC Compliance

- **RFC-001**: Micro-Signal Lexicon v1.0 (7 Shelves, 14 Signals)
- **RFC-002**: Governance Telemetry Encoding v1.0 (HMAC-SHA256 + Ed25519)

## Protocol

- WINDI Handshake Protocol v1.1 (frozen)
- Marco Zero: 2026-01-19
- Three Dragons Protocol: Guardian + Architect + Witness
