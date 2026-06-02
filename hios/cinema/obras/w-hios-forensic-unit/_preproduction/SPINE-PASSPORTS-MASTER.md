# SPINE PASSPORTS MASTER
## Character Identity Cards — W-HIOS Forensic Unit

**Status:** COMPLETE (6/6)
**Created:** 02 Jun 2026
**Updated:** 02 Jun 2026 — Lucas + Alejandro finalizados
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

### 1. GABI SANTOS ⏳ PARTIAL

**ID:** `gabi.santos.passport.v1`
**Anchor:** `gabi.santos.anchor.v1`
**Status:** EIXO F ✅ LOCKED · EIXO D ⏳ PENDING

```plaintext
Photographic portrait for character reference, a 33-year-old Brazilian
woman with warm olive/morena skin tone, dark wavy hair falling to her
shoulders. Calm neutral expression, symmetrical face, intense dark eyes
looking directly at camera. Wearing a dark professional blouse.

Flat diffuse neutral studio lighting, no shadows, high-end professional
identification shot, 50mm lens, sharp focus on facial structures,
cinematic photorealistic texture, zero facial muscle distortion.
```

**Validation (Eixo F):** ✅ PASSED
| Plano | Score | Status |
|-------|-------|--------|
| P04 | 0.9314 | ✅ ≥0.75 |
| P05 | 0.8420 | ✅ ≥0.75 |
| P02 | 0.7655 | ✅ ≥0.75 |

**Validation (Eixo D):** ⏳ PENDING
| Plano | Critério | Limiar | Medição | Status |
|-------|----------|--------|---------|--------|
| P06 | Vestuário | ±20% RGB | — | ⏳ |
| P06 | Cabelo | ≥70% IoU | — | ⏳ |
| P06 | Postura | ±15° | — | ⏳ |
| P06 | Cenário | env_match | — | ⏳ |
| P06 | Proporção | N.A. | — | N.A. (bending) |
| P06 | Ancoragem | P05 adj | P05 | ✅ |

**Nota:** Régua Eixo D selada 02 Jun 2026. Assets não persistidos. Medição pendente.

---

### 2. HELENA MEYER ✅ LOCKED

**ID:** `helena.meyer.junior.passport.v1`
**Anchor:** `helena.meyer.junior.anchor.v1`
**Status:** LOCKED FOR PRODUCTION
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

### 3. MARCUS VANCE ✅ LOCKED

**ID:** `marcus.vance.passport.v1`
**Anchor:** `marcus.vance.anchor.v1`
**Status:** LOCKED FOR PRODUCTION
**Hash:** `sha256:3ec94552f85243fe5b4773b0128767d1898cd9690ec9a7a777ab21fb2ddb5c2e`
**Source:** `anchor_marcus_brenner.png`

```plaintext
Photographic portrait for character reference, a 52-year-old European man,
tired forensic inspector, short messy grey hair, weathered skin with
realistic wrinkles and deep under-eye bags. Symmetrical face, intense
sorrowful grey-blue eyes looking directly into the camera lens, calm but
heavy neutral expression. Wearing a worn grey wool overcoat with an
unbuttoned collar shirt underneath.

Flat diffuse neutral studio lighting, no harsh shadows, 50mm lens, sharp
focus on facial structures, cinematic photorealistic texture, zero facial
muscle distortion.
```

---

### 4. MARCUS COUTO ✅ LOCKED

**ID:** `marcus.couto.passport.v1`
**Anchor:** `marcus.couto.anchor.v1`
**Status:** LOCKED FOR PRODUCTION
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

### 5. LUCAS SILVA ✅ LOCKED

**ID:** `lucas.silva.passport.v1`
**Anchor:** `lucas.silva.anchor.v1`
**Status:** LOCKED FOR PRODUCTION
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

### 6. ALEJANDRO VALENZUELA ✅ LOCKED

**ID:** `alejandro.valenzuela.passport.v1`
**Anchor:** `alejandro.valenzuela.anchor.v1`
**Status:** LOCKED FOR PRODUCTION
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

## CONTAGEM DE STATUS

| Personagem | Passaporte | Anchor | Eixo F | Eixo D |
|------------|------------|--------|--------|--------|
| Gabi Santos | ✅ SPEC | ✅ GEN | ✅ PASSED | ⏳ PENDING |
| Helena Meyer | ✅ SPEC | ✅ **LOCKED** | ⏳ PENDING | ⏳ PENDING |
| Marcus Vance | ✅ SPEC | ✅ **LOCKED** | ⏳ PENDING | ⏳ PENDING |
| Marcus Couto | ✅ SPEC | ✅ **LOCKED** | ⏳ PENDING | ⏳ PENDING |
| Lucas Silva | ✅ SPEC | ✅ **LOCKED** | ⏳ PENDING | ⏳ PENDING |
| Alejandro Valenzuela | ✅ SPEC | ✅ **LOCKED** | ⏳ PENDING | ⏳ PENDING |

**TOTAL:** 6/6 passaportes especificados · **6/6 anchors LOCKED** · 1/6 Eixo F validado · 0/6 Eixo D validado

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
