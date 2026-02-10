#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# WINDI FORENSIC — Test Script for /v1/forensic/validate-handwritten
# "O Tabelião Digital do Compromisso Manuscrito"
# ═══════════════════════════════════════════════════════════════

BASE_URL="${1:-http://localhost:8091}"

echo "╔══════════════════════════════════════════════════════╗"
echo "║  WINDI FORENSIC — TEST SUITE                        ║"
echo "║  Target: $BASE_URL                                  ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# ─── Test 1: Health Check ────────────────────────────────────
echo "🔍 Test 1: Health Check"
curl -s "$BASE_URL/v1/forensic/health" | python3 -m json.tool
echo ""

# ─── Test 2: Basic Validation (no financial link) ────────────
echo "🔍 Test 2: Basic Validation (MEDIUM governance)"

# Create a dummy test image
echo "WINDI-TEST-IMAGE-CONTENT" > /tmp/test_napkin.jpg

curl -s -X POST "$BASE_URL/v1/forensic/validate-handwritten" \
  -H "X-WINDI-Identity: dragon-hq-001" \
  -H "X-Governance-Level: MEDIUM" \
  -F "image_file=@/tmp/test_napkin.jpg" \
  -F 'metadata_json={"timestamp_mobile":"2026-02-10T14:30:00Z","device_id":"DRAGON-MOBILE-001","gps_latitude":47.7267,"gps_longitude":10.3168,"device_model":"Pixel 9 Pro","capture_resolution":"4032x3024"}' \
  | python3 -m json.tool
echo ""

# ─── Test 3: HIGH Governance + Financial Link ────────────────
echo "🔍 Test 3: HIGH Governance + Financial Settlement Link"

curl -s -X POST "$BASE_URL/v1/forensic/validate-handwritten" \
  -H "X-WINDI-Identity: dragon-hq-001" \
  -H "X-Governance-Level: HIGH" \
  -F "image_file=@/tmp/test_napkin.jpg" \
  -F 'metadata_json={"timestamp_mobile":"2026-02-10T14:32:00Z","device_id":"DRAGON-MOBILE-001","gps_latitude":47.7267,"gps_longitude":10.3168}' \
  -F "link_financial_id=PIX-2026021014-ABCD-7890" \
  | python3 -m json.tool
echo ""

# ─── Test 4: Missing Identity (should fail 401) ─────────────
echo "🔍 Test 4: Missing Identity Header (expect 401)"

curl -s -X POST "$BASE_URL/v1/forensic/validate-handwritten" \
  -H "X-Governance-Level: BASIC" \
  -F "image_file=@/tmp/test_napkin.jpg" \
  -F 'metadata_json={"timestamp_mobile":"2026-02-10T14:30:00Z","device_id":"TEST"}' \
  | python3 -m json.tool
echo ""

echo "═══ TEST SUITE COMPLETE ═══"
echo "Port Map: 8091 = WINDI Forensic (Digital Notary)"
echo "Strato deploy: nohup python3 forensic_validate_handwritten.py > /tmp/forensic.log 2>&1 &"
