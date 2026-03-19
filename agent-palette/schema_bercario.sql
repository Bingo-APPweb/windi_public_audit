-- WINDI Berçário — wallet_databank.db
-- Dragon Hub :8108
-- DNA: ALMA → DID → CÉREBRO → LEDGER → MUNDO
-- I9 + I11 · IRREMEDIÁVEL
-- Kempten, Bavaria · 2026

PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

-- ─── WALLETS ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS wallets (
    wallet_id       TEXT PRIMARY KEY,
    did             TEXT,
    tier            TEXT NOT NULL DEFAULT 'FREE',
    born_at         TEXT NOT NULL,
    last_seen_at    TEXT NOT NULL,
    total_sessions  INTEGER NOT NULL DEFAULT 0,
    estado_atual    TEXT NOT NULL DEFAULT 'nasceu',
    fingerprint     TEXT,
    lang            TEXT NOT NULL DEFAULT 'pt'
);

-- ─── SESSIONS ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sessions (
    session_id      TEXT PRIMARY KEY,
    wallet_id       TEXT NOT NULL REFERENCES wallets(wallet_id),
    estado          TEXT NOT NULL,
    started_at      TEXT NOT NULL,
    ended_at        TEXT,
    duration_s      INTEGER,
    context         TEXT
);

-- ─── BIRTH EVENTS (IRREMEDIÁVEL) ──────────────────────────────────
CREATE TABLE IF NOT EXISTS birth_events (
    event_id            TEXT PRIMARY KEY,
    wallet_id           TEXT NOT NULL REFERENCES wallets(wallet_id),
    event_type          TEXT NOT NULL,
    sealed_at           TEXT NOT NULL,
    ledger_receipt_id   TEXT,
    irremediavel        INTEGER NOT NULL DEFAULT 1
);

-- ─── ÍNDICES ──────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_sessions_wallet ON sessions(wallet_id);
CREATE INDEX IF NOT EXISTS idx_events_wallet   ON birth_events(wallet_id);
CREATE INDEX IF NOT EXISTS idx_wallets_did     ON wallets(did);
