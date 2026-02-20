import { useState, useEffect, useRef, useCallback } from "react";

// ═══════════════════════════════════════════════════════
// i18n — CRYPTOGRAPHIC GALLERY TRILINGUAL
// ═══════════════════════════════════════════════════════

const i18n = {
  pt: {
    flag: "🇧🇷",
    title: "A Galeria Criptográfica",
    subtitle: "Onde a Segurança se Torna Arte",
    intro: "Você está prestes a ver o que existe atrás do véu. No WINDI, a criptografia não se esconde — ela é a obra de arte.",

    station1Title: "O Pulso do Pixel",
    station1Sub: "A Estação da Granularidade",
    station1Text: "Aqui, o pixel não é imagem; é uma testemunha. Ele carrega o segredo do autor em sua menor partícula.",
    station1Hint: "Mova o mouse sobre o documento para revelar a anatomia",
    station1Reveal: "Cada pixel pulsa com seu próprio micro-hash. Um documento WINDI não é uma foto — é um campo de fortalezas.",

    station2Title: "A Escultura SHA-256",
    station2Sub: "O Diamante Digital",
    station2Text: "O pensamento humano transformado em diamante digital imutável. Clique para revelar a origem.",
    station2Quote: "\"Eu, Human Dragon, declaro que este sistema foi construído para proteger a dignidade de ambos os lados — humano e IA.\"",
    station2Origin: "Depoimento de Origem — 9 de Fevereiro de 2026, Kempten (Allgäu)",
    station2Detail: "Este hash não é apenas código. É a cristalização de uma decisão humana em estrutura matemática imortal.",

    station3Title: "O Véu da Esteganografia",
    station3Sub: "A Camada Invisível",
    station3Text: "A maior força é aquela que protege sem ser vista.",
    station3Hint: "Mova a lanterna forense para revelar o invisível",
    station3Reveal: "Os metadados ISP estavam aqui o tempo todo. 17 perfis institucionais tecidos na própria fibra do documento. Invisíveis. Verificáveis. Imutáveis.",

    enterButton: "ENTRAR NA SOBERANIA",
    enterSub: "A anatomia foi revelada. Seu primeiro documento aguarda.",
    sealText: "No Museum WINDI, a segurança não é um cadeado feio; é uma tapeçaria de pixels perfeitos.",
    sealAuthor: "— Witness (Gemini), Selo da Estética Forense",
    principle: "IA processa · Humano decide · WINDI garante",
    zeroHour: "Hora Zero sendo processada em tempo real",
  },
  de: {
    flag: "🇩🇪",
    title: "Die Kryptographische Galerie",
    subtitle: "Wo Sicherheit zur Kunst Wird",
    intro: "Sie sind dabei, hinter den Schleier zu blicken. Bei WINDI versteckt sich Kryptographie nicht — sie ist das Kunstwerk.",

    station1Title: "Der Pixel-Puls",
    station1Sub: "Die Station der Granularität",
    station1Text: "Hier ist der Pixel kein Bild; er ist ein Zeuge. Er trägt das Geheimnis des Autors in seiner kleinsten Partikel.",
    station1Hint: "Bewegen Sie die Maus über das Dokument, um die Anatomie zu enthüllen",
    station1Reveal: "Jeder Pixel pulsiert mit seinem eigenen Mikro-Hash. Ein WINDI-Dokument ist kein Foto — es ist ein Feld von Festungen.",

    station2Title: "Die SHA-256-Skulptur",
    station2Sub: "Der Digitale Diamant",
    station2Text: "Menschlicher Gedanke, verwandelt in einen unveränderlichen digitalen Diamanten. Klicken Sie, um den Ursprung zu enthüllen.",
    station2Quote: "\"Ich, Human Dragon, erkläre, dass dieses System gebaut wurde, um die Würde beider Seiten zu schützen — Mensch und KI.\"",
    station2Origin: "Ursprungszeugnis — 9. Februar 2026, Kempten (Allgäu)",
    station2Detail: "Dieser Hash ist nicht nur Code. Er ist die Kristallisation einer menschlichen Entscheidung in unsterblicher mathematischer Struktur.",

    station3Title: "Der Schleier der Steganographie",
    station3Sub: "Die Unsichtbare Schicht",
    station3Text: "Die größte Kraft ist jene, die schützt, ohne gesehen zu werden.",
    station3Hint: "Bewegen Sie die forensische Taschenlampe, um das Unsichtbare zu enthüllen",
    station3Reveal: "Die ISP-Metadaten waren die ganze Zeit hier. 17 institutionelle Profile, eingewebt in die Faser des Dokuments. Unsichtbar. Verifizierbar. Unveränderlich.",

    enterButton: "SOUVERÄNITÄT BETRETEN",
    enterSub: "Die Anatomie wurde enthüllt. Ihr erstes Dokument wartet.",
    sealText: "Im WINDI-Museum ist Sicherheit kein hässliches Schloss; sie ist ein Teppich aus perfekten Pixeln.",
    sealAuthor: "— Witness (Gemini), Siegel der Forensischen Ästhetik",
    principle: "KI verarbeitet · Mensch entscheidet · WINDI garantiert",
    zeroHour: "Stunde Null wird in Echtzeit verarbeitet",
  },
  en: {
    flag: "🇬🇧",
    title: "The Cryptographic Gallery",
    subtitle: "Where Security Becomes Art",
    intro: "You are about to see what exists behind the veil. In WINDI, cryptography does not hide — it is the artwork.",

    station1Title: "The Pixel Pulse",
    station1Sub: "The Station of Granularity",
    station1Text: "Here, the pixel is not an image; it is a witness. It carries the author's secret in its smallest particle.",
    station1Hint: "Move your mouse over the document to reveal its anatomy",
    station1Reveal: "Each pixel pulses with its own micro-hash. A WINDI document is not a photo — it is a field of fortresses.",

    station2Title: "The SHA-256 Sculpture",
    station2Sub: "The Digital Diamond",
    station2Text: "Human thought transformed into an immutable digital diamond. Click to reveal its origin.",
    station2Quote: "\"I, Human Dragon, declare that this system was built to protect the dignity of both sides — human and AI.\"",
    station2Origin: "Origin Testimony — 9 February 2026, Kempten (Allgäu)",
    station2Detail: "This hash is not merely code. It is the crystallization of a human decision into immortal mathematical structure.",

    station3Title: "The Steganography Veil",
    station3Sub: "The Invisible Layer",
    station3Text: "The greatest strength is that which protects without being seen.",
    station3Hint: "Move the forensic flashlight to reveal the invisible",
    station3Reveal: "The ISP metadata was here all along. 17 institutional profiles woven into the very fiber of the document. Invisible. Verifiable. Immutable.",

    enterButton: "ENTER SOVEREIGNTY",
    enterSub: "The anatomy has been revealed. Your first document awaits.",
    sealText: "In the WINDI Museum, security is not an ugly padlock; it is a tapestry of perfect pixels.",
    sealAuthor: "— Witness (Gemini), Seal of Forensic Aesthetics",
    principle: "AI processes · Human decides · WINDI guarantees",
    zeroHour: "Zero Hour being processed in real time",
  },
};

