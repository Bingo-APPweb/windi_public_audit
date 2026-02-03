# WINDI v0.1 Document Integrity Framework

## Implementation of Governance-Embedded Cryptographic Envelopes

**WINDI Publishing House — Kempten, Bavaria**

**Masterarbeit Technical Chapter**

---

## 1. Problem Statement

### 1.1 The Document Governance Gap

Traditional document management systems treat content and metadata as separate entities. A PDF can be modified, metadata falsified, and there exists no mathematical proof binding the document to its governance context. This creates a fundamental trust problem in institutional workflows, particularly critical under the EU AI Act requirements for AI-assisted document generation.

### 1.2 Research Question

*How can cryptographic integrity mechanisms be embedded directly into document workflows to create verifiable governance-content binding that enables offline regulatory verification?*

---

## 2. WINDI v0.1 Specification

### 2.1 Envelope Architecture

The WINDI Envelope v0.1 implements a four-layer integrity model:

```
┌─────────────────────────────────────────────────────────────┐
│                    WINDI ENVELOPE v0.1                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │  DOCUMENT   │    │ GOVERNANCE  │    │  INTEGRITY  │     │
│  │             │    │             │    │             │     │
│  │ document_id │    │ issuer_id   │    │ gov_digest  │     │
│  │ version_id  │───▶│ actor_id    │───▶│ doc_hash    │     │
│  │ body_sha256 │    │ intent_code │    │ struct_sig  │     │
│  │             │    │ policy_ref  │    │             │     │
│  └─────────────┘    │ timestamp   │    └─────────────┘     │
│                     │ jurisdiction│                         │
│                     └─────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Cryptographic Chain

The integrity chain follows a deterministic computation sequence:

| Step | Operation | Output |
|------|-----------|--------|
| 1 | SHA-256(document_bytes) | body_sha256 |
| 2 | SHA-256(C14N(governance)) | governance_digest |
| 3 | SHA-256(governance_digest + body_sha256) | doc_hash |
| 4 | HMAC-SHA256(issuer_secret, doc_hash) | struct_sig |

### 2.3 Canonical JSON (C14N)

To ensure deterministic hashing of governance metadata, the specification mandates Canonical JSON serialization:

```python
def canonical_json(data: Dict[str, Any]) -> bytes:
    return json.dumps(
        data, 
        sort_keys=True, 
        separators=(",", ":")
    ).encode("utf-8")
```

This eliminates JSON ordering ambiguity and ensures identical objects produce identical hashes regardless of serialization context.

---

## 3. Implementation

### 3.1 System Integration

The WINDI v0.1 module was integrated into the A4 Desk BABEL system at the following points:

```
A4 Desk BABEL v4.7-gov
├── /opt/windi/engine/windi_c14n.py      ← Core cryptographic module
├── /opt/windi/data/envelopes/           ← Envelope storage
└── a4desk_tiptap_babel.py               ← Integration points
    ├── Import block (line 24)
    ├── generate_windi_envelope()
    ├── save_windi_envelope()
    └── API endpoints
        ├── /api/windi/status
        ├── /api/windi/envelope/{id}
        └── /api/windi/verify/{id}
```

### 3.2 Envelope Generation Flow

```
User clicks "Export PDF"
         │
         ▼
┌─────────────────────────┐
│   Generate PDF bytes    │
│   (wkhtmltopdf)         │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Compute body_sha256    │
│  SHA-256(pdf_bytes)     │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Build governance obj   │
│  - issuer_id            │
│  - responsible_actor_id │
│  - intent_code          │
│  - policy_reference     │
│  - jurisdictions        │
│  - timestamp_issued     │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Compute gov_digest     │
│  SHA-256(C14N(gov))     │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Compute doc_hash       │
│  SHA-256(gov + body)    │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Compute struct_sig     │
│  HMAC(secret, doc_hash) │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Save envelope.json     │
│  Return PDF to user     │
└─────────────────────────┘
```

### 3.3 Core Functions

**build_windi_envelope()** — Constructs complete envelope with all integrity proofs:

```python
def build_windi_envelope(
    document_id: str,
    version_id: str,
    content_type: str,
    body_bytes: bytes,
    issuer_id: str,
    responsible_actor_id: str,
    intent_code: str,
    policy_reference: str,
    issuer_secret: bytes,
    jurisdictions: list = None
) -> Dict[str, Any]:
    
    timestamp = datetime.now(timezone.utc).isoformat()
    
    governance = {
        "issuer_id": issuer_id,
        "responsible_actor_id": responsible_actor_id,
        "intent_code": intent_code,
        "policy_reference": policy_reference,
        "jurisdictions": jurisdictions or ["DE", "EU"],
        "timestamp_issued": timestamp
    }
    
    body_sha = sha256_hex(body_bytes)
    gov_digest = governance_digest(governance)
    doc_hash = document_hash(gov_digest, body_sha)
    struct_sig = structural_signature(issuer_secret, doc_hash)
    
    return {
        "schema": "windi.envelope",
        "schema_version": "0.1",
        "document": {
            "document_id": document_id,
            "version_id": version_id,
            "content_type": content_type,
            "body_sha256": body_sha
        },
        "governance": governance,
        "integrity": {
            "governance_digest": gov_digest,
            "doc_hash": doc_hash,
            "struct_sig": struct_sig,
            "algo": "sha256+hmac-sha256"
        }
    }
