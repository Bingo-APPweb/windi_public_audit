# DECUPAGEM-CENA-04 — A Queda

```
doc_type:        decupagem
cena:            Cena 4
titulo:          A Queda
producao:        W-HIOS-FORENSIC-UNIT (O Peso do Eco — Piloto)
localizacao:     EXT. Pátio Interno do Complexo Vanguard-Nexus
tempo:           Noite (23:50)
duracao:         ~2 minutos
personagens:     Gabi (corpo imóvel)
data:            2026-06-17
autor:           CCode (Architect) + Human Dragon (I9)
metodo:          METHOD-CINEMA-CONTINUITY-001 + ACHADO-P5-ESTRUTURAL-001
```

---

## SINOPSE DA CENA

Um corpo atravessa a claraboia de vidro. Gabi está imóvel no centro dos destroços.
Silêncio absoluto. Luto. Peso. A câmara desce até ao rosto dela — não vemos uma
vítima, vemos a mãe que prometeu voltar. Olhos abertos, sem vida, mas com dignidade.
No bolso do blazer rasgado, o telemóvel vibra: "ÂNCORA — PROTOCOLO ACTIVADO".
O contador começa: 240 segundos. Gabi morreu, mas o dragão está prestes a acordar.

**Função narrativa:** O detonador. A morte que activa todo o sistema de provas.
Esta cena é LUTO com camada de MISTÉRIO — não é gore, é peso emocional.

---

## ANÁLISE DE MOVIMENTO (ACHADO-P5-ESTRUTURAL-001)

| Momento | Tipo de Movimento | Risco | Solução |
|---------|-------------------|-------|---------|
| Corpo atravessa claraboia | Queda (VFX/silhueta) | N/A | Não requer identidade |
| Gabi imóvel nos destroços | **ESTÁTICO** | ✅ ZERO | Anchor-frame perfeito |
| Close-up do rosto | **ESTÁTICO** | ✅ ZERO | Anchor-frame perfeito |
| Telemóvel vibra | Prop estático | ✅ ZERO | Insert simples |

**Esta cena é IDEAL para geração.** Corpo imóvel = sem drift de identidade.

---

## PLANOS DECUPADOS

### BLOCO A — O Impacto (3 planos)

#### P04-01 · WIDE · Claraboia Vista de Baixo
| Campo | Valor |
|-------|-------|
| **Tipo** | Wide establishing (looking up) |
| **Enquadramento** | Claraboia de vidro vista de baixo, noite, silêncio |
| **Movimento de câmara** | Fixo |
| **Duração** | 2s |
| **Som** | Silêncio absoluto... depois estilhaçar súbito |
| **Personagem** | — |
| **Identidade forense** | ❌ Não requerida |
| **Geração** | Ambiente arquitectónico — fácil |
| **Nota** | "O silêncio absoluto do dinheiro adormecido" |

#### P04-02 · WIDE · Corpo Atravessa (Silhueta)
| Campo | Valor |
|-------|-------|
| **Tipo** | Wide action |
| **Enquadramento** | Silhueta escura atravessa o vidro, estilhaços caem |
| **Movimento de câmara** | Fixo |
| **Duração** | 1.5s |
| **Som** | Estrondo do vidro, eco nas paredes de mármore |
| **Personagem** | Gabi (silhueta apenas) |
| **Identidade forense** | ❌ Não requerida (silhueta) |
| **Geração** | Silhueta + VFX vidro — médio |
| **Nota** | Identidade não visível — apenas forma humana a cair |

#### P04-03 · WIDE · Destroços Assentam
| Campo | Valor |
|-------|-------|
| **Tipo** | Wide aftermath |
| **Enquadramento** | Estilhaços de vidro a cair como diamantes negros, poeira assenta |
| **Movimento de câmara** | Fixo |
| **Duração** | 3s |
| **Som** | Vidro a cair, silêncio gradual |
| **Personagem** | — |
| **Identidade forense** | ❌ Não requerida |
| **Geração** | Ambiente + partículas — médio |
| **Nota** | Transição para o silêncio |

---

### BLOCO B — O Corpo (4 planos)

