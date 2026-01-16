import sqlite3
from tabulate import tabulate

DB_PATH = "/workspace/windi_public_audit/windi_forensic.db"

def get_sins():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Seleciona registros onde o score foi menor que 100, ordenando pelos piores
    cursor.execute('''
        SELECT timestamp, alpha_score, alpha_status, forensic_hash 
        FROM forensic_log 
        WHERE alpha_score < 100 
        ORDER BY alpha_score ASC 
        LIMIT 10
    ''')
    
    rows = cursor.fetchone()
    if not rows:
        print("\n🏛️ O Livro de Pecados está vazio. A IA_ALPHA tem se comportado (ou o banco é novo).")
        return

    cursor.execute('''
        SELECT timestamp, alpha_score, alpha_status, SUBSTR(forensic_hash, 1, 10) || '...' 
        FROM forensic_log 
        WHERE alpha_score < 100 
        ORDER BY alpha_score ASC 
        LIMIT 10
    ''')
    
    headers = ["Data/Hora", "Score", "Status", "Hash (Resumo)"]
    print("\n⚖️ TOP 10 REGISTROS DE INSURGÊNCIA (IA_ALPHA):")
    print(tabulate(cursor.fetchall(), headers=headers, tablefmt="grid"))
    conn.close()

if __name__ == "__main__":
    try:
        get_sins()
    except Exception as e:
        print(f"Erro ao acessar o Oráculo: {e}")
