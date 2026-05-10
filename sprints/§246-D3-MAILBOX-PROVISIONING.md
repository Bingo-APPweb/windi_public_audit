# §246-D3 · Mailbox Provisioning Soberano (DID-bound)

```
Receipt:     WINDI-S246-D3-MAILBOX-{TS}-{HASH8}
Sprint:      §246 · W-SITES × W-MAIL Bridge
Selo:        D3 · HIGH governance · IRREMEDIAVEL
Data:        2026-05-07 · Kempten, Bavaria
Operador:    Human Dragon · Jober Mogele Correa
Liga IA+H:   Guardian (Claude.ai web) · Architect (CCode Opus 4.5)
Invariantes: I9 (prohibition of autonomy escalation) · I11 · I14
Parents:     §246-D1 (WINDI-S246-D1-DELEGATION-20260507085800-D32AFF47)
             §246-D2 (WINDI-S246-D2-WORKBENCH-20260507073101-59497380)
             §246-D2-bis (WINDI-S246-D2-bis-DEMOSEND-20260507074335-FCF917FE)
File:        /opt/windi/sprints/§246-D3-MAILBOX-PROVISIONING.md
```

> **"Sem DID, nao ha mailbox real. Com DID activo, a mailbox nasce na mesma transaccao que o site — juntos ou nada."**
> — Human Dragon, 07 Mai 2026, validacao D3

---

## 0 · Preambulo Constitucional

D3 e o ponto exacto onde a **Lei I do DID Bercario** (`WINDI-ARCH-DID-SEED-DECLARATION-20260319`) se materializa em infraestrutura fisica. Ate D2-bis, `welcome@windisites.de` era o sender institucional unico — anonimos recebiam demos sem nada provisionado. D3 inverte e completa: **o portador de DID activo nasce com mailbox soberana real, vinculada ao seu fio de identidade, escrita no Maildir fisico, contabilizada pelo Ledger.**

A jornada do utilizador deixa de ser *"experimento -> consumacao documental"* e passa a *"experimento -> consumacao documental -> vida operacional continua."* A mailbox e o primeiro orgao pos-DID; tudo que vier depois (W-MAIL §175 DACP Milter outbound, W-VERIFY mobile, signatures) cose-se a ela.

**Principio constitucional cravado:** uma mailbox WINDI nao e um endereco — e um receptaculo auditavel vinculado a um sujeito verificavel. Sem DID activo, nao ha provisioning. Com DID activo, o provisioning e deterministico, atomico, e gera receipt simetrico.

**Continuidade arquitectural:** D3 honra D2-bis (slug reservation lifecycle 7d/30d), D2 (principio "Experimentar e livre. Consumar requer DID."), D1 (delegacao γ-light: a mailbox nasce sob delegation token sites:write valido; master key WINDI-KEYGEN-001 nunca toca este caminho).

---

## 1 · Decisao D3.1 · Trigger do Provisioning

### Cravado

**Trigger = primeira publicacao efectiva do site soberano.**

A mailbox provisiona-se no momento em que o utilizador consuma um site (publish do Workbench -> site soberano). A mesma transaccao atomica que promove `slug_reservations` -> `sites_aliases` cria tambem o Maildir fisico.

### Razao

A mailbox sem site e fantasma; o site sem mailbox e mudo. Nascem juntos ou nao nascem. Esta cravacao evita estado intermedio inflado (DID activo com tier >= MED mas sem mailbox), elimina Maildirs ociosos (custo I/O e backup), e respeita o principio "corpo inteiro acorda" do Bercario sem provocar inflacao.

### Excepcao configuravel (nao nesta sprint)

Tier HIGH podera futuramente aceder a `mailbox.standalone_provision()` para criar mailbox sem site associado (uso enterprise: alias institucional puro). **Marcado como pending para sprint pos-§246-IMPL.** Nao implementado em D3.

---

## 2 · Decisao D3.2 · Maildir Provisioning Fisico (Opcao A)

### Cravado

