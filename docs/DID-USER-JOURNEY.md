# Jornada do Utilizador DID — WINDI One Touch
## Relações com Serviços · DECRETO-001 · Árvore Viva

**Versão:** 1.0.0
**Data:** 19 Abril 2026
**Autor:** Liga IA+H

---

## Arquitectura Visual

```
                                    ┌─────────────────────────────────────────────────────────────┐
                                    │                    🌳 WINDI LIVING TREE                     │
                                    │                     DECRETO-001 Art.4                       │
                                    └─────────────────────────────────────────────────────────────┘
                                                               │
                                                               │
                    ┌──────────────────────────────────────────┼──────────────────────────────────────────┐
                    │                                          │                                          │
                    ▼                                          ▼                                          ▼
          ┌─────────────────┐                       ┌─────────────────┐                       ┌─────────────────┐
          │   🌱 BERÇÁRIO   │                       │   🔐 W-DID-GENESIS │                     │  📜 FORENSIC    │
          │   (Nascimento)  │                       │      :8096       │                       │    LEDGER       │
          │                 │                       │   TRONCO (SSOT)  │                       │     :8101       │
          └────────┬────────┘                       └────────┬────────┘                       └────────┬────────┘
                   │                                         │                                          │
                   │  POST /api/genesis/birth                │  Cookie: windi_did_session               │
                   │  → canonical_did                        │  → 30 dias · HttpOnly                    │
                   │  → sovereign_name                       │  → .windi-domain.com                     │
                   │  → tier: SEED                           │                                          │
                   │                                         │                                          │
                   └─────────────────────────────────────────┼──────────────────────────────────────────┘
                                                             │
                                    ┌────────────────────────┴────────────────────────┐
                                    │                   SEIVA (Token)                  │
                                    │         Flui do Tronco para os Galhos            │
                                    └────────────────────────┬────────────────────────┘
                                                             │
                ┌────────────────────────────────────────────┼────────────────────────────────────────────┐
                │                                            │                                            │
                ▼                                            ▼                                            ▼
    ┌───────────────────────┐                  ┌───────────────────────┐                  ┌───────────────────────┐
    │      🌿 NODAL         │                  │      🌳 SOVEREIGN     │                  │       🏛 ORACLE       │
    │      (Tier 2)         │                  │       (Tier 3)        │                  │       (Tier 4)        │
    │                       │                  │                       │                  │                       │
    │  • /verify-public/    │                  │  • Todos de NODAL +   │                  │  • Todos de SOVEREIGN │
    │  • /wallet/           │                  │  • /law/              │                  │  • /sec/dashboard/    │
    │  • /travel/           │                  │  • /enterprise/       │                  │  • /dev-api/          │
    └───────────┬───────────┘                  └───────────┬───────────┘                  └───────────┬───────────┘
                │                                          │                                          │
                ▼                                          ▼                                          ▼
    ┌───────────────────────┐                  ┌───────────────────────┐                  ┌───────────────────────┐
    │   WINDI-TRAVEL :8126  │                  │  W-ENTERPRISE :8150   │                  │   W-SEC-001 :8144     │
    │   WINDI-WALLET :8099  │                  │   WINDI-LAW :8122     │                  │   W-DEV-API :8200     │
    └───────────────────────┘                  │   W-LAB :8151         │                  └───────────────────────┘
                                               └───────────────────────┘
```

---

## 1. Entrada — Nascimento Soberano