#### P04-04 · WIDE · Gabi no Centro dos Destroços
| Campo | Valor |
|-------|-------|
| **Tipo** | Wide establishing |
| **Enquadramento** | Gabi imóvel no centro do pátio, rodeada de vidro partido |
| **Movimento de câmara** | Fixo |
| **Duração** | 4s |
| **Som** | Silêncio absoluto |
| **Personagem** | Gabi (corpo inteiro, distante) |
| **Identidade forense** | 🟡 Opcional (distância dilui features) |
| **Geração** | Figura + ambiente — médio |
| **Nota** | Estabelece a composição visual — corpo pequeno no espaço vasto |

#### P04-05 · MEDIUM · Corpo de Gabi (Lateral)
| Campo | Valor |
|-------|-------|
| **Tipo** | Medium shot |
| **Enquadramento** | Gabi deitada, vista lateral, blazer rasgado visível |
| **Movimento de câmara** | Fixo |
| **Duração** | 3s |
| **Som** | Silêncio |
| **Personagem** | Gabi |
| **Identidade forense** | 🟡 Desejável (perfil) |
| **Threshold** | ≥0.65 OPERATIONAL |
| **Geração** | Joey Method — figura deitada |
| **Nota** | Mostra o blazer rasgado onde está o telemóvel |

#### P04-06 · CLOSE-UP · Rosto de Gabi (Descida de Câmara)
| Campo | Valor |
|-------|-------|
| **Tipo** | Close-up |
| **Enquadramento** | Rosto de Gabi, olhos abertos, serena dignidade |
| **Movimento de câmara** | Descida lenta (pode ser simulada em pós) |
| **Duração** | 5s |
| **Som** | Silêncio total |
| **Personagem** | Gabi |
| **Expressão** | Olhos abertos, sem vida, mas dignidade serena |
| **Identidade forense** | ✅ **ANCHOR-FRAME OBRIGATÓRIO** |
| **Threshold** | ≥0.75 FORENSE |
| **Geração** | Joey Method (gen4_image) — **CRÍTICO** |
| **Nota narrativa** | "Não vemos uma vítima. Vemos a mãe que prometeu voltar." |
| **Conexão** | Este rosto DEVE conectar visualmente com P00-06 (sorriso) |

#### P04-07 · EXTREME CLOSE-UP · Olhos de Gabi
| Campo | Valor |
|-------|-------|
| **Tipo** | Extreme close-up |
| **Enquadramento** | Apenas os olhos de Gabi, abertos, reflectindo o céu nocturno |
| **Movimento de câmara** | Fixo |
| **Duração** | 3s |
| **Som** | Silêncio... depois vibração subtil |
| **Personagem** | Gabi (olhos) |
| **Identidade forense** | 🟡 Parcial (olhos apenas) |
| **Geração** | Detalhe extremo — médio |
| **Nota** | Transição poética para o telemóvel — os olhos não vêem, mas o sistema vê |

---

### BLOCO C — O Protocolo Activa (4 planos)

#### P04-08 · INSERT · Bolso do Blazer Rasgado
| Campo | Valor |
|-------|-------|
| **Tipo** | Insert detalhe |
| **Enquadramento** | Bolso interior do blazer rasgado, telemóvel parcialmente visível |
| **Movimento de câmara** | Fixo |
| **Duração** | 2s |
| **Som** | Vibração começa |
| **Personagem** | — |
| **Identidade forense** | ❌ Não requerida |
| **Geração** | Prop estático — fácil |

#### P04-09 · INSERT · Ecrã do Telemóvel (Sinal Perdido)
| Campo | Valor |
|-------|-------|
| **Tipo** | Insert close-up |
| **Enquadramento** | Ecrã do telemóvel, texto aparece |
| **Movimento de câmara** | Fixo |
| **Duração** | 2s |
| **Som** | Vibração + beep subtil |
| **Texto no ecrã** | `SINAL BIOMÉTRICO: PERDIDO` |
| **Personagem** | — |
| **Identidade forense** | ❌ Não requerida |
| **Geração** | UI mockup — fácil |
| **Nota** | O sistema detectou a morte |