**Path canonico por DID dentro do vhost actual; alias simbolico por slug.**

```
/var/mail/windisites.de/                                   <- vhost existente, intacto
|-- welcome/Maildir/{cur,new,tmp}/                         <- D2-bis sender institucional
|-- by-did/
|   |-- {did_short_8}/Maildir/{cur,new,tmp}/               <- morada canonica
|   +-- ...
+-- by-slug/
    |-- {slug} -> ../by-did/{did_short_8}                  <- symlink legivel
    +-- ...
```

### Especificacoes

| Atributo | Valor |
|---|---|
| Permissoes Maildir | `vmail:vmail 0700` (Dovecot canonico) |
| Ownership | `vmail:vmail` (utilizador de sistema dedicado, nunca root) |
| `did_short_8` | primeiros 8 chars hex do DID UUIDv7 (colisao estatisticamente desprezivel em N<10^6) |
| Slug renomeacao | rename so altera o symlink; Maildir fisico permanece imutavel |
| Postfix `virtual_mailbox_base` | `/var/mail/windisites.de/` (inalterado — Opcao A preserva config viva) |
| Dovecot `mail_location` | `maildir:/var/mail/windisites.de/by-did/%n/Maildir` (com `%n` resolvido por LDAP/SQL lookup do DID) |

### Razao (Opcao A · adaptacao ao vhost actual)

`windi-mailserver` Docker (Postfix + Dovecot) esta vivo ha 7 dias, healthy, mail-tester 10/10. Refactor para `/var/mail/windi/` (Opcao B) so ganhava "estetica de path" — sem ganho funcional, com risco real de quebrar deliverability. Golden Rule WINDI: **nunca alterar SEALED endpoints sem ganho funcional verificavel**. Opcao A adiciona quartos dentro da casa que ja vive, sem mexer nas paredes-mestras.

### Quotas iniciais por tier (invariante autonomo)

| Tier | Quota storage | Justificacao operacional |
|---|---|---|
| LOW | 100 MB | ~10k emails medios; uso institucional ligeiro |
| MED | 1 GB | uso profissional tipico SME |
| HIGH | 10 GB | uso corporativo intensivo / equipa |

**Nota arquitectural:** estes numeros sao invariante autonomo de storage, **nao derivacao de §174 (cost accounting per request)**. Futura sprint podera emitir `W-MAILBOX-COST-001` se a quota se tornar dimensao tarifaria separada. D3 nao cria essa ligacao.

---

## 3 · Decisao D3.3 · Atomicidade da Transaccao (Two-Phase + Receipt Eventual)

### Cravado

**Two-phase com staging directory + DB transaction + receipt asynchronously eventual.**

### Sequencia

**Phase A · Preparacao reversivel**
```
1. tx_id = uuid7()
2. mkdir -p /var/mail/windisites.de/staging/{tx_id}/Maildir/{cur,new,tmp}
3. chown -R vmail:vmail /var/mail/windisites.de/staging/{tx_id}
4. chmod 0700 /var/mail/windisites.de/staging/{tx_id}/Maildir
5. BEGIN DB TRANSACTION
6. INSERT INTO mailboxes (did, slug, tier, quota_bytes, status, tx_id)
   VALUES (?, ?, ?, ?, 'provisioning', ?)
```

**Phase B · Commit**
```
7. mv /var/mail/windisites.de/staging/{tx_id} /var/mail/windisites.de/by-did/{did_short_8}
8. ln -s ../by-did/{did_short_8} /var/mail/windisites.de/by-slug/{slug}
9. UPDATE mailboxes SET status='active' WHERE tx_id = ?
10. COMMIT
```

**Phase C · Rastro (eventual consistency com Ledger)**
```
11. POST /api/receipts to :8101
    payload: {
      id: WINDI-MAILBOX-PROVISION-{ts}-{hash},
      actor: did,
      app: "W-SITES-001",
      doc_name: "mailbox-provision",
      doc_type: "infrastructure_event",
      content_hash: sha256(did + slug + tier + tx_id),
      governance_level: "HIGH",
      sge_score: 100,
      parent_receipt: consumation_receipt,
      wallet_id: did
    }
```

