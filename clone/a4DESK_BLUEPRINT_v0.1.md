# a4Desk BLUEPRINT TÉCNICO v0.1

**De Manifesto a Máquina**
**Data:** 2026-02-09
**Status:** ARCHITECTURAL_FOUNDATION

---

## VISÃO GERAL

O a4Desk é um **Desktop-first Runtime** de verdade documental.
Não é um app. É uma **película de vidro forense** sobre o sistema operacional.

---

# PARTE 1: ESTRUTURA DE DIRETÓRIOS DO CLONE

```
a4desk-clone/
│
├── core/                          # IMUTÁVEL - Lei, não config
│   ├── __init__.py
│   ├── invariants.py              # I1-I9 enforced
│   ├── zk_boundary.py             # Zero-Knowledge: permitido/proibido
│   ├── ledger.py                  # Append-only + Merkle + verificador
│   ├── seal.py                    # QR + metadados + selo visual + proof_id
│   └── policy_engine.py           # Thresholds configuráveis (não invariantes)
│
├── expression/                    # CONFIGURÁVEL - Expressão controlada
│   ├── agent_conduct.yaml         # Tom, modos FLOW/ATTENTION/PAUSE
│   ├── branding/
│   │   ├── logo.svg
│   │   ├── palette.yaml
│   │   └── templates/
│   ├── language_pack/
│   │   ├── pt_BR.yaml
│   │   ├── de_DE.yaml
│   │   └── en_US.yaml
│   └── workflows/
│       └── escalation_chain.yaml
│
├── runtime/                       # TRÊS PLANOS DO DESKTOP HYBRID
│   ├── workspace/                 # Plano 1: FLOW
│   │   ├── editor.py
│   │   ├── templates/
│   │   └── autosave.py
│   ├── governance/                # Plano 2: SILENT
│   │   ├── scanner.py
│   │   ├── flags.py
│   │   └── decision_modal.py
│   └── forensic/                  # Plano 3: INVISIBLE
│       ├── outbox.py
│       ├── receipts.py
│       ├── ledger_local.py
│       └── hub_sync.py
│
├── api/                           # ENDPOINTS LOCAIS
│   ├── __init__.py
│   ├── seal.py                    # POST /api/seal
│   ├── ledger.py                  # GET /api/ledger
│   ├── verify.py                  # POST /api/verify
│   └── health.py                  # GET /api/health
│
├── agent/                         # WINDI AGENT - Maestro UX
│   ├── __init__.py
│   ├── states.py                  # FLOW/ATTENTION/PAUSE
│   ├── conductor.py               # Orquestrador de fricção mínima
│   └── prohibitions.py            # Hard blocks (R4/R5)
│
├── sync/                          # PROTOCOLO CLONE ↔ HUB
│   ├── mtls.py                    # Identidade soberana do clone
│   ├── outbox.py                  # Offline-first queue
│   ├── proof_envelope.py          # Apenas provas, não conteúdo
│   └── rate_limiter.py
│
├── contracts/                     # CONTRATOS JSON/YAML
│   ├── proof_envelope.json
│   ├── receipt.json
│   ├── decision.json
│   └── document_state.json
│
├── config/                        # CONFIGURAÇÃO DO CLONE
│   ├── clone_identity.yaml
│   ├── policies.yaml              # R0-R5 thresholds
│   └── hub_connection.yaml
│
└── installer/                     # EMPACOTAMENTO
    ├── linux/
    ├── windows/
    └── macos/
```

---

# PARTE 2: CONTRATOS JSON/YAML

## 2.1 ProofEnvelope (proof_envelope.json)

```json
{
  "$schema": "https://windi.systems/schemas/proof_envelope.v1.json",
  "envelope_id": "UUID",
  "clone_id": "CLONE_IDENTITY_HASH",
  "timestamp_utc": "ISO8601",
  "document": {
    "hash_sha256": "string",
    "byte_ranges": [
      {"start": 0, "end": 1024, "hash": "string"}
    ],
    "metadata_hash": "string"
  },
  "decision": {
    "type": "APPROVED | OVERRIDDEN | DEFERRED",
    "human_id": "ISP_HASH",
    "reason": "string (required if OVERRIDDEN)",
    "timer_seconds": 0
  },
  "receipts": [
    {"type": "ROUTE", "timestamp": "ISO8601"},
    {"type": "ACK", "timestamp": "ISO8601"},
    {"type": "SEAL", "timestamp": "ISO8601"}
  ],
  "seal": {
    "proof_id": "string",
    "qr_data": "base64",
    "visual_hash": "string"
  }
}
```

## 2.2 Receipt (receipt.json)

```json
{
  "$schema": "https://windi.systems/schemas/receipt.v1.json",
  "receipt_id": "UUID",
  "type": "ROUTE | ACK | SEAL | VERIFY | ALERT",
  "document_hash": "string",
  "clone_id": "string",
  "timestamp_utc": "ISO8601",
  "payload": {
    "action": "string",
    "result": "SUCCESS | PENDING | FAILED",
    "details": {}
  },
  "signature": "string"
}
```

