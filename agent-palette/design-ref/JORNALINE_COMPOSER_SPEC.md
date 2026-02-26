# JORNALINE COMPOSER SPEC v1.0
## WINDI Palette — Citizen Journalism with Forensic Dignity
**Date:** 2026-02-24
**Author:** Architect Dragon
**Status:** DESIGN READY — Awaiting Implementation

---

## VISION

> "Um rapaz na Rua 5 de Julho pode reportar um acontecimento jornalístico
> com a mesma dignidade e créditos de cartório que um jornalista profissional."

Jornaline = **Jornalismo + Online + Forense**

Every citizen becomes a verified witness. Every report becomes an immutable record.

---

## 1. ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────────┐
│                     PALETTE v1.0.0-W                                │
├─────────────────────────────────────────────────────────────────────┤
│  Side Rail │  Header + Respiradouro                                 │
│            ├────────────────────────────────────────────────────────┤
│    💬      │                                                        │
│    📄      │         JORNALINE COMPOSER (Full Panel)                │
│    📁      │                                                        │
│    🗞️ ←────│  Triggered from Chat or dedicated button               │
│    ...     │                                                        │
├────────────┴────────────────────────────────────────────────────────┤
│                        Input Bar                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Entry Points

1. **Chat command**: `/jornaline` or `/communique`
2. **Input bar button**: 🗞️ icon next to document buttons
3. **Side Rail**: New tab `jornaline` (between docs and files)
4. **Docs tab**: "Nova Jornaline" button in header

---

## 2. COMPOSER LAYOUT

```
┌─────────────────────────────────────────────────────────────────────┐
│  🗞️ Nova Jornaline                              [Fechar ×]          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  TEMPLATE: [Jornaline ▾] [Report ▾] [Impacto: MED ▾]          │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  TÍTULO                                                        │ │
│  │  ┌──────────────────────────────────────────────────────────┐ │ │
│  │  │ Incêndio na Rua 5 de Julho — Testemunho Cidadão         │ │ │
│  │  └──────────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  CONTEÚDO                                    [B][I][Q][H][L]   │ │
│  │  ┌──────────────────────────────────────────────────────────┐ │ │
│  │  │                                                          │ │ │
│  │  │  O incêndio começou por volta das 14:32 no edifício     │ │ │
│  │  │  número 47. Vi fumo a sair da janela do 3º andar.       │ │ │
│  │  │                                                          │ │ │
│  │  │  > "Ouvi um estrondo e depois vi as chamas"             │ │ │
│  │  │  > — Moradora do prédio vizinho                          │ │ │
│  │  │                                                          │ │ │
│  │  │  Os bombeiros chegaram em aproximadamente 8 minutos.     │ │ │
│  │  │                                                          │ │ │
│  │  └──────────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  📷 EVIDENCE GALLERY                          [+ Adicionar]    │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │ │
│  │  │ ┌──────┐ │ │ ┌──────┐ │ │ ┌──────┐ │ │          │          │ │
│  │  │ │ IMG  │ │ │ │ IMG  │ │ │ │ VID  │ │ │   ➕     │          │ │
│  │  │ │      │ │ │ │      │ │ │ │ ▶    │ │ │   drag   │          │ │
│  │  │ └──────┘ │ │ └──────┘ │ │ └──────┘ │ │   drop   │          │ │
│  │  │ 14:35:22 │ │ 14:38:45 │ │ 14:40:12 │ │          │          │ │
│  │  │ 📍 -23.5 │ │ 📍 -23.5 │ │ 2m 15s   │ │          │          │ │
│  │  │ [×]      │ │ [×]      │ │ [×]      │ │          │          │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  🔗 LINKS & REFERÊNCIAS                                        │ │
│  │  ├── https://bombeiros.cv/incidente-2026-0047    [✓] [×]      │ │
│  │  ├── https://twitter.com/user/status/123...      [⏳] [×]      │ │
│  │  └── [+ Adicionar URL verificável]                             │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│  🛡️ PROTOCOLO FORENSE (Preview)                                     │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Autor: João Silva · Cidadão                                   │ │
│  │  Timestamp: 2026-02-24T14:45:00Z · Device: Chrome/Mac          │ │
│  │  Location: -23.5505°, -46.6333° (±15m)                         │ │
│  │  Evidence: 2 fotos + 1 vídeo · Bundle hash: pending...         │ │
│  │  ISP: ISP-COM-02 Jornaline · Governance: HIGH                  │ │
│  └────────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│    [📝 Guardar Rascunho]              [🔍 Submeter para Revisão]    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. COMPONENT BREAKDOWN

### 3.1 Template Selector

```javascript
const ISP_TEMPLATES = [
  { id: "ISP-COM-01", name: "Amtliches Kommuniqué", icon: "📜", governance: "HIGH" },
  { id: "ISP-COM-02", name: "Jornaline", icon: "🗞️", governance: "MEDIUM" },
  { id: "ISP-COM-03", name: "Feldbericht", icon: "📋", governance: "MEDIUM" },
  { id: "ISP-COM-04", name: "Security Advisory", icon: "🔒", governance: "HIGH" },
  { id: "ISP-COM-05", name: "Governance Decision", icon: "⚖️", governance: "HIGH" },
  { id: "ISP-COM-06", name: "System Bulletin", icon: "📢", governance: "MEDIUM" },
];

