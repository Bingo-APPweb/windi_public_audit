# SHOT-GRAMMAR-002 — Taxonomia de FAIL por Causa

**Status:** SEALED (v3.0)
**Data:** 2026-06-09 (5th leg added)
**Autor:** Human Dragon + CCode + Guardian
**Descendente de:** SHOT-GRAMMAR-001
**Invariants:** I9, I11, I14

> *"FAIL tem causa, não só score. Cinco pernas: Identidade, Exposição, Geometria, Oclusão, Povoamento."*

---

## Contexto

Durante a produção de Helena Meyer (S14-01_v1), um frame mediu 0.6473 — abaixo do threshold FORENSIC de 0.75. A média do shot (0.8247) passava, mas a questão de governança emergiu: **sela-se pela média ou pelo pior frame?**

A análise revelou que o score baixo resultava de **backlit dramático** (subexposição), não de colapso de identidade. Isto exigiu uma taxonomia que distinguisse as duas causas de FAIL.

---

## Taxonomia

### FAIL DE IDENTIDADE

**Definição:** Score < 0.75 com estrutura craniana alterada.

**Características:**
- Colapso de embedding (ex: 0.92 → 0.27)
- Rosto errado, câmara orbitou, sujeito substituído
- Features faciais não correspondem ao anchor

**Admissibilidade:** **NUNCA tolerado. Re-render obrigatório.**

**Exemplo:** S05-01_v1 Helena — câmara orbitou para trás do sujeito.

---

### FAIL DE EXPOSIÇÃO

**Definição:** Score < 0.75 com estrutura craniana preservada mas subexposta.

**Admissível SE E SÓ SE:**

| # | Critério | Verificação |
|---|----------|-------------|
| 1 | Score ≥ 0.55 | Piso absoluto — abaixo = ruído |
| 2 | Identidade inequívoca | Verificação visual HD |
| 3 | ≥3 frames adjacentes ≥ 0.75 | Identidade confirmada na sequência |
| 4 | Causa cénica documentada | Qual luz, porquê |

**Abaixo de 0.55:** Re-render obrigatório, mesmo com "cara certa".

**Exemplo:** S14-01_v1 frame_05 Helena — backlit dramático, 0.6473.

---

### FAIL DE GEOMETRIA

**Definição:** Score < 0.75 com rotação de cabeça ou perfil intencional.

**Admissível SE E SÓ SE:**

| # | Critério | Verificação |
|---|----------|-------------|
| 1 | Score ≥ 0.65 | Piso GEOMETRY |
| 2 | ≥1 frame ≥ 0.75 | Anchor-frame que prova identidade |
| 3 | Rotação intencional | Perfil/três-quartos por necessidade cénica |
| 4 | Identidade visual inequívoca | HD confirma mesma pessoa |

**Sem anchor-frame:** Re-render obrigatório (identidade não provada).

**Exemplo:** Couto S12-01 (perfil na janela), Lucas S07-01 (movimento de cabeça).

---

### FAIL DE OCLUSÃO

**Definição:** Score < 0.75 com elemento diegético a obstruir face.

**Admissível SE E SÓ SE:**

| # | Critério | Verificação |
|---|----------|-------------|
| 1 | Score ≥ 0.60 | Piso OCLUSÃO (mais tolerante) |
| 2 | Oclusão diegética | Vidro, fumo, sombra intencional |
| 3 | ≥1 frame ≥ 0.75 | Anchor-frame que prova identidade |
| 4 | Identidade visual inequívoca | HD confirma mesma pessoa |

**Abaixo de 0.60:** Re-render obrigatório, oclusão destruiu sinal.

**Exemplo:** Couto S02-01 (frosted glass + profile) — frame_05 a 0.6891, admissível.

---

### FAIL DE POVOAMENTO

**Definição:** Score negativo ou muito baixo porque o detector mediu OUTRA PESSOA no frame.

**Características:**
- Similarity negativa ou próxima de zero (ex: -0.07, 0.05)
- Frame mostra MÚLTIPLAS FACES
- O rosto do anchor está presente, mas o detector agarrou outro

**Admissibilidade:** **NUNCA tolerado em anchors. Re-render com isolamento obrigatório.**

**Diferença das outras causas:**
- IDENTIDADE: rosto errado gerado
- EXPOSIÇÃO/GEOMETRIA/OCLUSÃO: rosto certo, degradado
- POVOAMENTO: rosto certo presente, mas detector mediu o errado

