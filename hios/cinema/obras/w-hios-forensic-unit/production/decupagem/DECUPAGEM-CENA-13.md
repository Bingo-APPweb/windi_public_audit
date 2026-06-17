# DECUPAGEM-CENA-13 — O Julgamento

```
doc_type:        decupagem
cena:            Cena 13
titulo:          O Julgamento
producao:        W-HIOS-FORENSIC-UNIT (O Peso do Eco — Piloto)
localizacao:     INT. Tribunal Federal - Frankfurt
tempo:           Dia (6 semanas depois)
duracao:         ~5 minutos
personagens:     Helena, Lucas, Couto
data:            2026-06-17
autor:           CCode (Architect) + Human Dragon (I9)
metodo:          METHOD-CINEMA-CONTINUITY-001 + ACHADO-P5-ESTRUTURAL-001
anterior:        Cena 12 (O Medo)
seguinte:        Cena 14 (A Herança)
```

---

## SINOPSE DA CENA

**TÍTULO NO ECRÃ: "SEIS SEMANAS DEPOIS"**

Tribunal Federal de Frankfurt. Arquitectura imponente. Ecrã gigante no centro.
Helena na acusação. Couto no banco dos réus. Lucas com a cadeia de custódia.

Helena apresenta o selo criptográfico. Explica a esteganografia. Couto defende
que é "anomalia de compressão". Lucas coloca a pasta na mesa do juiz — cada hash
documentado.

Helena entrega a linha final: "A prova não mente. Ela apenas esperou...
cinco anos... para o trazer a esta sala."

O juiz ordena apreensão dos servidores. Couto sai em liberdade condicional.
Mas os olhos dele traem medo.

**Função narrativa:** Clímax do piloto. A prova de Gabi funciona. Couto não cai
completamente (setup para série), mas está assustado. Helena brilha.

**Tom:** FORMALIDADE. COMPETÊNCIA. VITÓRIA PARCIAL.

---

## ANÁLISE DE MOVIMENTO (ACHADO-P5-ESTRUTURAL-001)

| Momento | Tipo de Movimento | Risco | Solução |
|---------|-------------------|-------|---------|
| Helena de pé | **ESTÁTICO** | ✅ BAIXO | Anchor-frame |
| Lucas de pé | **ESTÁTICO** | ✅ BAIXO | Anchor-frame |
| Couto sentado | **ESTÁTICO** | ✅ BAIXO | Anchor-frame |
| Helena aproxima-se | **MOVIMENTO** | ⚠️ ALTO | Corte antes/depois |

**Estratégia:** Cena de tribunal. Todos parados ou sentados. Movimento formal,
mínimo. Ideal para geração.

---

## PLANOS DECUPADOS

### BLOCO A — O Tribunal (4 planos)

