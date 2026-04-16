#!/bin/bash
# Restart WINDI Travel to apply login feature
echo "=== Restarting WINDI Travel ==="
systemctl restart windi-travel
sleep 2
systemctl status windi-travel --no-pager | head -10
echo ""
echo "=== Testing login-request endpoint ==="
curl -s -X POST http://localhost:8126/login-request \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com"}' | head -100
echo ""
echo "=== DONE ==="
echo "Test: https://windi-domain.com/travel/gate/"
