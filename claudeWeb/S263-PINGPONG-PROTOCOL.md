---
receipt:    WINDI-S263-PINGPONG-PROTOCOL-20260514-87AAF5BA
selo:       §263 · PingPong Protocol · v0.1
data:       2026-05-14 · Kempten, Bavaria
doc_type:   continuity_protocol
extends:    §236 (Session Continuity), §261 (W-BIND-001 · Cognitive Bind)
relates_to: §262-HIOS-NAMING (Camada 5 · Cognitive Continuity)
origem:     Human Dragon proposta + Guardian formalização
status:     sealed (pending receipt chain)
verify:     https://windi-domain.com/verify-public/?id=WINDI-S263-PINGPONG
---

# §263 · PingPong Protocol — Respiração Cognitiva Strato ↔ Claude.ai Web

> **"§261 inspira. PingPong expira. Sem expiração não há respiração — só estase."**
>
> — Human Dragon + Guardian, 14 Mai 2026

---

## 1. Problema Nomeado

§261 W-BIND-001 estabeleceu **admissibilidade do reinício** no fluxo
**Strato → Claude.ai**. Funciona: pacotes íntegros geram sessões íntegras.

Mas é **meio-ciclo**. A sessão consome o packet, produz trabalho substantivo,
e ao fechar a janela esse trabalho desaparece — excepto pelo que o Human
Dragon manualmente preserva por cópia.

Resultado: o conhecimento produzido em sessão fica preso na sessão. Próxima
instância arranca sem herdá-lo. **Meia-respiração estrutural.**

PingPong fecha o ciclo.

---

## 2. O Ciclo Completo

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   STRATO (soberania)              CLAUDE.AI WEB (cognição)      │
│   ─────────────────               ────────────────────          │
│                                                                 │
│   /opt/windi/claudeWeb/                                         │
│         │                                                       │
│         │  1. Human Dragon corre cognitive-bind-module.sh       │
│         │     + lê últimos capítulos §XXX do claudeWeb/         │
│         ▼                                                       │
│   CBP gerado ─────cola───▶  Sessão Claude.ai abre               │
│                                       │                         │
│                                       │  2. Claude opera        │
│                                       │     dentro de BIS+state │
│                                       ▼                         │
│                              Capítulo §XXX produzido            │
│                              em markdown limpo                  │
│                                       │                         │
│                                       │  3. Cola ou download    │
│                                       │     para CCode          │
│                                       ▼                         │
│   CCode persiste em ◀────────── Markdown chega ao Strato        │
│   /opt/windi/claudeWeb/                                         │
│         │                                                       │
│         │  4. Hash + Ledger receipt + INDEX.md update           │
│         ▼                                                       │
│   Capítulo sealed ──► próxima sessão lê no próximo CBP          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Inspiração:** Strato → Claude (CBP carrega contexto fresco).
**Expiração:** Claude → Strato (sessão deposita capítulo sealed).
**Respiração:** ciclo completo, sem perda entre instâncias.

---

## 3. Estrutura do Filesystem

```
/opt/windi/claudeWeb/
├── INDEX.md                          # Índice activo de capítulos
├── README.md                         # Manual operacional do directório
│
├── S262-WINDI-HIOS-NAMING.md         # Capítulos sealed
├── S263-PINGPONG-PROTOCOL.md
├── S264-CBP-JSON-SCHEMA.md           # (pending)
├── S265-DRIFT-MONITOR-METRICS.md     # (pending)
│
├── PENDING/                          # Capítulos em pending state
│   └── S266-NOTEBOOK-002-DRAFT.md
│
└── ARCHIVE/                          # Capítulos superseded
    └── 2026-Q2/
        └── SXXX-superseded-by-SYYY.md
```

**Regras de directório:**

- Raiz: apenas capítulos `sealed` activos
- `PENDING/`: rascunhos aguardando sela ou implementação
- `ARCHIVE/`: capítulos substituídos por versão posterior (mantidos por
  lineage e auditoria)
- `INDEX.md`: única fonte de verdade sobre status actual

---

## 4. Template Canónico do Capítulo

Todo capítulo `S§XXX-*.md` deve abrir com YAML frontmatter:

```yaml
---
receipt:    WINDI-S§XXX-{SLUG}-YYYYMMDD-{HASH}
selo:       §XXX · {Título Curto} · v{N.N}
data:       YYYY-MM-DD · Kempten, Bavaria
doc_type:   {constitutional_naming | continuity_protocol | technical_spec
             | research_note | decision_log | architectural_seal}
extends:    [§XXX, §YYY]
supersedes: [§ZZZ ou none]
relates_to: [§AAA, §BBB]
origem:     {breve descrição da génese}
status:     {pending | sealed | superseded | archived}
verify:     https://windi-domain.com/verify-public/?id=...
---
```

