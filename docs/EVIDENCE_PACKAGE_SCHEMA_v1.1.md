# WINDI Evidence Package Schema v1.1
## Standard for Multimedia Communiqué Evidence Bundles

**Version:** 1.1.0
**Date:** 2026-02-19
**Status:** ACTIVE
**Author:** Dragon (CGO) + Guardian (Claude)
**Type:** ISP Multimedia Foundation

---

## 1. PURPOSE

This schema defines the official standard for Evidence Packages (.jmpg) that
accompany WINDI Multimedia Communiqués. It establishes:

- File structure within the bundle
- Manifest format (manifest.json)
- Hash chain requirements
- Metadata obligations
- Evidence element identification

**Principle:** "The evidence speaks. The hash proves. The Ledger remembers."

---

## 2. BUNDLE STRUCTURE

```
EV-{YYYYMMDD}-{NNNN}.jmpg
├── manifest.json          ← Evidence Package Manifest (this schema)
├── evidence/
│   ├── IMG-01.png         ← Image evidence
│   ├── IMG-02.png
│   ├── IMG-03.png
│   ├── VID-01.mp4         ← Video evidence (reference file or low-res proxy)
│   └── DOC-01.pdf         ← Document evidence
└── metadata/
    ├── capture_log.json   ← Capture timestamps and origins
    └── chain.json         ← Hash chain verification data
```

### Naming Convention

| Component | Format | Example |
|-----------|--------|---------|
| Bundle ID | `EV-{YYYYMMDD}-{NNNN}` | `EV-20260219-0001` |
| Image | `IMG-{NN}.{ext}` | `IMG-01.png` |
| Video | `VID-{NN}.{ext}` | `VID-01.mp4` |
| Document | `DOC-{NN}.{ext}` | `DOC-01.pdf` |
| Audio | `AUD-{NN}.{ext}` | `AUD-01.wav` |

---

## 3. MANIFEST.JSON — Official Structure

```json
{
  "$schema": "windi-evidence-package-v1.1",
  "evidence_id": "EV-20260219-0001",
  "version": "1.1.0",

  "communique": {
    "id": "COM-20260219-0001",
    "type": "COMMUNIQUE_MULTIMEDIA",
    "title": "MULTIMEDIA COMMUNIQUÉ — First Prototype",
    "category": "INCIDENT",
    "impact_level": "HIGH"
  },

  "created_at": "2026-02-19T14:00:00Z",
  "created_by": {
    "name": "Jober Mögele Correa",
    "role": "Chief Governance Officer",
    "organization": "WINDI Publishing House"
  },

  "evidence": {
    "total_files": 4,
    "total_bytes": 5155840,
    "types": {
      "images": 3,
      "videos": 1,
      "documents": 0,
      "audio": 0
    },
    "files": [
      {
        "id": "IMG-01",
        "filename": "IMG-01.png",
        "type": "image",
        "mime_type": "image/png",
        "sha256": "7a3f92c1e8b4d7f6a5c3e2d1b0a9f8e7d6c5b4a3921011f0e9d8c7b6a594321",
        "bytes": 350208,
        "dimensions": "1920x1080",
        "caption": {
          "de": "Dashboard vor dem Integritätsaudit",
          "en": "Dashboard before integrity audit",
          "pt": "Dashboard antes da auditoria de integridade"
        },
        "captured_at": "2026-02-19T13:45:00Z",
        "source": "operator",
        "source_detail": "Manual screenshot via Desktop (:8100)"
      },
      {
        "id": "IMG-02",
        "filename": "IMG-02.png",
        "type": "image",
        "mime_type": "image/png",
        "sha256": "b29d4e7f1a6cd7f6a5c3e2d1b0a9f8e7d6c5b4a3921011f0e9d8c7b6a594321",
        "bytes": 293888,
        "dimensions": "1920x1080",
        "caption": {
          "de": "Systemstatus nach erfolgreicher Bereinigung",
          "en": "System state after successful cleanup",
          "pt": "Estado do sistema após limpeza bem-sucedida"
        },
        "captured_at": "2026-02-19T13:50:00Z",
        "source": "operator",
        "source_detail": "Manual screenshot via Desktop (:8100)"
      },
      {
        "id": "IMG-03",
        "filename": "IMG-03.png",
        "type": "image",
        "mime_type": "image/png",
        "sha256": "e51c8d3f2b9ad7f6a5c3e2d1b0a9f8e7d6c5b4a3921011f0e9d8c7b6a594321",
        "bytes": 202752,
        "dimensions": "1440x900",
        "caption": {
          "de": "Sentinel LAW — Permanente Überwachung aktiv",
          "en": "Sentinel LAW — Permanent monitoring active",
          "pt": "Sentinel LAW — Monitoramento permanente ativo"
        },
        "captured_at": "2026-02-19T13:52:00Z",
        "source": "sentinel",
        "source_detail": "Automated capture by Sentinel LAW (:8102)"
      },
      {
        "id": "VID-01",
        "filename": "VID-01.mp4",
        "type": "video",
        "mime_type": "video/mp4",
        "sha256": "f83a12d4c7e9d7f6a5c3e2d1b0a9f8e7d6c5b4a3921011f0e9d8c7b6a594321",
        "bytes": 4308992,
        "duration_seconds": 24,
        "resolution": "1920x1080",
        "caption": {
          "de": "Service-Terminierung — Aufzeichnung",
          "en": "Service termination — Recording",
          "pt": "Terminação do serviço — Gravação"
        },
        "captured_at": "2026-02-19T13:48:00Z",
        "source": "operator",
        "source_detail": "Screen recording via Desktop (:8100)"
      }
    ]
  },

  "hashes": {
    "content_hash": "a83f92c1e8b4d7f6a5c3e2d1b0a9f8e7d6c5b4a3921011f0e9d8c7b6a5943210",
    "content_hash_method": "SHA-256 of concatenated file hashes in manifest order",
    "bundle_hash": "9bc21ef7a843d2e51c8d3f2b9a7e4f6d1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d",
    "bundle_hash_method": "SHA-256 of final .jmpg binary",
    "chain_algorithm": "content_hash = SHA256(IMG-01.sha256 + IMG-02.sha256 + ... + VID-01.sha256)"
  },

  "ledger": {
    "receipt_id": "VR-COM-MM-20260219-0001",
    "receipt_type": "COMMUNIQUE_MULTIMEDIA",
    "ledger_status": "sealed",
    "sealed_at": "2026-02-19T14:00:30Z"
  },

  "governance": {
    "sge_score": null,
    "risk_level": "R3",
    "doc_type": "COMMUNIQUE",
    "impact_level": "HIGH",
    "flow_status": "PUBLISHED",
    "department_code": "GOV"
  },

  "verification": {
    "verify_url": "https://admin.windia4desk.tech/communique/COM-20260219-0001/verify",
    "evidence_verify_url": "https://admin.windia4desk.tech/communique/COM-20260219-0001/evidence/verify",
    "immutable": true,
    "immutable_since": "2026-02-19T14:00:30Z"
  }
}
```