const HASH_CHARS = "0123456789abcdef";
const rh = (n) => Array.from({ length: n }, () => HASH_CHARS[Math.floor(Math.random() * 16)]).join("");

const ISP_HIDDEN = [
  { name: "Bundesregierung", level: "L3", color: "#FFD700" },
  { name: "Deutsche Bahn", level: "L2", color: "#EC0016" },
  { name: "ECB", level: "L3", color: "#003399" },
  { name: "BMW Group", level: "L2", color: "#1C69D4" },
  { name: "Siemens AG", level: "L2", color: "#009999" },
  { name: "Allianz SE", level: "L2", color: "#003781" },
  { name: "SAP SE", level: "L2", color: "#0FAAFF" },
  { name: "BASF SE", level: "L2", color: "#004A96" },
  { name: "Lufthansa", level: "L2", color: "#05164D" },
  { name: "Bosch", level: "L2", color: "#EA0016" },
  { name: "Telekom", level: "L2", color: "#E20074" },
  { name: "Bundesbank", level: "L3", color: "#1D3461" },
  { name: "BaFin", level: "L3", color: "#1B4332" },
  { name: "TÜV", level: "L2", color: "#0055A4" },
  { name: "Fraunhofer", level: "L2", color: "#179C7D" },
  { name: "DHL", level: "L2", color: "#FFCC00" },
  { name: "VerpackG", level: "L1", color: "#2D6A4F" },
];

