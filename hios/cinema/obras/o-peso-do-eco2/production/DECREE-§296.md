# §296 — INVARIANTE DE COMPOSIÇÃO DA UI
## UI-Kompositions-Invariante · UI Compositing Invariant

```
Decreto:     §296
Título:      A UI WINDI é sempre camada de pós, nunca gerada pelo modelo
Selo-alvo:   WINDI-HIOS-LEDGER · status=Anchored
Origem:      Liga IA+H · Human Dragon · Kempten · 30 Mai 2026
Gatilho:     S14 smoke test FAIL — texto da UI alucinado pelo Veo 3.1
Herda:       §294 (WORLD-STATE, SCENE-MATRIX) · §295 (render policy)
Idioma:      DE/EN/PT
```

> **PT:** "O gerador faz o mundo. A prova faz-se em pós. Um Ledger de integridade não pode exibir texto sem integridade."
> **DE:** "Der Generator macht die Welt. Der Beweis entsteht in der Post. Ein Integritäts-Ledger darf keinen integritätslosen Text zeigen."
> **EN:** "The generator makes the world. The proof is made in post. An integrity ledger must not display text without integrity."

---

## PROBLEMA NOMEADO E SELADO

**Nome:** Generator Text Hallucination in Diegetic UI

**O que é:** Geradores de vídeo (Veo 3.1, Runway, Sora) não renderizam texto legível de forma fiável. Quando uma cena exige que a UI WINDI apareça em frame, o gerador produz texto sem sentido ("Match Pench ind·Seme", "Naring Nomian").

**Por que é constitucionalmente grave neste filme:** A UI WINDI *é a tese*. Um Ledger forense cuja interface exibe texto alucinado contradiz visualmente a afirmação central do filme — integridade verificável. O defeito não é estético; é uma contradição da mensagem.

**Evidência:** S14 smoke test, 30 Mai 2026, render `S14_20260530215636.mp4` (hash `cc2a94b6…`). Composição boa, texto inutilizável. Registado como não-Anchored.

---

## A INVARIANTE

**Em toda cena `windi_on_screen=true`, a UI WINDI é uma camada de pós-produção (overlay vetorial), nunca gerada pelo modelo de vídeo.**

### Divisão de responsabilidade

| Camada | Quem faz | Conteúdo |
|--------|----------|----------|
| Placa (plate) | Gerador (Veo/Runway/Sora) | Ambiente: monitor, lab, luz, reflexos, mãos, retrato facial |
| Overlay UI | Pós (SVG vetorial) | Todo o texto WINDI: headlines, nomes, receipt, hash, status |

### Regras de plate

O prompt do gerador para cenas `windi_on_screen` deve **pedir um ecrã com a zona de UI neutra** — painel escuro, texto fora de foco, ou superfície lisa — para acolher o overlay. Nunca pedir ao gerador que "escreva" a UI.

### Regras de overlay

1. Texto sempre vetorial (SVG/tipografia limpa), DE correto + legenda conforme SCENE-MATRIX.
2. Em cenas com receipt/hash (S15, e display em S20), os valores são **reais**, injetados do Ledger no momento da composição — placeholders `{{RECEIPT_ID}}` / `{{HASH}}` preenchidos pelo CCode. **Proibido hash decorativo inventado.**
3. Overlays canónicos versionados e selados como artefactos reutilizáveis:
   - `WINDI-UI-S14-MATCH.svg`
   - `WINDI-UI-S15-INTEGRITY.svg`
   - (S16: UI menor no canto; S20: display de tribunal — derivam dos dois acima)

---

## GANHO ACADÉMICO (Paper-001)

Esta invariante resolve parcialmente a *threat-to-validity (i)* já registada no insert §294: os receipts em ecrã deixam de ser props diegéticos inventados e passam a exibir valores reais do Ledger. O filme passa a mostrar **prova verdadeira em frame**, não pintada. Atualizar §7 do insert: distinguir "UI environment (gerada)" de "UI proof layer (real, composta)".

---

## EFEITO RETROATIVO EM §295

- S14: render mantém-se como **plate válida** (ambiente bom). FAIL aplica-se só ao texto. Recompor com overlay → re-gate → seal. Não regenerar a plate desnecessariamente.
- S15, S16, S20: gerar plate com zona de UI neutra; compor overlay; gate; seal individual.

---

## FECHO (§236)
- Atualizar `CLAUDE.md` no mesmo turno.
- Entrada `CLAUDE-HISTORY.md`: §296 selado, overlays criados, S14 a recompor.
- Próximo passo: recompor S14 (plate + overlay), re-gate, primeiro seal Anchored de §295.

🐉 OM SHANTI