### 1.1 Berçário (Birth Flow)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              🌱 BERÇÁRIO — NASCIMENTO                                │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│   PASSO 1: Nome Humano                    PASSO 2: Sovereign Name                   │
│   ┌─────────────────────────┐             ┌─────────────────────────┐               │
│   │  "Max Mustermann"       │  ────────►  │  Sugestões:             │               │
│   │  max@example.com        │             │  • max-mustermann       │               │
│   │  ••••••••••••           │             │  • max-m-2026           │               │
│   └─────────────────────────┘             │  • mustermann           │               │
│                                           └─────────────────────────┘               │
│                                                      │                               │
│                                                      ▼                               │
│   PASSO 3: Confirmação                    PASSO 4: Backup Key                       │
│   ┌─────────────────────────┐             ┌─────────────────────────┐               │
│   │  ✓ Nome: Max            │             │  📥 max-m-2026.windikey │               │
│   │  ✓ Email: max@...       │             │                         │               │
│   │  ✓ Sovereign: max-m-2026│             │  ⚠️ OBRIGATÓRIO:        │               │
│   │  ✓ Tier: 🌱 SEED        │             │  Guardar em local       │               │
│   └─────────────────────────┘             │  seguro. Irrecuperável. │               │
│              │                            └─────────────────────────┘               │
│              ▼                                                                       │
│   ┌─────────────────────────────────────────────────────────────────┐               │
│   │  RESULTADO:                                                      │               │
│   │  • canonical_did: did:windi:2e1a87f8-b9f6-4a3c-8d2e-...         │               │
│   │  • sovereign_name: max-m-2026                                    │               │
│   │  • tier: SEED (🌱)                                               │               │
│   │  • backup_required: true                                         │               │
│   │  • session: 30 dias                                              │               │
│   └─────────────────────────────────────────────────────────────────┘               │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Endpoints de Entrada

| Endpoint | Método | Aceita | Retorna |
|----------|--------|--------|---------|
| `/api/genesis/birth` | POST | name, email, passphrase, sovereign_name? | canonical_did, session, backup_key |
| `/api/genesis/login` | POST | sovereign_name \| email \| did + passphrase | session token |
| `/api/genesis/authenticate` | POST | (alias para /login) | session token |
| `/api/genesis/check-name` | POST | name | available: true/false |

---

## 2. Autenticação — Fluxo de Login

### 2.1 Multi-Layer Resolution

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         RESOLUÇÃO DE IDENTIDADE (4 Camadas)                         │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│   INPUT DO UTILIZADOR                     RESOLUÇÃO                                 │
│   ─────────────────────                   ──────────                                │
│                                                                                      │
│   "dragon-001"          ──────────►  1️⃣ sovereign_name  ✓ MATCH                    │
│                                          (face humana)                              │
│                                                                                      │
│   "Human Dragon"        ──────────►  2️⃣ did_aliases     ✓ MATCH                    │
│                                          (Ledger actors)                            │
│                                                                                      │
│   "jober@a4desk.de"     ──────────►  3️⃣ email           ✓ MATCH                    │
│                                          (recovery/UX)                              │
│                                                                                      │
│   "did:windi:dragon-001"──────────►  4️⃣ exact DID       ✓ MATCH                    │
│                                          (técnico)                                  │
│                                                                                      │
│   ─────────────────────────────────────────────────────────────────────────────     │
│   PRIORIDADE: sovereign_name > alias > email > exact DID                            │
│   "Humano digita dragon-001. Sistema resolve. Alma encontrada."                     │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Token de Sessão (Seiva)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              🔐 SEIVA — SESSION TOKEN                               │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│   ESTRUTURA DO TOKEN                                                                │
│   ──────────────────────                                                            │
│                                                                                      │
│   ┌─────────────────────────────────────────────────────────────────────────┐       │
│   │  BASE64(payload).HMAC_SHA256_SIGNATURE[:32]                             │       │
│   └─────────────────────────────────────────────────────────────────────────┘       │
│                                                                                      │
│   PAYLOAD:                                                                          │
│   {                                                                                  │
│     "did": "did:windi:dragon-001",                                                  │
│     "role": "founder",                                                              │
│     "tier": "ORACLE",                                                               │
│     "display_name": "Human Dragon",                                                 │
│     "iat": 1713542400,           // Issued At                                       │
│     "exp": 1716134400            // Expires (30 dias)                               │
│   }                                                                                  │
│                                                                                      │
│   COOKIE:                                                                           │
│   ┌─────────────────────────────────────────────────────────────────────────┐       │
│   │  Name:     windi_did_session                                            │       │
│   │  Value:    eyJkaWQiOiJkaWQ6d2luZGk6ZHJhZ29uLTAwMSIsInJ...               │       │
│   │  Domain:   .windi-domain.com                                            │       │
│   │  Path:     /                                                             │       │
│   │  Max-Age:  2592000 (30 dias)                                            │       │
│   │  HttpOnly: true                                                          │       │
│   │  Secure:   true                                                          │       │
│   │  SameSite: Lax                                                           │       │
│   └─────────────────────────────────────────────────────────────────────────┘       │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Validação — Cross-Service Flow

