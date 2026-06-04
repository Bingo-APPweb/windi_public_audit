# ATR — Admissibilidade Travada pelo Roteiro

**Corolário aplicado da PAF — Princípio da Autoria Forense (Lei VIII, IRREMEDIÁVEL)**
**Domínio:** WINDI-HIOS Cinema
*Script-Locked Admissibility*

> **§299** · selado por Human Dragon 🐉 · 2026-06-04
> **Invariants:** I1, I9, I11, I14
> **Commit:** ver receipt no Ledger

---

## Frase canónica

> **O roteiro tranca a admissibilidade, não a geração.**
> **O WINDI garante no gate, não no render.**

---

## Filiação constitucional

A ATR **não é lei nova**. É a PAF aplicada ao audiovisual generativo.

A PAF (Lei VIII) estabelece *que* a autoria é forense. A ATR estabelece *como* a
autoria humana se faz cumprir quando a matéria-prima é gerada por modelos
estocásticos:

| Acto | Agente | Papel na ATR |
|------|--------|--------------|
| Decidir | Humano | Escreve e aprova o roteiro — o contrato de admissão |
| Garantir | WINDI | Opera o gate de validação que executa o contrato |
| Processar | IA | Gera blocos candidatos (Veo / Runway / Sora) |

**A IA processa. O Humano decide. O WINDI garante.**

Por descender directamente da PAF, a ATR **herda a irremediabilidade** da Lei VIII
sem necessitar de invariante próprio.

---

## As três proposições

**1. A geração é estocástica e permanece estocástica.**
Não prometemos determinismo sobre Veo, Runway ou Sora. Mesmo com *seed* fixa não
existe controlo ao nível do pixel. Quem prometer "roteiro que compila o filme
idêntico" está a construir sobre areia. O WINDI não mente — e por isso não promete
isto.

**2. O roteiro define o critério de admissão de cada bloco à obra.**
É **contrato, não compilador**. O roteiro não comanda o motor; define o que pode
*entrar na obra*. A força não vive na geração — vive no gate.

**3. Nada entra na montagem sem passar o critério que o próprio roteiro escreveu.**
`on_fail → Regeneration Queue` é inegociável. A obra fecha o círculo não obrigando
a geração a obedecer, mas tornando a validação implacável.

---

## Threshold Canónico de Identidade

### O Número

```
validation.identity ≥ 0.68
```

### Derivação (S22 — Primeira Jurisprudência ATR)

O threshold não foi escolhido. Foi **derivado do dado**.

| Parâmetro | Valor | Fonte |
|-----------|-------|-------|
| Drift max (pior impostor) | 0.3572 | Marcus v2 frame_01 |
| Genuine min (pior genuíno) | 0.8140 | Helena v5 frame_08 |
| Gap | 0.4568 | genuine_min - drift_max |
| Bias forense | 70% | margem maior contra impostor |

**Fórmula:**
```
threshold = drift_max + (bias × gap)
threshold = 0.3572 + (0.7 × 0.4568)
threshold = 0.6770 → arredondado para 0.68
```

**Margens resultantes:**
```
vs impostor: 0.68 - 0.3572 = 0.3228  ← margem MAIOR (forense)
vs genuíno:  0.8140 - 0.68 = 0.1340  ← margem menor (custo: regenerar)
```

### Base de Evidência

| Personagem | Genuine Min | Drift Max | Separation | Frames |
|------------|-------------|-----------|------------|--------|
| Marcus | 0.8448 | 0.3572 | 0.4876 | 21 |
| Helena | 0.8140 | 0.3149 | 0.4991 | 18 |

**Convergência:** Δ < 0.05 em todas as métricas → threshold **canónico** (não por-personagem).

**Held-out testado:**
- Cross-character (Helena vs Marcus anchor, vice-versa)
- Drift v2 (mesmo personagem, versão antiga)
- Drift v3 (mesmo personagem, versão intermédia)
- Drift v4 (mesmo personagem, versão recente)

### Nota de Recalibração

O threshold é canónico **com a base de evidência actual** — dois personagens,
três tipos de held-out (63 frames). Se um terceiro personagem divergir
significativamente (Δ > 0.10), a ATR não quebra; **recalibra**. O número é
forense, não eterno.

---

## Schema do bloco de cena

Cada bloco do roteiro é legível por máquina e costura o que já existe — Scene
Matrix, Continuity Bible, Regeneration Queue, passaporte SPINE:

```yaml
SCENE S22:
  anchor.character     : marcus@spine-v4
  anchor.location      : berlin-office@env-001
  directive.shot       : "médio, noite, luz fria"
  directive.dialog     : [...]  # idioma: DE
  generation.engine    : runway-gen4

  validation.identity  : ≥ 0.68   # threshold canónico ATR
  validation.continuity: vs S21.last_frame

  on_fail              : → Regeneration Queue
  on_pass              : → seal → Ledger
```

O roteiro é a chave porque define o **critério de admissibilidade** — não porque
comanda o motor.

---

## Custo × Complexidade (Primeira Linha)

```
S22 · gate-only · 04 Jun 2026
  frames processados : 63
  tempo embedding    : ~15s
  tempo total        : ~20s
  custo externo      : 0 tokens (local, ArcFace/InsightFace)
  threshold extraído : 0.68 (derivado, não escolhido)
  separação mínima   : 0.4876
```

---

## Nomenclatura

- **ATR** — Admissibilidade Travada pelo Roteiro
- EN: *Script-Locked Admissibility*
- Evitar "SLA" (colide com *service level agreement*)
- Evitar "script-locked generation" — descreve a leitura falsa

O correcto é **script-locked admissibility**: o roteiro tranca o que entra na
obra, não o que sai do modelo.

---

## Ficheiros de Suporte

| Ficheiro | Localização |
|----------|-------------|
| Script S22 | `/opt/windi/hios/cinema/obras/o-peso-do-eco/scripts/s22_gate_calibration.py` |
| Resultados Marcus | `s22_results/S22_GATE_CALIBRATION_20260604_073533.json` |
| Resultados Helena Drift | `s22_results/S22_HELENA_DRIFT_20260604_074046.json` |
| Anchors | `/opt/windi/hios/cinema/obras/o-peso-do-eco/anchors/cast_v2/` |

---

*Corolário da PAF · Lei VIII · WINDI-HIOS Cinema*
*Primeira Jurisprudência: S22 — 04 Jun 2026*

**OM SHANTI 🐉**
