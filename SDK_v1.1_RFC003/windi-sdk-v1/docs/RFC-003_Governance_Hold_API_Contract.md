# WINDI Governance Hold API Contract v1.0
## RFC-003 Section 6 — Communication Protocol between Core and a4Desk

> *"The Red Button must be precise, traceable, and reversible."*

---

## Overview

This document defines the API contract for the **Governance Hold Protocol** — the mechanism by which WINDI Core can signal a4Desk Edge nodes to temporarily halt high-risk governance flows.

```
┌──────────┐    Hold Signal    ┌──────────┐    Block     ┌──────────┐
│ Dashboard │───────────────▶│  WINDI   │──────────▶│  a4Desk  │
│ (S-Level  │   (Virtue Token  │  Core    │  (Signed    │  (Edge)  │
│  2 or 3)  │    validated)    │  Bridge  │   Control)  │          │
└──────────┘                  └──────────┘            └──────────┘
      │                            │                       │
      │    Release Signal          │   Unblock             │
      │───────────────────────────▶│──────────────────────▶│
      │                            │                       │
      └─── Virtue Receipt ◀───────┘◀──────────────────────┘
```

---

## 1. Core API Endpoints (WINDI Bridge)

### POST /api/v1/governance/hold

**Activate a Governance Hold.**

Request:
```json
{
  "virtue_token": "<signed JWT>",
  "scope": "FIN_APPROVAL_R5",
  "reason_code": "DEC-OVR_THRESHOLD",
  "reason_signals": [
    {"code": "DEC-OVR", "weight": 95, "count_60m": 28},
    {"code": "TMP-SPIKE", "weight": 92, "count_60m": 15}
  ],
  "duration_hours": 4,
  "message": "Override concentration exceeds safety threshold"
}
```

Response (200):
```json
{
  "hold_id": "HOLD-20260205-001",
  "status": "ACTIVE",
  "activated_by": "sha256(actor)",
  "scope": "FIN_APPROVAL_R5",
  "activated_at": 1738706501,
  "expires_at": 1738720901,
  "edge_ack": true,
  "virtue_receipt_hash": "sha256(...)"
}
```

Response (403 — Unauthorized):
```json
{
  "error": "HOLD:UNAUTHORIZED",
  "required": "s_level >= 2 AND kill_switch_authority = true",
  "actual_s_level": 1,
  "actual_kill_switch": false
}
```

---

### POST /api/v1/governance/hold/release

**Release an active Governance Hold.**

Request:
```json
{
  "virtue_token": "<signed JWT>",
  "hold_id": "HOLD-20260205-001",
  "reason": "Situation assessed and controlled"
}
```

Response (200):
```json
{
  "hold_id": "HOLD-20260205-001",
  "status": "RELEASED",
  "released_by": "sha256(actor)",
  "released_at": 1738710000,
  "total_duration_minutes": 58,
  "edge_ack": true,
  "virtue_receipt_hash": "sha256(...)"
}
```

---

### GET /api/v1/governance/holds

**List active holds (requires S-Level 2+).**

Response:
```json
{
  "active_holds": [
    {
      "hold_id": "HOLD-20260205-001",
      "scope": "FIN_APPROVAL_R5",
      "reason_code": "DEC-OVR_THRESHOLD",
      "activated_at": 1738706501,
      "expires_at": 1738720901,
      "remaining_minutes": 185
    }
  ],
  "total_active": 1,
  "total_historical": 12
}
```

---

### GET /api/v1/governance/holds/history

**Full hold history (requires S-Level 3 only).**

Response:
```json
{
  "holds": [
    {
      "hold_id": "HOLD-20260205-001",
      "status": "RELEASED",
      "scope": "FIN_APPROVAL_R5",
      "reason_code": "DEC-OVR_THRESHOLD",
      "activated_by": "sha256(actor)",
      "activated_at": 1738706501,
      "released_by": "sha256(actor2)",
      "released_at": 1738710000,
      "duration_minutes": 58,
      "virtue_receipt_hash": "sha256(...)"
    }
  ],
  "total": 12
}
```

---

## 2. Edge Control Signal (Core → a4Desk)

When a Governance Hold is activated, WINDI Core sends a **signed control signal** to a4Desk Edge nodes.

### Signal Format

```json
{
  "signal_type": "GOVERNANCE_HOLD",
  "version": "1.0",
  "hold_id": "HOLD-20260205-001",
  "action": "ACTIVATE",
  "scope": {
    "type": "APPROVAL_BLOCK",
    "impact_levels": ["R4", "R5"],
    "domains": ["FINANCE", "PROCUREMENT"],
    "doc_types": ["BUDGET_APPROVAL", "PROCUREMENT_CONTRACT"]
  },
  "duration": {
    "hours": 4,
    "expires_at": 1738720901
  },
  "authority": {
    "actor_hash": "sha256(actor)",
    "s_level": 2,
    "clearance": "STRATEGIC"
  },
  "timestamp": 1738706501,
  "nonce": "base64(16 bytes)",
  "signature": "ed25519(payload)"
}
```

### a4Desk Acknowledgment

