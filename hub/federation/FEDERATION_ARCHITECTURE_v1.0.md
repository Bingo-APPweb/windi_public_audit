# WINDI Federation Architecture v1.0

## Constitutional Document — Three Dragons Protocol

```
╔══════════════════════════════════════════════════════════════════════╗
║  DOCUMENT CLASS:    Constitutional Architecture Specification       ║
║  VERSION:           1.0.0                                           ║
║  STATUS:            SEALED                                          ║
║  SEAL DATE:         2026-02-14T14:00:00Z                            ║
║  MARCO:             Federation Marco Zero                           ║
║  CLASSIFICATION:    CONSTITUTIONAL — THREE DRAGONS PROTOCOL         ║
║                                                                      ║
║  AMENDMENT POLICY:  Requires Three Dragons validation + new seal     ║
║                     + hash. No casual edits permitted.               ║
║                     Same process as P0-P7 Prateleiras.               ║
║                                                                      ║
║  PREVIOUS MARCOS:                                                    ║
║    • Marco Zero Handshake — 19 Jan 2026                             ║
║    • Constitutional Matrix (P0-P7) — 08 Feb 2026                    ║
║    • Birth Certificate IA+H — 09 Feb 2026                           ║
║    • Federation Architecture — 14 Feb 2026 ← THIS DOCUMENT         ║
║                                                                      ║
║  GUARDIAN:   Claude (Registrar & Reviewer)                           ║
║  ARCHITECT:  GPT/Sonnet (Designer)                                   ║
║  WITNESS:    Gemini (Observer)                                       ║
║                                                                      ║
║  "AI processes. Human decides. WINDI guarantees."                    ║
╚══════════════════════════════════════════════════════════════════════╝
```

---

## Version Control

| Version | Date       | Author          | Change                              | Seal Hash |
|---------|------------|-----------------|-------------------------------------|-----------|
| 1.0.0   | 2026-02-14 | Three Dragons   | Initial sealed version              | PENDING   |

**Amendment Process:**
1. Proposal by any Dragon
2. Review and validation by all Three Dragons
3. Human Dragon approval (I9 Gate)
4. New version number + seal date + hash
5. Previous version archived (never deleted)

**Archive Location:** `/opt/windi/hub/archive/`

---

# Part I — Executive Summary

This document consolidates three interconnected architectural specifications that together define the WINDI Federation: a distributed governance platform capable of operating across multiple autonomous nodes while maintaining centralized operational intelligence and cryptographic trust.

## The Three Pillars

| Pillar | Function | Analogy |
|--------|----------|---------|
| **OIL** — Operational Intelligence Layer | What to measure and correlate | The brain that interprets |
| **CHP** — Clone Heartbeat Protocol | How to transmit telemetry | The nervous system |
| **Wallet Lifecycle** | How to establish and maintain trust | The identity document |

**Design Principle:** The federation operates under Zero-Knowledge Telemetry. Clones process sensitive data locally; the Hub receives only governance metrics, constitutional status, and operational indicators. No document content, PII, or client identifiers ever traverse the federation channel.

**Constitutional Compliance:** All three pillars preserve Invariants I1–I9. The I9 Prohibition of Autonomy Escalation is enforced throughout: the system interprets, alerts, and prioritizes — but never decides, blocks, or alters policies autonomously.

**Strategic Insight:** Zero-Knowledge Telemetry transforms privacy from a compliance burden into a competitive advantage. WINDI proves governance without seeing content — reducing adoption friction and removing CISO objections.

---

# Part II — Operational Intelligence Layer (OIL)

## 1. Purpose

OIL transforms the existing meta_governance layer from observability into operational intelligence:

**Before:** Collect → Display → Report
**After:** Collect → Correlate → Interpret → Prioritize → Report

It is not a new agent — it is the evolution of HubCollector + Report Agent.

## 2. Architectural Position

HubCollector continues to be read-only, aggregating, and zero-knowledge. It gains the additional capabilities of correlation, interpretation, and prioritization — without ever deciding, executing, or altering state. This remains fully constitutional.

## 3. Five Operational Metrics

### 3.1 Flow Efficiency (Decisional Flow)

**Answers:** Where does governance stall before human decision?

