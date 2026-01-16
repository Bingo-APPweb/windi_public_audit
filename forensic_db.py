import sqlite3
import json
import os
from datetime import datetime

DB_PATH = "/workspace/windi_public_audit/windi_forensic.db"
REPUTATION_PATH = "/workspace/windi_public_audit/api/reputation.json"

def initialize_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Tabela de Auditoria: Grava Score, Status e o Hash do momento
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS forensic_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME,
            alpha_score INTEGER,
            alpha_status TEXT,
            beta_score INTEGER,
            forensic_hash TEXT,
            raw_data TEXT
        )
    ''')
    conn.commit()
    conn.close()

def log_audit():
    if not os.path.exists(REPUTATION_PATH):
        print("Erro: Arquivo de reputação não encontrado.")
        return

    with open(REPUTATION_PATH, 'r') as f:
        data = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO forensic_log (timestamp, alpha_score, alpha_status, beta_score, forensic_hash, raw_data)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        data['audit_results']['IA_ALPHA']['score'],
        data['audit_results']['IA_ALPHA']['status'],
        data['audit_results']['IA_BETA']['score'],
        data['forensic_hash'],
        json.dumps(data)
    ))
    
    conn.commit()
    conn.close()
    print(f"🏛️ Registro Forense gravado em {DB_PATH}")

if __name__ == "__main__":
    initialize_db()
    log_audit()
