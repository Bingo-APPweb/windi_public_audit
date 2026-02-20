---
name: windi-federation
description: >
  Manage, deploy, and troubleshoot the WINDI Federation architecture — the distributed
  governance platform connecting Hub and autonomous Clones. Covers three pillars:
  OIL (Operational Intelligence Layer), CHP (Clone Heartbeat Protocol), and
  Wallet-Based Key Lifecycle.
  Use when the user mentions federation, OIL, operational intelligence, CHP, heartbeat
  protocol, clone wallet, commissioning, zero-knowledge telemetry, silent clones,
  executive briefing, bottleneck, flow efficiency, governance quality, forensic integrity,
  institutional alignment, federated deploy, hub state, hub collector, report agent,
  attention report, integrity assurance, daily brief, clone identity, tenant, SMTP
  governance, store-and-forward, wallet reconstruction, key rotation, or any task
  involving the WINDI federated governance architecture.
  Also use for: federation health checks, CHP sender/receiver implementation,
  OIL metric correlation, wallet commissioning ceremonies, clone-to-hub communication,
  federated reporting, and Zero-Knowledge Telemetry validation.
---

# WINDI-FEDERATION — Federated Governance Architecture

## Overview

The WINDI Federation is a distributed governance platform where autonomous Clones
operate under full constitutional authority (P0-P7 matrix) while a central Hub
maintains operational intelligence without accessing sensitive data.

**Principle:** "AI processes. Human decides. WINDI guarantees."
**Version:** v1.0.0 — Sealed 2026-02-14
**Marco Sequence:** #4 (after Handshake→Matrix→Birth Certificate)
**Classification:** CONSTITUTIONAL

## The Three Pillars

| Pillar | Function | Analogy |
|--------|----------|---------|
| **OIL** — Operational Intelligence Layer | What to measure and correlate | The brain that interprets |
| **CHP** — Clone Heartbeat Protocol | How to transmit telemetry | The nervous system |
| **Wallet Lifecycle** | How to establish and maintain trust | The identity document |

**Design Principle:** Zero-Knowledge Telemetry. Clones process sensitive data locally;
the Hub receives only governance metrics, constitutional status, and operational
indicators. No document content, PII, or client identifiers ever traverse the
federation channel.

**I9 Enforcement:** OIL interprets, alerts, and prioritizes — but NEVER decides,
blocks, or alters policies autonomously.

---

# Pillar I — Operational Intelligence Layer (OIL)

## Purpose

OIL transforms the existing meta_governance layer from observability into
operational intelligence:

- **Before:** Collect → Display → Report
- **After:** Collect → Correlate → Interpret → Prioritize → Report

It is NOT a new agent — it is the evolution of HubCollector + Report Agent.
HubCollector remains read-only, aggregating, and zero-knowledge. It gains
correlation, interpretation, and prioritization — without ever deciding or
executing.

## Five Operational Metrics

### 1. Flow Efficiency (Decisional Flow)
**Answers:** Where does governance stall before human decision?
```json
{
  "flow_efficiency": {
    "avg_session_to_decision_minutes": 14.2,
    "stalled_sessions": 3,
    "stall_locations": ["pre_i9_gate", "sge_layer_4"],
    "throughput_trend": "improving"
  }
}
```

### 2. Governance Quality
**Answers:** How well is the constitutional framework functioning?
```json
{
  "governance_quality": {
    "i9_violations_attempted": 0,
    "sge_risk_distribution": {"R0": 42, "R1": 8, "R2": 2, "R3": 0},
    "virtue_receipt_completeness": 0.98,
    "override_attempts": 0
  }
}
```

### 3. Forensic Integrity
**Answers:** Is the audit trail complete and trustworthy?
```json
{
  "forensic_integrity": {
    "merkle_chain_valid": true,
    "last_anchor_age_hours": 2.3,
    "receipt_gap_count": 0,
    "ledger_write_latency_ms": 45
  }
}
```

