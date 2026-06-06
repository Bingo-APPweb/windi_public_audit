# SHOT-GRAMMAR-001 — Production Method by Shot Type
## W-HIOS FORENSIC UNIT · O Peso do Eco

**Version:** 1.0
**Created:** 04 Jun 2026
**Method Origin:** Paper-001 Finding 2
**Constitutional Bindings:** I9, I11, I14, I19
**Architecture:** Hybrid (system enforces measurement discipline, human confirms shot type)

---

## 1. Justification

This production method is not an aesthetic preference. It derives directly from **Finding 2** of Paper-001:

> Video generation of bodies-with-faces fails through subject framing loss. The generator does not degrade identity — it SUBSTITUTES the subject by moving them out of frame, turning them around, or filling the frame with other faces.

**The solution:** Do not ask the generator for what it cannot do. Separate shots that carry identity (face) from shots that carry action (body, hands, detail), measuring forensically only the former.

This links the method to the finding and makes the Shot Grammar descend from Paper-001, not float beside it.

---

## 2. Three Shot Types

### IDENTITY
- **Definition:** Face dominates frame. Subject recognizable.
- **Generation:** Joey method (frame-by-frame with anchor reference)
- **Measurement:** SPINE-CAST required. Tier declared (FORENSE ≥0.75 or OPERACIONAL ≥0.65)
- **Seal:** CHARACTER-STATE entry with measurement data
- **State Machine:** PENDING → MEASURED → SEALED

### ACTION
- **Definition:** Body, hands, feet, props, scenery, screen inserts. No measurable face.
- **Generation:** Free generation. No anchor required.
- **Measurement:** SPINE-CAST not applicable.
- **Continuity:** Guaranteed by wardrobe, props, and editing — not by biometrics.
- **State Machine:** GENERATED → APPROVED

### CONFRONT
- **Definition:** Face + full body in same frame.
- **Policy:** MINIMIZE. Avoid where possible through editing.
- **Where inevitable:** Accept lower tier, mark as "continuity by editing, not forensic"
- **State Machine:** PENDING → MEASURED (accept OPERACIONAL) → SEALED with disclaimer

---

## 3. Anti-Estimate Discipline

**Lesson from Paper-001 Errata:** "A number without a measurement run is not a number."

### Rules

1. Every IDENTITY cell has state: `PENDING` → `MEASURED` → `SEALED`
2. No similarity value without `run_id`, `det_score`, and `n_faces`
3. A shot awaiting measurement stays `PENDING` — never filled with expected value
4. System refuses to seal IDENTITY without measurement run
5. System refuses to mark MEASURED without detector metadata

### Hybrid Architecture (Confirmed)

| Component | Enforcement |
|-----------|-------------|
| Measurement discipline | **System enforces** — refuses numbers without run_id |
| Shot type classification | **Human confirms** — proposes type, human approves before seal |
| Tier acceptance | **Human decides** — system shows measurement, human accepts or rejects |

---

## 4. Disambiguation Gate — The Two Marcus

### Problem

The script deliberately creates two grey-haired middle-aged men named Marcus as moral mirrors:
- **Marcus Couto** — Cartel executor, villain
- **Marcus Vance** — Interpol inspector, guardian

If both generate as "grey-haired, 40-50, dark suit", ArcFace may confuse them — or worse, the generator may bleed one into the other.

### Visual Differentiation (Confirmed)

| Character | Defining Trait | In Script |
|-----------|----------------|-----------|
| **Couto** | Clean-shaven, hair slicked back | Line 156-157 |
| **Vance** | Grey beard (short) | **NEW — production decision** |

### Confusion Test Protocol

Before generating any scene with both Marcus characters:

1. Generate Couto anchor (clean-shaven)
2. Generate Vance anchor (grey beard)
3. Measure Couto embedding against Vance anchor
4. **Require:** similarity < 0.50 (well below OPERACIONAL)
5. If ≥ 0.50: anchors too similar, redesign visual differentiation

This gate must pass before Scenes 10-13 (where both may appear) can proceed.

---

## 5. Scene-by-Scene Classification

### Legend

