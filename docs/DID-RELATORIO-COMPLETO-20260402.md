# RELATÓRIO COMPLETO — DID: A SEMENTE WINDI

**Data:** 2 de Abril de 2026
**Solicitado por:** Human Dragon
**Elaborado por:** Architect

---

## 1. RESUMO EXECUTIVO

O sistema DID (Decentralized Identity) do WINDI implementa o fluxo filosófico:

```
ALMA → DID → CÉREBRO → LEDGER → MUNDO
(Semente)  (Identidade)  (Contexto)  (Prova)  (Distribuição)
```

É uma arquitectura de **soberania identitária** onde:
- **O humano controla a sua identidade** (não a plataforma)
- **A criptografia prova existência** (não bases de dados)
- **Verificação pública é possível** (sem vendor lock-in)
- **Evolução é append-only** (história preservada)
- **Confiança é conquistada** (scores evoluem)

---

## 2. AS 5 CAMADAS DA IDENTIDADE

### Camada 0: ALMA — Lead Inception (Port :8096)

O ponto de entrada. Leads capturados das landing pages.

```
Landing Page → POST /api/leads → LeadLedger (append-only)
                                       ↓
                              Hash chain garante integridade
                                       ↓
                           ❌ NUNCA processado sem aprovação humana (I1)
```

**Ficheiro:** `/opt/windi/leads/windi_leads.py`

---

### Camada 1: DID — Wallet Bridge

Quando um lead é **aprovado pelo humano**, a ponte converte em wallet:

```python
def on_lead_approved(lead_data):
    # Detecta PF vs PJ
    is_pj = company not in ["-", "gmail.com", "outlook.com"]

    # Gera:
    # - human_id (UUIDv7) — identidade única
    # - Ed25519 keypair — par criptográfico
    # - fingerprint — SHA-256 da identidade
    # - wallet_id — WALLET-YYYYMMDD-NNNN (legível)
```

**Ficheiro:** `/opt/windi/wallet/wallet_bridge.py`

---

### Camada 2: CÉREBRO — Wallet Service (Port :8099)

O serviço core que provisiona e gere wallets.

**10 Passos do Provisioning:**

| # | Passo | Descrição |
|---|-------|-----------|
| 1 | VALIDATE | Verifica lead_id, kind, email |
| 2 | IDEMPOTENCE | Previne duplicados |
| 3 | GENERATE | human_id + Ed25519 keypair |
| 4 | INSERT | wallet_human (IMUTÁVEL) |
| 5 | CREATE ORG | Se PJ, cria organização |
| 6 | CONTEXT | wallet_context + trust_score inicial |
| 7 | FORENSIC | Regista WALLET_PROVISIONED no Ledger |
| 8 | LEDGER LINK | Cria referência ao hash forense |
| 9 | KEY HISTORY | Regista evento key_created |
| 10 | STORE KEYS | Chave privada em `/opt/windi/tsil/wallet_keys/` |

**Output:**
```json
{
  "wallet_id": "WALLET-20260401-0001",
  "fingerprint": "SHA256...",
  "trust": {"score": 50.0, "level": "T1"}
}
```

---

### Camada 3: Identity Gates (Domínios Específicos)

#### LAW Gate (:8122)
- Identidade para profissionais jurídicos
- Acesso ao LAW Workspace (§57)
- Magic Link Login (§109)
- **12 empresas registadas**

#### Travel Gate (:8126)
- Identidade para viajantes
- Integra com MARIA Decision Engine
- "Provar que eu estava lá" (I14)
- **Magic Link activo**

**State Machine comum:**
```
UNBORN → PROVISIONAL → EMAIL_PENDING → VERIFIED
   ↓                        ↓
(24h timeout)           (48h timeout)
```

---

### Camada 4: LEDGER — Prova Forense (Port :8101)

Toda acção significativa é selada:

```json
{
  "receipt_id": "WINDI-VIRTUE-20260401-XXXXX",
  "content_hash": "SHA256...",
  "actor": "WALLET-20260401-0001",
  "verify_url": "windi-domain.com/verify-public/?id=...",
  "sealed_at": "2026-04-01T15:30:45Z"
}
```

**Invariante I11:** Uma vez selado = **IRREMEDIÁVEL**.

---

### Camada 5: MUNDO — Verificação Pública

Qualquer pessoa no mundo pode verificar:

```
GET windi-domain.com/verify-public/?id=RECEIPT-ID

→ Retorna: hash, creator_wallet_id, timestamp, QR code
→ Sem PII exposto
→ Prova matemática de existência
```

---

## 3. SCHEMA DE DADOS (SQLite MVP)

```sql
wallet_human (IMUTÁVEL)
├── human_id (UUIDv7) — Identidade principal
├── pubkey_ed25519 — Chave pública
├── fingerprint — SHA-256 único
├── lead_id — Rastreabilidade
└── email, display_name

wallet_context (MUTÁVEL com versioning)
├── wallet_id — WALLET-YYYYMMDD-NNNN
├── governance_level — L1/L2/L3
├── state — active/frozen/revoked
└── trust_score → 0-100

trust_events (IMUTÁVEL, append-only)
├── signal_type — receipt_ok / policy_violation
├── weight — +2 (positivo) ou -5 (negativo)
└── source_ref — link para a decisão
```