## 2.3 Decision (decision.json)

```json
{
  "$schema": "https://windi.systems/schemas/decision.v1.json",
  "decision_id": "UUID",
  "document_hash": "string",
  "human": {
    "isp_hash": "string",
    "session_id": "string"
  },
  "flags_presented": [
    {"rule": "R3", "severity": "MEDIUM", "description": "string"},
    {"rule": "R4", "severity": "HIGH", "description": "string"}
  ],
  "choice": {
    "type": "APPROVED | OVERRIDDEN | DEFERRED",
    "reason": "string (required if OVERRIDDEN/DEFERRED)",
    "timer_elapsed_seconds": 0,
    "timestamp_utc": "ISO8601"
  },
  "virtue_receipt": {
    "receipt_id": "UUID",
    "proof": "string"
  }
}
```

## 2.4 DocumentState (document_state.json)

```json
{
  "$schema": "https://windi.systems/schemas/document_state.v1.json",
  "states": [
    {
      "name": "DRAFT",
      "description": "Documento em edição",
      "plane": "WORKSPACE",
      "agent_mode": "FLOW",
      "transitions": ["CHECKING"]
    },
    {
      "name": "CHECKING",
      "description": "Scan de governança ativo",
      "plane": "GOVERNANCE",
      "agent_mode": "FLOW",
      "transitions": ["PENDING", "DRAFT"]
    },
    {
      "name": "PENDING",
      "description": "Aguardando decisão humana",
      "plane": "GOVERNANCE",
      "agent_mode": "ATTENTION | PAUSE",
      "transitions": ["SEALED", "DRAFT", "DEFERRED"]
    },
    {
      "name": "DEFERRED",
      "description": "Decisão adiada com timer",
      "plane": "GOVERNANCE",
      "agent_mode": "ATTENTION",
      "transitions": ["PENDING", "DRAFT"]
    },
    {
      "name": "SEALED",
      "description": "Documento selado - imutável",
      "plane": "FORENSIC",
      "agent_mode": "FLOW",
      "transitions": []
    }
  ]
}
```

---

# PARTE 3: MÁQUINA DE ESTADOS DO DOCUMENTO

```
                    ┌─────────────────────────────────────────┐
                    │                                         │
                    ▼                                         │
┌─────────┐    ┌──────────┐    ┌─────────┐    ┌────────┐     │
│  DRAFT  │───▶│ CHECKING │───▶│ PENDING │───▶│ SEALED │     │
│  (FLOW) │    │  (FLOW)  │    │(ATT/PAU)│    │ (FLOW) │     │
└─────────┘    └──────────┘    └─────────┘    └────────┘     │
     ▲              │               │                         │
     │              │               │                         │
     └──────────────┴───────────────┼─────────────────────────┘
                                    │
                                    ▼
                              ┌──────────┐
                              │ DEFERRED │
                              │  (ATT)   │
                              └──────────┘

LEGENDA:
- FLOW: Agent invisível (só ícone)
- ATT: ATTENTION - mensagem curta, opções claras
- PAU: PAUSE - modal + timer + razão obrigatória
```

---

# PARTE 4: ENDPOINTS LOCAIS

## API Local (localhost:4747)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/api/seal` | Selar documento com decisão humana |
| GET | `/api/ledger` | Consultar ledger local (append-only) |
| POST | `/api/verify` | Verificar integridade de documento |
| GET | `/api/health` | Status do clone + métricas |
| POST | `/api/decision` | Registrar decisão humana |
| GET | `/api/receipts/{doc_hash}` | Listar receipts de documento |
| POST | `/api/sync/trigger` | Forçar sync com Hub (se online) |

### POST /api/seal

```json
{
  "document_path": "/path/to/invoice.pdf",
  "decision": {
    "type": "APPROVED",
    "reason": null
  }
}
```

**Response:**
```json
{
  "proof_id": "WINDI-2026-0209-XXXX",
  "seal": {
    "qr_path": "/sealed/invoice_qr.png",
    "embedded": true
  },
  "receipts": ["ROUTE", "ACK", "SEAL"],
  "ledger_entry": 1247
}
```

---

# PARTE 5: POLÍTICAS MÍNIMAS R0-R5 (MEDIUM: FATURAS)

```yaml
# config/policies.yaml
medium: "INVOICE_B2B"
version: "0.1.0"

rules:
  R0_CREATION:
    description: "Verificação básica de criação"
    severity: LOW
    action: LOG_ONLY
    checks:
      - template_valid
      - required_fields_present

  R1_IDENTITY:
    description: "ISP do autor presente"
    severity: MEDIUM
    action: FLAG_SOFT
    checks:
      - isp_signature_valid
      - author_authenticated

  R2_INTEGRITY:
    description: "Hash e estrutura íntegros"
    severity: HIGH
    action: FLAG_HARD
    checks:
      - content_hash_valid
      - no_external_links
      - no_executable_content

  R3_COMPLIANCE:
    description: "Conformidade fiscal básica"
    severity: MEDIUM
    action: HUMAN_REVIEW
    checks:
      - tax_id_format_valid
      - amounts_consistent
      - dates_logical

  R4_ANOMALY:
    description: "Padrões anômalos detectados"
    severity: HIGH
    action: HUMAN_MANDATORY
    timer_seconds: 30
    checks:
      - unusual_amount_pattern
      - recipient_first_time
      - round_number_alert

  R5_CRITICAL:
    description: "Violação de invariante"
    severity: CRITICAL
    action: BLOCK
    checks:
      - invariant_violation
      - zk_boundary_breach
      - seal_tampering_attempt
```

