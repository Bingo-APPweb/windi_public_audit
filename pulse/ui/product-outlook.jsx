import { useState, useMemo } from "react";

const GOLD = "#C9A227";
const BG = "#0A0A11";
const CARD = "#111119";
const CARD2 = "#161620";
const BORDER = "#1E1E30";
const GREEN = "#22C55E";
const RED = "#EF4444";
const AMBER = "#F59E0B";
const BLUE = "#3B82F6";
const PURPLE = "#8B5CF6";
const PINK = "#EC4899";
const DIM = "#6B6B88";
const TEXT = "#E2E2EA";

// ═══════════════════════════════════════════════════════
// REAL DATA — Based on server diagnostics 24 Feb 2026
// ═══════════════════════════════════════════════════════

const FEATURES = [
  // ━━━ LAYER 1: DOCUMENT PRODUCTION ENGINES (The Industrial Core) ━━━
  {
    id: "D01", name: "PDF Export Engine",
    desc: "reportlab + qrcode. N2(SHA-256) → N3(serial WINDI-2026-XXXX) → N4(gold QR). systemd on :8103.",
    server: "deployed", palette: "declared", wired: false,
    serverPath: "/opt/windi/export-engine/", port: "8103",
    category: "production", priority: 1,
    gap: "Palette UI lists PDF format but fetch('/api/dragon/render') returns 404. Need: wire render button → Export Engine :8103",
  },
  {
    id: "D02", name: "DOCX Production",
    desc: "a4Desk BABEL editor + python-docx in Export Engine. Full template pipeline.",
    server: "deployed", palette: "declared", wired: false,
    serverPath: "/opt/windi/a4desk-editor/ + /opt/windi/export-engine/", port: "8085+8103",
    category: "production", priority: 1,
    gap: "Palette declares docx in tier formats but no route connects to BABEL/Export. Need: /api/palette/export/docx → :8103",
  },
  {
    id: "D03", name: "PPTX ISP Engine",
    desc: "Node.js pptxgenjs engine. 3 ISPs deployed: WINDI-Governance, Deutsche Bahn, Bundesregierung. Noir+Gold, Corporate Red, Federal Blue.",
    server: "deployed", palette: "declared", wired: false,
    serverPath: "/opt/windi/ppt-engine/", port: "none (CLI)",
    category: "production", priority: 1,
    gap: "Engine exists as CLI (node isp_ppt_engine.js). Palette declares pptx format. Need: HTTP wrapper service + /api/palette/export/pptx route. THIS IS THE MISSING PIECE.",
  },
  {
    id: "D04", name: "XLSX Spreadsheet Engine",
    desc: "Declared in Palette tier config (Pro+Enterprise) but NO engine exists on server.",
    server: "missing", palette: "declared", wired: false,
    serverPath: "—", port: "—",
    category: "production", priority: 2,
    gap: "Create openpyxl-based engine. Similar architecture to PDF Export. ISP-aware chart styling.",
  },
  {
    id: "D05", name: "JMPG Viewer/Export",
    desc: "JMPG format viewer. systemd service created but had startup issues.",
    server: "partial", palette: "declared", wired: false,
    serverPath: "/opt/windi/jmpg-viewer/ + /opt/windi/desktop/export/", port: "8104",
    category: "production", priority: 3,
    gap: "Fix systemd crash. Wire to Palette via /api/palette/export/jmpg",
  },

  // ━━━ LAYER 2: FORENSIC STACK (The Trust Layer) ━━━
  {
    id: "F01", name: "Forensic Ledger",
    desc: "SQLite + SHA-256 chain. 4629+ receipts. CRUD + warroom + reconcile. systemd :8101.",
    server: "deployed", palette: "not-present", wired: false,
    serverPath: "/opt/windi/forensic-ledger/", port: "8101",
    category: "forensic", priority: 1,
    gap: "Palette has ZERO connection to Ledger. Need: /api/palette/seal → hash content → create receipt → return WINDI-2026-XXXX serial",
  },
  {
    id: "F02", name: "Forensic Vault",
    desc: "Immutable multimedia storage. Dual-hash → Ledger. nginx alias serves static. HTTP 200 confirmed.",
    server: "deployed", palette: "not-present", wired: false,
    serverPath: "/opt/windi/forensic-vault/", port: "8106",
    category: "forensic", priority: 2,
    gap: "Palette cannot store sealed docs in Vault. Need: /api/palette/vault → dual-hash → Ledger receipt → immutable storage",
  },
  {
    id: "F03", name: "Wave1 Seal Pipeline (N1-N4)",
    desc: "Complete pipeline: render → serial → SHA-256+footer+meta → gold QR → ledger → download. SEALED 23 Feb.",
    server: "deployed", palette: "not-present", wired: false,
    serverPath: "/opt/windi/export-engine/ (integrated)", port: "8103",
    category: "forensic", priority: 1,
    gap: "Wave1 pipeline works for Desktop D1 (:8100) but NOT for Palette. Need: unified export route that triggers full N1→N4 chain",
  },
  {
    id: "F04", name: "Paperless.io Signature",
    desc: "Schnittstelle connector + Command Bridge. eIDAS legal signatures. OAuth2 + HMAC webhooks.",
    server: "deployed", palette: "not-present", wired: false,
    serverPath: "/opt/windi/tsil/schnittstelle.py + /opt/windi/bridge/", port: "8095+8097",
    category: "forensic", priority: 1,
    gap: "Major feature! Palette needs 'Sign Document' button → Command Bridge → Paperless.io → webhook → Virtue Receipt. Full legal seal flow.",
  },

  // ━━━ LAYER 3: INTELLIGENCE (The Brain) ━━━
  {
    id: "I01", name: "Dragon Server (LLM Brain)",
    desc: "Claude Sonnet via API. Three Dragons routing. Armadura de Seda. v0.7.2-D deployed.",
    server: "deployed", palette: "broken", wired: false,
    serverPath: "/opt/windi/agent-palette/agent_dragon_server.py", port: "8108",
    category: "intelligence", priority: 0,
    gap: "CRITICAL: /api/dragon/health returns 404! /api/dragon/chat returns 'Not found'. Dragon Server crashed or not running. Agent falls back to local responses only.",
  },
  {
    id: "I02", name: "Local Intelligence (Fallback)",
    desc: "34 JS functions: classifyInput, detectLang, extractEntities, parseIntent, agentThink, applyLayer7, renderDocTemplate, extractInvoiceFields.",
    server: "n/a", palette: "deployed", wired: true,
    serverPath: "inline in ui/index.html", port: "8108",
    category: "intelligence", priority: 0,
  },
  {
    id: "I03", name: "OCR / Multimodal",
    desc: "Tesseract 5.3.0 installed. Paperless Bridge v1.0 with AutoCat. UI button calls /api/multimodal/ocr.",
    server: "deployed", palette: "declared", wired: false,
    serverPath: "/opt/windi/ (tesseract installed)", port: "—",
    category: "intelligence", priority: 1,
    gap: "Palette UI calls fetch('/palette/api/multimodal/ocr') but NO backend handler. Need: OCR endpoint in Dragon Server or new service.",
  },
  {
    id: "I04", name: "URL Verification",
    desc: "Palette UI calls /api/multimodal/verify-url but no backend exists.",
    server: "missing", palette: "declared", wired: false,
    serverPath: "—", port: "—",
    category: "intelligence", priority: 3,
    gap: "Create URL verification handler. Fetch page → extract metadata → SGE risk analysis.",
  },
  {
    id: "I05", name: "Wisdom Chain",
    desc: "5 sealed blocks. Palette has WisdomBtn + fetch('/api/wisdom/candidate'). Engine on server.",
    server: "deployed", palette: "declared", wired: false,
    serverPath: "/opt/windi/engine/wisdom/", port: "—",
    category: "intelligence", priority: 2,
    gap: "WisdomBtn exists in UI. Backend endpoint not wired. Need: /api/wisdom/candidate handler + list/status endpoints.",
  },
  {
    id: "I06", name: "Product Identity Skill",
    desc: "Agent must know pricing (P=Free, M=€25-40, G=€80-120), privacy, DSGVO, business model.",
    server: "deployed", palette: "not-loaded", wired: false,
    serverPath: "/opt/windi/skills/core/product-identity/", port: "—",
    category: "intelligence", priority: 1,
    gap: "Skill file exists on server but Dragon Server doesn't load it. Agent can't answer 'Was kostet WINDI?' with authority.",
  },

  // ━━━ LAYER 4: GOVERNANCE (The Constitution) ━━━
  {
    id: "G01", name: "9 Invariants (I1-I9)",
    desc: "validateInvariants() runs on every response. I9 IRREMEDIABLE. Active in UI JS.",
    server: "n/a", palette: "deployed", wired: true,
    serverPath: "inline", port: "8108",
    category: "governance", priority: 0,
  },
  {
    id: "G02", name: "8 Stability Layers (S1-S8)",
    desc: "Processing pipeline in Dragon Brain.",
    server: "n/a", palette: "deployed", wired: true,
    serverPath: "inline", port: "8108",
    category: "governance", priority: 0,
  },
  {
    id: "G03", name: "Layer 7 Communication Filter",
    desc: "applyLayer7() semantic post-filter. Armadura de Seda integration.",
    server: "n/a", palette: "deployed", wired: true,
    serverPath: "inline", port: "8108",
    category: "governance", priority: 0,
  },
  {
    id: "G04", name: "Sentinel LAW Monitor",
    desc: "5-tier escalation. p95=32.7ms. I9 compliant. systemd :8102. GREEN status.",
    server: "deployed", palette: "not-present", wired: false,
    serverPath: "/opt/windi/sentinel-law/", port: "8102",
    category: "governance", priority: 2,
    gap: "Palette has no visibility into Sentinel. Need: /api/sentinel/status for health/alerts display in GovPanel.",
  },
  {
    id: "G05", name: "Constitutional Panel (Via C)",
    desc: "Regulators see Constitution, Invariants, EU AI Act compliance in browser. Static data.",
    server: "n/a", palette: "missing", wired: false,
    serverPath: "—", port: "—",
    category: "governance", priority: 1,
    gap: "New UI section. Show I1-I9, EU AI Act 8/8, Compliance Passport metrics. Visible WITHOUT LLM.",
  },
  {
    id: "G06", name: "Compliance Passport v2.0",
    desc: "GOLD tier. Gov100%, Op93.5%, Road80.6%. CLI generate|verify|status.",
    server: "deployed", palette: "partial", wired: false,
    serverPath: "/opt/windi/docs/", port: "—",
    category: "governance", priority: 1,
    gap: "Palette shows 'GOLD' tier but no detailed metrics. Need: /api/compliance/passport endpoint.",
  },
  {
    id: "G07", name: "Verfassungsprompts Bridge (Via A)",
    desc: "CLAUDE.md constitutional identity for Dragon Server. 7 exegetical scenarios + 5 stress tests.",
    server: "deployed", palette: "not-loaded", wired: false,
    serverPath: "/opt/windi/CLAUDE.md + /opt/windi/docs/constitutional/", port: "—",
    category: "governance", priority: 2,
    gap: "Dragon Server uses own system prompt. Doesn't load CLAUDE.md constitutional depth.",
  },

  // ━━━ LAYER 5: ECOSYSTEM CONNECTIVITY ━━━
  {
    id: "E01", name: "Communiqué Engine",
    desc: "create→review→publish=SEALED. ISP wired with 6 templates + Resolver v1.0.0.",
    server: "partial", palette: "declared", wired: false,
    serverPath: "/opt/windi/communique/", port: "8105",
    category: "ecosystem", priority: 1,
    gap: "Palette references communiqué in 9 places. Engine exists but needs completion + /api/palette/communique route.",
  },
  {
    id: "E02", name: "ISP Template Selection",
    desc: "13 ISP templates defined in Palette UI (COM-01~06 + 7 ISP configs). 18 ISPs on governance API.",
    server: "deployed", palette: "partial", wired: false,
    serverPath: "/opt/windi/isp/", port: "8080",
    category: "ecosystem", priority: 1,
    gap: "Palette has ISP definitions inline but doesn't fetch from live ISP API. Need: /api/isp/list + apply to document generation.",
  },
  {
    id: "E03", name: "Desktop D1 Integration",
    desc: "React+Tiptap+Zustand+FastAPI. Full editor with Ledger seal. systemd :8100.",
    server: "deployed", palette: "not-present", wired: false,
    serverPath: "/opt/windi/desktop/", port: "8100",
    category: "ecosystem", priority: 3,
    gap: "Palette and Desktop are separate UIs. Future: deep link or embedded mode.",
  },
  {
    id: "E04", name: "Wallet 'O Espelho'",
    desc: "React trilingual + KLAR/NOIR. TrustRadar + Ed25519 Seal. UUIDv7.",
    server: "planned", palette: "not-present", wired: false,
    serverPath: "/opt/windi/wallet/", port: "8099",
    category: "ecosystem", priority: 3,
    gap: "Wallet service not yet operational. Future integration.",
  },

  // ━━━ LAYER 6: UI & OPERATIONS ━━━
  {
    id: "U01", name: "KLAR/NOIR Themes",
    desc: "Pergaminho (#F5F0E0) + Dark (#0E0E14). Toggle present.",
    server: "n/a", palette: "deployed", wired: true,
    serverPath: "inline", port: "8108",
    category: "ui", priority: 0,
  },
  {
    id: "U02", name: "Trilingual (DE/EN/PT)",
    desc: "Auto-detect + respond in detected language. LANG_AMBIGUOUS fix deployed.",
    server: "n/a", palette: "deployed", wired: true,
    serverPath: "inline", port: "8108",
    category: "ui", priority: 0,
  },
  {
    id: "U03", name: "SealBadge + GovPanel",
    desc: "Compact seal indicator + expandable governance details.",
    server: "n/a", palette: "deployed", wired: true,
    serverPath: "inline", port: "8108",
    category: "ui", priority: 0,
  },
  {
    id: "U04", name: "TierSwitch (P/M/G)",
    desc: "Personal/Medium/Governance tier selector. Affects format availability.",
    server: "n/a", palette: "deployed", wired: true,
    serverPath: "inline", port: "8108",
    category: "ui", priority: 0,
  },
  {
    id: "U05", name: "Chat History Persistence",
    desc: "Save and restore sessions across reloads.",
    server: "missing", palette: "missing", wired: false,
    serverPath: "—", port: "—",
    category: "ui", priority: 2,
    gap: "SQLite session store. List/resume conversations.",
  },
  {
    id: "U06", name: "systemd for Palette",
    desc: "Dragon Server runs via nohup — needs proper systemd unit.",
    server: "missing", palette: "n/a", wired: false,
    serverPath: "—", port: "8108",
    category: "ops", priority: 1,
    gap: "Create /etc/systemd/system/windi-palette.service. Auto-restart on crash.",
  },
];