---

## 4. TRUST SCORE — NÍVEIS DE CONFIANÇA

| Nível | Score | Privilégios |
|-------|-------|-------------|
| T1 (New) | 0-40 | Provisório, poucos privilégios |
| T2 (Trusted) | 40-70 | Pode criar documentos |
| T3 (Verified) | 70-85 | Pode selar documentos próprios |
| T4 (Sovereign) | 85-95 | Pode endossar outros (Virtue) |
| T5 (Oracle) | 95-100 | Status cerimonial, raro |

**Evolução:**
```
Acção                    Peso    Resultado
────────────────────────────────────────────
Receipt selado           +2      Score ↑
Violação de política     -5      Score ↓
Auditoria passou         +3      Score ↑
```

---

## 5. USO DO DID NOS SISTEMAS WINDI

### No Canvas (GEN 7 Desktop)
```
User → /desktop → Carrega wallet_context
                → Cria documento
                → POST /api/dragon/chat (com wallet_id)
                → Selo com atribuição DID
```

### No MARIA Travel
```python
def get_travel_preferences(did):
    return {
        "avoid_stops": True,        # Da memória
        "price_sensitivity": 0.5,   # Do histórico
        "prefer_morning": True      # Aprendido
    }
```

### No Export (.jmpg)
```
Documento → .jmpg package
         → creator_did no manifest
         → did_hash no binary trigger
         → Verificável offline
```

### No Virtue Receipt (Endorsement)
```
Endorser DID → Valida competência de outro
            → Receipt selado no Ledger
            → Rede de confiança cresce
```

---

## 6. ESTADO ACTUAL (2 Abril 2026)

| Métrica | Valor |
|---------|-------|
| **Total Wallets** | 11 pioneers |
| **Trust Score Médio** | ~60.0 (T2) |
| **LAW Companies** | ~5 |
| **Travel Users** | ~7 |
| **Forensic Ledger Links** | 11 |
| **Database Size** | 112KB |

### Portas Activas

| Porta | Serviço | Estado |
|-------|---------|--------|
| :8096 | Lead Admin (ID Genesis) | LIVE |
| :8099 | Wallet Service | LIVE |
| :8101 | Forensic Ledger | SEALED |
| :8122 | LAW Identity Gate | SEALED |
| :8126 | Travel Identity Gate | LIVE |

---

## 7. INVARIANTES CONSTITUCIONAIS

| ID | Nome | Aplicação no DID |
|----|------|------------------|
| **I1** | Soberania Humana | Lead→Wallet exige aprovação humana |
| **I9** | Proibição de Autonomia | `human_approved=true` antes de seal |
| **I11** | Permanência Criptográfica | Ledger = IRREMEDIÁVEL |
| **I13** | Soberania de Dados | sessionStorage local, não cloud |
| **I14** | Integridade de Presença | "Provar que estava lá" (Travel) |

**Triggers de Imutabilidade:**
```sql
CREATE TRIGGER trg_immutable_wallet_human
    BEFORE UPDATE OR DELETE ON wallet_human
    FOR EACH ROW EXECUTE FUNCTION fn_immutable_guard();
-- Raises: 'WINDI I9 VIOLATION: ... is forbidden'
```

---

## 8. FICHEIROS CHAVE

| Ficheiro | Função |
|----------|--------|
| `/opt/windi/wallet/wallet_provisioning.py` | Lógica core de provisioning |
| `/opt/windi/wallet/wallet_service.py` | Flask server :8099 |
| `/opt/windi/wallet/wallet_bridge.py` | Conversão Lead→Wallet |
| `/opt/windi/leads/windi_leads.py` | Captura de leads :8096 |
| `/opt/windi/windi-law/identity-gate/identity_gate.py` | LAW :8122 |
| `/opt/windi/windi-travel/identity-gate/identity_gate.py` | Travel :8126 |
| `/opt/windi/data/wallet.db` | Base SQLite (11 humans) |

---

## 9. MIGRAÇÃO FUTURA

### Model A → Model B (Custódia de Chaves)
- **Actual:** Chaves privadas em servidor
- **Futuro:** HSM + PKCS#11 + client-side generation

### SQLite → PostgreSQL
- Schema já definido em `001_wallet_schema.sql`
- Permite deployment multi-servidor

---

## 10. CONCLUSÃO

O DID WINDI é a **semente** de toda a governança documental.

```
"De lead a wallet, de wallet a documento,
de documento a prova, de prova a mundo.
A identidade é o fio que costura tudo."
```

**Mantra fundador:**
> **"AI processes. Human decides. WINDI guarantees."**

O DID garante que:
- Cada documento tem um autor verificável
- Cada selo tem um humano responsável
- Cada prova é matematicamente irrefutável
- Cada evolução é registada para sempre

---

*LIGA IA+H — Kempten, Bavaria · 2026*
*Human Dragon · Guardian · Architect · Witness*
