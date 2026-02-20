-- ============================================================================
-- WINDI WALLET — Sistema Nervoso Central de Identidade Soberana
-- DDL v1.0.0 | 2026-02-15
-- Three Dragons Protocol: AI processes. Human decides. WINDI guarantees.
-- ============================================================================
-- Princípios:
--   1. wallet_human é IMUTÁVEL (append-only, nunca UPDATE/DELETE)
--   2. wallet_key_history é IMUTÁVEL (append-only)
--   3. wallet_context é VERSIONÁVEL (mudanças geram eventos em _history)
--   4. ledger_link é IMUTÁVEL (referência a hashes forenses)
--   5. trust_events é IMUTÁVEL (append-only, auditável)
-- ============================================================================

-- ─── EXTENSÕES ──────────────────────────────────────────────────────────────
-- UUIDv7 gerado na aplicação (Python uuid7), armazenado como uuid nativo.
-- pgcrypto disponível caso necessário para hashing no DB.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================================================
-- A. CAMADA IMUTÁVEL — IDENTIDADE HUMANA
-- "O humano existe antes da instituição."
-- ============================================================================

-- ─── wallet_human ───────────────────────────────────────────────────────────
-- 1 registro por humano soberano. Nunca editado, nunca deletado.
-- Campos opcionais (display_name, legal_name, email) preenchidos no provisioning.
-- A chave Ed25519 é a âncora criptográfica da existência.

CREATE TABLE IF NOT EXISTS wallet_human (
    human_id        UUID PRIMARY KEY,                           -- UUIDv7 (app)
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by      TEXT NOT NULL,                               -- actor: admin:jober / system / witness

    status          TEXT NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'suspended', 'revoked')),

    -- Dados de identidade (opcionais, minimizados por DSGVO)
    display_name    TEXT,
    legal_name      TEXT,
    email           TEXT,

    -- Âncora criptográfica
    pubkey_ed25519  TEXT NOT NULL,                               -- base64 da chave pública
    sip_pass_hash   TEXT,                                        -- argon2id hash da passphrase SIP
    fingerprint     TEXT NOT NULL UNIQUE,                        -- SHA-256(pubkey + human_id + created_at)

    -- Referência ao lead de origem
    lead_id         TEXT,                                        -- LEAD-YYYYMMDD-... (rastreabilidade)

    -- Metadados extensíveis
    meta            JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_wallet_human_pubkey
    ON wallet_human(pubkey_ed25519);

CREATE UNIQUE INDEX IF NOT EXISTS ux_wallet_human_fingerprint
    ON wallet_human(fingerprint);

CREATE INDEX IF NOT EXISTS ix_wallet_human_email
    ON wallet_human(email) WHERE email IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_wallet_human_lead
    ON wallet_human(lead_id) WHERE lead_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_wallet_human_created
    ON wallet_human(created_at);

COMMENT ON TABLE wallet_human IS
    'Camada Imutável: identidade soberana do humano. Nunca UPDATE/DELETE.';


-- ─── wallet_key_history ─────────────────────────────────────────────────────
-- Rotação de chaves, revogação, criação. Append-only.