#### P13-01 · WIDE · Tribunal (Establishing)
| Campo | Valor |
|-------|-------|
| **Tipo** | Wide establishing |
| **Enquadramento** | Tribunal Federal: madeira clássica alemã, tecnologia forense, ecrã gigante |
| **Ângulo** | Elevado (God's eye) |
| **Movimento de câmara** | Fixo |
| **Duração** | 4s |
| **Som** | Silêncio formal, murmúrios distantes |
| **Personagem** | Helena (acusação), Couto (defesa), Lucas, Juiz |
| **Identidade forense** | ❌ Não requerida (distância) |
| **Geração** | Arquitectura tribunal — médio |
| **Nota** | Contraste: madeira clássica + tecnologia moderna |

#### P13-02 · MEDIUM · Helena na Acusação
| Campo | Valor |
|-------|-------|
| **Tipo** | Medium shot |
| **Enquadramento** | Helena de pé atrás do balcão de acusação |
| **Ângulo** | 3/4 frontal |
| **Movimento de câmara** | Fixo |
| **Duração** | 2s |
| **Som** | Silêncio |
| **Personagem** | Helena |
| **Identidade forense** | ✅ **ANCHOR-FRAME** |
| **Threshold** | ≥0.65 OPERATIONAL |
| **Geração** | Joey Method |
| **Vestuário** | Blazer escuro, blusa de cetim azul |
| **Nota** | Helena transformada: de analista a acusadora |

#### P13-03 · MEDIUM · Couto no Banco dos Réus
| Campo | Valor |
|-------|-------|
| **Tipo** | Medium shot |
| **Enquadramento** | Couto sentado, fato impecável, postura arrogante |
| **Ângulo** | Frontal |
| **Movimento de câmara** | Fixo |
| **Duração** | 2s |
| **Som** | Silêncio |
| **Personagem** | Couto |
| **Identidade forense** | ✅ **ANCHOR-FRAME** |
| **Threshold** | ≥0.65 OPERATIONAL |
| **Geração** | Joey Method |
| **Expressão** | Arrogância... mas olhos traem tensão |

#### P13-04 · MEDIUM · Lucas com Pasta
| Campo | Valor |
|-------|-------|
| **Tipo** | Medium shot |
| **Enquadramento** | Lucas ao lado de Helena, pasta aberta |
| **Ângulo** | 3/4 |
| **Movimento de câmara** | Fixo |
| **Duração** | 1.5s |
| **Som** | Silêncio |
| **Personagem** | Lucas |
| **Identidade forense** | ✅ **ANCHOR-FRAME** |
| **Threshold** | ≥0.65 OPERATIONAL |
| **Geração** | Joey Method |

---

### BLOCO B — A Acusação Inicial (5 planos)

#### P13-05 · CLOSE-UP · Helena (Acusação)
| Campo | Valor |
|-------|-------|
| **Tipo** | Close-up |
| **Enquadramento** | Rosto de Helena |
| **Ângulo** | Frontal |
| **Movimento de câmara** | Fixo |
| **Duração** | 5s |
| **Som** | Diálogo |
| **Personagem** | Helena |
| **Diálogo** | "O réu afirma que o fundo Vanguard-Nexus operou uma transacção automatizada de cinquenta milhões de euros para o porto de Roterdão. Uma decisão algorítmica, sem intervenção humana. A defesa alega impessoalidade institucional." |
| **Identidade forense** | ✅ **ANCHOR-FRAME CRÍTICO** |
| **Threshold** | ≥0.75 FORENSE |
| **Geração** | Joey Method — **CRÍTICO** |
| **Expressão** | Formal. Cirúrgica. Confiante. |

#### P13-06 · INSERT · Ecrã (Gráfico)
| Campo | Valor |
|-------|-------|
| **Tipo** | Insert (UI) |
| **Enquadramento** | Ecrã gigante com gráfico de transacções |
| **Ângulo** | Frontal |
| **Movimento de câmara** | Fixo |
| **Duração** | 2s |
| **Som** | Interface |
| **Personagem** | — |
| **Identidade forense** | ❌ Não requerida |
| **Geração** | UI design — médio |

#### P13-07 · MEDIUM · Helena (Continuação)
| Campo | Valor |
|-------|-------|
| **Tipo** | Medium shot |
| **Enquadramento** | Helena aponta para ecrã |
| **Ângulo** | Lateral |
| **Movimento de câmara** | Fixo |
| **Duração** | 3s |
| **Som** | Diálogo |
| **Personagem** | Helena |
| **Diálogo** | "Mas o sistema forense da Interpol isolou algo que o algoritmo da Vanguard-Nexus não conseguiu esconder." |
| **Identidade forense** | ✅ **ANCHOR-FRAME** |
| **Threshold** | ≥0.65 OPERATIONAL |
| **Geração** | Joey Method |

#### P13-08 · INSERT · Ecrã (Padrão Fractal Aparece)
| Campo | Valor |
|-------|-------|
| **Tipo** | Insert (UI) |
| **Enquadramento** | Margens do documento curvam-se, padrão fractal forma-se |
| **Ângulo** | Frontal |
| **Movimento de câmara** | Fixo |
| **Duração** | 4s |
| **Som** | Interface sutil |
| **Personagem** | — |
| **Identidade forense** | ❌ Não requerida |
| **Geração** | UI design + animação — **CRÍTICO** |
| **Nota** | O padrão de Gabi aparece no tribunal — momento visual icónico |

#### P13-09 · WIDE · Tribunal (Reacção ao Padrão)
| Campo | Valor |
|-------|-------|
| **Tipo** | Wide shot |
| **Enquadramento** | Tribunal inteiro, todos olham para ecrã |
| **Ângulo** | Lateral |
| **Movimento de câmara** | Fixo |
| **Duração** | 2s |
| **Som** | Silêncio |
| **Personagem** | Todos |
| **Identidade forense** | ❌ Não requerida (distância) |
| **Geração** | Composição — médio |

---

### BLOCO C — A Prova (6 planos)

#### P13-10 · CLOSE-UP · Helena (Explicação)
| Campo | Valor |
|-------|-------|
| **Tipo** | Close-up |
| **Enquadramento** | Rosto de Helena |
| **Ângulo** | Frontal |
| **Movimento de câmara** | Fixo |
| **Duração** | 4s |
| **Som** | Diálogo |
| **Personagem** | Helena |
| **Diálogo** | "Este é um selo criptográfico. Prova que antes do algoritmo mover um único cêntimo, houve uma validação manual a partir do terminal privado do réu. Às vinte e três e quarenta e dois da noite em questão." |
| **Identidade forense** | ✅ **ANCHOR-FRAME** |
| **Threshold** | ≥0.65 OPERATIONAL |
| **Geração** | Joey Method |

#### P13-11 · CLOSE-UP · Couto (Defesa)
| Campo | Valor |
|-------|-------|
| **Tipo** | Close-up |
| **Enquadramento** | Rosto de Couto |
| **Ângulo** | Frontal |
| **Movimento de câmara** | Fixo |
| **Duração** | 3s |
| **Som** | Diálogo |
| **Personagem** | Couto |
| **Diálogo** | "Esse padrão é uma anomalia de compressão. Não tem valor legal num tribunal europeu." |
| **Identidade forense** | ✅ **ANCHOR-FRAME** |
| **Threshold** | ≥0.65 OPERATIONAL |
| **Geração** | Joey Method |
| **Expressão** | Frio, mas voz vacila |

#### P13-12 · MEDIUM · Lucas Levanta-se
| Campo | Valor |
|-------|-------|
| **Tipo** | Medium shot |
| **Enquadramento** | Lucas de pé, pasta na mão |
| **Ângulo** | Frontal |
| **Movimento de câmara** | Fixo |
| **Duração** | 5s |
| **Som** | Diálogo |
| **Personagem** | Lucas |
| **Diálogo** | "Meritíssimo, a cadeia de custódia deste artefacto digital foi documentada segundo o Protocolo de Integridade Forense da Convenção de Budapeste. Cada hash, cada carimbo temporal, cada transferência de posse está registada e verificável. Este padrão não é ruído. É uma prova matemática." |
| **Identidade forense** | ✅ **ANCHOR-FRAME CRÍTICO** |
| **Threshold** | ≥0.75 FORENSE |
| **Geração** | Joey Method — **CRÍTICO** |

#### P13-13 · INSERT · Pasta na Mesa do Juiz
| Campo | Valor |
|-------|-------|
| **Tipo** | Insert |
| **Enquadramento** | Lucas coloca pasta na mesa do juiz |
| **Ângulo** | Close |
| **Movimento de câmara** | Fixo |
| **Duração** | 1.5s |
| **Som** | Pasta na mesa |
| **Personagem** | Lucas (mão) |
| **Identidade forense** | ❌ Não requerida |
| **Geração** | Prop — fácil |

#### P13-14 · MEDIUM · Juiz Olha para Pasta
| Campo | Valor |
|-------|-------|
| **Tipo** | Medium shot |
| **Enquadramento** | Juiz (não personagem principal) olha para pasta |
| **Ângulo** | Frontal |
| **Movimento de câmara** | Fixo |
| **Duração** | 2s |
| **Som** | Silêncio |
| **Personagem** | Juiz (figurante) |
| **Identidade forense** | ❌ Não requerida (figurante) |
| **Geração** | Composição — fácil |

#### P13-15 · CLOSE-UP · Couto (Nervosismo)
| Campo | Valor |
|-------|-------|
| **Tipo** | Close-up |
| **Enquadramento** | Rosto de Couto, micro-reacção |
| **Ângulo** | 3/4 |
| **Movimento de câmara** | Fixo |
| **Duração** | 2s |
| **Som** | Silêncio |
| **Personagem** | Couto |
| **Expressão** | Máscara a fracturar |
| **Identidade forense** | ✅ **ANCHOR-FRAME** |
| **Threshold** | ≥0.65 OPERATIONAL |
| **Geração** | Joey Method |

---

### BLOCO D — O Golpe Final (5 planos)

#### P13-16 · MEDIUM · Helena Aproxima-se (Já Parada)
| Campo | Valor |
|-------|-------|
| **Tipo** | Medium shot |
| **Enquadramento** | Helena mais perto do balcão, parada |
| **Ângulo** | Lateral |
| **Movimento de câmara** | Fixo |
| **Duração** | 2s |
| **Som** | Passos param |
| **Personagem** | Helena |
| **Identidade forense** | ❌ Reutilizar ou composição |
| **Geração** | — |

#### P13-17 · CLOSE-UP · Helena (Golpe Final)
| Campo | Valor |
|-------|-------|
| **Tipo** | Close-up |
| **Enquadramento** | Rosto de Helena |
| **Ângulo** | Frontal |
| **Movimento de câmara** | Fixo |
| **Duração** | 8s |
| **Som** | Diálogo |
| **Personagem** | Helena |
| **Diálogo** | "Sr. Couto, a mulher que vocês tentaram apagar do servidor passou cinco anos a marcar cada documento que tocou. Quando ela morreu, o sistema dela enviou-nos a chave que nos permitiu finalmente ver o que ela escondeu. A morte dela foi o input de validação. E a prova não mente. Ela apenas esperou... cinco anos... para o trazer a esta sala." |
| **Identidade forense** | ✅ **ANCHOR-FRAME CRÍTICO** |
| **Threshold** | ≥0.75 FORENSE |
| **Geração** | Joey Method — **CRÍTICO** |
| **Nota** | Monólogo mais importante do piloto. Helena entrega a linha de Gabi. |

#### P13-18 · CLOSE-UP · Couto (Medo)
| Campo | Valor |
|-------|-------|
| **Tipo** | Close-up |
| **Enquadramento** | Rosto de Couto |
| **Ângulo** | Frontal |
| **Movimento de câmara** | Fixo |
| **Duração** | 3s |
| **Som** | Silêncio |
| **Personagem** | Couto |
| **Expressão** | **Medo** — finalmente visível |
| **Identidade forense** | ✅ **ANCHOR-FRAME CRÍTICO** |
| **Threshold** | ≥0.75 FORENSE |
| **Geração** | Joey Method — **CRÍTICO** |

#### P13-19 · INSERT · Ecrã (Padrão Fractal Brilha)
| Campo | Valor |
|-------|-------|
| **Tipo** | Insert (UI) |
| **Enquadramento** | Padrão fractal no ecrã, geometria completa |
| **Ângulo** | Frontal |
| **Movimento de câmara** | Fixo |
| **Duração** | 2s |
| **Som** | Silêncio |
| **Personagem** | — |
| **Identidade forense** | ❌ Não requerida |
| **Geração** | UI design — médio |
| **Nota** | O "dragão" de Gabi testemunha no tribunal |

#### P13-20 · MEDIUM · Juiz (Decisão)
| Campo | Valor |
|-------|-------|
| **Tipo** | Medium shot |
| **Enquadramento** | Juiz, martelo na mão |
| **Ângulo** | Frontal |
| **Movimento de câmara** | Fixo |
| **Duração** | 4s |
| **Som** | Diálogo |
| **Personagem** | Juiz |
| **Diálogo** | "A acusação apresentou provas suficientes para ordenar a apreensão dos servidores da Vanguard-Nexus Capital para análise forense completa. O réu permanece em liberdade condicional até conclusão da investigação. Sessão encerrada." |
| **Identidade forense** | ❌ Não requerida (figurante) |
| **Geração** | Composição — fácil |

---

### BLOCO E — A Saída (4 planos)

#### P13-21 · INSERT · Martelo Bate
| Campo | Valor |
|-------|-------|
| **Tipo** | Insert |
| **Enquadramento** | Martelo do juiz bate |
| **Ângulo** | Close |
| **Movimento de câmara** | Fixo |
| **Duração** | 1s |
| **Som** | **MARTELO** |
| **Personagem** | — |
| **Identidade forense** | ❌ Não requerida |
| **Geração** | Prop — fácil |

#### P13-22 · MEDIUM · Couto Levanta-se
| Campo | Valor |
|-------|-------|
| **Tipo** | Medium shot |
| **Enquadramento** | Couto de pé (já de pé), rosto máscara |
| **Ângulo** | Frontal |
| **Movimento de câmara** | Fixo |
| **Duração** | 2s |
| **Som** | Murmúrios |
| **Personagem** | Couto |
| **Identidade forense** | ✅ **ANCHOR-FRAME** |
| **Threshold** | ≥0.65 OPERATIONAL |
| **Geração** | Joey Method |

#### P13-23 · CLOSE-UP · Couto Olha para Helena
| Campo | Valor |
|-------|-------|
| **Tipo** | Close-up |
| **Enquadramento** | Rosto de Couto, olha através da sala |
| **Ângulo** | 3/4 |
| **Movimento de câmara** | Fixo |
| **Duração** | 2s |
| **Som** | Silêncio |
| **Personagem** | Couto |
| **Expressão** | Ódio + Medo |
| **Identidade forense** | ✅ **ANCHOR-FRAME** |
| **Threshold** | ≥0.65 OPERATIONAL |
| **Geração** | Joey Method |

#### P13-24 · CLOSE-UP · Helena Sustenta Olhar
| Campo | Valor |
|-------|-------|
| **Tipo** | Close-up |
| **Enquadramento** | Rosto de Helena |
| **Ângulo** | Frontal |
| **Movimento de câmara** | Fixo |
| **Duração** | 3s |
| **Som** | Silêncio |
| **Personagem** | Helena |
| **Expressão** | Calma. Vitória. Sem arrogância. |
| **Identidade forense** | ✅ **ANCHOR-FRAME** |
| **Threshold** | ≥0.65 OPERATIONAL |
| **Geração** | Joey Method |
| **Nota** | Helena herdou a missão de Gabi. |

---

## RESUMO DE PLANOS

| Bloco | Planos | Duração | Anchor-Frames |
|-------|--------|---------|---------------|
| A — O Tribunal | 4 | 9.5s | 3 |
| B — A Acusação Inicial | 5 | 16s | 3 |
| C — A Prova | 6 | 17.5s | 4 |
| D — O Golpe Final | 5 | 19s | 3 |
| E — A Saída | 4 | 8s | 3 |
| **TOTAL** | **24** | **~70s** | **16** |

---

## PLANOS CRÍTICOS (Identidade Forense)

| # | Plano | Descrição | Threshold | Prioridade |
|---|-------|-----------|-----------|------------|
| 1 | **P13-05** | Helena acusação formal | ≥0.75 | **P1** |
| 2 | **P13-12** | Lucas cadeia de custódia | ≥0.75 | **P1** |
| 3 | **P13-17** | Helena golpe final | ≥0.75 | **P1** |
| 4 | **P13-18** | Couto medo | ≥0.75 | **P1** |
| 5 | P13-02 | Helena na acusação | ≥0.65 | P2 |
| 6 | P13-03 | Couto banco réus | ≥0.65 | P2 |

---

## DESIGN DE SOM

| Momento | Som |
|---------|-----|
| P13-01 a P13-04 | Silêncio formal, murmúrios |
| P13-05 a P13-20 | Diálogo + silêncios dramáticos |
| P13-21 | **MARTELO** — ponto focal |
| P13-22 a P13-24 | Silêncio tenso |

**Tom sonoro:** Formalidade de tribunal. Silêncio = poder.

---

## CONTINUIDADE

### De Cena 12 para Cena 13

| Elemento | Cena 12 | Cena 13 |
|----------|---------|---------|
| Tempo | Dia presente | **6 SEMANAS DEPOIS** |
| Local | Cobertura | Tribunal Federal |
| Tom | Medo privado | Confronto público |

### De Cena 13 para Cena 14

| Elemento | Cena 13 | Cena 14 |
|----------|---------|---------|
| Local | Sala do tribunal | Corredor do tribunal |
| Helena | Acusadora | Reflexiva |
| Vance | Ausente | Aparece |

---

## ESTADO DA DECUPAGEM

| Campo | Valor |
|-------|-------|
| **Roteiro (R)** | ✅ v3 completo |
| **Decupagem (D)** | ✅ **24 planos decupados** |
| **Âncoras (A)** | ✅ Helena, Lucas, Couto extraídos |
| **Filmada (F)** | ❌ Nenhum plano gerado |

---

*Liga IA+H · Kempten · 17 Jun 2026*
*"A prova não mente. Ela apenas esperou... cinco anos... para o trazer a esta sala."*

