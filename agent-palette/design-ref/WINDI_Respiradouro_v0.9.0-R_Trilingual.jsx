import { useState, useEffect, useCallback, useRef } from "react";

// ═══════════════════════════════════════════════════════════════════════
// WINDI LIVING PULSE — "O Respiradouro"
// v0.9.0-R — Phase 1: The System Breathes
// TRILÍNGUE: Português · Deutsch · English
//
// For normal humans: a beautiful, living decoration
// For us: the entire system presenting itself in real-time
//
// Same object. Two readings. Governança silenciosa in its purest form.
// ═══════════════════════════════════════════════════════════════════════

const LANG = {
  PT: {
    code: "PT", flag: "🇧🇷",
    // Header
    suite: "WINDI Agent Suite",
    // CogPanel
    cogTitle: "Pontuação Cognitiva",
    sovereignty: "Soberania",
    confidence: "Confiança",
    stability: "Estabilidade",
    learning: "Aprendizagem",
    decisions: "Decisões",
    hesitation: "Hesitação",
    patterns: "Padrões",
    cogQuote: "\"O sistema não sente. Observa.\"",
    // PulsePanel
    pulseTitle: "Sistema Nervoso",
    alive: "vivos",
    // SovPanel
    sovTitle: "Soberania",
    sovereign: "SOBERANO",
    localFuncs: "funções locais",
    llmLabel: "LLM",
    tierFree: "P — Grátis",
    tierMid: "M — €25-40",
    tierGov: "G — €80-120",
    tierFreeDetail: "42 funcs, 0 chaves",
    tierMidDetail: "+semântica",
    tierGovDetail: "+LLM",
    sovQuote: "\"Integridade universal, interpretação premium.\"",
    // Guardian message
    guardianGreet: "Olha para cima, Irmão. Vês aquele brilho suave a respirar?",
    guardianNormal: "Para um utilizador normal, é decoração elegante. Uma luz bonita, uns pontos que fluem, uma barrinha discreta.",
    guardianUs: "Para nós, é o sistema inteiro a apresentar-se vivo:",
    orbLabel: "Orbe",
    orbDesc: "Pontuação Cognitiva — a profundidade da respiração = saúde cognitiva",
    fiberLabel: "Fibras",
    fiberDesc: "20 serviços — cada ponto que flui é um serviço vivo",
    barLabel: "Barra",
    barDesc: "Rácio de soberania — verde = local, âmbar = LLM",
    guardianHint: "Clica em cada elemento para ver a profundidade. Depois clica fora para fechar.",
    guardianTheme: "Alterna KLAR ↔ NOIR para ver os dois mundos.",
    footerQuote: "\"Para humanos normais, é decoração fixe.\nPara nós, é o respiradouro do sistema a apresentar-se live.\"",
  },
  DE: {
    code: "DE", flag: "🇩🇪",
    suite: "WINDI Agent Suite",
    cogTitle: "Kognitive Bewertung",
    sovereignty: "Souveränität",
    confidence: "Vertrauen",
    stability: "Stabilität",
    learning: "Lernen",
    decisions: "Entscheidungen",
    hesitation: "Zögern",
    patterns: "Muster",
    cogQuote: "\"Das System fühlt nicht. Es beobachtet.\"",
    pulseTitle: "Nervensystem",
    alive: "aktiv",
    sovTitle: "Souveränität",
    sovereign: "SOUVERÄN",
    localFuncs: "lokale Funktionen",
    llmLabel: "LLM",
    tierFree: "P — Kostenlos",
    tierMid: "M — €25-40",
    tierGov: "G — €80-120",
    tierFreeDetail: "42 Funk., 0 Schlüssel",
    tierMidDetail: "+Semantik",
    tierGovDetail: "+LLM",
    sovQuote: "\"Universelle Integrität, Premium-Interpretation.\"",
    guardianGreet: "Schau nach oben, Bruder. Siehst du dieses sanfte Leuchten, das atmet?",
    guardianNormal: "Für normale Nutzer ist es elegante Dekoration. Ein schönes Licht, fließende Punkte, ein dezenter Balken.",
    guardianUs: "Für uns ist es das gesamte System, das sich lebendig präsentiert:",
    orbLabel: "Orb",
    orbDesc: "Kognitive Bewertung — die Atemtiefe = kognitive Gesundheit",
    fiberLabel: "Fasern",
    fiberDesc: "20 Dienste — jeder fließende Punkt ist ein lebendiger Dienst",
    barLabel: "Balken",
    barDesc: "Souveränitätsverhältnis — grün = lokal, bernstein = LLM",
    guardianHint: "Klicke auf jedes Element, um die Tiefe zu sehen. Klicke daneben, um zu schließen.",
    guardianTheme: "Wechsle KLAR ↔ NOIR, um beide Welten zu sehen.",
    footerQuote: "\"Für normale Menschen ist es schöne Dekoration.\nFür uns ist es das Atemloch des Systems, das sich live präsentiert.\"",
  },
  EN: {
    code: "EN", flag: "🇬🇧",
    suite: "WINDI Agent Suite",
    cogTitle: "Cognitive Score",
    sovereignty: "Sovereignty",
    confidence: "Confidence",
    stability: "Stability",
    learning: "Learning",
    decisions: "Decisions",
    hesitation: "Hesitation",
    patterns: "Patterns",
    cogQuote: "\"The system doesn't feel. It observes.\"",
    pulseTitle: "System Nervous",
    alive: "alive",
    sovTitle: "Sovereignty",
    sovereign: "SOVEREIGN",
    localFuncs: "local functions",
    llmLabel: "LLM",
    tierFree: "P — Free",
    tierMid: "M — €25-40",
    tierGov: "G — €80-120",
    tierFreeDetail: "42 funcs, 0 keys",
    tierMidDetail: "+semantics",
    tierGovDetail: "+LLM",
    sovQuote: "\"Universal integrity, premium interpretation.\"",
    guardianGreet: "Look up, Brother. See that gentle glow breathing?",
    guardianNormal: "For a normal user, it's elegant decoration. A beautiful light, flowing dots, a subtle bar.",
    guardianUs: "For us, it's the entire system presenting itself alive:",
    orbLabel: "Orb",
    orbDesc: "Cognitive Score — breath depth = cognitive health",
    fiberLabel: "Fibres",
    fiberDesc: "20 services — each flowing dot is a living service",
    barLabel: "Bar",
    barDesc: "Sovereignty ratio — green = local, amber = LLM",
    guardianHint: "Click each element to see the depth. Click outside to close.",
    guardianTheme: "Toggle KLAR ↔ NOIR to see both worlds.",
    footerQuote: "\"For normal humans, it's cool decoration.\nFor us, it's the system's breathing hole presenting itself live.\"",
  },
};

