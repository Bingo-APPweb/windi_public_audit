# 🚨 SPRINT 0 — RESSUSCITAR DRAGON SERVER

## CONTEXTO
O WINDI Pulse (recém-deployed em :8109) confirma:
- `:8108` Palette UI → HTTP 200 ✅ (a página estática funciona)
- `/api/dragon/health` → HTTP 404 ❌ (cérebro LLM morto)
- `/api/dragon/chat` → HTTP 404 ❌ (chat morto)
- systemd: **no-unit** (roda via nohup — por isso morreu e ninguém reiniciou)

SEM o Dragon Server, o Palette é uma casca. Todos os Sprints 1-4 dependem dele.

## REGRA WINDI
"Antes de operar código, opera ambiente."

## PASSO 1 — Diagnóstico do ambiente

```bash
echo "=== DRAGON SERVER DIAGNÓSTICO ==="

# O que está na porta 8108?
ss -tlnp | grep :8108

# Existe processo do dragon server?
ps aux | grep -i "dragon\|agent_dragon\|palette" | grep -v grep

# O arquivo existe?
ls -la /opt/windi/agent-palette/agent_dragon_server.py

# Que processos servem a porta 8108?
# (o Palette UI é servido por quem? nginx alias estático? ou o próprio dragon server?)
cat /etc/nginx/sites-enabled/admin.windia4desk.tech | grep -A 10 "palette"

# Verificar se é o dragon server que serve tudo (UI + API) ou se são separados
head -50 /opt/windi/agent-palette/agent_dragon_server.py

# Verificar logs existentes
ls -la /opt/windi/logs/dragon* /opt/windi/logs/palette* 2>/dev/null
tail -30 /opt/windi/logs/dragon*.log 2>/dev/null || echo "No dragon logs found"
tail -30 /opt/windi/logs/palette*.log 2>/dev/null || echo "No palette logs found"

# Verificar se tem .env ou config
cat /opt/windi/agent-palette/.env 2>/dev/null || echo "No .env"
ls -la /opt/windi/agent-palette/
```

## PASSO 2 — Entender a arquitectura

O Dragon Server (`agent_dragon_server.py`) provavelmente:
- Serve a UI estática (HTML/JS) em `/` → por isso HTTP 200
- Tem rotas API em `/api/dragon/health`, `/api/dragon/chat`, `/api/dragon/generate`, `/api/dragon/render`
- Usa Claude Sonnet API via chave em `/opt/windi/tsil/`
- Precisa de variável de ambiente com API key

Verificar:
```bash
# Procurar API key reference
grep -n "ANTHROPIC\|API_KEY\|api_key\|claude\|sonnet" /opt/windi/agent-palette/agent_dragon_server.py | head -20

# Procurar como o servidor arranca
grep -n "def main\|if __name__\|app.run\|serve\|HTTPServer\|uvicorn\|flask" /opt/windi/agent-palette/agent_dragon_server.py | head -10

# Procurar as rotas API
grep -n "def do_GET\|def do_POST\|@app.route\|@app.get\|@app.post\|/api/dragon" /opt/windi/agent-palette/agent_dragon_server.py | head -20

# Verificar que porta usa
grep -n "8108\|PORT\|port" /opt/windi/agent-palette/agent_dragon_server.py | head -10
```

## PASSO 3 — Ressuscitar o Dragon Server

Baseado no diagnóstico, uma destas opções:

### Opção A: Se é Python HTTP Server simples
```bash
# Matar qualquer ghost
kill $(pgrep -f "agent_dragon_server") 2>/dev/null
sleep 2

# Limpar cache
find /opt/windi/agent-palette/ -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# Testar manualmente
cd /opt/windi/agent-palette
python3 agent_dragon_server.py &
sleep 5
curl -s http://localhost:8108/api/dragon/health | python3 -m json.tool
# Se funcionar → matar e prosseguir para systemd
kill %1
```

### Opção B: Se precisa de API key como env var
```bash
# Verificar a key
ls -la /opt/windi/tsil/
cat /opt/windi/tsil/.anthropic_key 2>/dev/null || \
cat /opt/windi/tsil/anthropic_api_key 2>/dev/null || \
grep -r "ANTHROPIC" /opt/windi/agent-palette/ --include="*.env" 2>/dev/null

# Criar .env se necessário
cat > /opt/windi/agent-palette/.env << 'EOF'
ANTHROPIC_API_KEY=$(cat /opt/windi/tsil/.anthropic_key 2>/dev/null || cat /opt/windi/tsil/anthropic_api_key 2>/dev/null)
PORT=8108
EOF
```

## PASSO 4 — systemd permanente