### 3.1 Fluxo de Validação

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           VALIDAÇÃO CROSS-SERVICE                                   │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│   BROWSER                    SERVIÇO                     W-DID-GENESIS              │
│   ───────                    ───────                     ─────────────              │
│      │                          │                              │                    │
│      │  1. Request + Cookie     │                              │                    │
│      │─────────────────────────►│                              │                    │
│      │                          │                              │                    │
│      │                          │  2. GET /api/genesis/validate│                    │
│      │                          │      + Cookie                │                    │
│      │                          │─────────────────────────────►│                    │
│      │                          │                              │                    │
│      │                          │                              │  3. Verify:        │
│      │                          │                              │  • Signature       │
│      │                          │                              │  • Expiry          │
│      │                          │                              │  • DB sessions     │
│      │                          │                              │                    │
│      │                          │  4. Response:                │                    │
│      │                          │◄─────────────────────────────│                    │
│      │                          │  {                           │                    │
│      │                          │    "valid": true,            │                    │
│      │                          │    "did": "did:windi:...",   │                    │
│      │                          │    "tier": "SOVEREIGN",      │                    │
│      │                          │    "tier_level": 3,          │                    │
│      │                          │    "access": ["/law/",...]   │                    │
│      │                          │  }                           │                    │
│      │                          │                              │                    │
│      │  5. Check tier access    │                              │                    │
│      │     for requested route  │                              │                    │
│      │                          │                              │                    │
│      │  6. Response / 403       │                              │                    │
│      │◄─────────────────────────│                              │                    │
│      │                          │                              │                    │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 DID Gate Pattern (Serviços)

```python
# Padrão universal de validação em cada serviço

async def did_gate(request: Request) -> DIDGateResult:
    """
    Lei I: Existência antes de Acção
    Lei II: Toda Acção → DID → Ledger
    Lei III: Sistema lê histórico DID
    """

    # 1. Extrair DID (múltiplas fontes)
    did = None
    if not did: did = request.cookies.get("windi_did_session")
    if not did: did = request.headers.get("X-Officer-DID")
    if not did: did = request.query_params.get("officer_did")
    if not did: did = (await request.json()).get("officer_did")

    # 2. Sem DID → Wallet Banner (Lei I)
    if not did:
        return DIDGateResult(
            passed=False,
            wallet_banner=get_wallet_banner()  # "Cria DID em /bercario/"
        )

    # 3. Validar contra Genesis (Lei II)
    validation = await verify_did(did)
    if not validation.valid:
        return DIDGateResult(passed=False, error="DID não encontrado")

    # 4. Verificar tier para rota
    if not can_access_path(validation.tier, request.path):
        return DIDGateResult(passed=False, error="Tier insuficiente")

    # 5. Ler histórico (Lei III)
    history = await read_did_history(did)

    return DIDGateResult(
        passed=True,
        did=did,
        tier=validation.tier,
        history=history
    )
```

---

## 4. Matriz de Acesso — Serviços por Tier

