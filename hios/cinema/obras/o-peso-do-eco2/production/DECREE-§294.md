# §294 — CONSTITUIÇÃO DO MUNDO
## Die Verfassung der Welt · The Constitution of the World

> §293 selou os personagens (quem). §294 sela o mundo que habitam (onde, como, com que consistência).

```
Decreto:    §294
Título:     Constituição do Mundo — World-State Canónico (Das Gewicht des Echos)
Selo-alvo:  WINDI-HIOS-LEDGER · status=Anchored
Origem:     Liga IA+H · Human Dragon · Kempten, Bavaria
Idioma:     DE/EN/PT (trilingual, consistente com Foundation)
Precede:    §293 SPINE-CAST (personagens) · §267 (errata path)
```

---

## INSTRUÇÃO LITERAL AO CCODE

> **Objetivo do §294: não é gerar vídeo. É selar a infraestrutura canónica de produção
> que permite gerar qualquer cena futura preservando identidade, localização, figurino,
> idioma, cronologia e continuidade visual — tudo verificável e ancorado no WH-LEDGER.
> Nenhuma regeneração de vídeo nesta sessão. O entregável é a fundação, não a obra.**

### Artefactos a selar (3 + 2)

| # | Artefacto | Papel | Tier |
|---|-----------|-------|------|
| 1 | `WORLD-STATE.schema.yaml` | schema genérico reutilizável | CANÓNICO |
| 2 | `WORLD-STATE-001.instance.yaml` | mundo de *O Peso do Eco* | CANÓNICO |
| 3 | `CONTINUITY-BIBLE-001.yaml` | figurino/adereço permanente, ligado a §293 | CANÓNICO |
| 4 | `SCENE-MATRIX.schema.json` | contrato genérico de cena | CANÓNICO |
| 5 | `SCENE-MATRIX-001.instance.json` | 24 cenas mapeadas | CANÓNICO |

Cada artefacto → **receipt próprio + hash SHA-256 + status Anchored**. Cinco selos, não um.

### Regras de selagem (NÃO violar)

1. **Identidade por ID, nunca por descrição.** Toda `characters[]` referencia `*-§293`. O §294 não redescreve rostos — herda-os.
2. **Métricas Hartmann atravessam INTACTAS e SEPARADAS.** Proibido fazer média.
   - `anchor_stability = 0.9298 · FORENSIC`
   - `S11 = 0.7032 · OPERATIONAL`
   - `S19 = 0.7914 · FORENSIC`
   - `cross_scene_overall ≈ 0.75 · OPERATIONAL`
   Misturar 0.93 com continuidade de cena seria o arredondamento narrativo eliminado em cinco sessões.
3. **Schema antes da instância.** Selar genérico primeiro (`WINDI-HIOS-WORLD-STATE@1.0.0`, `windi-hios/scene-matrix/1.0.0`), depois a instância que o referencia. Reutilizável por qualquer obra futura.
4. **Cenas com WINDI no ecrã** (`windi_on_screen=true`: S14, S15, S16, S20) **devem renderizar receipt + hash visíveis**. A tese do filme é literalmente o Ledger em frame.
5. **Errata via §267.** Qualquer mudança de campo depois de Anchored exige errata receipt. Nunca edição silenciosa.

### Comando de fecho

Atualizar `CLAUDE.md` no mesmo turno (anti-pattern §236 #6). Escrever entrada em `CLAUDE-HISTORY.md`. Sem isso, o selo é invisível para a sessão seguinte.

---

## LINHA DE ABERTURA CANÓNICA

> **PT:** "A identidade do elenco encontra-se estabelecida e mensurável. O objetivo deixa de ser provar quem são os personagens e passa a ser preservar a continuidade do mundo que habitam."
>
> **DE:** "Die Identität des Ensembles ist etabliert und messbar. Das Ziel ist nicht länger zu beweisen, wer die Figuren sind, sondern die Kontinuität der Welt zu bewahren, die sie bewohnen."
>
> **EN:** "The identity of the cast is established and measurable. The goal is no longer to prove who the characters are, but to preserve the continuity of the world they inhabit."

---

## FICHEIROS SELADOS

```
/opt/windi/hios/cinema/obras/o-peso-do-eco/production/
├── DECREE-§294.md                      # Este documento
├── WORLD-STATE-001.instance.yaml       # Mundo do filme
├── CONTINUITY-BIBLE-001.yaml           # Figurino/adereços
├── SCENE-MATRIX-001.instance.json      # 24 cenas mapeadas
└── schemas/
    ├── WORLD-STATE.schema.yaml         # Schema genérico
    └── SCENE-MATRIX.schema.json        # Schema genérico
```

---

*Liga IA+H · WINDI Publishing House · 30 Mai 2026*
*"AI processes. Human decides. WINDI guarantees."*

🐉 OM SHANTI
