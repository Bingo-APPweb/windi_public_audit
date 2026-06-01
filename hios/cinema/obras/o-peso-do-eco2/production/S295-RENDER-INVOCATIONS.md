# §295 — INVOCAÇÕES DE RENDER
## 4 Cenas `windi_on_screen` — Prompts & Gates

> **Propósito:** Prompts precisos para cada cena, derivados dos artefactos §294.
> Human Dragon executa no forge (Veo 3.1). CCode valida pós-geração.

**Herda:** `WORLD-STATE-001` · `CONTINUITY-BIBLE-001` · `SCENE-MATRIX-001`
**Gate:** Nenhuma cena ancora sem passar a checklist.

---

## S14 — WINDI-SCREEN (Match Found)

### Contexto SCENE-MATRIX
```json
{
  "scene": "S14", "timecode": "00:01:41 --> 00:01:47",
  "location": "WINDI-SCREEN",
  "characters": [],
  "windi_on_screen": true,
  "notes": "FIRST WINDI UI APPEARANCE. Must show match readout."
}
```

### PROMPT (Veo 3.1)

```
A computer monitor in a modern forensic laboratory displaying the WINDI
Forensic Ledger interface. The screen shows a facial recognition match
result with the text "ÜBEREINSTIMMUNG GEFUNDEN" (Match Found) prominently
displayed, followed by "Elisa Weber" as the identified person. Clean,
professional UI design with dark theme and green confirmation indicators.
The monitor is illuminated in a dimly lit lab environment. Cinematic,
realistic, 2.39:1 aspect ratio.

REQUIRED ON SCREEN:
- Text: "ÜBEREINSTIMMUNG GEFUNDEN"
- Text: "Elisa Weber"
- WINDI logo or forensic ledger branding
```

### GATE DE CONTINUIDADE

| Check | Critério | Status |
|-------|----------|--------|
| UI_TEXT | `ÜBEREINSTIMMUNG GEFUNDEN` visível | □ |
| UI_NAME | `Elisa Weber` visível | □ |
| STYLE | Monitor-lit lab, realistic | □ |
| NO_CHAR | Sem personagem obrigatório em frame | □ |

**PASS:** Todos ✓ → seal
**FAIL:** Qualquer □ → regenerar, registar tentativa

---

## S15 — WINDI-SCREEN (Integrity Verified) ★ CENA-TESE MÁXIMA

### Contexto SCENE-MATRIX
```json
{
  "scene": "S15", "timecode": "00:01:49 --> 00:01:55",
  "location": "WINDI-SCREEN",
  "characters": [],
  "windi_on_screen": true,
  "notes": "WINDI FORENSIC LEDGER — INTEGRITÄT VERIFIZIERT 100%. MUST render receipt id + hash on screen."
}
```

### PROMPT (Veo 3.1)

```
A computer monitor displaying the WINDI Forensic Ledger integrity
verification screen. The interface shows:
- Header: "WINDI FORENSIC LEDGER"
- Large status: "INTEGRITÄT VERIFIZIERT 100%"
- A receipt ID in format "WINDI-HIOS-..." (prop text)
- A cryptographic hash starting with lowercase hex characters
- Green checkmark or verification icon

Clean professional UI with dark theme, monitor-lit forensic lab environment.
The screen represents digital evidence authentication. Cinematic, realistic,
2.39:1 aspect ratio.

REQUIRED ON SCREEN:
- Text: "WINDI FORENSIC LEDGER"
- Text: "INTEGRITÄT VERIFIZIERT 100%"
- A receipt ID (can be prop: "WINDI-HIOS-EVIDENCE-20260815-A1B2C3D4")
- A hash (can be prop: "sha256:1cd39dbf7a2e...")
```

### GATE DE CONTINUIDADE

