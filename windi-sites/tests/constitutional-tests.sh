#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# W-SITES-001 Constitutional Test Suite
# §11 Invariants: I1 · I9 · I11 · I12 · I14
# PRODUCT-SITES-001 Compliance
# ═══════════════════════════════════════════════════════════════

SITES_GATE="http://127.0.0.1:8192"
SITES_FACTORY="http://127.0.0.1:8091/sites/factory"
PASSED=0
FAILED=0

echo "═══════════════════════════════════════════════════════════════"
echo "W-SITES-001 Constitutional Test Suite"
echo "Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Helper function
test_result() {
    local name="$1"
    local invariant="$2"
    local expected="$3"
    local actual="$4"

    if [[ "$actual" == *"$expected"* ]]; then
        echo "✅ PASS: $name [$invariant]"
        ((PASSED++))
    else
        echo "❌ FAIL: $name [$invariant]"
        echo "   Expected: $expected"
        echo "   Actual: $actual"
        ((FAILED++))
    fi
}

# ═══════════════════════════════════════════════════════════════
# TEST 1: I14 — Explicit Failure (missing client_did)
# ═══════════════════════════════════════════════════════════════
echo "[1/9] I14: Create without client_did should fail explicitly"
RESULT=$(curl -s -X POST "$SITES_FACTORY/create" \
    -H "Content-Type: application/json" \
    -d '{"site_name": "Test Site"}' 2>/dev/null)
test_result "Create without client_did" "I14" "client_did required" "$RESULT"

# ═══════════════════════════════════════════════════════════════
# TEST 2: I14 — Explicit Failure (missing site_name)
# ═══════════════════════════════════════════════════════════════
echo "[2/9] I14: Create without site_name should fail explicitly"
RESULT=$(curl -s -X POST "$SITES_FACTORY/create" \
    -H "Content-Type: application/json" \
    -d '{"client_did": "did:windi:test-001"}' 2>/dev/null)
test_result "Create without site_name" "I14" "site_name required" "$RESULT"

# ═══════════════════════════════════════════════════════════════
# TEST 3: I1 — Sovereignty (valid creation with DID)
# ═══════════════════════════════════════════════════════════════
echo "[3/9] I1: Create site with valid DID (client sovereignty)"
RESULT=$(curl -s -X POST "$SITES_FACTORY/create" \
    -H "Content-Type: application/json" \
    -d '{"client_did": "did:windi:test-001", "site_name": "Constitutional Test Site"}' 2>/dev/null)
SITE_ID=$(echo "$RESULT" | grep -o '"site_id":"[^"]*"' | cut -d'"' -f4)
test_result "Create with valid DID" "I1" "ok" "$RESULT"
echo "   Site ID: $SITE_ID"

# ═══════════════════════════════════════════════════════════════
# TEST 4: I9 — Approval Gate (attempt seal without approval)
# ═══════════════════════════════════════════════════════════════
echo "[4/9] I9: Seal without approval should be blocked"
# First update to C2
curl -s -X POST "$SITES_FACTORY/update" \
    -H "Content-Type: application/json" \
    -d "{\"site_id\": \"$SITE_ID\", \"design_brief\": {\"title\": \"Test\"}}" >/dev/null 2>&1
# Then render to C3
curl -s -X POST "$SITES_FACTORY/render" \
    -H "Content-Type: application/json" \
    -d "{\"site_id\": \"$SITE_ID\", \"pages\": [{\"name\": \"home\", \"content\": \"Test content\"}]}" >/dev/null 2>&1
# Then review to C4
curl -s -X POST "$SITES_FACTORY/review" \
    -H "Content-Type: application/json" \
    -d "{\"site_id\": \"$SITE_ID\", \"review\": {\"quality\": \"ok\"}}" >/dev/null 2>&1
# Now try to seal without approval
RESULT=$(curl -s -X POST "$SITES_FACTORY/seal" \
    -H "Content-Type: application/json" \
    -d "{\"site_id\": \"$SITE_ID\"}" 2>/dev/null)
test_result "Seal without approval blocked" "I9" "not approved" "$RESULT"

# ═══════════════════════════════════════════════════════════════
# TEST 5: I9 — Approval Gate (human_approved=false rejected)
# ═══════════════════════════════════════════════════════════════
echo "[5/9] I9: Approve with human_approved=false should be rejected"
RESULT=$(curl -s -X POST "$SITES_FACTORY/approve" \
    -H "Content-Type: application/json" \
    -d "{\"site_id\": \"$SITE_ID\", \"human_approved\": false, \"approved_by\": \"test\"}" 2>/dev/null)
test_result "human_approved=false rejected" "I9" "human_approved=true required" "$RESULT"

# ═══════════════════════════════════════════════════════════════
# TEST 6: I1 — Approval requires approver identity
# ═══════════════════════════════════════════════════════════════
echo "[6/9] I1: Approval without approved_by should fail"
RESULT=$(curl -s -X POST "$SITES_FACTORY/approve" \
    -H "Content-Type: application/json" \
    -d "{\"site_id\": \"$SITE_ID\", \"human_approved\": true}" 2>/dev/null)
test_result "Approval requires approved_by" "I1" "approved_by required" "$RESULT"

# ═══════════════════════════════════════════════════════════════
# TEST 7: I9 — Valid approval passes gate
# ═══════════════════════════════════════════════════════════════
echo "[7/9] I9: Valid approval (human_approved=true + approved_by) passes"
RESULT=$(curl -s -X POST "$SITES_FACTORY/approve" \
    -H "Content-Type: application/json" \
    -d "{\"site_id\": \"$SITE_ID\", \"human_approved\": true, \"approved_by\": \"human-dragon\"}" 2>/dev/null)
test_result "Valid approval passes I9 gate" "I9" "I9 Gate passed" "$RESULT"

# ═══════════════════════════════════════════════════════════════
# TEST 8: I11 — Ledger seal creates permanent receipt
# ═══════════════════════════════════════════════════════════════
echo "[8/9] I11: Seal creates permanent Ledger receipt"
RESULT=$(curl -s -X POST "$SITES_FACTORY/seal" \
    -H "Content-Type: application/json" \
    -d "{\"site_id\": \"$SITE_ID\"}" 2>/dev/null)
test_result "Seal creates Ledger receipt" "I11" "WINDI-SITE-" "$RESULT"

# ═══════════════════════════════════════════════════════════════
# TEST 9: I11 — Double seal rejected (irremediable)
# ═══════════════════════════════════════════════════════════════
echo "[9/9] I11: Double seal rejected (C6 is IRREMEDIÁVEL)"
RESULT=$(curl -s -X POST "$SITES_FACTORY/seal" \
    -H "Content-Type: application/json" \
    -d "{\"site_id\": \"$SITE_ID\"}" 2>/dev/null)
test_result "Double seal rejected" "I11" "already sealed" "$RESULT"

# ═══════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "Constitutional Test Results: $PASSED/$((PASSED + FAILED)) PASSED"
echo "═══════════════════════════════════════════════════════════════"

if [ $FAILED -eq 0 ]; then
    echo "✅ ALL TESTS PASSED — Constitutional compliance verified"
    exit 0
else
    echo "❌ $FAILED TESTS FAILED — Constitutional violations detected"
    exit 1
fi
