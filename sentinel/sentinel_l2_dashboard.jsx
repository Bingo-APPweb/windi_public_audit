import { useState, useEffect, useCallback } from "react";

// ─────────────────────────────────────────────────────────
// WINDI SENTINEL — Nível 2: Painel de Autorização Humana
// "Sentinel propõe. Humano autoriza. WINDI garante."
// ─────────────────────────────────────────────────────────

const TRANSLATIONS = {
  DE: {
    title: "Sentinel Kontrollzentrum",
    subtitle: "Protokoll der menschlichen Intervention",
    pending: "Ausstehend",
    history: "Verlauf",
    authorize: "Genehmigen",
    veto: "Ablehnen",
    noProposals: "Keine ausstehenden Vorschläge",
    allClear: "Alle Systeme nominal — der Sentinel wacht.",
    service: "Dienst",
    action: "Aktion",
    impact: "Auswirkung",
    severity: "Schweregrad",
    failures: "Ausfälle",
    created: "Erstellt",
    status: "Status",
    decidedBy: "Entschieden von",
    vetoReason: "Grund der Ablehnung",
    vetoPlaceholder: "Begründung für die Ablehnung...",
    confirmAuth: "Ausführung genehmigen?",
    confirmVeto: "Vorschlag ablehnen?",
    receipt: "Quittung",
    level: "Autorisierungsstufe",
    command: "Befehl",
    goldenRule: "I9: Keine Autonomie-Eskalation · Der Mensch entscheidet immer",
    impactLevels: { LOW: "Gering", MEDIUM: "Mittel", HIGH: "Hoch", CRITICAL: "Kritisch" },
    authLevels: {
      PRE_AUTHORIZED: "Vorautorisiert",
      HUMAN_EXPLICIT: "Menschliche Genehmigung",
      HUMAN_CONFIRMED: "Bestätigt + Passphrase",
      FORBIDDEN: "Verboten"
    },
    statusLabels: {
      PENDING: "Ausstehend", AUTHORIZED: "Genehmigt", VETOED: "Abgelehnt",
      EXECUTING: "Wird ausgeführt", COMPLETED: "Abgeschlossen",
      FAILED: "Fehlgeschlagen", EXPIRED: "Abgelaufen"
    },
    systemStatus: "Systemstatus",
    healthy: "Gesund",
    cycles: "Zyklen",
    uptime: "Betriebszeit",
    sentinel: "Sentinel"
  },
  EN: {
    title: "Sentinel Control Center",
    subtitle: "Human Intervention Protocol",
    pending: "Pending",
    history: "History",
    authorize: "Authorize",
    veto: "Veto",
    noProposals: "No pending proposals",
    allClear: "All systems nominal — the Sentinel watches.",
    service: "Service",
    action: "Action",
    impact: "Impact",
    severity: "Severity",
    failures: "Failures",
    created: "Created",
    status: "Status",
    decidedBy: "Decided by",
    vetoReason: "Veto reason",
    vetoPlaceholder: "Reason for vetoing...",
    confirmAuth: "Authorize execution?",
    confirmVeto: "Veto this proposal?",
    receipt: "Receipt",
    level: "Authorization Level",
    command: "Command",
    goldenRule: "I9: No Autonomy Escalation · The Human always decides",
    impactLevels: { LOW: "Low", MEDIUM: "Medium", HIGH: "High", CRITICAL: "Critical" },
    authLevels: {
      PRE_AUTHORIZED: "Pre-authorized",
      HUMAN_EXPLICIT: "Human Approval",
      HUMAN_CONFIRMED: "Confirmed + Passphrase",
      FORBIDDEN: "Forbidden"
    },
    statusLabels: {
      PENDING: "Pending", AUTHORIZED: "Authorized", VETOED: "Vetoed",
      EXECUTING: "Executing", COMPLETED: "Completed",
      FAILED: "Failed", EXPIRED: "Expired"
    },
    systemStatus: "System Status",
    healthy: "Healthy",
    cycles: "Cycles",
    uptime: "Uptime",
    sentinel: "Sentinel"
  },
  PT: {
    title: "Centro de Controle Sentinel",
    subtitle: "Protocolo de Intervenção Humana",
    pending: "Pendente",
    history: "Histórico",
    authorize: "Autorizar",
    veto: "Vetar",
    noProposals: "Nenhuma proposta pendente",
    allClear: "Todos os sistemas nominais — o Sentinel vigia.",
    service: "Serviço",
    action: "Ação",
    impact: "Impacto",
    severity: "Severidade",
    failures: "Falhas",
    created: "Criado",
    status: "Status",
    decidedBy: "Decidido por",
    vetoReason: "Razão do veto",
    vetoPlaceholder: "Motivo do veto...",
    confirmAuth: "Autorizar execução?",
    confirmVeto: "Vetar esta proposta?",
    receipt: "Recibo",
    level: "Nível de Autorização",
    command: "Comando",
    goldenRule: "I9: Proibição de Escalação de Autonomia · O Humano sempre decide",
    impactLevels: { LOW: "Baixo", MEDIUM: "Médio", HIGH: "Alto", CRITICAL: "Crítico" },
    authLevels: {
      PRE_AUTHORIZED: "Pré-autorizado",
      HUMAN_EXPLICIT: "Aprovação Humana",
      HUMAN_CONFIRMED: "Confirmado + Passphrase",
      FORBIDDEN: "Proibido"
    },
    statusLabels: {
      PENDING: "Pendente", AUTHORIZED: "Autorizado", VETOED: "Vetado",
      EXECUTING: "Executando", COMPLETED: "Concluído",
      FAILED: "Falhou", EXPIRED: "Expirado"
    },
    systemStatus: "Status do Sistema",
    healthy: "Saudável",
    cycles: "Ciclos",
    uptime: "Tempo ativo",
    sentinel: "Sentinel"
  }
};

