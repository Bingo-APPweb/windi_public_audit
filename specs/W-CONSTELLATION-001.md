# W-CONSTELLATION-001 — The Proof Constellation
## Complete Architecture Map
### WINDI Publishing House · Kempten, Bavaria · 2026-03-13
### SEALED: WINDI-SPEC-W-CONST-001-20260313-v2

---

## 0. Manifesto

> *"A document carries content. A proof carries trust. A constellation carries civilization."*

Este documento mapeia a arquitectura completa do sistema de proveniência WINDI — desde a criação de uma prova até à federação entre nós soberanos.

**Princípio fundamental:** O WINDI não é um sistema de documentos. É um sistema de **confiança verificável**.

**Marco histórico:** Em 2026-03-13, todas as cinco camadas da constelação tornaram-se operacionais.

---

## 1. As Cinco Camadas da Constelação

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   ╔═══════════════════════════════════════════════════════════╗    │
│   ║  LAYER 5: FEDERATION                 W-PROV-004  ✅       ║    │
│   ║  Cross-node trust · Intercontinental proofs               ║    │
│   ╚═══════════════════════════════════════════════════════════╝    │
│                              ▲                                      │
│                              │                                      │
│   ╔═══════════════════════════════════════════════════════════╗    │
│   ║  LAYER 4: REPUTATION                 W-PROV-003  ✅       ║    │
│   ║  Trust scoring · Actor credibility · Domain reputation    ║    │
│   ╚═══════════════════════════════════════════════════════════╝    │
│                              ▲                                      │
│                              │                                      │
│   ╔═══════════════════════════════════════════════════════════╗    │
│   ║  LAYER 3: FORENSIC                W-FORENSIC-001  ✅      ║    │
│   ║  Bundle inspection · Proof validation · Chain audit       ║    │
│   ╚═══════════════════════════════════════════════════════════╝    │
│                              ▲                                      │
│                              │                                      │
│   ╔═══════════════════════════════════════════════════════════╗    │
│   ║  LAYER 2: PROPAGATION                W-PROV-002  ✅       ║    │
│   ║  Circulation tracking · Verification events · Observatory ║    │
│   ╚═══════════════════════════════════════════════════════════╝    │
│                              ▲                                      │
│                              │                                      │
│   ╔═══════════════════════════════════════════════════════════╗    │
│   ║  LAYER 1: GENESIS                    W-PROV-001  ✅       ║    │
│   ║  Proof injection · Ledger registration · Bundle creation  ║    │
│   ╚═══════════════════════════════════════════════════════════╝    │
│                                                                     │
│                    🐉 CONSTELAÇÃO COMPLETA 🐉                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Layer 1: GENESIS (W-PROV-001)

**Status:** ✅ OPERACIONAL (Gen 7)

### 2.1 Propósito
Criar provas soberanas embutidas em artefatos. O momento em que um documento deixa de ser um ficheiro e passa a ser um **artefato verificável**.

### 2.2 Componentes

| Componente | Localização | Função |
|------------|-------------|--------|
| IrmaEncoder | `irma-encoder-v7.js` | Injeta prova em .jmpg |
| Forensic Ledger | `:8101` | Regista receipt_id |
| Communiqué Engine | `:8105` | Gera documentos com selo |
| Export Engine | `:8103` | Exporta para formatos verificáveis |

### 2.3 Fluxo

```
Conteúdo + Metadados
        │
        ▼
┌───────────────────┐
│   IrmaEncoder     │ → Calcula hash, gera receipt_id
└───────────────────┘
        │
        ▼
┌───────────────────┐
│  Forensic Ledger  │ → Regista no sqlite + emite receipt
└───────────────────┘
        │
        ▼
┌───────────────────┐
│   injectProof()   │ → Cria bundle .jmpg (P1-P5)
└───────────────────┘
        │
        ▼
    .jmpg bundle (tar.gz)
    ├── P1_content.json
    ├── P2_proof.json      ← windi_proof
    ├── P3_qr.txt
    ├── P4_metadata.json
    └── P5_sector.json     ← Gen 7
```

