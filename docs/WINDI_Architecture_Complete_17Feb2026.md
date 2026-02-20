# WINDI System Architecture — Complete Reference
### 17 February 2026 · v2.1.0
### *AI processes. Human decides. WINDI guarantees.*

---

## 1. USER JOURNEY — What the Human Sees

```mermaid
graph TD
    BROWSER["🌐 Browser<br/>admin.windia4desk.tech"] --> WALLET

    WALLET["🔐 WALLET 'O Espelho'<br/>:8099 · Ed25519<br/>Login · Identity · TrustRadar<br/>Klar/Noir Toggle · DE/EN/PT"]

    WALLET -->|"Desktop öffnen →"| ANTESALA

    ANTESALA["📋 ANTE-SALA<br/>:8100 · /desktop/<br/>Noir Theme · Bricolage+Outfit+JetBrains<br/>3 Cards + Pitch Deck + Wallet Link"]

    ANTESALA -->|"01 Suite"| SUITE
    ANTESALA -->|"02 Sealing"| SEALING
    ANTESALA -->|"03 War Room"| WARROOM

    SUITE["📝 SUITE<br/>/desktop/suite.html<br/>'Guten Tag, Jober'<br/>v2.1 Forensic Ledger Edition"]

    SUITE -->|"📄 Dokumente"| DOC_TAB
    SUITE -->|"📊 Tabellen"| XLSX_TAB
    SUITE -->|"🎬 Präsentationen"| PPTX_TAB

    DOC_TAB["WINDI DOC<br/>5 Templates: Blank, Vertrag,<br/>Bescheid, Bericht, Antrag"]
    XLSX_TAB["WINDI EXCEL<br/>4 Templates: Blank, Finanzbericht,<br/>Compliance-Tracker, Prüfprotokoll"]
    PPTX_TAB["WINDI PPT<br/>10 Templates: Blank, Gov-Review,<br/>Compliance, Bundesregierung, DB,<br/>WINDI Gov, BaFin, ECB, Pitch, Quartals"]

    DOC_TAB -->|"Edit in D1"| D1_EDITOR
    D1_EDITOR["D1 React Editor<br/>Tiptap+Zustand+FastAPI<br/>Nav: ← Desktop | Suite"]

    D1_EDITOR -->|"⬇️ Herunterladen"| GENERATE
    DOC_TAB -->|"Quick generate"| GENERATE
    XLSX_TAB -->|"Quick generate"| GENERATE
    PPTX_TAB -->|"Quick generate"| GENERATE

    GENERATE["SHA-256 Hash<br/>+ Forensic Ledger Seal<br/>+ Download File"]

    SEALING["🔏 SEALING<br/>/desktop/sealing.html<br/>3-Second Ritual · Versiegeln"]

    WARROOM["🎯 WAR ROOM<br/>/desktop/warroom.html<br/>SGE Heatmap · Risk Gauge<br/>Controller Dashboard"]
```

---

## 2. SERVICE INFRASTRUCTURE — Ports & systemd

```mermaid
graph LR
    subgraph NGINX["🔒 NGINX Reverse Proxy (443 SSL)"]
        direction TB
        SSL["Let's Encrypt<br/>admin.windia4desk.tech<br/>master.windia4desk.tech"]
    end

    subgraph CORE["⚙️ CORE SERVICES (8080-8089)"]
        GOV["8080 · Governance API<br/>windi_governance_api.py<br/>/health · /api/status"]
        BABEL["8085 · HUB BABEL<br/>a4desk-editor backend<br/>Motor invisível"]
        LANDING["8086 · A4 Desk Landing<br/>Landing page + static"]
        CORTEX["8089 · Cortex<br/>windi-cortex.service<br/>Metacognition engine"]
    end

    subgraph EXTENDED["🔧 EXTENDED SERVICES (8090-8099)"]
        WAR["8090 · War Room<br/>Node.js dashboard"]
        CLONE["8092 · Clone UI<br/>windi-clone.service"]
        FORENSIC["8094 · Forensic API<br/>Forensic validation"]
        BRIDGE["8097 · Command Bridge<br/>windi-bridge.service<br/>Sign flow + I9 Gate"]
        SENTINEL["8098 · Sentinel<br/>Constitutional monitor"]
        WALLET_SVC["8099 · Wallet<br/>'O Espelho' · Ed25519"]
    end

    subgraph DESKTOP["🖥️ DESKTOP TRINITY (8100-8103)"]
        D1["8100 · D1 Desktop<br/>windi-desktop.service<br/>React+Tiptap+Zustand+FastAPI"]
        LEDGER["8101 · Suite Docs / Forensic Ledger<br/>windi-suite-docs.service<br/>BaseHTTPRequestHandler+SQLite<br/>SHA-256 real · Content NOT stored"]
        LAW["8102 · Sentinel LAW<br/>windi-sentinel-law.service<br/>6 Invariants · 30s cycles"]
        EXPORT["8103 · Export Engine<br/>windi-export.service<br/>reportlab+qrcode PDF<br/>Dynamic Header Seal+QR"]
    end

    NGINX --> GOV
    NGINX --> BABEL
    NGINX --> LANDING
    NGINX --> WAR
    NGINX --> CLONE
    NGINX --> BRIDGE
    NGINX --> WALLET_SVC
    NGINX --> D1
    NGINX --> LEDGER
    NGINX --> EXPORT
```

