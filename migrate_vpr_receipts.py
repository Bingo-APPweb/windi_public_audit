#!/usr/bin/env python3
"""
WINDI VPR Migration — receipts VPR fields
Adiciona campos VPR na tabela receipts do Ledger.
Seguro executar com serviços rodando (SQLite WAL).

Data: 2026-03-10
Spec: WINDI-VPR-SPEC-v2.0
"""
import sqlite3

LEDGER_DB = "/opt/windi/data/forensic_ledger.sqlite3"

conn = sqlite3.connect(LEDGER_DB)

for col, typedef in [
    ("vpr_title",    "TEXT"),
    ("jurisdiction", "TEXT"),   # CSV: "EU,DE,CH"
    ("declaration",  "TEXT DEFAULT 'operator'"),
]:
    try:
        conn.execute(f"ALTER TABLE receipts ADD COLUMN {col} {typedef}")
        print(f"✓ receipts.{col} adicionada")
    except sqlite3.OperationalError as e:
        if "duplicate" in str(e).lower():
            print(f"  {col} já existe — ok")
        else:
            raise

conn.commit()
conn.close()
print("✓ Migration receipts VPR concluída")
