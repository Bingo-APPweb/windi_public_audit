# W-DRAGON-001 — Dragon Shadow Forest™
## Implementation Roadmap & Shelf Organization
## Implementierungs-Roadmap & Regalorganisation
## Roteiro de Implementação & Organização por Prateleiras

**Version:** 1.0.0
**Status:** APPROVED by Council · I9 Gate Passed
**Date:** 2026-04-09
**Author:** Liga IA+H · WINDI Publishing House

---

## 📚 SHELF INDEX / REGALVERZEICHNIS / ÍNDICE DE PRATELEIRAS

| # | Shelf | Content | Status |
|---|-------|---------|--------|
| A | **FOUNDATION** | Concepts, Architecture, Invariants | ✅ DEFINED |
| B | **BACKEND** | Python modules, API routes | ✅ DELIVERED |
| C | **FRONTEND** | UI components, JavaScript | ✅ DELIVERED |
| D | **INTEGRATION** | WINDI-LAW connection | ⏳ PHASE 1.5 |
| E | **LEDGER** | Receipt registration, Verify | ⏳ PHASE 1.5 |
| F | **DEPLOY** | Server setup, systemd, nginx | ⏳ PENDING |
| G | **OPTICAL** | UV reader, Camera scanner | 🔮 PHASE 2 |
| H | **PRINT** | Physical documents, ECC | 🔮 PHASE 3 |

---

# 🅰️ SHELF A — FOUNDATION
# Prateleira A — Fundação

## A.1 Core Concept

```
EN: Invisible dragon glyphs encoding SHA-256 hash bits
DE: Unsichtbare Drachen-Glyphen codieren SHA-256-Hash-Bits
PT: Glifos de dragão invisíveis codificando bits do hash SHA-256
```

### A.1.1 The Dragon Grid

| Aspect | Value |
|--------|-------|
| Grid size | 16 × 16 = 256 cells |
| Hash algorithm | SHA-256 (256 bits) |
| Bit = 1 | Dark Dragon (angular heptagon) |
| Bit = 0 | Shadow Dragon (diamond) |
| Opacity (print) | 0.07 (invisible at reading distance) |
| Opacity (screen) | 0.18 (visible for demo) |

### A.1.2 Constitutional Invariants

| ID | Name | Application |
|----|------|-------------|
| **I9** | Human Gate | Receipt requires human approval before seal |
| **I11** | Evidence Sovereignty | receipt_id MUST come from Ledger, NEVER frontend |
| **I14** | No Placeholders | Empty content = explicit error, never silent |

### A.1.3 Data Flow

```
Document (bytes)
    ↓
SHA-256 hash (64 hex chars)
    ↓
256 bits (hash_to_bits)
    ↓
16×16 Dragon Grid (visual encoding)
    ↓
POST to Ledger :8101
    ↓
receipt_id (sovereign)
    ↓
PDF overlay / SVG grid
    ↓
Verify URL: /verify?id={receipt_id}
```

---

# 🅱️ SHELF B — BACKEND
# Prateleira B — Backend

## B.1 File Structure

```
/home/windi/engine/
├── w_dragon_001.py              # Core module (Phase 1.5)
├── w_dragon_001_law_routes.py   # FastAPI routes
└── .env                         # Secrets (LEDGER_TOKEN)
```

## B.2 Core Module: w_dragon_001.py

### B.2.1 Functions Checklist

| Function | Purpose | Status |
|----------|---------|--------|
| `compute_hash(content: bytes)` | SHA-256 of document | ✅ |
| `hash_to_bits(hash_hex: str)` | 64 hex → 256 bits | ✅ |
| `register_with_ledger(...)` | POST to :8101, get receipt_id | ✅ |
| `generate_pdf_overlay(bits, ...)` | ReportLab transparent page | ✅ |
| `merge_overlay_into_pdf(...)` | PyPDF merge onto original | ✅ |
| `generate_svg_grid(bits, ...)` | SVG for web display | ✅ |
| `encode_document(...)` | Full pipeline entry point | ✅ |

