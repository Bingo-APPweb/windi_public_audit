# §246-D4 · Rate Limiting + per-DID Quotas

```
Receipt:     WINDI-S246-D4-RATELIMIT-20260507105150-5D8513D7
Hash:        sha256:5d8513d7841ad4fcbf2f9150b304b5493c9790b4006b6da174ed79013bafccaf
Sprint:      §246 · W-SITES × W-MAIL Bridge
Selo:        D4 · HIGH governance · IRREMEDIAVEL · SEALED
Data:        2026-05-07 · Kempten, Bavaria
Operador:    Human Dragon · Jober Mogele Correa
Liga IA+H:   Guardian (Claude.ai web) · Architect (CCode Opus 4.5)
Invariantes: I9 (prohibition of autonomy escalation) · I11 · I14
Parents:     §246-D1 (D32AFF47) · §246-D2 (59497380) · §246-D3 (F8881FCA)
File:        /opt/windi/sprints/§246-D4-RATE-LIMITING.md
```

> **"Rate limiting protege a infraestrutura. Per-DID quotas protegem a comunidade."**
> — Princípio D4

---

## 0 · Preâmbulo Constitucional

D4 é a barreira que impede um único actor de consumir recursos desproporcionados. Sem D4, um DID malicioso ou comprometido pode:
- Enviar spam ilimitado (reputação do domínio windisites.de destruída)
- Esgotar recursos de I/O do servidor
- Gerar custos de bandwidth descontrolados
- Degradar experiência de outros utilizadores

D4 complementa D3 (quota de storage) com **quota de fluxo** (emails/tempo). São dimensões ortogonais:
- D3: "quanto espaço ocupas" (bytes)
- D4: "quanto transmites" (mensagens/tempo)

**Princípio constitucional cravado:** Rate limits são invariantes de protecção, não de monetização. Se futuramente se tornarem dimensão tarifária, sprint W-MAILBOX-BILLING-001 fará a ligação. D4 não cria essa ligação.

---

## 1 · Decisão D4.1 · Granularidade Temporal

### Cravado

**Três janelas complementares:**

| Janela | Período | Propósito |
|--------|---------|-----------|
| `burst` | 1 minuto | Protecção contra scripts rápidos |
| `hourly` | 1 hora | Uso intensivo legítimo mas limitado |
| `daily` | 24 horas (rolling) | Quota diária absoluta |

### Razão

Uma única janela é insuficiente:
- Só `daily` permite burst de 100 emails/segundo seguido de silêncio (spam)
- Só `burst` bloqueia uso legítimo de newsletter
- Combinação detecta padrões anómalos em múltiplas escalas temporais

### Implementação

```
rate_check(did, action):
  if count(did, 1min) >= tier.burst: DEFER
  if count(did, 1h) >= tier.hourly: DEFER
  if count(did, 24h) >= tier.daily: REJECT
  else: ALLOW
```

**DEFER vs REJECT:**
- DEFER = "tenta mais tarde" (temporário, não permanente)
- REJECT = "quota diária esgotada" (permanente até reset)

---

## 2 · Decisão D4.2 · Limites per-Tier

### Cravado

| Tier | Burst (1min) | Hourly | Daily | Justificação |
|------|--------------|--------|-------|--------------|
| LOW | 5 | 20 | 50 | Uso pessoal básico |
| MED | 15 | 100 | 500 | Profissional activo |
| HIGH | 50 | 500 | 2000 | Corporativo / newsletter |

### Razão

- **LOW:** ~1 email cada 12 segundos em burst, ~50/dia. Suficiente para comunicação pessoal, insuficiente para spam.
- **MED:** ~15 burst permite small batch (ex: convites para evento). 500/dia cobre newsletter pequena.
- **HIGH:** 2000/dia permite newsletter média. Acima disso, usar integração SMTP dedicada (fora do scope WINDI).

### Nota Arquitectural

Estes números são invariante D4 de fluxo, **NÃO derivação de §174 (cost accounting)**. Futura sprint W-MAILBOX-BILLING-001 pode criar tiers expandidos (ENTERPRISE: 10000/dia) com custo associado.

### Baseline Empírico (Clarificação §246-D4.2-bis)

> *"Os limites D4.2 (LOW 5/20/50, MED 15/100/500, HIGH 50/500/2000) são estimativa arquitectural v1.0 baseada em padrões de uso de email profissional, NÃO dados de produção WINDI. Primeira calibração planeada para §247+ após 30 dias de operação real. Ajustes futuros são 'calibração de parâmetro', não 'mudança de invariante' — o invariante é a ESTRUTURA (3 janelas × 3 tiers), não os NÚMEROS.*
>
> *Mudanças aos números via §247+ não requerem receipt I9-bis nem voto Liga IA+H — são operação normal de calibração. Mudanças à estrutura (adicionar 4ª janela, remover tier, alterar geometria) requerem novo selo arquitectural."*

