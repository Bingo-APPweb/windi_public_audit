import { useState, useMemo } from "react";

// ============================================================
// WINDI DAY-BY-DAY GOVERNANCE BRIEFING v3.0 — PLACEHOLDER
// For: master.windia4desk.tech (Showcase / Demonstration)
// Three Dragons Final Edition
// Guardian (Claude) + Architect (GPT) + Witness (Gemini)
// "Simple in Design, Rich in INHALT"
// ============================================================

const L = {
  en: {
    title: "Governance Briefing", subtitle: "Day-by-Day Report", subtitleAlt: "Tagesbericht",
    preparedFor: "Prepared for", preparedBy: "Prepared by", date: "Briefing Date", nextMeeting: "Next Meeting",
    pulse: "Governance Pulse", pulseAlt: "Governance-Puls",
    operational: "Operational", attention: "Attention Required", critical: "Critical",
    decisionsTitle: "Decisions", decisionsAlt: "Entscheidungen",
    decided: "Decided", pending: "Pending", escalated: "Escalated",
    risksTitle: "Risk Overview", risksAlt: "Risikoübersicht",
    newRisks: "New", activeRisks: "Active", resolvedRisks: "Resolved",
    holdsTitle: "Governance Holds", holdsAlt: "Governance-Holds",
    holdActive: "Active", holdReason: "Reason", holdSince: "Since", holdBy: "Initiated by",
    metricsTitle: "Key Metrics", metricsAlt: "Kennzahlen", vs: "vs prev. day",
    docsProcessed: "Docs Processed", sgeAvg: "SGE Average", complianceRate: "Compliance Rate",
    avgResponse: "Avg. Response", overrides: "Human Overrides", flagged: "Flagged Docs",
    agendaTitle: "Meeting Agenda", agendaAlt: "Besprechungsagenda",
    priority: "Priority", topic: "Topic", owner: "Owner", duration: "Est.",
    actionTitle: "Action Items", actionAlt: "Maßnahmen",
    actionItem: "Action", responsible: "Responsible", deadline: "Deadline", statusLabel: "Status",
    open: "Open", inProgress: "In Progress", done: "Done",
    notesTitle: "Secretary Notes", notesAlt: "Sekretariatshinweise",
    confidential: "CONFIDENTIAL",
    footer: "Governance-sensitive. Distribution restricted to authorized personnel.",
    high: "High", medium: "Medium", low: "Low",
    complianceTitle: "Compliance Snapshot", complianceAlt: "Compliance-Übersicht",
    euAiAct: "EU AI Act", bsiC5: "BSI C5", iso27001: "ISO 27001", gdpr: "GDPR",
    compliant: "Compliant", partial: "Partial", review: "Under Review",
    dailySummary: "Daily Summary", dailySummaryAlt: "Tageszusammenfassung",
    continuity: "Continuity", continuityAlt: "Kontinuität", intact: "INTACT",
    sessionHash: "Session Hash", sessionHashAlt: "Sitzungs-Hash",
    ledgerAnchor: "Ledger Anchor", ledgerAnchorAlt: "Ledger-Verankerung",
    signature: "Signature", signatureAlt: "Signatur",
    compDisclaimer: "Regulatory alignment status at time of report generation.",
    compDisclaimerAlt: "Stand der regulatorischen Ausrichtung zum Zeitpunkt der Berichtserstellung.",
    reportId: "Report ID", generated: "Generated",
    full: "Full", meeting: "Meeting", director: "Director", secretary: "Secretary",
    meetingBanner: "MEETING MODE — Filtered for decision-relevant items",
    meetingBannerAlt: "MEETING-MODUS — Gefiltert auf entscheidungsrelevante Inhalte",
    directorBanner: "DIRECTOR VIEW — Decisions, risks, and compliance focus",
    directorBannerAlt: "DIREKTOR-ANSICHT — Fokus auf Entscheidungen, Risiken und Compliance",
    printFull: "Print Briefing", printMeeting: "Print Meeting Brief",
    printDirector: "Print Director Brief", printSecretary: "Print Full Briefing",
    economicImpact: "Economic Impact Forecast", economicImpactAlt: "Prognose wirtschaftl. Auswirkung",
    burnRate: "Est. daily burn rate", burnRateAlt: "Geschätzter Tagesverlust",
    basedOn: "Based on cluster avg. volume", basedOnAlt: "Basierend auf Cluster-Durchschnittsvolumen",
    viewLabel: "View", modeLabel: "Mode",
    condensed: "~10 min focus",
    signatureBlock: "Director Signature",
    signatureBlockAlt: "Unterschrift Direktor",
    dateField: "Date", dateFieldAlt: "Datum",
    signHere: "___________________________",
    showcaseBanner: "SHOWCASE — Example data for demonstration purposes",
    showcaseBannerAlt: "BEISPIEL — Demodaten zu Demonstrationszwecken",
  },
  de: {
    title: "Governance-Briefing", subtitle: "Tagesbericht", subtitleAlt: "Day-by-Day Report",
    preparedFor: "Erstellt für", preparedBy: "Erstellt von", date: "Briefing-Datum", nextMeeting: "Nächste Besprechung",
    pulse: "Governance-Puls", pulseAlt: "Governance Pulse",
    operational: "Betriebsbereit", attention: "Aufmerksamkeit erfordl.", critical: "Kritisch",
    decisionsTitle: "Entscheidungen", decisionsAlt: "Decisions",
    decided: "Entschieden", pending: "Ausstehend", escalated: "Eskaliert",
    risksTitle: "Risikoübersicht", risksAlt: "Risk Overview",
    newRisks: "Neu", activeRisks: "Aktiv", resolvedRisks: "Gelöst",
    holdsTitle: "Governance-Holds", holdsAlt: "Governance Holds",
    holdActive: "Aktiv", holdReason: "Grund", holdSince: "Seit", holdBy: "Eingeleitet von",
    metricsTitle: "Kennzahlen", metricsAlt: "Key Metrics", vs: "gg. Vortag",
    docsProcessed: "Verarb. Dokumente", sgeAvg: "SGE-Durchschnitt", complianceRate: "Compliance-Quote",
    avgResponse: "Ø Reaktionszeit", overrides: "Menschl. Übersteuerg.", flagged: "Markierte Dok.",
    agendaTitle: "Besprechungsagenda", agendaAlt: "Meeting Agenda",
    priority: "Priorität", topic: "Thema", owner: "Verantwortlich", duration: "Dauer",
    actionTitle: "Maßnahmen", actionAlt: "Action Items",
    actionItem: "Maßnahme", responsible: "Verantwortlich", deadline: "Frist", statusLabel: "Status",
    open: "Offen", inProgress: "In Bearbeitung", done: "Erledigt",
    notesTitle: "Sekretariatshinweise", notesAlt: "Secretary Notes",
    confidential: "VERTRAULICH",
    footer: "Governance-relevant. Verteilung nur an autorisiertes Personal.",
    high: "Hoch", medium: "Mittel", low: "Niedrig",
    complianceTitle: "Compliance-Übersicht", complianceAlt: "Compliance Snapshot",
    euAiAct: "EU AI Act", bsiC5: "BSI C5", iso27001: "ISO 27001", gdpr: "DSGVO",
    compliant: "Konform", partial: "Teilweise", review: "In Prüfung",
    dailySummary: "Tageszusammenfassung", dailySummaryAlt: "Daily Summary",
    continuity: "Kontinuität", continuityAlt: "Continuity", intact: "INTAKT",
    sessionHash: "Sitzungs-Hash", sessionHashAlt: "Session Hash",
    ledgerAnchor: "Ledger-Verankerung", ledgerAnchorAlt: "Ledger Anchor",
    signature: "Signatur", signatureAlt: "Signature",
    compDisclaimer: "Stand der regulatorischen Ausrichtung zum Zeitpunkt der Berichtserstellung.",
    compDisclaimerAlt: "Regulatory alignment status at time of report generation.",
    reportId: "Berichts-ID", generated: "Erstellt",
    full: "Voll", meeting: "Meeting", director: "Direktor", secretary: "Sekretariat",
    meetingBanner: "MEETING-MODUS — Gefiltert auf entscheidungsrelevante Inhalte",
    meetingBannerAlt: "MEETING MODE — Filtered for decision-relevant items",
    directorBanner: "DIREKTOR-ANSICHT — Fokus auf Entscheidungen, Risiken und Compliance",
    directorBannerAlt: "DIRECTOR VIEW — Decisions, risks, and compliance focus",
    printFull: "Briefing drucken", printMeeting: "Meeting-Briefing drucken",
    printDirector: "Direktor-Briefing drucken", printSecretary: "Voll-Briefing drucken",
    economicImpact: "Prognose wirtschaftl. Auswirkung", economicImpactAlt: "Economic Impact Forecast",
    burnRate: "Geschätzter Tagesverlust", burnRateAlt: "Est. daily burn rate",
    basedOn: "Basierend auf Cluster-Durchschnittsvolumen", basedOnAlt: "Based on cluster avg. volume",
    viewLabel: "Ansicht", modeLabel: "Modus",
    condensed: "~10 Min. Fokus",
    signatureBlock: "Unterschrift Direktor",
    signatureBlockAlt: "Director Signature",
    dateField: "Datum", dateFieldAlt: "Date",
    signHere: "___________________________",
    showcaseBanner: "BEISPIEL — Demodaten zu Demonstrationszwecken",
    showcaseBannerAlt: "SHOWCASE — Example data for demonstration purposes",
  },
};

