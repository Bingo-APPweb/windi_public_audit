# AUDITORIA-RAIZ-RATIFICACAO-I11-20260620

Status: RATIFICATION CANDIDATE / not sealed / no Ledger receipt generated here
Date: 2026-06-20
Executor: Codex
Scope: WINDI-HIOS root audit, post CODEX-B classification review

## 0. Purpose

This document separates:

1. findings that are solid enough to inherit,
2. findings that require I1 review before ratification,
3. the hash/closure correction required by I11,
4. the doctrine-level consequence of the audit.

It does not rewrite `WINDI-HIOS-INVENTORY.md`.
It does not edit `CLAUDE.md`.
It does not generate a Ledger receipt.

## 1. Hash Closure Correction

The audit text reported a sequencing problem:

```text
pre-CODEX hash: 8886d36c...
declared "final" hash: 35d516e4...
later measured hash: e4b3d2a5...
```

This is forensically unsafe because a target file cannot reliably contain its own final hash after further edits. Writing a closing hash into the target changes the target.

Current STRATO measurement of the inventory target:

```text
target: /opt/windi/docs/audit/WINDI-HIOS-INVENTORY.md
sha256: 4c219002e60a5ea587a810d1058c6067dabf1eb970b6d1a9f7dce5441072215b
lines: 490
size: 42294 bytes
mtime: 2026-06-20 14:40:16.197717591 +0200
```

Closure sidecar created:

```text
/opt/windi/docs/audit/AUDITORIA-RAIZ-INVENTORY-CLOSURE-20260620.md
sha256: 556ecae8a684958c4332ac9abec6a53f3a36f40207b8ca96fe2cbcb360e9debd
```

Ratification note:

```text
finish target
measure target
write external closure
do not touch target under that closure
```

If the inventory is edited again, this closure expires and a new sidecar must be created.

## 2. Solid Findings To Inherit

### 2.1 Chain Of Custody At Entry

The pre-CODEX hash reported for the inventory input matched the CCode handoff:

```text
8886d36c...
```

Interpretation: the input chain was intact at handoff.

### 2.2 `CLAUDE.md` Contains Live-State Drift

Measured on STRATO:

```text
/home/windi/CLAUDE.md and /opt/windi/CLAUDE.md declare LIVE:
W-UDB-001     :8140
W-LAB-001     :8151
W-CACHE-001   :8160
W-ACADEMY-001 :8180
```

Current port measurement:

```text
8140 ABSENT
8151 ABSENT
8160 ABSENT
8180 ABSENT
```

Interpretation: the institutional map declares live services that are not listening on the measured territory.

This is a P0 map-truth finding, not merely four dead ports.

### 2.3 Services That Changed State Without A Known Receipt

April health matrix recorded `:8096` as `404`.
June measurement shows `:8096` listening and functioning as DID Genesis source.

The audit also identified the same class of temporal drift for:

```text
8127
8128
8129
8132
8141
8142
8200
```

Current measurement confirms these ports are listening:

```text
8096 LISTEN
8127 LISTEN
8128 LISTEN
8129 LISTEN
8132 LISTEN
8141 LISTEN
8142 LISTEN
8200 LISTEN
```

Interpretation: these are not necessarily wrong services. The failure is missing provenance of activation or recovery. The map and the Ledger do not yet explain when and how they changed state.

### 2.4 Body Anatomy Exists

The audit produced the first usable body anatomy:

```text
OSSO
NERVO
MUSCULO
CORTEX
ANDAIME
?
```

Interpretation: the body lexicon is usable, but individual classifications still require ratification where evidence is ambiguous.

## 3. Findings Requiring I1 Review

### 3.1 ENGINE `:8080`

Earlier classification in the inventory:

```text
ENGINE :8080 -> ANDAIME
```

Later classification in the inventory:

```text
ENGINE :8080 -> OSSO
```

Current STRATO evidence:

