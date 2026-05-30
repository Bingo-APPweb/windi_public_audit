# §296 — PLATE PROMPTS (UI Neutral Zone)
## Prompts para Plates — Generator faz mundo, Pós faz prova

> **Invariante §296:** "O gerador faz o mundo. A prova faz-se em pós."
> Generator NUNCA renderiza texto WINDI. Plate contém zona neutra para overlay.

**Herda:** S295-RENDER-INVOCATIONS.md (gates) · DECREE-§296.md (invariante)
**Overlays:** WINDI-UI-S14-MATCH.svg · WINDI-UI-S15-INTEGRITY.svg

---

## S15 — PLATE (Integrity Screen Environment)

### PROMPT (Veo 3.1) — ZONA NEUTRA

```
A computer monitor in a modern forensic laboratory displaying a verification
interface. The screen shows a dark professional UI with glowing elements —
but any text is BLURRED or OUT OF FOCUS, creating a placeholder zone where
text will be added in post-production.

The monitor displays:
- A shield or checkmark icon (green glow)
- Abstract data visualization elements
- Receipt/hash area visible but TEXT INTENTIONALLY BLURRED

Monitor-lit lab environment, cold blue ambient lighting. The screen is the
hero element. Cinematic, realistic, 2.39:1 aspect ratio.

IMPORTANT: DO NOT render legible text. All text elements should be
decoratively blurred or abstracted. Clean dark UI theme with green accents.
```

### GATE (Plate Only)
- [ ] Monitor visível, centralizado
- [ ] UI dark theme com accents verdes
- [ ] Zona de texto blurred/neutra (não legível)
- [ ] Lab environment realista

### POST-COMPOSITION
Overlay: `WINDI-UI-S15-INTEGRITY.svg`
Injecta: `{{RECEIPT_ID}}` = receipt real do Ledger · `{{HASH}}` = hash real

---

## S16 — PLATE (Helena + Monitor com carro)

### PROMPT (Veo 3.1) — ZONA NEUTRA

```
A blonde woman detective (Helena) in her early 40s stands in a modern
forensic laboratory, pointing at a computer monitor. She wears a dark
navy wool coat over professional attire. Her blonde hair is pulled back
in a professional updo. She has angular features and a focused expression.

On the monitor screen, footage shows a dark sedan car in the background —
this is crucial evidence. The car should be a dark (black or very dark grey)
luxury sedan, clearly visible in what appears to be analysed video footage.

The main WINDI UI elements on the monitor are BLURRED or ABSTRACTED —
placeholder zones for post-production text overlay. Only the CAR FOOTAGE
should be clearly visible.

Cold blue lighting, multiple monitors. Bavaria, Germany forensic lab.
Cinematic, realistic, 2.39:1 aspect ratio.

CRITICAL CONTINUITY:
- Helena: dark navy coat, blonde hair pulled back
- Car visible on monitor: dark sedan (Marcus's vehicle)
- UI text zones: BLURRED, not legible
```

### GATE (Plate Only)
- [ ] Helena face cosine ≥ 0.65 (SPINE-CAST)
- [ ] Helena coat: dark navy
- [ ] Helena hair: blonde, pulled back
- [ ] Car on monitor: dark sedan visível
- [ ] UI zones: blurred/neutra

### POST-COMPOSITION
Overlay: `WINDI-UI-S14-MATCH.svg` (scaled, corner position)

---

## S20 — PLATE (Courtroom + Display)

### PROMPT (Veo 3.1) — ZONA NEUTRA

```
A Bavarian regional courtroom (Landgericht Kempten). Dark oak wood panelling,
tall windows with cold natural daylight streaming in. German flag and
Bavarian flag visible on the bench area.

Helena (blonde woman detective in her early 40s) stands addressing the court.
She wears a dark navy wool coat, her blonde hair pulled back professionally.
She gestures toward a large courtroom display screen.

The display screen shows:
- Evidence footage of a dark sedan (same car from previous scenes)
- WINDI verification interface — but TEXT IS BLURRED/ABSTRACTED
- Green verification indicators visible (icons, not text)

The atmosphere is tense, clinical. This is the climactic evidence presentation.
Cinematic, realistic, 2.39:1 aspect ratio. Bavaria, Germany, 2026.

CRITICAL CONTINUITY:
- Courtroom: dark oak, DE + Bavaria flags, natural daylight
- Helena: dark navy coat, blonde hair pulled back
- Display: car footage + BLURRED UI text zone
```

### GATE (Plate Only)
- [ ] Helena face cosine ≥ 0.65 (SPINE-CAST)
- [ ] Helena coat: dark navy (continuity S16)
- [ ] Courtroom: dark oak panelling
- [ ] Flags: DE + Bavaria visíveis
- [ ] Daylight: natural, cool
- [ ] Display: car + blurred UI zone

### POST-COMPOSITION
Overlay: `WINDI-UI-S15-INTEGRITY.svg` (scaled for courtroom display)

---

## ORDEM DE EXECUÇÃO

1. **S15** — Plate simples (só monitor) → Compose com overlay + valores REAIS → Seal
2. **S16** — Plate Helena+monitor → SPINE-CAST → Compose overlay corner → Seal
3. **S20** — Plate courtroom+Helena → SPINE-CAST → Compose overlay display → Seal

---

## SCRIPT DE GERAÇÃO

```bash
# Para cada cena:
python3 generate_s295_scenes.py --scene S15 --prompt "$(cat S296-PLATE-PROMPTS.md | ...)"

# Ou usar generate_s295_scenes.py actualizado com prompts §296
```

---

*Liga IA+H · WINDI Publishing House · 30 Mai 2026*
*"O gerador faz o mundo. A prova faz-se em pós."*
