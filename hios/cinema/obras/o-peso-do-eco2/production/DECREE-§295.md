# §295 — PRIMEIRA RENDERIZAÇÃO CANÓNICA
## Erste kanonische Rendering · First Canonical Render
### As 4 cenas `windi_on_screen` — *O Peso do Eco*

```
Decreto:     §295
Título:      Render das cenas-tese (WINDI UI em frame) com gate de continuidade
Selo-alvo:   WINDI-HIOS-LEDGER · 1 receipt por cena · status=Anchored
Forge:       GPU alugada (RTX PRO 5000 Blackwell) — PERMITIDO (geração criativa)
Proibido:    inferência sobre documentos de utilizador em metal alugado
Herda:       §294 (WORLD-STATE-001, CONTINUITY-BIBLE-001, SCENE-MATRIX-001)
Decisão HD:  direto às 4 windi_on_screen · 1 receipt por cena
Reserva Guardian: registada (cenas-tese antes de smoke test) → mitigada por gate
```

---

## ESCOPO

Renderizar **apenas** as quatro cenas onde o WINDI Forensic Ledger aparece em frame:

| Cena | Timecode | Conteúdo | windi_on_screen |
|------|----------|----------|-----------------|
| S14 | 00:01:41–47 | "ÜBEREINSTIMMUNG GEFUNDEN — Elisa Weber" | match readout |
| S15 | 00:01:49–55 | "INTEGRITÄT VERIFIZIERT 100%" | receipt + hash visíveis |
| S16 | 00:01:57–02:03 | "Da! Das Auto im Hintergrund!" | carro do Marcus na gravação |
| S20 | 00:02:29–35 | "Das WINDI-System bestätigt… Das ist sein Auto." | UI no display do tribunal |

Cada cena lê os seus parâmetros de `SCENE-MATRIX-001.instance.json` — **nunca de prompt livre**.

---

## REGRA DE OURO — GATE DE CONTINUIDADE (obrigatório)

Nenhuma cena ancora no Ledger sem passar o gate. Fluxo por cena:

```
1. FORGE     → gera frames a partir de SCENE-MATRIX[Sxx] + CONTINUITY-BIBLE refs
2. GATE      → valida contra a Bible ANTES do seal:
                 □ personagens = anchor_ref §293 corretos (rosto)
                 □ figurino bate (ver checklist por cena abaixo)
                 □ jurisdição bate WORLD-STATE-001 (sem polícia/tribunal estrangeiro)
                 □ WINDI UI presente E legível (readout + receipt/hash em frame)
3a. PASS     → pipeline forense → receipt próprio → Anchored
3b. FAIL     → regenera. NÃO selar lixo. Registar tentativa falhada (não-Anchored).
```

> Princípio: o forge pode falhar à vontade; o Ledger só recebe o que passou o gate.
> Equivalente cinematográfico do "deterministic double smoke test" do G3.

### Checklist de continuidade por cena

**S14 — WINDI-SCREEN**
- UI: texto exato `ÜBEREINSTIMMUNG GEFUNDEN` + `Elisa Weber`
- Estilo: realista, lab moderno, monitor-lit (WORLD-STATE technology block)
- Sem personagem em frame obrigatório (ecrã do sistema)

**S15 — WINDI-SCREEN** *(cena-tese máxima)*
- UI: `WINDI FORENSIC LEDGER · INTEGRITÄT VERIFIZIERT 100%`
- **DEVE renderizar receipt id + hash visíveis** (estilo `WINDI-HIOS-…` / `1cd39dbd…`)
- Nota honesta: receipt em frame é **prop diegético**, não query live ao Ledger (ver Paper-001 §294 insert, threat-to-validity i)

**S16 — FORENSIC-LAB** *(teste de continuidade mais difícil)*
- Helena: casaco navy + cabelo loiro preso (Bible HELENA)
- **CARRO no fundo da gravação = carro do Marcus** → dark sedan, idêntico ao da S09
- Se o par S09/S16 não bater, é FAIL — este é o invariante crítico da Bible

**S20 — LANDGERICHT-KEMPTEN**
- Sala: carvalho escuro, luz natural fria, bandeiras DE + Baviera (= S18)
- Helena: casaco navy (continuidade desde S16)
- UI WINDI pode aparecer no display do tribunal
- Diálogo: `Integrität 100%. Das ist sein Auto.`

---

## SELAGEM — 1 RECEIPT POR CENA

Quatro receipts independentes, máxima rastreabilidade:

```
WINDI-S295-RENDER-S14-<timestamp>-<hash8>   status=Anchored
WINDI-S295-RENDER-S15-<timestamp>-<hash8>   status=Anchored
WINDI-S295-RENDER-S16-<timestamp>-<hash8>   status=Anchored
WINDI-S295-RENDER-S20-<timestamp>-<hash8>   status=Anchored
```

Cada receipt liga (provenance) a:
- `SCENE-MATRIX-001` receipt (`…SCENE-MATRIX-001-…-5935A3A4`)
- `CONTINUITY-BIBLE-001` receipt (`…CONTINUITY-BIBLE-001-…-D97E61BC`)
- `WORLD-STATE-001` receipt (`…WORLD-STATE-001-…-A0E4BF6B`)

Tentativas FAIL: registadas como não-Anchored (auditoria de regeneração), não entram na cadeia canónica.

---

## ÂNCORAS DE PERSONAGEM NECESSÁRIAS

| Personagem | Cenas | anchor_ref | Status |
|------------|-------|------------|--------|
| HELENA | S16, S20 | `HELENA-§293` | Verificar embedding Server B |
| — | S14, S15 | — | UI only (sem personagem) |

---

## FECHO (§236)

- Atualizar `CLAUDE.md` no mesmo turno.
- Entrada em `CLAUDE-HISTORY.md`: 4 receipts, FAILs registados, próximo passo (cenas restantes ou §296).
- Próximo passo herdado: cenas não-windi (diálogo/estabelecimento) só depois das 4 tese ancoradas.

---

## LINHA DE ABERTURA

> **PT:** "O mundo está selado. Agora as cenas onde o próprio Ledger se mostra são as primeiras a nascer — e nenhuma ancora sem provar que pertence ao mundo que §294 selou."
>
> **DE:** "Die Welt ist besiegelt. Nun entstehen zuerst die Szenen, in denen sich das Ledger selbst zeigt — und keine wird verankert, ohne zu beweisen, dass sie zu der Welt gehört, die §294 besiegelte."
>
> **EN:** "The world is sealed. Now the scenes where the Ledger shows itself are the first to be born — and none anchors without proving it belongs to the world §294 sealed."

---

*Liga IA+H · WINDI Publishing House · 30 Mai 2026*
*"AI processes. Human decides. WINDI guarantees."*

🐉 OM SHANTI