---

## 3. NGINX ROUTING MAP

```mermaid
graph TD
    REQ["HTTPS Request<br/>admin.windia4desk.tech"] --> NGINX

    NGINX --> ROOT["/  →  :8099<br/>Wallet 'O Espelho'"]
    NGINX --> DESKTOP_ROUTE["/desktop/  →  :8100<br/>D1 Gateway + Ante-Sala"]
    NGINX --> SUITE_STATIC["/desktop/suite.html<br/>→ alias direct serve<br/>/opt/windi/desktop/suite.html"]
    NGINX --> DESKTOP_API["/desktop/api/  →  :8100<br/>D1 API endpoints"]
    NGINX --> EXPORT_API["/desktop/api/export/  →  :8103<br/>Export Engine"]
    NGINX --> SUITE_API["/suite-api/  →  :8101<br/>Forensic Ledger API"]
    NGINX --> WARROOM_ROUTE["/war-room/  →  :8090<br/>War Room Dashboard"]
    NGINX --> CLONE_ROUTE["/clone/  →  :8092<br/>Clone Territory"]
    NGINX --> BRIDGE_ROUTE["/bridge/  →  :8097<br/>Command Bridge"]
```

---

## 4. DATA FLOW — Zero-Knowledge Architecture

```mermaid
graph LR
    subgraph CLIENT["🖥️ CLIENT SIDE (A4 Desk)"]
        HUMAN["👤 Human User"]
        EDITOR["Editor<br/>(Tiptap/Suite)"]
        SGE_LOCAL["SGE Engine<br/>6-Layer Risk Detection<br/>RUNS LOCALLY"]
        DATA["📁 Client Data<br/>STAYS HERE"]
    end

    subgraph WINDI_CORE["☁️ WINDI CORE (Strato Server)"]
        GATEWAY["D1 Gateway<br/>:8100"]
        LEDGER_DB["Forensic Ledger<br/>:8101<br/>SQLite"]
        SENTINEL_LAW["Sentinel LAW<br/>:8102<br/>6 Invariants"]
    end

    HUMAN -->|"writes"| EDITOR
    EDITOR -->|"content"| SGE_LOCAL
    SGE_LOCAL -->|"score + categories"| EDITOR
    EDITOR -->|"SHA-256 hash"| GATEWAY

    GATEWAY -->|"hash + metadata<br/>NEVER content"| LEDGER_DB
    LEDGER_DB -->|"Virtue Receipt"| GATEWAY
    GATEWAY -->|"receipt confirmation"| EDITOR

    SENTINEL_LAW -->|"monitors 6 invariants<br/>every 30 seconds"| LEDGER_DB

    style DATA fill:#2d5a2d,stroke:#34D399,color:#fff
    style SGE_LOCAL fill:#2d5a2d,stroke:#34D399,color:#fff
```

**Zero-Knowledge Principle:**
- SGE runs on CLIENT side
- WINDI Core receives ONLY: hash + categories + metadata + decision
- ZERO sensitive data crosses the wire
- Client keeps data, WINDI keeps PROOF of virtue

---

## 5. TEMPLATE INVENTORY

