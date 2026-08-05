# WINDI Git Hooks — Witness Enforcement

## Purpose

These hooks enforce the principle: **every policy assertion needs a nameable witness**.

A runtime assertion in a policy document without an accompanying AC reference or
Testemunhas section is DOCUMENTADO≠IMPLEMENTADO — the policy promises what the
code doesn't do.

## Installation

### Option A: Symlink (per-repo)

```bash
# From repository root
ln -sf ../../scripts/hooks/pre-commit .git/hooks/pre-commit
```

### Option B: core.hooksPath (recommended for multiple repos)

```bash
git config core.hooksPath scripts/hooks
```

To apply to both repos:
```bash
cd /home/windi && git config core.hooksPath scripts/hooks
cd /opt/windi && ln -sf /home/windi/scripts/hooks/pre-commit .git/hooks/pre-commit
```

## Components

| Script | Purpose |
|--------|---------|
| `pre-commit` | **Prevention** — blocks commits with policy content lacking witnesses |
| `audit-policy-witnesses.sh` | **Detection** — finds bypasses in committed history |

Prevention + Detection = complete control.

## Self-Test

The pre-commit hook includes a self-test using the historical §PG commit as
negative control:

```bash
./pre-commit --selftest
```

Expected output: 4 tests passed.

If Test 1 (§PG without witnesses) does not fail, the hook is miscalibrated.

## Scope (HOOK-AC4)

On day 1, only these patterns are checked:
- `*POLICY*`
- `*DOUTRINA*`
- `*-spec*`
- `W-*-001*`
- `*CANONICAL*`

Scope expands after 2 weeks without false positives.

## Bypass

The `--no-verify` flag cannot be blocked, by design. Use it sparingly:

```bash
git commit --no-verify -m "Emergency commit"
```

Bypasses are detectable via the audit script:
```bash
./audit-policy-witnesses.sh --since=20
```

## Reference

- **Incident:** W-INCIDENTE-FRONTEIRA-002
- **Principle:** REPRESENTADO≠OPERANTE
- **Date:** 2026-08-06 · Kempten, Bavaria

---

*"A hook that gives false positives teaches everyone to use --no-verify."*
