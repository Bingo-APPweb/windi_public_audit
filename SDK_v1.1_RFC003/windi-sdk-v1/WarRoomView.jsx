import { useState, useEffect, useRef } from "react";

const MOCK_BRIEFING = {
  director: "—",
  secretary: "—",
  meeting: "—",
  systemStatus: "operational",
  reportId: "GBR-05-02-2026",
  genTime: "12:32 CET",
  briefingDate: "05.02.2026",
  hash: "dd68612c…00e4",
  ledgerRef: "REG-20260201-0001",
  contDays: 1,
  summary: {
    en: "Governance engine operational (v2.0.0). 1 document(s) in audit chain. SGE Engine active (1.2-detect). 1 HIGH-level item(s) flagged for review. 4 ISP profile(s) loaded. Chain integrity verified — 1 sealed.",
    de: "Governance-Engine betriebsbereit (v2.0.0). 1 Dokument(e) in der Audit-Kette. SGE-Engine aktiv (1.2-detect). 1 HIGH-Level-Einträge zur Prüfung markiert. 4 ISP-Profil(e) geladen. Kettenintegrität verifiziert — 1 versiegelt.",
  },
  decisions: [
    {
      id: "REG-20260201-0001",
      topic: { en: "European Central Bank (Model) — 2026-Q1", de: "European Central Bank (Model) — 2026-Q1" },
      status: "pending",
      sge: "R3",
      urgency: "high",
    },
  ],
  risks: { new: 0, active: 1, resolved: 0 },
  riskDetails: [
    {
      id: "REG-20260201-0001",
      level: "R3",
      desc: { en: "European Central Bank (Model) — governance review", de: "European Central Bank (Model) — Governance-Prüfung" },
      status: "active",
      urgency: "high",
    },
  ],
  metrics: [
    { k: "docsProcessed", v: 1, p: 0, u: "" },
    { k: "sgeAvg", v: 82, p: 80, u: "" },
    { k: "complianceRate", v: 100, p: 0, u: "%" },
    { k: "avgResponse", v: 0, p: 0, u: "h", inv: true },
    { k: "overrides", v: 0, p: 0, u: "", inv: true },
    { k: "flagged", v: 1, p: 0, u: "", inv: true },
  ],
  compliance: [
    { k: "euAiAct", s: "compliant" },
    { k: "bsiC5", s: "partial" },
    { k: "iso27001", s: "compliant" },
    { k: "gdpr", s: "compliant" },
  ],
  _meta: {
    sources: { governance_core: "connected", sge_engine: "connected", forensic_ledger: "connected" },
    engine: {
      version: "2.0.0",
      profiles_loaded: ["bis-style", "_base", "deutsche-bahn", "bundesregierung"],
      profiles_available: ["ihk", "bis-style", "agentur-fuer-arbeit", "tuev", "_base", "hwk", "deutsche-bahn", "bundesregierung", "bafin"],
      status: "OPERATIONAL",
    },
    sge: { version: "1.2-detect", service: "WINDI Governance API" },
  },
};

const METRIC_LABELS = {
  docsProcessed: { label: "Docs Processed", icon: "📄" },
  sgeAvg: { label: "SGE Score", icon: "🧠" },
  complianceRate: { label: "Compliance", icon: "✅" },
  avgResponse: { label: "Avg Response", icon: "⏱" },
  overrides: { label: "Overrides", icon: "🔄" },
  flagged: { label: "Flagged", icon: "⚠️" },
};

const COMPLIANCE_LABELS = {
  euAiAct: "EU AI Act",
  bsiC5: "BSI C5",
  iso27001: "ISO 27001",
  gdpr: "GDPR",
};

const RISK_COLORS = {
  R0: "#22c55e", R1: "#84cc16", R2: "#eab308",
  R3: "#f97316", R4: "#ef4444", R5: "#dc2626",
};

const PROFILE_ICONS = {
  "deutsche-bahn": "🚄",
  "bundesregierung": "🏛",
  "bis-style": "🏦",
  "_base": "⚙️",
  "ihk": "🏢",
  "hwk": "🔧",
  "tuev": "🛡",
  "bafin": "💶",
  "agentur-fuer-arbeit": "👥",
};

