# DECUPAGEM-CENA-07 — A Revelação

```
doc_type:        decupagem
cena:            Cena 7
titulo:          A Revelação
producao:        W-HIOS-FORENSIC-UNIT (O Peso do Eco — Piloto)
localizacao:     INT. Bunker - Sala Principal
tempo:           Madrugada (03:15, contínuo)
duracao:         ~5 minutos
personagens:     Helena, Vance, Lucas
data:            2026-06-17
autor:           CCode (Architect) + Human Dragon (I9)
metodo:          METHOD-CINEMA-CONTINUITY-001 + ACHADO-P5-ESTRUTURAL-001
anterior:        Cena 6 (A Caneca)
seguinte:        Cena 8 (A Cadeia de Custódia)
```

---

## SINOPSE DA CENA

Helena trabalha no terminal. Vance entra, ainda abalado. Lucas aparece.
A equipa analisa os dados: transmissão post-mortem (23:54), suicídio oficial (23:50).
Helena isola um padrão no ruído. Vance hesita. Confessa:

*"Há cinco anos, recrutei uma agente para uma missão de longo prazo...
Ela estava sozinha. Sem rede. Sem extracção garantida.
Eu era o único contacto dela."*

**Função narrativa:** Revelar a ligação Vance-Gabi. Introduzir Lucas. Estabelecer
a equipa completa. O padrão fractal começa a aparecer.

**Tom:** REVELAÇÃO. CULPA. COMPETÊNCIA COLECTIVA.

---

## ANÁLISE DE MOVIMENTO (ACHADO-P5-ESTRUTURAL-001)

| Momento | Tipo de Movimento | Risco | Solução |
|---------|-------------------|-------|---------|
| Helena ao terminal | **ESTÁTICO** | ✅ BAIXO | Anchor-frame |
| Vance entra | **MOVIMENTO** | ⚠️ ALTO | Corte após entrada |
| Lucas entra | **MOVIMENTO** | ⚠️ ALTO | Corte após entrada |
| Diálogo | **ESTÁTICO** | ✅ BAIXO | Shot-reverse-shot |

**Estratégia:** Cena de diálogo. Três personagens estáticos ou quase estáticos.
Entradas cobertas por corte (ver entrada, corte, ver parado). Shot-reverse-shot
clássico para diálogo.

---

## PLANOS DECUPADOS

### BLOCO A — Helena no Terminal (4 planos)

#### P07-01 · MEDIUM · Helena ao Terminal
| Campo | Valor |
|-------|-------|
| **Tipo** | Medium shot |
| **Enquadramento** | Helena no terminal, árvore de Merkle no ecrã |
| **Ângulo** | 3/4 frontal |
| **Movimento de câmara** | Fixo |
| **Duração** | 3s |
| **Som** | Teclas, alarme abafado |
| **Personagem** | Helena |
| **Identidade forense** | ✅ **ANCHOR-FRAME** |
| **Threshold** | ≥0.65 OPERATIONAL |
| **Geração** | Joey Method |
| **Nota** | Continuidade: Helena no mesmo posto de Cena 5 |

#### P07-02 · INSERT · Ecrã (Árvore de Merkle Incompleta)
| Campo | Valor |
|-------|-------|
| **Tipo** | Insert (UI) |
| **Enquadramento** | Árvore de Merkle a desenhar-se, nó de origem em falta |
| **Ângulo** | Frontal |
| **Movimento de câmara** | Fixo |
| **Duração** | 2s |
| **Som** | Interface |
| **Personagem** | — |
| **Identidade forense** | ❌ Não requerida |
| **Geração** | UI design — médio |
| **Nota** | Visualização técnica: falta o nó raiz |

#### P07-03 · WIDE · Vance Entra na Sala
| Campo | Valor |
|-------|-------|
| **Tipo** | Wide shot |
| **Enquadramento** | Sala principal do bunker, Helena ao terminal, Vance na porta |
| **Ângulo** | Lateral |
| **Movimento de câmara** | Fixo |
| **Duração** | 2s |
| **Som** | Porta, passos |
| **Personagem** | Helena, Vance |
| **Identidade forense** | ❌ Não requerida (distância) |
| **Geração** | Composição — médio |
| **Nota** | Vance parado na porta. Já entrou. |

