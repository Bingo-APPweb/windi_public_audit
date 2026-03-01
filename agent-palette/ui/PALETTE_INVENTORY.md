# WINDI PALETTE TOOL INVENTORY

> **Generated:** 2026-03-01
> **Source:** `/opt/windi/agent-palette/ui/index.html` (307.7 KB, ~8000 lines)
> **Status:** ~70% LIVE | ~20% PARTIAL | ~10% FALLBACK

---

## EXECUTIVE SUMMARY

The WINDI Palette is a **sovereign document production desktop** with integrated forensic infrastructure. The core pipeline (document creation → sealing → export → ledger → vault) is fully functional. Distribution channels and productivity tools need completion.

---

## ARCHITECTURE OVERVIEW

```mermaid
graph TB
    subgraph USER["👤 USER INTERFACE"]
        CHAT["💬 Chat"]
        DOCS["📄 Docs"]
        DESK["🎨 Desk"]
        WALLET["👛 Wallet"]
        SEARCH["🔍 Search"]
        FILES["📁 Files"]
        JOURNAL["📰 Journal"]
        INSIGHTS["🧠 Insights"]
        PRODUCTS["🛒 Products"]
        HISTORY["🕐 History"]
    end

    subgraph DRAGONS["🐉 DRAGON LAYER"]
        GUARDIAN["🛡️ Guardian"]
        ARCHITECT["🏗️ Architect"]
        WITNESS["👁️ Witness"]
    end

    subgraph FORENSIC["🔐 FORENSIC LAYER"]
        LEDGER["📒 Ledger :8101"]
        VAULT["🏛️ Vault :8106"]
        EXPORT["📦 Export :8103"]
        SENTINEL["🛡️ Sentinel :8102"]
    end

    subgraph DISTRIBUTION["📡 DISTRIBUTION"]
        EMAIL["📧 Email"]
        WHATSAPP["💬 WhatsApp"]
        SMS["📱 SMS"]
        COMMUNIQUE["📰 Communiqué :8105"]
    end

    CHAT --> DRAGONS
    DOCS --> EXPORT
    DRAGONS --> FORENSIC
    EXPORT --> LEDGER
    EXPORT --> VAULT
    DOCS --> DISTRIBUTION

    style CHAT fill:#4ade80,stroke:#22c55e
    style DOCS fill:#4ade80,stroke:#22c55e
    style DESK fill:#4ade80,stroke:#22c55e
    style WALLET fill:#4ade80,stroke:#22c55e
    style SEARCH fill:#4ade80,stroke:#22c55e
    style JOURNAL fill:#fbbf24,stroke:#f59e0b
    style FILES fill:#fbbf24,stroke:#f59e0b
    style INSIGHTS fill:#fbbf24,stroke:#f59e0b
    style PRODUCTS fill:#ef4444,stroke:#dc2626
    style HISTORY fill:#ef4444,stroke:#dc2626
    style LEDGER fill:#4ade80,stroke:#22c55e
    style VAULT fill:#4ade80,stroke:#22c55e
    style EXPORT fill:#4ade80,stroke:#22c55e
    style SENTINEL fill:#ef4444,stroke:#dc2626
    style EMAIL fill:#fbbf24,stroke:#f59e0b
    style WHATSAPP fill:#fbbf24,stroke:#f59e0b
    style SMS fill:#fbbf24,stroke:#f59e0b
    style COMMUNIQUE fill:#fbbf24,stroke:#f59e0b
```

---

## SIDEBAR TABS INVENTORY

```mermaid
graph LR
    subgraph LIVE["✅ LIVE"]
        C1["💬 Chat"]
        C2["📄 Docs"]
        C3["🎨 Desk"]
        C4["👛 Wallet"]
        C5["🔍 Search"]
    end

    subgraph PARTIAL["⚠️ PARTIAL"]
        P1["🧠 Insights"]
        P2["📁 Files"]
        P3["📰 Journal"]
    end

    subgraph FALLBACK["🔲 FALLBACK"]
        F1["🛒 Products"]
        F2["🕐 History"]
    end

    style C1 fill:#4ade80
    style C2 fill:#4ade80
    style C3 fill:#4ade80
    style C4 fill:#4ade80
    style C5 fill:#4ade80
    style P1 fill:#fbbf24
    style P2 fill:#fbbf24
    style P3 fill:#fbbf24
    style F1 fill:#ef4444
    style F2 fill:#ef4444
```

