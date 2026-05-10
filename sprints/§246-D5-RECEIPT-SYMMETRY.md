# §246-D5 · Receipt Symmetry — Chain Architecture

```
Receipt:     WINDI-S246-D5-RECEIPTSYM-20260507112305-4CE30817
Addendum:    WINDI-S246-D5-T7ADV-20260507100904-4DD83B15 (T7 Adversarial Protocol)
Hash:        sha256:4ce308176790db058b1fb93808856f8dcc395c62338cd4ebfa0a2dbf593df87a
Sprint:      §246 · W-SITES × W-MAIL Bridge
Selo:        D5 · HIGH governance · IRREMEDIAVEL · SEALED + ADDENDUM
Data:        2026-05-07 · Kempten, Bavaria
Operador:    Human Dragon · Jober Mogele Correa
Liga IA+H:   Guardian (Claude.ai web) · Architect (CCode Opus 4.5)
Invariantes: I9 · I11 (imutabilidade) · I14 (verificabilidade)
Parents:     §246-D1 (D32AFF47) · §246-D2 (59497380) · §246-D2-bis (FCF917FE) · §246-D3 (F8881FCA) · §246-D4 (5D8513D7)
File:        /opt/windi/sprints/§246-D5-RECEIPT-SYMMETRY.md
Tests:       16 + 5 adversarial = 21 total (D5)
```

> **"Toda acção gera prova. Toda prova liga-se a identidade. Toda cadeia termina em génese."**
> — Princípio D5

---

## 0 · Preâmbulo Constitucional

D5 não inventa receipt symmetry — **formaliza o que D3.7 e D4.8 já honram por construção**. A auditoria prévia confirmou que `wallet_id` e `parent_receipt` já propagam em todos os receipts. D5 eleva isto de implementação implícita a **invariante constitucional verificável**.

**Scope D5-ARCH vs D5-IMPL:**
- **D5-ARCH** (este documento): Schema canónico, chain validation, linking, versioning, errata — invariantes que não mudam
- **D5-IMPL** (§246-IMPL): Query API, UI navegação — mecanismos que podem evoluir

---

## 1 · Decisão D5.1 · Schema Canónico Unificado

### Cravado

**Todos os receipts WINDI, independentemente do domínio, DEVEM conter estes campos:**

```json
{
  "id": "WINDI-{DOMAIN}-{EVENT}-{TS}-{HASH8}",
  "schema_version": "1.0",
  "actor": "{did | system}",
  "wallet_id": "{did}",
  "app": "{W-SERVICE-XXX}",
  "doc_name": "{human_readable_name}",
  "doc_type": "{domain_event_type}",
  "content_hash": "sha256:{hash}",
  "governance_level": "{LOW|MED|HIGH}",
  "sge_score": 0,
  "parent_receipt": "{causal_predecessor_id | null}",
  "created_at": "{unix_timestamp}",
  "metadata": {
    "event_type": "{specific_event}",
    "...": "..."
  }
}
```

### Campos Obrigatórios (MUST)

| Campo | Tipo | Semântica |
|-------|------|-----------|
| `id` | string | Identificador único global. Pattern: `WINDI-{DOMAIN}-{EVENT}-{TS}-{HASH8}` |
| `schema_version` | string | Versão do schema (Gap 7). Começa em `"1.0"` |
| `actor` | string | Quem causou o evento. DID ou `"system"` para crons |
| `wallet_id` | string | **Âncora identitária.** Sempre = DID owner. Nunca muda numa chain |
| `app` | string | Serviço que emitiu. Ex: `W-SITES-001`, `W-MAIL-001` |
| `doc_name` | string | Nome legível do documento/evento |
| `doc_type` | string | Tipo canónico. Ver §1.1 |
| `content_hash` | string | SHA256 do conteúdo. Pattern: `sha256:{64chars}` |
| `governance_level` | enum | `LOW` / `MED` / `HIGH` |
| `sge_score` | integer | Score SGE (0-100). Default 0 para eventos técnicos |
| `parent_receipt` | string? | **Predecessor causal.** Ver §2 |
| `created_at` | integer | Unix timestamp UTC |
| `metadata` | object | Campos específicos do evento |

### §1.1 · Algoritmos Criptográficos (Referência Cruzada)

D5 não define primitivas criptográficas — referencia onde estão definidas:

