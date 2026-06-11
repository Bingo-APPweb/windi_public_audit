# WINDI SEAL — Architecture & Engineering Manual
**Version:** 1.0.0
**Date:** 11 June 2026
**Status:** SEALED · Receipt `WINDI-ARC-VERIFY-SURFACE-20260611`
**Classification:** Partner Distribution — Anthropic / Advisors
**Author:** WINDI Publishing House · Liga IA+H

---

## Executive Summary

WINDI SEAL is a **privacy-first provenance verification system** that allows anyone to cryptographically seal digital content — proving existence, authorship, and integrity — without uploading the content to any server.

**Core Innovation:** The file never leaves the user's device. Only the SHA-256 hash is transmitted and stored.

**Three Seal Types:**
- **SELO-CAPTURA** — Immediate capture (photo/video/audio), high evidentiary weight
- **SELO-COMPOSIÇÃO** — Edited work with documented lineage
- **SELO-NARRATIVA** — Creative universe (fiction, cinema, synthetic characters)

**Distribution Model:** Claude Artifacts, Canva Apps, GPT Store, embeddable widgets.

---

## Table of Contents

1. [System Architecture](#1-system-architecture)
2. [Frontend: windi-seal-v2.html](#2-frontend-windi-seal-v2html)
3. [Backend: Forensic Ledger API](#3-backend-forensic-ledger-api)
4. [The Three Seal Types](#4-the-three-seal-types)
5. [Privacy & Security Model](#5-privacy--security-model)
6. [API Reference](#6-api-reference)
7. [UI/UX Guidelines](#7-uiux-guidelines)
8. [Current State & Gaps](#8-current-state--gaps)
9. [Deployment Architecture](#9-deployment-architecture)
10. [Partner Integration Guide](#10-partner-integration-guide)
11. [Roadmap](#11-roadmap)

---

## 1. System Architecture

### 1.1 High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER DEVICE                                 │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    WINDI SEAL UI                             │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │   │
│  │  │  📷 Capture │  │  🎬 Editor  │  │  🔍 Verify  │          │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘          │   │
│  │                         │                                    │   │
│  │                         ▼                                    │   │
│  │  ┌───────────────────────────────────────────────────────┐  │   │
│  │  │              crypto.subtle.digest()                    │  │   │
│  │  │              SHA-256 computed LOCALLY                  │  │   │
│  │  │              File NEVER leaves device                  │  │   │
│  │  └───────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              │ Only hash + metadata                 │
│                              ▼                                      │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               │ HTTPS
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      WINDI INFRASTRUCTURE                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                 FORENSIC LEDGER API (:8101)                  │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │   │
│  │  │   POST      │  │    GET      │  │   Merkle    │          │   │
│  │  │  /receipts  │  │  /receipts  │  │   Proofs    │          │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                   SQLite + Merkle Tree                       │   │
│  │                   57,000+ receipts                           │   │
│  │                   Append-only, immutable                     │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Core Principles

| Principle | Implementation |
|-----------|----------------|
| **Privacy by Design** | Hash computed on device; file never uploaded |
| **Zero-Knowledge Proof** | Server proves existence without seeing content |
| **Append-Only Ledger** | No updates, no deletes — immutable history |
| **Sovereign Identity** | DID-based authorship (did:windi:*) |
| **Explicit Failure** | Never mock data; fail clearly (I14 invariant) |
| **Human Approval** | AI proposes, human decides (I9 invariant) |

### 1.3 Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | Vanilla HTML/CSS/JS | Zero dependencies, embeddable anywhere |
| **Crypto** | Web Crypto API | SHA-256, client-side, secure context required |
| **Camera** | MediaDevices API | getUserMedia, MediaRecorder |
| **Backend** | Python 3.11 | Lightweight HTTP server |
| **Database** | SQLite | Single-file, portable, reliable |
| **Merkle** | Custom implementation | Transparency log, proof generation |

---

## 2. Frontend: windi-seal-v2.html

### 2.1 File Location & Versions

| File | Version | Hash | Purpose |
|------|---------|------|---------|
| `/opt/windi/artifacts/windi-seal-v2.html` | v2.4 | `77e7d94e...` | Production artifact |
| `/opt/windi/artifacts/verify-living-surface-v1.html` | v1.0 | `6f118d7b...` | Verification-only surface |

### 2.2 Architecture

```
windi-seal-v2.html (35KB, single-file)
├── <style> — Complete CSS (~130 lines)
│   ├── CSS Variables (NOIR/KLAR themes)
│   ├── Component styles
│   └── Responsive breakpoints
├── <body> — Semantic HTML (~130 lines)
│   ├── Header (logo, language toggle, theme toggle)
│   ├── Mode tabs (Capturar / Comentar)
│   ├── Capture zone (camera, video, upload, hash input)
│   ├── Editor zone (canvas, PiP, text overlay)
│   ├── Scan zone (progress animation)
│   └── Result zone (verdict, bio-card, actions)
└── <script> — Logic (~270 lines)
    ├── State management
    ├── Camera handling (MediaDevices)
    ├── Video recording (MediaRecorder)
    ├── Hash computation (crypto.subtle)
    ├── Canvas composition
    └── Result display
```

### 2.3 Key Functions

```javascript
// Hash computation — THE CORE PRIVACY FEATURE
async function computeHash(file) {
  const buffer = await file.arrayBuffer();
  const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
  return Array.from(new Uint8Array(hashBuffer))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');
}

// Camera with facing mode (front/back)
async function startCamera(withAudio = false) {
  const constraints = {
    video: { facingMode, width: { ideal: 1280 }, height: { ideal: 720 } },
    audio: withAudio
  };
  cameraStream = await navigator.mediaDevices.getUserMedia(constraints);
}

// Video recording with audio
function startRecording() {
  let mime = 'video/webm';
  if (MediaRecorder.isTypeSupported('video/webm;codecs=vp9,opus'))
    mime = 'video/webm;codecs=vp9,opus';
  mediaRecorder = new MediaRecorder(cameraStream, {
    mimeType: mime,
    audioBitsPerSecond: 128000,
    videoBitsPerSecond: 2500000
  });
}
```

### 2.4 State Variables

```javascript
// Core state
let currentMode = null;        // 'camera' | 'video' | 'upload' | 'hash'
let currentTab = 'capture';    // 'capture' | 'editor'
let capturedFile = null;       // File object
let cameraStream = null;       // MediaStream
let facingMode = 'environment'; // 'environment' | 'user'

// Recording
let isRecording = false;
let mediaRecorder = null;
let recordedChunks = [];

// Editor
let bgImage = null;
let bgVideo = null;
let pipStream = null;
let overlayTextValue = '';

// §4.4 Seal Types
let sealType = 'capture';      // 'capture' | 'composition' | 'narrative'
let sourceHash = null;         // Lineage reference for compositions
let narrativeClass = null;     // For narrative seals: 'fiction', etc.
```

### 2.5 UI Components

| Component | Purpose | Status |
|-----------|---------|--------|
| **Viewfinder** | Camera preview, captured media display | ✅ Working |
| **Recording Indicator** | Red dot + timer during video capture | ✅ Working |
| **Camera Flip** | Switch front/back camera | ✅ Working |
| **Capture Modes** | Photo / Video / Upload / Hash buttons | ✅ Working |
| **Editor Canvas** | Composition workspace | ✅ Working |
| **PiP Camera** | Picture-in-Picture overlay | ✅ Working |
| **Position Grid** | 9-position PiP placement | ✅ Working |
| **Text Overlay** | Commentary text on canvas | ✅ Working |
| **Scan Animation** | Progress feedback during seal | ✅ Working |
| **Verdict Card** | Result display (3 seal types) | ✅ Working |
| **Bio Card** | Metadata display (date, author, integrity) | ✅ Working |
| **Lineage Row** | Source hash for compositions | ✅ Working |

### 2.6 Themes & i18n

**Themes:**
```css
[data-theme=noir] {
  --bg: #050508;
  --card: #0a0a10;
  --gold: #c9a84c;
  --green: #00ff88;    /* SELO-CAPTURA */
  --gold: #c9a84c;     /* SELO-COMPOSIÇÃO */
  --purple: #a855f7;   /* SELO-NARRATIVA */
}

[data-theme=klar] {
  --bg: #fafaf8;
  --card: #fff;
  --green: #00aa55;
  --gold: #8b7424;
  --purple: #7c3aed;
}
```

**Languages:** PT / DE / EN with full i18n for all verdict texts and disclaimers.

---

## 3. Backend: Forensic Ledger API

### 3.1 Service Location

| Service | Port | Status |
|---------|------|--------|
| Forensic Ledger API | :8101 | ✅ LIVE |
| Verify Public | :8114 | ✅ LIVE |

### 3.2 Database Schema

```sql
CREATE TABLE receipts (
  id                TEXT PRIMARY KEY,
  created_at        TEXT NOT NULL,
  actor             TEXT NOT NULL,      -- did:windi:* or email
  wallet_id         TEXT NOT NULL,      -- sovereign identity
  device_id         TEXT,
  app               TEXT NOT NULL,
  doc_name          TEXT NOT NULL,
  doc_type          TEXT NOT NULL,      -- doc|xlsx|pptx|...
  local_filename    TEXT,
  content_hash      TEXT NOT NULL,      -- sha256:...
  bytes             INTEGER,
  governance_level  TEXT,               -- LOW|MEDIUM|HIGH
  sge_score         REAL,               -- 0.0-1.0
  isp_context       TEXT,
  template_id       TEXT,
  tags_json         TEXT,
  flags_json        TEXT,
  ed25519_pub       TEXT,
  ed25519_sig       TEXT,
  merkle_root       TEXT,
  status            TEXT,
  metadata_json     TEXT,
  jurisdiction      TEXT,
  declaration       TEXT,
  parent_receipt_id TEXT                -- Chain linking
);
```

### 3.3 Current Statistics

```
Total Receipts: 57,000+
Daily Average: ~200 receipts
Uptime: 99.9%
```

---

## 4. The Three Seal Types

### 4.1 Taxonomia Tripartida

```
┌─────────────────────────────────────────────────────────────────┐
│                    TAXONOMIA DE SELOS WINDI                     │
├─────────────────┬───────────────────┬───────────────────────────┤
│  SELO-CAPTURA   │  SELO-COMPOSIÇÃO  │     SELO-NARRATIVA        │
│  🟢 Verde       │  🟡 Ouro          │     🟣 Púrpura             │
├─────────────────┼───────────────────┼───────────────────────────┤
│  Origem         │  Obra derivada    │     Universo criativo     │
│  primária       │                   │                           │
├─────────────────┼───────────────────┼───────────────────────────┤
│  📷 Foto        │  💬 Comentário    │  🎭 Ficção Dramática       │
│  🎬 Vídeo       │  📰 Reportagem    │  🎬 Cinema                 │
│  🎙️ Áudio       │  📊 Apresentação  │  📖 Personagens Fictícios  │
│  📄 Documento   │  📓 Diário        │                           │
├─────────────────┼───────────────────┼───────────────────────────┤
│  AFIRMA:        │  AFIRMA:          │  AFIRMA:                  │
│  "Este ficheiro │  "Esta obra foi   │  "Esta narrativa foi      │
│  existia neste  │  criada por este  │  publicada nesta forma."  │
│  estado."       │  DID."            │                           │
├─────────────────┼───────────────────┼───────────────────────────┤
│  NÃO AFIRMA:    │  NÃO AFIRMA:      │  NÃO AFIRMA:              │
│  veracidade     │  fontes são       │  existência real          │
│  do conteúdo    │  verdadeiras      │  das entidades            │
└─────────────────┴───────────────────┴───────────────────────────┘
```

### 4.2 Disclaimers

**SELO-CAPTURA:**
> "O selo prova existência e integridade do momento — não a veracidade do conteúdo."

**SELO-COMPOSIÇÃO:**
> "O selo prova que esta composição foi criada neste momento e está inalterada desde então. Material de fundo referenciado na linhagem."

**SELO-NARRATIVA:**
> "O selo prova que esta narrativa foi publicada nesta forma. Não afirma existência real das entidades representadas."

### 4.3 Receipt Structure

```json
{
  "id": "WINDI-DOCTRINE-CINE-VERIFY-001-20260611155006",
  "created_at": "2026-06-11T15:50:06+02:00",
  "actor": "did:windi:dragon-001",
  "wallet_id": "did:windi:dragon-001",
  "app": "windi-seal-v2.4",
  "doc_name": "Captured moment",
  "doc_type": "doc",
  "content_hash": "sha256:b4cf91c68ad1d6c3...",
  "governance_level": "HIGH",
  "sge_score": 0.95,
  "metadata_json": {
    "seal_type": "capture",
    "source_hash": null,
    "lineage": []
  }
}
```

---

## 5. Privacy & Security Model

### 5.1 Zero-Upload Architecture

```
USER DEVICE                          SERVER
────────────                         ──────
File (50MB photo)
    │
    ▼
SHA-256 computation ◄──────────────── crypto.subtle (local)
    │
    │ "sha256:a1b2c3d4..."
    │ (64 characters)
    ▼
────────────────────────────────────► POST /api/receipts
                                          │
                                          ▼
                                     Store hash + metadata
                                     (NO file content)
```

**Key Privacy Guarantees:**
1. File never leaves the device
2. Server cannot see file content
3. Only 64-character hash is transmitted
4. GDPR-compliant by design
5. No cloud storage of media

### 5.2 CORS Configuration

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, OPTIONS
```

This enables:
- Claude Artifacts embedding
- Third-party widget integration
- Cross-origin API calls

### 5.3 Security Considerations

| Risk | Mitigation |
|------|------------|
| Hash collision | SHA-256 has 2^256 possibilities; collision practically impossible |
| Replay attack | Timestamps + unique receipt IDs |
| DID spoofing | DID validation against Genesis registry |
| API abuse | Rate limiting per DID (planned) |

---

## 6. API Reference

### 6.1 Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/receipts` | Create new receipt |
| GET | `/api/receipts/{id}` | Get receipt by ID |
| GET | `/api/receipts?limit=N` | List recent receipts |
| GET | `/api/receipts/by-hash/{hash}` | Find by content hash |
| GET | `/api/merkle/proof/{id}` | Get Merkle proof |
| GET | `/api/merkle/root` | Get current Merkle root |

### 6.2 POST /api/receipts

**Request:**
```json
{
  "schema_version": "1.0",
  "id": "WINDI-...-TIMESTAMP",
  "created_at": "2026-06-11T15:50:06+02:00",
  "actor": "did:windi:dragon-001",
  "wallet_id": "did:windi:dragon-001",
  "app": "windi-seal-v2.4",
  "doc_name": "My Photo",
  "doc_type": "doc",
  "content_hash": "sha256:...",
  "governance_level": "HIGH",
  "sge_score": 0.95
}
```

**Response:**
```json
{
  "ok": true,
  "stored": true,
  "id": "WINDI-...-TIMESTAMP",
  "privacy": "content_not_stored",
  "message": "Virtue Receipt '...' sealed in Forensic Ledger"
}
```

### 6.3 GET /api/receipts/{id}

**Response:**
```json
{
  "ok": true,
  "receipt": {
    "id": "WINDI-...",
    "created_at": "2026-06-11T15:50:06+02:00",
    "actor": "did:windi:dragon-001",
    "doc_name": "My Photo",
    "content_hash": "sha256:...",
    "governance_level": "HIGH"
  }
}
```

---

## 7. UI/UX Guidelines

### 7.1 Design Principles

1. **Instant Understanding** — User knows what's happening in 2 seconds
2. **No Jargon** — "Selo" not "cryptographic hash attestation"
3. **Trust Through Transparency** — Show exactly what's being sealed
4. **Mobile First** — Touch targets ≥ 44px
5. **Offline Capable** — Hash computation works without network

### 7.2 Color Language

| State | Color | Meaning |
|-------|-------|---------|
| 🟢 Green | `#00ff88` | Verified / Capture / Success |
| 🟡 Gold | `#c9a84c` | Composition / Brand / Action |
| 🟣 Purple | `#a855f7` | Narrative / Creative / Fiction |
| 🔴 Red | `#ff4444` | Recording / Error / Alert |
| ⚪ Dim | `#6a6a7a` | Secondary / Disabled |

### 7.3 Animation Guidelines

- **Scan line:** 2s ease-in-out infinite
- **Progress bar:** 0.3s transitions
- **Log entries:** 0.3s fade-in slide-up
- **Button hover:** 0.2s all properties

### 7.4 Responsive Breakpoints

```css
@media (max-width: 400px) {
  /* Stack buttons, reduce padding */
}
```

### 7.5 Accessibility

- Semantic HTML structure
- ARIA labels on interactive elements
- High contrast in both themes
- Keyboard navigation support

---

## 8. Current State & Gaps

### 8.1 What's Working (✅)

| Feature | Status | Notes |
|---------|--------|-------|
| Photo capture | ✅ | All browsers |
| Video capture | ✅ | WebM with VP9+Opus |
| Audio recording | ✅ | 128kbps AAC |
| Camera flip | ✅ | Front/back switch |
| File upload | ✅ | Any file type |
| Hash verification | ✅ | Hash input mode |
| SHA-256 local | ✅ | crypto.subtle |
| Editor mode | ✅ | Background + PiP + Text |
| PiP positioning | ✅ | 9-position grid |
| Three seal types | ✅ | Capture/Composition/Narrative |
| Lineage tracking | ✅ | sourceHash for compositions |
| Trilingual UI | ✅ | PT/DE/EN |
| NOIR/KLAR themes | ✅ | Dark/Light |
| CORS open | ✅ | Embeddable anywhere |
| Ledger API | ✅ | 57k+ receipts |
| Merkle proofs | ✅ | Transparency log |

### 8.2 Known Gaps (⚠️)

| Gap | Priority | Description | Effort |
|-----|----------|-------------|--------|
| **Gate 0** | 🔴 CRITICAL | `/api/receipts/{id}` returns not_found for all IDs when called from Artifacts | 1 day |
| Safari MP4 | 🟡 HIGH | Safari records MP4, not WebM; needs codec detection | 2 hours |
| Real device test | 🟡 HIGH | Need measurement run on iOS Safari, Android Chrome | 1 day |
| Rate limiting | 🟡 MEDIUM | Per-DID quota enforcement | 4 hours |
| Receipt Explainer | 🟢 LOW | Ollama-powered natural language explanation | 2 days |
| Video composition | 🟢 LOW | Record composed video, not just screenshot | 1 week |

### 8.3 Gate 0 — The Critical Blocker

**Problem:** The Verify API at `/api/receipts/{id}` returns `not_found` for all receipt IDs when called from external surfaces (Claude Artifacts, browser widgets).

**Impact:** The entire "curiosity funnel" breaks at the first step. A curious user scanning a QR code finds nothing.

**Solution:** Connect the public Verify API (:8114) to the real Ledger database (57k+ receipts).

**Effort:** One afternoon of backend work.

---

## 9. Deployment Architecture

### 9.1 Current Infrastructure

```
Server: Strato VPS (87.106.29.233)
Domain: windi-domain.com
OS: Debian Linux

Services:
├── :8101 — Forensic Ledger API
├── :8114 — Verify Public
├── nginx — Reverse proxy, SSL termination
└── SQLite — Single-file database
```

### 9.2 Artifact Distribution

**Current:**
```
https://windi-domain.com/artifacts/windi-seal-v2.html
```

**Potential Partners:**
- Claude Artifacts (Anthropic)
- Canva Apps
- GPT Store (OpenAI)
- Notion embeds
- WordPress plugins

### 9.3 Embedding Example

```html
<iframe
  src="https://windi-domain.com/artifacts/windi-seal-v2.html"
  width="100%"
  height="600"
  frameborder="0"
  allow="camera; microphone"
></iframe>
```

---

## 10. Partner Integration Guide

### 10.1 For Claude Artifacts

The artifact is already compatible with Claude Artifacts:
- Single HTML file
- No external dependencies
- CORS headers configured
- Camera permissions declarable

**Usage:**
```
User: "Create a provenance seal for my photo"
Claude: [Renders windi-seal-v2.html artifact]
```

### 10.2 For Canva Apps

Requirements for Canva App Store:
- [ ] OAuth integration (optional)
- [ ] Canva SDK wrapper
- [ ] Design export to sealed receipt
- [ ] Brand guidelines compliance

### 10.3 API Integration

Third parties can integrate via API:

```javascript
// Seal a document
const response = await fetch('https://windi-domain.com/api/receipts', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    schema_version: '1.0',
    id: `PARTNER-${Date.now()}`,
    created_at: new Date().toISOString(),
    actor: 'did:windi:partner-001',
    wallet_id: 'did:windi:partner-001',
    app: 'partner-app',
    doc_name: 'User Document',
    doc_type: 'doc',
    content_hash: 'sha256:...',
    governance_level: 'MEDIUM',
    sge_score: 0.8
  })
});

// Verify a document
const receipt = await fetch(
  `https://windi-domain.com/api/receipts/${receiptId}`
).then(r => r.json());
```

---

## 11. Roadmap

### Phase 1: Foundation (✅ COMPLETE)
- [x] Local SHA-256 computation
- [x] Three seal types
- [x] Lineage tracking
- [x] Trilingual UI
- [x] Ledger integration
- [x] Merkle proofs

### Phase 2: Distribution (🔄 IN PROGRESS)
- [ ] **Gate 0: Fix Verify API** ← CRITICAL
- [ ] Safari iOS codec fix
- [ ] Real device testing
- [ ] Anthropic partnership submission
- [ ] Documentation (this manual)

### Phase 3: Scale
- [ ] Rate limiting per DID
- [ ] Receipt Explainer (Ollama)
- [ ] Video composition export
- [ ] Canva App submission
- [ ] GPT Store submission

### Phase 4: Ecosystem
- [ ] W-Travel integration
- [ ] W-Journal integration
- [ ] Enterprise API tier
- [ ] White-label offering

---

## Appendix A: File Hashes (Sealed)

| File | SHA-256 | Receipt |
|------|---------|---------|
| windi-seal-v2.html | `77e7d94eb60c739f...` | `WINDI-SEAL-V24-ARTIFACT-20260611155034` |
| DOCTRINE-CINE-VERIFY-001.md | `b4cf91c68ad1d6c3...` | `WINDI-DOCTRINE-CINE-VERIFY-001-20260611155006` |
| LEI-TAXONOMIA-TRIPARTIDA.md | `afe65d0a29c2c7cc...` | `WINDI-LEI-TAXONOMIA-TRIPARTIDA-20260611155031` |
| WB-CURIOSITY-FUNNEL.md | `2325a8135b73fca9...` | `WINDI-WB-CURIOSITY-FUNNEL-20260611155032` |

---

## Appendix B: Constitutional Invariants

| ID | Name | Impact |
|----|------|--------|
| I1 | Human Sovereignty | Human touch activates; never autonomous |
| I9 | No Autonomy Escalation | AI proposes, human decides |
| I11 | Cryptographic Evidence Permanence | Ledger receipt is immutable forever |
| I12 | Language Sovereignty | UI universal; document sovereign |
| I14 | Explicit Failure | Missing data = clear error, never mock |

---

## Appendix C: Contact

**WINDI Publishing House**
Kempten, Bavaria, Germany

**Liga IA+H:**
- 🐉 Human Dragon — CGO
- 🛡️ Guardian — Protection & Ethics
- 🏗️ Architect — Structure & Construction
- 👁️ Witness — Observation & Validation

---

> *"AI processes. Human decides. WINDI guarantees."*

> *"Tudo pode ser selado. Nem tudo significa a mesma coisa."*

---

**Document sealed:** `WINDI-ARC-VERIFY-SURFACE-20260611`
**SHA-256:** (computed at distribution)