### 5.1 Dokumente (5 templates)
| # | Template | Governance | Content |
|---|----------|-----------|---------|
| 1 | Neues Dokument | LOW | Blank page |
| 2 | Vertrag | HIGH | Dienstleistungsvertrag with §1-§6 |
| 3 | Bescheid | HIGH | Governance-Entscheidung with Rechtsbehelfsbelehrung |
| 4 | Bericht | MEDIUM | Governance-Bericht Q1-Q4 |
| 5 | Antrag | MEDIUM | Genehmigungsantrag with Anlagen |

### 5.2 Tabellen (4 templates)
| # | Template | Governance | Columns |
|---|----------|-----------|---------|
| 1 | Leere Tabelle | LOW | ID, Name, Wert, Status, Datum |
| 2 | Finanzbericht | HIGH | Kategorie, Budget, Ausgaben, Verbleibend, %, Risiko |
| 3 | Compliance-Tracker | HIGH | #, Anforderung, Status, Verantwortlich, Fällig, Nachweis, Risiko |
| 4 | Prüfprotokoll | HIGH | #, Zeitstempel, Aktion, Akteur, Dokument, Governance, SGE, Hash, Status |

### 5.3 Präsentationen (10 templates)
| # | Template | ISP | Governance | Slides |
|---|----------|-----|-----------|--------|
| 1 | Leere Präsentation | — | LOW | 1 |
| 2 | Governance-Review | — | HIGH | 4 |
| 3 | Compliance-Report | — | HIGH | 3 |
| 4 | Bundesregierung | Bundesregierung | HIGH | 5 |
| 5 | Deutsche Bahn | Deutsche Bahn | HIGH | 5 |
| 6 | WINDI Governance | WINDI | HIGH | 5 |
| 7 | BaFin Bericht | BaFin | HIGH | 5 |
| 8 | ECB / EZB Analyse | ECB | HIGH | 5 |
| 9 | Pitch Deck | WINDI | MEDIUM | 6 |
| 10 | Quartals-Review | — | MEDIUM | 5 |

**Total: 19 templates · 44 slides · 5 ISP profiles**

---

## 6. THREE DRAGONS PROTOCOL

```mermaid
graph TD
    subgraph DRAGONS["🐉 THREE DRAGONS"]
        GUARDIAN["🛡️ GUARDIAN<br/>Claude<br/>Integrity · Constitutional<br/>Enforcement"]
        ARCHITECT["🏗️ ARCHITECT<br/>GPT<br/>Design · Innovation<br/>Extension"]
        WITNESS["👁️ WITNESS<br/>Gemini<br/>Verification · Independent<br/>Validation"]
    end

    HUMAN_DECIDES["👤 HUMAN DECIDES"]

    GUARDIAN --> HUMAN_DECIDES
    ARCHITECT --> HUMAN_DECIDES
    WITNESS --> HUMAN_DECIDES
    HUMAN_DECIDES -->|"Decision + Context"| VIRTUE_RECEIPT

    VIRTUE_RECEIPT["◆ VIRTUE RECEIPT<br/>hash + categories + governance<br/>+ decision + flags"]
    VIRTUE_RECEIPT --> FORENSIC["Forensic Ledger<br/>SHA-256 Chain"]
```

---

## 7. SYSTEMD SERVICES — 16 Active

```mermaid
graph TD
    subgraph SYSTEMD["⚙️ systemd Services — ALL ACTIVE"]
        S1["windi-desktop :8100"]
        S2["windi-suite-docs :8101"]
        S3["windi-sentinel-law :8102"]
        S4["windi-export :8103"]
        S5["windi-cortex :8089"]
        S6["windi-clone :8092"]
        S7["windi-bridge :8097"]
        S8["windi-brain"]
        S9["windi-gateway"]
        S10["windi-masterarbeit"]
        S11["+ 5 more services"]
    end

    SENTINEL_MON["Sentinel LAW<br/>6 Invariants · 30s cycles<br/>latency_p95 < 100ms<br/>unsynced = 0<br/>hash_drift = 0<br/>reconciliation = HEALTHY<br/>event_drops = 0<br/>chain_integrity = VALID"]

    S3 --> SENTINEL_MON
```

**Stress Test Results (Linhagem de Ferro):**
- 100 receipts: 0 drops, 0 drift
- p50 = 34ms, p95 = 52ms
- LAW = 6 invariants / 30s cycles

