#!/bin/bash
# W-VD-CUT-001 — Smoke Test
# Liga IA+H · Kempten, Bavaria · 2026

set -e

# Configuration
VD_CUT_URL="http://127.0.0.1:8128"
LEDGER_URL="http://127.0.0.1:8101"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "========================================"
echo "W-VD-CUT-001 Smoke Test"
echo "========================================"
echo ""

PASSED=0
FAILED=0

# Test function
test_endpoint() {
    local name="$1"
    local url="$2"
    local expected_status="${3:-200}"

    status=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")

    if [ "$status" = "$expected_status" ]; then
        echo -e "${GREEN}[PASS]${NC} $name (HTTP $status)"
        ((PASSED++))
    else
        echo -e "${RED}[FAIL]${NC} $name (Expected $expected_status, got $status)"
        ((FAILED++))
    fi
}

echo "1. Service Health Checks"
echo "------------------------"
test_endpoint "VD-CUT Health" "$VD_CUT_URL/vd-cut/health"
test_endpoint "Ledger Health" "$LEDGER_URL/health"

echo ""
echo "2. FFmpeg Check"
echo "---------------"
if command -v ffmpeg &> /dev/null; then
    echo -e "${GREEN}[PASS]${NC} FFmpeg installed"
    ((PASSED++))
    ffmpeg -version | head -1
else
    echo -e "${RED}[FAIL]${NC} FFmpeg not installed"
    ((FAILED++))
fi

if command -v ffprobe &> /dev/null; then
    echo -e "${GREEN}[PASS]${NC} FFprobe installed"
    ((PASSED++))
else
    echo -e "${RED}[FAIL]${NC} FFprobe not installed"
    ((FAILED++))
fi

echo ""
echo "3. Directory Structure"
echo "----------------------"
check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}[PASS]${NC} $1"
        ((PASSED++))
    else
        echo -e "${RED}[FAIL]${NC} $1 missing"
        ((FAILED++))
    fi
}

check_dir "/opt/windi/vd-cut"
check_dir "/opt/windi/media/vd-cut/incoming"
check_dir "/opt/windi/media/vd-cut/exports"
check_dir "/opt/windi/media/vd-cut/sealed"

echo ""
echo "4. Database"
echo "-----------"
if [ -f "/opt/windi/vd-cut/vd_cut.db" ]; then
    echo -e "${GREEN}[PASS]${NC} Database file exists"
    ((PASSED++))

    # Check tables
    tables=$(sqlite3 /opt/windi/vd-cut/vd_cut.db ".tables" 2>/dev/null)
    if echo "$tables" | grep -q "video_projects"; then
        echo -e "${GREEN}[PASS]${NC} video_projects table exists"
        ((PASSED++))
    else
        echo -e "${YELLOW}[WARN]${NC} Tables may not be initialized (will be created on first run)"
    fi
else
    echo -e "${YELLOW}[WARN]${NC} Database not yet created (will be created on first run)"
fi

echo ""
echo "5. NOMAD-BOT Integration"
echo "------------------------"
test_endpoint "NOMAD-BOT Health" "http://127.0.0.1:8127/webhook/" "405"

# Check if video handler exists
if [ -f "/opt/windi/nomad-bot/handlers/video.py" ]; then
    echo -e "${GREEN}[PASS]${NC} Video handler installed"
    ((PASSED++))
else
    echo -e "${RED}[FAIL]${NC} Video handler missing"
    ((FAILED++))
fi

echo ""
echo "========================================"
echo "Results: $PASSED passed, $FAILED failed"
echo "========================================"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed${NC}"
    exit 1
fi
