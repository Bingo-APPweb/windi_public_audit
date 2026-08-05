#!/bin/bash
# =============================================================================
# WINDI Audit Script — Policy Witness Detection (Post-hoc)
# =============================================================================
# Twin of pre-commit hook. Runs same checks over committed history.
# Detects --no-verify bypasses that leave policy docs without witnesses.
#
# HOOK-AC3: Prevention (pre-commit) + Detection (this audit) = complete control
#
# Usage:
#   ./audit-policy-witnesses.sh              # Audit current HEAD
#   ./audit-policy-witnesses.sh --all        # Audit all policy files
#   ./audit-policy-witnesses.sh --since=N    # Audit last N commits
#
# Reference: W-INCIDENTE-FRONTEIRA-002
# Born: 2026-08-06 · Kempten, Bavaria
# =============================================================================

# Colors
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

# Policy patterns (same as pre-commit hook)
POLICY_PATTERNS="POLICY|DOUTRINA|CANONICAL|spec"

# Runtime assertion patterns
RUNTIME_PATTERNS="é avisado|will be notified|wird benachrichtigt|podem expirar|can expire|können ablaufen|Art\. [0-9]+|GDPR|DSGVO|Consentimento|consent|Einwilligung|retenção|retention|Aufbewahrung"

# Witness patterns
WITNESS_PATTERNS="^## Testemunhas|AC-[A-Z][0-9]|\*\*Testemunha\*\*:|Testemunha:"

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

audit_current() {
    echo -e "${CYAN}WINDI Policy Witness Audit — Current HEAD${NC}"
    echo "==========================================="
    echo ""

    local issues=0
    local checked=0

    # Find policy files
    local policy_files
    policy_files=$(find . -name "*.md" -type f 2>/dev/null | grep -iE "$POLICY_PATTERNS" | grep -v ".git" || true)

    if [ -z "$policy_files" ]; then
        echo "No policy files found matching patterns."
        return 0
    fi

    for file in $policy_files; do
        ((checked++))
        if ! audit_file "$file"; then
            echo -e "${RED}✗ MISSING WITNESSES:${NC} $file"
            ((issues++))
        fi
    done

    echo ""
    echo "==========================================="
    echo "Checked: $checked files"

    if [ "$issues" -gt 0 ]; then
        echo -e "${RED}Issues: $issues files with runtime assertions but no witnesses${NC}"
        echo ""
        echo "These files may have bypassed the pre-commit hook (--no-verify)"
        echo "or were committed before the hook was installed."
        return 1
    else
        echo -e "${GREEN}All policy files have proper witness documentation.${NC}"
        return 0
    fi
}

audit_commits() {
    local count="${1:-10}"

    echo -e "${CYAN}WINDI Policy Witness Audit — Last $count Commits${NC}"
    echo "=================================================="
    echo ""

    local issues=0

    # Get commits that touched policy files
    local commits
    commits=$(git log --oneline -n "$count" --all -- "*POLICY*" "*DOUTRINA*" "*CANONICAL*" "*spec*" 2>/dev/null || echo "")

    if [ -z "$commits" ]; then
        echo "No recent commits touching policy files."
        return 0
    fi

    echo "Commits touching policy files:"
    echo "$commits"
    echo ""

    # For each commit, check if policy files have witnesses
    while IFS= read -r line; do
        local hash
        hash=$(echo "$line" | cut -d' ' -f1)

        if [ -z "$hash" ]; then
            continue
        fi

        # Get policy files in this commit
        local files
        files=$(git diff-tree --no-commit-id --name-only -r "$hash" 2>/dev/null | grep -iE "$POLICY_PATTERNS" || true)

        for file in $files; do
            # Get content at that commit
            local content
            content=$(git show "$hash:$file" 2>/dev/null || echo "")

            if [ -z "$content" ]; then
                continue
            fi

            # Check for runtime assertions
            if ! echo "$content" | grep -qiE "$RUNTIME_PATTERNS"; then
                continue
            fi

            # Check for witnesses
            if ! echo "$content" | grep -qE "$WITNESS_PATTERNS"; then
                echo -e "${YELLOW}Commit $hash:${NC} $file — ${RED}no witnesses${NC}"
                ((issues++))
            fi
        done
    done <<< "$commits"

    echo ""
    echo "=================================================="

    if [ "$issues" -gt 0 ]; then
        echo -e "${RED}Found $issues policy additions without witnesses in history.${NC}"
        echo "These represent --no-verify bypasses or pre-hook commits."
        return 1
    else
        echo -e "${GREEN}All audited commits have proper witness documentation.${NC}"
        return 0
    fi
}

# Entry point
case "${1:-}" in
    --all)
        audit_current
        ;;
    --since=*)
        count="${1#--since=}"
        audit_commits "$count"
        ;;
    --help)
        echo "WINDI Policy Witness Audit"
        echo ""
        echo "Usage:"
        echo "  $0              Audit current HEAD"
        echo "  $0 --all        Audit all policy files"
        echo "  $0 --since=N    Audit last N commits"
        echo "  $0 --help       Show this help"
        echo ""
        echo "This is the detection twin of the pre-commit hook."
        echo "Prevention (hook) + Detection (audit) = complete control."
        ;;
    *)
        audit_current
        ;;
esac