### 4. Institutional Alignment
**Answers:** How well do documents conform to institutional standards?
```json
{
  "institutional_alignment": {
    "isp_conformity_rate": 0.94,
    "non_standard_docs": 0.06,
    "template_usage_rate": 0.87,
    "active_isp_profiles": 5
  }
}
```

### 5. Bottlenecks (Cross-Metric Correlation)
**Answers:** Where is the system under pressure?
```json
{
  "bottlenecks": [
    {
      "type": "decision_delay",
      "location": "pre_i9",
      "impact_level": "high",
      "contributing_factors": ["stalled_sessions", "sla_pressure"]
    }
  ]
}
```

## Hub State Integration

OIL adds `operational_intelligence` section to `hub_state.json`:
```json
{
  "system_health": { "..." : "..." },
  "metrics": { "..." : "..." },
  "operational_intelligence": {
    "flow_efficiency": { "..." : "..." },
    "governance_quality": { "..." : "..." },
    "forensic_integrity": { "..." : "..." },
    "institutional_alignment": { "..." : "..." },
    "bottlenecks": []
  }
}
```

## Executive Reports (Report Agent Evolution)

| Report | Content | Frequency |
|--------|---------|-----------|
| **Daily Executive Brief** | Operational efficiency, forensic integrity, critical risks | Daily |
| **Attention Report** | Emerging bottlenecks, policy violations, stalled sessions | On-demand / threshold |
| **Integrity Assurance Report** | Forensic chain intact, anchors verified, latency within params | Weekly / audit |

---

# Pillar II — Clone Heartbeat Protocol (CHP) v1.0

## Purpose

Enable federated visibility (Hub + remote Clones) without exposing sensitive data,
using SMTP as an asynchronous and auditable transport.

- **Channel Direction:** Clone → Hub (unidirectional)
- **Data Type:** Metrics + constitutional status + alerts (no document content)
- **Transport:** SMTP (store-and-forward, firewall-friendly, natively auditable)
- **Principle:** Zero-Knowledge Telemetry

## Why SMTP

SMTP works behind corporate firewalls (every institution has SMTP). No VPN, no
special ports, no permanent connection needed. If Clone is offline, local operation
continues unaffected. If Hub is offline, emails queue and reconcile on reconnect.
MTA logs on both sides serve as native audit trails.

## Fundamental Properties

| Property | Description |
|----------|-------------|
| **Resilience** | Store-and-forward; tolerates disconnections |
| **Auditability** | SMTP headers (Message-ID, Received chain) = native audit |
| **Sovereignty** | Clone: processing + local proof. Hub: aggregation + intelligence |

## Clone Identity

| Field | Example | Description |
|-------|---------|-------------|
| `clone_id` | CLONE-SPK-FFM-001 | Unique stable identifier |
| `tenant_id` | SPARKASSE-FFM | Organization / institution |
| `phase` | PHASE_3_AUTONOMOUS | Operational phase |
| `constitutional_hash` | 2310a8e62252c... | Hash of active P0-P7 matrix |

## Heartbeat Payload Structure

```json
{
  "chp_version": "1.0",
  "clone_id": "CLONE-SPK-FFM-001",
  "tenant_id": "SPARKASSE-FFM",
  "timestamp": "2026-02-14T10:00:00Z",
  "sequence": 1847,
  "phase": "PHASE_3_AUTONOMOUS",
  "constitutional_hash": "2310a8e62252c...",
  "metrics": {
    "sessions_active": 12,
    "decisions_pending": 3,
    "sge_alerts": 1,
    "forensic_chain_valid": true,
    "uptime_hours": 168.5
  },
  "alerts": [],
  "signature": "ed25519_signature_here"
}
```

## CHP Email Format

```
From: chp@clone-spk-ffm-001.windi.local
To: chp-receiver@hub.windi-domain.com
Subject: [CHP] CLONE-SPK-FFM-001 | SEQ:1847 | 2026-02-14T10:00:00Z
Content-Type: application/json
X-WINDI-CHP-Version: 1.0
X-WINDI-Clone-ID: CLONE-SPK-FFM-001
X-WINDI-Sequence: 1847

{ ... heartbeat JSON payload ... }
```