---

## 4. EVIDENCE ELEMENT RULES

### 4.1 Images

| Rule | Requirement |
|------|-------------|
| Format | PNG, JPEG, WebP |
| Max resolution | 3840×2160 (4K) |
| Max file size | 10 MB |
| Thumbnail | Auto-generated, max 400px width |
| Caption | Required, trilingual (DE/EN/PT) |
| Hash | SHA-256 of raw file bytes, required |
| Timestamp | ISO 8601, required |
| Source | Required: `operator`, `sentinel`, `audit`, `system` |

### 4.2 Video

| Rule | Requirement |
|------|-------------|
| Format | MP4 (H.264), WebM |
| Max duration | 300 seconds (5 min) |
| Max file size | 50 MB |
| Embedding | NEVER embedded in HTML — reference only |
| Duration | Required, in seconds |
| Resolution | Required |
| Caption | Required, trilingual |
| Hash | SHA-256 of raw file bytes, required |

### 4.3 Documents

| Rule | Requirement |
|------|-------------|
| Format | PDF |
| Max pages | 50 |
| Max file size | 20 MB |
| Caption | Required, trilingual |
| Hash | SHA-256 of raw file bytes, required |

### 4.4 Audio

| Rule | Requirement |
|------|-------------|
| Format | WAV, MP3, OGG |
| Max duration | 600 seconds (10 min) |
| Max file size | 30 MB |
| Caption | Required, trilingual |
| Hash | SHA-256 of raw file bytes, required |

---

## 5. SOURCE TYPES

| Source | Description | Example |
|--------|-------------|---------|
| `operator` | Manual capture by human operator | Screenshot, recording |
| `sentinel` | Automated capture by Sentinel LAW | Health check snapshot |
| `audit` | Captured during formal audit | Compliance evidence |
| `system` | System-generated automatically | Error logs, metrics |
| `external` | From external source | Third-party report |

---

## 6. HASH CHAIN

The content_hash is computed as:

```
content_hash = SHA256(
  file[0].sha256 +
  file[1].sha256 +
  ... +
  file[N].sha256
)
```

Where files are concatenated in manifest order (as listed in evidence.files[]).

The bundle_hash is computed as:

```
bundle_hash = SHA256(final_jmpg_bytes)
```

Both hashes are registered in the Forensic Ledger (:8101).

---

## 7. RECEIPT NAMING

| Type | Format | Example |
|------|--------|---------|
| Text Communiqué | `VR-COM-{hash_prefix}` | `VR-COM-570c2162f086` |
| Multimedia Communiqué | `VR-COM-MM-{YYYYMMDD}-{NNNN}` | `VR-COM-MM-20260219-0001` |

---

## 8. INTEGRATION POINTS

```
Desktop (:8100) ──capture──→ Evidence Files
                              ↓
Export Engine (:8103) ──hash+bundle──→ .jmpg
                                       ↓
Communiqué Engine (:8105) ──publish──→ HTML + Verify
                                       ↓
Forensic Ledger (:8101) ──seal──→ Receipt
                                       ↓
Forensic Vault (:8106) ──read──→ Audit Access
```

---

## 9. ARCHITECTURAL INVARIANTS

1. **Evidence files are NEVER stored in the Ledger** — only hashes
2. **Video is NEVER embedded** — reference only
3. **Every evidence element MUST have a SHA-256 hash**
4. **Every evidence element MUST have a trilingual caption**
5. **The manifest order defines the hash chain order**
6. **Once sealed, the Evidence Package is immutable (HTTP 403 on modification)**
7. **The Evidence Package travels WITH the Communiqué, not separately**
8. **Source attribution is mandatory** — who/what captured this evidence
9. **Timestamps are mandatory** — when was this evidence captured

---

## 10. COMPATIBILITY

- Compatible with JMPG Viewer (:8104) — dual-hash verification
- Compatible with Forensic Ledger (:8101) — receipt registration
- Compatible with Sentinel LAW (:8102) — integrity monitoring
- Compatible with Export Engine (:8103) — bundle generation
- Future: Compatible with BABEL editor — evidence attachment workflow

---

*WINDI Publishing House · Kempten, Bavaria*
*"AI processes. Human decides. WINDI guarantees."*
