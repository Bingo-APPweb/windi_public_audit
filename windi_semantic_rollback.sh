#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# WINDI SEMANTIC ROLLBACK v2.1
# Emergency Rollback Script - Reverte migração semântica
# Marco Zero + 10 days | 29 Janeiro 2026
# ═══════════════════════════════════════════════════════════════════════════════
# "AI processes. Human decides. WINDI guarantees."
# ═══════════════════════════════════════════════════════════════════════════════
#
# USO:
#   ./windi_semantic_rollback.sh                    # Lista backups disponíveis
#   ./windi_semantic_rollback.sh <backup_dir>      # Restaura de backup específico
#   ./windi_semantic_rollback.sh --latest          # Restaura do backup mais recente
#   ./windi_semantic_rollback.sh --dry-run <dir>   # Simula sem executar
#
# ═══════════════════════════════════════════════════════════════════════════════

set -e

BACKUP_BASE="/opt/windi/backups"
ROLLBACK_LOG="/opt/windi/backups/rollback_$(date +%Y%m%d_%H%M).log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🔄 WINDI SEMANTIC ROLLBACK v2.1${NC}"
echo -e "${BLUE}   Emergency Rollback Script${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════════${NC}"
echo ""

# ═══════════════════════════════════════════════════════════════════════════════
# FUNCTION: List available backups
# ═══════════════════════════════════════════════════════════════════════════════

list_backups() {
    echo -e "${YELLOW}📦 Available semantic migration backups:${NC}"
    echo ""
    
    # Find all pre_semantic backups
    BACKUPS=$(find "$BACKUP_BASE" -maxdepth 1 -type d -name "pre_semantic_v2_1_*" 2>/dev/null | sort -r)
    
    if [ -z "$BACKUPS" ]; then
        echo -e "${RED}   ❌ No semantic migration backups found in $BACKUP_BASE${NC}"
        echo ""
        echo "   Looking for any recent backups..."
        ls -la "$BACKUP_BASE" | grep -E "^d" | tail -10
        return 1
    fi
    
    COUNT=0
    for backup in $BACKUPS; do
        COUNT=$((COUNT + 1))
        DIRNAME=$(basename "$backup")
        # Extract date from dirname
        DATE_PART=$(echo "$DIRNAME" | sed 's/pre_semantic_v2_1_//')
        
        # Check what files exist in backup
        FILES=""
        [ -f "$backup/windi_constitution.py" ] && FILES="${FILES}constitution "
        [ -f "$backup/windi_agent_v3.py" ] && FILES="${FILES}agent "
        [ -f "$backup/windi_gateway.py" ] && FILES="${FILES}gateway "
        [ -f "$backup/chat_integration.py" ] && FILES="${FILES}chat "
        [ -f "$backup/invariants.py" ] && FILES="${FILES}invariants "
        
        echo -e "   ${GREEN}[$COUNT]${NC} $DIRNAME"
        echo -e "       Files: ${FILES:-none}"
        echo ""
    done
    
    echo -e "${YELLOW}   Latest backup: $(echo "$BACKUPS" | head -1)${NC}"
    echo ""
}

# ═══════════════════════════════════════════════════════════════════════════════
# FUNCTION: Validate backup directory
# ═══════════════════════════════════════════════════════════════════════════════

validate_backup() {
    local BACKUP_DIR="$1"
    
    if [ ! -d "$BACKUP_DIR" ]; then
        echo -e "${RED}❌ Backup directory not found: $BACKUP_DIR${NC}"
        return 1
    fi
    
    # Check for at least one critical file
    if [ ! -f "$BACKUP_DIR/windi_constitution.py" ] && \
       [ ! -f "$BACKUP_DIR/windi_agent_v3.py" ] && \
       [ ! -f "$BACKUP_DIR/windi_gateway.py" ]; then
        echo -e "${RED}❌ No valid backup files found in: $BACKUP_DIR${NC}"
        return 1
    fi
    
    return 0
}

# ═══════════════════════════════════════════════════════════════════════════════
# FUNCTION: Perform rollback
# ═══════════════════════════════════════════════════════════════════════════════

