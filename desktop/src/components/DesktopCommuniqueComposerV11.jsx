import { useState, useEffect, useCallback, useRef } from "react";

// ═══════════════════════════════════════════════════════════════
//  WINDI Desktop Communiqué Composer v1.1
//  "AI processes. Human decides. WINDI guarantees."
//
//  v1.1 CHANGELOG (from Architect + Guardian analysis):
//  ✔ Canonical JSON: sorted keys for hash determinism JS ↔ Python
//  ✔ schema_version, created_at, origin in payload
//  ✔ Stronger irreversible publish confirmation
//  ✔ Title validation gate before publish
//  ✔ Post-publish: direct link to Viewer (:8104)
//  ✔ Wallet identity placeholder (Ed25519)
//  ✔ Media dropzone placeholder
//  ✔ Autosave indicator
//
//  Pipeline: Composer → Communiqué Engine (:8105) → Ledger (:8101)
//            Composer → Export Engine (:8103) → .jmpg → Viewer (:8104)
// ═══════════════════════════════════════════════════════════════

const SCHEMA_VERSION = "1.1";
const ORIGIN = "WINDI Desktop Composer";

// ─── Canonical JSON (RFC 8785 simplified) ───
// Deterministic serialization: sorted keys, no spaces.
// Ensures JS hash === Python hash (json.dumps(obj, sort_keys=True, separators=(',',':')))
function canonicalize(obj) {
  if (obj === null || typeof obj !== "object") return JSON.stringify(obj);
  if (Array.isArray(obj)) return "[" + obj.map(canonicalize).join(",") + "]";
  const sorted = Object.keys(obj).sort();
  return "{" + sorted.map(k => JSON.stringify(k) + ":" + canonicalize(obj[k])).join(",") + "}";
}

// ─── SHA-256 ───
async function sha256(text) {
  const enc = new TextEncoder().encode(text);
  const buf = await crypto.subtle.digest("SHA-256", enc);
  return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, "0")).join("");
}

// ─── Unique Block ID ───
let _idCounter = 0;
const uid = () => `blk-${Date.now()}-${++_idCounter}`;

// ═══════════════════════════════════════════════════════════════
//  DESIGN TOKENS
// ═══════════════════════════════════════════════════════════════
const NOIR = {
  bg: "#09090b", surface: "#111113", elevated: "#18181b",
  border: "#27272a", borderHover: "#3f3f46",
  text: "#e4e4e7", textMuted: "#a1a1aa", textDim: "#71717a",
  gold: "#c4940f", goldDim: "#8a6a0a", goldBright: "#eab308",
  goldSurface: "rgba(196,148,15,0.06)", goldBorder: "rgba(196,148,15,0.18)",
  danger: "#ef4444", dangerDim: "rgba(239,68,68,0.12)",
  success: "#22c55e", successDim: "rgba(34,197,94,0.10)",
  info: "#3b82f6", infoDim: "rgba(59,130,246,0.10)",
  warn: "#f59e0b", warnDim: "rgba(245,158,11,0.10)",
};
const KLAR = {
  bg: "#fafaf9", surface: "#ffffff", elevated: "#f4f4f5",
  border: "#e4e4e7", borderHover: "#d4d4d8",
  text: "#18181b", textMuted: "#71717a", textDim: "#a1a1aa",
  gold: "#92700c", goldDim: "#b8860b", goldBright: "#78590a",
  goldSurface: "rgba(146,112,12,0.05)", goldBorder: "rgba(146,112,12,0.15)",
  danger: "#dc2626", dangerDim: "rgba(220,38,38,0.08)",
  success: "#16a34a", successDim: "rgba(22,163,74,0.08)",
  info: "#2563eb", infoDim: "rgba(37,99,235,0.08)",
  warn: "#d97706", warnDim: "rgba(217,119,6,0.08)",
};

const TEMPLATES = [
  { id: "comunicado", icon: "◆", label: { de: "Kommuniqué", en: "Communiqué", pt: "Comunicado" }, desc: { de: "Offizielle Mitteilung", en: "Official statement", pt: "Declaração oficial" } },
  { id: "jornaline", icon: "◈", label: { de: "Presseartikel", en: "Press Article", pt: "Jornaline" }, desc: { de: "Journalistisches Format", en: "Editorial format", pt: "Formato editorial" } },
  { id: "field-report", icon: "◇", label: { de: "Feldbericht", en: "Field Report", pt: "Relatório" }, desc: { de: "Technischer Bericht", en: "Technical report", pt: "Relatório técnico" } },
  { id: "pressemitteilung", icon: "◊", label: { de: "Pressemitteilung", en: "Press Release", pt: "Nota de Imprensa" }, desc: { de: "Pressemitteilung", en: "Press release", pt: "Nota oficial" } },
  { id: "internal-memo", icon: "▪", label: { de: "Internes Memo", en: "Internal Memo", pt: "Memorando" }, desc: { de: "Vertraulich", en: "Confidential", pt: "Confidencial" } },
  { id: "generic", icon: "▫", label: { de: "Allgemein", en: "Generic", pt: "Genérico" }, desc: { de: "Flexibel", en: "Flexible", pt: "Flexível" } },
];

const IMPACT_LEVELS = [
  { id: "LOW", color: "#22c55e", label: { de: "Niedrig", en: "Low", pt: "Baixo" } },
  { id: "MED", color: "#eab308", label: { de: "Mittel", en: "Medium", pt: "Médio" } },
  { id: "HIGH", color: "#f97316", label: { de: "Hoch", en: "High", pt: "Alto" } },
  { id: "CRIT", color: "#ef4444", label: { de: "Kritisch", en: "Critical", pt: "Crítico" } },
];

const RISK_LEVELS = ["R0", "R1", "R2", "R3", "R4", "R5"];
const RISK_COLORS = { R0: "#22c55e", R1: "#84cc16", R2: "#eab308", R3: "#f97316", R4: "#ef4444", R5: "#dc2626" };

const BLOCK_TYPES = [
  { type: "heading", icon: "H", label: "Heading" },
  { type: "paragraph", icon: "¶", label: "Paragraph" },
  { type: "quote", icon: "❝", label: "Quote" },
  { type: "list", icon: "☰", label: "List" },
  { type: "divider", icon: "―", label: "Divider" },
];

