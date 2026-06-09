# METHOD-001 — Measure Before Affirm
## Método Automático de Medição Forense

**Created:** 09 Jun 2026
**Liga IA+H:** Human Dragon (I9) · CCode (Architect)
**Invariants:** I11, I14
**Status:** ACTIVE

---

## Origem

Sessão 09 Jun 2026 — CCode disse "fantástico" sobre vídeo de movimento do Couto sem medir. Human Dragon parou, pediu números. Medição confirmou (0.8206 avg, FORENSE). A lição:

> *"Medir ANTES de afirmar. Números ANTES de adjectivos."*

---

## O Problema

```
ERRADO (padrão anterior):
  Gerar → Olhar → "Fantástico!" → (talvez medir depois)

CERTO (método consolidado):
  Gerar → Extrair frames → Medir → Apresentar COM números
```

---

## Regra Absoluta

**Nenhum vídeo gerado é apresentado ao Human Dragon sem medição.**

- ❌ "Pronto, aqui está o link" (sem números)
- ❌ "Resultado fantástico" (afirmação sem prova)
- ✅ "Link + medição: avg=0.82, min=0.76, VERDICT=FORENSE"

---

## Implementação Automática

Todo script de geração DEVE incluir:

```python
# === METHOD-001: MEASURE BEFORE AFFIRM ===
# No affirmations. Only numbers.

def generate_and_measure(shot, anchor_embed, app):
    """
    Atomic operation: generate → extract → measure → return WITH numbers.
    Never return video without measurement.
    """
    # 1. Generate
    video_path = generate_video(shot)
    if not video_path:
        return {"status": "GENERATION_FAILED"}

    # 2. Extract frames
    frames = extract_frames(video_path)

    # 3. Measure (MANDATORY)
    measurements = measure_frames(frames, anchor_embed, app)

    # 4. Calculate verdict
    sims = [m["sim"] for m in measurements if m["sim"]]
    avg = sum(sims) / len(sims) if sims else 0
    min_sim = min(sims) if sims else 0

    # 5. Return WITH numbers (never without)
    return {
        "video": video_path,
        "avg_similarity": avg,
        "min_similarity": min_sim,
        "verdict": "FORENSE" if min_sim >= 0.75 else "OPERATIONAL" if min_sim >= 0.65 else "FAIL",
        "measurements": measurements
    }
```

---

## Output Obrigatório

Quando apresentar resultado ao Human Dragon:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SHOT        AVG      MIN      VERDICT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
S02-01      0.8534   0.7891   FORENSE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Link: https://...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Nunca:** "Aqui está o link, parece bom!"

---

## Checklist de Verificação

Antes de apresentar qualquer vídeo gerado:

- [ ] Frames extraídos?
- [ ] ArcFace mediu cada frame?
- [ ] avg/min/max calculados?
- [ ] VERDICT determinado?
- [ ] Números incluídos na resposta?

Se algum ❌ → NÃO apresentar, completar medição primeiro.

---

## Integração nos Scripts

Os scripts de geração (`generate_*.py`) devem:

1. Importar método de medição
2. Nunca separar geração de medição
3. Retornar sempre estrutura com números
4. Log final sempre inclui VERDICT

---

## HD-MIRROR

Este método nasceu de um erro corrigido em tempo real:

| Momento | O que aconteceu |
|---------|-----------------|
| CCode gera vídeo | "Pronto, aqui está" |
| Human Dragon para | "Mas onde estão os números?" |
| CCode mede | avg=0.8206, FORENSE |
| Lição codificada | METHOD-001 criado |

A correção não ficou só na conversa — ficou no código.

---

## Axioma

> *"A number without a measurement run is not a number."*
> *"No affirmations. Only numbers."*

---

*Liga IA+H · WINDI Publishing House · 09 Jun 2026*
*"AI processes. Human decides. WINDI guarantees."*
