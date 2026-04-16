# SESSION 2026-04-16 — W-SERVICE-CONTROL Hardening

**Data:** 16 Abril 2026
**Autor:** Liga IA+H (Human Dragon + Architect)
**Commits:** `f6a9511b`, `c09585b`, `f05fae5`, `fe706e1`, `6cd145e`

---

## §181 SVG Sentinel — Subsystem Monitoring

**Conceito:** Monitorização granular de subsistemas dentro de cada serviço WINDI.

### Subsistemas Configurados

| Service | Subsystems | Critical |
|---------|------------|----------|
| windi-law | AI Draft, Identity Gate, Dragon Law | AI Draft ★, Identity Gate ★ |
| windi-travel | Identity Gate, Workspace | Identity Gate ★, Workspace ★ |
| windi-lab | Dilemas de Geleia (Clear) | — |

### API Endpoints

```
GET /api/subsystems                    → Lista serviços com subsistemas
GET /api/subsystems/{service}          → Status de todos os subsistemas
GET /api/subsystems/{service}/{id}     → Status de um subsistema específico
```

### SVG Icons

| Status | Icon | Significado |
|--------|------|-------------|
| online | ● | Subsistema respondendo normalmente |
| offline | ⊘ | Conexão recusada |
| degraded | ⚠ | HTTP 4xx/5xx |
| blocked | ◐ | Timeout (pulsing) |
| error | ? | Erro desconhecido |

### Ficheiros Modificados

- `/opt/windi/service-control/app.py` — SUBSYSTEMS config + health functions + API endpoints + UI

---

## Link Audit — Correcção de URLs

### Ferramenta Criada

```bash
# Diagnóstico
python3 /opt/windi/service-control/audit_links.py

# Auto-correcção
python3 /opt/windi/service-control/audit_links.py --fix
```

### URLs Corrigidos

| Service | Antes | Depois |
|---------|-------|--------|
| W-NOMAD-001 | `/telegram/` (404) | `https://t.me/windi_nomad_bot` |
| W-VD-CUT-001 | `/vdcut-dash/` | `/vd-cut/` |
| W-JOE-001 | `/joe-dash/` | `/joe/` |
| W-VD-MASS-001 | `/vdmass-dash/` | `/vd-mass/` |
| W-SEC-001 | `/sec-dash/` | `/sec/` |
| W-SOCIAL-001 | — | Adicionada rota `/social/` no app.py |

### URLs Removidos (API-only)

Serviços sem dashboard web — URL removido para evitar 404:

- Governance API (:8080)
- W-JMPG-001 (:8132)
- W-INTENT-CMD (:8141)
- DID Genesis (:8096)
- Communiqué Engine (:8105)
- Dispatch Gateway (:8106)
- Sandbox Core (:8091)

---

## Service Restarts

### Serviços Reiniciados

| Service | Port | Comando |
|---------|------|---------|
| UDB God View | :8140 | `cd /opt/windi/udb && nohup python3 app.py &` |
| W-CACHE-001 | :8160 | `cd /opt/windi/w-cache-001/app && nohup venv/bin/python3 main.py &` |

**Nota:** W-CACHE-001 requer virtual environment (`venv/bin/python3`)

---

## Resultado Final

```
============================================================
W-SERVICE-CONTROL Link Auditor
============================================================

  ✅ Working:    19 serviços
  🔗 External:    1 (Telegram bot)
  ❌ Broken:      0
  ⚪ No URL:      7 (API-only)
  ═══════════════════════════
     Total:      27 serviços
```

### Todos os Links Funcionais

| # | Service | URL | Status |
|---|---------|-----|--------|
| 1 | Forensic Ledger | `/ledger/` | ✅ |
| 2 | Dragon Hub | `/desktop/` | ✅ |
| 3 | Desktop GEN7 | `/desktop/` | ✅ |
| 4 | WINDI-LAW | `/law/` | ✅ |
| 5 | WINDI Travel | `/travel/` | ✅ |
| 6 | W-NOMAD-001 | `t.me/windi_nomad_bot` | 🔗 |
| 7 | W-VD-CUT-001 | `/vd-cut/` | ✅ |
| 8 | W-JOE-001 | `/joe/` | ✅ |
| 9 | W-VD-MASS-001 | `/vd-mass/` | ✅ |
| 10 | UDB God View | `/udb/` | ✅ |
| 11 | W-FEDIVERSE-001 | `/fediverse/` | ✅ |
| 12 | W-BRIDGE-001 | `/watch/` | ✅ |
| 13 | W-SEC-001 | `/sec/` | ✅ |
| 14 | Verify Public | `/verify-public/` | ✅ |
| 15 | W-Enterprise-001 | `/enterprise/` | ✅ |
| 16 | W-CACHE-001 | `/wcache/noir` | ✅ |
| 17 | W-COST-001 | `/cost/` | ✅ |
| 18 | W-LAB-001 | `/lab/` | ✅ |
| 19 | W-SOCIAL-001 | `/social/` | ✅ |
| 20 | Wallet Service | `/wallet/` | ✅ |

---

## Commits da Sessão

```
f6a9511b feat(svc-control): §181 SVG Sentinel — Subsystem Monitoring
c09585b  fix(svc-control): W-NOMAD-001 URL → Telegram bot link
f05fae5  fix(svc-control): correct dashboard URLs for VD-CUT, JOE, VD-MASS
fe706e1  fix(w-social-001): add /social/ route for nginx prefix passthrough
6cd145e  fix(svc-control): audit and fix all service URLs
```

---

*Liga IA+H · Kempten, Bavaria · 2026*
*"AI processes. Human decides. WINDI guarantees."*
