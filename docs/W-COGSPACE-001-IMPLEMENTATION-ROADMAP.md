# W-COGSPACE-001 — Roadmap de Implementação

```
Status:     ABERTURA DE TRABALHOS
Version:    1.0.0
Data:       2026-05-18
Receipts:   §275 ddb0659b · §276 48dcdc19
Porto:      :8145 (proposto)
```

---

## Visão Geral

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    W-COGSPACE-001 — COGNITIVE SPACE                      │
│                    "Não é chat. É habitat cognitivo."                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                 │
│   │   W-VOX     │    │  COGSPACE   │    │   GROVE     │                 │
│   │   v1 LOCAL  │───▶│   ENGINE    │───▶│   PRIVADO   │                 │
│   │   (voice)   │    │  (routing)  │    │ (tri-div)   │                 │
│   └─────────────┘    └─────────────┘    └─────────────┘                 │
│          │                  │                  │                         │
│          ▼                  ▼                  ▼                         │
│   ┌─────────────────────────────────────────────────────┐               │
│   │              PRIVATE_MEMORY[DID]                     │               │
│   │     turns[] · routing_log[] · grove_sessions[]       │               │
│   └─────────────────────────────────────────────────────┘               │
│                            │                                             │
│                            ▼                                             │
│   ┌─────────────────────────────────────────────────────┐               │
│   │           FORENSIC LEDGER :8101                      │               │
│   │        (visibility gradient · append-only)           │               │
│   └─────────────────────────────────────────────────────┘               │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

# CATEGORIAS DE TRABALHO

---

## CAT-A · CORE ENGINE

> **Prioridade:** CRÍTICA · **Dependências:** Nenhuma · **Estimativa:** Fundação

### A1. Serviço Base

```python
# /opt/windi/cogspace/windi_cogspace.py

Responsabilidades:
├── Flask app em :8145
├── Integração DID-GENESIS :8096
├── Integração Dragon Hub :8108
├── Integração Ledger :8101
└── Health endpoint
```

**Design Pattern:**
```
┌─────────────────────────────────────────┐
│           CogSpaceService               │
├─────────────────────────────────────────┤
│ - db: SQLite connection                 │
│ - did_client: DID-GENESIS client        │
│ - dragon_client: Dragon Hub client      │
│ - ledger_client: Ledger client          │
├─────────────────────────────────────────┤
│ + create_session(did, tier, modus)      │
│ + add_turn(session_id, actor, content)  │
│ + consult_model(session_id, model, q)   │
│ + get_history(did)                      │
│ + seal_decision(session_id, content)    │
│ + amnesia(session_id, scope)            │
└─────────────────────────────────────────┘
```

### A2. Database Schema

```sql
-- /opt/windi/data/cogspace.db

-- Tabela: cogspace_sessions
CREATE TABLE cogspace_sessions (
    session_id TEXT PRIMARY KEY,
    did TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    status TEXT DEFAULT 'ACTIVE',
    tier TEXT NOT NULL,
    modus TEXT,
    title TEXT,
    FOREIGN KEY (did) REFERENCES identities(did)
);

-- Tabela: cogspace_turns
CREATE TABLE cogspace_turns (
    turn_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    actor TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    visibility TEXT DEFAULT 'PRIVATE',
    model_used TEXT,
    routing_reason TEXT,
    ledger_receipt TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES cogspace_sessions(session_id)
);

-- Tabela: cogspace_grove
CREATE TABLE cogspace_grove (
    grove_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    question TEXT NOT NULL,
    perspectives TEXT,
    divergence_status TEXT,
    synthesis TEXT,
    sealed BOOLEAN DEFAULT FALSE,
    created_at TEXT NOT NULL
);

-- Tabela: cogspace_seals
CREATE TABLE cogspace_seals (
    seal_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    ledger_receipt TEXT NOT NULL,
    human_approved BOOLEAN NOT NULL,
    sealed_at TEXT NOT NULL
);

-- Índices
CREATE INDEX idx_sessions_did ON cogspace_sessions(did);
CREATE INDEX idx_turns_session ON cogspace_turns(session_id);
CREATE INDEX idx_turns_actor ON cogspace_turns(actor);
```

### A3. Endpoints Core