```text
unit: windi-governance.service
loaded: yes
enabled: yes
active: active (running)
uptime: since 2026-04-27
description: WINDI Governance API v1.0.0 - Core Constitutional Engine (:8080)
process: /usr/bin/python3 /opt/windi/engine/windi_governance_api.py
health: /health returns status ok, service windi-governance, protocol three-dragons, i9 active
```

Recommendation:

```text
ENGINE :8080 should not be ratified as ANDAIME.
Recommended body_part: OSSO
Recommended canonicality: canonical or core, pending I1 wording
```

Reason: a stable systemd-owned governance service active for nearly two months is not scaffolding.

### 3.2 ENGINE-ALT `:8111`

Current STRATO evidence:

```text
port: 8111 LISTEN
process: /usr/bin/python3 /opt/windi/engine/dragon_chat_service.py
cwd: /opt/windi/engine
health: status healthy, service dragon-chat, version 2.6.0
```

Recommendation:

```text
Do not mark as obsolete without I1 review.
Recommended provisional classification: CORTEX or ? / parallel
Open question: duplicate engine, cognitive surface, or legitimate parallel role?
```

Reason: it is live, healthy, and appears semantically cognitive. The shared directory with `:8080` is a topology smell, not proof of scaffolding.

## 4. Doctrine-Level Finding

The audit's main discovery is not only:

```text
some services are dead
some services healed without receipts
some classifications are wrong
```

The larger discovery is:

```text
the institutional map diverged from the operational territory
```

Consequences:

1. `CLAUDE.md` cannot currently be treated as a perfect source of live-state truth.
2. Service state declarations need measured provenance.
3. Live/dead status should be generated or periodically audited from territory, not carried indefinitely as static memory.
4. Every future "LIVE" claim should have either a recent measurement or a receipt-backed state transition.

Candidate doctrine:

```text
METODO-MAPA-VERDADE-001

The map must not outrun the territory.
A service may be described as intended, designed, candidate, installed, or live.
Only a measured listening service with a valid health route, or an explicit state receipt, may be called LIVE.
```

## 5. Ratification Table

| Item | Status | Ratification |
| --- | --- | --- |
| Input chain hash `8886d36c...` | observed from audit context | ACCEPT |
| Inline final hash pattern | forensically unsafe | REJECT PATTERN |
| Sidecar closure pattern | created and measured | ACCEPT |
| `CLAUDE.md` declares dead services LIVE | measured | ACCEPT P0 |
| `:8096` April 404 -> June live without receipt | measured from April/June evidence | ACCEPT P0 |
| Seven additional 404/live drift ports | measured as listening now | ACCEPT AS OPEN PROVENANCE |
| ENGINE `:8080` as ANDAIME | contradicted by evidence | REJECT / RECLASSIFY |
| ENGINE `:8080` as OSSO | supported by evidence | RECOMMEND I1 RATIFICATION |
| ENGINE-ALT `:8111` as obsolete/ANDAIME | not supported | REJECT WITHOUT MORE EVIDENCE |
| ENGINE-ALT `:8111` as CORTEX or parallel | plausible | I1 REVIEW |
| METODO-MAPA-VERDADE-001 | doctrine candidate | I1 SESSION NEEDED |

## 6. Recommended Next Order

1. Ratify the closure sidecar as the correct hash-closing mechanism.
2. Mark the old inline-final-hash method as invalid for audit closure.
3. Correct the human interpretation of ENGINE `:8080` from `ANDAIME` to `OSSO`.
4. Leave ENGINE-ALT `:8111` as `? / parallel` or `CORTEX candidate` until reviewed.
5. Open a separate `METODO-MAPA-VERDADE-001` decision session before editing `CLAUDE.md`.
6. Do not patch service maps by hand until the method for live-state truth is decided.

## 7. Closing Statement

The audit did not merely find dead ports.

It proved that the memory map of WINDI-HIOS can diverge from the territory it claims to describe.

This is not a failure of the project. It is the discovery that makes the next level possible:

```text
one territory
one measured map
one canonical identity door
many consumers
```

