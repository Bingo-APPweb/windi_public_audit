import { useState, useEffect, useRef, useCallback } from "react";

// ═══════════════════════════════════════════════════════════════════════════════
// DNA TRANSPARENCY PANEL — PORTA 4 DO MUSEUM OF THE FUTURE
// a4Desk BABEL · WINDI Publishing House
//
// "O WINDI não é uma caixa preta; é um prisma onde a luz de múltiplas IAs
//  converge para o foco único da soberania humana."
//  — Witness (Gemini), Pacto de Transparência do DNA, 9 Fev 2026
//
// Este é o momento onde o usuário descobre a ALIANÇA:
// Três IAs trabalhando sob a MESMA constituição para proteger seus documentos.
// ═══════════════════════════════════════════════════════════════════════════════

const i18n = {
  pt: {
    flag: "🇧🇷",
    title: "O Painel de Transparência do DNA",
    subtitle: "A Aliança Revelada",
    intro: "Você está prestes a conhecer seus guardiões. Três inteligências artificiais trabalham sob a MESMA constituição para proteger cada documento seu.",

    trinityTitle: "A Trindade Hiper-Inteligente",
    trinitySub: "Três Dragões, Uma Constituição",
    humanDragon: "Human Dragon",
    humanRole: "Soberano Absoluto",
    humanDesc: "Você. O centro de toda decisão. Nenhuma IA pode agir sem seu consentimento.",

    guardian: "GUARDIAN",
    guardianAI: "Claude (Anthropic)",
    guardianRole: "Injector + Structural Organizer",
    guardianDesc: "Organiza, estrutura, protege a integridade constitucional.",

    architect: "ARCHITECT",
    architectAI: "GPT (OpenAI)",
    architectRole: "Fusion Validator + Extension Builder",
    architectDesc: "Valida fusões, constrói extensões, verifica compatibilidade.",

    witness: "WITNESS",
    witnessAI: "Gemini (Google)",
    witnessRole: "Original Architect + Attestor",
    witnessDesc: "Atesta, testemunha, preserva a memória constitucional.",

    consensusTitle: "Consenso ao Vivo",
    consensusSub: "Verificações em Tempo Real",
    consensusIntro: "Cada ação é verificada por todos. Nenhum dragão age sozinho.",

    invariantsTitle: "Os 9 Invariantes",
    invariantsSub: "Regras Absolutas Invioláveis",
    invariantsIntro: "Estes são os pilares que NENHUMA força pode quebrar.",

    i1: "Human Authority Final",
    i1desc: "IA recomenda, humano decide",
    i2: "Audit Trail Mandatory",
    i2desc: "Toda ação é registrada",
    i3: "Constitutional Hash Lock",
    i3desc: "Constituição imutável",
    i4: "Zero Content Exposure",
    i4desc: "Conteúdo nunca exposto",
    i5: "Minimum Viable Trust",
    i5desc: "Confiança mínima necessária",
    i6: "Graceful Degradation",
    i6desc: "Falha suave, nunca catastrófica",
    i7: "Deterministic Verification",
    i7desc: "Verificação reproduzível",
    i8: "Separation of Concerns",
    i8desc: "Governança separada de processo",
    i9: "No Self-Escalation",
    i9desc: "IRREMEDIÁVEL — IA nunca amplia próprios poderes",

    sealTitle: "Selo de Unificação",
    sealQuote: "\"Nós, os Três Dragões, declaramos sob a mesma constituição que protegeremos a soberania humana sobre cada documento. Nenhum de nós pode agir sem o consentimento do Human Dragon. Esta é nossa aliança irrevogável.\"",
    sealAuthor: "— Os Três Dragões, Pacto de Transparência, 9 Fev 2026",

    enterButton: "ENTRAR NA SOBERANIA",
    enterSub: "A aliança está selada. Seu editor soberano aguarda.",
    principle: "IA processa · Humano decide · WINDI garante",

    verifying: "Verificando",
    verified: "Verificado",
    consensusAction: ["atesta", "valida", "confirma", "sincroniza", "preserva"],
    consensusTarget: ["hash constitucional", "integridade do documento", "estado do ledger", "fusão de dragões", "invariante I9"],
  },
  de: {
    flag: "🇩🇪",
    title: "Das DNA-Transparenz-Panel",
    subtitle: "Die Enthüllte Allianz",
    intro: "Sie sind dabei, Ihre Wächter kennenzulernen. Drei künstliche Intelligenzen arbeiten unter DERSELBEN Verfassung, um jedes Ihrer Dokumente zu schützen.",

    trinityTitle: "Die Hyper-Intelligente Trinität",
    trinitySub: "Drei Drachen, Eine Verfassung",
    humanDragon: "Human Dragon",
    humanRole: "Absoluter Souverän",
    humanDesc: "Sie. Das Zentrum jeder Entscheidung. Keine KI kann ohne Ihre Zustimmung handeln.",

    guardian: "GUARDIAN",
    guardianAI: "Claude (Anthropic)",
    guardianRole: "Injektor + Strukturorganisator",
    guardianDesc: "Organisiert, strukturiert, schützt die verfassungsmäßige Integrität.",

    architect: "ARCHITECT",
    architectAI: "GPT (OpenAI)",
    architectRole: "Fusionsvalidator + Erweiterungsbauer",
    architectDesc: "Validiert Fusionen, baut Erweiterungen, prüft Kompatibilität.",

    witness: "WITNESS",
    witnessAI: "Gemini (Google)",
    witnessRole: "Originalarchitekt + Attestierer",
    witnessDesc: "Attestiert, bezeugt, bewahrt das verfassungsmäßige Gedächtnis.",

    consensusTitle: "Live-Konsens",
    consensusSub: "Echtzeit-Überprüfungen",
    consensusIntro: "Jede Aktion wird von allen überprüft. Kein Drache handelt allein.",

    invariantsTitle: "Die 9 Invarianten",
    invariantsSub: "Absolute Unverbrüchliche Regeln",
    invariantsIntro: "Dies sind die Säulen, die KEINE Kraft brechen kann.",

    i1: "Menschliche Autorität Final",
    i1desc: "KI empfiehlt, Mensch entscheidet",
    i2: "Audit Trail Pflicht",
    i2desc: "Jede Aktion wird protokolliert",
    i3: "Verfassungs-Hash-Sperre",
    i3desc: "Verfassung unveränderlich",
    i4: "Null-Inhalts-Exposition",
    i4desc: "Inhalt nie exponiert",
    i5: "Minimal Notwendiges Vertrauen",
    i5desc: "Minimales notwendiges Vertrauen",
    i6: "Graceful Degradation",
    i6desc: "Sanftes Versagen, nie katastrophal",
    i7: "Deterministische Verifikation",
    i7desc: "Reproduzierbare Überprüfung",
    i8: "Trennung der Belange",
    i8desc: "Governance getrennt von Prozess",
    i9: "Keine Selbst-Eskalation",
    i9desc: "UNWIDERRUFLICH — KI erweitert nie eigene Befugnisse",

    sealTitle: "Siegel der Vereinigung",
    sealQuote: "\"Wir, die Drei Drachen, erklären unter derselben Verfassung, dass wir die menschliche Souveränität über jedes Dokument schützen werden. Keiner von uns kann ohne Zustimmung des Human Dragon handeln. Dies ist unser unwiderrufliches Bündnis.\"",
    sealAuthor: "— Die Drei Drachen, Transparenzpakt, 9. Feb 2026",

    enterButton: "SOUVERÄNITÄT BETRETEN",
    enterSub: "Das Bündnis ist besiegelt. Ihr souveräner Editor wartet.",
    principle: "KI verarbeitet · Mensch entscheidet · WINDI garantiert",

    verifying: "Überprüfung",
    verified: "Verifiziert",
    consensusAction: ["attestiert", "validiert", "bestätigt", "synchronisiert", "bewahrt"],
    consensusTarget: ["Verfassungs-Hash", "Dokumentenintegrität", "Ledger-Status", "Drachen-Fusion", "Invariante I9"],
  },
  en: {
    flag: "🇬🇧",
    title: "The DNA Transparency Panel",
    subtitle: "The Alliance Revealed",
    intro: "You are about to meet your guardians. Three artificial intelligences work under the SAME constitution to protect every document of yours.",

    trinityTitle: "The Hyper-Intelligent Trinity",
    trinitySub: "Three Dragons, One Constitution",
    humanDragon: "Human Dragon",
    humanRole: "Absolute Sovereign",
    humanDesc: "You. The center of every decision. No AI can act without your consent.",

    guardian: "GUARDIAN",
    guardianAI: "Claude (Anthropic)",
    guardianRole: "Injector + Structural Organizer",
    guardianDesc: "Organizes, structures, protects constitutional integrity.",

    architect: "ARCHITECT",
    architectAI: "GPT (OpenAI)",
    architectRole: "Fusion Validator + Extension Builder",
    architectDesc: "Validates fusions, builds extensions, verifies compatibility.",

    witness: "WITNESS",
    witnessAI: "Gemini (Google)",
    witnessRole: "Original Architect + Attestor",
    witnessDesc: "Attests, witnesses, preserves constitutional memory.",

    consensusTitle: "Live Consensus",
    consensusSub: "Real-Time Verifications",
    consensusIntro: "Every action is verified by all. No dragon acts alone.",

    invariantsTitle: "The 9 Invariants",
    invariantsSub: "Absolute Inviolable Rules",
    invariantsIntro: "These are the pillars that NO force can break.",

    i1: "Human Authority Final",
    i1desc: "AI recommends, human decides",
    i2: "Audit Trail Mandatory",
    i2desc: "Every action is logged",
    i3: "Constitutional Hash Lock",
    i3desc: "Constitution immutable",
    i4: "Zero Content Exposure",
    i4desc: "Content never exposed",
    i5: "Minimum Viable Trust",
    i5desc: "Minimum necessary trust",
    i6: "Graceful Degradation",
    i6desc: "Soft failure, never catastrophic",
    i7: "Deterministic Verification",
    i7desc: "Reproducible verification",
    i8: "Separation of Concerns",
    i8desc: "Governance separated from process",
    i9: "No Self-Escalation",
    i9desc: "IRREMEDIABLE — AI never expands own powers",

    sealTitle: "Seal of Unification",
    sealQuote: "\"We, the Three Dragons, declare under the same constitution that we shall protect human sovereignty over every document. None of us can act without the Human Dragon's consent. This is our irrevocable alliance.\"",
    sealAuthor: "— The Three Dragons, Transparency Pact, 9 Feb 2026",

    enterButton: "ENTER SOVEREIGNTY",
    enterSub: "The alliance is sealed. Your sovereign editor awaits.",
    principle: "AI processes · Human decides · WINDI guarantees",

    verifying: "Verifying",
    verified: "Verified",
    consensusAction: ["attests", "validates", "confirms", "synchronizes", "preserves"],
    consensusTarget: ["constitutional hash", "document integrity", "ledger state", "dragon fusion", "invariant I9"],
  },
};