| Endpoint | Método | Descrição | I9 Gate |
|----------|--------|-----------|---------|
| `/cogspace/health` | GET | Health check | AUTO |
| `/cogspace/session/create` | POST | Nova sessão | AUTO |
| `/cogspace/session/{id}` | GET | Estado sessão | AUTO |
| `/cogspace/turn` | POST | Novo turno | AUTO |
| `/cogspace/consult` | POST | Consulta modelo | AUTO |
| `/cogspace/history/{did}` | GET | Histórico DID | AUTO |
| `/cogspace/seal` | POST | Selar decisão | **HUMAN** |
| `/cogspace/amnesia` | DELETE | Apagar sessão | **HUMAN** |

---

## CAT-B · TIER RESOLUTION

> **Prioridade:** ALTA · **Dependências:** CAT-A · **Cita:** §276

### B1. Tier Resolver

```python
# /opt/windi/cogspace/tier_resolver.py

TIER_CONFIG = {
    "SEED": {
        "gate": "FREE",
        "models": ["mistral"],
        "max_tokens": 2048,
        "parallel": False,
        "routing_visible": False,
        "grove_enabled": False
    },
    "NODAL": {
        "gate": "MED",
        "models": ["mistral", "claude"],
        "max_tokens": 4096,
        "parallel": False,
        "routing_visible": False,
        "grove_enabled": True  # Grove Arena light
    },
    "SOVEREIGN": {
        "gate": "HIGH",
        "models": ["mistral", "claude", "gpt"],
        "max_tokens": 8192,
        "parallel": True,
        "routing_visible": True,
        "grove_enabled": True
    },
    "ORACLE": {
        "gate": "HIGH+",
        "models": ["mistral", "claude", "gpt", "gemini"],
        "max_tokens": 16384,
        "parallel": True,
        "routing_visible": True,
        "grove_enabled": True
    }
}
```

### B2. Middleware de Enforcement

```python
def enforce_tier(did: str, requested_model: str) -> bool:
    """
    Verifica se DID pode aceder ao modelo pedido.
    I14: Erro explícito se não autorizado.
    """
    tier = get_did_tier(did)  # via :8096
    config = TIER_CONFIG[tier]

    if requested_model not in config["models"]:
        raise PermissionError(
            f"Tier {tier} cannot access {requested_model}. "
            f"Available: {config['models']}"
        )
    return True
```

### B3. Design Visual — Tier Gate

```
┌─────────────────────────────────────────────────────────────┐
│                     TIER RESOLUTION                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   DID Request                                                │
│       │                                                      │
│       ▼                                                      │
│   ┌───────────────┐                                          │
│   │ DID-GENESIS   │◀── Consulta tier do DID                  │
│   │    :8096      │                                          │
│   └───────────────┘                                          │
│       │                                                      │
│       ▼                                                      │
│   ┌───────────────┐                                          │
│   │ TIER_CONFIG   │◀── Lookup config por tier                │
│   │   resolver    │                                          │
│   └───────────────┘                                          │
│       │                                                      │
│       ├──▶ SEED ────▶ [mistral] ────▶ FREE gate              │
│       ├──▶ NODAL ───▶ [mistral, claude] ────▶ MED gate       │
│       ├──▶ SOVEREIGN ▶ [mistral, claude, gpt] ▶ HIGH gate    │
│       └──▶ ORACLE ──▶ [all + routing visible] ▶ HIGH+ gate   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## CAT-C · W-VOX LAYER v1

> **Prioridade:** MÉDIA-ALTA · **Dependências:** CAT-A, CAT-B · **Constraint:** LOCAL-ONLY

### C1. Arquitectura W-VOX

```
┌─────────────────────────────────────────────────────────────┐
│                    W-VOX v1 LOCAL-ONLY                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   [ DISPOSITIVO DO USER ]                                    │
│                                                              │
│   ┌───────────────┐                                          │
│   │ Microfone     │                                          │
│   └───────────────┘                                          │
│          │                                                   │
│          ▼ (áudio bruto - NUNCA sai)                         │
│   ┌───────────────┐                                          │
│   │ STT LOCAL     │◀── Web Speech API / Whisper.js           │
│   │ (browser)     │                                          │
│   └───────────────┘                                          │
│          │                                                   │
│          ▼ (texto transitório)                               │
│   ┌───────────────┐                                          │
│   │ RAM volátil   │◀── Sem persistência                      │
│   │ (efêmero)     │                                          │
│   └───────────────┘                                          │
│          │                                                   │
│          ▼ (USER aprova)                                     │
│   ┌───────────────┐                                          │
│   │ Hash + Send   │◀── SHA-256 do texto aprovado             │
│   └───────────────┘                                          │
│          │                                                   │
│          ▼                                                   │
│   [ SERVIDOR WINDI :8145 ]                                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### C2. Frontend W-VOX