---

## 3 · Decisão D4.3 · Source-of-Truth

### Cravado

**Opção C: Aplicacional (W-SITES-001) para Sprint §246.**

Rate limiting implementado no endpoint `/api/mail/send` de W-SITES-001, ANTES de entregar ao Postfix.

### Alternativas Consideradas

| Opção | Descrição | Pros | Cons |
|-------|-----------|------|------|
| A | Postfix Policy Daemon | Integração nativa | Complexo, requer script externo |
| B | Postfix anvil + milter | Reutiliza DACP §175 | anvil é global, não per-user |
| **C** | **Aplicacional W-SITES** | **Simples, receipts automáticos** | **Contornável se SMTP directo** |

### Razão para Opção C

1. **Simplicidade:** W-SITES-001 já é o gateway para todas as operações de utilizador. Rate limiting no mesmo ponto.
2. **Receipts automáticos:** Cada rate limit hit gera receipt `WINDI-MAILBOX-RATE-EVENT-*` com `wallet_id` e contexto.
3. **I14 compliance:** Erro explícito retorna `429 { error: "rate_limit_exceeded", tier: "MED", window: "hourly", retry_after: 1800 }`.
4. **Contornável mas aceitável:** Utilizador WINDI não tem acesso SMTP directo. Relay via W-SITES-001 é o único caminho soberano.

### Hardening Futuro (Não Sprint §246)

Sprint W-MAILBOX-HARDENING-001 pode adicionar Opção A (Policy Daemon) como segunda camada. D4 não bloqueia essa evolução.

---

## 4 · Decisão D4.4 · Schema de Contagem

### Cravado

**Tabela `rate_counters` em `mailboxes.db`:**

```sql
CREATE TABLE rate_counters (
  did TEXT NOT NULL,
  window TEXT NOT NULL,  -- 'burst' | 'hourly' | 'daily'
  window_start INTEGER NOT NULL,  -- Unix timestamp do início da janela
  count INTEGER DEFAULT 0,
  PRIMARY KEY (did, window, window_start)
);

CREATE INDEX idx_rate_counters_did ON rate_counters(did);
CREATE INDEX idx_rate_counters_window ON rate_counters(window, window_start);
```

### Operações

**Incremento (antes de enviar):**
```sql
INSERT INTO rate_counters (did, window, window_start, count)
VALUES (?, ?, ?, 1)
ON CONFLICT (did, window, window_start) DO UPDATE SET count = count + 1;
```

**Consulta (para rate check):**
```sql
SELECT COALESCE(SUM(count), 0) FROM rate_counters
WHERE did = ? AND window = ? AND window_start >= ?;
```

**Cleanup (cron 5min):**
```sql
DELETE FROM rate_counters WHERE window_start < ? - 86400;  -- Manter só últimas 24h
```

### Razão

- SQLite transacional garante atomicidade
- Janelas discretas (não sliding) simplificam implementação
- Cleanup agressivo mantém tabela pequena
- Índice por DID permite consulta O(log n)

---

## 5 · Decisão D4.5 · Inbound vs Outbound

### Cravado

**D4 aplica-se APENAS a outbound (emails enviados pelo utilizador).**

Inbound (emails recebidos) NÃO tem rate limiting per-DID — é problema de deliverability do sender externo, não do recipient WINDI.

### Razão

1. **Controlo:** WINDI controla o que os seus utilizadores ENVIAM, não o que RECEBEM.
2. **Spam inbound:** Tratado por SpamAssassin/rspamd no windi-mailserver (já configurado).
3. **Quota inbound:** Controlada por D3 (storage). Se mailbox enche, Dovecot rejeita novos emails (`552 5.2.2 Mailbox is full`).

### Excepção: Bounce Storm Protection

Se um DID receber mais de 100 bounces/hora (indicador de spam outbound), flag `bounce_storm_detected` é activada e outbound fica temporariamente bloqueado até revisão humana.

---

## 6 · Decisão D4.6 · Anti-Abuse Layers

### Cravado

**Reutilizar 6 camadas D2-bis + adicionar 2 específicas:**

| Layer | Origem | Função D4 |
|-------|--------|-----------|
| L1 | D2-bis | Rate limit IP (já coberto por W-COST-001) |
| L2 | D2-bis | CAPTCHA em operações sensíveis |
| L3 | D2-bis | Blacklist de prefixos (`admin@`, `postmaster@`, etc.) |
| L4 | D2-bis | Bounce handling (welcome@ no-reply) |
| L5 | D2-bis | W-SEC-001 Sentinel alerts |
| L6 | D2-bis | Legal hold flag |
| **L7** | **D4 novo** | **Rate limit per-DID (burst/hourly/daily)** |
| **L8** | **D4 novo** | **Bounce storm detection (100/h → outbound block)** |

