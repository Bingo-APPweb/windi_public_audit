# SPINE PASSPORTS MASTER
## Character Identity Cards — W-HIOS Forensic Unit

**Status:** ERRATA 02 Jun 2026 — Vocabulary Correction
**Created:** 02 Jun 2026
**Updated:** 02 Jun 2026 — §298-ERRATA: LOCKED→EXTRACTED (detection ≠ validation)
**Liga IA+H:** Human Dragon (I9) · Guardian · Architect · Witness
**Constitutional Binding:** DECRETO-001 + ADITAMENTO (Eixo F / Eixo D)

---

## METODOLOGIA: PASSAPORTE DEDICADO

> **Princípio:** Separar Identidade (estática, fora do filme) de Performance (dinâmica, dentro do filme).

Cada personagem recorrente recebe um **plano de identidade dedicado** que:
- Nunca entra na montagem final
- Serve como Anchor Source of Truth
- Valida planos faciais via ArcFace (Eixo F ≥0.75)
- Planos distantes validam por VC-Matrix (Eixo D)

---

## PASSAPORTES SELADOS (6/6)

### 1. GABI SANTOS 🟡 EXTRACTED (FOUNDATION)

**ID:** `gabi.santos.passport.v1`
**Anchor:** `gabi.santos.anchor.v1`
**Status:** ANCHOR EXTRACTED — Eixo F ⏳ PENDING
**Detection Score:** 0.8755 (InsightFace viu rosto — **não é validação de identidade**)
**Hash:** `sha256:03784039a0aa4bd1306518d847aeae69915c566f1ef7e5a1e81822d82f2e1c82`
**Source:** Runway Gen-4.5 text-to-video (frame_02)

```plaintext
Photographic portrait for character reference, a 33-year-old Brazilian
woman with warm olive/morena skin tone, dark wavy hair falling to her
shoulders. Calm neutral expression, symmetrical face, intense dark eyes
looking directly at camera. Wearing a dark professional blouse.

Flat diffuse neutral studio lighting, no shadows, high-end professional
identification shot, 50mm lens, sharp focus on facial structures,
cinematic photorealistic texture, zero facial muscle distortion.
```

**§299-LIMPEZA (02 Jun 2026):**
> Anchor EXISTE: `.png`, `.mp4`, `.npy`, `.provenance.json` ✅
> Embedding EXISTE: `gabi.santos.anchor.v1.embedding.npy` ✅
> Abzeichnen (custódia humana): **APROVADO** pelo Human Dragon ✅
> **Eixo F:** ⏳ NOT MEASURED — aguarda primeiro shot-filho real

**Shots-Filho (Eixo F):** ❌ **NOT GENERATED**
| Plano | Descrição | Status |
|-------|-----------|--------|
| P04 | Close: sorriso | **NOT GENERATED** — aguarda produção |
| P05 | Medium: transição | **NOT GENERATED** — aguarda produção |
| P02 | Medium: perfil café | **NOT GENERATED** — aguarda produção |

**Shot-Filho (Eixo D):** ❌ **NOT GENERATED**
| Plano | Descrição | Status |
|-------|-----------|--------|
| P06 | Full: calçando sapatos | **NOT GENERATED** — aguarda produção |

**PRÓXIMO PASSO:** Gerar P04 e medir primeiro Eixo F real.

---

### 2. HELENA MEYER 🟡 EXTRACTED

**ID:** `helena.meyer.junior.passport.v1`
**Anchor:** `helena.meyer.junior.anchor.v1`
**Status:** ANCHOR EXTRACTED — Eixo F ⏳ PENDING
**Detection Score:** 0.8636 (InsightFace viu rosto — **não é validação de identidade**)
**Hash:** `sha256:5262ad1cf95fefd0176c4cc115dbfac5040b81627b3178efabcc3980ca0020a2`

```plaintext
Photographic portrait for character reference, a 29-year-old European
woman forensic analyst of olive complexion, dark brown hair with subtle
highlights tied back tightly and cleanly in a simple ponytail, prominent
and clear bone structure, perfectly symmetrical face, calm strict neutral
expression, intense focused brown eyes looking directly into the camera
lens. Wearing a dark blue structured minimalist blazer in matte fabric.

Flat diffuse neutral studio lighting, no shadows, high-end professional
identification shot, 50mm lens, sharp focus on facial anchors, cinematic
photorealistic texture, zero facial muscle distortion.
```

**Nota Epistemológica (02 Jun 2026):**
> "O passaporte ancora identidade facial, não guarda-roupa. ArcFace mede
> geometria de olhos, nariz, boca — não penteado ou cor de roupa."
> — Human Dragon