const CATEGORIES = ["LAUNCH", "UPDATE", "ALERT", "GOVERNANCE", "REPORT"];
const IMPACT_LEVELS = ["LOW", "MED", "HIGH", "CRIT"];
```

### 3.2 Rich Text Editor

Toolbar buttons:
| Button | Function | Output |
|--------|----------|--------|
| **B** | Bold | `<strong>text</strong>` |
| *I* | Italic | `<em>text</em>` |
| Q | Quote | `<blockquote>text</blockquote>` |
| H | Heading | `<h2>text</h2>` |
| L | List | `<ul><li>text</li></ul>` |
| — | Divider | `<hr/>` |

Implementation: `contenteditable` div with execCommand or lightweight library.

### 3.3 Evidence Gallery

```javascript
const Evidence = {
  id: "ev-001",
  type: "image" | "video" | "audio" | "document",
  file: File,
  preview: base64 | objectURL,
  metadata: {
    timestamp: "2026-02-24T14:35:22Z",  // EXIF or upload time
    gps: { lat: -23.5505, lng: -46.6333, accuracy: 15 },
    device: "iPhone 14 Pro",
    hash: "sha256:a7f3b2c1..."  // Computed on upload
  },
  status: "pending" | "hashed" | "error"
};
```

**Upload Flow:**
1. User drags/drops or clicks [+ Adicionar]
2. File is read, preview generated
3. SHA-256 hash computed client-side
4. EXIF/metadata extracted (if image)
5. GPS captured from browser (if permitted)
6. Evidence card appears in gallery

### 3.4 Link Verifier

```javascript
const Link = {
  url: "https://example.com/article",
  status: "pending" | "verified" | "failed" | "unreachable",
  title: "Extracted page title",
  timestamp: "2026-02-24T14:50:00Z",
  hash: "sha256:..."  // Hash of fetched content
};
```

**Verification Flow:**
1. User pastes URL
2. `POST /api/dragon/verify-url` (existing endpoint)
3. Server fetches, extracts title, computes hash
4. Status badge: ✓ verified, ⏳ pending, ✗ failed

### 3.5 Forensic Preview

Shows what will be sealed:

```javascript
const ForensicPreview = {
  author: {
    name: "João Silva",
    role: "Cidadão",  // or "Jornalista", "Instituição"
    verified: false   // Future: identity verification
  },
  timestamp: "2026-02-24T14:45:00Z",
  device: {
    browser: "Chrome 120",
    os: "macOS 14.2",
    ip_hint: "203.x.x.x"  // Partial, privacy-aware
  },
  location: {
    lat: -23.5505,
    lng: -46.6333,
    accuracy: 15,
    source: "browser"  // or "manual", "exif"
  },
  evidence: {
    images: 2,
    videos: 1,
    documents: 0,
    total_bytes: 4_500_000,
    bundle_hash: "pending..."  // Computed on submit
  },
  isp: {
    template: "ISP-COM-02",
    name: "Jornaline",
    governance: "HIGH"
  }
};
```

---

## 4. DATA FLOW

```
┌─────────────────────────────────────────────────────────────────┐
│                    COMPOSER (Frontend)                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. Collect content: title, body (HTML), evidence[], links[]    │
│  2. Compute hashes client-side (evidence files)                 │
│  3. Build canonical JSON payload                                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  POST /api/communique/create                                    │
│  {                                                              │
│    "title_de": "...", "title_en": "...", "title_pt": "...",    │
│    "body_de": "<html>...", "body_en": "...", "body_pt": "...", │
│    "category": "REPORT",                                        │
│    "impact_level": "MED",                                       │
│    "isp_template": "ISP-COM-02",                                │
│    "author_name": "João Silva",                                 │
│    "author_role": "Cidadão",                                    │
│    "evidence": [                                                │
│      { "type": "image", "hash": "...", "metadata": {...} },    │
│      { "type": "video", "hash": "...", "metadata": {...} }     │
│    ],                                                           │
│    "links": [                                                   │
│      { "url": "...", "hash": "...", "verified": true }         │
│    ],                                                           │
│    "forensic": {                                                │
│      "device": "...",                                           │
│      "location": {...},                                         │
│      "timestamp": "..."                                         │
│    }                                                            │
│  }                                                              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Communiqué Engine (:8105)                                      │
│  1. Validate ISP template                                       │
│  2. Create DRAFT record                                         │
│  3. Return { id: "COM-2026-0048", status: "DRAFT" }            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  POST /api/communique/{id}/evidence/upload (multipart)          │
│  Upload actual files → stored in /published/{id}/evidence/      │
│  Each file hashed and verified against client-provided hash     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  POST /api/communique/{id}/review                               │
│  Status: DRAFT → REVIEW                                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  POST /api/communique/{id}/publish (by reviewer)                │
│  1. Bundle all evidence into .jmpg package                      │
│  2. Compute final content_hash + bundle_hash                    │
│  3. POST to Forensic Ledger (:8101)                            │
│  4. Broadcast to Forensic Vault (:8106)                        │
│  5. Generate PDF with QR code                                   │
│  6. Status: REVIEW → PUBLISHED                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. UI STATES