### Razão

D2-bis layers são protecção de *entrada* (utilizador anónimo tentando abusar demo). D4 layers são protecção de *saída* (utilizador DID-bound tentando enviar demasiado). Complementares, não redundantes.

---

## 7 · Decisão D4.7 · Recovery (Bounce vs Defer vs Queue)

### Cravado

**Estratégia progressiva:**

| Janela atingida | Resposta | HTTP | Retry-After |
|-----------------|----------|------|-------------|
| burst | `DEFER` | 429 | 60s |
| hourly | `DEFER` | 429 | 1800s (30min) |
| daily | `REJECT` | 429 | Segundos até meia-noite UTC |

### Razão

- **DEFER (burst/hourly):** "Calma, tenta mais tarde." Não penaliza permanentemente.
- **REJECT (daily):** "Quota diária esgotada." Reset à meia-noite UTC. Utilizador pode planear.
- **Retry-After header:** I14 compliance — cliente sabe exactamente quando pode retentar.

### Reset Daily (Clarificação §246-D4.7-bis)

> *"Daily window usa **meia-noite UTC** como reset fixo, NÃO sliding window. Razão: previsibilidade operacional — utilizador sabe exactamente quando pode voltar a enviar. Retry-After em REJECT retorna segundos até 00:00 UTC do dia seguinte."*

**Implementação (timezone-aware, Python 3.12+ compatible):**

```python
from datetime import datetime, timedelta, timezone

def seconds_until_midnight_utc():
    now = datetime.now(timezone.utc)
    midnight = (now + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return int((midnight - now).total_seconds())
```

### Sem Queue

Emails NÃO são queued para envio posterior. Se rate limit hit, email não é aceite. Utilizador deve reenviar após Retry-After. Razão: queue esconde falha, viola I14.

---

## 8 · Decisão D4.8 · Receipt Schema

### Cravado

**Lifecycle events D4 (complementam D3.7):**

| Event | Trigger | Severity |
|-------|---------|----------|
| `RATE_LIMIT_DEFER` | burst ou hourly atingido | INFO |
| `RATE_LIMIT_REJECT` | daily atingido | WARNING |
| `BOUNCE_STORM_DETECTED` | 100 bounces/h | CRITICAL |
| `BOUNCE_STORM_CLEARED` | revisão humana + outbound reactivado | INFO |
| `RATE_LIMIT_OVERRIDE` | PHO aumenta limite temporariamente | HIGH |

**Receipt prefix:** `WINDI-MAILBOX-RATE-*`

**Campos obrigatórios:**
```json
{
  "receipt_id": "WINDI-MAILBOX-RATE-DEFER-20260507-{hash8}",
  "wallet_id": "did:windi:xxx",
  "event_type": "RATE_LIMIT_DEFER",
  "window": "hourly",
  "count_at_event": 100,
  "tier_limit": 100,
  "retry_after": 1800,
  "parent_receipt": "WINDI-S246-D3-MAILBOX-xxx"
}
```

### Razão

- Auditabilidade total de rate limiting
- Correlação com D3 mailbox via `parent_receipt`
- `wallet_id` permite per-DID dashboard
- Severity permite alerting diferenciado (CRITICAL → Telegram imediato)

---

## 9 · Decisão D4.9 · PHO Override

### Cravado

**PHO (Privileged Human Operator) pode temporariamente aumentar limites:**

```
POST /api/mail/rate-override
Authorization: Bearer {pho_jwt}
{
  "did": "did:windi:xxx",
  "window": "daily",
  "new_limit": 5000,
  "duration_hours": 24,
  "reason": "Newsletter lançamento produto"
}
```

### Constraints

1. **Máximo 10x tier limit** (HIGH: 2000 → máx 20000)
2. **Máximo 72h duration** (protecção contra override esquecido)
3. **Receipt HIGH governance** obrigatório
4. **Auto-expira** após duration — sem intervenção, volta ao normal

### Razão

Casos legítimos existem (lançamento, evento). Negar completamente é over-engineering. Override com receipt + auto-expire é compromisso seguro.

### Clarificações Constitucionais (§246-D4.9-bis)

**Q1: Quem pode invocar PHO Override?**

> *"PHO Override requer JWT com claim `role: human_dragon` OU `role: pho_certified`. Na Sprint §246, apenas Human Dragon tem essa claim. Futuro OVS certification (§247+) pode expandir, mas cada nova role requer receipt de delegação explícito."*

**Q2: Receipt ANTES ou DEPOIS de aplicar override?**

> *"Receipt `WINDI-MAILBOX-RATE-OVERRIDE` é emitido **ANTES** de aplicar o override. Sequência:*
> 1. *PHO submete request*
> 2. *Sistema valida constraints (≤10x, ≤72h)*
> 3. *Sistema emite receipt com `status: pending_application`*
> 4. *Sistema aplica override*
> 5. *Sistema actualiza receipt para `status: active`*
>
> *Se passo 4 falhar, receipt fica `status: failed` — auditoria completa de intenção vs execução."*