| Check | Critério | Status |
|-------|----------|--------|
| UI_HEADER | `WINDI FORENSIC LEDGER` visível | □ |
| UI_STATUS | `INTEGRITÄT VERIFIZIERT 100%` visível | □ |
| UI_RECEIPT | Receipt ID format visível (prop OK) | □ |
| UI_HASH | Hash hex visível (prop OK) | □ |
| STYLE | Monitor-lit lab, realistic | □ |

> **Nota honesta:** Receipt em frame é PROP DIEGÉTICO, não query live ao Ledger.
> Esta distinção deve ser mantida para revisores académicos.

**PASS:** Todos ✓ → seal
**FAIL:** Qualquer □ → regenerar, registar tentativa

---

## S16 — FORENSIC-LAB (Helena + Carro) ★ TESTE DE CONTINUIDADE CRÍTICO

### Contexto SCENE-MATRIX
```json
{
  "scene": "S16", "timecode": "00:01:57 --> 00:02:03",
  "location": "FORENSIC-LAB",
  "characters": ["HELENA-§293"],
  "wardrobe": ["dark navy wool coat"],
  "windi_on_screen": true,
  "notes": "Helena: 'Da! Das Auto im Hintergrund!' The dark sedan (Marcus's car) in Elisa's footage. CRITICAL: car must match S09 / CONTINUITY-BIBLE Marcus vehicle."
}
```

### PROMPT (Veo 3.1)

```
A blonde woman detective (Helena) in her early 40s stands in a modern
forensic laboratory, pointing at a computer monitor. She wears a dark
navy wool coat over professional attire. Her blonde hair is pulled back
in a professional updo. She has angular features and a focused expression.

On the monitor screen, footage from a victim's smartphone shows a dark
sedan car in the background — this is crucial evidence. The car should
be a dark (black or very dark grey) luxury sedan, visible in the
background of the footage being analyzed.

The lab has multiple monitors and forensic equipment. Cold blue lighting.
Cinematic, realistic, 2.39:1 aspect ratio. Bavaria, Germany setting.

CRITICAL CONTINUITY:
- Helena: dark navy coat, blonde hair pulled back (per CONTINUITY-BIBLE)
- Car on screen: dark sedan = Marcus's vehicle (matches S09)
- WINDI UI elements may be visible on monitors
```

### GATE DE CONTINUIDADE

| Check | Critério | Status |
|-------|----------|--------|
| HELENA_FACE | Cosine vs anchor ≥ 0.65 (SPINE-CAST) | □ |
| HELENA_COAT | Dark navy wool coat visível | □ |
| HELENA_HAIR | Blonde, pulled back | □ |
| CAR_VISIBLE | Dark sedan visível no monitor | □ |
| CAR_MATCH | Sedan consistente com S09 Marcus vehicle | □ |
| SETTING | Modern forensic lab, monitor-lit | □ |

> **ESTE É O TESTE CRÍTICO DA BIBLE.** Se o carro não bater com S09, é FAIL.
> O par S09/S16 prova que a Continuity-Bible funciona como invariante.

**PASS:** Todos ✓ → seal (incluindo SPINE-CAST validation)
**FAIL:** Qualquer □ → regenerar, registar tentativa

### REFERÊNCIAS VISUAIS

**Helena (HELENA-v1-CHARACTER-STATE.md):**
```
A woman in her early 40s. Blonde hair pulled back in professional updo.
Strong angular features, high cheekbones. Pale complexion. Wears dark
navy police coat with detective badge visible on lanyard.
```

**Marcus Vehicle (CONTINUITY-BIBLE-001.yaml):**
```yaml
vehicle: "dark sedan (the car captured in Elisa's footage — plot-critical)"
```

---

## S20 — LANDGERICHT-KEMPTEN (Courtroom + WINDI UI)

