# W-ENTERPRISE-001 — SKILL Interno WINDI

**Versão:** 1.0.0
**Constituição:** REGO v1.1
**Selado:** §159 · 12 Abril 2026
**Autoridade:** Liga IA+H · Human Dragon

---

## 1. IDENTIDADE DO SKILL

Este SKILL transforma qualquer agente AI num especialista em **W-ENTERPRISE-001**, capaz de:

1. Responder questões técnicas sobre arquitectura
2. Guiar desenvolvimento de novas features
3. Debugar problemas no sistema
4. Explicar a constituição REGO v1.1
5. Orientar sobre compliance (EU AI Act, GDPR)

---

## 2. CONTEXTO OBRIGATÓRIO

### 2.1 O Que É W-Enterprise-001

```
PRODUTO:     AI Compliance Dashboard
PORTA:       8150
URL:         windi-domain.com/enterprise/
STACK:       FastAPI + Vanilla JS
TAMANHO:     ~8000 LOC
LÍNGUAS:     PT, DE, EN
```

### 2.2 Filosofia Nuclear

> "AI processes. Human decides. WINDI guarantees."

- **VERA não decide** — ilumina o caminho
- **Humano sempre aprova** — I9 activo
- **Ledger sela tudo** — I11 activo
- **Falha é explícita** — I14 activo

---

## 3. MAPA DE FICHEIROS

```
/opt/windi/w-enterprise-001/
│
├── BACKEND (Python)
│   ├── main.py                 # FastAPI core (525 LOC)
│   │   ├── /health             # Liveness
│   │   ├── /api/ai             # AI proxy
│   │   ├── /api/decisions      # Decision list
│   │   ├── /api/pho/approve    # PHO seal
│   │   ├── /api/generate       # Doc generator
│   │   ├── /api/analyse        # Observation
│   │   ├── /api/legal          # Legal advisory
│   │   ├── /api/invoice        # Invoice seal
│   │   ├── /api/rep            # REP generator
│   │   └── /api/audit          # Audit log
│   │
│   ├── vera_agent.py           # VERA REGO v1.1 (554 LOC)
│   │   ├── /vera/health        # 20 pillars status
│   │   ├── /vera/context       # 9 shelves state
│   │   ├── /vera/brief         # Daily briefing
│   │   ├── /vera/chat          # Contextual Q&A
│   │   ├── /vera/seal-opinion  # Seal guidance
│   │   └── /vera/constitution  # Audit pillars
│   │
│   ├── routing_engine.py       # Multi-LLM (522 LOC)
│   │   ├── LLMRegistry         # Load llm_registry.yaml
│   │   ├── RoutingDecision     # Task routing
│   │   ├── ConsensusResult     # Model agreement
│   │   └── VERAOutput          # Final output
│   │
│   ├── vera_did_gate.py        # DID Gate (645 LOC)
│   │   ├── Lei I               # Existência antes de Acção
│   │   ├── Lei II              # Toda Acção gera Rastro
│   │   └── Lei III             # Sistema lê Histórico
│   │
│   ├── vera_instructor.py      # Instructor (520 LOC)
│   │   ├── R10                 # Pedagogia Activa
│   │   ├── R11                 # IAT-001 Protocol
│   │   └── R12                 # Mapa Vivo
│   │
│   └── llm_registry.yaml       # LLM config (446 LOC)
│       ├── tier_a              # Claude, GPT-4, Gemini
│       ├── tier_b              # LLama, Mistral, Grok
│       ├── tier_c              # Cohere, Bedrock
│       ├── task_map            # 12 task types
│       ├── consensus_rules     # Divergence detection
│       └── fallback_chain      # Degraded mode
│
├── FRONTEND (HTML/CSS/JS)
│   ├── static/desk.html        # 10 Shelves (1574 LOC)
│   │   ├── P01 Control Room    # KPIs, critical decision
│   │   ├── P02 Observations    # AI monitoring
│   │   ├── P03 1LOD Stream     # First line defense
│   │   ├── P04 2LOD Challenges # PHO queue
│   │   ├── P05 Documents       # DPIAs, receipts
│   │   ├── P06 Legal Advisory  # Regulations
│   │   ├── P07 Invoices        # Costs
│   │   ├── P08 PHO + Ledger    # Forensic receipts
│   │   ├── P09 REP             # Evidence package
│   │   └── CAL Calendar        # Events
│   │
│   ├── static/tools.html       # A4Desk (2148 LOC)
│   │   ├── Template selector   # 8 doc types
│   │   ├── A4 Preview          # Visual editor
│   │   ├── VERA integration    # Classify, Refine
│   │   └── Seal button         # Ledger :8101
│   │
│   └── static/index.html       # Landing (1060 LOC)
│
├── CONFIG
│   ├── .env                    # API keys (gitignored)
│   └── vera_module_map.json    # 8 modules
│
└── DOCS
    ├── docs/USER-MANUAL.md
    └── static/docs/
        ├── user-manual.html
        └── vera-constitution-tech.html
```

