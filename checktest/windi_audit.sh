#!/bin/bash
# ============================================================
# WINDI PLATFORM AUDIT — Full Health Check
# Run on Strato server: bash windi_audit.sh | tee audit_$(date +%Y%m%d_%H%M%S).log
# ============================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

PASS=0
FAIL=0
WARN=0

print_header() {
    echo ""
    echo -e "${BLUE}${BOLD}══════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}${BOLD}  $1${NC}"
    echo -e "${BLUE}${BOLD}══════════════════════════════════════════════════${NC}"
}

check_ok()   { echo -e "  ${GREEN}✅ $1${NC}"; ((PASS++)); }
check_fail() { echo -e "  ${RED}❌ $1${NC}"; ((FAIL++)); }
check_warn() { echo -e "  ${YELLOW}⚠️  $1${NC}"; ((WARN++)); }
check_info() { echo -e "  ${CYAN}ℹ️  $1${NC}"; }

check_endpoint() {
    local NAME=$1
    local URL=$2
    local EXPECTED_CODE=${3:-200}
    local RESULT
    local HTTP_CODE
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 --max-time 8 "$URL")
    if [ "$HTTP_CODE" = "$EXPECTED_CODE" ]; then
        check_ok "$NAME → HTTP $HTTP_CODE"
    elif [ "$HTTP_CODE" = "000" ]; then
        check_fail "$NAME → TIMEOUT / NOT REACHABLE"
    else
        check_warn "$NAME → HTTP $HTTP_CODE (expected $EXPECTED_CODE)"
    fi
}

check_port() {
    local PORT=$1
    local SERVICE=$2
    if ss -tlnp | grep -q ":$PORT "; then
        local PROC=$(ss -tlnp | grep ":$PORT " | grep -oP 'pid=\K[0-9]+' | head -1)
        local PNAME=$(ps -p $PROC -o comm= 2>/dev/null || echo "unknown")
        check_ok "Port $PORT ($SERVICE) → LISTENING [$PNAME]"
    else
        check_fail "Port $PORT ($SERVICE) → NOT LISTENING"
    fi
}

check_systemd() {
    local SERVICE=$1
    local STATUS=$(systemctl is-active windi-$SERVICE 2>/dev/null)
    if [ "$STATUS" = "active" ]; then
        check_ok "systemd: windi-$SERVICE → active"
    else
        check_fail "systemd: windi-$SERVICE → $STATUS"
    fi
}

check_db() {
    local NAME=$1
    local PATH=$2
    if [ -f "$PATH" ]; then
        local SIZE=$(du -h "$PATH" | cut -f1)
        local ROWS=$(sqlite3 "$PATH" "SELECT COUNT(*) FROM sqlite_master WHERE type='table';" 2>/dev/null || echo "?")
        check_ok "DB: $NAME → EXISTS ($SIZE, $ROWS tables)"
    else
        check_fail "DB: $NAME → NOT FOUND at $PATH"
    fi
}

echo ""
echo -e "${BOLD}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║     WINDI PLATFORM AUDIT — $(date '+%Y-%m-%d %H:%M:%S')     ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════════════╝${NC}"

# ── 1. SYSTEM RESOURCES ─────────────────────────────────────
print_header "1. SYSTEM RESOURCES"
CPU_LOAD=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | tr -d ',')
MEM_FREE=$(free -m | awk 'NR==2{printf "%.0f%%", $3*100/$2}')
DISK_USED=$(df -h /opt/windi 2>/dev/null | awk 'NR==2{print $5}' || df -h / | awk 'NR==2{print $5}')
check_info "CPU Load: $CPU_LOAD | RAM Used: $MEM_FREE | Disk /opt/windi: $DISK_USED"
LOAD_NUM=$(echo $CPU_LOAD | tr -d ',')
if (( $(echo "$LOAD_NUM < 2.0" | bc -l 2>/dev/null || echo 1) )); then
    check_ok "CPU load within normal range ($CPU_LOAD)"
else
    check_warn "CPU load elevated ($CPU_LOAD)"
fi

# ── 2. SYSTEMD SERVICES ─────────────────────────────────────
print_header "2. SYSTEMD SERVICES"
for SVC in landing-pmg forensic-ledger forensic-vault export-engine communique jmpg-viewer desktop sentinel sentinel-law wallet; do
    check_systemd $SVC
done

echo ""
check_info "Checking additional known services..."
for SVC in brain bridge clone cortex gateway masterarbeit; do
    STATUS=$(systemctl is-active windi-$SVC 2>/dev/null)
    if [ "$STATUS" = "active" ]; then
        check_ok "systemd: windi-$SVC → active"
    else
        check_warn "systemd: windi-$SVC → $STATUS (optional)"
    fi
done