// ============================================================
// PLACEHOLDER DATA — Realistic governance scenario
// ============================================================

const D = {
  director: "Dr. M. Weber", secretary: "S. Bergmann", meeting: "09:30",
  systemStatus: "operational", reportId: "GBR-2026-02-05", genTime: "08:12 CET",
  hash: "3f9c7a2e…a81e", ledgerRef: "RFC003-DAY-2026-02-05", contDays: 18,
  summary: {
    en: "Document processing stable at 142 units. One new R3 risk flagged on supplier contract cluster — under SGE review. Three pending decisions require Director approval before 14:00. Compliance rate improved to 96.8% after VerpackG certificate renewal. Governance continuity uninterrupted for 18 consecutive days.",
    de: "Dokumentenverarbeitung stabil bei 142 Einheiten. Ein neues R3-Risiko bei Lieferantenvertrags-Cluster identifiziert — SGE-Prüfung läuft. Drei ausstehende Entscheidungen erfordern Direktorfreigabe vor 14:00 Uhr. Compliance-Quote auf 96,8% verbessert nach VerpackG-Zertifikatserneuerung. Governance-Kontinuität seit 18 Tagen ununterbrochen.",
  },
  decisions: [
    { id: "DEC-047", topic: { en: "Supplier contract renewal — Cluster B", de: "Lieferantenvertragsverlängerung — Cluster B" }, status: "pending", sge: "R3", urgency: "high" },
    { id: "DEC-048", topic: { en: "Budget reallocation Q1 marketing", de: "Budgetumschichtung Q1 Marketing" }, status: "pending", sge: "R2", urgency: "medium" },
    { id: "DEC-049", topic: { en: "New data processor agreement", de: "Neue Auftragsverarbeitungsvereinbarung" }, status: "pending", sge: "R2", urgency: "high" },
    { id: "DEC-044", topic: { en: "Office lease extension approved", de: "Büromietverlängerung genehmigt" }, status: "decided", sge: "R1", urgency: "low" },
    { id: "DEC-045", topic: { en: "IT security patch rollout approved", de: "IT-Sicherheitspatch-Rollout genehmigt" }, status: "decided", sge: "R1", urgency: "medium" },
  ],
  risks: { new: 1, active: 4, resolved: 2 },
  riskDetails: [
    { id: "RSK-112", level: "R3", desc: { en: "Supplier contract value mismatch", de: "Wertabweichung Lieferantenvertrag" }, status: "new", urgency: "high" },
    { id: "RSK-108", level: "R2", desc: { en: "Delayed LUCID registration update", de: "Verzögerte LUCID-Aktualisierung" }, status: "active", urgency: "medium" },
    { id: "RSK-103", level: "R2", desc: { en: "Cross-dept approval chain incomplete", de: "Abt.-übergreifende Freigabekette unvollständig" }, status: "active", urgency: "medium" },
    { id: "RSK-099", level: "R1", desc: { en: "Minor template version mismatch", de: "Geringfügige Template-Abweichung" }, status: "active", urgency: "low" },
  ],
  holds: [{
    id: "HOLD-7A3F", reason: { en: "SGE score below threshold on contract cluster", de: "SGE-Wert unter Schwellenwert bei Vertragscluster" },
    since: "04.02.2026 16:42", by: "SGE Auto-Hold", level: "S2", burn: "€4,200", cluster: "Cluster B",
  }],
  metrics: [
    { k: "docsProcessed", v: 142, p: 138, u: "" },
    { k: "sgeAvg", v: 81.2, p: 79.8, u: "" },
    { k: "complianceRate", v: 96.8, p: 95.4, u: "%" },
    { k: "avgResponse", v: 2.4, p: 2.7, u: "h", inv: true },
    { k: "overrides", v: 3, p: 5, u: "", inv: true },
    { k: "flagged", v: 4, p: 6, u: "", inv: true },
  ],
  agenda: [
    { topic: { en: "Review flagged supplier contracts", de: "Prüfung markierter Lieferantenverträge" }, owner: "Dr. Weber", pr: "high", dur: "15 min" },
    { topic: { en: "Q1 budget reallocation decision", de: "Entscheidung Budgetumschichtung Q1" }, owner: "F. Klein", pr: "high", dur: "10 min" },
    { topic: { en: "LUCID registration status", de: "Status LUCID-Registrierung" }, owner: "A. Richter", pr: "medium", dur: "5 min" },
    { topic: { en: "Data processor agreement review", de: "Prüfung AV-Vereinbarung" }, owner: "Dr. Weber", pr: "high", dur: "10 min" },
    { topic: { en: "Weekly compliance summary", de: "Wöchentliche Compliance-Zusammenfassung" }, owner: "S. Bergmann", pr: "low", dur: "5 min" },
  ],
  actions: [
    { a: { en: "Sign supplier contract amendment", de: "Lieferantenvertragsnachtrag unterzeichnen" }, r: "Dr. Weber", dl: "05.02.2026", s: "open" },
    { a: { en: "Confirm LUCID registration renewal", de: "LUCID-Erneuerung bestätigen" }, r: "A. Richter", dl: "07.02.2026", s: "inProgress" },
    { a: { en: "Review data processor DPA draft", de: "Entwurf AV-Vereinbarung prüfen" }, r: "Legal", dl: "06.02.2026", s: "open" },
    { a: { en: "Archive Q4 audit documentation", de: "Q4-Auditdokumentation archivieren" }, r: "S. Bergmann", dl: "10.02.2026", s: "done" },
  ],
  notes: {
    en: "• Room B2 reserved 09:30–10:15\n• Contract summary in folder (Tab 3)\n• F. Klein remote — video link sent\n• Coffee & water arranged\n• Signature slot blocked 14:00–14:30",
    de: "• Raum B2 reserviert 09:30–10:15\n• Vertragsübersicht in Mappe (Reiter 3)\n• F. Klein remote — Videolink versendet\n• Kaffee & Wasser bereit\n• Unterschriftentermin 14:00–14:30 blockiert",
  },
  compliance: [
    { k: "euAiAct", s: "compliant" }, { k: "bsiC5", s: "review" },
    { k: "iso27001", s: "compliant" }, { k: "gdpr", s: "compliant" },
  ],
};

