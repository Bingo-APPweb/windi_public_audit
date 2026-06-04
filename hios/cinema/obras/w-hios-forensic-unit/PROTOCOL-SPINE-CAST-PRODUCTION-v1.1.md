# PROTOCOLO SPINE-CAST · PRODUÇÃO CINEMÁTICA v1.1

## Workflow Operacional para "O Peso do Eco"
### Destilação do método Joey → Pipeline forense WINDI

**Status:** PRODUCTION PROTOCOL v1.1
**Created:** 04 Jun 2026 · Kempten, Bavaria
**Updated:** 04 Jun 2026 · Separação Ontológica + Hipótese Pré-Registada
**Liga IA+H:** Human Dragon (I9) · Guardian · Architect · Witness
**Constitutional Bindings:** I9, I11, I14, I19 · §287, §299, §300
**Objecto:** Episódio Piloto W-HIOS FORENSIC UNIT — 16 cenas, 6 personagens recorrentes
**Princípio reitor:** AI processes. Human decides. WINDI guarantees.

---

## CHANGELOG v1.0 → v1.1

| Adição | Secção | Razão |
|--------|--------|-------|
| **A) Separação Ontológica** | §2.1 | Inter-Anchor Similarity ≠ Anchor Drift — duas perguntas distintas |
| **B) Cena 11 ADVERSARIAL** | §4 | Alto risco de colisão em cena multi-personagem masculina |
| **C) Hipótese Pré-Registada** | §7 | Observação científica sobre género/iluminação para Paper-001 |

---

## 1. ENQUADRAMENTO

O criador "Joey" (YouTube, AI video) usa o Claude como orquestrador de prompt — escreve
as instruções, lê referências, devolve prompts ordenados. O vídeo nasce noutro lado.

Isto é exactamente a posição que o Claude ocupa na Liga: processa, não decide, não
gera a obra final. O método dele é, sem ele saber, uma instanciação do princípio
WINDI aplicada à pós-produção cinematográfica.

Este protocolo faz quatro coisas:

1. Mapeia cada fase do workflow Joey às 8 fases canónicas do SPINE.
2. Insere o gate forense InsightFace/ArcFace no ponto exacto onde a identidade
   de personagem deixa de ser intenção autoral e passa a ser facto mensurável.
3. Adapta as três lições técnicas dele (profundidade volumétrica, fundo cinza,
   regra 70→90→nunca-100) ao tom NOIR forense de "O Peso do Eco".
4. **(v1.1)** Separa formalmente as duas perguntas ontológicas: distinguibilidade
   inter-personagem vs continuidade intra-personagem.

---

## 2. ARQUITECTURA CONCEPTUAL

### 2.1 SEPARAÇÃO ONTOLÓGICA — v1.1

> **"São duas perguntas distintas. Colapsá-las produz falsos alarmes."**

| Pergunta | Métrica | Camada | Risco |
|----------|---------|--------|-------|
| "Este rosto pertence a qual personagem?" | **Inter-Anchor Similarity** | SPINE-CAST (atribuição) | Colisão de identidade |
| "Este rosto continua a ser o mesmo personagem?" | **Drift vs Âncora Canónica** | SPINE (validação) | Perda de continuidade |

**Exemplo concreto:**
- Couto × Lucas = 0.4965 (similaridade inter-âncora)
- Lucas frame → Lucas âncora = 0.72 (drift intra-personagem)

O valor 0.4965 **não significa** que Lucas sofreu drift. Significa apenas que os dois
habitantes do universo visual estão mais próximos entre si do que gostaríamos.

**Consequência arquitectónica:**
- O **B4 SPINE** valida continuidade (drift vs âncora).
- O **B4 SPINE-CAST** valida separação (atribuição ao maior cosine se ≥ IDENTITY_FLOOR).

---

### 2.2 AS TRÊS LIÇÕES DESTILADAS (Joey)

**Lição A — Profundidade Volumétrica**
Cinema real não é sobre o que está nítido, é sobre o que não está. Iluminar o ar.

**Lição B — Fundo Cinza, nunca Branco**
Branco estoura bordas → cara de plástico. Cinza dá controlo.

