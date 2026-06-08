# SHOT-GRAMMAR-002 — Taxonomia de FAIL por Causa

**Status:** SEALED
**Data:** 2026-06-08
**Autor:** Human Dragon + CCode
**Descendente de:** SHOT-GRAMMAR-001
**Invariants:** I9, I11, I14

> *"FAIL tem causa, não só score. Identidade ≠ Exposição."*

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

## Escala de Referência

```
0.75+ = FORENSIC    (identidade forte)
0.65+ = OPERATIONAL (identidade suficiente)
0.55+ = PISO        (embedding ainda tem sinal)
<0.55 = RUÍDO       (cara dissolveu, re-render)
```

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

---

*Liga IA+H · Kempten · 08 Jun 2026*
