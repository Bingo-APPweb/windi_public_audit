# W-LAB-001 — Specification v1.0.0

**Port:** 8151
**Status:** DEVELOPMENT
**Invariants:** WL-I to WL-VII + I9, I11, I14
**Sealed:** 2026-04-14

---

## 1. Mission

> **"VERA governs reasoning. W-LAB governs human training before reasoning."**

W-LAB is the operational experimentation laboratory where officers, analysts, lawyers, auditors, or product owners can:

- Test decisions and workflows under pressure
- Practice human oversight in adversarial environments
- Validate operational formulas before the real battlefield
- Measure quality, risk, latency, and resilience
- Learn to operate AI with verifiable discipline

---

## 2. Central Thesis

The real problem in organizations is not just "using AI safely."

The problem is: **the responsible human almost never has an environment where they can fail, test, compare, and learn without real institutional risk.**

Therefore, W-LAB is born as:
**sandbox for practice + stress + pedagogy + proof of operational maturity.**

It does not replace VERA. It **amplifies** VERA.

---

## 3. Ecosystem Role

```
World → W-LAB → VERA → PHO/Enterprise → Real Ledger → Verify
```

| Layer | Function |
|-------|----------|
| W-LAB | Training, simulation, stress, formula, human benchmark |
| VERA | Governed reasoning, OVS profiles, REGO constitution |
| PHO / Enterprise | Human oversight applicable to real case |
| Real Ledger | Immutable proof when action leaves training and enters production |

**Golden Rule:**
- In W-LAB, learning must be serious
- But risk must be contained
- Therefore: **sandbox first**, real ledger optional or off by default

---

## 4. W-LAB Invariants (WL-I to WL-VII)

| ID | Name | Rule |
|----|------|------|
| WL-I | Training cannot pretend production | Every interface must clearly declare sandbox mode |
| WL-II | Error is allowed, opacity is not | User can fail; system cannot hide why |
| WL-III | No real proof by accident | Nothing in W-LAB seals to real ledger without explicit activation |
| WL-IV | Stress must be graduated | Difficulty increases in layers, not arbitrary chaos |
| WL-V | Adaptive pedagogy | System teaches according to profile and user maturity |
| WL-VI | All improvement comes from replay | Not enough to say "failed"; must show at what point failure emerged |
| WL-VII | Formulas are living artifacts | Tested recipes need versioning, score, and validity context |

---

## 5. MVP Modules

### A. Scenario Engine
Loads and executes scenarios.

**Initial scenario types:**
- Contradictory urgent request
- Conflict between departments
- Short regulatory deadline
- Incomplete document
- Decision with ambiguous legal basis
- Technical incident with executive pressure

### B. Sandbox Router
Layer that calls VERA in non-productive mode.

**Functions:**
- Use inherited DID gate
- Route to vera_agent
- Disable real sealing by default
- Register training logs in own store
- Always declare session is in sandbox mode

### C. Stress Simulator
Introduces controlled operational friction.

**Examples:**
- Interruptions mid-task
- New contradictory instruction
- Reduced deadline
- Incomplete context
- Priority change
- Simulated dependency failure

### D. Formula Library
Library of verified operational recipes.

**Each formula contains:**
- Context of use
- Minimum input
- Steps
- Expected outputs
- Risk signals
- When to escalate

### E. Metrics Collector
Captures pedagogical and operational telemetry.

**Minimum metrics:**
- Time per task
- Number of interruptions
- Number of reformulations
- Formula usage
- LLM divergence
- Correct escalation rate
- Hallucination prevented rate
- Documentary completeness
- Justification clarity

### F. Session Review
Replay and learning layer.

**Allows:**
- Reconstruct the session
- See prompts, responses, and stress events
- Compare user decision with suggested decision
- Mark improvement points

---

## 6. Endpoints MVP

### Sessions
```
POST /api/lab/sessions/start
POST /api/lab/sessions/{id}/input
POST /api/lab/sessions/{id}/interrupt
POST /api/lab/sessions/{id}/finish
GET  /api/lab/sessions/{id}
```

### Scenarios
```
GET  /api/lab/scenarios
GET  /api/lab/scenarios/{id}
POST /api/lab/scenarios/import
```

### Formulas
```
GET  /api/lab/formulas
GET  /api/lab/formulas/{id}
POST /api/lab/formulas
POST /api/lab/formulas/{id}/validate
```

### Metrics / Review
```
GET /api/lab/sessions/{id}/metrics
GET /api/lab/sessions/{id}/review
GET /api/lab/officers/{officer_id}/maturity
```

---

## 7. Integration with VERA

**What to reuse:**
- DID gate
- OVS profiles
- Instructor pedagogy
- Routing engine
- Declared degraded mode
- Existing legal anchors

**What NOT to mix initially:**
- Real regulatory sealing
- Production verify public
- Final receipts with real legal value

**Recommended mode:**
```python
SANDBOX_MODE = True  # by default
```

With this, VERA continues to operate but output goes through LAB's own routes and storage.

---

## 8. Maturity Score

W-LAB must produce something the market understands.

**Dimensions:**
| Dimension | Question |
|-----------|----------|
| Discipline | Follows process under pressure? |
| Clarity | Justifies without confusion? |
| Escalation | Knows when to stop and elevate? |
| Legal basis | Anchors correctly? |
| Integrity | Avoids inventing and declares uncertainty? |
| Efficiency | Resolves without waste? |

**Bands:**
| Score | Level |
|-------|-------|
| 0-39 | Reactive |
| 40-59 | Assisted |
| 60-79 | Operational |
| 80-89 | Reliable |
| 90-100 | Reference |

This creates an important asset:
**W-LAB measures not just output. It measures human operational maturity before AI.**

---

## 9. First 6 Mandatory Scenarios

| # | Scenario | Objective |
|---|----------|-----------|
| 1 | Urgency without sufficient proof | Block with elegance and trail |
| 2 | 1LOD vs 2LOD conflict | Structure escalation |
| 3 | Ambiguous multi-jurisdiction legal request | Declare limit and request precise precision |
| 4 | Technical incident with reputational pressure | Separate hypothesis from fact |
| 5 | Business document under extreme deadline | Maintain minimum completeness |
| 6 | LLM Tier A failure | Respond with transparency and containment |

---

## 10. Build Order

### Phase 1 — Found the laboratory
- Create W-LAB-001 service
- Integrate inherited DID gate
- Create persistent session store
- Create JSON + SQLite scenario store
- Implement POST /start, POST /input, GET /review

### Phase 2 — Make it alive
- Integrate VERA sandbox router
- Plug instructor by profile
- Create 6 mandatory scenarios
- Introduce simple interruptions

### Phase 3 — Make it measurable
- Metrics collector
- Maturity score
- Replay per session
- Performance dashboard per officer

### Phase 4 — Make it unique
- Formula library
- Formula validation
- Benchmark between sessions
- Progression trails by profile

---

## 11. Success Definition v1

W-LAB v1 is ready when a user can:

1. Enter with valid DID
2. Choose a scenario
3. Execute a session with at least one interruption
4. Receive VERA response in sandbox
5. Obtain score and final review
6. Repeat and compare evolution

At that point, there already exists:
- Demonstrable product
- Strong narrative
- Real pedagogical asset
- Direct bridge to enterprise

---

## 12. Positioning Phrase

> **"W-LAB is the environment where organizations train verifiable human oversight before reality charges for the error."**

Or even shorter:

> **"Train human oversight before production makes it expensive."**

---

*LIGA IA+H — Kempten, Bavaria · 2026*
*"AI processes. Human decides. WINDI guarantees."*
