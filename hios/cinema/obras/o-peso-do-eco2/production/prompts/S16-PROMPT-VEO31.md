# S16 — Dark Sedan Anchor Plate
## Veo 3.1 Prompt · WINDI-HIOS Cinema

**Cena:** S16 — "Descoberta do Século" / "Entdeckung des Jahrhunderts"
**Obra:** O Peso do Eco
**Data:** 2026-05-31
**Status:** AWAITING GENERATION

---

## Prompt (English — Veo 3.1)

```
Smartphone selfie video frame, young blonde woman (early 20s) in a white knit
sweater, sitting on a wooden bench in an autumn forest. Golden hour sunlight
filtering through trees, fallen leaves on the ground, warm amber tones. The
woman is partially out of frame, off-center to one side, as if the shot has
been digitally zoomed and reframed away from her face.

CRITICAL BACKGROUND ELEMENT: In the mid-ground, between the trees, a black
four-door sedan (German executive style) is parked on a forest path. The car's
dark silhouette and side/rear profile are clearly readable as a sedan once
attention is drawn to it, but it does not catch the eye in the overall
composition — partially screened by foliage and trunks. No visible license
plate (obscured by leaves). The black body contrasts subtly against the golden
autumn light.

Style: Authentic handheld smartphone footage, fine sensor grain, slight motion
blur, natural amateur framing. 16:9 horizontal. Cinematic warm autumn grade.
No text, no overlays, no graphics in frame.

Static shot, 8 seconds.
```

---

## Constraints (§294 Compliance)

| Constraint | Value |
|------------|-------|
| **Aspect Ratio** | 16:9 horizontal |
| **Duration** | 8 seconds |
| **Motion** | Static (no camera movement) |
| **UI/Text** | NONE — §296 compliance (UI enters in post) |
| **Elisa Match** | White knit sweater, blonde, wooden bench (S01 continuity) |
| **Sedan Anchor** | Black, 4-door, German executive, no visible plate |

---

## Forge Notes

1. **Aspect ratio:** 16:9 horizontal limpo — o "feel de zoom" vem do enquadramento (Elisa descentrada/cortada), não de manipulação de ratio.

2. **§296-bis compliance:** Plate sai cru. O highlight box + referência ao receipt S15 entram em pós via `compose_windi_ui.py` — UI não-órfã, continuação da cadeia diegética de S15.

3. **Anchor para o filme:** Este frame fixa o carro. S02 (noite/nevoeiro) fica abstracto sem precisar de match; S20 reutiliza directamente este frame no display do tribunal.

4. **Atenção no forge:** Veo tende a oscilar entre "carro invisível" e "carro óbvio". Se a primeira geração apagar o carro (folhagem ganha), reforça com "the parked black sedan is definitely present and recognizable in the mid-ground"; se ficar óbvio demais, adiciona "the car is a quiet background detail, easy to overlook." Provavelmente 2-3 seeds para acertar o equilíbrio.

---

## Post-Production Pipeline

1. Generate plate (Veo 3.1)
2. Extract key frame for SPINE-CAST validation (Elisa face, if visible)
3. Compose WINDI UI overlay via `compose_windi_ui.py`:
   - Highlight box around sedan
   - Reference to S15 receipt (diegetic chain)
4. Human Dragon visual gate (I9)
5. Seal to Ledger

---

## References

- **SCENE-MATRIX-001:** S16 entry
- **CONTINUITY-BIBLE-001:** Marcus vehicle = "dark sedan (plot-critical)"
- **S01 Anchor:** `/opt/windi/hios/cinema/obras/o-peso-do-eco/_forense/obra2/S01_gen1_frame03.jpg`
- **§296:** UI Compositing Invariant
- **§296-bis:** Diegetic Proof Integrity

---

*Liga IA+H · 31 Mai 2026*