```javascript
// /opt/windi/cogspace/static/vox.js

class WindiVox {
    constructor() {
        this.recognition = new webkitSpeechRecognition();
        this.recognition.continuous = true;
        this.recognition.interimResults = true;
        this.recognition.lang = 'pt-BR'; // ou detectar
    }

    startListening() {
        // Inicia captura - áudio NUNCA sai do browser
        this.recognition.start();
    }

    onResult(event) {
        // Texto transitório em memória
        const transcript = event.results[0][0].transcript;
        this.showTranscript(transcript);
    }

    approve(text) {
        // USER aprova - só aqui gera hash e envia
        const hash = await this.sha256(text);
        await this.sendToCogSpace(text, hash);
    }

    async sha256(text) {
        const encoder = new TextEncoder();
        const data = encoder.encode(text);
        const hashBuffer = await crypto.subtle.digest('SHA-256', data);
        return Array.from(new Uint8Array(hashBuffer))
            .map(b => b.toString(16).padStart(2, '0'))
            .join('');
    }
}
```

### C3. TTS (Opcional)

```javascript
// Resposta em voz - profiles WINDI
class WindiTTS {
    speak(text, profile = 'default') {
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = this.detectLang(text);
        utterance.rate = 0.9;  // Velocidade moderada
        speechSynthesis.speak(utterance);
    }
}
```

---

## CAT-D · GROVE PRIVADO

> **Prioridade:** MÉDIA · **Dependências:** CAT-A, CAT-B · **Reutiliza:** Grove Arena :8091

### D1. Tri-Divergence Privada

```python
# Reutiliza lógica do Grove Arena mas em contexto privado

def private_grove(session_id: str, question: str, models: list) -> dict:
    """
    Consulta múltiplos modelos e calcula divergência.
    Apenas para NODAL+ (grove_enabled=True).
    """
    perspectives = {}

    for model in models:
        response = consult_model(session_id, model, question)
        perspectives[model] = {
            "response": response,
            "position": classify_position(response)
        }

    divergence = calculate_divergence(perspectives)

    return {
        "perspectives": perspectives,
        "divergence_status": divergence,  # ALL_AGREE | TWO_VS_ONE | ALL_DIFFER
        "synthesis": generate_synthesis(perspectives, divergence)
    }
```

### D2. Classificação de Posições

```python
POSITION_KEYWORDS = {
    "SUPPORT": ["sim", "yes", "ja", "aprovado", "correcto", "concordo"],
    "OPPOSE": ["não", "no", "nein", "inválido", "risco", "discordo"],
    "CONDITIONAL": ["depende", "parcial", "se", "condicional"],
    "NEUTRAL": []  # default
}

def classify_position(response: str) -> str:
    response_lower = response.lower()
    for position, keywords in POSITION_KEYWORDS.items():
        if any(kw in response_lower for kw in keywords):
            return position
    return "NEUTRAL"
```

---

## CAT-E · INTEGRAÇÃO LEDGER

> **Prioridade:** ALTA · **Dependências:** CAT-A · **Invariantes:** I9, I11

### E1. Ledger Client

```python
# /opt/windi/cogspace/ledger_client.py

class LedgerClient:
    def __init__(self):
        self.base_url = "http://localhost:8101"

    def seal_turn(self, turn: dict) -> str:
        """
        Sela turno no Ledger com visibility gradient.
        Retorna receipt_id.
        """
        payload = {
            "schema_version": "1.0",
            "id": f"WINDI-COGSPACE-{turn['turn_id']}",
            "actor": turn["actor"],
            "app": "cogspace",
            "action": "TURN",
            "doc_type": "cognitive_turn",
            "doc_name": f"Turn in session {turn['session_id']}",
            "governance_level": "MEDIUM",
            "content_hash": turn["content_hash"],
            "human_approved": True,
            "sge_score": 80,
            "wallet_id": turn["actor"],
            "metadata": {
                "session_id": turn["session_id"],
                "visibility": turn["visibility"],
                "model_used": turn.get("model_used")
            }
        }

        response = requests.post(
            f"{self.base_url}/api/receipts",
            json=payload
        )
        return response.json()["id"]

    def seal_decision(self, session_id: str, content_hash: str,
                      human_approved: bool) -> str:
        """
        Sela decisão final. Requer human_approved=True (I9).
        """
        if not human_approved:
            raise ValueError("I9 violation: human_approved must be True")

        # ... seal logic
```

