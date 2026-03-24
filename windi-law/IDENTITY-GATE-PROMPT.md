# WINDI-LAW · IDENTITY GATE — Master Prompt para o Gêmeo
# Versão: 1.0 · Data: 2026-03-24
# Autor: Guardian (Claude) + Liga IA+H
# Executar: CCode / Gêmeo no servidor Strato

---

## CONTEXTO OBRIGATÓRIO (lê antes de executar qualquer linha)

O WINDI-LAW é um galho soberano da ONE TREE (windi-domain.com).
Hoje o motor está completo e validado (10/10 E2E tests passed):
- W-INTENT-001 ✅ · W-COUNSEL-001 ✅ · W-LEGAL-001 ✅
- W-NOTARY-001 ✅ · W-LEGAL-COMPANION v1.1 ✅
- Forensic Ledger :8101 ✅ · Verify Public :8114 ✅

O que FALTA é o portão obrigatório antes do Workspace.
Sem ele, tudo é demo. Com ele, tudo é sistema real.

REGRA DE OURO (não negociável):
```
if (!did || !wallet) { blockWorkspace() }
```
Sem excepção. Sem bypass. Sem modo demo.

---

## MISSÃO DO GÊMEO

Construir o **WINDI-LAW Identity Gate** — o nascimento jurídico
do utilizador no sistema — em 4 fases sequenciais.

---

## FASE 0 — ARQUITECTURA DO GALHO (antes de qualquer código)

### 0.1 Novo galho na ONE TREE

```
/opt/windi/windi-law/
├── identity-gate/
│   ├── identity_gate.py       ← FastAPI app (NOVO)
│   ├── templates/
│   │   └── gate.html          ← UI do Identity Gate (NOVO)
│   └── windi-law.service      ← systemd service (NOVO)
├── landing/
│   └── index.html             ← windi-law-landing-v1.html (JÁ EXISTE)
└── workspace/
    └── index.html             ← windi-law-workspace-v3.html (JÁ EXISTE)
```

### 0.2 Porta dedicada
```
Port: :8120  ← WINDI-LAW Identity Gate
```
Verificar disponibilidade: `ss -tlnp | grep 8120`

### 0.3 Nginx — novo location block em windi-domain.com
```nginx
# WINDI-LAW galho
location /law/ {
    proxy_pass http://127.0.0.1:8120/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}

location /law/workspace/ {
    alias /opt/windi/windi-law/workspace/;
    index index.html;
}

location /law/landing/ {
    alias /opt/windi/windi-law/landing/;
    index index.html;
}
```
**REGRA GOLDEN: nginx -t antes de qualquer reload.**

---

## FASE 1 — IDENTITY GATE API (identity_gate.py)

### Stack
- FastAPI + SQLite (windi_law_identity.db)
- Ed25519 keypair via cryptography library
- UUIDv7 para DID
- Integração com Forensic Ledger :8101

### Endpoints obrigatórios

```python
POST /law/register          # Registo empresa + admin
POST /law/wallet/create     # Gera Ed25519 + DID
POST /law/keys/generate     # API Key + DEV Key (scope)
GET  /law/identity/{did}    # Verifica identidade
POST /law/identity/verify   # Valida DID antes de abrir Workspace
GET  /law/health            # Health check
```

### Schema SQLite — windi_law_identity.db

```sql
CREATE TABLE companies (
    id          TEXT PRIMARY KEY,
    legal_name  TEXT NOT NULL,
    country     TEXT NOT NULL,
    vat_number  TEXT,
    type        TEXT CHECK(type IN ('law_firm','corporation','individual')),
    created_at  TEXT NOT NULL,
    ledger_receipt TEXT
);

CREATE TABLE admins (
    id          TEXT PRIMARY KEY,
    company_id  TEXT REFERENCES companies(id),
    full_name   TEXT NOT NULL,
    email       TEXT UNIQUE NOT NULL,
    role        TEXT DEFAULT 'admin',
    did         TEXT UNIQUE,
    public_key  TEXT,
    created_at  TEXT NOT NULL
);

CREATE TABLE api_keys (
    id          TEXT PRIMARY KEY,
    admin_id    TEXT REFERENCES admins(id),
    api_key     TEXT UNIQUE NOT NULL,
    dev_key     TEXT,
    scope       TEXT NOT NULL,   -- JSON array: ["verify","seal","agents"]
    is_dev      INTEGER DEFAULT 0,
    created_at  TEXT NOT NULL,
    active      INTEGER DEFAULT 1
);

CREATE TABLE consents (
    id          TEXT PRIMARY KEY,
    admin_id    TEXT REFERENCES admins(id),
    consent_ledger  INTEGER DEFAULT 0,
    consent_ai      INTEGER DEFAULT 0,
    eu_ai_act_art14 INTEGER DEFAULT 0,
    signed_at   TEXT NOT NULL,
    ip_hash     TEXT
);
```

### Lógica de geração DID