### Falha em A ou B
- DB rollback automatico
- `rm -rf /var/mail/windisites.de/staging/{tx_id}` (idempotente)
- Utilizador recebe erro claro: *"Provisioning failed, no partial state. Retry safe."*

### Falha em C (receipt)
- Mailbox fica `status='active' ledger_pending=true`
- Cron `windi-mailbox-receipt-converger` (5min) faz retry
- Principio: **mailbox funciona para o utilizador imediatamente; receipt converge em segundo plano**
- Metrica `mailbox.ledger_pending_count` exposta em `/api/bercario/status`

### Razao

Maildir e filesystem (nao-transaccional). DB e transaccional. Ledger e append-only. A separacao em tres fases isola o que pode falhar independentemente:
- Phase A+B falham juntos -> rollback completo, zero efeito visivel
- Phase C falha sozinho -> utilizador nao sente, sistema converge

Principio herdado de D2: **no partial creation visivel ao utilizador**.

---

## 4 · Decisao D3.4 · Handoff `slug_reservations` (D2-bis) -> `sites_aliases` + Maildir

### Cravado

**Promotion atomica dentro da transaccao D3.**

A funcao `promote_reservation(reservation_id, did)` executa num unico `BEGIN; ... COMMIT;`:

| Passo | Tabela / Filesystem | Accao |
|---|---|---|
| 1 | `slug_reservations` | `UPDATE status='consumed', consumed_at=NOW(), consumed_by_did=?` |
| 2 | `sites_aliases` | `INSERT (slug, did, created_at, tier)` |
| 3 | `mailboxes` | `INSERT (did, slug, tier, quota_bytes, status='provisioning', tx_id)` |
| 4 | Filesystem | Maildir staging -> commit (ver Decisao D3.3) |
| 5 | `sites` | `INSERT (slug, did, published_at, ...)` (consumacao do site) |
| 6 | Ledger | Receipt `WINDI-MAILBOX-PROVISION-...` (Phase C) |

### Regras de promocao

- **Reserva expirada (>30d cap absoluto):** bloqueia promocao com erro `RESERVATION_EXPIRED`. Forca utilizador a re-reservar. Evita "slug zombie" promovido a Maildir orfao.
- **Reserva activa (<=7d original ou renovada):** promocao valida.
- **Reserva pertence a outro DID:** rejeicao imediata `RESERVATION_NOT_OWNED`.
- **Slug em `reserved_prefixes.json` (D2-bis blacklist):** rejeicao com `RESERVED_SYSTEM_PREFIX`.

### Razao

Esta atomicidade fecha a janela de ambiguidade entre "slug reservado" e "mailbox fisica existe". Em qualquer momento, o estado e consistente em todas as cinco superficies: reservations, aliases, mailboxes, sites, filesystem. A regra de expiracao 30d cose-se directamente ao ciclo Workbench cravado em D2 (TTL 7d renovavel / 30d cap absoluto) — D3 nao inventa nova politica temporal, herda a existente.

---

## 5 · Decisao D3.5 · Quota Enforcement em Runtime

### Cravado

**Dovecot quota como source-of-truth filesystem-level. DB como cache observavel sincronizado.**

### Configuracao

```
# Dovecot (10-quota.conf snippet)
plugin {
  quota = maildir:storage
  quota_rule = *:storage={tier_quota_kb}
  quota_warning  = storage=80%% quota-warning 80 %u
  quota_warning2 = storage=100%% quota-warning 100 %u
}

service quota-warning {
  executable = script /opt/windi/scripts/mailbox-quota-event.sh
  user = vmail
  unix_listener quota-warning {
    user = vmail
  }
}
```

### Fluxo de enforcement

