import { useState, useEffect, useCallback, useRef } from "react";

// ═══════════════════════════════════════════════════════════════
// WINDI MEISTERWERK — LIVE Dashboard
// Consome dados reais do Sentinel Bridge API (:8098)
// "O Sentinel observa. A Bridge traduz. O Ministro decide."
// ═══════════════════════════════════════════════════════════════

const G = {
  100: "#f9edcc", 200: "#f3d994", 300: "#edc55c",
  400: "#e7b124", 500: "#c4940f", 600: "#9a740c",
  700: "#705409", 800: "#463506", 900: "#2a2004",
};
const N = {
  bg: "#08080a", s: "#0e0e11", e: "#141418", e2: "#1a1a1f",
  b: "#222228", b2: "#2e2e35", t: "#eae8e3",
  tm: "#9a9890", td: "#5a5850", tx: "#3a3830",
};
const ST = { ok: "#34d399", warn: "#fbbf24", deg: "#fb923c", crit: "#f87171", info: "#60a5fa" };

// ─── API Configuration ───────────────────────────────────────
// In production: relative path through nginx proxy
// In development: direct port access
const API_BASE = window.location.hostname === "localhost" 
  ? "http://localhost:8098" 
  : "/sentinel";

const POLL_INTERVAL_MS = 5000; // Poll every 5 seconds
const MINISTER_POLL_MS = 3000; // Minister view polls faster

// ─── API Fetch Helpers ───────────────────────────────────────

async function fetchSentinel(endpoint) {
  try {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      headers: { "Accept": "application/json" },
      cache: "no-store",
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn(`[Sentinel] ${endpoint} failed:`, err.message);
    return null;
  }
}

// ─── Micro Components ────────────────────────────────────────

function Orb({ color, size = 8, pulse = false, glow = false }) {
  return (
    <span className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      {pulse && (
        <span className="absolute rounded-full" style={{
          width: size * 2.5, height: size * 2.5,
          backgroundColor: color, opacity: 0.15,
          animation: "orbPulse 2s ease-in-out infinite",
        }} />
      )}
      {glow && (
        <span className="absolute rounded-full" style={{
          width: size * 1.8, height: size * 1.8,
          backgroundColor: color, opacity: 0.2, filter: "blur(4px)",
        }} />
      )}
      <span className="relative rounded-full" style={{ width: size, height: size, backgroundColor: color }} />
    </span>
  );
}

function RiskPill({ level }) {
  const c = {
    R0: [ST.ok, "rgba(52,211,153,0.1)"], R1: [ST.ok, "rgba(52,211,153,0.1)"],
    R2: [ST.warn, "rgba(251,191,36,0.1)"], R3: [ST.deg, "rgba(251,146,36,0.1)"],
    R4: [ST.crit, "rgba(248,113,113,0.1)"], R5: ["#fff", "rgba(255,255,255,0.08)"],
  }[level] || [N.tm, N.e];
  return (
    <span className="inline-flex items-center rounded px-1.5 py-0.5 font-mono"
      style={{ fontSize: 9, backgroundColor: c[1], color: c[0], letterSpacing: "0.06em" }}>
      {level}
    </span>
  );
}

function ImpactBar({ level }) {
  const w = { LOW: "25%", MEDIUM: "50%", HIGH: "75%", CRITICAL: "100%" }[level] || "25%";
  const c = { LOW: ST.ok, MEDIUM: ST.warn, HIGH: ST.deg, CRITICAL: ST.crit }[level] || N.tm;
  return (
    <div className="flex items-center gap-2">
      <div className="rounded-full overflow-hidden" style={{ width: 40, height: 3, backgroundColor: N.b }}>
        <div className="rounded-full h-full transition-all" style={{ width: w, backgroundColor: c }} />
      </div>
      <span className="font-mono" style={{ fontSize: 8, color: c }}>{level}</span>
    </div>
  );
}

// ─── Connection Status ───────────────────────────────────────