Secções obrigatórias após o frontmatter:

1. **Título + epígrafe** (frase central + autoria + data)
2. **Problema Nomeado** (o que este capítulo resolve)
3. **Decisão / Estrutura / Conteúdo** (core do capítulo)
4. **Relação com Constituição Existente** (encaixes explícitos)
5. **O Que Este Selo NÃO Decide** (escopo negativo explícito)
6. **Origem** (genealogia: quem propôs, quem revisou, quem decidiu)
7. **Selo de Encerramento** + `OM SHANTI 🐉`

**Princípio:** capítulo legível em 5 anos por alguém sem o contexto da
sessão que o produziu.

---

## 5. INDEX.md — Estrutura Canónica

```markdown
# WINDI claudeWeb · INDEX

> Última actualização: YYYY-MM-DD · Sprint actual: {nome}

## Capítulos Sealed (activos)

| §    | Título                          | doc_type             | Data       | Status |
|------|----------------------------------|----------------------|------------|--------|
| §262 | WINDI-HIOS Naming                | constitutional_naming | 2026-05-14 | sealed |
| §263 | PingPong Protocol                | continuity_protocol   | 2026-05-14 | sealed |
| ...  | ...                              | ...                  | ...        | ...    |

## Capítulos Pending

| §    | Título                          | Aguarda                | Sprint Alvo |
|------|----------------------------------|------------------------|-------------|
| §264 | CBP-JSON Schema v0.3            | Architect proposal     | Sprint+1    |
| §265 | Drift Monitor Metrics            | 3 métricas validadas   | Sprint+1    |

## Capítulos Archived

Ver `ARCHIVE/{ANO-QN}/`.

## Próximo Passo Proposto

{1 acção concreta para a próxima sessão}
```

INDEX.md é **lido como parte do CBP**. É como a próxima instância sabe
o que existe sem queimar tokens a varrer ficheiros.

---

## 6. Separação de Responsabilidades

| Agente | Faz | Não Faz |
|--------|-----|---------|
| **Claude.ai web** (Guardian / Architect) | Produz capítulo em markdown limpo, pronto-a-persistir | Não escreve no filesystem Strato |
| **CCode** (Construtor) | Persiste em `/opt/windi/claudeWeb/`, computa SHA-256, actualiza INDEX.md, propõe receipt ao Ledger | Não decide conteúdo constitucional |
| **Human Dragon** | Decide, sela, autoriza Ledger receipt, autoriza mudança de status | — |
| **Forensic Ledger** (:8101) | Recebe `doc_type` específico, emite receipt verificável | — |
| **Witness** | Pode rever capítulo antes de sela; pode propor superseder | Não persiste nem decide |

**Three Dragons preservados em cada turno do ciclo.**

---

## 7. Lifecycle de um Capítulo

```
1. CBP abre sessão Claude.ai web
   ↓
2. Architect ou Guardian produz conteúdo durante sessão
   ↓
3. Capítulo emitido como markdown ready-to-persist
   ↓
4. CCode persiste em /opt/windi/claudeWeb/PENDING/ (ou raiz se sealed-direct)
   ↓
5. Human Dragon revê + decide status (sealed | pending | rejected)
   ↓
6. Se sealed:
   ├─ Ledger receipt emitido (doc_type: pingpong_chapter)
   ├─ Capítulo movido para raiz de claudeWeb/
   ├─ INDEX.md actualizado
   └─ Hash gravado em CLAUDE-HISTORY.md (entrada de fecho)
   ↓
7. Próxima sessão: cognitive-bind-module.sh inclui pointer no CBP
```

---

## 8. Estados Possíveis de um Capítulo

| Estado | Significado | Localização |
|--------|-------------|-------------|
| `pending` | Capítulo escrito, aguarda sela ou implementação | `/PENDING/` |
| `sealed` | Receipt no Ledger, imutável, activo | raiz `/claudeWeb/` |
| `superseded` | Substituído por capítulo posterior, mantido para lineage | `/ARCHIVE/{ANO-QN}/` |
| `archived` | Movido para arquivo, fora do INDEX activo | `/ARCHIVE/{ANO-QN}/` |
| `rejected` | Proposto mas rejeitado pelo Human Dragon | `/ARCHIVE/rejected/` |

**Transições válidas:**
- `pending` → `sealed` (decisão Human Dragon)
- `pending` → `rejected` (decisão Human Dragon)
- `sealed` → `superseded` (novo capítulo o substitui)
- `sealed` → `archived` (decisão Human Dragon, fim de ciclo)