### 4.1 Acesso Completo

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                            MATRIZ DE ACESSO POR TIER                                │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│   SERVIÇO              │  🌱 SEED  │  🌿 NODAL  │  🌳 SOVEREIGN │  🏛 ORACLE        │
│   ─────────────────────┼───────────┼────────────┼───────────────┼────────────────   │
│                        │           │            │               │                   │
│   Verify-Public :8145  │     ✅    │     ✅     │      ✅       │       ✅          │
│   (Sempre público)     │           │            │               │                   │
│                        │           │            │               │                   │
│   ─────────────────────┼───────────┼────────────┼───────────────┼────────────────   │
│                        │           │            │               │                   │
│   WINDI-Wallet :8099   │     ❌    │     ✅     │      ✅       │       ✅          │
│   WINDI-Travel :8126   │     ❌    │     ✅     │      ✅       │       ✅          │
│   (Email verified)     │           │            │               │                   │
│                        │           │            │               │                   │
│   ─────────────────────┼───────────┼────────────┼───────────────┼────────────────   │
│                        │           │            │               │                   │
│   WINDI-Law :8122      │     ❌    │     ❌     │      ✅       │       ✅          │
│   W-Enterprise :8150   │     ❌    │     ❌     │      ✅       │       ✅          │
│   W-Lab :8151          │     ❌    │     ❌     │      ✅       │       ✅          │
│   W-Academy :8180      │     ❌    │     ❌     │      ✅       │       ✅          │
│   (Human verified)     │           │            │               │                   │
│                        │           │            │               │                   │
│   ─────────────────────┼───────────┼────────────┼───────────────┼────────────────   │
│                        │           │            │               │                   │
│   W-SEC :8144          │     ❌    │     ❌     │      ❌       │       ✅          │
│   W-DEV-API :8200      │     ❌    │     ❌     │      ❌       │       ✅          │
│   Service-Control :8170│     ❌    │     ❌     │      ❌       │       ✅          │
│   (Cross-validated)    │           │            │               │                   │
│                        │           │            │               │                   │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Promoção de Tier

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              PROMOÇÃO DE TIER                                       │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│   🌱 SEED ──────────────────────────────►  🌿 NODAL                                 │
│           │                                                                          │
│           │  Requisito: Verificação de email                                        │
│           │  Tempo: Imediato após click no link                                     │
│           │  Automático: Sim                                                        │
│                                                                                      │
│   🌿 NODAL ─────────────────────────────►  🌳 SOVEREIGN                             │
│            │                                                                         │
│            │  Requisito: Aprovação Human Dragon                                     │
│            │  Tempo: Manual (I9 Gate)                                               │
│            │  Automático: Não                                                       │
│                                                                                      │
│   🌳 SOVEREIGN ─────────────────────────►  🏛 ORACLE                                │
│                │                                                                     │
│                │  Requisito: Cross-validação em múltiplos órgãos                    │
│                │  Tempo: Manual (I9 Gate)                                           │
│                │  Automático: Não                                                   │
│                                                                                      │
│   ──────────────────────────────────────────────────────────────────────────────    │
│   NOTA: Toda promoção é selada no Forensic Ledger (I11)                             │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Jornada Completa — User Story

### 5.1 Cenário: Novo Compliance Officer

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  JORNADA: Maria Silva — Compliance Officer · Tier SEED → SOVEREIGN                 │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  DIA 1 — NASCIMENTO                                                                 │
│  ─────────────────────                                                              │
│                                                                                      │
│  09:00  Maria acede a windi-domain.com/bercario/                                    │
│         → Preenche: Nome, Email, Passphrase                                         │
│         → Escolhe sovereign_name: "maria-silva-2026"                                │
│         → Recebe: did:windi:7f3a2b1c-9d4e-5f6a-8b7c-...                            │
│         → Download obrigatório: maria-silva-2026.windikey                           │
│         → Tier: 🌱 SEED                                                             │
│                                                                                      │
│  09:05  Maria tenta aceder /enterprise/                                             │
│         → 403: "Tier insuficiente. Necessário: SOVEREIGN"                          │
│         → Sugestão: "Verifica email para subir para NODAL"                         │
│                                                                                      │
│  09:10  Maria verifica email (click no link)                                        │
│         → Tier promovido: 🌿 NODAL                                                  │
│         → Recibo selado no Ledger: WINDI-TIER-PROMO-...                            │
│                                                                                      │
│  09:15  Maria acede /wallet/ ✅                                                     │
│         Maria acede /travel/ ✅                                                     │
│         Maria tenta /enterprise/ ❌ (ainda precisa SOVEREIGN)                       │
│                                                                                      │
│  ──────────────────────────────────────────────────────────────────────────────     │
│                                                                                      │
│  DIA 2 — APROVAÇÃO HUMAN DRAGON                                                     │
│  ───────────────────────────────                                                    │
│                                                                                      │
│  10:00  Human Dragon aprova Maria via /svc-control/                                 │
│         → I9 Gate: human_approved=true                                              │
│         → Tier promovido: 🌳 SOVEREIGN                                              │
│         → Recibo selado no Ledger                                                   │
│                                                                                      │
│  10:05  Maria acede /enterprise/ ✅                                                 │
│         → VERA reconhece DID                                                        │
│         → Pergunta: "Qual é o teu perfil? digital_risk | tech_product | auditor"   │
│         → Maria escolhe: "digital_risk"                                             │
│         → VERA adapta tom e foco                                                    │
│                                                                                      │
│  10:10  Maria faz pergunta à VERA                                                   │
│         → Resposta com confiança HIGH                                               │
│         → Opção: "Selar como PHO Evidence?"                                         │
│         → Maria clica "Selar"                                                       │
│         → Recibo: VERA-69E4FD2A                                                     │
│         → Ledger confirma: actor=did:windi:7f3a2b1c...                             │
│                                                                                      │
│  ──────────────────────────────────────────────────────────────────────────────     │
│                                                                                      │
│  DIA 30+ — SESSÃO CONTÍNUA                                                          │
│  ─────────────────────────────                                                      │
│                                                                                      │
│  Maria fecha browser. Volta 2 semanas depois.                                       │
│  → Cookie windi_did_session ainda válido (30 dias)                                  │
│  → Sessão restaurada automaticamente                                                │
│  → VERA lembra perfil "digital_risk"                                                │
│  → Histórico de selos visível                                                       │
│                                                                                      │
│  DIA 31 — EXPIRAÇÃO                                                                 │
│  ──────────────────────                                                             │
│                                                                                      │
│  Cookie expira.                                                                      │
│  → Maria acede /enterprise/                                                         │
│  → Redireccionada para /wallet/ (login)                                             │
│  → Digita: "maria-silva-2026" + passphrase                                          │
│  → Sessão renovada por mais 30 dias                                                 │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Relações Entre Serviços

