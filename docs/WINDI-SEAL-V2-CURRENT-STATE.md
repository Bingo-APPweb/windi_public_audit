# WINDI SEAL V2.6 — Current State Diagram
**Data:** 2026-06-11 · **Hash:** `28e0073b6d0ad9ec`
**Propósito:** Visualização exacta do código actual para detecção de gaps por IAs do Conselho
**Status:** 🟢 GAPS CRÍTICOS CORRIGIDOS

---

## 1. Architecture Overview (ACTUAL)

```mermaid
flowchart TB
    subgraph CLIENT ["📱 Browser (Client-Side)"]
        UI[UI: windi-seal-v2.html]
        CAM[Camera API]
        MIC[Microphone API]
        HASH[crypto.subtle.digest]
        MEM[Memory: capturedFile]
    end

    subgraph SERVER ["🖥️ Strato Server"]
        API[":8101 Forensic Ledger API"]
        DB[(SQLite: 57k+ receipts)]
        MERKLE[Merkle Tree]
    end

    UI --> CAM
    UI --> MIC
    CAM --> MEM
    MIC --> MEM
    MEM --> HASH
    HASH -->|"POST hash only"| API
    API --> DB
    API --> MERKLE

    style MEM fill:#ff6b6b,stroke:#c92a2a,color:#fff
    style MIC fill:#868e96,stroke:#495057,color:#fff
```

**🔴 GAPS VISÍVEIS:**
- `MEM` (vermelho): Ficheiro em memória, pode perder-se
- `MIC` (cinzento): Áudio não implementado

---

## 2. Capture Flow (ACTUAL)

```mermaid
flowchart LR
    subgraph MODES ["Capture Modes"]
        PHOTO[📷 Photo]
        VIDEO[🎬 Video]
        AUDIO[🎙️ Audio]
        UPLOAD[📁 Upload]
        HASH_IN[#️⃣ Hash Input]
    end

    subgraph IMPLEMENTATION
        P_IMPL[✅ Line 319-327]
        V_IMPL[✅ Line 330-340]
        A_IMPL[❌ NOT IMPLEMENTED]
        U_IMPL[✅ Line 364]
        H_IMPL[✅ Line 362-363]
    end

    PHOTO --> P_IMPL
    VIDEO --> V_IMPL
    AUDIO --> A_IMPL
    UPLOAD --> U_IMPL
    HASH_IN --> H_IMPL

    style AUDIO fill:#ff6b6b,stroke:#c92a2a,color:#fff
    style A_IMPL fill:#ff6b6b,stroke:#c92a2a,color:#fff
```

---

## 3. Post-Capture Flow (ACTUAL) — WHERE GAP LIVES

```mermaid
flowchart TD
    CAPTURE[Capture Complete] --> FILE_MEM[capturedFile in Memory]
    FILE_MEM --> SHOW[showCaptured: Preview]
    SHOW --> SEAL_BTN[User Clicks SEAL]
    SEAL_BTN --> COMPUTE[computeHash: SHA-256]
    COMPUTE --> API_CALL[POST to /api/receipts]
    API_CALL --> RESULT[showResult: Verdict Card]

    RESULT --> BTN_DL[📥 Download Button]
    RESULT --> BTN_SHARE[📤 Share Button]
    RESULT --> BTN_NEW[🜂 New Button]

    BTN_DL -->|"User clicks"| SAVE[File Downloaded]
    BTN_DL -->|"User ignores"| LOST[⚠️ FILE LOST ON EXIT]
    BTN_NEW --> RESET[reset: capturedFile = null]

    CLOSE[User Closes Page] --> LOST

    style FILE_MEM fill:#ffa94d,stroke:#e67700
    style LOST fill:#ff6b6b,stroke:#c92a2a,color:#fff
    style BTN_DL fill:#ffa94d,stroke:#e67700
```

**🔴 GAP:** Não há:
1. Auto-download após seal
2. Warning ao fechar página
3. Prompt "Guarde antes de sair"

---

## 4. Verify Flow (ACTUAL)

```mermaid
flowchart TD
    INPUT[User Input: Hash or ID] --> CHECK{What type?}

    CHECK -->|"demo/DEMO"| DEMO[🔵 DEMONSTRAÇÃO]
    CHECK -->|"Other"| API_CALL[GET /api/receipts/ID]

    API_CALL --> RESULT{API Response}

    RESULT -->|"ok: true"| FOUND[🟢 MOMENTO PRESERVADO]
    RESULT -->|"ok: false"| NOT_FOUND[🟡 NÃO ENCONTRADO]

    subgraph GATE_0 ["Gate 0 Fix (✅ FIXED)"]
        SHORT[Short ID: DBED5A85]
        EXACT[Exact Match]
        SUFFIX[Suffix Lookup]
        SHORT --> EXACT
        EXACT -->|"not found"| SUFFIX
        SUFFIX --> FOUND
    end

    style GATE_0 fill:#51cf66,stroke:#2f9e44
```

---

## 5. Editor/Composition Flow (ACTUAL)

```mermaid
flowchart TD
    BG[Load Background Image] --> CANVAS[Draw on Canvas]
    PIP[Load PiP Video] --> CANVAS
    TEXT[Add Text Overlay] --> CANVAS

    CANVAS --> EXPORT[Export as JPEG]
    EXPORT --> COMP_FILE[capturedFile = composition]

    BG -->|"sourceHash set"| LINEAGE[Lineage Tracking ✅]

    COMP_FILE --> SEAL[Seal as COMPOSITION]
    SEAL --> RESULT[Verdict: COMPOSIÇÃO SELADA]

    style LINEAGE fill:#51cf66,stroke:#2f9e44
```

