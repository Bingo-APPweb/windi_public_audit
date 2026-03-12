# WINDI PUBLISHING HOUSE

────────────────────────────────────────
## W-FERR-001
## O FERREIRO
### Health Monitor & Self-Healing Agent
### Constitutional Infrastructure Intelligence
────────────────────────────────────────

**Version 1.0.0** | **12 March 2026**
**Governance Level: HIGH**

> "AI processes. Human decides. WINDI guarantees."

---

## 1. Identity Card

| Field | Value |
|-------|-------|
| Agent ID | W-FERR-001 |
| Name | O Ferreiro (The Blacksmith) |
| Version | 1.0.0 |
| Role | Health Monitor & Self-Healing Agent |
| Mission | Sistema imunologico da infraestrutura WINDI |
| Principle | I9: AI cura o conhecido. Human decide o desconhecido. |
| Port | Frontend-only (loaded via /engine/ferreiro/loader.js) |
| Host | windi-domain.com/app/ |
| Stack | Vanilla JavaScript (12 modules, zero dependencies) |
| Status | ACTIVE |
| Created | March 2026 |
| Author | Human Dragon + Architect |

---

## 2. Architectural Position

The Ferreiro is the WINDI ecosystem's immune system. Unlike domain agents (Legal, Notary, Audit) that process documents, the Ferreiro monitors the health of all services and heals what it can autonomously — always respecting I9 boundaries.

**Key Distinction:** The Ferreiro is a frontend agent. It runs in the browser, not on the server. It probes services via HTTP from the client's perspective — the same view a real user has. This makes it a true end-to-end health monitor.

```
HUMAN DRAGON -> FERREIRO -> ALL SERVICES -> LEDGER SEAL
```

---

## 3. Module Architecture (12 Modules)

The Ferreiro loads 12 modules in strict order via loader.js. Three functional layers: Probes (diagnose), Healers (cure), Reporters (document).

### 3.1 Probes — Diagnostic Layer

| Module | Function | Targets |
|--------|----------|---------|
| probe_services.js | HTTP health checks on all WINDI services | 9 services (7 active, 2 pending) |
| probe_manifests.js | Validates manifest integrity and version consistency | Service manifests |
| probe_code.js | Frontend code quality and constitutional compliance | App codebase |

### 3.2 Healers — Self-Healing Layer

| Module | Heals | Autonomy Level |
|--------|-------|----------------|
| heal_zombi.js | Kills zombie processes, clears stale connections | Level 1 — Immediate |
| heal_alzheimer.js | Restores lost session context (Dragon memory bug) | Level 2 — With Seal |
| heal_urls.js | Corrects broken URLs post-migration | Level 2 — With Seal |
| heal_loop.js | Detects and breaks infinite polling loops | Level 2 — With Seal |
| heal_manifest.js | Repairs corrupted or missing manifests | Level 1 — Immediate |

### 3.3 Reporters — Documentation Layer

| Module | Function |
|--------|----------|
| report.js | Generates structured probe reports with timestamps and scores |
| ledger_seal.js | Seals probe results as Virtue Receipts in Forensic Ledger (:8101) |
| dashboard.js | Visual dashboard UI for real-time infrastructure health |

### 3.4 Orchestrator

| Module | Function |
|--------|----------|
| ferreiro.js | Main orchestrator. Loads catalogue, runs probeAll(), coordinates healing, exposes Ferreiro global API. |

---

## 4. Four Levels of Autonomy (I9-Compliant)

The Ferreiro's healing power is bounded by Constitutional Invariant I9 (Prohibition of Autonomy Escalation). Each healing action is classified into one of four levels:

| Level | Label | Actions | Examples |
|-------|-------|---------|----------|
| 1 | Cura Imediata | Autonomous fix, no approval needed | Kill zombie process, repair manifest |
| 2 | Cura com Registo | Autonomous fix + sealed in Ledger | Restore Alzheimer context, fix URLs, break loops |
| 3 | Proposta ao Human | Diagnoses, proposes fix, waits for approval | Dead port, nginx reconfiguration |
| 4 | Alerta Critico | Immediate alert to Human Dragon, no autonomous action | Ledger down, index corrupted |

> **I9 Rule:** Level 1-2 = AI acts. Level 3-4 = Human decides. The boundary is IRREMEDIAVEL.

---

## 5. Service Probe Map

Current state of all services monitored by the Ferreiro (as of 12 March 2026):