// ═══════════════════════════════════════════════════════════════
//  i18n
// ═══════════════════════════════════════════════════════════════
const i18n = {
  title: { de: "Kommuniqué Composer", en: "Communiqué Composer", pt: "Compositor de Comunicados" },
  template: { de: "Vorlage", en: "Template", pt: "Modelo" },
  metadata: { de: "Metadaten", en: "Metadata", pt: "Metadados" },
  content: { de: "Inhalt", en: "Content", pt: "Conteúdo" },
  impact: { de: "Auswirkung", en: "Impact", pt: "Impacto" },
  risk: { de: "Risikostufe", en: "Risk Level", pt: "Nível de Risco" },
  department: { de: "Abteilung", en: "Department", pt: "Departamento" },
  tags: { de: "Schlagwörter", en: "Tags", pt: "Tags" },
  author: { de: "Verfasser", en: "Author", pt: "Autor" },
  docTitle: { de: "Dokumenttitel", en: "Document Title", pt: "Título do Documento" },
  publish: { de: "Veröffentlichen", en: "Publish", pt: "Publicar" },
  exportJmpg: { de: ".jmpg exportieren", en: "Export .jmpg", pt: "Exportar .jmpg" },
  saveDraft: { de: "Entwurf", en: "Draft", pt: "Rascunho" },
  addBlock: { de: "Block hinzufügen", en: "Add Block", pt: "Adicionar Bloco" },
  noBlocks: { de: "Inhaltsblöcke hinzufügen...", en: "Add content blocks to begin...", pt: "Adicione blocos de conteúdo..." },
  governance: { de: "Governance", en: "Governance", pt: "Governança" },
  draft: { de: "Entwurf", en: "Draft", pt: "Rascunho" },
  published: { de: "Veröffentlicht", en: "Published", pt: "Publicado" },
  sealed: { de: "Versiegelt", en: "Sealed", pt: "Selado" },
  hashPreview: { de: "Content-Hash (Echtzeit)", en: "Content Hash (real-time)", pt: "Hash de Conteúdo (tempo real)" },
  ledgerNote: { de: "Wird unveränderlich im Forensic Ledger registriert", en: "Will be immutably registered in Forensic Ledger", pt: "Será registrado imutavelmente no Forensic Ledger" },
  publishWarn: { de: "Diese Aktion versiegelt das Kommuniqué dauerhaft im Forensic Ledger. Dieser Vorgang ist unwiderruflich.", en: "This action permanently seals the communiqué in the Forensic Ledger. This operation is irreversible.", pt: "Esta ação sela permanentemente o comunicado no Forensic Ledger. Esta operação é irreversível." },
  titleRequired: { de: "Titel ist erforderlich", en: "Title is required", pt: "Título é obrigatório" },
  language: { de: "Sprache", en: "Language", pt: "Idioma" },
  pipeline: { de: "Pipeline", en: "Pipeline", pt: "Pipeline" },
  summary: { de: "Zusammenfassung", en: "Summary", pt: "Resumo" },
  result: { de: "Ergebnis", en: "Result", pt: "Resultado" },
  openViewer: { de: "Im Viewer öffnen", en: "Open in Viewer", pt: "Abrir no Viewer" },
  openPublic: { de: "Öffentliche Seite", en: "Public Page", pt: "Página Pública" },
  canonical: { de: "Kanonisch", en: "Canonical", pt: "Canônico" },
  walletSign: { de: "Wallet signieren", en: "Sign with Wallet", pt: "Assinar com Wallet" },
  identity: { de: "Identität", en: "Identity", pt: "Identidade" },
  mediaZone: { de: "Medien hierher ziehen", en: "Drop media here", pt: "Solte mídia aqui" },
  blocks: { de: "Blöcke", en: "Blocks", pt: "Blocos" },
};
const t = (key, lang) => i18n[key]?.[lang] || i18n[key]?.en || key;

