import { useState, useEffect, useCallback } from "react";

// ═══════════════════════════════════════════════════════════════════════════════
// MUSEUM OF THE FUTURE — ORCHESTRATOR
// a4Desk BABEL · WINDI Publishing House
//
// 5 Portas Sequenciais:
//   Porta 1: Hello World        → Nascimento (Boot Constitucional)
//   Porta 2: Genesis Museum     → Origem (Timeline Sagrada)
//   Porta 3: Cryptographic Gallery → Anatomia (Pixel + SHA + Stegano)
//   Porta 4: DNA Transparency Panel → Aliança (Trindade + Consenso)
//   Porta 5: Sovereign Editor   → Soberania (3 Modos Cognitivos)
//
// Design: Noir theme + Gold accents + Trilingual (PT/DE/EN)
// ═══════════════════════════════════════════════════════════════════════════════

// Import all phase components
import HelloWorld from "./A4DeskHelloWorld_v3_i18n.jsx";
import GenesisMuseum from "./GenesisMuseum_v1.jsx";
import CryptographicGallery from "./CryptographicGallery_v1.jsx";
import DNATransparencyPanel from "./DNATransparencyPanel_v1.jsx";
import SovereignEditor from "./SovereignEditor_v1.jsx";

// ═══════════════════════════════════════════
// PHASE TRANSITION SCREEN
// ═══════════════════════════════════════════

function PhaseTransition({ principle, onComplete }) {
  useEffect(() => {
    const timer = setTimeout(onComplete, 1000);
    return () => clearTimeout(timer);
  }, [onComplete]);

  return (
    <div style={{
      position: "fixed", inset: 0, zIndex: 1000,
      background: "#050505",
      display: "flex", alignItems: "center", justifyContent: "center",
      animation: "fadeIn 0.5s ease",
    }}>
      <div style={{
        fontFamily: "'Bricolage Grotesque', serif",
        fontSize: "0.8rem", fontWeight: 300,
        color: "#444", letterSpacing: "0.15em",
        textTransform: "uppercase",
        animation: "pulseText 1s ease infinite",
      }}>
        {principle}
      </div>
      <style>{`
        @keyframes fadeIn { from{opacity:0} to{opacity:1} }
        @keyframes pulseText { 0%,100%{opacity:0.4} 50%{opacity:0.8} }
      `}</style>
    </div>
  );
}

// ═══════════════════════════════════════════
// ACCESSIBILITY PANEL (Global)
// ═══════════════════════════════════════════

