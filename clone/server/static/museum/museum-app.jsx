const { useState, useEffect, useCallback } = React;

// ═══════════════════════════════════════════════════════
// MUSEUM APP — Container das 5 Fases
// "Memorial do Futuro" · a4Desk BABEL · WINDI
//
// clone-a4Desk-WINDI
// A escrita humana, agora com espinha dorsal.
// ═══════════════════════════════════════════════════════

const PRINCIPLES = {
  pt: "IA processa · Humano decide · WINDI garante",
  de: "KI verarbeitet · Mensch entscheidet · WINDI garantiert",
  en: "AI processes · Human decides · WINDI guarantees",
};

const PHASE_NAMES = {
  pt: ["Hello World", "Museum da Origem", "Galeria Criptográfica", "Painel DNA", "Editor Soberano"],
  de: ["Hello World", "Museum des Ursprungs", "Kryptographische Galerie", "DNA-Panel", "Souveräner Editor"],
  en: ["Hello World", "Genesis Museum", "Cryptographic Gallery", "DNA Panel", "Sovereign Editor"],
};

// Phase indicator dots
function PhaseIndicator({ phase, lang }) {
  return (
    <div style={{
      position: "fixed", bottom: "20px", left: "50%",
      transform: "translateX(-50%)", zIndex: 50,
      display: "flex", flexDirection: "column", alignItems: "center",
      gap: "8px", padding: "12px 20px",
      background: "rgba(0,0,0,0.7)", borderRadius: "12px",
      border: "1px solid rgba(255,255,255,0.04)",
      backdropFilter: "blur(10px)",
    }}>
      <div style={{
        fontFamily: "'JetBrains Mono', monospace",
        fontSize: "0.55rem", color: "#D4AF37",
        letterSpacing: "0.1em", textTransform: "uppercase",
      }}>
        {PHASE_NAMES[lang]?.[phase - 1] || `Phase ${phase}`}
      </div>
      <div style={{ display: "flex", gap: "8px" }}>
        {[1, 2, 3, 4, 5].map(p => (
          <div key={p} style={{
            width: p === phase ? "24px" : "8px", height: "8px",
            borderRadius: "4px", transition: "all 0.4s ease",
            background: p === phase ? "#D4AF37"
              : p < phase ? "rgba(212,175,55,0.3)"
              : "rgba(255,255,255,0.08)",
          }} />
        ))}
      </div>
    </div>
  );
}

// Clone signature watermark
function CloneSignature() {
  return (
    <div style={{
      position: "fixed", top: "20px", left: "20px", zIndex: 50,
      opacity: 0.4, pointerEvents: "none",
    }}>
      <span style={{
        fontFamily: "'Playfair Display', serif",
        fontStyle: "italic", fontWeight: 400,
        fontSize: "0.7rem", color: "#D4AF37",
      }}>clone</span>
      <span style={{ color: "#7A7A7A", margin: "0 0.1em", fontSize: "0.7rem" }}>-</span>
      <span style={{
        fontFamily: "'Outfit', sans-serif",
        fontWeight: 300, fontSize: "0.7rem", color: "#888",
      }}>a4Desk</span>
      <span style={{ color: "#7A7A7A", margin: "0 0.1em", fontSize: "0.7rem" }}>-</span>
      <span style={{
        fontFamily: "'JetBrains Mono', monospace",
        fontWeight: 500, letterSpacing: "0.1em",
        fontSize: "0.65rem", color: "#AAA",
      }}>WINDI</span>
    </div>
  );
}

function MuseumApp() {
  const [phase, setPhase] = useState(1);
  const [lang, setLang] = useState("pt");
  const [transitioning, setTransitioning] = useState(false);
  const [showBridge, setShowBridge] = useState(false);
  const [ready, setReady] = useState(false);

  // Hide loading screen after components are ready
  useEffect(() => {
    const timer = setTimeout(() => {
      document.getElementById('loading')?.classList.add('hidden');
      setReady(true);
    }, 3000);
    return () => clearTimeout(timer);
  }, []);

  const nextPhase = useCallback(() => {
    if (phase >= 5) {
      // Last phase — redirect to main editor
      window.location.href = "/";
      return;
    }
    // Transition animation
    setTransitioning(true);
    setTimeout(() => {
      setShowBridge(true);
      setTimeout(() => {
        setPhase(prev => prev + 1);
        setShowBridge(false);
        setTransitioning(false);
      }, 1000);
    }, 600);
  }, [phase]);

  if (!ready) return null;

  return (
    <div style={{ minHeight: "100vh", background: "#050505" }}>
      {/* Clone watermark */}
      <CloneSignature />

      {/* Transition bridge */}
      {showBridge && (
        <div className="phase-bridge">
          <span>{PRINCIPLES[lang]}</span>
        </div>
      )}

      {/* Phase content */}
      <div className={`phase-container ${transitioning ? "phase-exit" : "phase-enter"}`}>
        {phase === 1 && typeof A4DeskHelloWorld !== 'undefined' &&
          React.createElement(A4DeskHelloWorld, {
            lang, setLang, onComplete: nextPhase
          })
        }
        {phase === 2 && typeof GenesisMuseum !== 'undefined' &&
          React.createElement(GenesisMuseum, {
            lang, setLang, onComplete: nextPhase
          })
        }
        {phase === 3 && typeof CryptographicGallery !== 'undefined' &&
          React.createElement(CryptographicGallery, {
            lang, setLang, onComplete: nextPhase
          })
        }
        {phase === 4 && typeof DNATransparencyPanel !== 'undefined' &&
          React.createElement(DNATransparencyPanel, {
            lang, setLang, onComplete: nextPhase
          })
        }
        {phase === 5 && typeof SovereignEditor !== 'undefined' &&
          React.createElement(SovereignEditor, {
            lang, setLang
          })
        }
      </div>

      {/* Phase indicator */}
      {!showBridge && <PhaseIndicator phase={phase} lang={lang} />}
    </div>
  );
}

// Mount the app with error handling
try {
  const root = ReactDOM.createRoot(document.getElementById('root'));
  root.render(React.createElement(MuseumApp));
  console.log("Museum of the Future initialized");
  console.log("clone-a4Desk-WINDI — A escrita humana, agora com espinha dorsal.");
} catch (e) {
  console.error("Museum mount error:", e);
  document.getElementById('loading-text').textContent = 'Mount Error: ' + e.message;
  document.getElementById('loading').classList.add('hidden');
}