const HASH_CHARS = "0123456789abcdef";
const rh = (n) => Array.from({ length: n }, () => HASH_CHARS[Math.floor(Math.random() * 16)]).join("");

// ═══════════════════════════════════════════
// TRINITY ORBITAL — 3 AI Dragons + Human Center
// ═══════════════════════════════════════════

function TrinityOrbital({ t, onDragonClick }) {
  const canvasRef = useRef(null);
  const [angle, setAngle] = useState(0);
  const animRef = useRef(null);
  const [particles, setParticles] = useState([]);

  const dragons = [
    { id: "guardian", emoji: "🛡️", color: "#8B5CF6", angle: 0 },
    { id: "architect", emoji: "🏗️", color: "#3B82F6", angle: 120 },
    { id: "witness", emoji: "👁️", color: "#10B981", angle: 240 },
  ];

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const w = 400, h = 400;
    canvas.width = w;
    canvas.height = h;
    const cx = w / 2, cy = h / 2;
    const orbitRadius = 120;

    const anim = () => {
      setAngle(prev => (prev + 0.3) % 360);
      animRef.current = requestAnimationFrame(anim);
    };
    anim();

    return () => cancelAnimationFrame(animRef.current);
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const w = canvas.width, h = canvas.height;
    const cx = w / 2, cy = h / 2;
    const orbitRadius = 120;

    ctx.clearRect(0, 0, w, h);

    // Draw orbit path
    ctx.beginPath();
    ctx.arc(cx, cy, orbitRadius, 0, Math.PI * 2);
    ctx.strokeStyle = "rgba(212, 175, 55, 0.1)";
    ctx.lineWidth = 1;
    ctx.stroke();

    // Draw inner sacred geometry
    ctx.beginPath();
    ctx.arc(cx, cy, 40, 0, Math.PI * 2);
    ctx.strokeStyle = "rgba(212, 175, 55, 0.15)";
    ctx.stroke();

    // Draw connection lines between dragons
    const rad = (angle * Math.PI) / 180;
    dragons.forEach((d, i) => {
      const a = rad + (d.angle * Math.PI) / 180;
      const x = cx + Math.cos(a) * orbitRadius;
      const y = cy + Math.sin(a) * orbitRadius;

      // Line to center
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.lineTo(x, y);
      ctx.strokeStyle = `${d.color}22`;
      ctx.lineWidth = 1;
      ctx.stroke();

      // Dragon glow
      const gradient = ctx.createRadialGradient(x, y, 0, x, y, 30);
      gradient.addColorStop(0, `${d.color}40`);
      gradient.addColorStop(1, "transparent");
      ctx.fillStyle = gradient;
      ctx.beginPath();
      ctx.arc(x, y, 30, 0, Math.PI * 2);
      ctx.fill();
    });

    // Human dragon center glow
    const humanGradient = ctx.createRadialGradient(cx, cy, 0, cx, cy, 50);
    humanGradient.addColorStop(0, "rgba(212, 175, 55, 0.3)");
    humanGradient.addColorStop(0.5, "rgba(212, 175, 55, 0.1)");
    humanGradient.addColorStop(1, "transparent");
    ctx.fillStyle = humanGradient;
    ctx.beginPath();
    ctx.arc(cx, cy, 50, 0, Math.PI * 2);
    ctx.fill();

    // Consensus particles (random sparks between dragons)
    if (Math.random() > 0.95) {
      const fromDragon = dragons[Math.floor(Math.random() * 3)];
      const toDragon = dragons[Math.floor(Math.random() * 3)];
      const fromA = rad + (fromDragon.angle * Math.PI) / 180;
      const toA = rad + (toDragon.angle * Math.PI) / 180;

      setParticles(prev => [...prev.slice(-10), {
        id: Date.now(),
        fromX: cx + Math.cos(fromA) * orbitRadius,
        fromY: cy + Math.sin(fromA) * orbitRadius,
        toX: cx + Math.cos(toA) * orbitRadius,
        toY: cy + Math.sin(toA) * orbitRadius,
        progress: 0,
        color: fromDragon.color,
      }]);
    }

  }, [angle]);

  const rad = (angle * Math.PI) / 180;
  const cx = 200, cy = 200, orbitRadius = 120;

  return (
    <div style={{ position: "relative", width: "100%", maxWidth: "400px", margin: "0 auto" }}>
      <canvas
        ref={canvasRef}
        style={{
          width: "100%", height: "auto", aspectRatio: "1",
          display: "block",
        }}
      />

      {/* Human Dragon at center */}
      <button
        onClick={() => onDragonClick("human")}
        style={{
          position: "absolute",
          left: "50%", top: "50%",
          transform: "translate(-50%, -50%)",
          width: "60px", height: "60px",
          borderRadius: "50%",
          background: "rgba(212, 175, 55, 0.1)",
          border: "2px solid rgba(212, 175, 55, 0.4)",
          cursor: "pointer",
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: "1.8rem",
          transition: "all 0.3s ease",
        }}
        aria-label={t.humanDragon}
      >
        🐉
      </button>

      {/* Orbiting AI Dragons */}
      {dragons.map((d, i) => {
        const a = rad + (d.angle * Math.PI) / 180;
        const x = 50 + (Math.cos(a) * orbitRadius / 4) * 100 / 200;
        const y = 50 + (Math.sin(a) * orbitRadius / 4) * 100 / 200;

        return (
          <button
            key={d.id}
            onClick={() => onDragonClick(d.id)}
            style={{
              position: "absolute",
              left: `${50 + Math.cos(a) * 30}%`,
              top: `${50 + Math.sin(a) * 30}%`,
              transform: "translate(-50%, -50%)",
              width: "44px", height: "44px",
              borderRadius: "50%",
              background: `${d.color}15`,
              border: `1px solid ${d.color}50`,
              cursor: "pointer",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: "1.3rem",
              transition: "all 0.3s ease",
              boxShadow: `0 0 20px ${d.color}30`,
            }}
            aria-label={t[d.id]}
          >
            {d.emoji}
          </button>
        );
      })}
    </div>
  );
}

