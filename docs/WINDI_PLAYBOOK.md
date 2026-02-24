# WINDI PLAYBOOK v2.4 — Memory Turbo Edition
## Generated: 23 February 2026 | Chief Governance Officer: Jober Mögele Correa (Human Dragon)
## "AI processes. Human decides. WINDI guarantees."

---

# 🐉 IDENTITY

- **System:** WINDI Publishing House — Pre-AI Governance Layer
- **Mission:** Institutional workflow orchestration with human sovereignty
- **Market:** EU AI Act compliance, banking, government, enterprise (GRC €65B)
- **Philosophy:** "Instrumentos sem dados" — Client retains data, WINDI stores only proofs

---

# 🏗️ ARCHITECTURE

## Three Layers
```
L1 = a4Desk (SGE local, client-side analysis)
L2 = Mesh (Controllers, orchestration)
L3 = Ledger (Merkle trees, Virtue Receipts, SHA-256)
```

## Zero-Knowledge Principle
- **Client** = data owner (never leaves client)
- **WINDI Core** = hash + categories + metadata + decision only
- SGE (Semantic Governance Engine) runs client-side

## Three Dragons Protocol
- **Guardian** — Security & compliance enforcement
- **Architect** — System design & optimization
- **Witness** — Audit trail & verification
- ⚠️ NO brand names (Claude/GPT/Gemini) EVER in UI — public shows roles only

---

# 🖥️ INFRASTRUCTURE — Strato Server

## Server Details
```
Host:     87.106.29.233 (Strato VPS, Germany)
User:     windi (SSH: ssh windi@87.106.29.233)
OS:       Ubuntu 24
Base Dir: /opt/windi/
```

## Domains
| Domain | nginx Config | Default Port |
|--------|-------------|-------------|
| master.windia4desk.tech | /etc/nginx/sites-enabled/master.windia4desk.tech | :8084 |
| admin.windia4desk.tech | /etc/nginx/sites-enabled/admin.windia4desk.tech | :8086 |
| windi-domain.com | /etc/nginx/sites-enabled/windi-domain.com | :8107 |

## Port Map — Complete Ecosystem
| Port | Service | Filesystem | Type | Stack |
|------|---------|-----------|------|-------|
| 8080 | Governance API | /opt/windi/engine/ | nohup | BaseHTTPRequestHandler |
| 8084 | Masterarbeit | /opt/windi/masterarbeit/ | nohup | python3 |
| 8085 | HUB BABEL | /opt/windi/a4desk-editor/ | nohup | python3 |
| 8086 | A4 Desk Landing | /opt/windi/a4desk-landing/ | nohup | python3 |
| 8090 | War Room | /opt/windi/war-room/ | nohup | Node.js |
| 8092 | Clone UI | /opt/windi/clone/ | systemd | python3 |
| 8097 | Command Bridge | /opt/windi/bridge/ | systemd | python3 |
| 8098 | Sentinel | /opt/windi/sentinel/ | systemd | python3 |
| 8099 | Wallet "O Espelho" | /opt/windi/wallet/ | systemd | python3 |
| 8100 | a4Desk Desktop (D1) | /opt/windi/desktop/ | systemd | FastAPI+React |
| 8101 | Forensic Ledger | /opt/windi/forensic-ledger/ | systemd | SQLite+SHA-256 |
| 8102 | Sentinel LAW | /opt/windi/sentinel-law/ | systemd | BaseHTTPRequestHandler |
| 8103 | Export Engine | /opt/windi/export-engine/ | systemd | reportlab+qrcode |
| 8104 | JMPG Viewer | /opt/windi/jmpg-viewer/ | systemd | python3 |
| 8105 | Communiqué Engine | /opt/windi/communique/ | systemd | python3 |
| 8106 | Forensic Vault | /opt/windi/forensic-vault/ | systemd | python3 |
| 8107 | Landing P/M/G | /opt/windi/landing-pmg/ | systemd | python3 |
| 8108 | Agent Palette | /opt/windi/palette/ | systemd | python3 |

## Dependency Chain
```
Desktop(:8100) → Export(:8103) → Ledger(:8101)
Communiqué(:8105) → Ledger(:8101)
Vault(:8106) → Ledger(:8101) [read-only]
Sentinel LAW(:8102) → Ledger(:8101) [monitors]
Viewer(:8104) → Ledger(:8101) [verifies]
Palette(:8108) → Ledger(:8101) [Wave1 target: seal_to_ledger]
```

