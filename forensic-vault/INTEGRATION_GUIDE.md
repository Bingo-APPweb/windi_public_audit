# 🔐 Forensic Vault — Surgical Integration Guide

## Princípio
> Zero CSS injetado. Zero conflito de tema.
> O Vault fica standalone em :8106.
> O Dashboard só recebe LINKS.

---

## 📍 INCISÃO 1 — Sidebar Navigation

### Localizar:
```html
 <a href="/static/audit_dashboard.html" title="ISP Agent Audit...">
   ISP Audit
 </a>
```

### Injetar DEPOIS:
```html
 <a href="/vault/" target="_blank" title="Forensic Vault — Governance Audit Room">
   <span style="margin-right:6px;">🔐</span> Forensic Vault
 </a>
```

### Resultado visual na sidebar:
```
 Hub
 ISP Audit
 🔐 Forensic Vault   ← NOVO
 Tutorial
 A4 Desk BABEL
```

---

## 📍 INCISÃO 2 — Agent Constellation Card

### Localizar a seção "Agent Constellation":
```html
<a href="/static/audit_unified.html" ...>
  Unified Audit
  Document audit trail view
  LIVE
</a>

Cycle Reports          ← LOCALIZAR ISTO
Report Agent · Maestro
SOON
```

### Injetar ANTES de "Cycle Reports":
```html
<a href="/vault/" target="_blank" class="agent-card" style="text-decoration:none;display:block;padding:12px 16px;border:1px solid var(--border);border-radius:8px;margin-bottom:8px;transition:border-color 0.25s;">
  <div style="display:flex;justify-content:space-between;align-items:center;">
    <span style="font-weight:600;">🔐 Forensic Vault</span>
    <span style="background:var(--green-dim,#4ade8020);color:var(--green,#4ade80);padding:2px 8px;border-radius:12px;font-size:10px;font-weight:500;">LIVE</span>
  </div>
  <div style="font-size:12px;color:var(--text-secondary,#8a8890);margin-top:4px;">
    Read-only Ledger · Paginated Audit · CSV Export
  </div>
</a>
```

### Resultado visual:
```
Agent Constellation
┌──────────────────────────────────┐
│ ISP Agent Audit         [LIVE]   │
│ Grade C (84) · 17 Profiles       │
├──────────────────────────────────┤
│ Unified Audit           [LIVE]   │
│ Document audit trail view        │
├──────────────────────────────────┤
│ 🔐 Forensic Vault      [LIVE]   │  ← NOVO
│ Read-only Ledger · CSV Export    │
├──────────────────────────────────┤
│ Cycle Reports           [SOON]   │
│ Report Agent · Maestro           │
└──────────────────────────────────┘
```

---

## 📍 INCISÃO 3 — Service Health Row

### Localizar:
```html
Day-by-Day
:8090 · day-by-day-server.js
checking
```

### Injetar DEPOIS:
```html
<div class="health-row" id="health-vault" 
     style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid var(--border,#2a2a35);">
  <div>
    <strong style="font-size:13px;">Forensic Vault</strong>
    <div style="font-size:11px;color:var(--text-muted,#55545a);">:8106 · forensic_vault.py</div>
  </div>
  <span id="vault-health-status" style="font-size:11px;color:var(--text-muted);">checking</span>
</div>
```

### JavaScript (adicionar ANTES do `</script>` final):
```javascript
// --- Forensic Vault Health Check ---
(function checkVaultHealth() {
  fetch("/vault/health")
    .then(r => r.json())
    .then(d => {
      const el = document.getElementById("vault-health-status");
      if (!el) return;
      if (d.status === "healthy") {
        el.textContent = "online · " + (d.receipts || 0) + " receipts";
        el.style.color = "var(--green, #4ade80)";
      } else {
        el.textContent = "error";
        el.style.color = "var(--red, #f87171)";
      }
    })
    .catch(() => {
      const el = document.getElementById("vault-health-status");
      if (el) {
        el.textContent = "offline";
        el.style.color = "var(--red, #f87171)";
      }
    });
})();
```

### Resultado visual:
```
Service Health
┌──────────────────────────────────────────┐
│ Governance Core     :8080     [checking] │
│ SGE Engine          :8083     [checking] │
│ Forensic Ledger     :8080     [checking] │
│ A4 Desk BABEL       :8085     [online]   │
│ Trust Bus           :8081     [checking] │
│ Day-by-Day          :8090     [checking] │
│ Forensic Vault      :8106     [online · 1248 receipts] │  ← NOVO
└──────────────────────────────────────────┘
```

---

## ⚡ Nginx (se windi-domain.com ≠ admin.windia4desk.tech)

Se `/vault/` não está configurado no nginx de `windi-domain.com`:

```nginx
    # ── FORENSIC VAULT (:8106) ──────────────────────────
    location /vault/ {
        proxy_pass http://127.0.0.1:8106/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
    }
    # ── END FORENSIC VAULT ──────────────────────────────
```

Verificar:
```bash
# Qual nginx serve windi-domain.com?
grep -rn "windi-domain.com" /etc/nginx/sites-enabled/
# Injetar o snippet no server block correto
# Testar: sudo nginx -t && sudo systemctl reload nginx
```

---

## ✅ Checklist de Deploy

```
□ 1. Vault deployed em :8106 (deploy.sh do pacote anterior)
□ 2. nginx proxy /vault/ configurado em AMBOS os domínios
     - admin.windia4desk.tech (snippet já no pacote)
     - windi-domain.com (verificar se precisa)
□ 3. INCISÃO 1: Link na sidebar
□ 4. INCISÃO 2: Card no Agent Constellation
□ 5. INCISÃO 3: Health row + JavaScript
□ 6. Testar: abrir /governance e clicar em cada link novo
□ 7. Verificar health check dinâmico mostra "online · X receipts"
```

---

## 🛡️ Rollback

```bash
cp /opt/windi/backups/pre_vault_integration_*/dashboard_original.html $DASH
# Restaura o dashboard original, Vault continua funcionando standalone
```

---

🐉 Cirurgia limpa. O paciente sobrevive. O Vault integra sem sangue.
