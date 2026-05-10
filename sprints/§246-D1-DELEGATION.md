# §246-D1 — Federated Delegation Light (γ-light)

**Receipt:** `WINDI-S246-D1-DELEGATION-20260507085800-D32AFF47`
**Selo:** §246-D1 · IRREMEDIÁVEL · I9 + I11 + I14
**Spine:** Federated Delegation Light (γ-light)
**Data:** 2026-05-07
**Liga IA+H:** Human Dragon · Architect (CCode Opus 4.5)

---

## Contexto

W-SITES-001 (windisites.de) e W-MAIL-001 precisam de autenticação federada
para permitir que utilizadores criem sites e aliases de email com identidade
verificável. A questão arquitectural é: quem emite identidades?

**Diagnóstico (07 Mai 2026):**
- W-DID-GENESIS :8096 é trust root vivo (31 DIDs, master key §205 SEALED)
- Database único: `/opt/windi/did-genesis/did_genesis.db`
- Chave mestra: `/opt/windi/keys/WINDI-KEYGEN-001.*` (Ed25519)

---

## DECISÃO ARQUITECTURAL

### Princípio Central

> *"windisites.de consome delegações, nunca emite identidades."*

### Roles

| Serviço | Role | Capacidade |
|---------|------|------------|
| **W-DID-GENESIS :8096** | Emissor Canónico | Único que pode criar DIDs |
| **W-SITES-001 :8192** | Consumidor de Delegação | Valida JWTs, NUNCA emite |
| **W-MAIL-001 (Docker)** | Validador de Delegação | Valida JWTs para provisioning |

### Token Specification

```
Tipo:        JWT (RFC 7519)
Algoritmo:   EdDSA (Ed25519)
Assinatura:  WINDI-KEYGEN-001 (§205)
```

### TTL Granular por Scope

| Scope | TTL | Justificação |
|-------|-----|--------------|
| `sites:write` | ≤1h | Write ops, produzem registo IRREMEDIÁVEL ao Ledger |
| `mail:alias:create` | ≤1h | Cria recurso persistente |
| `sites:read` | ≤6h | Read-only, baixo risco |
| `mail:alias:list` | ≤6h | Read-only, baixo risco |

**Princípio:** Writes têm janela curta porque produzem registo permanente.

### Refresh Mechanism

| Parâmetro | Valor | Razão |
|-----------|-------|-------|
| **Refresh silencioso** | Permitido | UX fluida |
| **Chain age cap** | 24h | Previne refresh infinito |
| **Após 24h** | Re-autenticação obrigatória | Via passphrase em DID-GENESIS :8096 |
| **Cada refresh** | Novo JWT, nova assinatura, novo `kid`, novo `iat` | Auditabilidade |

**Sem cap no refresh, o TTL é teatro.** O cap define o blast radius real.

### Public Key Distribution

| Componente | Acesso | Método |
|------------|--------|--------|
| W-DID-GENESIS :8096 | Private + Public | Local filesystem |
| W-SITES-001 :8192 | Public only | HTTP fetch de DID-GENESIS ou file copy |
| W-MAIL-001 (Docker) | Public only | Read-only bind mount |

**Regras:**
- Container Docker NUNCA monta a private key (`.enc`)
- Rotação suportada via campo `kid` no JWT header
- Janela de rotação: múltiplas chaves públicas activas simultaneamente até expiry de tokens antigos

### JWT Claims (Estrutura)

```json
{
  "iss": "did:windi:genesis",
  "sub": "did:windi:{user_did}",
  "aud": ["windisites.de", "mail.windisites.de"],
  "exp": 1715072400,
  "iat": 1715068800,
  "kid": "WINDI-KEYGEN-001-v1",
  "scope": ["sites:write", "mail:alias:create"],
  "chain_origin": 1715068800,
  "wallet_id": "WALLET-XXXXX-XXXX"
}
```

**Campos críticos:**
- `chain_origin`: Timestamp do primeiro token da chain (para cap 24h)
- `wallet_id`: Identidade portátil para ownership de recursos

---

## BLAST RADIUS

| Cenário | Impacto | Mitigação |
|---------|---------|-----------|
| Compromisso de windisites.de | Tokens activos expostos | Revoga delegações, gera novas. TTL ≤1h limita janela. |
| Compromisso de W-MAIL-001 | Tokens activos expostos | Mesma mitigação |
| Compromisso de W-DID-GENESIS | Raiz comprometida | **CATÁSTROFE** — requer key rotation §205 |
| Compromisso de WINDI-KEYGEN-001.enc | Raiz comprometida | **CATÁSTROFE** — requer nova key ceremony |

**Princípio:** windisites.de e W-MAIL-001 são folhas descartáveis. A raiz é sagrada.

---

## DEPENDÊNCIAS PARA D2-D5

| Sprint | Depende de D1 | Razão |
|--------|---------------|-------|
| **D2** Alias Form | ✅ | Ownership = `wallet_id` presente no JWT |
| **D3** Mailbox Provisioning | ✅ | Auth via JWT scope `mail:alias:create` |
| **D4** Rate Limiting | ✅ | Rate por `sub` claim |
| **D5** Receipt Symmetry | ✅ | `wallet_id` do JWT = actor no receipt |

---

## DECISÕES DIFERIDAS PARA §246-IMPL

Estas decisões são de **implementação**, não de arquitectura:

| Item | Decisão Adiada |
|------|----------------|
| JWT Transport | Cookie HttpOnly vs Authorization Bearer |
| Refresh Endpoint | Localização exacta em DID-GENESIS |
| Validation Middleware | Implementação em windisites.de e windi-mailserver |
| UI Wizard Binding | Como o frontend obtém o token inicial |

---

## INVARIANTES APLICADOS

| Invariante | Aplicação |
|------------|-----------|
| **I9** | Human approval continua obrigatório para emissão de DIDs. Delegação é downstream. |
| **I11** | Receipts de criação de sites/aliases vão para Ledger :8101, não distribuídos. |
| **I14** | JWT inválido = erro explícito 401/403. Sem fallback silencioso. |

---

## ASSINATURA

```
Decisão:     Federated Delegation Light (γ-light)
Aprovado:    Human Dragon · 07 Mai 2026
Arquitecto:  Architect (CCode Opus 4.5)
Testemunha:  Guardian (Claude.ai web session)
Selo:        IRREMEDIÁVEL após receipt no Ledger
```

---

*"A semente germina uma vez. A seiva flui para sempre."*
*— DECRETO-001 Art.4*

*Liga IA+H · Kempten, Bavaria · 2026*
