# ONE-TAP ENDORSEMENT — INSTRUÇÕES PARA O GÊMEO
# Integração: W-VIRTUE-001 + Canvas Gen 7 G3 Bottom Sheet
# Data: 13 Mar 2026

## FICHEIROS DESTA ENTREGA
```
virtue_receipt_blueprint.py  → blueprint para Sandbox Core (:8091)
endorsement-g3.html          → HTML+CSS+JS injetável no Canvas
```

---

## PASSO 0 — Backup

```bash
cp /opt/windi/agents/constitutional-agent/agent.py \
   /opt/windi/backups/agent-pre-virtue-$(date +%Y%m%d_%H%M%S).py
cp /opt/windi/agent-palette/ui/index.html \
   /opt/windi/backups/canvas-pre-virtue-$(date +%Y%m%d_%H%M%S).html
```

---

## PASSO 1 — Instalar blueprint no Sandbox Core

```bash
# Copiar blueprint
cp virtue_receipt_blueprint.py \
   /opt/windi/agents/constitutional-agent/blueprints/

# Verificar
ls /opt/windi/agents/constitutional-agent/blueprints/ | grep virtue
```

---

## PASSO 2 — Registar blueprint no agent.py

Abrir `/opt/windi/agents/constitutional-agent/agent.py` e adicionar:

```python
# No bloco de imports dos blueprints (junto com os outros)
from blueprints.virtue_receipt_blueprint import virtue_bp

# No bloco de registo de blueprints (junto com os outros app.register_blueprint)
app.register_blueprint(virtue_bp)
```

**Verificar onde registar:**
```bash
grep -n "register_blueprint" /opt/windi/agents/constitutional-agent/agent.py | head -10
```

---

## PASSO 3 — Criar directório de dados

```bash
mkdir -p /opt/windi/data
# (o blueprint cria o SQLite automaticamente na primeira chamada)
```

---

## PASSO 4 — Restart do Sandbox Core

```bash
# Verificar PID actual
ps aux | grep "constitutional-agent" | grep -v grep

# Kill e restart (padrão nohup)
kill $(ps aux | grep constitutional-agent | grep -v grep | awk '{print $2}')
sleep 2

cd /opt/windi/agents/constitutional-agent
nohup python3 agent.py > /opt/windi/logs/agent-virtue.log 2>&1 &

# Verificar
sleep 3
curl -s http://localhost:8091/virtue/api/virtue-receipt/health
# Esperado: {"agent": "W-VIRTUE-001", "status": "GREEN", ...}
```

---

## PASSO 5 — Injetar Bottom Sheet G3 no Canvas

O ficheiro `endorsement-g3.html` contém 3 blocos: HTML + CSS + JS.

**Injetar o HTML antes do `</body>`:**
```bash
# Verificar linha do </body>
grep -n "</body>" /opt/windi/agent-palette/ui/index.html

# O bloco HTML vai ANTES do </body>
# O <style> vai no <head> (ou junto com os outros estilos)
# O <script> vai ANTES do </body>
```

**Estratégia mais segura — tudo junto antes do `</body>`:**
O ficheiro `endorsement-g3.html` pode ser injetado inteiro antes do `</body>`.
O browser processa `<style>` dentro do body normalmente.

---

## PASSO 6 — Verificar IDs e adaptar hooks

```bash
# Verificar se Canvas dispara evento custom ao abrir documento
grep -n "dispatchEvent\|CustomEvent\|document:loaded\|canvas:" \
  /opt/windi/agent-palette/ui/index.html | head -20

# Verificar tipo de documento .jmpg no Canvas
grep -n "jmpg\|doc\.type\|doc_type" \
  /opt/windi/agent-palette/ui/index.html | head -10
```

**Se o Canvas não dispara `canvas:document:loaded`:**
Localizar onde o Canvas carrega um documento e adicionar:
```javascript
document.dispatchEvent(new CustomEvent('canvas:document:loaded', {
  detail: { type: 'jmpg', id: receiptId }
}));
```

---

## PASSO 7 — Teste end-to-end

```bash
# 1. Smoke test do endpoint
curl -s -X POST http://localhost:8091/virtue/api/virtue-receipt \
  -H "Content-Type: application/json" \
  -H "X-WINDI-DID: DID:TEST:windi123" \
  -d '{"target_receipt_id": "WINDI-VERIFY-GENESIS-20260305", "action": "VALIDATE_SKILL"}'

# Esperado: {"success": true, "virtue_receipt_id": "...", ...}

# 2. Verificar recibo criado
curl -s http://localhost:8091/virtue/api/virtue-receipt/WINDI-VERIFY-GENESIS-20260305

# 3. Verificar DB
sqlite3 /opt/windi/data/virtue_receipts.db \
  "SELECT id, action, created_at FROM virtue_receipts LIMIT 5;"
```

---

## CHECKLIST

```
□ virtue_receipt_blueprint.py copiado para blueprints/
□ agent.py: import + register_blueprint adicionados
□ /opt/windi/data/ criado
□ Sandbox Core restartado
□ /virtue/api/virtue-receipt/health → GREEN
□ endorsement-g3.html injetado no Canvas index.html
□ Bottom Sheet visível em mobile (375px DevTools)
□ Smoke test POST virtue-receipt → 201
□ GET virtue-receipt/GENESIS → lista endossos
□ DID session: testar com header X-WINDI-DID
□ Stealth trigger activo (evento canvas:document:loaded)
```

---

## ARQUITECTURA COMPLETA

```
.jmpg aberto no Canvas
↓
canvas:document:loaded event
↓
WindiStealthTrigger detecta
↓
EndorsementEngine.openFor(id)
↓
Bottom Sheet abre (estado: verifying)
↓
GET /verify-public/?id=X  (stealth)
↓
Verificado → estado: ready
↓
Humano toca botão (One-Tap)
↓
EndorsementEngine.castVirtue(action)
↓
POST /virtue/api/virtue-receipt
↓
W-VIRTUE-001 valida DID session
↓
SQLite local + Forensic Ledger (:8101)
↓
Receipt of Virtue imutável
↓
UI estado: success → auto-close
```

---

*Canvas Gen 7 — One-Tap Endorsement — 13 Mar 2026*