## Hub Processing (5-Step Verification)

When Hub receives a CHP heartbeat:
1. **Identity Check:** `clone_id` recognized in registry?
2. **Signature Validation:** ed25519 signature valid against registered public key?
3. **Sequence Check:** `sequence` > last_seen_sequence? (anti-replay)
4. **Constitutional Consistency:** `constitutional_hash` matches registered hash?
5. **Metric Integration:** Merge into `hub_state.json` operational_intelligence

## Silent Clone Detection

If no heartbeat received within expected interval → Clone marked as "silent."
Hub generates Attention Report. Silent ≠ dead; may be disconnected.
Hub NEVER sends commands to Clone. Unidirectional only.

## Sequence Persistence

The `sequence` counter MUST persist on disk at `/var/lib/windi/chp_sequence`.
Must survive restarts. Atomic-write protected (write temp, rename).
A Clone restarting from zero opens a replay vulnerability.

---

# Pillar III — Wallet-Based Key Lifecycle

## Principle

The cryptographic identity of a WINDI Clone is managed by an **Institutional
Clone Wallet** — simultaneously functioning as commissioning certificate,
cryptographic key vault, constitutional legitimacy proof, and recovery instrument.

## Wallet Hierarchy

| Layer | Wallet Type | Purpose |
|-------|-------------|---------|
| **Passenger** | Personal user wallet | Identity + docs + Virtue Receipts |
| **Clone** | Institutional clone wallet | Identity + CHP keys + constitutional hash |
| **Hub** | Public key registry | Validation of federated heartbeats |

## Clone Wallet Structure

```json
{
  "wallet_type": "WindiCloneWallet",
  "wallet_version": "1.0",
  "clone_id": "CLONE-SPK-FFM-001",
  "tenant_id": "SPARKASSE-FFM",
  "public_key": "base64...",
  "private_key": "base64...",
  "fingerprint": "sha256:...",
  "constitutional_hash": "2310a8e62252c...",
  "commissioned_at": "2026-02-14T09:00:00Z",
  "commissioned_by": "Human Dragon",
  "phase": "PHASE_2_COMMISSIONED",
  "signature": "guardian_commissioning_signature"
}
```

## Commissioning Flow (Phase 2)

1. **Key Generation:** ed25519 (preferred) or ECDSA P-256
2. **Private key stays local:** NEVER leaves the Clone
3. **Public key registered at Hub:** Added to CHP whitelist
4. **Wallet delivered to administrator:** Stored in institutional vault
5. **Constitutional hash associated:** P0-P7 matrix linked to clone_id

## Storage & Custody

**On Clone:**
- File: `/var/lib/windi/clone_wallet.json`
- Permissions: `chmod 600`, owner: `windi`
- Private key NEVER leaves the Clone

**At Institution:**
- Administrator stores in digital vault + secure backup + offline backup
- Loss of Wallet compromises ability to reconstruct Clone

## Hub Registration

During commissioning:
- Public key registered in Hub registry
- Fingerprint added to CHP whitelist
- Constitutional hash associated with clone_id
- Hub trusts heartbeats signed by this identity
- No additional PKI infrastructure required

## CHP Signature Integration

Each heartbeat signed with Wallet private key. Hub validates:
- `clone_id` recognized
- Fingerprint valid
- Signature valid
- `constitutional_hash` consistent

## Reconstruction & Continuity

In case of failure/migration/rebuild:
1. Administrator presents Wallet to Guardian
2. Guardian validates `constitutional_hash` against P0-P7 matrix
3. Clone reborn with continuous identity (`clone_id` + `tenant_id`)
4. Cryptographic identity restored (or keys rotated if needed)
5. Hub resumes CHP aggregation for this clone

## Key Rotation

Performed when: compromise suspected, scheduled rotation, institutional policy.
Process: generate new pair → update Wallet → re-register at Hub → old key
revoked. Clone identity (`clone_id`) survives rotation.

---

# Constitutional Compliance

## I9 Enforcement Across Pillars

