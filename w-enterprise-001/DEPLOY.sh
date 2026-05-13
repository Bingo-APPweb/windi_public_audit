# W-Enterprise-001 — Deploy Guide
# Execute na ordem. Um bloco de cada vez.
# =============================================

# ── PASSO 1 — Verificar porta livre ──────────────────────
ssh windi@87.106.29.233
ss -tlnp | grep 8150
# Esperado: nada (porta livre)

# ── PASSO 2 — Criar directório ───────────────────────────
mkdir -p /opt/windi/w-enterprise-001/static
mkdir -p /opt/windi/logs

# ── PASSO 3 — Copiar ficheiros do teu computador ─────────
# (executar no teu computador local, não no servidor)
scp main.py windi@87.106.29.233:/opt/windi/w-enterprise-001/
scp requirements.txt windi@87.106.29.233:/opt/windi/w-enterprise-001/
scp static/index.html windi@87.106.29.233:/opt/windi/w-enterprise-001/static/
scp .env windi@87.106.29.233:/opt/windi/w-enterprise-001/

# ── PASSO 4 — Instalar dependências ─────────────────────
pip3 install fastapi uvicorn httpx pydantic --break-system-packages

# ── PASSO 5 — Permissões do .env ─────────────────────────
chmod 600 /opt/windi/w-enterprise-001/.env

# ── PASSO 6 — Testar manualmente (30 seg) ────────────────
cd /opt/windi/w-enterprise-001
python3 main.py &
sleep 3
curl -s http://127.0.0.1:8150/health | python3 -m json.tool
# Esperado: {"service": "W-Enterprise-001", "status": "operational"}
kill %1

# ── PASSO 7 — Instalar systemd service ───────────────────
sudo tee /etc/systemd/system/windi-enterprise.service << 'EOF'
[Unit]
Description=WINDI W-Enterprise-001 AI Compliance Dashboard v1.0.0
Documentation=https://windi-domain.com/enterprise/health
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=windi
Group=windi
WorkingDirectory=/opt/windi/w-enterprise-001
EnvironmentFile=/opt/windi/w-enterprise-001/.env
ExecStart=/usr/bin/python3 /opt/windi/w-enterprise-001/main.py
Restart=always
RestartSec=5
StandardOutput=append:/opt/windi/logs/w-enterprise-001.log
StandardError=append:/opt/windi/logs/w-enterprise-001.log
NoNewPrivileges=yes
ProtectSystem=strict
ReadWritePaths=/opt/windi/logs /opt/windi/w-enterprise-001

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable windi-enterprise.service
sudo systemctl start windi-enterprise.service

# ── PASSO 8 — Verificar serviço ──────────────────────────
sudo systemctl status windi-enterprise.service --no-pager
curl -s http://127.0.0.1:8150/health | python3 -m json.tool

# ── PASSO 9 — Nginx: backup primeiro ─────────────────────
sudo cp /etc/nginx/sites-enabled/one-tree-windi-domain.com \
    /opt/windi/backups/pre_enterprise_$(date +%Y%m%d_%H%M%S)_nginx.bak

# ── PASSO 10 — Descobrir linha SSL no nginx ───────────────
grep -n "listen 443 ssl" /etc/nginx/sites-enabled/one-tree-windi-domain.com
# Anota o número da linha → LINE_NUM

# ── PASSO 11 — Injectar snippet nginx (antes do SSL) ─────
# Substitui LINE_NUM pelo número real da linha anterior
# Este sed insere ANTES da linha do listen 443
LINE_NUM=$(grep -n "listen 443 ssl" /etc/nginx/sites-enabled/one-tree-windi-domain.com | head -1 | cut -d: -f1)
INJECT=$((LINE_NUM - 1))

sudo sed -i "${INJECT}a\\
\\
    # ── W-ENTERPRISE-001 AI Compliance Dashboard (:8150) ──\\
    location /enterprise/ {\\
        proxy_pass http://127.0.0.1:8150/;\\
        proxy_http_version 1.1;\\
        proxy_set_header Host \$host;\\
        proxy_set_header X-Real-IP \$remote_addr;\\
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;\\
        proxy_set_header X-Forwarded-Proto \$scheme;\\
        proxy_read_timeout 120s;\\
        proxy_connect_timeout 10s;\\
    }\\
    location /enterprise/api/ {\\
        proxy_pass http://127.0.0.1:8150/api/;\\
        proxy_http_version 1.1;\\
        proxy_set_header Host \$host;\\
        proxy_set_header X-Real-IP \$remote_addr;\\
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;\\
        proxy_set_header X-Forwarded-Proto \$scheme;\\
        proxy_read_timeout 120s;\\
        proxy_connect_timeout 10s;\\
        add_header Access-Control-Allow-Origin \"https://windi-domain.com\" always;\\
        add_header Access-Control-Allow-Methods \"GET, POST, OPTIONS\" always;\\
        add_header Access-Control-Allow-Headers \"Content-Type, Authorization, X-DID-Token\" always;\\
        if (\$request_method = OPTIONS) { return 204; }\\
    }\\
    # ── END W-ENTERPRISE-001 ──────────────────────────────" \
    /etc/nginx/sites-enabled/one-tree-windi-domain.com

# ── PASSO 12 — Testar e recarregar nginx ─────────────────
sudo nginx -t
# Esperado: syntax is ok / test is successful

sudo systemctl reload nginx

# ── PASSO 13 — Smoke test final ──────────────────────────
curl -s https://windi-domain.com/enterprise/health | python3 -m json.tool
curl -s -o /dev/null -w "%{http_code}" https://windi-domain.com/enterprise/
# Esperado: 200

echo "✅ W-Enterprise-001 LIVE em https://windi-domain.com/enterprise/"