| # | Tab | Icon | Status | BE Endpoint | Output | Forensic |
|---|-----|------|--------|-------------|--------|----------|
| 1 | Chat | 💬 | ✅ LIVE | Dragon :8108, Local Motor | Messages, Documents | Via Events |
| 2 | Docs | 📄 | ✅ LIVE | Export :8103, Ledger :8101 | PDF/JMPG, Receipts | YES |
| 3 | Desk | 🎨 | ✅ LIVE | Local | Canvas layers | NO |
| 4 | Wallet | 👛 | ✅ LIVE | Local | DID, Trust, Receipts | YES |
| 5 | Search | 🔍 | ✅ LIVE | Local | Filtered results | NO |
| 6 | Files | 📁 | ⚠️ PARTIAL | localStorage | Doc list | NO |
| 7 | Journal | 📰 | ⚠️ PARTIAL | Communiqué :8105 | Article list | NO |
| 8 | Insights | 🧠 | ⚠️ PARTIAL | Cognition (demo) | Demo insights | NO |
| 9 | Products | 🛒 | 🔲 FALLBACK | — | — | — |
| 10 | History | 🕐 | 🔲 FALLBACK | — | — | — |

---

## DOCUMENT TYPES (16 Total)

```mermaid
graph TB
    subgraph FREE["🆓 FREE TIER - 6 Types"]
        F1["✉️ Letter"]
        F2["📧 Email"]
        F3["📝 Note"]
        F4["📋 Memo"]
        F5["📖 Journal"]
        F6["🍳 Recipe"]
    end

    subgraph MED["💼 MED TIER - 6 Types"]
        M1["📊 Report"]
        M2["📜 Contract"]
        M3["💰 Invoice"]
        M4["📒 Protocol"]
        M5["🔬 Analysis"]
        M6["📽️ Presentation"]
    end

    subgraph HIGH["👑 HIGH TIER - 4 Types"]
        H1["📡 Communiqué"]
        H2["🏛️ Certificate"]
        H3["🎨 Creative Virtue"]
        H4["📄 Brief"]
    end

    FREE --> SEAL["🔐 Seal Engine"]
    MED --> SEAL
    HIGH --> SEAL
    SEAL --> EXPORT["📦 Export JMPG"]
    EXPORT --> LEDGER["📒 Ledger"]
    EXPORT --> VAULT["🏛️ Vault"]

    style F1 fill:#4ade80
    style F2 fill:#4ade80
    style F3 fill:#4ade80
    style F4 fill:#4ade80
    style F5 fill:#4ade80
    style F6 fill:#4ade80
    style M1 fill:#60a5fa
    style M2 fill:#60a5fa
    style M3 fill:#60a5fa
    style M4 fill:#60a5fa
    style M5 fill:#60a5fa
    style M6 fill:#60a5fa
    style H1 fill:#a78bfa
    style H2 fill:#a78bfa
    style H3 fill:#a78bfa
    style H4 fill:#a78bfa
```

### Document Type Details

| Tier | Type | Icon | Complexity | Seal | Dragon DNA | Status |
|------|------|------|------------|------|------------|--------|
| FREE | Letter | ✉️ | STRUCTURED | Merkle | Yes | ✅ LIVE |
| FREE | Email | 📧 | STRUCTURED | Merkle | Yes | ✅ LIVE |
| FREE | Note | 📝 | SIMPLE | SHA-256 | Yes | ✅ LIVE |
| FREE | Memo | 📋 | STRUCTURED | Merkle | Yes | ✅ LIVE |
| FREE | Journal | 📖 | SIMPLE | SHA-256 | Yes | ✅ LIVE |
| FREE | Recipe | 🍳 | STRUCTURED | SHA-256 | Yes | ✅ LIVE |
| MED | Report | 📊 | STRUCTURED | Merkle | Yes | ✅ LIVE |
| MED | Contract | 📜 | FORM | Merkle | Yes | ✅ LIVE |
| MED | Invoice | 💰 | FORM | Merkle | Yes | ✅ LIVE |
| MED | Protocol | 📒 | STRUCTURED | SHA-256 | Yes | ✅ LIVE |
| MED | Analysis | 🔬 | STRUCTURED | SHA-256 | Yes | ✅ LIVE |
| MED | Presentation | 📽️ | STRUCTURED | SHA-256 | Yes | ✅ LIVE |
| HIGH | Communiqué | 📡 | GOVERNANCE | Merkle | Yes | ✅ LIVE |
| HIGH | Certificate | 🏛️ | GOVERNANCE | Merkle | Yes | ✅ LIVE |
| HIGH | Creative Virtue | 🎨 | GOVERNANCE | Merkle | Yes | ✅ LIVE |
| HIGH | Brief | 📄 | GOVERNANCE | Merkle | Yes | ✅ LIVE |

