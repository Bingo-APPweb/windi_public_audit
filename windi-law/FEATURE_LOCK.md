# WINDI-LAW Feature Lock v1.0
# CONSTITUTIONAL CONTRACT — READ BEFORE ANY EDIT

**Purpose:** This file protects SEALED features from accidental overwrite.
**Rule:** The Gêmeo MUST read this file BEFORE editing any windi-law file.

---

## SEALED FEATURES — DO NOT REMOVE

| # | Feature | File | Key Markers | Status |
|---|---------|------|-------------|--------|
| 1 | **Media Bar** 📎🖼📄🎥 | `prompt-area/index.html` | `cmd-media-bar`, `handleMedia`, `attachedFiles` | SEALED |
| 2 | **SHA-256 client-side** | `prompt-area/index.html` | `hashFile`, `crypto.subtle.digest` | SEALED |
| 3 | **Identity SCHLÜSSEL** | `prompt-area/index.html` | `sb-schluessel`, `sb-key-hash`, `copyFingerprint` | SEALED |
| 4 | **Identity WALLET** | `prompt-area/index.html` | `sb-wallet`, `sb-pioneer-num`, `sb-credits` | SEALED |
| 5 | **ab-seal + Modal I9** | `prompt-area/index.html` | `openSealModal`, `confirmSeal`, `modal-i9` | SEALED |
| 6 | **ab-verify** | `prompt-area/index.html` | `verifyReceipt`, `__lastReceipt` | SEALED |
| 7 | **ab-chain** | `prompt-area/index.html` | `showChain`, `__evidenceChain` | SEALED |
| 8 | **CIA badges** | `prompt-area/index.html` | `updateCIA`, `cia-i9`, `cia-i11` | SEALED |
| 9 | **QR SVG** | `prompt-area/index.html` | `generateQRSVG`, `showQRCode`, `downloadQR` | SEALED |
| 10 | **Wallet Gate Link** | `prompt-area/index.html` | `createWallet`, `/law/gate` redirect | SEALED |
| 11 | **i18n DE/PT/EN** | `prompt-area/index.html` | `var LANG`, `setLang`, `applyI18n` | SEALED |
| 12 | **Theme NOIR/KLAR** | `prompt-area/index.html` | `toggleTheme`, `data-theme` | SEALED |

---

## VERIFICATION MARKERS

Before any commit, run:
```bash
/opt/windi/windi-law/tests/feature-lock-check.sh
```

If ANY marker is missing → **COMMIT BLOCKED**.

---

## RULES FOR THE GÊMEO

1. **READ this file** before editing `prompt-area/` or `workspace/`
2. **NEVER delete** any function listed above
3. **NEVER overwrite** one file with another without checking markers
4. **If copying files** (e.g., workspace → prompt-area), verify ALL markers survive
5. **If a marker is missing**, restore from git history BEFORE commit

---

## WHAT HAPPENED (25 Mar 2026)

The Gêmeo copied `workspace/index.html` to `prompt-area/index.html` without checking.
This overwrote the Media Bar (📎🖼📄🎥) that existed in prompt-area.
Result: Feature lost. User noticed. Had to restore from git.

**This file prevents that from happening again.**

---

## ADDING NEW SEALED FEATURES

When a new feature is complete and tested:
1. Add row to the table above
2. Add marker check to `tests/feature-lock-check.sh`
3. Commit both files together

---

*LIGA IA+H — Kempten, Bavaria · 2026*
*"What is sealed, stays sealed."*
