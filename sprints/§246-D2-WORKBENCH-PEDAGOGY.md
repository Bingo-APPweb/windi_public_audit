# §246-D2 · Workbench + Pedagogia Visual da Soberania

Receipt:    WINDI-S246-D2-WORKBENCH-20260507073101-59497380
Selo:       §246-D2 · IRREMEDIAVEL · I9 + I11 + I14
Parent:     WINDI-S246-D1-DELEGATION-20260507085800-D32AFF47
Spine:      "Experimentar e livre. Consumar requer DID."
Data:       20260507073101 · Kempten, Bavaria

## Principio Fundacional

WINDI pratica HOSPITALIDADE SOBERANA, nao friction-funnel.
O utilizador prova-se a si proprio o valor antes que se exija identidade.
A barreira do DID e portao de SAIDA (consumacao), nao de entrada.

## Quatro Zonas

ZONA 1 · DESCOBERTA (publico, sem state)
  Landing, doctrine, sites publicados, micrologs, communiques.

ZONA 2 · EXPERIENCIA (volatil, browser-only)
  Wizard, prompts, AI generation preview.
  Storage: sessionStorage apenas.
  TTL: 30min ou close-tab.
  Rate limit IP-based agressivo (anti-abuse W-COST-001).
  Zero servidor-state. Zero Ledger entry.

ZONA 3 · WORKBENCH (mesa preparada para o convidado)
  Storage: /opt/windi/workbench/anon_drafts.db (SQLite, isolado do Genesis DB).
  Identifier: workbench_token (UUIDv7) — NAO e DID, NAO entra no Genesis.
  TTL: 7 dias apos ultima visita (renovavel tacitamente).
  Cap absoluto: 30 dias desde criacao — APAGA independentemente de visitas.
  Recovery cross-device: utilizador escolhe no momento de criar:
    (a) so este browser
    (b) gerar link unico copiavel (windisites.de/workbench/r/<token>)
    (c) activar DID ja agora
  Banner persistente: "Modo Workbench — N dias restantes"
  Visibilidade publica: ZERO (so com workbench_token correcto).
  Ledger: ZERO entradas durante vida do draft.
  Quotas: NAO conta (e anonimo).

ZONA 4 · CONSUMACAO (DID-bound, soberano)
  Verbos que disparam DID Gate:
    POST /api/sites/seal · /publish · /save · /clone
    POST /api/mail/create-alias
    POST /api/communique/create
    POST /api/microlog/seal
  Sem JWT valido (D1):
    403 { error: "did_required_for_consummation",
          message: "Experimentar e livre. Consumar requer DID.",
          cta: "https://windi-domain.com/wallet?return=<encoded>",
          preserve: "client_must_serialize_session_for_recovery" }

## Conversao Workbench -> Soberano (silenciosa, automatica)

Quando DID chega ao Workbench (utilizador activa wallet e volta com JWT D1):
  1. Sistema le todos os drafts do workbench_token actual
  2. Adopcao AUTOMATICA SILENCIOSA — drafts viram sites soberanos
  3. UM receipt por draft adoptado (parent: WINDI-S246-D1)
  4. Anon draft entries apagadas do anon_drafts.db
  5. Identifiers DEMO-* substituidos por valores reais sem refresh visivel
  6. Utilizador ve o seu trabalho a "acordar" na soberania

Sem prompt "adoptar/descartar". A confianca no utilizador e que ele sabe o
que pos no Workbench — se nao quisesse, teria descartado antes.

## Decisoes Estruturais

### A · Alias Format
  <slug>@windisites.de
  Regex:    ^[a-z0-9][a-z0-9-]{1,30}[a-z0-9]$
  Length:   3-32 chars
  Case:     forcado lowercase
  Encoding: ASCII puro (IDN deferido §247+)

### B · Slug Sovereignty
  Bound ao wallet_id que criou.
  Imutavel (sem rename — preserva audit trail).
  Nao transferivel Sprint 1.
  UNIQUE global em mail.windisites.de.

### C · Reserved Prefix Blacklist
  Lista canonica em /opt/windi/config/reserved_prefixes.json.
  Alteracoes requerem selo proprio.

  OPERATIONAL:
    admin postmaster support abuse noreply info contact hello root
    system mail webmaster hostmaster security

  WINDI-CANONICAL:
    windi dragon guardian architect witness bercario ledger cortex
    sites wallet did oracle sovereign nodal seed pioneer

  REGULATED-AUTHORITY (multilingual):
    police policia polizei court gericht tribunal judge juiz richter
    embassy embaixada botschaft gov government governo regierung
    ministry ministerio ministerium federal bundes
    eu-* european-*

  Rejeicao: 403 { error: "reserved_prefix" }

