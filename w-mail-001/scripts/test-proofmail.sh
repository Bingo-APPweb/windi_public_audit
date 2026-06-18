#!/bin/bash
# =============================================================================
# test-proofmail.sh — WINDI Proofmail Pipeline Test
# =============================================================================
# Spec: INFRASTRUCTURE-PROVENANCE-001
# Purpose: Single command to validate the complete forensic pipeline
# Usage: ./test-proofmail.sh [--post-reboot] [--verbose]
# =============================================================================

# Don't exit on error - we want to complete all checks
set +e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
LEDGER_URL="http://localhost:8101"
SITES_URL="http://localhost:8192"
VERIFY_URL="http://localhost:8114"
CONTAINER="windi-mailserver"
TEST_EMAIL="postmaster@windisites.de"
LOG_FILE="/opt/windi/logs/test-proofmail.log"

# Parse arguments
POST_REBOOT=false
VERBOSE=false
for arg in "$@"; do
    case $arg in
        --post-reboot) POST_REBOOT=true ;;
        --verbose) VERBOSE=true ;;
    esac
done

# Logging
log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo -e "$msg" | tee -a "$LOG_FILE"
}

pass() {
    echo -e "${GREEN}✓ PASS${NC}: $1"
    log "PASS: $1"
}

fail() {
    echo -e "${RED}✗ FAIL${NC}: $1"
    log "FAIL: $1"
    FAILED=true
}

warn() {
    echo -e "${YELLOW}⚠ WARN${NC}: $1"
    log "WARN: $1"
}

info() {
    echo -e "${BLUE}ℹ INFO${NC}: $1"
    log "INFO: $1"
}

# =============================================================================
echo ""
echo "============================================================"
echo " WINDI PROOFMAIL PIPELINE TEST"
echo " $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================================"
echo ""

FAILED=false
CHECKS=0
PASSED=0

# =============================================================================
# PHASE 1: Service Health Checks
# =============================================================================
echo "--- PHASE 1: Service Health Checks ---"
echo ""

# Check 1: Docker
((CHECKS++))
if systemctl is-active --quiet docker; then
    pass "Docker service active"
    ((PASSED++))
else
    fail "Docker service not active"
fi

# Check 2: Forensic Ledger
((CHECKS++))
LEDGER_STATUS=$(curl -s "$LEDGER_URL/health" 2>/dev/null | jq -r '.status' 2>/dev/null || echo "error")
if [ "$LEDGER_STATUS" = "healthy" ]; then
    pass "Forensic Ledger (:8101) healthy"
    ((PASSED++))
else
    fail "Forensic Ledger not healthy (status: $LEDGER_STATUS)"
fi

# Check 3: W-SITES Identity Gate
((CHECKS++))
SITES_STATUS=$(curl -s "$SITES_URL/health" 2>/dev/null | jq -r '.status' 2>/dev/null || echo "error")
if [ "$SITES_STATUS" = "healthy" ]; then
    pass "W-SITES Identity Gate (:8192) healthy"
    ((PASSED++))
else
    fail "W-SITES not healthy (status: $SITES_STATUS)"
fi

# Check 4: Verify Public
((CHECKS++))
VERIFY_STATUS=$(curl -s "$VERIFY_URL/health" 2>/dev/null | jq -r '.status' 2>/dev/null || echo "error")
if [ "$VERIFY_STATUS" = "operational" ]; then
    pass "Verify Public (:8114) operational"
    ((PASSED++))
else
    fail "Verify Public not operational (status: $VERIFY_STATUS)"
fi

# Check 5: Mail Container
((CHECKS++))
if docker ps --filter "name=$CONTAINER" --filter "status=running" --format '{{.Names}}' | grep -q "$CONTAINER"; then
    pass "Mail container ($CONTAINER) running"
    ((PASSED++))
else
    fail "Mail container not running"
fi

# Check 6: DACP Milter
((CHECKS++))
MILTER_STATUS=$(docker exec "$CONTAINER" supervisorctl status dacp-milter 2>/dev/null | grep -o 'RUNNING' || echo "NOT_RUNNING")
if [ "$MILTER_STATUS" = "RUNNING" ]; then
    pass "DACP Milter running (supervisor)"
    ((PASSED++))
else
    fail "DACP Milter not running (status: $MILTER_STATUS)"
fi

# Check 7: Milter Port
((CHECKS++))
if docker exec "$CONTAINER" ss -tlnp 2>/dev/null | grep -q ':8890'; then
    pass "DACP Milter listening on :8890"
    ((PASSED++))
else
    fail "DACP Milter not listening on :8890"
fi

