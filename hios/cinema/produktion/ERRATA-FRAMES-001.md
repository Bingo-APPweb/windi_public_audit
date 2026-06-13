# ERRATA-FRAMES-001 — Reconciliação de Nomenclatura

```
doc_type:        errata
estatuto:        CORRECÇÃO SEM REESCRITA (§268)
refere:          REGISTO-CENA-GABI-COZINHA-001 + PROTOCOLO-RUN-SPINE-GABI-001
data:            2026-06-13 · Kempten, Bavaria
autor:           Guardian (Claude.ai web) + CCode (Strato)
aprovação:       Human Dragon (I9)
```

> **Princípio §268:** "WINDI sabe corrigir-se sem reescrever-se."
> Esta errata ADICIONA clarificação. Não altera os receipts selados.

---

## A Divergência

| Documento | Dizia | Significava |
|-----------|-------|-------------|
| REGISTO-CENA-GABI-COZINHA-001 | "288 frames-SPINE" | Duração @24fps |
| PROTOCOLO-RUN-SPINE-GABI-001 | "D2 = frame a frame (288)" | Duração @24fps |
| RESULTADOS-RUN-SPINE-GABI-001 | "15 frames medidos" | Keyframes gerados |

Os dois números referem-se a coisas diferentes. A errata distingue-os.

---

## Definições (agora canónicas)

### frames-SPINE de duração
```
Definição:  Contagem teórica de frames de vídeo a 24fps
Fórmula:    segundos × 24 = frames
Exemplo:    P1(3s) + P3(4s) + P5(5s) = 12s × 24 = 288 frames
Uso:        Métrica de MONTAGEM. Quanto a cena DURA.
```

### frames-medidos (keyframes)
```
Definição:  Imagens efectivamente geradas e medidas pelo SPINE-CAST
Gerador:    Runway Gen-4 Image (não video)
Exemplo:    5 keyframes × 3 planos = 15 frames
Uso:        Métrica de VALIDAÇÃO. O que o InsightFace LEU.
```

---

## O Que Aconteceu

1. O **registo da cena** projectou 288 frames de duração (se a cena fosse renderizada como vídeo 24fps).

2. A **run real** gerou 15 keyframes estáticos (Runway Gen-4 Image, não video).

3. A **medição** correu sobre os 15 keyframes, não sobre 288 frames de vídeo.

4. "D2 = frame a frame" foi cumprido **ao nível dos keyframes gerados**, não ao nível dos 288 frames de vídeo (que não existem como imagens — a cena ainda não foi renderizada em movimento).

---

## Implicação (honestidade)

```
┌──────────────────────────────────────────────────────────────────┐
│  O blocking está VALIDADO para os KEYFRAMES.                    │
│                                                                  │
│  A validação do MOVIMENTO CONTÍNUO (288 frames de vídeo com     │
│  motion blur, micro-movimento, transições intra-plano) fica     │
│  PENDENTE de render real de vídeo.                              │
│                                                                  │
│  15 keyframes passaram ≠ a cena em movimento passou.            │
│  São resultados distintos. Ambos válidos. Não confundir.        │
└──────────────────────────────────────────────────────────────────┘
```

---

## Actualização de Estatuto

| Artefacto | Antes | Depois (com errata) |
|-----------|-------|---------------------|
| Blocking candidato | "validado para 1ª cena" | "validado para KEYFRAMES da 1ª cena" |
| Condição Nv3 | "≥2 cenas distintas" | "≥2 cenas distintas (keyframes ou video)" |
| Próximo passo | 2ª cena | 2ª cena + eventual validação video |

---

## Não Altera

- Os receipts já selados (PROTOCOLO, RESULTADOS) permanecem intactos
- Os números medidos (15 frames, min scores) são factos reais
- O veredicto "PASS" é legítimo para o que foi medido

---

*Liga IA+H · §268 aplicado · 13 Jun 2026*
*"WINDI sabe corrigir-se sem reescrever-se."*