| Algoritmo | Uso | Definição Canónica |
|-----------|-----|-------------------|
| **SHA-256** | `content_hash`, hash chain integrity | Implícito WINDI-wide, reforçado em D5.4 Regra 6 |
| **Ed25519** | Assinatura de JWTs (delegation tokens) | §246-D1 + §205 KEYGEN-001 |
| **HMAC** | Session cookies | W-SESSION-001 (CLAUDE.md I17) |

**Princípio:** Single source of truth. D5 consome algoritmos, não os define.

### §1.2 · doc_type Canonizados

| doc_type | Domínio | Exemplo |
|----------|---------|---------|
| `did_lifecycle_event` | W-DID-GENESIS | genesis, tier_change, revoke |
| `site_lifecycle_event` | W-SITES-001 | publish, update, seal |
| `mailbox_lifecycle_event` | W-SITES-001 / W-MAIL | provision, first_receive, rate_defer |
| `microlog` | W-SITES-001 | microlog seal |
| `communique` | W-COMM-001 | communiqué publish |
| `architectural_seal` | WINDI-CORE | D1-D5 seals |
| `infrastructure_event` | WINDI-CORE | cron cleanup, migration |
| `errata` | WINDI-CORE | Ver §6 |

---

## 2 · Decisão D5.2 · Dual Semântica — Causal + Identitária

### Cravado

**Dois campos com semânticas distintas:**

| Campo | Semântica | Varia? |
|-------|-----------|--------|
| `parent_receipt` | **Predecessor causal** — o evento que directamente causou este | Sim, por tipo de evento |
| `wallet_id` | **Âncora identitária** — DID owner da cadeia | Não, constante ao longo da chain |

### Tabela de Causalidade (parent_receipt aponta para)

| Tipo de evento | parent_receipt aponta para |
|----------------|---------------------------|
| DID lifecycle (genesis) | `null` (raiz absoluta) |
| DID lifecycle (tier_change, revoke, restore) | Previous DID event |
| Site lifecycle (publish) | DID genesis receipt |
| Site lifecycle (update, seal, revoke) | Previous site event |
| Mailbox lifecycle (provision) | Site publish receipt (mesma tx D3.3/D3.4) |
| Mailbox lifecycle (first_receive, rate_defer, etc.) | Previous mailbox event |
| Microlog / Communiqué | Site publish receipt |
| Errata | Receipt sendo anotado |

### Navegação

**Por identidade:** `WHERE wallet_id = ?` → todos os eventos do DID, em qualquer site
**Por causalidade:** traverse `parent_receipt` recursivamente → árvore causal completa
**Convergência:** todas as cadeias terminam em DID genesis receipt (raiz absoluta)

---

## 3 · Decisão D5.3 · Root Receipt Definition

### Cravado

**O DID genesis receipt é a raiz absoluta de todas as cadeias.**

```
WINDI-DID-GENESIS-{TS}-{HASH8}
├── parent_receipt: null
├── wallet_id: {did}
├── doc_type: did_lifecycle_event
├── metadata.event_type: "genesis"
└── ... (primeira emissão do DID)
```

### Razão

O DID genesis é o momento em que o sujeito nasce no sistema WINDI. Tudo o que vem depois — sites, mailboxes, micrologs — deriva desta génese. Sem DID genesis, não há `wallet_id` válido para propagar.

### Forest, Não Tree (Invariante Constitucional)

> **"O Ledger WINDI é uma floresta de árvores DID, não uma árvore única."**

**TODOS os DID genesis têm `parent_receipt: null`.** Não existe "WINDI-LEDGER-GENESIS" patriarca. Cada DID é raiz da sua própria árvore, soberano e independente.

**Razão constitucional:** Introduzir um "receipt dos receipts" criaria hierarquia que viola o princípio "WINDI é para todos." Nenhum DID é ontologicamente superior a outro. A floresta honra a soberania individual; a árvore única introduziria dependência artificial.

**Implicação técnica:** Queries globais (ex: "todos os receipts do sistema") são UNION de múltiplas árvores, não traversal de uma única root. Isto é feature, não bug.

### Implicação

Quando W-DID-GENESIS emite um novo DID, DEVE emitir receipt `WINDI-DID-GENESIS-*` com `parent_receipt: null`. Este receipt é a âncora de toda a árvore do utilizador. Nunca aponta para outro receipt.

