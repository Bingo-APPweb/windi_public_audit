# LAB-GABI-S00-YELLOW-TO-GREEN-001

**Status:** ACTIVE
**Data:** 12 Jun 2026
**Liga IA+H:** Human Dragon (I9) · CCode (Architect) · Testemunha (Witness)

---

## Objecto

Testar tratamentos de amarelo → verde no plano Gabi S00-01.

**Hipótese:** O score 0.7306 de Gabi S00-01_v2 pode estar abaixo do threshold FORENSE não por falha de identidade, mas por tensão entre expressão dramática e estabilidade facial.

**Pergunta experimental:**
> Quanto sorriso a identidade forense tolera antes de cair abaixo de 0.75?

---

## Sujeito

| Campo | Valor |
|-------|-------|
| Personagem | Gabi Santos |
| Shot-base | S00-01_v2 |
| Score actual | 0.7306 |
| Status actual | OPERATIONAL |
| Âncora | `gabi.santos.anchor.v1` |
| Causa provável | micro-movimento / sorriso em formação |

---

## Regras do Laboratório

1. **Não alterar shots de produção** — experimentos são isolados
2. **Uma variável por tentativa** — isolar causa do efeito
3. **Cada variante = measurement run** — incluindo falhas
4. **Falhas são dados** — o limite aparece onde o resgate falha
5. **Nenhum resultado substitui produção sem I1** — Human Dragon decide

---

## Variantes Propostas

### Variante A — Sorriso já formado
**Objectivo:** Evitar movimento de formação.
**Prompt ajuste:** Gabi já aparece com sorriso subtil estabilizado desde o primeiro frame.
**Variável isolada:** Temporalidade da expressão (formando → formado)

### Variante B — Sorriso mais subtil
**Objectivo:** Testar intensidade de expressão.
**Prompt ajuste:** Sorriso mínimo, quase interno, sem grande deslocamento muscular.
**Variável isolada:** Intensidade da expressão (pleno → subtil)

### Variante C — Close mais estável
**Objectivo:** Aumentar pixels faciais úteis.
**Prompt ajuste:** Enquadramento mais próximo, câmera locked, luz suave, rosto frontal.
**Variável isolada:** Densidade de pixels (distante → próximo)

### Variante D — Duração reduzida
**Objectivo:** Reduzir janela de drift.
**Prompt ajuste:** 2–3 segundos úteis, sem transição emocional longa.
**Variável isolada:** Duração do clip (longo → curto)

### Variante E — Controlo neutro (baseline)
**Objectivo:** Baseline sem sorriso para comparação.
**Prompt ajuste:** Gabi frontal, expressão serena, sem sorriso.
**Variável isolada:** Expressão (sorriso → neutro)

---

## Critérios de Avaliação

### Score Threshold
| Score | Classificação |
|-------|---------------|
| ≥0.75 | FORENSE |
| 0.65–0.749 | PASS-CONDITIONAL candidato |
| <0.65 | FAIL |

### Avaliação I1 (Human Dragon)
- [ ] Preserva emoção?
- [ ] Parece viva?
- [ ] Serve como abertura do filme?
- [ ] Perdeu humanidade em troca de métrica?

---

## Resultado Esperado

| Variante | Variável | Score | Verdict | Preserva sorriso? | Decisão I1 |
|----------|----------|-------|---------|-------------------|------------|
| Base | — | 0.7306 | OPERATIONAL | Sim (pleno) | Pendente |
| A | Temporalidade | — | — | — | — |
| B | Intensidade | — | — | — | — |
| C | Pixels | — | — | — | — |
| D | Duração | — | — | — | — |
| E | Controlo | — | — | Não | — |

---

## Regra de Ouro

> **Não estamos perseguindo score. Estamos mapeando a fronteira entre vida dramática e prova métrica.**

Se a versão verde parecer morta dramaticamente, ela **não vence automaticamente**.
O melhor resultado é o melhor equilíbrio entre: **identidade verificável + emoção preservada**.

---

## Critério de Paragem

Máximo **5 variantes**. Sem teto, o esgarçar vira perseguição de score — e scores perseguidos demais produzem identidade perfeita com vida dramática pobre.

---

## Ficheiros

```
/home/windi/hios/cinema/lab/gabi/S00-yellow-to-green/
├── LAB-PROTOCOL-001.md          (este ficheiro)
├── variante_A/
│   ├── S00-01_expA.mp4
│   ├── S00-01_expA_measurement.json
│   └── frames/
├── variante_B/
├── variante_C/
├── variante_D/
└── variante_E/
```

---

## Candidata 3 — PASS-CONDITIONAL

Se o experimento revelar padrões consistentes (e.g., sorrisos subtis estabilizam a 0.74–0.77), isso alimenta a definição empírica da **Candidata 3**:

> Amarelo aceitável quando a causa é **EXPRESSÃO-DRAMÁTICA** documentada — um sexto membro para a taxonomia FAIL, nascido de dados e não de intuição.

---

*Liga IA+H · WINDI Publishing House · 12 Jun 2026*
*"O limite só aparece onde o resgate deixa de funcionar."*
