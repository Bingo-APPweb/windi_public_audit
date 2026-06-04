# W-HIOS FORENSIC UNIT — CAST MATERIAL PROOF
## Prova Material de Existência do Cast

**Generated:** 2026-06-02T16:51:39Z
**Updated:** 2026-06-04T17:05:00Z — **6/6 APROVADOS (I9 GATE PASSED)**
**Liga IA+H:** Human Dragon (I9) · Guardian · Architect · CCode (Witness)

---

## ABZEICHNEN (Custódia Humana) — §299-FINAL

### 6/6 Anchors Vistos Directamente

> **Regra Guardian:** "O Abzeichnen faz-se sempre sobre o ficheiro-âncora, nunca sobre um frame candidato."

Todas as 6 caras foram mostradas ao Human Dragon como **ficheiro-âncora directo** (não frames de subpasta).
Isto elimina a possibilidade de discrepância entre o que se vê e o que se sela.

| Personagem | Ficheiro Visto | Human Dragon Viu | Status |
|------------|----------------|------------------|--------|
| Gabi Santos | `gabi.santos.anchor.v1.png` | ✅ 02 Jun 2026 | ✅ **APROVADO** |
| Helena Meyer | `helena.meyer.junior.anchor.v1.png` | ✅ 04 Jun 2026 | ✅ **APROVADO** |
| Marcus Vance | `marcus.vance.anchor.v1.png` | ✅ 04 Jun 2026 | ✅ **APROVADO** |
| Marcus Couto | `marcus.couto.anchor.v1.png` | ✅ 04 Jun 2026 | ✅ **APROVADO** |
| Lucas Silva | `lucas.silva.anchor.v1.png` | ✅ 04 Jun 2026 | ✅ **APROVADO** |
| Alejandro | `alejandro.valenzuela.anchor.v1.png` | ✅ 04 Jun 2026 | ✅ **APROVADO** |

**Verificação I9:** 04 Jun 2026 ~17:00 UTC · Human Dragon confirmou "É ele/ela?" via GitHub
**Método:** Visualização directa dos PNGs no repositório público windi_public_audit

### Notas do Juiz (Guardian) — Actualizadas 04 Jun 2026

**Heterogeneidade de Fundo (Paper-001 — Declarar, não esconder):**
- **Vance:** Fundo ESCURO (não cinza) — quebra Lição B do Joey. Detection sólida (0.8638), mas âncora nasceu em condições diferentes das outras cinco. **VARIÁVEL A DECLARAR.**
- **Helena:** Fundo CLARO com algum brilho na testa/maçãs do rosto — afasta-se do ideal cinza-neutro. Funciona, mas é a que mais se afasta. **VARIÁVEL A DECLARAR.**

**Observações técnicas:**
- **Gabi:** Fundo cinza perfeito, luz lateral suave, zero gloss. Registo da Cena 0 (humano, desarmado) — correcto para stress-test viva-vs-arquivo.
- **Couto × Vance:** Cosine 0.2057 — visualmente e numericamente são duas pessoas distintas. Espelho moral funciona.
- **Lucas:** Barba stubble introduz variância no ArcFace. O 0.8119 mais baixo é esperado. É o personagem a vigiar na Cena 11.
- **Alejandro:** Fundo cinza, limpo, frontal. Sólido.

**Notas históricas (02 Jun):**
- Helena: Blazer preto/carvão (spec dizia azul escuro). Não desqualifica — ArcFace mede geometria facial.
- Couto/Lucas/Alejandro: Inicialmente vistos como frames de subpasta. Corrigido ao mostrar anchors directos.

---

## ASSETS COM HASH SHA-256