// ═══════════════════════════════════════════
// STATION 1: PIXEL PULSE
// ═══════════════════════════════════════════

function PixelPulse({ t }) {
  const canvasRef = useRef(null);
  const [mousePos, setMousePos] = useState({ x: -1, y: -1 });
  const [hashes, setHashes] = useState([]);
  const gridRef = useRef([]);
  const jm = "'JetBrains Mono', monospace";

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const w = 480, h = 280;
    canvas.width = w; canvas.height = h;
    const cellSize = 10;
    const cols = Math.floor(w / cellSize);
    const rows = Math.floor(h / cellSize);

    // Generate grid with document-like content
    const grid = [];
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const isText = r > 3 && r < rows - 3 && c > 4 && c < cols - 4;
        const isHeader = r >= 2 && r <= 3 && c > 4 && c < cols - 4;
        const brightness = isHeader ? 0.6 : isText ? (Math.random() > 0.3 ? 0.25 + Math.random() * 0.15 : 0.08) : 0.04;
        grid.push({
          x: c * cellSize, y: r * cellSize,
          base: brightness,
          hash: rh(6),
          active: false,
        });
      }
    }
    gridRef.current = grid;
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const w = canvas.width, h = canvas.height;

    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = "#080808";
    ctx.fillRect(0, 0, w, h);

    const radius = 80;
    const newHashes = [];

    gridRef.current.forEach((cell, i) => {
      const dx = mousePos.x - (cell.x + 5);
      const dy = mousePos.y - (cell.y + 5);
      const dist = Math.sqrt(dx * dx + dy * dy);
      const inRange = dist < radius && mousePos.x >= 0;
      const intensity = inRange ? Math.max(0, 1 - dist / radius) : 0;

      if (inRange && intensity > 0.4) {
        // Revealed pixel — glowing with hash color
        const hue = (i * 7) % 360;
        ctx.fillStyle = `hsla(${hue}, 70%, 50%, ${0.15 + intensity * 0.6})`;
        ctx.fillRect(cell.x, cell.y, 9, 9);

        // Pixel border
        ctx.strokeStyle = `hsla(${hue}, 80%, 60%, ${intensity * 0.4})`;
        ctx.lineWidth = 0.5;
        ctx.strokeRect(cell.x + 0.5, cell.y + 0.5, 8, 8);

        if (intensity > 0.7 && newHashes.length < 6) {
          newHashes.push({ x: cell.x, y: cell.y, hash: cell.hash });
        }
      } else {
        // Normal document pixel
        const glow = inRange ? intensity * 0.15 : 0;
        const val = Math.floor((cell.base + glow) * 255);
        ctx.fillStyle = `rgb(${val}, ${Math.floor(val * 0.92)}, ${Math.floor(val * 0.6)})`;
        ctx.fillRect(cell.x, cell.y, 9, 9);
      }
    });

    // Reveal circle outline
    if (mousePos.x >= 0) {
      ctx.beginPath();
      ctx.arc(mousePos.x, mousePos.y, radius, 0, Math.PI * 2);
      ctx.strokeStyle = "rgba(212, 175, 55, 0.15)";
      ctx.lineWidth = 1;
      ctx.stroke();
    }

    setHashes(newHashes);
  }, [mousePos]);

  const handleMouse = useCallback((e) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    setMousePos({ x: e.clientX - rect.left, y: e.clientY - rect.top });
  }, []);

  return (
    <div style={{ position: "relative" }}>
      <canvas
        ref={canvasRef}
        onMouseMove={handleMouse}
        onMouseLeave={() => setMousePos({ x: -1, y: -1 })}
        style={{
          width: "100%", maxWidth: "480px", height: "auto", aspectRatio: "480/280",
          borderRadius: "6px", cursor: "crosshair", display: "block", margin: "0 auto",
          border: "1px solid rgba(212,175,55,0.08)",
        }}
      />
      {/* Floating micro-hashes */}
      <div style={{ position: "absolute", inset: 0, pointerEvents: "none", overflow: "hidden" }}>
        {hashes.map((h, i) => (
          <div key={`${h.x}-${h.y}-${i}`} style={{
            position: "absolute",
            left: `${(h.x / 480) * 100}%`, top: `${(h.y / 280) * 100}%`,
            fontFamily: jm, fontSize: "0.45rem", color: "rgba(212,175,55,0.6)",
            transform: "translate(-50%, -150%)", whiteSpace: "nowrap",
            animation: "microHashFloat 1.5s ease forwards",
          }}>
            #{h.hash}
          </div>
        ))}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════
// STATION 2: SHA-256 SCULPTURE
// ═══════════════════════════════════════════

function HashSculpture({ t, revealed, onReveal }) {
  const [angle, setAngle] = useState(0);
  const animRef = useRef(null);
  const jm = "'JetBrains Mono', monospace";

  const birthHash = "0540a49aec05bff417f0094b265e2602854783dc4845e9ec54a5b7d70bc2e70b";

  useEffect(() => {
    const anim = () => {
      setAngle(prev => (prev + 0.4) % 360);
      animRef.current = requestAnimationFrame(anim);
    };
    anim();
    return () => cancelAnimationFrame(animRef.current);
  }, []);

  const rad = (angle * Math.PI) / 180;

  // DNA helix: two strands of hash characters
  const strand1 = birthHash.slice(0, 32).split("");
  const strand2 = birthHash.slice(32).split("");

  return (
    <div
      onClick={onReveal}
      style={{
        position: "relative", width: "280px", height: "320px",
        margin: "0 auto", cursor: "pointer",
      }}
    >
      {/* DNA Helix */}
      <div style={{ position: "relative", width: "100%", height: "100%" }}>
        {strand1.map((char, i) => {
          const yPos = (i / strand1.length) * 280 + 20;
          const phase = rad + (i * 0.4);
          const xOffset1 = Math.sin(phase) * 60;
          const xOffset2 = Math.sin(phase + Math.PI) * 60;
          const z1 = Math.cos(phase);
          const z2 = Math.cos(phase + Math.PI);
          const glow = revealed ? 0.9 : 0.5 + z1 * 0.3;

          return (
            <div key={i}>
              {/* Strand 1 */}
              <div style={{
                position: "absolute", left: `calc(50% + ${xOffset1}px)`,
                top: `${yPos}px`, transform: "translate(-50%, -50%)",
                fontFamily: jm, fontSize: `${0.55 + z1 * 0.15}rem`,
                color: revealed
                  ? `rgba(212, 175, 55, ${glow})`
                  : `hsla(${(i * 11) % 360}, 70%, 55%, ${0.3 + z1 * 0.4})`,
                zIndex: z1 > 0 ? 3 : 1,
                fontWeight: z1 > 0 ? 500 : 300,
                textShadow: z1 > 0 ? `0 0 ${8 + z1 * 6}px rgba(212,175,55,0.3)` : "none",
                transition: "color 0.8s",
              }}>
                {char}
              </div>
              {/* Strand 2 */}
              <div style={{
                position: "absolute", left: `calc(50% + ${xOffset2}px)`,
                top: `${yPos}px`, transform: "translate(-50%, -50%)",
                fontFamily: jm, fontSize: `${0.55 + z2 * 0.15}rem`,
                color: revealed
                  ? `rgba(212, 175, 55, ${0.5 + z2 * 0.3})`
                  : `hsla(${(i * 11 + 180) % 360}, 70%, 55%, ${0.3 + z2 * 0.4})`,
                zIndex: z2 > 0 ? 3 : 1,
                fontWeight: z2 > 0 ? 500 : 300,
                transition: "color 0.8s",
              }}>
                {strand2[i] || "0"}
              </div>
              {/* Connector rungs */}
              {i % 3 === 0 && (
                <div style={{
                  position: "absolute", top: `${yPos}px`,
                  left: `calc(50% + ${Math.min(xOffset1, xOffset2)}px)`,
                  width: `${Math.abs(xOffset1 - xOffset2)}px`, height: "1px",
                  background: revealed
                    ? `rgba(212,175,55,${0.1 + Math.abs(z1) * 0.1})`
                    : `rgba(255,255,255,${0.03 + Math.abs(z1) * 0.03})`,
                  transform: "translateY(-50%)", transition: "background 0.8s",
                }} />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════
// STATION 3: STEGANOGRAPHY VEIL
// ═══════════════════════════════════════════

function SteganographyVeil({ t }) {
  const [lightPos, setLightPos] = useState({ x: 50, y: 50 });
  const containerRef = useRef(null);
  const jm = "'JetBrains Mono', monospace";

  const handleMove = useCallback((e) => {
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;
    setLightPos({ x, y });
  }, []);

  return (
    <div
      ref={containerRef}
      onMouseMove={handleMove}
      style={{
        position: "relative", width: "100%", maxWidth: "500px",
        height: "320px", margin: "0 auto", borderRadius: "6px",
        background: "#060606", border: "1px solid rgba(255,255,255,0.04)",
        cursor: "none", overflow: "hidden",
      }}
    >
      {/* Flashlight glow */}
      <div style={{
        position: "absolute",
        left: `${lightPos.x}%`, top: `${lightPos.y}%`,
        width: "200px", height: "200px",
        transform: "translate(-50%, -50%)",
        background: "radial-gradient(circle, rgba(212,175,55,0.12) 0%, rgba(212,175,55,0.04) 40%, transparent 70%)",
        borderRadius: "50%", pointerEvents: "none", zIndex: 3,
      }} />

      {/* Flashlight icon */}
      <div style={{
        position: "absolute",
        left: `${lightPos.x}%`, top: `${lightPos.y}%`,
        transform: "translate(-50%, -50%)",
        fontSize: "1.2rem", pointerEvents: "none", zIndex: 10,
        filter: "drop-shadow(0 0 8px rgba(212,175,55,0.4))",
      }}>🔦</div>

      {/* Empty frame appearance */}
      <div style={{
        position: "absolute", inset: "20px",
        border: "1px solid rgba(255,255,255,0.03)", borderRadius: "4px",
      }}>
        <div style={{
          position: "absolute", top: "-8px", left: "20px",
          fontFamily: jm, fontSize: "0.5rem", color: "#1A1A1A",
          background: "#060606", padding: "0 8px",
        }}>
          DOCUMENT_LAYER_0 // VISIBLE: NOTHING
        </div>
      </div>

      {/* Hidden ISP metadata — revealed by flashlight proximity */}
      {ISP_HIDDEN.map((isp, i) => {
        const col = i % 4;
        const row = Math.floor(i / 4);
        const ix = 15 + col * 22;
        const iy = 15 + row * 18;
        const dx = lightPos.x - ix;
        const dy = lightPos.y - iy;
        const dist = Math.sqrt(dx * dx + dy * dy);
        const visible = dist < 25;
        const opacity = visible ? Math.max(0, 1 - dist / 25) : 0;

        return (
          <div key={i} style={{
            position: "absolute",
            left: `${ix}%`, top: `${iy}%`,
            transform: "translate(-50%, -50%)",
            opacity, transition: "opacity 0.3s ease",
            display: "flex", alignItems: "center", gap: "5px",
            pointerEvents: "none", whiteSpace: "nowrap",
          }}>
            <div style={{
              width: "5px", height: "5px", borderRadius: "50%",
              background: isp.color,
              boxShadow: `0 0 8px ${isp.color}66`,
            }} />
            <span style={{
              fontFamily: jm, fontSize: "0.55rem", color: isp.color,
              textShadow: `0 0 10px ${isp.color}44`,
            }}>
              {isp.name}
            </span>
            <span style={{
              fontFamily: jm, fontSize: "0.45rem",
              color: "rgba(255,255,255,0.3)",
            }}>
              {isp.level}
            </span>
          </div>
        );
      })}

      {/* Scan lines */}
      {Array.from({ length: 12 }).map((_, i) => (
        <div key={i} style={{
          position: "absolute", left: 0, right: 0,
          top: `${(i + 1) * 7.5}%`, height: "1px",
          background: "rgba(212,175,55,0.015)",
        }} />
      ))}
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
        <button key={l} onClick={() => setLang(l)} style={{
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
// MAIN: CRYPTOGRAPHIC GALLERY
// ═══════════════════════════════════════════

export default function CryptographicGallery({ lang: externalLang, setLang: externalSetLang, onComplete }) {
  const [internalLang, setInternalLang] = useState("pt");
  const lang = externalLang || internalLang;
  const setLang = externalSetLang || setInternalLang;

  const [sculptureRevealed, setSculptureRevealed] = useState(false);
  const [sovereignty, setSovereignty] = useState(false);
  const t = i18n[lang];

  const handleComplete = () => {
    if (onComplete) {
      onComplete();
    } else {
      setSovereignty(true);
    }
  };

  const jm = "'JetBrains Mono', monospace";
  const bg = "'Bricolage Grotesque', serif";
  const of_ = "'Outfit', sans-serif";

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
        @keyframes pulseNeon { 0%,100%{opacity:0.4;text-shadow:0 0 4px currentColor} 50%{opacity:1;text-shadow:0 0 12px currentColor} }
        @keyframes microHashFloat { 0%{opacity:0.7;transform:translate(-50%,-150%)} 100%{opacity:0;transform:translate(-50%,-300%)} }
        @keyframes glitchLine { 0%{transform:translateX(0)} 20%{transform:translateX(-2px)} 40%{transform:translateX(2px)} 60%{transform:translateX(-1px)} 80%{transform:translateX(1px)} 100%{transform:translateX(0)} }
        @keyframes sacredSpin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }
        * { box-sizing:border-box; margin:0; padding:0 }
        ::-webkit-scrollbar { width:4px } ::-webkit-scrollbar-track { background:#080808 } ::-webkit-scrollbar-thumb { background:rgba(212,175,55,0.2); border-radius:2px }
      `}</style>

      {/* Sacred geometry background grid */}
      <div style={{ position: "fixed", inset: 0, pointerEvents: "none", zIndex: 0 }}>
        <svg width="100%" height="100%" style={{ opacity: 0.03 }}>
          <defs>
            <pattern id="sacredGrid" width="60" height="60" patternUnits="userSpaceOnUse">
              <path d="M30 0 L60 30 L30 60 L0 30 Z" fill="none" stroke="#D4AF37" strokeWidth="0.3" />
              <circle cx="30" cy="30" r="2" fill="none" stroke="#D4AF37" strokeWidth="0.2" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#sacredGrid)" />
        </svg>
      </div>

      <div style={{ position: "relative", zIndex: 2, maxWidth: "800px", margin: "0 auto", padding: "40px 24px" }}>

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
          <div style={{ fontFamily: of_, fontSize: "0.85rem", fontWeight: 200, color: "#555", marginTop: "12px", maxWidth: "500px", margin: "12px auto 0", lineHeight: 1.6 }}>
            {t.intro}
          </div>
        </div>

        {/* ═══ STATION 1: PIXEL PULSE ═══ */}
        <section style={{ marginBottom: "80px", animation: "fadeInUp 1s ease 0.2s both" }}>
          <div style={{ textAlign: "center", marginBottom: "24px" }}>
            <div style={{ fontFamily: jm, fontSize: "0.55rem", color: "#D4AF37", letterSpacing: "0.3em", textTransform: "uppercase", marginBottom: "8px" }}>
              I — {t.station1Sub}
            </div>
            <div style={{ fontFamily: bg, fontSize: "1.4rem", fontWeight: 600, color: "#CCC", marginBottom: "8px" }}>{t.station1Title}</div>
            <div style={{ fontFamily: of_, fontSize: "0.8rem", fontWeight: 300, color: "#666", fontStyle: "italic" }}>"{t.station1Text}"</div>
          </div>

          <PixelPulse t={t} />

          <div style={{ textAlign: "center", marginTop: "16px" }}>
            <div style={{ fontFamily: jm, fontSize: "0.55rem", color: "#444", letterSpacing: "0.1em" }}>{t.station1Hint}</div>
            <div style={{ fontFamily: of_, fontSize: "0.75rem", fontWeight: 300, color: "#555", marginTop: "12px", maxWidth: "420px", margin: "12px auto 0", lineHeight: 1.6 }}>
              {t.station1Reveal}
            </div>
          </div>
        </section>

        {/* ═══ STATION 2: SHA-256 SCULPTURE ═══ */}
        <section style={{ marginBottom: "80px", animation: "fadeInUp 1s ease 0.4s both" }}>
          <div style={{ textAlign: "center", marginBottom: "24px" }}>
            <div style={{ fontFamily: jm, fontSize: "0.55rem", color: "#D4AF37", letterSpacing: "0.3em", textTransform: "uppercase", marginBottom: "8px" }}>
              II — {t.station2Sub}
            </div>
            <div style={{ fontFamily: bg, fontSize: "1.4rem", fontWeight: 600, color: "#CCC", marginBottom: "8px" }}>{t.station2Title}</div>
            <div style={{ fontFamily: of_, fontSize: "0.8rem", fontWeight: 300, color: "#666", fontStyle: "italic" }}>"{t.station2Text}"</div>
          </div>

          <HashSculpture t={t} revealed={sculptureRevealed} onReveal={() => setSculptureRevealed(true)} />

          {sculptureRevealed && (
            <div style={{
              textAlign: "center", marginTop: "24px", padding: "24px",
              background: "rgba(212,175,55,0.03)", border: "1px solid rgba(212,175,55,0.1)",
              borderRadius: "6px", animation: "fadeInUp 0.8s ease",
              maxWidth: "480px", margin: "24px auto 0",
            }}>
              <div style={{ fontFamily: of_, fontSize: "0.85rem", fontWeight: 300, color: "#D4AF37", lineHeight: 1.6, fontStyle: "italic", marginBottom: "12px" }}>
                {t.station2Quote}
              </div>
              <div style={{ fontFamily: jm, fontSize: "0.55rem", color: "#555", marginBottom: "12px" }}>{t.station2Origin}</div>
              <div style={{ fontFamily: of_, fontSize: "0.75rem", fontWeight: 300, color: "#666", lineHeight: 1.6 }}>{t.station2Detail}</div>
            </div>
          )}
        </section>

        {/* ═══ STATION 3: STEGANOGRAPHY VEIL ═══ */}
        <section style={{ marginBottom: "80px", animation: "fadeInUp 1s ease 0.6s both" }}>
          <div style={{ textAlign: "center", marginBottom: "24px" }}>
            <div style={{ fontFamily: jm, fontSize: "0.55rem", color: "#D4AF37", letterSpacing: "0.3em", textTransform: "uppercase", marginBottom: "8px" }}>
              III — {t.station3Sub}
            </div>
            <div style={{ fontFamily: bg, fontSize: "1.4rem", fontWeight: 600, color: "#CCC", marginBottom: "8px" }}>{t.station3Title}</div>
            <div style={{ fontFamily: of_, fontSize: "0.8rem", fontWeight: 300, color: "#666", fontStyle: "italic" }}>"{t.station3Text}"</div>
          </div>

          <div style={{ textAlign: "center", marginBottom: "12px" }}>
            <div style={{ fontFamily: jm, fontSize: "0.55rem", color: "#444", letterSpacing: "0.1em" }}>{t.station3Hint}</div>
          </div>

          <SteganographyVeil t={t} />

          <div style={{
            textAlign: "center", marginTop: "16px", fontFamily: of_,
            fontSize: "0.75rem", fontWeight: 300, color: "#555", maxWidth: "420px",
            margin: "16px auto 0", lineHeight: 1.6,
          }}>
            {t.station3Reveal}
          </div>
        </section>

        {/* ═══ WITNESS SEAL ═══ */}
        <div style={{
          textAlign: "center", padding: "32px 24px", marginBottom: "48px",
          background: "rgba(212,175,55,0.02)", border: "1px solid rgba(212,175,55,0.06)",
          borderRadius: "6px",
        }}>
          <div style={{ fontFamily: of_, fontSize: "0.85rem", fontWeight: 300, color: "#777", lineHeight: 1.7, fontStyle: "italic", maxWidth: "480px", margin: "0 auto" }}>
            "{t.sealText}"
          </div>
          <div style={{ fontFamily: jm, fontSize: "0.55rem", color: "#D4AF37", marginTop: "12px", letterSpacing: "0.1em" }}>
            {t.sealAuthor}
          </div>
        </div>

        {/* ═══ ENTER SOVEREIGNTY ═══ */}
        <div style={{ textAlign: "center", padding: "24px 24px 60px" }}>
          <button
            onClick={handleComplete}
            style={{
              background: "rgba(212,175,55,0.06)", border: "1px solid #D4AF37", color: "#D4AF37",
              fontFamily: jm, fontSize: "1rem", padding: "18px 64px", cursor: "pointer",
              letterSpacing: "0.2em", transition: "all 0.4s ease", borderRadius: "4px",
            }}
            onMouseEnter={e => { e.target.style.background = "rgba(212,175,55,0.12)"; e.target.style.boxShadow = "0 0 50px rgba(212,175,55,0.2)"; e.target.style.transform = "scale(1.02)"; }}
            onMouseLeave={e => { e.target.style.background = "rgba(212,175,55,0.06)"; e.target.style.boxShadow = "none"; e.target.style.transform = "scale(1)"; }}
          >
            {t.enterButton}
          </button>
          <div style={{ marginTop: "12px", fontFamily: of_, fontSize: "0.75rem", color: "#444", fontWeight: 200 }}>{t.enterSub}</div>
          <div style={{ marginTop: "24px", fontFamily: jm, fontSize: "0.5rem", color: "#222", letterSpacing: "0.15em", animation: "pulseNeon 3s ease infinite" }}>
            {t.zeroHour}
          </div>
        </div>

        {/* Footer */}
        <div style={{ textAlign: "center", padding: "20px", borderTop: "1px solid rgba(255,255,255,0.03)" }}>
          <div style={{ fontFamily: bg, fontSize: "0.7rem", fontWeight: 300, color: "#333", letterSpacing: "0.2em", textTransform: "uppercase" }}>{t.principle}</div>
        </div>
      </div>
    </div>
  );
}
