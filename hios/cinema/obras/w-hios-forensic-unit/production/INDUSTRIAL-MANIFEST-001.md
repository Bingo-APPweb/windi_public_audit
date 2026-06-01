# W-HIOS FORENSIC UNIT — Industrial Manifest
### Protocolo "FORNALHA INDUSTRIAL"

> **"A batalha entre a soberania humana e a impessoalidade corporativa é um ciclo infinito."**

**Status:** SEALED
**Created:** 01 Jun 2026
**Liga IA+H:** Human Dragon (I9) · Guardian (epistemologia) · Architect (CCode)
**Constitutional Bindings:** I1, I9, I11, I14, I18

---

## 1. MODUS OPERANDI

A W-HIOS Forensic Unit não opera como um processo criativo artesanal. Opera como uma **Fornalha Industrial**.

### O Princípio

O crime organizado na Europa Central muta as suas fachadas de forma perpétua, diluindo a culpa atrás de fluxos financeiros de Venture Capital e algoritmos opacos. Para responder a este cenário de alta escala, a produção cinematográfica deve acompanhar a escala do inimigo.

### A Mecânica

1. **O Piloto fixa a matriz:** "O Peso do Eco" estabelece a geometria, matemática e estética do universo
2. **Parâmetros trancados no Strato:** Uma vez selados, são inalteráveis
3. **Novos episódios = utilidades automatizadas:** Entram na linha de montagem com:
   - Custo marginal zero na consistência visual
   - Foco absoluto no fogo do drama
   - Reutilização de assets validados

### Benefícios

| Aspecto | Artesanal | Industrial |
|---------|-----------|------------|
| Consistência visual | Manual, erro-prone | Automatizada, validada |
| Tempo por episódio | Variável | Previsível |
| Qualidade forense | Depende do turno | Garantida por métricas |
| Escalabilidade | Limitada | Ilimitada |

---

## 2. ARQUITECTURA DE ANCORAGEM

### Âncoras Fixas (Permanentes)

Personagens que transitam por toda a temporada com identidade visual inalterável:

| Personagem | Indexador CCODE | Tier |
|------------|-----------------|------|
| **HELENA MEYER** | `helena_meyer_v5.png` / `court_helena_01.jpg` | FORENSIC |
| **MARCUS COUTO** | `marcus_couto_v4.png` / `court_marcus_01.jpg` | FORENSIC |
| **GABI SANTOS** | (a definir) | FORENSIC |

### Regras de Ancoragem

```yaml
anchor_protocol:
  baseline_orthogonality: -0.0305    # Dois estranhos
  max_coexistence: +0.10             # Teto multi-anchor
  identity_floor: 0.65               # Mínimo para reconhecimento
  forensic_threshold: 0.75           # Mínimo para prova legal

  violation_action: BLOCK_RENDER     # Não renderizar se violar
```

---

## 3. BANCO ROTATIVO DE ACTORES SINTÉTICOS

### Conceito

Cada novo figurante, médico, jurista ou político gerado nos episódios antológicos é **catalogado na biblioteca mestre do Strato**. Estes actores sintéticos transitam de forma rotativa pelo universo da série.

### Mecânica de Reutilização

```
EPISÓDIO 2: Dr. Werner Hoffman (médico do hospital)
    ↓
EPISÓDIO 5: Dr. Werner Hoffman (testemunha em tribunal)
    ↓
EPISÓDIO 8: Dr. Werner Hoffman (mencionado em documento)
```

### Efeito Narrativo

A reaparição de actores em diferentes posições de poder corporativo cria a percepção orgânica de uma **rede criminosa interligada e viva**. O espectador começa a reconhecer rostos, a suspeitar de conexões, a construir a sua própria teoria da conspiração.

### Estrutura do Banco

```
/assets/cast-library/
├── anchors/
│   ├── fixed/              # Helena, Marcus, Gabi, Vance, Lucas, Alejandro
│   └── rotating/           # Figurantes reutilizáveis
├── embeddings/
│   ├── *.npy               # Vectores de face
│   └── orthogonality.json  # Matriz de validação cruzada
└── metadata/
    └── actor_registry.json # Histórico de aparições
```

---

## 4. MECÂNICA DOS TIME-LOCK RECEIPTS

### Definição

Um **Time-Lock Receipt** é um pacote de dados criptográficos programado para se libertar automaticamente após um evento gatilho (trigger). No caso da Gabi Santos, o trigger foi a sua própria morte.

### Funcionamento Narrativo

