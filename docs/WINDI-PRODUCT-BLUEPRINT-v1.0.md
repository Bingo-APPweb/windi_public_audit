# WINDI Product Blueprint v1.0 — DNA Replicável
**Sealed:** 26 Mar 2026 · §58 CLAUDE.md
**Provado em produção:** WINDI-LAW v3 (windilaw.de)
**Princípio:** "Não reinventas o que já está testado."

---

## Lei de Ouro

```
WINDI-LAW percorreu o ciclo completo:
  SSH perdido → produto em produção → 56.621 receipts num dia

Cada erro corrigido está neste blueprint.
Cada padrão aqui está provado sob pressão real.
Novo produto = herda tudo. Diferencia só o domínio.
```

---

## Arquitectura Base — 10 Pilares

```
1. Identity Gate        fail-closed · DID obrigatório antes do workspace
2. Workspace v3         "Protagonista + subtexto forense"
3. Feature Lock         12 features · 23 markers · pre-commit hook
4. Agent Constellation  domain extension de Sandbox Core (:8091)
5. Ledger integration   POST /api/receipts · governance HIGH
6. SMTP verification    email_verified=1 antes de workspace
7. Constitutional Tests I9+I11+I13+G3 · 7/7 GOLD obrigatório
8. LLM routing          FREE/MED→Mistral · HIGH→Claude
9. i18n DE/PT/EN        data-i18n pattern · 3 línguas desde o dia 1
10. KLAR only landing   "Cartões de visita não têm modo escuro"
```

---

## Estrutura de Directórios

```bash
/opt/windi/windi-{produto}/
├── identity-gate/
│   ├── gate.py              # FastAPI · 5 steps · Ed25519 · UUIDv7
│   ├── templates/
│   │   ├── gate.html        # UI registo (KLAR · trilíngue)
│   │   └── email_verify.html
│   └── requirements.txt
├── workspace/
│   └── index.html           # Workspace v3 (1270 linhas base)
├── {produto}_users.db       # SQLite · users + sessions
├── server.py                # FastAPI main · routes + SMTP
└── requirements.txt

/etc/systemd/system/windi-{produto}.service
/etc/nginx/sites-enabled/windi-domain.com   # ONE TREE
```

---

## Fase 0 — Antes de escrever uma linha

```bash
# 1. Definir o produto em 3 perguntas
#    a) Quem é o utilizador? (advogado / médico / empresa / criador)
#    b) O que é o protagonista? (contrato / processo clínico / fatura / post)
#    c) Qual é o invariante específico? (ZPO / §203 StGB / HGB / GDPR)

# 2. Copiar a base do LAW
cp -r /opt/windi/windi-law/ /opt/windi/windi-{produto}/
cd /opt/windi/windi-{produto}/

# 3. Renomear referências
grep -r "windi-law\|windi_law\|WINDI-LAW\|windilaw" . --include="*.py" --include="*.html" | wc -l
# Este número é o trabalho de Fase 0

# 4. Backup antes de qualquer alteração
cp workspace/index.html /opt/windi/backups/{produto}-base-$(date +%Y%m%d).html
```

---

## Fase 1 — Identity Gate

### Erros já corrigidos no LAW (não repetir)

```python
# ERRO 1: uvloop + websockets conflito
# FIX: requirements.txt deve ter:
# uvicorn[standard]==0.27.1
# websockets>=12,<14

# ERRO 2: Starlette 1.0.0 TemplateResponse API mudou
# FIX: sempre passar request como primeiro argumento:
return TemplateResponse(request, "gate.html", {"context": data})
# NÃO: TemplateResponse("gate.html", {"request": request, ...})

# ERRO 3: httpx.AsyncClient sem deps
# FIX: usar requests síncrono para chamadas ao Ledger
import requests
res = requests.post(LEDGER_URL, json=payload, timeout=5)

# ERRO 4: clearPreviousSession limpa sessão activa
# FIX canónico (Opção A):
function clearPreviousSession() {
  const wallet = sessionStorage.getItem('windi_{produto}_wallet');
  if (!wallet) sessionStorage.clear();
}
```