| Personagem | Ficheiro | SHA-256 | Tamanho |
|------------|----------|---------|---------|
| Alejandro Valenzuela | alejandro.valenzuela.anchor.v1.png | `bcec886a46d78493...` | 544K |
| Gabi Santos | gabi.santos.anchor.v1.png | `03784039a0aa4bd1...` | 531K |
| Helena Meyer Junior | helena.meyer.junior.anchor.v1.png | `5262ad1cf95fefd0...` | 1.3M |
| Lucas Silva | lucas.silva.anchor.v1.png | `9bcbb6a4ef1bda20...` | 467K |
| Marcus Couto | marcus.couto.anchor.v1.png | `5083fd1c0cf64eab...` | 367K |
| Marcus Vance | marcus.vance.anchor.v1.png | `3ec94552f85243fe...` | 1.6M |

## DETECTION SCORES

| Personagem | Det.Score | Fundo | Status |
|------------|-----------|-------|--------|
| Gabi Santos | 0.8755 | ✅ Cinza | 🟢 **LOCKED** |
| Helena Meyer | 0.8636 | ⚠️ Claro | 🟢 **LOCKED** |
| Marcus Vance | 0.8638 | ⚠️ Escuro | 🟢 **LOCKED** |
| Marcus Couto | 0.8811 | ✅ Cinza | 🟢 **LOCKED** |
| Lucas Silva | 0.8119 | ✅ Cinza | 🟢 **LOCKED** |
| Alejandro Valenzuela | 0.8763 | ✅ Cinza | 🟢 **LOCKED** |

**TOTAL:** 6/6 LOCKED · Human Dragon I9 Gate: 04 Jun 2026
**Nota Paper-001:** 4/6 em fundo cinza ideal, 2/6 em fundos não-ideais (declarar como variável)

---

## FULL SHA-256 HASHES

```
bcec886a46d78493601a663d204fd8b2b3e4c483176ef1ded18e5ddd57ef0189  alejandro.valenzuela.anchor.v1.png
03784039a0aa4bd1306518d847aeae69915c566f1ef7e5a1e81822d82f2e1c82  gabi.santos.anchor.v1.png
5262ad1cf95fefd0176c4cc115dbfac5040b81627b3178efabcc3980ca0020a2  helena.meyer.junior.anchor.v1.png
9bcbb6a4ef1bda2010e77bb522ef222efbf9ddac26ab461b09dcab70e42c3808  lucas.silva.anchor.v1.png
5083fd1c0cf64eab3b40dacab335adecdd125a643e9ca5e31b4acd9e068e515a  marcus.couto.anchor.v1.png
3ec94552f85243fe5b4773b0128767d1898cd9690ec9a7a777ab21fb2ddb5c2e  marcus.vance.anchor.v1.png
07ae1d695c87486ab1fcb3690551a936c7629c8fd6ae217402300b24592c5b5f  alejandro.valenzuela.anchor.v1.mp4
1b6b784cfd66eeca85e5e7e936d10d5c579d7742f5a841d78a486a80bc6a8f2e  gabi.santos.anchor.v1.mp4
920b93ef926ed1c37d8a8e6b2dfdd16ec76eb16d174fca18cff97be90382a419  lucas.silva.anchor.v1.mp4
3b0b265cf29957a3ef773bc7697febadc5bc43863d6af405f750b79bb3e6d6c2  marcus.couto.anchor.v1.mp4
02df054ac7ebbe840de23eeea4de31ff349831b09ed2020735047388f6e7da51  alejandro.valenzuela.anchor.v1.provenance.json
0a519d165e99b9b6cb006a5e33b5e956812ec1c8266bb1f363267098da49c090  gabi.santos.anchor.v1.provenance.json
6a002605e434509e08474e2a788c40baf2741e517cce9e70e63cc27bca4aa5f0  helena.meyer.junior.anchor.v1.provenance.json
d36a640c70dc498f6f5256188c3883db06dc23a4dcf53cde4f481f21d0bae67e  lucas.silva.anchor.v1.provenance.json
136471c0bd6814dd869289b07e829c3e7a6c5514da61d278b28bd0207410be5f  marcus.couto.anchor.v1.provenance.json
af6f4e602ab4568829361d750345c96b9fc024ef1d6ca29e1e141b46dc4d992d  marcus.vance.anchor.v1.provenance.json
```

---
*Liga IA+H · WINDI Publishing House · 2026-06-02*