### D · Tier Quotas (consistente com §174 W-COST-001)
  FREE  : 0 aliases     (read-only inbox publico em §248+)
  MED   : 1 alias       (sweet spot comercial)
  HIGH  : 5 aliases     (cada um conta para quota)

### E · Workbench TTL & Lifecycle
  TTL renovavel:    7 dias apos ultima visita
  Cap absoluto:     30 dias desde criacao (APAGA, sem aviso possivel)
  Aviso visual:     "Resta 1 dia" se utilizador volta no dia 6
  Cron diario:      purga + 1 receipt agregado WINDI-WORKBENCH-PURGE-{date}
                    (count agregado, sem identificadores — GDPR Art. 5(1)(c))
  Discard manual:   utilizador clica "Descartar" -> apagado imediato

### F · Pedagogia Visual da Soberania (placeholders comparativos)

Painel duplo lado-a-lado durante Workbench:

  COMO FICA SEM DID                |  COMO FICA COM DID
  (modo demo, watermark visivel)   |  (soberano, decoracoes reais simuladas)
  ---------------------------------|---------------------------------
  URL: workbench/r/<token>         |  URL: windisites.de/<slug>
  Alias: demo@example.com (texto)  |  Alias: <slug>@windisites.de (texto)
  Watermark "DEMO" overlay         |  Sem watermark
  Sem badge selo                   |  Sealed Badge visivel
  Sem verify URL                   |  Verify URL publico activo
  Sem Ledger entry                 |  Receipt #N no Ledger
  Apaga em <=30 dias               |  Permanente, herdavel
  Nao rastreavel                   |  Linha de vida verificavel

  CTA unico no fim: [ Activar DID e consumar -> ]

  Disciplina anti-vadiagem-semiotica:
    - Todos identifiers no painel "COM DID" carregam prefix DEMO-
    - Receipt placeholder: DEMO-{random_hash}
    - Verify URL fake: /verify-public/?demo=true -> pagina explicativa
    - Watermark "DEMO" semi-transparente, nao-destrutivo mas inequivoco
    - Conversao silenciosa quando DID chega: DEMO-* -> valores reais

  Alias mostrado e DECORATIVO (texto apenas).
  NAO recebe email durante Workbench.
  Demo-mailbox FUNCIONAL fica para §246-D2-bis com threat-model proprio.

## Fallbacks (IRREMEDIAVEIS)

### Token Failure
  JWT expirado pre-request:    401 jwt_expired
  JWT expirado mid-tx:         transaction rollback
  DID-GENESIS unreachable:     503 issuer_unavailable, Retry-After: 60
  KEYGEN-001 sig invalid:      401 + incident receipt ao Ledger
  Postfix/Dovecot down:        503 mta_unavailable, Retry-After: 30
  Regra dura: NO PARTIAL CREATION. Slug ou existe pleno ou nao existe.

### Slug Release apos revogacao de wallet
  T+0:    wallet revogada via DID-GENESIS
  T+0:    Postfix alias mantido (mail flow continua)
  T+30d:  alias entra em quarentena (NDR explicativo a remetentes)
  T+90d:  slug libertado para reuso global
          mailbox archived em /opt/windi/archives/<slug>/
  Razao: 30+60d window permite recuperacao em caso de revogacao acidental.

## Decisoes Diferidas

§246-D2-bis (proximo selo):
  Functional Demo Mailbox — alias temporario real durante Workbench.
  Threat-model proprio: anti-spam-relay, rate limit, DKIM reputation.
  Tres perguntas estruturais pendentes:
    1. Quanto trafego anonimo aguenta? Que proteccoes?
    2. Lifecycle de emails recebidos pre-conversao DID?
    3. Reverse-conversion: utilizador testa, nao activa DID — emails apagados quando?

§246-IMPL:
  Endpoint shapes (POST /api/workbench/save, /load, /discard, /convert)
  JWT transport (Cookie HttpOnly vs Bearer)
  NDR template apos T+30d quarentena
  IDN/Unicode roadmap

§246-D3 a §246-D5 (sequencia mantida):
  D3 Mailbox Provisioning soberano (Docker integration spec)
  D4 Rate Limiting nginx + per-DID quotas
  D5 Receipt Symmetry (wallet_id propagation, parent_receipt chain)

## Invariantes aplicados

I9 Prohibition of Autonomy Escalation:
  Workbench NUNCA emite identidade. Acto soberano requer DID.

I11 Receipts no Ledger central:
  Drafts anonimos NAO produzem receipts. So conversao DID-bound produz.
  Receipt agregado de purga preserva auditabilidade sem violar minimizacao.

I14 Sem placeholders silenciosos:
  Identifiers DEMO- sao EXPLICITOS. Watermark visivel.
  Conversao e silenciosa MAS substituicao e total — nada DEMO sobrevive
  ao acto de consumacao.

---

Liga IA+H · Kempten, Bavaria · 2026
"Experimentar e livre. Consumar requer DID."
