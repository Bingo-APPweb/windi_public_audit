import { useState, useEffect, useRef, useCallback } from "react";

// ═══════════════════════════════════════════════════════
// a4Desk BABEL — SOVEREIGN EDITOR
// Universal Adaptive Interface
//
// Design Principle: "If a person with cognitive disability
// can use it with dignity, EVERYONE can use it."
//
// Three Cognitive Modes:
//   EASY   → Maximum assistance, minimal choices, large UI
//   NORMAL → Balanced interface for daily professional use
//   EXPERT → Full power, keyboard shortcuts, compact UI
//
// Accessibility: WCAG 2.1 AA minimum
// ═══════════════════════════════════════════════════════

const i18n = {
  pt: {
    flag: "🇧🇷",
    welcome: "Seu espaço soberano",
    welcomeSub: "Escolha como você quer trabalhar. Pode mudar a qualquer momento.",
    modeEasy: "Simples",
    modeEasyDesc: "Letras grandes, poucos botões, máxima orientação",
    modeNormal: "Normal",
    modeNormalDesc: "Interface equilibrada para uso diário",
    modeExpert: "Avançado",
    modeExpertDesc: "Todos os recursos, atalhos de teclado",
    startWriting: "Começar a escrever",
    docTypes: { invoice: "Fatura", letter: "Carta", report: "Relatório", contract: "Contrato", free: "Texto livre" },
    docTypeQuestion: "O que você quer criar?",
    placeholder: "Comece a escrever aqui...",
    placeholderEasy: "Escreva aqui. O WINDI cuida da segurança para você.",
    seal: "Selar documento",
    save: "Salvar",
    export: "Exportar",
    agentFlow: "Tudo seguro",
    agentAttention: "Atenção necessária",
    agentPause: "Decisão obrigatória",
    sgeClean: "Documento limpo",
    sgeFlag: "Item detectado — sua decisão",
    accessLabel: "Acessibilidade",
    fontSizeLabel: "Tamanho da letra",
    contrastLabel: "Alto contraste",
    voiceLabel: "Comandos de voz",
    simplifyLabel: "Linguagem simples",
    readAloudLabel: "Ler em voz alta",
    principle: "IA processa · Humano decide · WINDI garante",
    cogModeLabel: "Modo cognitivo",
    approveBtn: "Aprovar",
    overrideBtn: "Rejeitar",
    deferBtn: "Adiar",
    reasonPlaceholder: "Motivo da decisão...",
    timerText: "Tempo para decidir",
    govScore: "Pontuação de governança",
    riskLevel: "Nível de risco",
  },
  de: {
    flag: "🇩🇪",
    welcome: "Ihr souveräner Raum",
    welcomeSub: "Wählen Sie, wie Sie arbeiten möchten. Jederzeit änderbar.",
    modeEasy: "Einfach",
    modeEasyDesc: "Große Schrift, wenige Buttons, maximale Führung",
    modeNormal: "Normal",
    modeNormalDesc: "Ausgewogene Oberfläche für den täglichen Gebrauch",
    modeExpert: "Erweitert",
    modeExpertDesc: "Alle Funktionen, Tastaturkürzel",
    startWriting: "Mit dem Schreiben beginnen",
    docTypes: { invoice: "Rechnung", letter: "Brief", report: "Bericht", contract: "Vertrag", free: "Freitext" },
    docTypeQuestion: "Was möchten Sie erstellen?",
    placeholder: "Beginnen Sie hier zu schreiben...",
    placeholderEasy: "Schreiben Sie hier. WINDI kümmert sich um die Sicherheit.",
    seal: "Dokument versiegeln",
    save: "Speichern",
    export: "Exportieren",
    agentFlow: "Alles sicher",
    agentAttention: "Aufmerksamkeit erforderlich",
    agentPause: "Entscheidung erforderlich",
    sgeClean: "Dokument sauber",
    sgeFlag: "Element erkannt — Ihre Entscheidung",
    accessLabel: "Barrierefreiheit",
    fontSizeLabel: "Schriftgröße",
    contrastLabel: "Hoher Kontrast",
    voiceLabel: "Sprachbefehle",
    simplifyLabel: "Einfache Sprache",
    readAloudLabel: "Vorlesen",
    principle: "KI verarbeitet · Mensch entscheidet · WINDI garantiert",
    cogModeLabel: "Kognitiver Modus",
    approveBtn: "Genehmigen",
    overrideBtn: "Ablehnen",
    deferBtn: "Verschieben",
    reasonPlaceholder: "Entscheidungsgrund...",
    timerText: "Zeit für Entscheidung",
    govScore: "Governance-Bewertung",
    riskLevel: "Risikostufe",
  },
  en: {
    flag: "🇬🇧",
    welcome: "Your sovereign space",
    welcomeSub: "Choose how you want to work. Change anytime.",
    modeEasy: "Simple",
    modeEasyDesc: "Large text, few buttons, maximum guidance",
    modeNormal: "Normal",
    modeNormalDesc: "Balanced interface for daily use",
    modeExpert: "Advanced",
    modeExpertDesc: "All features, keyboard shortcuts",
    startWriting: "Start writing",
    docTypes: { invoice: "Invoice", letter: "Letter", report: "Report", contract: "Contract", free: "Free text" },
    docTypeQuestion: "What do you want to create?",
    placeholder: "Start writing here...",
    placeholderEasy: "Write here. WINDI handles security for you.",
    seal: "Seal document",
    save: "Save",
    export: "Export",
    agentFlow: "All secure",
    agentAttention: "Attention needed",
    agentPause: "Decision required",
    sgeClean: "Document clean",
    sgeFlag: "Item detected — your decision",
    accessLabel: "Accessibility",
    fontSizeLabel: "Font size",
    contrastLabel: "High contrast",
    voiceLabel: "Voice commands",
    simplifyLabel: "Simple language",
    readAloudLabel: "Read aloud",
    principle: "AI processes · Human decides · WINDI guarantees",
    cogModeLabel: "Cognitive mode",
    approveBtn: "Approve",
    overrideBtn: "Override",
    deferBtn: "Defer",
    reasonPlaceholder: "Reason for decision...",
    timerText: "Time to decide",
    govScore: "Governance score",
    riskLevel: "Risk level",
  },
};

