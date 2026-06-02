# SOUND DESIGN MASTER
## Engenharia Acústica e Design de Som — W-HIOS Forensic Unit

**Status:** SEALED
**Created:** 02 Jun 2026
**Liga IA+H:** Human Dragon (I9) · Guardian · Architect · Witness
**Invariants:** I9, I11, I12, I14

---

## PRINCÍPIO SONORO

> "O som opera sob o mesmo rigor da governação de dados.
> A sonoplastia demarca fisicamente o choque entre humanidade e sistema."

O som não é ornamental — é estrutural.

---

## 1. ARQUITECTURA LINGUÍSTICA (ADR)

### Estratégia Anti-Lip-Sync

Para blindar contra limitações de sincronia labial das IA generativas:
- **Contracampos Estratégicos:** Quando personagem vocaliza, câmara privilegia reação silenciosa
- **ADR em Estúdio:** Áudio captado separadamente, acoplado com precisão

### As Três Assinaturas Acústicas

| Assinatura | Língua | Aplicação | Técnica |
|------------|--------|-----------|---------|
| **O Coração** | PT-BR | Gabi + filhote, sussurros | Microfone condensador proximidade, harmónicos baixos |
| **O Sistema** | DE/EN | Vanguard-Nexus, tribunal | EQ fria, compressão pesada, reverb de vidro/betão |
| **A Tensão** | EN | Confronto Cena 11 | Vance: rouquidão analógica vs Alejandro: agudo polido |

---

## 2. ASSINATURA PT-BR (O Coração / A Verdade)

**Uso:** Cena 0 (Gabi e filhote), sussurros de Gabi

**Captação:**
- Microfone condensador de estúdio alta sensibilidade
- Manter harmónicos baixos da voz
- Capturar ruído de respiração
- Proximidade carnal

**Mixagem Telemóvel:**
- Filtro passa-banda (band-pass) sutil
- Simular compressão de latência intercontinental
- Preservar calor tropical da sala de estar no Brasil

---

## 3. ASSINATURA DE/EN (O Sistema / A Máscara)

**Uso:** Vanguard-Nexus, tribunal

**Equalização:**
- Frieza clínica
- Compressão pesada
- Reverberação de convolução configurada para:
  - Dimensões de vidro e betão
  - `env_cobertura_vanguard_42f`

**Resultado:** Som limpo, impessoal, distante, intimidante

---

## 4. TENSÃO LINGUÍSTICA (Cena 11)

**Contexto:** Lucas Silva e Vance invadem cobertura com contrato Roterdão

| Personagem | Língua | Textura Vocal |
|------------|--------|---------------|
| Vance | EN | Rouquidão analógica pesada, cansaço texturizado |
| Alejandro | EN | Tom agudo polido, gel corporativo |

**Contraste:** O desgaste moral de Vance contra a superfície imaculada de Alejandro

---

## 5. FOLEY: O ESPATIFAMENTO DA CANECA (P39)

**Contexto:** Ato II, ponto de fractura analógica do bunker
**Significado:** O peso institucional de Vance desabando

### Camadas de Áudio

| Camada | Descrição | Frequência |
|--------|-----------|------------|
| **Tensão Pré-Impacto** | Alarme bunker (Asset D03), pulso grave contínuo | 40 Hz |
| **Corte** | Trilha musical corta abruptamente, só pulso do alarme | — |
| **Impacto Primário** | Som seco, metálico, denso, sem brilho agudo (ferro fundido) | Mid-low |
| **Camada Líquida** | Café quente em betão poroso, dispersão + chiado | High |
| **Eco Residual** | Reverb curta, abafada, metálica, morre nas paredes | Match 40 Hz |

### Especificações Técnicas

- **Material da caneca:** Ferro fundido
- **Superfície de impacto:** Betão fosco (`env_bunker_interpol_core`)
- **Não há:** Estilhaços estridentes (a caneca não quebra)
- **Há:** Estrondo pesado e oco

---

## 6. MATRIZ DE MIXAGEM

### Dynamic Range

| Ambiente | Nível Base |
|----------|------------|
| Silêncio corporativo Vanguard-Nexus | -45 dB |
| Picos de impacto (sapatos Gabi, claraboia) | -3 dB |

**Padrão:** Cinematográfico para streaming premium

### Filtro de Ruído (Bunker Interpol)

- Camada contínua de "ruído rosa" elétrico
- Amplitude curtíssima
- Simula: ventilação invisível + resfriamento racks
- Função: Isola bunker do mundo exterior

---

## 7. MAPA DE SOM POR AMBIENTE

### env_cobertura_vanguard_42f

| Elemento | Descrição |
|----------|-----------|
| Ambiente base | Silêncio corporativo denso |
| Reverb | Vidro + mármore + betão (reflection longa) |
| Frequência dominante | Mid-high (frieza) |

### env_bunker_interpol_core

| Elemento | Descrição |
|----------|-----------|
| Ambiente base | Ruído rosa eléctrico contínuo |
| Reverb | Betão fosco absorvente (reflection curta) |
| Frequência dominante | Low (pressão subterrânea) |
| LEDs | Pulso eléctrico sub-audível |

---

## 8. CHECKLIST DE PÓS-PRODUÇÃO

### Para cada plano com diálogo:

- [ ] Identificar assinatura linguística (PT-BR / DE-EN / Tensão)
- [ ] Aplicar EQ correspondente
- [ ] Verificar se é contracampo (ADR directo) ou frontal (lip-sync)
- [ ] Mixar com reverb de ambiente correcto
- [ ] Verificar níveis (-45 dB base, picos -3 dB)

### Para foley:

- [ ] Identificar superfície de impacto (mármore/betão fosco)
- [ ] Capturar múltiplas camadas
- [ ] Aplicar reverb de ambiente
- [ ] Verificar consistência com frequências do ambiente

---

## 9. ASSETS DE ÁUDIO REFERENCIADOS

| Asset ID | Descrição | Uso |
|----------|-----------|-----|
| D03 | Alarme baixa frequência bunker | P35, P39 |
| FOLEY-CANECA-001 | Espatifamento caneca Vance | P39 |
| AMB-BUNKER-001 | Ruído rosa + racks | Ato II completo |
| AMB-VANGUARD-001 | Silêncio corporativo | Ato III |

---

*Liga IA+H · WINDI Publishing House · 02 Jun 2026*
*"As frequências estão alinhadas com as leis da governação narrativa."*