CREATE TABLE IF NOT EXISTS wallet_key_history (
    key_event_id    UUID PRIMARY KEY,                           -- UUIDv7
    human_id        UUID NOT NULL REFERENCES wallet_human(human_id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    event_type      TEXT NOT NULL
                    CHECK (event_type IN ('key_created', 'key_rotated', 'key_revoked')),

    pubkey_ed25519  TEXT NOT NULL,
    reason          TEXT,
    ledger_ref      TEXT,                                        -- hash/entry no Forensic Ledger
    meta            JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS ix_wallet_key_hist_human
    ON wallet_key_history(human_id, created_at DESC);

COMMENT ON TABLE wallet_key_history IS
    'Histórico imutável de chaves criptográficas. Append-only.';


-- ============================================================================
-- B. CAMADA CONTEXTUAL — VÍNCULO INSTITUCIONAL
-- "O humano habita contextos. Os contextos pertencem às instituições."
-- ============================================================================

-- ─── org ────────────────────────────────────────────────────────────────────
-- Organizações registradas no ecossistema WINDI.

CREATE TABLE IF NOT EXISTS org (
    org_id          UUID PRIMARY KEY,                           -- UUIDv7
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    name            TEXT NOT NULL,
    domain          TEXT,                                        -- ex: empresa.de
    brand_dna       JSONB NOT NULL DEFAULT '{}'::jsonb,          -- cores, ícones, tipografia

    status          TEXT NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'suspended', 'archived')),

    isp_profile_id  TEXT,                                        -- ref ao ISP em /opt/windi/isp/
    meta            JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_org_domain
    ON org(domain) WHERE domain IS NOT NULL;

COMMENT ON TABLE org IS
    'Organizações no ecossistema WINDI. brand_dna define aparência do A4Desk.';


-- ─── wallet_context ─────────────────────────────────────────────────────────
-- N contextos por humano. PF (org_id NULL) ou PJ (org_id preenchido).
-- Mutável: state pode transitar active → frozen → revoked.

CREATE TABLE IF NOT EXISTS wallet_context (
    context_id      UUID PRIMARY KEY,                           -- UUIDv7
    human_id        UUID NOT NULL REFERENCES wallet_human(human_id),
    org_id          UUID REFERENCES org(org_id),                -- NULL = Pessoa Física

    context_type    TEXT NOT NULL
                    CHECK (context_type IN ('PF', 'PJ')),

    role            TEXT NOT NULL DEFAULT 'operator',            -- operator|manager|director|minister|admin
    authority_scope JSONB NOT NULL DEFAULT '{}'::jsonb,          -- permissões semânticas
    governance_level TEXT NOT NULL DEFAULT 'L1',                 -- L1 = básico, L2 = completo, L3 = soberano

    isp_profile_id  TEXT,                                        -- ISP aplicado neste contexto
    policy_version  TEXT,                                        -- ex: v2.2.0

    -- Ciclo de vida
    state           TEXT NOT NULL DEFAULT 'active'
                    CHECK (state IN ('active', 'frozen', 'revoked')),

    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    frozen_at       TIMESTAMPTZ,
    revoked_at      TIMESTAMPTZ,
    revoked_reason  TEXT,

    -- Wallet ID legível (para interfaces e receipts)
    wallet_id       TEXT NOT NULL UNIQUE,                        -- WALLET-YYYYMMDD-NNNN

    meta            JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS ix_wallet_ctx_human
    ON wallet_context(human_id, created_at DESC);

CREATE INDEX IF NOT EXISTS ix_wallet_ctx_org
    ON wallet_context(org_id, created_at DESC) WHERE org_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_wallet_ctx_state
    ON wallet_context(state);

COMMENT ON TABLE wallet_context IS
    'Contextos operacionais do humano. PF ou PJ. Mutável com versionamento.';


-- ─── wallet_context_history ─────────────────────────────────────────────────
-- Toda mudança em wallet_context gera um evento aqui. Append-only.

CREATE TABLE IF NOT EXISTS wallet_context_history (
    ctx_event_id    UUID PRIMARY KEY,                           -- UUIDv7
    context_id      UUID NOT NULL REFERENCES wallet_context(context_id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    actor           TEXT NOT NULL,                               -- quem mudou
    event_type      TEXT NOT NULL
                    CHECK (event_type IN (
                        'created', 'updated', 'frozen', 'revoked',
                        'role_changed', 'scope_changed', 'reactivated'
                    )),

    diff            JSONB NOT NULL,                             -- o que mudou
    ledger_ref      TEXT,                                        -- hash no Forensic
    meta            JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS ix_wallet_ctx_hist
    ON wallet_context_history(context_id, created_at DESC);

COMMENT ON TABLE wallet_context_history IS
    'Histórico de mudanças em contextos. Append-only, auditável.';


-- ============================================================================
-- C. CAMADA DE REFERÊNCIA — LEDGER LINK
-- "Não duplica dados. Aponta para provas."
-- ============================================================================

CREATE TABLE IF NOT EXISTS ledger_link (
    link_id         UUID PRIMARY KEY,                           -- UUIDv7
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    human_id        UUID NOT NULL REFERENCES wallet_human(human_id),
    context_id      UUID REFERENCES wallet_context(context_id), -- NULL se evento pré-contexto

    ref_type        TEXT NOT NULL
                    CHECK (ref_type IN (
                        'RECEIPT', 'DECISION', 'INCIDENT', 'FOUNDATION',
                        'KEY_EVENT', 'WALLET_PROVISIONED', 'CONTEXT_FROZEN',
                        'CONTEXT_REVOKED', 'TRUST_UPDATE'
                    )),

    ref_id          TEXT NOT NULL,                               -- WALLET-..., DEC-..., INFRA-...
    ledger_hash     TEXT NOT NULL,                               -- SHA-256 do registro forense
    ledger_entry    TEXT,                                        -- entry number no Forensic Ledger

    UNIQUE(ref_type, ref_id, ledger_hash)
);

CREATE INDEX IF NOT EXISTS ix_ledger_link_human
    ON ledger_link(human_id, created_at DESC);

CREATE INDEX IF NOT EXISTS ix_ledger_link_ctx
    ON ledger_link(context_id, created_at DESC) WHERE context_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_ledger_link_ref
    ON ledger_link(ref_type, ref_id);

COMMENT ON TABLE ledger_link IS
    'Referências imutáveis ao Forensic Ledger. Sem dados duplicados.';


-- ============================================================================
-- D. TRUST SCORE EVOLUTIVO
-- "Confiança não se declara. Se demonstra."
-- ============================================================================

-- ─── trust_score ────────────────────────────────────────────────────────────
-- Estado atual do trust por contexto. Atualizado por eventos.

CREATE TABLE IF NOT EXISTS trust_score (
    context_id      UUID PRIMARY KEY REFERENCES wallet_context(context_id),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    score           NUMERIC(5,2) NOT NULL DEFAULT 50.00,         -- 0.00 a 100.00
    level           TEXT NOT NULL DEFAULT 'T1'                   -- T1=novo, T2=confiável, T3=verificado, T4=soberano
                    CHECK (level IN ('T1', 'T2', 'T3', 'T4')),

    -- Contadores auditáveis
    signals         JSONB NOT NULL DEFAULT '{
        "receipts_ok": 0,
        "receipts_total": 0,
        "decisions_made": 0,
        "policy_violations": 0,
        "audits_passed": 0,
        "recovery_events": 0
    }'::jsonb
);

COMMENT ON TABLE trust_score IS
    'Estado atual de confiança por contexto. Calculado a partir de trust_events.';


-- ─── trust_events ───────────────────────────────────────────────────────────
-- Cada sinal de confiança é um evento append-only.

CREATE TABLE IF NOT EXISTS trust_events (
    trust_event_id  UUID PRIMARY KEY,                           -- UUIDv7
    context_id      UUID NOT NULL REFERENCES wallet_context(context_id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    signal_type     TEXT NOT NULL
                    CHECK (signal_type IN (
                        'receipt_ok', 'receipt_flagged',
                        'policy_violation', 'policy_compliance',
                        'audit_pass', 'audit_fail',
                        'recovery', 'escalation',
                        'manual_adjustment'
                    )),

    weight          NUMERIC(6,2) NOT NULL,                      -- positivo ou negativo
    description     TEXT,

    source_ref      JSONB NOT NULL DEFAULT '{}'::jsonb,          -- link ao ledger/decisão
    ledger_ref      TEXT
);

CREATE INDEX IF NOT EXISTS ix_trust_events_ctx
    ON trust_events(context_id, created_at DESC);

COMMENT ON TABLE trust_events IS
    'Eventos de confiança. Append-only, cada sinal é auditável.';


-- ============================================================================
-- E. TRIGGERS DE IMUTABILIDADE (I9: Prohibition of Autonomy Escalation)
-- "O que foi escrito, permanece escrito."
-- ============================================================================

-- Função genérica que bloqueia UPDATE e DELETE
CREATE OR REPLACE FUNCTION fn_immutable_guard()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION
        'WINDI I9 VIOLATION: % on immutable table % is forbidden. '
        'Ref: Three Dragons Protocol — Invariant I9.',
        TG_OP, TG_TABLE_NAME;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Aplicar em todas as tabelas imutáveis
CREATE OR REPLACE TRIGGER trg_immutable_wallet_human
    BEFORE UPDATE OR DELETE ON wallet_human
    FOR EACH ROW EXECUTE FUNCTION fn_immutable_guard();

CREATE OR REPLACE TRIGGER trg_immutable_key_history
    BEFORE UPDATE OR DELETE ON wallet_key_history
    FOR EACH ROW EXECUTE FUNCTION fn_immutable_guard();

CREATE OR REPLACE TRIGGER trg_immutable_ledger_link
    BEFORE UPDATE OR DELETE ON ledger_link
    FOR EACH ROW EXECUTE FUNCTION fn_immutable_guard();

CREATE OR REPLACE TRIGGER trg_immutable_trust_events
    BEFORE UPDATE OR DELETE ON trust_events
    FOR EACH ROW EXECUTE FUNCTION fn_immutable_guard();

-- wallet_context_history é append-only também
CREATE OR REPLACE TRIGGER trg_immutable_ctx_history
    BEFORE UPDATE OR DELETE ON wallet_context_history
    FOR EACH ROW EXECUTE FUNCTION fn_immutable_guard();


-- ============================================================================
-- F. TRIGGER DE VERSIONAMENTO (wallet_context → wallet_context_history)
-- Toda UPDATE em wallet_context gera automaticamente um evento histórico.
-- ============================================================================

CREATE OR REPLACE FUNCTION fn_wallet_context_version()
RETURNS TRIGGER AS $$
DECLARE
    v_diff JSONB;
    v_event TEXT;
BEGIN
    -- Determinar tipo de evento
    IF OLD.state != NEW.state THEN
        v_event := NEW.state;  -- 'frozen', 'revoked', 'active' (reactivated)
        IF NEW.state = 'active' AND OLD.state != 'active' THEN
            v_event := 'reactivated';
        END IF;
    ELSIF OLD.role != NEW.role THEN
        v_event := 'role_changed';
    ELSIF OLD.authority_scope::text != NEW.authority_scope::text THEN
        v_event := 'scope_changed';
    ELSE
        v_event := 'updated';
    END IF;

    -- Construir diff
    v_diff := jsonb_build_object(
        'old_state', OLD.state,
        'new_state', NEW.state,
        'old_role', OLD.role,
        'new_role', NEW.role,
        'old_governance_level', OLD.governance_level,
        'new_governance_level', NEW.governance_level
    );

    -- Inserir evento histórico
    INSERT INTO wallet_context_history (
        ctx_event_id, context_id, actor, event_type, diff
    ) VALUES (
        gen_random_uuid(),   -- fallback se UUIDv7 não disponível no DB
        OLD.context_id,
        COALESCE(current_setting('app.current_actor', true), 'system'),
        v_event,
        v_diff
    );

    -- Atualizar timestamp
    NEW.updated_at := now();

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trg_wallet_context_version
    BEFORE UPDATE ON wallet_context
    FOR EACH ROW EXECUTE FUNCTION fn_wallet_context_version();


-- ============================================================================
-- G. VIEWS OPERACIONAIS
-- ============================================================================

-- View: estado completo do wallet para o A4Desk (/api/wallet/me)
CREATE OR REPLACE VIEW v_wallet_full AS
SELECT
    wh.human_id,
    wh.display_name,
    wh.fingerprint,
    wh.status AS human_status,
    wh.created_at AS human_created_at,
    wc.context_id,
    wc.wallet_id,
    wc.context_type,
    wc.role,
    wc.authority_scope,
    wc.governance_level,
    wc.isp_profile_id,
    wc.state AS context_state,
    o.org_id,
    o.name AS org_name,
    o.domain AS org_domain,
    o.brand_dna,
    ts.score AS trust_score,
    ts.level AS trust_level,
    ts.signals AS trust_signals
FROM wallet_human wh
JOIN wallet_context wc ON wc.human_id = wh.human_id
LEFT JOIN org o ON o.org_id = wc.org_id
LEFT JOIN trust_score ts ON ts.context_id = wc.context_id;

COMMENT ON VIEW v_wallet_full IS
    'Vista completa do wallet para renderização no A4Desk.';


-- View: contagem de ledger links por humano
CREATE OR REPLACE VIEW v_wallet_activity AS
SELECT
    wh.human_id,
    wh.display_name,
    wc.wallet_id,
    wc.context_type,
    COUNT(ll.link_id) AS total_ledger_entries,
    COUNT(CASE WHEN ll.ref_type = 'RECEIPT' THEN 1 END) AS receipts,
    COUNT(CASE WHEN ll.ref_type = 'DECISION' THEN 1 END) AS decisions,
    MAX(ll.created_at) AS last_activity
FROM wallet_human wh
JOIN wallet_context wc ON wc.human_id = wh.human_id
LEFT JOIN ledger_link ll ON ll.human_id = wh.human_id
GROUP BY wh.human_id, wh.display_name, wc.wallet_id, wc.context_type;

COMMENT ON VIEW v_wallet_activity IS
    'Resumo de atividade por wallet para dashboards.';


-- ============================================================================
-- H. DADOS INICIAIS (seed para o primeiro humano do ecossistema)
-- ============================================================================
-- NOTA: Não insere aqui. O provisioning via API é o único caminho legítimo.
-- Este bloco existe apenas como referência do formato.

/*
INSERT INTO wallet_human (human_id, created_by, display_name, email, pubkey_ed25519, fingerprint, lead_id)
VALUES (
    '018e0000-0000-7000-8000-000000000001',
    'system:genesis',
    'Jober Mögele Correa',
    'jober@a4desk.de',
    'ed25519:BASE64_PUBKEY_HERE',
    'sha256:FINGERPRINT_HERE',
    'LEAD-20260215-151736'
);
*/

-- ============================================================================
-- FIM DO DDL — WALLET WINDI v1.0.0
-- "Sem WALLET, há login. Com WALLET, há existência digital soberana." 🐉
-- ============================================================================