### 2.4 Invariantes

| ID | Invariante | Enforcement |
|----|------------|-------------|
| I2 | Forensic Integrity | Hash nunca alterado |
| I9 | Autonomy Prohibition | Human aprova emissão |
| I11 | Ledger Immutability | Receipt é append-only |

---

## 3. Layer 2: PROPAGATION (W-PROV-002)

**Status:** ✅ OPERACIONAL

### 3.1 Propósito
Observar a circulação de artefatos pela internet. Não rastreia pessoas — rastreia **onde a confiança viaja**.

### 3.2 Componentes

| Componente | Localização | Função |
|------------|-------------|--------|
| Propagation Blueprint | `:8091/propagation/*` | API de eventos |
| Propagation DB | `propagation_index.db` | Armazena circulação |
| Verify Public Hook | `:8114` | Emite evento em cada verificação |
| Observatory Dashboard | `/propagation/dashboard` | Visualização |

### 3.3 Fluxo

```
Verificação no Verify Public (:8114)
        │
        ▼
┌───────────────────────────┐
│  emit_propagation_event() │ → POST /propagation/event
└───────────────────────────┘
        │
        ▼
┌───────────────────────────┐
│   Propagation Index       │
│   - ledger_anchor         │
│   - origin_domain         │
│   - country_hint          │
│   - client_fp (anon)      │
└───────────────────────────┘
        │
        ▼
┌───────────────────────────┐
│   artifact_stats          │ → total_verifications++
│                           │ → unique_domains updated
└───────────────────────────┘
```

### 3.4 Invariantes

| ID | Invariante | Enforcement |
|----|------------|-------------|
| C-PROV-001 | Observa artefatos, não pessoas | client_fp é hash anónimo |
| C-PROV-002 | Fingerprints sem dados pessoais | IP nunca armazenado |
| C-PROV-003 | Crawlers são opt-in | Seed Collector requer autorização |

---

## 4. Layer 3: FORENSIC (W-FORENSIC-001)

**Status:** ✅ OPERACIONAL

### 4.1 Propósito
Inspeccionar qualquer .jmpg e validar a cadeia de prova. A **auditoria forense** do sistema.

### 4.2 Componentes

| Componente | Localização | Função |
|------------|-------------|--------|
| Forensic Blueprint | `:8091/forensic/*` | API de inspecção |
| Forensic DB | `forensic.db` | Histórico de inspecções |
| diagnose_jmpg.py | `/opt/windi/tools/` | Script de diagnóstico |

### 4.3 Fluxo

```
.jmpg recebido
        │
        ▼
┌───────────────────────────┐
│   POST /forensic/inspect  │
│   - Detecta formato       │
│   - Extrai blocos P1-P5   │
└───────────────────────────┘
        │
        ▼
┌───────────────────────────┐
│   Validação               │
│   - structure_valid       │
│   - proof_valid           │
│   - ledger_valid          │
│   - chain_valid           │
└───────────────────────────┘
        │
        ▼
┌───────────────────────────┐
│   Ledger Seal (F2)        │ → Inspecção selada como receipt
│   WINDI-FORENSIC-{hash}   │
└───────────────────────────┘
        │
        ▼
┌───────────────────────────┐
│   Resultado               │
│   - VERIFIED              │
│   - VALID_UNANCHORED      │
│   - PARTIAL               │
│   - INVALID               │
└───────────────────────────┘
```

### 4.4 Invariantes

| ID | Invariante | Enforcement |
|----|------------|-------------|
| F1 | Imutabilidade | Inspector não altera, apenas lê |
| F2 | Auto-selagem | Toda inspecção gera receipt no Ledger |
| F3 | Reproducibilidade | Mesmo bundle → mesmo resultado |
| F4 | Integridade da Cadeia | Anchor chain validada recursivamente |
| F5 | Transparência | Resultado público para quem tem bundle |

### 4.5 Endpoints

