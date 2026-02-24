# 🐉 WINDI PULSE DEPLOY — Execute agora no Strato

## MISSÃO
Deploy do WINDI Pulse (ecosystem health monitor) na porta :8109 com systemd, 
nginx routes, e 2 dashboard UIs estáticas. Tudo interno — Three Dragons only.

O arquivo `/opt/windi/pulse/windi_pulse.py` JÁ está no servidor.

## PASSO 1 — Verificar arquivo e dependências

```bash
ls -la /opt/windi/pulse/windi_pulse.py
python3 -c "import sqlite3, json, hashlib, threading; print('deps OK')"
mkdir -p /opt/windi/pulse/ui
mkdir -p /opt/windi/data
mkdir -p /opt/windi/logs
```

## PASSO 2 — Testar localmente (quick test)

```bash
cd /opt/windi/pulse
timeout 10 python3 windi_pulse.py &
sleep 5
curl -s http://localhost:8109/api/pulse/health | python3 -m json.tool
# Deve retornar: {"service": "WINDI Pulse", "version": "1.0.0", "status": "operational"}
# Se OK, matar o processo de teste
kill %1 2>/dev/null
```

## PASSO 3 — systemd service

```bash
sudo tee /etc/systemd/system/windi-pulse.service << 'EOF'
[Unit]
Description=WINDI Pulse v1.0.0 — Ecosystem Health Monitor
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=windi
Group=windi
WorkingDirectory=/opt/windi/pulse
ExecStart=/usr/bin/python3 /opt/windi/pulse/windi_pulse.py
Restart=always
RestartSec=10
StandardOutput=append:/opt/windi/logs/pulse.log
StandardError=append:/opt/windi/logs/pulse.log
NoNewPrivileges=yes
ProtectSystem=strict
ReadWritePaths=/opt/windi/data /opt/windi/logs /opt/windi/pulse

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable windi-pulse.service
sudo systemctl start windi-pulse.service
sleep 3
sudo systemctl status windi-pulse.service --no-pager
curl -s http://localhost:8109/api/pulse/health | python3 -m json.tool
```

## PASSO 4 — Primeiro scan completo

Espera ~60s para o background scanner completar, depois:

```bash
sleep 60
curl -s http://localhost:8109/api/pulse/scan | python3 -c "
import json,sys
d=json.load(sys.stdin)
s=d.get('summary',{})
print('=== WINDI PULSE — FIRST SCAN ===')
print(f'Services: {s.get(\"total\",0)} total, {s.get(\"alive\",0)} alive, {s.get(\"dead\",0)} dead, {s.get(\"degraded\",0)} degraded')
print(f'Health: {s.get(\"health_pct\",0)}%')
print(f'Wiring: {s.get(\"wired\",0)}/{s.get(\"total_wires\",0)} ({s.get(\"wire_pct\",0)}%)')
print(f'Sentinel: {s.get(\"sentinel_status\",\"unknown\")}')
print()
for svc in d.get('services',[]):
    icon = '✅' if svc['status']=='alive' else '⚠️' if svc['status']=='degraded' else '❌'
    crit = ' [CRITICAL]' if svc.get('critical') else ''
    print(f'  {icon} :{svc[\"port\"]} {svc[\"name\"]} → {svc[\"status\"]} (HTTP {svc[\"http_code\"]}){crit}')
"
```

## PASSO 5 — nginx (3 location blocks)

```bash
# Backup
sudo cp /etc/nginx/sites-enabled/admin.windia4desk.tech /opt/windi/backups/nginx_pre_pulse_$(date +%Y%m%d_%H%M%S).conf

# Encontrar linha SSL para injetar ANTES
grep -n "listen 443 ssl" /etc/nginx/sites-enabled/admin.windia4desk.tech
```

Injetar ANTES da linha "listen 443 ssl" e FORA de qualquer outro location block:

```nginx
    # ── WINDI Pulse API (:8109) ──────────────────────────
    location /pulse/api/ {
        proxy_pass http://127.0.0.1:8109/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 30s;
        proxy_connect_timeout 5s;
        add_header Access-Control-Allow-Origin "https://admin.windia4desk.tech" always;
        add_header Access-Control-Allow-Methods "GET, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Content-Type" always;
        if ($request_method = OPTIONS) {
            return 204;
        }
    }

    # ── WINDI Pulse Outlook UI (static) ──────────────────
    location /pulse/ {
        alias /opt/windi/pulse/ui/;
        index index.html;
        try_files $uri $uri/ /pulse/index.html;
    }

    # ── Palette → Pulse proxy ────────────────────────────
    location /palette/api/pulse/ {
        proxy_pass http://127.0.0.1:8109/api/pulse/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 30s;
        add_header Access-Control-Allow-Origin "https://admin.windia4desk.tech" always;
        add_header Access-Control-Allow-Methods "GET, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Content-Type" always;
        if ($request_method = OPTIONS) {
            return 204;
        }
    }
```

