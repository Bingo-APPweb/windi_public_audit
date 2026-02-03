#!/usr/bin/env python3
"""
WINDI Certification - Backup & Restore System
Para migração fácil entre servidores (RunPod → Strato)

Uso:
    python3 backup_restore.py backup              # Cria backup completo
    python3 backup_restore.py restore <arquivo>  # Restaura de backup
    python3 backup_restore.py export-json        # Exporta dados em JSON
    python3 backup_restore.py auto               # Backup automático (para cron)
"""

import os
import sys
import json
import shutil
import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path

# Configuração
DB_PATH = os.environ.get('WINDI_CERT_DB', 'windi_certification.db')
BACKUP_DIR = os.environ.get('WINDI_BACKUP_DIR', './backups')
APP_DIR = os.path.dirname(os.path.abspath(__file__))

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def generate_hash(content):
    """Gera hash SHA-256 para verificação de integridade"""
    if isinstance(content, str):
        content = content.encode()
    return hashlib.sha256(content).hexdigest()[:16]

def backup_full():
    """
    Cria backup completo: código + banco + configuração
    Formato: windi_cert_backup_YYYYMMDD_HHMMSS.zip
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"windi_cert_backup_{timestamp}"
    backup_path = Path(BACKUP_DIR) / backup_name
    
    # Criar diretório de backup
    Path(BACKUP_DIR).mkdir(parents=True, exist_ok=True)
    backup_path.mkdir(parents=True, exist_ok=True)
    
    print(f"📦 Criando backup: {backup_name}")
    
    # 1. Copiar banco de dados
    if os.path.exists(DB_PATH):
        shutil.copy2(DB_PATH, backup_path / 'windi_certification.db')
        print(f"   ✓ Banco de dados copiado")
    else:
        print(f"   ⚠ Banco não encontrado: {DB_PATH}")
    
    # 2. Copiar código fonte
    for item in ['app.py', 'requirements.txt', 'README.md']:
        src = Path(APP_DIR) / item
        if src.exists():
            shutil.copy2(src, backup_path / item)
            print(f"   ✓ {item} copiado")
    
    # 3. Copiar templates
    templates_src = Path(APP_DIR) / 'templates'
    if templates_src.exists():
        shutil.copytree(templates_src, backup_path / 'templates')
        print(f"   ✓ Templates copiados")
    
    # 4. Copiar static (se existir)
    static_src = Path(APP_DIR) / 'static'
    if static_src.exists() and any(static_src.iterdir()):
        shutil.copytree(static_src, backup_path / 'static')
        print(f"   ✓ Static copiados")
    
    # 5. Exportar dados em JSON legível
    json_export = export_data_json()
    with open(backup_path / 'data_export.json', 'w', encoding='utf-8') as f:
        json.dump(json_export, f, indent=2, ensure_ascii=False)
    print(f"   ✓ Export JSON criado")
    
    # 6. Criar manifesto
    manifest = {
        'backup_id': backup_name,
        'created_at': datetime.now().isoformat(),
        'source_server': os.environ.get('HOSTNAME', 'unknown'),
        'db_hash': generate_hash(open(backup_path / 'windi_certification.db', 'rb').read()) if (backup_path / 'windi_certification.db').exists() else None,
        'stats': json_export.get('stats', {}),
        'windi_principle': 'AI processes. Human decides. WINDI guarantees.'
    }
    
    with open(backup_path / 'manifest.json', 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    print(f"   ✓ Manifesto criado")
    
    # 7. Criar ZIP
    zip_path = shutil.make_archive(
        str(Path(BACKUP_DIR) / backup_name),
        'zip',
        BACKUP_DIR,
        backup_name
    )
    
    # 8. Limpar diretório temporário
    shutil.rmtree(backup_path)
    
    # 9. Calcular hash do ZIP final
    with open(zip_path, 'rb') as f:
        zip_hash = generate_hash(f.read())
    
    print(f"\n✅ Backup completo criado!")
    print(f"   📁 Arquivo: {zip_path}")
    print(f"   🔐 Hash: {zip_hash}")
    print(f"   📊 Stats: {json_export.get('stats', {})}")
    
    return zip_path, zip_hash

def export_data_json():
    """
    Exporta todos os dados do banco em formato JSON legível
    Útil para auditoria e migração manual
    """
    if not os.path.exists(DB_PATH):
        return {'error': 'Database not found', 'stats': {}}
    
    conn = get_db()
    c = conn.cursor()
    
    export = {
        'exported_at': datetime.now().isoformat(),
        'system': 'WINDI Agent Certification System v0.2',
        'stats': {},
        'applications': [],
        'waqp_evaluations': [],
        'shp_handshakes': [],
        'certifications': []
    }
    
    # Aplicações
    c.execute('SELECT * FROM applications ORDER BY created_at')
    for row in c.fetchall():
        export['applications'].append(dict(row))
    
    # Avaliações WAQP
    c.execute('SELECT * FROM waqp_evaluations ORDER BY application_id, scenario_id')
    for row in c.fetchall():
        export['waqp_evaluations'].append(dict(row))
    
    # Handshakes SHP
    c.execute('SELECT * FROM shp_handshakes ORDER BY application_id, step')
    for row in c.fetchall():
        export['shp_handshakes'].append(dict(row))
    
    # Certificações
    c.execute('SELECT * FROM certifications ORDER BY issued_at')
    for row in c.fetchall():
        export['certifications'].append(dict(row))
    
    # Stats
    export['stats'] = {
        'total_applications': len(export['applications']),
        'total_evaluations': len(export['waqp_evaluations']),
        'total_handshakes': len(export['shp_handshakes']),
        'total_certifications': len(export['certifications']),
        'certified_gold': len([c for c in export['certifications'] if c.get('level') == 'gold']),
        'certified_silver': len([c for c in export['certifications'] if c.get('level') == 'silver']),
        'certified_bronze': len([c for c in export['certifications'] if c.get('level') == 'bronze'])
    }
    
    conn.close()
    return export

def restore_backup(backup_file):
    """
    Restaura sistema completo de um backup
    """
    if not os.path.exists(backup_file):
        print(f"❌ Arquivo não encontrado: {backup_file}")
        return False
    
    print(f"🔄 Restaurando de: {backup_file}")
    
    # Criar diretório temporário para extração
    temp_dir = Path('./temp_restore')
    temp_dir.mkdir(exist_ok=True)
    
    try:
        # Extrair ZIP
        shutil.unpack_archive(backup_file, temp_dir)
        
        # Encontrar diretório do backup
        backup_dirs = [d for d in temp_dir.iterdir() if d.is_dir()]
        if not backup_dirs:
            print("❌ Backup inválido: estrutura não encontrada")
            return False
        
        backup_content = backup_dirs[0]
        
        # Verificar manifesto
        manifest_path = backup_content / 'manifest.json'
        if manifest_path.exists():
            with open(manifest_path) as f:
                manifest = json.load(f)
            print(f"   📋 Backup ID: {manifest.get('backup_id')}")
            print(f"   📅 Criado em: {manifest.get('created_at')}")
            print(f"   🖥️ Servidor origem: {manifest.get('source_server')}")
        
        # Confirmar restauração
        confirm = input("\n⚠️ Isso substituirá dados existentes. Continuar? (s/N): ")
        if confirm.lower() != 's':
            print("Restauração cancelada.")
            shutil.rmtree(temp_dir)
            return False
        
        # Restaurar banco de dados
        db_backup = backup_content / 'windi_certification.db'
        if db_backup.exists():
            # Fazer backup do atual antes
            if os.path.exists(DB_PATH):
                shutil.copy2(DB_PATH, f"{DB_PATH}.pre_restore")
                print(f"   ✓ Backup do DB atual: {DB_PATH}.pre_restore")
            
            shutil.copy2(db_backup, DB_PATH)
            print(f"   ✓ Banco de dados restaurado")
        
        # Restaurar templates
        templates_backup = backup_content / 'templates'
        if templates_backup.exists():
            templates_dest = Path(APP_DIR) / 'templates'
            if templates_dest.exists():
                shutil.rmtree(templates_dest)
            shutil.copytree(templates_backup, templates_dest)
            print(f"   ✓ Templates restaurados")
        
        # Restaurar static
        static_backup = backup_content / 'static'
        if static_backup.exists():
            static_dest = Path(APP_DIR) / 'static'
            if static_dest.exists():
                shutil.rmtree(static_dest)
            shutil.copytree(static_backup, static_dest)
            print(f"   ✓ Static restaurado")
        
        # Limpar
        shutil.rmtree(temp_dir)
        
        print("\n✅ Restauração completa!")
        
        # Mostrar stats
        export = export_data_json()
        print(f"   📊 Aplicações: {export['stats']['total_applications']}")
        print(f"   📊 Certificações: {export['stats']['total_certifications']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na restauração: {e}")
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        return False

def auto_backup():
    """
    Backup automático para uso com cron
    Mantém últimos 10 backups
    """
    # Criar backup
    zip_path, zip_hash = backup_full()
    
    # Limpar backups antigos (manter últimos 10)
    backup_dir = Path(BACKUP_DIR)
    backups = sorted(backup_dir.glob('windi_cert_backup_*.zip'), key=os.path.getmtime)
    
    while len(backups) > 10:
        old = backups.pop(0)
        old.unlink()
        print(f"   🗑️ Removido backup antigo: {old.name}")
    
    # Log para registro
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'file': str(zip_path),
        'hash': zip_hash,
        'type': 'auto'
    }
    
    log_file = backup_dir / 'backup_log.jsonl'
    with open(log_file, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')
    
    return zip_path

def print_help():
    print("""