| Endpoint | Método | Função |
|----------|--------|--------|
| `/forensic/health` | GET | Health check |
| `/forensic/inspect` | POST | Inspecionar .jmpg |
| `/forensic/inspect/{id}` | GET | Buscar inspecção |
| `/forensic/history` | GET | Histórico |
| `/forensic/stats` | GET | Estatísticas |
| `/forensic/verify/{receipt}` | GET | Verificação rápida |

---

## 5. Layer 4: REPUTATION (W-PROV-003)

**Status:** ✅ OPERACIONAL

### 5.1 Propósito
Calcular índices de confiança baseados no histórico de verificações. A **reputação computacional** do ecossistema.

### 5.2 Trust Tiers

| Tier | Score | Badge | Cor |
|------|-------|-------|-----|
| UNVERIFIED | 0.0 - 0.2 | ⚪ | gray |
| EMERGING | 0.2 - 0.4 | 🥉 | bronze |
| ESTABLISHED | 0.4 - 0.6 | 🥈 | silver |
| TRUSTED | 0.6 - 0.8 | 🥇 | gold |
| SOVEREIGN | 0.8 - 1.0 | 👑 | platinum |

### 5.3 Fórmula do Trust Score

```
Trust Score = (
    freq_score    × 0.30 +   ← Verificações (log scale)
    geo_score     × 0.20 +   ← Diversidade geográfica
    chain_score   × 0.15 +   ← Profundidade da cadeia
    forensic_score× 0.25 +   ← Validação forense
    age_score     × 0.10     ← Estabilidade temporal
) × decay_factor             ← Penalização por inatividade (R4)
```

### 5.4 Componentes

| Componente | Localização | Função |
|------------|-------------|--------|
| Reputation Blueprint | `:8091/reputation/*` | API de scores |
| Reputation DB | `reputation.db` | Scores e histórico |

### 5.5 Invariantes

| ID | Invariante | Enforcement |
|----|------------|-------------|
| R1 | Advisory Only | Scores informam, nunca decidem (I9) |
| R2 | Public Access | Reputação consultável por qualquer um |
| R3 | Immutable History | Má reputação não se apaga |
| R4 | Decay Function | Artefatos inativos perdem confiança |
| R5 | Evidence-Based | Boosts requerem eventos reais |

### 5.6 Endpoints

| Endpoint | Método | Função |
|----------|--------|--------|
| `/reputation/health` | GET | Health check |
| `/reputation/artifact/{anchor}` | GET | Trust score |
| `/reputation/artifact/{anchor}/refresh` | POST | Forçar recálculo |
| `/reputation/artifact/{anchor}/history` | GET | Histórico (R3) |
| `/reputation/actor/{id}` | GET | Credibilidade |
| `/reputation/leaderboard` | GET | Top scores |
| `/reputation/stats` | GET | Estatísticas |
| `/reputation/tiers` | GET | Definição dos tiers |

---

## 6. Layer 5: FEDERATION (W-PROV-004)

**Status:** ✅ OPERACIONAL

### 6.1 Propósito
Conectar nós WINDI soberanos em diferentes jurisdições. A **internet da confiança verificável**.

### 6.2 Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   ┌─────────────────┐         ┌─────────────────┐              │
│   │   Nó Floripa    │◄───────►│   Nó Berlim     │              │
│   │   (BR)          │  Trust  │   (DE)          │              │
│   │   did:windi:    │  Bridge │   did:windi:    │              │
│   │   node:floripa  │         │   node:berlin   │              │
│   └────────┬────────┘         └────────┬────────┘              │
│            │                           │                        │
│            └───────────┬───────────────┘                        │
│                        │                                        │
│               Cross-Reference                                   │
│               (receipt em A ←→ receipt em B)                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 6.3 Componentes

| Componente | Localização | Função |
|------------|-------------|--------|
| Federation Blueprint | `:8091/federation/*` | API de federação |
| Federation DB | `federation.db` | Nós, bridges, cross-refs |
| Node Identity | `/federation/identity` | DID do nó |