| Symbol | Meaning |
|--------|---------|
| 👤 | IDENTITY shot — requires SPINE-CAST |
| 🎬 | ACTION shot — free generation |
| ⚠️ | CONFRONT shot — minimize, accept lower tier |
| ⭐ | Emotional anchor — highest forensic priority |

---

### COLD OPEN — A ÚLTIMA COISA NORMAL

#### CENA 0 — Coffee Station (3 min)

| Shot | Type | Character | Notes |
|------|------|-----------|-------|
| Bare feet on marble | 🎬 | Gabi | Insert detail |
| Heels beside counter | 🎬 | — | Prop |
| Pen behind ear | 🎬 | Gabi | Insert detail |
| Finger touching screen | 🎬 | Gabi | Hand detail |
| Phone screen (video call) | 🎬 | — | UI insert |
| **Gabi's smile to son** | 👤⭐ | Gabi | Emotional heart — MUST be FORENSE |
| Camera receding through corridor | 🎬 | — | Environment |

---

### ATO I — A QUEDA

#### CENA 1 — Vanguard Office Terminal (2 min)

| Shot | Type | Character | Notes |
|------|------|-----------|-------|
| Screen: extraction progress bar | 🎬 | — | UI insert |
| Hands removing USB token | 🎬 | Gabi | Hand detail |
| Document on table | 🎬 | — | Prop |
| Fiber optic scanner | 🎬 | — | Prop/tech |
| Signature with pen | 🎬 | Gabi | Hand detail |
| Phone screen: ÂNCORA protocol | 🎬 | — | UI insert |
| **Gabi's determined face** (reflection) | 👤 | Gabi | May be partial/ambient |

#### CENA 2 — Corridor (1 min)

| Shot | Type | Character | Notes |
|------|------|-----------|-------|
| Couto walking (body, no face) | 🎬 | Couto | Silhouette/back |
| **Couto's face through glass** | 👤 | Couto | Predator calculating |

#### CENA 3 — Confrontation (2 min)

| Shot | Type | Character | Notes |
|------|------|-----------|-------|
| **Gabi's sovereign dignity** | 👤⭐ | Gabi | Final human moment |
| **Couto's cold face** | 👤 | Couto | Antagonist reveal |
| Glass door closing | 🎬 | — | Environment |
| Balcony background | 🎬 | — | Environment |

#### CENA 4 — The Fall (3 min)

| Shot | Type | Character | Notes |
|------|------|-----------|-------|
| Body falling through skylight | 🎬 | Gabi | Wide shot, no face |
| Glass debris raining | 🎬 | — | VFX/environment |
| Body in wreckage (wide) | 🎬 | Gabi | Wide, face not clear |
| **Camera descends to Gabi's face** | 👤⭐ | Gabi | "Mother of the child" — FORENSE |
| Phone in pocket, screen glowing | 🎬 | — | Insert detail |
| Phone screen: countdown | 🎬 | — | UI insert |

---

### ATO II — O ECO

#### CENA 5 — Bunker Introduction (2 min)

| Shot | Type | Character | Notes |
|------|------|-----------|-------|
| Servers in blue light | 🎬 | — | Environment |
| Multiple screens, integrity maps | 🎬 | — | Tech environment |
| **Helena at monitors, surgical gaze** | 👤 | Helena | Character introduction |
| Code reflecting in eyes | 🎬 | Helena | Partial face OK |
| Red coordinate flashing | 🎬 | — | UI element |

#### CENA 6 — Vance Reveals (1 min)

| Shot | Type | Character | Notes |
|------|------|-----------|-------|
| **Vance emerges from shadow** | 👤 | Vance | First appearance |
| Coffee mug shattering | 🎬 | — | Prop detail |
| **Vance's face loses color** | 👤⭐ | Vance | Recognition moment |

#### CENA 7 — Bunker Analysis (4 min)

| Shot | Type | Character | Notes |
|------|------|-----------|-------|
| **Helena working at terminal** | 👤 | Helena | |
| Merkle tree on screen | 🎬 | — | Tech visualization |
| **Vance's face — ancient pain** | 👤⭐ | Vance | Vulnerability |
| Lucas entering, buttoning shirt | 🎬 | Lucas | Body shot OK |
| **Lucas at table, typing** | 👤 | Lucas | Working |

