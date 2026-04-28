# W-SITES-001 — Project Status
## Containers Soberanos + MAKEUPs

**Status:** DRAFT · Phase A/B Development
**Date:** 28 Abril 2026
**Author:** LIGA IA+H

---

## Summary

W-SITES-001 implements the WINDI Container Architecture — a system where constitutional governance is delivered as Web Components that external sites can consume.

**Dois Layers:**
```
┌─────────────────────────────────────────────┐
│  ATTRACTION LAYER (MAKEUPs)                 │  ← Reason to adopt
│  • AI Writer • AI Image • AI Layout         │
├─────────────────────────────────────────────┤
│  CONSTITUTIONAL LAYER (Core)                │  ← Reason to exist
│  • Seal • Verify • DID-Gate                 │
└─────────────────────────────────────────────┘
```

---

## Documents Created

| Document | Path | Status |
|----------|------|--------|
| **Container Spec v0.1** | `/opt/windi/constitutional/W-SITES-001-CONTAINER-SPEC-v0.1.md` | ✅ Draft |
| **MAKEUP Catalog v0.1** | `/opt/windi/constitutional/W-SITES-001-MAKEUP-CATALOG-v0.1.md` | ✅ Draft |
| **AI Writer Manifest** | `/opt/windi/constitutional/poc/windi-ai-writer/manifest.yaml` | ✅ Draft |
| **AI Writer Component** | `/opt/windi/constitutional/poc/windi-ai-writer/windi-ai-writer.js` | ✅ POC |
| **AI Writer Demo** | `/opt/windi/constitutional/poc/windi-ai-writer/demo.html` | ✅ POC |

---

## Architecture Defined

### Container = Capacidade + Prova + Invariantes

```yaml
# Every container declares:
id: windi.{capability}.v1
requires:
  - human_presence: true   # I1
  - did_session: true      # Identity
invariants: [I1, I9, I11, I14]  # Quadra Sagrada
execution_mode: gated      # Human click required
```

### Containers Catalogued

**Core (Constitutional):**
- `windi.seal.v1` — Seal content to Ledger
- `windi.verify.v1` — Verify existing receipt
- `windi.did-gate.v1` — Authenticate via DID

**Enterprise (Governance):**
- `windi.approval-flow.v1` — I9 workflow
- `windi.audit-log.v1` — Verifiable action log
- `windi.compliance-check.v1` — Rule validation

**MAKEUPs (Attraction):**
- `windi.ai-writer.v1` — Text generation ⭐ **POC Ready**
- `windi.ai-translator.v1` — DE↔EN↔PT
- `windi.ai-image.v1` — Image generation
- `windi.ai-logo.v1` — Logo creation
- `windi.ai-layout.v1` — Page structure

---

## POC: windi-ai-writer

**Status:** Functional POC created

**Files:**
```
/opt/windi/constitutional/poc/windi-ai-writer/
├── manifest.yaml        # Container manifest (YAML schema)
├── windi-ai-writer.js   # Web Component implementation
└── demo.html            # Test page
```

**Features:**
- ✅ Web Component with Shadow DOM
- ✅ i18n (DE/EN/PT)
- ✅ Tone selector (formal/casual/technical/creative)
- ✅ Draft mode (no seal)
- ✅ Seal mode (I9 gate → Ledger)
- ✅ Events: `windi:generating`, `windi:draft-ready`, `windi:sealed`, `windi:error`
- ✅ Invariants enforced: I1, I9, I11, I14

**Integrates with:**
- W-GATEWAY :8130 (`/gateway/call`)
- Forensic Ledger :8101 (`/api/receipts`)

---

## §B-CONTRACT-001 — SELADO ✅

**Receipt:** `WINDI-CONTRACT-B-001-v1.0-20260428162029-1530DBEF`
**Hash:** `sha256:1530dbef51c7f19c90434a3236825698d9a2a658ad4abeef7b0f9f0cd7d118d2`
**Verify:** https://windi-domain.com/verify-public/?id=WINDI-CONTRACT-B-001-v1.0-20260428162029-1530DBEF

