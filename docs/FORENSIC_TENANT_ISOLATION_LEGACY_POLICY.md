# WINDI Forensic Tenant Isolation — Legacy Policy

**Version:** 1.0.0
**Cutover Date:** 26 February 2026
**Status:** ACTIVE

---

## Executive Summary

WINDI implements **forensic-metadata tenant isolation**: a ledger-anchored segregation model where each evidence record contains an immutable `tenant_id` with cryptographic tamper protection (`metadata_hash`).

This document defines the policy for **legacy receipts** created before the cutover date.

---

## Policy Rules

### 1. Cutover Date

- **Date:** 2026-02-26 23:59:59 UTC (end of rollout day)
- **Timestamp:** `1772198399`
- **Enforcement:** All receipts created **after** this timestamp MUST have:
  - `metadata.tenant_id` (required)
  - `metadata.metadata_hash` (SHA-256, verifiable)

### 2. Legacy Receipts (Pre-Cutover)

Receipts created **before** the cutover date are classified as **legacy**:

| Characteristic | Behavior |
|----------------|----------|
| Missing `tenant_id` | **Exempt** — treated as single-tenant by default |
| Missing/invalid `metadata_hash` | **Exempt** — hash verification skipped |
| Cross-tenant conflicts | **Not exempt** — conflicts are always flagged |

### 3. Single-Tenant Default

Legacy receipts without explicit `tenant_id` are considered:
- **Single-tenant by default** (the system was single-tenant before rollout)
- **Not a compliance gap** (no multi-tenant risk existed)
- **Auditor-safe** (documented exemption policy)

---

## Verification Behavior

### Test Scripts

| Script | Legacy Behavior |
|--------|-----------------|
| `assert_tenant_presence.py` | Exempts pre-cutover receipts |
| `verify_tenant_isolation.py` | Exempts pre-cutover hash verification |
| `verify_tenant_boundary_events.py` | No exemptions (conflicts always fail) |
| `generate_auditor_multitenant_report.py` | Reports legacy counts separately |

### Flags

```bash
# Default: respect legacy allowlist
python3 verify_tenant_isolation.py

# Strict: fail on ANY missing tenant_id (ignores legacy)
python3 assert_tenant_presence.py --no-legacy

# Specific tenant
python3 verify_tenant_isolation.py barclays-pilot
```

---

## Legacy Allowlist

Located at: `/opt/windi/orchestrator/tests/legacy_receipts_allowlist.json`

```json
{
  "exempt_missing_tenant_id": ["hsbc-pilot", "pre-tenant-rollout"],
  "exempt_metadata_hash": ["hsbc-pilot"],
  "legacy_ledger_ids": ["VR-COM-d71f7d8bc81b"],
  "legacy_receipt_prefixes": ["TC-hsbc-pil-20260226-0015"]
}
```

### Adding Exemptions

To add a legacy receipt to the allowlist:

1. Add the ledger ID to `legacy_ledger_ids`
2. OR add the tenant ID to `exempt_missing_tenant_id`
3. Run verification to confirm exemption applies

---

## Optional Migration

Legacy receipts **can** be migrated to full compliance:

### Migration Process

1. **Backfill `tenant_id`**: Assign default tenant based on context
2. **Recompute `metadata_hash`**: Generate new SHA-256 hash
3. **Create migration receipt**: Log the migration in ledger
4. **Remove from allowlist**: Receipt now subject to full enforcement

### Migration Receipt Example

```json
{
  "doc_type": "doc",
  "doc_name": "[MIGRATION] Backfill tenant_id for legacy receipt",
  "metadata": {
    "receipt_type": "tenant_migration",
    "original_receipt_id": "VR-COM-d71f7d8bc81b",
    "migrated_tenant_id": "hsbc-pilot",
    "migration_reason": "Post-cutover compliance backfill",
    "migrated_at": "2026-02-27T10:00:00Z"
  }
}
```

---

## Audit Representation

When presenting to auditors:

1. **Clearly separate** legacy vs. post-cutover receipts
2. **Document exemption policy** (this file)
3. **Show zero conflicts** (cross-tenant violations)
4. **Demonstrate new receipts pass** all checks

### Sample Auditor Statement

> "Legacy receipts created before the multi-tenant rollout (2026-02-26) are exempt from `tenant_id` enforcement as the system was single-tenant at that time. All post-cutover receipts are subject to full tenant isolation verification including cryptographic hash validation. Zero cross-tenant conflicts have been detected."

---

## Regulatory Alignment

This policy aligns with:

| Standard | Requirement | Coverage |
|----------|-------------|----------|
| **EU AI Act** | Traceability | Legacy documented, new enforced |
| **GDPR** | Data segregation | Forensic isolation post-cutover |
| **BaFin MaRisk** | IT governance | Clear policy, audit trail |
| **ISO 27001** | Change management | Cutover documented |
| **SOC2** | Logical controls | Exemption policy defined |

---

## Contact

- **Policy Owner:** WINDI Governance Institute
- **Architect:** Three Dragons Protocol
- **Principle:** "AI processes. Human decides. WINDI guarantees."

---

*Document sealed: 26 February 2026*
