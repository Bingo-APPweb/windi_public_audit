#!/bin/bash
# W-SESSION-001 — Smoke Test for Sovereign Sessions
# WINDI Publishing House · Kempten, Bavaria · 02 Apr 2026
#
# Usage: bash smoke-session.sh
# Tests:
#   1. Module imports
#   2. Token creation/verification
#   3. Database tables exist
#   4. API endpoints respond (when enabled)

set -e

echo "═══════════════════════════════════════════════════════════"
echo "W-SESSION-001 — Sovereign Session Smoke Test"
echo "═══════════════════════════════════════════════════════════"
echo ""

cd /opt/windi/session

# Load .env for testing
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Test 1: Module imports
echo "1. Testing module imports..."
python3 -c "
from sovereign_session import (
    create_session_token,
    verify_session_token,
    generate_device_id,
    hash_ip_for_signal,
    get_device_name_from_ua,
    is_valid_windi_did,
    ENABLE_SOVEREIGN_SESSION,
    SESSION_TTL_DAYS
)
print('   ✓ All imports successful')
print(f'   Feature enabled: {ENABLE_SOVEREIGN_SESSION}')
print(f'   Session TTL: {SESSION_TTL_DAYS} days')
"

# Test 2: Token creation & verification
echo ""
echo "2. Testing token creation & verification..."
python3 -c "
from sovereign_session import create_session_token, verify_session_token

did = 'did:windi:travel:smoketest'
device_id = 'smoke_test_device_hash'

token, payload = create_session_token(did, device_id)
result = verify_session_token(token)

if result.valid:
    print('   ✓ Token created and verified')
    print(f'   Session ID: {payload.sid[:8]}...')
else:
    print('   ✗ Token verification failed:', result.error)
    exit(1)
"

# Test 3: Database tables
echo ""
echo "3. Testing database tables..."
DB_PATH="/opt/windi/windi-travel/identity-gate/windi_travel_identity.db"
if [ -f "$DB_PATH" ]; then
    TABLES=$(sqlite3 "$DB_PATH" "SELECT name FROM sqlite_master WHERE type='table' AND (name='sovereign_sessions' OR name='device_bindings');")
    if echo "$TABLES" | grep -q "sovereign_sessions" && echo "$TABLES" | grep -q "device_bindings"; then
        echo "   ✓ Tables exist: sovereign_sessions, device_bindings"
    else
        echo "   ✗ Missing tables. Run migration first."
        exit 1
    fi
else
    echo "   ⚠ Database not found at $DB_PATH"
fi

# Test 4: Middleware imports
echo ""
echo "4. Testing middleware imports..."
cd /opt/windi/windi-travel
python3 -c "
from auth_middleware import (
    authenticate_request,
    require_auth,
    get_auth_context,
    SOVEREIGN_COOKIE,
    LEGACY_COOKIE
)
print('   ✓ Middleware imports successful')
print(f'   Sovereign cookie: {SOVEREIGN_COOKIE}')
print(f'   Legacy cookie: {LEGACY_COOKIE}')
"

# Test 5: API endpoint (if service is running)
echo ""
echo "5. Testing API endpoint (session/verify)..."
RESPONSE=$(curl -s -w "\n%{http_code}" http://localhost:8126/session/verify 2>/dev/null || echo "000")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✓ Endpoint responds: $BODY"
elif [ "$HTTP_CODE" = "400" ]; then
    echo "   ✓ Endpoint responds (feature disabled - expected)"
elif [ "$HTTP_CODE" = "000" ]; then
    echo "   ⚠ Service not running on :8126"
else
    echo "   ⚠ Unexpected response: HTTP $HTTP_CODE"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "Smoke Test Complete!"
echo ""
echo "To enable sovereign sessions:"
echo "  1. Edit /opt/windi/windi-travel/identity-gate/.env"
echo "  2. Set ENABLE_SOVEREIGN_SESSION=true"
echo "  3. sudo systemctl restart windi-travel-gate"
echo "═══════════════════════════════════════════════════════════"