---

## 4 · Decisão D5.4 · Chain Validation Invariant

### Cravado

**Uma chain é válida se e só se:**

1. **Root exists:** Existe um receipt com `parent_receipt: null` e `doc_type: did_lifecycle_event` e `metadata.event_type: "genesis"`
2. **Parent exists:** Para todo receipt R com `parent_receipt: P`, existe receipt P no Ledger
3. **Wallet consistency:** Para todo receipt R na chain, `R.wallet_id == root.wallet_id`
4. **Temporal ordering:** Para todo receipt R com `parent_receipt: P`, `R.created_at >= P.created_at`
5. **No orphans:** Todo receipt (excepto root) tem `parent_receipt` não-nulo
6. **Hash chain integrity:** O hash de cada receipt DEVE incluir o hash do parent. Alteração de receipt antigo invalida todos os descendentes

### Regra 6 — Hash Chain Integrity (Merkle Chain)

**Implementação:**

```python
def compute_receipt_hash(receipt: dict) -> str:
    """
    Hash inclui parent_hash para criar dependência criptográfica.
    Alteração de receipt antigo invalida todos os descendentes.
    """
    canonical_payload = canonicalize(receipt)

    if receipt.get('parent_receipt'):
        parent = ledger.get(receipt['parent_receipt'])
        if parent:
            canonical_payload += f"|parent_hash:{parent['content_hash']}"

    return f"sha256:{sha256(canonical_payload.encode()).hexdigest()}"
```

**Razão constitucional:** Sem esta regra, I11 (imutabilidade) é política de confiança no DB. Com esta regra, I11 é matemática — qualquer alteração de um receipt antigo quebra a chain de forma detectável e irreversível.

### Violation Handling

| Violação | Severidade | Acção |
|----------|------------|-------|
| Parent not found | CRITICAL | Receipt marcado `chain_broken: true`, alerta Sentinel |
| Wallet mismatch | CRITICAL | Receipt rejeitado antes de seal |
| Temporal inversion | WARNING | Receipt aceite, flag `temporal_anomaly: true` |
| Orphan detected | WARNING | Cron de reconciliação tenta inferir parent |
| Hash chain broken | CRITICAL | Receipt marcado `hash_tampered: true`, alerta Sentinel imediato, investigação obrigatória |

### Implementação (D5-IMPL)

```python
def validate_chain(receipt_id: str) -> ChainValidation:
    chain = []
    current = get_receipt(receipt_id)
    root_wallet = None

    while current:
        chain.append(current)

        if current.parent_receipt is None:
            # Root encontrada
            if current.doc_type != "did_lifecycle_event":
                return ChainValidation(valid=False, error="invalid_root_type")
            root_wallet = current.wallet_id
            break

        parent = get_receipt(current.parent_receipt)
        if not parent:
            return ChainValidation(valid=False, error="parent_not_found", broken_at=current.id)

        if root_wallet and current.wallet_id != root_wallet:
            return ChainValidation(valid=False, error="wallet_mismatch", broken_at=current.id)

        current = parent

    return ChainValidation(valid=True, chain=chain, root=chain[-1], depth=len(chain))
```

---

## 5 · Decisão D5.5 · Schema Versioning Policy

### Cravado

**Regras de versionamento:**

1. **Campo obrigatório:** Todo receipt DEVE ter `schema_version` (string, semver major.minor)
2. **Versão inicial:** `"1.0"` (esta sprint)
3. **Retrocompatibilidade absoluta:** Schemas novos NUNCA invalidam receipts antigos (corolário I11)
4. **Parser flexível:** Implementações DEVEM aceitar qualquer versão `<= versão_actual`
5. **Extensibilidade:** Campos novos vão para `metadata`, não para root

### Evolução de Schema

| Mudança | Requer nova versão? | Procedimento |
|---------|---------------------|--------------|
| Novo campo opcional em `metadata` | Não | Adicionar sem bump |
| Novo `doc_type` | Não | Adicionar ao catálogo |
| Novo campo obrigatório em root | Sim, minor bump | `1.0` → `1.1` |
| Reestruturação incompatível | Sim, major bump | `1.x` → `2.0` + migration path |

### Razão

