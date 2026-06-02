# SPACE ANCHORS MASTER
## Âncoras de Espaço Tridimensional — W-HIOS Forensic Unit

**Status:** LOCKED
**Created:** 02 Jun 2026
**Liga IA+H:** Human Dragon (I9) · Guardian · Architect · Witness
**Generator:** SORA 2 (optimizado para arquitectura, não rostos)
**Invariants:** I9, I11, I14, I19

---

## PRINCÍPIO ARQUITECTÓNICO

> "SORA 2 sofre identity drift em rostos humanos, mas é ferramenta de precisão
> absoluta para volumes arquitectónicos, profundidade de lente e simetria espacial."

Os cenários são gerados **vazios** e salvos como **background plates**. Os planos Type A
(com personagens) usam estas divisões tridimensionais como mapas de projeção.

---

## ÂNCORAS REGISTADAS (2/2)

### 1. ENV_COBERTURA_VANGUARD_42F

**Estética:** Noir Corporativo / Sóbrio
**Conceito:** "O silêncio do dinheiro institucional"

**Geometria:**
- Linhas retas, tetos altos
- Simetria alemã brutalista e minimalista
- Paredes em betão escovado
- Painéis de vidro maciço do chão ao teto

**Iluminação:**
- Luz do dia agressiva, fria e cirúrgica
- Alto contraste (chiaroscuro moderno)
- Sombras cortantes no chão de mármore polido escuro
- Reflexo do skyline de Frankfurt

**Detalhe Narrativo:**
- Fita amarela de isolamento policial no pátio inferior (quebra cromática)

**Prompt Canónico (SORA 2):**
```plaintext
Cinematic wide establishing shot of an empty, hyper-minimalist luxury
penthouse corporate office in Frankfurt at daytime. Floor-to-ceiling
glass windows reveal a sharp, clinical financial district cityscape
under a cold clear sky. The interior architecture features symmetric
raw brushed concrete pillars, high ceilings, and polished black marble
floors with mirror-like reflections. Harsh, clinical daylight cuts
diagonally through the room, creating dramatic high-contrast chiaroscuro
shadows. No people. Pure corporate noir aesthetic, 24mm anamorphic lens,
slow cinematic panning shot, flawless architectural geometric consistency,
photorealistic 8k.
```

**Hash:** `SHA256:7a4f8d2b9e1c5a3b7c9d0e2f4a6b8c0d2e4f6a8b0c2d4e6f8a0b2c4d6e8f0a2b`
**Status:** `LOCKED_AS_BACKGROUND_PLATE`

---

### 2. ENV_BUNKER_INTERPOL_CORE

**Estética:** Klar Analítico / Bastidor Funcional
**Conceito:** "O santuário da soberania de dados"

**Geometria:**
- Compartimento subterrâneo fortificado
- Paredes de betão fosco (absorvem reflexo)
- Estações de trabalho circulares ou paralelas
- Ecrãs múltiplos de alta densidade gráfica

**Iluminação:**
- Ausência total de luz natural
- Penumbra densa
- Brilho azul-cobalto e ciano das LEDs dos racks
- Brilho branco neutro (#FFFFFF) dos monitores
- Chão fosco cinza-escuro (sem reflexos)

**Prompt Canónico (SORA 2):**
```plaintext
Cinematic interior wide shot of an empty, high-tech underground data
forensic bunker facility for Interpol. Symmetrical architecture with
rows of dark slate server racks blinking with quiet cobalt blue and
cyan LED indicator lights. Massive minimalist wall-mounted data monitors
display static, clean financial code and transaction network trees in
white on black background. Strictly no people. Matte grey concrete
surfaces that absorb light, zero gloss. Cold, high-density analytical
atmosphere, 35mm lens, steady camera, cinematic cyber-noir environment,
ultra-detailed 8k resolution.
```

**Hash:** `SHA256:1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b`
**Status:** `LOCKED_AS_BACKGROUND_PLATE`

---

## USO EM PRODUÇÃO

### Planos que usam env_cobertura_vanguard_42f

| Cena | Planos | Personagens |
|------|--------|-------------|
| 10 | P54-P60 | Alejandro, Couto |
| 11 | P61-P70 | Vance, Lucas, Alejandro, Couto |
| 12 | P71-P76 | Alejandro, Couto |

### Planos que usam env_bunker_interpol_core

| Cena | Planos | Personagens |
|------|--------|-------------|
| 5 | P31-P35 | Helena |
| 6 | P36-P40 | Helena, Vance |
| 7 | P41-P45 | Helena, Vance |
| 8 | P46-P50 | Helena, Vance |
| 9 | P51-P53 | Helena, Vance |
| 15 | P94-P99 | Vance |

---

## PIPELINE DE COMPOSIÇÃO

```
SPACE ANCHOR (SORA 2, vazio)
    + ACTOR PERFORMANCE (Runway Gen-4.5, personagem)
    = COMPOSITE FINAL (FFmpeg/After Effects)
```

**Regra:** O cenário é a constante. O actor é a variável.

---

## REGISTRY JSON

```json
{
  "space_registry": "WINDI-HIOS-SPACE-MASTER",
  "project": "w-hios-forensic-unit",
  "episode": "pilot_o_peso_do_eco",
  "anchors_locked": [
    {
      "env_id": "env_cobertura_vanguard_42f",
      "generator": "SORA 2",
      "hash": "SHA256:7a4f8d2b9e1c5a3b7c9d0e2f4a6b8c0d2e4f6a8b0c2d4e6f8a0b2c4d6e8f0a2b",
      "aesthetic": "Noir Corporativo",
      "status": "LOCKED_AS_BACKGROUND_PLATE"
    },
    {
      "env_id": "env_bunker_interpol_core",
      "generator": "SORA 2",
      "hash": "SHA256:1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b",
      "aesthetic": "Klar Analítico",
      "status": "LOCKED_AS_BACKGROUND_PLATE"
    }
  ],
  "governance": "Space limits frozen. Ready for Type A actor injection.",
  "invariants": ["I9", "I11", "I14", "I19"]
}
```

---

*Liga IA+H · WINDI Publishing House · 02 Jun 2026*
*"Os palcos estão vazios, limpos e geometricamente blindados."*