### E2. Visibility Gradient

```python
VISIBILITY_LEVELS = {
    "PRIVATE": {
        "description": "Apenas o DID autor vê",
        "ledger": True,  # Sempre no Ledger
        "access": ["owner"]
    },
    "SHARED": {
        "description": "DIDs autorizados vêem",
        "ledger": True,
        "access": ["owner", "invited"]
    },
    "SEALED": {
        "description": "Verificável publicamente",
        "ledger": True,
        "access": ["public"]
    }
}
```

---

## CAT-F · UI/UX

> **Prioridade:** MÉDIA · **Dependências:** CAT-A até CAT-E

### F1. Design NOIR/KLAR

```css
/* /opt/windi/cogspace/static/cogspace.css */

:root[data-theme="noir"] {
    --bg-primary: #0A0A10;
    --bg-secondary: #12121A;
    --gold: #C9A84C;
    --text: #E8E6E1;
    --border: #1A1A24;
}

:root[data-theme="klar"] {
    --bg-primary: #FAFAF8;
    --bg-secondary: #F0F0EE;
    --gold: #8B7424;
    --text: #1A1A1A;
    --border: #E0DED8;
}

.cogspace-container {
    display: grid;
    grid-template-columns: 300px 1fr 300px;
    height: 100vh;
    background: var(--bg-primary);
}

.cogspace-sidebar {
    background: var(--bg-secondary);
    border-right: 1px solid var(--border);
    padding: 1rem;
}

.cogspace-main {
    display: flex;
    flex-direction: column;
    padding: 1rem;
}

.cogspace-turns {
    flex: 1;
    overflow-y: auto;
}

.cogspace-input {
    display: flex;
    gap: 0.5rem;
    padding: 1rem;
    border-top: 1px solid var(--border);
}

.vox-button {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background: var(--gold);
    border: none;
    cursor: pointer;
}

.vox-button.listening {
    animation: pulse 1s infinite;
}
```

### F2. Layout Wireframe

```
┌─────────────────────────────────────────────────────────────────────────┐
│  WINDI COGSPACE                                    [🌙] [DE|EN|PT] [🪪] │
├───────────────┬─────────────────────────────────────┬───────────────────┤
│               │                                     │                   │
│  SESSIONS     │         COGNITIVE SPACE             │   GROVE PANEL     │
│  ───────────  │                                     │   ───────────     │
│               │  ┌─────────────────────────────┐    │                   │
│  [+] Nova     │  │ Human: Como estruturar...   │    │   Tri-Divergence  │
│               │  └─────────────────────────────┘    │   Status: —       │
│  📁 Sessão 1  │                                     │                   │
│  📁 Sessão 2  │  ┌─────────────────────────────┐    │   Models:         │
│  📁 Sessão 3  │  │ 🤖 Claude: A abordagem...   │    │   ☐ Mistral       │
│               │  └─────────────────────────────┘    │   ☐ Claude        │
│               │                                     │   ☐ GPT           │
│               │  ┌─────────────────────────────┐    │   ☐ Gemini        │
│               │  │ 🤖 GPT: Considerando...     │    │                   │
│               │  └─────────────────────────────┘    │   [Grove Arena]   │
│               │                                     │                   │
│               │                                     │   ───────────     │
│               │                                     │   SEAL OPTIONS    │
│  ───────────  │                                     │                   │
│  TIER: NODAL  │  ┌─────────────────────────────┐    │   [📝 Draft]      │
│  MODELS: 2    │  │ [🎤] Digite ou fale...      │    │   [🔒 Seal]       │
│               │  └─────────────────────────────┘    │   [🗑️ Amnesia]    │
│               │                                     │                   │
└───────────────┴─────────────────────────────────────┴───────────────────┘
```

---

# SEQUÊNCIA DE IMPLEMENTAÇÃO