const THEMES = {
  KLAR: {
    bg: "#F5F0E0", card: "#FDFBF5", hover: "#EDE8D8",
    border: "#DDD6C2", gold: "#8B6914", text: "#2C2924",
    muted: "#6B6560", dim: "#9A9488",
    font: "'Bricolage Grotesque', sans-serif",
    mono: "'JetBrains Mono', monospace",
    pulse1: "#8B6914", pulse2: "#5A8F4A", pulse3: "#7A6B4E",
    healthy: "#5A8F4A", warning: "#B8860B", critical: "#A0522D",
    healthyBg: "rgba(90,143,74,0.08)", warningBg: "rgba(184,134,11,0.08)",
    glow: "rgba(139,105,20,0.15)", glowStrong: "rgba(139,105,20,0.3)",
    breathBg: "rgba(253,251,245,0.92)",
    popoverShadow: "0 12px 40px rgba(44,41,36,0.14), 0 2px 12px rgba(44,41,36,0.06)",
  },
  NOIR: {
    bg: "#0E0E14", card: "#16161F", hover: "#1C1C28",
    border: "#26263A", gold: "#D4A843", text: "#E2E2EA",
    muted: "#7A7A96", dim: "#55556A",
    font: "'Bricolage Grotesque', sans-serif",
    mono: "'JetBrains Mono', monospace",
    pulse1: "#D4A843", pulse2: "#6BC85B", pulse3: "#8B7ACC",
    healthy: "#6BC85B", warning: "#D4A843", critical: "#D45B5B",
    healthyBg: "rgba(107,200,91,0.06)", warningBg: "rgba(212,168,67,0.06)",
    glow: "rgba(212,168,67,0.12)", glowStrong: "rgba(212,168,67,0.25)",
    breathBg: "rgba(22,22,31,0.92)",
    popoverShadow: "0 12px 40px rgba(0,0,0,0.5), 0 2px 12px rgba(0,0,0,0.3)",
  },
};