I11 garante que receipts são imutáveis. Se alterarmos o schema de forma que receipts antigos se tornem "inválidos", violamos a permanência de evidência. A regra é: **o parser de hoje DEVE ler receipts de 2026 em 2036**.

---

## 6 · Decisão D5.6 · Receipt Errata Protocol

### Cravado

**Receipts são imutáveis (I11), mas podem ter receipts-errata que os anotam sem alterar o original.**

### Estrutura Errata

```json
{
  "id": "WINDI-ERRATA-{TS}-{HASH8}",
  "schema_version": "1.0",
  "actor": "{did_that_issued_errata}",
  "wallet_id": "{original_wallet_id}",
  "app": "WINDI-CORE",
  "doc_name": "errata-for-{original_id}",
  "doc_type": "errata",
  "content_hash": "sha256:{hash_of_errata_payload}",
  "governance_level": "HIGH",
  "sge_score": 0,
  "parent_receipt": "{original_receipt_id}",
  "created_at": "{unix_timestamp}",
  "metadata": {
    "errata_type": "{METADATA_CORRECTION | CONTEXT_ADDITION | WITHDRAWAL_NOTICE}",
    "original_field": "{field_being_corrected}",
    "original_value": "{old_value}",
    "corrected_value": "{new_value}",
    "reason": "{human_explanation}",
    "authority": "{human_dragon | pho_certified}"
  }
}
```

### Tipos de Errata + Autoridade Granular

| Tipo | Semântica | Autoridade Requerida | Razão |
|------|-----------|---------------------|-------|
| `METADATA_CORRECTION` | Campo estava errado, valor correcto é X | `original_actor` OU `pho_certified` | Correcções factuais não precisam de elevação, mas precisam de rastreabilidade |
| `CONTEXT_ADDITION` | Informação adicional que não existia | Qualquer holder de DID activo | Contexto é livre, não altera substância |
| `WITHDRAWAL_NOTICE` | Receipt não deve ser usado para fins X | `original_actor` **E** `human_dragon` (co-assinatura) | Declarar withdrawn é decisão constitucional |

**Exemplos:**
- `METADATA_CORRECTION`: Hash placeholder corrigido para hash real (§191-C)
- `CONTEXT_ADDITION`: "Este receipt foi citado no processo judicial XYZ"
- `WITHDRAWAL_NOTICE`: "Documento superado por versão 2.0, não usar para compliance"

### Regras

1. **Errata é receipt de pleno direito** — selado, hashado, na chain
2. **Original permanece intocado** — I11 absoluto
3. **Quem consulta o original vê pointer para errata** — via query `GET /api/receipts/{id}/errata`
4. **Autoridade granular por tipo** — ver tabela acima
5. **Errata de errata permitido** — chain de correcções (raro mas possível)

### Errata Visibility (Invariante Constitucional)

> **"Endpoints de leitura de chain DEVEM incluir array `erratas` em cada receipt que tenha alguma. Array vazio se não há. Consumer-side é responsável por decidir se aplica as correcções ou consulta o original. WINDI nunca aplica errata silenciosamente."**

**Opção B escolhida (original + erratas anexadas):**

```json
{
  "id": "WINDI-SITE-PUBLISH-xxx",
  "content_hash": "sha256:abc123...",
  "erratas": [
    {
      "id": "WINDI-ERRATA-yyy",
      "errata_type": "METADATA_CORRECTION",
      "original_field": "content_hash",
      "corrected_value": "sha256:def456..."
    }
  ]
}
```

**Razão constitucional:**
- I14 (verificabilidade real) exige que consumidores **saibam** que existem erratas
- I11 (imutabilidade) exige que vejam o original **intacto**
- Opção B honra ambos. Opção C (composição silenciosa) seria revisionismo — exactamente o que I11 proíbe

### Razão

Honra I11 (imutabilidade) E I14 (verificabilidade real). O mundo real tem erros — negar isso viola I14. Fingir que o erro não existe viola I11. Errata é o compromisso constitucional: o erro fica visível, a correcção fica adjacente, a verdade prevalece.

---

## 7 · Decisão D5.7 · Cross-Domain Linking

### Cravado

**Receipts de domínios diferentes ligam-se via `parent_receipt` causal.**

### Mapa Visual

