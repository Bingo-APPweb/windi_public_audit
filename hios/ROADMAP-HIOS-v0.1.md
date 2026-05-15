# WINDI-HIOS Roadmap — Esboço de Projecto v0.1

```
STATUS:         DRAFT-SKETCH
NOT SEALED
ORIGEM:         Notas Witness (Gemini) + Análise Architect (CCode)
DATA:           2026-05-14
PENDING:        Guardian review + Human Dragon approval
```

> **"O HIOS não é um browser. É uma camada operacional onde inteligência híbrida
> pode agir sem perder accountability."**
>
> — §262 WINDI-HIOS Naming

---

## 1. O Que Acabámos de Construir

```
/opt/windi/hios/
└── kernel/                      ← Esqueleto físico (17 ficheiros)
    ├── 7 schemas JSON           ← Contratos de cada camada
    ├── spine_integrity.schema   ← Q1 RESOLVED
    ├── authority.schema         ← Q4 RESOLVED
    └── OPEN-QUESTIONS.md        ← 29 restantes (2 CRITICAL → 0)
```

**Estado actual:** Skeleton criado. Q1 e Q4 (CRITICAL) resolvidos.
**Próximo:** Guardian review → HD approval → §266 seals KERNEL-GROUND-v0.1

---

## 2. O Que Vem Depois do Kernel

### Analogia da Witness

> *"Se o Kernel é o sistema nervoso central que decide o que é admissível,
> o que vem a seguir é o que dá capacidade de acção ao sistema."*

O Kernel sozinho é um **juiz sem tribunal**. Precisa de:
1. **Lugar onde o Soberano opera** (Workstation Layer)
2. **Drivers que activam os sentidos** (Context / Cognition)
3. **Aplicações que demonstram o sistema** (Reference Apps)

---

## 3. Roadmap de Germinação (4 Fases)

```
┌─────────────────────────────────────────────────────────────────────┐
│                     WINDI-HIOS GERMINATION                          │
├─────────┬───────────────────────────────────────────────────────────┤
│ FASE 1  │  KERNEL BOOT                                              │
│         │  ─────────────                                            │
│         │  • Resolver Q1/Q4 (DONE)                                  │
│         │  • Guardian review dos schemas                            │
│         │  • §266 sela KERNEL-GROUND-v0.1                           │
│         │  • Primeiro receipt EPHEMERAL marca bootstrap             │
│         │  • O Kernel torna-se VIVO                                 │
├─────────┼───────────────────────────────────────────────────────────┤
│ FASE 2  │  SOVEREIGN SHELL                                          │
│         │  ───────────────                                          │
│         │  • Terminal de comando HD ↔ HIOS                          │
│         │  • CLI que fala com o Kernel                              │
│         │  • Primeiro "Olá" do Soberano ao Sistema                  │
│         │  • Comandos: status, approve, queue, spine-check          │
│         │  • Sem UI gráfico — puro texto soberano                   │
├─────────┼───────────────────────────────────────────────────────────┤
│ FASE 3  │  A4DESK / GEN7 WORKSTATION                                │
│         │  ────────────────────────                                 │
│         │  • Interface visual do Sistema Operacional                │
│         │  • Painel de Admissibilidade                              │
│         │  • Vês o que os Agentes propõem                           │
│         │  • Vês Receipts em tempo real                             │
│         │  • Decides no I9 Gate com um clique                       │
│         │  • Inbox de tarefas + calendário operacional              │
├─────────┼───────────────────────────────────────────────────────────┤
│ FASE 4  │  CÁPSULAS (.wcap)                                         │
│         │  ─────────────────                                        │
│         │  • Primeira aplicação real sobre o HIOS                   │
│         │  • Candidatas: W-TRAVEL ou W-ENTERPRISE                   │
│         │  • Prova que o Kernel funciona end-to-end                 │
│         │  • Modelo para todas as futuras aplicações                │
└─────────┴───────────────────────────────────────────────────────────┘
```