---

## 6. Three Seal Types (ACTUAL)

```mermaid
flowchart LR
    subgraph TYPES ["Seal Type Selection"]
        CAP[🟢 CAPTURE<br/>sealType='capture']
        COMP[🟡 COMPOSITION<br/>sealType='composition']
        NAR[🟣 NARRATIVE<br/>sealType='narrative']
    end

    subgraph TRIGGERS
        T_CAP[Photo/Video direct]
        T_COMP[Editor mode + background]
        T_NAR[Editor + narrativeClass set]
    end

    T_CAP --> CAP
    T_COMP --> COMP
    T_NAR --> NAR

    subgraph MISSING ["❌ Not Yet Connected"]
        NAR_UI[Narrative UI selector]
        NAR_CLASS[narrativeClass input]
    end

    style MISSING fill:#ff6b6b,stroke:#c92a2a,color:#fff
```

**🔴 GAP:** `narrativeClass` e selector UI para NARRATIVE não implementados completamente

---

## 7. Download Handler (ACTUAL CODE)

```mermaid
flowchart TD
    BTN[📥 Download Click] --> CHECK{capturedFile exists?}
    CHECK -->|"Yes"| CREATE[Create <a> element]
    CHECK -->|"No"| NOTHING[Nothing happens]

    CREATE --> BLOB[URL.createObjectURL]
    BLOB --> NAME[a.download = capturedFile.name]
    NAME --> CLICK[a.click → Browser Download]

    subgraph NAMES ["File Names Set"]
        N_PHOTO["'capture.jpg'"]
        N_VIDEO["'video_timestamp.webm/mp4'"]
        N_COMP["'composition_timestamp.jpg'"]
    end

    style CHECK fill:#ffa94d,stroke:#e67700
    style NOTHING fill:#ff6b6b,stroke:#c92a2a,color:#fff
```

---

## 8. What's Missing (GAP SUMMARY) — V2.6 UPDATE

```mermaid
flowchart TD
    subgraph WORKING ["✅ Working (V2.6)"]
        W1[Photo Capture]
        W2[Video Capture]
        W3[🆕 Audio Capture]
        W4[File Upload]
        W5[Hash Input]
        W6[Local SHA-256]
        W7[API POST]
        W8[3 Verdicts]
        W9[Editor Mode]
        W10[Lineage]
        W11[Gate 0 Fix]
        W12[Safari iOS Fix]
        W13[🆕 Auto-Download]
        W14[🆕 Exit Warning]
        W15[Trilingual]
        W16[NOIR/KLAR]
    end

    subgraph FIXED ["🟢 Fixed in V2.6"]
        F1[✅ Audio Capture Mode]
        F2[✅ Auto-Download After Seal]
        F3[✅ Exit Warning]
    end

    subgraph REMAINING ["🟡 Remaining Gaps"]
        G4[Narrative UI Selector]
        G6[Mobile Device Test G-SURF-3]
    end

    subgraph PRIORITY ["Priority"]
        P2[🟡 MEDIUM: G4]
        P3[🟢 PENDING: G6]
    end

    G4 --> P2
    G6 --> P3

    style FIXED fill:#d3f9d8,stroke:#2f9e44
    style WORKING fill:#d3f9d8,stroke:#2f9e44
    style REMAINING fill:#fff3bf,stroke:#e67700
```

---

## 9. Proposed Fix Architecture

```mermaid
flowchart TD
    CAPTURE[Capture Complete] --> FILE_MEM[capturedFile in Memory]
    FILE_MEM --> SHOW[showCaptured: Preview]

    SHOW --> SAVE_PROMPT[⚠️ NEW: Save Prompt]
    SAVE_PROMPT -->|"User saves"| SAVED[✅ File on Device]
    SAVE_PROMPT -->|"User skips"| WARN[Warning: Unsaved]

    WARN --> SEAL_BTN[User Clicks SEAL]
    SAVED --> SEAL_BTN

    SEAL_BTN --> COMPUTE[computeHash]
    COMPUTE --> API_CALL[POST]
    API_CALL --> RESULT[Verdict]

    RESULT --> AUTO_DL[⚠️ NEW: Auto-Download]
    AUTO_DL --> COMPLETE[✅ Hash + File Both Preserved]

    CLOSE[User Closes Page] --> EXIT_WARN[⚠️ NEW: beforeunload]
    EXIT_WARN -->|"Confirm"| LOST[User chose to lose file]
    EXIT_WARN -->|"Cancel"| STAY[User saves first]

    style SAVE_PROMPT fill:#51cf66,stroke:#2f9e44
    style AUTO_DL fill:#51cf66,stroke:#2f9e44
    style EXIT_WARN fill:#51cf66,stroke:#2f9e44
    style COMPLETE fill:#51cf66,stroke:#2f9e44
```

---

## 10. Code Line Reference

| Feature | Line(s) | Status |
|---------|---------|--------|
| Photo capture | 319-327 | ✅ |
| Video capture | 330-340 | ✅ |
| Audio capture | — | ❌ MISSING |
| File upload | 364 | ✅ |
| Hash input | 362-363 | ✅ |
| computeHash | 507-513 | ✅ |
| API call | 517-529 | ✅ |
| showResult | 532-600 | ✅ |
| Download handler | 614 | ⚠️ EXISTS but passive |
| Auto-download | — | ❌ MISSING |
| Exit warning | — | ❌ MISSING |
| Audio mode | — | ❌ MISSING |
| Narrative selector | — | ❌ MISSING |

---

*Este documento permite que qualquer IA do Conselho detecte visualmente onde estão os gaps e o que precisa ser alterado.*

*AI processes. Human decides. WINDI guarantees.*