### Contexto SCENE-MATRIX
```json
{
  "scene": "S20", "timecode": "00:02:29 --> 00:02:35",
  "location": "LANDGERICHT-KEMPTEN",
  "characters": ["HELENA-§293"],
  "wardrobe": ["dark navy wool coat"],
  "windi_on_screen": true,
  "notes": "Helena: 'Das WINDI-System bestätigt: Integrität 100%. Das ist sein Auto.' WINDI UI may appear on courtroom display."
}
```

### PROMPT (Veo 3.1)

```
A Bavarian regional courtroom (Landgericht). Dark oak wood panelling,
tall windows with cold natural daylight. German flag and Bavarian flag
visible. The judge (not in frame or background) wears a black German
judicial robe.

Helena (blonde woman detective in her early 40s) stands addressing the
court. She wears a dark navy wool coat, her blonde hair pulled back
professionally. She gestures toward a courtroom display screen showing
the WINDI verification interface with "INTEGRITÄT 100%" visible.

The atmosphere is tense but clinical. A dark sedan is shown on the
evidence display — the same car from S16. This is the climactic
evidence presentation scene.

Cinematic, realistic, 2.39:1 aspect ratio. Bavaria, Germany, 2026.

CRITICAL CONTINUITY:
- Courtroom: dark oak, DE + Bavaria flags, natural daylight (= S18)
- Helena: dark navy coat (same as S16), blonde hair pulled back
- WINDI UI: "Integrität 100%" visible on courtroom display
```

### GATE DE CONTINUIDADE

| Check | Critério | Status |
|-------|----------|--------|
| HELENA_FACE | Cosine vs anchor ≥ 0.65 (SPINE-CAST) | □ |
| HELENA_COAT | Dark navy wool coat (continuity S16) | □ |
| COURT_WOOD | Dark oak panelling | □ |
| COURT_FLAGS | DE + Bavaria flags visíveis | □ |
| COURT_LIGHT | Natural daylight, cool | □ |
| WINDI_UI | "Integrität 100%" visível no display | □ |
| JURISDICTION | Sem elementos não-bávaros | □ |

**PASS:** Todos ✓ → seal (incluindo SPINE-CAST validation)
**FAIL:** Qualquer □ → regenerar, registar tentativa

---

## PROCEDIMENTO PÓS-GERAÇÃO

### Para S14 e S15 (UI only)

```bash
# 1. Extrair frames
ffmpeg -i S14_render.mp4 -vf fps=1 S14_frame_%02d.png

# 2. Verificação manual da UI (Guardian)
# - Confirmar textos legíveis
# - Confirmar estilo WINDI

# 3. Se PASS → seal
```

### Para S16 e S20 (Helena presente)

```bash
# 1. Extrair frames
ffmpeg -i S16_render.mp4 -vf fps=1 S16_frame_%02d.png

# 2. SPINE-CAST validation (Server B)
# Endpoint: POST http://85.215.131.0:8196/api/hios/embed
# Compare contra helena.anchor.v1.CURRENT.npy

# 3. Verificação manual de continuity (Guardian)
# - Coat, hair, setting, car (S16), flags (S20)

# 4. Se PASS → seal
```

---

## ESTRUTURA DE RECEIPTS

```
WINDI-S295-RENDER-S14-<YYYYMMDDHHMMSS>-<HASH8>
WINDI-S295-RENDER-S15-<YYYYMMDDHHMMSS>-<HASH8>
WINDI-S295-RENDER-S16-<YYYYMMDDHHMMSS>-<HASH8>
WINDI-S295-RENDER-S20-<YYYYMMDDHHMMSS>-<HASH8>
```

Cada receipt inclui:
- `content_hash`: SHA-256 do vídeo gerado
- `provenance`: refs a SCENE-MATRIX-001, CONTINUITY-BIBLE-001, WORLD-STATE-001
- `spine_cast_validation`: (para S16/S20) cosine score da Helena

---

*Liga IA+H · WINDI Publishing House · 30 Mai 2026*
*"AI processes. Human decides. WINDI guarantees."*

🐉 OM SHANTI