```bash
# Criar service unit (ajustar ExecStart baseado no diagnóstico do Passo 2)
sudo tee /etc/systemd/system/windi-palette.service << 'SERVICEEOF'
[Unit]
Description=WINDI Agent Palette — Dragon Server v0.7.0-D
Documentation=https://admin.windia4desk.tech/palette/
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=windi
Group=windi
WorkingDirectory=/opt/windi/agent-palette
EnvironmentFile=-/opt/windi/agent-palette/.env
ExecStart=/usr/bin/python3 /opt/windi/agent-palette/agent_dragon_server.py
Restart=always
RestartSec=5
StandardOutput=append:/opt/windi/logs/palette.log
StandardError=append:/opt/windi/logs/palette.log
NoNewPrivileges=yes
ProtectSystem=strict
ReadWritePaths=/opt/windi/logs /opt/windi/agent-palette /opt/windi/data /opt/windi/tsil

[Install]
WantedBy=multi-user.target
SERVICEEOF

# Matar qualquer processo nohup existente na 8108
kill $(pgrep -f "agent_dragon_server") 2>/dev/null
sleep 2

# Ativar systemd
sudo systemctl daemon-reload
sudo systemctl enable windi-palette.service
sudo systemctl start windi-palette.service
sleep 5

# Verificar
sudo systemctl status windi-palette.service --no-pager
```

## PASSO 5 — Validação do Dragon Brain

```bash
echo "=== DRAGON SERVER VALIDATION ==="

# Health
echo -n "Health: "
curl -s http://localhost:8108/api/dragon/health | python3 -m json.tool

# Chat test EN
echo -e "\nChat EN: "
curl -s -X POST http://localhost:8108/api/dragon/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Who are you?","tier":"LOW","language":"en"}' | python3 -m json.tool

# Chat test DE
echo -e "\nChat DE: "
curl -s -X POST http://localhost:8108/api/dragon/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Wer bist du?","tier":"LOW","language":"de"}' | python3 -m json.tool

# Chat test PT
echo -e "\nChat PT: "
curl -s -X POST http://localhost:8108/api/dragon/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Quem é você?","tier":"LOW","language":"pt"}' | python3 -m json.tool

# Render test
echo -e "\nRender: "
curl -s -X POST http://localhost:8108/api/dragon/render \
  -H "Content-Type: application/json" \
  -d '{"template":"invoice","data":{"company":"Test"},"language":"en"}' | head -200

# Wisdom candidate
echo -e "\nWisdom: "
curl -s -X POST http://localhost:8108/api/wisdom/candidate \
  -H "Content-Type: application/json" \
  -d '{"text":"test wisdom"}' | head -100
```

## PASSO 6 — Verificar via HTTPS (nginx)

```bash
echo "=== HTTPS VALIDATION ==="
curl -s https://admin.windia4desk.tech/palette/api/dragon/health | python3 -m json.tool
curl -s -X POST https://admin.windia4desk.tech/palette/api/dragon/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Health check from Sprint 0","tier":"LOW","language":"en"}' | head -200
```

## PASSO 7 — Confirmar no Pulse

```bash
# Esperar próximo scan do Pulse (60s)
sleep 65

# Verificar que Pulse detectou a mudança
curl -s http://localhost:8109/api/pulse/scan | python3 -c "
import json,sys
d=json.load(sys.stdin)
for svc in d['services']:
    if svc['id'] == 'palette':
        print(f'Palette: {svc[\"status\"]} (HTTP {svc[\"http_code\"]})')
        print(f'systemd: {svc[\"systemd\"]}')
        if svc.get('extra_checks'):
            for name, ec in svc['extra_checks'].items():
                icon = '✅' if ec.get('alive') and ec.get('code',999) < 400 else '❌'
                print(f'  {icon} {name}: HTTP {ec.get(\"code\",0)}')

# Verificar Memory Loop (deve ter evento de mudança)
print()
events = json.load(open('/dev/stdin') if False else sys.stdin) if False else None
"

curl -s http://localhost:8109/api/pulse/history | python3 -c "
import json,sys
d=json.load(sys.stdin)
print('=== MEMORY LOOP (últimos eventos) ===')
for ev in d.get('events',[])[:5]:
    print(f'  [{ev[\"severity\"]}] {ev[\"message\"]}')
"
```

## RESULTADO ESPERADO

Após Sprint 0 completo:
- `windi-palette.service` → **active (running)**
- `/api/dragon/health` → **200 + JSON com versão e status**
- `/api/dragon/chat` → **200 + resposta trilíngue do Dragon**
- Pulse detecta: **"Agent Palette: degraded → alive"**
- systemd garante: **auto-restart se crashar, sobrevive reboot**

O Dragon acorda. O cérebro volta. Os Sprints 1-4 ficam desbloqueados. 🐉🔥
