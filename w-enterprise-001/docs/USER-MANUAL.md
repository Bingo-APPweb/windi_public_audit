# W-Enterprise-001 — User Manual

**AI Compliance Dashboard**
**Version:** 1.0
**Date:** April 2026
**Author:** WINDI Publishing House · Liga IA+H

---

## Table of Contents

1. [Introduction](#1-introduction)
   - 1.1 [What is W-Enterprise-001?](#11-what-is-w-enterprise-001)
   - 1.2 [Why PHO Matters](#12-why-pho-matters)
   - 1.3 [Glossary](#13-glossary)
2. [Quick Start](#2-quick-start)
   - 2.1 [Accessing the Dashboard](#21-accessing-the-dashboard)
   - 2.2 [Interface Overview](#22-interface-overview)
   - 2.3 [Your First Approval](#23-your-first-approval)
3. [Workflow](#3-workflow)
   - 3.1 [Review Pending Decisions](#31-review-pending-decisions)
   - 3.2 [Approve with PHO](#32-approve-with-pho)
   - 3.3 [Reject or Escalate](#33-reject-or-escalate)
   - 3.4 [Verify Receipts](#34-verify-receipts)
4. [Features](#4-features)
   - 4.1 [Dashboard Statistics](#41-dashboard-statistics)
   - 4.2 [Audit Log](#42-audit-log)
   - 4.3 [Export & Reports](#43-export--reports)
5. [Integration](#5-integration)
   - 5.1 [API Reference](#51-api-reference)
   - 5.2 [Connect AI Systems](#52-connect-ai-systems)
6. [Reference](#6-reference)
   - 6.1 [Constitutional Invariants](#61-constitutional-invariants)
   - 6.2 [Troubleshooting](#62-troubleshooting)
   - 6.3 [Support](#63-support)

---

## 1. Introduction

### 1.1 What is W-Enterprise-001?

**W-Enterprise-001** is the WINDI AI Compliance Dashboard — a human oversight system designed for enterprises using artificial intelligence in high-risk decision-making.

In simple terms: when your AI system makes a recommendation (approve a loan, settle a claim, flag fraud), this dashboard ensures a **qualified human reviews and approves** that decision before it takes effect.

```
AI System → Decision → Human Review → PHO Seal → Ledger → Execution
```

Every approval generates a **cryptographic receipt** that proves:

- **WHO** approved (identity of the reviewer)
- **WHEN** approved (exact timestamp)
- **WHAT** was approved (SHA-256 hash of the decision)
- **WHERE** it's recorded (immutable Forensic Ledger)

### 1.2 Why PHO Matters

> **EU AI Act — Article 14**
>
> High-risk AI systems shall be designed and developed in such a way that they can be effectively overseen by natural persons during the period in which the AI system is in use.

**PHO** stands for **Prescribed Human Oversight**. Under the EU AI Act (effective 2026), companies deploying high-risk AI systems must demonstrate that:

1. A human can understand the AI's recommendations
2. A human can override or reject those recommendations
3. There is an **auditable trail** of all human oversight actions

**Without PHO compliance:**
- Regulatory fines up to 35M EUR or 7% of global turnover
- Decisions may be legally contested
- Reputational damage

**With W-Enterprise-001:**
- Court-admissible proof of human oversight
- Immutable cryptographic receipts
- Real-time compliance dashboard

### 1.3 Glossary

| Term | Definition |
|------|------------|
| **PHO** | Prescribed Human Oversight — the act of a human reviewing and approving an AI decision |
| **Receipt** | Cryptographic proof of a PHO action, containing hash, timestamp, and identity |
| **Ledger** | WINDI Forensic Ledger — immutable database where all receipts are permanently stored |
| **SHA-256** | Cryptographic hash function that creates a unique fingerprint of the decision data |
| **SGE Score** | Semantic Governance Engine score — risk classification from 0 (low) to 10 (critical) |
| **Trust Officer** | The human authorized to review and approve AI decisions in the organization |
| **Decision** | An AI system output that requires human oversight before execution |
| **Verify Public** | Public endpoint where anyone can independently verify a receipt's authenticity |

---

## 2. Quick Start

### 2.1 Accessing the Dashboard

Open your browser and navigate to:

```
https://windi-domain.com/enterprise/
```

> **Pilot Mode:** During pilot phase, the dashboard operates with a fixed token. In production, you will authenticate using your organization's DID (Decentralized Identity) credentials.

### 2.2 Interface Overview

The dashboard is organized into four main areas:

#### A) Top Bar
- **WINDI ENTERPRISE** — Logo and system identifier
- **Ledger · Live** — Connection status to the Forensic Ledger
- **User Badge** — Your identity as Trust Officer

#### B) Sidebar Navigation
- **Decisions** — Main view of pending and verified decisions
- **PHO Receipts** — Archive of all sealed approvals
- **Audit Export** — Download compliance reports
- **Verify Public** — Link to independent verification
- **Configuration** — AI systems, rules, reviewers (admin)

#### C) Statistics Panel

| Metric | Description |
|--------|-------------|
| PHO Verified Today | Number of decisions approved with PHO seal today |
| Pending Oversight | Decisions awaiting human review (requires action) |
| Compliance Rate | Percentage of decisions with PHO coverage this week |
| Ledger Receipts | Total receipts stored in the immutable ledger |

#### D) Decisions Table

The main working area showing all AI decisions with their status:
- **Missing PHO** — Requires your review
- **PHO Verified** — Already approved and sealed

### 2.3 Your First Approval

Follow these steps to approve your first AI decision:

1. Find a decision with **Missing PHO** status
2. Click the **Approve with PHO** button
3. Review the decision details in the modal
4. Select your decision: Approved / Modified / Rejected / Escalated
5. Add an optional oversight note
6. Click **Seal PHO Receipt**
7. Wait for the cryptographic seal to complete
8. View your receipt with verification link

---

## 3. Workflow

### 3.1 Review Pending Decisions

Decisions appear in the table as soon as your connected AI systems generate them. Each decision shows:

| Field | Description |
|-------|-------------|
| Decision Title | Human-readable summary of what the AI recommends |
| Decision ID | Unique identifier (e.g., DEC-2026-0041) |
| AI System | The system that generated this decision |
| Risk Level | HIGH / MEDIUM / LOW classification |
| Time | When the decision was created |
| Status | Missing PHO or PHO Verified |

> **Important:** Decisions marked **HIGH** risk require human oversight before any action is taken. Proceeding without PHO approval violates EU AI Act Article 14.

### 3.2 Approve with PHO

When you click **Approve with PHO**, a modal opens with:

#### Decision Preview
Shows the decision title, ID, AI system, and risk level for confirmation.

#### PHO Seal Information
Reminder that your approval will generate a cryptographic receipt containing your identity, timestamp, decision hash, and immutable ledger anchor.

#### Reviewer Name
Your name as it will appear on the receipt. This identifies you as the responsible human overseer.

#### Decision Options

| Option | When to Use |
|--------|-------------|
| **Approved** | You agree with the AI's recommendation — proceed as suggested |
| **Approved with Modifications** | You agree but with changes (document in the note) |
| **Rejected** | You disagree — return to AI system for reconsideration |
| **Escalated** | Requires senior review — outside your authorization level |

#### Oversight Note
Optional field to document your rationale. This becomes part of the cryptographic record.

### 3.3 Reject or Escalate

If you select **Rejected**:
- The decision is marked as rejected in the system
- A receipt is still generated (proof that oversight occurred)
- The AI system should be notified to reconsider or generate alternatives

If you select **Escalated**:
- The decision is flagged for senior review
- Your escalation is recorded in the audit trail
- A notification should be sent to the appropriate authority

### 3.4 Verify Receipts

After sealing, every receipt can be verified independently:

1. Click the **Verify** button on any verified decision
2. Or visit `windi-domain.com/verify-public/?id=RECEIPT_ID`
3. The verification page shows all receipt details
4. Anyone can verify — no login required

---

## 4. Features

### 4.1 Dashboard Statistics

The statistics panel provides real-time metrics:

| Metric | Target | Action if Low |
|--------|--------|---------------|
| PHO Verified Today | Match decision volume | Review pending queue |
| Pending Oversight | 0 (ideal) | Prioritize HIGH risk first |
| Compliance Rate | 100% | Check for oversight gaps |
| Ledger Receipts | Growing | Normal operation |

### 4.2 Audit Log

The audit log shows recent PHO activities:

- **PHO Sealed** — Successful approval with receipt
- **Oversight Gap** — Decision executed without PHO (violation)

Each entry shows:
- Timestamp of the action
- Decision reference
- Receipt ID (ledger anchor)
- Short hash for verification

### 4.3 Export & Reports

Click **Audit Export** to download a CSV file containing:

- Receipt ID
- Decision title
- Reviewer name
- Timestamp
- SHA-256 hash
- Compliance status

This export is suitable for:
- Regulatory audits
- Internal compliance reviews
- Legal discovery
- Board reporting

---

## 5. Integration

### 5.1 API Reference

W-Enterprise-001 provides a REST API for integration with your AI systems:

#### Health Check

```http
GET /enterprise/health

Response:
{
  "service": "W-Enterprise-001",
  "version": "1.0.0",
  "status": "operational",
  "invariants": ["I1", "I9", "I11", "I14"]
}
```

#### List Decisions

```http
GET /enterprise/api/decisions

Response:
{
  "decisions": [...],
  "stats": {
    "pending": 3,
    "verified": 12,
    "total": 15,
    "compliance_rate": 80
  }
}
```

#### Create Decision

```http
POST /enterprise/api/decisions
Content-Type: application/json

{
  "title": "Loan Application Risk Assessment",
  "system": "AllianzRisk-AI v3.2",
  "risk_level": "HIGH",
  "description": "Automated risk score: 72/100",
  "sge_score": 7.2
}
```

#### PHO Approval

```http
POST /enterprise/api/pho/approve
Content-Type: application/json

{
  "decision_id": "DEC-2026-0041",
  "decision_title": "Loan Application Risk Assessment",
  "reviewer": "Anna Mueller",
  "outcome": "APPROVED",
  "note": "Risk acceptable for SME segment",
  "risk_level": "HIGH",
  "sge_score": 7.2
}

Response:
{
  "ok": true,
  "receipt_id": "WINDI-PHO-20260412-A4F8C9D2",
  "hash": "a4f8c9d2e1b3f7a8...",
  "timestamp": "2026-04-12T09:14:22Z",
  "ledger_ok": true,
  "verify_url": "https://windi-domain.com/verify-public/?id=...",
  "eu_ai_act": "Article 14 — Human Oversight — Compliant"
}
```

#### Audit Log

```http
GET /enterprise/api/audit

Response:
{
  "log": [...],
  "total": 47
}
```

### 5.2 Connect AI Systems

To connect your AI system to W-Enterprise-001:

1. **Configure webhook** — Your AI system should POST decisions to `/enterprise/api/decisions`
2. **Include metadata** — Title, system name, risk level, description, SGE score
3. **Wait for approval** — Do not execute until PHO receipt is generated
4. **Verify receipt** — Optionally confirm via the verification endpoint

> **Critical Requirement:** Your AI system must NOT execute high-risk decisions until a PHO receipt exists. This is the core compliance requirement of EU AI Act Article 14.

---

## 6. Reference

### 6.1 Constitutional Invariants

W-Enterprise-001 operates under WINDI's constitutional framework. These invariants are **non-negotiable**:

| ID | Name | Impact |
|----|------|--------|
| **I1** | Human Sovereignty | AI suggests, human decides. Never autonomous execution. |
| **I9** | Human Approval Gate | `human_approved=true` required before any seal. **IRREMEDIABLE** |
| **I11** | Cryptographic Evidence | SHA-256 hash sealed to Forensic Ledger. Immutable forever. **IRREMEDIABLE** |
| **I14** | Explicit Failure | No placeholders. Missing data = explicit error. **IRREMEDIABLE** |

> **IRREMEDIABLE** — Invariants marked as IRREMEDIABLE cannot be overridden by any configuration, user, or system. They are hardcoded into the system architecture.

### 6.2 Troubleshooting

#### Ledger Offline
- **Symptom:** "Ledger Offline" in top bar
- **Cause:** Connection to Forensic Ledger (:8101) unavailable
- **Impact:** Receipts are generated locally with `ledger_mode: "local_fallback"`
- **Resolution:** Contact system administrator. Local receipts remain valid but should be synced when ledger recovers.

#### Session Expired
- **Symptom:** Actions fail with 401 error
- **Cause:** Authentication token expired
- **Resolution:** Refresh the page or re-authenticate with your DID credentials

#### Decision Not Appearing
- **Symptom:** AI system created a decision but it's not in the dashboard
- **Cause:** API integration issue
- **Resolution:** Check that POST to `/enterprise/api/decisions` returned 200/201

#### Hash Mismatch on Verification
- **Symptom:** Verify Public shows different hash
- **Cause:** Data modified after sealing (potential tampering)
- **Resolution:** This is a critical alert. Investigate immediately. The original sealed data should be retrieved from the Forensic Ledger.

### 6.3 Support

**Documentation:** https://windi-domain.com/enterprise/docs/

**API Status:** https://windi-domain.com/enterprise/health

**Verify Endpoint:** https://windi-domain.com/verify-public/

**Contact:**
- WINDI Publishing House
- Kempten, Bavaria, Deutschland
- windi-domain.com

---

## Appendix: Receipt Schema

Every PHO receipt contains:

```json
{
  "receipt_id": "WINDI-PHO-20260412-A4F8C9D2",
  "decision_id": "DEC-2026-0041",
  "decision_title": "Loan Application Risk Assessment",
  "reviewer": "Anna Mueller",
  "outcome": "APPROVED",
  "note": "Risk acceptable for SME segment",
  "hash": "a4f8c9d2e1b3f7a8c9d2e1b3f7a8c9d2e1b3f7a8c9d2e1b3f7a8c9d2e1b3f7a8",
  "timestamp": "2026-04-12T09:14:22.000Z",
  "ledger_ok": true,
  "verify_url": "https://windi-domain.com/verify-public/?id=WINDI-PHO-20260412-A4F8C9D2",
  "invariants": ["I1", "I9", "I11"],
  "eu_ai_act": "Article 14 — Human Oversight — Compliant"
}
```

---

*WINDI Publishing House · Liga IA+H · Kempten, Bavaria · 2026*

*"AI processes. Human decides. WINDI guarantees."*
