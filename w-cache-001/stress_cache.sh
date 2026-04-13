#!/bin/bash
# ═══════════════════════════════════════════════
# W-CACHE-001 · REAL CACHE STRESS TEST
# Tests cache + policy under load
# ═══════════════════════════════════════════════

BASE="http://127.0.0.1:8160/api/cache/v1"

echo "🔥 W-CACHE-001 STRESS TEST START - $(date)"
echo "   Testing: PUT + PROMOTE + POLICY"
echo ""

# Counter for unique IDs
COUNT=0

# Function to create and promote verify entry (should auto-allow)
stress_verify() {
    local i=$1
    local TIMELINE_ID="stress-timeline-$i"

    # Create L2 entry
    RESULT=$(curl -s -X POST "$BASE/entries" \
        -H "Content-Type: application/json" \
        -d "{
            \"namespace\": \"verify.stress\",
            \"tier\": \"L2_DETERMINISTIC\",
            \"scope\": \"RECEIPT\",
            \"value\": {\"test\": \"stress-$i\"},
            \"timeline\": {
                \"timeline_id\": \"$TIMELINE_ID\",
                \"state_version\": 1,
                \"state_hash\": \"hash-$i\"
            }
        }")

    # Extract cache_id
    CACHE_ID=$(echo $RESULT | grep -o '"cache_id":"[^"]*"' | cut -d'"' -f4)

    if [ -n "$CACHE_ID" ]; then
        # Promote (should auto-allow for verify.*)
        curl -s -X POST "$BASE/promote" \
            -H "Content-Type: application/json" \
            -d "{
                \"cache_id\": \"$CACHE_ID\",
                \"content_hash\": \"sha256:stress-$i\",
                \"receipt_id\": \"WINDI-STRESS-VERIFY-$i\"
            }" > /dev/null
    fi
}

# Function to test enterprise policy (should DENY without human_approved)
stress_enterprise() {
    local i=$1
    local TIMELINE_ID="enterprise-timeline-$i"

    # Create L2 entry
    RESULT=$(curl -s -X POST "$BASE/entries" \
        -H "Content-Type: application/json" \
        -d "{
            \"namespace\": \"enterprise.decision\",
            \"tier\": \"L2_DETERMINISTIC\",
            \"scope\": \"CASE\",
            \"value\": {\"decision\": \"stress-$i\"},
            \"timeline\": {
                \"timeline_id\": \"$TIMELINE_ID\",
                \"state_version\": 1,
                \"state_hash\": \"hash-$i\"
            }
        }")

    # Extract cache_id
    CACHE_ID=$(echo $RESULT | grep -o '"cache_id":"[^"]*"' | cut -d'"' -f4)

    if [ -n "$CACHE_ID" ]; then
        # Try to promote WITHOUT human_approved (should DENY)
        curl -s -X POST "$BASE/promote" \
            -H "Content-Type: application/json" \
            -d "{
                \"cache_id\": \"$CACHE_ID\",
                \"content_hash\": \"sha256:enterprise-$i\",
                \"human_approved\": false
            }" > /dev/null
    fi
}

echo "📝 Phase 1: Creating 50 VERIFY entries (auto-promote)"
for i in {1..50}
do
    stress_verify $i &
    sleep 0.02
done
wait
echo "   ✅ Done"

echo ""
echo "🔒 Phase 2: Creating 30 ENTERPRISE entries (should DENY)"
for i in {1..30}
do
    stress_enterprise $i &
    sleep 0.02
done
wait
echo "   ✅ Done"

echo ""
echo "📊 Phase 3: Burst read test"
for i in {1..100}
do
    curl -s "$BASE/metrics" > /dev/null &
done
wait
echo "   ✅ Done"

echo ""
echo "🔥 STRESS TEST COMPLETE - $(date)"
