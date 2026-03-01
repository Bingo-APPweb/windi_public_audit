#!/bin/bash
# WINDI One Tree — Hardcoded Domain Hunt

AMBER='\033[0;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "\n${AMBER}═══ HARDCODED DOMAIN HUNT ═══${NC}\n"

SCAN_DIRS=(
    /opt/windi/agent-palette
    /opt/windi/a4desk-landing
    /opt/windi/desktop
    /opt/windi/clone
    /opt/windi/landing-pmg
    /opt/windi/bridge
    /opt/windi/engine
    /opt/windi/forensic-vault
    /opt/windi/forensic-ledger
    /opt/windi/export-engine
    /opt/windi/windi-communique-v1.0.0
    /opt/windi/sentinel
    /opt/windi/sentinel-law
    /opt/windi/masterarbeit
    /opt/windi/SDK_v1.1_RFC003
    /opt/windi/war-room
)

TOTAL=0

for DOMAIN in "admin.windia4desk.tech" "master.windia4desk.tech"; do
    echo -e "${AMBER}── Searching: ${DOMAIN} ──${NC}\n"
    COUNT=0
    for DIR in "${SCAN_DIRS[@]}"; do
        if [ -d "$DIR" ]; then
            RESULTS=$(grep -rn "$DOMAIN" "$DIR" \
                --include="*.html" \
                --include="*.js" \
                --include="*.jsx" \
                --include="*.py" \
                --include="*.json" \
                --include="*.css" \
                --include="*.env" \
                --include="*.conf" \
                2>/dev/null | grep -v node_modules | grep -v ".git" | grep -v __pycache__ | grep -v ".pyc" || true)
            if [ -n "$RESULTS" ]; then
                echo "$RESULTS"
                FOUND=$(echo "$RESULTS" | wc -l)
                COUNT=$((COUNT + FOUND))
            fi
        fi
    done
    if [ $COUNT -eq 0 ]; then
        echo -e "  ${GREEN}✅ Zero references${NC}\n"
    else
        echo -e "\n  ${RED}❌ ${COUNT} references found${NC}\n"
    fi
    TOTAL=$((TOTAL + COUNT))
done

echo -e "${AMBER}═══ SUMMARY ═══${NC}"
if [ $TOTAL -eq 0 ]; then
    echo -e "${GREEN}✅ Zero hardcoded old domain references — clean!${NC}"
else
    echo -e "${RED}❌ ${TOTAL} total references — must replace with relative paths${NC}"
    echo ""
    echo "Replacement rules:"
    echo "  https://admin.windia4desk.tech/...  →  /..."
    echo "  https://master.windia4desk.tech/... →  /..."
    echo "  fetch('https://admin...')  →  fetch('/api/...')"
fi
echo ""