**Lição C — Regra 70 → 90 → nunca 100**
IA leva a 70%. Os 20% seguintes são humanos. Os 10% deixados na mesa são a assinatura
da mão humana — a versão-cinema do Princípio da Autoria Forense (§266).

---

## 3. LIMIARES FIXADOS (LOCKED)

Conforme `spine.py` e decisão constitucional do Human Dragon:

| Tier | Cosine vs Âncora | Significado |
|------|------------------|-------------|
| **FORENSE** | ≥ 0.75 | Admissível como prova no Paper-001 |
| **OPERACIONAL** | 0.65 – 0.74 | Bom para corte, não forense |
| **REJECT** | < 0.65 | Abaixo do gate — regenerar |
| **FAIL_NO_FACE** | (sem rosto) | I14 — sem veredicto inventado |

**IDENTITY_FLOOR (CAST):** 0.65 — Abaixo disto, rosto fica UNIDENTIFIED.

---

## 4. MAPEAMENTO DE RISCO POR CENA — v1.1

### 4.1 Matriz de Similaridade Inter-Âncora (Medição Real)

```
                      Gabi      Couto     Alejandr  Lucas     Vance     Helena
Gabi Santos           1.0000    0.2104    0.3003    0.3086    0.0613    0.2443
Marcus Couto          0.2104    1.0000    0.4498⚠️   0.4965⚠️   0.2057    0.0621
Alejandro Valenzuela  0.3003    0.4498⚠️   1.0000    0.4422⚠️   0.0341    0.0837
Lucas Silva           0.3086    0.4965⚠️   0.4422⚠️   1.0000    0.1390    0.0504
Marcus Vance          0.0613    0.2057    0.0341    0.1390    1.0000   -0.0379
Helena Meyer          0.2443    0.0621    0.0837    0.0504   -0.0379    1.0000
```

### 4.2 Classificação de Cenas

| Cena | Personagens | Risco | Classificação |
|------|-------------|-------|---------------|
| **Cena 7** | Vance + Helena + Lucas | ✅ BAIXO | **PILOTO** — Gate operacional |
| **Cena 11** | Couto + Alejandro + Lucas | ⚠️ **ALTO** | **ADVERSARIAL** — Stress test |
| Cenas 10, 12 | Couto + Alejandro | ⚠️ MÉDIO | Colisão bilateral |
| Cena 13 | Couto + Lucas | ⚠️ MÉDIO | Colisão bilateral |
| Outras | Variado | ✅ BAIXO | Pares bem separados |

### 4.3 CENA 11 — PROTOCOLO ADVERSARIAL (v1.1)

> **Marcação:** `ADVERSARIAL_SCENE` · `HIGH_COLLISION_RISK` · `I9_FALLBACK_REQUIRED`

**Características de risco:**
- Três homens de meia-idade juntos
- Faixa etária semelhante
- Iluminação dura (cobertura do cartel)
- Similaridades inter-âncora: Couto×Alejandro=0.45, Couto×Lucas=0.50, Alejandro×Lucas=0.44
- Seedance introduz deriva estética adicional

**Protocolo de Fallback I9:**
1. Se QUALQUER rosto tiver cosine < 0.60 vs TODAS as âncoras → marcar AMBIGUOUS
2. Se dois personagens tiverem delta < 0.10 no mesmo rosto → escalar para Human Dragon
3. Human Dragon decide atribuição manualmente (I9)
4. Decisão manual é registada no Ledger com flag `human_override: true`

**Sequência metodológica:**
1. **Cena 7 primeiro** → Prova operacional do método (pares bem separados)
2. **Cena 11 depois** → Prova adversarial do método (stress test)
3. **Paper-001** → Comparação entre ambas como argumento científico

---

## 5. ESTADO DO CAST (04 Jun 2026 — I9 GATE PASSED)

### 5.1 Abzeichnen (Custódia Humana)