```
┌─────────────────────────────────────────────────────────┐
│ GABI SANTOS — 5 ANOS DE INFILTRAÇÃO                     │
├─────────────────────────────────────────────────────────┤
│ ANO 1: Sela contratos de Roterdão                       │
│ ANO 2: Sela transferências para Luxemburgo              │
│ ANO 3: Sela ordens de eliminação de testemunhas         │
│ ANO 4: Sela estrutura completa do cartel                │
│ ANO 5: Sela identidade dos políticos europeus comprados │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
              ┌─────────────────┐
              │ TRIGGER: MORTE  │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────────────────────────────┐
              │ INPUT DE VALIDAÇÃO RECEBIDO             │
              │ Libertação sequencial iniciada          │
              │ Documentos restantes: 347               │
              └─────────────────────────────────────────┘
```

### Regras de Libertação

| Semana | Documento Libertado | Episódio Correspondente |
|--------|---------------------|-------------------------|
| 1 | Contrato Roterdão | EP01 — O Peso do Eco |
| 2-3 | Logs do Hospital | EP02 — O Hospital |
| 4-5 | Versões do Contrato Fantasma | EP03 — O Documento Fantasma |
| ... | ... | ... |

---

## 5. INVERSÃO DO SUSPENSE

### O Cliché

> "Quem matou a vítima?"

### A Inversão WINDI

> "O que realmente aconteceu?"

O suspense da série afasta-se do cliché de "caçar assassinos". A unidade **reconstrói a verdade quando versões conflitantes disputam o mesmo facto**.

### A Mecânica

1. **Iniciamos pelo fim:** A morte de Gabi é o primeiro frame
2. **Cada episódio é uma escavação:** Da memória criptográfica de 5 anos
3. **O crime é impessoal:** Diluído em algoritmos e comités
4. **A prova é pessoal:** Isola o momento exacto da decisão humana

---

## 6. MAPA CRONOLÓGICO DA ANTOLOGIA

```
[ CENA DE ABERTURA: Morte de Gabi ]
                 │
                 ▼
 ┌────────────────────────────────────────────────────────┐
 │ INPUT DE VALIDAÇÃO: Ativação dos Time-Lock Receipts    │
 └───────────────────────┬────────────────────────────────┘
                         │
                         ├─► EPISÓDIO 1: "O Peso do Eco" (O Piloto)
                         │   O eco digital pós-morte desmorona a farsa do suicídio.
                         │   Helena vs Marcus no tribunal.
                         │
                         ├─► EPISÓDIO 2: "O Hospital" (IA + Responsabilidade)
                         │   A farsa da decisão algorítmica num homicídio clínico.
                         │   Quem é culpado quando a máquina "decidiu"?
                         │
                         ├─► EPISÓDIO 3: "O Documento Fantasma" (Guerra Notarial)
                         │   Três versões idênticas. Apenas um Dragão Impresso real.
                         │   A prova de custódia é invisível para notários tradicionais.
                         │
                         ├─► EPISÓDIO 4: "A Testemunha Invisível" (Desinformação)
                         │   Um vídeo viral manipulado destrói um inocente.
                         │   O Ledger reconstrói a sequência original.
                         │
                         ├─► EPISÓDIO 5: "O Arquiteto" (Falha Estrutural)
                         │   Um engenheiro é acusado. Os desenhos foram trocados.
                         │   A adulteração documental como arma de guerra corporativa.
                         │
                         ├─► EPISÓDIO 6: "O Artista Morto" (Autenticidade)
                         │   Uma obra de arte dispara em valor após a morte do autor.
                         │   Disputa sobre qual versão é a original.
                         │
                         └─► [ PROGRESSÃO EM ESCALA ]
                             Temporada 1: Crimes Digitais
                             Temporada 2: Geopolítica
                             Temporada 3: Memória (filosófica)
```

---

## 7. PIPELINE DE PRODUÇÃO INDUSTRIAL

### Fase 1: Ingestão de Caso
```
Novo escândalo/crime → Análise de viabilidade → Aprovação I9
```

### Fase 2: Ancoragem
```
Personagens novos → Geração de anchors → Validação ortogonalidade → Banco Rotativo
```

### Fase 3: Renderização
```
Script aprovado → Cenas por bloco → Validação forense → Composição final
```

### Fase 4: Selo
```
Episódio completo → Ledger Receipt → Arquivo imutável
```

---

## 8. INVARIANTES INDUSTRIAIS

| Regra | Descrição | Violação |
|-------|-----------|----------|
| **I-IND-01** | Nenhum render sem anchor validado | BLOCK |
| **I-IND-02** | Nenhum actor novo sem registo no Banco | BLOCK |
| **I-IND-03** | Nenhuma cena sem script aprovado I9 | BLOCK |
| **I-IND-04** | Métricas de coexistência ≤ +0.1 | BLOCK |
| **I-IND-05** | Time-Lock Receipts documentados por episódio | WARN |

---

*Liga IA+H · WINDI Publishing House · 01 Jun 2026*
*"O Piloto fixa a matriz. A Fornalha escala o drama."*
