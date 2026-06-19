# DOCUMENT-SANITATION-MATRIX-001

**Status:** MEASURED
**Date:** 2026-06-13
**Mission:** Document continuity sanitation
**Purpose:** Classify documentation status/header issues without mutating source files

## Summary

- `HEADER_PATCH`: 8
- `NEEDS_TRIAGE`: 48
- `OK`: 9
- `STATUS_NORMALIZE`: 18

## Matrix

| file | status | missing_headers | action | recommendation |
|---|---|---|---|---|
| `ACTION-0-WITNESS-ADMISSIBILITY-001.md` | `CONSTITUTIONAL BLOCKING QUESTION` | Purpose | `STATUS_NORMALIZE` | Map legacy/free-form status to DOCUMENT-STATUS-STANDARD-001. |
| `ALIAS-ADMISSION-DOCTRINE-001.md` | `SEALED` | - | `OK` | No action required. |
| `ALIAS-PROMOTE-001-v0.2.md` | `AWAITING I9` | - | `OK` | No action required. |
| `ALIAS-PROMOTE-001-v0.3.md` | `AWAITING I9` | - | `OK` | No action required. |
| `ALIAS-RESOLUTION-001.md` | `SEALED` | Mission | `HEADER_PATCH` | Add missing required metadata without changing body. |
| `ALIAS-RUN-001.md` | `MEASURED` | Date, Mission, Purpose | `HEADER_PATCH` | Add missing required metadata without changing body. |
| `ATR-ADMISSIBILIDADE-TRAVADA-PELO-ROTEIRO.md` | `MISSING` | Status, Date, Mission, Purpose | `NEEDS_TRIAGE` | Missing status and required headers; classify before use. |
| `AUTHORITY-GATE-001.md` | `CANDIDATE` | - | `OK` | No action required. |
| `CONTINUITY-OPS-001.md` | `CANDIDATE` | - | `OK` | No action required. |
| `CONTRIBUTION-GRAMMAR-001.md` | `CANDIDATE` | Purpose | `HEADER_PATCH` | Add missing required metadata without changing body. |
| `DEPLOY_GUIDE.md` | `READY FOR DEPLOY` | Date, Mission, Purpose | `STATUS_NORMALIZE` | Map legacy/free-form status to DOCUMENT-STATUS-STANDARD-001. |
| `DIAG-MED-TIER-20260606.md` | `SEALED` | Date, Mission, Purpose | `HEADER_PATCH` | Add missing required metadata without changing body. |
| `DID-AUDIT-2026-04-15.md` | `MISSING` | Status, Date, Mission, Purpose | `NEEDS_TRIAGE` | Missing status and required headers; classify before use. |
| `DID-RELATORIO-COMPLETO-20260402.md` | `MISSING` | Status, Date, Mission, Purpose | `NEEDS_TRIAGE` | Missing status and required headers; classify before use. |
| `DID-USER-JOURNEY.md` | `MISSING` | Status, Date, Mission, Purpose | `NEEDS_TRIAGE` | Missing status and required headers; classify before use. |
| `DOCUMENT-STATUS-STANDARD-001.md` | `CANDIDATE` | - | `OK` | No action required. |
| `DRIFT-INVENTORY-20260420.md` | `MISSING` | Status, Date, Mission, Purpose | `NEEDS_TRIAGE` | Missing status and required headers; classify before use. |
| `ERRATA-MED-503-20260606.md` | `SEALED` | Date, Mission, Purpose | `HEADER_PATCH` | Add missing required metadata without changing body. |
| `EVIDENCE_PACKAGE_SCHEMA_v1.1.md` | `ACTIVE` | Mission, Purpose | `STATUS_NORMALIZE` | Map legacy/free-form status to DOCUMENT-STATUS-STANDARD-001. |
| `FORENSIC_TENANT_ISOLATION_LEGACY_POLICY.md` | `ACTIVE` | Date, Mission, Purpose | `STATUS_NORMALIZE` | Map legacy/free-form status to DOCUMENT-STATUS-STANDARD-001. |
| `FOUNDATION-AS-WINDI-MEANS-IT.md` | `MISSING` | Status, Date, Mission, Purpose | `NEEDS_TRIAGE` | Missing status and required headers; classify before use. |
| `FUNDACAO_B2_20260215.md` | `MISSING` | Status, Date, Mission, Purpose | `NEEDS_TRIAGE` | Missing status and required headers; classify before use. |
| `G-SURF-3-TEST-PROTOCOL.md` | `MISSING` | Status, Date, Mission, Purpose | `NEEDS_TRIAGE` | Missing status and required headers; classify before use. |
| `GUARDIAN-BRIEF-S261.md` | `MISSING` | Status, Date, Mission, Purpose | `NEEDS_TRIAGE` | Missing status and required headers; classify before use. |
| `INVARIANTS.md` | `Active (until C5)` | Date, Mission, Purpose | `STATUS_NORMALIZE` | Map legacy/free-form status to DOCUMENT-STATUS-STANDARD-001. |
| `KNOWN_BUGS_AND_FIXES.md` | `MISSING` | Status, Date, Mission, Purpose | `NEEDS_TRIAGE` | Missing status and required headers; classify before use. |
| `MATRIZ-FATO-CONTRIBUICAO-001.md` | `CANDIDATE` | Mission | `HEADER_PATCH` | Add missing required metadata without changing body. |
| `MOBILE-AUDIT-REPORT-2026-03-13.md` | `MISSING` | Status, Date, Mission, Purpose | `NEEDS_TRIAGE` | Missing status and required headers; classify before use. |
| `NOTEBOOK-001-HYBRID-COGNITIVE-SYSTEMS.md` | `FOUNDATIONAL DOCUMENT` | Mission, Purpose | `STATUS_NORMALIZE` | Map legacy/free-form status to DOCUMENT-STATUS-STANDARD-001. |
| `ONBOARDING-MAP-001.md` | `CANDIDATE` | - | `OK` | No action required. |
| `PARTICIPATION-LAYER-INDEX-001.md` | `CANDIDATE` | - | `OK` | No action required. |
| `PROOF-SELF-CORRECTION-WITHOUT-REWRITE.md` | `MISSING` | Status, Date, Mission, Purpose | `NEEDS_TRIAGE` | Missing status and required headers; classify before use. |
| `PUBLIC-WINDI-HIOS-ARCHITECTURE-20260518.md` | `MISSING` | Status, Date, Mission, Purpose | `NEEDS_TRIAGE` | Missing status and required headers; classify before use. |
| `RESEARCH-RECEIPTS-001.md` | `CANDIDATE` | - | `OK` | No action required. |
| `S129-NOMAD-SEAL-ANATOMY.md` | `MISSING` | Status, Date, Mission, Purpose | `NEEDS_TRIAGE` | Missing status and required headers; classify before use. |
| `S247-NOMENCLATURA-CANONICA-WINDI.md` | `SEALED · Receipt `WINDI-S247-NOMENCLATURA-20260507201003-A3B99EA6` · 2026-05-07` | Date, Mission, Purpose | `STATUS_NORMALIZE` | Map legacy/free-form status to DOCUMENT-STATUS-STANDARD-001. |
| `S248-LEI-V-FOUNDATION-DIRECTION.md` | `SEALED` | Date, Mission, Purpose | `HEADER_PATCH` | Add missing required metadata without changing body. |
| `S250-LEI-VII-ORGANIC-GROWTH.md` | `STRUCTURAL (REMEDIABLE)` | Date, Mission, Purpose | `STATUS_NORMALIZE` | Map legacy/free-form status to DOCUMENT-STATUS-STANDARD-001. |
| `S266-KERNEL-HIGH-QUESTIONS-RESOLUTION.md` | `MISSING` | Status, Date, Mission, Purpose | `NEEDS_TRIAGE` | Missing status and required headers; classify before use. |
| `S269-PINGPONG-GENESIS-FIRST-RUNTIME.md` | `MISSING` | Status, Date, Mission, Purpose | `NEEDS_TRIAGE` | Missing status and required headers; classify before use. |
| `S297-LEI-DA-PROVENIENCIA-INSEPARAVEL.md` | `SEALED · **Invariant:** I19 · **Date:** 2026-06-01` | Date, Mission, Purpose | `STATUS_NORMALIZE` | Map legacy/free-form status to DOCUMENT-STATUS-STANDARD-001. |
| `SESSION-2026-04-16-SERVICE-CONTROL.md` | `MISSING` | Status, Date, Mission, Purpose | `NEEDS_TRIAGE` | Missing status and required headers; classify before use. |
| `SESSION-SEAL-20260517-PINGPONG-GENESIS.md` | `MISSING` | Status, Date, Mission, Purpose | `NEEDS_TRIAGE` | Missing status and required headers; classify before use. |
| `SKILL-ghost-exorcism.md` | `MISSING` | Status, Date, Mission, Purpose | `NEEDS_TRIAGE` | Missing status and required headers; classify before use. |
| `SKILL-windi-agent-palette.md` | `MISSING` | Status, Date, Mission, Purpose | `NEEDS_TRIAGE` | Missing status and required headers; classify before use. |
| `SKILL_PALETTE_FREEMIUM.md` | `MISSING` | Status, Date, Mission, Purpose | `NEEDS_TRIAGE` | Missing status and required headers; classify before use. |
| `SKILL_agent_palette_v2.md` | `MISSING` | Status, Date, Mission, Purpose | `NEEDS_TRIAGE` | Missing status and required headers; classify before use. |
| `SYSTEM-ABSORPTION-AUDIT-20260420.md` | `MISSING` | Status, Mission | `NEEDS_TRIAGE` | Missing status and required headers; classify before use. |
| `TASK_DIRECTOR_v1.0.md` | `MISSING` | Status, Date, Mission, Purpose | `NEEDS_TRIAGE` | Missing status and required headers; classify before use. |
| `TEST_PROMPTS.md` | `MISSING` | Status, Date, Mission, Purpose | `NEEDS_TRIAGE` | Missing status and required headers; classify before use. |
| `TIER-RESOLUTION-CANON.md` | `MISSING` | Status, Date, Mission, Purpose | `NEEDS_TRIAGE` | Missing status and required headers; classify before use. |
| `TUTORIAL-CANVAS.md` | `MISSING` | Status, Mission, Purpose | `NEEDS_TRIAGE` | Missing status and required headers; classify before use. |
| `W-COGSPACE-001-IMPLEMENTATION-ROADMAP.md` | `MISSING` | Status, Date, Mission, Purpose | `NEEDS_TRIAGE` | Missing status and required headers; classify before use. |
| `W-COGSPACE-001-SOLO-SPEC.md` | `MISSING` | Status, Date, Mission, Purpose | `NEEDS_TRIAGE` | Missing status and required headers; classify before use. |
| `W-DRAGON-001-ROADMAP.md` | `APPROVED by Council · I9 Gate Passed` | Mission, Purpose | `STATUS_NORMALIZE` | Map legacy/free-form status to DOCUMENT-STATUS-STANDARD-001. |
| `WINDI-EVIDENCE-BLUEPRINT-V1.md` | `BLUEPRINT | AWAITING SEAL` | Mission, Purpose | `STATUS_NORMALIZE` | Map legacy/free-form status to DOCUMENT-STATUS-STANDARD-001. |
| `WINDI-FIELD-BLUEPRINT-V1.md` | `MISSING` | Status, Date, Mission, Purpose | `NEEDS_TRIAGE` | Missing status and required headers; classify before use. |
| `WINDI-LEXICON-STUB.md` | `MISSING` | Status, Date, Mission, Purpose | `NEEDS_TRIAGE` | Missing status and required headers; classify before use. |
| `WINDI-MANIFESTO.md` | `MISSING` | Status, Date, Mission, Purpose | `NEEDS_TRIAGE` | Missing status and required headers; classify before use. |
| `WINDI-POLICY-DATA-CANONICAL-V1.0.md` | `MISSING` | Status, Date, Mission, Purpose | `NEEDS_TRIAGE` | Missing status and required headers; classify before use. |
| `WINDI-PRODUCT-BLUEPRINT-v1.0.md` | `MISSING` | Status, Date, Mission, Purpose | `NEEDS_TRIAGE` | Missing status and required headers; classify before use. |
| `WINDI-PRODUCT-SITES-001-DRAFT.md` | `MISSING` | Status, Date, Mission, Purpose | `NEEDS_TRIAGE` | Missing status and required headers; classify before use. |
| `WINDI-SEAL-ARCHITECTURE-MANUAL-v1.md` | `SEALED · Receipt `WINDI-ARC-VERIFY-SURFACE-20260611`` | Mission, Purpose | `STATUS_NORMALIZE` | Map legacy/free-form status to DOCUMENT-STATUS-STANDARD-001. |
| `WINDI-SEAL-V2-CODE-AUDIT.md` | `MISSING` | Status, Date, Mission, Purpose | `NEEDS_TRIAGE` | Missing status and required headers; classify before use. |
| `WINDI-SEAL-V2-CURRENT-STATE.md` | `🟢 GAPS CRÍTICOS CORRIGIDOS` | Date, Mission, Purpose | `STATUS_NORMALIZE` | Map legacy/free-form status to DOCUMENT-STATUS-STANDARD-001. |
| `WINDI-SEAL-VERIFY-GAP.md` | `✅ CORRIGIDO em V2.8 (`FD9C54FB`)` | Date, Mission, Purpose | `STATUS_NORMALIZE` | Map legacy/free-form status to DOCUMENT-STATUS-STANDARD-001. |
| `WINDI-SYSTEMD-TEMPLATE-001.md` | `SEALED` | Date, Mission, Purpose | `HEADER_PATCH` | Add missing required metadata without changing body. |
| `WINDI_Architecture_Complete_17Feb2026.md` | `MISSING` | Status, Date, Mission, Purpose | `NEEDS_TRIAGE` | Missing status and required headers; classify before use. |
| `WINDI_Engine_Communique_Architecture_v1.0.md` | `DRAFT → Aprovação Humana Pendente` | Date, Mission, Purpose | `STATUS_NORMALIZE` | Map legacy/free-form status to DOCUMENT-STATUS-STANDARD-001. |
| `WINDI_GEMEO_PLAYBOOK.md` | `MISSING` | Status, Date, Mission, Purpose | `NEEDS_TRIAGE` | Missing status and required headers; classify before use. |
| `WINDI_PLAYBOOK.md` | `MISSING` | Status, Date, Mission, Purpose | `NEEDS_TRIAGE` | Missing status and required headers; classify before use. |
| `WINDI_PLAYBOOK_20260224.md` | `MISSING` | Status, Date, Mission, Purpose | `NEEDS_TRIAGE` | Missing status and required headers; classify before use. |
| `WINDI_PLAYBOOK_20260224_COGOBS.md` | `MISSING` | Status, Date, Mission, Purpose | `NEEDS_TRIAGE` | Missing status and required headers; classify before use. |
| `WINDI_PLAYBOOK_20260224_RESPIRADOURO.md` | `MISSING` | Status, Date, Mission, Purpose | `NEEDS_TRIAGE` | Missing status and required headers; classify before use. |
| `WINDI_SESSION_PROTOCOL.md` | `MISSING` | Status, Date, Mission, Purpose | `NEEDS_TRIAGE` | Missing status and required headers; classify before use. |
| `WINDI_Session_17Feb2026_Complete.md` | `MISSING` | Status, Date, Mission, Purpose | `NEEDS_TRIAGE` | Missing status and required headers; classify before use. |
| `WINDI_WISDOM_SEAL_20260221.md` | `Memory UPDATED ✅ | Strato PENDING (requires SSH)` | Date, Mission, Purpose | `STATUS_NORMALIZE` | Map legacy/free-form status to DOCUMENT-STATUS-STANDARD-001. |
| `WPIL-REPORT-20260416.md` | `✅ LIVE em Produção` | Date, Mission, Purpose | `STATUS_NORMALIZE` | Map legacy/free-form status to DOCUMENT-STATUS-STANDARD-001. |
| `agentes-windi.md` | `MISSING` | Status, Date, Mission, Purpose | `NEEDS_TRIAGE` | Missing status and required headers; classify before use. |
| `registry_v2.10.0.md` | `MISSING` | Status, Date, Mission, Purpose | `NEEDS_TRIAGE` | Missing status and required headers; classify before use. |
| `registry_v2.7.0.md` | `MISSING` | Status, Date, Mission, Purpose | `NEEDS_TRIAGE` | Missing status and required headers; classify before use. |
| `registry_v2.8.0.md` | `MISSING` | Status, Date, Mission, Purpose | `NEEDS_TRIAGE` | Missing status and required headers; classify before use. |
| `windi_isp_builder_report_v1.0.md` | `FORJADO ✅` | Date, Mission, Purpose | `STATUS_NORMALIZE` | Map legacy/free-form status to DOCUMENT-STATUS-STANDARD-001. |

## Line of Guard

> Saneamento documental classifica antes de corrigir.
