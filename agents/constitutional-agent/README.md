# 🐉 WINDI Constitutional Execution Agent v1.0.0

**Codename:** Praktikant  
**Phase:** 2 — Clone Commissioning  
**Port:** 8091  

> *"The WINDI Agent is a permanent institutional Praktikant: it prepares, verifies, and organizes — but never decides and never signs."*

## Principle

```
AI processes. Human decides. WINDI guarantees.
```

## Architecture

```
windi-agent/
├── agent.py                          # Main Agent + Flask API (port 8091)
├── config.py                         # Configuration, constants, paths
├── core/
│   ├── invariants.py                 # 9 Invariants (I1-I9) enforcement
│   ├── constitutional_gate.py        # Pre-operation validation + Decision Trace
│   └── manifest.py                   # Agent Initialization Manifest
├── monitors/
│   └── canonical_compliance.py       # Genesis Node alignment checker
├── orchestration/
│   └── proof_orchestrator.py         # Virtue Receipt + Human Escalation
└── tests/
    └── test_invariants.py            # 23 tests (I9 focus)
```

## Components

| Component | Role | File |
|---|---|---|
| **Constitutional Gate** | Pre-validates every operation against 9 Invariants | `core/constitutional_gate.py` |
| **Invariant Enforcer** | I1-I9 enforcement, I9 is IRREMEDIABLE | `core/invariants.py` |
| **Agent Manifest** | Professional, auditable activation record | `core/manifest.py` |
| **Canonical Compliance Monitor** | Verifies alignment with Genesis Node | `monitors/canonical_compliance.py` |
| **Proof Orchestrator** | Prepares Virtue Receipts for Hub attestation | `orchestration/proof_orchestrator.py` |

## The Agent CAN

- ✔ Execute semantic analysis (SGE)
- ✔ Prepare proof structures
- ✔ Enforce spec compliance
- ✔ Format data for Hub anchorage
- ✔ Trigger exception workflows to humans
- ✔ Monitor canonical compliance

## The Agent CANNOT

- ✗ Override a human decision
- ✗ Sign on behalf of an operator
- ✗ Escalate its own authority (I9)
- ✗ Act as a parallel decision authority
- ✗ Resolve exceptions autonomously
- ✗ Make policy or governance judgments

## Quick Start

```bash
# Run tests (23 tests, all must pass)
cd /opt/windi/agents/constitutional-agent
python3 tests/test_invariants.py

# Activate Agent (headless)
python3 agent.py --node-id "W-00000000000000000000001" --operator "Human Dragon" --no-api

# Activate Agent with API (port 8091)
nohup python3 agent.py --node-id "W-00000000000000000000001" --operator "Human Dragon" > /tmp/agent.log 2>&1 &
```

## API Endpoints (Port 8091)

| Endpoint | Method | Description |
|---|---|---|
| `/agent/health` | GET | Health check |
| `/agent/status` | GET | Full agent status |
| `/agent/manifest` | GET | Current activation manifest |
| `/agent/analyze` | POST | Analyze document (SGE) |
| `/agent/compliance` | GET | Run canonical compliance scan |
| `/agent/decision` | POST | Record human decision on receipt |
| `/agent/escalations` | GET | List pending human escalations |

## Deployment to Strato

```bash
# 1. Backup existing agents
BK="/opt/windi/backups/agents_$(date +%Y%m%d_%H%M%S)"
mkdir -p $BK && cp -r /opt/windi/agents/ $BK/

# 2. Deploy agent
mkdir -p /opt/windi/agents/constitutional-agent
scp -r windi-agent/* windi@87.106.29.233:/opt/windi/agents/constitutional-agent/

# 3. Install dependencies
ssh windi@87.106.29.233 "pip install flask --break-system-packages"

# 4. Run tests
ssh windi@87.106.29.233 "cd /opt/windi/agents/constitutional-agent && python3 tests/test_invariants.py"

# 5. Activate
ssh windi@87.106.29.233 "cd /opt/windi/agents/constitutional-agent && nohup python3 agent.py --node-id 'W-00000000000000000000001' --operator 'Human Dragon' > /tmp/agent.log 2>&1 &"

# 6. Verify
curl http://87.106.29.233:8091/agent/health
```

## Integration Points

- **SGE Engine:** `/opt/windi/engine/semantic_governance.py` (TODO: direct integration)
- **Governance API:** Port 8080 (`/opt/windi/engine/windi_governance_api.py`)
- **Clone Matrix:** `/opt/windi/clone/matrix/P0-P7` (Phase 1 SEALED)
- **ISP Registry:** `/opt/windi/isp/` (17 profiles)
- **a4Desk BABEL:** Port 8085 (document editor)

## Version History

| Version | Date | Changes |
|---|---|---|
| 1.0.0 | 2026-02-10 | Initial release. Constitutional Gate, Invariant Enforcer (I1-I9), Agent Manifest, Canonical Compliance Monitor, Proof Orchestrator, Human Escalation, Decision Trace Commitment. 23/23 tests passing. |

---

*WINDI Constitutional Execution Agent v1.0.0*  
*Tripartite Governance Framework — Three Dragons Protocol*  
*"Autonomous processing, sovereign decision."*  
*© 2026 WINDI Publishing House. Kempten (Allgäu), Bavaria, Germany.*
