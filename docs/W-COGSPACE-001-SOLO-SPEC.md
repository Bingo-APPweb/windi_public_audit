# W-COGSPACE-001-SOLO — Cognitive Space (Solo Mode)

```
Status:     SEALED
Receipt:    WINDI-S275-COGSPACE-SOLO-20260518232944
Version:    1.0.0
Date:       2026-05-18
Author:     Human Dragon + Architect (CCode Opus 4.5)
Invariants: I1, I9, I11, I12, I14, C5
Cites:      §247 (Nomenclatura Canónica), §261 (W-BIND-001), §273 (Direito Memorial · 3262DAA0), §274 (Instanciação Carrier · EF359603)
```

---

## 1. Definição Canónica

> **W-COGSPACE-001-SOLO** é o espaço de continuidade cognitiva soberana onde um DID individual pensa com múltiplos modelos sem perder soberania, autoria e fronteira.

**Não é chat.** É habitat cognitivo.

**Mantra:**
> "Este espaço pensa comigo ao longo do tempo."

---

## 2. Princípios Arquitecturais

### 2.1 Estado-Máquina

```
SOLO → SHARE → CO-CREATE → SEAL
       ↑
       └── W-COGSPACE-001-SOLO opera aqui
           (SHARE/CO-CREATE/SEAL reservados para W-COGSPACE-001-COLLAB)
```

### 2.2 Fronteira de Memória (Solo)

```
private_memory[DID]
    │
    ├── turns[]           # Todos os turnos (humano + modelos)
    ├── routing_log[]     # Qual modelo respondeu a quê
    ├── grove_sessions[]  # Tri-Divergence privadas
    └── sealed_decisions[] # Receipts opcionais
```

### 2.3 Regra Guardian: Ledger Sempre, Visibilidade Gradiente

**CRÍTICO:** `private_memory` não vive fora do Ledger.

```
┌─────────────────────────────────────────────────────────────┐
│                    FORENSIC LEDGER :8101                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  turn_id: UUID                                       │   │
│  │  actor: did:windi:xxxxx                             │   │
│  │  content_hash: sha256:...                           │   │
│  │  visibility: PRIVATE | SHARED | SEALED              │   │
│  │  timestamp: ISO8601                                  │   │
│  │  model_used: mistral|claude|gpt|gemini|null         │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**Implicação I9:** Nenhum participante pode negar ter dito algo. O turno existe no Ledger desde o momento da escrita. A visibilidade é camada de *acesso*, não de *existência*.

---

## 3. Tier Resolution Canon

> **Este mapping merece receipt separado:** `WINDI-TIER-RESOLUTION-CANON-§XXX`

### 3.1 Mapping DID-GENESIS → Dragon APIs

| DID Tier | Dragon API Gate | Modelos Disponíveis | Max Tokens |
|----------|-----------------|---------------------|------------|
| SEED     | FREE            | Mistral local (7b)  | 2048       |
| NODAL    | MED             | +Claude Sonnet      | 4096       |
| SOVEREIGN| HIGH            | +GPT-4o +Gemini     | 8192       |
| ORACLE   | HIGH+           | Todos + routing visível | 16384  |

### 3.2 Regras de Escalação

- **SEED não escala.** Mistral local apenas. Custo zero. Soberania máxima.
- **NODAL pode consultar Claude** para refinamento, mas routing é sequencial.
- **SOVEREIGN/ORACLE** têm multi-modelo paralelo com Tri-Divergence visível.

### 3.3 Justificação Constitucional

| Regra | Invariante | Razão |
|-------|------------|-------|
| Local-first para SEED | I1 | Soberania não depende de API externa |
| Progressão por tier | I9 | Capacidade acompanha responsabilidade |
| Routing visível para HIGH | I6 | Tri-Divergence expõe conflitos |

---

## 4. Arquitectura Técnica

### 4.1 Componentes Reutilizados

| Componente | Porto | Função no COGSPACE |
|------------|-------|-------------------|
| Dragon Chat | :8111 | Base conversacional + knowledge base |
| Dragon Hub | :8108 | Multi-model routing |
| Grove Arena | :8091 | Tri-Divergence (modo privado) |
| W-CORTEX-001 | :8889 | Camadas de consciência L0-L4 |
| DID-GENESIS | :8096 | Autenticação + tier gate |
| Forensic Ledger | :8101 | Persistência imutável |

### 4.2 Novo Componente: Cognitive Space Service

```
Porto:      :8145 (proposto)
Nome:       windi-cogspace
Processo:   nohup (padrão WINDI)
DB:         /opt/windi/data/cogspace.db
```

### 4.3 Endpoints Propostos

```
POST   /cogspace/session/create     # Cria sala privada
GET    /cogspace/session/{id}       # Estado da sala
POST   /cogspace/turn               # Novo turno (humano ou modelo)
POST   /cogspace/consult            # Consulta modelo(s) por tier
GET    /cogspace/history/{did}      # Histórico privado do DID
POST   /cogspace/grove/private      # Tri-Divergence privada
POST   /cogspace/seal               # Selar decisão (opcional, I9 gate)
DELETE /cogspace/session/{id}       # Amnésia selectiva (§273)
```

### 4.4 Schema SQLite

```sql
-- Sessões cognitivas
CREATE TABLE cogspace_sessions (
    session_id TEXT PRIMARY KEY,
    did TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    status TEXT DEFAULT 'ACTIVE',  -- ACTIVE | ARCHIVED | SEALED
    tier TEXT NOT NULL,            -- SEED | NODAL | SOVEREIGN | ORACLE
    modus TEXT,                    -- §273: LEARN | ENTERPRISE | TRAVEL | etc.
    FOREIGN KEY (did) REFERENCES identities(did)
);