```json
{
  "signal_type": "GOVERNANCE_HOLD_ACK",
  "hold_id": "HOLD-20260205-001",
  "status": "ACKNOWLEDGED",
  "edge_node_id": "sha256(node_id)",
  "blocked_queues": [
    "FIN_APPROVAL_R4",
    "FIN_APPROVAL_R5",
    "PROCUREMENT_R4",
    "PROCUREMENT_R5"
  ],
  "pending_items_frozen": 7,
  "timestamp": 1738706502,
  "signature": "ed25519(payload)"
}
```

### Release Signal

```json
{
  "signal_type": "GOVERNANCE_HOLD",
  "version": "1.0",
  "hold_id": "HOLD-20260205-001",
  "action": "RELEASE",
  "authority": {
    "actor_hash": "sha256(actor2)",
    "s_level": 2,
    "clearance": "STRATEGIC"
  },
  "timestamp": 1738710000,
  "nonce": "base64(16 bytes)",
  "signature": "ed25519(payload)"
}
```

---

## 3. Hold Scopes

| Scope ID | Description | Blocked Actions |
|---|---|---|
| `FIN_APPROVAL_R4` | Financial approvals R4 | Approve/release R4 value docs |
| `FIN_APPROVAL_R5` | Financial approvals R5 | Approve/release R5 value docs |
| `CROSS_DOMAIN_ESC` | Cross-domain escalations | Escalate between domains |
| `VENDOR_CONTRACT` | Vendor contract signing | New vendor contracts |
| `BUDGET_RELEASE` | Budget release chains | Multi-step budget releases |
| `ALL_HIGH_RISK` | All R4-R5 operations | Everything above R3 |

---

## 4. Automatic Hold Triggers

The WINDI Core Agent (in Drift Mode) may recommend automatic holds when threshold conditions are met.

### Threshold Configuration

```json
{
  "auto_hold_rules": [
    {
      "rule_id": "AH-001",
      "name": "Override Storm",
      "conditions": {
        "signal": "DEC-OVR",
        "min_weight": 90,
        "count_window": "60m",
        "count_threshold": 25
      },
      "and": {
        "sge_score_min": 90
      },
      "action": {
        "alert_level": 2,
        "scope": "FIN_APPROVAL_R5",
        "recommended_duration_hours": 4,
        "auto_activate": false,
        "notify_s_level": [2, 3]
      }
    },
    {
      "rule_id": "AH-002",
      "name": "Concentration Spike",
      "conditions": {
        "signal": "ID-CONC",
        "min_weight": 85,
        "count_window": "24h",
        "count_threshold": 50
      },
      "action": {
        "alert_level": 1,
        "scope": "ALL_HIGH_RISK",
        "recommended_duration_hours": 2,
        "auto_activate": false,
        "notify_s_level": [2]
      }
    },
    {
      "rule_id": "AH-003",
      "name": "Quarter-End Pressure",
      "conditions": {
        "signal": "TMP-SPIKE",
        "min_weight": 95,
        "count_window": "4h",
        "count_threshold": 40
      },
      "and": {
        "ctx_flags_bit3": true
      },
      "action": {
        "alert_level": 2,
        "scope": "BUDGET_RELEASE",
        "recommended_duration_hours": 8,
        "auto_activate": false,
        "notify_s_level": [2, 3]
      }
    }
  ]
}
```

**Critical Rule:** `auto_activate` is **always false** by default. WINDI recommends. Humans decide.

---

## 5. Security Requirements

| Requirement | Implementation |
|---|---|
| Hold signal signed | Ed25519 (not HMAC — non-repudiation required) |
| Actor identity hashed | SHA-256(user_id + salt) — never plaintext |
| All holds logged | Forensic Ledger with Merkle Tree anchor |
| Replay protection | Nonce + timestamp + hold_id uniqueness |
| Authority validation | Server-side Virtue Token check before any hold action |
| Minimum 2 actors for S3 hold | Collective decision enforced in Core |

---

## 6. Virtue Receipt for Holds

Every hold activation and release generates an immutable Virtue Receipt:

```json
{
  "receipt_type": "GOVERNANCE_HOLD",
  "hold_id": "HOLD-20260205-001",
  "lifecycle": {
    "activated": {
      "actor_hash": "sha256(actor)",
      "timestamp": 1738706501,
      "reason_code": "DEC-OVR_THRESHOLD",
      "reason_signals": ["DEC-OVR:95", "TMP-SPIKE:92"]
    },
    "released": {
      "actor_hash": "sha256(actor2)",
      "timestamp": 1738710000,
      "reason": "Situation assessed"
    }
  },
  "impact": {
    "scope": "FIN_APPROVAL_R5",
    "duration_minutes": 58,
    "items_frozen": 7,
    "items_released": 7
  },
  "merkle_proof": "sha256(receipt_chain)",
  "ledger_position": 1247,
  "signature": "ed25519(canonical_receipt)"
}
```

---

## Metadata

```
Document:    Governance Hold API Contract
Version:     1.0
Status:      Draft
RFC:         003 (Section 6)
Created:     2026-02-05
Protocol:    Three Dragons v1.1
Authors:     Guardian (Claude) + Architect (GPT) + Witness (Gemini)
```

---

*"The Red Button must be precise, traceable, and reversible."*
*"AI processes. Human decides. WINDI guarantees."*