perform_rollback() {
    local BACKUP_DIR="$1"
    local DRY_RUN="$2"
    
    echo -e "${YELLOW}🔄 Starting rollback from: $BACKUP_DIR${NC}"
    echo ""
    
    # Start logging
    if [ "$DRY_RUN" != "true" ]; then
        echo "WINDI SEMANTIC ROLLBACK LOG" > "$ROLLBACK_LOG"
        echo "Date: $(date)" >> "$ROLLBACK_LOG"
        echo "Source: $BACKUP_DIR" >> "$ROLLBACK_LOG"
        echo "========================================" >> "$ROLLBACK_LOG"
    fi
    
    # Rollback each file
    local RESTORED=0
    local FAILED=0
    
    # --- windi_constitution.py ---
    if [ -f "$BACKUP_DIR/windi_constitution.py" ]; then
        echo -n "   📄 windi_constitution.py → /opt/windi/engine/ ... "
        if [ "$DRY_RUN" = "true" ]; then
            echo -e "${BLUE}[DRY-RUN]${NC}"
        else
            if cp "$BACKUP_DIR/windi_constitution.py" /opt/windi/engine/windi_constitution.py; then
                echo -e "${GREEN}✅${NC}"
                echo "RESTORED: windi_constitution.py" >> "$ROLLBACK_LOG"
                RESTORED=$((RESTORED + 1))
            else
                echo -e "${RED}❌${NC}"
                echo "FAILED: windi_constitution.py" >> "$ROLLBACK_LOG"
                FAILED=$((FAILED + 1))
            fi
        fi
    fi
    
    # --- windi_agent_v3.py ---
    if [ -f "$BACKUP_DIR/windi_agent_v3.py" ]; then
        echo -n "   📄 windi_agent_v3.py → /opt/windi/engine/ ... "
        if [ "$DRY_RUN" = "true" ]; then
            echo -e "${BLUE}[DRY-RUN]${NC}"
        else
            if cp "$BACKUP_DIR/windi_agent_v3.py" /opt/windi/engine/windi_agent_v3.py; then
                echo -e "${GREEN}✅${NC}"
                echo "RESTORED: windi_agent_v3.py" >> "$ROLLBACK_LOG"
                RESTORED=$((RESTORED + 1))
            else
                echo -e "${RED}❌${NC}"
                echo "FAILED: windi_agent_v3.py" >> "$ROLLBACK_LOG"
                FAILED=$((FAILED + 1))
            fi
        fi
    fi
    
    # --- invariants.py ---
    if [ -f "$BACKUP_DIR/invariants.py" ]; then
        echo -n "   📄 invariants.py → /opt/windi/brain/ ... "
        if [ "$DRY_RUN" = "true" ]; then
            echo -e "${BLUE}[DRY-RUN]${NC}"
        else
            if cp "$BACKUP_DIR/invariants.py" /opt/windi/brain/invariants.py; then
                echo -e "${GREEN}✅${NC}"
                echo "RESTORED: invariants.py" >> "$ROLLBACK_LOG"
                RESTORED=$((RESTORED + 1))
            else
                echo -e "${RED}❌${NC}"
                echo "FAILED: invariants.py" >> "$ROLLBACK_LOG"
                FAILED=$((FAILED + 1))
            fi
        fi
    fi
    
    # --- windi_gateway.py ---
    if [ -f "$BACKUP_DIR/windi_gateway.py" ]; then
        echo -n "   📄 windi_gateway.py → /opt/windi/gateway/ ... "
        if [ "$DRY_RUN" = "true" ]; then
            echo -e "${BLUE}[DRY-RUN]${NC}"
        else
            if cp "$BACKUP_DIR/windi_gateway.py" /opt/windi/gateway/windi_gateway.py; then
                echo -e "${GREEN}✅${NC}"
                echo "RESTORED: windi_gateway.py" >> "$ROLLBACK_LOG"
                RESTORED=$((RESTORED + 1))
            else
                echo -e "${RED}❌${NC}"
                echo "FAILED: windi_gateway.py" >> "$ROLLBACK_LOG"
                FAILED=$((FAILED + 1))
            fi
        fi
    fi
    
    # --- chat_integration.py ---
    if [ -f "$BACKUP_DIR/chat_integration.py" ]; then
        echo -n "   📄 chat_integration.py → /opt/windi/a4desk-editor/intent_parser/ ... "
        if [ "$DRY_RUN" = "true" ]; then
            echo -e "${BLUE}[DRY-RUN]${NC}"
        else
            if cp "$BACKUP_DIR/chat_integration.py" /opt/windi/a4desk-editor/intent_parser/chat_integration.py; then
                echo -e "${GREEN}✅${NC}"
                echo "RESTORED: chat_integration.py" >> "$ROLLBACK_LOG"
                RESTORED=$((RESTORED + 1))
            else
                echo -e "${RED}❌${NC}"
                echo "FAILED: chat_integration.py" >> "$ROLLBACK_LOG"
                FAILED=$((FAILED + 1))
            fi
        fi
    fi
    
    # --- constitutional_validator_v2.py ---
    if [ -f "$BACKUP_DIR/constitutional_validator_v2.py" ]; then
        echo -n "   📄 constitutional_validator_v2.py → /opt/windi/templates/ ... "
        if [ "$DRY_RUN" = "true" ]; then
            echo -e "${BLUE}[DRY-RUN]${NC}"
        else
            if cp "$BACKUP_DIR/constitutional_validator_v2.py" /opt/windi/templates/constitutional_validator_v2.py; then
                echo -e "${GREEN}✅${NC}"
                echo "RESTORED: constitutional_validator_v2.py" >> "$ROLLBACK_LOG"
                RESTORED=$((RESTORED + 1))
            else
                echo -e "${RED}❌${NC}"
                echo "FAILED: constitutional_validator_v2.py" >> "$ROLLBACK_LOG"
                FAILED=$((FAILED + 1))
            fi
        fi
    fi
    
    # --- Remove semantic_framework_v2_1.py (created by migration) ---
    if [ -f /opt/windi/engine/semantic_framework_v2_1.py ]; then
        echo -n "   🗑️  Removing semantic_framework_v2_1.py ... "
        if [ "$DRY_RUN" = "true" ]; then
            echo -e "${BLUE}[DRY-RUN]${NC}"
        else
            if rm /opt/windi/engine/semantic_framework_v2_1.py; then
                echo -e "${GREEN}✅${NC}"
                echo "REMOVED: semantic_framework_v2_1.py" >> "$ROLLBACK_LOG"
            else
                echo -e "${YELLOW}⚠️ (may not exist)${NC}"
            fi
        fi
    fi
    
    echo ""
    
    if [ "$DRY_RUN" = "true" ]; then
        echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════════${NC}"
        echo -e "${BLUE}   DRY-RUN COMPLETE - No changes made${NC}"
        echo -e "${BLUE}   Run without --dry-run to execute rollback${NC}"
        echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════════${NC}"
    else
        echo "========================================" >> "$ROLLBACK_LOG"
        echo "RESTORED: $RESTORED files" >> "$ROLLBACK_LOG"
        echo "FAILED: $FAILED files" >> "$ROLLBACK_LOG"
        
        echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}   ✅ ROLLBACK COMPLETE${NC}"
        echo -e "${GREEN}   Restored: $RESTORED files${NC}"
        if [ $FAILED -gt 0 ]; then
            echo -e "${RED}   Failed: $FAILED files${NC}"
        fi
        echo -e "${GREEN}   Log: $ROLLBACK_LOG${NC}"
        echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════════════${NC}"
        
        echo ""
        echo -e "${YELLOW}⚠️ NEXT STEPS - Restart services:${NC}"
        echo ""
        echo "   sudo systemctl restart windi-brain.service"
        echo "   sudo systemctl restart windi-cortex.service"
        echo "   sudo systemctl restart windi-gateway.service"
        echo ""
        echo "   pkill -f 'python3 a4desk_tiptap_babel.py'"
        echo "   cd /opt/windi/a4desk-editor && nohup python3 a4desk_tiptap_babel.py > /tmp/a4desk.log 2>&1 &"
        echo ""
    fi
}

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