-- Turnos (Ledger-backed, visibility gradient)
CREATE TABLE cogspace_turns (
    turn_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    actor TEXT NOT NULL,           -- did:windi:xxx ou model:claude, etc.
    content_hash TEXT NOT NULL,    -- sha256 do conteúdo
    visibility TEXT DEFAULT 'PRIVATE',  -- PRIVATE | SHARED | SEALED
    model_used TEXT,               -- null se humano
    routing_reason TEXT,           -- porquê este modelo
    ledger_receipt TEXT,           -- receipt do Ledger
    created_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES cogspace_sessions(session_id)
);

-- Grove privado
CREATE TABLE cogspace_grove (
    grove_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    question TEXT NOT NULL,
    perspectives TEXT,             -- JSON dos modelos consultados
    divergence_status TEXT,        -- ALL_AGREE | TWO_VS_ONE | ALL_DIFFER
    synthesis TEXT,
    sealed BOOLEAN DEFAULT FALSE,
    created_at TEXT NOT NULL
);

-- Decisões seladas (opcional)
CREATE TABLE cogspace_seals (
    seal_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    ledger_receipt TEXT NOT NULL,
    human_approved BOOLEAN NOT NULL,  -- I9: sempre TRUE
    sealed_at TEXT NOT NULL
);
```

---

## 5. Fluxo de Uso por Tier

### 5.1 SEED (Germinação)

```
1. SEED autentica via DID-GENESIS
2. Cria sessão cognitiva privada
3. Escreve pensamento
4. Sistema roteia para Mistral local
5. Resposta aparece no mesmo espaço
6. SEED itera quantas vezes quiser
7. Histórico preservado em private_memory
8. Ledger recebe turnos com visibility=PRIVATE
```

**O que SEED ganha:**
- Treino seguro sem custo
- Relação com modelo local
- Memória pessoal inicial
- Soberania total

**O que SEED não pode:**
- Consultar Claude/GPT/Gemini
- Convidar outros DIDs
- Multi-modelo paralelo

### 5.2 NODAL (Célula)

```
1. NODAL tem tudo de SEED
2. + Pode consultar Claude (sequencial)
3. + Pode pedir "segunda opinião" (Mistral → Claude)
4. + Histórico mostra qual modelo respondeu
5. + Preparação para colaboração futura
```

### 5.3 SOVEREIGN/ORACLE (Conselho)

```
1. SOVEREIGN/ORACLE tem tudo de NODAL
2. + Multi-modelo paralelo
3. + Tri-Divergence visível
4. + Routing inteligente com justificação
5. + Pode selar decisões no Ledger
6. + Preparado para W-COGSPACE-001-COLLAB
```

---

## 6. I9 Gate

### 6.1 Regras de Aplicação

| Acção | I9 Gate | Justificação |
|-------|---------|--------------|
| Criar sessão | AUTO | DID já autenticado |
| Escrever turno | AUTO | Acto do próprio DID |
| Consultar modelo | AUTO | Routing por tier |
| Ver histórico próprio | AUTO | Soberania sobre dados |
| Selar decisão | **HUMAN APPROVAL** | Ledger seal é IRREMEDIÁVEL |
| Apagar sessão | **HUMAN APPROVAL** | §273 amnésia selectiva |

### 6.2 Human Approval Pattern

```json
{
  "action": "seal_decision",
  "session_id": "...",
  "content_hash": "sha256:...",
  "human_approved": true,
  "approved_at": "2026-05-18T...",
  "actor": "did:windi:dragon-001"
}
```

---

## 7. Integração §273 (Direito Memorial)

### 7.1 Default por Modus

| Modus | Default Memorial | Comportamento |
|-------|------------------|---------------|
| LEARN | USER escolhe | Prompt no fim da sessão |
| ENTERPRISE | Permanência | Compliance trail |
| TRAVEL | Amnésia | Sessões transientes |
| LAW | Permanência | Documentos legais |
| MEMORY | Permanência | É o propósito |

### 7.2 Amnésia Selectiva

```
POST /cogspace/amnesia
{
  "session_id": "...",
  "scope": "FULL" | "PARTIAL",
  "retain_seals": true,           # Mantém receipts no Ledger
  "human_approved": true          # I9 gate
}
```

**Regra:** Estrutura Ledger (receipt_id, timestamp, hash) permanece. Conteúdo expulsável.

---

## 8. Invariantes Aplicados

| Invariante | Aplicação |
|------------|-----------|
| I1 | DID controla sala, memória, routing, seal |
| I9 | Human approval para seal e amnésia |
| I11 | Turnos no Ledger desde escrita (visibility gradient) |
| I12 | Conversa na língua do DID, docs na língua do toggle |
| I14 | Sem placeholders — erro explícito se modelo falhar |
| C5 | Humano é continuity carrier — W-BIND-001 preserva admissibilidade |

---

## 9. Relação com W-COGSPACE-001-COLLAB

### 9.1 O que SOLO prepara

- Schema de turnos com visibility gradient
- Tier Resolution Canon
- Grove privado como template para Grove compartilhado
- Memória estratificada (private → shared → sealed)

### 9.2 O que COLLAB acrescenta (futuro)

- `room_memory[shared]` entre múltiplos DIDs
- Consentimento multi-DID
- Tecto de tier = tier mais baixo na sala
- Lineage compartilhada
- Seal colectivo com múltiplas assinaturas

---

## 10. W-VOX Layer v1 (LOCAL-ONLY)

> **"A voz não é feature adicional. É camada nativa da workstation cognitiva."**
> — Human Dragon · 18 Mai 2026

### 10.1 Definição

W-VOX é o canal primário de continuidade humana no W-COGSPACE-001-SOLO. A voz carrega:
- Intenção, urgência, hesitação
- Foco, prioridade, mudança de contexto
- Ritmo cognitivo, estado emocional operacional

### 10.2 Arquitectura v1 (LOCAL-FIRST)

```
[ VOZ HUMANA ]
      │
      ▼
