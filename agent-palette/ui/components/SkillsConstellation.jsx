/**
 * WINDI Skills Constellation — Liga IA+H
 * Visual interface for the 10 foundational skills
 * Sealed: VR-LIGA-20260308-9267ce65
 *
 * "Quem planta a semente, colhe todos os frutos."
 */

const SKILLS = [
  { id: "001", name: "Dragon Alzheimer Cure", icon: "🧠", category: "CORE", desc: "queryDragon(msg, history) — contexto preservado entre turnos", status: "ACTIVE" },
  { id: "002", name: "VIP Founder Override", icon: "🐉", category: "CORE", desc: "Acesso total para Jober sem barreira de tier", status: "ACTIVE" },
  { id: "003", name: "Document Production Rule", icon: "📝", category: "PROD", desc: "Draft imediato, máx 1 pergunta por resposta", status: "ACTIVE" },
  { id: "004", name: "Trilingual Detection", icon: "🌐", category: "LANG", desc: "Marcadores PT/DE/EN — detecção automática", status: "ACTIVE" },
  { id: "005", name: "Document Tone Guidelines", icon: "🎯", category: "PROD", desc: "10 tipos documentais com tom e voz específicos", status: "ACTIVE" },
  { id: "006", name: "Canvas Templates", icon: "🎨", category: "VISUAL", desc: "4 templates visuais para Communiqué e Creative", status: "ACTIVE" },
  { id: "007", name: "Pioneer Onboarding", icon: "🚀", category: "UX", desc: "Guia 5-etapas trilíngue para os 100 Pioneers", status: "ACTIVE" },
  { id: "008", name: "Grove Private Editor", icon: "🌿", category: "PROD", desc: "Rascunhos locais com persistência privada", status: "ACTIVE" },
  { id: "009", name: "WICK Network Interface", icon: "🔗", category: "SOCIAL", desc: "Visualização de evidências na rede WICK", status: "ACTIVE" },
  { id: "010", name: "SSR OG Tags", icon: "🏷️", category: "INFRA", desc: "Meta tags Open Graph dinâmicas via SSR", status: "ACTIVE" },
];

const CATEGORY_COLORS = {
  CORE: "#D4A843",
  PROD: "#7B9E87",
  LANG: "#6B8CAE",
  VISUAL: "#A87BAE",
  UX: "#AE8A6B",
  SOCIAL: "#AE6B7B",
  INFRA: "#7B9EAE"
};