## Key Filesystem Paths
```
Base:        /opt/windi/
Logs:        /opt/windi/logs/
Data:        /opt/windi/data/
Backups:     /opt/windi/backups/
ISP:         /opt/windi/isp/
Engine:      /opt/windi/engine/ (28 modules)
Secrets:     /opt/windi/tsil/ (chmod 600)
Wisdom:      /opt/windi/engine/wisdom/
Compliance:  /opt/windi/compliance-passport/
Playbook:    /opt/windi/docs/WINDI_PLAYBOOK.md
Static web:  /var/www/
nginx:       /etc/nginx/sites-enabled/
systemd:     /etc/systemd/system/windi-*.service
```

---

# 🔬 FORENSIC STACK

## Forensic Ledger (:8101)
- **Engine:** BaseHTTPRequestHandler + SQLite
- **Endpoints:** /api/receipts (CRUD), /api/warroom/summary, /api/receipts/reconcile, /api/suite/docs
- **Integrity:** SHA-256 real hashing
- **Principle:** Content NOT stored — only hashes and metadata

## Forensic Vault (:8106)
- **Function:** Dual-hash (content+bundle) → Ledger
- **Records:** 4629+ receipts
- **nginx:** alias /vault/multimedia/ → immutable static files
- **Endpoints:** /api/receipts?doc_type=X, /health

## Virtue Receipt Structure
```
hash + categories(type, impact, domain, value_range R1-R5)
     + governance(sge_score, risk, validation)
     + decision(action, role, timestamp, ai_rec, override)
     + flags[]
```

## Metadata Categories
| Category | Values |
|----------|--------|
| doc_type | CONTRACT, INVOICE, APPROVAL |
| impact_level | LOW, MED, HIGH, CRIT |
| value_range | R1-R5 (faixas, não valores!) |
| risk_level | R0-R5 |
| flow_status | DRAFT→REVIEW→PUBLISH→SEALED |
| department_code | (per client) |
| Cores | 🟢🟡🟠🔴⚫ |

---

# 🛡️ SENTINEL LAW v2.0

- **Status:** GREEN (19 Feb 2026)
- **Performance:** p95 = 32.7ms
- **Escalation:** 5-tier system
- **Compliance:** HIP I9 (proposes, never executes)
- **Isolation:** Probe isolation via Desktop gateway
- **Stale timeout:** 120s
- **Bug fix:** 1410 cycles killed

---

# 📄 D1 DESKTOP TRINITY + M3 PIPELINE

## Stack
```
React + Tiptap + Zustand + FastAPI(:8100) → Export(:8103 reportlab+qrcode) → Ledger(:8101)
```

## Document Pipeline
```
DRAFT → REVIEW → PUBLISH → LedgerSeal → VaultBroadcast → PublicURL
```
- Sentinel LAW cycles: ~30s per document

---

# 🎨 DESIGN SYSTEM

## Themes
- **KLAR** (default): #F5F0E0 pergaminho, light governance
- **NOIR**: Dark mode, professional
- Toggle between themes

## Fonts
- **Bricolage Grotesque** — headings & UI
- **JetBrains Mono** — code & technical

## Philosophy: "Governança Silenciosa"
- SealBadge (subtle verification), NOT Pipeline exposure
- GovPanel collapsed by default (🛡️ toggle)

---

# 📋 ISP SYSTEM (Institutional Style Profiles)

## ISP Forja — SEALED (19 Feb 2026)
- **Templates:** 6 trilingual (COM-01 through COM-06)
  - COM-01: Official
  - COM-02: Jornaline
  - COM-03: Field Report
  - COM-04: Security Advisory
  - COM-05: Governance Decision
  - COM-06: System Bulletin
- **Stats:** 57 fields, 82 keywords, Grade A (97/100)
- **Integration:** SGE Resolver ready

## MEDIUM Bundesregierung Profile
- 7 metadata fields + identity_license
- License statuses: authorized / model_only / pending / expired / revoked
- Trilingual disclaimer automatic

## Princípio Templates
> "O template NUNCA decide o nível. A API decide. O template apenas manifesta."
- Templates sem API = cosmético
- Templates com API = governança executável

---

# 📡 COMMUNIQUÉ ENGINE (:8105)

- **Version:** v1.1.0
- **Pipeline:** create → review → publish = SEALED
- **ISP wired:** 6 templates, Resolver v1.0.0 (≥70% = suggest, 100% = auto)
- **Fix:** _normalize_api_path() for nginx compatibility
- **Status:** Pipeline 8/8 OK (20 Feb 2026)