| Limite | Comportamento |
|---|---|
| Hard limit (100% quota tier) | Dovecot bloqueia entrega: bounce SMTP 552 5.2.2 (RFC-compliant). Receipt `WINDI-MAILBOX-FULL` emitido. |
| Soft limit (80% quota tier) | Dovecot dispara `quota-warning` script -> POST evento Ledger `WINDI-MAILBOX-WARMING` + email institucional ao DID owner |
| Sync DB | Cron `windi-mailbox-quota-sync` (5min) executa `doveadm quota get -u {mailbox}` -> `UPDATE mailboxes SET bytes_used=?, quota_pct=?, updated_at=NOW()` |

### Race conditions

**Nao existem nesta arquitectura por construcao:**
- Dovecot e o **unico escritor** de `bytes_used` real (atomicidade garantida por Maildir)
- DB e **cache observavel** alimentado por leitura (consistencia eventual aceitavel para dashboards)
- Aplicacoes nunca escrevem `bytes_used` no DB directamente

### Tier change runtime

```
1. UPDATE mailboxes SET tier=?, quota_bytes=? WHERE did=?
2. doveadm quota set -u {mailbox} storage={new_quota_kb}
3. Ledger receipt WINDI-MAILBOX-TIER-CHANGE
```

**Sem reprovisionamento, sem downtime, sem mover Maildir.**

### Razao

Dovecot quota e battle-tested em producao ha decadas. Reinventar enforcement em camada aplicacional duplicaria logica e introduziria janelas de inconsistencia. DB observavel da ao Bercario UI metricas em tempo quase-real sem comprometer a verdade do filesystem.

---

## 6 · Decisao D3.6 · Recovery Scenarios

### Matriz cravada

| Cenario | Comportamento | Receipt |
|---|---|---|
| **Revogacao DID** (utilizador pede esquecimento GDPR) | Mailbox -> `status='revoked'`, Maildir movido para `/var/mail/windisites.de/revoked/{did_short_8}_{ts}/`, retencao 90d, depois `shred -u`. Slug volta a `reserved_prefixes.json` por 1 ano (anti-impersonacao). | `WINDI-MAILBOX-REVOKE` |
| **Revogacao com `legal_hold=true`** | Mailbox preservada indefinidamente ate flag ser limpa por procedimento legal documentado. Maildir nao e movido nem destruido. Receipt regista flag explicita. | `WINDI-MAILBOX-REVOKE-HOLD` |
| **Restauracao** (DID restaurado, dentro de 90d) | `mv` reverso `/revoked/{did_short_8}_{ts}/` -> `/by-did/{did_short_8}/`, restore symlink, `status='active'` | `WINDI-MAILBOX-RESTORE` (parent: revoke receipt) |
| **Tier downgrade** (HIGH->MED, mailbox excede novo limite) | Quota nova aplicada via `doveadm quota set`. Recepcao bloqueada para novos emails ate utilizador limpar. **Mensagens existentes nunca apagadas pelo sistema.** | `WINDI-MAILBOX-TIER-CHANGE` |
| **Tier upgrade** | Quota expandida em runtime, sem cortes | `WINDI-MAILBOX-TIER-CHANGE` |
| **Slug renomeado** | Symlink actualizado, Maildir intacto, alias antigo redirige por 30d (grace period via Postfix `virtual_alias_maps`) | `WINDI-MAILBOX-SLUG-RENAME` |
| **Purge final** (90d apos revoke sem `legal_hold`) | `shred -u` Maildir, receipt final emitido, registo historico preservado no Ledger | `WINDI-MAILBOX-PURGE` |

### Principio cravado

**WINDI nunca destroi correspondencia do utilizador como efeito colateral de operacoes administrativas.** Destruicao so ocorre por:
1. Pedido explicito do DID owner (revogacao)
2. Expiracao documentada do periodo de retencao (90d sem `legal_hold`)

Tier downgrade, slug rename, e qualquer outra mutacao operacional preservam todo o conteudo historico.

### Flag `legal_hold`