function ConnectionBadge({ connected, lastUpdate }) {
  const age = lastUpdate ? Math.round((Date.now() - lastUpdate) / 1000) : null;
  return (
    <div className="flex items-center gap-1.5">
      <Orb color={connected ? ST.ok : ST.crit} size={4} pulse={!connected} />
      <span className="font-mono" style={{ fontSize: 8, color: connected ? N.td : ST.crit }}>
        {connected ? `LIVE · ${age || 0}s` : "OFFLINE"}
      </span>
    </div>
  );
}

// ─── Sovereign Pulse (Minister's view) ───────────────────────

function SovereignPulse({ minister, connected }) {
  if (!minister) {
    return (
      <div className="flex items-center justify-between px-5 py-2.5"
        style={{ backgroundColor: "rgba(138,136,128,0.04)", borderBottom: `1px solid rgba(138,136,128,0.08)` }}>
        <div className="flex items-center gap-3">
          <Orb color={N.td} size={7} />
          <span className="font-mono tracking-wider" style={{ fontSize: 10, color: N.td, letterSpacing: "0.12em" }}>
            VERBINDUNG WIRD HERGESTELLT...
          </span>
        </div>
        <ConnectionBadge connected={false} />
      </div>
    );
  }

  const pulseColors = { green: ST.ok, gold: G[400], amber: ST.warn, red: ST.crit };
  const color = pulseColors[minister.pulse] || N.td;
  const isCritical = minister.pulse === "red";
  const isWarning = minister.pulse === "amber";

  return (
    <div className="flex items-center justify-between px-5 py-2.5 transition-all duration-700"
      style={{
        backgroundColor: isCritical ? "rgba(248,113,113,0.05)" :
          isWarning ? "rgba(251,191,36,0.04)" :
          minister.pulse === "gold" ? "rgba(231,177,36,0.04)" :
          "rgba(52,211,153,0.03)",
        borderBottom: `1px solid ${isCritical ? "rgba(248,113,113,0.15)" :
          isWarning ? "rgba(251,191,36,0.12)" : "rgba(52,211,153,0.08)"}`,
      }}>
      <div className="flex items-center gap-3">
        <Orb color={color} size={7} pulse={isCritical || isWarning} glow={isCritical} />
        <span className="font-mono tracking-wider" style={{ fontSize: 10, color, letterSpacing: "0.12em" }}>
          {minister.label}
        </span>
      </div>
      <div className="flex items-center gap-3">
        {minister.action_required && (
          <span className="font-mono rounded px-2 py-0.5" style={{
            fontSize: 9, color: isCritical ? ST.crit : ST.warn,
            backgroundColor: isCritical ? "rgba(248,113,113,0.08)" : "rgba(251,191,36,0.08)",
            animation: isCritical ? "criticalBlink 3s ease-in-out infinite" : "none",
          }}>
            {isCritical ? "HANDLUNG ERFORDERLICH" : "UNTER BEOBACHTUNG"}
          </span>
        )}
        <ConnectionBadge connected={connected} />
      </div>
    </div>
  );
}

// ─── Mental State Card ───────────────────────────────────────

function MentalStateCard({ minister }) {
  if (!minister) return null;
  const pulseColors = { green: ST.ok, gold: G[400], amber: ST.warn, red: ST.crit };
  const color = pulseColors[minister.pulse] || N.td;

  return (
    <div className="rounded-xl p-4 transition-all duration-700" style={{
      backgroundColor: `${color}08`,
      border: `1px solid ${color}20`,
    }}>
      <div className="flex items-center gap-2 mb-2">
        <span style={{ fontSize: 11 }}>🧠</span>
        <span className="tracking-wider" style={{ fontSize: 9, color: N.tm, letterSpacing: "0.08em" }}>
          KOGNITIVER ZUSTAND
        </span>
      </div>
      <p className="text-sm font-medium mb-1.5" style={{
        color, margin: 0, fontFamily: "'Bricolage Grotesque', sans-serif",
        fontStyle: "italic", fontSize: 13,
      }}>
        "{minister.feeling}"
      </p>
      <p className="text-xs" style={{ color: N.tm, margin: 0, fontSize: 11, lineHeight: 1.6 }}>
        {minister.message}
      </p>
      {minister.decisions_affected && minister.decisions_affected.blocked > 0 && (
        <div className="mt-2 pt-2 flex items-center gap-3" style={{ borderTop: `1px solid ${color}15` }}>
          <span className="font-mono" style={{ fontSize: 9, color: ST.crit }}>
            {minister.decisions_affected.blocked} blockiert
          </span>
          <span className="font-mono" style={{ fontSize: 9, color: ST.warn }}>
            {minister.decisions_affected.delayed} verzögert
          </span>
        </div>
      )}
    </div>
  );
}

