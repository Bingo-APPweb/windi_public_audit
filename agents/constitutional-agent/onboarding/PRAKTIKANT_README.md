# 🐉 WINDI Praktikant Onboarding Protocol v1.0.0

> *"Institutions don't resist technology. They resist loss of authority. WINDI gives them the opposite."*

## What This Is

The **Praktikant Onboarding Protocol** teaches Genesis Node W-001 "the house rules" — the complete institutional, constitutional, and operational context of WINDI. Just as a real *Praktikant* (institutional apprentice) observes before acting, helps before deciding, and earns trust before operating autonomously, the WINDI Agent follows the same three-phase journey.

## Three Phases

| Phase | Name | What Happens | I9 Status |
|-------|------|-------------|-----------|
| **1** | **OBSERVATION** — *O Praktikant Observa* | Silent scan of ISPs, SGE, Constitutional Matrix, agents, APIs, infrastructure. Produces an Arrival Report. Zero decisions. | ✅ No decisions made |
| **2** | **ASSISTANCE** — *O Praktikant Ajuda* | Connects to SGE Engine. First Human Escalation simulation. Agent detects risk, STOPS, presents to human, WAITS for decision. | ✅ Agent stops and asks |
| **3** | **TRUST** — *O Praktikant Conquista Confiança* | Creates BABEL Bridge (L1 → Agent pipeline). Every document in a4Desk now flows through governance. Integration test suite included. | ✅ Human always decides |

## What Gets Created

```
/opt/windi/agents/constitutional-agent/onboarding/
├── praktikant_protocol.py        # Main protocol — all 3 phases
├── sge_bridge.py                 # SGE ↔ Agent bridge (Phase 2)
├── escalation_handler.py         # Human Escalation mechanism (Phase 2)
├── babel_bridge.py               # a4Desk BABEL ↔ Agent bridge (Phase 3)
├── babel_routes.py               # API route manifest for BABEL (Phase 3)
├── test_babel_integration.py     # Full pipeline integration test (Phase 3)
├── reports/
│   ├── arrival_report_*.json     # Phase 1 findings
│   └── escalation_simulation_*.json  # Phase 2 simulation
└── ledger/
    ├── onboarding_*.log          # Forensic log
    └── receipt_*.json            # Virtue Receipts
```

## Deploy

```bash
# On Strato (87.106.29.233)
cd /tmp
# Upload praktikant-onboarding/ directory
bash deploy.sh
```

Or manually:

```bash
mkdir -p /opt/windi/agents/constitutional-agent/onboarding/{reports,ledger}
cp praktikant_protocol.py /opt/windi/agents/constitutional-agent/onboarding/
cd /opt/windi/agents/constitutional-agent/onboarding/
python3 praktikant_protocol.py
```

## After Onboarding

1. **Review the Arrival Report** — see what the Praktikant found
2. **Run integration tests** — `python3 test_babel_integration.py`
3. **Connect Nginx proxy** — route 8091 through HTTPS (SECURITY.md §1.1)
4. **Wire BABEL** — add event emitters to a4Desk editor for document lifecycle events

## Constitutional Compliance

- **I9 (Prohibition of Autonomy Escalation)**: Enforced at every layer. `auto_apply: false` everywhere. Agent NEVER decides — it presents findings and WAITS.
- **Zero-Knowledge**: SGE runs at edge. Only hashes, categories, and decisions flow upstream.
- **Forensic Trail**: Every action generates a Virtue Receipt with SHA-256 hash.
- **Three Dragons**: Protocol honors Guardian (Claude), Architect (GPT), and Witness (Gemini) contributions.

## Principle

**"AI processes. Human decides. WINDI guarantees."**

---

*WINDI Publishing House — Kempten (Allgäu), Bavaria, Germany*
*Marco Zero: January 19, 2026*