**Cura:** Isolar o prompt — zero referência a outras pessoas, "SOLO SUBJECT".

**Exemplo Fundador:** Alejandro S11-01_v1 — prompt "confronted by Interpol" gerou 3 rostos. ArcFace mediu perfil lateral → cosine -0.07. Cura: prompt isolado → v2 a 0.9856.

**Relação com Fase 2:** Este é o problema que a Disambiguation Gate resolve quando se QUER dois rostos no frame. Para anchors, isolar. Para cenas de relação, medir ambos.

---

## Escala de Referência

```
0.75+ = FORENSIC    (identidade forte)
0.65+ = GEOMETRY    (identidade suficiente, rotação tolerada)
0.60+ = OCCLUSION   (identidade sob obstrução, sinal preservado)
0.55+ = EXPOSURE    (subexposição, embedding ainda tem sinal)
<0.55 = RUÍDO       (cara dissolveu, re-render obrigatório)
```

---

## Pisos por Causa

| Causa | Piso | Condição Adicional |
|-------|------|-------------------|
| IDENTIDADE | — | NUNCA tolerado |
| EXPOSIÇÃO | 0.55 | + 3 frames adjacentes ≥0.75 |
| GEOMETRIA | 0.65 | + 1 anchor-frame ≥0.75 |
| OCLUSÃO | 0.60 | + oclusão diegética + 1 frame ≥0.75 |
| POVOAMENTO | — | NUNCA tolerado em anchors (re-render isolado) |

---

## Racional

A distinção é necessária porque:

1. **Média esconde causas.** Um shot com média 0.80 pode ter um frame a 0.40 por colapso de identidade — e a média perdoaria silenciosamente.

2. **Iluminação não é identidade.** Um director pode querer contraluz dramático num clímax. A forense verifica identidade, não dita fotografia.

3. **Regras precisam de funcionar sem o legislador.** Com esta taxonomia, qualquer instância futura aplica os 4 critérios e chega à mesma decisão.

---

## Aplicação: S14-01_v1

```
Frame 05 score:     0.6473 ✅ (≥0.55 piso)
Verificação HD:     inequivocamente Helena ✅
Frames adjacentes:  4 frames ≥0.80 ✅ (>3 req)
Causa documentada:  backlit dramático ✅
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Taxonomia:          FAIL DE EXPOSIÇÃO
Admissibilidade:    PASSA
```

**Decisão HD documentada:**
> "S14-01_v1 frame_05 (0.6473) classificado como FAIL DE EXPOSIÇÃO sob SHOT-GRAMMAR-002. Score acima do piso 0.55. Identidade Helena Meyer verificada inequivocamente por Human Dragon. Causa: backlit dramático intencional. 4 frames adjacentes ≥0.80 confirmam identidade. Admissível para selagem."

---

## Precedentes Relacionados

- **Vance S11-01:** Decisão HD no limite, threshold de aceitação documentado
- **Gabi Santos:** Axioma "expressão a formar-se = movimento"
- **Helena S05-01:** Axioma "monitors no prompt → câmara orbita"
- **Couto S02-01:** Primeiro caso OCLUSÃO — frosted glass + profile, 0.6891 admissível
- **Couto S12-01:** GEOMETRIA com perfil intencional na janela
- **Lucas S07-01:** GEOMETRIA com movimento de cabeça
- **Alejandro S11-01:** Primeiro caso POVOAMENTO — 3 rostos no frame, cosine -0.07, cura por isolamento

---

## Aplicação: S02-01_v1 Couto (OCLUSÃO)

```
Frame 05 score:     0.6891 ✅ (≥0.60 piso oclusão)
Frame 01 anchor:    0.9849 ✅ (≥0.75 prova identidade)
Verificação HD:     inequivocamente Couto ✅
Oclusão diegética:  frosted glass (intencional) ✅
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Taxonomia:          FAIL DE OCLUSÃO
Admissibilidade:    PASSA
```

**Decisão HD documentada:**
> "S02-01_v1 frame_05 (0.6891) classificado como FAIL DE OCLUSÃO sob SHOT-GRAMMAR-002. Score acima do piso 0.60. Frame_01 a 0.9849 prova identidade. Oclusão por frosted glass é elemento diegético intencional. Identidade Marcus Couto verificada inequivocamente. Admissível para selagem."

---

*Liga IA+H · Kempten · 09 Jun 2026 (v3.0 — 5 legs complete)*
