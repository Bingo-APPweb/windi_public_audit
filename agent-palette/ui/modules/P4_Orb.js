/**
 * ═══════════════════════════════════════════════════════════════════════════════════
 * WINDI P4 — Status Orb
 * Visual indicator of ecosystem health - pulsing SVG orb
 * ═══════════════════════════════════════════════════════════════════════════════════
 * 
 * States:
 * - ALL_GREEN: all services up, sov >= 90%
 * - DEGRADED: 1-2 services down OR sov 70-89%
 * - CRITICAL: 3+ services down OR sov < 70%
 * - UNKNOWN: loading/no data
 * 
 * @module P4_Orb
 * @version 1.0.0
 */

const { useState, useEffect, useCallback, useRef } = React;

// ─── ORB STATES ───────────────────────────────────────────────────────────────
export const ORB_STATES = {
  ALL_GREEN: "ALL_GREEN",
  DEGRADED: "DEGRADED",
  CRITICAL: "CRITICAL",
  UNKNOWN: "UNKNOWN"
};

// ─── STATUS LABELS ────────────────────────────────────────────────────────────
const STATUS_LABELS = {
  de: {
    ALL_GREEN: "Alle Systeme aktiv",
    DEGRADED: "Eingeschränkt",
    CRITICAL: "Kritisch",
    UNKNOWN: "Prüfe...",
    refresh: "Aktualisieren",
    lastCheck: "Letzte Prüfung",
    services: "Dienste"
  },
  en: {
    ALL_GREEN: "All systems active",
    DEGRADED: "Degraded",
    CRITICAL: "Critical",
    UNKNOWN: "Checking...",
    refresh: "Refresh",
    lastCheck: "Last check",
    services: "Services"
  },
  pt: {
    ALL_GREEN: "Todos sistemas activos",
    DEGRADED: "Degradado",
    CRITICAL: "Crítico",
    UNKNOWN: "A verificar...",
    refresh: "Actualizar",
    lastCheck: "Última verificação",
    services: "Serviços"
  }
};

// ─── SERVICES TO CHECK ────────────────────────────────────────────────────────
const HEALTH_SERVICES = [
  { key: "wallet", port: 8099, name: "Wallet" },
  { key: "ledger", port: 8101, name: "Ledger" },
  { key: "export", port: 8103, name: "Export" },
  { key: "vault", port: 8106, name: "Vault" },
  { key: "pulse", port: 8109, name: "Pulse" }
];

// ─── HEALTH CHECK CACHE ───────────────────────────────────────────────────────
let healthCache = {
  results: {},
  timestamp: 0,
  TTL: 30000 // 30 seconds
};

/**
 * Checks health of a single service
 * @param {string} endpoint - Service URL
 * @param {number} timeout - Timeout in ms
 * @returns {Promise<{online: boolean, latency: number}>}
 */
async function checkServiceHealth(endpoint, timeout = 2000) {
  if (!endpoint) return { online: false, latency: -1 };
  
  const start = Date.now();
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    
    const response = await fetch(endpoint, {
      method: "HEAD",
      signal: controller.signal,
      mode: "no-cors" // Allow cross-origin for health checks
    });
    
    clearTimeout(timeoutId);
    const latency = Date.now() - start;
    return { online: true, latency };
  } catch (e) {
    return { online: false, latency: -1 };
  }
}

/**
 * Checks health of all services
 * @param {object} endpoints - Endpoints object from context
 * @param {boolean} force - Force refresh, ignore cache
 * @returns {Promise<object>}
 */
export async function checkServices(endpoints, force = false) {
  const now = Date.now();
  
  // Return cached results if fresh
  if (!force && healthCache.timestamp > 0 && (now - healthCache.timestamp) < healthCache.TTL) {
    return healthCache.results;
  }

  const results = {};
  const checks = HEALTH_SERVICES.map(async svc => {
    const endpoint = endpoints ? endpoints[svc.key] : null;
    const health = await checkServiceHealth(endpoint);
    results[svc.key] = {
      ...svc,
      endpoint,
      ...health
    };
  });

  await Promise.all(checks);
  
  // Update cache
  healthCache = {
    results,
    timestamp: now,
    TTL: healthCache.TTL
  };

  return results;
}

