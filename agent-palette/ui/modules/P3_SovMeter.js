/**
 * ═══════════════════════════════════════════════════════════════════════════════════
 * WINDI P3 — SovMeter (Sovereignty Meter)
 * Measures system sovereignty: local services / total services
 * ═══════════════════════════════════════════════════════════════════════════════════
 * 
 * Different from TrustRadar (user trust score)
 * SovMeter measures SYSTEM sovereignty percentage
 * 
 * @module P3_SovMeter
 * @version 1.0.0
 */

const { useState, useEffect } = React;

// ─── SOVEREIGNTY LABELS ───────────────────────────────────────────────────────
const SOV_LABELS = {
  de: {
    sovereign: "Souverän",
    hybrid: "Hybrid",
    dependent: "Abhängig",
    local: "Lokal",
    cloud: "Cloud",
    encrypted: "Verschlüsselt",
    services: "Dienste",
    sovereignty: "Souveränität"
  },
  en: {
    sovereign: "Sovereign",
    hybrid: "Hybrid",
    dependent: "Dependent",
    local: "Local",
    cloud: "Cloud",
    encrypted: "Encrypted",
    services: "Services",
    sovereignty: "Sovereignty"
  },
  pt: {
    sovereign: "Soberano",
    hybrid: "Híbrido",
    dependent: "Dependente",
    local: "Local",
    cloud: "Cloud",
    encrypted: "Encriptado",
    services: "Serviços",
    sovereignty: "Soberania"
  }
};

// ─── SERVICES TO CHECK ────────────────────────────────────────────────────────
const SOVEREIGNTY_SERVICES = [
  { key: "wallet", port: 8099, name: "Wallet" },
  { key: "desktop", port: 8100, name: "Desktop" },
  { key: "ledger", port: 8101, name: "Ledger" },
  { key: "sentinel", port: 8102, name: "Sentinel" },
  { key: "export", port: 8103, name: "Export" },
  { key: "jmpg", port: 8104, name: "JMPG" },
  { key: "communique", port: 8105, name: "Communiqué" },
  { key: "vault", port: 8106, name: "Vault" },
  { key: "pulse", port: 8109, name: "Pulse" }
];

/**
 * Calculates sovereignty score
 * @param {object} context - WindiContext instance
 * @returns {{score: number, local: number, total: number, breakdown: object[]}}
 */
export function calculateSovereignty(context) {
  if (!context || !context.endpoints) {
    return { score: 0, local: 0, total: SOVEREIGNTY_SERVICES.length, breakdown: [] };
  }

  const breakdown = [];
  let localCount = 0;
  const total = SOVEREIGNTY_SERVICES.length;

  for (const svc of SOVEREIGNTY_SERVICES) {
    const endpoint = context.endpoints[svc.key];
    const isLocal = endpoint && (
      endpoint.includes("localhost") || 
      endpoint.includes("127.0.0.1") ||
      endpoint.includes("windi-domain.com") // Our server = local
    );
    
    breakdown.push({
      key: svc.key,
      name: svc.name,
      port: svc.port,
      available: endpoint !== null,
      isLocal: isLocal
    });

    if (isLocal) localCount++;
  }

  const score = total > 0 ? Math.round((localCount / total) * 100) : 0;
  return { score, local: localCount, total, breakdown };
}

/**
 * Gets sovereignty status based on score
 * @param {number} score - Sovereignty percentage
 * @returns {{status: string, emoji: string, color: string}}
 */
export function getSovereigntyStatus(score) {
  if (score >= 90) return { status: "sovereign", emoji: "🏛️", color: "success" };
  if (score >= 70) return { status: "hybrid", emoji: "⚡", color: "warning" };
  return { status: "dependent", emoji: "⚠️", color: "danger" };
}

/**
 * SovMeter React Component
 * Displays sovereignty percentage with visual indicator
 * 
 * @param {object} props
 * @param {object} props.context - WindiContext instance
 * @param {object} props.theme - KLAR/NOIR theme object
 * @param {string} props.lang - Language code (de/en/pt)
 * @param {boolean} props.compact - Compact mode (default true)
 */