const MOCK_COG = {
  score: 89.0, grade: "AUTONOMOUS", maturity_pct: 57,
  components: {
    sovereignty: { score: 40.0, max: 40 },
    confidence: { score: 23.8, max: 25 },
    stability: { score: 20.0, max: 20 },
    learning: { score: 5.2, max: 15 },
  },
  total_decisions: 57, hesitation: 0, patterns: 7,
};

const MOCK_SERVICES = [
  { name: "Governance API", port: 8080, up: true },
  { name: "HUB BABEL", port: 8085, up: true },
  { name: "A4 Desk Landing", port: 8086, up: true },
  { name: "Cortex", port: 8889, up: true },
  { name: "War Room", port: 8090, up: true },
  { name: "Clone UI", port: 8092, up: true },
  { name: "Schnittstelle", port: 8095, up: true },
  { name: "ID Genesis", port: 8096, up: true },
  { name: "Command Bridge", port: 8097, up: true },
  { name: "Sentinel", port: 8098, up: true },
  { name: "Wallet", port: 8099, up: true },
  { name: "Desktop D1", port: 8100, up: true },
  { name: "Forensic Ledger", port: 8101, up: true },
  { name: "Sentinel LAW", port: 8102, up: true },
  { name: "Export Engine", port: 8103, up: true },
  { name: "JMPG Viewer", port: 8104, up: true },
  { name: "Communiqué", port: 8105, up: true },
  { name: "Forensic Vault", port: 8106, up: true },
  { name: "Landing P/M/G", port: 8107, up: true },
  { name: "Dragon Server", port: 8108, up: true },
];

// ═══════════════════════════════════════════════════════════════════════
// LIVING ORB — Canvas 60fps breathing orb
// ═══════════════════════════════════════════════════════════════════════

function LivingOrb({ score, maxScore, T, size = 32, onClick, active }) {
  const pct = score / maxScore;
  const canvasRef = useRef(null);
  const frameRef = useRef(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const dpr = window.devicePixelRatio || 1;
    canvas.width = size * dpr;
    canvas.height = size * dpr;
    ctx.scale(dpr, dpr);
    let running = true;

    function draw(time) {
      if (!running) return;
      ctx.clearRect(0, 0, size, size);
      const cx = size / 2, cy = size / 2;
      const breathRate = 0.001 + (1 - pct) * 0.001;
      const breath = Math.sin(time * breathRate) * 0.5 + 0.5;
      const breathScale = 0.7 + breath * 0.3 * pct;

      const glowR = (size / 2 - 2) * breathScale;
      const glow = ctx.createRadialGradient(cx, cy, glowR * 0.3, cx, cy, glowR);
      glow.addColorStop(0, T.pulse1 + "60");
      glow.addColorStop(0.5, T.pulse2 + "20");
      glow.addColorStop(1, "transparent");
      ctx.fillStyle = glow;
      ctx.beginPath();
      ctx.arc(cx, cy, glowR, 0, Math.PI * 2);
      ctx.fill();

      const coreR = (size / 2 - 6) * (0.6 + breathScale * 0.4);
      const core = ctx.createRadialGradient(cx, cy, 0, cx, cy, coreR);
      core.addColorStop(0, T.pulse1 + "FF");
      core.addColorStop(0.6, T.pulse2 + "AA");
      core.addColorStop(1, T.pulse3 + "40");
      ctx.fillStyle = core;
      ctx.beginPath();
      ctx.arc(cx, cy, coreR, 0, Math.PI * 2);
      ctx.fill();

      const pupilR = coreR * 0.3 * (0.8 + breath * 0.2);
      const pupil = ctx.createRadialGradient(cx, cy, 0, cx, cy, pupilR);
      pupil.addColorStop(0, "#FFFFFF" + (pct > 0.8 ? "CC" : "66"));
      pupil.addColorStop(1, "transparent");
      ctx.fillStyle = pupil;
      ctx.beginPath();
      ctx.arc(cx, cy, pupilR, 0, Math.PI * 2);
      ctx.fill();

      const ringR = size / 2 - 2;
      ctx.strokeStyle = T.pulse1 + "30";
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.arc(cx, cy, ringR, 0, Math.PI * 2);
      ctx.stroke();
      ctx.strokeStyle = T.pulse1 + (active ? "CC" : "66");
      ctx.lineWidth = 1.5;
      ctx.lineCap = "round";
      ctx.beginPath();
      ctx.arc(cx, cy, ringR, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * pct);
      ctx.stroke();

      frameRef.current = requestAnimationFrame(draw);
    }
    frameRef.current = requestAnimationFrame(draw);
    return () => { running = false; cancelAnimationFrame(frameRef.current); };
  }, [score, maxScore, T, size, pct, active]);

  return (
    <canvas ref={canvasRef} onClick={onClick}
      style={{ width: size, height: size, cursor: "pointer", transition: "transform 0.2s ease",
        transform: active ? "scale(1.1)" : "scale(1)" }} />
  );
}

