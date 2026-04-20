# W-ACTUARY-001 — Verifiable Actuarial Intelligence Layer

**Port:** 8015
**Invariants:** I9, I11, I14
**Status:** PROTOTYPE

> *"We augment actuarial models with verifiable ground truth."*

## Concept

W-Actuary-001 demonstrates how cryptographically anchored events can be normalized into actuarial signals and traced back to public verification.

**Traditional actuarial models:**
- Statistically sophisticated
- Mathematically sound
- Epistemologically fragile (inputs are declared/inferred, not proven)

**WINDI actuarial layer:**
- Events are cryptographically verified
- Timestamps are exact
- Locations are anchored
- Actors are identified (DID)
- Everything traces back to public verification

## Architecture

```
Event (Real World)
    ↓
Receipt (WINDI Ledger) — I11: Cryptographic Evidence
    ↓
Normalize (W-Actuary) — Event → Actuarial Signal
    ↓
Score (W-Actuary) — Risk Adjustment Factor
    ↓
Verify (Public) — Traceable to origin
```

## Quick Start

```bash
# 1. Install dependencies
cd /opt/windi/w-actuary-001/backend
pip install -r requirements.txt

# 2. Run the service
python main.py

# 3. Open frontend
# http://127.0.0.1:8015 (or serve frontend/index.html)
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Service health check |
| GET | `/receipts` | List demo receipts |
| GET | `/normalize/{id}` | Normalize receipt to actuarial event |
| POST | `/score` | Score normalized event |
| GET | `/demo/full-flow/{id}` | Complete pipeline demo |

## Event Type Mapping

| Event Type | Risk Category | Base Weight |
|------------|---------------|-------------|
| TRAVEL_MOVEMENT | MOBILITY | 0.30 |
| HOTEL_CHECKIN | ACCOMMODATION | 0.20 |
| MOBILITY_SEQUENCE | MOBILITY | 0.35 |
| PAYMENT_VERIFIED | FINANCIAL | 0.40 |
| DOCUMENT_SEALED | LEGAL | 0.50 |
| PRESENCE_CONFIRMED | IDENTITY | 0.25 |

## Confidence Levels

| Level | Multiplier | Description |
|-------|------------|-------------|
| VERIFIED | 1.0 | Cryptographically proven |
| WITNESSED | 0.85 | Multiple attestations |
| DECLARED | 0.5 | Self-reported |
| INFERRED | 0.3 | Reconstructed |

## Risk Adjustment Logic

```
adjustment_factor = 1.0
                  - (confidence_multiplier × 0.2)
                  - location_bonus (0.1 if anchored)
                  - time_bonus (0.05 if exact)

final_score = base_weight × adjustment_factor
```

**Key insight:** Verified events reduce uncertainty → better risk assessment → potential for lower premiums or faster claims.

## Integration with WINDI

The demo uses mock receipts in `demo_data/receipts.json`. To connect to real WINDI data:

1. Replace `load_receipts()` with call to Forensic Ledger `:8101`
2. Use actual `verify_url` from receipts
3. Map real event types to actuarial categories

## Files

```
w-actuary-001/
├── backend/
│   ├── main.py           # FastAPI service
│   └── requirements.txt
├── frontend/
│   └── index.html        # NOIR demo UI
├── demo_data/
│   └── receipts.json     # Mock receipts
└── README.md
```

## Deployment

```bash
# Run with nohup (WINDI pattern)
cd /opt/windi/w-actuary-001/backend
nohup python main.py > /var/log/windi/w-actuary-001.log 2>&1 &
```

## Constitutional Compliance

- **I9:** Human approval required for any seal operation
- **I11:** All scored events traceable to Forensic Ledger
- **I14:** No placeholders — missing data = explicit error

---

*WINDI Publishing House · Kempten, Bavaria · 2026*
*"AI processes. Human decides. WINDI guarantees."*