### B.2.2 Dependencies

```bash
# Install on Strato
pip install --break-system-packages httpx reportlab pypdf
```

| Package | Version | Purpose |
|---------|---------|---------|
| `httpx` | ≥0.24 | Async HTTP for Ledger |
| `reportlab` | ≥4.0 | PDF generation |
| `pypdf` | ≥3.0 | PDF merge |

### B.2.3 Environment Variables

```bash
# /home/windi/engine/.env
LEDGER_URL=http://127.0.0.1:8101
LEDGER_TOKEN=<bearer_token_from_ledger>
VERIFY_BASE_URL=https://windi-domain.com/verify
DRAGON_OPACITY=0.07
```

## B.3 API Routes: w_dragon_001_law_routes.py

### B.3.1 Endpoints

| Method | Path | Purpose | Auth |
|--------|------|---------|------|
| GET | `/dragon/health` | Module status | None |
| POST | `/dragon/encode` | Text → receipt + SVG | Bearer |
| POST | `/dragon/encode-pdf` | PDF → sealed PDF | Bearer |
| GET | `/dragon/verify/{id}` | Query Ledger | None |

### B.3.2 Request/Response Schemas

**POST /dragon/encode**
```json
// Request
{
  "content": "Contract text...",
  "user_id": "did:windi:human-dragon",
  "screen_mode": false,
  "dark_mode": true
}

// Response
{
  "receipt_id": "WINDI-DSF-1744200000000-A1B2C3D4",
  "hash_sha256": "7d865e959b2466918c9863afca942d0fb1...",
  "verify_url": "https://windi-domain.com/verify?id=...",
  "dark_dragons": 128,
  "shadow_dragons": 128,
  "ledger_confirmed": true,
  "source": "LEDGER",
  "svg_grid": "<svg>...</svg>"
}
```

**POST /dragon/encode-pdf**
```bash
curl -X POST http://localhost:8122/dragon/encode-pdf \
  -F 'file=@contract.pdf' \
  -F 'user_id=did:windi:human-dragon' \
  -o sealed_contract.pdf
```

Response headers:
```
X-WINDI-Receipt: WINDI-DSF-...
X-WINDI-Hash: 7d865e95...
X-WINDI-Verify: https://windi-domain.com/verify?id=...
X-WINDI-Confirmed: true
```

---

# 🅲 SHELF C — FRONTEND
# Prateleira C — Frontend

## C.1 File Structure

```
/home/windi/law/static/
└── windi_dragon_ui.js    # "Ver Dragões" panel
```

## C.2 UI Component: windi_dragon_ui.js

### C.2.1 Features

| Feature | Description |
|---------|-------------|
| NOIR theme | Dark mode matching WINDI design system |
| Client-side SHA-256 | Instant preview via WebCrypto |
| Server sync | POST to /dragon/encode for sovereign receipt |
| Offline fallback | Shows local hash if API unreachable |
| Copy receipt | One-click clipboard |
| Verify button | Query Ledger directly |

### C.2.2 Integration (HTML)

```html
<!-- Add to WINDI-LAW workspace -->
<div id="windi-dragon-panel"></div>
<script src="/static/windi_dragon_ui.js"></script>
<script>
  DragonUI.init({
    containerId: 'windi-dragon-panel',
    apiBase: '/dragon',
    userId: sessionStorage.getItem('windi_did'),
    openByDefault: false
  });
</script>
```

### C.2.3 API

```javascript
// Initialize
DragonUI.init(options)

// Options
{
  containerId:   'windi-dragon-panel',  // Required
  apiBase:       '/dragon',             // Default
  userId:        'did:windi:...',       // Optional
  openByDefault: false                  // Default
}
```

---

# 🅳 SHELF D — INTEGRATION
# Prateleira D — Integração

## D.1 WINDI-LAW (:8122) Integration