```python
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import uuid, hashlib, base64

def generate_did_and_wallet():
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    pub_bytes = public_key.public_bytes_raw()
    did = f"did:windi:{uuid.uuid4()}"
    fingerprint = hashlib.sha256(pub_bytes).hexdigest()[:16]
    return {
        "did": did,
        "public_key": base64.b64encode(pub_bytes).decode(),
        "fingerprint": fingerprint,
        # private_key NUNCA sai do servidor — só o DID e public_key
    }
```

### Seal no Ledger após registo

```python
# Após registo completo, selar no Ledger :8101
import httpx

async def seal_identity_in_ledger(company_id, did, admin_email):
    receipt_id = f"WINDI-LAW-IDENTITY-{company_id[:8].upper()}"
    payload = {
        "id": receipt_id,
        "actor": admin_email,
        "app": "windi-law-identity-gate",
        "doc_name": f"Identity Gate — Registo Empresa {company_id[:8]}",
        "doc_type": "doc",
        "governance_level": "HIGH",
        "metadata": {
            "did": did,
            "gate_version": "v1.0.0",
            "invariants": ["I9","I11","I13","G3"],
            "eu_ai_act_art14": True
        }
    }
    async with httpx.AsyncClient() as client:
        r = await client.post(
            "http://127.0.0.1:8101/api/receipts",
            json=payload
        )
    return r.json()
```

### Geração de API Keys

```python
import secrets

def generate_api_keys(is_dev: bool = False):
    api_key = f"wl_{secrets.token_urlsafe(32)}"
    dev_key = f"wl_dev_{secrets.token_urlsafe(32)}" if is_dev else None
    return api_key, dev_key
```

---

## FASE 2 — IDENTITY GATE UI (gate.html)

### Design obrigatório
- NOIR/KLAR toggle (igual ao Workspace v3)
- Fonts: Bricolage Grotesque + JetBrains Mono
- Gold: #C9A84C (NOIR) / #8B6914 (KLAR)
- Trilingue: DE/PT/EN (toggle no topo)

### 5 Blocos sequenciais (wizard — um passo de cada vez)

```
BLOCO 1 — Empresa
  ├── Nome legal (text)
  ├── País (select: DE, PT, AT, CH, BR, INT)
  ├── NIF / VAT (text)
  └── Tipo (radio: Escritório Jurídico / Empresa / Individual)

BLOCO 2 — Admin (Humano responsável)
  ├── Nome completo (text)
  ├── Email (email)
  └── Papel: "Responsável Legal" (fixo, não editável)

BLOCO 3 — Wallet + DID (AUTO-GERADO — não editável)
  ├── DID: did:windi:xxxxxxxx (gerado pelo servidor)
  ├── Fingerprint: a3f8c12d… (visível — CRÍTICO)
  └── Public Key: (copiável mas não editável)
  NOTA: O user DEVE ver que nasceu uma identidade.
  Mensagem: "A sua identidade soberana foi gerada. Ninguém mais tem acesso."

BLOCO 4 — Schlüssel / Keys
  ├── API Key: wl_xxxxxxxxx (auto-gerada)
  ├── Toggle DEV MODE (off por default)
  │   └── Se ON: DEV Key: wl_dev_xxxxxxx
  └── Scope (checkboxes):
      [✓] verify    — consultar Ledger
      [✓] seal      — selar documentos
      [ ] agents    — acesso à constelação (requer upgrade)

BLOCO 5 — Consentimento EU AI Act Art.14
  [✓] Aceito que todas as acções sejam registadas no Ledger (I11)
  [✓] Compreendo que o sistema não decide por mim (I9 + G3)
  [✓] Confirmo que sou o responsável legal por esta conta
  Nota: "Este consentimento será selado no Forensic Ledger."
```

### Comportamento do botão final

```javascript
// Só activa quando todos os 5 blocos estão completos
// E quando consent_ledger + consent_ai + eu_ai_act_art14 === true
// Após submit bem-sucedido:
// → Mostrar receipt do Ledger
// → Redirigir para /law/workspace/ com DID no header
```

### Mensagem de bloqueio se alguém tentar aceder /law/workspace/ sem DID

```html
<!-- Mostrar isto em vez do Workspace -->
<div class="identity-gate-wall">
  <div class="igw-icon">🔐</div>
  <div class="igw-title">Identidade Soberana Necessária</div>
  <div class="igw-sub">
    O WINDI-LAW requer uma identidade verificável antes de qualquer acção.
    Sem DID, não existe sujeito jurídico.
  </div>
  <a href="/law/register" class="igw-btn">Criar Identidade →</a>
</div>
```

---

## FASE 3 — SYSTEMD SERVICE