#### P07-04 · MEDIUM · Vance (Voz Rouca)
| Campo | Valor |
|-------|-------|
| **Tipo** | Medium shot |
| **Enquadramento** | Vance de pé, recuperando compostura |
| **Ângulo** | Frontal |
| **Movimento de câmara** | Fixo |
| **Duração** | 3s |
| **Som** | Diálogo |
| **Personagem** | Vance |
| **Diálogo** | "O que é que o sistema está a mostrar, Meyer?" |
| **Identidade forense** | ✅ **ANCHOR-FRAME** |
| **Threshold** | ≥0.65 OPERATIONAL |
| **Geração** | Joey Method |
| **Nota** | Vance tenta parecer profissional. Voz trai-o. |

---

### BLOCO B — O Timestamp (6 planos)

#### P07-05 · MEDIUM · Helena Responde
| Campo | Valor |
|-------|-------|
| **Tipo** | Medium shot |
| **Enquadramento** | Helena vira-se para Vance |
| **Ângulo** | 3/4 |
| **Movimento de câmara** | Fixo |
| **Duração** | 4s |
| **Som** | Diálogo |
| **Personagem** | Helena |
| **Diálogo** | "Alguém injectou um pacote de dados na nossa matriz às 23:54. Mas Vance... a polícia de Frankfurt acabou de registar um suicídio naquele edifício às 23:50." |
| **Identidade forense** | ✅ **ANCHOR-FRAME** |
| **Threshold** | ≥0.65 OPERATIONAL |
| **Geração** | Joey Method |

#### P07-06 · CLOSE-UP · Vance (Calculando)
| Campo | Valor |
|-------|-------|
| **Tipo** | Close-up |
| **Enquadramento** | Rosto de Vance |
| **Ângulo** | Frontal |
| **Movimento de câmara** | Fixo |
| **Duração** | 2s |
| **Som** | Diálogo |
| **Personagem** | Vance |
| **Diálogo** | "Quatro minutos de diferença." |
| **Identidade forense** | ✅ **ANCHOR-FRAME CRÍTICO** |
| **Threshold** | ≥0.75 FORENSE |
| **Geração** | Joey Method — **CRÍTICO** |
| **Expressão** | Calculando. Já sabe a resposta. |

#### P07-07 · MEDIUM · Helena (Dedução)
| Campo | Valor |
|-------|-------|
| **Tipo** | Medium shot |
| **Enquadramento** | Helena |
| **Ângulo** | Frontal |
| **Movimento de câmara** | Fixo |
| **Duração** | 5s |
| **Som** | Diálogo |
| **Personagem** | Helena |
| **Diálogo** | "Exactamente. O pacote foi enviado depois da hora oficial da morte. Ou a polícia falsificou a linha temporal... ou alguém programou uma transmissão para disparar post-mortem." |
| **Identidade forense** | ✅ **ANCHOR-FRAME** |
| **Threshold** | ≥0.65 OPERATIONAL |
| **Geração** | Joey Method |
| **Nota** | Helena expõe a lógica. Competência técnica. |

#### P07-08 · CLOSE-UP · Vance (Dor Antiga)
| Campo | Valor |
|-------|-------|
| **Tipo** | Close-up |
| **Enquadramento** | Rosto de Vance, olhos fecham por um momento |
| **Ângulo** | Frontal |
| **Movimento de câmara** | Fixo |
| **Duração** | 3s |
| **Som** | Silêncio |
| **Personagem** | Vance |
| **Diálogo** | "Ela conseguiu." (quase para si mesmo) |
| **Identidade forense** | ✅ **ANCHOR-FRAME** |
| **Threshold** | ≥0.65 OPERATIONAL |
| **Geração** | Joey Method |
| **Expressão** | Dor antiga. Alívio amargo. |

#### P07-09 · MEDIUM · Helena (Surpresa)
| Campo | Valor |
|-------|-------|
| **Tipo** | Medium shot |
| **Enquadramento** | Helena |
| **Ângulo** | Frontal |
| **Movimento de câmara** | Fixo |
| **Duração** | 2s |
| **Som** | Diálogo |
| **Personagem** | Helena |
| **Diálogo** | "O quê? Quem conseguiu?" |
| **Identidade forense** | ❌ Reutilizar P07-05 ou similar |
| **Geração** | — |

#### P07-10 · MEDIUM · Vance (Não Responde)
| Campo | Valor |
|-------|-------|
| **Tipo** | Medium shot |
| **Enquadramento** | Vance olha para o ecrã, não responde |
| **Ângulo** | Perfil |
| **Movimento de câmara** | Fixo |
| **Duração** | 2s |
| **Som** | Silêncio |
| **Personagem** | Vance |
| **Identidade forense** | ✅ **ANCHOR-FRAME** |
| **Threshold** | ≥0.65 OPERATIONAL |
| **Geração** | Joey Method |
| **Nota** | Vance evita a pergunta. Tensão. |