#### P04-10 · INSERT · Ecrã do Telemóvel (Protocolo Activado)
| Campo | Valor |
|-------|-------|
| **Tipo** | Insert close-up |
| **Enquadramento** | Ecrã do telemóvel, protocolo activa |
| **Movimento de câmara** | Fixo |
| **Duração** | 2s |
| **Som** | Tom de activação |
| **Texto no ecrã** | `ÂNCORA — PROTOCOLO ACTIVADO` |
| **Personagem** | — |
| **Identidade forense** | ❌ Não requerida |
| **Geração** | UI mockup — fácil |

#### P04-11 · INSERT · Ecrã do Telemóvel (Contador)
| Campo | Valor |
|-------|-------|
| **Tipo** | Insert close-up |
| **Enquadramento** | Ecrã com contador a decrementar |
| **Movimento de câmara** | Fixo |
| **Duração** | 3s |
| **Som** | Tick subtil a cada segundo |
| **Texto no ecrã** | `TRANSMISSÃO EM: 240... 239... 238...` |
| **Personagem** | — |
| **Identidade forense** | ❌ Não requerida |
| **Geração** | UI animada — médio |
| **Nota** | 4 minutos até o dragão acordar |

---

### BLOCO D — Fecho (2 planos)

#### P04-12 · WIDE · Corpo e Telemóvel
| Campo | Valor |
|-------|-------|
| **Tipo** | Wide pullback |
| **Enquadramento** | Gabi imóvel, telemóvel a brilhar no bolso, pátio escuro |
| **Movimento de câmara** | Pullback lento (pode ser estático com crop em pós) |
| **Duração** | 4s |
| **Som** | Contador continua (off), ambiente nocturno |
| **Personagem** | Gabi (corpo distante) |
| **Identidade forense** | ❌ Não requerida (distância) |
| **Geração** | Composição visual — médio |
| **Nota** | Estabelece a solidão e o peso do momento |

#### P04-13 · TITLE CARD · Frase Final
| Campo | Valor |
|-------|-------|
| **Tipo** | Title card (texto sobre negro ou sobre P04-12) |
| **Texto** | *"Gabi morreu. Mas o dragão do filho dela está prestes a acordar."* |
| **Duração** | 3s |
| **Som** | Contador continua, fade |
| **Geração** | Pós-produção |
| **Nota** | Opcional — pode ser voice-over ou texto |

---

## RESUMO DE PLANOS

| Bloco | Planos | Duração | Anchor-Frames |
|-------|--------|---------|---------------|
| A — O Impacto | 3 | 6.5s | 0 |
| B — O Corpo | 4 | 15s | **1** |
| C — O Protocolo Activa | 4 | 9s | 0 |
| D — Fecho | 2 | 7s | 0 |
| **TOTAL** | **13** | **~38s** | **1** |

**Nota:** Esta cena é mais silêncio do que acção. O tempo real será ~2 min
com respiração entre cortes e peso emocional.

---

## PLANOS CRÍTICOS (Identidade Forense Obrigatória)

| # | Plano | Enquadramento | Threshold | Prioridade |
|---|-------|---------------|-----------|------------|
| 1 | **P04-06** | Rosto de Gabi, olhos abertos, dignidade | ≥0.75 | **P1** |

**Esta cena tem APENAS 1 anchor-frame crítico** — o close-up do rosto de Gabi morta.
Este é O plano que carrega toda a identidade da cena.

**Estratégia de geração:**
- Usar Joey Method (gen4_image) para P04-06
- Gerar 5+ variantes
- Medir contra gabi.santos.anchor.v1
- Expressão: olhos abertos, serena, digna (não gore, não trauma)
- Se <0.75, re-gerar até passar

---

## CONEXÃO EMOCIONAL CENA 0 ↔ CENA 4

| Cena 0 (Vida) | Cena 4 (Morte) |
|---------------|----------------|
| P00-06: Sorriso pleno, olhos brilhantes | P04-06: Olhos abertos, sem vida, dignidade |
| Promessa: "Vou guardar esse dragão para sempre" | Realidade: O dragão está prestes a acordar |
| Luz quente, intimidade | Luz fria, solidão |

**O espectador DEVE reconhecer o mesmo rosto.** A conexão emocional depende da
identidade forense estar preservada entre estas duas cenas.

