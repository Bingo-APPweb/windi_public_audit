#!/bin/bash
# W-SEC-001 Smoke Test
# Usage: bash smoke-test.sh

BASE_URL="http://127.0.0.1:8144"

echo "=== W-SEC-001 Smoke Test ==="
echo ""

# 1. Health check
echo "1. Health check..."
curl -s "$BASE_URL/health" | python3 -m json.tool
echo ""

# 2. First event
echo "2. Sending first event..."
RESP1=$(curl -s -X POST "$BASE_URL/sec/events" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id":"sec_evt_smoke_001",
    "timestamp":"2026-04-08T12:00:00Z",
    "source":"smoke-test",
    "sensor":"test_sensor",
    "event_type":"rate_limit_exceeded",
    "severity":"medium",
    "confidence":0.85,
    "actor":{"ip":"203.0.113.10","session_id":"sess_smoke","user_agent":"smoke-test/1.0"},
    "target":{"service":"test-service","endpoint":"/test/endpoint","method":"POST"},
    "threat":{"family":"abuse","vector":"api_flood"}
  }')
echo "$RESP1" | python3 -m json.tool
INCIDENT_ID=$(echo "$RESP1" | python3 -c "import sys, json; print(json.load(sys.stdin)['incident_id'])")
echo "Incident ID: $INCIDENT_ID"
echo ""

# 3. Second event (should correlate)
echo "3. Sending second event (should correlate)..."
curl -s -X POST "$BASE_URL/sec/events" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id":"sec_evt_smoke_002",
    "timestamp":"2026-04-08T12:00:30Z",
    "source":"smoke-test",
    "sensor":"test_sensor",
    "event_type":"rate_limit_exceeded",
    "severity":"medium",
    "confidence":0.87,
    "actor":{"ip":"203.0.113.10","session_id":"sess_smoke","user_agent":"smoke-test/1.0"},
    "target":{"service":"test-service","endpoint":"/test/endpoint","method":"POST"},
    "threat":{"family":"abuse","vector":"api_flood"}
  }' | python3 -m json.tool
echo ""

# 4. Third event (different actor - new incident)
echo "4. Sending event from different actor (new incident)..."
curl -s -X POST "$BASE_URL/sec/events" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id":"sec_evt_smoke_003",
    "timestamp":"2026-04-08T12:01:00Z",
    "source":"smoke-test",
    "sensor":"test_sensor",
    "event_type":"token_invalid",
    "severity":"low",
    "confidence":0.90,
    "actor":{"ip":"198.51.100.20","session_id":"sess_other","user_agent":"other-client/2.0"},
    "target":{"service":"auth-service","endpoint":"/auth/login","method":"POST"},
    "threat":{"family":"intrusion","vector":"credential_stuffing"}
  }' | python3 -m json.tool
echo ""

# 5. List incidents
echo "5. Listing all incidents..."
curl -s "$BASE_URL/sec/incidents" | python3 -m json.tool
echo ""

# 6. Get first incident details
echo "6. Getting incident details: $INCIDENT_ID..."
curl -s "$BASE_URL/sec/incidents/$INCIDENT_ID" | python3 -m json.tool
echo ""

# 7. Get incident events
echo "7. Getting incident events..."
curl -s "$BASE_URL/sec/incidents/$INCIDENT_ID/events" | python3 -m json.tool
echo ""

# 8. Seal incident
echo "8. Sealing incident (anchoring to ledger)..."
curl -s -X POST "$BASE_URL/sec/incidents/$INCIDENT_ID/seal" | python3 -m json.tool
echo ""

# 9. Metrics
echo "9. Checking metrics..."
curl -s "$BASE_URL/metrics" | python3 -m json.tool
echo ""

echo "=== Smoke Test Complete ==="