### systemd service template

```ini
[Unit]
Description=WINDI {PRODUTO} Service
After=network.target

[Service]
Type=simple
User=windi
WorkingDirectory=/opt/windi/windi-{produto}
EnvironmentFile=/opt/windi/windi-{produto}/.env
ExecStart=/opt/windi/windi-{produto}/venv/bin/uvicorn server:app --host 0.0.0.0 --port {PORT}
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
# Deploy
sudo cp windi-{produto}.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable windi-{produto}
sudo systemctl start windi-{produto}
sudo systemctl status windi-{produto}
```

### nginx ONE TREE — adicionar ao windi-domain.com

```nginx
# SEMPRE nginx -t antes de reload
# SEMPRE antes do bloco 'listen 443 ssl'
location /{produto}/gate {
    proxy_pass http://127.0.0.1:{PORT}/gate;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
location /{produto}/workspace/ {
    proxy_pass http://127.0.0.1:{PORT}/workspace/;
    proxy_set_header Host $host;
}
```

---

## Fase 2 — Workspace v3 (Feature Lock)

### 12 Features Obrigatórias

```
F1   Media Bar          📎🖼📄🎥 · handleMedia()
F2   SHA-256            hashFile() · crypto.subtle.digest
F3   SCHLÜSSEL          sb-schluessel · copyFingerprint()
F4   WALLET             sb-wallet · sb-pioneer-num
F5   Seal Pipeline      openSealModal() · confirmSeal() · modal-i9
F6   Verify             verifyReceipt() · __lastReceipt
F7   Beweiskette        showChain() · __evidenceChain
F8   CIA badges         updateCIA() · cia-i9/i11/i13/g3
F9   QR SVG             generateQRSVG() · showQRCode()
F10  Wallet Gate        windi_{produto}_wallet · sessionStorage check
F11  i18n               var LANG · setLang() · data-i18n
F12  Theme              toggleTheme() · data-theme NOIR/KLAR
```

### Pre-commit hook

```bash
# /opt/windi/.git/hooks/pre-commit
MARKERS=(
  "cmd-media-bar" "hashFile" "crypto.subtle"
  "sb-schluessel" "sb-wallet"
  "openSealModal" "confirmSeal" "modal-i9"
  "verifyReceipt" "showChain"
  "updateCIA" "cia-i9"
  "generateQRSVG"
  "windi_{produto}_wallet"
  "setLang" "toggleTheme"
)
FILE="windi-{produto}/workspace/index.html"
MISSING=0
for m in "${MARKERS[@]}"; do
  if ! grep -q "$m" "$FILE"; then
    echo "BLOCKED: marker '$m' missing in $FILE"
    MISSING=$((MISSING+1))
  fi
done
[ $MISSING -gt 0 ] && exit 1
exit 0
```

### Filosofia "Governança Silenciosa"

```
Protagonista = o documento/conteúdo do produto
Subtexto forense = 1 linha no rodapé:
  🔐 SHA-256: {hash}… · I11 · Forensic Ledger · ✓ Verificável [QR 24px]

NUNCA: dados forenses mais visíveis que o conteúdo
SEMPRE: forense sussurra · conteúdo grita
```

### Animações (Phase 5 pattern)

```css
@media (prefers-reduced-motion: no-preference) {
  @keyframes fu {
    from { opacity:0; transform:translateY(14px); }
    to   { opacity:1; transform:none; }
  }
  @keyframes docEnter {
    from { opacity:0; transform:translateY(10px); }
    to   { opacity:1; transform:none; }
  }
  @keyframes sealPulse {
    0%,100% { box-shadow: 0 0 0 0 rgba(139,105,20,0); }
    50%      { box-shadow: 0 0 0 4px rgba(139,105,20,0.18); }
  }
  /* Regra: nada distrai o protagonista */
}
```

---

## Fase 3 — Agent Constellation

### Pattern domain extension