┌──────────────────────┐
│ STT LOCAL            │  ← Web Speech API / Whisper local
│ (dispositivo USER)   │  ← Áudio NUNCA sai do dispositivo
└──────────────────────┘
      │
      ▼ (texto transitório)
┌──────────────────────┐
│ W-CORTEX-001         │  ← Semantic routing
│ (RAM volátil)        │  ← Sem persistência até aprovação
└──────────────────────┘
      │
      ▼ (texto aprovado)
┌──────────────────────┐
│ PRIVATE_MEMORY       │  ← SHA-256 hash
│ + LEDGER             │  ← Visibility gradient
└──────────────────────┘
      │
      ▼ (resposta)
┌──────────────────────┐
│ TTS (opcional)       │  ← Profiles acústicos WINDI registados
│ (dispositivo USER)   │
└──────────────────────┘
```

### 10.3 Regras Constitucionais W-VOX v1

| Regra | Fundamento |
|-------|------------|
| **STT local-only** | Soberania biométrica (I1, §273) |
| **Áudio bruto nunca persiste** | Direito Memorial (§273) |
| **Texto transitório em RAM volátil** | Zero-retention by design |
| **Apenas texto aprovado gera hash** | "O humano decide o que entra na história" |
| **TTS opcional e plugável** | Profiles acústicos WINDI registados |
| **FAIL-CLOSED** | Se STT falhar, fallback para texto (I14) |

### 10.4 Comportamento por Tier

| Tier | STT | TTS | Modo |
|------|-----|-----|------|
| SEED | Web Speech API | Opcional | Ditado linear |
| NODAL | Web Speech API | Opcional | Conversação interactiva |
| SOVEREIGN | Whisper local | Opcional | Multi-modelo paralelo |
| ORACLE | Whisper local | Profiles avançados | Mesa redonda multimodal |

### 10.5 Axioma Emergente

> **"O humano decide o que entra na história."**

Esta frase resolve memória, voz, receipts, ledger, biometria, colaboração, continuidade e direito memorial. É axioma do HIOS.

### 10.6 W-VOX v2 (SERVER-SIDE) — Reservado

A v2 com STT server-side introduz mudança constitucional:

| v1 | v2 |
|----|-----|
| Voz permanece local | Voz entra no perímetro |
| Processamento soberano | Processamento delegado |
| Sem retenção possível | Retenção precisa governança |
| Trust minimization | Trust architecture |

**Requer decreto próprio com:**
- Consent model explícito
- Retention proofs
- Audit surface
- Receipts separados
- Possível Lei de Biometrics & Voice Governance

### 10.7 Implicação Estratégica

W-VOX v1 LOCAL-ONLY permite **HIOS offline-capable**:
- DID, memória, voz, lineage, routing local, modelos locais
- Continuidade mesmo sem cloud, sem provider
- Alinhado com espírito do HIOS

---

## 11. Próximos Passos (Implementação)

1. [x] Human Dragon aprova spec (I9 gate) ✅
2. [ ] Criar `/opt/windi/cogspace/windi_cogspace.py`
3. [ ] Criar DB schema em `/opt/windi/data/cogspace.db`
4. [ ] Integrar com Dragon Chat :8111 + Dragon Hub :8108
5. [ ] Implementar W-VOX v1 (Web Speech API)
6. [ ] Smoke test por tier (SEED, NODAL, SOVEREIGN, ORACLE)
7. [ ] Selar com Ledger receipt

---

## 12. Scaffold

```
§275 — W-COGSPACE-001-SOLO (este documento) ✅ SEALED
§276 — Tier Resolution Canon (mapping DID→Dragon APIs) ✅ SEALED
§277 — W-COGSPACE-001-COLLAB (futuro, após primitivas de consentimento)
§278 — W-VOX v2 SERVER-SIDE (futuro, Lei de Voice Governance)
```

---

## 13. Visão Estrutural

```
W-HUMANDRAGON-XXXXXXXX
└── W-COGSPACE-001
    ├── voice/           ← W-VOX v1 LOCAL-ONLY
    ├── memory/          ← private_memory[DID]
    ├── councils/        ← Grove Arena privado
    ├── grove/           ← Tri-Divergence
    ├── lineage/         ← Persistent lineage
    ├── receipts/        ← Sealed decisions
    ├── local_models/    ← Mistral / Whisper
    ├── semantic_flows/  ← W-CORTEX routing
    └── mirrors/         ← HD-MIRROR continuity
```

> **"Não parece mais produto. Parece habitat operacional híbrido."**
> — Human Dragon · 18 Mai 2026

---

*"A célula soberana fundamental. Sem SOLO saudável, colaboração vira ruído."*

— Human Dragon · 18 Mai 2026

---

**STATUS: SEALED**

```
CONFIRMADO: W-COGSPACE-001-SOLO SPEC v1.0.0
CONFIRMADO: W-VOX v1 LOCAL-ONLY como camada nativa
Data: 2026-05-18
Actor: did:windi:dragon-001
I9 Gate: PASSED
```