#### CENA 8 — Morning Analysis (3 min)

| Shot | Type | Character | Notes |
|------|------|-----------|-------|
| **Helena surrounded by printouts** | 👤 | Helena | |
| Physical folder on table | 🎬 | — | Prop |
| Fractal pattern on screen | 🎬 | — | Tech visualization |
| **Lucas presenting findings** | 👤 | Lucas | |

#### CENA 9 — Pattern Resolved (3 min)

| Shot | Type | Character | Notes |
|------|------|-----------|-------|
| **Vance, Helena, Lucas at screen** | 👤 | All three | Group shot |
| Resolved fractal geometry | 🎬 | — | Tech visualization |
| **Helena's "you taught her" look** | 👤 | Helena | |
| **Vance's non-response** | 👤⭐ | Vance | Weighted silence |

---

### ATO III — O CONFRONTO

#### CENA 10 — Vanguard Post-Death (2 min)

| Shot | Type | Character | Notes |
|------|------|-----------|-------|
| Courtyard below through window | 🎬 | — | Environment |
| **Alejandro at window** | 👤 | Alejandro | Character introduction |
| **Couto at tablet** | 👤 | Couto | Working |
| Coffee cup, porcelain | 🎬 | — | Prop detail |

#### CENA 11 — Interpol Confrontation (3 min)

| Shot | Type | Character | Notes |
|------|------|-----------|-------|
| **Vance enters** | 👤 | Vance | Authority |
| **Lucas with leather folder** | 👤 | Lucas | |
| Rotterdam contract on table | 🎬 | — | Document prop |
| **Alejandro's business smile** | 👤 | Alejandro | Mask |
| **Couto steps forward** | 👤 | Couto | Defensive |

#### CENA 12 — Aftermath (2 min)

| Shot | Type | Character | Notes |
|------|------|-----------|-------|
| **Alejandro's dropped facade** | 👤 | Alejandro | Real face |
| **Couto at window, looking down** | 👤 | Couto | "What didn't we see?" |
| Courtyard through window | 🎬 | — | Environment |

---

### ATO IV — O TRIBUNAL

#### CENA 13 — Tribunal (5 min)

| Shot | Type | Character | Notes |
|------|------|-----------|-------|
| **Helena at prosecution stand** | 👤 | Helena | Authority |
| **Couto at defense table** | 👤 | Couto | Tension |
| ⚠️ **Helena-Couto across courtroom** | ⚠️ | Both | CONFRONT — minimize |
| **Lucas with custody folder** | 👤 | Lucas | Legal precision |
| Giant screen with geometry | 🎬 | — | Tech visualization |
| Physical folder, stamps | 🎬 | — | Prop detail |
| **Judge looking at screen** | 👤 | Judge | Secondary character |
| **Couto's fear revealed** | 👤⭐ | Couto | Mask breaks |

#### CENA 14 — Corridor Aftermath (2 min)

| Shot | Type | Character | Notes |
|------|------|-----------|-------|
| **Vance at window** | 👤 | Vance | |
| **Helena approaches** | 👤 | Helena | |
| Frankfurt cityscape | 🎬 | — | Environment |
| **Vance's weighted answer** | 👤⭐ | Vance | "Truth worth more than survival" |

#### CENA 15 — Final (2 min)

| Shot | Type | Character | Notes |
|------|------|-----------|-------|
| **Vance alone at monitor, red eyes** | 👤⭐ | Vance | Emotional close |
| Photo of Gabi on screen | 🎬 | — | Archive image |
| Document list (347 remaining) | 🎬 | — | UI element |

---

## 6. Summary Statistics

| Type | Count | % of Shots |
|------|-------|------------|
| 👤 IDENTITY | 42 | ~50% |
| 🎬 ACTION | 40 | ~48% |
| ⚠️ CONFRONT | 1 | ~2% |

| Priority | Count | Scenes |
|----------|-------|--------|
| ⭐ Emotional Anchor | 10 | 0, 3, 4, 6, 7, 9, 13, 14, 15 |