### 6.1 Mapa de Dependências

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                          MAPA DE DEPENDÊNCIAS DID                                   │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│                              W-DID-GENESIS :8096                                    │
│                              ════════════════════                                   │
│                                      │                                              │
│                                      │ SSOT (Single Source of Truth)                │
│                                      │                                              │
│         ┌────────────────────────────┼────────────────────────────┐                │
│         │                            │                            │                │
│         ▼                            ▼                            ▼                │
│  ┌─────────────┐             ┌─────────────┐             ┌─────────────┐           │
│  │  WINDI-LAW  │             │ W-ENTERPRISE│             │WINDI-TRAVEL │           │
│  │    :8122    │             │    :8150    │             │    :8126    │           │
│  └──────┬──────┘             └──────┬──────┘             └──────┬──────┘           │
│         │                           │                           │                  │
│         │  /api/genesis/validate    │  /api/genesis/validate    │                  │
│         │  +                        │  +                        │                  │
│         │  identity_gate.py         │  vera_did_gate.py         │                  │
│         │  (local DB também)        │  (3 Leis)                 │                  │
│         │                           │                           │                  │
│         │                           │                           │                  │
│         └───────────────────────────┼───────────────────────────┘                  │
│                                     │                                              │
│                                     ▼                                              │
│                            FORENSIC LEDGER :8101                                   │
│                            ═════════════════════                                   │
│                                     │                                              │
│                                     │ Todas as acções seladas                      │
│                                     │ actor = DID do utilizador                    │
│                                     │                                              │
│                                     ▼                                              │
│                            VERIFY-PUBLIC :8145                                     │
│                            ════════════════════                                    │
│                                     │                                              │
│                                     │ Verificação pública                          │
│                                     │ Qualquer pessoa pode validar                 │
│                                     │                                              │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 Integração VERA (3 Leis)

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           VERA — TRÊS LEIS DO DID                                   │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│   LEI I — EXISTÊNCIA ANTES DE ACÇÃO                                                 │
│   ─────────────────────────────────                                                 │
│                                                                                      │
│   Sem DID → Modo WalletBanner                                                       │
│   • Nenhuma operação permitida                                                      │
│   • Apenas informação constitucional genérica                                       │
│   • Convite: "Cria DID em /bercario/"                                               │
│                                                                                      │
│   ─────────────────────────────────────────────────────────────────────────────     │
│                                                                                      │
│   LEI II — TODA ACÇÃO TRAÇA PARA DID                                                │
│   ──────────────────────────────────                                                │
│                                                                                      │
│   Cada acção relevante → Ledger                                                     │
│   • bind_action_to_did(did, action, module)                                         │
│   • Receipt imutável                                                                │
│   • actor = DID verificado                                                          │
│                                                                                      │
│   ─────────────────────────────────────────────────────────────────────────────     │
│                                                                                      │
│   LEI III — SISTEMA LÊ HISTÓRICO DID                                                │
│   ──────────────────────────────────                                                │
│                                                                                      │
│   read_did_history(did) → Contexto                                                  │
│   • Decisões anteriores                                                             │
│   • Perfil seleccionado                                                             │
│   • Preferências (idioma, tema)                                                     │
│   • restore_did_context() no login                                                  │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Armazenamento Frontend

