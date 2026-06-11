# WINDI SEAL V2 — Code Audit Report
**Data:** 2026-06-11
**Artifact:** `windi-seal-v2.html` v2.5 · Hash: `6777b4017799ac13`
**Auditor:** CCode (Architect) + Human Dragon (Discovery)
**Propósito:** Identificar gaps entre Manual de Arquitectura e implementação real

---

## Metodologia

1. Leitura do Manual de Arquitectura (v1.md)
2. Varredura do código fonte (windi-seal-v2.html)
3. Comparação: claim vs reality
4. Classificação: ✅ Funciona | ⚠️ Gap | 🔴 Crítico

---

## 1. Capture Flow

### 1.1 Photo Capture
| Claim | Code Line | Reality | Status |
|-------|-----------|---------|--------|
| Camera activates | 319-326 | `getUserMedia()` + viewfinder | ✅ |
| Front/back flip | 322, 397-401 | `facingMode` toggle | ✅ |
| Photo captured | 327 | `canvas.toBlob()` → `capturedFile` | ✅ |
| Hash computed locally | 517, 507-513 | `crypto.subtle.digest('SHA-256')` | ✅ |

### 1.2 Video Recording
| Claim | Code Line | Reality | Status |
|-------|-----------|---------|--------|
| Recording starts | 330-340 | `MediaRecorder` API | ✅ |
| REC indicator | 337, 47-50 | `.rec-indicator` animado | ✅ |
| Safari iOS fix | 333-339 | mp4 fallback se webm não suportado | ✅ v2.5 |
| Video saved | 339 | `capturedFile` set com blob | ✅ |

### 1.3 Audio Recording
| Claim | Code Line | Reality | Status |
|-------|-----------|---------|--------|
| Audio-only mode | — | **NÃO IMPLEMENTADO** | 🔴 GAP |

**FINDING:** O manual menciona áudio, mas o código só tem photo/video/upload. Falta modo áudio standalone.

### 1.4 File Persistence
| Claim | Code Line | Reality | Status |
|-------|-----------|---------|--------|
| File saved to device | 614 | Download button exists | ⚠️ UX GAP |
| Auto-save | — | **NÃO EXISTE** | 🔴 GAP |
| Save prompt | — | **NÃO EXISTE** | 🔴 GAP |

**FINDING (Human Dragon):** Após seal, botão Download existe mas:
- Não é proeminente
- Não há prompt "Guarde o seu ficheiro antes de sair"
- Se utilizador fecha página → media perdida para sempre
- Receipt existe no Ledger mas ficheiro original desapareceu

---

## 2. Verify Flow

### 2.1 Three States
| State | Code Line | Trigger | Status |
|-------|-----------|---------|--------|
| MOMENTO PRESERVADO | 562-568 | API `ok:true` | ✅ |
| DEMONSTRAÇÃO | 591-594 | hash `demo`/`DEMO` | ✅ |
| NÃO ENCONTRADO | 583-590 | API `ok:false` | ✅ |

### 2.2 Suffix Lookup (Gate 0 Fix)
| Claim | Reality | Status |
|-------|---------|--------|
| Short IDs resolve | `7A1A5282` → full receipt | ✅ FIXED |

---

## 3. Editor Flow

### 3.1 Composition
| Feature | Code Line | Status |
|---------|-----------|--------|
| Background image | 412-425 | ✅ |
| PiP video overlay | 426-445 | ✅ |
| 9-position grid | 464-474 | ✅ |
| Text overlay | 475-480 | ✅ |
| Export composition | 481-489 | ✅ |
| Lineage tracking | 416-419 | ✅ `sourceHash` set |

---

## 4. UI/UX Gaps

### 4.1 Critical UX Issues

| Issue | Severity | Description | Proposed Fix |
|-------|----------|-------------|--------------|
| **Media Loss Risk** | 🔴 CRITICAL | User can seal but lose original file | Add "Save File" step before/after seal |
| **No Audio Mode** | 🔴 HIGH | Manual claims audio, code only has photo/video | Add audio capture mode |
| **Download Hidden** | ⚠️ MEDIUM | Download button not prominent | Redesign result UI |
| **No Exit Warning** | ⚠️ MEDIUM | Page close loses unsaved media | Add `beforeunload` warning |

### 4.2 Proposed Solutions

#### Solution A: Auto-Download After Seal
```javascript
// After successful seal, auto-trigger download
if(capturedFile){
  const a=document.createElement('a');
  a.href=URL.createObjectURL(capturedFile);
  a.download=capturedFile.name;
  a.click();
}
```

#### Solution B: Prominent Save Step
```html
<!-- Before seal, show save reminder -->
<div class="save-reminder">
  ⚠️ Guarde o ficheiro ANTES de selar!
  <button id="saveFirst">📥 Guardar Agora</button>
</div>
```

#### Solution C: Exit Warning
```javascript
window.onbeforeunload = function(){
  if(capturedFile) return "Tem um ficheiro não guardado!";
};
```

#### Solution D: Audio Mode
```javascript
// Add audio-only recording mode
function startAudioRecording(){
  navigator.mediaDevices.getUserMedia({audio:true,video:false})
    .then(stream=>{
      // MediaRecorder for audio-only
    });
}
```

---

## 5. Security & Privacy

| Claim | Reality | Status |
|-------|---------|--------|
| Zero-upload | ✅ Hash only, no file upload | ✅ |
| Local hash | ✅ `crypto.subtle` in browser | ✅ |
| HTTPS required | ✅ Camera requires secure context | ✅ |
| No server storage | ✅ Only receipt metadata | ✅ |

---

## 6. Browser Compatibility

| Browser | Photo | Video | Audio | Verify |
|---------|-------|-------|-------|--------|
| Chrome Desktop | ✅ | ✅ webm | ⏳ | ✅ |
| Chrome Android | ⏳ G-SURF-3 | ⏳ G-SURF-3 | ⏳ | ⏳ |
| Safari macOS | ✅ | ⚠️ mp4 | ⏳ | ✅ |
| Safari iOS | ⏳ G-SURF-3 | ⏳ v2.5 fix | ⏳ | ⏳ |
| Firefox | ✅ | ✅ webm | ⏳ | ✅ |

---

## 7. Summary of Findings

### Critical Gaps (🔴)
1. **Media Persistence** — File can be lost after seal
2. **Audio Mode** — Claimed but not implemented

### High Priority (⚠️)
3. **Download UX** — Button exists but not prominent
4. **Exit Warning** — No protection against accidental loss
5. **Mobile Testing** — G-SURF-3 pending

### Working Features (✅)
- Photo/Video capture
- SHA-256 local hashing
- Three seal types (Capture/Composition/Narrative)
- Editor mode with PiP
- Lineage tracking
- Verify with 3 states
- Gate 0 suffix lookup
- Safari iOS codec fix
- Trilingual UI
- NOIR/KLAR themes

---

## 8. Recommendations for Advisors

### Immediate Actions (Before Demo)
1. Fix Media Persistence UX — add auto-download or save step
2. Add Exit Warning — prevent accidental loss
3. Complete G-SURF-3 — real device testing

### Short Term (Week)
4. Implement Audio Mode
5. Redesign result screen with prominent save
6. Add "Save to Photos" for mobile

### Medium Term (Month)
7. IndexedDB local cache for recent seals
8. QR code with download link
9. Share API integration (mobile)

---

*AI processes. Human decides. WINDI guarantees.*
