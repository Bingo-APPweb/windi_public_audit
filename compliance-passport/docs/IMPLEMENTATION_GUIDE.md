# WINDI Compliance Passport — Implementation Guide
## Deploy on Strato (87.106.29.233)

### Architecture Overview

```
                    ┌─────────────────────────────────────┐
                    │     COMPLIANCE PASSPORT SYSTEM       │
                    │                                      │
  Auditor ──GET───▶ │  /verify/{agent_id}/{root_hash}     │
                    │         │                            │
  Forja ───POST───▶ │  /passport/generate                 │
                    │         │                            │
                    │    ┌────▼────┐                       │
                    │    │Generator│                       │
                    │    └────┬────┘                       │
                    │         │                            │
                    │    ┌────┴──────────────────────┐     │
                    │    │                           │     │
                    │    ▼           ▼           ▼   │     │
                    │ Ledger:8101 Sentinel    Agents │     │
                    │ (receipts)  (cycles)   (registry)   │
                    │    │           │           │         │
                    │    └────┬──────┴───────────┘         │
                    │         ▼                            │
                    │    PassportSeal (Ed25519)            │
                    │         │                            │
                    │         ▼                            │
                    │    Ledger Receipt (seal recorded)    │
                    │         │                            │
                    │         ▼                            │
                    │    JSON Output → /passports/         │
                    └─────────────────────────────────────┘
```

### Integration Steps

#### Phase 1: Schema + Generator (Current)
- [x] JSON Schema v1.0 defined
- [x] Python generator + verifier implemented
- [x] CLI demo mode working
- [ ] Deploy to Strato as service or integrate with Renderer :8108

#### Phase 2: Connect to Live Data
- [ ] Wire `_fetch_agent_identity()` to agent registry DB
- [ ] Wire `_aggregate_sentinel()` to Sentinel LAW DB
- [ ] Wire `_build_ledger_proof()` to Forensic Ledger :8101
- [ ] Deploy Ed25519 issuing key for passport signing

#### Phase 3: HTTP Endpoints
- [ ] Add `/passport/generate` to existing HTTP handler
- [ ] Add `/passport/verify` for auditor self-service
- [ ] Add `/verify/{agent_id}/{hash}` public endpoint
- [ ] Register passport issuance in Ledger

#### Phase 4: Torre Integration
- [ ] Torre de Observação displays aggregate passport stats
- [ ] Forja wizard triggers passport generation on Agent seal
- [ ] Compliance Dashboard shows ecosystem-wide compliance rate

### Port Strategy
Option A: Add to Renderer :8108 (recommended — already handles doc generation)
Option B: New service :8109 (if passport logic grows complex)

### Gov Score Formula v1.0
```
Gov Score = (
    sentinel_compliance × 0.40    # (1 - violation_rate) × 100
  + chain_integrity    × 0.30    # VERIFIED=100, PENDING=50, BROKEN=0
  + volume_score       × 0.20    # log10(receipts)/4 × 100
  + i9_verification    × 0.10    # binary: 100 or 0
)
```

### EU AI Act Article Mapping
| Article | Title                    | WINDI Mechanism                      | Coverage      |
|---------|--------------------------|--------------------------------------|---------------|
| Art. 9  | Risk Management          | SGE 6-Layer Analysis (R0-R5)         | FULL          |
| Art. 12 | Record-Keeping           | Forensic Ledger SHA-256 Receipts     | FULL          |
| Art. 13 | Transparency             | Torre de Observação (live dashboard)  | FULL          |
| Art. 14 | Human Oversight          | I1 + I9 (structural invariants)      | FULL          |
| Art. 15 | Accuracy & Robustness    | Ed25519 + Sentinel LAW v2.0          | ARCHITECTURAL |
| Art. 17 | Quality Management       | WAQP Certification + Tier System     | FULL          |
| Art. 26 | Deployer Obligations     | Constitutional Invariants I1-I9      | PARTIAL       |
| Art. 61 | Post-Market Monitoring   | Sentinel continuous 5-tier escalation | FULL          |

### Verification Flow for Auditors
```bash
# 1. Receive passport JSON from Agent operator
# 2. Run verification (zero WINDI dependencies needed)
python compliance_passport.py verify passport.json

# Output:
# ══════════════════════════════════════════════════════════
#   WINDI COMPLIANCE PASSPORT — VERIFICATION REPORT
#   Passport: CP-GUAR-20260221-a3f7c1b2
# ══════════════════════════════════════════════════════════
#   OVERALL: ✅ VERIFIED
#   ✅ schema_completeness........... PASS
#   ✅ hash_integrity................ PASS
#   ✅ validity_window............... PASS
#   ✅ i9_invariant.................. PASS
#   ✅ zero_knowledge................ PASS
#   ✅ chain_integrity............... PASS
# ══════════════════════════════════════════════════════════

# 3. Independently verify chain hash against public endpoint
curl https://windi-domain.com/api/v1/verify/AGT-GUAR-xxx/abc123...
```

### Files
- `compliance_passport_schema.json` — JSON Schema (for validators/auditors)
- `compliance_passport.py` — Generator + Verifier (for Strato deployment)
- This file — Implementation roadmap

---
"AI processes. Human decides. WINDI guarantees."
© 2026 WINDI Publishing House · Three Dragons Protocol