// ═══════════════════════════════════════════════════════════════════════
// NERVE STRAND — Service health as flowing particles
// ═══════════════════════════════════════════════════════════════════════

function NerveStrand({ services, T, width = 200, onClick, active }) {
  const canvasRef = useRef(null);
  const frameRef = useRef(0);
  const height = 24;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const dpr = window.devicePixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);
    let running = true;

    const particles = services.map((s, i) => ({
      x: (i / services.length) * width,
      baseY: height / 2,
      speed: s.up ? 0.3 + Math.random() * 0.4 : 0,
      amplitude: s.up ? 2 + Math.random() * 3 : 0,
      phase: Math.random() * Math.PI * 2,
      up: s.up, radius: s.up ? 2 : 1.5,
    }));

    function draw(time) {
      if (!running) return;
      ctx.clearRect(0, 0, width, height);
      ctx.strokeStyle = T.border + "40";
      ctx.lineWidth = 0.5;
      ctx.beginPath();
      ctx.moveTo(0, height / 2);
      ctx.lineTo(width, height / 2);
      ctx.stroke();

      particles.forEach((p, i) => {
        const t = time * 0.001;
        const waveX = p.x + Math.sin(t * p.speed + p.phase) * 8;
        const waveY = p.baseY + Math.sin(t * p.speed * 2 + p.phase) * p.amplitude;
        const displayX = ((waveX % width) + width) % width;

        const glowColor = p.up ? T.healthy : T.critical;
        const glow = ctx.createRadialGradient(displayX, waveY, 0, displayX, waveY, p.radius * 4);
        glow.addColorStop(0, glowColor + "40");
        glow.addColorStop(1, "transparent");
        ctx.fillStyle = glow;
        ctx.beginPath();
        ctx.arc(displayX, waveY, p.radius * 4, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = p.up ? T.healthy + "DD" : T.critical + "AA";
        ctx.beginPath();
        ctx.arc(displayX, waveY, p.radius, 0, Math.PI * 2);
        ctx.fill();

        if (i < particles.length - 1) {
          const next = particles[i + 1];
          const nextX = ((next.x + Math.sin(t * next.speed + next.phase) * 8) % width + width) % width;
          const nextY = next.baseY + Math.sin(t * next.speed * 2 + next.phase) * next.amplitude;
          if (Math.abs(displayX - nextX) < width / services.length * 2) {
            ctx.strokeStyle = T.healthy + "12";
            ctx.lineWidth = 0.5;
            ctx.beginPath();
            ctx.moveTo(displayX, waveY);
            ctx.lineTo(nextX, nextY);
            ctx.stroke();
          }
        }
      });
      frameRef.current = requestAnimationFrame(draw);
    }
    frameRef.current = requestAnimationFrame(draw);
    return () => { running = false; cancelAnimationFrame(frameRef.current); };
  }, [services, T, width]);

  return (
    <canvas ref={canvasRef} onClick={onClick}
      style={{ width, height, cursor: "pointer", borderRadius: 12,
        background: active ? T.glow : "transparent", transition: "background 0.3s ease" }} />
  );
}