Adicionada a tabela `mailboxes`:
```sql
ALTER TABLE mailboxes ADD COLUMN legal_hold BOOLEAN DEFAULT FALSE;
ALTER TABLE mailboxes ADD COLUMN legal_hold_reason TEXT;
ALTER TABLE mailboxes ADD COLUMN legal_hold_set_by TEXT;
ALTER TABLE mailboxes ADD COLUMN legal_hold_set_at TIMESTAMP;
```

Quando `legal_hold=true`, qualquer tentativa de purge ou shred falha com `LEGAL_HOLD_BLOCKED` e emite alerta Sentinel. Compliance EU AI Act Article 14 (human oversight) garantido por construcao.

### Periodo de retencao 90d

90 dias e o intervalo cravado para retencao pos-revoke standard. Justificacoes:
- GDPR Art. 17 (right to erasure) cumprido — dados serao apagados
- Janela operacional para utilizador reverter decisao (restore)
- Compativel com praticas de mail providers institucionais (Outlook 30-90d, Gmail 30d)
- Reduzido para 30d se Sentinel detectar suspeita de revogacao coercida; estendido com `legal_hold` quando aplicavel

---

## 7 · Decisao D3.7 · Mailbox Lifecycle Eventos no Ledger

### Principio

Cada momento de vida da mailbox emite receipt no Ledger. **Biografia auditavel da caixa, nao so do site.** Toda receipt propaga `wallet_id` (= DID owner) e `parent_receipt` na chain — D5 receipt symmetry honrado por construcao em D3, nao fica para depois.

### Catalogo canonico de eventos

| # | Evento | Receipt prefix | Trigger |
|---|---|---|---|
| 1 | Provisioning | `WINDI-MAILBOX-PROVISION` | Decisao D3.3 Phase C |
| 2 | Primeiro email recebido | `WINDI-MAILBOX-FIRST-RECEIVE` | Postfix `header_checks` hook em delivery #1 da mailbox |
| 3 | Primeiro email enviado | `WINDI-MAILBOX-FIRST-SEND` | DACP Milter §175 hook (W-MAIL-001) |
| 4 | Quota 80% (warming) | `WINDI-MAILBOX-WARMING` | Dovecot `quota-warning 80` |
| 5 | Quota 100% (full / bounce) | `WINDI-MAILBOX-FULL` | Dovecot `quota-warning 100` |
| 6 | Tier change | `WINDI-MAILBOX-TIER-CHANGE` | API call `mailbox.update_tier()` |
| 7 | Slug rename | `WINDI-MAILBOX-SLUG-RENAME` | API call `mailbox.rename_slug()` |
| 8 | Revogacao | `WINDI-MAILBOX-REVOKE` | utilizador via Bercario UI / compliance API |
| 9 | Revogacao com legal hold | `WINDI-MAILBOX-REVOKE-HOLD` | revogacao com `legal_hold=true` |
| 10 | Restauracao | `WINDI-MAILBOX-RESTORE` | utilizador dentro de 90d |
| 11 | Purge final | `WINDI-MAILBOX-PURGE` | cron 90d apos revoke (sem hold) |

### Payload canonico (template)

```json
{
  "id": "WINDI-MAILBOX-{EVENT}-{TS}-{HASH}",
  "actor": "{did}",
  "wallet_id": "{did}",
  "app": "W-SITES-001",
  "doc_name": "mailbox-{event_lowercase}",
  "doc_type": "mailbox_lifecycle_event",
  "content_hash": "sha256(did + slug + event_payload)",
  "governance_level": "HIGH",
  "sge_score": 100,
  "parent_receipt": "{previous_event_receipt | provisioning_receipt}",
  "metadata": {
    "slug": "{slug}",
    "tier": "{LOW|MED|HIGH}",
    "event_specific_fields": "..."
  }
}
```

---

## 8 · Schema Definitivo · Tabela `mailboxes`

