#!/bin/bash
# Restart WINDI-LAW para aplicar tema toggle

echo "=== Restarting WINDI-LAW ==="
systemctl restart windi-law
sleep 2
systemctl status windi-law | head -8

echo ""
echo "=== Verificando endpoint ==="
curl -s http://127.0.0.1:8122/ai-draft/health | head -1

echo ""
echo "=========================================="
echo "Toggle de tema adicionado!"
echo "☀ = NOIR activo (clica para KLAR)"
echo "☽ = KLAR activo (clica para NOIR)"
echo "=========================================="