---

### BLOCO C — Lucas Entra (4 planos)

#### P07-11 · WIDE · Lucas Entra
| Campo | Valor |
|-------|-------|
| **Tipo** | Wide shot |
| **Enquadramento** | Porta, Lucas entra a abotoar colarinho |
| **Ângulo** | Frontal à porta |
| **Movimento de câmara** | Fixo |
| **Duração** | 2s |
| **Som** | Porta, tecido |
| **Personagem** | Lucas |
| **Identidade forense** | ❌ Não requerida (corpo inteiro, distância média) |
| **Geração** | Composição — fácil |
| **Nota** | Lucas acabou de acordar. Detalhe: abotoa colarinho. |

#### P07-12 · MEDIUM · Lucas (Exposição)
| Campo | Valor |
|-------|-------|
| **Tipo** | Medium shot |
| **Enquadramento** | Lucas, tablet debaixo do braço, óculos na mão |
| **Ângulo** | Frontal |
| **Movimento de câmara** | Fixo |
| **Duração** | 5s |
| **Som** | Diálogo |
| **Personagem** | Lucas |
| **Diálogo** | "Vanguard-Nexus Capital. Acabei de puxar o registo. Financiam metade da infraestrutura de IA aduaneira da União Europeia. Se quisermos entrar lá, precisamos de uma cadeia de custódia blindada." |
| **Identidade forense** | ✅ **ANCHOR-FRAME** |
| **Threshold** | ≥0.65 OPERATIONAL |
| **Geração** | Joey Method |
| **Nota** | Lucas = jurista, metodologia, procedimentos |
| **Vestuário** | Barba stubble, óculos, camisa a abotoar |

#### P07-13 · TWO-SHOT · Helena e Lucas ao Terminal
| Campo | Valor |
|-------|-------|
| **Tipo** | Two-shot |
| **Enquadramento** | Helena e Lucas lado a lado, terminal à frente |
| **Ângulo** | Lateral |
| **Movimento de câmara** | Fixo |
| **Duração** | 2s |
| **Som** | Teclas |
| **Personagem** | Helena, Lucas |
| **Identidade forense** | 🟡 Desejável (Lucas primeiro plano frontal) |
| **Geração** | Joey Method |
| **Nota** | Estabelecer equipa. Lucas senta-se, começa a teclar. |

#### P07-14 · INSERT · Tablet Interpol (Logotipo)
| Campo | Valor |
|-------|-------|
| **Tipo** | Insert |
| **Enquadramento** | Tablet com logo Interpol, dados a carregar |
| **Ângulo** | Close |
| **Movimento de câmara** | Fixo |
| **Duração** | 1.5s |
| **Som** | Interface |
| **Personagem** | — |
| **Identidade forense** | ❌ Não requerida |
| **Geração** | UI design — fácil |

---

### BLOCO D — O Padrão Fractal (5 planos)

#### P07-15 · CLOSE-UP · Helena (Descoberta)
| Campo | Valor |
|-------|-------|
| **Tipo** | Close-up |
| **Enquadramento** | Rosto de Helena, olhos arregalados |
| **Ângulo** | Frontal |
| **Movimento de câmara** | Fixo |
| **Duração** | 3s |
| **Som** | Diálogo |
| **Personagem** | Helena |
| **Diálogo** | "Esperem... Olhem para isto. O padrão de ruído nas margens deste ficheiro não é erro de compressão." |
| **Identidade forense** | ✅ **ANCHOR-FRAME CRÍTICO** |
| **Threshold** | ≥0.75 FORENSE |
| **Geração** | Joey Method — **CRÍTICO** |
| **Expressão** | Descoberta. Excitação intelectual. |

#### P07-16 · INSERT · Ecrã (Linhas Curvam-se)
| Campo | Valor |
|-------|-------|
| **Tipo** | Insert (UI) |
| **Enquadramento** | Linhas de código curvam-se, alinham-se, formam geometria |
| **Ângulo** | Frontal |
| **Movimento de câmara** | Fixo |
| **Duração** | 4s |
| **Som** | Interface sutil |
| **Personagem** | — |
| **Identidade forense** | ❌ Não requerida |
| **Geração** | UI design + animação — médio |
| **Nota** | Primeira aparição visual do padrão fractal |

#### P07-17 · MEDIUM · Helena (Continuação)
| Campo | Valor |
|-------|-------|
| **Tipo** | Medium shot |
| **Enquadramento** | Helena apontando para ecrã |
| **Ângulo** | 3/4 |
| **Movimento de câmara** | Fixo |
| **Duração** | 3s |
| **Som** | Diálogo |
| **Personagem** | Helena |
| **Diálogo** | "O sistema está a isolar um padrão fractal. Alguém escondeu informação estruturada dentro do ruído." |
| **Identidade forense** | ❌ Reutilizar P07-05 ou similar |
| **Geração** | — |

