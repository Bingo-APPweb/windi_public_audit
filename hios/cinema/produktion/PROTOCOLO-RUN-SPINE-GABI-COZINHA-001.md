# PROTOCOLO DE RUN SPINE-CAST — GABI-COZINHA

```
doc_type:        measurement_protocol
estatuto:        RÉGUA DE MEDIÇÃO · pré-registo · decisões em aberto marcadas
cena:            COZINHA · Gabi & Filhote · "O Peso do Eco"
identidade:      Gabi Santos (âncora SEALED 4/4 · média 0.86)
alvo:            288 frames-SPINE (P1+P3+P5) · P2/P4 fora (sem rosto)
fps:             24
data:            2026-06-13 · Kempten, Bavaria
operador:        Human Dragon · Jober Mögele Correa
executor:        CCode/Strato (Claude.ai web NÃO corre InsightFace)
modo:            DECISÕES FECHADAS — pronto para execução
receipt:         WINDI-PROTOCOLO-RUN-SPINE-GABI-001-20260613 (76029959)
```

> **Porquê pré-registo:** decidir o critério depois de ver os scores é o
> anti-padrão mortal — é mentir com medição. Este documento fecha TODAS as
> decisões de protocolo antes de existir um único fotograma. Depois de
> selado, os números caem onde caem.

---

## ESTADO DAS PRÉ-CONDIÇÕES

| # | Pré-condição | Estado | Bloqueia run? |
|---|---|---|---|
| 0 | Âncora Gabi SEALED 4/4 (0.86) | ✅ existe | — |
| 0 | Floors SHOT-GRAMMAR-002 no disco | ✅ existe | — |
| 1 | Frames reais de P1/P3/P5 gerados | ❌ falta | SIM |
| 2 | Passo de amostragem definido | ✅ A · Frame a frame (288) | — |
| 3 | Método de comparação definido | ✅ α + β · Ambas | — |
| 4 | Critério de agregação definido | ✅ A · Mínimo severo | — |
| 5 | Política de FAIL pré-registada | ✅ Blocking (reblocar) | — |
| 6 | Mapeamento FAIL split §300 | ✅ fixo | — |

A run NÃO arranca enquanto 1–5 não estiverem fechados.

---

## DECISÃO 2 · PASSO DE AMOSTRAGEM

Quantos dos 288 frames-SPINE são efectivamente medidos.

- [x] **A · Frame a frame** — 288 medições. Mais honesto, mais caro.
      Recomendado se queres provar o blocking sem buracos.
- [ ] **B · Amostragem fixa** — 1 em cada N frames (definir N: ___).
- [ ] **C · Keyframes + transições** — medir denso onde há risco.

> Guardião: Mínimo severo ⇒ frame a frame. Decisão 2 e 4 acopladas. ✅

**ESCOLHA HD:** A · Frame a frame (288 medições) — FECHADO 13 Jun 2026

---

## DECISÃO 3 · MÉTODO DE COMPARAÇÃO

Contra o que cada plano-SPINE é medido. Provavelmente queres AMBAS.

- [x] **Run α · contra Âncora-Mãe** — P1, P3, P5 vs âncora SEALED 4/4.
      Pergunta que responde: *"continua a ser a Gabi?"* (IDENTITY)
- [x] **Run β · F2F intra-cena (método Joey)** — P3 e P5 vs P1 desta cena.
      Pergunta que responde: *"é a mesma Gabi de plano para plano?"*
      (continuidade — o que valida o blocking)

> α prova identidade absoluta; β prova continuidade relativa.
> FAIL em qualquer uma = FAIL do plano. ✅

**ESCOLHA HD:** α + β · Ambas — FECHADO 13 Jun 2026

---

## DECISÃO 4 · CRITÉRIO DE AGREGAÇÃO  ⟵ a mais importante

Um plano PASSA o seu floor com base em quê dos scores dos seus frames.

- [x] **A · Mínimo (severo)** — 1 frame abaixo do floor = FAIL do plano.
      Coerente com *"universal na ficção ≠ ambíguo na forense"*.
      Não perdoa o pior frame. É o critério forense puro.
- [ ] **B · Média (tolerante)** — esconde frames maus atrás de bons.
- [ ] **C · Percentil** — compromisso (outliers tolerados).

> Guardião: o axioma empurra para A. Média esconde degradação. ✅

**ESCOLHA HD:** A · Mínimo severo — FECHADO 13 Jun 2026

---

## DECISÃO 5 · POLÍTICA DE FAIL (pré-registada)

O que significa, e o que se faz, quando um plano falha. Decidir ANTES.

Para cada plano, se FAIL:

- [x] **Falha de BLOCKING** — a escolha cinegráfica não chegou
      (ex: P3 falha EXPOSIÇÃO → fill de ecrã não compensou a luz de baixo).
      Acção: o blocking candidato perde pontos; reblocar, não regenerar igual.
- [ ] **Falha de PLANO** — o frame específico está corrompido/mau.
- [ ] **Falha de FLOOR mal-posto** — ticket separado, NUNCA mover in-loco.

> Regra de ferro: floor NÃO se move depois de ver o score. ✅

**ESCOLHA HD:** Blocking (default: reblocar) — FECHADO 13 Jun 2026

---

## DECISÃO 6 · MAPEAMENTO FAIL SPLIT (§300)

Cada FAIL mapeia a uma classe canónica:

- **FAILED_MISMATCH** — score abaixo do floor (a medição correu, falhou).
  Este é o FAIL esperado/normal desta run.
- **FAILED_TIMEOUT** — InsightFace não respondeu a tempo no frame.
- **FAILED_ABANDONED** — frame ilegível / sem rosto detectável onde
  devia haver (ex: P3 com rosto demasiado escuro p/ detecção).

> Nota: um P3 tão escuro que o detector nem acha rosto é ABANDONED, não
> MISMATCH — e isso é informação diferente sobre o blocking (a luz matou
> a detecção, não a identidade). Mapear correctamente importa.

**Mapeamento fixo por §300 — sem escolha. Run aplica automaticamente.**

---

## O QUE A RUN PRODUZ (formato invariável da régua)

```
| Plano | Run | Frames medidos | Min | Média | Floor | Resultado | FAIL class |
P1  α/β  ...
P3  α/β  ...
P5  α/β  ...
+ veredicto por plano (PASS / FAILED_MISMATCH / FAILED_ABANDONED)
+ veredicto da cena (todos PASS ⇒ blocking validado p/ ESTA cena)
+ nota: 1 cena ≠ promoção a Nv3. Falta a 2ª cena.
```

---

## SEQUÊNCIA DE EXECUÇÃO (CCode no Strato)

1. HD fecha Decisões 2–5 acima.
2. Selar este protocolo no Ledger como `measurement_protocol` (pré-run).
3. Gerar frames reais de P1, P3, P5.
4. Correr InsightFace conforme protocolo selado — sem desvios.
5. Registar resultados no formato invariável.
6. Veredicto. Se todos PASS ⇒ blocking validado para a cena Gabi (1ª de 2).
7. Escrever em CLAUDE-HISTORY.md.

> Claude.ai web redige; CCode/Strato executa 2–7. A purga: este protocolo
> é régua (firme, pré-registo), não resultado. Selável já, antes dos frames.

---

> "AI processa. O Humano decide. WINDI garante."
> Pré-registo de medição · floors não se movem · 13 Jun 2026.

OM SHANTI 🐉