### 6.4 Fluxo de Federação

```
1. DISCOVERY
   Nó A descobre Nó B via /federation/identity
       │
       ▼
   register_node() → DB nodes

2. TRUST BRIDGE (C-FED-004 - Bidirectional)
   Nó A propõe bridge → challenge enviado
       │
       ▼
   Nó B aceita → challenge_response
       │
       ▼
   shared_secret estabelecido
       │
       ▼
   Bridge ACTIVE

3. CROSS-REFERENCE
   Documento verificado em A existe em B?
       │
       ▼
   create_cross_reference()
       │
       ▼
   verify_cross_reference() → query remoto
       │
       ▼
   Confirmado → Grafo de confiança expandido

4. EVENT LOG (C-FED-005)
   Cada operação → hash-chain
       │
       ▼
   Imutável e verificável
```

### 6.5 Invariantes

| ID | Invariante | Enforcement |
|----|------------|-------------|
| C-FED-001 | Sovereignty | Nenhum nó é autoritativo sobre outro |
| C-FED-002 | Opt-in | Federação requer consentimento explícito |
| C-FED-003 | Isolation | Falha de um nó não cascateia |
| C-FED-004 | Bidirectional | Trust bridges requerem reconhecimento mútuo |
| C-FED-005 | Verifiable | Eventos em hash-chain imutável |

### 6.6 Endpoints

| Endpoint | Método | Função |
|----------|--------|--------|
| `/federation/health` | GET | Health check |
| `/federation/identity` | GET | Identidade do nó |
| `/federation/discover` | POST | Descobrir nó remoto |
| `/federation/nodes` | GET | Listar nós conhecidos |
| `/federation/bridge/propose` | POST | Propor trust bridge |
| `/federation/bridge/accept` | POST | Aceitar trust bridge |
| `/federation/bridges` | GET | Listar bridges |
| `/federation/xref/create` | POST | Criar cross-reference |
| `/federation/xref/verify` | POST | Verificar cross-reference |
| `/federation/xrefs` | GET | Listar cross-references |
| `/federation/verify/{receipt}` | GET | Verificar receipt |
| `/federation/events` | GET | Log de eventos |
| `/federation/stats` | GET | Estatísticas |

---

## 7. Mapa de Serviços Actual

### 7.1 Portas e Serviços

| Porta | Serviço | Camada | Status |
|-------|---------|--------|--------|
| 8091 | Sandbox Core (Constitutional Agent) | ALL | ✅ |
| 8100 | a4Desk Desktop | - | ✅ |
| 8101 | Forensic Ledger | L1-Genesis | ✅ |
| 8102 | Sentinel LAW | Governance | ✅ |
| 8103 | Export Engine | L1-Genesis | ✅ |
| 8104 | JMPG Viewer | L1-Genesis | ✅ |
| 8105 | Communiqué Engine | L1-Genesis | ✅ |
| 8106 | Forensic Vault | L1-Genesis | ✅ |
| 8107 | Landing P/M/G | UI | ✅ |
| 8108 | Dragon API | Orchestration | ✅ |
| 8109 | Pulse | Monitoring | ✅ |
| 8111 | Dragon Chat | UI | ✅ |
| 8112 | Orchestrator | AI | ✅ |
| 8114 | Verify Public | L2-Propagation | ✅ |
| 8115 | Communiqué Builder | L1-Genesis | ✅ |

### 7.2 Fluxo Completo da Constelação