---

## FORENSIC PIPELINE

```mermaid
sequenceDiagram
    participant U as 👤 User
    participant FE as 💻 Palette FE
    participant DNA as 🧬 DNA Flow
    participant SEAL as 🔐 Seal Engine
    participant EXP as 📦 Export :8103
    participant LED as 📒 Ledger :8101
    participant VAU as 🏛️ Vault :8106

    U->>FE: Write document
    FE->>DNA: Guided field capture
    DNA->>FE: docFields populated
    U->>FE: Click Finalize
    FE->>SEAL: buildSealPayloadWithProgress()
    Note over SEAL: SHA-256 per field<br/>Merkle root computation<br/>GDPR redaction
    SEAL->>FE: Receipt with hash
    FE->>FE: EventBus.emit(DOCUMENT_SEALED)
    FE->>EXP: POST /api/export/jmpg
    EXP->>FE: JMPG binary + filename
    FE->>U: Download JMPG
    FE->>LED: POST /api/receipts
    LED->>FE: ledgerRegistered: true
    FE->>VAU: Stats refresh
    VAU->>FE: Pulse animation
```

### Pipeline Status

| Step | Component | Status | Notes |
|------|-----------|--------|-------|
| 1 | Document Creation | ✅ LIVE | All 16 types |
| 2 | DNA Guided Flow | ✅ LIVE | Field-by-field capture |
| 3 | Finalize Modal | ✅ LIVE | 2-step validation |
| 4 | Merkle Root | ✅ LIVE | Real SHA-256 |
| 5 | GDPR Redaction | ✅ LIVE | PII fields masked |
| 6 | Receipt Generation | ✅ LIVE | Cryptographic hash |
| 7 | EventBus Emission | ✅ LIVE | DOCUMENT_SEALED |
| 8 | Export JMPG | ✅ LIVE | Binary download |
| 9 | Ledger Registration | ⚠️ PARTIAL | API called, no verification |
| 10 | Vault Update | ⚠️ PARTIAL | Stats refresh, no storage |

---

## BACKEND SERVICES

```mermaid
graph TB
    subgraph ACTIVE["✅ ACTIVELY USED"]
        D["🐉 Dragon :8108"]
        L["📒 Ledger :8101"]
        E["📦 Export :8103"]
        V["🏛️ Vault :8106"]
        C["📰 Communiqué :8105"]
    end

    subgraph PARTIAL["⚠️ PARTIALLY WIRED"]
        DT["🖥️ Desktop :8110"]
    end

    subgraph UNUSED["🔲 NOT WIRED"]
        S["🛡️ Sentinel :8102"]
        CX["🧠 Cortex :8889"]
        SC["🔌 Schnittstelle :8095"]
        BR["🌉 Bridge :8097"]
        ID["🆔 ID Genesis :8096"]
        PU["💓 Pulse :8109"]
    end

    style D fill:#4ade80
    style L fill:#4ade80
    style E fill:#4ade80
    style V fill:#4ade80
    style C fill:#4ade80
    style DT fill:#fbbf24
    style S fill:#ef4444
    style CX fill:#ef4444
    style SC fill:#ef4444
    style BR fill:#ef4444
    style ID fill:#ef4444
    style PU fill:#ef4444
```

### Endpoint Details

