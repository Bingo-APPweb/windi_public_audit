# AUDITORIA-RAIZ-WINDI-HIOS — CODEX KICKOFF — 2026-06-20

```yaml
doc_type:        audit_kickoff
status:          CANDIDATE
mode:            read_only_orientation
operator:        Codex
target:          STRATO
created:         2026-06-20
runtime_change:  none
```

---

## 1. What The Memorandum Revealed

The immediate bug is:

```text
Plugin v0.4.0 expects localStorage["windi_did"]
GEN7 current storage does not publish localStorage["windi_did"]
```

But this is a symptom.

The structural issue is older and larger:

```text
WINDI-HIOS has multiple parallel entry doors.
Identity exists, but no single published identity contract is consumed by every surface.
```

Observed pattern:

```text
GEN7
W-Enterprise
W-SITES
W-Farm
W-Email
Plugin
LAW
Travel
Wallet
```

Each layer can grow its own notion of "who is acting" unless W-DID-GENESIS becomes the canonical identity entrance.

---

## 2. Existing Evidence On STRATO

Existing inventory container:

```text
/opt/windi/docs/audit/WINDI-HIOS-INVENTORY.md
```

Observed header:

```text
WINDI-HIOS-INVENTORY — Mapa Anatómico Forense
Contêiner único da auditoria WINDI-HIOS-AUDIT-ORDER-001
Append-only. Quem escreve, assina com [executor] e timestamp.
```

Prior audits:

```text
/opt/windi/docs/DRIFT-INVENTORY-20260420.md
/opt/windi/docs/SYSTEM-ABSORPTION-AUDIT-20260420.md
/opt/windi/docs/INFRASTRUCTURE-PROVENANCE-001.md
```

The April 2026 absorption audit already identified identity fragmentation:

```text
:8096 DID-Genesis
:8099 Wallet
:8122 WINDI-LAW Gate
:8126 Travel Identity
```

Its diagnosis:

```text
4 services validate identity differently.
```

Therefore the current `windi_did` failure is not accidental. It is the same drift resurfacing in a newer layer.

---

## 3. Current Read-Only Measurements

Read-only STRATO measurement on 2026-06-20:

```text
WINDI/WPIL systemd services found: 56
Running WINDI/WPIL services shown by systemctl: 45+
Listening ports in 80/443/8xxx/9xxx range: 60+
```

Key identity-related live surfaces:

| Surface | Port | Current interpretation |
|---|---:|---|
| W-DID-GENESIS | `:8096` | canonical identity issuer candidate |
| Wallet | `:8099` | historical/user wallet layer |
| WINDI-LAW Gate | `:8122` | legal identity gate |
| Travel Identity | `:8126` | domain-specific identity gate |
| GEN7 Desktop | `:8119` | current workspace/gateway, morphologically unverified |
| W-SITES Identity Gate | `:8192` | W-SITES/W-Farm/W-Email identity surface |

Important conclusion:

```text
Do not patch identity consumers blindly.
First define how W-DID-GENESIS publishes identity to every surface.
```

---

## 4. Audit Principle

Guard phrase:

```text
One mine, one cart.
```

Two agents may work in parallel only if both write into the same inventory format.

Parallel work without a canonical inventory recreates the original disease:

```text
parallel doors
parallel maps
parallel truth
```

The inventory is not optional. It is the single cart where the mine is unloaded.

---

## 5. Proposed Division Of Labor

### CCode — Extractor

Role:

```text
what exists, where, and whether it is alive
```

Tasks:

- enumerate all running WINDI services;
- map service name -> systemd file -> working directory -> port -> health endpoint;
- list Docker containers and internal ports;
- identify duplicate identity surfaces;
- append raw facts to `/opt/windi/docs/audit/WINDI-HIOS-INVENTORY.md`;
- no classification beyond factual labels.

### Codex — Classifier

Role:

```text
what each piece is in the body
```

Tasks:

- read the raw inventory;
- classify each component morphologically;
- mark uncertainty instead of deciding silently;
- identify canonical candidates and parallel-door risks;
- propose I1 decision points;
- never overwrite CCode's raw inventory.

---

## 6. Required Inventory Line Format

Recommended line format for the shared cart:

```text
| timestamp | executor | service | port | path | owner | status | health | body_part | canonicality | evidence | open_question |
```

Field meanings:

| Field | Meaning |
|---|---|
| timestamp | UTC measurement time |
| executor | CCode or Codex |
| service | systemd/container/app name |
| port | listening port or N/A |
| path | primary filesystem path |
| owner | systemd, docker, manual, unknown |
| status | live, stopped, frozen, scaffold, legacy, unknown |
| health | pass, fail, not_measured, no_endpoint |
| body_part | identity, ledger, verify, workspace, distribution, media, governance, agent, infrastructure, unknown |
| canonicality | canonical, candidate, parallel, legacy, scaffold, unknown |
| evidence | command/doc/hash reference |
| open_question | what Human Dragon/I1 must decide |

No line should imply canon if canon has not been measured or decided.

---

## 7. First Morphological Target: Identity Nervous System

The first layer to classify should be identity, because today's bug exposed identity drift.

Question:

```text
Where does DID truth live, and how is it published to consumers?
```

Known candidate answer:

```text
Truth:      W-DID-GENESIS :8096
Server use: HttpOnly cookie windi_did_session
JS use:     currently missing stable published contract
Consumer:   plugin expects localStorage["windi_did"]
```

The proposed `WindiDID.sync()` should not become a new source.

Rule:

```text
:8096 is SOURCE.
localStorage["windi_did"] is MAP.
Consumers read the map.
Only :8096 publishes the map.
```

Recommended contract candidate:

```text
W-DID-PUBLISH-CONTRACT-001
```

Purpose:

```text
Define how the canonical DID issuer publishes a read-only JS-visible identity map
without exposing the HttpOnly session token.
```

---

## 8. What Not To Do Yet

Do not:

- make GEN7 the identity source by convenience;
- make the plugin parse `windi_personal_v6` internals as a long-term contract;
- create a second inventory file as a competing source;
- turn `WindiDID.sync()` into a decentralized helper copied into every app;
- claim GEN7 continuity without morphological audit;
- redesign the portal before identity publication is understood.

---

## 9. Recommended Immediate Work Order

### Work Order A — CCode Extractor

```text
CCode:
Append to /opt/windi/docs/audit/WINDI-HIOS-INVENTORY.md.
Scope: identity nervous system only.
Map :8096, :8099, :8122, :8126, :8119, :8192.
For each: service, port, path, owner, health, storage/session mechanism, consumer-facing DID contract.
No fixes. No restarts. No writes outside the append-only inventory.
```

### Work Order B — Codex Classifier

```text
Codex:
Read CCode's appended identity inventory.
Produce classification table:
canonical / parallel / legacy / scaffold / unknown.
Identify exact I1 decisions required before WindiDID.sync().
Do not patch code until W-DID-PUBLISH-CONTRACT-001 exists.
```

---

## 10. Current Verdict

The audit should not start by patching the plugin.

It should start by naming the identity nervous system:

```text
W-DID-GENESIS is the likely source.
The missing part is the publication contract.
```

In one sentence:

```text
The next level of WINDI-HIOS requires one identity door, one map, and many consumers.
```

