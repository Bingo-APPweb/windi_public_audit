#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# WINDI Wisdom Protocol v0.1 — Instalação no Strato
# 
# Uso: bash install_wisdom_v01.sh
#
# O que faz:
# 1. Cria estrutura de directórios em /opt/windi/engine/wisdom/
# 2. Copia schema.py e wisdom_block_manager.py
# 3. Sela o Bloco Genesis (WB-INSP-00000000)
# 4. Testa o ciclo completo: create → list → tick → decide
#
# "AI processes. Human decides. WINDI guarantees."
# ═══════════════════════════════════════════════════════════════════

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
GOLD='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m'

BASE="/opt/windi/engine/wisdom"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${GOLD}"
echo "═══════════════════════════════════════════════════════"
echo "  🛡️  WINDI Wisdom Protocol v0.1 — Instalação"
echo "  🐉 Three Dragons Convergence • 2026-02-21"
echo "═══════════════════════════════════════════════════════"
echo -e "${NC}"

# ─── Passo 1: Estrutura de Directórios ───
echo -e "${CYAN}[1/5] Criando estrutura de directórios...${NC}"

mkdir -p "${BASE}"/{data,logs}
mkdir -p "${BASE}"/candidates/{echo,pattern,archetype}
mkdir -p "${BASE}"/blocks/{governance,infrastructure,legal-compliance,security-risk,operations,human-factors,philosophy-ethics,culture-language,manifest-ledger}

touch "${BASE}/__init__.py"

echo -e "${GREEN}  ✅ Directórios criados em ${BASE}${NC}"

# ─── Passo 2: Copiar Módulos ───
echo -e "${CYAN}[2/5] Copiando módulos Python...${NC}"

if [ -f "${SCRIPT_DIR}/schema.py" ]; then
    cp "${SCRIPT_DIR}/schema.py" "${BASE}/schema.py"
    echo -e "${GREEN}  ✅ schema.py copiado${NC}"
else
    echo -e "${RED}  ❌ schema.py não encontrado em ${SCRIPT_DIR}${NC}"
    echo "     Certifica-te que schema.py está no mesmo directório que este script."
    exit 1
fi

if [ -f "${SCRIPT_DIR}/wisdom_block_manager.py" ]; then
    cp "${SCRIPT_DIR}/wisdom_block_manager.py" "${BASE}/wisdom_block_manager.py"
    chmod +x "${BASE}/wisdom_block_manager.py"
    echo -e "${GREEN}  ✅ wisdom_block_manager.py copiado${NC}"
else
    echo -e "${RED}  ❌ wisdom_block_manager.py não encontrado em ${SCRIPT_DIR}${NC}"
    exit 1
fi

# ─── Passo 3: Selar Bloco Genesis ───
echo -e "${CYAN}[3/5] Selando Bloco Genesis (WB-INSP-00000000)...${NC}"

cd "${BASE}"
python3 wisdom_block_manager.py genesis

echo -e "${GREEN}  ✅ Genesis selado${NC}"

# ─── Passo 4: Teste do Ciclo Completo ───
echo -e "${CYAN}[4/5] Testando ciclo completo...${NC}"

echo -e "  ${GOLD}→ Criando candidato de teste...${NC}"
python3 wisdom_block_manager.py create \
    --session "install-test-$(date +%Y%m%d)" \
    --chamber pattern \
    --essence "O átomo precisa estar estável antes do organismo crescer. Convergência Guardian×Architect×Witness." \
    --tags "governance,wisdom,convergence,test" \
    --situation "milestone" \
    --actors "guardian,architect,witness,human_dragon" \
    --intensity 0.9

echo ""
echo -e "  ${GOLD}→ Dashboard de Selagem:${NC}"
python3 wisdom_block_manager.py list

echo ""
echo -e "  ${GOLD}→ Simulando passagem de 60 minutos...${NC}"
python3 wisdom_block_manager.py tick --minutes 60

echo ""
echo -e "  ${GOLD}→ Info do protocolo:${NC}"
python3 wisdom_block_manager.py info

# ─── Passo 5: Verificação Final ───
echo -e "${CYAN}[5/5] Verificação final...${NC}"

echo ""
echo -e "${GOLD}Estrutura criada:${NC}"
find "${BASE}" -type f | head -30 | sort

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ WINDI Wisdom Protocol v0.1 — Instalação Completa${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${GOLD}Próximos passos:${NC}"
echo -e "  1. Revisa o candidato de teste no Dashboard"
echo -e "  2. Decide (approve/defer/reject):"
echo -e "     ${CYAN}python3 ${BASE}/wisdom_block_manager.py decide \\"
echo -e "       <caminho-do-candidato.json> --action approve \\"
echo -e "       --category INSP --n1 philosophy-ethics --n4 canonical${NC}"
echo -e "  3. Verifica o manifest:"
echo -e "     ${CYAN}cat ${BASE}/manifest.json | python3 -m json.tool${NC}"
echo ""
echo -e "  ${GOLD}Nota sobre Ledger:${NC}"
echo -e "  O manager tenta POST para localhost:8101 (Ledger) e :8106 (Vault)."
echo -e "  Se ambos retornarem erro, a selagem local funciona normalmente."
echo -e "  Para adaptar o endpoint, edita LEDGER_URL em wisdom_block_manager.py"
echo -e "  ou usa: ${CYAN}WISDOM_LEDGER_URL=http://... python3 wisdom_block_manager.py ...${NC}"
echo ""
echo -e "  🛡️🐉 ${GOLD}O rastro é a prova.${NC}"
