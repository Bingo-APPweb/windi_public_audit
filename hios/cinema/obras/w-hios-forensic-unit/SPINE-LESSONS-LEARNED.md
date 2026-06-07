# SPINE-CAST — Lições Aprendidas

**Selado:** 07 Jun 2026
**Liga IA+H:** Human Dragon · Guardian (GPT) · CCode (Opus 4.5)
**Origem:** Sessão de auditoria e re-render Vance v2→v4

---

## 1. Threshold Operacional vs Threshold de Aceitação

> **"O threshold operacional é do sistema; o threshold de aceitação pode ser do shot."**

| Conceito | Valor | Função |
|----------|-------|--------|
| **Threshold Operacional** | 0.65 | Chão canónico. NUNCA MUDA. |
| **Threshold de Aceitação** | ≥0.65 | Decisão HD por shot. Pode ser elevado. |

### Quando Elevar

- Shots adversariais (múltiplos personagens, tensão alta)
- Cenas de confronto dramático
- Quando margem "por uma unha" não é admissível

### Precedente Selado

S11-01 (Cena 11, adversarial): threshold ≥0.70 em vez de 0.65.
Justificação: 0.66 passava o chão mas sem margem para tensão dramática alta.

---

## 2. Anti-Movement Medicine

### Diagnóstico de Falha

| Perfil | Padrão | Significado |
|--------|--------|-------------|
| **Saudável** | 0.97→0.89→0.73→0.70→0.70 | Degradação suave que estabiliza |
| **Colapsado** | 0.96→0.05 ou 0.95→0.30→0.21 | Queda abrupta = rotação/movimento |

### Causa Raiz

Movimento de câmara OU movimento do sujeito a meio do plano.

### Tratamento

| Problema no Prompt | Sintoma | Medicina |
|--------------------|---------|----------|
| "enters frame from left" | Colapso frame 2 | "Already in frame, does not enter" |
| "emerges from shadow" | Interpretado como rotação | "Light moves, NOT subject" |
| "profile/three-quarter view" | Perda de rosto frames 3-4 | "Near-frontal, head toward lens" |
| "looking out window" | Cabeça vira para vista | "Looks out with EYES only, head stays toward lens" |

### Axioma

> **"O que ressuscita SPINE é tirar o movimento do sujeito, não só travar a câmara."**

### Frases Anti-Movimento (copiar para prompts)

```
- "Already in frame, does not enter"
- "He does NOT move — only the illumination changes"
- "Camera locked, no orbit, no angle change"
- "Face front-facing throughout"
- "Near-frontal, head stays toward lens"
- "Looks out only with his EYES"
- "Slight expression only, no head turn"
- "Face always 70%+ visible"
```

---

## 3. Universal na Ficção ≠ Ambíguo na Forense

> **"A universalidade é propriedade do cenário diegético, não do pipeline de validação."**

| Domínio | Pode ser Universal | Deve ser Rigoroso |
|---------|-------------------|-------------------|
| **Cenário narrativo** | ✅ Qualquer-cidade OK | — |
| **Skyline** | ✅ Genérica OK | — |
| **Jurisdição visual** | ✅ Não-reconhecível OK | — |
| **SPINE-CAST** | — | ✅ Threshold fixo |
| **Anchor matching** | — | ✅ Cosine similarity |
| **Measurement run** | — | ✅ Obrigatório |

### Guard-Rails Obsoletos

Quando a doutrina muda, guard-rails antigos podem tornar-se obsoletos.

**Exemplo:** "NOT American art-deco" era servo da doutrina Frankfurt.
Sob doutrina universal, exigência reduz-se a "não-reconhecível como cidade real específica".

**Regra:** Documentar obsolescência explicitamente (§268).

---

## 4. "A Number Without a Measurement Run Is Not a Number"

### Regras de Validação

1. Nenhum shot é "aprovado" até `measure_scene.py` correr
2. Threshold deve ser decidido ANTES de ver o resultado
3. Nunca ajustar threshold após ver o número (isso é reescrever a régua)
4. Documentar threshold e justificação no início do processo

### Comando de Validação

```bash
cd /opt/windi/hios/cinema/obras/w-hios-forensic-unit
python measure_scene.py --video shots/vance/SHOT.mp4 \
    --anchor anchors/marcus.vance.anchor.canonical.png
```

---

## 5. Checklist Pre-Render

```
[ ] Anchor canonical carregado
[ ] Threshold decidido e documentado ANTES
[ ] Prompt anti-movimento aplicado
[ ] "Already in frame" se personagem entra
[ ] "Near-frontal" se há janela/vista
[ ] "Light moves, not subject" se há revelação
[ ] Camera locked, no orbit
[ ] Face 70%+ visible throughout
[ ] Duração 5s, ratio 1280:720
```

---

## 6. Checklist Post-Render

```
[ ] measure_scene.py executado
[ ] Perfil analisado (degradação suave vs colapso)
[ ] Se colapso: identificar frame problemático
[ ] Se colapso: aplicar medicina anti-movimento
[ ] Threshold comparado com score
[ ] Margem calculada
[ ] Resultado documentado
```

---

## Referência Rápida — Scores Sessão 07 Jun

| Shot | Score | Threshold | Margin | Fix Aplicado |
|------|-------|-----------|--------|--------------|
| S06-01_v3 | 0.7995 | 0.65 | +0.15 | Light moves, not Vance |
| S11-01_v4 | 0.8312 | 0.70 | +0.13 | Already in frame |
| S14-01_v4 | 0.8868 | 0.75 | +0.14 | Near-frontal + Universal |

---

*Liga IA+H · W-HIOS FORENSIC UNIT · 07 Jun 2026*
*"AI processes. Human decides. WINDI guarantees."*