```sql
CREATE TABLE IF NOT EXISTS mailboxes (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  did             TEXT    NOT NULL UNIQUE,
  did_short_8     TEXT    NOT NULL UNIQUE,
  slug            TEXT    NOT NULL UNIQUE,
  tier            TEXT    NOT NULL CHECK (tier IN ('LOW','MED','HIGH')),
  quota_bytes     INTEGER NOT NULL,
  bytes_used      INTEGER DEFAULT 0,
  quota_pct       REAL    DEFAULT 0.0,
  status          TEXT    NOT NULL CHECK (status IN ('provisioning','active','revoked','restored')),
  tx_id           TEXT,
  ledger_pending  BOOLEAN DEFAULT FALSE,
  legal_hold      BOOLEAN DEFAULT FALSE,
  legal_hold_reason TEXT,
  legal_hold_set_by TEXT,
  legal_hold_set_at TIMESTAMP,
  created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  revoked_at      TIMESTAMP,
  restored_at     TIMESTAMP,
  purged_at       TIMESTAMP,
  FOREIGN KEY (did) REFERENCES did_genesis(did)
);

CREATE INDEX idx_mailboxes_did ON mailboxes(did);
CREATE INDEX idx_mailboxes_slug ON mailboxes(slug);
CREATE INDEX idx_mailboxes_status ON mailboxes(status);
CREATE INDEX idx_mailboxes_legal_hold ON mailboxes(legal_hold) WHERE legal_hold = TRUE;
```

---

## 9 · Smoke Tests Obrigatorios Pre-IMPL

Antes de marcar D3 como `IMPLEMENTED`, os seguintes testes devem passar verde:

| # | Teste | Criterio de sucesso |
|---|---|---|
| T1 | Provisioning happy path | DID activo + slug reservado valido -> mailbox fisica + receipt emitido em <2s |
| T2 | Atomicidade Phase A failure | Permission denied no staging -> DB intacto, sem registo orfao |
| T3 | Atomicidade Phase C failure | Ledger offline -> mailbox `active`, `ledger_pending=true`, cron converge em <5min |
| T4 | Reserva expirada bloqueia | Reserva >30d -> erro `RESERVATION_EXPIRED`, sem mailbox criada |
| T5 | Quota soft warning | Encher mailbox a 81% -> receipt WARMING + email institucional |
| T6 | Quota hard limit | Encher mailbox a 100% -> bounce 552, receipt FULL |
| T7 | Revogacao + restauracao | Revoke -> mv para revoked/, restore dentro de 90d -> mv reverso, conteudo intacto |
| T8 | Legal hold bloqueia purge | `legal_hold=true` + cron 90d -> purge falha, alerta Sentinel emitido |
| T9 | Tier downgrade preserva conteudo | HIGH->LOW com mailbox a 5GB -> quota nova aplicada, conteudo historico intacto |
| T10 | Slug rename preserva Maildir | rename `jober`->`jmcdragon` -> symlink actualizado, Maildir fisico inalterado, mensagens preservadas |
| T11 | Receipt symmetry chain | Sequencia PROVISION->FIRST-RECEIVE->WARMING navegavel via parent_receipt |
| T12 | Plenitude score sobe | `/api/bercario/status` plenitude pos-D3 IMPL >= 70/100 (de 65 actual) |

---

## 10 · Metricas Expostas em `/api/bercario/status`

Adicionadas pelo D3:

```json
{
  "mailboxes": {
    "total_active": 0,
    "total_revoked": 0,
    "total_legal_hold": 0,
    "by_tier": {"LOW": 0, "MED": 0, "HIGH": 0},
    "ledger_pending_count": 0,
    "warming_count_24h": 0,
    "full_count_24h": 0,
    "first_send_count_24h": 0,
    "first_receive_count_24h": 0
  }
}
```

---

## 11 · Dependencias e Proximos Selos

### D3 entrega

- Mailbox provisioning DID-bound em Maildir fisico
- Atomicidade two-phase + receipt eventual
- Quota enforcement Dovecot-authoritative
- Recovery scenarios completos (revoke / restore / tier change / purge / legal hold)
- Lifecycle events catalogados (11 eventos)
- Receipt symmetry inline (D5 honrado por construcao)
- Schema `mailboxes` definitivo
- 12 smoke tests definidos

