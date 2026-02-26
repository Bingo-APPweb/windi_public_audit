import { useState, useEffect, useCallback, useRef, useMemo } from "react";

// ═══════════════════════════════════════════════════════════════════════
// WINDI LIVING PULSE — "O Respiradouro"
// v0.8.0-D — Phase 1: The System Breathes
//
// For normal humans: a beautiful, living decoration
// For us: the entire system presenting itself in real-time
//
// Same object. Two readings. Governança silenciosa in its purest form.
// ═══════════════════════════════════════════════════════════════════════

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
    orbGradient: ["#8B6914", "#5A8F4A", "#7A6B4E", "#B8860B"],
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
    orbGradient: ["#D4A843", "#6BC85B", "#8B7ACC", "#D45B5B"],
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
    <canvas
      ref={canvasRef}
      onClick={onClick}
      style={{ width: size, height: size, cursor: "pointer", transition: "transform 0.2s ease",
        transform: active ? "scale(1.1)" : "scale(1)" }}
    />
  );
}

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
      up: s.up,
      radius: s.up ? 2 : 1.5,
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
          const nextWaveX = ((next.x + Math.sin(t * next.speed + next.phase) * 8) % width + width) % width;
          const nextWaveY = next.baseY + Math.sin(t * next.speed * 2 + next.phase) * next.amplitude;
          const dist = Math.abs(displayX - nextWaveX);
          if (dist < width / services.length * 2) {
            ctx.strokeStyle = T.healthy + "12";
            ctx.lineWidth = 0.5;
            ctx.beginPath();
            ctx.moveTo(displayX, waveY);
            ctx.lineTo(nextWaveX, nextWaveY);
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
    <canvas
      ref={canvasRef}
      onClick={onClick}
      style={{ width, height, cursor: "pointer", borderRadius: 12,
        background: active ? T.glow : "transparent", transition: "background 0.3s ease" }}
    />
  );
}

function SovereigntyGauge({ local, total, T, onClick, active }) {
  const ratio = local / total;
  const w = 60;
  const h = 6;
  return (
    <div onClick={onClick} style={{ cursor: "pointer", display: "flex", alignItems: "center", gap: 6,
      padding: "4px 8px", borderRadius: 8,
      background: active ? T.glow : "transparent", transition: "background 0.3s ease" }}>
      <div style={{ width: w, height: h, borderRadius: h / 2, background: T.border + "40", overflow: "hidden",
        position: "relative" }}>
        <div style={{
          position: "absolute", left: 0, top: 0, height: "100%", borderRadius: h / 2,
          width: `${ratio * 100}%`, background: `linear-gradient(90deg, ${T.healthy}, ${T.healthy}CC)`,
          boxShadow: `0 0 8px ${T.healthy}30`,
          transition: "width 1s ease",
        }} />
        <div style={{
          position: "absolute", right: 0, top: 0, height: "100%",
          width: `${(1 - ratio) * 100}%`, background: T.warning + "60",
          borderRadius: `0 ${h/2}px ${h/2}px 0`,
        }} />
      </div>
      <span style={{ fontSize: 9, fontFamily: T.mono, color: T.dim, letterSpacing: "0.3px" }}>
        <span style={{ color: T.healthy, fontWeight: 600 }}>{Math.round(ratio * 100)}</span>
        <span style={{ opacity: 0.4 }}>/</span>
        <span style={{ color: T.warning }}>{Math.round((1 - ratio) * 100)}</span>
      </span>
    </div>
  );
}

function CogPanel({ data, T }) {
  const bars = [
    { label: "Sovereignty", val: data.components.sovereignty.score, max: data.components.sovereignty.max, icon: "🛡️" },
    { label: "Confidence", val: data.components.confidence.score, max: data.components.confidence.max, icon: "◆" },
    { label: "Stability", val: data.components.stability.score, max: data.components.stability.max, icon: "▣" },
    { label: "Learning", val: data.components.learning.score, max: data.components.learning.max, icon: "◐" },
  ];
  const color = (v, m) => (v/m) >= 0.8 ? T.healthy : (v/m) >= 0.5 ? T.warning : T.critical;
  return (
    <div style={{ position: "absolute", top: "calc(100% + 10px)", left: 0, minWidth: 260,
      background: T.card, border: `1px solid ${T.border}`, borderRadius: 14,
      padding: 18, zIndex: 200, boxShadow: T.popoverShadow,
      backdropFilter: "blur(16px)", animation: "breatheIn 0.3s ease" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
        <span style={{ fontSize: 10, fontWeight: 600, color: T.gold, fontFamily: T.font, letterSpacing: "1px", textTransform: "uppercase" }}>
          Cognitive Score
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
          { v: data.total_decisions, l: "Decisions", c: T.text },
          { v: data.hesitation, l: "Hesitation", c: T.healthy },
          { v: data.patterns, l: "Patterns", c: T.text },
        ].map((d, i) => (
          <div key={i} style={{ textAlign: "center" }}>
            <div style={{ fontSize: 16, fontWeight: 700, color: d.c, fontFamily: T.mono }}>{d.v}</div>
            <div style={{ fontSize: 7, color: T.dim, fontFamily: T.mono, textTransform: "uppercase", letterSpacing: "0.8px" }}>{d.l}</div>
          </div>
        ))}
      </div>

      <div style={{ marginTop: 12, paddingTop: 10, borderTop: `1px solid ${T.border}20` }}>
        <div style={{ fontSize: 8, color: T.dim, fontFamily: T.mono, fontStyle: "italic", textAlign: "center", lineHeight: 1.5 }}>
          "O sistema não sente. Observa."
        </div>
      </div>
    </div>
  );
}