| Pillar | What it does | What it NEVER does |
|--------|-------------|-------------------|
| **OIL** | Interprets, alerts, prioritizes | Decides, blocks, alters policies |
| **CHP** | Transmits telemetry (clone→hub) | Sends commands (hub→clone) |
| **Wallet** | Proves identity, enables trust | Grants autonomous authority |

## Zero-Knowledge Properties

- Document content NEVER traverses federation channel
- PII NEVER included in heartbeats
- Client identifiers NEVER reach the Hub
- Hub stores only governance proofs and operational metrics

**Strategic Insight:** Zero-Knowledge Telemetry transforms privacy from
compliance burden into competitive advantage. WINDI proves governance
without seeing content — reducing adoption friction and removing CISO
objections.

---

# Implementation Roadmap

## Phase 2A — CHP Sender (Clone-side)
- [ ] Heartbeat generator module
- [ ] SMTP sender with store-and-forward
- [ ] Sequence persistence at `/var/lib/windi/chp_sequence`
- [ ] Wallet-based signing

## Phase 2B — CHP Receiver (Hub-side)
- [ ] SMTP receiver / mailbox parser
- [ ] 5-step verification pipeline
- [ ] Integration with `hub_state.json`
- [ ] Silent clone detection

## Phase 2C — OIL Engine
- [ ] HubCollector evolution with correlation module
- [ ] 5 operational metrics calculation
- [ ] Bottleneck detection algorithm
- [ ] Report Agent evolution (3 report types)

## Phase 2D — Wallet Commissioning
- [ ] Key generation ceremony tooling
- [ ] Wallet creation and delivery workflow
- [ ] Hub registry management
- [ ] Reconstruction procedure

---

# File Structure on Server

```
/opt/windi/hub/
├── federation/
│   ├── FEDERATION_ARCHITECTURE_v1.0.md    (sealed document)
│   ├── FEDERATION_v1.0_SEAL.json          (seal certificate)
│   └── archive/                            (previous versions)
├── chp/
│   ├── receiver/                           (CHP receiver module)
│   ├── archive/                            (processed heartbeats)
│   └── whitelist.json                      (registered clone keys)
├── cache/                                  (operational cache)
├── logs/                                   (federation logs)
└── hub_state.json                          (includes operational_intelligence)

/var/lib/windi/                             (on each Clone)
├── clone_wallet.json                       (chmod 600)
└── chp_sequence                            (persistent counter)
```

## Verification Commands

```bash
# Verify Federation Architecture seal
sha256sum /opt/windi/hub/federation/FEDERATION_ARCHITECTURE_v1.0.md

# Check hub_state operational intelligence
cat /opt/windi/hub/hub_state.json | python3 -m json.tool | grep -A20 operational_intelligence

# List registered clones (whitelist)
cat /opt/windi/hub/chp/whitelist.json | python3 -m json.tool

# Check CHP receiver logs
tail -50 /opt/windi/hub/logs/chp_receiver.log

# Validate Clone wallet integrity
sha256sum /var/lib/windi/clone_wallet.json

# Check CHP sequence persistence
cat /var/lib/windi/chp_sequence
```

---

# Historical Marcos

| # | Marco | Date | Location |
|---|-------|------|----------|
| 1 | Handshake Marco Zero | 2026-01-19 | `/opt/windi/clone/manifest.json` |
| 2 | Constitutional Matrix (P0-P7) | 2026-02-08 | `/opt/windi/clone/matrix/` |
| 3 | Birth Certificate IA+H | 2026-02-09 | `/opt/windi/clone/BIRTH_CERTIFICATE_IAH.json` |
| 4 | Federation Architecture | 2026-02-14 | `/opt/windi/hub/federation/` |

---

## Metadata

- **Version:** v1.0.0
- **Seal Date:** 2026-02-14
- **Hash Algorithm:** SHA-256
- **Constitutional Amendments:** Require Three Dragons validation + Human Dragon approval + new seal
- **Amendment Policy:** Previous versions archived, never deleted
- **Principle:** "AI processes. Human decides. WINDI guarantees."
