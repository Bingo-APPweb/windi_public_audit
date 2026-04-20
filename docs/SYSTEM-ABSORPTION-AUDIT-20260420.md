# WINDI System Absorption Audit
**Date:** 20 April 2026
**Author:** Human Dragon + Architect
**Purpose:** Map services by function, identify overlaps, define /seal absorption zones

---

## 1. INVENTORY — 58 Active Ports

### TRUNK (Forensic Core) — IMMUTABLE
| Port | Service | Function | Status |
|------|---------|----------|--------|
| :8101 | Forensic Ledger | Receipt storage, verification | **SEALED** |
| :8114 | Verify Public | Public verification API | **LIVE** |
| :8106 | Forensic Vault | Immutable file storage | **SEALED** |

### IDENTITY (DID Layer)
| Port | Service | Function | Status |
|------|---------|----------|--------|
| :8096 | W-DID-GENESIS | Sovereign identity tree | **LIVE** |
| :8099 | Wallet | Pioneer registry, DID binding | **LIVE** |
| :8122 | WINDI-LAW Gate | Identity + Dragon Shadow | **SEALED** |
| :8126 | Travel Identity | Travel-specific DID gate | **LIVE** |

### AGENTS (AI Processing)
| Port | Service | Function | Status |
|------|---------|----------|--------|
| :8091 | Sandbox Core | 9 Agent blueprints | **LIVE** |
| :8108 | Dragon Hub | AI routing (Mistral/Anthropic) | **LIVE** |
| :8119 | GEN7 Desktop | Sovereign editor gateway | **LIVE** |
| :8150 | W-Enterprise VERA | AI compliance secretary | **LIVE** |
| :8141 | Intent-CMD | Director-as-a-Service | **LIVE** |

### MEDIA (Video/Image Processing)
| Port | Service | Function | Status |
|------|---------|----------|--------|
| :8128 | VD-CUT + CLASSIFY + VISION + OBS | Video cutting, classification, forensics | **LIVE** |
| :8131 | VD-MASS | Batch video processing (MLT) | **LIVE** |
| :8132 | JMPG Server | Proof card rendering | **LIVE** |
| :8104 | JMPG Viewer | Proof card display | **LIVE** |

### GOVERNANCE (Compliance & Monitoring)
| Port | Service | Function | Status |
|------|---------|----------|--------|
| :8080 | Governance API | Core governance engine | **LIVE** |
| :8151 | W-LAB | Governance laboratory | **LIVE** |
| :8152 | W-COST | Cost intelligence | **LIVE** |
| :8180 | W-ACADEMY | Training & certification | **LIVE** |
| :8015 | W-ACTUARY | Actuarial intelligence | **LIVE** |

### INFRASTRUCTURE (Platform Services)
| Port | Service | Function | Status |
|------|---------|----------|--------|
| :8160 | W-CACHE | Verifiable cache (L2/L3) | **LIVE** |
| :8170 | Service Control | 29-service monitoring | **LIVE** |
| :8144 | W-SEC | Security sentinel | **SEALED** |
| :8200 | W-DEV-API | Developer API gateway | **LIVE** |

### DISTRIBUTION (Output Channels)
| Port | Service | Function | Status |
|------|---------|----------|--------|
| :8127 | Nomad Bot | Telegram interface | **LIVE** |
| :8142 | Fediverse | Mastodon + BlueSky | **LIVE** |
| :8143 | BIG-BRIDGE | HLS streaming | **LIVE** |
| :8133 | W-SOCIAL | Professional presence | **LIVE** |
| :8105 | Communiqué | Document distribution | **LIVE** |

### WORKSPACE (User-Facing)
| Port | Service | Function | Status |
|------|---------|----------|--------|
| :8119 | Desktop GEN7 | Main workspace | **LIVE** |
| :8153 | Travel Map | Berlin pitch map | **LIVE** |

---

## 2. OVERLAP ANALYSIS