// ═══════════════════════════════════════════════════════════════
//  MAIN COMPONENT
// ═══════════════════════════════════════════════════════════════
export default function DesktopCommuniqueComposer() {
  const [theme, setTheme] = useState("noir");
  const [lang, setLang] = useState("de");
  const C = theme === "noir" ? NOIR : KLAR;

  // ─── Document state ───
  const [docTitle, setDocTitle] = useState("");
  const [author, setAuthor] = useState("");
  const [template, setTemplate] = useState("comunicado");
  const [impactLevel, setImpactLevel] = useState("MED");
  const [riskLevel, setRiskLevel] = useState("R1");
  const [department, setDepartment] = useState("");
  const [tags, setTags] = useState("");
  const [docLang, setDocLang] = useState("de");

  // ─── Content blocks ───
  const [blocks, setBlocks] = useState([
    { id: uid(), type: "heading", level: 1, text: "" },
    { id: uid(), type: "paragraph", text: "" },
  ]);

  // ─── UI state ───
  const [contentHash, setContentHash] = useState(null);
  const [status, setStatus] = useState("draft");
  const [publishResult, setPublishResult] = useState(null);
  const [showConfirm, setShowConfirm] = useState(null);
  const [showAddBlock, setShowAddBlock] = useState(false);
  const [focusedBlock, setFocusedBlock] = useState(null);
  const [validationErrors, setValidationErrors] = useState([]);
  const [lastSaved, setLastSaved] = useState(null);
  const [walletConnected, setWalletConnected] = useState(false);
  const [mediaFiles, setMediaFiles] = useState([]);
  const editorRef = useRef(null);

  // ═══════════════════════════════════════════════════════════
  //  CANONICAL HASH — sorted keys, deterministic
  //  Matches Python: json.dumps(obj, sort_keys=True, separators=(',',':'))
  // ═══════════════════════════════════════════════════════════
  useEffect(() => {
    const timer = setTimeout(async () => {
      const cleanBlocks = blocks.map(b => {
        const { id, ...rest } = b;
        return rest;
      });
      const canonical = canonicalize(cleanBlocks);
      const hash = await sha256(canonical);
      setContentHash(hash);
    }, 400);
    return () => clearTimeout(timer);
  }, [blocks]);

  // ─── Autosave indicator ───
  useEffect(() => {
    const timer = setTimeout(() => {
      if (blocks.some(b => b.text || (b.items && b.items.some(i => i)))) {
        setLastSaved(new Date());
      }
    }, 2000);
    return () => clearTimeout(timer);
  }, [blocks, docTitle, author, template]);

  // ═══════════════════════════════════════════════════════════
  //  BLOCK OPERATIONS
  // ═══════════════════════════════════════════════════════════
  const addBlock = useCallback((type) => {
    const b = type === "heading" ? { id: uid(), type: "heading", level: 2, text: "" }
      : type === "divider" ? { id: uid(), type: "divider" }
      : type === "list" ? { id: uid(), type: "list", ordered: false, items: [""] }
      : type === "quote" ? { id: uid(), type: "quote", text: "" }
      : { id: uid(), type: "paragraph", text: "" };
    setBlocks(prev => [...prev, b]);
    setShowAddBlock(false);
  }, []);

  const updateBlock = useCallback((id, updates) => {
    setBlocks(prev => prev.map(b => b.id === id ? { ...b, ...updates } : b));
  }, []);

  const removeBlock = useCallback((id) => {
    setBlocks(prev => prev.filter(b => b.id !== id));
  }, []);

  const moveBlock = useCallback((id, dir) => {
    setBlocks(prev => {
      const idx = prev.findIndex(b => b.id === id);
      if (idx < 0) return prev;
      const ni = idx + dir;
      if (ni < 0 || ni >= prev.length) return prev;
      const a = [...prev];
      [a[idx], a[ni]] = [a[ni], a[idx]];
      return a;
    });
  }, []);

  // ═══════════════════════════════════════════════════════════
  //  BUILD PAYLOAD — v1.1 with schema_version, created_at, origin
  // ═══════════════════════════════════════════════════════════
  const buildPayload = useCallback(() => ({
    schema_version: SCHEMA_VERSION,
    origin: ORIGIN,
    created_at: new Date().toISOString(),
    title: docTitle,
    author,
    template,
    content_blocks: blocks.map(({ id, ...rest }) => rest),
    metadata: {
      doc_type: "COMMUNIQUE",
      impact_level: impactLevel,
      department_code: department || "EDITORIAL",
      language: docLang,
      tags: tags.split(",").map(t => t.trim()).filter(Boolean),
      risk_level: riskLevel,
    },
    media: mediaFiles.map(f => ({ filename: f.name, mime_type: f.type, size: f.size })),
  }), [docTitle, author, template, blocks, impactLevel, department, docLang, tags, riskLevel, mediaFiles]);

  // ═══════════════════════════════════════════════════════════
  //  VALIDATION GATE
  // ═══════════════════════════════════════════════════════════
  const validate = useCallback(() => {
    const errs = [];
    if (!docTitle.trim()) errs.push(t("titleRequired", lang));
    if (!author.trim()) errs.push(lang === "de" ? "Verfasser ist erforderlich" : lang === "pt" ? "Autor é obrigatório" : "Author is required");
    if (blocks.filter(b => b.type !== "divider").every(b => !(b.text || "").trim() && !(b.items || []).some(i => i.trim()))) {
      errs.push(lang === "de" ? "Mindestens ein Inhaltsblock erforderlich" : lang === "pt" ? "Pelo menos um bloco com conteúdo" : "At least one content block required");
    }
    setValidationErrors(errs);
    return errs.length === 0;
  }, [docTitle, author, blocks, lang]);

  // ═══════════════════════════════════════════════════════════
  //  PUBLISH → Communiqué Engine (:8105) → Ledger (:8101)
  // ═══════════════════════════════════════════════════════════
  const handlePublish = useCallback(async () => {
    setShowConfirm(null);
    if (!validate()) return;
    setStatus("sealing");
    try {
      const payload = buildPayload();
      const hash = contentHash || await sha256(canonicalize(payload.content_blocks));
      const ts = new Date();
      const comId = `COM-${ts.toISOString().slice(0, 10).replace(/-/g, "")}-${hash.slice(0, 8).toUpperCase()}`;

      // Production: POST /desktop/communique/api/publish → :8105
      await new Promise(r => setTimeout(r, 900));

      const bundleHash = await sha256(hash + comId + ts.toISOString());
      setPublishResult({
        com_id: comId,
        content_hash: hash,
        bundle_hash: bundleHash,
        receipt_id: `VR-COM-${hash.slice(0, 12)}`,
        ledger_registered: true,
        sealed_at: ts.toISOString(),
        viewer_url: `/desktop/communique/view/${comId}`,
        public_url: `/communique/${comId}`,
      });
      setStatus("published");
    } catch (err) {
      setStatus("error");
    }
  }, [buildPayload, contentHash, validate]);

  // ═══════════════════════════════════════════════════════════
  //  EXPORT .jmpg → Export Engine (:8103) → Ledger → Viewer (:8104)
  // ═══════════════════════════════════════════════════════════
  const handleExportJmpg = useCallback(async () => {
    setShowConfirm(null);
    if (!validate()) return;
    setStatus("sealing");
    try {
      const payload = { ...buildPayload(), return_format: "json" };
      const hash = contentHash || await sha256(canonicalize(payload.content_blocks));
      const pkgId = `JMPG-${new Date().toISOString().slice(0, 10).replace(/-/g, "")}-${hash.slice(0, 8).toUpperCase()}`;

      // Production: POST /desktop/api/export/jmpg → :8103
      await new Promise(r => setTimeout(r, 700));

      const manifestHash = await sha256(hash + pkgId);
      setPublishResult({
        package_id: pkgId,
        content_hash: hash,
        manifest_hash: manifestHash,
        receipt_id: `VR-JMPG-${hash.slice(0, 12)}`,
        ledger_registered: true,
        format: ".jmpg",
        viewer_url: `/desktop/jmpg/?verify=${pkgId}`,
      });
      setStatus("published");
    } catch (err) {
      setStatus("error");
    }
  }, [buildPayload, contentHash, validate]);

  // ═══════════════════════════════════════════════════════════
  //  MEDIA DROP (placeholder)
  // ═══════════════════════════════════════════════════════════
  const handleDrop = useCallback((e) => {
    e.preventDefault();
    const files = Array.from(e.dataTransfer?.files || []).filter(f =>
      f.type.startsWith("image/") || f.type === "application/pdf"
    );
    setMediaFiles(prev => [...prev, ...files.map(f => ({ name: f.name, type: f.type, size: f.size }))]);
  }, []);

  // ═══════════════════════════════════════════════════════════
  //  STYLES (functional, no Tailwind needed)
  // ═══════════════════════════════════════════════════════════
  const font = {
    display: "'Bricolage Grotesque', 'Georgia', serif",
    body: "'Outfit', 'Segoe UI', sans-serif",
    mono: "'JetBrains Mono', 'Cascadia Code', monospace",
  };

  const s = {
    root: { fontFamily: font.body, backgroundColor: C.bg, color: C.text, minHeight: "100vh", display: "flex", flexDirection: "column", fontSize: 13 },

    // Header
    header: { display: "flex", alignItems: "center", justifyContent: "space-between", padding: "10px 18px", borderBottom: `1px solid ${C.border}`, backgroundColor: C.surface },
    logoArea: { display: "flex", alignItems: "center", gap: 10 },
    logo: { fontFamily: font.display, fontWeight: 700, fontSize: 16, color: C.gold, letterSpacing: "-0.02em" },
    ver: { fontFamily: font.mono, fontSize: 9, color: C.textDim, padding: "2px 6px", borderRadius: 3, backgroundColor: C.elevated, border: `1px solid ${C.border}` },
    badge: (variant) => ({
      display: "inline-flex", alignItems: "center", gap: 3, padding: "2px 8px",
      borderRadius: 10, fontSize: 9, fontFamily: font.mono, fontWeight: 600, letterSpacing: "0.04em",
      backgroundColor: variant === "draft" ? C.infoDim : variant === "published" ? C.successDim : variant === "sealing" ? C.warnDim : C.dangerDim,
      color: variant === "draft" ? C.info : variant === "published" ? C.success : variant === "sealing" ? C.warn : C.danger,
    }),
    headerR: { display: "flex", alignItems: "center", gap: 6 },
    langPill: (on) => ({ fontFamily: font.mono, fontSize: 9, padding: "3px 7px", borderRadius: 3, border: `1px solid ${on ? C.gold : C.border}`, backgroundColor: on ? C.goldSurface : "transparent", color: on ? C.gold : C.textDim, cursor: "pointer", fontWeight: on ? 600 : 400 }),
    themeBtn: { fontFamily: font.mono, fontSize: 10, padding: "4px 10px", borderRadius: 5, border: `1px solid ${C.border}`, backgroundColor: "transparent", color: C.textMuted, cursor: "pointer" },

    // Main
    main: { display: "flex", flex: 1, overflow: "hidden" },

    // Sidebar
    side: { width: 270, borderRight: `1px solid ${C.border}`, backgroundColor: C.surface, overflowY: "auto", padding: 14, display: "flex", flexDirection: "column", gap: 18 },
    secTitle: { fontSize: 9, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: C.textDim, marginBottom: 6, fontFamily: font.mono },
    tplCard: (on) => ({ display: "flex", alignItems: "center", gap: 9, padding: "8px 10px", borderRadius: 7, cursor: "pointer", transition: "all 0.12s", backgroundColor: on ? C.goldSurface : "transparent", border: `1px solid ${on ? C.goldBorder : "transparent"}` }),
    tplIcon: (on) => ({ fontSize: 15, color: on ? C.gold : C.textDim, flexShrink: 0 }),
    tplLabel: (on) => ({ fontSize: 11, fontWeight: 600, color: on ? C.gold : C.text }),
    tplDesc: { fontSize: 9, color: C.textDim, marginTop: 1 },
    fieldLabel: { fontSize: 9, color: C.textDim, marginBottom: 3, display: "block", fontFamily: font.mono },
    input: { width: "100%", backgroundColor: C.elevated, border: `1px solid ${C.border}`, borderRadius: 5, padding: "7px 9px", color: C.text, fontSize: 12, outline: "none", fontFamily: font.body, boxSizing: "border-box" },
    impactRow: { display: "flex", gap: 4 },
    impactBtn: (on, color) => ({
      flex: 1, display: "flex", alignItems: "center", justifyContent: "center", gap: 3,
      padding: "5px 2px", borderRadius: 5, cursor: "pointer", fontSize: 9, fontFamily: font.mono, fontWeight: 600,
      backgroundColor: on ? `${color}16` : C.elevated,
      border: `1px solid ${on ? color : C.border}`,
      color: on ? color : C.textDim,
    }),
    dot: (color) => ({ width: 7, height: 7, borderRadius: "50%", backgroundColor: color, flexShrink: 0 }),
    riskRow: { display: "flex", gap: 3, flexWrap: "wrap" },
    riskBtn: (on, r) => ({
      padding: "3px 7px", borderRadius: 3, cursor: "pointer", fontSize: 9, fontFamily: font.mono, fontWeight: 600,
      backgroundColor: on ? `${RISK_COLORS[r]}16` : C.elevated,
      border: `1px solid ${on ? RISK_COLORS[r] : C.border}`,
      color: on ? RISK_COLORS[r] : C.textDim,
    }),

    // Editor
    editor: { flex: 1, overflowY: "auto", padding: "20px 24px", display: "flex", flexDirection: "column", gap: 10 },
    blockWrap: (focused) => ({ position: "relative", backgroundColor: C.surface, border: `1px solid ${focused ? C.goldBorder : C.border}`, borderRadius: 7, transition: "border-color 0.12s", overflow: "hidden" }),
    blockBar: { display: "flex", alignItems: "center", justifyContent: "space-between", padding: "3px 8px", backgroundColor: C.elevated, borderBottom: `1px solid ${C.border}` },
    blockLabel: { fontSize: 8, fontFamily: font.mono, color: C.textDim, textTransform: "uppercase", letterSpacing: "0.06em" },
    blockBtn: { background: "none", border: "none", color: C.textDim, cursor: "pointer", fontSize: 11, padding: "1px 3px", borderRadius: 2, lineHeight: 1 },
    ta: { width: "100%", backgroundColor: "transparent", border: "none", color: C.text, fontSize: 13, outline: "none", resize: "vertical", fontFamily: font.body, lineHeight: 1.65, padding: "10px 12px", boxSizing: "border-box", minHeight: 56 },
    taH: (l) => ({ width: "100%", backgroundColor: "transparent", border: "none", color: C.text, outline: "none", resize: "vertical", fontFamily: font.display, fontWeight: 700, fontSize: l === 1 ? 21 : l === 2 ? 17 : 14, lineHeight: 1.3, padding: "10px 12px", boxSizing: "border-box", minHeight: 44 }),
    taQ: { width: "100%", backgroundColor: "transparent", border: "none", color: C.gold, fontSize: 13, outline: "none", resize: "vertical", fontFamily: font.body, fontStyle: "italic", lineHeight: 1.65, padding: "10px 12px 10px 18px", boxSizing: "border-box", minHeight: 56, borderLeft: `3px solid ${C.goldBorder}` },
    dividerLine: { height: 1, backgroundColor: C.border, margin: "6px 12px" },
    addBtn: { display: "flex", alignItems: "center", justifyContent: "center", gap: 5, padding: "9px", border: `1px dashed ${C.border}`, borderRadius: 7, backgroundColor: "transparent", color: C.textDim, cursor: "pointer", fontSize: 11, fontFamily: font.body, transition: "all 0.12s" },
    addMenu: { display: "flex", gap: 5, flexWrap: "wrap", padding: 6, backgroundColor: C.elevated, borderRadius: 7, border: `1px solid ${C.border}` },
    addOpt: { display: "flex", alignItems: "center", gap: 3, padding: "5px 9px", borderRadius: 5, cursor: "pointer", backgroundColor: C.surface, border: `1px solid ${C.border}`, color: C.textMuted, fontSize: 10, fontFamily: font.mono, transition: "all 0.12s" },

    // Media dropzone
    dropzone: { border: `1px dashed ${C.border}`, borderRadius: 7, padding: "14px 12px", textAlign: "center", color: C.textDim, fontSize: 11, cursor: "pointer", transition: "all 0.12s", backgroundColor: "transparent" },
    mediaTag: { display: "inline-flex", alignItems: "center", gap: 4, padding: "3px 8px", borderRadius: 4, backgroundColor: C.elevated, border: `1px solid ${C.border}`, fontSize: 9, fontFamily: font.mono, color: C.textMuted, marginRight: 4, marginBottom: 4 },

    // Right panel
    right: { width: 290, borderLeft: `1px solid ${C.border}`, backgroundColor: C.surface, overflowY: "auto", padding: 14, display: "flex", flexDirection: "column", gap: 16 },
    hashBox: { fontFamily: font.mono, fontSize: 9, color: C.gold, backgroundColor: C.goldSurface, border: `1px solid ${C.goldBorder}`, borderRadius: 5, padding: "7px 9px", wordBreak: "break-all", lineHeight: 1.7 },
    pipeRow: { display: "flex", alignItems: "center", justifyContent: "space-between", padding: "3px 0" },
    pipeDot: (active) => ({ width: 5, height: 5, borderRadius: "50%", backgroundColor: active ? C.success : C.textDim, flexShrink: 0 }),
    summaryRow: { display: "flex", justifyContent: "space-between", alignItems: "center", padding: "2px 0" },
    resultCard: { backgroundColor: C.successDim, border: `1px solid rgba(34,197,94,0.20)`, borderRadius: 7, padding: 10 },
    resultRow: { display: "flex", justifyContent: "space-between", gap: 6, padding: "2px 0" },
    resultKey: { fontSize: 9, color: C.textDim, fontFamily: font.mono, flexShrink: 0 },
    resultVal: (ok) => ({ fontSize: 9, color: ok ? C.success : C.text, fontFamily: font.mono, textAlign: "right", wordBreak: "break-all" }),
    viewerBtn: { display: "inline-flex", alignItems: "center", gap: 5, padding: "6px 12px", borderRadius: 5, border: `1px solid ${C.goldBorder}`, backgroundColor: C.goldSurface, color: C.gold, cursor: "pointer", fontSize: 10, fontFamily: font.mono, fontWeight: 600, marginTop: 6 },

    // Wallet
    walletBox: { display: "flex", alignItems: "center", justifyContent: "space-between", padding: "6px 9px", borderRadius: 5, backgroundColor: C.elevated, border: `1px solid ${C.border}` },
    walletBtn: { fontSize: 9, fontFamily: font.mono, padding: "3px 8px", borderRadius: 3, border: `1px solid ${C.goldBorder}`, backgroundColor: C.goldSurface, color: C.gold, cursor: "pointer" },

    // Action bar
    actionBar: { display: "flex", alignItems: "center", justifyContent: "space-between", padding: "9px 18px", borderTop: `1px solid ${C.border}`, backgroundColor: C.surface },
    actionBtn: (v) => ({
      display: "inline-flex", alignItems: "center", gap: 5, padding: "7px 14px", borderRadius: 5, border: "none", cursor: "pointer", fontSize: 11, fontWeight: 600, fontFamily: font.body, transition: "all 0.12s",
      ...(v === "primary" ? { backgroundColor: C.gold, color: "#0a0a0a" } :
        v === "secondary" ? { backgroundColor: C.elevated, color: C.text, border: `1px solid ${C.border}` } :
        { backgroundColor: "transparent", color: C.textMuted, border: `1px solid ${C.border}` }),
    }),

    // Errors
    errBox: { backgroundColor: C.dangerDim, border: `1px solid rgba(239,68,68,0.20)`, borderRadius: 5, padding: "6px 10px", marginBottom: 4 },
    errText: { fontSize: 10, color: C.danger, fontFamily: font.mono },

    // Confirm
    overlay: { position: "fixed", top: 0, left: 0, right: 0, bottom: 0, backgroundColor: "rgba(0,0,0,0.55)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000, backdropFilter: "blur(2px)" },
    confirmBox: { backgroundColor: C.surface, border: `1px solid ${C.goldBorder}`, borderRadius: 10, padding: 22, maxWidth: 420, width: "92%", boxShadow: "0 12px 40px rgba(0,0,0,0.35)" },
  };

  // ═══════════════════════════════════════════════════════════
  //  BLOCK RENDERER
  // ═══════════════════════════════════════════════════════════
  const renderBlock = (block, idx) => {
    const focused = focusedBlock === block.id;
    return (
      <div key={block.id} style={s.blockWrap(focused)}>
        <div style={s.blockBar}>
          <span style={s.blockLabel}>
            {BLOCK_TYPES.find(bt => bt.type === block.type)?.icon} {block.type}
            {block.type === "heading" && ` h${block.level || 1}`}
          </span>
          <div style={{ display: "flex", gap: 1 }}>
            {idx > 0 && <button style={s.blockBtn} onClick={() => moveBlock(block.id, -1)}>↑</button>}
            {idx < blocks.length - 1 && <button style={s.blockBtn} onClick={() => moveBlock(block.id, 1)}>↓</button>}
            <button style={{ ...s.blockBtn, color: C.danger }} onClick={() => removeBlock(block.id)}>✕</button>
          </div>
        </div>

        {block.type === "heading" && (
          <div>
            <div style={{ padding: "3px 12px 0", display: "flex", gap: 3 }}>
              {[1, 2, 3].map(l => (
                <button key={l} onClick={() => updateBlock(block.id, { level: l })}
                  style={{ ...s.blockBtn, fontSize: 9, backgroundColor: block.level === l ? C.goldSurface : "transparent", color: block.level === l ? C.gold : C.textDim, padding: "1px 5px", borderRadius: 2, border: `1px solid ${block.level === l ? C.goldBorder : "transparent"}` }}>
                  H{l}
                </button>
              ))}
            </div>
            <textarea style={s.taH(block.level || 1)} value={block.text || ""} onChange={e => updateBlock(block.id, { text: e.target.value })} onFocus={() => setFocusedBlock(block.id)} onBlur={() => setFocusedBlock(null)} placeholder={`Heading ${block.level || 1}...`} rows={1} />
          </div>
        )}
        {block.type === "paragraph" && (
          <textarea style={s.ta} value={block.text || ""} onChange={e => updateBlock(block.id, { text: e.target.value })} onFocus={() => setFocusedBlock(block.id)} onBlur={() => setFocusedBlock(null)} placeholder="..." rows={3} />
        )}
        {block.type === "quote" && (
          <textarea style={s.taQ} value={block.text || ""} onChange={e => updateBlock(block.id, { text: e.target.value })} onFocus={() => setFocusedBlock(block.id)} onBlur={() => setFocusedBlock(null)} placeholder="Quote..." rows={2} />
        )}
        {block.type === "list" && (
          <div style={{ padding: "6px 12px" }}>
            <div style={{ display: "flex", gap: 3, marginBottom: 5 }}>
              {[false, true].map(ord => (
                <button key={String(ord)} onClick={() => updateBlock(block.id, { ordered: ord })}
                  style={{ ...s.blockBtn, fontSize: 9, backgroundColor: block.ordered === ord ? C.goldSurface : "transparent", color: block.ordered === ord ? C.gold : C.textDim, padding: "1px 7px", borderRadius: 2, border: `1px solid ${block.ordered === ord ? C.goldBorder : "transparent"}` }}>
                  {ord ? "1. Ordered" : "• List"}
                </button>
              ))}
            </div>
            {(block.items || [""]).map((item, i) => (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 5, marginBottom: 3 }}>
                <span style={{ color: C.textDim, fontSize: 11, fontFamily: font.mono, minWidth: 14, textAlign: "right" }}>
                  {block.ordered ? `${i + 1}.` : "•"}
                </span>
                <input style={{ ...s.input, padding: "3px 7px", fontSize: 12 }} value={item}
                  onChange={e => { const items = [...(block.items || [""])]; items[i] = e.target.value; updateBlock(block.id, { items }); }}
                  onKeyDown={e => {
                    if (e.key === "Enter") { e.preventDefault(); const items = [...(block.items || [""])]; items.splice(i + 1, 0, ""); updateBlock(block.id, { items }); }
                    if (e.key === "Backspace" && !item && (block.items || []).length > 1) { e.preventDefault(); const items = [...(block.items || [""])]; items.splice(i, 1); updateBlock(block.id, { items }); }
                  }}
                  placeholder={`Item ${i + 1}...`} />
              </div>
            ))}
          </div>
        )}
        {block.type === "divider" && <div style={s.dividerLine} />}
      </div>
    );
  };

  // ═══════════════════════════════════════════════════════════
  //  RENDER
  // ═══════════════════════════════════════════════════════════
  return (
    <div style={s.root}>
      <link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@400;600;700&family=Outfit:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet" />

      {/* ═══ HEADER ═══ */}
      <div style={s.header}>
        <div style={s.logoArea}>
          <span style={s.logo}>◆ {t("title", lang)}</span>
          <span style={s.ver}>v{SCHEMA_VERSION}</span>
          <span style={s.badge(status)}>
            {status === "draft" ? "●" : status === "published" ? "✓" : status === "sealing" ? "◎" : "✕"}
            {" "}{status === "draft" ? t("draft", lang) : status === "published" ? t("sealed", lang) : status === "sealing" ? "SEALING..." : "ERROR"}
          </span>
          {lastSaved && (
            <span style={{ fontSize: 9, color: C.textDim, fontFamily: font.mono }}>
              {lastSaved.toLocaleTimeString()}
            </span>
          )}
        </div>
        <div style={s.headerR}>
          {["de", "en", "pt"].map(l => (
            <button key={l} style={s.langPill(lang === l)} onClick={() => setLang(l)}>{l.toUpperCase()}</button>
          ))}
          <button style={s.themeBtn} onClick={() => setTheme(t => t === "noir" ? "klar" : "noir")}>
            {theme === "noir" ? "☀ Klar" : "◐ Noir"}
          </button>
        </div>
      </div>

      {/* ═══ MAIN ═══ */}
      <div style={s.main}>

        {/* ═══ LEFT SIDEBAR ═══ */}
        <div style={s.side}>
          {/* Templates */}
          <div>
            <div style={s.secTitle}>{t("template", lang)}</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
              {TEMPLATES.map(tpl => (
                <div key={tpl.id} style={s.tplCard(template === tpl.id)} onClick={() => setTemplate(tpl.id)}>
                  <span style={s.tplIcon(template === tpl.id)}>{tpl.icon}</span>
                  <div>
                    <div style={s.tplLabel(template === tpl.id)}>{tpl.label[lang]}</div>
                    <div style={s.tplDesc}>{tpl.desc[lang]}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Metadata */}
          <div>
            <div style={s.secTitle}>{t("metadata", lang)}</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <div>
                <label style={s.fieldLabel}>{t("docTitle", lang)} *</label>
                <input style={{ ...s.input, borderColor: validationErrors.length && !docTitle.trim() ? C.danger : C.border }} value={docTitle} onChange={e => setDocTitle(e.target.value)} placeholder="..." />
              </div>
              <div>
                <label style={s.fieldLabel}>{t("author", lang)} *</label>
                <input style={{ ...s.input, borderColor: validationErrors.length && !author.trim() ? C.danger : C.border }} value={author} onChange={e => setAuthor(e.target.value)} placeholder="..." />
              </div>
              <div>
                <label style={s.fieldLabel}>{t("impact", lang)}</label>
                <div style={s.impactRow}>
                  {IMPACT_LEVELS.map(il => (
                    <button key={il.id} style={s.impactBtn(impactLevel === il.id, il.color)} onClick={() => setImpactLevel(il.id)}>
                      <span style={s.dot(il.color)} /> {il.id}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label style={s.fieldLabel}>{t("risk", lang)}</label>
                <div style={s.riskRow}>
                  {RISK_LEVELS.map(r => (
                    <button key={r} style={s.riskBtn(riskLevel === r, r)} onClick={() => setRiskLevel(r)}>{r}</button>
                  ))}
                </div>
              </div>
              <div>
                <label style={s.fieldLabel}>{t("department", lang)}</label>
                <input style={s.input} value={department} onChange={e => setDepartment(e.target.value)} placeholder="EDITORIAL" />
              </div>
              <div>
                <label style={s.fieldLabel}>{t("language", lang)}</label>
                <div style={{ display: "flex", gap: 3 }}>
                  {["de", "en", "pt"].map(l => (
                    <button key={l} style={s.langPill(docLang === l)} onClick={() => setDocLang(l)}>{l.toUpperCase()}</button>
                  ))}
                </div>
              </div>
              <div>
                <label style={s.fieldLabel}>{t("tags", lang)}</label>
                <input style={s.input} value={tags} onChange={e => setTags(e.target.value)} placeholder="governance, compliance..." />
              </div>
            </div>
          </div>

          {/* Wallet Identity */}
          <div>
            <div style={s.secTitle}>{t("identity", lang)}</div>
            <div style={s.walletBox}>
              <div>
                <div style={{ fontSize: 10, color: walletConnected ? C.success : C.textDim }}>
                  {walletConnected ? "● Ed25519" : "○ " + t("walletSign", lang)}
                </div>
                <div style={{ fontSize: 8, color: C.textDim, fontFamily: font.mono }}>
                  Wallet :8099
                </div>
              </div>
              <button style={s.walletBtn} onClick={() => setWalletConnected(w => !w)}>
                {walletConnected ? "✓" : "→"}
              </button>
            </div>
          </div>
        </div>

        {/* ═══ CENTER EDITOR ═══ */}
        <div style={s.editor} ref={editorRef}>
          {/* Validation Errors */}
          {validationErrors.length > 0 && (
            <div style={s.errBox}>
              {validationErrors.map((e, i) => (
                <div key={i} style={s.errText}>⚠ {e}</div>
              ))}
            </div>
          )}

          {blocks.length === 0 && (
            <div style={{ textAlign: "center", padding: 36, color: C.textDim, fontSize: 12 }}>
              {t("noBlocks", lang)}
            </div>
          )}

          {blocks.map((b, i) => renderBlock(b, i))}

          {/* Add Block */}
          {showAddBlock ? (
            <div style={s.addMenu}>
              {BLOCK_TYPES.map(bt => (
                <button key={bt.type} style={s.addOpt} onClick={() => addBlock(bt.type)}
                  onMouseEnter={e => { e.currentTarget.style.borderColor = C.gold; e.currentTarget.style.color = C.gold; }}
                  onMouseLeave={e => { e.currentTarget.style.borderColor = C.border; e.currentTarget.style.color = C.textMuted; }}>
                  <span style={{ fontSize: 13 }}>{bt.icon}</span> {bt.label}
                </button>
              ))}
              <button style={{ ...s.addOpt, color: C.textDim }} onClick={() => setShowAddBlock(false)}>✕</button>
            </div>
          ) : (
            <button style={s.addBtn} onClick={() => setShowAddBlock(true)}
              onMouseEnter={e => { e.currentTarget.style.borderColor = C.gold; e.currentTarget.style.color = C.gold; }}
              onMouseLeave={e => { e.currentTarget.style.borderColor = C.border; e.currentTarget.style.color = C.textDim; }}>
              + {t("addBlock", lang)}
            </button>
          )}

          {/* Media Dropzone */}
          <div style={s.dropzone} onDragOver={e => e.preventDefault()} onDrop={handleDrop}
            onMouseEnter={e => { e.currentTarget.style.borderColor = C.gold; }}
            onMouseLeave={e => { e.currentTarget.style.borderColor = C.border; }}>
            {mediaFiles.length === 0 ? (
              <span>📎 {t("mediaZone", lang)}</span>
            ) : (
              <div style={{ display: "flex", flexWrap: "wrap" }}>
                {mediaFiles.map((f, i) => (
                  <span key={i} style={s.mediaTag}>
                    {f.name}
                    <button style={{ ...s.blockBtn, color: C.danger, fontSize: 9 }} onClick={() => setMediaFiles(prev => prev.filter((_, j) => j !== i))}>✕</button>
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* ═══ RIGHT PANEL ═══ */}
        <div style={s.right}>
          {/* Governance Hash */}
          <div>
            <div style={s.secTitle}>{t("governance", lang)}</div>
            <div style={{ marginBottom: 6 }}>
              <div style={{ fontSize: 9, color: C.textDim, marginBottom: 3 }}>{t("hashPreview", lang)}</div>
              <div style={s.hashBox}>
                {contentHash ? (
                  <>
                    <span style={{ opacity: 0.5 }}>SHA-256{" "}</span>
                    <span style={{ opacity: 0.3 }}>{t("canonical", lang)}{" "}</span>
                    <br />{contentHash}
                  </>
                ) : <span style={{ opacity: 0.3 }}>...</span>}
              </div>
              <div style={{ fontSize: 8, color: C.textDim, marginTop: 3, fontStyle: "italic" }}>
                {t("ledgerNote", lang)}
              </div>
            </div>
          </div>

          {/* Summary */}
          <div>
            <div style={s.secTitle}>{t("summary", lang)}</div>
            {[
              ["Schema", `v${SCHEMA_VERSION}`],
              ["Template", TEMPLATES.find(tp => tp.id === template)?.label[lang]],
              [t("blocks", lang), `${blocks.length}`],
              ["Impact", impactLevel],
              ["Risk", riskLevel],
              ["Lang", docLang.toUpperCase()],
              ["Wallet", walletConnected ? "Ed25519 ✓" : "—"],
              ["Media", `${mediaFiles.length} files`],
            ].map(([k, v]) => (
              <div key={k} style={s.summaryRow}>
                <span style={{ fontSize: 10, color: C.textDim }}>{k}</span>
                <span style={{ fontSize: 10, color: C.text, fontFamily: font.mono }}>{v}</span>
              </div>
            ))}
          </div>

          {/* Pipeline */}
          <div>
            <div style={s.secTitle}>{t("pipeline", lang)}</div>
            {[
              { label: "Composer", port: ":8100", live: true },
              { label: "Export Engine", port: ":8103", live: true },
              { label: "Communiqué Engine", port: ":8105", live: true },
              { label: "Forensic Ledger", port: ":8101", live: true },
              { label: "Wallet", port: ":8099", live: walletConnected },
              { label: "JMPG Viewer", port: ":8104", live: true },
            ].map(svc => (
              <div key={svc.label} style={s.pipeRow}>
                <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
                  <span style={s.pipeDot(svc.live)} />
                  <span style={{ fontSize: 10, color: C.text }}>{svc.label}</span>
                </div>
                <span style={{ fontSize: 9, color: C.textDim, fontFamily: font.mono }}>{svc.port}</span>
              </div>
            ))}
          </div>

          {/* Publish Result */}
          {publishResult && (
            <div>
              <div style={s.secTitle}>{t("result", lang)}</div>
              <div style={s.resultCard}>
                {Object.entries(publishResult).filter(([k]) => k !== "viewer_url" && k !== "public_url").map(([k, v]) => (
                  <div key={k} style={s.resultRow}>
                    <span style={s.resultKey}>{k}</span>
                    <span style={s.resultVal(typeof v === "boolean" ? v : true)}>
                      {typeof v === "boolean" ? (v ? "✓" : "✕") :
                        String(v).length > 28 ? String(v).slice(0, 12) + "…" + String(v).slice(-8) : String(v)}
                    </span>
                  </div>
                ))}
              </div>
              {/* Post-publish buttons */}
              <div style={{ display: "flex", gap: 6, marginTop: 8, flexWrap: "wrap" }}>
                {publishResult.viewer_url && (
                  <button style={s.viewerBtn} onClick={() => window.open(publishResult.viewer_url, "_blank")}>
                    <svg style={{width:14,height:14,verticalAlign:"middle",marginRight:4}} viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="9" cy="9" r="6"/><path d="M14 14L18 18"/></svg>{t("openViewer", lang)}
                  </button>
                )}
                {publishResult.public_url && (
                  <button style={s.viewerBtn} onClick={() => window.open(publishResult.public_url, "_blank")}>
                    <svg style={{width:14,height:14,verticalAlign:"middle",marginRight:4}} viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="10" cy="10" r="8"/><path d="M2 10H18"/><ellipse cx="10" cy="10" rx="4" ry="8"/></svg>{t("openPublic", lang)}
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ═══ ACTION BAR ═══ */}
      <div style={s.actionBar}>
        <div style={{ display: "flex", gap: 6 }}>
          <button style={s.actionBtn("ghost")} onClick={() => { setStatus("draft"); setPublishResult(null); setValidationErrors([]); }}>
            ○ {t("saveDraft", lang)}
          </button>
          <button style={s.actionBtn("secondary")} onClick={() => { if (validate()) setShowConfirm("jmpg"); }}>
            <svg style={{width:14,height:14,verticalAlign:"middle",marginRight:4}} viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="2" width="14" height="16" rx="2"/><line x1="7" y1="6" x2="13" y2="6"/><line x1="7" y1="10" x2="13" y2="10"/><line x1="7" y1="14" x2="10" y2="14"/></svg>{t("exportJmpg", lang)}
          </button>
        </div>
        <button style={s.actionBtn("primary")} onClick={() => { if (validate()) setShowConfirm("publish"); }}
          disabled={status === "sealing"}>
          ◆ {t("publish", lang)}
        </button>
      </div>

      {/* ═══ CONFIRM DIALOG ═══ */}
      {showConfirm && (
        <div style={s.overlay} onClick={() => setShowConfirm(null)}>
          <div style={s.confirmBox} onClick={e => e.stopPropagation()}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
              <span style={{ fontSize: 20, color: C.gold }}>◆</span>
              <span style={{ fontSize: 14, fontWeight: 700, fontFamily: font.display, color: C.text }}>
                {showConfirm === "publish" ? t("publish", lang) : t("exportJmpg", lang)}
              </span>
            </div>

            {/* Strong irreversible warning */}
            <div style={{ backgroundColor: C.warnDim, border: `1px solid rgba(245,158,11,0.2)`, borderRadius: 5, padding: "8px 10px", marginBottom: 12 }}>
              <p style={{ fontSize: 11, color: C.warn, lineHeight: 1.55, margin: 0, fontWeight: 500 }}>
                ⚠ {t("publishWarn", lang)}
              </p>
            </div>

            {/* Document summary in confirm */}
            <div style={{ display: "flex", flexDirection: "column", gap: 3, marginBottom: 12 }}>
              {[
                [t("docTitle", lang), docTitle || "—"],
                [t("author", lang), author || "—"],
                ["Template", TEMPLATES.find(tp => tp.id === template)?.label[lang]],
                ["Impact", impactLevel],
                ["Risk", riskLevel],
              ].map(([k, v]) => (
                <div key={k} style={{ display: "flex", justifyContent: "space-between" }}>
                  <span style={{ fontSize: 10, color: C.textDim }}>{k}</span>
                  <span style={{ fontSize: 10, color: C.text, fontFamily: font.mono }}>{v}</span>
                </div>
              ))}
            </div>

            {contentHash && (
              <div style={{ ...s.hashBox, marginBottom: 14, fontSize: 8 }}>
                <span style={{ opacity: 0.5 }}>SHA-256 CANONICAL: </span>{contentHash}
              </div>
            )}

            <div style={{ display: "flex", justifyContent: "flex-end", gap: 6 }}>
              <button style={s.actionBtn("ghost")} onClick={() => setShowConfirm(null)}>Cancel</button>
              <button style={s.actionBtn("primary")} onClick={showConfirm === "publish" ? handlePublish : handleExportJmpg}>
                {showConfirm === "publish" ? "◆ SEAL & PUBLISH" : <><svg style={{width:14,height:14,verticalAlign:"middle",marginRight:4}} viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="2" width="14" height="16" rx="2"/><line x1="7" y1="6" x2="13" y2="6"/><line x1="7" y1="10" x2="13" y2="10"/><line x1="7" y1="14" x2="10" y2="14"/></svg>SEAL &amp; EXPORT</>}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
