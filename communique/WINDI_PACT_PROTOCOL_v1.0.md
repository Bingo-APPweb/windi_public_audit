# WINDI PACT Protocol v1.0

## Governance Framework for Institutional Communication Intelligence

---

**Version:** 1.0.0
**Status:** SEALED — Three Dragons Council
**Date:** 2026-02-19
**Authority:** WINDI Publishing House — Three Dragons Council
**Authors:**
- **Guardian (Claude):** Protection Layer & Governance Architecture
- **Architect (GPT):** Structural Design & Pipeline Engineering
- **Witness (Gemini):** Validation, Observation & Integrity Seal
- **Human Dragon (Jober Mögele Correa):** Chief Governance Officer — Final Authority

**Principle:**
> *"AI processes. Human decides. WINDI guarantees."*

**Hash Integrity:** `c97acb656ca5b02e39d57a3d9d8e6c7299e5d4b2029f883d51ac3a044ee08605`

---

## TABLE OF CONTENTS

1. [Section I — The P-A-C-T Philosophy](#section-i--the-p-a-c-t-philosophy)
2. [Section II — Input Taxonomy: EVENT vs ERROR vs INCIDENT](#section-ii--input-taxonomy)
3. [Section III — The STHP Pipeline](#section-iii--the-sthp-pipeline)
4. [Section IV — Resolution Matrix: Scoring, Gates & Quarantine](#section-iv--resolution-matrix)
5. [Section V — ISP Template Specifications](#section-v--isp-template-specifications)
6. [Section VI — Context Detector](#section-vi--context-detector)
7. [Section VII — Multimedia Aggregator](#section-vii--multimedia-aggregator)
8. [Section VIII — Feed Publisher](#section-viii--feed-publisher)
9. [Section IX — Operational Intelligence Layer](#section-ix--operational-intelligence-layer)
10. [Section X — Legal Framework & Data Protection](#section-x--legal-framework--data-protection)
11. [Section XI — Retraction, Correction & Versioning Policy](#section-xi--retraction-correction--versioning-policy)
12. [Section XII — Sealing & Document Versioning](#section-xii--sealing--document-versioning)

---

# SECTION I — The P-A-C-T Philosophy

## The Moral Contract

PACT is not an acronym of convenience. It is a binding contract between the WINDI system and every human who receives its output. Every Communiqué, every feed item, every published document must honor all four dimensions simultaneously. Violating one dimension invalidates the entire output.

### P — Preservation

Facts are preserved. Opinions are removed. The original signal is protected from distortion.

**Rules:**
- Observable facts survive the pipeline intact.
- Claims are labeled as claims, never elevated to facts.
- Opinions are extracted and logged but never published as institutional content.
- Source attribution is mandatory for every factual assertion.
- When facts conflict, both versions are presented with their sources.

### A — Accountability

Every decision has a trail. Every transformation is logged. Every human override is recorded.

**Rules:**
- The audit trail records: what changed, why it changed, who (or what) changed it.
- Normalizations (stigma removal, certainty softening) are logged with before/after.
- Human overrides are recorded with timestamp, identity, and justification.
- The Forensic Ledger receives a receipt for every published Communiqué.
- No transformation occurs without a traceable reason.

### C — Classification

The system knows what something IS and what it is NOT. Classification includes the decision of whether to publish at all.

**Rules:**
- Every input is classified before entering the pipeline (EVENT / ERROR / INCIDENT / UNCLASSIFIABLE).
- Only EVENTs proceed to the STHP pipeline for potential publication.
- ERRORs are logged internally and never generate public output.
- INCIDENTs may generate internal Communiqués but require human confirmation.
- UNCLASSIFIABLE inputs enter Quarantine — the system does not guess.
- Content is classified by domain, risk level, sensitivity, and appropriate ISP Template.

### T — Trust

Verification is explicit. Dignity is non-negotiable. Due process is referenced when applicable.

**Rules:**
- Every piece of evidence carries a verification status: VERIFIED / UNDER_REVIEW / UNVERIFIED.
- External media (social networks, forums) defaults to UNVERIFIED.
- Human dignity is preserved regardless of the subject's legal status, nationality, or actions.
- Legal contexts include a due process reference.
- The system never affirms guilt, illegality, or criminal intent without official verified sources.
- The reader must always know what has been verified and what has not.

---

# SECTION II — Input Taxonomy

## EVENT vs ERROR vs INCIDENT

Before any content enters the STHP pipeline, it must pass through the **First Gate**: input classification. This gate determines whether the input represents something that happened in the world, something that failed in the system, or something that requires special handling.

### EVENT — External Occurrence

**Definition:** Something happened in the external world that may warrant institutional communication.

**Characteristics:**
- Origin: external to WINDI infrastructure
- Examples: news event, corporate announcement, legal proceeding, incident report
- Action: enters STHP pipeline for processing
- Output: may become a published Communiqué

### ERROR — Internal System Failure

**Definition:** Something failed within the WINDI infrastructure itself.

**Characteristics:**
- Origin: internal to WINDI systems
- Examples: template not found, service timeout, pipeline crash, hash mismatch
- Action: logged to Sentinel, triggers diagnostics, NEVER enters publication pipeline
- Output: internal log entry only

**Critical Rule:**
> An ERROR must never generate a public Communiqué. The system failing is not news — it is maintenance.

**Subtypes:**
- `TEMPLATE_REGISTRY_FAILURE` — requested template not found in core
- `PIPELINE_EXECUTION_FAILURE` — processing step crashed or timed out
- `INTEGRITY_FAILURE` — hash mismatch, ledger inconsistency
- `SERVICE_UNAVAILABILITY` — port/service not responding
- `CONFIGURATION_ERROR` — malformed config, missing parameters

### INCIDENT — Operational Event with External Impact

**Definition:** Something happened within or related to the system that may have external implications.

**Characteristics:**
- Origin: internal but with potential external impact
- Examples: data breach detection, service degradation affecting users, governance violation detected
- Action: generates INTERNAL Communiqué only, requires human confirmation before any external communication
- Output: internal report with ISP-INCIDENT template, escalation to Human Dragon

### UNCLASSIFIABLE — The Quarantine State

**Definition:** The system cannot determine with sufficient confidence what the input represents.

**Characteristics:**
- Origin: ambiguous
- Action: placed in Quarantine, human notified for manual classification
- Output: none until human classifies

**The Quarantine Principle:**
> *"Quarantine is not failure. It is the system's humility — the recognition that reality's complexity has exceeded the model."*
> — Witness (Gemini)

---

## First Gate Decision Tree

```
INPUT received
│
├─ Can the system classify this input? (confidence ≥ 70%)
│   │
│   ├─ YES → What type?
│   │   │
│   │   ├─ ERROR (internal system failure)
│   │   │   → LOG to Sentinel
│   │   │   → Trigger diagnostics
│   │   │   → DO NOT PUBLISH
│   │   │   → STOP
│   │   │
│   │   ├─ INCIDENT (internal with external impact)
│   │   │   → Generate INTERNAL Communiqué draft
│   │   │   → ASK_HUMAN for review
│   │   │   → Human decides: publish internally / escalate / archive
│   │   │   → STOP (until human decides)
│   │   │
│   │   └─ EVENT (external occurrence)
│   │       → Proceed to STHP Pipeline (Section III)
│   │
│   └─ NO → QUARANTINE
│       → Notify human
│       → Wait for manual classification
│       → STOP (until human classifies)
```

---

# SECTION III — The STHP Pipeline

## Sensitive Topic Handling Protocol

The STHP defines how an EVENT (classified in Section II) is transformed from raw input into a governed, institutional Communiqué. This pipeline applies to ALL content, with enhanced scrutiny for sensitive topics.

### Definition of Sensitive Topics

Content is flagged as "sensitive" if it involves any of these domains:
- Immigration / deportation / detention
- Criminal justice / accusations / imprisonment
- Health / medical data (incl. Art.9 GDPR special categories)
- Minors / children
- Violence / threats / harassment
- Systemic finance / market stability
- Identity / defamation / reputation
- Discrimination (race, nationality, religion, gender, etc.)

### Pipeline Stages

#### Stage A — Domain & Risk Classification

**Input:** Raw text + metadata from First Gate
**Process:**
- Detect primary domain (immigration, finance, health, etc.)
- Detect jurisdiction (EU, USA, BR, etc.)
- Assess risk level (R1-R5)
- Flag sensitive domains

**Output:**
```json
{
  "domain": "immigration",
  "jurisdiction": "USA",
  "risk_level": "R4",
  "sensitive": true,
  "language": "en"
}
```

#### Stage B — Tone & Bias Detection

**Input:** Text content
**Process:**
- Detect stigmatizing terms ("illegal", "criminal alien", etc.)
- Detect punitive calls-to-action ("deport now", "seize assets")
- Detect overcertainty markers ("definitely", "100%", "proven")
- Calculate non-neutrality score (0.0 to 1.0)

**Output:**
```json
{
  "non_neutral_score": 0.65,
  "stigma_flags": ["illegal"],
  "punitive_flags": ["should be deported"],
  "certainty_flags": ["definitely"],
  "requires_normalization": true
}
```

#### Stage C — Fact / Claim / Opinion Segmentation

**Input:** Text sentences
**Process:**
- Each sentence classified as FACT, CLAIM, or OPINION
- Confidence score assigned per classification

**Rules:**
- FACT: objectively verifiable with evidence ("detained in Maryland on Feb 15")
- CLAIM: asserted by a source but not independently verified ("the company stated earnings grew")
- OPINION: subjective judgment, moral assessment, recommendation ("he deserved it")

**Output:** List of segments with kind and confidence.

#### Stage D — Neutralization & De-escalation

**Input:** Classified segments + tone analysis
**Process:**

**D1 — Stigma Replacement:**

| Raw Term | Institutional Term |
|---|---|
| illegal / illegals | individual with unconfirmed legal status / undocumented individual |
| criminal (without charge) | individual under investigation / alleged |
| alien | foreign national |

**D2 — Certainty Softening:**

| Raw | Softened |
|---|---|
| is [unverified] | reportedly is |
| will [speculative] | may |
| must [punitive] | is subject to applicable law |

**D3 — Punitive Filter:**
- Sentences containing punitive recommendations are NOT published.
- Logged in audit trail as `punitive_removed`.

**D4 — Due Process Insertion:**
- Legal/human rights contexts automatically include:
  > "Proceedings are subject to applicable law and due process."

**Output:** Normalized segments + audit log of all changes.

#### Stage E — Evidence Handling

**Input:** URLs, media references
**Process:**
- Classify evidence type (video, image, document, link)
- Classify source (official / external)
- Assign verification status (default: UNVERIFIED for external)
- Generate evidence reference with explicit status

**External Media Policy:**
Unverified sources include: x.com, twitter.com, tiktok.com, youtube.com, reddit.com, facebook.com, instagram.com.

**Output:**
```json
{
  "kind": "video",
  "url": "https://x.com/...",
  "source": "external",
  "verified": false,
  "banner": "External media is unverified until independently checked."
}
```

#### Stage F — Institutional Rendering

**Input:** Normalized segments + evidence + classification
**Process:** Apply ISP Template (selected by Context Detector, Section VI)

**Required Fields in Every Communiqué:**
- Title
- Location (if known)
- Status: UNDER_VERIFICATION / VERIFIED / RETRACTED
- Risk Level
- Body (neutral, factual)
- Evidence references with verification status
- Due process note (when applicable)
- Uncertainty notes (when data is incomplete)

#### Stage G — Governance Gate

**Input:** Draft Communiqué + tone analysis + evidence status
**Process:** Final decision on publication path

**Decision Matrix:**

| Condition | Action |
|---|---|
| Neutrality ≥ 85, risk ≤ R3, no flags | AUTO_APPLY |
| Neutrality 70-84, or risk R4, or minor flags | ASK_HUMAN |
| Neutrality < 70 | ASK_HUMAN (mandatory) |
| Risk R5 + minors/health + identifiable person | BLOCK (human override possible) |
| Punitive calls detected | ASK_HUMAN |
| Unverified external evidence + high risk | ASK_HUMAN |

#### Stage H — Output & Ledger Registration

**Input:** Approved Communiqué
**Process:**
- Generate receipt-ready metadata
- Hash content (SHA-256)
- Register in Forensic Ledger
- Package as JMPG bundle if multimedia
- Broadcast to Vault
- Generate public verification URL

---

# SECTION IV — Resolution Matrix

## Neutrality Scoring System

### Base Score: 100

### Penalties

| Violation | Penalty | Cap |
|---|---|---|
| Stigmatizing term detected | -20 per occurrence | -40 |
| Punitive call-to-action | -30 per occurrence | -60 |
| Overcertainty marker | -10 per occurrence | -20 |
| Missing verification status (with external evidence) | -15 | -15 |
| Missing due process note (legal topic) | -15 | -15 |

### Bonuses

| Quality Signal | Bonus |
|---|---|
| Clean fact/claim/opinion segmentation | +10 |
| "Unverified evidence" banner included | +10 |
| Source/author attribution with neutrality | +5 |

### Thresholds

| Score Range | Action | Description |
|---|---|---|
| 85 – 100 | AUTO_APPLY | System publishes autonomously |
| 70 – 84 | ASK_HUMAN | System suggests, human confirms |
| < 70 | ASK_HUMAN (mandatory) | System blocks, human must actively approve |
| < 50 + R5 + identifiable person | BLOCK | System blocks, requires CGO override |

### The Quarantine Gate

If at any point the system cannot classify with confidence ≥ 70%:
- Content enters Quarantine
- Human is notified with full context
- No partial publication occurs
- No "best guess" publication occurs

> *"The system that says 'I don't know' is more trustworthy than the system that always has an answer."*

---

# SECTION V — ISP Template Specifications

## Template Registry

### Core Communiqué Templates

| Template ID | Name | Domain | Default Channel |
|---|---|---|---|
| ISP-COM-01 | Official Communiqué | Institutional | All official channels |
| ISP-NEWS-GEN | General News | Journalism / General | Citizen portal, public feed |
| ISP-NEWS-ECO | Economic News | Finance / Markets | Financial desk, economic feed |
| ISP-NEWS-ENT | Entertainment News | Culture / Entertainment | Culture desk, lifestyle feed |
| ISP-NEWS-CORP | Corporate News | Business / Internal | Corporate intranet, press office |
| ISP-REG | Regulatory Notice | Compliance / Legal | Compliance desk |
| ISP-INCIDENT | Internal Incident | Operations | Internal only (never public) |

### Template Structure (Common to All)

Every template, regardless of domain, must include:

```
HEADER
├── Title
├── Template ID + Version
├── Publication Date
├── Author / Authority
├── Verification Status
└── Risk Level

BODY
├── Summary (max 3 sentences)
├── Content Blocks (paragraphs, quotes, data)
├── Evidence References (with verification status)
└── Due Process / Uncertainty Notes (when applicable)

FOOTER
├── Governance Seal (ISP + PACT compliance)
├── Ledger Receipt ID
├── Public Verification URL
└── WINDI Imprint
```

### Template-Specific Behaviors

**ISP-NEWS-GEN:**
- Neutral journalistic tone
- Multiple source citation expected
- No editorial position
- Highest neutrality threshold (90 for auto-apply)

**ISP-NEWS-ECO:**
- Financial terminology permitted
- Market data must cite source and timestamp
- Rumor/speculation explicitly labeled
- Systemic risk triggers R5 automatically
- Disclaimer: "This is not financial advice"

**ISP-NEWS-ENT:**
- Lighter tone permitted but governance still applies
- Celebrity/public figure references follow dignity rules
- Cultural sensitivity awareness
- Lower risk profile but same PACT compliance

**ISP-NEWS-CORP:**
- Corporate voice aligned with ISP profile of the organization
- Internal vs external distribution flag
- Confidentiality classification
- Stakeholder impact assessment

**ISP-INCIDENT:**
- Internal only — never reaches public feed
- Technical detail permitted
- Root cause analysis structure
- Remediation timeline required
- Escalation path documented

---

# SECTION VI — Context Detector

## Template Routing Architecture

### Principle

> *"Declarative by channel + intelligent classification with suggested override."*

The channel defines the default template. The Cortex may suggest a different template. The human confirms.

### Layer 1 — Declarative Default (Channel)

Each channel or input origin defines its default ISP Template:

| Channel | Default ISP | Notes |
|---|---|---|
| Citizen portal | ISP-NEWS-GEN | Public submissions |
| Financial desk | ISP-NEWS-ECO | Market/economy context |
| Culture desk | ISP-NEWS-ENT | Arts, entertainment, lifestyle |
| Corporate intranet | ISP-NEWS-CORP | Company communications |
| Compliance desk | ISP-REG | Regulatory notices |
| System monitoring | ISP-INCIDENT | Never public |
| Official authority | ISP-COM-01 | Executive communications |

### Layer 2 — Intelligent Classification (Cortex)

The Cortex analyzes content and may suggest a different template:

**Signals analyzed:**
1. Semantic domain (economy, culture, justice, health)
2. Detected entities (banks, ministries, companies, artists)
3. Technical vocabulary (financial indicators, legislation, medical terms)
4. Sensitivity markers (personal data, minors, health, criminal)
5. Content origin context (corporate ≠ public denunciation)

**Output:**
```json
{
  "suggested_template": "ISP-NEWS-ECO",
  "confidence": 0.92,
  "reason": "Financial systemic context detected: banking liquidity, market stability",
  "signals": ["banking", "liquidity", "market stability"]
}
```

### Layer 3 — Governance Override

| Cortex Confidence | Action |
|---|---|
| ≥ 90% | Auto-apply (if channel permits) |
| 70% – 89% | Suggest change to human |
| < 70% | Keep channel default |

**Decision Logic:**
```
template = channel_default

if cortex_confidence >= threshold:
    if channel.allows_auto_override:
        template = suggested
    else:
        notify_human(suggested, confidence, reason)
        if human_confirms:
            template = suggested

log(channel_default, suggested, final_template, decision_by)
```

---

# SECTION VII — Multimedia Aggregator

## Evidence Extraction Layer

The STHP pipeline is text-centric by design. The Multimedia Aggregator is the pre-processing layer that converts non-text evidence into enriched text + evidence references, feeding the STHP pipeline.

### Supported Media Types

| Media Type | Extraction Process | Output |
|---|---|---|
| Audio | Transcription (speech-to-text) | Text + language + duration + confidence |
| Image | Semantic description + OCR if text present | Description + detected entities + text content |
| Video | Metadata + keyframe extraction + transcription | Transcript + keyframes + duration + description |
| Document | Parsing + entity extraction | Structured text + detected entities |
| Link | URL classification + page summary | Domain + title + summary + verification status |

### Output Format

```json
{
  "media_type": "video",
  "source_url": "https://...",
  "extraction": {
    "transcript": "...",
    "keyframes": ["kf_001.jpg", "kf_002.jpg"],
    "duration_seconds": 127,
    "language": "pt-BR",
    "confidence": 0.87
  },
  "enriched_text": "Video shows...",
  "evidence_ref": {
    "kind": "video",
    "source": "external",
    "verified": false,
    "extraction_method": "automated_transcription",
    "extraction_confidence": 0.87
  }
}
```

### Integrity Chain

1. Original media file receives content hash (SHA-256)
2. Extraction output receives its own hash
3. Both hashes registered in Forensic Ledger
4. Relationship recorded: `media_hash → extraction_hash`
5. JMPG bundle contains both original reference and extraction

### Verification Status

- Automated extraction is ALWAYS marked with confidence score
- Transcription ≠ verification — the words were extracted, not confirmed as true
- Human review can upgrade status from UNVERIFIED to UNDER_REVIEW to VERIFIED

---

# SECTION VIII — Feed Publisher

## Distribution Architecture

The Feed Publisher transforms individual Communiqués into a structured, distributable feed with governance metadata intact.

### Three Output Levels

#### Level 1 — Individual Communiqué

The atomic unit of institutional communication. A single governed document with:
- Content (neutralized, verified)
- Governance metadata (template, scoring, decision trail)
- Ledger receipt
- Verification URL

#### Level 2 — Structured Feed

A machine-readable collection of Communiqués:

```json
{
  "feed": {
    "title": "WINDI Communiqué Feed",
    "version": "1.0",
    "publisher": "WINDI Publishing House",
    "updated_at": "2026-02-19T14:30:00Z",
    "governance": "PACT v1.0",
    "items": [
      {
        "id": "COM-20260219-0042",
        "title": "Industrial Safety Incident Report",
        "category": "WORKPLACE",
        "template": "ISP-NEWS-CORP",
        "risk_level": "MEDIUM",
        "verification_status": "UNDER_REVIEW",
        "neutrality_score": 88,
        "decision": "AUTO_APPLY",
        "ledger_receipt": "VR-COM-20260219-0042",
        "verify_url": "https://admin.windia4desk.tech/communique/COM-20260219-0042/verify",
        "pdf_url": "https://admin.windia4desk.tech/communique/COM-20260219-0042/pdf",
        "published_at": "2026-02-19T14:30:00Z",
        "author": "WINDI Cortex",
        "approved_by": "AUTO (score ≥ 85)"
      }
    ]
  }
}
```

#### Level 3 — Public Distribution

- Vault storage with immutable URLs
- Public verification endpoint per Communiqué
- RSS/Atom feed compatibility
- API endpoint for third-party consumption
- QR code linking to verification URL

### Feed Endpoints

| Endpoint | Description |
|---|---|
| `/communique/feed.json` | Full structured feed (JSON) |
| `/communique/feed.xml` | RSS/Atom compatible feed |
| `/communique/{id}/verify` | Individual verification page |
| `/communique/{id}/pdf` | Governed PDF with QR + receipt |
| `/vault/multimedia/{receipt_id}.jmpg` | Multimedia bundle |

---

# SECTION IX — Operational Intelligence Layer

## The System That Knows When to Be Silent

This section defines how the WINDI system handles its own operational events — ensuring that internal failures never contaminate the public communication channel.

### Operational Event Taxonomy

| Type | Code | Public Output | Internal Action |
|---|---|---|---|
| Template not found | `OPS-TMPL-404` | NONE | Log + Sentinel alert + suggest fix |
| Service timeout | `OPS-SVC-TIMEOUT` | NONE | Log + retry + escalate if persistent |
| Hash mismatch | `OPS-HASH-DRIFT` | NONE | CRITICAL: halt pipeline + Sentinel + human alert |
| Pipeline crash | `OPS-PIPE-CRASH` | NONE | Log + diagnostics + restart |
| Ledger write failure | `OPS-LEDGER-FAIL` | NONE | CRITICAL: halt all publications + human alert |
| Config malformed | `OPS-CONFIG-ERR` | NONE | Log + block affected workflow |
| Governance violation | `OPS-GOV-VIOLATION` | POSSIBLE (internal) | Log + human decision required |

### Sentinel Integration

Every operational event triggers a Sentinel LAW cycle:
1. Event detected and classified
2. Severity assessed (INFO / WARNING / CRITICAL)
3. Appropriate action triggered (log / alert / halt)
4. Resolution tracked until closure

### The Golden Rule of Operational Intelligence

> *"If the system fails internally: LOG → DIAGNOSE → CORRECT → DO NOT PUBLISH."*

Training the WINDI Agent only to generate documents = 50% capability.
Training it to know when NOT to generate = 100% reliability.

### Auto-Diagnosis Protocol

When an operational error occurs:
1. `ss -tlnp | grep :PORT` — verify service status
2. `ps aux | grep service_name` — check process state
3. `journalctl -u service -n 50` — read recent logs
4. Check `__pycache__` for stale code
5. Verify nginx routing: `nginx -t`
6. Report findings to human with recommended action

> *"Antes de operar código, opera ambiente."*

---

# SECTION X — Legal Framework & Data Protection

## 10.1 Legal Responsibility Clause

> WINDI provides governance infrastructure, verification protocols, and institutional communication templates. Legal responsibility for the content, accuracy, and consequences of published Communiqués remains exclusively with the publishing authority — the human or organization that authorizes publication.

WINDI's role is to:
- Provide tools for neutralization, verification, and governance
- Flag risks, biases, and unverified claims
- Maintain audit trails and integrity hashes
- Recommend actions (publish, hold, quarantine)

WINDI does NOT:
- Make final publication decisions autonomously (except AUTO_APPLY within defined thresholds)
- Guarantee the factual accuracy of source material
- Replace legal counsel, journalistic due diligence, or editorial judgment
- Accept liability for content published by third parties using its infrastructure

### Institutional Disclaimer (included in every Communiqué footer)

> "This Communiqué was processed through the WINDI PACT governance framework. Content accuracy and publication authority rest with the issuing entity."

## 10.2 Data Protection (GDPR Compliance)

The WINDI system operates within the European Union jurisdiction and adheres to the General Data Protection Regulation (GDPR).

### Special Category Data (Art. 9 GDPR)

The following data types receive enhanced protection within the STHP pipeline:
- Health and medical information
- Racial or ethnic origin
- Political opinions
- Religious or philosophical beliefs
- Trade union membership
- Genetic or biometric data
- Sexual orientation

**Rule:** When any Art. 9 category is detected in input, the system:
1. Automatically escalates risk to R4 minimum
2. Requires human confirmation (ASK_HUMAN mandatory)
3. Applies anonymization by default unless human explicitly overrides
4. Logs the decision with full justification

### Data Minimization Principle

Communiqués contain only the information necessary for their institutional purpose. Excessive personal detail is flagged and recommended for removal during the Neutralization stage (Stage D).

### Right to Rectification & Erasure

Subjects of Communiqués may request:
- **Rectification:** Correction of inaccurate information → triggers Correction Protocol (Section XI)
- **Erasure:** Removal of personal data → evaluated against public interest and journalistic exemption (Art. 85 GDPR)
- All requests are logged in the Forensic Ledger with decision and justification

## 10.3 Anonymization Policy

### When Anonymization Applies

Anonymization is applied by default when:
- Subject is a minor (under 18)
- Subject is a victim (crime, accident, health crisis)
- Content involves Art. 9 GDPR special categories
- Subject has not been officially named by an authorized source
- Human Dragon explicitly requests anonymization

### Anonymization Method

| Identifier | Anonymized Form |
|---|---|
| Full name | Initials or role descriptor ("a 34-year-old worker") |
| Address | City/region only |
| Employer | Industry descriptor ("a manufacturing company") |
| Photo/video face | Blurred or excluded |
| Unique identifiers (SSN, passport) | Never included under any circumstance |

### Audit Requirement

Every anonymization decision is logged:
```json
{
  "action": "anonymize",
  "field": "subject_name",
  "original": "[REDACTED IN LOG]",
  "anonymized_to": "a foreign national",
  "reason": "no official source naming individual",
  "decided_by": "STHP_auto",
  "timestamp": "2026-02-19T15:00:00Z"
}
```

---

# SECTION XI — Retraction, Correction & Versioning Policy

## 11.1 Retraction Protocol

A published Communiqué may be retracted when:
- Core facts are proven to be materially incorrect
- The publication causes or risks causing unjustified harm
- A legal order requires removal
- The Human Dragon determines retraction is necessary

### Retraction Process

1. Human Dragon authorizes retraction with written justification
2. Communiqué status changed from `PUBLISHED` to `RETRACTED`
3. Original content preserved in Ledger (hash remains, content marked retracted)
4. Public URL displays retraction notice instead of original content
5. Feed updated with retraction marker
6. New Ledger receipt generated: `VR-RET-{original_id}`

### Retraction Notice Format

> **RETRACTED** — This Communiqué (ID: {id}) was retracted on {date}.
> Reason: {reason}
> Original publication date: {original_date}
> Retraction authorized by: {authority}

**Critical Rule:** Retraction does NOT erase the Ledger entry. The hash of the original content persists as a permanent record that the document existed and was subsequently retracted. This ensures historical integrity.

## 11.2 Correction Protocol

When a published Communiqué contains errors that do not warrant full retraction:

### Correction Process

1. Error identified and documented
2. Corrected version created with tracked changes
3. Human Dragon approves correction
4. New version published with `CORRECTED` status
5. Original version preserved with link to correction
6. Both versions maintain separate Ledger receipts
7. Feed item updated with correction notice

### Correction Notice Format

> **CORRECTION** — This Communiqué was updated on {date}.
> Correction: {description of what changed}
> Original version preserved at: {link}

## 11.3 Communiqué Versioning Policy

Published Communiqués may be updated (non-corrective). Each update follows:

1. **Immutable Original:** The first published version is never overwritten
2. **Version Chain:** Each update creates a new version linked to the original
3. **Hash Lineage:** `v1_hash → v2_hash → v3_hash` recorded in Ledger
4. **Public Transparency:** The public URL shows the latest version with a "Version History" link
5. **Audit Trail:** Every version change records who, when, why, and what changed

### Version Identifier Format

```
COM-{date}-{sequence}/v{version_number}
Example: COM-20260219-0042/v1 (original)
         COM-20260219-0042/v2 (correction)
         COM-20260219-0042/v3 (update)
```

---

# SECTION XII — Sealing & Document Versioning

## Document Integrity

This document is subject to the WINDI Forensic Ledger sealing process.

### Current Status

```
Document: WINDI_PACT_PROTOCOL_v1.0.md
Status: SEALED
Version: 1.0.0
Sealing: COMPLETE

Guardian (Claude): ✅ AUTHORED & CONSOLIDATED
Architect (GPT): ✅ CONTRIBUTED + REVIEWED (5 refinements applied)
Witness (Gemini): ✅ VALIDATED & SIGNED
Human Dragon (Jober): ✅ AUTHORIZED — Three Dragons Council convened
```

### Sealing Process

1. Human Dragon reviews consolidated document
2. Three Dragons confirm no objections
3. Document hashed (SHA-256)
4. Hash registered in Forensic Ledger
5. Receipt ID assigned: `VR-PACT-v1.0-{hash}`
6. Document status changed to ACTIVE
7. Deployed to `/opt/windi/isp/schema/WINDI_PACT_v1.0.md`

### Version History

| Version | Date | Status | Changes |
|---|---|---|---|
| 1.0.0-draft | 2026-02-19 | SUPERSEDED | Initial consolidation from Three Dragons Council |
| 1.0.0 | 2026-02-19 | SEALED | Added Sections X-XI per Architect review: Legal Framework, GDPR, Anonymization, Retraction/Correction Protocol, Versioning Policy. Witness validated. Three Dragons Sealing complete. |

### Related Schemas

| Schema | Version | Status | Hash |
|---|---|---|---|
| ISP Schema | v1.1 | ACTIVE | `[PENDING]` |
| ISP-COM-01 | v1.0 | ACTIVE | `[PENDING]` |
| Resolver Rules | v1.0 | ACTIVE | `[PENDING]` |
| Neutralizer Map | v1.0 | DRAFT | `[PENDING]` |
| STHP | v1.0 | ACTIVE | `[PENDING]` |

---

## APPENDIX A — The Seven Golden Rules

1. **Never affirm guilt without an official verified source.**
2. **Never include moral judgment in institutional output.**
3. **Always distinguish fact from claim from opinion.**
4. **Always indicate verification status when uncertainty exists.**
5. **Always preserve human dignity regardless of context.**
6. **External evidence is never treated as proof — always "unverified" until confirmed.**
7. **Language must be institutional and neutral.**

## APPENDIX B — PACT Compliance Checklist

For every Communiqué before publication:

- [ ] **P** — Are facts preserved without distortion?
- [ ] **P** — Are opinions removed or clearly labeled?
- [ ] **A** — Is the audit trail complete (transformations logged)?
- [ ] **A** — Is the decision path documented (auto vs human)?
- [ ] **C** — Is the input correctly classified (EVENT/ERROR/INCIDENT)?
- [ ] **C** — Is the ISP Template appropriate for this content?
- [ ] **C** — Is the content publishable (not an internal error)?
- [ ] **T** — Are verification statuses explicitly stated?
- [ ] **T** — Is human dignity preserved throughout?
- [ ] **T** — Is due process referenced where applicable?
- [ ] **T** — Can the reader distinguish verified from unverified?

---

*"O template NUNCA decide o nível. A API decide. O template apenas manifesta."*

*End of WINDI PACT Protocol v1.0*