// ============================================================
// ATOMS
// ============================================================

const mono = "'IBM Plex Mono', monospace";
const serif = "'Newsreader', Georgia, serif";

function Dot({ status }) {
  const c = { operational: "#22c55e", attention: "#f59e0b", critical: "#ef4444" }[status] || "#999";
  return <span style={{ display: "inline-block", width: "8px", height: "8px", borderRadius: "50%", background: c, boxShadow: `0 0 5px ${c}50` }} />;
}

function Bg({ bg, color, border, label }) {
  return <span style={{ fontSize: "9.5px", fontWeight: "600", padding: "2px 7px", borderRadius: "3px", background: bg, color, border: `1px solid ${border}`, fontFamily: mono, whiteSpace: "nowrap" }}>{label}</span>;
}

function Pri({ level, t }) {
  const m = { high: ["#fef2f2","#dc2626","#fecaca"], medium: ["#fffbeb","#d97706","#fde68a"], low: ["#f0fdf4","#16a34a","#bbf7d0"] };
  const c = m[level] || m.low;
  return <Bg bg={c[0]} color={c[1]} border={c[2]} label={t[level]} />;
}

function Rsk({ level }) {
  const c = { R0:"#22c55e", R1:"#84cc16", R2:"#eab308", R3:"#f97316", R4:"#ef4444", R5:"#7f1d1d" }[level] || "#999";
  return <Bg bg={`${c}15`} color={c} border={`${c}40`} label={level} />;
}