```

---

## 4. EU AI Act Compliance Mapping

### 4.1 Article Alignment

| EU AI Act Article | Requirement | WINDI Implementation |
|-------------------|-------------|---------------------|
| Article 52 | Transparency obligations | `governance.intent_code`, `governance.policy_reference` |
| Article 17 | Quality management system | `governance.responsible_actor_id`, immutable content binding |
| Article 61 | Post-market monitoring | `governance.timestamp_issued`, verifiable audit trail |
| Article 13 | Transparency to users | Human Authorship Notice in document |

### 4.2 Governance Metadata Fields

```json
{
  "governance": {
    "issuer_id": "windi.publishing.de",
    "responsible_actor_id": "WINDI-CEO-001:Jober Mögele Correa",
    "intent_code": "export.pdf",
    "policy_reference": "eu.ai.act.article.52",
    "jurisdictions": ["DE", "EU"],
    "timestamp_issued": "2026-01-31T12:46:17.308748+00:00"
  }
}
```

---

## 5. Verification Model

### 5.1 Offline Verification (No Secrets Required)

A regulator can verify document integrity without network access:

```bash
# Regulator receives: document.pdf + envelope.json

# Step 1: Compute body hash
sha256sum document.pdf
# Compare with envelope.document.body_sha256

# Step 2: Recompute governance_digest
# Parse envelope.governance, canonicalize, hash
# Compare with envelope.integrity.governance_digest

# Step 3: Recompute doc_hash
# SHA256(governance_digest + body_sha256)
# Compare with envelope.integrity.doc_hash
```

### 5.2 Full Verification (With Issuer Secret)

```bash
# Additionally verify struct_sig
# HMAC-SHA256(issuer_secret, doc_hash)
# Compare with envelope.integrity.struct_sig
```

### 5.3 API Verification

```
GET /api/windi/verify/{document_id}

Response:
{
  "verification": {
    "ok": true,
    "checks": {
      "schema": true,
      "schema_version": true,
      "governance_digest_match": true,
      "doc_hash_match": true
    }
  }
}
```

---

## 6. Production Deployment

### 6.1 Server Configuration

| Component | Location |
|-----------|----------|
| WINDI Strato Server | 87.106.29.233 (Germany) |
| A4 Desk BABEL | Port 8085 |
| Envelope Storage | /opt/windi/data/envelopes/ |
| WINDI Engine | /opt/windi/engine/ |

### 6.2 Environment Variables

```bash
WINDI_ISSUER_ID=windi.publishing.de
WINDI_ISSUER_SECRET=[HMAC secret key]
WINDI_POLICY_REF=eu.ai.act.article.52
```

### 6.3 Live Endpoints

| Endpoint | Function |
|----------|----------|
| https://windi-domain.com/api/windi/status | Integration status |
| https://windi-domain.com/api/windi/envelope/{id} | Get envelope |
| https://windi-domain.com/api/windi/verify/{id} | Verify integrity |

---

## 7. Results

### 7.1 Functional Validation

| Test Case | Result |
|-----------|--------|
| Envelope generation on PDF export | ✅ |
| Governance digest computation | ✅ |
| Document hash binding | ✅ |
| Structural signature | ✅ |
| API verification endpoint | ✅ |
| Offline verification possible | ✅ |

### 7.2 Sample Envelope (Production)

```json
{
  "schema": "windi.envelope",
  "schema_version": "0.1",
  "document": {
    "document_id": "BABEL-20260129213544",
    "version_id": "v1",
    "content_type": "application/pdf",
    "body_sha256": "c1a86358d0b9fa155a7327c9eb89575ffb6738077ee9ecfde3bbcc4cd6b17608"
  },
  "governance": {
    "issuer_id": "windi.publishing.de",
    "responsible_actor_id": "WINDI-CEO-001:Jober Mögele Correa",
    "intent_code": "export.pdf",
    "policy_reference": "eu.ai.act.article.52",
    "jurisdictions": ["DE", "EU"],
    "timestamp_issued": "2026-01-31T12:46:17.308748+00:00"
  },
  "integrity": {
    "governance_digest": "73069ea070249546cc5ebb754f5b9665caeee504e7b99d0296ddcea909e085f9",
    "doc_hash": "6ab6bc50bf3cc46dcc8ce55335007e7a378102dc0ccba01eeeb24508f202df21",
    "struct_sig": "e7f92e85f9d50bd40d675016226d972c51458e876db45588a9d26242aa30428b",
    "algo": "sha256+hmac-sha256"
  }
}
```

---

## 8. Limitations and Future Work

### 8.1 Current Limitations

- HMAC-based signatures require shared secret (symmetric)
- No certificate chain for public verification
- Single issuer model

### 8.2 Proposed Extensions (v0.2)

- **Asymmetric signatures** (Ed25519) for public verification
- **Registry integration** for certificate issuance
- **Blockchain anchoring** for timestamping
- **Multi-issuer support** with key management

---

## 9. Conclusion

The WINDI v0.1 Document Integrity Framework demonstrates a practical implementation of governance-embedded cryptographic envelopes. By binding document content to governance metadata through a deterministic hash chain, the system enables verifiable compliance with EU AI Act transparency requirements while preserving human sovereignty over AI-assisted document workflows.

The implementation proves that institutional-grade document governance can be achieved with standard cryptographic primitives (SHA-256, HMAC) and minimal infrastructure overhead.

---

**Implementation Date:** 31 January 2026

**Author:** Jober Mögele Correa (Chief Governance Officer)

**Technical Assistance:** Claude (Guardian Dragon)

**Validation:** GPT (Architect Dragon)

---

*"AI processes. Human decides. WINDI guarantees."*

**OM SHANTI** 🐉
