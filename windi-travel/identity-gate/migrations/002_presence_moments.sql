-- ==============================================================================
-- W-PRESENCE-001 — Presence Moments Index Table
-- ==============================================================================
-- WINDI Publishing House · Kempten, Bavaria
-- Migration: 002_presence_moments.sql
-- Date: 02 Apr 2026
--
-- Tabela de ÍNDICE OPERACIONAL para momentos de presença.
-- NÃO é a fonte de verdade — o Ledger é a prova canónica.
-- Esta tabela serve para:
--   - Timeline do utilizador
--   - Filtros e busca
--   - Observabilidade
--
-- Run with: sqlite3 windi_travel_identity.db < 002_presence_moments.sql
-- ==============================================================================

-- ==============================================================================
-- TABLE: presence_moments
-- ==============================================================================
-- Índice operacional de momentos declarados pelo humano.
-- Cada entrada corresponde a um receipt no Ledger.
-- A presença é DECLARADA, não detectada (I14).
-- ==============================================================================

CREATE TABLE IF NOT EXISTS presence_moments (
    -- ══════════════════════════════════════════════════════════════════════════
    -- IDENTIFICADORES
    -- ══════════════════════════════════════════════════════════════════════════
    local_id        TEXT PRIMARY KEY,              -- UUID local (gerado no backend)
    receipt_id      TEXT UNIQUE,                   -- WINDI-PRESENCE-xxx (do Ledger)

    -- ══════════════════════════════════════════════════════════════════════════
    -- IDENTIDADE (de W-SESSION-001)
    -- ══════════════════════════════════════════════════════════════════════════
    did             TEXT NOT NULL,                 -- did:windi:travel:xxx
    session_id      TEXT,                          -- sessão soberana que gerou (opcional)

    -- ══════════════════════════════════════════════════════════════════════════
    -- TIMESTAMPS
    -- ══════════════════════════════════════════════════════════════════════════
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),  -- quando foi criado no sistema
    declared_at     TEXT NOT NULL,                            -- momento declarado pelo humano

    -- ══════════════════════════════════════════════════════════════════════════
    -- PRESENCE LEVEL (hierarquia probatória)
    -- ══════════════════════════════════════════════════════════════════════════
    -- P1 = Temporal  (DID + timestamp + intent)
    -- P2 = Contextual (P1 + evidence)
    -- P3 = Spatial   (P2 + GPS location)
    -- ══════════════════════════════════════════════════════════════════════════
    presence_level  TEXT NOT NULL DEFAULT 'P1'
                    CHECK(presence_level IN ('P1', 'P2', 'P3')),

    -- ══════════════════════════════════════════════════════════════════════════
    -- CONTEÚDO DECLARADO
    -- ══════════════════════════════════════════════════════════════════════════
    intent          TEXT NOT NULL,                 -- intenção declarada pelo humano
    title           TEXT,                          -- título opcional

    -- ══════════════════════════════════════════════════════════════════════════
    -- LOCALIZAÇÃO (P3)
    -- ══════════════════════════════════════════════════════════════════════════
    -- location_mode: como a localização foi obtida
    --   'gps'  = GPS do browser (mais preciso)
    --   'ip'   = IP geolocation / WhereAmI (aproximado)
    --   'none' = sem localização (ainda válido como P1/P2)
    -- ══════════════════════════════════════════════════════════════════════════
    location_mode   TEXT DEFAULT 'none'
                    CHECK(location_mode IN ('gps', 'ip', 'none')),
    location_label  TEXT,                          -- "Kempten, Bavaria" (legível)
    lat             REAL,                          -- latitude
    lng             REAL,                          -- longitude
    precision_m     INTEGER,                       -- precisão em metros

    -- ══════════════════════════════════════════════════════════════════════════
    -- EVIDÊNCIA (P2/P3)
    -- ══════════════════════════════════════════════════════════════════════════
    -- evidence_kind: tipo de evidência anexada
    --   'image' = fotografia
    --   'audio' = gravação de voz
    --   'text'  = nota textual
    --   'none'  = sem evidência (P1)
    --
    -- IMPORTANTE: Apenas HASH da evidência vai para o Ledger.
    -- O conteúdo bruto fica em storage controlado.
    -- ══════════════════════════════════════════════════════════════════════════
    evidence_kind   TEXT DEFAULT 'none'
                    CHECK(evidence_kind IN ('image', 'audio', 'text', 'none')),
    evidence_hash   TEXT,                          -- sha256 da evidência (prova)
    evidence_path   TEXT,                          -- path local ou URL de storage

    -- ══════════════════════════════════════════════════════════════════════════
    -- LEDGER (prova canónica)
    -- ══════════════════════════════════════════════════════════════════════════
    content_hash    TEXT NOT NULL,                 -- sha256 do payload completo
    verify_url      TEXT,                          -- link público de verificação

    -- ══════════════════════════════════════════════════════════════════════════
    -- ESTADO
    -- ══════════════════════════════════════════════════════════════════════════
    -- 'SEALED'  = selado no Ledger com sucesso
    -- 'PENDING' = aguardando confirmação do Ledger
    -- 'FAILED'  = falha ao selar (retry possível)
    -- ══════════════════════════════════════════════════════════════════════════
    state           TEXT DEFAULT 'PENDING'
                    CHECK(state IN ('SEALED', 'PENDING', 'FAILED')),

    -- ══════════════════════════════════════════════════════════════════════════
    -- FOREIGN KEY
    -- ══════════════════════════════════════════════════════════════════════════
    FOREIGN KEY(did) REFERENCES admins(did)
);


-- ==============================================================================
-- ÍNDICES
-- ==============================================================================
-- Optimizados para queries comuns:
--   - Timeline por DID
--   - Filtro por nível de presença
--   - Ordenação por data
--   - Busca por receipt_id
-- ==============================================================================

-- Timeline do utilizador (mais comum)
CREATE INDEX IF NOT EXISTS idx_presence_did_created
    ON presence_moments(did, created_at DESC);

-- Filtro por nível de presença
CREATE INDEX IF NOT EXISTS idx_presence_level
    ON presence_moments(presence_level);

-- Busca por receipt (para verify)
CREATE INDEX IF NOT EXISTS idx_presence_receipt
    ON presence_moments(receipt_id);

-- Momentos selados por DID (para contagem/stats)
CREATE INDEX IF NOT EXISTS idx_presence_did_sealed
    ON presence_moments(did)
    WHERE state = 'SEALED';

-- Momentos com localização (para mapa futuro)
CREATE INDEX IF NOT EXISTS idx_presence_location
    ON presence_moments(did, lat, lng)
    WHERE location_mode != 'none';


-- ==============================================================================
-- NOTAS DE IMPLEMENTAÇÃO
-- ==============================================================================
--
-- REGRA DE OURO:
--   Esta tabela é ÍNDICE, não VERDADE.
--   O Ledger (:8101) é a fonte canónica de prova.
--   Se houver divergência, o Ledger prevalece.
--
-- INVARIANTES:
--   I14 — Presence Integrity: presença é DECLARADA, não detectada
--   I9  — Autonomy Prohibition: confirmação humana obrigatória
--   I11 — Cryptographic Permanence: Ledger = IRREMEDIÁVEL
--
-- COMPATIBILIDADE:
--   Esta migration é ADITIVA — não altera tabelas existentes:
--   - sovereign_sessions (W-SESSION-001)
--   - device_bindings (W-SESSION-001)
--   - admins
--   - companies
--   - api_keys
--
-- ==============================================================================