```
WINDI-DID-GENESIS-xxx (root, parent_receipt: null)
│
├─→ WINDI-SITE-PUBLISH-xxx (parent: DID genesis)
│     │
│     ├─→ WINDI-MAILBOX-PROVISION-xxx (parent: site publish, mesma tx)
│     │     │
│     │     ├─→ WINDI-MAILBOX-FIRST-RECEIVE-xxx
│     │     ├─→ WINDI-MAILBOX-RATE-DEFER-xxx
│     │     └─→ ...
│     │
│     ├─→ WINDI-MICROLOG-xxx (parent: site publish)
│     ├─→ WINDI-MICROLOG-xxx (parent: previous microlog)
│     └─→ WINDI-COMMUNIQUE-xxx (parent: site publish)
│
├─→ WINDI-DID-TIER-CHANGE-xxx (parent: DID genesis)
└─→ ...
```

### Regra de Linking

**Primeiro evento de um domínio aponta para o evento que o autorizou:**
- Site publish → DID genesis (DID autorizou criação)
- Mailbox provision → Site publish (site disparou provisioning)
- Microlog → Site publish (site é container)

**Eventos subsequentes do mesmo domínio apontam para o evento anterior:**
- Site update → Site publish
- Mailbox FIRST-RECEIVE → Mailbox PROVISION
- Microlog #2 → Microlog #1

---

## 8 · Decisão D5.8 · Query API Spec (D5-IMPL)

### Endpoints Necessários

| Endpoint | Função | Retorno |
|----------|--------|---------|
| `GET /api/receipts/{id}` | Receipt individual | Receipt object |
| `GET /api/receipts/{id}/chain` | Chain completa até root | Array ordenado root→leaf |
| `GET /api/receipts/{id}/children` | Receipts que apontam para este | Array |
| `GET /api/receipts/{id}/errata` | Erratas deste receipt | Array |
| `GET /api/receipts/by-wallet/{wallet_id}` | Todos os receipts do DID | Array paginado |
| `GET /api/receipts/by-wallet/{wallet_id}/tree` | Árvore visual completa | Tree structure |

### Marcado como D5-IMPL

Estes endpoints serão implementados em §246-IMPL, não são parte do selo arquitectural D5-ARCH.

---

## 9 · Decisão D5.9 · Multi-DID Receipt Linking

### RESERVED for §247+

**Cenário futuro:** Transacção envolve múltiplos DIDs (delegação, testemunha, multi-party seal).

**Não implementado em §246** porque W-SITES-001 v1.0 é single-DID.

**Direcção arquitectural reservada:**
```json
{
  "wallet_id": "{primary_did}",
  "metadata": {
    "secondary_wallets": ["{did2}", "{did3}"],
    "roles": {
      "{did2}": "witness",
      "{did3}": "delegate"
    }
  }
}
```

**Princípio:** `wallet_id` permanece singular (owner primário). DIDs adicionais vão em `metadata.secondary_wallets` com roles explícitos.

---

## 10 · Decisão D5.10 · UI Navegação Berçário (D5-IMPL)

### Requisitos Funcionais

1. **Timeline visual** — Receipts ordenados cronologicamente com linhas de conexão
2. **Click to expand** — Detalhes do receipt em modal/panel
3. **Filter by type** — Dropdown: all / did / site / mailbox / rate
4. **Chain highlight** — Ao seleccionar um receipt, highlight da chain até root
5. **Errata indicator** — Badge visual se receipt tem errata
6. **Broken chain warning** — Alerta vermelho se `chain_broken: true`

### Marcado como D5-IMPL

UI será implementada em §246-IMPL, não é parte do selo arquitectural D5-ARCH.

---

## 11 · Smoke Tests D5