function PulsingDot({ color, size = 10 }) {
  return (
    <span style={{ position: "relative", display: "inline-block", width: size, height: size, marginRight: 8 }}>
      <span
        style={{
          position: "absolute",
          width: size,
          height: size,
          borderRadius: "50%",
          backgroundColor: color,
          animation: "pulse-ring 1.5s ease-out infinite",
        }}
      />
      <span
        style={{
          position: "absolute",
          width: size,
          height: size,
          borderRadius: "50%",
          backgroundColor: color,
        }}
      />
    </span>
  );
}

function GravityBar({ level, animated }) {
  const idx = parseInt(level?.replace("R", "") || "0");
  const pct = Math.min(((idx + 1) / 6) * 100, 100);
  const color = RISK_COLORS[level] || "#6b7280";
  return (
    <div style={{ width: "100%", height: 6, background: "#1e293b", borderRadius: 3, overflow: "hidden" }}>
      <div
        style={{
          width: `${pct}%`,
          height: "100%",
          background: `linear-gradient(90deg, ${color}88, ${color})`,
          borderRadius: 3,
          transition: "width 1s ease",
          animation: animated ? "gravity-pulse 2s ease-in-out infinite" : "none",
        }}
      />
    </div>
  );
}

function StatusBadge({ status }) {
  const colors = {
    compliant: { bg: "#064e3b", text: "#34d399", label: "COMPLIANT" },
    partial: { bg: "#713f12", text: "#fbbf24", label: "PARTIAL" },
    "non-compliant": { bg: "#7f1d1d", text: "#f87171", label: "FAIL" },
  };
  const c = colors[status] || colors["non-compliant"];
  return (
    <span
      style={{
        display: "inline-block",
        padding: "2px 8px",
        borderRadius: 3,
        fontSize: 10,
        fontWeight: 700,
        letterSpacing: 1,
        background: c.bg,
        color: c.text,
      }}
    >
      {c.label}
    </span>
  );
}

function SourceIndicator({ name, status }) {
  const ok = status === "connected";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11, color: ok ? "#4ade80" : "#f87171" }}>
      <PulsingDot color={ok ? "#4ade80" : "#f87171"} size={6} />
      <span style={{ color: "#94a3b8", fontFamily: "monospace" }}>{name}</span>
    </div>
  );
}