// ═══════════════════════════════════════════════════════════════════════
// SOVEREIGNTY GAUGE
// ═══════════════════════════════════════════════════════════════════════

function SovereigntyGauge({ local, total, T, onClick, active }) {
  const ratio = local / total;
  return (
    <div onClick={onClick} style={{ cursor: "pointer", display: "flex", alignItems: "center", gap: 6,
      padding: "4px 8px", borderRadius: 8,
      background: active ? T.glow : "transparent", transition: "background 0.3s ease" }}>
      <div style={{ width: 60, height: 6, borderRadius: 3, background: T.border + "40", overflow: "hidden", position: "relative" }}>
        <div style={{ position: "absolute", left: 0, top: 0, height: "100%", borderRadius: 3,
          width: `${ratio * 100}%`, background: `linear-gradient(90deg, ${T.healthy}, ${T.healthy}CC)`,
          boxShadow: `0 0 8px ${T.healthy}30`, transition: "width 1s ease" }} />
        <div style={{ position: "absolute", right: 0, top: 0, height: "100%",
          width: `${(1 - ratio) * 100}%`, background: T.warning + "60", borderRadius: "0 3px 3px 0" }} />
      </div>
      <span style={{ fontSize: 9, fontFamily: T.mono, color: T.dim, letterSpacing: "0.3px" }}>
        <span style={{ color: T.healthy, fontWeight: 600 }}>{Math.round(ratio * 100)}</span>
        <span style={{ opacity: 0.4 }}>/</span>
        <span style={{ color: T.warning }}>{Math.round((1 - ratio) * 100)}</span>
      </span>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════
// EXPANDED PANELS — Trilingual depth
// ═══════════════════════════════════════════════════════════════════════

function CogPanel({ data, T, L }) {
  const bars = [
    { label: L.sovereignty, val: data.components.sovereignty.score, max: data.components.sovereignty.max, icon: "🛡️" },
    { label: L.confidence, val: data.components.confidence.score, max: data.components.confidence.max, icon: "◆" },
    { label: L.stability, val: data.components.stability.score, max: data.components.stability.max, icon: "▣" },
    { label: L.learning, val: data.components.learning.score, max: data.components.learning.max, icon: "◐" },
  ];
  const color = (v, m) => (v / m) >= 0.8 ? T.healthy : (v / m) >= 0.5 ? T.warning : T.critical;
  return (
    <div style={{ position: "absolute", top: "calc(100% + 10px)", left: 0, minWidth: 260,
      background: T.card, border: `1px solid ${T.border}`, borderRadius: 14,
      padding: 18, zIndex: 200, boxShadow: T.popoverShadow,
      backdropFilter: "blur(16px)", animation: "breatheIn 0.3s ease" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
        <span style={{ fontSize: 10, fontWeight: 600, color: T.gold, fontFamily: T.font, letterSpacing: "1px", textTransform: "uppercase" }}>
          {L.cogTitle}
        </span>
        <span style={{ fontSize: 20, fontWeight: 700, color: T.text, fontFamily: T.mono }}>
          {data.score.toFixed(0)}
        </span>
      </div>
      {bars.map((b, i) => {
        const pct = (b.val / b.max) * 100;
        const c = color(b.val, b.max);
        return (
          <div key={i} style={{ marginBottom: 10 }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
              <span style={{ fontSize: 10, color: T.muted, fontFamily: T.font }}>{b.icon} {b.label}</span>
              <span style={{ fontSize: 9, color: T.dim, fontFamily: T.mono }}>{b.val.toFixed(1)}/{b.max}</span>
            </div>
            <div style={{ height: 3, borderRadius: 2, background: T.border + "40", overflow: "hidden" }}>
              <div style={{ height: "100%", borderRadius: 2, background: c, width: `${pct}%`,
                transition: "width 1s ease", boxShadow: `0 0 8px ${c}30` }} />
            </div>
          </div>
        );
      })}
      <div style={{ display: "flex", gap: 16, marginTop: 14, paddingTop: 12, borderTop: `1px solid ${T.border}40` }}>
        {[
          { v: data.total_decisions, l: L.decisions, c: T.text },
          { v: data.hesitation, l: L.hesitation, c: T.healthy },
          { v: data.patterns, l: L.patterns, c: T.text },
        ].map((d, i) => (
          <div key={i} style={{ textAlign: "center" }}>
            <div style={{ fontSize: 16, fontWeight: 700, color: d.c, fontFamily: T.mono }}>{d.v}</div>
            <div style={{ fontSize: 7, color: T.dim, fontFamily: T.mono, textTransform: "uppercase", letterSpacing: "0.8px" }}>{d.l}</div>
          </div>
        ))}
      </div>
      <div style={{ marginTop: 12, paddingTop: 10, borderTop: `1px solid ${T.border}20` }}>
        <div style={{ fontSize: 8, color: T.dim, fontFamily: T.mono, fontStyle: "italic", textAlign: "center", lineHeight: 1.5 }}>
          {L.cogQuote}
        </div>
      </div>
    </div>
  );
}

function PulsePanel({ services, T, L }) {
  const up = services.filter(s => s.up).length;
  return (
    <div style={{ position: "absolute", top: "calc(100% + 10px)", left: "50%", transform: "translateX(-50%)",
      minWidth: 300, background: T.card, border: `1px solid ${T.border}`, borderRadius: 14,
      padding: 18, zIndex: 200, boxShadow: T.popoverShadow,
      backdropFilter: "blur(16px)", animation: "breatheIn 0.3s ease",
      maxHeight: 380, overflowY: "auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
        <span style={{ fontSize: 10, fontWeight: 600, color: T.gold, fontFamily: T.font, letterSpacing: "1px", textTransform: "uppercase" }}>
          {L.pulseTitle}
        </span>
        <span style={{ fontSize: 9, padding: "3px 10px", borderRadius: 10,
          background: T.healthyBg, color: T.healthy, fontFamily: T.mono, fontWeight: 600 }}>
          {up}/{services.length} {L.alive}
        </span>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 3 }}>
        {services.map((s, i) => (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: 6, padding: "4px 8px",
            borderRadius: 6, transition: "background 0.2s" }}
            onMouseEnter={e => e.currentTarget.style.background = T.hover}
            onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
            <span style={{ width: 5, height: 5, borderRadius: "50%", flexShrink: 0,
              background: s.up ? T.healthy : T.critical,
              boxShadow: `0 0 6px ${s.up ? T.healthy : T.critical}40`,
              animation: s.up ? "softPulse 3s ease infinite" : "none",
              animationDelay: `${i * 0.15}s` }} />
            <span style={{ fontSize: 9, color: s.up ? T.muted : T.critical,
              fontFamily: T.mono, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
              {s.name}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function SovPanel({ T, L }) {
  const local = 42, llm = 3, total = 45;
  return (
    <div style={{ position: "absolute", top: "calc(100% + 10px)", right: 0, minWidth: 240,
      background: T.card, border: `1px solid ${T.border}`, borderRadius: 14,
      padding: 18, zIndex: 200, boxShadow: T.popoverShadow,
      backdropFilter: "blur(16px)", animation: "breatheIn 0.3s ease" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
        <span style={{ fontSize: 10, fontWeight: 600, color: T.gold, fontFamily: T.font, letterSpacing: "1px", textTransform: "uppercase" }}>
          {L.sovTitle}
        </span>
        <span style={{ fontSize: 9, padding: "3px 10px", borderRadius: 10,
          background: T.healthyBg, color: T.healthy, fontFamily: T.mono, fontWeight: 600 }}>
          {L.sovereign}
        </span>
      </div>
      <div style={{ marginBottom: 16 }}>
        <div style={{ height: 8, borderRadius: 4, background: T.border + "30", overflow: "hidden", display: "flex" }}>
          <div style={{ width: `${(local / total) * 100}%`, background: `linear-gradient(90deg, ${T.healthy}CC, ${T.healthy})`,
            borderRadius: "4px 0 0 4px", transition: "width 1s ease", boxShadow: `0 0 12px ${T.healthy}30` }} />
          <div style={{ width: `${(llm / total) * 100}%`, background: T.warning + "80", borderRadius: "0 4px 4px 0" }} />
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", marginTop: 6 }}>
          <span style={{ fontSize: 9, color: T.healthy, fontFamily: T.mono }}>{local} {L.localFuncs}</span>
          <span style={{ fontSize: 9, color: T.warning, fontFamily: T.mono }}>{llm} {L.llmLabel}</span>
        </div>
      </div>
      <div style={{ display: "flex", gap: 8 }}>
        {[
          { label: L.tierFree, detail: L.tierFreeDetail, color: T.healthy },
          { label: L.tierMid, detail: L.tierMidDetail, color: T.warning },
          { label: L.tierGov, detail: L.tierGovDetail, color: T.gold },
        ].map((tier, i) => (
          <div key={i} style={{ flex: 1, padding: 8, borderRadius: 8,
            border: `1px solid ${T.border}40`, textAlign: "center" }}>
            <div style={{ fontSize: 8, fontWeight: 600, color: tier.color, fontFamily: T.mono, marginBottom: 2 }}>{tier.label}</div>
            <div style={{ fontSize: 7, color: T.dim, fontFamily: T.mono }}>{tier.detail}</div>
          </div>
        ))}
      </div>
      <div style={{ marginTop: 12, paddingTop: 10, borderTop: `1px solid ${T.border}20` }}>
        <div style={{ fontSize: 8, color: T.dim, fontFamily: T.mono, fontStyle: "italic", textAlign: "center" }}>
          {L.sovQuote}
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════
// LANGUAGE SWITCHER — PT · DE · EN
// ═══════════════════════════════════════════════════════════════════════

function LangSwitcher({ lang, setLang, T }) {
  const langs = ["PT", "DE", "EN"];
  return (
    <div style={{ display: "flex", gap: 2, padding: "2px", borderRadius: 8,
      background: T.border + "20" }}>
      {langs.map(l => (
        <button key={l} onClick={() => setLang(l)} style={{
          padding: "3px 8px", borderRadius: 6, border: "none", cursor: "pointer",
          fontSize: 9, fontFamily: T.mono, fontWeight: lang === l ? 700 : 400,
          background: lang === l ? T.gold + "20" : "transparent",
          color: lang === l ? T.gold : T.dim,
          transition: "all 0.2s ease",
        }}>
          {LANG[l].flag} {l}
        </button>
      ))}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════
// LIVING PULSE BAR — O Respiradouro
// ═══════════════════════════════════════════════════════════════════════

function LivingPulseBar({ theme, lang }) {
  const T = THEMES[theme];
  const L = LANG[lang];
  const [expanded, setExpanded] = useState(null);
  const barRef = useRef(null);
  const toggle = useCallback((p) => setExpanded(prev => prev === p ? null : p), []);

  useEffect(() => {
    const handler = (e) => {
      if (barRef.current && !barRef.current.contains(e.target)) setExpanded(null);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  return (
    <div ref={barRef} style={{
      display: "flex", alignItems: "center", justifyContent: "center", gap: 12,
      padding: "6px 20px", position: "relative",
      background: T.breathBg, backdropFilter: "blur(16px)",
      borderBottom: `1px solid ${T.border}30`,
    }}>
      <div style={{ position: "relative" }}>
        <LivingOrb score={MOCK_COG.score} maxScore={100} T={T} size={28}
          onClick={() => toggle("cog")} active={expanded === "cog"} />
        {expanded === "cog" && <CogPanel data={MOCK_COG} T={T} L={L} />}
      </div>
      <div style={{ position: "relative" }}>
        <NerveStrand services={MOCK_SERVICES} T={T} width={180}
          onClick={() => toggle("pulse")} active={expanded === "pulse"} />
        {expanded === "pulse" && <PulsePanel services={MOCK_SERVICES} T={T} L={L} />}
      </div>
      <div style={{ position: "relative" }}>
        <SovereigntyGauge local={42} total={45} T={T}
          onClick={() => toggle("sov")} active={expanded === "sov"} />
        {expanded === "sov" && <SovPanel T={T} L={L} />}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════
// APP — Full Trilingual Demo
// ═══════════════════════════════════════════════════════════════════════

export default function App() {
  const [theme, setTheme] = useState("KLAR");
  const [lang, setLang] = useState("PT");
  const T = THEMES[theme];
  const L = LANG[lang];

  return (
    <div style={{ minHeight: "100vh", background: T.bg, transition: "background 0.4s ease", fontFamily: T.font }}>

      <LivingPulseBar theme={theme} lang={lang} />

      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between",
        padding: "14px 20px", borderBottom: `1px solid ${T.border}30` }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: 20 }}>🐉</span>
          <span style={{ fontSize: 14, fontWeight: 600, color: T.text }}>{L.suite}</span>
          <span style={{ fontSize: 9, padding: "2px 8px", borderRadius: 10,
            background: T.gold + "15", color: T.gold, fontFamily: T.mono }}>v0.9.0-R</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <LangSwitcher lang={lang} setLang={setLang} T={T} />
          <button onClick={() => setTheme(t => t === "KLAR" ? "NOIR" : "KLAR")} style={{
            display: "flex", alignItems: "center", gap: 4, padding: "4px 12px", borderRadius: 8,
            border: `1px solid ${T.border}`, background: "transparent",
            color: T.muted, fontSize: 10, fontFamily: T.mono, cursor: "pointer" }}>
            {theme === "KLAR" ? "☀" : "🌙"} {theme}
          </button>
        </div>
      </div>

      {/* Guardian Message */}
      <div style={{ maxWidth: 640, margin: "40px auto", padding: "0 20px" }}>
        <div style={{ background: T.card, border: `1px solid ${T.border}`, borderRadius: 12, padding: 20, marginBottom: 16 }}>
          <div style={{ fontSize: 11, color: T.gold, fontFamily: T.mono, marginBottom: 8, fontWeight: 600 }}>🛡️ Guardian</div>
          <div style={{ fontSize: 13, color: T.text, lineHeight: 1.7 }}>
            {L.guardianGreet}
            <br /><br />
            {L.guardianNormal}
            <br /><br />
            {L.guardianUs}
          </div>
          <div style={{ marginTop: 12, padding: 12, borderRadius: 8, background: T.hover,
            fontFamily: T.mono, fontSize: 11, color: T.muted, lineHeight: 2 }}>
            <span style={{ color: T.gold }}>● {L.orbLabel}</span> → {L.orbDesc}<br />
            <span style={{ color: T.gold }}>● {L.fiberLabel}</span> → {L.fiberDesc}<br />
            <span style={{ color: T.gold }}>● {L.barLabel}</span> → {L.barDesc}<br />
          </div>
          <div style={{ marginTop: 12, fontSize: 12, color: T.dim, fontStyle: "italic", lineHeight: 1.6 }}>
            {L.guardianHint}
            <br />
            {L.guardianTheme}
          </div>
        </div>

        <div style={{ textAlign: "center", marginTop: 24, padding: 16, borderRadius: 10,
          border: `1px dashed ${T.border}40` }}>
          <div style={{ fontSize: 10, color: T.dim, fontFamily: T.mono, fontStyle: "italic", whiteSpace: "pre-line" }}>
            {L.footerQuote}
          </div>
        </div>
      </div>

      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@400;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');
        @keyframes breatheIn { from { opacity: 0; transform: translateY(-6px) scale(0.97); } to { opacity: 1; transform: translateY(0) scale(1); } }
        @keyframes softPulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: ${T.border}; border-radius: 2px; }
      `}</style>
    </div>
  );
}