const CATEGORIES = {
  production: { label: "Document Production", icon: "🏭", color: GOLD, desc: "The Industrial Core — PDF, DOCX, PPTX, XLSX, JMPG" },
  forensic: { label: "Forensic Stack", icon: "🔐", color: GREEN, desc: "Trust Layer — Ledger, Vault, Wave1, Paperless Signatures" },
  intelligence: { label: "Intelligence", icon: "🧠", color: PURPLE, desc: "Dragon Brain — LLM, OCR, Wisdom, Skills" },
  governance: { label: "Governance", icon: "⚖️", color: BLUE, desc: "Constitutional Layer — Invariants, Sentinel, Compliance" },
  ecosystem: { label: "Ecosystem", icon: "🔗", color: PINK, desc: "Service Connectivity — Communiqué, ISP, Desktop, Wallet" },
  ui: { label: "UI & Interface", icon: "🎨", color: AMBER, desc: "User Experience — Themes, Language, Controls" },
  ops: { label: "Operations", icon: "⚙️", color: DIM, desc: "Infrastructure — systemd, Keys, Monitoring" },
};

const WIRING_STATUS = {
  true: { label: "WIRED ✓", color: GREEN, bg: "rgba(34,197,94,0.12)" },
  false: { label: "NOT WIRED", color: RED, bg: "rgba(239,68,68,0.08)" },
};