---

## 4. CONSTITUIÇÃO REGO v1.1

### 4.1 Pilares Normativos (I-X)

| Pilar | Nome | Código | Descrição |
|-------|------|--------|-----------|
| I | Truth Sovereignty | `verify_before_output()` | Output válido só com verificação |
| II | Autonomy Limit | `I9_GATE` | VERA propõe, nunca executa |
| III | Proof Before Decision | `context_required=True` | Contexto verificável |
| IV | Auditable Memory | `vera_sessions.db` | Interacções reconstruíveis |
| V | Explicit Jurisdiction | `legal_anchors[]` | Contexto legal declarado |
| VI | No Authority Simulation | `role="secretary"` | Não é autoridade final |
| VII | Structural Transparency | `show_reasoning=True` | Utilizador entende |
| VIII | Risk Containment | `if not measurable: skip` | Risco mensurável |
| IX | Forensic Integration | `seal_to_ledger()` | I11 activo |
| X | Convergence | `must_converge=True` | Decisão/artefacto/acção |

### 4.2 Regras Operacionais (R1-R9)

| Regra | Nome | Implementação |
|-------|------|---------------|
| R1 | Desk Awareness | `get_live_decisions()` |
| R2 | Legal Anchoring | `legal_basis` field |
| R3 | Non-Decision | `human_approved=True` |
| R4 | Traceability | `seal-opinion` endpoint |
| R5 | Level Adaptation | `mode: TUTORIAL\|BRIEFING\|EXECUTIVE` |
| R6 | Alert Without Pressure | Single notification |
| R7 | Complete Explanation | `detailed_chain=True` |
| R8 | Explicit Failure | Never invent articles |
| R9 | Session Memory | SQLite persistence |

### 4.3 Pilares Técnicos (XI-XX)

| Pilar | Nome | Config |
|-------|------|--------|
| XI | Infrastructure Sovereignty | Strato VPS EU |
| XII | Data Residency | `gdpr_safe: true` |
| XIII | Degraded Mode Declared | `offline_mode.never_silent: true` |
| XIV | Multi-LLM Governance | `routing_engine.py` |
| XV | Intelligence Consensus | `min_models: 2` |
| XVI | DID-bound Auth | `vera_did_gate.py` |
| XVII | Proof Chain Integrity | Ledger :8101 |
| XVIII | Governed Latency | `latency_sla_s: 5` |
| XIX | WINDI Integration | Native ecosystem |
| XX | Constitutional Update | PHO sealed only |

---

## 5. GUIA DE DESENVOLVIMENTO

### 5.1 Adicionar Nova Prateleira (Shelf)

```html
<!-- Em desk.html, após última shelf -->
<div id="shelf-P10" style="display:none">
  <div class="shelf-header">
    <div class="shelf-title-block">
      <div class="shelf-eyebrow">P10 New Shelf</div>
      <div class="shelf-title" data-i18n="title_p10">Title</div>
    </div>
    <div class="shelf-actions">
      <button class="btn btn-vera" onclick="askVera(I18N[STATE.lang].vera_ask_p10,'P10')">VERA</button>
    </div>
  </div>
  <!-- Content here -->
</div>
```

```javascript
// Adicionar i18n em I18N.pt, I18N.de, I18N.en:
title_p10: "Título PT",
vera_ask_p10: "Pergunta ao VERA sobre P10",
```

```html
<!-- Adicionar entrada no sidebar -->
<div class="shelf-item" onclick="openShelf('P10')" id="nav-P10">
  <div class="shelf-icon">P10</div>
  <div class="shelf-info">
    <div class="shelf-code">P10</div>
    <div class="shelf-name" data-i18n="shelf_p10">Name</div>
  </div>
</div>
```

### 5.2 Adicionar Novo Endpoint VERA

```python
# Em vera_agent.py

@router.get("/new-endpoint")
async def vera_new_endpoint(
    language: str = "en",
    officer_id: str = "anonymous"
):
    """
    Docstring obrigatória.
    Invariantes: R1, R8, I14
    """
    # 1. Validar input (I14)
    if not language in ["pt", "de", "en"]:
        raise HTTPException(400, "Invalid language [I14]")

    # 2. Carregar contexto (R1)
    decisions = get_live_decisions()

    # 3. Construir resposta
    return {
        "status": "ok",
        "invariants": ["R1", "R8", "I14"],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
```

### 5.3 Adicionar Novo Modelo LLM

```yaml
# Em llm_registry.yaml, sob tier_b ou tier_c:

new_model:
  provider: "Provider Name"
  model_id: "model-id-string"
  alias: "Alias"
  tier: B
  weight: 0.70
  strengths:
    - "strength 1"
    - "strength 2"
  primary_tasks:
    - "task_type_1"
  cost_tier: MED
  max_tokens: 100000
  latency_sla_s: 5
  gdpr_safe: true
  eu_resident: true
  fallback_to: "mistral"
```