/**
 * Determines orb state from health results and sovereignty score
 * @param {object} healthResults - Results from checkServices
 * @param {number} sovScore - Sovereignty percentage
 * @returns {string} - One of ORB_STATES
 */
export function determineOrbState(healthResults, sovScore) {
  if (!healthResults || Object.keys(healthResults).length === 0) {
    return ORB_STATES.UNKNOWN;
  }

  const services = Object.values(healthResults);
  const downCount = services.filter(s => !s.online).length;

  if (downCount >= 3 || sovScore < 70) {
    return ORB_STATES.CRITICAL;
  }
  
  if (downCount >= 1 || sovScore < 90) {
    return ORB_STATES.DEGRADED;
  }

  return ORB_STATES.ALL_GREEN;
}

/**
 * StatusOrb React Component
 * Animated SVG orb showing system health
 * 
 * @param {object} props
 * @param {object} props.context - WindiContext instance
 * @param {number} props.sovScore - Sovereignty percentage
 * @param {object} props.theme - KLAR/NOIR theme object
 * @param {string} props.lang - Language code
 * @param {number} props.size - Orb size in px (default 32)
 */
export function StatusOrb({ context, sovScore = 93, theme, lang = "de", size = 32 }) {
  const [orbState, setOrbState] = useState(ORB_STATES.UNKNOWN);
  const [healthResults, setHealthResults] = useState({});
  const [expanded, setExpanded] = useState(false);
  const [lastCheck, setLastCheck] = useState(null);
  const [checking, setChecking] = useState(false);
  const checkRef = useRef(null);

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

  const labels = STATUS_LABELS[lang] || STATUS_LABELS.en;

  // Orb colors by state
  const orbColors = {
    [ORB_STATES.ALL_GREEN]: th.success,
    [ORB_STATES.DEGRADED]: th.warning,
    [ORB_STATES.CRITICAL]: th.danger,
    [ORB_STATES.UNKNOWN]: th.dim
  };

  const orbColor = orbColors[orbState];

  // Perform health check
  const doHealthCheck = useCallback(async (force = false) => {
    if (!context || !context.endpoints) return;
    
    setChecking(true);
    try {
      const results = await checkServices(context.endpoints, force);
      setHealthResults(results);
      setOrbState(determineOrbState(results, sovScore));
      setLastCheck(new Date());
    } catch (e) {
      console.warn("[StatusOrb] Health check failed:", e);
    }
    setChecking(false);
  }, [context, sovScore]);

  // Initial check and periodic refresh
  useEffect(() => {
    doHealthCheck();
    
    // Refresh every 60 seconds
    checkRef.current = setInterval(() => doHealthCheck(), 60000);
    
    return () => {
      if (checkRef.current) clearInterval(checkRef.current);
    };
  }, [doHealthCheck]);

  // Update state when sovScore changes
  useEffect(() => {
    if (Object.keys(healthResults).length > 0) {
      setOrbState(determineOrbState(healthResults, sovScore));
    }
  }, [sovScore, healthResults]);

  // Animation style based on state
  const getAnimation = () => {
    switch (orbState) {
      case ORB_STATES.ALL_GREEN:
        return "pulse 2s ease-in-out infinite";
      case ORB_STATES.DEGRADED:
        return "blink 1.5s ease-in-out infinite";
      case ORB_STATES.CRITICAL:
        return "blink 0.5s ease-in-out infinite";
      default:
        return "none";
    }
  };

  // Inject keyframes
  useEffect(() => {
    const styleId = "windi-orb-styles";
    if (!document.getElementById(styleId)) {
      const style = document.createElement("style");
      style.id = styleId;
      style.textContent = String.raw`
        @keyframes pulse {
          0%, 100% { opacity: 0.7; transform: scale(1); }
          50% { opacity: 1; transform: scale(1.05); }
        }
        @keyframes blink {
          0%, 100% { opacity: 0.4; }
          50% { opacity: 1; }
        }
      `;
      document.head.appendChild(style);
    }
  }, []);

  return (
    <div style={{ position: "relative" }}>
      {/* Orb SVG */}
      <svg
        width={size}
        height={size}
        viewBox="0 0 32 32"
        onClick={() => setExpanded(!expanded)}
        style={{ cursor: "pointer", animation: getAnimation() }}
      >
        {/* Glow effect */}
        <defs>
          <filter id="orbGlow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
            <feMerge>
              <feMergeNode in="coloredBlur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
        </defs>
        
        {/* Main circle */}
        <circle
          cx="16"
          cy="16"
          r="12"
          fill={orbColor}
          filter="url(#orbGlow)"
          style={{ transition: "fill 0.3s ease" }}
        />
        
        {/* Inner highlight */}
        <circle
          cx="13"
          cy="13"
          r="4"
          fill="rgba(255,255,255,0.3)"
        />
      </svg>

      {/* Mini Dashboard Popover */}
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
            minWidth: 220,
            boxShadow: "0 4px 16px rgba(0,0,0,0.1)",
            zIndex: 100,
            fontFamily: "'Bricolage Grotesque', sans-serif"
          }}
          onClick={e => e.stopPropagation()}
        >
          {/* Header */}
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 10 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <div style={{
                width: 10,
                height: 10,
                borderRadius: "50%",
                background: orbColor
              }} />
              <span style={{ fontSize: 12, fontWeight: 700, color: th.text }}>
                {labels[orbState]}
              </span>
            </div>
            <button
              onClick={() => setExpanded(false)}
              style={{ background: "none", border: "none", color: th.dim, cursor: "pointer", fontSize: 14 }}
            >×</button>
          </div>

          {/* Services List */}
          <div style={{ fontSize: 10, marginBottom: 10 }}>
            {HEALTH_SERVICES.map(svc => {
              const result = healthResults[svc.key] || { online: false, latency: -1 };
              return (
                <div key={svc.key} style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                  padding: "3px 0",
                  borderBottom: "1px solid " + th.border + "44"
                }}>
                  <div style={{
                    width: 6,
                    height: 6,
                    borderRadius: "50%",
                    background: result.online ? th.success : th.danger
                  }} />
                  <span style={{ color: th.text }}>{svc.name}</span>
                  <span style={{ 
                    marginLeft: "auto", 
                    fontFamily: "'JetBrains Mono', monospace",
                    fontSize: 9,
                    color: th.dim 
                  }}>
                    :{svc.port}
                  </span>
                  <span style={{ 
                    fontSize: 9,
                    color: result.online ? th.success : th.danger 
                  }}>
                    {result.online ? (result.latency + "ms") : "✗"}
                  </span>
                </div>
              );
            })}
          </div>

          {/* Footer */}
          <div style={{ 
            display: "flex", 
            alignItems: "center", 
            justifyContent: "space-between",
            fontSize: 9,
            color: th.dim 
          }}>
            <span>
              {labels.lastCheck}: {lastCheck ? lastCheck.toLocaleTimeString() : "-"}
            </span>
            <button
              onClick={() => doHealthCheck(true)}
              disabled={checking}
              style={{
                padding: "3px 8px",
                borderRadius: 4,
                background: th.gold + "15",
                border: "1px solid " + th.gold + "33",
                color: th.gold,
                fontSize: 9,
                cursor: "pointer",
                opacity: checking ? 0.5 : 1
              }}
            >
              {checking ? "..." : labels.refresh}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default { StatusOrb, checkServices, determineOrbState, ORB_STATES };
