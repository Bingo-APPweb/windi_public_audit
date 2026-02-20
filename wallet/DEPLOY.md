# WINDI WALLET — Guia de Deploy v1.0.0
## De Lead Aprovado a Identidade Soberana

**Data:** 2026-02-15
**Protocolo:** Three Dragons v1.1 — I9 Active
**Custódia:** Modelo A (servidor) para MVP

---

## Pré-requisitos

O WALLET integra com serviços **já operacionais**:

| Serviço         | Porta | Status    | Papel no WALLET                    |
|-----------------|-------|-----------|------------------------------------|
| Governance API  | 8080  | ✅ Active | Host dos endpoints `/api/wallet/*` |
| BABEL / A4Desk  | 8085  | ✅ Active | Renderiza via `/api/wallet/me`     |
| Forensic Ledger | 8094  | ⚠️ Inter. | Registra `WALLET_PROVISIONED`      |
| ID Genesis      | 8096  | ✅ Active | Lead Admin (fonte dos leads)       |

---

## Passo 1: Copiar arquivos ao servidor

```bash
# No servidor (SSH como windi)
mkdir -p /opt/windi/wallet
mkdir -p /opt/windi/wallet/ddl
mkdir -p /opt/windi/data          # já existe
mkdir -p /opt/windi/logs          # já existe
mkdir -p /opt/windi/tsil/wallet_keys
chmod 700 /opt/windi/tsil/wallet_keys

# Copiar os arquivos:
# - wallet_provisioning.py → /opt/windi/wallet/
# - ddl/001_wallet_schema.sql → /opt/windi/wallet/ddl/
```

## Passo 2: Instalar dependências (opcionais)

```bash
# UUIDv7 (recomendado, mas tem fallback para UUID4)
pip install uuid-utils --break-system-packages

# PyNaCl para Ed25519 real (recomendado, mas tem fallback)
pip install pynacl --break-system-packages

# requests já deve estar disponível (Flask depende)
pip install requests --break-system-packages
```

## Passo 3: Teste standalone

```bash
cd /opt/windi/wallet

# Rodar teste isolado (cria DB de teste)
WALLET_DB_PATH=/opt/windi/data/wallet_test.db \
python3 wallet_provisioning.py

# Esperado:
# [OK] DB initialized
# [OK/WARN] PyNaCl: True/False
# [OK/WARN] UUIDv7: True/False
# --- Test Provision (PF) ---
# { "status": "ok", "wallet_id": "WALLET-20260215-0001", ... }
# --- Test Idempotency ---
# Idempotent: True

# Limpar teste
rm /opt/windi/data/wallet_test.db
```

## Passo 4: Integrar na Governance API (:8080)

A Governance API está em `/opt/windi/engine/windi_governance_api.py`.

### Opção A: Blueprint (recomendado)

Adicionar ao final do arquivo da Governance API, **antes** de `app.run()`:

```python
# ─── WALLET MODULE ───────────────────────────────────────────
import sys
sys.path.insert(0, '/opt/windi/wallet')
from wallet_provisioning import create_wallet_blueprint
app.register_blueprint(create_wallet_blueprint())
# ─── END WALLET ──────────────────────────────────────────────
```

### Opção B: Importação direta (se Blueprint não funcionar)

```python
# No governance API, adicionar routes manualmente:
sys.path.insert(0, '/opt/windi/wallet')
import wallet_provisioning as wp

wp.init_db()

@app.route('/api/wallet/provision', methods=['POST'])
def wallet_provision():
    data = request.get_json(force=True)
    try:
        result = wp.provision_wallet(data)
        return jsonify(result), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/wallet/me', methods=['GET'])
def wallet_me():
    email = request.args.get('email')
    wallet_id = request.args.get('wallet_id')
    if wallet_id:
        result = wp.get_wallet_by_id(wallet_id)
    elif email:
        result = wp.get_wallet_by_email(email)
    else:
        return jsonify({"error": "email or wallet_id required"}), 400
    if not result:
        return jsonify({"error": "not found"}), 404
    return jsonify(result)

@app.route('/api/wallet/context/<cid>/freeze', methods=['POST'])
def wallet_freeze(cid):
    data = request.get_json(force=True) if request.data else {}
    try:
        result = wp.freeze_context(cid, data.get('actor', 'system'), data.get('reason', ''))
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/wallet/stats', methods=['GET'])
def wallet_stats():
    return jsonify(wp.get_wallet_stats())

@app.route('/api/wallet/health', methods=['GET'])
def wallet_health():
    stats = wp.get_wallet_stats()
    return jsonify({"status": "healthy", "module": "WALLET v1.0.0", **stats})
```

## Passo 5: Reiniciar Governance API

```bash
# Se systemd:
sudo systemctl restart windi-governance

# Se nohup:
pkill -f windi_governance_api.py
cd /opt/windi/engine
nohup python3 windi_governance_api.py > /opt/windi/logs/governance.log 2>&1 &
sleep 2
```

## Passo 6: Verificar endpoints