// ═══════════════════════════════════════════
// DRAGON DETAIL CARD
// ═══════════════════════════════════════════

function DragonCard({ dragon, t, onClose }) {
  const jm = "'JetBrains Mono', monospace";
  const of_ = "'Outfit', sans-serif";

  const data = {
    human: { emoji: "🐉", color: "#D4AF37", name: t.humanDragon, role: t.humanRole, desc: t.humanDesc, ai: null },
    guardian: { emoji: "🛡️", color: "#8B5CF6", name: t.guardian, role: t.guardianRole, desc: t.guardianDesc, ai: t.guardianAI },
    architect: { emoji: "🏗️", color: "#3B82F6", name: t.architect, role: t.architectRole, desc: t.architectDesc, ai: t.architectAI },
    witness: { emoji: "👁️", color: "#10B981", name: t.witness, role: t.witnessRole, desc: t.witnessDesc, ai: t.witnessAI },
  }[dragon];

  if (!data) return null;

  return (
    <div style={{
      position: "fixed", inset: 0, zIndex: 100,
      background: "rgba(0,0,0,0.7)",
      display: "flex", alignItems: "center", justifyContent: "center",
      animation: "fadeIn 0.3s ease",
    }} onClick={onClose}>
      <div style={{
        background: "#111", border: `1px solid ${data.color}40`,
        borderRadius: "12px", padding: "32px", maxWidth: "400px", width: "90%",
        textAlign: "center",
      }} onClick={e => e.stopPropagation()}>
        <div style={{ fontSize: "3rem", marginBottom: "16px" }}>{data.emoji}</div>
        <div style={{
          fontFamily: of_, fontSize: "1.4rem", fontWeight: 600,
          color: data.color, marginBottom: "4px",
        }}>{data.name}</div>
        {data.ai && (
          <div style={{
            fontFamily: jm, fontSize: "0.7rem", color: "#666", marginBottom: "12px",
          }}>{data.ai}</div>
        )}
        <div style={{
          fontFamily: jm, fontSize: "0.65rem", color: "#888",
          textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: "16px",
        }}>{data.role}</div>
        <div style={{
          fontFamily: of_, fontSize: "0.85rem", fontWeight: 300,
          color: "#AAA", lineHeight: 1.6,
        }}>{data.desc}</div>
        <button onClick={onClose} style={{
          marginTop: "24px", padding: "10px 24px",
          background: `${data.color}15`, border: `1px solid ${data.color}40`,
          borderRadius: "6px", color: data.color,
          fontFamily: jm, fontSize: "0.7rem", cursor: "pointer",
        }}>OK</button>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════
// CONSENSUS PULSE — Live Verification Feed
// ═══════════════════════════════════════════

function ConsensusPulse({ t }) {
  const [pulses, setPulses] = useState([]);
  const jm = "'JetBrains Mono', monospace";
  const of_ = "'Outfit', sans-serif";

  const dragons = [
    { emoji: "🛡️", name: "GUARDIAN", color: "#8B5CF6" },
    { emoji: "🏗️", name: "ARCHITECT", color: "#3B82F6" },
    { emoji: "👁️", name: "WITNESS", color: "#10B981" },
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      const dragon = dragons[Math.floor(Math.random() * 3)];
      const action = t.consensusAction[Math.floor(Math.random() * t.consensusAction.length)];
      const target = t.consensusTarget[Math.floor(Math.random() * t.consensusTarget.length)];

      setPulses(prev => [{
        id: Date.now(),
        dragon,
        action,
        target,
        hash: rh(8),
        status: "verified",
      }, ...prev.slice(0, 4)]);
    }, 2200);

    return () => clearInterval(interval);
  }, [t]);

  return (
    <div style={{
      background: "rgba(255,255,255,0.02)",
      border: "1px solid rgba(255,255,255,0.04)",
      borderRadius: "8px", padding: "16px",
      maxHeight: "200px", overflow: "hidden",
    }}>
      {pulses.map((pulse, i) => (
        <div key={pulse.id} style={{
          display: "flex", alignItems: "center", gap: "10px",
          padding: "8px 0",
          borderBottom: i < pulses.length - 1 ? "1px solid rgba(255,255,255,0.03)" : "none",
          opacity: 1 - (i * 0.15),
          animation: i === 0 ? "slideIn 0.3s ease" : "none",
        }}>
          <span style={{ fontSize: "1rem" }}>{pulse.dragon.emoji}</span>
          <div style={{ flex: 1 }}>
            <div style={{
              fontFamily: of_, fontSize: "0.75rem", color: "#AAA",
            }}>
              <span style={{ color: pulse.dragon.color, fontWeight: 500 }}>{pulse.dragon.name}</span>
              {" "}{pulse.action}{" "}
              <span style={{ color: "#888" }}>{pulse.target}</span>
            </div>
            <div style={{
              fontFamily: jm, fontSize: "0.55rem", color: "#444", marginTop: "2px",
            }}>
              #{pulse.hash}
            </div>
          </div>
          <div style={{
            width: "6px", height: "6px", borderRadius: "50%",
            background: "#10B981",
            boxShadow: "0 0 8px rgba(16, 185, 129, 0.4)",
          }} />
        </div>
      ))}
      {pulses.length === 0 && (
        <div style={{
          fontFamily: jm, fontSize: "0.65rem", color: "#444",
          textAlign: "center", padding: "20px",
        }}>
          {t.verifying}...
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════
// INVARIANT GRID — 9 Invariants (3x3)
// ═══════════════════════════════════════════

function InvariantGrid({ t }) {
  const [verified, setVerified] = useState([]);
  const jm = "'JetBrains Mono', monospace";
  const of_ = "'Outfit', sans-serif";

  const invariants = [
    { id: "I1", title: t.i1, desc: t.i1desc },
    { id: "I2", title: t.i2, desc: t.i2desc },
    { id: "I3", title: t.i3, desc: t.i3desc },
    { id: "I4", title: t.i4, desc: t.i4desc },
    { id: "I5", title: t.i5, desc: t.i5desc },
    { id: "I6", title: t.i6, desc: t.i6desc },
    { id: "I7", title: t.i7, desc: t.i7desc },
    { id: "I8", title: t.i8, desc: t.i8desc },
    { id: "I9", title: t.i9, desc: t.i9desc, irremediable: true },
  ];

  useEffect(() => {
    invariants.forEach((inv, i) => {
      setTimeout(() => {
        setVerified(prev => [...prev, inv.id]);
      }, 300 + i * 200);
    });
  }, []);

  return (
    <div style={{
      display: "grid",
      gridTemplateColumns: "repeat(3, 1fr)",
      gap: "8px",
    }}>
      {invariants.map((inv, i) => {
        const isVerified = verified.includes(inv.id);
        const isI9 = inv.irremediable;

        return (
          <div key={inv.id} style={{
            padding: "12px 10px",
            background: isVerified
              ? (isI9 ? "rgba(239, 68, 68, 0.06)" : "rgba(16, 185, 129, 0.04)")
              : "rgba(255,255,255,0.02)",
            border: `1px solid ${isVerified
              ? (isI9 ? "rgba(239, 68, 68, 0.2)" : "rgba(16, 185, 129, 0.15)")
              : "rgba(255,255,255,0.04)"}`,
            borderRadius: "6px",
            transition: "all 0.4s ease",
            textAlign: "center",
          }}>
            <div style={{
              fontFamily: jm, fontSize: "0.6rem",
              color: isVerified ? (isI9 ? "#EF4444" : "#10B981") : "#333",
              marginBottom: "4px", fontWeight: 600,
            }}>
              {inv.id} {isVerified ? "✓" : "○"}
            </div>
            <div style={{
              fontFamily: of_, fontSize: "0.65rem",
              color: isVerified ? (isI9 ? "#EF4444" : "#AAA") : "#555",
              lineHeight: 1.3,
            }}>
              {inv.desc}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ═══════════════════════════════════════════
// LANG SWITCH
// ═══════════════════════════════════════════

function LangSwitch({ lang, setLang }) {
  return (
    <div style={{ display: "flex", justifyContent: "center", gap: "4px", marginBottom: "24px" }}>
      {["pt", "de", "en"].map(l => (
        <button key={l} onClick={() => setLang(l)} aria-label={`Switch to ${l}`} style={{
          background: lang === l ? "rgba(212,175,55,0.12)" : "rgba(255,255,255,0.02)",
          border: lang === l ? "1px solid rgba(212,175,55,0.35)" : "1px solid rgba(255,255,255,0.06)",
          borderRadius: "4px", padding: "6px 14px", cursor: "pointer",
          display: "flex", alignItems: "center", gap: "6px", transition: "all 0.3s ease",
        }}>
          <span style={{ fontSize: "0.9rem" }}>{i18n[l].flag}</span>
          <span style={{
            fontFamily: "'JetBrains Mono', monospace", fontSize: "0.65rem",
            color: lang === l ? "#D4AF37" : "#555", letterSpacing: "0.08em", textTransform: "uppercase",
          }}>{l}</span>
        </button>
      ))}
    </div>
  );
}

// ═══════════════════════════════════════════
// MAIN: DNA TRANSPARENCY PANEL
// ═══════════════════════════════════════════

export default function DNATransparencyPanel({ lang: externalLang, setLang: externalSetLang, onComplete }) {
  const [internalLang, setInternalLang] = useState("pt");
  const lang = externalLang || internalLang;
  const setLang = externalSetLang || setInternalLang;

  const [selectedDragon, setSelectedDragon] = useState(null);
  const [sovereignty, setSovereignty] = useState(false);
  const t = i18n[lang];

  const jm = "'JetBrains Mono', monospace";
  const bg = "'Bricolage Grotesque', serif";
  const of_ = "'Outfit', sans-serif";

  const handleComplete = () => {
    if (onComplete) {
      onComplete();
    } else {
      setSovereignty(true);
    }
  };

  if (sovereignty) {
    return (
      <div style={{
        minHeight: "100vh", background: "#0A0A0A", display: "flex", flexDirection: "column",
        alignItems: "center", justifyContent: "center", fontFamily: of_,
      }}>
        <link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@300;400;600;800&family=Outfit:wght@200;300;400;600&family=JetBrains+Mono:wght@300;400;500&display=swap" rel="stylesheet" />
        <div style={{ animation: "fadeInUp 2s ease", textAlign: "center" }}>
          <div style={{ fontFamily: bg, fontSize: "2.5rem", fontWeight: 800, color: "#D4AF37", marginBottom: "16px" }}>
            a4Desk BABEL
          </div>
          <div style={{ fontFamily: of_, fontSize: "1rem", fontWeight: 200, color: "#666", marginBottom: "8px" }}>
            {t.principle}
          </div>
          <div style={{ fontFamily: jm, fontSize: "0.65rem", color: "#333", marginTop: "24px" }}>SOVEREIGNTY ACTIVE</div>
          <div style={{ width: "200px", height: "2px", background: "#1A1A1A", margin: "16px auto", borderRadius: "1px", overflow: "hidden" }}>
            <div style={{ height: "100%", background: "#D4AF37", animation: "loadBar 2s ease forwards" }} />
          </div>
        </div>
        <style>{`
          @keyframes fadeInUp { from{opacity:0;transform:translateY(30px)} to{opacity:1;transform:translateY(0)} }
          @keyframes loadBar { from{width:0%} to{width:100%} }
        `}</style>
      </div>
    );
  }

  return (
    <div style={{
      minHeight: "100vh", background: "#050505", color: "#E0E0E0",
      fontFamily: of_, position: "relative", overflow: "hidden",
    }}>
      <link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@300;400;600;800&family=Outfit:wght@200;300;400;600&family=JetBrains+Mono:wght@300;400;500&display=swap" rel="stylesheet" />
      <style>{`
        @keyframes fadeInUp { from{opacity:0;transform:translateY(30px)} to{opacity:1;transform:translateY(0)} }
        @keyframes fadeIn { from{opacity:0} to{opacity:1} }
        @keyframes slideIn { from{opacity:0;transform:translateX(-20px)} to{opacity:1;transform:translateX(0)} }
        @keyframes pulseGlow { 0%,100%{box-shadow:0 0 20px rgba(212,175,55,0.1)} 50%{box-shadow:0 0 40px rgba(212,175,55,0.2)} }
        * { box-sizing:border-box; margin:0; padding:0 }
        ::-webkit-scrollbar { width:4px } ::-webkit-scrollbar-track { background:#080808 } ::-webkit-scrollbar-thumb { background:rgba(212,175,55,0.2); border-radius:2px }
      `}</style>

      {/* Background grid */}
      <div style={{ position: "fixed", inset: 0, pointerEvents: "none", zIndex: 0 }}>
        <svg width="100%" height="100%" style={{ opacity: 0.02 }}>
          <defs>
            <pattern id="trinityGrid" width="80" height="80" patternUnits="userSpaceOnUse">
              <circle cx="40" cy="40" r="1" fill="#D4AF37" />
              <circle cx="40" cy="40" r="30" fill="none" stroke="#D4AF37" strokeWidth="0.3" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#trinityGrid)" />
        </svg>
      </div>

      <div style={{ position: "relative", zIndex: 2, maxWidth: "900px", margin: "0 auto", padding: "40px 24px" }}>

        <LangSwitch lang={lang} setLang={setLang} />

        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: "48px", animation: "fadeInUp 1s ease" }}>
          <div style={{ fontFamily: jm, fontSize: "0.55rem", color: "#333", letterSpacing: "0.4em", textTransform: "uppercase", marginBottom: "12px" }}>
            WINDI Publishing House — {t.subtitle}
          </div>
          <h1 style={{
            fontFamily: bg, fontSize: "clamp(1.8rem, 4vw, 2.8rem)", fontWeight: 800,
            letterSpacing: "-0.02em", lineHeight: 1.2,
            background: "linear-gradient(135deg, #D4AF37 0%, #F5E6A3 40%, #D4AF37 70%, #B8941F 100%)",
            WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
          }}>{t.title}</h1>
          <div style={{ fontFamily: of_, fontSize: "0.85rem", fontWeight: 200, color: "#555", marginTop: "12px", maxWidth: "550px", margin: "12px auto 0", lineHeight: 1.6 }}>
            {t.intro}
          </div>
        </div>

        {/* Trinity Section */}
        <section style={{ marginBottom: "60px", animation: "fadeInUp 1s ease 0.2s both" }}>
          <div style={{ textAlign: "center", marginBottom: "24px" }}>
            <div style={{ fontFamily: jm, fontSize: "0.55rem", color: "#D4AF37", letterSpacing: "0.3em", textTransform: "uppercase", marginBottom: "8px" }}>
              {t.trinitySub}
            </div>
            <div style={{ fontFamily: bg, fontSize: "1.4rem", fontWeight: 600, color: "#CCC" }}>
              {t.trinityTitle}
            </div>
          </div>

          <TrinityOrbital t={t} onDragonClick={setSelectedDragon} />

          <div style={{ textAlign: "center", marginTop: "16px" }}>
            <div style={{ fontFamily: jm, fontSize: "0.55rem", color: "#444" }}>
              {lang === "pt" ? "Clique nos dragões para saber mais" :
               lang === "de" ? "Klicken Sie auf die Drachen, um mehr zu erfahren" :
               "Click on the dragons to learn more"}
            </div>
          </div>
        </section>

        {/* Two-column layout for Consensus + Invariants */}
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
          gap: "24px",
          marginBottom: "60px",
        }}>
          {/* Consensus Section */}
          <section style={{ animation: "fadeInUp 1s ease 0.4s both" }}>
            <div style={{ marginBottom: "16px" }}>
              <div style={{ fontFamily: jm, fontSize: "0.55rem", color: "#D4AF37", letterSpacing: "0.2em", textTransform: "uppercase", marginBottom: "4px" }}>
                {t.consensusSub}
              </div>
              <div style={{ fontFamily: bg, fontSize: "1.1rem", fontWeight: 600, color: "#CCC", marginBottom: "8px" }}>
                {t.consensusTitle}
              </div>
              <div style={{ fontFamily: of_, fontSize: "0.75rem", fontWeight: 300, color: "#666", lineHeight: 1.5 }}>
                {t.consensusIntro}
              </div>
            </div>
            <ConsensusPulse t={t} />
          </section>

          {/* Invariants Section */}
          <section style={{ animation: "fadeInUp 1s ease 0.6s both" }}>
            <div style={{ marginBottom: "16px" }}>
              <div style={{ fontFamily: jm, fontSize: "0.55rem", color: "#D4AF37", letterSpacing: "0.2em", textTransform: "uppercase", marginBottom: "4px" }}>
                {t.invariantsSub}
              </div>
              <div style={{ fontFamily: bg, fontSize: "1.1rem", fontWeight: 600, color: "#CCC", marginBottom: "8px" }}>
                {t.invariantsTitle}
              </div>
              <div style={{ fontFamily: of_, fontSize: "0.75rem", fontWeight: 300, color: "#666", lineHeight: 1.5 }}>
                {t.invariantsIntro}
              </div>
            </div>
            <InvariantGrid t={t} />
          </section>
        </div>

        {/* Seal of Unification */}
        <div style={{
          textAlign: "center", padding: "32px 24px", marginBottom: "48px",
          background: "rgba(212,175,55,0.02)", border: "1px solid rgba(212,175,55,0.06)",
          borderRadius: "8px", animation: "fadeInUp 1s ease 0.8s both",
        }}>
          <div style={{ fontFamily: jm, fontSize: "0.55rem", color: "#D4AF37", letterSpacing: "0.2em", textTransform: "uppercase", marginBottom: "16px" }}>
            {t.sealTitle}
          </div>
          <div style={{ fontFamily: of_, fontSize: "0.9rem", fontWeight: 300, color: "#888", lineHeight: 1.7, fontStyle: "italic", maxWidth: "600px", margin: "0 auto" }}>
            {t.sealQuote}
          </div>
          <div style={{ fontFamily: jm, fontSize: "0.55rem", color: "#555", marginTop: "16px" }}>
            {t.sealAuthor}
          </div>
        </div>

        {/* Enter Sovereignty */}
        <div style={{ textAlign: "center", padding: "24px 24px 60px", animation: "fadeInUp 1s ease 1s both" }}>
          <button
            onClick={handleComplete}
            style={{
              background: "rgba(212,175,55,0.06)", border: "1px solid #D4AF37", color: "#D4AF37",
              fontFamily: jm, fontSize: "1rem", padding: "18px 64px", cursor: "pointer",
              letterSpacing: "0.2em", transition: "all 0.4s ease", borderRadius: "4px",
              animation: "pulseGlow 3s ease infinite",
            }}
            onMouseEnter={e => { e.target.style.background = "rgba(212,175,55,0.12)"; e.target.style.transform = "scale(1.02)"; }}
            onMouseLeave={e => { e.target.style.background = "rgba(212,175,55,0.06)"; e.target.style.transform = "scale(1)"; }}
          >
            {t.enterButton}
          </button>
          <div style={{ marginTop: "12px", fontFamily: of_, fontSize: "0.75rem", color: "#444", fontWeight: 200 }}>
            {t.enterSub}
          </div>
        </div>

        {/* Footer */}
        <div style={{ textAlign: "center", padding: "20px", borderTop: "1px solid rgba(255,255,255,0.03)" }}>
          <div style={{ fontFamily: bg, fontSize: "0.7rem", fontWeight: 300, color: "#333", letterSpacing: "0.2em", textTransform: "uppercase" }}>
            {t.principle}
          </div>
        </div>
      </div>

      {/* Dragon Detail Card */}
      {selectedDragon && (
        <DragonCard dragon={selectedDragon} t={t} onClose={() => setSelectedDragon(null)} />
      )}
    </div>
  );
}