DRY_RUN="false"
BACKUP_DIR=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN="true"
            shift
            ;;
        --latest)
            # Find most recent backup
            BACKUP_DIR=$(find "$BACKUP_BASE" -maxdepth 1 -type d -name "pre_semantic_v2_1_*" 2>/dev/null | sort -r | head -1)
            if [ -z "$BACKUP_DIR" ]; then
                echo -e "${RED}❌ No semantic migration backups found${NC}"
                exit 1
            fi
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [options] [backup_directory]"
            echo ""
            echo "Options:"
            echo "  --latest     Use most recent backup"
            echo "  --dry-run    Show what would be done without executing"
            echo "  --help       Show this help"
            echo ""
            echo "Examples:"
            echo "  $0                                    # List available backups"
            echo "  $0 --latest                           # Rollback from latest backup"
            echo "  $0 /opt/windi/backups/pre_semantic_v2_1_20260129_1430"
            echo "  $0 --dry-run --latest                 # Preview rollback"
            exit 0
            ;;
        *)
            BACKUP_DIR="$1"
            shift
            ;;
    esac
done

# If no backup specified, list available backups
if [ -z "$BACKUP_DIR" ]; then
    list_backups
    echo ""
    echo -e "${YELLOW}Usage:${NC}"
    echo "  $0 --latest                    # Rollback from latest backup"
    echo "  $0 <backup_directory>          # Rollback from specific backup"
    echo "  $0 --dry-run --latest          # Preview without executing"
    echo ""
    exit 0
fi

# Validate backup directory
if ! validate_backup "$BACKUP_DIR"; then
    exit 1
fi

# Confirm unless dry-run
if [ "$DRY_RUN" != "true" ]; then
    echo -e "${RED}⚠️  WARNING: This will overwrite current files with backup versions!${NC}"
    echo ""
    echo "   Backup source: $BACKUP_DIR"
    echo ""
    read -p "   Are you sure you want to proceed? (yes/no): " CONFIRM
    
    if [ "$CONFIRM" != "yes" ]; then
        echo ""
        echo "   Rollback cancelled."
        exit 0
    fi
    echo ""
fi

# Perform rollback
perform_rollback "$BACKUP_DIR" "$DRY_RUN"

echo ""
echo -e "${BLUE}\"AI processes. Human decides. WINDI guarantees.\"${NC}"
echo ""
