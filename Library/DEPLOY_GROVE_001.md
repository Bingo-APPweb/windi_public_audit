# Deploy W-GROVE-001 no Sandbox Core (:8091)
## Plano de 4 comandos

### PRÉ-REQUISITO: Lê sempre antes de tocar no servidor
```bash
ss -tlnp | grep 8091   # confirma que Sandbox Core está vivo
curl -s http://localhost:8091/health | head -20
ls /opt/windi/agents/constitutional-agent/blueprints/
```

---

### PASSO 1 — Upload dos arquivos
Arquivos criados em:
- `/opt/windi/agents/constitutional-agent/blueprints/W-GROVE-001_blueprint.json`
- `/opt/windi/agents/constitutional-agent/blueprints/grove_blueprint.py`

---

### PASSO 2 — Registar no agent.py
No servidor, em `agent.py` adiciona após o WICK blueprint:
```python
try:
    from blueprints.grove_blueprint import grove_bp
    app.register_blueprint(grove_bp)
    print("  [Grove] Grove Orchestrator v1.0.0 loaded on /grove/*")
except ImportError as e:
    print(f"  [Grove] Grove Orchestrator not loaded: {e}")
```

---

### PASSO 3 — Restart do constitutional-agent (nohup pattern)
```bash
# 1. Encontra PID
ps aux | grep "constitutional" | grep -v grep

# 2. Kill
kill <PID>
sleep 2

# 3. Purge cache
find /opt/windi/agents/constitutional-agent -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# 4. Restart
cd /opt/windi/agents/constitutional-agent
nohup python3 agent.py > /opt/windi/logs/constitutional-agent.log 2>&1 &

# 5. Verifica
sleep 3 && curl -s http://localhost:8091/grove/health
```

---

### PASSO 4 — Smoke Test
```bash
# Planta uma ideia
curl -s -X POST http://localhost:8091/grove/seed \
  -H "Content-Type: application/json" \
  -d '{"idea": "Governança de IA verificável com Ledger público", "user": "human_dragon"}' | python3 -m json.tool

# Espera ter session_id e root_node_id na resposta
# Se sim: W-GROVE-001 está vivo 🌱
```

---

### PASSO 5 — Genesis Receipt (após smoke test passar)
```bash
curl -s -X POST http://localhost:8091/grove/ideas/<SESSION_ID>/seal \
  -H "Content-Type: application/json" \
  -d '{"session_id": "<SESSION_ID>", "user": "human_dragon"}' | python3 -m json.tool

# Receipt esperado: WINDI-GROVE-GENESIS-20260308
# Isso sela o nascimento do W-GROVE-001 no Ledger para sempre.
```

---

## Invariante operacional
```
W-GROVE-001 vive em :8091 — NUNCA numa porta separada.
Humano confirma agentes ANTES de serem activados.
O Grove nunca abre chat externo. Contexto preservado sempre.
```

## Próximos passos após deploy
1. [ ] Conectar GroveDebatePanel no frontend (setGroveDebateOpen)
2. [ ] Testar roteamento para W-LEGAL-001 + W-COMM-001
3. [ ] Adicionar /grove/ideas/{id}/graph endpoint ao nginx público
4. [ ] Selar Genesis Receipt no Ledger
5. [ ] Actualizar agentes-windi.md com W-GROVE-001 v1.0.0

---

## Nota de conversão
O código original foi escrito em FastAPI (APIRouter).
Convertido para Flask Blueprint para compatibilidade com constitutional-agent.
Funcionalidade idêntica, apenas mudança de framework.