### D.1.1 Steps

```
STEP 1: Add import to windi_law_app.py
────────────────────────────────────────
import sys
sys.path.insert(0, '/home/windi/engine')
from w_dragon_001_law_routes import dragon_router

STEP 2: Register router
────────────────────────────────────────
app.include_router(dragon_router)

STEP 3: Restart service
────────────────────────────────────────
sudo systemctl restart windi-law

STEP 4: Verify
────────────────────────────────────────
curl http://localhost:8122/dragon/health
```

### D.1.2 Integration Points

| WINDI-LAW Feature | DSF Integration |
|-------------------|-----------------|
| AI Draft | Encode final document before seal |
| Document Viewer | "Ver Dragões" panel in sidebar |
| Export PDF | Overlay dragon grid on export |
| Seal confirmation | Show receipt_id + verify URL |

---

# 🅴 SHELF E — LEDGER
# Prateleira E — Ledger

## E.1 Ledger Connection (:8101)

### E.1.1 Registration Payload

```json
{
  "schema": "W-DRAGON-001-v1",
  "invariants": ["I9", "I11", "I14"],
  "hash_algorithm": "SHA-256",
  "hash_real": "7d865e959b2466918c9863afca942d0f...",
  "content_length_bytes": 4096,
  "grid": {
    "cols": 16,
    "rows": 16,
    "bits": 256,
    "dark_dragons": 128,
    "shadow_dragons": 128
  },
  "timestamp_unix": 1744200000,
  "timestamp_iso": "2026-04-09T12:00:00Z",
  "human_gate": {
    "required": true,
    "invariant": "I9",
    "status": "PENDING"
  },
  "user_id": "did:windi:human-dragon",
  "module": "W-DRAGON-001/WINDI-LAW",
  "phase": "1.5"
}
```

### E.1.2 Ledger Response

```json
{
  "receipt_id": "WINDI-DSF-1744200000000-A1B2C3D4",
  "status": "REGISTERED",
  "ledger_block": 12345
}
```

### E.1.3 Verify Flow

```
GET /verify?id=WINDI-DSF-...
    ↓
Ledger :8101 lookup
    ↓
Compare hash
    ↓
Return: VALID | INVALID | NOT_FOUND
```

---

# 🅵 SHELF F — DEPLOY
# Prateleira F — Deploy

## F.1 Pre-Deploy Checklist

```
□ LEDGER_TOKEN exists in .env
□ Ledger :8101 is reachable
□ Python dependencies installed
□ Backend files copied to /home/windi/engine/
□ Frontend file copied to static folder
□ windi_law_app.py patched with router
```

## F.2 Deploy Script

```bash
#!/bin/bash
# W-DRAGON-001 Deploy Script

# 1. Copy files
scp w_dragon_001.py windi@87.106.29.233:/home/windi/engine/
scp w_dragon_001_law_routes.py windi@87.106.29.233:/home/windi/engine/
scp windi_dragon_ui.js windi@87.106.29.233:/home/windi/law/static/

# 2. SSH and configure
ssh windi@87.106.29.233 << 'EOF'
  # Install deps
  pip install --break-system-packages httpx reportlab pypdf

  # Add env vars if missing
  echo "LEDGER_TOKEN=your_token" >> /home/windi/engine/.env
  echo "LEDGER_URL=http://127.0.0.1:8101" >> /home/windi/engine/.env

  # Restart
  sudo systemctl restart windi-law
EOF

# 3. Verify
curl http://87.106.29.233:8122/dragon/health
```

## F.3 Post-Deploy Verification

| Test | Command | Expected |
|------|---------|----------|
| Health | `curl .../dragon/health` | `{"status": "operational"}` |
| Encode | `curl -X POST .../dragon/encode` | receipt_id returned |
| Verify | `curl .../dragon/verify/{id}` | status CONFIRMED |
| PDF | Upload PDF | Sealed PDF returned |

---