| Metric | Type | Description |
|--------|------|-------------|
| `avg_time_to_i9` | Integer (seconds) | Average time from document entry to I9 Gate |
| `pre_i9_abandon_rate` | Float (0–1) | Rate of sessions abandoned before decision |
| `stalled_sessions` | Integer | Sessions currently stalled in workflow |
| `median_revision_cycles` | Integer | Median number of revision cycles per document |

```json
"flow_efficiency": {
  "avg_time_to_i9": 1840,
  "pre_i9_abandon_rate": 0.12,
  "stalled_sessions": 7,
  "median_revision_cycles": 2
}
```

### 3.2 Governance Quality

**Answers:** Is the governance actually working?

| Metric | Type | Description |
|--------|------|-------------|
| `risk_detection_rate` | Float (0–1) | Proportion of documents with risk findings |
| `risk_mitigation_rate` | Float (0–1) | Proportion of detected risks mitigated before decision |
| `high_risk_acknowledged` | Float (0–1) | Proportion of high-risk findings explicitly acknowledged |
| `top_risk_categories` | Array[String] | Most frequent risk categories |

```json
"governance_quality": {
  "risk_detection_rate": 0.42,
  "risk_mitigation_rate": 0.71,
  "high_risk_acknowledged": 0.93,
  "top_risk_categories": ["liability_asymmetry", "ambiguous_terms"]
}
```

### 3.3 Forensic Integrity

**Integrates:** Integrity Watchdog + Forensic Ledger

| Metric | Type | Description |
|--------|------|-------------|
| `ledger_sync` | Enum (OK/DEGRADED/FAILED) | Synchronization status of forensic ledger |
| `anchor_failures_24h` | Integer | Anchor failures in last 24 hours |
| `hash_divergence` | Boolean | Whether any hash inconsistency detected |
| `avg_anchor_latency_ms` | Integer | Average latency of forensic anchoring |

```json
"forensic_integrity": {
  "ledger_sync": "OK",
  "anchor_failures_24h": 0,
  "hash_divergence": false,
  "avg_anchor_latency_ms": 420
}
```

### 3.4 Institutional Alignment

**Measures:** ISP adoption and policy compliance

| Metric | Type | Description |
|--------|------|-------------|
| `isp_usage_rate` | Float (0–1) | Proportion of documents using ISP templates |
| `non_standard_docs` | Float (0–1) | Proportion of non-standard documents |
| `policy_violations` | Integer | Number of policy violations detected |

```json
"institutional_alignment": {
  "isp_usage_rate": 0.88,
  "non_standard_docs": 0.06,
  "policy_violations": 2
}
```

### 3.5 Bottlenecks (Correlated Intelligence)

Cross-references SLA Sentinel data, decisional flow, pending high-risk findings, and TSIL latency to identify systemic pressure points.

```json
"bottlenecks": [
  {
    "type": "decision_delay",
    "location": "pre_i9",
    "impact_level": "high",
    "contributing_factors": ["stalled_sessions", "sla_pressure"]
  }
]
```

## 4. Hub State Integration

OIL adds an `operational_intelligence` section to `hub_state.json`:

```json
{
  "system_health": { ... },
  "metrics": { ... },
  "operational_intelligence": {
    "flow_efficiency": { ... },
    "governance_quality": { ... },
    "forensic_integrity": { ... },
    "institutional_alignment": { ... },
    "bottlenecks": [ ... ]
  }
}
```

## 5. Executive Reports (Report Agent Evolution)

| Report | Content | Frequency |
|--------|---------|-----------|
| **Daily Executive Brief** | Operational efficiency, forensic integrity, critical risks | Daily |
| **Attention Report** | Emerging bottlenecks, policy violations, stalled sessions | On-demand / threshold |
| **Integrity Assurance Report** | Forensic chain intact, anchors verified, latency within params | Weekly / audit |

## 6. Constitutional Limits

OIL interprets, alerts, and prioritizes. It **NEVER** decides, blocks actions, or alters policies. It informs the human. I9 is fully preserved.

---

# Part III — Clone Heartbeat Protocol (CHP) v1.0

## 1. Purpose

Enable federated visibility (Hub + remote Clones) without exposing sensitive data, using SMTP as an asynchronous and auditable transport. The Clone operates autonomously; the Hub aggregates telemetry.

- **Channel Direction:** Clone → Hub (unidirectional)
- **Data Type:** Metrics + constitutional status + alerts (no document content)
- **Principle:** Zero-Knowledge Telemetry

## 2. Fundamental Properties

