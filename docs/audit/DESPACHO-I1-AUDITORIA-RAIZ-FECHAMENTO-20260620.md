# DESPACHO-I1-AUDITORIA-RAIZ-FECHAMENTO-20260620

Status: I1 RATIFICATION DISPATCH CANDIDATE / not sealed / no Ledger receipt generated here
Date: 2026-06-20
Subject: Root audit closure decisions for `WINDI-HIOS-INVENTORY.md`

## 1. Scope

This dispatch records the short closing decisions for the root audit cycle.

It does not edit:

```text
/opt/windi/docs/audit/WINDI-HIOS-INVENTORY.md
CLAUDE.md
systemd
nginx
Ledger
Verify
```

It only records the intended I1 ratification posture over the measured evidence.

## 2. Decision 1 — Closure Sidecar Accepted

I1 accepts the sidecar closure method as the correct mechanism for audit closure.

Canonical closure target:

```text
/opt/windi/docs/audit/WINDI-HIOS-INVENTORY.md
```

Current accepted target hash:

```text
4c219002e60a5ea587a810d1058c6067dabf1eb970b6d1a9f7dce5441072215b
```

Closure sidecar:

```text
/opt/windi/docs/audit/AUDITORIA-RAIZ-INVENTORY-CLOSURE-20260620.md
```

Closure sidecar hash:

```text
556ecae8a684958c4332ac9abec6a53f3a36f40207b8ca96fe2cbcb360e9debd
```

Ratified rule:

```text
finish target
measure target
write external closure
do not touch target under that closure
```

The previous inline-final-hash pattern is rejected for forensic closure because writing the hash into the target changes the target.

## 3. Decision 2 — ENGINE Classification Corrected

I1 accepts the correction:

```text
ENGINE :8080 is not ANDAIME.
ENGINE :8080 is OSSO.
```

Evidence measured on STRATO:

```text
windi-governance.service
active/running
enabled
running since 2026-04-27
Core Constitutional Engine (:8080)
/health returns status ok, protocol three-dragons, i9 active
```

Reason:

```text
A stable, enabled, systemd-owned governance service running for nearly two months is not scaffolding.
It is part of the constitutional skeleton.
```

## 4. Decision 3 — ENGINE-ALT Deferred

I1 does not ratify ENGINE-ALT `:8111` as obsolete or scaffolding.

Provisional state:

```text
ENGINE-ALT :8111
status: live
process: dragon_chat_service.py
version: 2.6.0
classification: CORTEX-candidate / parallel
decision: I1 REVIEW PENDING
```

Reason:

```text
The shared directory with ENGINE :8080 is a topology smell, not proof of obsolescence.
```

## 5. Decision 4 — Inventory Frozen Under Sidecar

The inventory is frozen under the sidecar hash:

```text
4c219002e60a5ea587a810d1058c6067dabf1eb970b6d1a9f7dce5441072215b
```

If `WINDI-HIOS-INVENTORY.md` is edited again, this freeze expires and a new sidecar closure must be measured.

Earlier hash values from the sequencing error are historical traces only. They are not current closure truth.

## 6. Doctrine Candidate Deferred

The audit revealed a doctrine-level problem:

```text
The institutional map diverged from the operational territory.
```

Candidate doctrine:

```text
METODO-MAPA-VERDADE-001
```

Core sentence:

```text
The map must not outrun the territory.
A service may be described as intended, designed, candidate, installed, or live.
Only a measured listening service with a valid health route, or an explicit state receipt, may be called LIVE.
```

I1 decision:

```text
Do not decide this doctrine at the end of this audit cycle.
Open a separate doctrine session for METODO-MAPA-VERDADE-001.
```

## 7. Closing

This dispatch closes the immediate root-audit cleanup posture:

```text
sidecar accepted
inline hash rejected
ENGINE corrected to OSSO
ENGINE-ALT deferred
inventory frozen under 4c219002...
map-truth doctrine deferred to its own session
```

No seal is claimed here.
No Ledger receipt is claimed here.
This document is ready for I1 review and later formalization if desired.
