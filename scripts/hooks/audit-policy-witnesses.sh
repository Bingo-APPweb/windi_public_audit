#!/bin/bash
# =============================================================================
# WINDI Audit Script — Policy Witness Detection (Post-hoc)
# =============================================================================
# Twin of pre-commit hook. Runs same checks over committed history.
# Detects --no-verify bypasses that leave policy docs without witnesses.
#
# HOOK-AC3: Prevention (pre-commit) + Detection (this audit) = complete control
#
# Features:
#   - Hook installation check (the guard must be guarded)
#   - LEGACY vs NEW distinction (pre-hook vs post-hook violations)
#   - Burn-down metric (legacy count can only decrease)
#
# Usage:
#   ./audit-policy-witnesses.sh              # Full audit
#   ./audit-policy-witnesses.sh --check      # Check hook installation only
#   ./audit-policy-witnesses.sh --since=N    # Audit last N commits
#   ./audit-policy-witnesses.sh --burndown   # Show burn-down metric
#
# Reference: W-INCIDENTE-FRONTEIRA-002
# Born: 2026-08-06 · Kempten, Bavaria
# =============================================================================

# Colors
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
GRAY='\033[0;90m'
NC='\033[0m'

# Hook installation date — cutoff for LEGACY vs NEW
HOOK_INSTALLED_DATE="2026-08-06"

# Policy patterns (same as pre-commit hook)
POLICY_PATTERNS="POLICY|DOUTRINA|CANONICAL|spec"

# Runtime assertion patterns
RUNTIME_PATTERNS="é avisado|will be notified|wird benachrichtigt|podem expirar|can expire|können ablaufen|Art\. [0-9]+|GDPR|DSGVO|Consentimento|consent|Einwilligung|retenção|retention|Aufbewahrung"

# Witness patterns
WITNESS_PATTERNS="^## Testemunhas|AC-[A-Z][0-9]|\*\*Testemunha\*\*:|Testemunha:"

# =============================================================================
# Hook Installation Check — The guard must be guarded
# =============================================================================
check_hook_installation() {
    echo -e "${CYAN}Hook Installation Status${NC}"
    echo "========================="
    echo ""

    local all_ok=true

    # Check /home/windi
    echo -n "  /home/windi: "
    if [ -x "/home/windi/.git/hooks/pre-commit" ]; then
        local target
        target=$(readlink -f "/home/windi/.git/hooks/pre-commit" 2>/dev/null || echo "direct")
        if [ -f "$target" ] && [ -x "$target" ]; then
            echo -e "${GREEN}✓ Installed${NC} ($target)"
        else
            echo -e "${RED}✗ Broken symlink${NC} → $target"
            all_ok=false
        fi
    else
        echo -e "${RED}✗ Not installed or not executable${NC}"
        all_ok=false
    fi

    # Check /opt/windi
    echo -n "  /opt/windi:  "
    if [ -x "/opt/windi/.git/hooks/pre-commit" ]; then
        local target
        target=$(readlink -f "/opt/windi/.git/hooks/pre-commit" 2>/dev/null || echo "direct")
        if [ -f "$target" ] && [ -x "$target" ]; then
            echo -e "${GREEN}✓ Installed${NC} ($target)"
        else
            echo -e "${RED}✗ Broken symlink${NC} → $target"
            all_ok=false
        fi
    else
        echo -e "${RED}✗ Not installed or not executable${NC}"
        all_ok=false
    fi

    echo ""

    if [ "$all_ok" = true ]; then
        echo -e "${GREEN}All hooks properly installed.${NC}"
        return 0
    else
        echo -e "${RED}Hook installation incomplete — enforcement may be inactive!${NC}"
        echo ""
        echo "To install:"
        echo "  ln -sf ../../scripts/hooks/pre-commit /home/windi/.git/hooks/pre-commit"
        echo "  ln -sf ../../scripts/hooks/pre-commit /opt/windi/.git/hooks/pre-commit"
        return 1
    fi
}

# =============================================================================
# Audit a single file
# =============================================================================
audit_file() {
    local file="$1"
    local content

    if [ ! -f "$file" ]; then
        return 0
    fi

    content=$(cat "$file")

    # Check if file has runtime assertions
    if ! echo "$content" | grep -qiE "$RUNTIME_PATTERNS"; then
        return 0  # No runtime assertions, skip
    fi

    # Check for witnesses
    if echo "$content" | grep -qE "$WITNESS_PATTERNS"; then
        return 0  # Has witnesses, pass
    fi

    # Runtime assertions without witnesses
    return 1
}

# =============================================================================
# Get file's last modification date in git
# =============================================================================
get_file_last_modified() {
    local file="$1"
    git log -1 --format="%ci" -- "$file" 2>/dev/null | cut -d' ' -f1
}