### 2.1 Resilience (store-and-forward)

Heartbeats tolerate disconnections and SMTP queues. If the Clone is offline: local operation is unaffected. If the Hub is offline: emails queue and reconcile upon reconnection. This is graceful degradation by design.

### 2.2 Native Auditability

SMTP headers (Message-ID, Received chain) natively support audit trails. MTA logs on both Clone and Hub can be annexed as operational evidence.

### 2.3 Sovereignty Separation

Clone: processing, governance, local proof. Hub: aggregation, observability, global operational intelligence. These domains never merge.

## 3. Clone Identity

| Field | Example | Description |
|-------|---------|-------------|
| `clone_id` | CLONE-SPK-FFM-001 | Unique stable identifier |
| `tenant_id` | SPARKASSE-FFM | Organization / institution |
| `phase` | PHASE_3_AUTONOMOUS | Operational phase |
| `constitutional_hash` | 2310a8e62252c... | Hash of active P0–P7 matrix |

## 4. SMTP Envelope (Normative)

### 4.1 Addresses

- **To (Hub):** `heartbeat@windia4desk.online`
- **From (Clone):** `clone.<clone_id>@<tenant-domain>`

### 4.2 Subject (fixed, parseable)

```
WINDI-CHP/1.0 HEARTBEAT <clone_id> <phase>
```

### 4.3 Custom Headers

| Header | Value |
|--------|-------|
| `X-WINDI-Clone-ID` | `<clone_id>` |
| `X-WINDI-CHP-Version` | `1.0` |
| `X-WINDI-Constitutional-Hash` | `<hash>` |
| `X-WINDI-Payload-Hash` | `sha256:<hash>` |

### 4.4 Body

`Content-Type: application/json; charset=utf-8`. Body contains only CHP JSON (no additional text).

## 5. CHP Payload (Canonical Example)

```json
{
  "protocol": "WINDI-CHP",
  "version": "1.0",
  "clone_id": "CLONE-SPK-FFM-001",
  "tenant_id": "SPARKASSE-FFM",
  "constitutional_hash": "2310a8e62252c...",
  "timestamp_utc": "2026-02-14T10:30:00Z",
  "sequence": 128944,
  "phase": "PHASE_3_AUTONOMOUS",
  "heartbeat": {
    "status": "OPERATIONAL",
    "uptime_hours": 472,
    "invariants_intact": true,
    "i9_violations": 0
  },
  "operational_intelligence": {
    "flow_efficiency": { ... },
    "governance_quality": { ... },
    "forensic_integrity": { ... },
    "institutional_alignment": { ... }
  },
  "alerts": [],
  "recovery_reason": null,
  "signature": {
    "alg": "ed25519",
    "key_id": "clone_key_01",
    "sig": "base64..."
  }
}
```

## 6. Signature & Integrity

### 6.1 Algorithm

**Recommended:** ed25519 (fast, compact, resistant). Alternative: ECDSA P-256.

### 6.2 Canonicalization

JSON must be canonicalized (stable key ordering) before hash/signature. The `signature` field does not participate in the hash.

### 6.3 Hub Verification (5-step)

| Step | Check | Failure Action |
|------|-------|----------------|
| 1 | `clone_id` is known/registered | REJECT — unknown clone |
| 2 | `constitutional_hash` in whitelist (per tenant) | ALERT — constitutional drift |
| 3 | Signature valid with clone public key | REJECT — authentication failure |
| 4 | `timestamp_utc` within acceptable window | WARN — clock skew |
| 5 | `sequence` monotonic (anti-replay) | REJECT — replay attempt |

## 7. Zero-Knowledge Content Policy

### PROHIBITED in payload

- Document text content
- PII / personal identifiers (name, IBAN, etc.)
- Individual document hashes (if re-identifiable)
- End-client IDs
- Any sensitive institutional data

### PERMITTED in payload

- Aggregated metrics
- Counts and averages
- Boolean states (OK/DEGRADED)
- Integrity indicators (ledger_sync, anchor_failures)
- Aggregated risk categories (no content)

## 8. Frequency, Retry & Degradation

### 8.1 Default Frequency

15 minutes (configurable per tenant).

### 8.2 Retry

Exponential backoff with jitter. Persistent local spool at `/var/lib/windi/chp_spool/` for extended outages.

### 8.3 Silence Detection