| Service | Port | Endpoints | Status |
|---------|------|-----------|--------|
| Dragon | 8108 | `POST /api/dragon` | ✅ Wired |
| Ledger | 8101 | `GET /health`, `POST /api/receipts` | ✅ Wired |
| Export | 8103 | `POST /api/export/jmpg` | ✅ Wired |
| Vault | 8106 | `GET /api/stats`, `GET /health` | ✅ Wired |
| Communiqué | 8105 | `GET /api/communique/list`, `/stats` | ✅ Wired |
| Desktop | 8110 | `POST /api/documents/create-from-dragon` | ⚠️ Partial |
| Sentinel | 8102 | — | 🔲 Not wired |
| Cortex | 8889 | — | 🔲 Not wired |

---

## FEATURE MODULES

### 1. Chat & Dragon Integration

```mermaid
graph LR
    subgraph CHAT["💬 Chat System"]
        LM["🔧 Local Motor<br/>(FREE)"]
        DG["🐉 Dragon<br/>(MED/HIGH)"]
        DNA["🧬 DNA Flow"]
    end

    LM --> |Deterministic| RESP["Response"]
    DG --> |Constitutional| RESP
    DNA --> |Field Capture| DOC["Document"]

    style LM fill:#4ade80
    style DG fill:#4ade80
    style DNA fill:#4ade80
```

| Feature | Status | Notes |
|---------|--------|-------|
| Local Motor (FREE) | ✅ LIVE | Deterministic responses |
| Dragon Chat (MED/HIGH) | ✅ LIVE | Constitutional AI |
| DNA Guided Flow | ✅ LIVE | Step-by-step fields |
| Document Extraction | ✅ LIVE | JSON blocks from Dragon |
| Title Capture | ✅ LIVE | awaitingTitle flag |

### 2. Wallet & DID

```mermaid
graph TB
    DID["🆔 DID Creation"]
    WALLET["👛 Wallet State"]
    TRUST["📊 Trust Score"]
    RECEIPTS["🧾 Receipts"]

    DID --> WALLET
    WALLET --> TRUST
    WALLET --> RECEIPTS
    TRUST --> |+2 per seal| TRUST

    style DID fill:#4ade80
    style WALLET fill:#4ade80
    style TRUST fill:#4ade80
    style RECEIPTS fill:#4ade80
```

| Feature | Status | Notes |
|---------|--------|-------|
| DID Modal | ✅ LIVE | PF/PJ selector |
| Wallet Creation | ✅ LIVE | localStorage |
| Trust Score | ✅ LIVE | +2 per finalized doc |
| Receipt Tracking | ✅ LIVE | Array in wallet |
| Persistence | ✅ LIVE | CONFIG.STORAGE_KEY |

### 3. Distribution Channels

```mermaid
graph TB
    DIST["📡 Distribution Modal"]

    subgraph CHANNELS["Channels"]
        EM["📧 Email"]
        WA["💬 WhatsApp"]
        SM["📱 SMS"]
    end

    DIST --> EM
    DIST --> WA
    DIST --> SM
    EM --> |"⚠️ UI only"| SEND["Send Handler"]
    WA --> |"⚠️ UI only"| SEND
    SM --> |"⚠️ UI only"| SEND

    style DIST fill:#fbbf24
    style EM fill:#fbbf24
    style WA fill:#fbbf24
    style SM fill:#fbbf24
    style SEND fill:#ef4444
```

| Feature | Status | Notes |
|---------|--------|-------|
| Distribute Modal | ⚠️ PARTIAL | UI complete |
| Email Channel | ⚠️ PARTIAL | Form exists, no send |
| WhatsApp Channel | ⚠️ PARTIAL | Field exists, not wired |
| SMS Channel | ⚠️ PARTIAL | Field exists, no API |
| Schedule Send | 🔲 FALLBACK | Button exists, no calendar |
| Recipient List | ✅ LIVE | Add/remove in UI |

### 4. Free Desk (Canvas Editor)

| Feature | Status | Notes |
|---------|--------|-------|
| Canvas Rendering | ✅ LIVE | SVG + grid |
| Layer Management | ✅ LIVE | Add/remove/duplicate |
| Text Editing | ✅ LIVE | contentEditable |
| Image Upload | ✅ LIVE | FileAPI |
| Drag & Drop | ✅ LIVE | Mouse events |
| Resize Handles | ✅ LIVE | 8-point |
| Z-Order | ✅ LIVE | Forward/backward |
| Undo/Redo | ✅ LIVE | History array |
| Grid Toggle | ✅ LIVE | Show/hide |
| Zoom | ✅ LIVE | 0.3x - 2.0x |
| Export to JMPG | ⚠️ PARTIAL | Finalize exists |