# =============================================================================
# Main audit with LEGACY vs NEW distinction
# =============================================================================
audit_current() {
    echo -e "${CYAN}WINDI Policy Witness Audit${NC}"
    echo "==========================="
    echo -e "${GRAY}Cutoff date: $HOOK_INSTALLED_DATE (LEGACY before, NEW after)${NC}"
    echo ""

    local legacy_count=0
    local new_count=0
    local checked=0

    # Find policy files
    local policy_files
    policy_files=$(find . -name "*.md" -type f 2>/dev/null | grep -iE "$POLICY_PATTERNS" | grep -v ".git" || true)

    if [ -z "$policy_files" ]; then
        echo "No policy files found matching patterns."
        return 0
    fi

    local legacy_files=()
    local new_files=()

    for file in $policy_files; do
        ((checked++))
        if ! audit_file "$file"; then
            # Determine if LEGACY or NEW
            local last_modified
            last_modified=$(get_file_last_modified "$file")

            if [[ "$last_modified" < "$HOOK_INSTALLED_DATE" ]] || [[ "$last_modified" == "$HOOK_INSTALLED_DATE" ]]; then
                legacy_files+=("$file")
                ((legacy_count++))
            else
                new_files+=("$file")
                ((new_count++))
            fi
        fi
    done

    # Report NEW violations (real problems — RED)
    if [ "$new_count" -gt 0 ]; then
        echo -e "${RED}NEW VIOLATIONS (post-hook — real problems):${NC}"
        for f in "${new_files[@]}"; do
            echo -e "  ${RED}✗${NC} $f"
        done
        echo ""
    fi

    # Report LEGACY violations (pre-hook — YELLOW, informational)
    if [ "$legacy_count" -gt 0 ]; then
        echo -e "${YELLOW}LEGACY (pre-hook, will fix on next touch):${NC}"
        for f in "${legacy_files[@]}"; do
            echo -e "  ${YELLOW}○${NC} $f"
        done
        echo ""
    fi

    # Summary
    echo "==========================="
    echo "Checked: $checked files"
    echo ""

    if [ "$new_count" -gt 0 ]; then
        echo -e "${RED}NEW violations: $new_count${NC} ← These need immediate attention"
    else
        echo -e "${GREEN}NEW violations: 0${NC} ← No post-hook bypasses detected"
    fi

    if [ "$legacy_count" -gt 0 ]; then
        echo -e "${YELLOW}LEGACY (burn-down): $legacy_count${NC} ← Will resolve on next file touch"
    fi

    echo ""

    # Return code: only fail on NEW violations
    if [ "$new_count" -gt 0 ]; then
        echo -e "${RED}Action required: NEW violations represent --no-verify bypasses.${NC}"
        return 1
    else
        if [ "$legacy_count" -gt 0 ]; then
            echo -e "${GREEN}No action required — legacy items resolve automatically via ratchet.${NC}"
        else
            echo -e "${GREEN}All policy files have proper witness documentation.${NC}"
        fi
        return 0
    fi
}

# =============================================================================
# Burn-down metric
# =============================================================================
show_burndown() {
    echo -e "${CYAN}WINDI Policy Witness Burn-Down${NC}"
    echo "==============================="
    echo ""

    local legacy_count=0

    # Find policy files
    local policy_files
    policy_files=$(find . -name "*.md" -type f 2>/dev/null | grep -iE "$POLICY_PATTERNS" | grep -v ".git" || true)

    for file in $policy_files; do
        if ! audit_file "$file"; then
            local last_modified
            last_modified=$(get_file_last_modified "$file")

            if [[ "$last_modified" < "$HOOK_INSTALLED_DATE" ]] || [[ "$last_modified" == "$HOOK_INSTALLED_DATE" ]]; then
                ((legacy_count++))
            fi
        fi
    done

    echo "Legacy files without witnesses: $legacy_count"
    echo ""
    echo "Hook installed: $HOOK_INSTALLED_DATE"
    echo "Ratchet policy: Legacy files gain witnesses when touched"
    echo ""

    if [ "$legacy_count" -eq 0 ]; then
        echo -e "${GREEN}Burn-down complete! All policy files have witnesses.${NC}"
    else
        echo "Burn-down progress:"
        echo "  Initial (2026-08-06): 8"
        echo "  Current:              $legacy_count"
        echo ""
        if [ "$legacy_count" -lt 8 ]; then
            local burned=$((8 - legacy_count))
            echo -e "${GREEN}Progress: $burned files resolved${NC}"
        fi
    fi
}

# =============================================================================
# Entry point
# =============================================================================
case "${1:-}" in
    --check)
        check_hook_installation
        ;;
    --since=*)
        count="${1#--since=}"
        # Audit commits (simplified version)
        echo -e "${CYAN}WINDI Policy Witness Audit — Last $count Commits${NC}"
        echo "Not yet implemented with LEGACY/NEW distinction."
        echo "Use default audit for current state."
        ;;
    --burndown)
        show_burndown
        ;;
    --help)
        echo "WINDI Policy Witness Audit"
        echo ""
        echo "Usage:"
        echo "  $0              Full audit (LEGACY vs NEW)"
        echo "  $0 --check      Check hook installation only"
        echo "  $0 --burndown   Show burn-down metric"
        echo "  $0 --help       Show this help"
        echo ""
        echo "LEGACY = pre-hook ($HOOK_INSTALLED_DATE), fixes on next touch"
        echo "NEW = post-hook violation, requires immediate attention"
        echo ""
        echo "This is the detection twin of the pre-commit hook."
        echo "Prevention (hook) + Detection (audit) = complete control."
        ;;
    *)
        check_hook_installation
        echo ""
        audit_current
        ;;
esac