```bash
# Testar e reload
sudo nginx -t && sudo systemctl reload nginx
```

## PASSO 6 — Criar HTML wrappers para as UIs

### 6A. Live Outlook (index.html)

Criar `/opt/windi/pulse/ui/index.html` — uma página HTML standalone que:
- Carrega React 18 via CDN (cdnjs.cloudflare.com)
- Carrega Babel standalone para JSX
- Faz fetch a `/pulse/api/pulse/scan`, `/pulse/api/pulse/outlook`, 
  `/pulse/api/pulse/history`, `/pulse/api/pulse/sentinel`
- Auto-refresh a cada 30 segundos
- Mostra: dashboard de métricas, lista de serviços com pulse animado,
  sprint progress (S0-S4), memory loop events, deep checks
- Design: NOIR theme (background #090910, gold #C9A227, JetBrains Mono)
- O arquivo `/opt/windi/pulse/ui/live-outlook.jsx` tem o componente React 
  completo — transformar para browser: remover imports, usar React globals,
  ajustar PULSE_BASE para "/pulse/api/pulse"

### 6B. Product Outlook (outlook.html)

Criar `/opt/windi/pulse/ui/outlook.html` — página HTML standalone que:
- Carrega React 18 + Babel via CDN
- Mostra as 36 features mapeadas do Palette com status
- Wiring view (server ↔ palette)
- Sprint plan (S0-S4)
- Design: NOIR theme matching
- O arquivo `/opt/windi/pulse/ui/product-outlook.jsx` tem o componente — 
  transformar para browser da mesma forma

IMPORTANTE: Se os arquivos .jsx NÃO estão no servidor, criar os HTMLs
com o componente inline. Ler o contexto da conversa para obter o código 
completo dos componentes React.

## PASSO 7 — Smoke test final

```bash
echo "╔═══════════════════════════════════════════════════════╗"
echo "║  🐉 WINDI PULSE — DEPLOY COMPLETE                     ║"
echo "╚═══════════════════════════════════════════════════════╝"

echo "=== systemd ==="
sudo systemctl is-active windi-pulse

echo "=== API endpoints ==="
curl -s -o /dev/null -w "  /pulse/api/pulse/health   → %{http_code}\n" https://admin.windia4desk.tech/pulse/api/pulse/health
curl -s -o /dev/null -w "  /pulse/api/pulse/scan     → %{http_code}\n" https://admin.windia4desk.tech/pulse/api/pulse/scan
curl -s -o /dev/null -w "  /pulse/api/pulse/outlook  → %{http_code}\n" https://admin.windia4desk.tech/pulse/api/pulse/outlook
curl -s -o /dev/null -w "  /pulse/api/pulse/sentinel → %{http_code}\n" https://admin.windia4desk.tech/pulse/api/pulse/sentinel

echo "=== UI pages ==="
curl -s -o /dev/null -w "  /pulse/                   → %{http_code}\n" https://admin.windia4desk.tech/pulse/
curl -s -o /dev/null -w "  /pulse/outlook.html       → %{http_code}\n" https://admin.windia4desk.tech/pulse/outlook.html

echo "=== Palette proxy ==="
curl -s -o /dev/null -w "  /palette/api/pulse/scan   → %{http_code}\n" https://admin.windia4desk.tech/palette/api/pulse/scan

echo "=== Files ==="
ls -la /opt/windi/pulse/windi_pulse.py
ls -la /opt/windi/pulse/ui/index.html
ls -la /opt/windi/pulse/ui/outlook.html
ls -la /opt/windi/data/pulse.db

echo ""
echo "URLs (Internal — Three Dragons Only):"
echo "  Live:    https://admin.windia4desk.tech/pulse/"
echo "  Map:     https://admin.windia4desk.tech/pulse/outlook.html"
echo "  API:     https://admin.windia4desk.tech/pulse/api/pulse/scan"
```

## REGRAS

- Seguir a regra "antes de operar código, opera ambiente": 
  `ss -tlnp | grep :8109` antes de tudo
- `sudo nginx -t` SEMPRE antes de reload
- Se o Pulse não arranca, verificar logs: `tail -30 /opt/windi/logs/pulse.log`
- Location Matrix update: `pulse:8109:A/pulse/:pulse/:σ`
- Porta 8109 é a PRÓXIMA disponível após 8108 (Palette)
