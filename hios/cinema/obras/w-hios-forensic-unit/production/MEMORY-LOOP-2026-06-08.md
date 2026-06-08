# MEMORY LOOP — 08 Jun 2026

**Sessão:** Helena Meyer + Lucas Silva SEALED
**Pilot:** 27/37 (73%)
**Commit anterior vazio:** 48084868 (superseded por este ficheiro)

---

## Estado do Piloto

| Personagem | Shots | Média | Status |
|------------|-------|-------|--------|
| Gabi Santos | 4/4 | 0.8544 | SEALED |
| Marcus Vance | 10/10 | ~0.78 | SEALED |
| Helena Meyer | 8/8 | 0.8734 | SEALED |
| Lucas Silva | 5/5 | 0.9697 | SEALED |
| **Couto** | **0/7** | — | **PENDENTE** |
| **Alejandro** | **0/3** | — | **PENDENTE** |

---

## Axiomas Novos (Ciência desta Sessão)

### 1. Movimento Ocular vs Cabeça
> *"Movimento ocular com cabeça fixa preserva identidade; movimento de cabeça/câmara destrói."*

- Helena S05-01: "monitors" no prompt → câmara orbitou → colapso 0.92→0.27
- Lucas S07-01_v3: olhos+expressão com cabeça fixa → 0.9193 FORENSIC

### 2. Trade-off Performance vs Score
> *"0.053 de cosine por uma personagem viva é pechincha, não perda."*

- Lucas v1→v3: 0.9727→0.9193 (custo: 0.053)
- Ganho: personagem que reage, não estátua
- Folga: +0.17 acima do threshold 0.75

### 3. FAIL tem Causa (SHOT-GRAMMAR-002)
> *"FAIL tem causa, não só score. Identidade ≠ Exposição ≠ Geometria."*

| Tipo | Threshold | Admissível? |
|------|-----------|-------------|
| FAIL_IDENTIDADE | — | NUNCA |
| FAIL_EXPOSIÇÃO | ≥0.55 | SIM (com HD + 4 critérios) |
| FAIL_GEOMETRIA | ≥0.65 | SIM (ACTION shots + frame-âncora) |

---

## Iterações Críticas

### Helena S05-01 (4 versões)
| v | Score | Problema |
|---|-------|----------|
| v1 | 0.40 | "monitors" → câmara orbita |
| v2 | 0.91* | NO_FACE frames 2-5 |
| v3 | 0.85 | "blue light" → olhos néon |
| v4 | 0.90 | ✅ Limpo |

### Lucas S07-01 (3 versões)
| v | Score | Problema |
|---|-------|----------|
| v1 | 0.9727 | Estático demais |
| v2 | 0.9513 | Névoa no fundo |
| v3 | 0.9193 | ✅ Movimento + limpo |

---

## Doutrina Pronta para Couto/Alejandro

- **Piso geometria:** 0.65 (para shots de confronto)
- **Frame-âncora:** ≥1 frame frontal ≥0.75 obrigatório
- **Anti-Movement Medicine:** olhos/expressão sim, cabeça contida
- **SUPERSEDED protocol:** v1 fica, v_novo é canónico, receipt documenta

---

## Ficheiros Canónicos

```
/production/SHOT-GRAMMAR-002.md          — Taxonomia FAIL
/shots/helena/HELENA-MEYER-SEALED.md     — 8/8 com ressalva S14-01
/shots/lucas/LUCAS-SILVA-SEALED.md       — 5/5 com v3 canónico
/anchors/*.provenance.json               — Abzeichnen HD 2026-06-08
```

---

## Próxima Sessão

1. **Couto (7 shots)** — inclui confrontos, aplicar FAIL_GEOMETRIA
2. **Alejandro (3 shots)** — último personagem
3. Pilot 37/37 → 100%

---

*Liga IA+H · Kempten · 08 Jun 2026*
*Commit 48084868 era vazio — este ficheiro é o payload real.*