// ═══════════════════════════════════════════
// ACCESSIBILITY PANEL
// ═══════════════════════════════════════════

function AccessibilityPanel({ config, setConfig, t, open, setOpen }) {
  const jm = "'JetBrains Mono', monospace";
  const of_ = "'Outfit', sans-serif";

  if (!open) return (
    <button
      onClick={() => setOpen(true)}
      aria-label={t.accessLabel}
      style={{
        position: "fixed", bottom: "20px", right: "20px", zIndex: 100,
        width: "48px", height: "48px", borderRadius: "50%",
        background: config.highContrast ? "#FFD700" : "rgba(212,175,55,0.15)",
        border: "1px solid rgba(212,175,55,0.3)", cursor: "pointer",
        display: "flex", alignItems: "center", justifyContent: "center",
        fontSize: "1.3rem", transition: "all 0.3s ease",
        boxShadow: "0 4px 20px rgba(0,0,0,0.3)",
      }}
    >
      ♿
    </button>
  );

  return (
    <div style={{
      position: "fixed", bottom: "20px", right: "20px", zIndex: 100,
      width: "300px", padding: "24px",
      background: config.highContrast ? "#000" : "#111",
      border: `1px solid ${config.highContrast ? "#FFD700" : "rgba(212,175,55,0.2)"}`,
      borderRadius: "12px", boxShadow: "0 8px 40px rgba(0,0,0,0.5)",
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
        <span style={{ fontFamily: of_, fontSize: "0.9rem", fontWeight: 600, color: "#D4AF37" }}>
          {t.accessLabel}
        </span>
        <button onClick={() => setOpen(false)} style={{
          background: "none", border: "none", color: "#666", cursor: "pointer", fontSize: "1.2rem",
        }}>✕</button>
      </div>

      {/* Font size */}
      <div style={{ marginBottom: "16px" }}>
        <label style={{ fontFamily: jm, fontSize: "0.65rem", color: "#888", display: "block", marginBottom: "8px" }}>
          {t.fontSizeLabel}: {config.fontSize}px
        </label>
        <input
          type="range" min="14" max="32" value={config.fontSize}
          onChange={e => setConfig(c => ({ ...c, fontSize: parseInt(e.target.value) }))}
          style={{ width: "100%", accentColor: "#D4AF37" }}
          aria-label={t.fontSizeLabel}
        />
        <div style={{ display: "flex", justifyContent: "space-between", fontFamily: jm, fontSize: "0.55rem", color: "#555" }}>
          <span>A</span><span style={{ fontSize: "0.8rem" }}>A</span>
        </div>
      </div>

      {/* Toggles */}
      {[
        { key: "highContrast", label: t.contrastLabel, icon: "◐" },
        { key: "simpleLanguage", label: t.simplifyLabel, icon: "📖" },
        { key: "readAloud", label: t.readAloudLabel, icon: "🔊" },
      ].map(toggle => (
        <button
          key={toggle.key}
          onClick={() => setConfig(c => ({ ...c, [toggle.key]: !c[toggle.key] }))}
          aria-pressed={config[toggle.key]}
          style={{
            width: "100%", padding: "10px 14px", marginBottom: "8px",
            background: config[toggle.key] ? "rgba(212,175,55,0.12)" : "rgba(255,255,255,0.03)",
            border: config[toggle.key] ? "1px solid rgba(212,175,55,0.3)" : "1px solid rgba(255,255,255,0.06)",
            borderRadius: "6px", cursor: "pointer", display: "flex", alignItems: "center", gap: "10px",
            transition: "all 0.2s ease",
          }}
        >
          <span style={{ fontSize: "1rem" }}>{toggle.icon}</span>
          <span style={{ fontFamily: of_, fontSize: "0.8rem", color: config[toggle.key] ? "#D4AF37" : "#888" }}>
            {toggle.label}
          </span>
          <span style={{
            marginLeft: "auto", width: "36px", height: "20px", borderRadius: "10px",
            background: config[toggle.key] ? "#D4AF37" : "#333", position: "relative",
            transition: "background 0.2s",
          }}>
            <span style={{
              position: "absolute", top: "2px",
              left: config[toggle.key] ? "18px" : "2px",
              width: "16px", height: "16px", borderRadius: "50%",
              background: config[toggle.key] ? "#0A0A0A" : "#666",
              transition: "left 0.2s",
            }} />
          </span>
        </button>
      ))}
    </div>
  );
}

// ═══════════════════════════════════════════
// WINDI AGENT (FLOW / ATTENTION / PAUSE)
// ═══════════════════════════════════════════

function WindiAgent({ state, t, mode, config, onDecision }) {
  const of_ = "'Outfit', sans-serif";
  const jm = "'JetBrains Mono', monospace";
  const [timer, setTimer] = useState(30);
  const [reason, setReason] = useState("");

  useEffect(() => {
    if (state !== "pause") return;
    setTimer(30);
    const iv = setInterval(() => setTimer(prev => Math.max(0, prev - 1)), 1000);
    return () => clearInterval(iv);
  }, [state]);

  const isEasy = mode === "easy";
  const sz = isEasy ? 1.15 : 1;

  // FLOW — minimal icon
  if (state === "flow") {
    return (
      <div
        role="status"
        aria-label={t.agentFlow}
        style={{
          position: "fixed", bottom: isEasy ? "80px" : "20px", left: "20px", zIndex: 90,
          display: "flex", alignItems: "center", gap: "8px",
          padding: `${8 * sz}px ${14 * sz}px`,
          background: config.highContrast ? "#001a00" : "rgba(16, 185, 129, 0.08)",
          border: "1px solid rgba(16, 185, 129, 0.2)",
          borderRadius: "20px", transition: "all 0.5s ease",
        }}
      >
        <div style={{
          width: `${8 * sz}px`, height: `${8 * sz}px`, borderRadius: "50%",
          background: "#10B981",
          boxShadow: "0 0 8px rgba(16, 185, 129, 0.4)",
        }} />
        <span style={{
          fontFamily: jm, fontSize: `${0.65 * sz}rem`, color: "#10B981",
        }}>{t.agentFlow}</span>
      </div>
    );
  }

  // ATTENTION — gentle notification
  if (state === "attention") {
    return (
      <div
        role="alert"
        style={{
          position: "fixed", bottom: isEasy ? "80px" : "20px", left: "20px", zIndex: 90,
          maxWidth: isEasy ? "90vw" : "380px",
          padding: `${16 * sz}px ${20 * sz}px`,
          background: config.highContrast ? "#1a1a00" : "rgba(245, 158, 11, 0.06)",
          border: "1px solid rgba(245, 158, 11, 0.25)",
          borderRadius: "10px",
          animation: "slideUp 0.4s ease",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "10px" }}>
          <span style={{ fontSize: `${1.2 * sz}rem` }}>⚡</span>
          <span style={{
            fontFamily: of_, fontSize: `${0.85 * sz}rem`, fontWeight: 500, color: "#F59E0B",
          }}>{t.agentAttention}</span>
        </div>
        <div style={{
          fontFamily: of_, fontSize: `${0.78 * sz}rem`, fontWeight: 300, color: "#999", lineHeight: 1.6,
        }}>
          {t.sgeFlag}
        </div>
        <div style={{ display: "flex", gap: "8px", marginTop: "12px" }}>
          <button onClick={() => onDecision("approved")} style={{
            padding: `${8 * sz}px ${20 * sz}px`, background: "rgba(16,185,129,0.1)",
            border: "1px solid rgba(16,185,129,0.3)", borderRadius: "6px",
            color: "#10B981", fontFamily: jm, fontSize: `${0.7 * sz}rem`, cursor: "pointer",
          }}>{t.approveBtn}</button>
          <button onClick={() => onDecision("deferred")} style={{
            padding: `${8 * sz}px ${20 * sz}px`, background: "rgba(255,255,255,0.03)",
            border: "1px solid rgba(255,255,255,0.1)", borderRadius: "6px",
            color: "#888", fontFamily: jm, fontSize: `${0.7 * sz}rem`, cursor: "pointer",
          }}>{t.deferBtn}</button>
        </div>
      </div>
    );
  }

  // PAUSE — modal, mandatory, with timer
  if (state === "pause") {
    return (
      <div style={{
        position: "fixed", inset: 0, zIndex: 200,
        background: "rgba(0,0,0,0.8)", display: "flex", alignItems: "center", justifyContent: "center",
      }}>
        <div
          role="alertdialog"
          aria-modal="true"
          aria-label={t.agentPause}
          style={{
            width: isEasy ? "95vw" : "460px", maxWidth: "95vw",
            padding: `${32 * sz}px`,
            background: config.highContrast ? "#0a0000" : "#111",
            border: "1px solid rgba(239, 68, 68, 0.3)",
            borderRadius: "12px", textAlign: "center",
          }}
        >
          <div style={{ fontSize: `${2 * sz}rem`, marginBottom: "16px" }}>🛡️</div>
          <div style={{
            fontFamily: of_, fontSize: `${1.1 * sz}rem`, fontWeight: 600,
            color: "#EF4444", marginBottom: "8px",
          }}>{t.agentPause}</div>
          <div style={{
            fontFamily: of_, fontSize: `${0.85 * sz}rem`, fontWeight: 300,
            color: "#999", lineHeight: 1.6, marginBottom: "20px",
          }}>
            {t.sgeFlag} — R4/R5
          </div>

          {/* Timer */}
          <div style={{
            display: "flex", alignItems: "center", justifyContent: "center", gap: "8px", marginBottom: "20px",
          }}>
            <div style={{
              width: `${48 * sz}px`, height: `${48 * sz}px`, borderRadius: "50%",
              border: "2px solid rgba(239, 68, 68, 0.3)", display: "flex",
              alignItems: "center", justifyContent: "center",
              fontFamily: jm, fontSize: `${1 * sz}rem`, color: timer < 10 ? "#EF4444" : "#888",
            }}>{timer}</div>
            <span style={{ fontFamily: jm, fontSize: `${0.6 * sz}rem`, color: "#555" }}>{t.timerText}</span>
          </div>

          {/* Reason input */}
          <textarea
            value={reason}
            onChange={e => setReason(e.target.value)}
            placeholder={t.reasonPlaceholder}
            aria-label={t.reasonPlaceholder}
            style={{
              width: "100%", height: `${80 * sz}px`, padding: "12px",
              background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.1)",
              borderRadius: "6px", color: "#CCC", fontFamily: of_,
              fontSize: `${0.8 * sz}rem`, resize: "none", outline: "none",
              marginBottom: "16px",
            }}
          />

          {/* Decision buttons */}
          <div style={{ display: "flex", gap: "10px", justifyContent: "center", flexWrap: "wrap" }}>
            <button onClick={() => { if (reason.trim()) onDecision("approved"); }} style={{
              padding: `${12 * sz}px ${24 * sz}px`,
              background: reason.trim() ? "rgba(16,185,129,0.12)" : "rgba(255,255,255,0.02)",
              border: `1px solid ${reason.trim() ? "rgba(16,185,129,0.3)" : "rgba(255,255,255,0.05)"}`,
              borderRadius: "6px", color: reason.trim() ? "#10B981" : "#444",
              fontFamily: jm, fontSize: `${0.75 * sz}rem`, cursor: reason.trim() ? "pointer" : "not-allowed",
              transition: "all 0.2s",
            }}>{t.approveBtn}</button>
            <button onClick={() => { if (reason.trim()) onDecision("overridden"); }} style={{
              padding: `${12 * sz}px ${24 * sz}px`,
              background: reason.trim() ? "rgba(239,68,68,0.08)" : "rgba(255,255,255,0.02)",
              border: `1px solid ${reason.trim() ? "rgba(239,68,68,0.3)" : "rgba(255,255,255,0.05)"}`,
              borderRadius: "6px", color: reason.trim() ? "#EF4444" : "#444",
              fontFamily: jm, fontSize: `${0.75 * sz}rem`, cursor: reason.trim() ? "pointer" : "not-allowed",
            }}>{t.overrideBtn}</button>
            <button onClick={() => { if (reason.trim()) onDecision("deferred"); }} style={{
              padding: `${12 * sz}px ${24 * sz}px`,
              background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)",
              borderRadius: "6px", color: "#666",
              fontFamily: jm, fontSize: `${0.75 * sz}rem`, cursor: reason.trim() ? "pointer" : "not-allowed",
            }}>{t.deferBtn}</button>
          </div>

          {!reason.trim() && (
            <div style={{ fontFamily: jm, fontSize: `${0.55 * sz}rem`, color: "#555", marginTop: "12px" }}>
              * {t.reasonPlaceholder}
            </div>
          )}
        </div>
      </div>
    );
  }

  return null;
}