```bash
# Health
curl -s http://localhost:8080/api/wallet/health | python3 -m json.tool

# Stats
curl -s http://localhost:8080/api/wallet/stats | python3 -m json.tool

# Provision (teste)
curl -s -X POST http://localhost:8080/api/wallet/provision \
  -H "Content-Type: application/json" \
  -d '{
    "lead_id": "LEAD-20260215-151736",
    "email": "jober@a4desk.de",
    "display_name": "Jober Mögele Correa",
    "kind": "PJ",
    "org": {"name": "WINDI Publishing House", "domain": "a4desk.de"},
    "role": "admin",
    "approved_by": "admin:jober"
  }' | python3 -m json.tool

# Query wallet
curl -s "http://localhost:8080/api/wallet/me?email=jober@a4desk.de" | python3 -m json.tool
```

## Passo 7: Nginx (já roteado)

A Governance API (:8080) já tem proxy no nginx.
Os novos endpoints `/api/wallet/*` são servidos automaticamente via `:8080`.

Verificar:
```bash
curl -s https://admin.windia4desk.tech/api/wallet/health | python3 -m json.tool
```

---

## Arquitetura de Arquivos Final

```
/opt/windi/
├── wallet/                          # ← NOVO
│   ├── wallet_provisioning.py       # Módulo principal
│   └── ddl/
│       └── 001_wallet_schema.sql    # DDL PostgreSQL (futuro)
├── data/
│   └── wallet.db                    # ← NOVO (SQLite MVP)
├── tsil/
│   └── wallet_keys/                 # ← NOVO (chaves privadas, 700)
│       └── <human_id>.key           # chmod 600
├── backups/
│   └── forensic_pending/            # ← NOVO (fallback se Forensic offline)
├── engine/
│   └── windi_governance_api.py      # Integra o Blueprint
└── logs/
    └── wallet.log                   # ← NOVO
```

---

## Contratos JSON — Referência Rápida

### POST /api/wallet/provision

**Request:**
```json
{
  "lead_id": "LEAD-20260215-151736",
  "email": "jober@a4desk.de",
  "display_name": "Jober Mögele Correa",
  "kind": "PJ",
  "org": { "name": "WINDI Publishing House", "domain": "a4desk.de" },
  "role": "admin",
  "approved_by": "admin:jober"
}
```

**Response (201):**
```json
{
  "status": "ok",
  "human_id": "018f...",
  "context_id": "0190...",
  "wallet_id": "WALLET-20260215-0001",
  "pubkey": "ed25519:...",
  "fingerprint": "70b5eae0...",
  "trust": { "score": 50.0, "level": "T1" },
  "ledger": { "entry_id": "2", "hash": "...", "ref_id": "WALLET-20260215-0001" },
  "next": { "a4_builder_url": "/a4builder?wallet=WALLET-20260215-0001" }
}
```

### GET /api/wallet/me?email=...

**Response:**
```json
{
  "human_id": "018f...",
  "display_name": "Jober Mögele Correa",
  "fingerprint": "70b5eae0...",
  "contexts": [
    {
      "wallet_id": "WALLET-20260215-0001",
      "context_type": "PJ",
      "role": "admin",
      "trust": { "score": 50.0, "level": "T1" },
      "org": { "name": "WINDI Publishing House", "domain": "a4desk.de" },
      "render": { "path": "PJ", "builder_url": "/a4builder?wallet=..." }
    }
  ]
}
```

### POST /api/wallet/context/{id}/freeze

**Request:**
```json
{ "actor": "hr:admin", "reason": "Employee departure" }
```

**Response:**
```json
{
  "status": "ok",
  "wallet_id": "WALLET-20260215-0001",
  "new_state": "frozen",
  "human_sovereignty": "preserved"
}
```

---

## Decisão de Custódia: Modelo A (MVP)

| Aspecto              | Modelo A (servidor)      | Modelo B (cliente)         |
|----------------------|--------------------------|----------------------------|
| Chave privada        | /opt/windi/tsil/         | No dispositivo do usuário  |
| Complexidade MVP     | Baixa ✅                 | Alta                       |
| Soberania real       | Parcial                  | Total ✅                   |
| Recuperação          | Simples (backup)         | Seed phrase necessário     |
| Migração             | Preparada via key_history| —                          |

**Decisão atual: Modelo A.**
**Preparação para B:** `wallet_key_history` já rastreia rotações.

---

## Migração futura: SQLite → PostgreSQL

O DDL (`001_wallet_schema.sql`) é PostgreSQL puro com triggers.
Quando migrar:

1. Instalar PostgreSQL no Strato (ou usar managed DB)
2. Executar `001_wallet_schema.sql`
3. Migrar dados: `sqlite3 wallet.db .dump | psql windi_wallet`
4. Atualizar `WALLET_DB_PATH` para DSN PostgreSQL
5. Adaptar `get_db()` para usar `psycopg2` em vez de `sqlite3`

---

## Checklist de Deploy

```
□ Arquivos copiados para /opt/windi/wallet/
□ Dependências instaladas (uuid-utils, pynacl)
□ Teste standalone passou
□ Blueprint integrado na Governance API
□ Governance API reiniciada
□ /api/wallet/health retorna "healthy"
□ /api/wallet/provision testado (PF e PJ)
□ /api/wallet/me retorna dados corretos
□ Idempotência verificada (mesmo lead_id não duplica)
□ Forensic Ledger registrou WALLET_PROVISIONED
□ Fallback forense funciona (se Ledger offline)
□ Permissões de /opt/windi/tsil/wallet_keys/ são 700
□ wallet.log escrevendo em /opt/windi/logs/
```

---

*"Sem WALLET, há login. Com WALLET, há existência digital soberana."* 🐉
