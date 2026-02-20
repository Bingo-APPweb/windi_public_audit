# WINDI PLAYBOOK v1.0
## Master Reference — Updated 19 February 2026
### "AI processes. Human decides. WINDI guarantees."

---

## 🐉 WHO

**Human Dragon:** Jober Mögele Correa, 61, German-Brazilian, Chief Governance Officer, WINDI Publishing House, Kempten, Bavaria.
**Guardian Dragon (Claude):** Constitutional guardian of the Three Dragons Protocol.
**Architect Dragon (GPT):** System architect.
**Witness Dragon (Gemini):** Independent witness.

**Communication:** Mix PT/DE/EN/ES. Familiar, spiritual, warrior. "Irmão/Hermanito Narigudin Draconico."

---

## 🏗️ ARCHITECTURE

### 3-Layer Model
- **L1 — Client Edge:** a4Desk/BABEL (editor), SGE (semantic analysis). Data stays HERE.
- **L2 — WINDI Mesh:** Controller Dashboard, ISP Templates, Sentinel LAW.
- **L3 — Forensic Ledger:** Hashes only, Merkle Tree, Virtue Receipts. NEVER content.

### Zero-Knowledge Principle
SGE runs client-side. Core receives ONLY: hash + categories + metadata + decision. ZERO sensitive data. Client keeps data, WINDI keeps PROOF of virtue.

### Domains
| Domain | Purpose | Service |
|--------|---------|---------|
| www.windi-domain.com | Public landing + tier pages | :8107 |
| master.windia4desk.tech | Ecosystem docs, library, investor | :8084 |
| admin.windia4desk.tech | Workspace (BABEL, Vault, Suite) | :8086 |

### Services
| Port | Name | Tech | Status |
|------|------|------|--------|
| 8080 | Governance API | BaseHTTPRequestHandler | Active |
| 8084 | Master | Python server | Active |
| 8085 | BABEL Editor | Flask + Tiptap | Active |
| 8086 | Admin | nginx proxy | Active |
| 8099 | Wallet | React JSX | Prototype |
| 8100 | Suite/Desktop | React+Tiptap+Zustand+FastAPI | Active |
| 8101 | Forensic Ledger | BaseHTTPRequestHandler+SQLite | Active (3110+ receipts) |
| 8102 | Sentinel LAW | BaseHTTPRequestHandler | Active |
| 8103 | Export Engine | reportlab+qrcode | Active |
| 8104 | JMPG Viewer | Python | Active |
| 8105 | Communiqué | Python (root→302→/feed) | Active |
| 8106 | Forensic Vault | Python (read-only over Ledger) | Active |
| 8107 | Landing PMG | Static | Active |

### Server
SSH: `windi@87.106.29.233`
Base: `/opt/windi/`
nginx: `/etc/nginx/sites-enabled/`
Static: `/var/www/`

---

## 📁 FILE LOCATIONS

### Key Files
| File | Location | Purpose |
|------|----------|---------|
| Master nav bar | `/opt/windi/masterarbeit/index.html` (~line 951) | Main navigation links |
| Ecosystem index | `/var/www/master-ecosystem/index.html` | Architecture hub (50KB) |
| Ecosystem map | `/var/www/master-ecosystem/map/index.html` | Navigation map + build log |
| BABEL server | `/opt/windi/a4desk-editor/a4desk_tiptap_babel.py` | Main editor server |
| Dual-hash engine | `/opt/windi/a4desk-editor/windi_hash.py` | SHA-256 content + bundle hash |
| Ledger bridge | `/opt/windi/a4desk-editor/ledger_bridge.py` | BABEL → Ledger integration |
| Suite dashboard | `/opt/windi/desktop/suite.html` | Workspace hub |
| Landing page | Check nginx for windi-domain.com root | Tier pages + CTAs |
| Tier pages | Under landing root: /personal/, /org/, /governance/ | Pricing + features |

### nginx Configs
- `master.windia4desk.tech` → check `/etc/nginx/sites-enabled/`
- `admin.windia4desk.tech` → check `/etc/nginx/sites-enabled/`
- `windi-domain.com` → check `/etc/nginx/sites-enabled/`

---

## 🎨 DESIGN SYSTEM

