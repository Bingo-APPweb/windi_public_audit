#!/bin/bash
# Restart WINDI-LAW to apply login feature
echo "=== Restarting WINDI-LAW ==="
systemctl restart windi-law
sleep 2
systemctl status windi-law --no-pager | head -10
echo ""
echo "=== Testing login-request endpoint ==="
curl -s -X POST http://localhost:8122/login-request \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com"}' | head -100
echo ""
echo "=== DONE ==="
echo "Test Travel: https://windi-domain.com/travel/gate/"
echo "Test LAW:    https://windi-domain.com/law/gate/"
