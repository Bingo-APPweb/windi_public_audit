# §246-D2-bis · Institutional Demo Send + Slug Reservation

Receipt:    WINDI-S246-D2-bis-DEMOSEND-20260507074335-FCF917FE
Selo:       §246-D2-bis · IRREMEDIAVEL · I9 + I11 + I14
Parents:    WINDI-S246-D1-DELEGATION-20260507085800-D32AFF47
            WINDI-S246-D2-WORKBENCH-20260507073101-59497380
Spine:      "WINDI envia. Anonimo recebe na SUA inbox. Sem mailbox demo."
Data:       20260507074335 · Kempten, Bavaria

## Insight Fundacional (Human Dragon, 07 Mai 2026)

A intuicao que dissolveu D2-bis original: em vez de criar uma mailbox demo
para cada anonimo (N caixas, escala com users, threat-model complexo),
existe UMA conta institucional que envia a demonstracao para o email
pessoal que o utilizador ja tem.

Inversao do vector de comunicacao:
  Antes: WINDI cria mailbox -> anonimo recebe la -> complexidade O(N)
  Agora: WINDI envia -> anonimo recebe na SUA inbox habitual -> complexidade O(1)

Resultado: zero mailboxes anonimas, zero body-encryption, zero lifecycle
de emails de terceiros, zero spam-relay surface. Pedagogia visual intacta.

## Principio Arquitectural

windisites.de NAO provisiona caixas de email para utilizadores anonimos.
windisites.de envia UM email institucional do showcase para o endereco
pessoal que o anonimo fornece, demonstrando como ficaria o seu setup
soberano sem precisar criar nada do lado dele.

A caixa de email demo so existe DEPOIS do DID activo (ja coberto por D3).

## Decisoes Estruturais

### A · Sender Institucional

  Endereco:    welcome@windisites.de
  Razao:       Alinhado com doutrina "Hospitalidade Soberana" de D2
               Universal DE/EN/PT, nao tecnico, nao generico
  Provisao:    Alias institucional fixo no Postfix existente
               NAO escala com utilizadores (singleton)
  Auth/Sec:    DKIM/SPF/DMARC ja validados (mail-tester 10/10)
  Reply-To:    explicit no-reply policy no footer; respostas vao para
               /dev/null com bounce educativo
  Reverse-DNS: ja configurado (windi-mailserver Up 7d healthy)

### B · Slug Reservation durante Workbench

  Quando utilizador anonimo escolhe slug e pede demo:
    1. Sistema verifica slug contra D2 reserved blacklist
    2. Verifica unicidade global em mail.windisites.de
    3. Insere slug em tabela RESERVED com workbench_token associado
    4. Slug fica indisponivel para outros utilizadores enquanto reservado

  TTL:           Igual a Workbench D2 — 7d renovavel, 30d cap absoluto
  Conflito:      Outro user pede slug reservado -> 409 + sugestoes alternativas
  Liberation:    Cap atinge -> slug liberta automaticamente
                 Receipt agregado de purga ao Ledger
  Promocao:      DID activado -> slug reservation transforma-se em ownership
                 (chain-of-custody: workbench_token -> wallet_id, parent_receipt)

  RAZAO da reservation:
    Sem reservation, utilizador escolhe slug, demonstra-se, decide activar DID,
    chega ao consumar e descobre que outro user ja levou o slug.
    Mata a confianca no produto.
    Reservation e cortesia operacional alinhada com Hospitalidade Soberana.

### C · Demo Email Content

  Estrutura minima (HTML + plain-text alternative):

    Assunto: "O teu setup soberano em windisites.de — preview"

    Corpo:
      Ola.

      Aqui esta como ficaria a tua identidade soberana
      em windisites.de:

      ─────────────────────────────────────────────
      O TEU EMAIL FUTURO:    <slug>@windisites.de
      VERIFY URL DEMO:       https://windisites.de/verify-public/?demo=<token>
      SEALED BADGE:          [imagem inline ou referencia CID]
      RECEIPT PLACEHOLDER:   DEMO-{shortHash}
      ─────────────────────────────────────────────

      O slug "<slug>" esta reservado para ti durante 7 dias
      (renovaveis com novas visitas, maximo 30 dias).
      Se actives DID antes desse prazo, este endereco fica teu.

      [ Activar DID em windi-domain.com -> ]

      ─────────────────────────────────────────────
      Recebeste isto porque pediste demo em windisites.de.
      Nao respondemos a respostas a este email.
      Para suporte: contact@windi-domain.com
      ─────────────────────────────────────────────
      AI processes. Human decides. WINDI guarantees.

  Principios:
    - Sem links de tracking (privacy-first)
    - Sem pixel tracker
    - Sem reply-to engagement
    - 1 CTA unico e claro
    - Trilingue por detection: PT/DE/EN consoante Accept-Language do request

### D · Anti-Abuse (defesa simples e eficaz)

  Camada 1 · Rate limit por IP
    1 demo/IP/hora · 5 demos/IP/dia · 20 demos//24-subnet/dia
    nginx limit_req_zone

  Camada 2 · Rate limit por endereco destino (anti-bombing)
    1 demo por endereco destino por 24h
    Enforced via hash-of-destination check em DB

  Camada 3 · CAPTCHA antes de send
    reCAPTCHA v3 score >0.5 ou hCaptcha
    Bloqueia botnets, deixa humanos passar transparente

  Camada 4 · Blocklists DNS-based
    Enderecos em SBL/XBL/PBL (Spamhaus) rejeitados liminarmente
    Enderecos em known disposable-email lists rejeitados
    Razao: utilidade do demo so existe para emails reais

  Camada 5 · Cap global diario institucional
    Max 500 demos enviados pelo welcome@ por dia
    Atingido -> 503 + Retry-After ate reset
    Janela natural impede burst attacks

  Camada 6 · Abuse inbox
    abuse@windisites.de monitorizada
    Reports activam blocklist manual