function GlobalAccessibility({ config, setConfig, open, setOpen, lang }) {
  const jm = "'JetBrains Mono', monospace";
  const of_ = "'Outfit', sans-serif";

  const labels = {
    pt: { title: "Acessibilidade", fontSize: "Tamanho da letra", contrast: "Alto contraste", close: "Fechar" },
    de: { title: "Barrierefreiheit", fontSize: "Schriftgröße", contrast: "Hoher Kontrast", close: "Schließen" },
    en: { title: "Accessibility", fontSize: "Font size", contrast: "High contrast", close: "Close" },
  };
  const t = labels[lang] || labels.en;

  if (!open) return (
    <button
      onClick={() => setOpen(true)}
      aria-label={t.title}
      style={{
        position: "fixed", bottom: "20px", right: "20px", zIndex: 9999,
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
      position: "fixed", bottom: "20px", right: "20px", zIndex: 9999,
      width: "280px", padding: "20px",
      background: config.highContrast ? "#000" : "#111",
      border: `1px solid ${config.highContrast ? "#FFD700" : "rgba(212,175,55,0.2)"}`,
      borderRadius: "12px", boxShadow: "0 8px 40px rgba(0,0,0,0.5)",
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
        <span style={{ fontFamily: of_, fontSize: "0.85rem", fontWeight: 600, color: "#D4AF37" }}>
          {t.title}
        </span>
        <button onClick={() => setOpen(false)} style={{
          background: "none", border: "none", color: "#666", cursor: "pointer", fontSize: "1.1rem",
        }} aria-label={t.close}>✕</button>
      </div>

      {/* Font size */}
      <div style={{ marginBottom: "14px" }}>
        <label style={{ fontFamily: jm, fontSize: "0.6rem", color: "#888", display: "block", marginBottom: "6px" }}>
          {t.fontSize}: {config.fontSize}px
        </label>
        <input
          type="range" min="14" max="32" value={config.fontSize}
          onChange={e => setConfig(c => ({ ...c, fontSize: parseInt(e.target.value) }))}
          style={{ width: "100%", accentColor: "#D4AF37" }}
          aria-label={t.fontSize}
        />
      </div>

      {/* High contrast toggle */}
      <button
        onClick={() => setConfig(c => ({ ...c, highContrast: !c.highContrast }))}
        aria-pressed={config.highContrast}
        style={{
          width: "100%", padding: "10px 12px",
          background: config.highContrast ? "rgba(212,175,55,0.12)" : "rgba(255,255,255,0.03)",
          border: config.highContrast ? "1px solid rgba(212,175,55,0.3)" : "1px solid rgba(255,255,255,0.06)",
          borderRadius: "6px", cursor: "pointer", display: "flex", alignItems: "center", gap: "10px",
        }}
      >
        <span style={{ fontSize: "0.9rem" }}>◐</span>
        <span style={{ fontFamily: of_, fontSize: "0.75rem", color: config.highContrast ? "#D4AF37" : "#888" }}>
          {t.contrast}
        </span>
        <span style={{
          marginLeft: "auto", width: "32px", height: "18px", borderRadius: "9px",
          background: config.highContrast ? "#D4AF37" : "#333", position: "relative",
        }}>
          <span style={{
            position: "absolute", top: "2px",
            left: config.highContrast ? "16px" : "2px",
            width: "14px", height: "14px", borderRadius: "50%",
            background: config.highContrast ? "#0A0A0A" : "#666",
            transition: "left 0.2s",
          }} />
        </span>
      </button>
    </div>
  );
}

// ═══════════════════════════════════════════
// PROGRESS INDICATOR
// ═══════════════════════════════════════════

function ProgressIndicator({ phase, total }) {
  return (
    <div style={{
      position: "fixed", top: "20px", left: "50%", transform: "translateX(-50%)",
      zIndex: 9998, display: "flex", gap: "8px", alignItems: "center",
      padding: "8px 16px", background: "rgba(0,0,0,0.6)",
      borderRadius: "20px", backdropFilter: "blur(10px)",
    }}>
      {Array.from({ length: total }).map((_, i) => (
        <div key={i} style={{
          width: i + 1 === phase ? "24px" : "8px",
          height: "8px",
          borderRadius: "4px",
          background: i + 1 <= phase ? "#D4AF37" : "rgba(255,255,255,0.15)",
          transition: "all 0.4s ease",
        }} />
      ))}
    </div>
  );
}

// ═══════════════════════════════════════════
// MAIN: MUSEUM APP ORCHESTRATOR
// ═══════════════════════════════════════════

export default function MuseumApp() {
  const [phase, setPhase] = useState(1); // 1-5
  const [lang, setLang] = useState("pt");
  const [transitioning, setTransitioning] = useState(false);
  const [accessOpen, setAccessOpen] = useState(false);
  const [accessConfig, setAccessConfig] = useState({
    fontSize: 16,
    highContrast: false,
  });

  const principles = {
    pt: "IA processa · Humano decide · WINDI garante",
    de: "KI verarbeitet · Mensch entscheidet · WINDI garantiert",
    en: "AI processes · Human decides · WINDI guarantees",
  };

  const nextPhase = useCallback(() => {
    if (phase < 5) {
      setTransitioning(true);
    } else {
      // Phase 5 is the editor — redirect or stay
      window.location.href = "/editor";
    }
  }, [phase]);

  const handleTransitionComplete = useCallback(() => {
    setPhase(prev => prev + 1);
    setTransitioning(false);
  }, []);

  // Apply high contrast to body
  useEffect(() => {
    document.body.style.background = accessConfig.highContrast ? "#000" : "#050505";
  }, [accessConfig.highContrast]);

  return (
    <div style={{
      minHeight: "100vh",
      background: accessConfig.highContrast ? "#000" : "#050505",
      fontSize: `${accessConfig.fontSize}px`,
    }}>
      <link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@300;400;600;800&family=Outfit:wght@200;300;400;600&family=JetBrains+Mono:wght@300;400;500&display=swap" rel="stylesheet" />
      <style>{`
        @keyframes phaseExit { to { opacity: 0; transform: translateY(-20px); } }
        @keyframes phaseEnter { from { opacity: 0; transform: translateY(30px); } to { opacity: 1; transform: translateY(0); } }
        * { box-sizing: border-box; }
      `}</style>

      {/* Progress Indicator */}
      <ProgressIndicator phase={phase} total={5} />

      {/* Phase Transition Overlay */}
      {transitioning && (
        <PhaseTransition
          principle={principles[lang]}
          onComplete={handleTransitionComplete}
        />
      )}

      {/* Phase Components */}
      <div style={{
        animation: transitioning ? "phaseExit 0.5s ease forwards" : "phaseEnter 0.8s ease",
      }}>
        {phase === 1 && (
          <HelloWorld
            lang={lang}
            setLang={setLang}
            onComplete={nextPhase}
          />
        )}
        {phase === 2 && (
          <GenesisMuseum
            lang={lang}
            setLang={setLang}
            onComplete={nextPhase}
          />
        )}
        {phase === 3 && (
          <CryptographicGallery
            lang={lang}
            setLang={setLang}
            onComplete={nextPhase}
          />
        )}
        {phase === 4 && (
          <DNATransparencyPanel
            lang={lang}
            setLang={setLang}
            onComplete={nextPhase}
          />
        )}
        {phase === 5 && (
          <SovereignEditor
            lang={lang}
            setLang={setLang}
          />
        )}
      </div>

      {/* Global Accessibility Panel */}
      <GlobalAccessibility
        config={accessConfig}
        setConfig={setAccessConfig}
        open={accessOpen}
        setOpen={setAccessOpen}
        lang={lang}
      />
    </div>
  );
}

// ═══════════════════════════════════════════
// STANDALONE EXPORTS FOR INDIVIDUAL TESTING
// ═══════════════════════════════════════════

export { HelloWorld, GenesisMuseum, CryptographicGallery, DNATransparencyPanel, SovereignEditor };
