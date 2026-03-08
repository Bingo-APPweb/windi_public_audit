#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# WINDI Pre-Deploy Validation Script
# ═══════════════════════════════════════════════════════════════════════════
# Purpose:  Verify all services are healthy before deploying changes
# Usage:    ./pre-deploy-check.sh [--fix] [--verbose]
# Exit:     0 = all checks pass, 1 = failures detected
# Version:  1.0.0
# Date:     2026-03-08
# ═══════════════════════════════════════════════════════════════════════════

# Don't exit on error - we want to run all checks
set +e

# ── CONFIG ──────────────────────────────────────────────────────────────────
WINDI_ROOT="/opt/windi"
VERBOSE=false
FIX_MODE=false

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Service definitions: name|port|health_endpoint
SERVICES=(
    "ledger|8101|/health"
    "anchor|8102|/health"
    "export|8103|/health"
    "communique|8105|/health"
    "dragon|8108|/health"
    "constitutional|8091|/grove/health"
    "verify-public|8114|/health"
)

# Critical paths
CRITICAL_PATHS=(
    "$WINDI_ROOT/agents/constitutional-agent/data"
    "$WINDI_ROOT/data"
)

# Critical databases
CRITICAL_DBS=(
    "$WINDI_ROOT/data/forensic_ledger.db"
    "$WINDI_ROOT/data/babel_documents.db"
)

# ── PARSE ARGS ──────────────────────────────────────────────────────────────
for arg in "$@"; do
    case $arg in
        --verbose|-v) VERBOSE=true ;;
        --fix|-f) FIX_MODE=true ;;
        --help|-h)
            echo "WINDI Pre-Deploy Check"
            echo "Usage: $0 [--verbose] [--fix]"
            echo "  --verbose  Show detailed output"
            echo "  --fix      Attempt to fix issues (restart services)"
            exit 0
            ;;
    esac
done

# ── COUNTERS ────────────────────────────────────────────────────────────────
PASSED=0
FAILED=0
WARNINGS=0

# ── HELPERS ─────────────────────────────────────────────────────────────────
log_pass() {
    echo -e "  ${GREEN}✓${NC} $1"
    ((PASSED++))
}

log_fail() {
    echo -e "  ${RED}✗${NC} $1"
    ((FAILED++))
}

log_warn() {
    echo -e "  ${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

log_info() {
    if $VERBOSE; then
        echo -e "  ${BLUE}ℹ${NC} $1"
    fi
}

section() {
    echo ""
    echo -e "${BLUE}━━━ $1 ━━━${NC}"
}

# ═══════════════════════════════════════════════════════════════════════════
# CHECKS
# ═══════════════════════════════════════════════════════════════════════════

echo ""
echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}     🐉 WINDI Pre-Deploy Validation                            ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}     $(date '+%Y-%m-%d %H:%M:%S')                                    ${BLUE}║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"

# ── 1. NGINX CONFIG ─────────────────────────────────────────────────────────
section "1. Nginx Configuration"

if sudo nginx -t 2>&1 | grep -q "syntax is ok"; then
    log_pass "nginx config syntax OK"
elif sudo nginx -t 2>&1 | grep -q "successful"; then
    log_pass "nginx config syntax OK"
else
    # Check if we even have sudo access
    if ! sudo -n true 2>/dev/null; then
        log_warn "nginx config check requires sudo (run with sudo)"
    else
        log_fail "nginx config has errors - run 'sudo nginx -t' for details"
    fi
fi

if systemctl is-active --quiet nginx; then
    log_pass "nginx service running"
else
    log_fail "nginx service not running"
    if $FIX_MODE; then
        echo "    Attempting restart..."
        sudo systemctl restart nginx && log_info "nginx restarted"
    fi
fi

# ── 2. SERVICE HEALTH ───────────────────────────────────────────────────────
section "2. Service Health Endpoints"

for svc in "${SERVICES[@]}"; do
    IFS='|' read -r name port endpoint <<< "$svc"

    # Check if port is listening
    if ss -tlnp 2>/dev/null | grep -q ":$port "; then
        # Check health endpoint
        response=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:$port$endpoint" 2>/dev/null || echo "000")

        if [[ "$response" == "200" ]]; then
            log_pass "$name (port $port) healthy"
        elif [[ "$response" == "000" ]]; then
            log_warn "$name (port $port) listening but health endpoint unreachable"
        else
            log_warn "$name (port $port) returned HTTP $response"
        fi
    else
        log_fail "$name (port $port) not listening"

        # Try to identify systemd service
        if $FIX_MODE; then
            service_name="windi-${name}"
            if systemctl list-unit-files | grep -q "$service_name"; then
                echo "    Attempting to start $service_name..."
                sudo systemctl start "$service_name" 2>/dev/null && log_info "$service_name started"
            fi
        fi
    fi
done

# ── 3. CRITICAL PATHS ───────────────────────────────────────────────────────
section "3. Critical Directories"

