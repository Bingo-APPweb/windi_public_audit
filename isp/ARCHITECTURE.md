# WINDI ISP – Governance Level Architecture

## Purpose
Risk-based document governance system that applies proportional security
controls depending on document classification.

## Core Principle
> "AI processes. Human decides. WINDI guarantees proportionally."

---

## Governance Levels

| Level  | Name                | Watermark | Ledger   | Use Case                          |
|--------|---------------------|-----------|----------|-----------------------------------|
| HIGH   | Forensic Full       | Visible   | Complete | Banking, legal, regulatory        |
| MEDIUM | Controlled Compact  | Invisible | Compact  | Internal technical/important docs |
| LOW    | Operational Light   | None      | Minimal  | Forms, logistics, checklists      |

---

## Configuration Structure
```
/opt/windi/isp/
├── governance_levels.json   → Global security behavior definitions
├── isp_loader.py            → Policy engine (decision logic)
├── ARCHITECTURE.md          → This file
├── README.md                → Usage documentation
├── _base/profile.json       → Template for new ISPs
└── <org>/
    ├── profile.json         → Organization-level defaults
    ├── styles.css           → Visual identity
    └── assets/              → Logos, images
```

---

## Decision Flow

1. Document generated with `institutional_profile` in metadata
2. ISP loads organization profile.json
3. ISP reads `governance.default_level` (or maps document_type)
4. ISP applies rules from governance_levels.json
5. Watermark applied only if `watermark_visible: true`

---

## Key Functions (isp_loader.py)

- `get_governance_config(profile_id, doc_type)` → Returns full config
- `should_apply_watermark(profile_id, doc_type)` → Boolean check

---

## Document Type Mapping

| Document Type      | Level  |
|--------------------|--------|
| contract           | HIGH   |
| financial_report   | HIGH   |
| legal_document     | HIGH   |
| technical_order    | MEDIUM |
| maintenance_report | MEDIUM |
| transport_form     | LOW    |
| material_request   | LOW    |
| checklist          | LOW    |

---

## Version History

- v1.0.0 (2026-02-01): Initial governance levels implementation
- Deutsche Bahn AG as first institutional profile

---

## Authors

WINDI Publishing House
Chief Governance Officer: Jober Mögele Correa

*AI processes. Human decides. WINDI guarantees.*