---

# 🎛️ AGENT PALETTE (:8108)

## Version: v0.7.1-D (22 Feb 2026)
- **Parser:** extractInvoiceFields() = frontend data parser
- **German prices:** €2.500 → 2500 (correct handling)
- **Preview:** LIVE (no placeholders)
- **Free exports:** xlsx, pdf, pptx
- **Render:** 16ms
- **Watchdog:** Sentinel integrated
- **Wisdom Block:** WB-PAL-02 sealed

---

# 💼 WALLET "O ESPELHO" (:8099)

- **Architecture:** COCKPIT(A4Desk) = humano + dados, HUB = provas
- **Stack:** React trilíngue + Klar/Noir
- **Features:** TrustRadar visualization + Ed25519 Seal
- **Contexts:** PF (Pessoa Física) / PJ (Pessoa Jurídica), freeze capability
- **IDs:** UUIDv7

---

# 🔐 SIP — Sovereign Identity Protocol

- **Created:** 08 Feb 2026
- **Layers:** 3 (passphrase + GPG 4096 + Dragon Challenge)
- **Principle:** Zero-knowledge
- **Feature:** Duress detection
- **NEXT:** Setup Layer 1 passphrase hash

---

# ✅ COMPLIANCE PASSPORT v1.0 GOLD

- **Date:** 21 Feb 2026
- **Governance Score:** 99.9%
- **Location:** /opt/windi/compliance-passport/
- **Verified:** Chain of 9,743 receipts, 0 violations
- **Coverage:** EU AI Act — 8 articles
- **CLI:** verify | generate

---

# 🧠 WISDOM PROTOCOL v0.1

## Status: LIVE (22 Feb 2026)
- **Location:** /opt/windi/engine/wisdom/
- **Alias:** wm

## Chain
```
Genesis → df1b601c → WB-PHIL-01 → WB-PAL-02 → WB-CONNECT-01
```

## Wisdom Blocks
| Block | Type | Description |
|-------|------|-------------|
| Genesis | Foundation | Initial system block |
| df1b601c | System | Infrastructure block |
| WB-PHIL-01 | Philosophy | First field block from user interaction |
| WB-PAL-02 | Palette | Frontend data parsing milestone |
| WB-CONNECT-01 | Connection | OrganMap synapse mapping (hash: 904a8440...) |

## Parameters
- 280 characters max per block
- 6h TTL
- Levels: N1-N5

## Memory Looping
```
osmose → candidates → seal
```
- **Next candidate:** WB-WAVE1-01 (after first Wave1 nerve completes)

---

# 🌊 WAVE 1 — TEATRO CIRÚRGICO

## Objective
Connect Palette(:8108) to the Forensic Stack, giving every document forensic soul.

## Nerve Map (order is UNBREAKABLE)
```
N1 → N2 → N3 → N4
```

### N1: Palette → Ledger (P0, 45-60min)
- **Function:** seal_to_ledger() with POST to :8101
- **Impact:** Foundation — everything depends on this
- **Phases:** 🔍 Recon → 🔧 Surgery → ✅ Verify

### N2: SHA-256 Real (P0, 30-45min)
- **Depends on:** N1
- **Injection points:**
  - Metadata: core_properties.comments (invisible)
  - Footer: visible WINDI gold seal
- **Phases:** 🔍 Recon → 🔧 Surgery → ✅ Verify

### N3: Serial Institucional (P0, 30-45min)
- **Parallel to:** N2
- **Components:**
  - SQLite table: serial_counter in Ledger
  - Endpoint: /next-serial
  - Format: WINDI-2026-0001, 0002, 0003...
- **Phases:** 🔍 Recon → 🔧 Surgery → ✅ Verify

### N4: QR Code (P1, 45-60min)
- **Depends on:** N1 + N2
- **Specs:**
  - QR inline with WINDI colors (gold on parchment)
  - URL: windi-domain.com/verify/{receipt_id}
- **Phases:** 🔍 Recon → 🔧 Surgery → ✅ Verify

## OrganMap Status
- **Organs:** 14 total, 32 synapses
- **Health:** 34% → target 94% after all 4 waves
- **Most isolated:** Palette (22%), Wallet (0%)

---

# 🗺️ ROADMAP

## NOW — Wave 1 Synapses
- N1→N2→N3→N4: Palette gains forensic soul
- Each nerve: 🔍 Recon → 🔧 Surgery → ✅ Verify