const SERVER_STATUS = {
  deployed: { label: "ON SERVER", color: GREEN },
  partial: { label: "PARTIAL", color: AMBER },
  missing: { label: "NOT BUILT", color: RED },
  planned: { label: "PLANNED", color: DIM },
  "n/a": { label: "N/A", color: DIM },
};

const PALETTE_STATUS = {
  deployed: { label: "IN PALETTE", color: GREEN },
  declared: { label: "DECLARED", color: AMBER },
  partial: { label: "PARTIAL", color: AMBER },
  "not-present": { label: "ABSENT", color: RED },
  "not-loaded": { label: "NOT LOADED", color: RED },
  broken: { label: "BROKEN ⚠️", color: RED },
  missing: { label: "MISSING", color: RED },
  "n/a": { label: "—", color: DIM },
};

// Sprint plan
const SPRINTS = [
  {
    id: "S0",
    title: "SPRINT 0 — Ressuscitar Dragon",
    subtitle: "Dragon Server crashed. Fix FIRST — everything depends on it.",
    color: RED,
    effort: "30 min",
    ids: ["I01"],
  },
  {
    id: "S1",
    title: "SPRINT 1 — Produção Documental",
    subtitle: "Wire ALL document engines to Palette. This is the showroom.",
    color: GOLD,
    effort: "1-2 dias",
    ids: ["D01", "D02", "D03", "F01", "F03"],
  },
  {
    id: "S2",
    title: "SPRINT 2 — Assinatura + Selo Forense",
    subtitle: "Paperless.io + Vault. Legal signatures from Palette.",
    color: GREEN,
    effort: "1 dia",
    ids: ["F04", "F02", "U06"],
  },
  {
    id: "S3",
    title: "SPRINT 3 — Inteligência & Identidade",
    subtitle: "OCR, Product Identity, Wisdom, Compliance Panel.",
    color: PURPLE,
    effort: "1-2 dias",
    ids: ["I03", "I06", "I05", "G05", "G06"],
  },
  {
    id: "S4",
    title: "SPRINT 4 — Ecossistema & Futuro",
    subtitle: "Communiqué, XLSX, Sentinel, remaining features.",
    color: BLUE,
    effort: "2-3 dias",
    ids: ["E01", "E02", "D04", "G04", "G07"],
  },
];