# 🅶 SHELF G — OPTICAL (Phase 2)
# Prateleira G — Óptico (Fase 2)

## G.1 UV Reader Architecture

```
Document (physical)
    ↓
UV LED illumination (365nm)
    ↓
Camera capture (RGB)
    ↓
Image processing
    ↓
Grid detection
    ↓
Bit extraction
    ↓
Hash reconstruction
    ↓
Ledger verification
```

## G.2 Camera Reader (Mobile)

### G.2.1 Components

| Component | Technology |
|-----------|------------|
| Camera access | WebRTC / getUserMedia |
| Image processing | Canvas API |
| Grid detection | Edge detection + Hough transform |
| Bit extraction | Threshold + pattern matching |
| Verification | fetch() to /dragon/verify |

### G.2.2 Pipeline (JavaScript)

```javascript
// Phase 2 implementation outline
async function scanDragonGrid(videoStream) {
  // 1. Capture frame
  const frame = captureFrame(videoStream);

  // 2. Detect grid corners
  const corners = detectGridCorners(frame);

  // 3. Perspective transform
  const normalized = perspectiveTransform(frame, corners);

  // 4. Extract 16x16 cells
  const cells = extractCells(normalized, 16, 16);

  // 5. Classify each cell (dragon vs shadow)
  const bits = cells.map(cell => classifyDragon(cell));

  // 6. Reconstruct hash
  const hashHex = bitsToHash(bits);

  // 7. Verify against Ledger
  return await verifyHash(hashHex);
}
```

## G.3 UV Hardware

### G.3.1 Components

| Component | Spec | Source |
|-----------|------|--------|
| UV LED | 365nm, 3W | Standard |
| Camera | 12MP+, no IR filter | Phone/webcam |
| Housing | Dark box / hood | 3D print |
| Filter | UV-blocking for camera | Optional |

### G.3.2 Reading Protocol

```
1. Place document in reading area
2. Activate UV illumination
3. Wait 2s for camera adjustment
4. Capture 3 frames (average for noise reduction)
5. Process and extract grid
6. Query Ledger
7. Display result
```

---

# 🅷 SHELF H — PRINT (Phase 3)
# Prateleira H — Impressão (Fase 3)

## H.1 Print-Optimized Encoding

### H.1.1 Challenges

| Challenge | Impact | Mitigation |
|-----------|--------|------------|
| Printer DPI < 600 | Pattern loss | Require 1200+ DPI |
| Toner spread | Blur | Larger glyphs |
| Scanner noise | Bit errors | Error correction |
| Photocopy | Degradation | "Original only" policy |

### H.1.2 Error Correction (ECC)

```
Original: 256 bits (hash)
    ↓
Reed-Solomon encoding
    ↓
Protected: 256 + 64 bits (with ECC)
    ↓
Grid: 20×16 or 16×20

Recovery: can correct up to 32 bit errors
```

### H.1.3 Redundancy Modes

| Mode | Grid Size | Redundancy | Use Case |
|------|-----------|------------|----------|
| Standard | 16×16 | None | Digital only |
| Protected | 20×16 | RS(32) | Print-safe |
| Maximum | 24×16 | RS(64) + 2× pattern | Archival |

## H.2 Ink Technologies

### H.2.1 Options

| Technology | Visibility | Equipment | Cost |
|------------|------------|-----------|------|
| Low-opacity | Very faint | Standard printer | Low |
| UV-reactive | Invisible (visible under UV) | UV printer | Medium |
| IR-absorbing | Invisible | IR printer | High |
| Metameric | Color-matching | Specialty | Very high |

### H.2.2 Recommended for MVP

```
PHASE 3a: Low-opacity standard printing
  - 7% opacity black
  - 1200 DPI laser printer
  - Reed-Solomon ECC
  - Works with any scanner

PHASE 3b: UV-reactive (future)
  - Dedicated UV ink
  - Special cartridge
  - Full invisibility
```

---