---

# PARTE 6: ESTADOS DO AGENT (OBRIGATÓRIOS)

```yaml
# expression/agent_conduct.yaml
version: "1.0.0"

states:
  FLOW:
    description: "Invisível, só presença"
    ui:
      visibility: "icon_only"
      color: "subtle_green"
      interruption: "never"
    triggers:
      - document_in_draft
      - no_flags_active
      - user_in_editing

  ATTENTION:
    description: "Mensagem humana curta, opções claras"
    ui:
      visibility: "toast_notification"
      color: "amber"
      interruption: "gentle"
      max_words: 25
    triggers:
      - flag_medium_detected
      - transition_pending
      - sync_status_change
    options:
      max: 3
      style: "clear_action_buttons"

  PAUSE:
    description: "Modal obrigatório + timer + razão"
    ui:
      visibility: "modal_blocking"
      color: "red"
      interruption: "mandatory"
    triggers:
      - flag_high_detected
      - R4_R5_violation
      - override_requested
    requirements:
      timer_minimum_seconds: 30
      reason_mandatory: true
      options: ["APPROVE", "OVERRIDE", "DEFER"]

prohibitions:
  hard_blocks:
    - "Nunca suavizar R4/R5"
    - "Nunca decidir pelo humano"
    - "Nunca pedir conteúdo sensível"
    - "Nunca virar autopilot"
    - "Nunca usar linguagem impositiva"

  agent_personality:
    codename: "Sexy Burocrático"
    traits:
      - "Calmo"
      - "Humano"
      - "Direto quando precisa"
      - "Nunca alarmista"
      - "Respeita a inteligência do usuário"
```

---

# PARTE 7: PROTOCOLO SYNC CLONE ↔ HUB

```yaml
# config/hub_connection.yaml
sync_protocol:
  version: "1.0.0"
  mode: "PROOF_ONLY"  # Hub não vê documento. Hub vê integridade.

  security:
    auth: "mTLS"
    clone_cert: "/certs/clone.pem"
    clone_key: "/certs/clone.key"
    hub_ca: "/certs/hub_ca.pem"

  behavior:
    offline_first: true
    outbox_path: "/data/outbox/"
    retry_strategy: "exponential_backoff"
    max_retries: 10

  rate_limiting:
    requests_per_minute: 60
    burst_allowed: 10

  multi_tenancy:
    partition_by: "org_id"
    isolation: "strict"

  payload:
    type: "ProofEnvelope"
    includes:
      - document_hash
      - byte_ranges
      - receipts
      - decision
      - health_metrics
    excludes:
      - document_content
      - user_pii
      - raw_text
```

---

# PARTE 8: MÉTRICAS DE SUCESSO

```yaml
# Métricas objetivas - para não virar religião
metrics:
  seal_time:
    description: "Tempo para selar documento"
    variants:
      - "sem_flags"
      - "com_flags"
    target: "<5s sem flags, <30s com flags"

  defer_rate:
    description: "Taxa de decisões adiadas em R4/R5"
    interpretation: "BOA - demonstra soberania humana ativa"
    healthy_range: "10-30%"

  override_rate:
    description: "Taxa de overrides e seus motivos"
    purpose: "Aprendizado do sistema"
    tracking: "reason_categories"

  false_positive_rate:
    description: "Flags percebidas como incorretas"
    target: "<5%"
    feedback_loop: true

  flow_adherence:
    description: "Tempo em modo FLOW vs interrupções"
    target: "90% do tempo sem interrupção"
    golden_rule: "Usuário deve esquecer que está protegido"
```

---

# PARTE 9: MVP v0.1 "UMA FATURA, UM CARTÓRIO"

## Escopo Mínimo

| Componente | Implementação |
|------------|---------------|
| Editor | Fatura B2B simples |
| Flags | R3 + R4 hardcoded |
| Modal | APPROVED/OVERRIDDEN/DEFERRED + reason + timer |
| Output | PDF com selo + QR + metadados embutidos |
| Ledger | Local append-only |
| Receipts | ROUTE, ACK, SEAL |

## Objetivo

> Provar a experiência humana e o rito cartorial.
> Filosofia vira máquina.

---

## REGISTRO FORENSE

```
DOCUMENTO:    a4DESK_BLUEPRINT_v0.1.md
TIPO:         Blueprint Técnico Fundacional
DATA:         2026-02-09
VERSÃO:       0.1.0-FOUNDATION
STATUS:       ARCHITECTURAL_READY
PRÓXIMO:      Implementação do Core Imutável
```

---

*De Manifesto a Máquina. A filosofia agora executa.*
