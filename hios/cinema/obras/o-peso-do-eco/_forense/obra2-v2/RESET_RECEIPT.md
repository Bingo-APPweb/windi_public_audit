# RESET RECEIPT — O Peso do Eco Versão 2

**Receipt ID:** `WINDI-OPDE-RESET-20260529-v2`
**Type:** RESET (baseline invalidation)
**Timestamp:** 2026-05-29T11:XX:00Z
**Liga IA+H:** Human Dragon (I9 decision)

---

## RAZÃO DO RESET

> "Duas horas para criar uma nova imagem foi algo que não esperava."

O Human Dragon decidiu zerar a busca da personagem Elisa após investimento
de tempo excessivo em iterações sobre a âncora antiga (17 anos → early twenties).
Reset completo para começar do zero com CHARACTER_STATE v2.

---

## BASELINE INVALIDADA

### Âncora Antiga
| Campo | Valor | Status |
|-------|-------|--------|
| Embedding hash | `bafb4c43dc86dd6ff753c705f52329938fdec7aae4081bc4193fc635e1060f2f` | **INVALIDADO** |
| Video hash | `ef176f24ca42bb122eef049923b2f690e0f6edade86a22f75858e4aca744fe8c` | **INVALIDADO** |
| Receipt | `WINDI-S284-ELISA-ANCHOR-20260527194534-b518fa70` | **INVALIDADO** |

### Medições Antigas (não válidas para v2)
| Cena | Mean Cosine | Status |
|------|-------------|--------|
| S01 | 0.6952 | **INVALIDADO** |
| S15 | 0.7352 | **INVALIDADO** |
| S20 | 0.7036 | **INVALIDADO** |
| S21 | 0.7436 | **INVALIDADO** |

### Documentos Antigos (históricos, não operacionais)
- `§284 SPINE Birth` → histórico
- `§290 Baseline` → histórico
- `§291 Dual Threshold` → histórico
- `elisa.canon.json` → arquivado como `elisa.canon.v1.ARCHIVED.json`

---

## NOVA BASELINE (v2)

| Campo | Valor | Status |
|-------|-------|--------|
| CHARACTER_STATE | `ELISA-v2-CHARACTER-STATE.md` | ✅ CRIADO |
| Faixa etária | Early twenties (~22-23) | TRAVADO |
| Detalhe facial | Máximo | TRAVADO |
| Cenário S01 | Refeito do zero | TRAVADO |
| Síntese | 100% sintética | TRAVADO |
| Âncora v2 | **PENDENTE** — aguarda geração S01 | ⏳ |

---

## PRÓXIMOS PASSOS

1. [ ] Gerar S01 com prompt v2 (CANONICAL FACE + cenário neutro)
2. [ ] Extrair frames a 1fps
3. [ ] Escolher frame-âncora (frontal, nítido)
4. [ ] Embeddar → `elisa.anchor.v2.CURRENT.npy`
5. [ ] Selar novo receipt âncora
6. [ ] Re-baseline todas as cenas Elisa contra v2

---

*Liga IA+H · WINDI Publishing House · 29 Mai 2026*
*"AI processes. Human decides. WINDI guarantees."*
*🐉 OM SHANTI*