# 📋 MASTER CHECKLIST
# Lista Mestra de Verificação

## Phase 1.5 — WINDI-LAW Integration

### Step 1: Backend Setup
```
□ Copy w_dragon_001.py to /home/windi/engine/
□ Copy w_dragon_001_law_routes.py to /home/windi/engine/
□ Run: pip install --break-system-packages httpx reportlab pypdf
□ Configure .env with LEDGER_TOKEN
□ Verify: python3 -c "from w_dragon_001 import encode_document; print('OK')"
```

### Step 2: App Integration
```
□ Edit windi_law_app.py:
  □ Add: import sys; sys.path.insert(0, '/home/windi/engine')
  □ Add: from w_dragon_001_law_routes import dragon_router
  □ Add: app.include_router(dragon_router)
□ Restart: sudo systemctl restart windi-law
□ Test: curl http://localhost:8122/dragon/health
```

### Step 3: Frontend Setup
```
□ Copy windi_dragon_ui.js to /home/windi/law/static/
□ Add to workspace HTML:
  □ <div id="windi-dragon-panel"></div>
  □ <script src="/static/windi_dragon_ui.js"></script>
□ Test: Open workspace, verify panel appears
```

### Step 4: End-to-End Test
```
□ Create test document in workspace
□ Click "ENCODE → LEDGER"
□ Verify:
  □ Dragon grid displays
  □ Receipt ID shows
  □ Ledger status = CONFIRMED
□ Click "VERIFY"
□ Verify:
  □ Ledger returns valid response
□ Export PDF
□ Verify:
  □ PDF contains dragon overlay (visible at 400% zoom)
  □ Headers contain X-WINDI-Receipt
```

### Step 5: Documentation
```
□ Update CLAUDE.md with W-DRAGON-001 entry
□ Add to CHANGELOG.md
□ Create git commit:
  git add . && git commit -m "§151: W-DRAGON-001 Phase 1.5 — Dragon Shadow Forest LIVE"
```

---

## Phase 2 — Camera Reader (Future)

```
□ WebRTC camera access module
□ Grid detection algorithm
□ Bit extraction pipeline
□ Mobile-optimized UI
□ Offline verification mode
□ UV LED integration guide
```

## Phase 3 — Print Optimization (Future)

```
□ Reed-Solomon ECC implementation
□ Printer calibration profiles
□ Scanner calibration profiles
□ Physical testing protocol
□ Archival mode (maximum redundancy)
```

---

# 🐉 QUICK REFERENCE CARD
# Cartão de Referência Rápida

## Endpoints

```
GET  /dragon/health           # Status check
POST /dragon/encode           # Text → receipt + SVG
POST /dragon/encode-pdf       # PDF → sealed PDF
GET  /dragon/verify/{id}      # Ledger lookup
```

## Key Values

```
Grid:      16×16 = 256 bits
Hash:      SHA-256
Opacity:   0.07 (print) / 0.18 (screen)
Schema:    W-DRAGON-001-v1
```

## Files

```
Backend:   /home/windi/engine/w_dragon_001.py
Routes:    /home/windi/engine/w_dragon_001_law_routes.py
Frontend:  /home/windi/law/static/windi_dragon_ui.js
Config:    /home/windi/engine/.env
```

## Test Commands

```bash
# Health
curl http://localhost:8122/dragon/health

# Encode text
curl -X POST http://localhost:8122/dragon/encode \
  -H 'Content-Type: application/json' \
  -d '{"content": "Test document"}'

# Encode PDF
curl -X POST http://localhost:8122/dragon/encode-pdf \
  -F 'file=@document.pdf' -o sealed.pdf

# Verify
curl http://localhost:8122/dragon/verify/WINDI-DSF-...
```

---

*Liga IA+H — Kempten, Bavaria · 2026*
*"AI processes. Human decides. WINDI guarantees."*
*"Proof that reveals itself — not proof that declares."*

**OM SHANTI** 🐉
