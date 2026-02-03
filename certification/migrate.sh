#!/bin/bash
# ============================================================
# WINDI Certification - Migration Script
# RunPod → Strato Server Transfer
# ============================================================
#
# Este script facilita a migração do sistema de certificação
# do RunPod para o servidor Strato.
#
# Princípio: "AI processes. Human decides. WINDI guarantees."
# ============================================================

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
GOLD='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GOLD}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  WINDI Agent Certification - Server Migration Tool"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${NC}"

# Detectar ambiente
detect_environment() {
    if [ -d "/workspace" ]; then
        echo -e "${YELLOW}📍 Ambiente detectado: RunPod${NC}"
        ENV="runpod"
    elif hostname | grep -q "strato\|h29"; then
        echo -e "${YELLOW}📍 Ambiente detectado: Strato${NC}"
        ENV="strato"
    else
        echo -e "${YELLOW}📍 Ambiente: Desconhecido${NC}"
        ENV="unknown"
    fi
}

# Menu principal
show_menu() {
    echo ""
    echo "Opções:"
    echo "  1) Criar backup para migração"
    echo "  2) Restaurar de backup"
    echo "  3) Verificar sistema"
    echo "  4) Configurar auto-backup (cron)"
    echo "  5) Instruções de migração"
    echo "  6) Sair"
    echo ""
    read -p "Escolha [1-6]: " choice
}

# Criar backup
create_backup() {
    echo -e "\n${GREEN}📦 Criando backup completo...${NC}"
    python3 backup_restore.py backup
    
    echo -e "\n${YELLOW}📋 Próximos passos:${NC}"
    echo "  1. Faça download do arquivo .zip gerado"
    echo "  2. Upload para o servidor Strato"
    echo "  3. Execute: python3 backup_restore.py restore <arquivo.zip>"
}

# Restaurar backup
restore_backup() {
    echo -e "\n${GREEN}🔄 Restauração de backup${NC}"
    
    # Listar backups disponíveis
    python3 backup_restore.py list
    
    read -p "Caminho do arquivo de backup: " backup_file
    
    if [ -f "$backup_file" ]; then
        python3 backup_restore.py restore "$backup_file"
    else
        echo -e "${RED}❌ Arquivo não encontrado: $backup_file${NC}"
    fi
}