### 5.1 Composer States

| State | UI | Actions Available |
|-------|-----|-------------------|
| `empty` | Empty form, placeholder text | Fill form |
| `editing` | Content being typed | Save Draft |
| `uploading` | Evidence upload in progress | Wait / Cancel |
| `draft_saved` | Green flash, ID shown | Submit for Review |
| `submitting` | Spinner, "Submitting..." | Wait |
| `submitted` | Success message, link to view | Close, View |
| `error` | Red banner with message | Retry, Close |

### 5.2 Evidence States

| State | Badge | Visual |
|-------|-------|--------|
| `pending` | ⏳ | Grey border, spinner |
| `hashing` | ⚙️ | Pulsing border |
| `hashed` | ✓ | Green border, hash preview |
| `uploading` | ↑ | Progress bar |
| `uploaded` | ✓✓ | Double check, green |
| `error` | ✗ | Red border, error message |

### 5.3 Link States

| State | Icon | Visual |
|-------|------|--------|
| `pending` | ⏳ | Grey text |
| `verifying` | ⚙️ | Spinner |
| `verified` | ✓ | Green, shows title |
| `failed` | ✗ | Red, shows error |
| `unreachable` | ⚠️ | Amber, "Could not reach" |

---

## 6. MOBILE CONSIDERATIONS

On mobile (< 768px):
- Composer becomes full-screen modal
- Evidence gallery becomes horizontal scroll
- GPS capture uses native geolocation API
- Camera button for direct photo capture
- Simplified toolbar (icons only)

```
┌─────────────────────────┐
│ 🗞️ Jornaline    [×]    │
├─────────────────────────┤
│ Template: [Jornaline ▾] │
├─────────────────────────┤
│ Título:                 │
│ ┌─────────────────────┐ │
│ │                     │ │
│ └─────────────────────┘ │
├─────────────────────────┤
│ Conteúdo:    [B][I][Q] │
│ ┌─────────────────────┐ │
│ │                     │ │
│ │                     │ │
│ │                     │ │
│ └─────────────────────┘ │
├─────────────────────────┤
│ 📷 Evidence ──────────► │
│ [IMG][IMG][VID][+]      │
├─────────────────────────┤
│ [📝 Draft] [🔍 Submit]  │
└─────────────────────────┘
```

---

## 7. INTEGRATION WITH PALETTE

### 7.1 New Button in Input Bar

```jsx
<button onClick={() => setJornalineOpen(true)}
        title={lang==="de"?"Jornaline erstellen":"Create Jornaline"}>
  🗞️
</button>
```

### 7.2 New State

```javascript
const [jornalineOpen, setJornalineOpen] = useState(false);
const [jornalineData, setJornalineData] = useState({
  template: "ISP-COM-02",
  category: "REPORT",
  impact: "MED",
  title: "",
  body: "",
  evidence: [],
  links: [],
});
```

### 7.3 Modal/Panel Render

```jsx
{jornalineOpen && (
  <JornalineComposer
    data={jornalineData}
    onChange={setJornalineData}
    onClose={() => setJornalineOpen(false)}
    onSubmit={handleJornalineSubmit}
    T={T}
    lang={lang}
  />
)}
```

---

## 8. IMPLEMENTATION PRIORITY