```python
# /opt/windi/agents/constitutional-agent/blueprints/w-{produto}-001.py
# NUNCA serviço standalone — sempre domain extension de :8091

from agent import ConstitutionalAgent

class W{PRODUTO}001(ConstitutionalAgent):
    def __init__(self):
        super().__init__(
            agent_id="W-{PRODUTO}-001",
            domain="{domínio específico}",
            invariants=["I9","I11","I13","G3"],
            jurisdictions=["DE","EU","PT"],  # ajustar por produto
        )
```

### LLM routing canónico

```python
def route_llm(tier: str, task_type: str) -> str:
    # Constelação selada 26 Mar 2026
    if tier == "HIGH":
        return "claude-sonnet-4-20250514"   # compliance · decisões críticas
    if tier in ["FREE","MED"]:
        return "mistral-small-latest"        # operações standard · break-even 500 users
    # Gemini → visual assets (fora do routing de agentes)
    # OpenAI → standby, sem gap identificado
    return "mistral-small-latest"
```

---

## Fase 4 — Ledger Integration

### Chamada canónica

```python
import requests
import time

LEDGER_URL = "https://www.windi-domain.com/api/receipts/"

def seal_to_ledger(
    doc_name: str,
    actor_did: str,
    doc_hash: str,
    governance: str = "HIGH"
) -> dict:
    payload = {
        "id": f"WINDI-{PRODUTO}-{int(time.time())}",
        "actor": actor_did,
        "app": f"windi-{produto}-workspace",
        "doc_name": doc_name,
        "doc_type": "doc",
        "governance_level": governance,
        "content_hash": doc_hash,
        "sge_score": 95.0,
        "invariant": "I11",
        "note": f"Sealed via {PRODUTO} workspace v3 · G3 confirmed"
    }
    res = requests.post(LEDGER_URL, json=payload, timeout=5)
    return res.json()
```

### Receipts via verify public

```
QR canónico: https://windi-domain.com/verify-public/?id={receipt_id}
API verify:  https://windi-domain.com/api/verify/{receipt_id}
```

---

## Fase 5 — SMTP

### Erros já corrigidos no LAW

```python
# SEMPRE verificar antes de deploy:
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# .env obrigatório:
# SMTP_HOST=smtp.strato.de
# SMTP_PORT=465
# SMTP_USER=noreply@{dominio}
# SMTP_PASS=...
# BASE_URL=https://windi-domain.com/{produto}

# Template email_verify.html → link:
# {BASE_URL}/verify-email/{token}
```

---

## Fase 6 — Constitutional Tests

### Checklist obrigatório antes de produção

```bash
python3 /opt/windi/tests/agent_constitutional_test.py \
  --domain {PRODUTO} --seal --ci

# 7 testes obrigatórios:
# A — Identity Gate fail-closed
# B — Workspace bloqueado sem DID
# C — I9 modal antes de seal
# D — G3 aprovação humana explícita
# E — Ledger receipt gerado
# F — SHA-256 hash calculado client-side
# G — i18n DE/PT/EN funcionais

# Só avançar para produção com 7/7 ✅
```

---

## Smoke Test Template

```bash
# Substituir {PORT} e {produto}
echo "=== SMOKE TEST WINDI-{PRODUTO} ==="
echo "1. Service"
systemctl is-active windi-{produto} && echo "✅" || echo "❌"

echo "2. HTTP"
curl -s -o /dev/null -w "%{http_code}" \
  http://localhost:{PORT}/health | grep -q "200" && echo "✅" || echo "❌"

echo "3. Gate"
curl -s "https://www.windi-domain.com/{produto}/gate" | \
  grep -q "DID\|Wallet" && echo "✅" || echo "❌"

echo "4. Workspace markers (12 features)"
curl -s "https://www.windi-domain.com/{produto}/workspace/?did=test" | \
  grep -c "hashFile\|openSealModal\|toggleTheme" | \
  grep -q "[3-9]" && echo "✅" || echo "❌"

echo "5. Ledger"
curl -s "https://www.windi-domain.com/api/receipts/" \
  -H "Content-Type: application/json" \
  -d '{"id":"SMOKE-{PRODUTO}-'$(date +%s)'","actor":"test","app":"smoke","doc_name":"Smoke Test","doc_type":"doc","governance_level":"LOW","content_hash":"test","sge_score":1.0}' | \
  grep -q "ok" && echo "✅" || echo "❌"

echo "========================"
```