export function SovMeter({ context, theme, lang = "de", compact = true }) {
  const [expanded, setExpanded] = useState(false);
  const [sovData, setSovData] = useState({ score: 93, local: 9, total: 9, breakdown: [] });

  const th = theme || {
    gold: "#8B6914",
    success: "#4A7C59",
    warning: "#B8860B",
    danger: "#A94442",
    dim: "#6B6560",
    text: "#2C2924",
    card: "#FDFBF5",
    border: "#DDD6C2"
  };

  const labels = SOV_LABELS[lang] || SOV_LABELS.en;

  useEffect(() => {
    if (context) {
      setSovData(calculateSovereignty(context));
    }
  }, [context]);

  const { status, emoji, color } = getSovereigntyStatus(sovData.score);
  const statusColor = th[color] || th.gold;
  const statusLabel = labels[status];

  // Compact view (header bar)
  if (compact && !expanded) {
    return (
      <div
        onClick={() => setExpanded(true)}
        style={{
          display: "flex",
          alignItems: "center",
          gap: 4,
          padding: "2px 8px",
          borderRadius: 6,
          background: statusColor + "15",
          border: "1px solid " + statusColor + "33",
          cursor: "pointer",
          fontSize: 9,
          fontFamily: "'JetBrains Mono', monospace",
          color: statusColor,
          transition: "all 0.2s"
        }}
        title={labels.sovereignty + ": " + sovData.score + "%"}
      >
        <span>{emoji}</span>
        <span style={{ fontWeight: 600 }}>{sovData.score}%</span>
        <span style={{ color: th.dim, fontSize: 8 }}>{labels.local}</span>
      </div>
    );
  }

  // Expanded view (tooltip/popover)
  return (
    <div style={{ position: "relative" }}>
      {/* Trigger */}
      <div
        onClick={() => setExpanded(!expanded)}
        style={{
          display: "flex",
          alignItems: "center",
          gap: 4,
          padding: "2px 8px",
          borderRadius: 6,
          background: statusColor + "15",
          border: "1px solid " + statusColor + "33",
          cursor: "pointer",
          fontSize: 9,
          fontFamily: "'JetBrains Mono', monospace",
          color: statusColor
        }}
      >
        <span>{emoji}</span>
        <span style={{ fontWeight: 600 }}>{sovData.score}%</span>
        <span style={{ color: th.dim, fontSize: 8 }}>{statusLabel}</span>
      </div>

      {/* Expanded Panel */}
      {expanded && (
        <div
          style={{
            position: "absolute",
            top: "100%",
            right: 0,
            marginTop: 6,
            background: th.card,
            border: "1px solid " + th.border,
            borderRadius: 10,
            padding: 12,
            minWidth: 200,
            boxShadow: "0 4px 16px rgba(0,0,0,0.1)",
            zIndex: 100,
            fontFamily: "'Bricolage Grotesque', sans-serif"
          }}
          onClick={e => e.stopPropagation()}
        >
          {/* Header */}
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 10 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <span style={{ fontSize: 16 }}>{emoji}</span>
              <span style={{ fontSize: 12, fontWeight: 700, color: th.text }}>{labels.sovereignty}</span>
            </div>
            <button
              onClick={() => setExpanded(false)}
              style={{ background: "none", border: "none", color: th.dim, cursor: "pointer", fontSize: 14 }}
            >×</button>
          </div>

          {/* Progress Bar */}
          <div style={{ 
            height: 8, 
            background: th.border, 
            borderRadius: 4, 
            overflow: "hidden",
            marginBottom: 10 
          }}>
            <div style={{
              height: "100%",
              width: sovData.score + "%",
              background: "linear-gradient(90deg, " + th.success + ", " + th.gold + ")",
              borderRadius: 4,
              transition: "width 0.5s ease"
            }} />
          </div>

          {/* Score */}
          <div style={{ 
            display: "flex", 
            justifyContent: "space-between", 
            fontSize: 11, 
            marginBottom: 10,
            color: th.text 
          }}>
            <span>{sovData.local}/{sovData.total} {labels.services}</span>
            <span style={{ fontWeight: 700, color: statusColor }}>{sovData.score}%</span>
          </div>

          {/* Breakdown */}
          <div style={{ fontSize: 9, color: th.dim }}>
            {sovData.breakdown.map(svc => (
              <div key={svc.key} style={{ 
                display: "flex", 
                alignItems: "center", 
                gap: 6, 
                padding: "2px 0" 
              }}>
                <span style={{ 
                  width: 6, 
                  height: 6, 
                  borderRadius: "50%", 
                  background: svc.isLocal ? th.success : (svc.available ? th.warning : th.danger)
                }} />
                <span>{svc.name}</span>
                <span style={{ marginLeft: "auto", fontFamily: "'JetBrains Mono', monospace" }}>
                  :{svc.port}
                </span>
                <span>{svc.isLocal ? "✓" : (svc.available ? "☁" : "✗")}</span>
              </div>
            ))}
          </div>

          {/* Legend */}
          <div style={{ 
            display: "flex", 
            gap: 10, 
            marginTop: 8, 
            paddingTop: 8, 
            borderTop: "1px solid " + th.border,
            fontSize: 8,
            color: th.dim 
          }}>
            <span>🏠 {labels.local}</span>
            <span>☁️ {labels.cloud}</span>
            <span>🔒 {labels.encrypted}</span>
          </div>
        </div>
      )}
    </div>
  );
}

export default { SovMeter, calculateSovereignty, getSovereigntyStatus };