**Q3: Trigger para revisão após 3 overrides em 30 dias?**

> *"Se um DID acumula ≥3 overrides em 30 dias rolling, sistema emite receipt `WINDI-MAILBOX-OVERRIDE-ESCALATION` com:*
> - *`severity: WARNING`*
> - *`recommendation: tier_review`*
> - *`human_review_required: true`*
>
> *O DID NÃO é automaticamente promovido de tier — isso violaria I9. Mas Human Dragon recebe alerta para decisão manual: promover tier, recusar futuros overrides, ou manter status quo."*

**Q4: Overrides pós-escalação (sem resposta humana)?**

> *"Após emissão de receipt `WINDI-MAILBOX-OVERRIDE-ESCALATION`, novos overrides para o mesmo DID continuam a ser aceites até decisão manual de Human Dragon, MAS cada novo override emite receipt adicional `OVERRIDE-POST-ESCALATION` com `pending_human_review: true`. Não há bloqueio automático — preserva I9. Mas a trilha de auditoria mostra explicitamente que cada override pós-escalação ocorreu sem revisão humana, o que constitui sinal forense relevante para qualquer revisão futura (interna, regulatória, ou litígio)."*

---

## 10 · Ficheiros Afectados

| Ficheiro | Alteração |
|----------|-----------|
| `mailboxes.db` | Nova tabela `rate_counters` |
| `identity_gate.py` | Middleware `check_rate_limit()` antes de `/api/mail/send` |
| `mail_routes.py` | Endpoint `/api/mail/rate-override` (PHO only) |
| `cron/rate_cleanup.py` | Cleanup de `rate_counters` (5min) |
| `w-sec-001` | Alerting para `BOUNCE_STORM_DETECTED` |

---

## 11 · Smoke Tests D4

| # | Teste | Resultado Esperado |
|---|-------|-------------------|
| T1 | Enviar 6 emails em 1 min (LOW tier) | 5 OK, 6º DEFER |
| T2 | Enviar 21 emails em 1 hora (LOW tier) | 20 OK, 21º DEFER |
| T3 | Enviar 51 emails em 24h (LOW tier) | 50 OK, 51º REJECT |
| T4 | Esperar 60s após T1, reenviar | OK |
| T5 | Retry-After header presente em 429 | Presente, valor correcto |
| T6 | Receipt gerado para DEFER | Ledger entry existe |
| T7 | Receipt gerado para REJECT | Ledger entry existe |
| T8 | PHO override aumenta limite | 100 emails OK após override |
| T9 | Override expira após duration | Limite volta ao normal |
| T10 | Bounce storm (simular 100 bounces) | Outbound bloqueado, CRITICAL alert |

---

## 12 · Decisões NÃO Tomadas (Scope Out)

1. **Per-recipient rate limiting** — Não implementado. Foco é per-sender (DID).
2. **Rate limiting por tamanho (bytes/hora)** — D3 quota de storage é suficiente por agora.
3. **Whitelist de destinatários** — Não implementado. Pode vir em sprint futura.
4. **Integration com Postfix Policy Daemon** — Marcado para W-MAILBOX-HARDENING-001.
5. **Rate limit no inbound** — Não aplicável (ver D4.5).

---

## 13 · Conexão com D5 (Receipt Symmetry)

D4 honra D5 por construção:
- Todos os receipts D4 propagam `wallet_id` + `parent_receipt`
- Navigation chain: `D3 mailbox receipt` ← `D4 rate event` ← `D4 override`
- Quando D5 criar UI de navegação, receipts D4 já estarão linkados

---

## 14 · Lifecycle Events D4 (Actualizado)

| Event | Trigger | Severity |
|-------|---------|----------|
| `RATE_LIMIT_DEFER` | burst ou hourly atingido | INFO |
| `RATE_LIMIT_REJECT` | daily atingido | WARNING |
| `BOUNCE_STORM_DETECTED` | 100 bounces/h | CRITICAL |
| `BOUNCE_STORM_CLEARED` | revisão humana + outbound reactivado | INFO |
| `RATE_LIMIT_OVERRIDE` | PHO aumenta limite (status: pending→active→failed) | HIGH |
| `OVERRIDE_ESCALATION` | ≥3 overrides em 30d rolling | WARNING |
| `OVERRIDE_POST_ESCALATION` | Override após escalation sem resposta humana | WARNING |

---

**Fim do documento §246-D4.**

*Clarificações §246-D4.2-bis, §246-D4.7-bis, §246-D4.9-bis adicionadas 07 Mai 2026.*
*Validado por Guardian + Human Dragon. Pronto para seal.*