function Badge({ children, color, bg, small }) {
  return (
    <span style={{
      display: "inline-flex", alignItems: "center",
      padding: small ? "1px 6px" : "2px 8px",
      borderRadius: 4, fontSize: small ? 9 : 10,
      fontWeight: 700, letterSpacing: "0.04em",
      color, backgroundColor: bg || `${color}18`,
      fontFamily: "'JetBrains Mono', monospace",
      whiteSpace: "nowrap",
    }}>
      {children}
    </span>
  );
}

function FeatureRow({ f, expanded, onToggle }) {
  const cat = CATEGORIES[f.category];
  const wired = WIRING_STATUS[f.wired];
  const srv = SERVER_STATUS[f.server];
  const pal = PALETTE_STATUS[f.palette];

  return (
    <div onClick={onToggle} style={{
      background: expanded ? CARD2 : CARD, border: `1px solid ${expanded ? `${cat.color}33` : BORDER}`,
      borderRadius: 8, padding: "10px 14px", cursor: "pointer",
      borderLeft: `3px solid ${f.wired ? GREEN : f.gap ? RED : DIM}`,
      transition: "all 0.15s",
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
        <span style={{ fontSize: 11, color: DIM, fontFamily: "'JetBrains Mono', monospace", width: 28, flexShrink: 0 }}>{f.id}</span>
        <span style={{ fontSize: 13, color: TEXT, fontWeight: 600, flex: 1, minWidth: 120 }}>{f.name}</span>
        <div style={{ display: "flex", gap: 4, flexWrap: "wrap", justifyContent: "flex-end" }}>
          <Badge color={srv.color} small>SRV: {srv.label}</Badge>
          <Badge color={pal.color} small>PAL: {pal.label}</Badge>
          <Badge color={wired.color} bg={wired.bg} small>{wired.label}</Badge>
        </div>
      </div>
      {expanded && (
        <div style={{ marginTop: 10, paddingTop: 10, borderTop: `1px solid ${BORDER}` }}>
          <p style={{ fontSize: 12, color: DIM, margin: "0 0 8px", lineHeight: 1.6 }}>{f.desc}</p>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 10, fontSize: 10, fontFamily: "'JetBrains Mono', monospace", marginBottom: 8 }}>
            {f.serverPath && f.serverPath !== "—" && (
              <span style={{ color: GOLD }}>path: <span style={{ color: TEXT }}>{f.serverPath}</span></span>
            )}
            {f.port && f.port !== "—" && (
              <span style={{ color: GOLD }}>port: <span style={{ color: TEXT }}>{f.port}</span></span>
            )}
          </div>
          {f.gap && (
            <div style={{ padding: "8px 10px", background: `${RED}08`, border: `1px solid ${RED}20`, borderRadius: 6 }}>
              <span style={{ fontSize: 10, color: RED, fontWeight: 700 }}>🔧 GAP:</span>
              <p style={{ fontSize: 11, color: TEXT, margin: "4px 0 0", lineHeight: 1.6 }}>{f.gap}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function PaletteOutlook() {
  const [expandedId, setExpandedId] = useState(null);
  const [viewMode, setViewMode] = useState("sprint");
  const [catFilter, setCatFilter] = useState("all");

  const stats = useMemo(() => {
    const wired = FEATURES.filter(f => f.wired).length;
    const onServer = FEATURES.filter(f => ["deployed", "partial"].includes(f.server)).length;
    const inPalette = FEATURES.filter(f => ["deployed", "declared", "partial"].includes(f.palette)).length;
    const gaps = FEATURES.filter(f => f.gap).length;
    const critical = FEATURES.filter(f => f.gap && f.priority <= 1).length;
    return { wired, onServer, inPalette, gaps, critical, total: FEATURES.length };
  }, []);

  const grouped = useMemo(() => {
    if (viewMode === "sprint") {
      return SPRINTS.map(s => ({
        key: s.id, title: s.title, subtitle: s.subtitle, color: s.color, effort: s.effort,
        items: s.ids.map(id => FEATURES.find(f => f.id === id)).filter(Boolean),
      }));
    }
    if (viewMode === "category") {
      return Object.entries(CATEGORIES)
        .map(([key, meta]) => ({
          key, title: `${meta.icon} ${meta.label}`, subtitle: meta.desc, color: meta.color,
          items: FEATURES.filter(f => f.category === key && (catFilter === "all" || !f.wired)),
        }))
        .filter(g => g.items.length > 0);
    }
    // wiring view
    return [
      { key: "wired", title: "✅ Fully Wired", color: GREEN, items: FEATURES.filter(f => f.wired) },
      { key: "broken", title: "🔴 BROKEN (needs immediate fix)", color: RED, items: FEATURES.filter(f => f.palette === "broken") },
      { key: "server-not-wired", title: "🟡 On Server → NOT in Palette", color: AMBER, items: FEATURES.filter(f => !f.wired && ["deployed", "partial"].includes(f.server) && !["deployed"].includes(f.palette) && f.palette !== "broken") },
      { key: "declared-not-wired", title: "🟠 Declared in Palette → No Backend", color: PINK, items: FEATURES.filter(f => !f.wired && ["declared"].includes(f.palette) && f.palette !== "broken") },
      { key: "both-missing", title: "⚫ Not Built Anywhere", color: DIM, items: FEATURES.filter(f => !f.wired && f.server === "missing" && ["missing", "not-present"].includes(f.palette)) },
    ].filter(g => g.items.length > 0);
  }, [viewMode, catFilter]);

  return (
    <div style={{ background: BG, minHeight: "100vh", color: TEXT, fontFamily: "'Bricolage Grotesque', system-ui, sans-serif", padding: "20px 16px" }}>
      <link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@300;400;600;700;800&family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet" />

      <div style={{ maxWidth: 960, margin: "0 auto" }}>
        {/* Header */}
        <div style={{ marginBottom: 20 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
            <span style={{ fontSize: 32 }}>🐉</span>
            <div>
              <h1 style={{ margin: 0, fontSize: 20, fontWeight: 800, color: GOLD }}>PALETTE PRODUCT OUTLOOK</h1>
              <p style={{ margin: 0, fontSize: 11, color: DIM, fontFamily: "'JetBrains Mono', monospace" }}>
                v0.7.0-D — Real Server Diagnostics — 24 Feb 2026
              </p>
            </div>
          </div>
          <p style={{ fontSize: 13, color: DIM, margin: 0, lineHeight: 1.6 }}>
            O Palette é onde os Dragões se expressam e demonstram toda a capacidade industrial do WINDI.
            Produção documental em todas as artes com Impressão Forensic global.
          </p>
        </div>

        {/* Dashboard Cards */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 8, marginBottom: 16 }}>
          {[
            { label: "Total Features", value: stats.total, color: TEXT },
            { label: "Fully Wired", value: stats.wired, color: GREEN },
            { label: "On Server", value: stats.onServer, color: BLUE },
            { label: "Gaps to Close", value: stats.gaps, color: RED },
            { label: "P1 Critical", value: stats.critical, color: GOLD },
          ].map(s => (
            <div key={s.label} style={{ background: CARD, border: `1px solid ${BORDER}`, borderRadius: 8, padding: "10px 12px", textAlign: "center" }}>
              <div style={{ fontSize: 22, fontWeight: 800, color: s.color, fontFamily: "'JetBrains Mono', monospace" }}>{s.value}</div>
              <div style={{ fontSize: 9, color: DIM, fontWeight: 600, letterSpacing: "0.06em", marginTop: 2 }}>{s.label.toUpperCase()}</div>
            </div>
          ))}
        </div>

        {/* Wiring Diagram */}
        <div style={{ background: CARD, border: `1px solid ${BORDER}`, borderRadius: 10, padding: 16, marginBottom: 16 }}>
          <h3 style={{ margin: "0 0 10px", fontSize: 13, fontWeight: 700, color: GOLD }}>🔌 Wiring Status — Server ↔ Palette</h3>
          <div style={{ height: 12, background: "#1a1a2e", borderRadius: 6, overflow: "hidden", display: "flex", marginBottom: 8 }}>
            <div style={{ width: `${(stats.wired / stats.total) * 100}%`, background: GREEN, transition: "width 0.4s" }} />
            <div style={{ width: `${((stats.onServer - stats.wired) / stats.total) * 100}%`, background: AMBER, transition: "width 0.4s" }} />
            <div style={{ width: `${((stats.total - stats.onServer) / stats.total) * 100}%`, background: `${RED}40`, transition: "width 0.4s" }} />
          </div>
          <div style={{ display: "flex", gap: 16, justifyContent: "center", fontSize: 10 }}>
            <span style={{ color: GREEN }}>● {stats.wired} wired</span>
            <span style={{ color: AMBER }}>● {stats.onServer - stats.wired} on server, not wired</span>
            <span style={{ color: `${RED}99` }}>● {stats.total - stats.onServer} not built</span>
          </div>
        </div>

        {/* CRITICAL ALERT */}
        <div style={{ background: `${RED}10`, border: `1px solid ${RED}30`, borderRadius: 10, padding: 14, marginBottom: 16 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
            <span style={{ fontSize: 16 }}>🚨</span>
            <span style={{ fontSize: 13, fontWeight: 700, color: RED }}>CRITICAL: Dragon Server DOWN</span>
          </div>
          <p style={{ fontSize: 12, color: TEXT, margin: 0, lineHeight: 1.6 }}>
            <code style={{ color: AMBER, fontSize: 11 }}>/api/dragon/health → 404</code> · <code style={{ color: AMBER, fontSize: 11 }}>/api/dragon/chat → "Not found"</code><br/>
            The LLM brain is not responding. All chat falls back to local JS intelligence.
            Sprint 0 must fix this before anything else.
          </p>
        </div>

        {/* View Controls */}
        <div style={{ display: "flex", gap: 4, background: CARD, padding: 3, borderRadius: 6, border: `1px solid ${BORDER}`, marginBottom: 16, width: "fit-content" }}>
          {[
            { key: "sprint", label: "🏃 Sprint Plan" },
            { key: "wiring", label: "🔌 Wiring View" },
            { key: "category", label: "📂 By Category" },
          ].map(v => (
            <button key={v.key} onClick={() => setViewMode(v.key)} style={{
              padding: "6px 14px", fontSize: 11, fontWeight: 600, border: "none", borderRadius: 4, cursor: "pointer",
              background: viewMode === v.key ? GOLD : "transparent",
              color: viewMode === v.key ? BG : DIM,
            }}>
              {v.label}
            </button>
          ))}
        </div>

        {/* Feature Groups */}
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          {grouped.map(group => (
            <div key={group.key}>
              <div style={{ display: "flex", alignItems: "baseline", gap: 8, marginBottom: 8 }}>
                <h2 style={{ margin: 0, fontSize: 14, fontWeight: 700, color: group.color || TEXT }}>{group.title}</h2>
                {group.subtitle && <span style={{ fontSize: 11, color: DIM }}>— {group.subtitle}</span>}
                {group.effort && <Badge color={group.color}>{group.effort}</Badge>}
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
                {group.items.map(f => (
                  <FeatureRow key={f.id} f={f} expanded={expandedId === f.id} onToggle={() => setExpandedId(expandedId === f.id ? null : f.id)} />
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Architecture Summary */}
        <div style={{ marginTop: 24, background: CARD, border: `1px solid ${BORDER}`, borderRadius: 10, padding: 16 }}>
          <h3 style={{ margin: "0 0 10px", fontSize: 13, fontWeight: 700, color: GOLD }}>🏗️ Target: Palette as Centro Nervoso Industrial</h3>
          <pre style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 9, color: DIM, lineHeight: 1.9, margin: 0, overflowX: "auto" }}>
{`  USER → Palette UI (:8108) → Dragon Brain (LLM + Local Intelligence)
              │
              ├─→ 🏭 PRODUCE ──→ PDF(:8103) DOCX(:8103) PPTX(ppt-engine) XLSX(new) JMPG(:8104)
              │                          ↓ all with N2-N4 Forensic Seal
              ├─→ 🔐 SEAL ────→ Ledger(:8101) → Vault(:8106) → Virtue Receipt
              │                          ↓
              ├─→ ✍️  SIGN ────→ Command Bridge(:8097) → Paperless.io (eIDAS)
              │                          ↓ webhook → receipt
              ├─→ 📡 PUBLISH ──→ Communiqué(:8105) → SEALED distribution
              │
              ├─→ 🧠 ANALYZE ──→ OCR(Tesseract) → AutoCat → SGE Risk(R0-R5)
              │
              ├─→ ⚖️  GOVERN ──→ Sentinel(:8102) monitors | I1-I9 validates
              │                  Compliance Passport | EU AI Act 8/8
              │
              └─→ 📋 TEMPLATES → 18 ISPs(:8080) → Apply to any format`}
          </pre>
        </div>

        {/* Footer */}
        <div style={{ marginTop: 20, textAlign: "center", fontSize: 10, color: DIM, lineHeight: 1.8 }}>
          <div style={{ color: GOLD, fontWeight: 700, fontSize: 11 }}>"KI verarbeitet. Der Mensch entscheidet. WINDI garantiert."</div>
          <div>WINDI Publishing House · Kempten, Bavaria · Palette Product Outlook</div>
          <div style={{ fontFamily: "'JetBrains Mono', monospace" }}>
            {stats.wired}/{stats.total} wired · {stats.gaps} gaps · 5 sprints · ∞ possibilities
          </div>
        </div>
      </div>
    </div>
  );
}