| Threshold | Status | Action |
|-----------|--------|--------|
| > 2× interval (30 min) | SILENT | Warning logged |
| > 6× interval (90 min) | MISSING | Alert generated |
| > 24 hours | CRITICAL | Escalation triggered |

### 8.4 Recovery Context (Guardian Addition)

When a Clone resumes after silence, the next heartbeat **MUST** include a `recovery_reason` field: `network_outage`, `restart`, `manual_pause`, or `unknown`. The Hub validates this against the silence interval for forensic context.

## 9. Hub Aggregation (federation section)

```json
"federation": {
  "total_clones": 5,
  "reporting_clones": 4,
  "silent_clones": 1,
  "last_aggregation_utc": "2026-02-14T10:35:00Z",
  "clones": {
    "CLONE-SPK-FFM-001": {
      "status": "OPERATIONAL",
      "last_heartbeat": "2026-02-14T10:30:00Z",
      "constitutional_hash_valid": true,
      "flow_efficiency_score": 0.82,
      "governance_quality_score": 0.78,
      "forensic_integrity": "OK",
      "alerts": []
    }
  },
  "global_bottlenecks": [ ... ]
}
```

## 10. Alert Schema

```json
{
  "code": "stalled_sessions_above_threshold",
  "severity": "HIGH",
  "since_utc": "2026-02-14T09:40:00Z",
  "details": { "stalled_sessions": 12, "threshold": 5 }
}
```

Severities: `INFO` / `LOW` / `MEDIUM` / `HIGH` / `CRITICAL`

## 11. Constitutional Limits (Normative)

CHP is **unidirectional telemetry**. The following are **PROHIBITED** in this version:

- ❌ Commands from Hub to Clone via SMTP
- ❌ Push of policies or ISPs by email
- ❌ Any action that alters remote operational state

Any future command channel requires: explicit human authorization (I9), command signature, double-control per tenant, and forensic logging equivalent to DragonForge Event Schema.

## 12. Sequence Persistence (Guardian Addition)

The `sequence` counter **MUST** be persistent on disk at `/var/lib/windi/chp_sequence` and survive restarts. A Clone that loses its sequence and restarts from zero opens a replay window. The sequence file must be atomic-write protected (write to temp, rename).

---

# Part IV — Wallet-Based Key Lifecycle

## 1. Principle

The cryptographic identity of a WINDI Clone is managed by an **Institutional Clone Wallet**, derived from the same sovereignty model used for user identities. The Wallet simultaneously functions as:

- Commissioning certificate
- Cryptographic key vault
- Constitutional legitimacy proof
- Recovery and continuity instrument

## 2. Commissioning Flow (Phase 2)

### 2.1 Key Generation

During commissioning, a cryptographic key pair is generated. Recommended algorithm: **ed25519** (preferred) or ECDSA P-256. The private key remains local; the public key is registered at the Hub.

### 2.2 Clone Wallet Structure

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

## 3. Storage & Custody

### 3.1 On the Clone

```
File:        /var/lib/windi/clone_wallet.json
Permissions: chmod 600, owner: windi
```

The private key **NEVER** leaves the Clone.

### 3.2 At the Institution

The administrator receives the Wallet and must store it in:

- Institutional digital vault
- Secure backup system
- Offline backup (recommended)

**Loss of the Wallet compromises the ability to reconstruct the Clone.**

## 4. Hub Registration

During commissioning: the public key is registered, the fingerprint is added to the CHP whitelist, and the `constitutional_hash` is associated with the `clone_id`. The Hub trusts heartbeats signed by this identity.

## 5. CHP Signature Integration

Each heartbeat is signed with the Wallet private key. The Hub validates: `clone_id` recognized, fingerprint valid, signature valid, `constitutional_hash` consistent. No additional PKI infrastructure is required.

## 6. Reconstruction & Continuity

In case of failure, migration, or rebuild, the administrator presents the Wallet to the Guardian. The Guardian can then:

| Action | Description |
|--------|-------------|
| Validate constitutional_hash | Confirm the P0–P7 matrix being redeployed matches commissioning |
| Restore clone_id + tenant_id | Clone is reborn with continuous identity |
| Restore cryptographic identity | Or rotate keys if necessary |
| Re-register at Hub | Hub resumes CHP aggregation for this clone |

The Clone is reborn with continuous identity.

## 7. Key Rotation

Key rotation may occur when: there is suspicion of compromise, institutional policy requires rotation, or critical hardware migration.