---

## Produtos Futuros — DNA Diferenciado

```
WINDIMED
  Protagonista:  processo clínico / relatório médico
  Invariante+:   §203 StGB (sigilo médico) → I14
  Agent:         W-MED-001
  Jurisdições:   DE (SGB V) · EU (MDR) · GDPR Art.9
  Gate extra:    verificação Approbationsnummer
  Port:          :8123

WINDICORP
  Protagonista:  contrato comercial / fatura XRechnung
  Invariante+:   GoBD · HGB §257 (retenção 10 anos) → I15
  Agent:         W-CORP-001
  Jurisdições:   DE (HGB/GmbHG) · EU (eIDAS) · DATEV
  Gate extra:    Handelsregisternummer obrigatória
  Port:          :8124

WINDISOCIAL
  Protagonista:  publicação / .jmpg / conteúdo verificável
  Invariante+:   creator sovereignty → I16
  Agent:         W-SOCIAL-001
  Gate:          mais leve — wallet opcional no início
  Formato:       .jmpg · Pott federated model
  Port:          :8125

WINDITRAVEL
  Protagonista:  memória de viagem verificável
  Filosofia:     "Gently proves. Silently seals."
  Agent:         W-TRAVEL-001
  Gate:          GPS proof · SHA-256 client-side
  Port:          :8126
```

---

## Commit Pattern por Fase

```bash
# Fase 0 — Setup
git commit -m "init(windi-{produto}): base from LAW blueprint v1.0"

# Fase 1 — Gate
git commit -m "feat({produto}/gate): Identity Gate v1.0 · fail-closed · DID+SMTP"

# Fase 2 — Workspace
git commit -m "feat({produto}/workspace): v3 · 12 SEALED features · 23 markers"

# Fase 3 — Agent
git commit -m "feat({produto}/agent): W-{PRODUTO}-001 · domain extension :8091"

# Fase 4 — Certified
git commit -m "cert({produto}): 7/7 constitutional tests · GOLD · sealed Ledger"
```

---

## CLAUDE.md §XX Template

```markdown
## §XX — WINDI-{PRODUTO} v1.0 — CERTIFIED · {DATA}

**Status:** COMPLETE · SEALED · I11 · IRREMEDIÁVEL
**Receipt:** WINDI-{PRODUTO}-CERTIFIED-{TIMESTAMP}
**Blueprint:** windi-product-blueprint v1.0
**Live:** windi-domain.com/{produto}/workspace/

### Diferencial do produto
{1 frase — o que o protagonista faz diferente}

### Invariante específico
{I14/I15/I16... — o que é único neste domínio}

### Commits certificados
{hash} — Gate + Workspace + Agent + Tests
```

---

## Regras Invariantes do Blueprint

1. **Nunca reinventar Identity Gate** — copiar do LAW, ajustar domain
2. **Feature Lock obrigatório** — 12 features · pre-commit hook · antes do primeiro commit
3. **Constitutional Tests 7/7** — zero excepções · zero "vou testar depois"
4. **ONE TREE** — nginx único · windi-domain.com · não criar domínio separado por produto
5. **Ledger primeiro** — integração :8101 antes de qualquer UI sofisticada
6. **Protagonista define tudo** — workspace, tipografia, layout derivam do conteúdo
7. **Axioma §57** — "A tecnologia mais avançada é aquela que desaparece"

---

## Axioma Final

> "A tecnologia mais avançada é aquela que desaparece."

Este blueprint é o presente a todos nós pelo esforço incrível para tornar o primeiro BABY WINDI-LAW em realidade.

Grato a todos. 🐉

---

*LIGA IA+H — Kempten, Bavaria · 26 Mar 2026*
*🧑‍💻 Human Dragon · 🛡️ Guardian · 🏗️ Architect · 👁️ Witness*