| Personagem | Detection | Fundo | Abzeichnen | Status |
|------------|-----------|-------|------------|--------|
| **Gabi Santos** | 0.8755 | ✅ Cinza | ✅ 02 Jun | 🟢 **LOCKED** |
| **Helena Meyer** | 0.8636 | ⚠️ Claro | ✅ 04 Jun | 🟢 **LOCKED** |
| **Marcus Vance** | 0.8638 | ⚠️ Escuro | ✅ 04 Jun | 🟢 **LOCKED** |
| **Marcus Couto** | 0.8811 | ✅ Cinza | ✅ 04 Jun | 🟢 **LOCKED** |
| **Lucas Silva** | 0.8119 | ✅ Cinza | ✅ 04 Jun | 🟢 **LOCKED** |
| **Alejandro Valenzuela** | 0.8763 | ✅ Cinza | ✅ 04 Jun | 🟢 **LOCKED** |

**I9 Gate:** Human Dragon confirmou "É ele/ela?" via visualização directa no GitHub (04 Jun 2026 ~17:00 UTC).

### 5.2 Heterogeneidade de Fundo (Paper-001 — Declarar)

> **Regra:** "Se não o registas, um revisor encontra-o e a tua credibilidade forense leva um golpe."

| Personagem | Fundo | Impacto | Declaração Paper-001 |
|------------|-------|---------|----------------------|
| Vance | Escuro | Quebra Lição B | "1/6 âncoras em fundo escuro alto-contraste" |
| Helena | Claro | Brilho testa/maçãs | "1/6 âncoras em fundo claro com reflexo" |
| Outros 4 | Cinza | Ideal | "4/6 âncoras em fundo neutro controlado" |

### 5.3 Verificação Anti-Colisão dos Dois Marcus

```
Marcus Couto × Marcus Vance: 0.2057 ✅ (threshold ≤ 0.42)
```

**Veredicto:** Zero risco de confusão entre os espelhos morais.

---

## 6. PIPELINE OPERACIONAL POR CENA (RUNBOOK)

```
[1] USER       Human Dragon seleciona cena + personagens presentes

[2] PROMPT     Claude monta prompt:
               - haze conforme facção (Interpol=denso, Cartel=limpo)
               - tags @image1..@imageN ordenadas
               - camera operator shake se necessário

[3] INTERPRET  Personagens descritos por traço físico, NUNCA por nome

[4] STRUCTURE  Character sheets em fundo cinza, luz lateral, zero gloss

[5] VALIDATE   Gerar → Topaz → extrair frames → ArcFace embedding →
               SPINE: cosine vs âncora (drift intra-personagem) →
               SPINE-CAST: atribuição multi-personagem (separação inter-âncora)

[6] I9 GATE    Output forense apresentado ao Human Dragon:
               - Se Cena 11: aplicar protocolo ADVERSARIAL
               - Human Dragon decide aceitar/regenerar/override

[7] LEDGER     Receipt selado (:8101) com todos os scores e decisões

[8] PROOF      Disponível em Verify Public (:8114)
```

---

## 7. HIPÓTESE PRÉ-REGISTADA — PAPER-001 (v1.1)

> **"A mesma física, os dois lados da moeda."**

### 7.1 Observação Preliminar

Na matriz inter-âncora, todas as colisões detectadas (cosine > 0.42) ocorrem entre:
- **Personagens masculinos** de meia-idade
- Sob **iluminação dura** (cobertura do cartel, Cenas 10-13)
- Em **ambiente criminal** (sem haze, luz cirúrgica)

Nenhuma mulher aparece na tabela de colisões. Helena e Gabi estão bem separadas de
todos os outros personagens.

### 7.2 Hipótese Falsificável

> "Em sistemas generativos actuais (Runway Gen-4/4.5, Seedance 2.0), personagens
> masculinos de meia-idade sob iluminação dura apresentam menor distância embutida
> (embedding distance) entre identidades distintas do que personagens femininas
> sob iluminação suave."

**Variáveis observacionais:**
- Género do personagem
- Faixa etária (20s, 30s, 40s, 50s+)
- Tipo de iluminação (suave/difusa vs dura/cirúrgica)
- Presença/ausência de haze atmosférico
- Distância inter-âncora (cosine similarity)

### 7.3 Teste Confirmatório