| Sprint | Task | Complexity |
|--------|------|------------|
| **J1** | Basic composer (title + body + template) | Medium |
| **J1** | Integration with existing /api/communique/create | Low |
| **J1** | Draft save + Submit for Review | Low |
| **J2** | Evidence gallery (upload + hash + preview) | High |
| **J2** | GPS capture + device metadata | Medium |
| **J2** | Evidence upload to server | Medium |
| **J3** | Link verifier integration | Medium |
| **J3** | Rich text editor (contenteditable) | Medium |
| **J3** | Forensic preview panel | Low |
| **J4** | Mobile responsive layout | Medium |
| **J4** | Camera capture (mobile) | Medium |
| **J4** | Offline draft storage (localStorage) | Low |

---

## 9. API EXTENSIONS NEEDED

### 9.1 Evidence Upload Endpoint

```
POST /api/communique/{id}/evidence/upload
Content-Type: multipart/form-data

Fields:
- file: binary
- type: "image" | "video" | "audio" | "document"
- client_hash: "sha256:..."
- metadata: JSON string

Response:
{
  "success": true,
  "evidence_id": "ev-001",
  "server_hash": "sha256:...",
  "hash_match": true,
  "stored_at": "/published/COM-2026-0048/evidence/ev-001.jpg"
}
```

### 9.2 Location Metadata

Browser geolocation to be captured client-side and sent with create payload:

```javascript
navigator.geolocation.getCurrentPosition(pos => {
  setJornalineData(prev => ({
    ...prev,
    forensic: {
      ...prev.forensic,
      location: {
        lat: pos.coords.latitude,
        lng: pos.coords.longitude,
        accuracy: pos.coords.accuracy,
        timestamp: new Date().toISOString()
      }
    }
  }));
});
```

---

## 10. LABELS (Trilingual)

```javascript
const JORNALINE_LABELS = {
  pt: {
    title: "Nova Jornaline",
    template: "Template",
    category: "Categoria",
    impact: "Impacto",
    titleField: "Título",
    titlePlaceholder: "O que aconteceu?",
    bodyField: "Conteúdo",
    bodyPlaceholder: "Descreve o que testemunhaste...",
    evidence: "Evidence Gallery",
    addEvidence: "Adicionar",
    dragDrop: "Arrasta fotos/vídeos aqui",
    links: "Links & Referências",
    addLink: "Adicionar URL verificável",
    forensic: "Protocolo Forense",
    author: "Autor",
    citizen: "Cidadão",
    timestamp: "Timestamp",
    location: "Localização",
    device: "Dispositivo",
    saveDraft: "Guardar Rascunho",
    submit: "Submeter para Revisão",
    success: "Jornaline criada!",
    viewIt: "Ver",
  },
  de: {
    title: "Neue Jornaline",
    template: "Vorlage",
    category: "Kategorie",
    impact: "Auswirkung",
    titleField: "Titel",
    titlePlaceholder: "Was ist passiert?",
    bodyField: "Inhalt",
    bodyPlaceholder: "Beschreibe, was du erlebt hast...",
    evidence: "Beweismaterial",
    addEvidence: "Hinzufügen",
    dragDrop: "Fotos/Videos hierher ziehen",
    links: "Links & Referenzen",
    addLink: "Verifizierbare URL hinzufügen",
    forensic: "Forensisches Protokoll",
    author: "Autor",
    citizen: "Bürger",
    timestamp: "Zeitstempel",
    location: "Standort",
    device: "Gerät",
    saveDraft: "Entwurf speichern",
    submit: "Zur Prüfung einreichen",
    success: "Jornaline erstellt!",
    viewIt: "Anzeigen",
  },
  en: {
    title: "New Jornaline",
    template: "Template",
    category: "Category",
    impact: "Impact",
    titleField: "Title",
    titlePlaceholder: "What happened?",
    bodyField: "Content",
    bodyPlaceholder: "Describe what you witnessed...",
    evidence: "Evidence Gallery",
    addEvidence: "Add",
    dragDrop: "Drag photos/videos here",
    links: "Links & References",
    addLink: "Add verifiable URL",
    forensic: "Forensic Protocol",
    author: "Author",
    citizen: "Citizen",
    timestamp: "Timestamp",
    location: "Location",
    device: "Device",
    saveDraft: "Save Draft",
    submit: "Submit for Review",
    success: "Jornaline created!",
    viewIt: "View",
  },
};
```

---

## 11. PRINCIPLE

> "O jornalismo cidadão não é amador. É o olhar da rua com a dignidade do tribunal."
>
> Cada foto tem hash. Cada testemunho tem timestamp.
> Cada cidadão tem voz. Cada voz tem prova.
>
> **"AI processes. Human witnesses. WINDI guarantees."**

---

*Sealed by Architect Dragon — 2026-02-24*
*Ready for Three Dragons Consensus*
