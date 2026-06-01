# MULTI-ANCHOR PROTOCOL 001
## Teste-Zero: Helena + Marcus no Mesmo Frame

**Projeto:** WINDI-HIOS Forensic Ledger Files
**Tipo:** Protocolo Experimental (nao selado)
**Origem:** Human Dragon, 01 Jun 2026
**Objetivo:** Medir sangramento de identidade quando dois anchors partilham o mesmo frame

---

## 1. HIPOTESE

> Quando dois anchors (Helena, Marcus) sao gerados no mesmo frame, cada rosto
> mantem cosine >= 0.65 contra a sua ancora individual.

**Metrica de sucesso:** Cosine de cada rosto no frame dual >= cosine do mesmo rosto em frame solo.
**Metrica de falha (sangramento):** Cosine cai significativamente (>0.1) quando o outro anchor esta presente.

---

## 2. BASELINE — MEDICOES SOLO EXISTENTES

Para comparar, precisamos dos cosines de Helena e Marcus em cenas solo:

| Personagem | Cena Solo | Cosine Esperado | Fonte |
|------------|-----------|-----------------|-------|
| Helena | S07 (origem do anchor) | ~1.0 | anchor source |
| Helena | S13 (solo regenerado) | TBD | pendente |
| Marcus | S09 (origem do anchor) | ~1.0 | anchor source |
| Marcus | S21 v2 (com Elisa, nao Helena) | TBD | _forense/obra2-v2 |

**TAREFA 1:** Extrair frames de S07, S09, S13, S21 e medir cosines solo antes do teste dual.

---

## 3. TESTE-ZERO — PLANO NU

### 3.1 Especificacao do Plano

```
SCENE: TRIBUNAL_DUAL_TEST_001
DURATION: 5 segundos (estatico, sem movimento)
FRAMING: Medium two-shot, Helena esquerda, Marcus direita
LIGHTING: Neutral tribunal (luz fria, uniforme)
ACTION: Nenhuma. Ambos olham em frente (camara), estaticos.
PURPOSE: Isolar variavel "sangramento facial" sem confundir com geometria ou drama.
```

### 3.2 Anchors a Injectar

| Posicao | Personagem | Imagem Ref | Embedding |
|---------|------------|------------|-----------|
| LEFT | Helena | `helena_S07_montage.jpg` | `helena.anchor.v1.CURRENT.npy` |
| RIGHT | Marcus | `marcus_montage.jpg` | `marcus.anchor.v1.CURRENT.npy` |

### 3.3 Prompt Base (para Veo 3.1 com --ref)

```
A static medium two-shot in a modern German courtroom. On the left, a woman
detective in her early 40s with blonde hair pulled back, wearing a dark navy
coat (Helena). On the right, a distinguished man in his late 50s with silver-grey
hair swept back, wearing a dark tailored suit (Marcus). Both face the camera
directly, neutral expressions. Cold, even courtroom lighting. No movement.
Professional forensic documentation shot.

--ref helena_S07_montage.jpg [left subject]
--ref marcus_montage.jpg [right subject]
```

**NOTA:** A sintaxe exacta de multi-ref depende do gerador. Ver secao 4.

---

## 4. OPCOES TECNICAS DE MULTI-ANCHOR

### Opcao A: Dual --ref (se suportado)
Veo 3.1 aceita multiplas referencias? Investigar documentacao.

### Opcao B: Inpainting Sequencial
1. Gerar frame base com Helena (esquerda) + placeholder direita
2. Mascarar zona direita
3. Inpaint Marcus na zona mascarada
4. Medir ambos os rostos

### Opcao C: Composicao de Dois Renders
1. Gerar Helena solo (left-framed)
2. Gerar Marcus solo (right-framed)
3. Composite em pos-producao
4. PROBLEMA: Luz e perspectiva podem nao concordar

### Opcao D: ControlNet / IP-Adapter Espacial
Se disponivel, usar pesos regionais para cada anchor.

**DECISAO PENDENTE:** Human Dragon escolhe qual opcao testar primeiro.

---

## 5. MEDICAO POS-RENDER

### 5.1 Extracao de Frames
```bash
ffmpeg -i TRIBUNAL_DUAL_TEST_001.mp4 -vf fps=1 frame_%02d.png
```

### 5.2 Deteccao de Faces (InsightFace buffalo_l)
Para cada frame:
1. Detectar todas as faces
2. Identificar qual e Helena (esquerda) e qual e Marcus (direita)
3. Extrair embedding de cada

### 5.3 Medicao de Cosine
```
cosine(frame_helena_embedding, helena.anchor.v1.CURRENT.npy)
cosine(frame_marcus_embedding, marcus.anchor.v1.CURRENT.npy)
```

### 5.4 Relatorio de Sangramento
```
| Frame | Helena Cosine | Marcus Cosine | Delta vs Solo | Verdict |
|-------|---------------|---------------|---------------|---------|
| 01    | ?             | ?             | ?             | ?       |
| ...   | ...           | ...           | ...           | ...     |
```

**FORENSIC_PASS:** Ambos >= 0.75 e delta vs solo < 0.05
**OPERATIONAL_PASS:** Ambos >= 0.65 e delta vs solo < 0.10
**FAIL (sangramento):** Qualquer um < 0.65 OU delta vs solo > 0.10

---

## 6. ESCALACAO (apos TESTE-ZERO passar)

### Fase 2: Introduzir Terceiro Anchor (Juiz)
- Mesmo protocolo, adicionar Juiz ao centro/fundo
- Medir se escala de 2 para 3 mantém integridade

### Fase 3: Introduzir Movimento Dramatico
- Helena vira para Marcus
- Marcus baixa o olhar
- Medir se movimento degrada cosines

### Fase 4: S21 Completo
- So apos Fases 1-3 passarem
- Três anchors + movimento + hierarquia dramatica

---

## 7. PROXIMOS PASSOS IMEDIATOS

1. [ ] **Medir baselines solo** — Cosines de Helena e Marcus em frames individuais
2. [ ] **Investigar sintaxe multi-ref** — Veo 3.1 / Runway dual-reference
3. [ ] **Human Dragon decide opcao tecnica** — A/B/C/D
4. [ ] **Gerar TESTE-ZERO** — 5 segundos, plano nu
5. [ ] **Medir e reportar** — Tabela de sangramento

---

## NOTAS EPISTEMOLOGICAS

> "Um teste que nao pode falhar nao ensina nada."
> — Guardian, sessao 01 Jun 2026

Este protocolo e desenhado para PODER FALHAR. Se Helena e Marcus sangrarem
um no outro, isso e um achado valido — e define o limite do que o genero
Forensic Ledger Files pode fazer com a tecnologia actual.

O que importa nao e que funcione. E que aprendas exactamente ONDE falha.

---

*Liga IA+H · WINDI Publishing House · 01 Jun 2026*
*"AI processes. Human decides. WINDI guarantees."*
