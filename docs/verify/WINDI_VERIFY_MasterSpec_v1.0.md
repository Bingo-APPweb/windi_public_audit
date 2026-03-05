# WINDI VERIFY — Master Specification v1.0

**Document ID:** WINDI-VERIFY-MASTER-SPEC-20260305
**Version:** 1.0.0
**Status:** ACTIVE — SEALED
**Classification:** INTERNAL / ARCHITECTURAL
**Author:** Three Dragons Protocol (Human Dragon + Architect)
**Date:** 05 March 2026
**Invariant:** I11 — Public Verifiability (IRREMEDIABLE)
**Genesis Record:** WINDI-VERIFY-GENESIS-20260305

---

## Constitutional Basis

**I11 — Public Verifiability (IRREMEDIABLE)**

> "Every sealed document must be publicly verifiable. Forever."

Invariant I11 cannot be revoked, suspended, or modified by any operator, administrator, or system update. Its activation on 05 March 2026 permanently commits the WINDI infrastructure to maintaining public verifiability for all sealed documents.

---

## Infrastructure

| Component | Value |
|-----------|-------|
| Service Port | :8114 |
| Public URL | windi-domain.com/verify-public/ |
| Direct Verify URL | windi-domain.com/verify/{hash} |
| Nginx Path | /verify-public/ → proxy_pass :8114 |
| Service File | /opt/windi/verify-public/ |
| Process Manager | systemd |
| Database Source | Forensic Ledger :8101 (SQLite + SHA-256) |
| API: verify | GET /api/verify/{id} |
| API: receipts | POST /api/receipts |
| Total Receipts | 39,711+ (05.03.26) |

---

## Verification Pipeline

```
INPUT: QR scan | File upload | Document ID | Direct URL
       ↓
HASH EXTRACTION: SHA-256 fingerprint from document
       ↓
LEDGER QUERY: GET /api/verify/{hash} → :8101
       ↓
RESULT A: hash found     → VERIFIED ✔
RESULT B: hash not found → NOT FOUND ✗
RESULT C: structure only → ANALYSIS ⚠
```

---

## Verification Modes

### Mode 1 — WINDI Verification (Primary) — ACTIVE
- Input: WINDI document (PDF with embedded hash and QR code)
- Process: SHA-256 hash extracted → queried against Forensic Ledger
- Output: VERIFIED ✔ with full metadata, or NOT FOUND ✗
- Authority: Maximum — backed by constitutional I11 guarantee

### Mode 2 — Generic Analysis (Secondary) — PLANNED
- Input: Any document file
- Process: Detect cryptographic elements (hash, QR, PGP, OpenTimestamp)
- Output: Analysis report — no WINDI verification claim
- Status: Medium-term roadmap

### Mode 3 — Constitutional Scanner — FUTURE
- Vision: WINDI Verify as an authenticity antivirus
- Any document enters, system answers: "Does this document have cryptographic proof of existence?"

---

## FREMDE Data Policy

| Phase | Policy | Rationale |
|-------|--------|-----------|
| NOW (v1.x) | Zero FREMDE. WINDI documents only. | Authority-building phase. No ambiguity. |
| MEDIUM (v2.x) | FREMDE read, not certified. Structural analysis only. | WINDI still = superior standard. |
| FUTURE (v3.x) | Constitutional scanner. Any document. WINDI judges. | WINDI = authenticity infrastructure. |

**Principle:** WINDI Verify first builds authority, then expands jurisdiction. FREMDE analysis never dilutes WINDI certification.

---

## Liveness Detection (Planned)

### Use Cases
- DID creation — PF (natural person) identity establishment
- HIGH-tier document signing — contracts, procurations, notarial acts
- War Room access — re-authentication for sensitive sessions

### Technical Approach
| Type | Method |
|------|--------|
| Passive liveness | Micro-movement analysis — blink, breath, natural motion |
| Active liveness | User prompted — turn, blink, smile, finger count |
| Storage policy | NO face image or video stored — constitutional requirement |
| Ledger record | liveness_confirmed=true + timestamp + event_hash ONLY |
| GDPR basis | Explicit consent required — biometric data category |
| I9 compliance | Camera does not escalate AI autonomy — human confirms presence |

### Roadmap
- v1.x (now): No liveness. Ed25519 + UUIDv7 sufficient for FREE/MED tiers.
- v2.x (medium): Liveness on HIGH-tier signature. eIDAS substantial level.
- v3.x (future): Liveness integrated with eIDAS qualified — legal presence proof.

---

## Roadmap

| Version | Status | Scope |
|---------|--------|-------|
| v1.0 (NOW) | ✅ LIVE | Verify Public :8114. QR + Upload + ID. WINDI-only. I11 sealed. Genesis record. |
| v1.1 | ⏳ NEXT | QR in documents → direct verify URL. Verify button in all email correspondence. |
| v1.2 | PLANNED | Verify Public UI refinement. Institutional design. Public documentation. |
| v2.0 | MEDIUM | FREMDE structural analysis. Hash/QR/signature detection without WINDI claim. |
| v2.1 | MEDIUM | Liveness detection for HIGH-tier signing. eIDAS substantial compliance. |
| v2.2 | MEDIUM | Verify Dashboard for tenants. Internal integrity overview. |
| v3.0 | FUTURE | Constitutional scanner. Universal authenticity analysis. WINDI = standard. |
| v3.1 | FUTURE | eIDAS qualified integration. Legal presence proof. Cross-jurisdiction. |

---

## Seal Record

| Field | Value |
|-------|-------|
| Document type | ARCHITECTURAL_SPEC |
| Impact level | CRITICAL |
| Risk level | R5 — Institutional |
| Seal requirement | Mandatory — Three Dragons Protocol |
| Retention | Permanent — I11 scope |
| Distribution | Internal — WINDI Architecture team |
| Sealed hash | [TO BE FILLED ON SEALING] |
| Seal timestamp | [TO BE FILLED ON SEALING] |
| Serial | [WINDI-2026-XXXX] |

---

*WINDI Publishing House — Kempten, Bavaria, Germany*
*Three Dragons Protocol — I11 IRREMEDIABLE — 05 March 2026*
*"AI processes. Human decides. WINDI guarantees."*