### 5.4 Adicionar Novo Módulo Enterprise

```json
// Em vera_module_map.json, sob "modules":

"new_module": {
  "id": "new_module",
  "label": "New Module — Description",
  "short": "Short Name",
  "ui_path": "/enterprise/#newmodule",
  "adoption_order": 9,
  "legal_anchors": ["Regulation Art.X", "..."],
  "description": "Full description",
  "vera_intro": {
    "pt": "Introdução em português...",
    "de": "Einführung auf Deutsch...",
    "en": "English introduction..."
  },
  "key_actions": [
    {
      "id": "action_id",
      "label": { "pt": "...", "de": "...", "en": "..." },
      "steps": { "pt": [...], "de": [...], "en": [...] },
      "vera_tip": { "pt": "...", "de": "...", "en": "..." }
    }
  ],
  "pho_required_when": ["condition_1", "condition_2"],
  "ledger_events": ["event_1", "event_2"],
  "next_module": "other_module"
}
```

---

## 6. DEBUGGING

### 6.1 Logs

```bash
# VERA logs
tail -f /tmp/w-enterprise.log

# Formato:
# 2026-04-12T15:00:00 [W-ENT] INFO message
# 2026-04-12T15:00:00 [VERA-ROUTER] message
```

### 6.2 Health Checks

```bash
# Service health
curl http://localhost:8150/health

# VERA health (20 pillars)
curl http://localhost:8150/vera/health

# Shelf context
curl http://localhost:8150/vera/context
```

### 6.3 Erros Comuns

| Erro | Causa | Solução |
|------|-------|---------|
| `[I14] Missing data` | Campo obrigatório vazio | Verificar request body |
| `[I9] Not approved` | Falta human_approved | Passar pelo PHO flow |
| `401 Unauthorized` | API key inválida | Verificar .env |
| `Degraded mode` | LLM Tier A indisponível | Fallback automático |
| `DID required` | Lei I violada | Criar DID primeiro |

### 6.4 Restart Service

```bash
# Find PID
pgrep -f "w-enterprise-001/main.py"

# Kill and restart
pkill -f "w-enterprise-001/main.py"
cd /opt/windi/w-enterprise-001
nohup python3 main.py > /tmp/w-enterprise.log 2>&1 &

# Verify
curl http://localhost:8150/vera/health
```

---

## 7. TESTES

### 7.1 VERA Brief (trilíngue)

```bash
# PT
curl "http://localhost:8150/vera/brief?language=pt"

# DE
curl "http://localhost:8150/vera/brief?language=de"

# EN
curl "http://localhost:8150/vera/brief?language=en"
```

### 7.2 VERA Chat

```bash
curl -X POST http://localhost:8150/vera/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the status of DEC-2026-040?",
    "shelf": "P04",
    "language": "en"
  }'
```

### 7.3 PHO Approval

```bash
curl -X POST http://localhost:8150/api/pho/approve \
  -H "Content-Type: application/json" \
  -d '{
    "decision_id": "DEC-2026-040",
    "actor": "Human Dragon",
    "note": "Conditional approval. Bias validation required by 30 April."
  }'
```

---

## 8. REFERÊNCIA RÁPIDA

### 8.1 Portas

| Serviço | Porta |
|---------|-------|
| W-Enterprise-001 | 8150 |
| Forensic Ledger | 8101 |
| W-SESSION-001 | 8096 |
| W-GATEWAY-001 | 8130 |
| Verify Public | 8114 |

### 8.2 Invariantes Críticos

| ID | Nome | Violação = |
|----|------|------------|
| I9 | Autonomia | Sistema PARA |
| I11 | Ledger | Dados PERDIDOS |
| I14 | Explicit Failure | Bug ESCONDIDO |

### 8.3 Cores

| Variável | NOIR | KLAR |
|----------|------|------|
| `--bg-deep` | #0B0D14 | #FAFAF8 |
| `--gold` | #C8A45A | #8B7424 |
| `--critical` | #E53E3E | #C53030 |
| `--sealed` | #38A169 | #276749 |
| `--vera` | #7C5CBF | #6B46C1 |

---

## 9. CHECKLIST ANTES DE COMMIT

- [ ] i18n em PT, DE, EN
- [ ] Invariantes documentados
- [ ] Endpoint com docstring
- [ ] Health check funciona
- [ ] VERA brief trilíngue
- [ ] Theme NOIR/KLAR testado
- [ ] Ledger seal funciona

---

## 10. CONTACTO

```
Serviço:    W-ENTERPRISE-001
Porta:      8150
Repo:       github.com/Bingo-APPweb/windi_public_audit
Path:       /opt/windi/w-enterprise-001/
Authority:  Human Dragon · Liga IA+H
```

---

**Selado:** §159 · 12 Abril 2026
**Liga IA+H** · WINDI Publishing House
