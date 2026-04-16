#!/bin/bash
# Test MARIA trilingual response
curl -s "http://127.0.0.1:8126/maria/plan" \
  -H "Content-Type: application/json" \
  -d '{"query":"restaurante","wallet_id":"test","lang":"PT","lat":48.8,"lng":2.3,"intent":{"type":"restaurant"}}' \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
v = d.get('maria_voice', {})
print('PT:', v.get('PT', '')[:80])
print('DE:', v.get('DE', '')[:80])
print('EN:', v.get('EN', '')[:80])
"
