# RESULTADOS — RUN SPINE-CAST GABI-COZINHA

```
doc_type:        measurement_results
estatuto:        MEDIÇÃO COMPLETA · 1ª cena do blocking candidato
cena:            COZINHA · Gabi & Filhote · "O Peso do Eco"
protocol:        WINDI-PROTOCOLO-RUN-SPINE-GABI-001-20260613
identidade:      Gabi Santos (âncora SEALED 4/4 · média 0.86)
data:            2026-06-13 · Kempten, Bavaria
operador:        Human Dragon · Jober Mögele Correa
executor:        CCode (Opus 4.5) · Strato
receipt:         (a preencher após POST)
```

---

## VEREDICTO FINAL

```
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   BLOCKING CANDIDATO: ✅ VALIDADO (1ª cena de 2 necessárias)    ║
║                                                                  ║
║   Todos os 15 frames mediados passaram os floors.               ║
║   Critério: Mínimo Severo (1 frame abaixo = FAIL)               ║
║   Resultado: 0 FAILs                                             ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## DECISÕES DO PROTOCOLO (fechadas antes da medição)

| Decisão | Escolha | Aplicado |
|---------|---------|----------|
| D2 — Amostragem | Frame a frame | ✅ 15/15 frames |
| D3 — Comparação | α + β (ambas) | ✅ 5 runs |
| D4 — Agregação | Mínimo severo | ✅ Min de cada run |
| D5 — Política FAIL | Blocking | (não aplicado — 0 FAILs) |

---

## RESULTADOS POR RUN

### Run α — Identidade Absoluta (vs Âncora-Mãe SEALED)

| Plano | Floor | Min | Avg | Max | Frames | Verdict |
|-------|-------|-----|-----|-----|--------|---------|
| P1 | 0.65 | 0.7462 | 0.8103 | 0.8467 | 5/5 | ✅ PASS |
| P3 | 0.55 | 0.6853 | 0.7393 | 0.8180 | 5/5 | ✅ PASS |
| P5 | 0.65 | 0.6983 | 0.7641 | 0.8341 | 5/5 | ✅ PASS |

**Pergunta respondida:** "Continua a ser a Gabi?" → **SIM**

### Run β — Continuidade Intra-Cena (vs P1 desta cena)

| Plano | Floor | Min | Avg | Max | Frames | Verdict |
|-------|-------|-----|-----|-----|--------|---------|
| P3 | 0.55 | 0.6512 | 0.7144 | 0.7564 | 5/5 | ✅ PASS |
| P5 | 0.65 | 0.6561 | 0.7184 | 0.7829 | 5/5 | ✅ PASS |

**Pergunta respondida:** "É a mesma Gabi de plano para plano?" → **SIM**

---

## FRAME-BY-FRAME (15 frames totais)

### P1 — Âncora Frontal (Run α)
| Frame | Score | Det | Verdict |
|-------|-------|-----|---------|
| P1_frame_001 | 0.7954 | 0.7845 | FORENSE |
| P1_frame_002 | 0.7462 | — | PASS |
| P1_frame_003 | 0.8431 | — | FORENSE |
| P1_frame_004 | 0.8200 | — | FORENSE |
| P1_frame_005 | 0.8467 | — | FORENSE |

### P3 — Sorriso Pousado (Run α)
| Frame | Score | Verdict |
|-------|-------|---------|
| P3_frame_001 | 0.8180 | FORENSE |
| P3_frame_002 | 0.6853 | PASS |
| P3_frame_003 | 0.7050 | PASS |
| P3_frame_004 | 0.7133 | PASS |
| P3_frame_005 | 0.7750 | FORENSE |

### P5 — Erguer Telemóvel (Run α)
| Frame | Score | Verdict |
|-------|-------|---------|
| P5_frame_001 | 0.7888 | FORENSE |
| P5_frame_002 | 0.7861 | FORENSE |
| P5_frame_003 | 0.6983 | PASS |
| P5_frame_004 | 0.7132 | PASS |
| P5_frame_005 | 0.8341 | FORENSE |

---

## VALIDAÇÃO DO BLOCKING CANDIDATO

O **Método de Blocking Forense-Consciente** foi validado nesta cena:

| Movimento | Plano | Testou | Resultado |
|-----------|-------|--------|-----------|
| 1. Ancorar primeiro | P1 | GEOMETRIA | ✅ Min 0.7462 |
| 2. Esconder transição no corte | P3 | EXPOSIÇÃO | ✅ Min 0.6853 |
| 3. Tirar rosto da oclusão | P2/P4 | (sem rosto) | ✅ N/A |
| 4. Subir objecto ao olhar | P5 | GEOMETRIA | ✅ Min 0.6983 |

**Nota:** O blocking funcionou. Os 4 movimentos produziram frames que respeitam os floors. A "câmara serve a identidade" foi demonstrada.

---

## FRAGILIDADE CONHECIDA — P5 (margem apertada)

```
P5 vs P1 (Run β): min 0.6561, floor 0.65
Folga: 0.0061 (seis milésimos)
```

**Análise Guardian:**
- Passou por uma unha. Sob mínimo severo, um frame ligeiramente pior = FAIL.
- O movimento "subir o objecto ao olhar" é o mais frágil dos quatro.
- O telemóvel erguido perto do rosto introduz variação de ângulo e sombra.

**Implicação para 2ª cena:**
- A 2ª cena deve stressar exactamente este movimento.
- Se algum movimento vai falhar, o dinheiro está em P5-análogos.

**Não é FAIL. É aviso útil.**

---

## CONDIÇÃO DE PROMOÇÃO A Nv3

```
Estado actual:    Nv2 (candidato)
Cenas validadas:  1/2
Próximo passo:    Validar 2ª cena distinta
```

> O blocking candidato precisa de **≥2 cenas distintas** para provar que é reprodutível.
> A Gabi-Cozinha é a 1ª. Falta a 2ª para promoção a Nv3 (doutrina selada).

---

## FICHEIROS GERADOS

```
/opt/windi/hios/cinema/produktion/gabi-cozinha/
├── P1_frames/
│   ├── P1_frame_001.png
│   ├── P1_frame_002.png
│   ├── P1_frame_003.png
│   ├── P1_frame_004.png
│   └── P1_frame_005.png
├── P3_frames/
│   ├── P3_frame_001.png
│   ├── P3_frame_002.png
│   ├── P3_frame_003.png
│   ├── P3_frame_004.png
│   └── P3_frame_005.png
├── P5_frames/
│   ├── P5_frame_001.png
│   ├── P5_frame_002.png
│   ├── P5_frame_003.png
│   ├── P5_frame_004.png
│   └── P5_frame_005.png
└── RESULTADOS-RUN-SPINE-GABI-001.md (este ficheiro)
```

---

## CUSTOS

| Item | Quantidade | Custo |
|------|------------|-------|
| Runway Gen-4 Image | 15 frames | $1.20 |
| InsightFace CPU | 20 medições | $0.00 |

---

*Liga IA+H · WINDI Publishing House · 13 Jun 2026*
*"Se controlas os frames, controlas a cena."*
*Blocking validado. 1ª cena de 2.*