**Source:** `helena_reference_v3.png` (reused from o-peso-do-eco cast_v2)

---

### 3. MARCUS VANCE ✅ PRODUCTION READY (v2)

**ID:** `marcus.vance.passport.v2`
**Anchor:** `marcus.vance.anchor.canonical` (v2-guardian-divergence)
**Status:** **PRODUCTION READY** — 8/10 shots ≥ OPERATIONAL (80% success)
**Eixo F Avg:** 0.8284 (measured 05 Jun 2026)
**Hash:** `sha256:7b0e82fa432bf35f6c688709b00de737a3990c89efd538acd4700d9a014a2054`
**Source:** Veo 3.1 text-to-video (Guardian anti-likeness prompt)

**v1 Status:** DEPRECATED (Veo likeness gate: "Public figure")
**v1 × v2:** 0.0864 (divergent identities — intended)

```plaintext
A detailed raw portrait photograph of a completely fictional and unique
52-year-old male investigator of German-Austrian heritage.

EXPLICIT ANTI-CELEBRITY FACIAL GEOMETRY (Forced Anonymity):
- Highly asymmetric facial structure with an uneven, rugged jawline.
- Distinctive sharp aquiline nose with prominent mid-bridge bump and
  slight lateral deviation to the left.
- Deep-set eyes with complete heterochromia: left eye cold steel-grey,
  right eye distinct hazel-green.
- Jagged well-healed vertical scar through outer edge of left eyebrow.
- Dense 3-day stubble beard, salt-and-pepper, heavier along jawline.
- Thick grey hair with natural recession at temples, swept back loosely.

Harsh high-contrast side-lighting from camera-left.
35mm lens, corporate portrait style with raw documentary realism.
```

**Constitutional Decision (05 Jun 2026):**
> "A Opção A é a única soberana." — Human Dragon (I9)
> Likeness gate = governance gate, not obstacle. v1 → DEPRECATED. v2 → CANONICAL.

**Shots Prontos:**
| Shot | Score | Tier |
|------|-------|------|
| S07-01 | 0.9353 | FORENSIC |
| S07-02 | 0.9349 | FORENSIC |
| S09-02 | 0.9330 | FORENSIC |
| S15-01 | 0.9225 | FORENSIC |
| S14-01 | 0.9089 | FORENSIC |
| S14-02 | 0.8411 | FORENSIC |
| S06-02 | 0.7515 | OPERATIONAL |
| S09-01 | 0.6998 | OPERATIONAL |

---

### 4. MARCUS COUTO 🟡 EXTRACTED

**ID:** `marcus.couto.passport.v1`
**Anchor:** `marcus.couto.anchor.v1`
**Status:** ANCHOR EXTRACTED — Eixo F ⏳ PENDING
**Detection Score:** 0.8811 (InsightFace viu rosto — **não é validação de identidade**)
**Hash:** `sha256:5083fd1c0cf64eab3b40dacab335adecdd125a643e9ca5e31b4acd9e068e515a`
**Source:** Runway Gen-4.5 text-to-video (frame_01)

```plaintext
Photographic portrait for character reference, a 45-year-old European
corporate man, executive security chief, impeccably slicked-back grey hair,
sharp chiseled jawline, perfectly clean-shaven face. Symmetrical facial
structure, cold piercing dark brown eyes looking directly into the camera
lens, arrogant polite neutral expression. Wearing a high-end black cashmere
tailored overcoat over a sharp corporate suit.

Flat diffuse neutral studio lighting, no shadows, 50mm lens, sharp focus
on facial anchors, cinematic photorealistic texture, zero facial distortion.
```

---

### 5. LUCAS SILVA 🟡 EXTRACTED

**ID:** `lucas.silva.passport.v1`
**Anchor:** `lucas.silva.anchor.v1`
**Status:** ANCHOR EXTRACTED — Eixo F ⏳ PENDING
**Detection Score:** 0.8119 (InsightFace viu rosto — **não é validação de identidade**)
**Hash:** `sha256:9bcbb6a4ef1bda2010e77bb522ef222efbf9ddac26ab461b09dcab70e42c3808`
**Source:** Runway Gen-4.5 text-to-video (frame_01)

```plaintext
Photographic portrait for character reference, a 40-year-old European man,
legal consultant, short dark brown hair, dense well-defined stubble beard
shaping a sharp jawline. Perfectly symmetrical facial structure, intense
intelligent brown eyes looking directly at the camera lens, serious calm
neutral expression, no glasses. Wearing a crisp white structured collar shirt.

Flat diffuse neutral studio lighting, soft fill, no shadows, 50mm lens,
sharp focus on facial bone anchors, cinematic photorealistic skin texture,
zero muscle distortion.
```