// ── Mock data for demonstration ──
const MOCK_SENTINEL_STATUS = {
  status: "NOMINAL",
  total_checks: 318,
  started_at: "2026-02-15T15:26:37Z",
  summary: { healthy: 9, total: 10, degraded: 0, critical: 0 },
  services: {
    governance: { status: "healthy", consecutive_ok: 258, port: 8080 },
    babel: { status: "healthy", consecutive_ok: 318, port: 8085 },
    landing: { status: "healthy", consecutive_ok: 318, port: 8086 },
    cortex: { status: "healthy", consecutive_ok: 318, port: 8089 },
    warroom: { status: "healthy", consecutive_ok: 318, port: 8090 },
    clone: { status: "healthy", consecutive_ok: 276, port: 8092 },
    forensic: { status: "unhealthy", consecutive_fail: 60, port: 8094 },
    bridge: { status: "healthy", consecutive_ok: 318, port: 8097 },
    brain: { status: "healthy", consecutive_ok: 318, port: null },
    gateway: { status: "healthy", consecutive_ok: 318, port: null },
  }
};

const MOCK_PROPOSALS = [
  {
    proposal_id: "SEN-20260215-0001",
    created_at: "2026-02-15T20:44:05Z",
    trigger_service: "windi-forensic",
    trigger_reason: "60 consecutive failures on :8094 — systemd inactive",
    trigger_severity: "ALERT",
    consecutive_failures: 60,
    action_type: "RESTART_SERVICE",
    action_command: "sudo systemctl restart windi-forensic",
    action_description: "Restart service windi-forensic",
    impact_level: "MEDIUM",
    authorization_required: "HUMAN_EXPLICIT",
    estimated_downtime_sec: 5,
    status: "PENDING",
    proposal_hash: "a7f3c91e2b4d8f01",
    description_de: "Dienst windi-forensic neu starten",
    description_en: "Restart service windi-forensic",
    description_pt: "Reiniciar serviço windi-forensic",
  }
];

const MOCK_HISTORY = [
  {
    proposal_id: "SEN-20260215-0000",
    created_at: "2026-02-15T16:01:43Z",
    trigger_service: "windi-governance",
    trigger_reason: "Health check path mismatch — /health vs /api/status",
    trigger_severity: "ALERT",
    action_type: "RESTART_SERVICE",
    impact_level: "MEDIUM",
    status: "VETOED",
    decided_by: "human_dragon",
    decided_at: "2026-02-15T16:05:00Z",
    veto_reason: "Falso alarme — API está operacional, path do check está errado",
    proposal_hash: "c4d2e8f1a3b7c901",
  }
];