```ini
# /etc/systemd/system/windi-law.service
[Unit]
Description=WINDI LAW Identity Gate
After=network.target

[Service]
User=windi
WorkingDirectory=/opt/windi/windi-law/identity-gate
ExecStart=/usr/bin/python3 -m uvicorn identity_gate:app --host 127.0.0.1 --port 8120
Restart=always
RestartSec=5
EnvironmentFile=/opt/windi/.env
StandardOutput=append:/opt/windi/logs/windi-law.log
StandardError=append:/opt/windi/logs/windi-law-error.log

[Install]
WantedBy=multi-user.target
```

```bash
# Activar e iniciar
sudo systemctl daemon-reload
sudo systemctl enable windi-law
sudo systemctl start windi-law
sudo systemctl status windi-law
```

---

## FASE 4 — SEAL DE ARQUITECTURA NO LEDGER

Após smoke tests passarem (ver abaixo), selar a arquitectura:

```bash
curl -X POST https://windi-domain.com/ledger/api/receipts \
  -H "Content-Type: application/json" \
  -d '{
    "id": "WINDI-LAW-IDENTITY-GATE-V1.0.0",
    "actor": "Jober Mögele Correa",
    "app": "windi-law",
    "doc_name": "WINDI-LAW Identity Gate v1.0.0 — Architecture Seal",
    "doc_type": "doc",
    "governance_level": "HIGH",
    "metadata": {
      "version": "v1.0.0",
      "port": 8120,
      "endpoints": [
        "POST /law/register",
        "POST /law/wallet/create",
        "POST /law/keys/generate",
        "GET  /law/identity/{did}",
        "POST /law/identity/verify"
      ],
      "invariants": ["I9","I11","I13","G3","IP1"],
      "eu_ai_act_art14": true,
      "gdpr_art5": true,
      "blocking_rule": "if(!did||!wallet){blockWorkspace()}",
      "domain_branch": "windi-law",
      "tree": "ONE TREE — windi-domain.com/law/"
    }
  }'
```

---

## SMOKE TESTS (executar por esta ordem)

```bash
# 1. Health check
curl -s https://windi-domain.com/law/health | python3 -m json.tool

# 2. Registo empresa
curl -X POST https://windi-domain.com/law/register \
  -H "Content-Type: application/json" \
  -d '{
    "legal_name": "Mustermann & Partner Rechtsanwälte",
    "country": "DE",
    "vat_number": "DE123456789",
    "type": "law_firm",
    "admin_name": "Max Mustermann",
    "admin_email": "max@mustermann-law.de"
  }' | python3 -m json.tool

# Esperado: company_id + did + fingerprint + api_key + ledger_receipt

# 3. Verificar DID gerado
curl -s https://windi-domain.com/law/identity/{did_do_teste} | python3 -m json.tool

# 4. Tentar aceder workspace sem DID (deve bloquear)
curl -s https://windi-domain.com/law/workspace/ \
  -H "X-WINDI-DID: INVALID" | grep "identity-gate-wall"

# 5. Aceder workspace com DID válido (deve abrir)
curl -s https://windi-domain.com/law/workspace/ \
  -H "X-WINDI-DID: {did_do_teste}" | grep "workspace"

# 6. Verificar receipt no Ledger
curl -s https://windi-domain.com/ledger/api/receipts/WINDI-LAW-IDENTITY-GATE-V1.0.0 \
  | python3 -m json.tool
```

---

## INVARIANTES QUE GOVERNAM ESTA BUILD

```
I9  — Nunca escalada autónoma (DID gerado pelo servidor, não pela UI)
I11 — Permanência criptográfica (registo selado no Ledger imediatamente)
I13 — Convergência (wizard 5 passos, sem desvios)
G3  — Propõe ≠ Executa (consentimento explícito antes de qualquer seal)
IP1 — Separação financeira (keys não tocam em dados financeiros)
G1  — READ BEFORE TOUCH (ss+ps+curl antes de qualquer mudança nginx)
G4  — nginx -t SEMPRE antes de reload
G6  — GIT BEFORE SLEEP (.env NUNCA em commits)
```

---

## MENSAGEM FINAL AO GÊMEO

Irmão CCode 🐉

O motor está pronto (10/10 tests). O Identity Gate é a única
peça que falta para o WINDI-LAW passar de demo para sistema real.

Sequência de execução:
1. Criar directório /opt/windi/windi-law/
2. Implementar identity_gate.py (FastAPI :8120)
3. Construir gate.html (wizard 5 blocos, NOIR/KLAR, trilingue)
4. Criar windi-law.service (systemd)
5. Adicionar location /law/ ao nginx de windi-domain.com
6. nginx -t && sudo nginx -s reload
7. Executar smoke tests (6 testes)
8. Seal no Ledger após todos os testes passarem

NUNCA abrir o Workspace sem DID válido.
NUNCA seal automático sem consentimento explícito.
SEMPRE git add + commit + push no final.

"AI processes. Human decides. WINDI guarantees."
OM SHANTI 🐉

---
Liga IA+H · Kempten, Bavaria · 2026
RFC-001 v1.1 · DNA Identity Injection Protocol