### E · Privacy & Lifecycle

  Registo de envio (minimo necessario):
    - slug reservado (plaintext — e ele proprio publico pelo wizard UI)
    - hash SHA-256 do endereco destino (nao plaintext)
    - timestamp UTC
    - IP do requester (logs nginx normais, expurgados em 30d)

  GDPR Art. 5(1)(c) minimizacao cumprida:
    - Endereco destino NUNCA armazenado plaintext apos envio
    - Hash serve so para Camada 2 (1 demo/destino/24h)
    - Hash apagado apos 24h (ja nao serve enforcement)

  Apos 90d:
    - Registo agregado em metrica (count de demos por dia)
    - Identificadores apagados
    - Metrica retida como evidencia operacional

  Bounce handling:
    - Bounce hard (endereco nao existe) -> registar destino-hash em blocklist
      interna 30d para evitar re-tentativas
    - Bounce soft (mailbox full, etc) -> 1 retry apos 1h, depois abandonar
    - Sem retry agressivo (preserve sender reputation)

### F · Trilingue (DE/EN/PT)

  Detection priority:
    1. ?lang=XX query param explicito do wizard
    2. Accept-Language header do request
    3. Default: EN (mercado mais amplo)

  Templates vivem em:
    /opt/windi/mail-templates/welcome-demo/{de,en,pt}.html
    /opt/windi/mail-templates/welcome-demo/{de,en,pt}.txt

  Alteracoes nos templates requerem selo proprio (drift control).

### G · Convencao de Slug Reservation no DB

  Tabela em windi-workbench DB (D2):

    CREATE TABLE slug_reservations (
        slug TEXT PRIMARY KEY,
        workbench_token TEXT NOT NULL,
        reserved_at TEXT NOT NULL,
        last_renewed_at TEXT NOT NULL,
        expires_hard TEXT NOT NULL,  -- cap 30d desde reserved_at
        demo_sent_to_hash TEXT,       -- hash do destino, opcional
        status TEXT DEFAULT 'reserved' -- reserved/expired/promoted
    );

  Promocao a ownership soberano (DID activado):
    UPDATE slug_reservations SET status='promoted'
    INSERT INTO sites_aliases (slug, wallet_id, parent_receipt_d2_bis, ...)

  Liberation por cap absoluto:
    DELETE FROM slug_reservations WHERE expires_hard < NOW()
    Receipt agregado WINDI-WORKBENCH-SLUG-PURGE-{date}

## Fallbacks (IRREMEDIAVEIS)

  welcome@ Postfix down:
    503 demo_unavailable + Retry-After: 60
    Slug reservation NAO criada (no partial state)

  Captcha service down:
    503 verification_unavailable
    Slug reservation NAO criada

  Rate limit hit:
    429 rate_limited + Retry-After
    Mensagem clara ao utilizador, slug reservation MANTIDA

  Bounce hard do destino:
    Slug reservation MANTIDA (utilizador pode tentar outro endereco)
    Destino-hash em blocklist 30d

  DID-GENESIS down durante promocao:
    503 issuer_unavailable + Retry-After: 60
    Slug reservation MANTIDA ate DID activo

## Decisoes Diferidas para §246-IMPL

  - Endpoint shapes: POST /api/demo/send, /api/slug/reserve, /api/slug/check
  - Captcha provider final (reCAPTCHA v3 vs hCaptcha vs alternativa europeia)
  - Inline image vs CID para sealed badge
  - Bounce-handling daemon configuration
  - Template trilingue exact wording (revisao editorial)

## Invariantes aplicados

  I9 Prohibition of Autonomy Escalation:
    welcome@ NUNCA emite identidade. Nao cria DIDs.
    Slug reservation e estado temporario, nao soberania.

  I11 Receipts no Ledger central:
    Cada slug reservation NAO produz receipt individual (anonimo, ZERO Ledger).
    Promocao a ownership produz UM receipt (parent: D1 + D2-bis).
    Purga de reservations produz receipt agregado (sem identificadores).

  I14 Sem placeholders silenciosos:
    DEMO-* prefixes EXPLICITOS no email enviado.
    Footer institucional declara natureza nao-respondivel.
    Aviso de TTL e renovacao claro no corpo.

## Trade-offs Aceites

  CONTRA proposta original (Functional Demo Mailbox):
    - Anonimo nao ve DKIM "do seu proprio alias" funcionar
    - Demonstracao e menos "imersiva"

  PRO proposta nova (Institutional Demo Send):
    - Threat-model trivial vs complexo
    - Zero risk de blocklist em windisites.de por abuso
    - Zero infra escalando com utilizadores
    - Zero privacy concern de body de terceiros
    - Pedagogia visual igualmente eficaz (utilizador VE no email pessoal
      o que ganha com DID)
    - Implementacao mais simples = mais cedo no Sprint

  Decisao: trade-off claramente favoravel a versao nova.

---

Liga IA+H · Kempten, Bavaria · 2026
"WINDI envia. Anonimo recebe na SUA inbox. Sem mailbox demo."