# ── 3. PORTS LISTENING ──────────────────────────────────────
print_header "3. PORT LISTENING CHECK"
check_port 8100 "Desktop"
check_port 8101 "Forensic Ledger (SEALED)"
check_port 8102 "Sentinel LAW"
check_port 8103 "Export Engine"
check_port 8104 "JMPG Viewer"
check_port 8105 "Communiqué Engine"
check_port 8106 "Forensic Vault"
check_port 8107 "Landing PMG"
check_port 8108 "Dragon v1.3.0"
check_port 8114 "Verify Public"
check_port 8091 "Sandbox Core / Agent Corps"
check_port 8080 "Governance API"

# ── 4. NOHUP PROCESSES ──────────────────────────────────────
print_header "4. NOHUP PROCESSES"
NOHUP_COUNT=$(ps aux | grep python | grep -v grep | wc -l)
check_info "Active python processes: $NOHUP_COUNT"
ps aux | grep -E "python.*808[0-9]|python.*809[0-9]|python.*81[0-9]{2}" | grep -v grep | while read -r line; do
    PORT=$(echo "$line" | grep -oP '\d{4}' | grep -E '^81|^80' | head -1)
    PID=$(echo "$line" | awk '{print $2}')
    SCRIPT=$(echo "$line" | awk '{print $NF}' | rev | cut -d'/' -f1 | rev)
    check_info "PID $PID → port ~$PORT → $SCRIPT"
done

# Check specifically for Dragon
if ps aux | grep -q "dragon" 2>/dev/null; then
    check_ok "Dragon process running"
else
    check_warn "Dragon process not detected (check port 8108)"
fi

# Check for Verify Public
if ps aux | grep -q "verify" 2>/dev/null; then
    check_ok "Verify Public process running"
else
    check_warn "Verify Public process not detected (check port 8114)"
fi

# Check Agent Corps
if ps aux | grep -q "constitutional" 2>/dev/null; then
    check_ok "Constitutional Agent (Agent Corps :8091) running"
else
    check_warn "Constitutional Agent not detected (check port 8091)"
fi

# ── 5. HTTP ENDPOINT TESTS ──────────────────────────────────
print_header "5. HTTP ENDPOINT TESTS (localhost)"

# Core pipeline
check_endpoint "Landing PMG"        "http://localhost:8107/"
check_endpoint "Landing /personal"  "http://localhost:8107/personal/"
check_endpoint "Forensic Ledger"    "http://localhost:8101/api/health"
check_endpoint "Export Engine"      "http://localhost:8103/health"
check_endpoint "Communiqué Engine"  "http://localhost:8105/health"
check_endpoint "Forensic Vault"     "http://localhost:8106/health"
check_endpoint "JMPG Viewer"        "http://localhost:8104/health"
check_endpoint "Desktop"            "http://localhost:8100/health"
check_endpoint "Sentinel LAW"       "http://localhost:8102/health"
check_endpoint "Verify Public"      "http://localhost:8114/verify-public/"
check_endpoint "Dragon Hub"         "http://localhost:8108/health"

echo ""
check_info "--- Agent Corps endpoints ---"
check_endpoint "Agent Corps Root"   "http://localhost:8091/health"
check_endpoint "W-LEGAL-001"        "http://localhost:8091/legal/health"
check_endpoint "W-NOTARY-001"       "http://localhost:8091/notary/health"
check_endpoint "W-COMPLY-001"       "http://localhost:8091/compliance/health"
check_endpoint "W-COMM-001"         "http://localhost:8091/comm/health"
check_endpoint "W-JOURN-001"        "http://localhost:8091/journalism/health"
check_endpoint "W-AUDIT-001"        "http://localhost:8091/audit/health"
check_endpoint "W-ACCT-001"         "http://localhost:8091/accounting/health"
check_endpoint "Grove Arena"        "http://localhost:8091/grove/health"

echo ""
check_info "--- Verify Public critical paths ---"
check_endpoint "Verify ?id param"   "http://localhost:8114/verify-public/?id=WINDI-I11-CONSTITUTIONAL-20260305"
check_endpoint "Ledger Receipt API" "http://localhost:8101/api/receipts/WINDI-I11-CONSTITUTIONAL-20260305"
check_endpoint "Ledger Verify API"  "http://localhost:8101/api/verify/WINDI-I11-CONSTITUTIONAL-20260305"

# ── 6. NGINX STATUS ─────────────────────────────────────────
print_header "6. NGINX STATUS"
if sudo nginx -t 2>&1 | grep -q "ok"; then
    check_ok "nginx config syntax OK"
else
    check_fail "nginx config has errors"
    sudo nginx -t 2>&1
fi

NGINX_STATUS=$(systemctl is-active nginx)
if [ "$NGINX_STATUS" = "active" ]; then
    check_ok "nginx service → active"
else
    check_fail "nginx service → $NGINX_STATUS"
fi

# Check HTTPS endpoints via windi-domain.com
echo ""
check_info "--- HTTPS public endpoints (windi-domain.com) ---"
check_endpoint "HTTPS Landing"        "https://windi-domain.com/"
check_endpoint "HTTPS Verify Public"  "https://windi-domain.com/verify-public/"
check_endpoint "HTTPS Vault"          "https://windi-domain.com/vault/"
check_endpoint "HTTPS Governance"     "https://windi-domain.com/governance"
check_endpoint "HTTPS App/Palette"    "https://windi-domain.com/app/"
check_endpoint "HTTPS Guardian"       "https://windi-domain.com/guardian/"