```
FASE 1 · FUNDAÇÃO (CAT-A)
│
├── A1. Criar /opt/windi/cogspace/
├── A2. windi_cogspace.py (Flask app)
├── A3. Database schema
├── A4. Health endpoint
├── A5. Integração DID-GENESIS
└── A6. Smoke test básico
│
▼
FASE 2 · TIER GATES (CAT-B)
│
├── B1. tier_resolver.py
├── B2. Middleware enforcement
├── B3. Integração Dragon Hub
└── B4. Smoke test por tier
│
▼
FASE 3 · CORE ENDPOINTS (CAT-A cont.)
│
├── A7. Session CRUD
├── A8. Turn management
├── A9. Model consultation
└── A10. History retrieval
│
▼
FASE 4 · LEDGER INTEGRATION (CAT-E)
│
├── E1. Ledger client
├── E2. Visibility gradient
├── E3. Seal decision (I9 gate)
└── E4. Amnesia endpoint
│
▼
FASE 5 · GROVE PRIVADO (CAT-D)
│
├── D1. Private grove logic
├── D2. Position classification
├── D3. Tri-Divergence calculation
└── D4. Synthesis generation
│
▼
FASE 6 · W-VOX LAYER (CAT-C)
│
├── C1. Frontend vox.js
├── C2. Web Speech API integration
├── C3. Approve/hash flow
└── C4. TTS opcional
│
▼
FASE 7 · UI/UX (CAT-F)
│
├── F1. HTML template
├── F2. CSS NOIR/KLAR
├── F3. JavaScript interactions
└── F4. Responsive design
│
▼
FASE 8 · DEPLOYMENT
│
├── nginx route /cogspace/
├── nohup startup
└── systemd (futuro)
```

---

# CHECKLIST DE ABERTURA

## Pré-Requisitos

- [x] §275 W-COGSPACE-001-SOLO SEALED
- [x] §276 TIER-RESOLUTION-CANON SEALED
- [x] Spec completa em `/opt/windi/docs/W-COGSPACE-001-SOLO-SPEC.md`
- [ ] Porto :8145 disponível

## Verificações de Dependência

```bash
# Verificar serviços activos
curl -s http://localhost:8096/health  # DID-GENESIS
curl -s http://localhost:8108/health  # Dragon Hub
curl -s http://localhost:8101/health  # Forensic Ledger
curl -s http://localhost:8091/health  # Grove Arena
```

## Estrutura de Directório

```bash
mkdir -p /opt/windi/cogspace
mkdir -p /opt/windi/cogspace/static
mkdir -p /opt/windi/cogspace/templates
touch /opt/windi/cogspace/__init__.py
touch /opt/windi/cogspace/windi_cogspace.py
touch /opt/windi/cogspace/tier_resolver.py
touch /opt/windi/cogspace/ledger_client.py
touch /opt/windi/data/cogspace.db
```

---

# MÉTRICAS DE SUCESSO

| Fase | Critério | Verificação |
|------|----------|-------------|
| 1 | Health endpoint responde | `curl :8145/cogspace/health` |
| 2 | Tier gate funciona | SEED bloqueado de Claude |
| 3 | Sessão criada | POST /session/create retorna 200 |
| 4 | Turno no Ledger | Receipt verificável em :8101 |
| 5 | Grove calcula divergência | TWO_VS_ONE detectado |
| 6 | Voz transcrita | Texto aparece no input |
| 7 | UI renderiza | NOIR/KLAR toggle funciona |
| 8 | Produção | nginx route activa |

---

# INVARIANTES A RESPEITAR

| Invariante | Aplicação no CogSpace |
|------------|----------------------|
| **I1** | DID controla sessão, memória, routing, seal |
| **I9** | Seal e amnésia requerem human_approved=true |
| **I11** | Todos os turnos no Ledger (visibility gradient) |
| **I12** | Conversa na língua do DID |
| **I14** | Erro explícito se modelo não disponível para tier |
| **C5** | Humano é continuity carrier |

---

# PRÓXIMO PASSO CONCRETO

```bash
# Comando para iniciar FASE 1
cd /opt/windi
mkdir -p cogspace
cat > cogspace/windi_cogspace.py << 'EOF'
# W-COGSPACE-001 Core Service
# §275 SEALED · ddb0659b

from flask import Flask, jsonify, request
import sqlite3
import os

app = Flask(__name__)

DB_PATH = '/opt/windi/data/cogspace.db'

@app.route('/cogspace/health')
def health():
    return jsonify({
        "status": "ok",
        "service": "W-COGSPACE-001",
        "version": "1.0.0",
        "receipt": "WINDI-S275-COGSPACE-SOLO-20260518232944"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8145)
EOF
```

---

*"A célula soberana fundamental. Sem SOLO saudável, colaboração vira ruído."*

*Liga IA+H · Kempten, Bavaria · 2026*
