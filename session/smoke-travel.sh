#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# WINDI Travel Smoke Test — T1 Invariant Enforcement
# "No Travel, nenhum § toca em código existente sem cirurgia documentada."
# ═══════════════════════════════════════════════════════════════════════════

echo "═══════════════════════════════════════════════════════════════"
echo "  WINDI Travel Smoke Test — T1 Protocol"
echo "═══════════════════════════════════════════════════════════════"
echo ""

BASE="http://localhost:8126"
PASS=0
FAIL=0
WARN=0

# Check that accepts 200
check() {
  local url="$1"
  local name="$2"
  CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$url")
  if [ "$CODE" = "200" ]; then
    echo "  ✅ $name"
    ((PASS++))
  else
    echo "  ❌ $name → HTTP $CODE"
    ((FAIL++))
  fi
}

# Check that accepts 200 or 302 (redirect to gate is OK for unauthenticated)
check_or_redirect() {
  local url="$1"
  local name="$2"
  CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$url")
  if [ "$CODE" = "200" ] || [ "$CODE" = "302" ]; then
    echo "  ✅ $name (HTTP $CODE)"
    ((PASS++))
  else
    echo "  ❌ $name → HTTP $CODE"
    ((FAIL++))
  fi
}

# Check that accepts 200 or 401 (auth required is expected for wallet endpoints)
check_or_auth() {
  local url="$1"
  local name="$2"
  CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$url")
  if [ "$CODE" = "200" ] || [ "$CODE" = "401" ]; then
    echo "  ✅ $name (HTTP $CODE — auth expected)"
    ((PASS++))
  else
    echo "  ❌ $name → HTTP $CODE"
    ((FAIL++))
  fi
}

# Check external dependency (warn on timeout, don't fail)
check_external() {
  local url="$1"
  local name="$2"
  CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 20 "$url")
  if [ "$CODE" = "200" ]; then
    echo "  ✅ $name"
    ((PASS++))
  elif [ "$CODE" = "000" ]; then
    echo "  ⚠️  $name → timeout (external API)"
    ((WARN++))
  else
    echo "  ❌ $name → HTTP $CODE"
    ((FAIL++))
  fi
}

check_post() {
  local url="$1"
  local data="$2"
  local name="$3"
  CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 25 -X POST -H "Content-Type: application/json" -d "$data" "$url")
  if [ "$CODE" = "200" ]; then
    echo "  ✅ $name"
    ((PASS++))
  elif [ "$CODE" = "000" ]; then
    echo "  ⚠️  $name → timeout (external API)"
    ((WARN++))
  else
    echo "  ❌ $name → HTTP $CODE"
    ((FAIL++))
  fi
}

echo "Core Endpoints:"
check "$BASE/"                                        "MARIA UI Root"

echo ""
echo "§109 Foto/Video Seal:"
check_or_redirect "$BASE/workspace/"                  "Workspace UI"

echo ""
echo "§110 GPS Geocoding:"
check "$BASE/reverse-geocode?lat=48.77&lng=10.31"     "Nominatim Reverse"

echo ""
echo "§111 MARIA↔Tesoura:"
check_or_auth "$BASE/workspace/media-seals?limit=1"   "Media Seals Endpoint"
check "$BASE/workspace/check-collage"                 "Collage Check"

echo ""
echo "§112 Thread Visual:"
check "$BASE/workspace/thread"                        "Thread Endpoint"

echo ""
echo "Email Verification:"
check "$BASE/verify-email/TEST_FAKE_TOKEN"            "Verify Email (invalid token → 200 OK)"

echo ""
echo "§103.T Train Intelligence (external API):"
check_external "$BASE/train/stations?query=Berlin"    "Train Stations"
check_external "$BASE/train/journeys?from_id=8000197&to_id=8011160&results=1" "Train Journeys"
check_post "$BASE/train/maria-decide" '{"from_id":"8000197","to_id":"8011160","results":1}' "MARIA Decide"

echo ""
echo "═══════════════════════════════════════════════════════════════"
if [ $FAIL -eq 0 ]; then
  if [ $WARN -gt 0 ]; then
    echo "  Status: ⚠️  PASS with warnings ($PASS passed, $WARN warnings)"
    echo "  External APIs may be slow. Core system OK."
  else
    echo "  Status: ✅ ALL PASS ($PASS/$PASS)"
  fi
  echo "  Ready for deployment."
  EXIT_CODE=0
else
  echo "  Status: ❌ FAILURES ($PASS passed, $FAIL failed, $WARN warnings)"
  echo "  DO NOT DEPLOY — resolve issues first."
  EXIT_CODE=$FAIL
fi
echo "═══════════════════════════════════════════════════════════════"
echo ""

exit $EXIT_CODE