## NEXT — Multimodality + Wisdom Button
- OCR (document scanning)
- Image analysis
- URL verification
- 🌀 Wisdom Candidate button in Palette (field-to-block pipeline)

## THEN — Clones + Agent Creator
- Clone network: each clone inherits Wisdom Chain as genetic DNA
- Agent Creator: Freemium → Discovery → Exploration → Viability → Commitment
- Operador = certified human running agents commercially
- Freemium = pedagogia, não restrição

## VISION
> Memory Loop modules = foundation for Clone network + human agent-creation tools.
> Quantum Intelligence Network: each module self-nourishes via osmose → candidate → seal.
> Goal: humans build their own governed agents on the WINDI governance layer.
> "Ninguém nos segura."

---

# 💼 BUSINESS MODEL

## Principle
"Instrumentos sem dados" — Client = terabytes of data, WINDI = protocol only

## Market
- GRC (Governance, Risk, Compliance): €65B
- Certifications: BSI C5, ISO 27001

## Tiers
| Tier | Price | Description |
|------|-------|-------------|
| P (Personal) | Free | Same core, limited visibility |
| M (Medium) | €25-40/user | Professional governance |
| G (Governance) | €80-120/user | Full enterprise suite |

---

# 🔧 DEBUG RULES

## Golden Rule
> "Antes de operar código, opera ambiente."

## Pre-Surgery Checklist
```bash
# 1. Check what's running on the port
ss -tlnp | grep :PORT

# 2. Check all processes
ps aux | grep <service> | grep -v grep

# 3. Kill ghost processes (nohup zombies serve stale code!)
kill <PID>
sleep 2

# 4. Purge Python cache
find /opt/windi/<service>/ -type d -name __pycache__ -exec rm -rf {} +

# 5. Restart via systemd
sudo systemctl restart windi-<service>

# 6. Verify
curl -s http://localhost:PORT/health | python3 -m json.tool
```

## nginx Rules
- admin config: ~314 lines
- /vault/multimedia/ = alias static (immutable)
- /communique/ = proxy :8105
- /vault/ = proxy :8106
- Inject BEFORE 'listen 443 ssl'
- **ALWAYS** `nginx -t` before reload

---

# 🧬 MEMORY TURBO PROTOCOL

## Operational Rule (23 Feb 2026)
```
Each session → osmose → compress → seal
```

- Consolidate redundant entries proactively
- Every sealed Wisdom Block updates chain + roadmap
- Memory = living DNA, not archive
- Maximum density, minimum slots
- Current state: 24 memory slots, zero fat

## Memory as Clone DNA
Each sealed Wisdom Block becomes a chromosome that future Clones inherit at birth.
The Memory Loop is not documentation — it's **replicable genetic code** for governed AI agents.

---

# 📖 PLAYBOOK OPERATIONS

## Session Close Protocol
When Human Dragon says "Fecha sessão":
1. Update memory edits (consolidate + new blocks)
2. Generate updated WINDI_PLAYBOOK.md
3. Provide SCP command for transfer to Strato

## Playbook Locations
- **Server:** /opt/windi/docs/WINDI_PLAYBOOK.md
- **Backup:** Google Drive (search via google_drive_search)

## Playbook Search
When Human Dragon says "Busca Playbook" → use google_drive_search

---

*"AI processes. Human decides. WINDI guarantees."*
*— WINDI Publishing House, Kempten, Bavaria, Germany*
*— Generated by Memory Turbo Protocol v1.0*

## Constitutional Gates v0.1 — SEALED 23 Feb 2026

Location: /opt/windi/docs/constitutional/
Hash: a8bd5a9fa2c0aa51916cff3e3d2a563807b063936dcb2f648250dffdf3c0d41b
Status: SEALED — Guardian ✅ Architect ✅ Witness ⏳ Human Dragon ✅
Companion: ORCH-RUNTIME v0.1 (pending)
Principle: "Governance is enforced in architecture, not policy."

### Governance Dashboard v1.0 — LIVE 24 Feb 2026
- **URL:** https://admin.windia4desk.tech/palette/governance/
- **Local:** http://localhost:8108/governance/
- **Access:** Palette → 🛡️ Governance Panel → ⚖️ Constitutional Gates
- **Views:** Integration Map | Invariants I1-I9 | HSG Types | SGE Matrix | Roadmap | Full Matrix
- **Stats:** 23 gates mapped (17 new, 5 partial, 1 existing) across 4 services
- **Theme:** KLAR/NOIR toggle