function Sts({ status, t }) {
  const m = {
    decided:["#f0fdf4","#16a34a","#bbf7d0",t.decided], pending:["#fffbeb","#d97706","#fde68a",t.pending],
    escalated:["#fef2f2","#dc2626","#fecaca",t.escalated], open:["#fffbeb","#d97706","#fde68a",t.open],
    inProgress:["#eff6ff","#2563eb","#bfdbfe",t.inProgress], done:["#f0fdf4","#16a34a","#bbf7d0",t.done],
    compliant:["#f0fdf4","#16a34a","#bbf7d0",t.compliant], partial:["#fffbeb","#d97706","#fde68a",t.partial],
    review:["#eff6ff","#2563eb","#bfdbfe",t.review], new:["#fef2f2","#dc2626","#fecaca",t.newRisks],
    active:["#fffbeb","#d97706","#fde68a",t.activeRisks],
  };
  const c = m[status] || m.open;
  return <Bg bg={c[0]} color={c[1]} border={c[2]} label={c[3]} />;
}

function Trend({ cur, prev, inv }) {
  const d = cur - prev; const p = prev ? Math.abs((d/prev)*100).toFixed(1) : "0";
  const up = d > 0; const good = inv ? !up : up;
  return <span style={{ fontSize: "10.5px", fontWeight: "600", color: d === 0 ? "#999" : good ? "#16a34a" : "#dc2626", fontFamily: mono }}>{d === 0 ? "—" : `${up ? "↑" : "↓"} ${p}%`}</span>;
}

function Metric({ label, v, u, p, t, inv }) {
  return (
    <div style={{ padding: "11px 13px", background: "#fff", border: "1px solid #e8e4dc", borderRadius: "4px" }}>
      <div style={{ fontSize: "8.5px", color: "#8c8578", fontFamily: mono, letterSpacing: "0.4px", marginBottom: "4px", textTransform: "uppercase" }}>{label}</div>
      <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between" }}>
        <span style={{ fontSize: "22px", fontWeight: "700", color: "#1a1814", fontFamily: serif }}>{v}<span style={{ fontSize: "12px", color: "#8c8578" }}>{u}</span></span>
        <Trend cur={v} prev={p} inv={inv} />
      </div>
      <div style={{ fontSize: "8.5px", color: "#b0a898", fontFamily: mono, marginTop: "2px" }}>{t.vs}: {p}{u}</div>
    </div>
  );
}

function Sec({ children, alt, n }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "7px", marginBottom: "10px", marginTop: "24px" }}>
      {n && <span style={{ width: "18px", height: "18px", borderRadius: "3px", background: "#1a1814", color: "#faf8f4", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "9px", fontWeight: "700", fontFamily: mono, flexShrink: 0 }}>{n}</span>}
      <span style={{ fontSize: "11px", fontWeight: "700", color: "#1a1814", fontFamily: mono, letterSpacing: "1px", textTransform: "uppercase" }}>{children}</span>
      {alt && <span style={{ fontSize: "9px", color: "#b0a898", fontFamily: mono, fontStyle: "italic" }}>/ {alt}</span>}
      <div style={{ flex: 1, height: "1px", background: "#e0dbd2" }} />
    </div>
  );
}

// ============================================================
// CONTROL BAR BUTTON
// ============================================================

function BarBtn({ active, label, onClick }) {
  return (
    <button onClick={onClick} style={{
      padding: "4px 11px", background: active ? "#c9a84c" : "transparent",
      color: active ? "#1a1814" : "#777", border: "none", cursor: "pointer",
      fontSize: "9.5px", fontWeight: "600", fontFamily: mono, transition: "all 0.15s",
    }}>{label}</button>
  );
}

// ============================================================
// MAIN — PLACEHOLDER VERSION
// ============================================================