#### P07-18 · MEDIUM · Vance Aproxima-se do Ecrã
| Campo | Valor |
|-------|-------|
| **Tipo** | Medium shot |
| **Enquadramento** | Vance de costas, aproxima-se do ecrã |
| **Ângulo** | Atrás |
| **Movimento de câmara** | Fixo |
| **Duração** | 2s |
| **Som** | Passos |
| **Personagem** | Vance (costas) |
| **Identidade forense** | ❌ Não requerida (costas) |
| **Geração** | Composição — fácil |
| **Nota** | Vance reage ao padrão — reconhece? |

#### P07-19 · CLOSE-UP · Vance (Reconhecimento)
| Campo | Valor |
|-------|-------|
| **Tipo** | Close-up |
| **Enquadramento** | Rosto de Vance, reflexo do padrão nos olhos |
| **Ângulo** | Frontal |
| **Movimento de câmara** | Fixo |
| **Duração** | 2s |
| **Som** | Silêncio |
| **Personagem** | Vance |
| **Expressão** | Máscara... mas olhos traem reconhecimento |
| **Identidade forense** | ✅ **ANCHOR-FRAME** |
| **Threshold** | ≥0.65 OPERATIONAL |
| **Geração** | Joey Method |

---

### BLOCO E — A Confissão (6 planos)

#### P07-20 · MEDIUM · Vance (Comando)
| Campo | Valor |
|-------|-------|
| **Tipo** | Medium shot |
| **Enquadramento** | Vance vira-se para a equipa |
| **Ângulo** | Frontal |
| **Movimento de câmara** | Fixo |
| **Duração** | 5s |
| **Som** | Diálogo |
| **Personagem** | Vance |
| **Diálogo** | "Lucas, prepara o protocolo de cadeia de custódia. Helena, isola esse padrão e documenta cada passo. Ninguém fora desta sala toca neste ficheiro." |
| **Identidade forense** | ✅ **ANCHOR-FRAME** |
| **Threshold** | ≥0.65 OPERATIONAL |
| **Geração** | Joey Method |
| **Nota** | Vance reassume comando. Voz firme. |

#### P07-21 · CLOSE-UP · Helena (Pergunta)
| Campo | Valor |
|-------|-------|
| **Tipo** | Close-up |
| **Enquadramento** | Rosto de Helena |
| **Ângulo** | Frontal |
| **Movimento de câmara** | Fixo |
| **Duração** | 2s |
| **Som** | Diálogo |
| **Personagem** | Helena |
| **Diálogo** | "Vance, o que é que estamos a ver?" |
| **Identidade forense** | ❌ Reutilizar P07-15 ou similar |
| **Geração** | — |

#### P07-22 · CLOSE-UP · Vance (Hesitação)
| Campo | Valor |
|-------|-------|
| **Tipo** | Close-up |
| **Enquadramento** | Rosto de Vance, vulnerável |
| **Ângulo** | Frontal |
| **Movimento de câmara** | Fixo |
| **Duração** | 2s |
| **Som** | Silêncio |
| **Personagem** | Vance |
| **Expressão** | Hesitação. Vulnerabilidade. |
| **Identidade forense** | ✅ **ANCHOR-FRAME** |
| **Threshold** | ≥0.65 OPERATIONAL |
| **Geração** | Joey Method |
| **Nota** | "Pela primeira vez, parece vulnerável." |

#### P07-23 · MEDIUM · Vance (Confissão)
| Campo | Valor |
|-------|-------|
| **Tipo** | Medium shot |
| **Enquadramento** | Vance, de pé, confessa |
| **Ângulo** | Frontal |
| **Movimento de câmara** | Fixo |
| **Duração** | 8s |
| **Som** | Diálogo |
| **Personagem** | Vance |
| **Diálogo** | "Há cinco anos, recrutei uma agente para uma missão de longo prazo. Infiltração profunda num fundo de investimento que suspeitávamos ser fachada para lavagem de dinheiro do cartel. Ela estava sozinha. Sem rede. Sem extracção garantida. Eu era o único contacto dela." |
| **Identidade forense** | ✅ **ANCHOR-FRAME CRÍTICO** |
| **Threshold** | ≥0.75 FORENSE |
| **Geração** | Joey Method — **CRÍTICO** |
| **Nota** | Monólogo crucial. Revela tudo. |