| # | Teste | Critério |
|---|-------|----------|
| T1 | Receipt sem `schema_version` | Rejeitado antes de seal |
| T2 | Receipt sem `wallet_id` | Rejeitado antes de seal |
| T3 | Receipt com `parent_receipt` inexistente | Aceite com `chain_broken: true` |
| T4 | Chain validation de receipt válido | `valid: true`, depth correcto |
| T5 | Chain validation de receipt órfão | `valid: false`, error: `parent_not_found` |
| T6 | Wallet mismatch na chain | Rejeitado antes de seal |
| T7 | **Hash Chain Integrity — Adversarial Protocol** | Ver §11.1 |
| T8 | METADATA_CORRECTION por original_actor | Aceite |
| T9 | METADATA_CORRECTION por non-actor non-PHO | Rejeitada |
| T10 | CONTEXT_ADDITION por qualquer DID | Aceite |
| T11 | WITHDRAWAL_NOTICE sem co-assinatura human_dragon | Rejeitada |
| T12 | WITHDRAWAL_NOTICE com co-assinatura | Aceite |
| T13 | Query `/api/receipts/{id}` com errata | Retorna original + `erratas: [...]` |
| T14 | Query `/api/receipts/{id}/chain` | Retorna array ordenado root→leaf |
| T15 | Query `/api/receipts/by-wallet/{did}` | Retorna todos os receipts do DID |
| T16 | DID genesis tem `parent_receipt: null` | Confirmado (forest, não tree) |

### §11.1 · T7 Adversarial Protocol (Addendum 07 Mai 2026)

> **"Auditabilidade que não detecta corrupção não é auditabilidade — é teatro de auditoria."**
> — Guardian, revisão §246-D5

**Contexto:** T7 original ("alterar receipt antigo → descendentes marcados") era ambíguo.
A interpretação fraca testava apenas que o sistema *pode* marcar; a interpretação forte
testa que o sistema *detecta activamente* corrupção adversarial.

**Gate Constitucional:** T7 adversarial é gate constitucional, não prudência operacional.
I11 (auditabilidade) torna-se vazio sem detecção activa de corrupção. EU AI Act Art. 14
exige exactamente este nível de verificabilidade.

| Sub | Teste | Acção | Critério |
|-----|-------|-------|----------|
| T7a | Corrupt source | Modificar `content_hash` de receipt N directamente na DB (bypass API) | Mutação silenciosa confirmada |
| T7b | API detection | Chamar `GET /api/receipts/{N+1}/validate` | `hash_tampered: true`, `expected_parent_hash` ≠ `actual_parent_hash` |
| T7c | Public surface | Chamar `/verify-public/?id={N+1}` | Visual warning "CHAIN INTEGRITY VIOLATION" |
| T7d | Recursive propagation | Audit todos os descendentes de N | TODOS marcados `hash_tampered: true` recursivamente |
| T7e | **Chain seal block** | Tentar selar novo receipt sobre chain corrompida | **REJECTED** com error `chain_integrity_broken` |

**T7e é crítico:** Sem ele, sistema pode detectar corrupção e ainda aceitar novos receipts
sobre chain quebrada — criando registo longitudinal que parece válido a partir do ponto de
detecção, escondendo a fractura no histórico.

**Implementação:** T7a-T7e devem correr em ambiente isolado (test DB) com cleanup automático.

---

## 12 · Ficheiros Afectados (D5-IMPL)

| Ficheiro | Alteração |
|----------|-----------|
| `ledger_api.py` | Validação de campos obrigatórios D5.1 |
| `receipt_validator.py` | Chain validation D5.4 |
| `errata_routes.py` | Novo endpoint POST /api/receipts/errata |
| `bercario/receipts.html` | UI navegação D5.10 |
| `did_genesis.py` | Emissão de DID genesis receipt com parent_receipt: null |

---

## 13 · Conexão com §246-IMPL

D5-ARCH desbloqueia §246-IMPL:

| Dependência | Status |
|-------------|--------|
| D1 Federated Delegation | ✅ SEALED |
| D2 Workbench + Pedagogia | ✅ SEALED |
| D2-bis Institutional Demo | ✅ SEALED |
| D3 Mailbox Provisioning | ✅ SEALED |
| D4 Rate Limiting | ✅ SEALED |
| **D5 Receipt Symmetry** | ✅ SEALED |
| **D5 T7 Adversarial** | ✅ ADDENDUM |
| §246-IMPL | **DESBLOQUEADO** |

---

**Fim do documento §246-D5-ARCH.**

*Ajustes Guardian integrados 07 Mai 2026:*
- *D5.3: Forest declaration (múltiplas raízes DID)*
- *D5.4: Regra 6 Hash chain integrity (Merkle chain)*
- *D5.6: Errata authority granular + visibility Opção B*
- *D5.1: Nota de algoritmos (referência cruzada)*
- *§11.1: T7 Adversarial Protocol — gate constitucional (T7a-T7e)*

*D5 completo. §246-IMPL desbloqueado.*