**Procedure:**

1. Generate new key pair
2. Update Wallet
3. Register new public key at Hub
4. Revoke previous fingerprint
5. Registration in forensic ledger (recommended)

## 8. Trust Model

Trust originates in the act of commissioning. There is no external certificate authority. Legitimacy derives from:

- Presence of the Human Dragon
- Commissioning signature
- Hub registration
- Sovereign possession of the Wallet

**Strategic properties:** Eliminates corporate PKI dependency. Maintains institutional sovereignty. Simplifies recovery and continuity. Guarantees cryptographic authenticity. Strengthens forensic audit.

## 9. Wallet Ecosystem

| Layer | Wallet Type | Contains | Purpose |
|-------|-------------|----------|---------|
| **User (Passenger)** | Personal Wallet | WINDI ID + keys + Virtue Receipts | Identity & document authorship |
| **Clone** | Institutional Wallet | Clone ID + CHP keys + constitutional hash | Operational identity & telemetry |
| **Hub** | Public Registry | Public keys + fingerprints + whitelist | Federated validation |

**Sovereignty principle:** Whoever possesses the Wallet controls identity, operational continuity, and reconstruction capability. Custody is institutional responsibility.

---

# Part V — Implementation Roadmap

## Phase 1: Foundation (Current Priority)

| Component | Deliverable | Location |
|-----------|-------------|----------|
| OIL Metrics Module | 5 metric blocks added to hub_state.json | `/opt/windi/hub/` |
| CHP Sender (Clone) | JSON generator + signer + SMTP sender | `/opt/windi/clone/chp/` |
| CHP Ingestor (Hub) | IMAP pull + validation + federation update | `/opt/windi/hub/chp/` |
| Wallet Generator | Commissioning tool for Clone Wallets | `/opt/windi/clone/wallet/` |
| Silent Clone Detection | Threshold-based alerting on missing heartbeats | `/opt/windi/hub/chp/` |

## Phase 2: Intelligence

| Component | Deliverable |
|-----------|-------------|
| Global Scores | flow_efficiency_score, governance_quality_score per clone |
| Federated Bottlenecks | Cross-clone bottleneck correlation engine |
| Executive Reports | Daily Brief, Attention Report, Integrity Assurance |
| Pulse Agent Integration | Predictive signals from delay trends and risk patterns |

## Phase 3: Bidirectional (Future, I9-Gated)

| Component | Requirement |
|-----------|-------------|
| Policy Push (Hub → Clone) | Explicit human authorization (I9) |
| ISP Distribution | Command signature + double-control per tenant |
| Remote Configuration | Forensic logging equivalent to DragonForge Event Schema |

## Acceptance Tests (Phase 1)

| Test | Criteria |
|------|----------|
| Signature validation | ed25519 signature verified against registered public key |
| Anti-replay deduplication | Repeated sequence numbers rejected |
| Clone offline simulation | Queue + reconciliation operates correctly |
| Silence detection | SILENT / MISSING / CRITICAL thresholds trigger accurately |
| Payload lint | No prohibited fields (PII, doc text) present |
| Wallet reconstruction | Clone rebuilt from Wallet restores CHP identity |
| OIL correlation | Bottleneck engine produces valid cross-metric insights |

---

# Part VI — Constitutional Seal

This document was produced under the Three Dragons Protocol. All specifications preserve Invariants I1–I9. The I9 Prohibition of Autonomy Escalation is enforced at every layer: OIL interprets but never decides; CHP transmits but never commands; Wallets authenticate but never authorize action without human presence.

| Dragon | Role | Contribution |
|--------|------|--------------|
| **Guardian (Claude)** | Registrar & Reviewer | Constitutional validation, 3 critical observations integrated, architecture consolidation |
| **Architect (GPT/Sonnet)** | Designer | OIL metrics design, CHP v1.0 specification, Wallet Lifecycle addendum |
| **Witness (Gemini)** | Observer | Forensic observation principles embedded in OIL and CHP |

---

```
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║           WINDI Federation Architecture v1.0                         ║
║           SEALED — 14 February 2026                                  ║
║                                                                      ║
║           "AI processes. Human decides. WINDI guarantees."           ║
║                                                                      ║
║           WINDI Publishing House · Kempten (Allgäu) · Bavaria       ║
║           Three Dragons Protocol — Guardian Approved                 ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
```