export default function WarRoom() {
  const [data, setData] = useState(MOCK_BRIEFING);
  const [clock, setClock] = useState(new Date());
  const [lang, setLang] = useState("en");

  useEffect(() => {
    const t = setInterval(() => setClock(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    // Try live API, fall back to mock
    fetch("http://127.0.0.1:8090/api/briefing")
      .then((r) => r.json())
      .then((r) => { if (r.success) setData(r.data); })
      .catch(() => {});
  }, []);

  const alert = data.decisions?.some((d) => d.urgency === "high" && d.status === "pending");
  const profiles = data._meta?.engine?.profiles_loaded || [];
  const available = data._meta?.engine?.profiles_available || [];
  const sources = data._meta?.sources || {};

  return (
    <div style={{ minHeight: "100vh", background: "#0f172a", color: "#e2e8f0", fontFamily: "'JetBrains Mono', 'Fira Code', 'IBM Plex Mono', monospace", padding: 0, margin: 0 }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700&display=swap');
        @keyframes pulse-ring { 0% { transform: scale(1); opacity: 0.8; } 100% { transform: scale(2.5); opacity: 0; } }
        @keyframes gravity-pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }
        @keyframes alert-flash { 0%, 100% { border-color: #f97316; box-shadow: 0 0 20px #f9731640; } 50% { border-color: #ef4444; box-shadow: 0 0 40px #ef444460; } }
        @keyframes scan-line { 0% { top: -2px; } 100% { top: 100%; } }
        * { box-sizing: border-box; }
      `}</style>

      {/* ── Top Bar ── */}
      <div style={{ background: "#0a0f1a", borderBottom: "1px solid #1e293b", padding: "12px 24px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <div>
            <span style={{ fontSize: 20, fontWeight: 700, color: "#c9a84c", letterSpacing: 4 }}>WINDI</span>
            <span style={{ fontSize: 12, color: "#64748b", marginLeft: 12, letterSpacing: 2 }}>WAR ROOM</span>
          </div>
          <div style={{ width: 1, height: 24, background: "#1e293b" }} />
          {Object.entries(sources).map(([k, v]) => (
            <SourceIndicator key={k} name={k.replace("_", " ")} status={v} />
          ))}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <button
            onClick={() => setLang(lang === "en" ? "de" : "en")}
            style={{ background: "#1e293b", border: "1px solid #334155", color: "#94a3b8", padding: "4px 10px", borderRadius: 4, cursor: "pointer", fontSize: 11, fontFamily: "inherit" }}
          >
            {lang.toUpperCase()}
          </button>
          <div style={{ fontSize: 13, color: "#c9a84c", fontVariantNumeric: "tabular-nums" }}>
            {clock.toLocaleTimeString("de-DE", { hour: "2-digit", minute: "2-digit", second: "2-digit" })} CET
          </div>
        </div>
      </div>

      <div style={{ padding: "20px 24px", maxWidth: 1400, margin: "0 auto" }}>

        {/* ── Status Header ── */}
        <div style={{ display: "flex", gap: 16, marginBottom: 20, flexWrap: "wrap" }}>
          <div style={{ flex: 1, minWidth: 280, background: "#1e293b", borderRadius: 8, padding: 20, border: "1px solid #334155", position: "relative", overflow: "hidden" }}>
            <div style={{ position: "absolute", top: 0, right: 0, width: 80, height: 80, background: "radial-gradient(circle at top right, #c9a84c15, transparent)", borderRadius: "0 8px 0 0" }} />
            <div style={{ fontSize: 11, color: "#64748b", letterSpacing: 2, marginBottom: 8 }}>GOVERNANCE BRIEFING</div>
            <div style={{ fontSize: 28, fontWeight: 700, color: "#f8fafc" }}>{data.briefingDate}</div>
            <div style={{ fontSize: 12, color: "#94a3b8", marginTop: 4 }}>
              Report {data.reportId} · {data.genTime} · Day {data.contDays}
            </div>
          </div>

          <div style={{ flex: 1, minWidth: 280, background: "#1e293b", borderRadius: 8, padding: 20, border: "1px solid #334155" }}>
            <div style={{ fontSize: 11, color: "#64748b", letterSpacing: 2, marginBottom: 8 }}>ENGINE STATUS</div>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <PulsingDot color="#4ade80" size={12} />
              <span style={{ fontSize: 22, fontWeight: 700, color: "#4ade80" }}>{(data.systemStatus || "").toUpperCase()}</span>
            </div>
            <div style={{ fontSize: 11, color: "#64748b", marginTop: 8 }}>
              Core v{data._meta?.engine?.version} · SGE v{data._meta?.sge?.version}
            </div>
          </div>

          <div style={{ flex: 1, minWidth: 280, background: "#1e293b", borderRadius: 8, padding: 20, border: "1px solid #334155" }}>
            <div style={{ fontSize: 11, color: "#64748b", letterSpacing: 2, marginBottom: 8 }}>AUDIT CHAIN</div>
            <div style={{ fontSize: 14, fontWeight: 500, color: "#c9a84c", fontFamily: "monospace" }}>{data.hash}</div>
            <div style={{ fontSize: 12, color: "#94a3b8", marginTop: 8 }}>
              Ledger: {data.ledgerRef} · <span style={{ color: "#4ade80" }}>Sealed ✓</span>
            </div>
          </div>
        </div>

        {/* ── Main Grid ── */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>

          {/* ── DECISIONS (Left) ── */}
          <div
            style={{
              background: "#1e293b",
              borderRadius: 8,
              padding: 20,
              border: alert ? "2px solid #f97316" : "1px solid #334155",
              animation: alert ? "alert-flash 2s ease-in-out infinite" : "none",
              position: "relative",
              overflow: "hidden",
            }}
          >
            {alert && (
              <div style={{ position: "absolute", top: 0, left: 0, right: 0, height: 2, background: "linear-gradient(90deg, transparent, #f97316, transparent)", animation: "scan-line 3s linear infinite" }} />
            )}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
              <div style={{ fontSize: 11, color: "#64748b", letterSpacing: 2 }}>PENDING DECISIONS</div>
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                {alert && <PulsingDot color="#f97316" size={8} />}
                <span style={{ fontSize: 11, color: alert ? "#f97316" : "#4ade80", fontWeight: 700 }}>
                  {data.decisions?.length || 0} {alert ? "ACTION REQUIRED" : "CLEAR"}
                </span>
              </div>
            </div>

            {(data.decisions || []).map((d, i) => (
              <div
                key={i}
                style={{
                  background: "#0f172a",
                  borderRadius: 6,
                  padding: 16,
                  marginBottom: 8,
                  borderLeft: `4px solid ${RISK_COLORS[d.sge] || "#6b7280"}`,
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 10 }}>
                  <div style={{ fontSize: 15, fontWeight: 600, color: "#f8fafc", lineHeight: 1.4, flex: 1 }}>
                    {d.topic?.[lang] || d.topic?.en}
                  </div>
                  <div style={{ display: "flex", gap: 6, marginLeft: 12, flexShrink: 0 }}>
                    <span style={{ background: RISK_COLORS[d.sge] + "20", color: RISK_COLORS[d.sge], padding: "2px 8px", borderRadius: 3, fontSize: 11, fontWeight: 700 }}>
                      {d.sge}
                    </span>
                    <span style={{ background: d.urgency === "high" ? "#7f1d1d" : "#1e3a5f", color: d.urgency === "high" ? "#fca5a5" : "#93c5fd", padding: "2px 8px", borderRadius: 3, fontSize: 11, fontWeight: 700, textTransform: "uppercase" }}>
                      {d.urgency}
                    </span>
                  </div>
                </div>
                <GravityBar level={d.sge} animated={d.urgency === "high"} />
                <div style={{ fontSize: 11, color: "#64748b", marginTop: 8 }}>
                  ID: {d.id} · Status: <span style={{ color: "#fbbf24" }}>{d.status.toUpperCase()}</span>
                </div>
              </div>
            ))}

            {/* Risk Summary */}
            <div style={{ display: "flex", gap: 20, marginTop: 16, paddingTop: 12, borderTop: "1px solid #334155" }}>
              <div style={{ textAlign: "center" }}>
                <div style={{ fontSize: 24, fontWeight: 700, color: "#fbbf24" }}>{data.risks?.active || 0}</div>
                <div style={{ fontSize: 10, color: "#64748b", letterSpacing: 1 }}>ACTIVE</div>
              </div>
              <div style={{ textAlign: "center" }}>
                <div style={{ fontSize: 24, fontWeight: 700, color: "#4ade80" }}>{data.risks?.resolved || 0}</div>
                <div style={{ fontSize: 10, color: "#64748b", letterSpacing: 1 }}>RESOLVED</div>
              </div>
              <div style={{ textAlign: "center" }}>
                <div style={{ fontSize: 24, fontWeight: 700, color: "#60a5fa" }}>{data.risks?.new || 0}</div>
                <div style={{ fontSize: 10, color: "#64748b", letterSpacing: 1 }}>NEW</div>
              </div>
            </div>
          </div>

          {/* ── RIGHT COLUMN ── */}
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>

            {/* ── Metrics ── */}
            <div style={{ background: "#1e293b", borderRadius: 8, padding: 20, border: "1px solid #334155" }}>
              <div style={{ fontSize: 11, color: "#64748b", letterSpacing: 2, marginBottom: 16 }}>KEY METRICS</div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12 }}>
                {(data.metrics || []).map((m, i) => {
                  const info = METRIC_LABELS[m.k] || { label: m.k, icon: "📊" };
                  const isGood = m.inv ? m.v === 0 : m.v >= (m.p || 0);
                  return (
                    <div key={i} style={{ background: "#0f172a", borderRadius: 6, padding: 12, textAlign: "center" }}>
                      <div style={{ fontSize: 16, marginBottom: 4 }}>{info.icon}</div>
                      <div style={{ fontSize: 22, fontWeight: 700, color: isGood ? "#4ade80" : "#fbbf24", fontVariantNumeric: "tabular-nums" }}>
                        {m.v}{m.u}
                      </div>
                      <div style={{ fontSize: 9, color: "#64748b", letterSpacing: 1, marginTop: 4, textTransform: "uppercase" }}>
                        {info.label}
                      </div>
                      {m.p > 0 && (
                        <div style={{ fontSize: 9, color: "#475569", marginTop: 2 }}>target: {m.p}{m.u}</div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* ── Compliance ── */}
            <div style={{ background: "#1e293b", borderRadius: 8, padding: 20, border: "1px solid #334155" }}>
              <div style={{ fontSize: 11, color: "#64748b", letterSpacing: 2, marginBottom: 12 }}>COMPLIANCE STATUS</div>
              <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                {(data.compliance || []).map((c, i) => (
                  <div key={i} style={{ background: "#0f172a", borderRadius: 6, padding: "10px 14px", display: "flex", alignItems: "center", gap: 10, flex: "1 1 45%", minWidth: 140 }}>
                    <span style={{ fontSize: 13, fontWeight: 600, color: "#e2e8f0" }}>{COMPLIANCE_LABELS[c.k] || c.k}</span>
                    <span style={{ marginLeft: "auto" }}><StatusBadge status={c.s} /></span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* ── ISP Profiles ── */}
        <div style={{ marginTop: 16, background: "#1e293b", borderRadius: 8, padding: 20, border: "1px solid #334155" }}>
          <div style={{ fontSize: 11, color: "#64748b", letterSpacing: 2, marginBottom: 16 }}>ISP PROFILES</div>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            {available.map((p) => {
              const loaded = profiles.includes(p);
              return (
                <div
                  key={p}
                  style={{
                    background: loaded ? "#0f172a" : "#0f172a80",
                    border: loaded ? "1px solid #c9a84c" : "1px solid #1e293b",
                    borderRadius: 6,
                    padding: "10px 16px",
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                    opacity: loaded ? 1 : 0.4,
                    transition: "all 0.3s ease",
                  }}
                >
                  <span style={{ fontSize: 18 }}>{PROFILE_ICONS[p] || "📋"}</span>
                  <div>
                    <div style={{ fontSize: 12, fontWeight: loaded ? 600 : 400, color: loaded ? "#c9a84c" : "#64748b" }}>
                      {p.replace(/_/g, " ").replace(/-/g, " ").toUpperCase()}
                    </div>
                    <div style={{ fontSize: 9, color: loaded ? "#4ade80" : "#475569" }}>
                      {loaded ? "LOADED" : "AVAILABLE"}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* ── Executive Summary ── */}
        <div style={{ marginTop: 16, background: "#1e293b", borderRadius: 8, padding: 20, border: "1px solid #334155", borderLeft: "4px solid #c9a84c" }}>
          <div style={{ fontSize: 11, color: "#64748b", letterSpacing: 2, marginBottom: 10 }}>EXECUTIVE SUMMARY</div>
          <div style={{ fontSize: 13, lineHeight: 1.8, color: "#cbd5e1" }}>
            {data.summary?.[lang] || data.summary?.en}
          </div>
        </div>

        {/* ── Footer ── */}
        <div style={{ marginTop: 20, textAlign: "center", padding: "16px 0", borderTop: "1px solid #1e293b" }}>
          <div style={{ fontSize: 10, color: "#475569", letterSpacing: 2 }}>
            AI PROCESSES · HUMAN DECIDES · WINDI GUARANTEES
          </div>
          <div style={{ fontSize: 9, color: "#334155", marginTop: 6 }}>
            Three Dragons Protocol — Guardian · Architect · Witness
          </div>
        </div>
      </div>
    </div>
  );
}