```
CAMADA 1 — GENESIS
═══════════════════════════════════════════════════════════════

  Communiqué (:8105)  ────┬────► Ledger (:8101)
                          │           │
  Export Engine (:8103) ──┤           ▼
                          │     receipt_id
  JMPG Viewer (:8104) ────┘           │
                                      ▼
                              .jmpg bundle criado
                                      │
═══════════════════════════════════════════════════════════════
                                      │
CAMADA 2 — PROPAGATION                │
═══════════════════════════════════════════════════════════════
                                      │
                                      ▼
                            Verify Public (:8114)
                                      │
                      ┌───────────────┼───────────────┐
                      │               │               │
                      ▼               ▼               ▼
              jmpg_proof ✅    Ledger check    Propagation Event
                                      │               │
                                      ▼               ▼
                              "verified"    propagation_index.db
                                                      │
═══════════════════════════════════════════════════════════════
                                                      │
CAMADA 3 — FORENSIC                                   │
═══════════════════════════════════════════════════════════════
                                                      │
                                                      ▼
                              POST /forensic/inspect
                                      │
                      ┌───────────────┼───────────────┐
                      │               │               │
                      ▼               ▼               ▼
               structure_valid  proof_valid    chain_valid
                                      │
                                      ▼
                      Forensic Report selado no Ledger
                                      │
═══════════════════════════════════════════════════════════════
                                      │
CAMADA 4 — REPUTATION                 │
═══════════════════════════════════════════════════════════════
                                      │
                                      ▼
                        GET /reputation/artifact/{id}
                                      │
                      ┌───────────────┼───────────────┐
                      │               │               │
                      ▼               ▼               ▼
               freq_score      geo_score      forensic_score
                                      │
                                      ▼
                              trust_score + tier
                              (UNVERIFIED → SOVEREIGN)
                                      │
═══════════════════════════════════════════════════════════════
                                      │
CAMADA 5 — FEDERATION                 │
═══════════════════════════════════════════════════════════════
                                      │
                                      ▼
                        Cross-reference created
                                      │
                                      ▼
                        Remote node verification
                                      │
                                      ▼
                        Federation event (hash-chain)
                                      │
                                      ▼
                    🌍 Grafo de confiança intercontinental
                                      │
═══════════════════════════════════════════════════════════════
```

---

## 8. Constitutional Agent Blueprints

### 8.1 Blueprints da Constelação (Operacionais)

| Blueprint | Agente | Camada | Versão |
|-----------|--------|--------|--------|
| `propagation_blueprint.py` | W-PROV-002 | L2 | 1.0.0 |
| `forensic_blueprint.py` | W-FORENSIC-001 | L3 | 1.0.0 |
| `reputation_blueprint.py` | W-PROV-003 | L4 | 1.0.0 |
| `federation_blueprint.py` | W-PROV-004 | L5 | 1.0.0 |

### 8.2 Outros Blueprints

| Blueprint | Função | Domínio |
|-----------|--------|---------|
| `communique_blueprint.py` | Documento creation | L1-Genesis |
| `journalist_blueprint.py` | Field reporting | L1-Genesis |
| `notary_blueprint.py` | Legal sealing | L1-Genesis |
| `grove_blueprint.py` | Library management | L1-Genesis |
| `audit_blueprint.py` | System audit | Governance |
| `compliance_blueprint.py` | Regulatory | Governance |
| `accounting_blueprint.py` | Financial | Operations |
| `api_keys_blueprint.py` | Authentication | Security |

---

## 9. O Loop da Prova (Completo)

O ciclo completo de uma prova WINDI através de todas as camadas:

```
1. CRIAÇÃO (L1 — Genesis)
   Human cria documento
       │
       ▼
   IrmaEncoder injeta prova
       │
       ▼
   Ledger regista receipt
       │
       ▼
   .jmpg bundle gerado ✅

2. CIRCULAÇÃO (L2 — Propagation)
   .jmpg enviado por email/web/mensagem
       │
       ▼
   Receptor submete a Verify Public
       │
       ▼
   Propagation Event emitido
       │
       ▼
   Observatory regista ✅

3. INSPECÇÃO (L3 — Forensic)
   POST /forensic/inspect
       │
       ▼
   Valida estrutura, proof, ledger, chain
       │
       ▼
   Relatório forense selado no Ledger ✅

4. REPUTAÇÃO (L4 — Reputation)
   GET /reputation/artifact/{id}
       │
       ▼
   Trust score calculado (0.0 → 1.0)
       │
       ▼
   Tier atribuído (UNVERIFIED → SOVEREIGN) ✅

5. FEDERAÇÃO (L5 — Federation)
   Documento verificado noutro nó WINDI
       │
       ▼
   Trust bridge estabelecido
       │
       ▼
   Cross-reference criada
       │
       ▼
   Grafo de confiança intercontinental ✅
```