#### P07-24 · CLOSE-UP · Helena (Compreensão)
| Campo | Valor |
|-------|-------|
| **Tipo** | Close-up |
| **Enquadramento** | Rosto de Helena |
| **Ângulo** | Frontal |
| **Movimento de câmara** | Fixo |
| **Duração** | 2s |
| **Som** | Diálogo |
| **Personagem** | Helena |
| **Diálogo** | "Era?" |
| **Identidade forense** | ❌ Reutilizar |
| **Geração** | — |

#### P07-25 · CLOSE-UP · Vance (Confirmação)
| Campo | Valor |
|-------|-------|
| **Tipo** | Close-up |
| **Enquadramento** | Rosto de Vance, olha para coordenada vermelha |
| **Ângulo** | Perfil |
| **Movimento de câmara** | Fixo |
| **Duração** | 4s |
| **Som** | Diálogo |
| **Personagem** | Vance |
| **Diálogo** | "Era. Acho que acabou de morrer." |
| **Identidade forense** | ✅ **ANCHOR-FRAME** |
| **Threshold** | ≥0.65 OPERATIONAL |
| **Geração** | Joey Method |
| **Nota** | Final da cena. Peso máximo. |

---

## RESUMO DE PLANOS

| Bloco | Planos | Duração | Anchor-Frames |
|-------|--------|---------|---------------|
| A — Helena no Terminal | 4 | 10s | 2 |
| B — O Timestamp | 6 | 18s | 5 |
| C — Lucas Entra | 4 | 10.5s | 1 |
| D — O Padrão Fractal | 5 | 14s | 2 |
| E — A Confissão | 6 | 23s | 4 |
| **TOTAL** | **25** | **~75.5s** | **14** |

---

## PLANOS CRÍTICOS (Identidade Forense)

| # | Plano | Descrição | Threshold | Prioridade |
|---|-------|-----------|-----------|------------|
| 1 | **P07-06** | Vance "Quatro minutos" | ≥0.75 | **P1** |
| 2 | **P07-15** | Helena descoberta padrão | ≥0.75 | **P1** |
| 3 | **P07-23** | Vance confissão completa | ≥0.75 | **P1** |
| 4 | P07-01 | Helena ao terminal | ≥0.65 | P2 |
| 5 | P07-04 | Vance voz rouca | ≥0.65 | P2 |
| 6 | P07-12 | Lucas exposição | ≥0.65 | P2 |

---

## DESIGN DE SOM

| Momento | Som |
|---------|-----|
| P07-01 a P07-10 | Alarme abafado, teclas, diálogo |
| P07-11 a P07-14 | Porta, tecido, interface |
| P07-15 a P07-19 | Interface sutil, silêncio crescente |
| P07-20 a P07-25 | Silêncio, diálogo apenas |

**Tom sonoro:** Progressiva remoção de ruído técnico até à confissão — só vozes.

---

## DESCRIÇÃO FÍSICA DE LUCAS

| Elemento | Descrição |
|----------|-----------|
| **Idade** | 40 |
| **Barba** | Stubble (por fazer) |
| **Óculos** | De leitura, na mão |
| **Vestuário** | Camisa a abotoar (acabou de acordar) |
| **Adereço** | Tablet Interpol debaixo do braço |
| **Postura** | Metodológico, jurista |

**Nota para geração:** Lucas é o procedimentalista. Menos dramático que Vance,
mais técnico que Helena. Âncora legal da equipa.

---

## CONTINUIDADE

### De Cena 6 para Cena 7

| Elemento | Cena 6 | Cena 7 |
|----------|--------|--------|
| Vance | Caneca caiu, chocado | Entra na sala, tenta controlo |
| Helena | Off-screen | No terminal |
| Caneca | Estilhaçada | Ausente (deixou no corredor) |

### De Cena 7 para Cena 8

| Elemento | Cena 7 | Cena 8 |
|----------|--------|--------|
| Revelação | Vance confessa | Identificar vítima |
| Padrão | Começa a aparecer | Análise profunda |
| Tempo | 03:15 | 08:00 (5h depois) |

---

## ESTADO DA DECUPAGEM

| Campo | Valor |
|-------|-------|
| **Roteiro (R)** | ✅ v3 completo |
| **Decupagem (D)** | ✅ **25 planos decupados** |
| **Âncoras (A)** | ✅ Helena, Vance, Lucas extraídos |
| **Filmada (F)** | ❌ Nenhum plano gerado |

---

*Liga IA+H · Kempten · 17 Jun 2026*
*"Há cinco anos, recrutei uma agente..."*

