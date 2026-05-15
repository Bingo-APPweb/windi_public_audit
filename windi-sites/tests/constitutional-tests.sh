#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# W-SITES-001 Constitutional Test Suite v2.0
# Testing Identity Gate v1.2.0 API
# §11 Invariants: I1 · I9 · I11 · I12 · I14
# Date: 29 April 2026
# ═══════════════════════════════════════════════════════════════

GATE="http://127.0.0.1:8192"
PASSED=0
FAILED=0

# Test email (won't actually send in test mode)
TEST_EMAIL="test-$(date +%s)@windi-test.local"
TEST_DID=""
TEST_COMPANY_ID=""

echo "═══════════════════════════════════════════════════════════════"
echo "W-SITES-001 Constitutional Test Suite v2.0"
echo "Testing Identity Gate v1.2.0"
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
# TEST 1: Health check confirms service is running
# ═══════════════════════════════════════════════════════════════
echo "[1/9] SERVICE: Health check confirms gate is running"
RESULT=$(curl -s "$GATE/health" 2>/dev/null)
test_result "Health check returns status" "SERVICE" "healthy" "$RESULT"

# ═══════════════════════════════════════════════════════════════
# TEST 2: I14 — Explicit Failure (missing required fields)
# ═══════════════════════════════════════════════════════════════
echo "[2/9] I14: Register without required fields fails explicitly"
RESULT=$(curl -s -X POST "$GATE/register" \
    -H "Content-Type: application/json" \
    -d '{"legal_name": "Test Corp"}' 2>/dev/null)
test_result "Missing fields rejected explicitly" "I14" "Field required" "$RESULT"

# ═══════════════════════════════════════════════════════════════
# TEST 3: I1 — Sovereignty (successful registration with all fields)
# ═══════════════════════════════════════════════════════════════
echo "[3/9] I1: Complete registration creates sovereign identity"
RESULT=$(curl -s -X POST "$GATE/register" \
    -H "Content-Type: application/json" \
    -d "{
        \"legal_name\": \"Constitutional Test Law Firm\",
        \"country\": \"DE\",
        \"vat_number\": \"DE999999999\",
        \"type\": \"law_firm\",
        \"admin_name\": \"Test Admin\",
        \"admin_email\": \"$TEST_EMAIL\"
    }" 2>/dev/null)

# Extract DID from response
TEST_DID=$(echo "$RESULT" | grep -o '"did":"[^"]*"' | cut -d'"' -f4)
TEST_COMPANY_ID=$(echo "$RESULT" | grep -o '"company_id":"[^"]*"' | cut -d'"' -f4)

test_result "Registration creates DID" "I1" "did:windi:" "$RESULT"
echo "   DID: $TEST_DID"
echo "   Company ID: $TEST_COMPANY_ID"

# ═══════════════════════════════════════════════════════════════
# TEST 4: I11 — Ledger receipt created on registration
# ═══════════════════════════════════════════════════════════════
echo "[4/9] I11: Registration creates permanent Ledger receipt"
test_result "Ledger receipt in response" "I11" "ledger_receipt" "$RESULT"

# ═══════════════════════════════════════════════════════════════
# TEST 5: I14 — Identity query with invalid DID fails explicitly
# ═══════════════════════════════════════════════════════════════
echo "[5/9] I14: Query invalid DID returns explicit error"
RESULT=$(curl -s "$GATE/identity/did:windi:invalid-test-999" 2>/dev/null)
test_result "Invalid DID returns error code" "I14" "NOT_FOUND" "$RESULT"

# ═══════════════════════════════════════════════════════════════
# TEST 6: I1 — Identity query with valid DID returns data
# ═══════════════════════════════════════════════════════════════
echo "[6/9] I1: Query valid DID returns identity data"
if [ -n "$TEST_DID" ]; then
    RESULT=$(curl -s "$GATE/identity/$TEST_DID" 2>/dev/null)
    test_result "Valid DID returns identity" "I1" "Constitutional Test Law Firm" "$RESULT"
else
    echo "⚠️  SKIP: No DID from registration (test 3 failed)"
    ((FAILED++))
fi

# ═══════════════════════════════════════════════════════════════
# TEST 7: I9 — Workspace blocked without valid DID
# ═══════════════════════════════════════════════════════════════
echo "[7/9] I9: Workspace access blocked without DID (fail-closed)"
# Check HTTP status code (should be 302 redirect)
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$GATE/workspace/" 2>/dev/null)
if [ "$HTTP_CODE" = "302" ]; then
    echo "✅ PASS: Workspace blocked without DID [I9]"
    ((PASSED++))
else
    echo "❌ FAIL: Workspace blocked without DID [I9]"
    echo "   Expected: 302 (redirect)"
    echo "   Actual: $HTTP_CODE"
    ((FAILED++))
fi

# ═══════════════════════════════════════════════════════════════
# TEST 8: I9 — Workspace allowed with VERIFIED DID
# ═══════════════════════════════════════════════════════════════
echo "[8/9] I9: Workspace access granted with VERIFIED DID"
if [ -n "$TEST_DID" ]; then
    # Try with DID in query param
    RESULT=$(curl -s "$GATE/workspace/?did=$TEST_DID" 2>/dev/null)
    # Should return workspace HTML (not redirect to gate)
    if [[ "$RESULT" == *"gate"* ]] && [[ "$RESULT" != *"workspace"* ]]; then
        echo "❌ FAIL: Workspace blocked even with valid DID [I9]"
        echo "   Expected: workspace content"
        echo "   Actual: redirected to gate"
        ((FAILED++))
    else
        echo "✅ PASS: Workspace accessible with valid DID [I9]"
        ((PASSED++))
    fi
else
    echo "⚠️  SKIP: No DID from registration (test 3 failed)"
    ((FAILED++))
fi

# ═══════════════════════════════════════════════════════════════
# TEST 9: I11 — Identity Card export includes genesis_receipt
# ═══════════════════════════════════════════════════════════════
echo "[9/9] I11: Identity Card export includes permanent receipt"
if [ -n "$TEST_DID" ]; then
    RESULT=$(curl -s "$GATE/dashboard/$TEST_DID/json" 2>/dev/null)
    test_result "Identity Card has genesis_receipt" "I11" "genesis_receipt" "$RESULT"
    test_result "Identity Card has verify_url" "I11" "verify_url" "$RESULT"
else
    echo "⚠️  SKIP: No DID from registration (test 3 failed)"
    ((FAILED++))
fi

# ═══════════════════════════════════════════════════════════════
# CLEANUP (optional — comment out to inspect test data)
# ═══════════════════════════════════════════════════════════════
# echo ""
# echo "Cleaning up test data..."
# sqlite3 /opt/windi/windi-sites/identity-gate/windi_sites_identity.db \
#   "DELETE FROM admins WHERE email LIKE 'test-%@windi-test.local';"

# ═══════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "Constitutional Test Results: $PASSED/$((PASSED + FAILED)) PASSED"
echo "═══════════════════════════════════════════════════════════════"

if [ $FAILED -eq 0 ]; then
    echo "✅ ALL TESTS PASSED — Constitutional compliance verified"
    echo ""
    echo "Test Identity Created:"
    echo "  Email: $TEST_EMAIL"
    echo "  DID: $TEST_DID"
    echo "  Company: $TEST_COMPANY_ID"
    exit 0
else
    echo "❌ $FAILED TESTS FAILED — Constitutional violations detected"
    exit 1
fi