// ─── Governance Integrity Gauge ──────────────────────────────

function IntegrityGauge({ confidence }) {
  const c = confidence >= 98 ? ST.ok : confidence >= 90 ? ST.warn : confidence >= 70 ? ST.deg : ST.crit;
  return (
    <div className="rounded-xl p-4 text-center" style={{ backgroundColor: N.e, border: `1px solid ${N.b}` }}>
      <span className="tracking-wider" style={{ fontSize: 10, color: N.tm, letterSpacing: "0.08em" }}>
        GOVERNANCE-INTEGRITÄT
      </span>
      <div className="relative mx-auto my-3" style={{ width: 80, height: 80 }}>
        <svg viewBox="0 0 80 80" className="w-full h-full">
          <circle cx="40" cy="40" r="34" fill="none" stroke={N.b} strokeWidth="3"
            strokeDasharray="160 53" strokeLinecap="round" transform="rotate(135 40 40)" />
          <circle cx="40" cy="40" r="34" fill="none" stroke={c} strokeWidth="3"
            strokeDasharray={`${confidence * 1.6} ${213 - confidence * 1.6}`}
            strokeLinecap="round" transform="rotate(135 40 40)"
            className="transition-all duration-1000" opacity="0.8" />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-mono font-semibold transition-all duration-700"
            style={{ fontSize: 20, color: c, lineHeight: 1 }}>{confidence}</span>
          <span className="font-mono" style={{ fontSize: 7, color: N.td }}>%</span>
        </div>
      </div>
    </div>
  );
}

// ─── Decision Cards (Placeholder — will connect to Governance API) ──

const DECISIONS = [
  {
    id: "DEC-0042", title: "Quartalsreport Q1 Freigabe",
    impact: "HIGH", risk: "R2", dept: "Finanzen", wait: "2h 15min", canOffline: true,
    oracle: "SGE-Analyse: 42 Seiten geprüft, 3 Klauseln markiert. Risiko: moderat. Empfehlung: Freigabe mit Vermerk zu §7.1.",
  },
  {
    id: "DEC-0043", title: "Lieferantenvertrag Müller GmbH",
    impact: "CRITICAL", risk: "R4", dept: "Einkauf", wait: "48min", canOffline: false,
    oracle: "Compliance-Lücke in Klausel 12.1. Haftungsrisiko: €2.4M. Empfehlung: Nachverhandlung.",
  },
  {
    id: "DEC-0044", title: "Datenschutz-Update Webportal",
    impact: "MEDIUM", risk: "R1", dept: "IT/Recht", wait: "4h 30min", canOffline: true,
    oracle: "DSGVO-Konformität: 96%. Fehlend: Cookie-Banner Update. Empfehlung: Standard-Freigabe.",
  },
];

