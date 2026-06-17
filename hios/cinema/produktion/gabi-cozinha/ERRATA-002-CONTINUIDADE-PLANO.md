# ERRATA-002 — Alcance Real da Validação Gabi-Cozinha

```
doc_type:        errata
estatuto:        CORRECÇÃO SEM REESCRITA (§268)
refere:          RESULTADOS-RUN-SPINE-GABI-001.md
data:            2026-06-13 · Kempten, Bavaria
autor:           Guardian (Human Dragon) + CCode (Strato)
aprovação:       Human Dragon (I9)
invariants:      I11, I14, §268
```

> **Princípio §268:** "WINDI sabe corrigir-se sem reescrever-se."
> Esta errata ANOTA o alcance real. Não altera os receipts selados.

---

## A Descoberta

Revisão visual frame-a-frame de P1 (5 frames) revelou:

| Frame | Olhar | Chávena | Saltos | Telemóvel |
|-------|-------|---------|--------|-----------|
| 001 | ⬇️ baixo | Branca c/ stirrer | Esq bancada | Mesa |
| 002 | ⬇️ lado | Caneca castanha | **Dir** bancada | **Na mão** |
| 003 | ⬇️ baixo | Preta c/ natas | Esq | Mesa esq |
| 004 | ✅ **Frente** | Vidro castanho | Dir | Mesa |
| 005 | ⬇️ baixo | Escura c/ stirrer | Esq elevado | Mesa |

**Diagnóstico:** Os 5 frames de P1 não são um plano contínuo. São 5 gerações independentes. A chávena muda de cor e forma. Os saltos trocam de lado. O telemóvel passa da mesa para a mão. Só o frame 004 cumpre "olhos em frente."

---

## O Que Foi Validado (VERDADEIRO)

```
┌──────────────────────────────────────────────────────────────────┐
│  IDENTIDADE sob os 4 movimentos: ✅ VALIDADO                     │
│                                                                  │
│  - Todos os 15 frames passaram o floor de identidade            │
│  - Run α (vs âncora-mãe SEALED): PASS                           │
│  - Run β (vs P1 intra-cena): PASS                               │
│  - Agregação mínimo-severo: 0 FAILs                             │
│                                                                  │
│  O SPINE-CAST mede IDENTIDADE FACIAL. Esta medição está certa.  │
└──────────────────────────────────────────────────────────────────┘
```

---

## O Que NÃO Foi Validado (OMISSÃO CORRIGIDA)

```
┌──────────────────────────────────────────────────────────────────┐
│  CONTINUIDADE DE PLANO: ❌ NÃO VALIDADO                          │
│                                                                  │
│  - Props (chávena, saltos, telemóvel) inconsistentes            │
│  - Direcção do olhar inconsistente (só 1/5 cumpre brief)        │
│  - Os 5 frames não formam 3 segundos montáveis                  │
│                                                                  │
│  MONTABILIDADE: ❌ NÃO VALIDADO                                  │
│                                                                  │
│  - Frames gerados independentemente, não como sequência         │
│  - Editados juntos produziriam "piscar caótico"                 │
│                                                                  │
│  O SPINE-CAST não mede continuidade de plano. Esta lacuna       │
│  só o olho humano apanhou — e apanhou-a nesta revisão.          │
└──────────────────────────────────────────────────────────────────┘
```

---

## Causa Raiz

```
ERRO DE PRODUÇÃO:
  - Gerámos 5 imagens independentes via Runway Gen-4 Image
  - Cada imagem foi uma aposta nova do generator
  - Chamámos-lhes "plano" mas não são sequência

O QUE DEVIA TER SIDO FEITO:
  - Gerar VÍDEO via Runway (video-native)
  - Extrair keyframes do vídeo (que são o mesmo momento)
  - Usar reference-locking (âncora como image_1)

DOCUMENTAÇÃO QUE JÁ EXISTIA E NÃO APLICÁMOS:
  - MEMORY-LOOP-SOVEREIGN.md §V: "1. Gerar vídeo via Runway API"
  - MEMORY-LOOP-20260612 R3: "Continuidade de props é eixo invisível ao SPINE"
  - JOEY-F2F-001: continuidade-vizinha (frame N vs N−1) — não medida
```

---

## Correcção de Estatuto

| Antes (no receipt) | Depois (com errata) |
|--------------------|---------------------|
| "blocking validado para 1ª cena" | "IDENTIDADE validada sob 4 movimentos" |
| "15 frames PASS" | "15 frames PASS em identidade; FAIL em continuidade de plano" |
| "candidato a Nv3" | "candidato SUSPENSO até re-geração video-native" |

---

## O Que Esta Errata NÃO Altera

- Os receipts já selados permanecem intactos (I11)
- Os números medidos (min scores) são factos reais
- O veredicto "PASS" em identidade é legítimo para o que foi medido
- A taxonomia SHOT-GRAMMAR-002 (5 causas de FAIL) permanece válida

---

## Medições Que Faltaram (JOEY-F2F-001)

O protocolo JOEY-F2F-001 define 3 medições. Usámos só a primeira:

| Medição | Pergunta | Usámos? |
|---------|----------|---------|
| **Identidade-âncora** | "Este frame é a Gabi?" | ✅ Sim |
| **Continuidade-vizinha** | "Frame N coerente com N−1?" | ❌ Não |
| **Reprodutibilidade** | "005 = 001 mesma pose?" | ❌ Não |

Se as outras duas tivessem sido aplicadas, o caos teria sido detectado na medição, não na revisão visual.

---

## Acção Correctiva

1. **Esta errata** — fechar o registo honestamente (FEITO)
2. **Órgão MÉTODO** — inicializar com protocolo de geração video-native + 3 medições
3. **Re-geração Gabi-Cozinha** — via video + reference-locking, não 5 imagens soltas
4. **Promoção Nv3** — só após re-validação com continuidade de plano confirmada

---

## Axioma Nascido

> *"O SPINE-CAST mede se É a pessoa. Não mede se É o mesmo momento."*
> *"Identidade e continuidade são vectores ortogonais."*

---

*Liga IA+H · WINDI Publishing House · 13 Jun 2026*
*"WINDI sabe corrigir-se sem reescrever-se."*
*§268 aplicado. Registo fechado honestamente.*