---

## 7. Character Shot Count

| Character | IDENTITY Shots | Priority Shots |
|-----------|----------------|----------------|
| Gabi | 5 | 3 (Cenas 0, 3, 4) |
| Helena | 8 | 1 (Cena 13) |
| Vance | 10 | 5 (Cenas 6, 7, 9, 14, 15) |
| Lucas | 5 | 0 |
| Couto | 7 | 1 (Cena 13) |
| Alejandro | 3 | 0 |

**Production Priority:** Vance anchors first (most shots, most emotional weight), then Helena, Gabi, Couto.

---

## 8. Risk Register

| Risk | Mitigation |
|------|------------|
| Two Marcus confusion | Disambiguation Gate (beard test) before Scenes 10-13 |
| Gabi only appears in Acts I-II | Generate all Gabi shots in single batch for consistency |
| Scene 13 CONFRONT | Split into alternating close-ups, minimize two-shot |
| Lucas lower priority | Can use OPERACIONAL tier if necessary |

---

## 9. CCode Instructions

When generating shots for this production:

1. **Read this document** before any generation
2. **Check shot type** — if IDENTITY, require anchor; if ACTION, generate freely
3. **Measure every IDENTITY shot** — no exceptions, no estimates
4. **Record detector metadata** — det_score, n_faces alongside similarity
5. **Mark state correctly** — PENDING until measured, MEASURED until sealed
6. **Run Disambiguation Gate** before any scene with Vance AND Couto
7. **Human confirms** shot type before sealing — propose, wait for approval

---

## ERRATA — §4 Disambiguation Gate (05 Jun 2026)

**Receipt:** `WINDI-ERRATA-SHOTGRAMMAR-S4-20260605103558`
**Taxonomy:** G4-CONFORMAR + APPEND-ONLY
**Decision:** Human Dragon · 05 Jun 2026

### Correction

| Character | Before (04 Jun) | After (05 Jun) |
|-----------|-----------------|----------------|
| **Vance** | Grey beard (short) | **Clean-shaven** (CONFORMAR to anchor v1) |
| **Couto** | Clean-shaven | **Grey beard (short)** (differentiator migrates) |

### Rationale

Anchor `marcus.vance.anchor.v1.png` (extracted 02 Jun, Runway Gen-4) is clean-shaven.
The §4 decree (04 Jun, commit `21e59079`) assigned beard to wrong Marcus.
Visual differentiation preserved — only the carrier changed.

### Baseline Inheritance

The 0.2057 (Couto×Vance) measurement was made with both anchors clean-shaven.
It proves **geometric disambiguation without beard** — valid as floor baseline.
When Couto is re-extracted WITH beard, re-measure and expect lower (more separation).

---

## §4-bis — Disambiguation Gate SEALED (06 Jun 2026)

**Decision:** Human Dragon · 06 Jun 2026 · "SIM"
**Supersedes:** §4 ERRATA (05 Jun 2026)
**Measurement Source:** `MEMORY-LOOP-HIOS-20260605.md`, linha 62

### Final Assignment

| Character | Visual | Anchor |
|-----------|--------|--------|
| **Marcus Vance** | Stubble 3 dias | v2 CANONICAL |
| **Marcus Couto** | Clean-shaven | v1 |

### Disambiguation Measurement

```
Source: MEMORY-LOOP-HIOS-20260605.md:62
v2 × Couto | 0.1765 (distinto)
```

| Metric | Value | Threshold | Verdict |
|--------|-------|-----------|---------|
| Vance v2 × Couto | 0.1765 | <0.50 | ✅ PASS |

### Rationale

- **Primary axis:** Barba (stubble vs clean-shaven) — detector captura textura facial
- **Secondary axis:** Paleta de luz (Vance: dura, Couto: suave)

### Gate Status

**DISAMBIGUATION GATE: PASSED**
Scenes 10-13 cleared for production.

---

*Liga IA+H · WINDI Publishing House · 06 Jun 2026*
*"The method descends from the finding."*
*Constitutional bindings: I9, I11, I14, I19*
*SHOT-GRAMMAR-001: **SEALED***