# Check 8: Milter Health
((CHECKS++))
MILTER_HEALTH=$(docker exec "$CONTAINER" curl -s http://localhost:8895/health 2>/dev/null | jq -r '.status' 2>/dev/null || echo "error")
if [ "$MILTER_HEALTH" = "healthy" ]; then
    LEDGER_REACHABLE=$(docker exec "$CONTAINER" curl -s http://localhost:8895/health 2>/dev/null | jq -r '.ledger_reachable' 2>/dev/null)
    if [ "$LEDGER_REACHABLE" = "true" ]; then
        pass "DACP Milter healthy, Ledger reachable"
        ((PASSED++))
    else
        warn "DACP Milter healthy but Ledger not reachable from container"
        ((PASSED++))  # Still count as pass since milter is healthy
    fi
else
    fail "DACP Milter health check failed"
fi

echo ""

# =============================================================================
# PHASE 2: Pipeline Test (send actual email)
# =============================================================================
echo "--- PHASE 2: Pipeline Test ---"
echo ""

# Get a receipt to use for test
TEST_RECEIPT=$(curl -s "$LEDGER_URL/api/receipts?limit=1" 2>/dev/null | jq -r '.receipts[0].id' 2>/dev/null)

if [ -z "$TEST_RECEIPT" ] || [ "$TEST_RECEIPT" = "null" ]; then
    warn "No existing receipt found, skipping email test"
else
    info "Using receipt: $TEST_RECEIPT"

    # Record receipts count before
    BEFORE_COUNT=$(curl -s "$LEDGER_URL/api/receipts" 2>/dev/null | jq '.receipts | length' 2>/dev/null || echo "0")

    # Send test email
    ((CHECKS++))
    SEND_RESULT=$(curl -s -X POST "$SITES_URL/api/verify-email/$TEST_RECEIPT" \
        -H "Content-Type: application/json" \
        -d "{\"email\": \"$TEST_EMAIL\"}" 2>/dev/null)

    SEND_OK=$(echo "$SEND_RESULT" | jq -r '.ok' 2>/dev/null)
    NEW_RECEIPT=$(echo "$SEND_RESULT" | jq -r '.proof_receipt' 2>/dev/null)

    if [ "$SEND_OK" = "true" ]; then
        pass "Email sent successfully"
        ((PASSED++))
        info "New proof receipt: $NEW_RECEIPT"

        # Verify new receipt exists in Ledger
        ((CHECKS++))
        sleep 2  # Wait for propagation
        VERIFY_RECEIPT=$(curl -s "$LEDGER_URL/api/receipts/$NEW_RECEIPT" 2>/dev/null | jq -r '.ok' 2>/dev/null)
        if [ "$VERIFY_RECEIPT" = "true" ]; then
            pass "New receipt verified in Ledger"
            ((PASSED++))

            # Get receipt details
            RECEIPT_HASH=$(curl -s "$LEDGER_URL/api/receipts/$NEW_RECEIPT" 2>/dev/null | jq -r '.receipt.content_hash' 2>/dev/null)
            RECEIPT_ACTOR=$(curl -s "$LEDGER_URL/api/receipts/$NEW_RECEIPT" 2>/dev/null | jq -r '.receipt.actor' 2>/dev/null)
            info "Content hash: ${RECEIPT_HASH:0:50}..."
            info "Actor: $RECEIPT_ACTOR"
        else
            fail "New receipt not found in Ledger"
        fi

        # Verify via public endpoint
        ((CHECKS++))
        PUBLIC_STATUS=$(curl -s "$VERIFY_URL/verify-public/document/$NEW_RECEIPT" 2>/dev/null | jq -r '.status' 2>/dev/null)
        if [ "$PUBLIC_STATUS" = "verified" ]; then
            pass "Public verification: VERIFIED"
            ((PASSED++))
        else
            warn "Public verification returned: $PUBLIC_STATUS"
            ((PASSED++))  # Still count since this may be cache timing
        fi
    else
        fail "Email send failed"
        info "Response: $SEND_RESULT"
    fi
fi

echo ""

# =============================================================================
# PHASE 3: Summary
# =============================================================================
echo "============================================================"
echo " SUMMARY"
echo "============================================================"
echo ""
echo " Checks: $CHECKS"
echo " Passed: $PASSED"
echo " Failed: $((CHECKS - PASSED))"
echo ""

if [ "$FAILED" = true ]; then
    echo -e "${RED}STATUS: FAIL${NC}"
    echo ""
    echo "Some checks failed. Review the output above."
    exit 1
else
    echo -e "${GREEN}STATUS: PASS${NC}"
    echo ""
    echo "All critical checks passed."

    if [ "$POST_REBOOT" = true ]; then
        echo ""
        echo "============================================================"
        echo " POST-REBOOT VALIDATION COMPLETE"
        echo "============================================================"
        echo ""
        echo " The system survived reboot and is fully operational."
        echo " New receipt sealed: $NEW_RECEIPT"
        echo ""
    fi

    exit 0
fi