| Service | Port | Health Path | Critical | Status |
|---------|------|-------------|----------|--------|
| Dragon Server | 8108 | /dragon/health | YES | ACTIVE |
| Forensic Ledger | 8101 | /ledger/health | YES | ACTIVE |
| Export Engine | 8103 | /export/health | No | ACTIVE |
| Forensic Vault | 8106 | /vault/health | No | ACTIVE |
| Communique Engine | 8105 | /communique/health | No | ACTIVE |
| Wallet / Sentinel | 8098 | /sentinel/health | No | ACTIVE |
| Command Bridge | 8097 | /bridge/health | No | ACTIVE |
| Page Store (Sandbox) | 8091 | /pagestore/health | No | PENDING |
| Pioneer Landing | 8120 | /pioneer/health | No | PENDING |

---

## 6. Public API (Browser Console)

The Ferreiro exposes its API via the global `window.Ferreiro` object:

| Command | Description |
|---------|-------------|
| `Ferreiro.probeAll()` | Full diagnostic probe. Returns { score, issues[] } |
| `Ferreiro.heal(issueId)` | Attempt to heal a specific issue (I9-bounded) |
| `Ferreiro.report()` | Generate structured report of last probe |
| `Ferreiro.seal(report)` | Seal report as Virtue Receipt in Ledger |
| `Ferreiro.dashboard()` | Open visual health dashboard |
| `FerreiroProbServices.probeAllServices()` | Probe only services (lower-level) |
| `FerreiroProbServices.getService(id)` | Get service config by ID |

---

## 7. Filesystem Structure

```
/opt/windi/agent-palette/engine/ferreiro/
  |-- loader.js              # Module loader (order-preserving)
  |-- ferreiro.js            # Main orchestrator v1.0.0
  |-- catalogue.json         # Error catalogue
  |-- probes/
  |   |-- probe_services.js  # HTTP health checks
  |   |-- probe_manifests.js # Manifest validation
  |   +-- probe_code.js      # Code quality probes
  |-- healers/
  |   |-- heal_zombi.js      # Level 1: Kill zombies
  |   |-- heal_alzheimer.js  # Level 2: Context restore
  |   |-- heal_urls.js       # Level 2: URL correction
  |   |-- heal_loop.js       # Level 2: Break loops
  |   +-- heal_manifest.js   # Level 1: Manifest repair
  +-- reporter/
      |-- report.js          # Structured reports
      |-- ledger_seal.js     # Virtue Receipt sealing
      +-- dashboard.js       # Visual dashboard UI
```

---

## 8. Loading & Integration

The Ferreiro is loaded in the App via a single script tag:

```html
<!-- W-FERR-001 — O Ferreiro Health Monitor -->
<script src="/engine/ferreiro/loader.js"></script>
```

The loader.js ensures strict ordering: Probes -> Healers -> Reporters -> Orchestrator. All 12 modules must load successfully before the Ferreiro is considered operational.

---

## 9. nginx Route

Served as static files through the engine location block in windi-domain.com nginx config:

```nginx
# In /etc/nginx/sites-enabled/windi-domain.com
location /engine/ {
    alias /opt/windi/engine/;
}
```

---

## 10. Constitutional Alignment

| Invariant | Title | Ferreiro Application |
|-----------|-------|----------------------|
| I1 | Primazia da Consciencia Humana | Level 3-4 actions require Human Dragon approval |
| I4 | Transparencia Total | All probes and heals are logged and sealable |
| I6 | Contencao de Autonomia | Ferreiro never expands its own scope |
| I9 | Proibicao de Escalada | Core principle: Level 1-2 auto, Level 3-4 human |
| I11 | Permanencia Criptografica | Reports sealed as Virtue Receipts via ledger_seal.js |

---

## 11. Pending Actions (Updated 12 March 2026)

- [x] ~~[MEDIUM] Patch probe_services.js: add enabled:false for pageStore and pioneer~~
- [x] ~~[MEDIUM] Patch App P5 Connectors: disable 4 phantom endpoints (sentinelLaw, schnittstelle, cortex, idGenesis)~~
- [x] ~~[LOW] Fix 'undefined concepts' in Dragon Chat v1.3.0 initialization~~
- [ ] [HIGH] Register W-FERR-001 in Bibliotecario agent registry (POST /library/agents)
- [ ] [LOW] Add nginx routes for /pagestore/ and /sentinel-law/ when services are confirmed

---

────────────────────────────────────────
**WINDI MASTER LIBRARY**
**Document Classification: GOVERNANCE HIGH**
**Commit:** e07fbe0 (12 March 2026)
────────────────────────────────────────