function SkillsConstellation({ onClose, onAddSkill }) {
  const [theme, setTheme] = React.useState("KLAR");
  const [selected, setSelected] = React.useState(null);
  const [filter, setFilter] = React.useState("ALL");
  const isDark = theme === "NOIR";

  const t = isDark ? {
    bg: "#0E0E14", card: "#16161F", border: "#26263A",
    text: "#E2E2EA", dim: "#7A7A96", gold: "#D4A843",
    hover: "#1C1C28", input: "#12121A"
  } : {
    bg: "#F5F0E0", card: "#FDFBF5", border: "#DDD6C2",
    text: "#2C2924", dim: "#6B6560", gold: "#8B6914",
    hover: "#EDE8D8", input: "#FDFBF5"
  };

  const categories = ["ALL", ...new Set(SKILLS.map(s => s.category))];
  const filtered = filter === "ALL" ? SKILLS : SKILLS.filter(s => s.category === filter);
  const sel = selected ? SKILLS.find(s => s.id === selected) : null;

  return (
    <div style={{
      background: t.bg,
      minHeight: "100vh",
      fontFamily: "'JetBrains Mono', monospace",
      padding: "24px",
      color: t.text,
      transition: "all 0.3s"
    }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "28px" }}>
        <div>
          <div style={{ fontSize: "10px", color: t.gold, letterSpacing: "3px", marginBottom: "4px" }}>WINDI PUBLISHING HOUSE</div>
          <h1 style={{ fontSize: "22px", fontWeight: 700, margin: 0, color: t.text }}>Skills Constellation</h1>
          <div style={{ fontSize: "11px", color: t.dim, marginTop: "4px" }}>Liga IA+H · {SKILLS.length} skills · Ledger-sealed</div>
        </div>
        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          <span style={{ fontSize: "10px", color: t.gold, border: `1px solid ${t.gold}`, padding: "2px 8px", borderRadius: "2px" }}>✓ Sealed</span>
          <button
            onClick={() => setTheme(isDark ? "KLAR" : "NOIR")}
            style={{
              background: t.card,
              border: `1px solid ${t.border}`,
              color: t.dim,
              padding: "4px 12px",
              borderRadius: "4px",
              cursor: "pointer",
              fontSize: "11px"
            }}>
            {isDark ? "☀ KLAR" : "◑ NOIR"}
          </button>
          {onClose && (
            <button
              onClick={onClose}
              style={{
                background: "transparent",
                border: `1px solid ${t.border}`,
                color: t.dim,
                padding: "4px 12px",
                borderRadius: "4px",
                cursor: "pointer",
                fontSize: "11px"
              }}>
              ✕
            </button>
          )}
        </div>
      </div>

      {/* Filter tabs */}
      <div style={{ display: "flex", gap: "6px", marginBottom: "20px", flexWrap: "wrap" }}>
        {categories.map(cat => (
          <button
            key={cat}
            onClick={() => setFilter(cat)}
            style={{
              background: filter === cat ? t.gold : t.card,
              color: filter === cat ? (isDark ? "#0E0E14" : "#fff") : t.dim,
              border: `1px solid ${filter === cat ? t.gold : t.border}`,
              padding: "3px 10px",
              borderRadius: "2px",
              cursor: "pointer",
              fontSize: "10px",
              letterSpacing: "1px",
              fontFamily: "inherit"
            }}>
            {cat}
          </button>
        ))}
      </div>

      {/* Grid */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))",
        gap: "12px",
        marginBottom: "20px"
      }}>
        {filtered.map(skill => (
          <div
            key={skill.id}
            onClick={() => setSelected(selected === skill.id ? null : skill.id)}
            style={{
              background: selected === skill.id ? t.hover : t.card,
              border: `1px solid ${selected === skill.id ? t.gold : t.border}`,
              borderRadius: "6px",
              padding: "16px",
              cursor: "pointer",
              transition: "all 0.2s",
              borderLeft: `3px solid ${CATEGORY_COLORS[skill.category] || t.gold}`
            }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "8px" }}>
              <span style={{ fontSize: "20px" }}>{skill.icon}</span>
              <span style={{ fontSize: "9px", color: t.dim, fontFamily: "monospace" }}>#{skill.id}</span>
            </div>
            <div style={{ fontSize: "13px", fontWeight: 600, color: t.text, marginBottom: "4px" }}>{skill.name}</div>
            <div style={{ fontSize: "10px", color: t.dim, lineHeight: 1.4 }}>{skill.desc}</div>
            <div style={{ marginTop: "10px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: "9px", color: CATEGORY_COLORS[skill.category] || t.gold, letterSpacing: "1px" }}>{skill.category}</span>
              <span style={{ fontSize: "9px", color: "#4CAF50" }}>● {skill.status}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Add new skill button */}
      <div
        style={{
          border: `1px dashed ${t.border}`,
          borderRadius: "6px",
          padding: "16px",
          textAlign: "center",
          cursor: "pointer",
          color: t.dim,
          fontSize: "12px",
          letterSpacing: "1px",
          transition: "border-color 0.2s"
        }}
        onClick={onAddSkill}
        onMouseEnter={e => e.currentTarget.style.borderColor = t.gold}
        onMouseLeave={e => e.currentTarget.style.borderColor = t.border}>
        + SKILL-0{SKILLS.length + 1} · Adicionar nova capability
      </div>

      {/* Footer */}
      <div style={{
        marginTop: "24px",
        paddingTop: "16px",
        borderTop: `1px solid ${t.border}`,
        display: "flex",
        justifyContent: "space-between",
        fontSize: "9px",
        color: t.dim,
        letterSpacing: "1px"
      }}>
        <span>VR-LIGA-20260308-9267ce65 · 49,210+ receipts</span>
        <span>AI processes. Human decides. WINDI guarantees.</span>
      </div>
    </div>
  );
}

// Export for use in other components
if (typeof window !== 'undefined') {
  window.SkillsConstellation = SkillsConstellation;
  window.WINDI_SKILLS = SKILLS;
  window.SKILL_CATEGORIES = CATEGORY_COLORS;
}