# ── 7. DATABASE INTEGRITY ───────────────────────────────────
print_header "7. DATABASE INTEGRITY"
check_db "Forensic Ledger"     "/opt/windi/forensic-ledger/forensic_ledger.sqlite3"
check_db "Transparency Anchor" "/opt/windi/forensic-ledger/transparency_anchor.db"
check_db "D1 Documents"        "/opt/windi/forensic-ledger/d1_documents.db"
check_db "Sentinel LAW"        "/opt/windi/forensic-ledger/sentinel_law.db"

# Count receipts
RECEIPT_COUNT=$(sqlite3 /opt/windi/forensic-ledger/forensic_ledger.sqlite3 "SELECT COUNT(*) FROM receipts;" 2>/dev/null || echo "?")
check_info "Forensic Ledger receipts: $RECEIPT_COUNT"

if [ "$RECEIPT_COUNT" != "?" ] && [ "$RECEIPT_COUNT" -gt 40000 ]; then
    check_ok "Receipt count healthy ($RECEIPT_COUNT)"
elif [ "$RECEIPT_COUNT" = "?" ]; then
    check_warn "Could not count receipts (check DB)"
else
    check_warn "Receipt count lower than expected ($RECEIPT_COUNT)"
fi

# ── 8. DISK & LOG HEALTH ────────────────────────────────────
print_header "8. DISK & LOG HEALTH"
DISK_PERCENT=$(df /opt/windi 2>/dev/null | awk 'NR==2{print $5}' | tr -d '%' || df / | awk 'NR==2{print $5}' | tr -d '%')
if [ "$DISK_PERCENT" -lt 80 ]; then
    check_ok "Disk usage: ${DISK_PERCENT}%"
elif [ "$DISK_PERCENT" -lt 90 ]; then
    check_warn "Disk usage: ${DISK_PERCENT}% — monitor closely"
else
    check_fail "Disk usage: ${DISK_PERCENT}% — CRITICAL"
fi

LOG_DIR_SIZE=$(du -sh /opt/windi/logs/ 2>/dev/null | cut -f1 || echo "?")
check_info "Logs directory size: $LOG_DIR_SIZE"

# Check for large log files
if [ -d "/opt/windi/logs" ]; then
    LARGE_LOGS=$(find /opt/windi/logs -name "*.log" -size +50M 2>/dev/null | wc -l)
    if [ "$LARGE_LOGS" -gt 0 ]; then
        check_warn "$LARGE_LOGS log file(s) over 50MB — consider rotation"
        find /opt/windi/logs -name "*.log" -size +50M | while read f; do
            check_info "Large: $f ($(du -sh $f | cut -f1))"
        done
    else
        check_ok "No oversized log files"
    fi
fi

# ── 9. BACKUP STATUS ────────────────────────────────────────
print_header "9. BACKUP STATUS"
if [ -d "/opt/windi/backups" ]; then
    LAST_BACKUP=$(ls -t /opt/windi/backups/ | head -1)
    BACKUP_COUNT=$(ls /opt/windi/backups/ | wc -l)
    check_ok "Backup directory exists ($BACKUP_COUNT snapshots)"
    check_info "Most recent: $LAST_BACKUP"
else
    check_warn "No backup directory found"
fi

# ── SUMMARY ─────────────────────────────────────────────────
echo ""
echo -e "${BOLD}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║                 AUDIT SUMMARY                   ║${NC}"
echo -e "${BOLD}╠══════════════════════════════════════════════════╣${NC}"
echo -e "${BOLD}║  ${GREEN}✅ PASS: $PASS${NC}${BOLD}                                      ║${NC}"
echo -e "${BOLD}║  ${YELLOW}⚠️  WARN: $WARN${NC}${BOLD}                                      ║${NC}"
echo -e "${BOLD}║  ${RED}❌ FAIL: $FAIL${NC}${BOLD}                                      ║${NC}"
echo -e "${BOLD}╠══════════════════════════════════════════════════╣${NC}"

TOTAL=$((PASS + FAIL + WARN))
if [ $FAIL -eq 0 ] && [ $WARN -le 3 ]; then
    echo -e "${BOLD}║  ${GREEN}🐉 STATUS: PLATFORM READY FOR STRESS TEST${NC}${BOLD}    ║${NC}"
elif [ $FAIL -le 3 ]; then
    echo -e "${BOLD}║  ${YELLOW}⚠️  STATUS: MINOR ISSUES — FIX BEFORE STRESS${NC}${BOLD}  ║${NC}"
else
    echo -e "${BOLD}║  ${RED}🔴 STATUS: CRITICAL ISSUES — DO NOT STRESS TEST${NC}${BOLD} ║${NC}"
fi
echo -e "${BOLD}╚══════════════════════════════════════════════════╝${NC}"
echo ""