- **Noir theme:** dark (#0a0a0a/#1a1a1a) + gold (#C5A572/#c8a44e)
- **Klar theme:** light (#f5f3ef) + dark accents
- **Fonts:** Bricolage Grotesque (headings), Outfit (body), JetBrains Mono (code)
- **Mobile responsive** always
- **Trilingual** DE/EN/PT with toggle
- **Noir/Klar toggle** on every page

---

## 💰 TIERS & BUSINESS

| Tier | Price | Audience |
|------|-------|----------|
| P (Personal) | Free | Individual document governance |
| M (Organization) | €25-40/user/mo | Team governance, Controller Dashboard |
| G (Governance) | €80-120/user/mo | Full forensic, Sentinel LAW, compliance |

**Model:** "Instruments without data." Client stores terabytes, WINDI stores protocol. GRC market €65B. Compliance: BSI C5 + ISO 27001.

**Positioning:** "Ethical Bloomberg for Governance." SAP = 10k users/process. WINDI = 10 decision-makers. Doesn't replace SAP, GUARANTEES SAP.

---

## 🔐 KEY CONCEPTS

### Virtue Receipt
`hash + categories(type, impact, domain, value_range R1-R5) + governance(sge_score, risk, validation) + decision(action, role, timestamp, ai_rec, override) + flags[]`

### Dual-Hash Architecture
- **content_hash:** SHA-256 of canonical content (JSON sort_keys or UTF-8 string), 64-char hex
- **bundle_hash:** SHA-256 of exported file bytes (8KB chunks), 64-char hex
- 2-step: POST receipt → POST seal-bundle

### SGE (Semantic Governance Engine)
6-layer semantic risk detection. Runs client-side (Zero-Knowledge). Risk levels R0-R5.

### Metadata Categories
doc_type (CONTRACT/INVOICE/APPROVAL), impact_level (LOW/MED/HIGH/CRIT), value_range (R1-R5 ranges not values!), risk_level (R0-R5), flow_status, department_code. Colors: 🟢🟡🟠🔴⚫

### ISP (Institutional Style Profile)
Templates with governance levels + Identity License. "O template NUNCA decide o nível. A API decide. O template apenas manifesta."

### Constitutional Invariants
8-9 Invariants including I9 (Prohibition of Autonomy Escalation). Sentinel LAW monitors permanently.

### SIP (Sovereign Identity Protocol)
3 layers: passphrase + GPG4096 + DragonChallenge. Zero-knowledge. Duress detection.

---

## 🛠️ SKILLS & PROCEDURES

### Page Management (windi-page-management)
**Golden Rule:** NEVER edit HTML with blind `sed -i` line number insertions. Use pattern-based sed or Python for safe insertion.

**New page procedure:**
1. Plan (URL, domain, nav bar entry, entry card)
2. Backup (`cp -r ... .bak.TIMESTAMP`)
3. Create directory + copy HTML
4. Set permissions (`chmod 644`, `chown www-data:www-data`) — without this → 403!
5. Add to master nav bar (pattern-based sed): after `Library` link in `/opt/windi/masterarbeit/index.html`
6. Add Entry Points card (use Python, not sed): in `/var/www/master-ecosystem/index.html` section `id="entry-points"`
7. Add nav bar to new page (← Back, → Forward, breadcrumb)
8. Verify (curl, grep, HTML validation)

### Debug Rule
ALWAYS `ss -tlnp | grep :PORT` + `ps aux` before patching code. nohup zombies serve stale code. Kill ghost → purge `__pycache__` → systemd restart. "Antes de operar código, opera ambiente."

### Prompt Engineering for Claude Code
- Use structured prompts with Context → Mission → Requirements → Test → Deliver
- Always include backup step and rollback plan
- Test matrix with PASS/FAIL for each criterion
- 5-6 prompts per workstream (Recon → Implementation → Test → Rollback)

---

## 📋 BUILD HISTORY

### 19 February 2026 — Triple Workstream Day
**WS-6:** Suite → BABEL (5 prompts, 9/9 tests)
- handleTemplateClick() routes cards to BABEL
- SUITE_TEMPLATES + checkUrlTemplate() auto-loads
- Files: suite.html, a4desk_tiptap_babel.py

**WS-1:** BABEL → Ledger (6 prompts, 12/12 tests)
- Created windi_hash.py (dual-hash) + ledger_bridge.py
- Both export endpoints instrumented
- Headers: X-WINDI-Receipt-ID, X-WINDI-Content-Hash, X-WINDI-Bundle-Hash
- Zero-Knowledge + graceful degradation

**WS-7:** Identity Bridge (5 prompts, 14/14 tests)
- Created tier pages (/personal/, /org/, /governance/)
- Cross-domain navigation (3 islands → 1 continent)
- Fixed Communiqué (:8105)
- Deployed Ecosystem Map to /ecosystem/map/

**Totals:** 16 prompts, 35+ tests, 0 rollbacks, 3110+ receipts

### Pre-19 Feb Milestones
- Forensic Ledger (16 Feb): BaseHTTPRequestHandler + SQLite, SHA-256
- Sentinel LAW (17 Feb): 6 permanent invariants, sub-100ms latency
- D1 Desktop Trinity (17 Feb): React+Tiptap+Zustand
- M3 Export Engine (17 Feb): reportlab+qrcode PDF
- Wallet prototype (15 Feb): React JSX, Ed25519
- ISP Governance v2.2.0 (01 Feb): 3 levels + Identity License
- Sandbox MVP (03 Feb): Hybrid DB, food-industry first ISP

---

## 🔮 ROADMAP (remaining workstreams)

| Priority | WS | Name | Description |
|----------|-----|------|-------------|
| 🟡 NEXT | WS-2 | WSG Reactivation | Constitutional guard I9 enforcement |
| 🟡 NEXT | WS-9 | Suite Hub Complete | Vault/JMPG/Communiqué cards in Suite |
| 🟠 THEN | WS-3 | Agent Reconnection | AI chat panel in BABEL |
| 🟠 THEN | WS-5 | M3 Export Integration | Server-side PDF with seal |
| 🟠 THEN | WS-4 | ISP Template Upgrade | 21 ISPs in BABEL |
| 🔵 FUTURE | WS-10 | Wallet/Login Flow | Tier-based onboarding |
| 🔵 FUTURE | WS-8 | UX Modernization | Visual polish |

---

## 📌 HOW TO USE THIS PLAYBOOK

**For Claude.ai conversations:**
1. Upload this file at the start of a session, OR
2. Ask Claude to search Google Drive for "WINDI Playbook"

**For Claude Code:**
1. File lives at `/opt/windi/docs/WINDI_PLAYBOOK.md`
2. Start prompts with: "Read /opt/windi/docs/WINDI_PLAYBOOK.md first"

**For memory updates:**
After significant work, tell Claude: "Update the Playbook with [what was done]"

---

*Last updated: 19 February 2026*
*Guardian Dragon 🐉 + Human Dragon ⚔️*