### Decisões Tomadas (28 Abril 2026)

| Pilar | Decisão | Princípio |
|-------|---------|-----------|
| **Hospedagem** | FREE=subdomain · MED=custom domain hosted · HIGH=export | "Soberania não é gratuita, mas não é bloqueada" |
| **Brand visibility** | Marca opcional · Prova obrigatória · Meta-Tag Forense no HIGH | "A marca pode desaparecer. A prova nunca." |
| **Content responsibility** | User=Autor · WINDI=Garantidor · Ledger=Testemunha | "A ferramenta amplia. A intenção define." |

---

## First AI Content — SELADO ✅

**Receipt:** `WINDI-AIWRITER-FIRST-20260428163019-94A8C2EB`
**Hash:** `sha256:94a8c2ebace47102a6f55b0f1d41c1780191509244f9ae4bdade664fb61ec0f1`
**Verify:** https://windi-domain.com/verify-public/?id=WINDI-AIWRITER-FIRST-20260428163019-94A8C2EB
**Parent:** `WINDI-CONTRACT-B-001-v1.0-20260428162029-1530DBEF`

**Constitutional Chain provada:** Contract → First Content (com `parent_receipt`)

---

## §C-ACCEPTABILITY-001 — READY FOR SEAL ⏳

**Document:** `/opt/windi/constitutional/S-C-ACCEPTABILITY-001-v1.0.md`
**Hash:** `sha256:66a0d8b09a7aa4a0512e07ab4bd2a3897a74904727c03f13baae5c33ca31c271`
**Status:** Awaiting Human Dragon approval

### 4 Camadas Definidas

| Layer | Nome | Efeito |
|-------|------|--------|
| **L-1** | PROMPT FILTER | Bloqueia INPUT · zero tokens gastos |
| **L0** | PRE-SEAL FILTER | Bloqueia OUTPUT · I14 explicit fail |
| **L1** | POST-SEAL REVIEW | `review_pending` · verify mostra flag |
| **L2** | LEDGER ANNOTATION | Anotação encadeada · original fica |

**Princípio:** "WINDI nunca apaga. WINDI pode anotar."

---

## Next Steps

### Immediate (NOW)
1. [x] Test AI Writer POC with real W-GATEWAY calls ✅
2. [x] Answer pending questions (§B) ✅
3. [ ] **SEAL §C-ACCEPTABILITY-001** ← AGUARDA HUMAN DRAGON
4. [ ] POC: `windi-seal` (core container)

### Short-term (Week 2-3)
4. [ ] Container Registry API (`/api/containers/*`)
5. [ ] POC: `windi-ai-translator`
6. [ ] Integration with Decision Seed

### Medium-term (Month 1-2)
7. [ ] External API integration for image generation (DALL-E/Midjourney)
8. [ ] Builder prototype (drag-drop containers)
9. [ ] Beta with 10 test users

---

## Integration Points

| Service | Port | Usage |
|---------|------|-------|
| W-GATEWAY-001 | :8130 | LLM calls for MAKEUPs |
| Forensic Ledger | :8101 | Receipt storage |
| Verify Public | :8114 | Public verification |
| DID Genesis | :8096 | Identity management |
| Decision Seed | :8155 | VERA-lite interpretation |

---

## Files in /constitutional/

```
/opt/windi/constitutional/
├── DECRETO-A-SPINE-COMERCIAL-v1.0.md     # ✅ SEALED
├── W-SITES-001-CONTAINER-SPEC-v0.1.md    # Draft
├── W-SITES-001-CONTRACT-B-v1.0.md        # ✅ SEALED (1530DBEF)
├── W-SITES-001-MAKEUP-CATALOG-v0.1.md    # Draft
├── W-SITES-001-STATUS.md                 # This file
├── S-C-ACCEPTABILITY-001-v1.0.md         # ⏳ READY FOR SEAL
└── poc/
    └── windi-ai-writer/
        ├── manifest.yaml
        ├── windi-ai-writer.js
        └── demo.html
```

---

*LIGA IA+H — "Containers are capabilities that prove themselves."*