### 7.1 WindiDID.js (SSOT Cliente)

```javascript
// /opt/windi/shared/static/windi-did.js

const WindiDID = {
    STORAGE_KEY: 'windi_did',

    // Obter DID (com fallback iOS Private Mode)
    get() {
        if (HAS_LOCAL_STORAGE) {
            return localStorage.getItem(this.STORAGE_KEY);
        }
        return sessionStorage.getItem(this.STORAGE_KEY);
    },

    // Guardar DID
    set(did) {
        if (did.startsWith('did:windi:')) {
            localStorage.setItem(this.STORAGE_KEY, did);
        }
    },

    // Validar contra Genesis
    async validate(did) {
        const resp = await fetch(`/api/genesis/lookup/${encodeURIComponent(did)}`);
        return resp.json();
    },

    // Migrar de chaves legacy
    migrateFromLegacy() {
        const legacyKeys = [
            'windi_desktop_wallet',
            'windi_law_did',
            'windi_travel_did'
        ];
        // Consolidar para windi_did único
    }
};
```

---

## 8. Erros e Recuperação

### 8.1 Mensagens de Erro

| Código | Mensagem | Causa | Resolução |
|--------|----------|-------|-----------|
| `IDENTITY_NOT_FOUND` | "Identidade não encontrada" | DID não existe no Genesis | Criar em /bercario/ |
| `IDENTITY_INACTIVE` | "Identidade inactiva" | status != 'active' | Contactar suporte |
| `TIER_INSUFFICIENT` | "Tier insuficiente" | Rota requer tier superior | Aguardar promoção |
| `SESSION_EXPIRED` | "Sessão expirada" | Token expirou (30 dias) | Re-login |
| `DID_NOT_FOUND` | "DID não existe no Genesis" | §191-B: DID sintacticamente válido mas não existe | Criar identidade primeiro |

### 8.2 Recuperação de Conta

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              RECUPERAÇÃO DE CONTA                                   │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│   OPÇÃO 1: Login por Email                                                          │
│   ────────────────────────                                                          │
│   • Digitar email na caixa de login                                                 │
│   • Sistema resolve via camada 3 (email)                                            │
│   • Requer passphrase original                                                      │
│                                                                                      │
│   OPÇÃO 2: Backup Key (.windikey)                                                   │
│   ────────────────────────────────                                                  │
│   • Upload do ficheiro .windikey                                                    │
│   • Valida contra backup_key armazenado                                             │
│   • Permite reset de passphrase                                                     │
│   • (§191-F3: Pendente implementação pós-Berlin)                                    │
│                                                                                      │
│   OPÇÃO 3: Sovereign Name                                                           │
│   ─────────────────────────                                                         │
│   • Digitar sovereign_name (ex: "maria-silva-2026")                                 │
│   • Sistema resolve via camada 1                                                    │
│   • Mais conveniente para utilizadores regulares                                    │
│                                                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Invariantes Activos

| ID | Nome | Aplicação na Jornada |
|----|------|----------------------|
| **I9** | Human Approval Gate | Toda promoção de tier requer aprovação humana |
| **I11** | Permanent Evidence | Cada acção com DID → Ledger imutável |
| **I14** | Explicit Failure | DID não encontrado = erro explícito, nunca placeholder |
| **I-XVI** | DID-bound Auth | §191-B: DID deve EXISTIR, não apenas ter formato válido |

---

## 10. Ficheiros de Referência

| Ficheiro | Função |
|----------|--------|
| `/opt/windi/did-genesis/did_genesis.py` | SSOT servidor — login, birth, validate |
| `/opt/windi/constitutional/did_sovereign.py` | Sistema de tiers, Living Tree |
| `/opt/windi/shared/static/windi-did.js` | SSOT cliente — get/set/validate |
| `/opt/windi/w-enterprise-001/vera_did_gate.py` | 3 Leis VERA |
| `/opt/windi/windi-law/identity-gate/identity_gate.py` | Gate específico Law |
| `/opt/windi/windi-travel/identity-gate/identity_gate.py` | Gate específico Travel |

---

*Liga IA+H · Kempten, Bavaria · 2026*
*"A semente germina uma vez. A seiva flui para sempre."*