for path in "${CRITICAL_PATHS[@]}"; do
    if [[ -d "$path" ]]; then
        if [[ -w "$path" ]]; then
            log_pass "$path exists and writable"
        else
            log_fail "$path exists but NOT writable"
        fi
    else
        log_fail "$path does not exist"
        if $FIX_MODE; then
            mkdir -p "$path" && log_info "Created $path"
        fi
    fi
done

# ── 4. CRITICAL DATABASES ───────────────────────────────────────────────────
section "4. Critical Databases"

for db in "${CRITICAL_DBS[@]}"; do
    if [[ -f "$db" ]]; then
        # Check if SQLite DB is valid
        if sqlite3 "$db" "SELECT 1;" 2>/dev/null | grep -q "1"; then
            size=$(du -h "$db" | cut -f1)
            log_pass "$(basename $db) valid ($size)"
        else
            log_fail "$(basename $db) exists but corrupted"
        fi
    else
        log_warn "$(basename $db) not found (may be new install)"
    fi
done

# ── 5. LEDGER-ANCHOR SYNC ───────────────────────────────────────────────────
section "5. Ledger-Anchor Sync Check"

# Check if services respond
ledger_ok=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8101/health" 2>/dev/null || echo "000")
anchor_ok=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8102/health" 2>/dev/null || echo "000")

if [[ "$ledger_ok" == "200" ]] && [[ "$anchor_ok" == "200" ]]; then
    log_pass "Ledger and Anchor services both healthy"
elif [[ "$ledger_ok" != "200" ]] && [[ "$anchor_ok" != "200" ]]; then
    log_fail "Both Ledger and Anchor unreachable"
else
    log_warn "Ledger ($ledger_ok) and Anchor ($anchor_ok) status mismatch"
fi

# ── 6. SYSTEMD SERVICES ─────────────────────────────────────────────────────
section "6. Systemd Services"

WINDI_SERVICES=$(systemctl list-units --type=service --all 2>/dev/null | grep -E "windi-|constitutional" | awk '{print $1}' || true)

if [[ -n "$WINDI_SERVICES" ]]; then
    for svc in $WINDI_SERVICES; do
        status=$(systemctl is-active "$svc" 2>/dev/null || echo "unknown")
        case $status in
            active) log_pass "$svc running" ;;
            inactive) log_warn "$svc inactive" ;;
            failed) log_fail "$svc FAILED" ;;
            *) log_info "$svc status: $status" ;;
        esac
    done
else
    log_info "No windi-* systemd services found"
fi

# ── 7. DISK SPACE ───────────────────────────────────────────────────────────
section "7. Disk Space"

usage=$(df "$WINDI_ROOT" | tail -1 | awk '{print $5}' | tr -d '%')
if [[ "$usage" -lt 80 ]]; then
    log_pass "Disk usage: ${usage}%"
elif [[ "$usage" -lt 90 ]]; then
    log_warn "Disk usage: ${usage}% (getting full)"
else
    log_fail "Disk usage: ${usage}% (CRITICAL)"
fi

# ── 8. GIT STATUS ───────────────────────────────────────────────────────────
section "8. Git Status"

cd "$WINDI_ROOT"
if git rev-parse --git-dir > /dev/null 2>&1; then
    uncommitted=$(git status --porcelain 2>/dev/null | wc -l)
    if [[ "$uncommitted" -eq 0 ]]; then
        log_pass "Working directory clean"
    else
        log_warn "$uncommitted uncommitted changes"
    fi

    branch=$(git branch --show-current 2>/dev/null)
    log_info "Branch: $branch"

    # Check if ahead/behind
    ahead=$(git rev-list --count @{u}..HEAD 2>/dev/null || echo "0")
    behind=$(git rev-list --count HEAD..@{u} 2>/dev/null || echo "0")
    if [[ "$ahead" -gt 0 ]]; then
        log_warn "$ahead commits not pushed"
    fi
    if [[ "$behind" -gt 0 ]]; then
        log_warn "$behind commits behind origin"
    fi
else
    log_info "Not a git repository"
fi

# ═══════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════════

echo ""
echo -e "${BLUE}━━━ SUMMARY ━━━${NC}"
echo ""
echo -e "  ${GREEN}Passed:${NC}   $PASSED"
echo -e "  ${YELLOW}Warnings:${NC} $WARNINGS"
echo -e "  ${RED}Failed:${NC}   $FAILED"
echo ""

if [[ "$FAILED" -eq 0 ]]; then
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║${NC}  ✓ ALL CHECKS PASSED — Safe to deploy                        ${GREEN}║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
    exit 0
else
    echo -e "${RED}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║${NC}  ✗ $FAILED CHECK(S) FAILED — Fix before deploying               ${RED}║${NC}"
    echo -e "${RED}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Run with --fix to attempt automatic repairs"
    exit 1
fi