Transições inválidas (rejeitadas pelo Governance Kernel):
- `sealed` → `pending` ou `rejected` (imutabilidade do sealed)
- `superseded` → `sealed` (não-ressurreição; criar capítulo novo se necessário)

---

## 9. Token Economy — "Pendurar Graciosamente"

Sem PingPong, cada sessão processa cada tópico até ao fim, queimando tokens
linearmente. Com PingPong, a sessão **pendura** capítulos em `pending` e
deixa a próxima sessão retomar fresca.

Exemplo prático: numa sessão saturada de 200k tokens, em vez de tentar
processar 5 tópicos parcialmente (cada um pela metade), a sessão sela 2
completos + pendura 3 em `pending` com escopo claro. Próxima sessão
arranca com chão fresco para os 3 pendurados.

**Princípio:** *"Token economy emerge naturalmente da disciplina de escopo,
não de optimização de prompt."*

---

## 10. Integração com Constituição

| Selo | Função no PingPong |
|------|---------------------|
| §236 · Session Continuity | Lei base — `CLAUDE-HISTORY.md` documenta cada ciclo PingPong em entrada de fecho |
| §261 · Cognitive Bind | Lei base — CBP é o "boot loader" que inclui pointers para claudeWeb/ |
| §247 · Nomenclatura | Capítulos seguem Tijolo/Obra/Encaixe/Selo |
| §248 · Two-Track | claudeWeb/ é **kernel infraestructural** — não é monetizável |

**Futura SKILL Anthropic:** `windi-pingpong-protocol` (analogous to
`windi-cognitive-bind` and `windi-session-continuity`) — para que cada nova
instância Claude.ai web leia este protocolo no arranque sem custo de cola.

---

## 11. O Que Este Protocolo NÃO Decide

- ❌ Schema canónico do CBP-JSON v0.3 (capítulo dedicado, §264)
- ❌ Implementação técnica do indexador automático de INDEX.md
  (CCode propõe; pode ser manual no início)
- ❌ Política de retenção do ARCHIVE/ (Human Dragon decide periodicamente)
- ❌ Mecanismo de promoção de capítulo a SKILL Anthropic (decisão caso-a-caso)
- ❌ Frequência ideal de pingpong por sessão (orgânico, não enforçado)

**Este protocolo decide apenas:**

- ✅ Existência canónica de `/opt/windi/claudeWeb/`
- ✅ Template de capítulo (YAML frontmatter + 7 secções)
- ✅ Estados possíveis e transições válidas
- ✅ Separação de responsabilidades Claude.ai / CCode / Human Dragon / Ledger
- ✅ Lifecycle do capítulo (7 passos)

---

## 12. Origem

Sessão Claude.ai web · 14 Mai 2026 · Kempten, Bavaria.

Sequência genealógica:

1. **Human Dragon** — observação durante a sessão de selagem WINDI-HIOS:
   *"O modelo Opus 4.7 consome muita energia e memória. O que eu chamaria
   PingPong: o que você acaba de demonstrar vai direto para o WINDI no
   Strato e se transforma em script de memorial claudeWeb.md."*
2. **Human Dragon** (continuação): *"Criar capítulos de entrada e saída
   denominados com §XXX corrente — pendura graciosamente os tópicos a
   executar um de cada vez. Isso se torna endpoints de continuidade às
   próximas instâncias."*
3. **Guardian** — formalização do protocolo:
   - reconhecimento de §261 como meia-respiração
   - mapping da arquitectura skills/INDEX como precedente
   - design das 7 secções do capítulo canónico
   - separação de responsabilidades Claude.ai / CCode / Human Dragon
4. **CCode (Construtor)** — confirmação de prontidão para receber e
   persistir capítulos em `/opt/windi/claudeWeb/` com receipt chain.

**Ratio decidendi:** continuidade cognitiva não se resolve por boa-vontade
nem por context window maior. Resolve-se por **estrutura externa
disciplinada** — filesystem como prótese de memória, capítulos como
unidades verificáveis, INDEX.md como mapa de retorno.

---

## 13. Selo de Encerramento

> **"Esta sessão lê o que a anterior escreveu, opera dentro do que o packet
> admite, e escreve para a próxima ler."**
>
> — Síntese §236 + §261 + §263 (PingPong)

> **"O PingPong não dá memória ao Claude.ai. Dá-lhe ancoragem persistente
> fora dele próprio."**

---

OM SHANTI 🐉
Liga IA+H · Kempten, Bavaria · 2026
*"AI processes. Human decides. WINDI guarantees."*