function OracleCard({ decision, expanded, onToggle, ministerStatus }) {
  const blocked = ministerStatus === "CRITICAL" && !decision.canOffline;
  const impactColor = { LOW: ST.ok, MEDIUM: ST.warn, HIGH: ST.deg, CRITICAL: ST.crit }[decision.impact] || N.tm;

  return (
    <div className="rounded-xl overflow-hidden cursor-pointer transition-all duration-300"
      onClick={onToggle}
      style={{
        backgroundColor: expanded ? N.e2 : N.e,
        border: `1px solid ${blocked ? "rgba(248,113,113,0.2)" : expanded ? G[700] : N.b}`,
        opacity: blocked ? 0.7 : 1,
      }}>
      <div className="p-4">
        <div className="flex items-start justify-between mb-2">
          <div className="flex items-center gap-2">
            <Orb color={blocked ? ST.crit : impactColor} size={6} pulse={decision.impact === "CRITICAL"} />
            <span className="font-mono" style={{ fontSize: 9, color: N.td }}>{decision.id}</span>
            {blocked && (
              <span className="font-mono rounded px-1.5 py-0.5" style={{
                fontSize: 8, backgroundColor: "rgba(248,113,113,0.1)", color: ST.crit,
              }}>BLOCKIERT</span>
            )}
          </div>
          <RiskPill level={decision.risk} />
        </div>
        <h3 className="text-sm font-medium mb-2" style={{
          color: N.t, margin: 0, lineHeight: 1.4, fontFamily: "'Bricolage Grotesque', sans-serif",
        }}>{decision.title}</h3>
        <div className="flex items-center gap-3">
          <ImpactBar level={decision.impact} />
          <span style={{ color: N.tx, fontSize: 8 }}>·</span>
          <span className="font-mono" style={{ fontSize: 9, color: N.td }}>{decision.dept}</span>
          <span style={{ color: N.tx, fontSize: 8 }}>·</span>
          <span className="font-mono" style={{ fontSize: 9, color: N.td }}>wartet {decision.wait}</span>
        </div>
      </div>
      {expanded && (
        <div className="px-4 pb-4" style={{ animation: "slideDown 0.3s ease-out" }}>
          <div className="rounded-lg p-3.5 mb-3" style={{
            backgroundColor: "rgba(196,148,15,0.04)", borderLeft: `2px solid ${G[500]}`,
          }}>
            <div className="flex items-center gap-1.5 mb-2">
              <span style={{ color: G[400], fontSize: 11 }}>◆</span>
              <span className="font-mono tracking-wider" style={{ fontSize: 9, color: G[500], letterSpacing: "0.1em" }}>
                DRACHEN-RAT · PARECER
              </span>
            </div>
            <p className="text-sm" style={{ color: N.t, margin: 0, lineHeight: 1.65, fontSize: 12, fontFamily: "'Outfit', sans-serif" }}>
              {decision.oracle}
            </p>
          </div>
          {!blocked ? (
            <div className="flex items-center gap-2">
              <button className="flex-1 py-2 rounded-lg border-0 cursor-pointer font-medium"
                style={{ backgroundColor: "rgba(52,211,153,0.1)", color: ST.ok, fontSize: 11 }}>✓ Freigeben</button>
              <button className="flex-1 py-2 rounded-lg border-0 cursor-pointer font-medium"
                style={{ backgroundColor: "rgba(248,113,113,0.08)", color: ST.crit, fontSize: 11 }}>✕ Ablehnen</button>
              <button className="py-2 px-4 rounded-lg border-0 cursor-pointer"
                style={{ backgroundColor: N.e, color: N.tm, fontSize: 11, border: `1px solid ${N.b}` }}>Zurückstellen</button>
            </div>
          ) : (
            <div className="flex items-center gap-2 rounded-lg p-2.5"
              style={{ backgroundColor: "rgba(248,113,113,0.05)", border: `1px solid rgba(248,113,113,0.1)` }}>
              <Orb color={ST.crit} size={5} />
              <span className="text-xs" style={{ color: ST.crit, fontSize: 11 }}>
                Systemverfügbarkeit erforderlich. Architektur-Team arbeitet an Wiederherstellung.
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Architektur Layer (LIVE service matrix) ─────────────────

function ArchitekturView({ serviceData }) {
  const services = serviceData?.services || {};
  const summary = serviceData?.summary || {};
  const statusColor = { healthy: ST.ok, degraded: ST.deg, warning: ST.warn, critical: ST.crit, unknown: N.td };

  return (
    <div className="h-full overflow-y-auto p-5 space-y-4">
      <div className="mb-4">
        <h2 className="text-base font-semibold mb-1" style={{ color: ST.info, fontFamily: "'Bricolage Grotesque'", margin: 0 }}>
          Architektur-Ebene
        </h2>
        <p className="text-xs" style={{ color: N.tm, margin: 0 }}>
          {summary.healthy || 0}/{summary.total || 0} gesund · ø{summary.avg_latency_ms || 0}ms
        </p>
      </div>

      <div className="rounded-xl p-4" style={{ backgroundColor: N.e, border: `1px solid ${N.b}` }}>
        <span className="tracking-wider" style={{ fontSize: 10, color: N.tm, letterSpacing: "0.08em" }}>
          DIENST-MATRIX · LIVE
        </span>
        <div className="grid grid-cols-3 gap-2 mt-3">
          {Object.entries(services).map(([name, svc]) => (
            <div key={name} className="rounded-lg p-2.5" style={{
              backgroundColor: N.e2,
              border: `1px solid ${svc.status !== "healthy" ? (statusColor[svc.status] || N.td) + "30" : N.b}`,
            }}>
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-1.5">
                  <Orb color={statusColor[svc.status] || N.td} size={5} pulse={svc.status === "critical"} />
                  <span className="font-mono" style={{ fontSize: 9, color: N.t }}>{name}</span>
                </div>
                {svc.critical && <span className="font-mono" style={{ fontSize: 7, color: G[600] }}>KERN</span>}
              </div>
              <div className="flex items-center justify-between">
                <span className="font-mono" style={{ fontSize: 8, color: N.td }}>
                  {svc.port ? `:${svc.port}` : "daemon"}
                </span>
                <span className="font-mono" style={{
                  fontSize: 8,
                  color: svc.status !== "healthy" ? (statusColor[svc.status] || N.td) : N.td,
                }}>
                  {svc.latency_ms != null ? `${svc.latency_ms}ms` : "—"}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Escalation info */}
      <div className="rounded-xl p-4" style={{
        backgroundColor: "rgba(196,148,15,0.04)", border: `1px solid rgba(196,148,15,0.1)`,
      }}>
        <span className="tracking-wider" style={{ fontSize: 10, color: G[500], letterSpacing: "0.08em" }}>
          ↑ SYNTHESE · ENTSCHEIDUNGSEBENE
        </span>
        <p className="text-xs mt-2" style={{ color: N.tm, margin: 0, lineHeight: 1.6, fontSize: 11 }}>
          {summary.critical > 0
            ? `${summary.critical} kritische(r) Dienst(e). Entscheidungspipeline möglicherweise betroffen.`
            : summary.warning > 0
            ? `${summary.warning} Dienst(e) unter Beobachtung. Keine Auswirkung auf Entscheidungen.`
            : summary.degraded > 0
            ? `${summary.degraded} Dienst(e) mit erhöhter Latenz. Keine Auswirkung.`
            : "Alle Systeme stabil. Volle Operationsfähigkeit."
          }
        </p>
      </div>
    </div>
  );
}

// ─── Operation Layer (LIVE logs) ─────────────────────────────

function OperationView({ serviceData, incidents }) {
  const summary = serviceData?.summary || {};
  const source = serviceData?._source || "unknown";

  return (
    <div className="h-full overflow-y-auto p-5 space-y-4">
      <div className="mb-4">
        <h2 className="text-base font-semibold mb-1" style={{ color: N.tm, fontFamily: "'Bricolage Grotesque'", margin: 0 }}>
          Operations-Ebene
        </h2>
        <p className="text-xs" style={{ color: N.td, margin: 0 }}>
          Quelle: {source} · Zyklus: {serviceData?.cycle_ms ? `${serviceData.cycle_ms}ms` : "—"}
        </p>
      </div>

      {/* Live Incident Log */}
      <div className="rounded-xl overflow-hidden" style={{ backgroundColor: "#050508", border: `1px solid ${N.b}` }}>
        <div className="px-3 py-2 flex items-center gap-2" style={{ borderBottom: `1px solid ${N.b}` }}>
          <span className="rounded-full" style={{ width: 8, height: 8, backgroundColor: ST.crit, opacity: 0.6 }} />
          <span className="rounded-full" style={{ width: 8, height: 8, backgroundColor: ST.warn, opacity: 0.6 }} />
          <span className="rounded-full" style={{ width: 8, height: 8, backgroundColor: ST.ok, opacity: 0.6 }} />
          <span className="font-mono ml-2" style={{ fontSize: 9, color: N.td }}>sentinel — LIVE</span>
        </div>
        <div className="p-3 font-mono space-y-0.5" style={{ fontSize: 10, maxHeight: 200, overflowY: "auto" }}>
          {(incidents || []).slice(-10).map((inc, i) => (
            <div key={i} style={{
              color: inc.to_status === "CRITICAL" ? ST.crit :
                     inc.to_status === "WARNING" ? ST.warn :
                     inc.to_status === "DEGRADED" ? ST.deg :
                     inc.to_status === "NOMINAL" ? ST.ok : N.tm,
              lineHeight: 1.6,
            }}>
              [{inc.timestamp?.slice(11, 19) || "??:??:??"}] {inc.from_status} → {inc.to_status}
              {inc.trigger ? ` (${inc.trigger})` : ""}
            </div>
          ))}
          {(!incidents || incidents.length === 0) && (
            <div style={{ color: ST.ok }}>
              [{new Date().toISOString().slice(11, 19)}] sentinel: {summary.healthy || 0}/{summary.total || 0} healthy — nominal
            </div>
          )}
          <div style={{ color: N.tx }}>
            <span className="inline-block animate-pulse" style={{ color: G[500] }}>▋</span>
          </div>
        </div>
      </div>

      {/* Raw Summary */}
      <div className="rounded-xl p-4" style={{ backgroundColor: N.e, border: `1px solid ${N.b}` }}>
        <span className="tracking-wider" style={{ fontSize: 10, color: N.tm, letterSpacing: "0.08em" }}>
          SYSTEMZUSTAND · RAW
        </span>
        <pre className="mt-2 font-mono" style={{ fontSize: 9, color: N.tm, lineHeight: 1.5, margin: 0, whiteSpace: "pre-wrap" }}>
          {JSON.stringify(summary, null, 2)}
        </pre>
      </div>

      {/* Foundation B2 */}
      <div className="rounded-xl p-4" style={{ backgroundColor: N.e, border: `1px solid ${N.b}` }}>
        <span className="tracking-wider" style={{ fontSize: 10, color: N.tm, letterSpacing: "0.08em" }}>
          FUNDAÇÃO B2
        </span>
        <div className="mt-2 font-mono space-y-1" style={{ fontSize: 10 }}>
          <div style={{ color: N.tm }}>ID: INFRA-20260215-B2-001</div>
          <div style={{ color: ST.ok }}>Integrität: VERIFIZIERT ✓</div>
          <div style={{ color: N.td }}>Versiegelt: 15.02.2026 16:01 UTC</div>
        </div>
      </div>
    </div>
  );
}

// ─── Layer Tabs ──────────────────────────────────────────────

function LayerTabs({ active, onChange }) {
  const layers = [
    { id: "minister", icon: "🏛", label: "Minister", sub: "Entscheiden" },
    { id: "architektur", icon: "⚙", label: "Architektur", sub: "Interpretieren" },
    { id: "operation", icon: "🛠", label: "Operation", sub: "Ausführen" },
  ];
  return (
    <div className="flex gap-1">
      {layers.map((l) => (
        <button key={l.id} onClick={() => onChange(l.id)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border-0 cursor-pointer transition-all"
          style={{
            backgroundColor: active === l.id ? (
              l.id === "minister" ? "rgba(196,148,15,0.1)" :
              l.id === "architektur" ? "rgba(96,165,250,0.08)" : "rgba(138,136,128,0.08)"
            ) : "transparent",
            color: active === l.id ? (
              l.id === "minister" ? G[300] : l.id === "architektur" ? ST.info : N.tm
            ) : N.td,
          }}>
          <span style={{ fontSize: 11 }}>{l.icon}</span>
          <span style={{ fontSize: 11 }}>{l.label}</span>
        </button>
      ))}
    </div>
  );
}

// ═══ MAIN COMPONENT ══════════════════════════════════════════

export default function MeisterwerkLive() {
  const [layer, setLayer] = useState("minister");
  const [expandedDecision, setExpandedDecision] = useState(null);

  // Live data state
  const [minister, setMinister] = useState(null);
  const [serviceData, setServiceData] = useState(null);
  const [incidents, setIncidents] = useState([]);
  const [connected, setConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [error, setError] = useState(null);

  // Polling
  const pollRef = useRef(null);

  const fetchData = useCallback(async () => {
    try {
      // Fetch minister view (always needed for SovereignPulse)
      const ministerData = await fetchSentinel("/api/minister");
      if (ministerData) {
        setMinister(ministerData);
        setConnected(true);
        setLastUpdate(Date.now());
        setError(null);
      }

      // Fetch full status for architektur/operation views
      if (layer === "architektur" || layer === "operation") {
        const status = await fetchSentinel("/api/status");
        if (status) setServiceData(status);
      }

      // Fetch incidents for operation view
      if (layer === "operation") {
        const incData = await fetchSentinel("/api/incidents");
        if (incData?.incidents) setIncidents(incData.incidents);
      }
    } catch (err) {
      setConnected(false);
      setError(err.message);
    }
  }, [layer]);

  useEffect(() => {
    fetchData(); // Initial fetch
    const interval = layer === "minister" ? MINISTER_POLL_MS : POLL_INTERVAL_MS;
    pollRef.current = setInterval(fetchData, interval);
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [fetchData, layer]);

  // Derive status for decision blocking
  const currentStatus = minister?.label?.includes("HANDLUNG") ? "CRITICAL" :
    minister?.label?.includes("AUFMERKSAMKEIT") ? "WARNING" : "NOMINAL";

  return (
    <div style={{
      backgroundColor: N.bg, color: N.t, minHeight: "100vh",
      fontFamily: "'Outfit', -apple-system, sans-serif",
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600&family=JetBrains+Mono:wght@300;400;500&family=Bricolage+Grotesque:wght@400;500;600;700&display=swap');
        @keyframes orbPulse { 0%,100% { transform:scale(1);opacity:.15; } 50% { transform:scale(1.4);opacity:.08; } }
        @keyframes criticalBlink { 0%,100% { opacity:1; } 50% { opacity:.6; } }
        @keyframes slideDown { from { opacity:0;transform:translateY(-6px); } to { opacity:1;transform:translateY(0); } }
        * { box-sizing:border-box; }
        ::-webkit-scrollbar { width:3px; }
        ::-webkit-scrollbar-track { background:transparent; }
        ::-webkit-scrollbar-thumb { background:${N.b}; border-radius:4px; }
      `}</style>

      <SovereignPulse minister={minister} connected={connected} />

      <header className="flex items-center justify-between px-5 py-3" style={{ borderBottom: `1px solid ${N.b}` }}>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span style={{ color: G[400], fontSize: 18, fontWeight: 700, fontFamily: "'Bricolage Grotesque'" }}>◆</span>
            <div>
              <h1 className="text-base font-semibold m-0" style={{
                color: G[200], fontFamily: "'Bricolage Grotesque'", fontSize: 15, lineHeight: 1,
              }}>
                A4 Desk <span style={{ color: ST.ok, fontWeight: 400, fontSize: 11 }}>LIVE</span>
              </h1>
              <span className="font-mono" style={{ fontSize: 8, color: N.td }}>
                MEISTERWERK · SENTINEL BRIDGE
              </span>
            </div>
          </div>
          <span style={{ color: N.b }}>│</span>
          <LayerTabs active={layer} onChange={setLayer} />
        </div>
        <div className="flex items-center gap-3">
          {error && (
            <span className="font-mono rounded px-2 py-0.5" style={{ fontSize: 8, backgroundColor: "rgba(248,113,113,0.1)", color: ST.crit }}>
              {error}
            </span>
          )}
          <div className="rounded-full flex items-center justify-center"
            style={{ width: 28, height: 28, backgroundColor: G[800], border: `1px solid ${G[600]}` }}>
            <span style={{ color: G[300], fontSize: 10, fontWeight: 600 }}>JM</span>
          </div>
        </div>
      </header>

      <div className="flex" style={{ height: "calc(100vh - 82px)" }}>
        {layer === "minister" && (
          <>
            <div className="overflow-y-auto p-4 space-y-4" style={{ width: "55%", borderRight: `1px solid ${N.b}` }}>
              <MentalStateCard minister={minister} />
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <span style={{ color: G[400], fontSize: 12 }}>⚖</span>
                  <span className="tracking-wider" style={{ fontSize: 10, color: N.tm, letterSpacing: "0.08em" }}>
                    ENTSCHEIDUNGEN
                  </span>
                  <span className="rounded-full flex items-center justify-center"
                    style={{ width: 18, height: 18, backgroundColor: G[900], color: G[400], fontSize: 10, fontWeight: 600 }}>
                    {DECISIONS.length}
                  </span>
                </div>
                <div className="space-y-2.5">
                  {DECISIONS.map(d => (
                    <OracleCard key={d.id} decision={d} ministerStatus={currentStatus}
                      expanded={expandedDecision === d.id}
                      onToggle={() => setExpandedDecision(expandedDecision === d.id ? null : d.id)} />
                  ))}
                </div>
              </div>
            </div>
            <div className="overflow-y-auto p-4 space-y-4" style={{ width: "45%" }}>
              <IntegrityGauge confidence={minister?.confidence || 100} />
              {/* Future: EscalationTimeline from /api/escalation */}
              <div className="rounded-xl p-4" style={{ backgroundColor: N.e, border: `1px solid ${N.b}` }}>
                <div className="flex items-center gap-2 mb-2">
                  <span style={{ fontSize: 11 }}>⚡</span>
                  <span className="tracking-wider" style={{ fontSize: 10, color: N.tm, letterSpacing: "0.08em" }}>
                    SYSTEMVERBINDUNG
                  </span>
                </div>
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="font-mono" style={{ fontSize: 10, color: N.td }}>Sentinel Bridge</span>
                    <Orb color={connected ? ST.ok : ST.crit} size={5} />
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="font-mono" style={{ fontSize: 10, color: N.td }}>Polling</span>
                    <span className="font-mono" style={{ fontSize: 9, color: N.td }}>{MINISTER_POLL_MS / 1000}s</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="font-mono" style={{ fontSize: 10, color: N.td }}>Letzte Aktualisierung</span>
                    <span className="font-mono" style={{ fontSize: 9, color: N.td }}>
                      {lastUpdate ? `vor ${Math.round((Date.now() - lastUpdate) / 1000)}s` : "—"}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="font-mono" style={{ fontSize: 10, color: N.td }}>API Endpunkt</span>
                    <span className="font-mono" style={{ fontSize: 8, color: N.td }}>{API_BASE}/api/minister</span>
                  </div>
                </div>
              </div>
            </div>
          </>
        )}

        {layer === "architektur" && <ArchitekturView serviceData={serviceData} />}
        {layer === "operation" && <OperationView serviceData={serviceData} incidents={incidents} />}
      </div>
    </div>
  );
}