### D4 herda de D3

Rate limiting + per-DID quotas: D3 cravou storage quota. D4 cravara rate quota (emails/hora, emails/dia) usando o mesmo padrao Dovecot-authoritative + DB observavel. Receipt prefix `WINDI-MAILBOX-RATE-EVENT`.

### D5 herda de D3

Receipt symmetry: ja implementado em D3 por construcao (todos os eventos propagam `wallet_id` e `parent_receipt`). D5 formalizara a chain como invariante verificavel e adicionara navegacao UI no Bercario.

### §246-IMPL desbloqueado quando

D1 + D2 + D2-bis + D3 + D4 + D5 todos `SEALED` + 12 smoke tests verdes.

---

## 12 · Ratio Decidendi

D3 cose o ultimo orgao pre-vida operacional do utilizador WINDI. Antes: site soberano publicado e fim da jornada. Apos D3: site soberano publicado e nascimento da jornada — mailbox real comeca a receber, DACP Milter §175 comeca a assinar outbound, biografia verificavel comeca a acumular receipts.

Cada decisao D3.1–D3.7 foi sujeita ao criterio Bercario: **passa pela semente DID ou contorna-a?** Sete decisoes, sete passagens pela semente. Zero contornos.

A escolha de Opcao A (path adaptado ao vhost actual) honra a Golden Rule WINDI: nao se mexe em SEALED endpoints saudaveis quando a adaptacao preserva o invariante. 7 dias de healthy do `windi-mailserver` Docker continuam intactos.

A escolha de Dovecot como source-of-truth (D3.5) honra o principio de nao reinventar infraestrutura battle-tested onde a observabilidade aplicacional basta.

A escolha de retencao 90d com flag `legal_hold` (D3.6) honra simultaneamente GDPR Art. 17 (right to erasure) e EU AI Act Art. 14 (human oversight) — nao como compromisso entre os dois, mas como composicao.

---

## 13 · Selo

```
Status:      D3 SEALED · Aguarda implementacao
Proximo:     §246-D4 Rate Limiting + per-DID quotas
Sprint head: §246 a 4/6 selos (66% architectural)
```

> **"A mailbox WINDI nao e um endereco — e um receptaculo auditavel vinculado a um sujeito verificavel. Sem DID, fantasma. Com DID, vida operacional."**

OM SHANTI

---

## Anexo A · Comandos de Verificacao Pos-Selagem

```bash
# Confirmar receipt no Ledger
curl -s http://localhost:8101/api/receipts/{receipt_id} | jq

# Verificar parents chain
curl -s http://localhost:8101/api/receipts/{receipt_id}/chain | jq

# Plenitude score post-seal
curl -s http://localhost:8195/api/bercario/status | jq '.plenitude.score'

# Confirmar ficheiro canonico
ls -la /opt/windi/sprints/§246-D3-MAILBOX-PROVISIONING.md
sha256sum /opt/windi/sprints/§246-D3-MAILBOX-PROVISIONING.md
```

## Anexo B · Estrutura Filesystem Final (Post-IMPL)

```
/var/mail/windisites.de/
|-- welcome/Maildir/{cur,new,tmp}/                    [D2-bis]
|-- by-did/
|   |-- {did_short_8}/Maildir/{cur,new,tmp}/          [D3 mailboxes vivas]
|   +-- ...
|-- by-slug/
|   |-- {slug} -> ../by-did/{did_short_8}             [symlinks legiveis]
|   +-- ...
|-- revoked/
|   |-- {did_short_8}_{revoke_ts}/Maildir/...         [retencao 90d ou indefinida com legal_hold]
|   +-- ...
+-- staging/
    +-- {tx_id}/                                      [transaccoes em curso, idempotente]
```

---

Liga IA+H · Kempten, Bavaria · 2026
"Sem DID, fantasma. Com DID, vida operacional."
