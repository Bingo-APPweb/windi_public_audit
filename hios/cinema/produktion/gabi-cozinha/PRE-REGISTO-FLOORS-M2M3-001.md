# PRÉ-REGISTO DE FLOORS — Re-geração Gabi-Cozinha (video-native)

```
doc_type:        measurement_protocol
estatuto:        PRÉ-REGISTO · selado ANTES dos frames · §268-compatível
refere:          METHOD-HIOS-GENERATION-001 (WINDI-METHOD-HIOS-GEN001-20260613134407-86A4FCF7)
cena:            COZINHA · Gabi & Filhote · "O Peso do Eco"
data:            2026-06-13 · Kempten, Bavaria
operador:        Human Dragon · Jober Mögele Correa
executor:        CCode (Opus 4.5) · Strato
aprovação:       Human Dragon (I9)
invariants:      I9, I11, I14, §268
```

> **Princípio:** "O número que aquele plano tem de respeitar, registado, não inventado."
> Este pré-registo define a postura de cada métrica ANTES de gerar os frames.

---

## CONTEXTO

Esta é a **re-geração** da cena Gabi-Cozinha após ERRATA-002 ter revelado que a primeira geração (5 imagens soltas) não produziu plano contínuo. A re-geração usa:

- **Video-native** (Runway Gen-4 Video, não Image)
- **Reference-locking** (âncora SEALED como image_1, cenário como image_2)
- **As 3 medições** do METHOD-HIOS-GENERATION-001 (M1, M2, M3)

---

## POSTURA DAS TRÊS MEDIÇÕES

### M1 — Identidade-Âncora

```
POSTURA:     GATE SEVERO
AGREGAÇÃO:   Mínimo (1 frame abaixo = FAIL)
FLOORS:      EXPOSIÇÃO 0.55 · GEOMETRIA 0.65
STATUS:      JÁ VALIDÁVEL (base empírica da 1ª run)
```

**Pergunta:** "Este frame é a Gabi?"
**Se FAIL:** Re-gerar obrigatório. Não prosseguir.

### M2 — Continuidade-Vizinha

```
POSTURA:     CALIBRAÇÃO (não julga nesta run)
EXPECTATIVA: M2 > M1 (frames adjacentes mais parecidos entre si)
FLOOR:       A DERIVAR desta run → vira gate na próxima
```

**Pergunta:** "Frame N coerente com N−1?"
**Se baixo ou errático:** Achado, não FAIL. Sinaliza que video-native não deu continuidade esperada.
**Propósito:** Conhecer a distribuição real para fixar floor empírico.

### M3 — Reprodutibilidade

```
POSTURA:     CALIBRAÇÃO + PROVA DE TRANSIÇÃO DE REGIME
EXPECTATIVA: ALTO (keyframes do mesmo vídeo = mesmo momento)
FLOOR:       A DERIVAR desta run
```

**Pergunta:** "Frame 005 = Frame 001 (mesma pose)?"
**Se alto:** Prova que video-native resolveu a reprodutibilidade.
**Se baixo:** Image-to-video chaining FALHOU → **PARAR e investigar**.

---

## NATUREZA DA RUN

```
┌─────────────────────────────────────────────────────────────────┐
│  TIPO:              CALIBRAÇÃO + CORRECÇÃO DE REGIME            │
│  NÃO É:             Validação para Nv3                          │
│                                                                 │
│  CONCLUSÃO PERMITIDA:                                           │
│    "Regime corrigido para video-native"                         │
│    "M1 gate: PASS/FAIL"                                         │
│    "M2/M3 calibrados: distribuição conhecida, floors derivados" │
│                                                                 │
│  CONCLUSÃO PROIBIDA:                                            │
│    "Blocking validado"                                          │
│    (M2/M3 ainda não são gates — não podem validar)              │
└─────────────────────────────────────────────────────────────────┘
```

---

## SEQUÊNCIA DE EXECUÇÃO

1. **Reference-locking**
   - Confirmar `gabi.santos.anchor.v1.png` acessível como `image_1`
   - Preparar referência de cenário (cozinha) como `image_2`

2. **Geração P1 como VÍDEO**
   - Runway Gen-4 Video (não Image)
   - Gramática descritiva ("The subject stands still...")
   - Extrair keyframes do vídeo

3. **Medição**
   - M1: Gate severo (PASS/FAIL)
   - M2: Calibração (medir distribuição N vs N−1)
   - M3: Calibração (medir 005 vs 001)

4. **Revisão Visual**
   - O olho valida o que a régua não mede
   - Caneta, chávena, saltos, cenário, montabilidade
   - **Obrigatório antes de concluir**

---

## AXIOMAS APLICÁVEIS

> *"A continuidade não se mede depois — constrói-se na geração."*

> *"O SPINE-CAST mede se É a pessoa. Não mede se É o mesmo momento."*

> *"Calibração declarada antes ≠ mover o floor depois."*

---

*Liga IA+H · WINDI Publishing House · 13 Jun 2026*
*Pré-registo selado. Frames ainda não existem.*
*§268: "WINDI sabe corrigir-se sem reescrever-se."*