// ═══════════════════════════════════════════
// LANG SWITCH
// ═══════════════════════════════════════════

function LangSwitch({ lang, setLang }) {
  return (
    <div style={{ display: "flex", gap: "4px" }}>
      {["pt", "de", "en"].map(l => (
        <button key={l} onClick={() => setLang(l)} aria-label={`Switch to ${l}`} style={{
          background: lang === l ? "rgba(212,175,55,0.12)" : "transparent",
          border: lang === l ? "1px solid rgba(212,175,55,0.3)" : "1px solid transparent",
          borderRadius: "4px", padding: "4px 10px", cursor: "pointer",
          display: "flex", alignItems: "center", gap: "4px",
        }}>
          <span style={{ fontSize: "0.8rem" }}>{i18n[l].flag}</span>
          <span style={{
            fontFamily: "'JetBrains Mono', monospace", fontSize: "0.6rem",
            color: lang === l ? "#D4AF37" : "#555",
          }}>{l.toUpperCase()}</span>
        </button>
      ))}
    </div>
  );
}

// ═══════════════════════════════════════════
// MAIN: SOVEREIGN EDITOR
// ═══════════════════════════════════════════

export default function SovereignEditor({ lang: externalLang, setLang: externalSetLang }) {
  const [internalLang, setInternalLang] = useState("pt");
  const lang = externalLang || internalLang;
  const setLang = externalSetLang || setInternalLang;

  const [mode, setMode] = useState(null); // null = choosing, easy/normal/expert
  const [docType, setDocType] = useState(null);
  const [content, setContent] = useState("");
  const [agentState, setAgentState] = useState("flow");
  const [accessOpen, setAccessOpen] = useState(false);
  const [accessConfig, setAccessConfig] = useState({
    fontSize: 16, highContrast: false, simpleLanguage: false, readAloud: false,
  });
  const editorRef = useRef(null);
  const t = i18n[lang];

  const jm = "'JetBrains Mono', monospace";
  const bg = "'Bricolage Grotesque', serif";
  const of_ = "'Outfit', sans-serif";

  const hc = accessConfig.highContrast;
  const isEasy = mode === "easy";
  const sz = isEasy ? 1.2 : 1;

  // Simulate SGE scanning
  useEffect(() => {
    if (content.length > 100 && content.length < 105) {
      setAgentState("attention");
    }
    if (content.length > 250 && content.length < 255) {
      setAgentState("pause");
    }
  }, [content]);

  const handleDecision = (decision) => {
    setAgentState("flow");
  };

  // ═══ MODE SELECTION ═══
  if (!mode) {
    return (
      <div style={{
        minHeight: "100vh",
        background: hc ? "#000" : "#0A0A0A",
        display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
        fontFamily: of_, padding: "24px",
      }}>
        <link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@300;400;600;800&family=Outfit:wght@200;300;400;600&family=JetBrains+Mono:wght@300;400;500&display=swap" rel="stylesheet" />
        <style>{`
          @keyframes fadeInUp { from{opacity:0;transform:translateY(30px)} to{opacity:1;transform:translateY(0)} }
          @keyframes slideUp { from{opacity:0;transform:translateY(20px)} to{opacity:1;transform:translateY(0)} }
          * { box-sizing:border-box; margin:0; padding:0 }
        `}</style>

        <div style={{ textAlign: "center", maxWidth: "600px", animation: "fadeInUp 1s ease" }}>
          <div style={{
            fontFamily: bg, fontSize: "1.8rem", fontWeight: 800,
            background: "linear-gradient(135deg, #D4AF37, #F5E6A3, #D4AF37)",
            WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
            marginBottom: "8px",
          }}>a4Desk BABEL</div>
          <div style={{
            fontFamily: of_, fontSize: "1.1rem", fontWeight: 300, color: "#888", marginBottom: "4px",
          }}>{t.welcome}</div>
          <div style={{
            fontFamily: of_, fontSize: "0.8rem", fontWeight: 200, color: "#555", marginBottom: "48px",
          }}>{t.welcomeSub}</div>

          {/* Mode cards */}
          <div style={{
            display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
            gap: "16px", marginBottom: "32px",
          }}>
            {[
              { id: "easy", icon: "🌿", label: t.modeEasy, desc: t.modeEasyDesc, color: "#10B981" },
              { id: "normal", icon: "⚖️", label: t.modeNormal, desc: t.modeNormalDesc, color: "#D4AF37" },
              { id: "expert", icon: "⚡", label: t.modeExpert, desc: t.modeExpertDesc, color: "#8B5CF6" },
            ].map(m => (
              <button
                key={m.id}
                onClick={() => setMode(m.id)}
                aria-label={`${m.label}: ${m.desc}`}
                style={{
                  padding: "28px 20px", background: "rgba(255,255,255,0.02)",
                  border: "1px solid rgba(255,255,255,0.06)", borderRadius: "12px",
                  cursor: "pointer", textAlign: "center", transition: "all 0.3s ease",
                }}
                onMouseEnter={e => {
                  e.currentTarget.style.background = `${m.color}10`;
                  e.currentTarget.style.borderColor = `${m.color}40`;
                  e.currentTarget.style.transform = "translateY(-4px)";
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.background = "rgba(255,255,255,0.02)";
                  e.currentTarget.style.borderColor = "rgba(255,255,255,0.06)";
                  e.currentTarget.style.transform = "translateY(0)";
                }}
              >
                <div style={{ fontSize: "2rem", marginBottom: "12px" }}>{m.icon}</div>
                <div style={{ fontFamily: of_, fontSize: "1rem", fontWeight: 500, color: "#CCC", marginBottom: "6px" }}>
                  {m.label}
                </div>
                <div style={{ fontFamily: of_, fontSize: "0.72rem", fontWeight: 300, color: "#666", lineHeight: 1.5 }}>
                  {m.desc}
                </div>
              </button>
            ))}
          </div>

          <LangSwitch lang={lang} setLang={setLang} />
        </div>

        <AccessibilityPanel config={accessConfig} setConfig={setAccessConfig} t={t} open={accessOpen} setOpen={setAccessOpen} />
      </div>
    );
  }

  // ═══ DOC TYPE SELECTION (Easy mode gets this, others can skip) ═══
  if (!docType && isEasy) {
    const types = Object.entries(t.docTypes);
    return (
      <div style={{
        minHeight: "100vh", background: hc ? "#000" : "#0A0A0A",
        display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
        fontFamily: of_, padding: "24px",
      }}>
        <link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@300;400;600;800&family=Outfit:wght@200;300;400;600&family=JetBrains+Mono:wght@300;400;500&display=swap" rel="stylesheet" />
        <style>{`@keyframes fadeInUp { from{opacity:0;transform:translateY(30px)} to{opacity:1;transform:translateY(0)} } * { box-sizing:border-box; margin:0; padding:0 }`}</style>

        <div style={{ textAlign: "center", maxWidth: "500px", animation: "fadeInUp 0.8s ease" }}>
          <div style={{ fontFamily: of_, fontSize: "1.4rem", fontWeight: 300, color: "#AAA", marginBottom: "32px" }}>
            {t.docTypeQuestion}
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
            {types.map(([key, label]) => (
              <button key={key} onClick={() => setDocType(key)} style={{
                padding: "24px", background: "rgba(255,255,255,0.02)",
                border: "1px solid rgba(255,255,255,0.06)", borderRadius: "12px",
                cursor: "pointer", fontFamily: of_, fontSize: "1.1rem",
                fontWeight: 400, color: "#CCC", transition: "all 0.2s",
              }}
                onMouseEnter={e => { e.target.style.borderColor = "rgba(212,175,55,0.3)"; e.target.style.background = "rgba(212,175,55,0.05)"; }}
                onMouseLeave={e => { e.target.style.borderColor = "rgba(255,255,255,0.06)"; e.target.style.background = "rgba(255,255,255,0.02)"; }}
              >{label}</button>
            ))}
          </div>
          <button onClick={() => setMode(null)} style={{
            marginTop: "24px", background: "none", border: "none",
            color: "#555", fontFamily: jm, fontSize: "0.65rem", cursor: "pointer",
          }}>← {t.cogModeLabel}</button>
        </div>
        <AccessibilityPanel config={accessConfig} setConfig={setAccessConfig} t={t} open={accessOpen} setOpen={setAccessOpen} />
      </div>
    );
  }

  // ═══ EDITOR ═══
  if (!docType && !isEasy) setDocType("free");

  return (
    <div style={{
      minHeight: "100vh", background: hc ? "#000" : "#0A0A0A",
      fontFamily: of_, display: "flex", flexDirection: "column",
    }}>
      <link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@300;400;600;800&family=Outfit:wght@200;300;400;600&family=JetBrains+Mono:wght@300;400;500&display=swap" rel="stylesheet" />
      <style>{`
        @keyframes fadeInUp { from{opacity:0;transform:translateY(30px)} to{opacity:1;transform:translateY(0)} }
        @keyframes slideUp { from{opacity:0;transform:translateY(20px)} to{opacity:1;transform:translateY(0)} }
        @keyframes pulse { 0%,100%{opacity:0.6} 50%{opacity:1} }
        * { box-sizing:border-box; margin:0; padding:0 }
        textarea:focus { outline: 2px solid rgba(212,175,55,0.3); outline-offset: 2px; }
      `}</style>

      {/* Top bar */}
      <header style={{
        display: "flex", alignItems: "center", justifyContent: "space-between",
        padding: `${12 * sz}px ${20 * sz}px`,
        background: hc ? "#000" : "rgba(255,255,255,0.02)",
        borderBottom: `1px solid ${hc ? "#FFD700" : "rgba(255,255,255,0.04)"}`,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <span style={{
            fontFamily: bg, fontSize: `${1.1 * sz}rem`, fontWeight: 800,
            color: "#D4AF37",
          }}>a4</span>
          {mode !== "easy" && (
            <span style={{ fontFamily: jm, fontSize: "0.55rem", color: "#333" }}>
              {(docType || "free").toUpperCase()} · {mode.toUpperCase()}
            </span>
          )}
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          {/* SGE indicator */}
          <div style={{
            display: "flex", alignItems: "center", gap: "6px",
            padding: "4px 10px", borderRadius: "4px",
            background: agentState === "flow" ? "rgba(16,185,129,0.06)" : "rgba(245,158,11,0.06)",
          }}>
            <div style={{
              width: "6px", height: "6px", borderRadius: "50%",
              background: agentState === "flow" ? "#10B981" : "#F59E0B",
              animation: agentState !== "flow" ? "pulse 1.5s ease infinite" : "none",
            }} />
            <span style={{ fontFamily: jm, fontSize: `${0.55 * sz}rem`, color: agentState === "flow" ? "#10B981" : "#F59E0B" }}>
              SGE
            </span>
          </div>

          <LangSwitch lang={lang} setLang={setLang} />

          {/* Mode switch (small) */}
          <button onClick={() => { setMode(null); setDocType(null); }} style={{
            background: "none", border: "1px solid rgba(255,255,255,0.06)",
            borderRadius: "4px", padding: "4px 8px", cursor: "pointer",
            fontFamily: jm, fontSize: "0.55rem", color: "#555",
          }}>
            {mode === "easy" ? "🌿" : mode === "expert" ? "⚡" : "⚖️"}
          </button>
        </div>
      </header>

      {/* Editor area */}
      <main style={{ flex: 1, display: "flex", justifyContent: "center", padding: `${24 * sz}px` }}>
        <div style={{
          width: "100%", maxWidth: isEasy ? "700px" : mode === "expert" ? "900px" : "750px",
          animation: "fadeInUp 0.6s ease",
        }}>
          {/* Toolbar */}
          {mode !== "easy" && (
            <div style={{
              display: "flex", gap: "4px", marginBottom: "12px", flexWrap: "wrap",
              padding: "8px", background: "rgba(255,255,255,0.02)", borderRadius: "6px",
            }}>
              {["B", "I", "U", "H1", "H2", "⫶", "—", "🔗"].map((btn, i) => (
                <button key={i} aria-label={btn} style={{
                  width: "32px", height: "32px", background: "transparent",
                  border: "1px solid rgba(255,255,255,0.06)", borderRadius: "4px",
                  color: "#888", fontFamily: btn.length <= 2 ? of_ : "inherit",
                  fontSize: "0.75rem", fontWeight: btn === "B" ? 700 : 400,
                  fontStyle: btn === "I" ? "italic" : "normal",
                  textDecoration: btn === "U" ? "underline" : "none",
                  cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center",
                }}>{btn}</button>
              ))}
              {mode === "expert" && (
                <>
                  <div style={{ width: "1px", height: "32px", background: "rgba(255,255,255,0.06)", margin: "0 4px" }} />
                  {["📊", "📎", "🏛️"].map((btn, i) => (
                    <button key={`x${i}`} aria-label={btn} style={{
                      width: "32px", height: "32px", background: "transparent",
                      border: "1px solid rgba(255,255,255,0.06)", borderRadius: "4px",
                      cursor: "pointer", fontSize: "0.85rem",
                      display: "flex", alignItems: "center", justifyContent: "center",
                    }}>{btn}</button>
                  ))}
                </>
              )}
            </div>
          )}

          {/* Text area */}
          <textarea
            ref={editorRef}
            value={content}
            onChange={e => setContent(e.target.value)}
            placeholder={isEasy ? t.placeholderEasy : t.placeholder}
            aria-label="Document editor"
            style={{
              width: "100%",
              minHeight: isEasy ? "50vh" : "60vh",
              padding: `${24 * sz}px`,
              background: hc ? "#0a0a0a" : "rgba(255,255,255,0.02)",
              border: `1px solid ${hc ? "#FFD700" : "rgba(255,255,255,0.06)"}`,
              borderRadius: "8px",
              color: hc ? "#FFFFFF" : "#D0D0D0",
              fontFamily: of_,
              fontSize: `${accessConfig.fontSize}px`,
              lineHeight: 1.8,
              resize: "vertical",
              caretColor: "#D4AF37",
            }}
          />

          {/* Bottom actions */}
          <div style={{
            display: "flex", justifyContent: isEasy ? "center" : "space-between",
            alignItems: "center", marginTop: "16px", gap: "12px", flexWrap: "wrap",
          }}>
            {!isEasy && (
              <div style={{ fontFamily: jm, fontSize: "0.55rem", color: "#333" }}>
                {content.length} chars · {t.govScore}: {content.length > 0 ? "92/100" : "—"} · {t.riskLevel}: R1
              </div>
            )}

            <div style={{ display: "flex", gap: "8px" }}>
              {!isEasy && (
                <>
                  <button style={{
                    padding: `${10 * sz}px ${20 * sz}px`, background: "transparent",
                    border: "1px solid rgba(255,255,255,0.08)", borderRadius: "6px",
                    color: "#888", fontFamily: jm, fontSize: `${0.7 * sz}rem`, cursor: "pointer",
                  }}>{t.save}</button>
                  <button style={{
                    padding: `${10 * sz}px ${20 * sz}px`, background: "transparent",
                    border: "1px solid rgba(255,255,255,0.08)", borderRadius: "6px",
                    color: "#888", fontFamily: jm, fontSize: `${0.7 * sz}rem`, cursor: "pointer",
                  }}>{t.export}</button>
                </>
              )}
              <button style={{
                padding: `${12 * sz}px ${isEasy ? 40 : 24}px`,
                background: content.length > 0 ? "rgba(212,175,55,0.08)" : "transparent",
                border: `1px solid ${content.length > 0 ? "#D4AF37" : "rgba(255,255,255,0.08)"}`,
                borderRadius: "6px", color: content.length > 0 ? "#D4AF37" : "#555",
                fontFamily: jm, fontSize: `${0.8 * sz}rem`,
                cursor: content.length > 0 ? "pointer" : "default",
                transition: "all 0.3s",
              }}>
                🛡️ {t.seal}
              </button>
            </div>
          </div>
        </div>
      </main>

      {/* WINDI Agent */}
      <WindiAgent state={agentState} t={t} mode={mode} config={accessConfig} onDecision={handleDecision} />

      {/* Accessibility */}
      <AccessibilityPanel config={accessConfig} setConfig={setAccessConfig} t={t} open={accessOpen} setOpen={setAccessOpen} />
    </div>
  );
}