// ── Impact color mapping ──
const impactColors = {
  LOW: { bg: "rgba(46,139,87,0.15)", border: "#2E8B57", text: "#2E8B57", glow: "rgba(46,139,87,0.3)" },
  MEDIUM: { bg: "rgba(196,148,15,0.15)", border: "#C4940F", text: "#C4940F", glow: "rgba(196,148,15,0.3)" },
  HIGH: { bg: "rgba(204,85,0,0.15)", border: "#CC5500", text: "#CC5500", glow: "rgba(204,85,0,0.3)" },
  CRITICAL: { bg: "rgba(180,30,30,0.15)", border: "#B41E1E", text: "#B41E1E", glow: "rgba(180,30,30,0.5)" },
};

const statusColors = {
  PENDING: "#C4940F",
  AUTHORIZED: "#2E8B57",
  VETOED: "#B41E1E",
  COMPLETED: "#2E8B57",
  FAILED: "#B41E1E",
  EXPIRED: "#666",
  EXECUTING: "#4A90D9",
};

// ── Sentinel Pulse SVG ──
function SentinelPulse({ status, size = 120 }) {
  const isNominal = status === "NOMINAL";
  const color = isNominal ? "#C4940F" : "#B41E1E";
  return (
    <svg width={size} height={size} viewBox="0 0 120 120">
      <defs>
        <filter id="sentinel-glow">
          <feGaussianBlur stdDeviation="3" result="blur" />
          <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
      </defs>
      <circle cx="60" cy="60" r="50" fill="none" stroke={color} strokeWidth="1" opacity="0.2" />
      <circle cx="60" cy="60" r="40" fill="none" stroke={color} strokeWidth="1" opacity="0.3">
        <animate attributeName="r" values="38;42;38" dur="3s" repeatCount="indefinite" />
        <animate attributeName="opacity" values="0.3;0.5;0.3" dur="3s" repeatCount="indefinite" />
      </circle>
      <circle cx="60" cy="60" r="28" fill={`${color}15`} stroke={color} strokeWidth="1.5" filter="url(#sentinel-glow)">
        <animate attributeName="r" values="26;30;26" dur="2s" repeatCount="indefinite" />
      </circle>
      {/* Shield icon */}
      <path d="M60 35 L75 45 L75 60 Q75 75 60 82 Q45 75 45 60 L45 45 Z"
        fill="none" stroke={color} strokeWidth="2" filter="url(#sentinel-glow)" />
      <path d="M53 58 L58 63 L68 53" fill="none" stroke={color} strokeWidth="2.5"
        strokeLinecap="round" strokeLinejoin="round" opacity={isNominal ? 1 : 0} />
      <text x="60" y="100" textAnchor="middle" fill={color}
        style={{ fontSize: "9px", fontFamily: "JetBrains Mono, monospace", letterSpacing: "2px" }}>
        {status}
      </text>
    </svg>
  );
}

