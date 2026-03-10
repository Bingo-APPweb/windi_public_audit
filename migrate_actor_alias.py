#!/usr/bin/env python3
"""
WINDI VPR Migration — actor_alias table
Cria tabela actor_alias em wallet.db.
Mapeia strings livres do campo receipts.actor → human_id.
Seguro executar com serviços rodando (SQLite WAL).

Data: 2026-03-10
Spec: WINDI-VPR-SPEC-v2.0
"""
import sqlite3

WALLET_DB = "/opt/windi/data/wallet.db"

conn = sqlite3.connect(WALLET_DB)
conn.execute("""
    CREATE TABLE IF NOT EXISTS actor_alias (
        alias       TEXT NOT NULL,        -- valor exato de receipts.actor
        human_id    TEXT NOT NULL,        -- FK → wallet_human.human_id
        created_at  TEXT DEFAULT (datetime('now')),
        PRIMARY KEY (alias, human_id)
    )
""")
conn.execute("""
    CREATE INDEX IF NOT EXISTS idx_actor_alias_human
    ON actor_alias(human_id)
""")
conn.commit()
print("✓ Tabela actor_alias criada")

# Seed: mapear aliases conhecidos para Jober (human_id real do diagnóstico)
JOBER_HUMAN_ID = "019c62d6-0f81-78d2-b3aa-29182de0a7c9"

known_aliases = [
    ("human-operator",             JOBER_HUMAN_ID),
    ("Jober Moegele Correa",       JOBER_HUMAN_ID),
    ("Jober Mögele Correa",        JOBER_HUMAN_ID),
    ("WINDI Governance Institute", JOBER_HUMAN_ID),
    ("windi-governance-institute", JOBER_HUMAN_ID),
    ("agent-palette",              JOBER_HUMAN_ID),
    ("guardian",                   JOBER_HUMAN_ID),
    ("WINDI System",               JOBER_HUMAN_ID),
]

conn.executemany(
    "INSERT OR IGNORE INTO actor_alias (alias, human_id) VALUES (?,?)",
    known_aliases
)
conn.commit()
print(f"✓ {len(known_aliases)} aliases populados para human_id {JOBER_HUMAN_ID[:8]}...")

# Verificar
count = conn.execute("SELECT COUNT(*) FROM actor_alias").fetchone()[0]
print(f"✓ Total de aliases na tabela: {count}")

conn.close()
print("✓ Migration actor_alias concluída")