### 🔴 HIGH OVERLAP — Candidates for Consolidation

#### A. Document Processing Pipeline
**Current fragmentation:**
- `:8103` Export Engine → PDF/PPTX export
- `:8104` JMPG Viewer → Proof card display
- `:8132` JMPG Server → Proof card generation
- `:8105` Communiqué → Document templates
- `:8106` Forensic Vault → File storage

**Problem:** 5 services touch "document output" without unified contract.

**Absorption target:** `/seal` endpoint consolidates:
- Intake (any format)
- Processing (normalize)
- Sealing (governance)
- Output (verified artifact)

#### B. Identity Validation
**Current fragmentation:**
- `:8096` DID-Genesis → Identity creation
- `:8099` Wallet → Pioneer binding
- `:8122` WINDI-LAW → Legal identity gate
- `:8126` Travel Identity → Travel-specific gate

**Problem:** 4 services validate identity differently.

**Absorption target:** Single `actor_did` validation in `/seal`:
- Call DID-Genesis once
- Cache result in request context
- All downstream uses same validation

#### C. Governance Classification
**Current fragmentation:**
- `:8091` Sandbox Core → SGE classification
- `:8150` VERA → EU AI Act compliance
- `:8080` Governance API → Generic governance

**Problem:** 3 services classify content with different schemas.

**Absorption target:** `/seal` Phase 2 (Sense) unifies:
- SGE score (0-100)
- ISP profile (regulatory)
- Governance level (LOW/MEDIUM/HIGH)

---

## 3. GAP ANALYSIS — What /seal Needs

### ✅ EXISTS — Can Reuse
| Need | Current Service | Port |
|------|-----------------|------|
| Hash storage | Forensic Ledger | :8101 |
| Public verify | Verify Public | :8114 |
| File storage | Forensic Vault | :8106 |
| DID validation | DID-Genesis | :8096 |
| AI classification | VERA | :8150 |
| QR generation | JMPG Server | :8132 |

### ❌ MISSING — Must Build
| Need | Description | Priority |
|------|-------------|----------|
| **Normalizer** | Convert PDF/DOCX/PPTX/HTML → internal format | P0 |
| **Adjudicator** | Apply I1/I9/I11/I14 rules, decide SEALED/REFUSED | P0 |
| **Seal Bundle Builder** | Generate sealed artifact + manifest + QR | P0 |
| **Refusal Receipts** | Store governance refusals as verifiable events | P1 |
| **Provenance Detector** | Identify AI-generated vs human-created content | P1 |
| **Semantic Diff** | Compare sealed vs source for drift detection | P2 |

---

## 4. ABSORPTION ZONES

### Zone A — INTAKE (New)
**Responsibility:** Accept artifacts from any source
**Absorbs:** Nothing (new capability)
**Creates:**
- `POST /api/seal` (multipart)
- `POST /api/seal/submit` (JSON)

### Zone B — NORMALIZE (New)
**Responsibility:** Convert to internal format
**Absorbs:**
- Export Engine (:8103) text extraction
- JMPG Viewer (:8104) format detection
**Creates:**
- Internal `NormalizedArtifact` schema
- Format-specific parsers (PDF, DOCX, PPTX, HTML, SVG)

### Zone C — SENSE (Consolidate)
**Responsibility:** Classify and detect
**Absorbs:**
- SGE scoring from Sandbox Core (:8091)
- ISP profiles from VERA (:8150)
- Provenance hints from Vision (:8128)
**Creates:**
- Unified `SenseResult` with SGE + ISP + Provenance

### Zone D — ADJUDICATE (New)
**Responsibility:** Apply invariants, decide outcome
**Absorbs:** Nothing (new capability)
**Creates:**
- Decision engine with I1/I9/I11/I14 rules
- Status: SEALED | SEALED_WITH_WARNINGS | REFUSED | NEEDS_OVERSIGHT