# Verificar sistema
verify_system() {
    echo -e "\n${GREEN}🔍 Verificando sistema...${NC}\n"
    
    # Verificar Python
    echo -n "Python 3: "
    if command -v python3 &> /dev/null; then
        python3 --version
    else
        echo -e "${RED}Não encontrado${NC}"
    fi
    
    # Verificar Flask
    echo -n "Flask: "
    python3 -c "import flask; print(flask.__version__)" 2>/dev/null || echo -e "${RED}Não instalado${NC}"
    
    # Verificar banco de dados
    DB_PATH=${WINDI_CERT_DB:-"windi_certification.db"}
    echo -n "Banco de dados: "
    if [ -f "$DB_PATH" ]; then
        SIZE=$(du -h "$DB_PATH" | cut -f1)
        echo -e "${GREEN}$DB_PATH ($SIZE)${NC}"
    else
        echo -e "${YELLOW}Não existe ainda (será criado no primeiro uso)${NC}"
    fi
    
    # Verificar templates
    echo -n "Templates: "
    if [ -d "templates" ]; then
        COUNT=$(ls templates/*.html 2>/dev/null | wc -l)
        echo -e "${GREEN}$COUNT arquivos${NC}"
    else
        echo -e "${RED}Diretório não encontrado${NC}"
    fi
    
    # Verificar porta
    echo -n "Porta padrão: "
    PORT=${PORT:-5000}
    echo "$PORT"
    
    # Stats do banco
    if [ -f "$DB_PATH" ]; then
        echo -e "\n${GOLD}📊 Estatísticas:${NC}"
        python3 -c "
import sqlite3
conn = sqlite3.connect('$DB_PATH')
c = conn.cursor()
try:
    c.execute('SELECT COUNT(*) FROM applications')
    apps = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM certifications')
    certs = c.fetchone()[0]
    print(f'   Aplicações: {apps}')
    print(f'   Certificações: {certs}')
except:
    print('   (tabelas ainda não criadas)')
conn.close()
"
    fi
}

# Configurar cron
setup_cron() {
    echo -e "\n${GREEN}⏰ Configurando backup automático...${NC}"
    
    SCRIPT_PATH=$(pwd)/backup_restore.py
    CRON_LINE="0 * * * * cd $(pwd) && python3 $SCRIPT_PATH auto >> /var/log/windi_backup.log 2>&1"
    
    echo "Linha para adicionar ao crontab:"
    echo -e "${YELLOW}$CRON_LINE${NC}"
    echo ""
    
    read -p "Adicionar ao crontab agora? (s/N): " confirm
    if [ "$confirm" = "s" ] || [ "$confirm" = "S" ]; then
        (crontab -l 2>/dev/null; echo "$CRON_LINE") | crontab -
        echo -e "${GREEN}✓ Crontab atualizado${NC}"
    fi
}

# Instruções de migração
show_instructions() {
    echo -e "${GOLD}"
    cat << 'EOF'
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  INSTRUÇÕES DE MIGRAÇÃO: RunPod → Strato
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PASSO 1: NO RUNPOD
──────────────────
  $ cd /workspace/windi_certification
  $ python3 backup_restore.py backup
  
  → Anote o nome do arquivo gerado (ex: windi_cert_backup_20260127_143022.zip)
  → Faça download via interface RunPod ou SCP

PASSO 2: TRANSFERÊNCIA
──────────────────────
  Opção A - Via SCP:
  $ scp backups/windi_cert_backup_*.zip user@strato:/path/to/destination/

  Opção B - Via interface web do Strato

PASSO 3: NO STRATO
──────────────────
  # Criar diretório (em IP diferente do A4 Desk!)
  $ mkdir -p /var/www/windi_certification
  $ cd /var/www/windi_certification
  
  # Upload do código (primeira vez)
  $ unzip windi_certification.zip
  
  # Restaurar dados do backup
  $ python3 backup_restore.py restore /path/to/backup.zip
  
  # Instalar dependências
  $ pip install flask
  
  # Configurar porta (diferente do A4 Desk 8888)
  $ export PORT=5001
  
  # Rodar em background
  $ nohup python3 app.py > /var/log/windi_cert.log 2>&1 &

PASSO 4: CONFIGURAR NGINX (opcional)
────────────────────────────────────
  # /etc/nginx/sites-available/windi_certification
  
  server {
      listen 80;
      server_name cert.windi.example.com;
      
      location / {
          proxy_pass http://127.0.0.1:5001;
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
      }
  }

PASSO 5: BACKUP AUTOMÁTICO
──────────────────────────
  $ crontab -e
  # Adicionar:
  0 * * * * cd /var/www/windi_certification && python3 backup_restore.py auto

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INTEGRAÇÃO COM WINDI PUBLISHING HOUSE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

O menu "SHP Protocol" na Publishing House pode apontar para:
  - /cert/ (registro)
  - /cert/admin (dashboard)
  
Os backups podem ser sincronizados com:
  /workspace/windi/backups/ (sistema existente)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"AI processes. Human decides. WINDI guarantees."
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF
    echo -e "${NC}"
}

# Main loop
detect_environment

while true; do
    show_menu
    
    case $choice in
        1) create_backup ;;
        2) restore_backup ;;
        3) verify_system ;;
        4) setup_cron ;;
        5) show_instructions ;;
        6) 
            echo -e "\n${GOLD}Até logo! WINDI guarantees. 🤝${NC}\n"
            exit 0
            ;;
        *)
            echo -e "${RED}Opção inválida${NC}"
            ;;
    esac
done