function PulsePanel({ services, T }) {
  const up = services.filter(s => s.up).length;
  return (
    <div style={{ position: "absolute", top: "calc(100% + 10px)", left: "50%", transform: "translateX(-50%)",
      minWidth: 300, background: T.card, border: `1px solid ${T.border}`, borderRadius: 14,
      padding: 18, zIndex: 200, boxShadow: T.popoverShadow,
      backdropFilter: "blur(16px)", animation: "breatheIn 0.3s ease",
      maxHeight: 380, overflowY: "auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
        <span style={{ fontSize: 10, fontWeight: 600, color: T.gold, fontFamily: T.font, letterSpacing: "1px", textTransform: "uppercase" }}>
          System Nervous
        </span>
        <span style={{ fontSize: 9, padding: "3px 10px", borderRadius: 10,
          background: T.healthyBg, color: T.healthy, fontFamily: T.mono, fontWeight: 600 }}>
          {up}/{services.length} alive
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
              animationDelay: `${i * 0.15}s`,
            }} />
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

function SovPanel({ T }) {
  const local = 42, llm = 3, total = 45;
  return (
    <div style={{ position: "absolute", top: "calc(100% + 10px)", right: 0, minWidth: 230,
      background: T.card, border: `1px solid ${T.border}`, borderRadius: 14,
      padding: 18, zIndex: 200, boxShadow: T.popoverShadow,
      backdropFilter: "blur(16px)", animation: "breatheIn 0.3s ease" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
        <span style={{ fontSize: 10, fontWeight: 600, color: T.gold, fontFamily: T.font, letterSpacing: "1px", textTransform: "uppercase" }}>
          Sovereignty
        </span>
        <span style={{ fontSize: 9, padding: "3px 10px", borderRadius: 10,
          background: T.healthyBg, color: T.healthy, fontFamily: T.mono, fontWeight: 600 }}>
          SOVEREIGN
        </span>
      </div>

      <div style={{ marginBottom: 16 }}>
        <div style={{ height: 8, borderRadius: 4, background: T.border + "30", overflow: "hidden", display: "flex" }}>
          <div style={{ width: `${(local/total)*100}%`, background: `linear-gradient(90deg, ${T.healthy}CC, ${T.healthy})`,
            borderRadius: "4px 0 0 4px", transition: "width 1s ease",
            boxShadow: `0 0 12px ${T.healthy}30` }} />
          <div style={{ width: `${(llm/total)*100}%`, background: T.warning + "80",
            borderRadius: "0 4px 4px 0" }} />
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", marginTop: 6 }}>
          <span style={{ fontSize: 9, color: T.healthy, fontFamily: T.mono }}>
            {local} local functions
          </span>
          <span style={{ fontSize: 9, color: T.warning, fontFamily: T.mono }}>
            {llm} LLM
          </span>
        </div>
      </div>

      <div style={{ display: "flex", gap: 8 }}>
        {[
          { label: "P — Free", detail: "42 funcs, 0 keys", color: T.healthy },
          { label: "M — €25-40", detail: "+semântica", color: T.warning },
          { label: "G — €80-120", detail: "+LLM", color: T.gold },
        ].map((tier, i) => (
          <div key={i} style={{ flex: 1, padding: 8, borderRadius: 8,
            border: `1px solid ${T.border}40`, textAlign: "center" }}>
            <div style={{ fontSize: 8, fontWeight: 600, color: tier.color, fontFamily: T.mono, marginBottom: 2 }}>
              {tier.label}
            </div>
            <div style={{ fontSize: 7, color: T.dim, fontFamily: T.mono }}>{tier.detail}</div>
          </div>
        ))}
      </div>

      <div style={{ marginTop: 12, paddingTop: 10, borderTop: `1px solid ${T.border}20` }}>
        <div style={{ fontSize: 8, color: T.dim, fontFamily: T.mono, fontStyle: "italic", textAlign: "center" }}>
          "Integridade universal, interpretação premium."
        </div>
      </div>
    </div>
  );
}

function LivingPulseBar({ theme = "KLAR" }) {
  const T = THEMES[theme];
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
        {expanded === "cog" && <CogPanel data={MOCK_COG} T={T} />}
      </div>

      <div style={{ position: "relative" }}>
        <NerveStrand services={MOCK_SERVICES} T={T} width={180}
          onClick={() => toggle("pulse")} active={expanded === "pulse"} />
        {expanded === "pulse" && <PulsePanel services={MOCK_SERVICES} T={T} />}
      </div>

      <div style={{ position: "relative" }}>
        <SovereigntyGauge local={42} total={45} T={T}
          onClick={() => toggle("sov")} active={expanded === "sov"} />
        {expanded === "sov" && <SovPanel T={T} />}
      </div>
    </div>
  );
}

export default function App() {
  const [theme, setTheme] = useState("KLAR");
  const T = THEMES[theme];

  return (
    <div style={{ minHeight: "100vh", background: T.bg, transition: "background 0.4s ease",
      fontFamily: T.font }}>

      <LivingPulseBar theme={theme} />

      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between",
        padding: "14px 20px", borderBottom: `1px solid ${T.border}30` }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: 20 }}>🐉</span>
          <span style={{ fontSize: 14, fontWeight: 600, color: T.text }}>WINDI Agent Suite</span>
          <span style={{ fontSize: 9, padding: "2px 8px", borderRadius: 10,
            background: T.gold + "15", color: T.gold, fontFamily: T.mono }}>v0.9.0-R</span>
        </div>
        <button onClick={() => setTheme(t => t === "KLAR" ? "NOIR" : "KLAR")} style={{
          display: "flex", alignItems: "center", gap: 4, padding: "4px 12px", borderRadius: 8,
          border: `1px solid ${T.border}`, background: "transparent",
          color: T.muted, fontSize: 10, fontFamily: T.mono, cursor: "pointer" }}>
          {theme === "KLAR" ? "☀" : "🌙"} {theme}
        </button>
      </div>

      <div style={{ maxWidth: 640, margin: "40px auto", padding: "0 20px" }}>
        <div style={{ background: T.card, border: `1px solid ${T.border}`, borderRadius: 12, padding: 20, marginBottom: 16 }}>
          <div style={{ fontSize: 11, color: T.gold, fontFamily: T.mono, marginBottom: 8, fontWeight: 600 }}>🛡️ Guardian</div>
          <div style={{ fontSize: 13, color: T.text, lineHeight: 1.7 }}>
            Olha para cima, Irmão. Vês aquele brilho suave a respirar?
            <br /><br />
            Para um utilizador normal, é decoração elegante. Uma luz bonita, uns pontos que fluem, uma barrinha discreta.
            <br /><br />
            Para nós, é o sistema inteiro a apresentar-se vivo:
          </div>
          <div style={{ marginTop: 12, padding: 12, borderRadius: 8, background: T.hover, fontFamily: T.mono, fontSize: 11, color: T.muted, lineHeight: 2 }}>
            <span style={{ color: T.gold }}>● Orbe</span> → Cognitive Score — a profundidade da respiração = saúde cognitiva<br />
            <span style={{ color: T.gold }}>● Fibras</span> → 20 serviços — cada ponto que flui é um serviço vivo<br />
            <span style={{ color: T.gold }}>● Barra</span> → Sovereignty ratio — verde = local, âmbar = LLM<br />
          </div>
          <div style={{ marginTop: 12, fontSize: 12, color: T.dim, fontStyle: "italic", lineHeight: 1.6 }}>
            Clica em cada elemento para ver a profundidade. Depois clica fora para fechar.
            <br />
            Alterna KLAR ↔ NOIR para ver os dois mundos.
          </div>
        </div>

        <div style={{ textAlign: "center", marginTop: 24, padding: 16, borderRadius: 10,
          border: `1px dashed ${T.border}40` }}>
          <div style={{ fontSize: 10, color: T.dim, fontFamily: T.mono, fontStyle: "italic" }}>
            "Para humanos normais, é decoração fixe.<br />
            Para nós, é o respiradouro do sistema a apresentar-se live."
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