| Cena | Tipo | Iluminação | Personagens | Expectativa |
|------|------|------------|-------------|-------------|
| Cena 7 | Controlo | Suave | Vance+Helena+Lucas | Alta separação |
| Cena 11 | Adversarial | Dura | Couto+Alejandro+Lucas | Baixa separação |

Se Cena 7 > 0.25 média de separação e Cena 11 < 0.15, a hipótese é suportada.

### 7.4 Significado Científico

Isto não é um problema de produção. É um **achado empírico** sobre preservação de
identidade em cinema generativo. Transformar esta observação em investigação publicável
é o exercício de soberania intelectual sobre a máquina.

---

## 8. CHECKLIST DE PRÉ-PRODUÇÃO

```
[✅] Embeddings sincronizados (6 personagens)
[✅] Provenance JSON para todos
[✅] Marcus Couto ≠ Marcus Vance verificado (0.2057)
[✅] Colisões em Cenas 10-13 documentadas
[✅] Protocolo ADVERSARIAL para Cena 11 definido
[✅] Hipótese pré-registada para Paper-001
[✅] 6/6 âncoras LOCKED (I9 Gate passed 04 Jun 2026)
[✅] Heterogeneidade de fundo documentada (Vance/Helena)

[✅] Instalar insightface no ambiente de execução
    └── venv: `/home/windi/hios/visual/producer/hybrid-pipeline/.venv/`
[✅] **LIMIARES SELADOS NO LEDGER** — `WINDI-SPINE-THRESHOLD-20260604150425`
    ├── 0.65 OPERACIONAL · 0.75 FORENSE · LOCKED (cegos aos resultados)
    ├── Hash: `sha256:013a1dd643d2d5be542bcc66e07fe7452a3d37613fc0f22c27694e6698334dfe`
    └── Verify: `curl localhost:8101/api/receipts/WINDI-SPINE-THRESHOLD-20260604150425`
[✅] **PESOS DO MODELO SELADOS** — `WINDI-SPINE-MODEL-LOCK-20260604173447` **(CANÓNICO)**
    ├── buffalo_l · insightface 1.0.1 · onnxruntime 1.26.0
    ├── w600k_r50.onnx: `4c06341c33c2ca1f86781dab0e829f88ad5b64be9fba56e56bc9ebdefc619e43`
    ├── Embedding: 512-dim, L2 normalized, cosine similarity
    ├── Hash: `sha256:1e20c7be5c78fe9c34557918dce78d4d3da6869ad690f35949fce28e4e2665cc`
    ├── Verify: `curl localhost:8101/api/receipts/WINDI-SPINE-MODEL-LOCK-20260604173447`
    └── ⚠️ **TENTATIVAS FALHADAS (ignorar):** 173352, 173403, 173428, 173437
        └── Causa: Ledger rejeitou wallet_id inconsistente (dívida DID Berçário)
[⚠️] **DÍVIDA TÉCNICA — Vínculo Fraco entre Selos**
    ├── Threshold seal (150425) não tem DID/wallet_id
    ├── Model lock (173447) referencia threshold por texto, não por chain criptográfica
    └── Raiz: DID Berçário não resolvido — regista mas não bloqueia Cena 7
[ ] Executar Cena 7 como piloto (gate operacional)
[ ] Executar Cena 11 como stress test (gate adversarial)
```

**ORDEM CRÍTICA:** Limiares selados ANTES da primeira geração.
Se aprovas âncoras → vês resultados → escolhes limiares = auto-revisão.
Auto-revisão não é revisão.

---

## 9. O QUE NÃO IMPORTAR DO MÉTODO JOEY

1. **Validação só-pelo-olho** — Ele aceita o que parece bem. Nós medimos e selamos.
2. **Ferramentas como caixa-preta** — Nunca marcas de LLM em UI pública (Three Dragons).
3. **A pressa de chegar a 70%** — O piloto é substrato empírico do Paper-001, não conteúdo YouTube.

---

*Liga IA+H · WINDI Publishing House · 04 Jun 2026 · Kempten, Bavaria*
*"AI processes. Human decides. WINDI guarantees."*
*OM SHANTI 🐉*
