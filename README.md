# 🐉 WINDI Publishing House
### AI Document Governance, Verification & Sovereign Identity

> **AI processes. Human decides. WINDI guarantees.**

WINDI is a production-grade governance framework for AI-assisted institutional documents. It combines sovereign identity (DID), a multi-agent constellation, cryptographic integrity, and public verification — built and operated from Kempten, Bavaria, Germany.

---

## ⚖️ Constitutional Principles

WINDI operates under a sealed constitutional framework. Every action in the system is governed by invariants that cannot be altered at runtime:

| Invariant | Description | Status |
|---|---|---|
| **I1** | Human Decision Gate — AI proposes, human authorizes | IRREMEDIÁVEL |
| **I9** | Prohibition of Autonomy Escalation | IRREMEDIÁVEL |
| **I11** | Permanence of Cryptographic Evidence | IRREMEDIÁVEL |

> *"IRREMEDIÁVEL"* — sealed in the Forensic Ledger. Irreversible by design.

The governance philosophy: **Four-Eyes Principle** (AI + Human oversight), structural integrity validation, cryptographic provenance, and full public auditability.

---

## 🏗️ Architecture Overview

WINDI runs as a sovereign platform on a single VPS (Strato, Germany), with **93.3% local operational sovereignty** — most intelligence runs locally, with external LLMs used only when quality justifies the cost.

```
windi-domain.com  (ONE TREE — single nginx, single identity)
│
├── /app/              → GEN7 Mobile Control Center
├── /desktop/          → GEN7 Desktop Workspace
├── /verify-public/    → Public Document Verification
├── /law/              → WINDI LAW — Legal Identity Gateway
├── /travel/           → WINDI TRAVEL — Sovereign Travel Layer
├── /agents/           → Agent Constellation (Sandbox Core)
└── /guardian/         → Constitutional Guard
```

---

## 🤖 Agent Constellation

Seven constitutional agents, running as domain extensions of a single Sandbox Core process:

| Agent | Role | Version |
|---|---|---|
| **W-LEGAL-001** | Evidence Git, multi-jurisdiction law (DE/EU/BR/INT) | v0.2.0 |
| **W-NOTARY-001** | Notarial document sealing | v1.0 |
| **W-COMPLY-001** | Regulatory compliance checks | v1.0 |
| **W-COMM-001** | Document Intelligence Hub (8 doc types) | v2.0.0 |
| **W-JOURN-001** | Journalistic publishing pipeline (J1–J6) | v1.0 |
| **W-AUDIT-001** | Constitutional audit trail | v1.0 |
| **W-ACCT-001** | GoBD-compliant accounting, ELSTER XML | Wave3 |

All agents follow the **Iron Rule**: *domain extensions of the constitutional core, never standalone services.*

---

## 🔐 Sovereign Identity — DID Wallet

WINDI users receive a **Decentralized Identifier (DID)** generated locally:

- **Ed25519** keypair + **UUIDv7** anchoring
- Identity created on-device — no raw data leaves the client
- Every document action is identity-bound
- **Berçário** (Cradle) system tracks identity lifecycle: `nasceu → entrou → saiu → voltou`
- GDPR Article 5(1)(c) by design — name + email for identification only

> *"WINDI knows who you are to guarantee what you produce. Nothing more."*

---

## 🔍 Forensic Ledger & Verification

Every document action creates a tamper-evident receipt sealed in the **Forensic Ledger** (40,000+ receipts in production).

### Public Verification

Anyone can verify a WINDI document:

| Interface | URL |
|---|---|
| Human-readable | `https://windi-domain.com/verify-public/?id=<receipt_id>` |
| Machine-readable API | `https://windi-domain.com/api/verify/<receipt_id>` |
| QR format | `WINDI:<receipt_id>|<sha256_hash>` |

**Constitutional Invariant I11** (sealed 2026-03-05):
*Permanence of Cryptographic Evidence — receipts are IRREMEDIÁVEL. Once sealed, unreachable by any process.*

---

## 🧱 Document Pipeline

```
Document Created
      ↓
Dragon AI Agent (proposes structure)
      ↓
Human Review Gate  ← Constitutional requirement
      ↓
SHA-256 Hash + Serial (WINDI-YYYY-XXXX)
      ↓
QR Code embedded
      ↓
Forensic Ledger (sealed receipt)
      ↓
Public Verification available
```

Supported document types: Communiqué, Präsentation, Zertifikat, Rechnung, Legal Evidence, Journalistic Article, Notarial Record, Accounting Export, and more.

---

## 🏛️ Products

| Product | Description | Status |
|---|---|---|
| **WINDI LAW** | Legal identity gateway, verified DID onboarding | LIVE |
| **WINDI TRAVEL** | Sovereign travel with GPS proofs, affiliate bridge | LIVE |
| **WINDI Verify** | Public document verification, Media Detector | LIVE |
| **WINDI Palette** | 14-type document routing hub, tier-aware workspace | LIVE |
| **WINDI Wallet** | Sovereign identity cockpit, Trust Radar | LIVE |

---

## 🎓 Academic Background

This platform supports the research project:

> **"WINDI — Governance Infrastructure for AI-Assisted Institutional Documents"**

The implementation demonstrates a fully operational reference architecture for:
- AI-human co-authorship governance
- Cryptographic document provenance
- Sovereign identity anchoring for institutional records
- Public auditability without data exposure

---

## 🛡️ Three Dragons Protocol

WINDI governance is structured around three constitutional roles (no brand names in UI — roles only):

- 🛡️ **Guardian** — enforces constitutional invariants
- 🏗️ **Architect** — designs and extends the system
- 👁️ **Witness** — observes, records, and seals

> *"AI processes. Human decides. WINDI guarantees."*

---

## 🔗 Links

| Resource | URL |
|---|---|
| Platform | https://windi-domain.com |
| Public Verification | https://windi-domain.com/verify-public/ |
| WINDI LAW | https://windi-domain.com/law/gate |
| WINDI TRAVEL | https://windi-domain.com/travel/gate |

---

## 📌 Purpose of This Repository

This repository contains technical components of the WINDI Verification & Governance Layer, including:

- 📄 PDF receipt generation with embedded QR codes
- 🔐 Cryptographic hash and structural integrity pipeline
- 🌐 Public verification endpoints (HTML & JSON)
- 🤖 Constitutional agent blueprints
- 🧭 Governance and integrity validation tooling

It serves as supplementary technical evidence for academic and regulatory review, and demonstrates a fully operational sovereign governance implementation.

---

*Founded 2026 · Kempten, Bavaria, Germany · Liga IA+H*

*"The document is not a file. It is a proof."* 🐉