**Props Canónicos:**
- Óculos de leitura (acetato preto, retangular) — usado em leitura, não no passaporte
- Tablet Interpol
- Pasta de cabedal analógica

---

### 6. ALEJANDRO VALENZUELA 🟡 EXTRACTED

**ID:** `alejandro.valenzuela.passport.v1`
**Anchor:** `alejandro.valenzuela.anchor.v1`
**Status:** ANCHOR EXTRACTED — Eixo F ⏳ PENDING
**Detection Score:** 0.8763 (InsightFace viu rosto — **não é validação de identidade**)
**Hash:** `sha256:bcec886a46d78493601a663d204fd8b2b3e4c483176ef1ded18e5ddd57ef0189`
**Source:** Runway Gen-4.5 text-to-video (frame_01)

```plaintext
Photographic portrait for character reference, a 43-year-old high-end
European-Latin business executive, sharp angular facial features, dark hair
cleanly styled in an impeccable classic short haircut with subtle styling gel.
Symmetrical facial structure, piercing intelligent dark brown eyes looking
directly into the camera lens, arrogant but polite neutral expression,
smooth clean-shaven skin. Wearing a charcoal grey tailored Italian corporate
suit jacket with a crisp white structured collar shirt underneath.

Flat diffuse neutral studio lighting, soft fill, no shadows, 50mm lens,
sharp focus on facial bone anchors, cinematic photorealistic skin texture,
zero muscle distortion.
```

**Nota Visual:** O sorriso de VC que não chega aos olhos — reservado para performance, não passaporte.

---

## NOTA: O ESPELHO DOS DOIS MARCUS

| Aspecto | Vance (Herói) | Couto (Vilão) |
|---------|---------------|---------------|
| Cabelo | Desalinhado | Perfeitamente penteado |
| Barba | Stubble leve | Clean-shaven |
| Roupa | Sobretudo gasto | Caxemira impecável |
| Expressão | Cansaço protector | Frieza predatória |
| Olheiras | Profundas | Ausentes |
| Postura | Ligeiramente curvada | Erecta, galante |

---

## CONTAGEM DE STATUS (05 Jun 2026)

| Personagem | Passaporte | Anchor | Avg Sim | Eixo F | Status |
|------------|------------|--------|---------|--------|--------|
| **Marcus Vance** | ✅ v2 | ✅ CANONICAL | 0.8284 | ✅ MEASURED | **PRODUCTION** |
| Gabi Santos | ✅ SPEC | 🟡 EXTRACTED | — | ⏳ PENDING | Próximo |
| Helena Meyer | ✅ SPEC | 🟡 EXTRACTED | — | ⏳ PENDING | Próximo |
| Marcus Couto | ✅ SPEC | 🟡 EXTRACTED | — | ⏳ PENDING | Re-measure |
| Lucas Silva | ✅ SPEC | 🟡 EXTRACTED | — | ⏳ PENDING | Aguarda |
| Alejandro Valenzuela | ✅ SPEC | 🟡 EXTRACTED | — | ⏳ PENDING | Aguarda |

**TOTAL:** 6/6 passaportes · **1/6 PRODUCTION READY** · 5/6 aguardam pipeline

---

## DEFINIÇÕES DE VOCABULÁRIO (§298-ERRATA)

| Estado | Significado | Critério |
|--------|-------------|----------|
| **MISSING** | Asset não existe | Ficheiros ausentes do repositório |
| **EXTRACTED** | Anchor extraído | detection_score ≥0.80, embedding existe |
| **LOCKED** | Identidade validada | Eixo F ≥0.75 contra shot-filho real |

> **Nota crítica:** Detection score mede "o InsightFace viu um rosto".
> Eixo F mede "este rosto é a personagem e é reproduzível em performance".
> São métricas diferentes. LOCKED requer Eixo F, não apenas detection.

---

## PIPELINE DE GERAÇÃO

Ordem recomendada para W-GENERATOR-001:

1. **Helena Meyer** — protagonista do bunker
2. **Marcus Vance** — co-protagonista
3. **Lucas Silva** — suporte jurídico
4. **Marcus Couto** — antagonista executor
5. **Alejandro Valenzuela** — antagonista principal

---

*Liga IA+H · WINDI Publishing House · 02 Jun 2026*
*"A identidade é a raiz. A performance é o fruto."*