// ── Service Health Grid ──
function ServiceGrid({ services, t, theme }) {
  const isDark = theme === "noir";
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))", gap: "8px" }}>
      {Object.entries(services).map(([name, svc]) => {
        const isHealthy = svc.status === "healthy";
        const borderColor = isHealthy ? "#2E8B5740" : "#B41E1E60";
        const dotColor = isHealthy ? "#2E8B57" : "#B41E1E";
        return (
          <div key={name} style={{
            padding: "10px 12px",
            borderRadius: "8px",
            border: `1px solid ${borderColor}`,
            background: isDark ? "rgba(255,255,255,0.02)" : "rgba(0,0,0,0.02)",
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "4px" }}>
              <div style={{
                width: "8px", height: "8px", borderRadius: "50%", background: dotColor,
                boxShadow: `0 0 6px ${dotColor}60`,
              }}>
                {isHealthy && (
                  <div style={{
                    width: "8px", height: "8px", borderRadius: "50%", background: dotColor,
                    animation: "pulse 2s ease-in-out infinite",
                  }} />
                )}
              </div>
              <span style={{
                fontSize: "11px", fontFamily: "JetBrains Mono, monospace",
                color: isDark ? "#e0d9c8" : "#1a1a2e",
                fontWeight: 600,
              }}>
                {name}
              </span>
            </div>
            <div style={{
              fontSize: "10px", fontFamily: "JetBrains Mono, monospace",
              color: isDark ? "#8a8070" : "#666",
            }}>
              {svc.port ? `:${svc.port}` : "sys"} · {isHealthy ? `${svc.consecutive_ok} OK` : `${svc.consecutive_fail} fail`}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ── Proposal Card ──
function ProposalCard({ proposal, t, theme, onAuthorize, onVeto }) {
  const [showVetoInput, setShowVetoInput] = useState(false);
  const [vetoReason, setVetoReason] = useState("");
  const [confirming, setConfirming] = useState(null);
  const isDark = theme === "noir";
  const impact = impactColors[proposal.impact_level] || impactColors.MEDIUM;
  const stColor = statusColors[proposal.status] || "#666";

  const handleAuth = () => {
    if (confirming === "auth") {
      onAuthorize(proposal.proposal_id);
      setConfirming(null);
    } else {
      setConfirming("auth");
    }
  };

  const handleVeto = () => {
    if (showVetoInput) {
      onVeto(proposal.proposal_id, vetoReason);
      setShowVetoInput(false);
      setVetoReason("");
    } else {
      setShowVetoInput(true);
    }
  };

  const isPending = proposal.status === "PENDING";
  const timeAgo = getTimeAgo(proposal.created_at);

  return (
    <div style={{
      border: `1px solid ${isPending ? impact.border + "60" : (isDark ? "#333" : "#ddd")}`,
      borderRadius: "12px",
      padding: "20px",
      marginBottom: "12px",
      background: isDark
        ? `linear-gradient(135deg, rgba(20,18,15,0.9), rgba(30,28,25,0.9))`
        : `linear-gradient(135deg, rgba(255,253,248,0.95), rgba(250,248,243,0.95))`,
      boxShadow: isPending ? `0 0 20px ${impact.glow}` : "none",
      transition: "all 0.3s ease",
    }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "12px" }}>
        <div>
          <div style={{
            fontFamily: "JetBrains Mono, monospace", fontSize: "13px", fontWeight: 700,
            color: isDark ? "#C4940F" : "#8B6914",
          }}>
            {proposal.proposal_id}
          </div>
          <div style={{
            fontSize: "11px", color: isDark ? "#8a8070" : "#888", marginTop: "2px",
            fontFamily: "JetBrains Mono, monospace",
          }}>
            {timeAgo}
          </div>
        </div>
        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          <span style={{
            padding: "3px 10px", borderRadius: "12px", fontSize: "10px", fontWeight: 700,
            fontFamily: "JetBrains Mono, monospace", letterSpacing: "0.5px",
            background: impact.bg, color: impact.text, border: `1px solid ${impact.border}40`,
          }}>
            {t.impactLevels[proposal.impact_level]}
          </span>
          <span style={{
            padding: "3px 10px", borderRadius: "12px", fontSize: "10px", fontWeight: 700,
            fontFamily: "JetBrains Mono, monospace",
            background: `${stColor}15`, color: stColor, border: `1px solid ${stColor}40`,
          }}>
            {t.statusLabels[proposal.status]}
          </span>
        </div>
      </div>

      {/* Body */}
      <div style={{ marginBottom: "12px" }}>
        <div style={{
          fontSize: "14px", fontWeight: 600, marginBottom: "6px",
          color: isDark ? "#e0d9c8" : "#1a1a2e",
        }}>
          {proposal[`description_${t === TRANSLATIONS.DE ? "de" : t === TRANSLATIONS.PT ? "pt" : "en"}`] || proposal.action_description}
        </div>
        <div style={{
          fontSize: "12px", color: isDark ? "#8a8070" : "#666",
          fontFamily: "JetBrains Mono, monospace", lineHeight: "1.5",
        }}>
          {proposal.trigger_reason}
        </div>
      </div>

      {/* Command preview */}
      <div style={{
        padding: "8px 12px", borderRadius: "6px", marginBottom: "12px",
        background: isDark ? "rgba(0,0,0,0.3)" : "rgba(0,0,0,0.04)",
        fontFamily: "JetBrains Mono, monospace", fontSize: "11px",
        color: isDark ? "#C4940F90" : "#8B691480",
        border: `1px solid ${isDark ? "#333" : "#e0e0e0"}`,
      }}>
        $ {proposal.action_command}
      </div>

      {/* Auth level + hash */}
      <div style={{
        display: "flex", justifyContent: "space-between", alignItems: "center",
        marginBottom: isPending ? "16px" : "0",
        fontSize: "10px", fontFamily: "JetBrains Mono, monospace",
        color: isDark ? "#666" : "#999",
      }}>
        <span>{t.level}: {t.authLevels[proposal.authorization_required]}</span>
        <span>hash: {proposal.proposal_hash}</span>
      </div>

      {/* Decided info for non-pending */}
      {!isPending && proposal.decided_by && (
        <div style={{
          padding: "8px 12px", borderRadius: "6px", marginTop: "8px",
          background: isDark ? "rgba(0,0,0,0.2)" : "rgba(0,0,0,0.02)",
          fontSize: "11px", color: isDark ? "#8a8070" : "#666",
        }}>
          {t.decidedBy}: <strong>{proposal.decided_by}</strong>
          {proposal.veto_reason && <span> · {t.vetoReason}: {proposal.veto_reason}</span>}
          {proposal.receipt_id && <span> · {t.receipt}: {proposal.receipt_id}</span>}
        </div>
      )}

      {/* Action buttons for pending */}
      {isPending && (
        <div>
          <div style={{ display: "flex", gap: "10px" }}>
            <button onClick={handleAuth} style={{
              flex: 1, padding: "10px 16px", borderRadius: "8px", cursor: "pointer",
              border: "1px solid #2E8B5760", fontSize: "13px", fontWeight: 700,
              fontFamily: "'Bricolage Grotesque', sans-serif",
              background: confirming === "auth" ? "#2E8B57" : "rgba(46,139,87,0.1)",
              color: confirming === "auth" ? "#fff" : "#2E8B57",
              transition: "all 0.2s ease",
            }}>
              {confirming === "auth" ? t.confirmAuth : t.authorize}
            </button>
            <button onClick={handleVeto} style={{
              flex: 1, padding: "10px 16px", borderRadius: "8px", cursor: "pointer",
              border: "1px solid #B41E1E40", fontSize: "13px", fontWeight: 700,
              fontFamily: "'Bricolage Grotesque', sans-serif",
              background: "rgba(180,30,30,0.05)",
              color: "#B41E1E",
              transition: "all 0.2s ease",
            }}>
              {t.veto}
            </button>
          </div>

          {showVetoInput && (
            <div style={{ marginTop: "10px" }}>
              <input
                type="text"
                value={vetoReason}
                onChange={(e) => setVetoReason(e.target.value)}
                placeholder={t.vetoPlaceholder}
                style={{
                  width: "100%", padding: "8px 12px", borderRadius: "6px",
                  border: `1px solid ${isDark ? "#444" : "#ddd"}`,
                  background: isDark ? "rgba(0,0,0,0.3)" : "#fff",
                  color: isDark ? "#e0d9c8" : "#1a1a2e",
                  fontFamily: "JetBrains Mono, monospace", fontSize: "12px",
                  outline: "none", boxSizing: "border-box",
                }}
                onKeyDown={(e) => e.key === "Enter" && handleVeto()}
                autoFocus
              />
            </div>
          )}

          {confirming === "auth" && (
            <div style={{
              marginTop: "8px", textAlign: "center",
              fontSize: "11px", color: "#C4940F",
              fontFamily: "JetBrains Mono, monospace",
            }}>
              click again to confirm
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function getTimeAgo(isoDate) {
  const diff = Date.now() - new Date(isoDate).getTime();
  const mins = Math.floor(diff / 60000);
  const hours = Math.floor(mins / 60);
  if (hours > 0) return `${hours}h ${mins % 60}m ago`;
  return `${mins}m ago`;
}

// ── Main Dashboard ──
export default function SentinelL2Dashboard() {
  const [theme, setTheme] = useState("noir");
  const [lang, setLang] = useState("EN");
  const [tab, setTab] = useState("pending");
  const [proposals, setProposals] = useState(MOCK_PROPOSALS);
  const [history, setHistory] = useState(MOCK_HISTORY);
  const [sentinelStatus, setSentinelStatus] = useState(MOCK_SENTINEL_STATUS);

  const t = TRANSLATIONS[lang];
  const isDark = theme === "noir";

  const handleAuthorize = useCallback((id) => {
    setProposals(prev => prev.map(p =>
      p.proposal_id === id
        ? { ...p, status: "AUTHORIZED", decided_by: "human_dragon",
            decided_at: new Date().toISOString(), receipt_id: `SEN-RECEIPT-${Date.now().toString(16).slice(-8)}` }
        : p
    ));
  }, []);

  const handleVeto = useCallback((id, reason) => {
    setProposals(prev => {
      const vetoed = prev.find(p => p.proposal_id === id);
      if (vetoed) {
        setHistory(h => [{ ...vetoed, status: "VETOED", decided_by: "human_dragon",
          decided_at: new Date().toISOString(), veto_reason: reason || "Human decision" }, ...h]);
      }
      return prev.filter(p => p.proposal_id !== id);
    });
  }, []);

  const pendingCount = proposals.filter(p => p.status === "PENDING").length;

  return (
    <div style={{
      minHeight: "100vh",
      background: isDark
        ? "linear-gradient(145deg, #0d0c0a 0%, #1a1814 50%, #0d0c0a 100%)"
        : "linear-gradient(145deg, #faf8f3 0%, #f5f0e8 50%, #faf8f3 100%)",
      color: isDark ? "#e0d9c8" : "#1a1a2e",
      fontFamily: "'Bricolage Grotesque', 'Outfit', sans-serif",
      padding: "24px",
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@400;600;700&family=Outfit:wght@300;400;500&family=JetBrains+Mono:wght@400;600;700&display=swap');
        @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.4; } }
        @keyframes slideIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
      `}</style>

      {/* Header */}
      <div style={{ maxWidth: "800px", margin: "0 auto" }}>
        {/* Controls */}
        <div style={{ display: "flex", justifyContent: "flex-end", gap: "8px", marginBottom: "20px" }}>
          {/* Theme toggle */}
          <button onClick={() => setTheme(theme === "noir" ? "klar" : "noir")} style={{
            padding: "4px 12px", borderRadius: "16px", cursor: "pointer",
            border: `1px solid ${isDark ? "#333" : "#ddd"}`, fontSize: "11px",
            fontFamily: "JetBrains Mono, monospace",
            background: isDark ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.05)",
            color: isDark ? "#8a8070" : "#666",
          }}>
            {isDark ? "◐ Klar" : "◑ Noir"}
          </button>
          {/* Language */}
          {["DE", "EN", "PT"].map(l => (
            <button key={l} onClick={() => setLang(l)} style={{
              padding: "4px 10px", borderRadius: "16px", cursor: "pointer",
              border: `1px solid ${lang === l ? "#C4940F" : isDark ? "#333" : "#ddd"}`,
              fontSize: "11px", fontFamily: "JetBrains Mono, monospace",
              background: lang === l ? "rgba(196,148,15,0.15)" : "transparent",
              color: lang === l ? "#C4940F" : isDark ? "#666" : "#999",
            }}>
              {l}
            </button>
          ))}
        </div>

        {/* Title + Pulse */}
        <div style={{ display: "flex", alignItems: "center", gap: "20px", marginBottom: "24px" }}>
          <SentinelPulse status={sentinelStatus.status} size={100} />
          <div>
            <h1 style={{
              margin: 0, fontSize: "28px", fontWeight: 700,
              color: isDark ? "#C4940F" : "#8B6914",
              fontFamily: "'Bricolage Grotesque', sans-serif",
            }}>
              {t.title}
            </h1>
            <p style={{
              margin: "4px 0 0", fontSize: "13px",
              color: isDark ? "#8a8070" : "#888",
              fontFamily: "'Outfit', sans-serif", fontWeight: 300,
            }}>
              {t.subtitle}
            </p>
            <div style={{
              marginTop: "8px", display: "flex", gap: "16px",
              fontSize: "11px", fontFamily: "JetBrains Mono, monospace",
              color: isDark ? "#666" : "#999",
            }}>
              <span>{t.cycles}: {sentinelStatus.total_checks}</span>
              <span>{t.healthy}: {sentinelStatus.summary.healthy}/{sentinelStatus.summary.total}</span>
              <span>{t.uptime}: {getTimeAgo(sentinelStatus.started_at).replace(" ago", "")}</span>
            </div>
          </div>
        </div>

        {/* I9 Golden Rule */}
        <div style={{
          padding: "10px 16px", borderRadius: "8px", marginBottom: "20px",
          border: `1px solid ${isDark ? "#C4940F20" : "#C4940F30"}`,
          background: isDark ? "rgba(196,148,15,0.05)" : "rgba(196,148,15,0.06)",
          textAlign: "center",
          fontSize: "11px", fontFamily: "JetBrains Mono, monospace",
          color: "#C4940F", letterSpacing: "0.5px",
        }}>
          {t.goldenRule}
        </div>

        {/* Service Grid */}
        <div style={{ marginBottom: "24px" }}>
          <h3 style={{
            fontSize: "14px", fontWeight: 600, marginBottom: "12px",
            color: isDark ? "#8a8070" : "#666",
            fontFamily: "'Outfit', sans-serif",
          }}>
            {t.systemStatus}
          </h3>
          <ServiceGrid services={sentinelStatus.services} t={t} theme={theme} />
        </div>

        {/* Tab Navigation */}
        <div style={{
          display: "flex", gap: "4px", marginBottom: "20px",
          borderBottom: `1px solid ${isDark ? "#222" : "#e0e0e0"}`,
          paddingBottom: "1px",
        }}>
          {[
            { key: "pending", label: t.pending, count: pendingCount },
            { key: "history", label: t.history, count: history.length },
          ].map(({ key, label, count }) => (
            <button key={key} onClick={() => setTab(key)} style={{
              padding: "8px 20px", cursor: "pointer",
              border: "none", borderBottom: `2px solid ${tab === key ? "#C4940F" : "transparent"}`,
              fontSize: "13px", fontWeight: tab === key ? 700 : 400,
              fontFamily: "'Bricolage Grotesque', sans-serif",
              background: "transparent",
              color: tab === key ? "#C4940F" : isDark ? "#666" : "#999",
              transition: "all 0.2s ease",
            }}>
              {label}
              {count > 0 && (
                <span style={{
                  marginLeft: "6px", padding: "1px 6px", borderRadius: "10px",
                  fontSize: "10px", fontFamily: "JetBrains Mono, monospace",
                  background: key === "pending" && count > 0 ? "rgba(196,148,15,0.2)" : isDark ? "#222" : "#eee",
                  color: key === "pending" && count > 0 ? "#C4940F" : isDark ? "#666" : "#999",
                }}>
                  {count}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Content */}
        <div style={{ animation: "slideIn 0.3s ease" }}>
          {tab === "pending" && (
            proposals.filter(p => p.status === "PENDING").length > 0
              ? proposals.filter(p => p.status === "PENDING").map(p => (
                  <ProposalCard key={p.proposal_id} proposal={p} t={t} theme={theme}
                    onAuthorize={handleAuthorize} onVeto={handleVeto} />
                ))
              : (
                <div style={{
                  textAlign: "center", padding: "60px 20px",
                  color: isDark ? "#444" : "#ccc",
                }}>
                  <div style={{ fontSize: "48px", marginBottom: "16px" }}>🛡️</div>
                  <div style={{
                    fontSize: "15px", fontWeight: 600, marginBottom: "6px",
                    color: isDark ? "#666" : "#999",
                  }}>
                    {t.noProposals}
                  </div>
                  <div style={{
                    fontSize: "12px", fontFamily: "JetBrains Mono, monospace",
                    color: isDark ? "#444" : "#bbb",
                  }}>
                    {t.allClear}
                  </div>
                </div>
              )
          )}

          {tab === "history" && (
            [...proposals.filter(p => p.status !== "PENDING"), ...history].map(p => (
              <ProposalCard key={p.proposal_id} proposal={p} t={t} theme={theme}
                onAuthorize={handleAuthorize} onVeto={handleVeto} />
            ))
          )}
        </div>

        {/* Footer */}
        <div style={{
          marginTop: "40px", padding: "16px", textAlign: "center",
          borderTop: `1px solid ${isDark ? "#1a1a1a" : "#e8e8e8"}`,
          fontSize: "10px", fontFamily: "JetBrains Mono, monospace",
          color: isDark ? "#333" : "#ccc", letterSpacing: "1px",
        }}>
          WINDI SENTINEL v1.0.0 · LEVEL 2 · HUMAN INTERVENTION PROTOCOL
          <br />
          KI verarbeitet · Mensch entscheidet · WINDI garantiert
        </div>
      </div>
    </div>
  );
}