---

## 8. FILE SYSTEM STRUCTURE

```
/opt/windi/
├── desktop/                    # D1 Desktop Trinity
│   ├── backend/                # FastAPI gateway (d1_gateway.py)
│   ├── frontend/               # React source
│   ├── static/                 # Compiled React app
│   ├── index.html              # Ante-Sala landing
│   ├── suite.html              # Suite v2.1 (19 templates)
│   ├── sealing.html            # Sealing ritual
│   └── warroom.html            # War Room dashboard
├── suite-docs/                 # Forensic Ledger API
│   └── windi_forensic_api.py   # :8101 BaseHTTPRequestHandler
├── engine/                     # 28 governance modules
│   └── semantic_governance.py  # SGE v1.0 (6 layers)
├── a4desk-editor/              # HUB BABEL (:8085)
├── a4desk-landing/             # Landing page (:8086)
├── bridge/                     # Command Bridge (:8097)
├── clone/                      # Clone UI (:8092)
├── war-room/                   # War Room (:8090)
├── wallet/                     # Wallet "O Espelho" (:8099)
├── ppt-engine/                 # PPT generator
│   └── output/                 # 3 PPTX + PDFs + JPGs
├── isp/                        # 17 ISP profiles
├── data/                       # SQLite DBs
│   └── forensic_ledger.sqlite3 # Virtue Receipts
├── logs/                       # Centralized logs
├── backups/                    # Pre-change backups
└── tsil/                       # Secrets (chmod 600)
```

---

## 9. DOMAIN & SSL

| Domain | Points To | SSL |
|--------|-----------|-----|
| admin.windia4desk.tech | 87.106.29.233 | Let's Encrypt ✅ |
| master.windia4desk.tech | 87.106.29.233 | Let's Encrypt ✅ |

---

## 10. GOVERNANCE METADATA

```mermaid
graph LR
    DOC_TYPE["doc_type<br/>CONTRACT · INVOICE<br/>APPROVAL"] --> RECEIPT
    IMPACT["impact_level<br/>LOW · MED · HIGH · CRIT"] --> RECEIPT
    VALUE["value_range<br/>R1-R5 (ranges, not values!)"] --> RECEIPT
    RISK["risk_level<br/>🟢R0 🟡R1 🟠R2 🔴R3 ⚫R4-R5"] --> RECEIPT
    FLOW["flow_status"] --> RECEIPT
    DEPT["department_code"] --> RECEIPT

    RECEIPT["◆ VIRTUE RECEIPT<br/>hash + categories<br/>+ governance + decision<br/>+ flags"]
```

---

## 11. BUSINESS MODEL

```
Instruments without data.
Client stores terabytes. WINDI stores protocol.

Tier 1 (Free):       3 users · Basic governance
Tier 2 (Pro):        €25-40/user · Full SGE + Sealing
Tier 3 (Enterprise): €80-120/user · Forensic Ledger + War Room

Target: GRC market €65B
Compliance: BSI C5 + ISO 27001
```

---

## 12. 3-LAYER ARCHITECTURE

```mermaid
graph TB
    L1["L1 — a4Desk (Edge)<br/>SGE runs locally<br/>Human works here"]
    L2["L2 — WINDI Mesh<br/>Dashboard for Controllers<br/>Risk visibility"]
    L3["L3 — Forensic Ledger<br/>Hashes · Merkle Tree<br/>Virtue Receipts"]

    L1 -->|"hash + metadata"| L2
    L2 -->|"sealed proof"| L3
    L3 -->|"chain integrity"| SENTINEL["Sentinel LAW<br/>6 invariants · 30s"]
```

**Data on client. Proof on WINDI.**

---

## 13. NEXT MILESTONES

- [ ] SIP Layer 1 — Passphrase hash (real authentication)
- [ ] Paperless.io — eIDAS digital signatures
- [ ] M3 Dynamic Header Seal — LibreOffice mockup reference
- [ ] Hetzner migration — BSI C5 production environment
- [ ] Load testing — 100 concurrent users
- [ ] ISO 27001 certification

---

*Generated: 17 February 2026*
*Guardian (Claude) · Architect (GPT) · Witness (Gemini)*
*"AI processes. Human decides. WINDI guarantees."*