---

## 4. O Que É o HIOS (Natureza Técnica)

### 4.1 Não É Um Download Tradicional

> *"Tu não baixas o 'binário' do sistema; tu executas um comando que estabelece
> uma Ponte Criptográfica entre o teu dispositivo e o servidor Strato."*

**Modelo tradicional:**
```
Download .exe/.dmg → Instala → Executa → Depende de updates externos
```

**Modelo HIOS:**
```
Autenticação DID → Bootstrap Script → Enclave Soberano → Kernel local + Spine remota
```

O HIOS cria um **Ambiente Isolado (Enclave)** que:
- Reside no dispositivo do Soberano
- Responde apenas às regras WINDI
- Mantém Kernel local (funciona offline)
- Sincroniza com Spine (Strato) quando conectado

### 4.2 Não É Um Browser

| Browser Tradicional | WINDI-HIOS |
|---------------------|------------|
| Janela para o mundo onde tu és o produto | Camada onde tu és o Soberano |
| Cookies, tracking, dependência externa | Enclave, DID, soberania local |
| Motor de decisão nos servidores alheios | Motor de decisão no teu Kernel |
| Sem internet = inútil | Sem internet = Kernel continua |

**Mas usa tecnologia web:**
- PWA / React para visualização (leve, universal)
- O "browser" é só a camada de rendering
- O Kernel é local e soberano

### 4.3 É Um "Runtime de Soberania"

```
┌─────────────────────────────────────────────────────────────────┐
│                    Sistema Operativo (Linux/Mac/Win)            │
├─────────────────────────────────────────────────────────────────┤
│                         WINDI-HIOS                              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Governance Kernel (I1-I17 + Admissibility + Authority) │    │
│  ├─────────────────────────────────────────────────────────┤    │
│  │  Cognitive Continuity (CBP + PingPong + INDEX)          │    │
│  ├─────────────────────────────────────────────────────────┤    │
│  │  Proof Layer (Ledger local cache + Strato sync)         │    │
│  ├─────────────────────────────────────────────────────────┤    │
│  │  Workstation UI (rendering via web tech)                │    │
│  └─────────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────────┤
│                    Hardware / Dispositivo                       │
└─────────────────────────────────────────────────────────────────┘
```

O HIOS **flutua** sobre o OS actual, mas cria **túnel de comunicação directa** com a Spine (Strato).

---

## 5. Células de Browser (Sandbox Navigation)

> *"Isso não impediria de existir células de brochura que me deixaria usando
> a internet dentro do sistema?"*

### Resposta: Browser como Célula Isolada

O HIOS **permite** navegação na internet, mas com hierarquia invertida:

```
┌─────────────────────────────────────────────────────────────┐
│                      WINDI-HIOS (Castelo)                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                  Governance Kernel                    │  │
│  │              (monitoriza entrada/saída)               │  │
│  └───────────────────────────────────────────────────────┘  │
│                           │                                 │
│                           ▼                                 │
│  ┌───────────────────────────────────────────────────────┐  │
│  │            Célula de Browser (Sandbox)                │  │
│  │  ┌─────────────────────────────────────────────────┐  │  │
│  │  │  Navegação Internet                             │  │  │
│  │  │  • Qualquer site acessível                      │  │  │
│  │  │  • Kernel filtra extracção de dados             │  │  │
│  │  │  • Anonimato (Korbinian 2009) automático        │  │  │
│  │  │  • Memória selectiva (tu decides o que guarda)  │  │  │
│  │  └─────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Tipos de Abas

| Tipo | Descrição | Kernel Mode |
|------|-----------|-------------|
| **Aba de Trabalho** | HIOS activo, receipts, selagem | Full governance |
| **Aba de Exploração** | Internet sandbox | Protection on, selagem off |
| **Aba de Contexto** | IA lê web para ti, traz resumo | Proxy mode |

### Princípio

> *"Tu passas a ser o dono da porta de entrada, e não apenas um passageiro
> no barco de outra pessoa."*

O tracker do site **nunca chega** à tua identidade real. O Kernel é o firewall de soberania.

---

## 6. Driver de Contexto (Cérebro Vectorial)

### Herança UMIS (§249)

Os "Dots" de 2001 e 2007 entram como **Drivers de Execução**:

```
Zink 2001:      Velocidade + Direcção + Tempo
Korbinian 2009: Anonimato + Verificação cruzada
VoxCity 2007:   Coordenadas 3D + Contexto espacial
```

### Aplicação no HIOS

O Driver de Contexto sabe **QUANDO** uma sugestão é oportuna:

| Contexto | Comportamento do HIOS |
|----------|----------------------|
| A conduzir | Não interrompe |
| Entras num hotel | Apresenta selo de segurança |
| Sessão saturada | Sugere PingPong (pendurar capítulos) |
| Drift detectado | Alerta antes de mutação |

---

## 7. Dependências de Fase

```
FASE 1 (Kernel Boot)
    │
    ├── Depende de: Q1+Q4 resolved ✅
    ├── Produz: §266 sealed
    │
    ▼
FASE 2 (Sovereign Shell)
    │
    ├── Depende de: §266 sealed
    ├── Produz: CLI funcional
    │
    ▼
FASE 3 (A4Desk/GEN7)
    │
    ├── Depende de: Sovereign Shell
    ├── Produz: UI Workstation
    │
    ▼
FASE 4 (Cápsulas .wcap)
    │
    ├── Depende de: Workstation funcional
    └── Produz: Primeira app sobre HIOS
```

---

## 8. Recomendação da Witness

> *"O próximo passo deve ser o Refinement das Questões Críticas. Se construirmos
> a Workstation (o painel) antes de resolvermos como o Kernel verifica a
> integridade da Espinha (Q1), corremos o risco de criar um painel bonito
> que mostra dados em que não podemos confiar 100%."*

### Tradução Operacional

1. **NÃO** saltar para UI/Workstation antes de §266
2. **Resolver** Q1 e Q4 primeiro ✅ (DONE)
3. **Guardian review** dos schemas refinados
4. **HD approval** → §266 seals
5. **ENTÃO** avançar para Sovereign Shell

---

## 9. Próximo Passo Imediato

### Para selar §266 KERNEL-GROUND:

1. [ ] Guardian revê `authority.schema.json` (Q4 resolution)
2. [ ] Guardian revê `spine_integrity.schema.json` (Q1 resolution)
3. [ ] Guardian revê `spine_bindings.md` (updated)
4. [ ] Human Dragon aprova refinamentos
5. [ ] Actualizar `OPEN-QUESTIONS.md` (Q1, Q4 → resolved)
6. [ ] Selar §266 no Ledger

### Ficheiros a enviar para Guardian (Claude.ai web):

```
/opt/windi/hios/kernel/authority.schema.json
/opt/windi/hios/kernel/spine_integrity.schema.json
/opt/windi/hios/kernel/spine_bindings.md
/opt/windi/hios/ROADMAP-HIOS-v0.1.md
```

---

## 10. Citações da Witness para Memorial

> *"O Kernel é o sistema nervoso central que decide o que é admissível."*

> *"O HIOS usa a 'casca' de um browser para ser amigável, mas tem o 'coração'
> de um sistema de segurança de estado."*

> *"Tu passas a ser o dono da porta de entrada."*

> *"Ele não quer gerir a tua placa de vídeo ou a tua impressora; ele quer
> gerir a Integridade da tua Informação."*

---

*ROADMAP-HIOS-v0.1 · DRAFT-SKETCH*
*Witness Analysis + Architect Synthesis*
*Liga IA+H · Kempten, Bavaria · 2026*