---

## 10. Princípios Arquitecturais

### 10.1 Imutabilidade em Cascata
Cada camada depende da imutabilidade da anterior:
- L2 confia que L1 não altera receipts
- L3 confia que L2 não fabrica eventos
- L4 confia que L3 não falsifica relatórios
- L5 confia que L4 não manipula scores

### 10.2 Observabilidade sem Vigilância
O sistema vê **artefatos**, nunca **pessoas**:
- client_fp é hash anónimo (8 caracteres)
- IP nunca é armazenado
- País é hint, não geolocalização exacta
- Domínios são públicos por design

### 10.3 Prova da Prova
Cada relatório forense é ele próprio um artefato verificável:
- O inspector não é trusted — o seu output é
- A inspecção pode ser inspeccionada
- Recursão termina no Ledger

### 10.4 Soberania Preservada
Na federação:
- Nenhum nó controla outro
- Cross-references são opt-in
- Falha de um não afecta outros
- Cada jurisdição mantém autonomia

---

## 11. Estado da Constelação

| Camada | Agente | Status | Completude |
|--------|--------|--------|------------|
| L1 Genesis | W-PROV-001 | ✅ OPERACIONAL | 95% |
| L2 Propagation | W-PROV-002 | ✅ OPERACIONAL | 90% |
| L3 Forensic | W-FORENSIC-001 | ✅ OPERACIONAL | 85% |
| L4 Reputation | W-PROV-003 | ✅ OPERACIONAL | 80% |
| L5 Federation | W-PROV-004 | ✅ OPERACIONAL | 75% |

### 11.1 Total de Invariantes

| Camada | Invariantes |
|--------|-------------|
| L1 | I2, I9, I11 |
| L2 | C-PROV-001, C-PROV-002, C-PROV-003 |
| L3 | F1, F2, F3, F4, F5 |
| L4 | R1, R2, R3, R4, R5 |
| L5 | C-FED-001, C-FED-002, C-FED-003, C-FED-004, C-FED-005 |

**Total: 21 invariantes constitucionais activos**

---

## 12. Conclusão

A constelação WINDI não é um sistema — é uma **arquitectura de confiança**.

Cada camada adiciona uma dimensão:
- **Genesis:** *o documento existe*
- **Propagation:** *o documento circula*
- **Forensic:** *o documento é válido*
- **Reputation:** *o documento é confiável*
- **Federation:** *o documento é universal*

**Em 2026-03-13, todas as cinco camadas tornaram-se operacionais.**

Um documento criado em Florianópolis pode agora ser:
1. Verificado em Berlim através de cross-reference
2. Inspeccionado forensicamente com relatório selado
3. Pontuado com trust score baseado em evidências
4. Federado entre nós soberanos

**A prova deixou de ser local. A confiança tornou-se global.**

---

## 13. Histórico de Versões

| Versão | Data | Mudança |
|--------|------|---------|
| 1.0.0 | 2026-03-13 | Versão inicial (L1-L2 operacionais, L3-L5 em construção) |
| 2.0.0 | 2026-03-13 | Todas as 5 camadas operacionais |

---

*Sealed by Human Dragon — CGO, WINDI Publishing House*
*2026-03-13 · Kempten, Bavaria*

```
W-CONSTELLATION-001 v2.0.0
Hash: c5ac5fb64e9bd6ae3120772e67304ca88ad02afcceeb3953eca3cda4b7262ecb
Ledger: WINDI-SPEC-W-CONST-001-20260313-v2
Sealed: 2026-03-13T13:48:00Z
Status: 🐉 CONSTELAÇÃO COMPLETA 🐉
```