WINDI Certification - Backup & Restore System
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Comandos:
    backup              Cria backup completo (código + dados)
    restore <arquivo>   Restaura de um arquivo de backup
    export-json         Exporta apenas dados em JSON
    auto                Backup automático (para cron)
    list                Lista backups existentes
    
Exemplos:
    python3 backup_restore.py backup
    python3 backup_restore.py restore ./backups/windi_cert_backup_20260127.zip
    python3 backup_restore.py export-json > dados.json

Para cron (backup a cada hora):
    0 * * * * cd /path/to/windi_certification && python3 backup_restore.py auto

Migração RunPod → Strato:
    1. No RunPod:  python3 backup_restore.py backup
    2. Download do ZIP gerado
    3. Upload para Strato
    4. No Strato:  python3 backup_restore.py restore <arquivo.zip>
    
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"AI processes. Human decides. WINDI guarantees."
    """)

def list_backups():
    """Lista backups existentes"""
    backup_dir = Path(BACKUP_DIR)
    if not backup_dir.exists():
        print("Nenhum backup encontrado.")
        return
    
    backups = sorted(backup_dir.glob('windi_cert_backup_*.zip'), key=os.path.getmtime, reverse=True)
    
    if not backups:
        print("Nenhum backup encontrado.")
        return
    
    print("\n📁 Backups disponíveis:")
    print("━" * 60)
    
    for b in backups:
        size = b.stat().st_size / 1024  # KB
        mtime = datetime.fromtimestamp(b.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
        print(f"   {b.name:<45} {size:>6.1f} KB  {mtime}")
    
    print("━" * 60)
    print(f"Total: {len(backups)} backups\n")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print_help()
        sys.exit(0)
    
    command = sys.argv[1].lower()
    
    if command == 'backup':
        backup_full()
    
    elif command == 'restore':
        if len(sys.argv) < 3:
            print("❌ Especifique o arquivo de backup")
            print("   Uso: python3 backup_restore.py restore <arquivo.zip>")
            sys.exit(1)
        restore_backup(sys.argv[2])
    
    elif command == 'export-json':
        export = export_data_json()
        print(json.dumps(export, indent=2, ensure_ascii=False))
    
    elif command == 'auto':
        auto_backup()
    
    elif command == 'list':
        list_backups()
    
    elif command in ['help', '-h', '--help']:
        print_help()
    
    else:
        print(f"❌ Comando desconhecido: {command}")
        print_help()
        sys.exit(1)