---

## GRAMÁTICA CINEMATOGRÁFICA APLICADA

| Elemento | Tratamento |
|----------|------------|
| Queda do corpo | Silhueta (P04-02) — sem identidade visível |
| Corpo no chão | Wide distante (P04-04) → Medium lateral (P04-05) → Close-up (P04-06) |
| Transição para telemóvel | Olhos (P04-07) → Bolso (P04-08) → Ecrã (P04-09) |

**Movimento de câmara simulado:** A "descida de câmara" em P04-06 pode ser:
- Gerada como plano estático
- Movimento adicionado em pós-produção (Ken Burns effect)

---

## PROPS E CONTINUIDADE

| Prop | Estado | Continuidade com |
|------|--------|------------------|
| Blazer rasgado | Rasgado no bolso interior | Cena 1 (blazer intacto) |
| Telemóvel pessoal | No bolso, ecrã activo | Cena 0 (na mesa), Cena 1 (guardado) |
| Token físico | Implícito no bolso | Cena 1 (retirado do USB) |

**Continuidade visual:** O blazer em Cena 4 DEVE ser o mesmo de Cena 0/1,
mas agora rasgado pela queda.

---

## DESIGN DE SOM

| Momento | Som |
|---------|-----|
| P04-01 | Silêncio absoluto (ambiente morto) |
| P04-02 | Estrondo súbito (vidro a partir) |
| P04-03 | Vidro a cair, eco, silêncio gradual |
| P04-04 a P04-07 | Silêncio total (luto) |
| P04-08 a P04-11 | Vibração, beeps, contador |
| P04-12 | Contador continua, ambiente |

**Tom:** LUTO com MISTÉRIO. Não é horror — é peso.

---

## UI DO TELEMÓVEL (Especificação)

```
┌────────────────────────────────┐
│                                │
│   SINAL BIOMÉTRICO: PERDIDO    │
│                                │
│   ─────────────────────────    │
│                                │
│   ÂNCORA — PROTOCOLO ACTIVADO  │
│                                │
│   TRANSMISSÃO EM:              │
│        240                     │
│                                │
└────────────────────────────────┘
```

**Estilo:** Minimalista, monocromático (branco sobre negro ou âmbar sobre negro).
Deve parecer sistema de segurança, não app consumer.

---

## ELENCO E ÂNCORAS

| Personagem | Aparição | Âncora | Estado |
|------------|----------|--------|--------|
| Gabi Santos | P04-02 a P04-12 | gabi.santos.anchor.v1 | ✅ EXTRACTED |

**Nota:** Gabi é o único personagem nesta cena. O telemóvel é "personagem" narrativo.

---

## ESTADO DA DECUPAGEM

| Campo | Valor |
|-------|-------|
| **Roteiro (R)** | ✅ v3 completo |
| **Decupagem (D)** | ✅ **13 planos decupados** |
| **Âncoras (A)** | ✅ Gabi extraída |
| **Filmada (F)** | ❌ Nenhum plano gerado |

**Cena 4 está pronta para geração.**

---

## PRÓXIMOS PASSOS

1. [ ] Gerar P04-06 (Rosto de Gabi morta) — Joey Method × 5+ variantes
2. [ ] Medir contra gabi.santos.anchor.v1, threshold ≥0.75
3. [ ] Garantir conexão visual com P00-06 (mesmo rosto, estados diferentes)
4. [ ] Gerar P04-04, P04-05 (corpo distante/médio) — menor prioridade
5. [ ] Criar UI mockups para P04-09, P04-10, P04-11
6. [ ] Gerar ambientes (pátio, vidro, destroços)

---

## NOTA SOBRE SENSIBILIDADE

Esta cena mostra uma morte, mas o tom é **LUTO**, não **GORE**.

- ❌ Não mostrar: sangue, trauma visível, expressão de dor
- ✅ Mostrar: dignidade serena, olhos abertos, paz

O prompt para P04-06 deve incluir: "serene dignity", "peaceful expression",
"eyes open but calm", "no visible trauma".

---

*Liga IA+H · Kempten · 17 Jun 2026*
*"Gabi morreu. Mas o dragão do filho dela está prestes a acordar."*