---

## GAPS & PRIORITIES

```mermaid
graph TB
    subgraph SPRINT1["🔴 Sprint 1: Core"]
        S1A["Distribution Wiring"]
        S1B["Communiqué Creation"]
    end

    subgraph SPRINT2["🟡 Sprint 2: Productivity"]
        S2A["Insights Real API"]
        S2B["History Timeline"]
    end

    subgraph SPRINT3["🟢 Sprint 3: Scale"]
        S3A["Products Catalog"]
        S3B["Voice STT"]
        S3C["File Import/Export"]
    end

    SPRINT1 --> SPRINT2 --> SPRINT3

    style S1A fill:#ef4444
    style S1B fill:#ef4444
    style S2A fill:#fbbf24
    style S2B fill:#fbbf24
    style S3A fill:#4ade80
    style S3B fill:#4ade80
    style S3C fill:#4ade80
```

### Priority Matrix

| Priority | Feature | Current | To Breathe |
|----------|---------|---------|------------|
| 🔴 HIGH | Distribution | ⚠️ UI only | Wire to Desktop :8110 |
| 🔴 HIGH | Communiqué Creation | ⚠️ List only | Add creation form in chat |
| 🟡 MED | Insights | 🔲 Demo | Fetch from Cognition API |
| 🟡 MED | History | 🔲 Empty | Action timeline |
| 🟢 LOW | Products | 🔲 Empty | Template catalog |
| 🟢 LOW | Voice | 🔲 Paste | Web Speech API |
| 🟢 LOW | Files | ⚠️ Local | Import/export external |

---

## TIER FEATURE MATRIX

| Feature | FREE | MED | HIGH |
|---------|------|-----|------|
| Chat (Local Motor) | ✅ | ✅ | ✅ |
| Chat (Dragon) | ❌ | ✅ | ✅ |
| Documents (6 base) | ✅ | ✅ | ✅ |
| Documents (MED+, 6) | ❌ | ✅ | ✅ |
| Documents (HIGH, 4) | ❌ | ❌ | ✅ |
| Export JMPG | ✅ | ✅ | ✅ |
| Forensic Ledger | ✅ | ✅ | ✅ |
| Vault Stats | ❌ | ✅ | ✅ |
| DID (Wallet) | ✅ | ✅ | ✅ |
| Distribution | ❌ | ✅ | ✅ |
| Communiqué View | ❌ | ❌ | ✅ |
| Insights | ❌ | ✅ | ✅ |
| Desk (Canvas) | ✅ | ✅ | ✅ |

---

## FALLBACK & PLACEHOLDER INDICATORS

### Found in Code

```javascript
// Products tab - button only, no UI
{id:"products",icon:"🛒",klass:"extra"}

// History tab - button only
{id:"history",icon:"🕐",klass:"extra"}

// DEMO_INSIGHTS fallback
const DEMO_INSIGHTS = {
  en: [{ type: 'momentum_score', text: '**MOMENTUM SCORE: 7.3 → 7.8**...' }],
  ...
};

// TODO: Wire to real actions
// TODO: Wire to real actions (invite_core_to_did, view_momentum_details, etc.)
```

---

## CONCLUSION

### What Works (✅ LIVE)

1. **Full Document Lifecycle** - All 16 types with real output
2. **Forensic Sealing** - Merkle roots, SHA-256, receipts
3. **Export Pipeline** - JMPG binary downloads
4. **Dragon Integration** - Constitutional chat, document extraction
5. **DID/Wallet** - Complete identity system
6. **Desk Canvas** - Full editor with layers

### What Needs Work (⚠️ PARTIAL)

1. **Distribution** - UI exists, no actual sending
2. **Communiqué** - List works, no creation
3. **Insights** - Always demo data
4. **Journal** - Fetch works, read-only

### What's Empty (🔲 FALLBACK)

1. **Products** - Button only
2. **History** - Button only
3. **Voice STT** - Manual paste

---

*"Gavetas principais estão cheias. Faltam as gavetas de conveniência."*

*ONE TREE respira. Cada ramo precisa de frutos.* 🌳🐉
