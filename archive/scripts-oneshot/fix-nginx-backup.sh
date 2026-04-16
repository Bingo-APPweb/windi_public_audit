#!/bin/bash
# Fix: Mover backup para local correcto

echo "=== Movendo backup para /opt/windi/backups/ ==="
mkdir -p /opt/windi/backups/nginx
mv /etc/nginx/sites-enabled/*.bak* /opt/windi/backups/nginx/ 2>/dev/null || true

echo "=== Testando nginx ==="
nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Nginx OK"
    echo ""
    echo "=== Reloading nginx ==="
    systemctl reload nginx
    echo "✅ Nginx reloaded"
else
    echo "❌ Nginx ainda tem erros"
fi