export default function WindiDayByDayPlaceholder() {
  const [lang, setLang] = useState("de");
  const [mode, setMode] = useState("full");
  const [view, setView] = useState("secretary");
  const t = L[lang];

  const isMeeting = mode === "meeting";
  const isDirector = view === "director";

  const decisions = useMemo(() => isMeeting ? D.decisions.filter(d => d.status === "pending") : D.decisions, [isMeeting]);
  const risks = useMemo(() => isMeeting ? D.riskDetails.filter(r => r.urgency === "high" || r.status === "new") : D.riskDetails, [isMeeting]);
  const agenda = useMemo(() => isMeeting ? D.agenda.filter(a => a.pr === "high") : D.agenda, [isMeeting]);
  const actions = useMemo(() => isMeeting ? D.actions.filter(a => a.s === "open") : D.actions, [isMeeting]);

  const pendC = D.decisions.filter(d => d.status === "pending").length;
  const decC = D.decisions.filter(d => d.status === "decided").length;

  let sn = 0;
  const nx = () => String(++sn);

  const showMetrics = !isMeeting;
  const showNotes = !isDirector;
  const showCompliance = !isMeeting;
  const showSignature = isDirector;

  const printLabel = isMeeting ? t.printMeeting : isDirector ? t.printDirector : t.printFull;

  return (
    <div style={{ minHeight: "100vh", background: "#eae6de", fontFamily: serif, color: "#1a1814" }}>
      <link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,300;0,6..72,400;0,6..72,500;0,6..72,600;0,6..72,700;1,6..72,400&family=IBM+Plex+Mono:wght@300;400;500;600;700&display=swap" rel="stylesheet" />

      {/* ======== SHOWCASE BANNER ======== */}
      <div className="np" style={{
        padding: "5px 20px", background: "linear-gradient(90deg, #c9a84c, #e8c84c, #c9a84c)",
        color: "#1a1814", fontSize: "9.5px", fontFamily: mono, fontWeight: "600",
        textAlign: "center", letterSpacing: "1.5px",
        display: "flex", justifyContent: "center", gap: "8px", alignItems: "center",
      }}>
        <span>◈</span>
        <span>{t.showcaseBanner}</span>
        <span style={{ opacity: 0.5 }}>/ {t.showcaseBannerAlt}</span>
        <span>◈</span>
      </div>

      {/* ======== TOP BAR ======== */}
      <div className="np" style={{ padding: "8px 20px", background: "#1a1814", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "6px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span style={{ color: "#c9a84c", fontSize: "12px", fontWeight: "700", fontFamily: mono, letterSpacing: "2px" }}>WINDI</span>
          <span style={{ color: "#444", fontSize: "10px", fontFamily: mono }}>Day-by-Day v3.0</span>
          <span style={{ color: "#c9a84c", fontSize: "8px", fontFamily: mono, padding: "1px 6px", border: "1px solid #c9a84c40", borderRadius: "2px", opacity: 0.7 }}>PLACEHOLDER</span>
        </div>
        <div style={{ display: "flex", gap: "5px", alignItems: "center" }}>
          <span style={{ fontSize: "8px", color: "#555", fontFamily: mono, marginRight: "2px" }}>{t.viewLabel}:</span>
          <div style={{ display: "flex", borderRadius: "3px", overflow: "hidden", border: "1px solid #333" }}>
            <BarBtn active={view === "secretary"} label={t.secretary} onClick={() => setView("secretary")} />
            <BarBtn active={view === "director"} label={t.director} onClick={() => setView("director")} />
          </div>
          <span style={{ fontSize: "8px", color: "#555", fontFamily: mono, marginLeft: "6px", marginRight: "2px" }}>{t.modeLabel}:</span>
          <div style={{ display: "flex", borderRadius: "3px", overflow: "hidden", border: "1px solid #333" }}>
            <BarBtn active={mode === "full"} label={t.full} onClick={() => setMode("full")} />
            <BarBtn active={mode === "meeting"} label={`⚡ ${t.meeting}`} onClick={() => setMode("meeting")} />
          </div>
          <div style={{ display: "flex", borderRadius: "3px", overflow: "hidden", border: "1px solid #333", marginLeft: "4px" }}>
            <BarBtn active={lang === "de"} label="DE" onClick={() => setLang("de")} />
            <BarBtn active={lang === "en"} label="EN" onClick={() => setLang("en")} />
          </div>
          <button onClick={() => window.print()} style={{
            padding: "4px 12px", background: "transparent", border: "1px solid #c9a84c",
            borderRadius: "3px", color: "#c9a84c", fontSize: "9.5px", fontWeight: "600",
            cursor: "pointer", fontFamily: mono, marginLeft: "4px",
          }}>{printLabel}</button>
        </div>
      </div>

      {/* ======== PAGE ======== */}
      <div style={{ maxWidth: "780px", margin: "16px auto", padding: "0 12px" }}>
        <div style={{ background: "#faf8f4", borderRadius: "3px", boxShadow: "0 1px 5px rgba(0,0,0,0.05)", overflow: "hidden" }}>

          {isMeeting && (
            <div style={{ padding: "6px 32px", background: "#c9a84c", color: "#1a1814", fontSize: "10px", fontFamily: mono, fontWeight: "600", display: "flex", gap: "6px" }}>
              <span>⚡ {t.meetingBanner}</span>
              <span style={{ opacity: 0.4 }}>/ {t.meetingBannerAlt}</span>
            </div>
          )}
          {isDirector && !isMeeting && (
            <div style={{ padding: "6px 32px", background: "#1a1814", color: "#c9a84c", fontSize: "10px", fontFamily: mono, fontWeight: "600", display: "flex", gap: "6px", borderBottom: "1px solid #333" }}>
              <span>◆ {t.directorBanner}</span>
              <span style={{ opacity: 0.4 }}>/ {t.directorBannerAlt}</span>
            </div>
          )}

          {/* ======== HEADER ======== */}
          <div style={{ padding: "24px 32px 18px", borderBottom: "3px solid #1a1814" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "12px" }}>
              <div>
                <div style={{ fontSize: "8.5px", fontFamily: mono, letterSpacing: "3px", color: "#c9a84c", fontWeight: "600", marginBottom: "2px" }}>WINDI GOVERNANCE</div>
                <div style={{ fontSize: "24px", fontWeight: "700", lineHeight: 1.1, letterSpacing: "-0.3px" }}>{t.title}</div>
                <div style={{ fontSize: "13px", color: "#8c8578", fontStyle: "italic", marginTop: "1px" }}>
                  {t.subtitle} <span style={{ color: "#c5bdb0" }}>/ {t.subtitleAlt}</span>
                </div>
              </div>
              <div style={{ padding: "6px 10px", background: "#1a1814", borderRadius: "3px", display: "flex", alignItems: "center", gap: "6px" }}>
                <Dot status={D.systemStatus} />
                <span style={{ color: "#faf8f4", fontSize: "9.5px", fontFamily: mono, fontWeight: "500" }}>{t[D.systemStatus]}</span>
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: "1px", background: "#e0dbd2", border: "1px solid #e0dbd2", borderRadius: "3px", overflow: "hidden" }}>
              {[
                [t.date, "05.02.2026"], [t.preparedFor, D.director], [t.preparedBy, D.secretary], [t.nextMeeting, D.meeting],
              ].map(([label, val], i) => (
                <div key={i} style={{ padding: "7px 10px", background: "#faf8f4" }}>
                  <div style={{ fontSize: "7.5px", fontFamily: mono, letterSpacing: "0.5px", color: "#8c8578", textTransform: "uppercase", marginBottom: "1px" }}>{label}</div>
                  <div style={{ fontSize: "12.5px", fontWeight: "600" }}>{val}</div>
                </div>
              ))}
            </div>

            <div style={{ marginTop: "8px", padding: "4px 9px", background: "#f5f2eb", border: "1px solid #e8e4dc", borderRadius: "3px", fontFamily: mono, fontSize: "8px", color: "#8c8578", display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: "4px" }}>
              <span>{t.sessionHash} <span style={{ opacity: 0.4 }}>/ {t.sessionHashAlt}</span>: <b style={{ color: "#1a1814" }}>{D.hash}</b></span>
              <span>{t.ledgerAnchor} <span style={{ opacity: 0.4 }}>/ {t.ledgerAnchorAlt}</span>: <b style={{ color: "#1a1814" }}>{D.ledgerRef}</b></span>
              <span>{t.signature} <span style={{ opacity: 0.4 }}>/ {t.signatureAlt}</span>: <b style={{ color: "#16a34a" }}>WINDI-CORE ✓</b></span>
            </div>
          </div>

          {/* ======== BODY ======== */}
          <div style={{ padding: "2px 32px 28px" }}>

            {/* 1. Summary */}
            <Sec n={nx()} alt={t.dailySummaryAlt}>{t.dailySummary}</Sec>
            <div style={{ padding: "12px 14px", background: "#f5f2eb", borderLeft: "3px solid #c9a84c", borderRadius: "0 3px 3px 0", fontSize: "13px", lineHeight: 1.7, color: "#3d3830" }}>
              {D.summary[lang]}
            </div>

            {/* 2. Pulse + Continuity */}
            <Sec n={nx()} alt={t.pulseAlt}>{t.pulse}</Sec>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: "8px" }}>
              {[
                { label: t.decisionsTitle, items: [[pendC, t.pending, "#d97706", "#fffbeb"], [decC, t.decided, "#16a34a", "#f0fdf4"]] },
                { label: t.risksTitle, items: [[D.risks.new, t.newRisks, "#dc2626", "#fef2f2"], [D.risks.active, t.activeRisks, "#d97706", "#fffbeb"], [D.risks.resolved, t.resolvedRisks, "#16a34a", "#f0fdf4"]] },
                { label: t.holdsTitle, items: [[D.holds.length, t.holdActive, D.holds.length > 0 ? "#dc2626" : "#16a34a", D.holds.length > 0 ? "#fef2f2" : "#f0fdf4"]] },
                { label: `${t.continuity} / ${t.continuityAlt}`, items: [[t.intact, `${D.contDays}d`, "#16a34a", "#f0fdf4"]] },
              ].map((g, i) => (
                <div key={i} style={{ padding: "10px", background: "#fff", border: "1px solid #e8e4dc", borderRadius: "4px" }}>
                  <div style={{ fontSize: "8px", fontFamily: mono, letterSpacing: "0.7px", color: "#8c8578", textTransform: "uppercase", marginBottom: "7px" }}>{g.label}</div>
                  {g.items.map(([n, l, c, bg], j) => (
                    <div key={j} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "3px" }}>
                      <span style={{ fontSize: "10.5px", color: "#5c5549" }}>{l}</span>
                      <span style={{ fontSize: "12px", fontWeight: "700", color: c, padding: "1px 6px", borderRadius: "3px", background: bg, fontFamily: mono }}>{n}</span>
                    </div>
                  ))}
                </div>
              ))}
            </div>

            {/* 3. Metrics */}
            {showMetrics && (
              <>
                <Sec n={nx()} alt={t.metricsAlt}>{t.metricsTitle}</Sec>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "7px" }}>
                  {D.metrics.map((m, i) => <Metric key={i} label={t[m.k]} v={m.v} u={m.u} p={m.p} t={t} inv={m.inv} />)}
                </div>
              </>
            )}

            {/* 4. Decisions */}
            <Sec n={nx()} alt={t.decisionsAlt}>{t.decisionsTitle}</Sec>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px" }}>
              <thead><tr style={{ borderBottom: "2px solid #1a1814" }}>
                <th style={{ ...th, width: "55px" }}>ID</th>
                <th style={th}>{t.topic}</th>
                <th style={{ ...th, width: "40px", textAlign: "center" }}>SGE</th>
                <th style={{ ...th, width: "60px", textAlign: "center" }}>{t.priority}</th>
                <th style={{ ...th, width: "80px", textAlign: "center" }}>{t.statusLabel}</th>
              </tr></thead>
              <tbody>
                {decisions.map((d, i) => (
                  <tr key={i} style={{ borderBottom: "1px solid #e8e4dc" }}>
                    <td style={{ ...td, fontFamily: mono, fontSize: "9.5px", color: "#8c8578" }}>{d.id}</td>
                    <td style={td}>{d.topic[lang]}</td>
                    <td style={{ ...td, textAlign: "center" }}><Rsk level={d.sge} /></td>
                    <td style={{ ...td, textAlign: "center" }}><Pri level={d.urgency} t={t} /></td>
                    <td style={{ ...td, textAlign: "center" }}><Sts status={d.status} t={t} /></td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* 5. Risks */}
            <Sec n={nx()} alt={t.risksAlt}>{t.risksTitle}</Sec>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px" }}>
              <thead><tr style={{ borderBottom: "2px solid #1a1814" }}>
                <th style={{ ...th, width: "60px" }}>ID</th>
                <th style={{ ...th, width: "36px", textAlign: "center" }}>SGE</th>
                <th style={th}>{lang === "de" ? "Beschreibung" : "Description"}</th>
                <th style={{ ...th, width: "65px", textAlign: "center" }}>{t.statusLabel}</th>
              </tr></thead>
              <tbody>
                {risks.map((r, i) => (
                  <tr key={i} style={{ borderBottom: "1px solid #e8e4dc" }}>
                    <td style={{ ...td, fontFamily: mono, fontSize: "9.5px", color: "#8c8578" }}>{r.id}</td>
                    <td style={{ ...td, textAlign: "center" }}><Rsk level={r.level} /></td>
                    <td style={td}>{r.desc[lang]}</td>
                    <td style={{ ...td, textAlign: "center" }}><Sts status={r.status} t={t} /></td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* 6. Holds + Economic Impact */}
            {D.holds.length > 0 && (
              <>
                <Sec n={nx()} alt={t.holdsAlt}>{t.holdsTitle}</Sec>
                {D.holds.map((h, i) => (
                  <div key={i} style={{ padding: "12px 14px", background: "#fef2f2", border: "1px solid #fecaca", borderLeft: "4px solid #dc2626", borderRadius: "0 4px 4px 0", marginBottom: "6px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                      <span style={{ fontFamily: mono, fontSize: "10.5px", fontWeight: "700", color: "#dc2626" }}>{h.id}</span>
                      <span style={{ fontFamily: mono, fontSize: "8.5px", color: "#999", background: "#fff", padding: "1px 6px", borderRadius: "2px" }}>{h.level}</span>
                    </div>
                    <div style={{ fontSize: "12.5px", color: "#3d3830", marginBottom: "5px" }}>
                      <strong>{t.holdReason}:</strong> {h.reason[lang]}
                    </div>
                    <div style={{ display: "flex", gap: "14px", fontSize: "10.5px", color: "#8c8578", marginBottom: "8px", flexWrap: "wrap" }}>
                      <span><strong>{t.holdSince}:</strong> {h.since}</span>
                      <span><strong>{t.holdBy}:</strong> {h.by}</span>
                    </div>
                    <div style={{ padding: "8px 10px", background: "#fff5f5", border: "1px dashed #fca5a5", borderRadius: "3px" }}>
                      <div style={{ fontSize: "8px", fontFamily: mono, letterSpacing: "0.8px", color: "#dc2626", textTransform: "uppercase", marginBottom: "3px" }}>
                        {t.economicImpact} <span style={{ opacity: 0.4 }}>/ {t.economicImpactAlt}</span>
                      </div>
                      <div style={{ display: "flex", alignItems: "baseline", gap: "6px" }}>
                        <span style={{ fontSize: "20px", fontWeight: "700", color: "#dc2626", fontFamily: serif }}>{h.burn}</span>
                        <span style={{ fontSize: "10px", color: "#8c8578" }}>/ day</span>
                      </div>
                      <div style={{ fontSize: "9px", color: "#999", fontFamily: mono, marginTop: "2px" }}>
                        {t.burnRate} ({h.cluster}). {t.basedOn}.
                      </div>
                    </div>
                  </div>
                ))}
              </>
            )}

            {/* 7. Agenda */}
            <Sec n={nx()} alt={t.agendaAlt}>{t.agendaTitle}</Sec>
            {isMeeting && (
              <div style={{ fontSize: "9px", fontFamily: mono, color: "#c9a84c", marginBottom: "6px", marginTop: "-6px" }}>
                {t.condensed}
              </div>
            )}
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px" }}>
              <thead><tr style={{ borderBottom: "2px solid #1a1814" }}>
                <th style={{ ...th, width: "22px", textAlign: "center" }}>#</th>
                <th style={th}>{t.topic}</th>
                <th style={{ ...th, width: "80px" }}>{t.owner}</th>
                <th style={{ ...th, width: "55px", textAlign: "center" }}>{t.priority}</th>
                <th style={{ ...th, width: "48px", textAlign: "center" }}>{t.duration}</th>
              </tr></thead>
              <tbody>
                {agenda.map((a, i) => (
                  <tr key={i} style={{ borderBottom: "1px solid #e8e4dc" }}>
                    <td style={{ ...td, textAlign: "center", fontFamily: mono, fontSize: "9.5px", color: "#8c8578" }}>{i + 1}</td>
                    <td style={td}>{a.topic[lang]}</td>
                    <td style={{ ...td, fontSize: "10.5px", color: "#5c5549" }}>{a.owner}</td>
                    <td style={{ ...td, textAlign: "center" }}><Pri level={a.pr} t={t} /></td>
                    <td style={{ ...td, textAlign: "center", fontFamily: mono, fontSize: "9.5px", color: "#8c8578" }}>{isMeeting ? "5–10'" : a.dur}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* 8. Actions */}
            <Sec n={nx()} alt={t.actionAlt}>{t.actionTitle}</Sec>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px" }}>
              <thead><tr style={{ borderBottom: "2px solid #1a1814" }}>
                <th style={th}>{t.actionItem}</th>
                <th style={{ ...th, width: "80px" }}>{t.responsible}</th>
                <th style={{ ...th, width: "75px", textAlign: "center" }}>{t.deadline}</th>
                <th style={{ ...th, width: "80px", textAlign: "center" }}>{t.statusLabel}</th>
              </tr></thead>
              <tbody>
                {actions.map((a, i) => (
                  <tr key={i} style={{ borderBottom: "1px solid #e8e4dc" }}>
                    <td style={td}>{a.a[lang]}</td>
                    <td style={{ ...td, fontSize: "10.5px", color: "#5c5549" }}>{a.r}</td>
                    <td style={{ ...td, textAlign: "center", fontFamily: mono, fontSize: "9.5px" }}>{a.dl}</td>
                    <td style={{ ...td, textAlign: "center" }}><Sts status={a.s} t={t} /></td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* 9. Compliance */}
            {showCompliance && (
              <>
                <Sec n={nx()} alt={t.complianceAlt}>{t.complianceTitle}</Sec>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: "7px" }}>
                  {D.compliance.map((c, i) => (
                    <div key={i} style={{ padding: "9px", background: "#fff", border: "1px solid #e8e4dc", borderRadius: "4px", textAlign: "center" }}>
                      <div style={{ fontSize: "9.5px", fontFamily: mono, fontWeight: "600", color: "#1a1814", marginBottom: "4px" }}>{t[c.k]}</div>
                      <Sts status={c.s} t={t} />
                    </div>
                  ))}
                </div>
                <div style={{ marginTop: "6px", fontSize: "8.5px", color: "#8c8578", fontFamily: mono, fontStyle: "italic" }}>
                  {t.compDisclaimer} <span style={{ opacity: 0.4 }}>/ {t.compDisclaimerAlt}</span>
                </div>
              </>
            )}

            {/* 10. Secretary Notes */}
            {showNotes && (
              <>
                <Sec n={nx()} alt={t.notesAlt}>{t.notesTitle}</Sec>
                <div style={{ padding: "12px 14px", background: "#fffde7", border: "1px solid #fde68a", borderRadius: "4px", fontSize: "12px", lineHeight: 1.8, color: "#5c5549", whiteSpace: "pre-line" }}>
                  {D.notes[lang]}
                </div>
              </>
            )}

            {/* Director: Signature Block */}
            {showSignature && (
              <>
                <Sec n={nx()} alt={t.signatureBlockAlt}>{t.signatureBlock}</Sec>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px", padding: "16px 0 8px" }}>
                  <div>
                    <div style={{ fontSize: "9px", fontFamily: mono, color: "#8c8578", letterSpacing: "0.5px", textTransform: "uppercase", marginBottom: "6px" }}>
                      {t.signatureBlock} <span style={{ opacity: 0.4 }}>/ {t.signatureBlockAlt}</span>
                    </div>
                    <div style={{ borderBottom: "1px solid #1a1814", width: "100%", marginBottom: "4px", paddingBottom: "28px" }} />
                    <div style={{ fontSize: "11px", color: "#5c5549" }}>{D.director}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: "9px", fontFamily: mono, color: "#8c8578", letterSpacing: "0.5px", textTransform: "uppercase", marginBottom: "6px" }}>
                      {t.dateField} <span style={{ opacity: 0.4 }}>/ {t.dateFieldAlt}</span>
                    </div>
                    <div style={{ borderBottom: "1px solid #1a1814", width: "100%", marginBottom: "4px", paddingBottom: "28px" }} />
                    <div style={{ fontSize: "11px", color: "#5c5549" }}>___.___.2026</div>
                  </div>
                </div>
              </>
            )}
          </div>

          {/* ======== FOOTER ======== */}
          <div style={{ padding: "10px 32px", borderTop: "2px solid #1a1814", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "6px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <span style={{ fontSize: "7.5px", fontWeight: "700", fontFamily: mono, padding: "2px 6px", background: "#1a1814", color: "#faf8f4", borderRadius: "2px", letterSpacing: "1.2px" }}>{t.confidential}</span>
              <span style={{ fontSize: "8.5px", color: "#8c8578", fontFamily: mono }}>{t.footer}</span>
            </div>
            <div style={{ fontSize: "7.5px", color: "#8c8578", fontFamily: mono }}>
              <span style={{ color: "#c9a84c" }}>WINDI v1.1</span> · RFC-003 · {t.reportId}: {D.reportId} · {t.generated}: 05.02.2026 {D.genTime}
            </div>
          </div>
        </div>
      </div>

      <style>{`
        @media print { .np { display: none !important; } body { background: #fff !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; } }
      `}</style>
    </div>
  );
}

const th = { padding: "6px 7px", textAlign: "left", fontSize: "8px", fontWeight: "700", fontFamily: "'IBM Plex Mono', monospace", letterSpacing: "0.7px", color: "#8c8578", textTransform: "uppercase" };
const td = { padding: "8px 7px", verticalAlign: "middle" };