### Zone E — BUILD (Consolidate)
**Responsibility:** Generate sealed artifacts
**Absorbs:**
- JMPG Server (:8132) proof card generation
- Forensic Vault (:8106) storage
- Ledger (:8101) receipt creation
**Creates:**
- Unified seal bundle (artifact + manifest + QR + verify URL)

### Zone F — DELIVER (Consolidate)
**Responsibility:** Return sealed package
**Absorbs:**
- Communiqué (:8105) delivery formatting
- Distribution Engine (:8091) channel routing
**Creates:**
- Standard response schema
- Optional channel delivery (Telegram, email, etc.)

---

## 5. IMPLEMENTATION RECOMMENDATION

### Phase 1 — Core /seal (2 weeks)
```
Zone A (Intake) + Zone D (Adjudicate) + Zone E (Build)
```
- Accept PDF/DOCX
- Validate DID via :8096
- Apply I9 gate
- Store in Ledger :8101
- Return verify URL

### Phase 2 — Normalization (1 week)
```
Zone B (Normalize)
```
- Add PPTX/HTML/SVG support
- Extract text/structure
- Internal format standardization

### Phase 3 — Sense Integration (1 week)
```
Zone C (Sense)
```
- Integrate SGE from :8091
- Integrate ISP from :8150
- Unified classification

### Phase 4 — Full Package (1 week)
```
Zone F (Deliver)
```
- QR generation
- Manifest attachment
- Channel delivery options

---

## 6. SERVICE DISPOSITION MAP

### 🟢 KEEP AS-IS (Core Infrastructure)
- `:8101` Forensic Ledger — TRUNK, immutable
- `:8114` Verify Public — Public interface
- `:8096` DID-Genesis — Identity source of truth
- `:8108` Dragon Hub — AI routing
- `:8144` W-SEC — Security monitoring

### 🟡 ABSORB PARTIALLY (Reuse Components)
- `:8091` Sandbox Core → SGE scoring moves to /seal
- `:8150` VERA → ISP profiles move to /seal
- `:8132` JMPG Server → QR generation moves to /seal
- `:8128` VD-CUT → Provenance detection moves to /seal

### 🟠 DEPRECATE AFTER /seal (Phase 2+)
- `:8103` Export Engine → Replaced by /seal output
- `:8104` JMPG Viewer → Merged into Verify Public
- `:8105` Communiqué → Delivery moves to /seal Zone F

### 🔴 EVALUATE (Potential Redundancy)
- `:8080` Governance API — Overlap with :8150 VERA?
- `:8126` Travel Identity — Duplicate of :8096?
- `:8122` WINDI-LAW Gate — Subset of :8096?

---

## 7. /seal CANONICAL LOCATION

**Recommended Port:** `:8102` (currently Sentinel-Law, can migrate)

**Or new port:** `:8145` (was expected for Verify Public, now free)

**Endpoints:**
```
POST /api/seal              → Multipart upload
POST /api/seal/submit       → JSON submission
GET  /api/seal/{id}         → Seal status
GET  /api/seal/{id}/bundle  → Download sealed package
```

**nginx route:**
```nginx
location ^~ /seal/ {
    proxy_pass http://windi_seal/;
    proxy_http_version 1.1;
    client_max_body_size 100m;
}
```

---

## 8. CONCLUSION

**Current state:** 58 ports, ~35 distinct services, significant overlap in document/identity/governance layers.

**After /seal absorption:**
- **Consolidated:** 5-7 services absorbed into /seal pipeline
- **Deprecated:** 3 services replaced entirely
- **Simplified:** Single entry point for "artifact → verified state"

**Strategic value:**
> Every external integration (SDK, MCP, partner) talks to ONE endpoint.
> Internal complexity hidden behind constitutional adjudication.

---

*WINDI Publishing House · 20 April 2026*
*"The seal endpoint converts digital outputs into adjudicated, independently verifiable states."*
