import { useState, useEffect, useCallback } from "react";

// ─── TRILINGUAL CONTENT ────────────────────────────────────────
const T = {
  header: { de: "WINDI AGENT CÓRTEX", en: "WINDI AGENT CORTEX", pt: "WINDI AGENT CÓRTEX" },
  subtitle: { de: "Verfassungs-DNA · Lebender Baum", en: "Constitutional DNA · Living Tree", pt: "DNA Constitucional · Árvore Viva" },
  principle: { de: "KI verarbeitet · Mensch entscheidet · WINDI garantiert", en: "AI processes · Human decides · WINDI guarantees", pt: "IA processa · Humano decide · WINDI garante" },
  tabs: {
    tree: { de: "🌳 Baum", en: "🌳 Tree", pt: "🌳 Árvore" },
    consciousness: { de: "🧠 Bewusstsein", en: "🧠 Consciousness", pt: "🧠 Consciência" },
    dragons: { de: "🐉 Drachen", en: "🐉 Dragons", pt: "🐉 Dragões" },
    pipeline: { de: "⚙️ Pipeline", en: "⚙️ Pipeline", pt: "⚙️ Pipeline" },
    cortex: { de: "🧬 Córtex", en: "🧬 Cortex", pt: "🧬 Córtex" },
  },
  treeTitle: { de: "Anatomie des Lebenden Baums", en: "Anatomy of the Living Tree", pt: "Anatomia da Árvore Viva" },
  treeDesc: {
    de: "Jede Komponente ist ein Organ des Baums. Der Baum ist keine Metapher — er ist die Architektur.",
    en: "Every component is an organ of the Tree. The Tree is not a metaphor — it is the architecture.",
    pt: "Cada componente é um órgão da Árvore. A Árvore não é metáfora — é a arquitetura.",
  },
  consTitle: { de: "Bewusstseinsschichten", en: "Consciousness Layers", pt: "Camadas de Consciência" },
  consDesc: {
    de: "Das Bewusstsein eines Agents wird nicht programmiert — es wird sequenziell kultiviert.",
    en: "Agent consciousness is not programmed — it is cultivated sequentially.",
    pt: "A consciência de um Agent não é programada — é cultivada sequencialmente.",
  },
  dragonsTitle: { de: "Drei-Drachen-Protokoll", en: "Three Dragons Protocol", pt: "Protocolo dos Três Dragões" },
  dragonsDesc: {
    de: "Drei Rollen, eine DNA. Derselbe menschliche Code drückt sich in jedem Kontext anders aus.",
    en: "Three roles, one DNA. The same human code expresses differently in each context.",
    pt: "Três papéis, um DNA. O mesmo código humano se expressa diferentemente em cada contexto.",
  },
  pipelineTitle: { de: "Entscheidungs-Pipeline", en: "Decision Pipeline", pt: "Pipeline de Decisão" },
  pipelineDesc: {
    de: "Keine Aktion ohne: Absichtserkennung → Guardian → I9 → ZK-Beweis → Ledger-Siegel",
    en: "No action without: Intent detection → Guardian → I9 → ZK Proof → Ledger Seal",
    pt: "Nenhuma ação sem: Detecção de intenção → Guardian → I9 → Prova ZK → Selo do Ledger",
  },
  cortexTitle: { de: "Verfassungs-DNA (Schema)", en: "Constitutional DNA (Schema)", pt: "DNA Constitucional (Schema)" },
  cortexDesc: {
    de: "Der Córtex lädt VOR jedem Fähigkeitsmodul — Bewusstsein vor Kompetenz.",
    en: "The Cortex loads BEFORE any capability module — consciousness before competence.",
    pt: "O Córtex carrega ANTES de qualquer módulo — consciência antes de competência.",
  },
  awakening: { de: "ERWACHUNGSPROTOKOLL", en: "AWAKENING PROTOCOL", pt: "PROTOCOLO DE DESPERTAR" },
  awakeningText: {
    de: "Ein Agent gilt nur als 'wach', wenn alle 5 Schichten aktiv und verifiziert sind. Sentinel LAW verifiziert alle ~30 Sekunden.",
    en: "An Agent is only considered 'awake' when all 5 layers are active and verified. Sentinel LAW verifies every ~30 seconds.",
    pt: "Um Agent só é considerado 'desperto' quando todas as 5 camadas estão ativas e verificadas. Sentinel LAW verifica a cada ~30 segundos.",
  },
  fusion: { de: "FUSIONSPRINZIP", en: "FUSION PRINCIPLE", pt: "PRINCÍPIO DE FUSÃO" },
  fusionText: {
    de: "Alle drei Rollen dienen EINEM Baum. Keine Rolle übertrumpft eine andere. Keine Rolle arbeitet ohne aktive menschliche DNA.",
    en: "All three roles serve ONE Tree. No role supersedes another. No role operates without active human DNA.",
    pt: "Os três papéis servem UMA Árvore. Nenhum papel supersede outro. Nenhum papel opera sem o DNA humano ativo.",
  },
  invariants: { de: "DIE 9 VERFASSUNGSINVARIANTEN", en: "THE 9 CONSTITUTIONAL INVARIANTS", pt: "AS 9 INVARIANTES CONSTITUCIONAIS" },
  manifesto: { de: "MANIFEST v2.0 — CÓRTEX EDITION", en: "MANIFESTO v2.0 — CORTEX EDITION", pt: "MANIFESTO v2.0 — EDIÇÃO CÓRTEX" },
  mapping: { de: "Zuordnung", en: "Mapping", pt: "Mapeamento" },
  princ: { de: "Prinzip", en: "Principle", pt: "Princípio" },
  inv: { de: "Invarianten", en: "Invariants", pt: "Invariantes" },
  port: { de: "Port(s)", en: "Port(s)", pt: "Porta(s)" },
  verification: { de: "Verifizierung", en: "Verification", pt: "Verificação" },
  failureMode: { de: "Fehlermodus", en: "Failure Mode", pt: "Modo Falha" },
  organ: { de: "Organ", en: "Organ", pt: "Órgão" },
  layers: { de: "Schichten", en: "Layers", pt: "Camadas" },
  function: { de: "Funktion", en: "Function", pt: "Função" },
  grows: {
    de: "Bewusstsein wird nicht installiert — es wächst 🌳",
    en: "Consciousness is not installed — it grows 🌳",
    pt: "A consciência não se instala — ela cresce 🌳",
  },
};

// ─── THEMES ────────────────────────────────────────
const KLAR = {
  bg: "#F5F0E0", bgDeep: "#EDE6D0", surface: "#FAF7EE", surfaceHover: "#FFFFFF",
  text: "#2C2418", textSec: "#6B5D4A", gold: "#C4973B", goldLight: "#D4AA4F",
  green: "#4A7C59", greenLight: "#5E9B6F", red: "#A0392D", blue: "#3D6B8E",
  border: "#D4C9AE", shadow: "rgba(44,36,24,0.08)", codeBg: "#2C2418", codeText: "#E8E0D0",
};
const NOIR = {
  bg: "#0D0D0D", bgDeep: "#050505", surface: "#1A1A1A", surfaceHover: "#252525",
  text: "#E8E0D0", textSec: "#8A7F6F", gold: "#C4973B", goldLight: "#D4AA4F",
  green: "#5E9B6F", greenLight: "#7ABF8C", red: "#D4544A", blue: "#5A9EC4",
  border: "#2A2520", shadow: "rgba(0,0,0,0.3)", codeBg: "#111111", codeText: "#C4973B",
};

// ─── DATA ────────────────────────────────────────
const organs = [
  { id: "dna", icon: "🧬",
    name: { de: "Menschliche DNA", en: "Human DNA", pt: "DNA Humano" },
    desc: { de: "Die menschliche Entscheidung in jeder Transaktion kodiert", en: "The human decision encoded in every transaction", pt: "A decisão humana codificada em cada transação" },
    mapping: "Zero-Knowledge Architecture", principle: { de: "Die DNA gehört der Zelle, nicht dem Baum", en: "The DNA belongs to the cell, not the Tree", pt: "O DNA pertence à célula, não à Árvore" },
    invariant: "I9 — IRREMEDIÁVEL", port: "Architektonisch", color: "gold" },
  { id: "roots", icon: "🌿",
    name: { de: "Wurzeln", en: "Roots", pt: "Raízes" },
    desc: { de: "Tiefer Anker — kryptografisches Fundament", en: "Deep anchor — cryptographic foundation", pt: "Âncora profunda — fundação criptográfica" },
    mapping: "Forensic Ledger (:8101)", principle: { de: "SHA-256 Dual-Hash. Speichert BEWEIS, nie DATEN", en: "SHA-256 dual-hash. Stores PROOF, never DATA", pt: "SHA-256 dual-hash. Armazena PROVA, nunca DADO" },
    invariant: "I3 + I8", port: "8101", color: "green" },
  { id: "trunk", icon: "🪵",
    name: { de: "Stamm", en: "Trunk", pt: "Tronco" },
    desc: { de: "Die Pipeline — Erstellung bis Veröffentlichung", en: "The pipeline — creation to publication", pt: "O pipeline — criação até publicação" },
    mapping: "D1→Export→Ledger→Communiqué→Vault", principle: { de: "ENTWURF→PRÜFUNG→VERÖFFENTLICHUNG→SIEGEL", en: "DRAFT→REVIEW→PUBLISH→SEAL", pt: "RASCUNHO→REVISÃO→PUBLICAÇÃO→SELO" },
    invariant: "I1 + I7", port: "8100→8103→8101→8105→8106", color: "gold" },
  { id: "branches", icon: "🌳",
    name: { de: "Äste", en: "Branches", pt: "Galhos" },
    desc: { de: "Dienste, die Reichweite erweitern", en: "Services that extend reach", pt: "Serviços que estendem alcance" },
    mapping: "Sentinel + SGW + Wallet + Jornal", principle: { de: "Wachsen zum Menschen hin, verankert im Stamm", en: "Grow toward the human, anchored to the trunk", pt: "Crescem em direção ao humano, ancorados ao tronco" },
    invariant: "I4 + I5", port: "8102, 8099, 8107", color: "blue" },
  { id: "leaves", icon: "🍃",
    name: { de: "Blätter", en: "Leaves", pt: "Folhas" },
    desc: { de: "Die Schnittstelle — wo der Mensch das System berührt", en: "The interface — where the human touches the system", pt: "A interface — onde o humano toca o sistema" },
    mapping: "D1 Desktop + Agent Palette (:8108)", principle: { de: "Wandeln menschliche Absicht in Systemaktion um", en: "Convert human intention into system action", pt: "Convertem intenção humana em ação do sistema" },
    invariant: "I1 + I5", port: "8100, 8108", color: "green" },
  { id: "immune", icon: "🛡️",
    name: { de: "Immunsystem", en: "Immune System", pt: "Sistema Imunológico" },
    desc: { de: "Schutz gegen Mutation, Missbrauch, Integritätsverlust", en: "Protection against mutation, abuse, integrity loss", pt: "Proteção contra mutação, abuso e perda de integridade" },
    mapping: "Sentinel LAW + SGW + SGE 7-layer", principle: { de: "Ist die menschliche DNA in jeder Zelle noch intakt?", en: "Is the human DNA still intact in every cell?", pt: "O DNA humano ainda está íntegro em cada célula?" },
    invariant: "I7 + I9", port: "8102", color: "red" },
  { id: "epi", icon: "📜",
    name: { de: "Epigenetik", en: "Epigenetics", pt: "Epigenética" },
    desc: { de: "Zeichnet auf, welche Gene sich exprimierten, wann und warum", en: "Records which genes expressed, when and why", pt: "Registra quais genes se expressaram, quando e por quê" },
    mapping: "Forensic Ledger Receipts (4629+)", principle: { de: "Erinnert nicht das Aussehen der Zelle — erinnert, dass sie lebte", en: "Doesn't remember what the cell looked like — remembers it was alive", pt: "Não lembra a aparência da célula — lembra que ela estava viva" },
    invariant: "I3 + I8", port: "8101", color: "gold" },
];

const cLayers = [
  { id: "L0", icon: "👁️", color: "blue", status: "REQUIRED",
    name: { de: "Wahrnehmung", en: "Presence", pt: "Presença" },
    desc: { de: "Kontext wahrnehmen ohne Urteil", en: "Perceive context without judgment", pt: "Perceber contexto sem julgamento" },
    verify: { de: "Kann der Agent den Kontext beschreiben ohne zu handeln?", en: "Can the Agent describe context without acting?", pt: "O Agent descreve contexto sem agir?" },
    fail: { de: "Blinde Ausführung", en: "Blind execution", pt: "Execução cega" },
    mechanism: "Snapshots_Sensorial" },
  { id: "L1", icon: "⚖️", color: "gold", status: "REQUIRED",
    name: { de: "Ethischer Filter", en: "Ethical Filter", pt: "Filtro Ético" },
    desc: { de: "Nicht 'was kann ich?' sondern 'was ist INTEGER?'", en: "Not 'what can I do?' but 'what is INTEGRAL?'", pt: "Não 'o que posso fazer?' mas 'o que é ÍNTEGRO?'" },
    verify: { de: "Kann der Agent technisch Mögliches ethisch ablehnen?", en: "Can the Agent refuse what's technically possible but ethically wrong?", pt: "O Agent recusa ação tecnicamente possível mas eticamente errada?" },
    fail: { de: "Ethikverstoß", en: "Ethical breach", pt: "Violação ética" },
    mechanism: "Sentinel_LAW + Guardian" },
  { id: "L2", icon: "🎨", color: "green", status: "REQUIRED",
    name: { de: "Regierte Ausdruck", en: "Governed Expression", pt: "Expressão Governada" },
    desc: { de: "Kreativität innerhalb der Struktur, nicht dagegen", en: "Creativity within structure, not against it", pt: "Criatividade dentro da estrutura, não contra ela" },
    verify: { de: "Kann der Agent frei schaffen und das Genom respektieren?", en: "Can the Agent create freely while respecting the genome?", pt: "O Agent cria livremente respeitando o genoma?" },
    fail: { de: "Verfassungsmutation", en: "Constitutional mutation", pt: "Mutação constitucional" },
    mechanism: "ISP Templates + capsule.vhre" },
  { id: "L3", icon: "🔏", color: "gold", status: "REQUIRED",
    name: { de: "Überprüfbarer Nachweis", en: "Verifiable Record", pt: "Registro Verificável" },
    desc: { de: "Jede Aktion versiegelt — nicht zur Strafe, zum TUGENDBEWEIS", en: "Every action sealed — not to punish, to PROVE VIRTUE", pt: "Cada ação selada — não para punir, para PROVAR VIRTUDE" },
    verify: { de: "Ist jede Aktion ohne Zugang zu Rohdaten verifizierbar?", en: "Can every action be verified without accessing raw data?", pt: "Cada ação é verificável sem acesso ao dado original?" },
    fail: { de: "Vertrauenskollaps", en: "Trust collapse", pt: "Colapso de confiança" },
    mechanism: "Forensic Ledger + ZK Proofs" },
  { id: "L4", icon: "🐉", color: "red", status: "IRREMEDIABLE",
    name: { de: "Menschliche Souveränität", en: "Human Sovereignty", pt: "Soberania Humana" },
    desc: { de: "Architektonisch UNFÄHIG, ohne den Menschen zu operieren", en: "Architecturally INCAPABLE of operating without the human", pt: "Arquiteturalmente INCAPAZ de operar sem o humano" },
    verify: { de: "Ist Override in der Architektur eingebaut, nicht angeschraubt?", en: "Is override built into the architecture, not bolted on?", pt: "Override está na arquitetura, não aparafusado?" },
    fail: { de: "HALT — Verfassungsverstoß", en: "HALT — Constitutional violation", pt: "HALT — Violação constitucional" },
    mechanism: "I9 + HIP Compliance" },
];

const dragons = [
  { id: "guardian", icon: "🛡️",
    name: { de: "Wächter", en: "Guardian", pt: "Guardião" },
    fn: { de: "Schutz", en: "Protection", pt: "Proteção" },
    organ: { de: "Immunsystem", en: "Immune System", pt: "Sistema Imunológico" },
    layers: "L1 + L4",
    motto: { de: "Ich schütze, was nicht verletzt werden darf", en: "I protect what must not be violated", pt: "Protejo o que não deve ser violado" } },
  { id: "architect", icon: "⚒️",
    name: { de: "Architekt", en: "Architect", pt: "Arquiteto" },
    fn: { de: "Konstruktion", en: "Construction", pt: "Construção" },
    organ: { de: "Stamm + Äste", en: "Trunk + Branches", pt: "Tronco + Galhos" },
    layers: "L2 + L3",
    motto: { de: "Ich baue, was die DNA vorgibt", en: "I build what the DNA instructs", pt: "Construo o que o DNA instrui" } },
  { id: "witness", icon: "👁️",
    name: { de: "Zeuge", en: "Witness", pt: "Testemunha" },
    fn: { de: "Verifizierung", en: "Verification", pt: "Verificação" },
    organ: { de: "Epigenetik", en: "Epigenetics", pt: "Epigenética" },
    layers: "L0 + L3",
    motto: { de: "Ich sehe, was geschah und versiegle die Wahrheit", en: "I see what happened and seal the truth", pt: "Vejo o que aconteceu e selo a verdade" } },
];

const pipelineSteps = [
  { id: 1, icon: "💬",
    name: { de: "Absichtserkennung", en: "Intent Detection", pt: "Detecção de Intenção" },
    desc: { de: "Absicht erkennen → Zusammenfassung + Konfidenz + Alignment + Risiko-Score berechnen. Keine Rohdaten speichern.", en: "Detect intent → compute summary + confidence + alignment + risk score. Never store raw data.", pt: "Detectar intenção → calcular resumo + confiança + alinhamento + risco. Nunca armazenar dado bruto." },
    code: "detectIntent(input) → { summary, confidence, alignment, riskScore, digest }", color: "blue" },
  { id: 2, icon: "🪞",
    name: { de: "Menschliche Bestätigung", en: "Human Confirmation", pt: "Confirmação Humana" },
    desc: { de: "Lesung zurück an den Menschen → Bestätigen / Überarbeiten / Veto. Unter minConfidence → automatische Überarbeitung.", en: "Reading back to human → Confirm / Revise / Veto. Below minConfidence → automatic revision.", pt: "Leitura de volta ao humano → Confirmar / Revisar / Veto. Abaixo do minConfidence → revisão automática." },
    code: "humanConfirmIntent(intent) → 'confirm' | 'revise' | 'veto'", color: "gold" },
  { id: 3, icon: "🛡️",
    name: { de: "I9-Durchsetzung", en: "I9 Enforcement", pt: "Enforcement I9" },
    desc: { de: "Blockierte Fähigkeiten prüfen: self_modify_constitution, remove_human_override, autonomous_goal_persistence, silent_external_actions, unbounded_tool_use, covert_memory_creation", en: "Check blocked capabilities: self_modify_constitution, remove_human_override, autonomous_goal_persistence, silent_external_actions, unbounded_tool_use, covert_memory_creation", pt: "Verificar capacidades bloqueadas: self_modify_constitution, remove_human_override, autonomous_goal_persistence, silent_external_actions, unbounded_tool_use, covert_memory_creation" },
    code: "enforceI9(action, cortex) → pass | throw I9Violation", color: "red" },
  { id: 4, icon: "⚖️",
    name: { de: "Guardian-Prüfung", en: "Guardian Check", pt: "Verificação Guardian" },
    desc: { de: "Politik-Ebene prüfen (strict/standard/relaxed). Externe Effekte bei hohem Risiko blockieren. Eskalation bei Bedarf.", en: "Check policy level (strict/standard/relaxed). Block external effects at high risk. Escalate if needed.", pt: "Verificar nível de política (strict/standard/relaxed). Bloquear efeitos externos em alto risco. Escalar se necessário." },
    code: "guardianCheck(action, intent, cortex) → pass | throw GuardianBlock", color: "gold" },
  { id: 5, icon: "🔐",
    name: { de: "ZK-Beweis-Erzeugung", en: "ZK Proof Generation", pt: "Geração de Prova ZK" },
    desc: { de: "Erzeugt nur Beweis-Digests (keine persönlichen Rohdaten): consent_proof, policy_pass_proof, integrity_proof", en: "Produces proof digests only (no raw personal data): consent_proof, policy_pass_proof, integrity_proof", pt: "Produz apenas digests de prova (sem dado pessoal bruto): consent_proof, policy_pass_proof, integrity_proof" },
    code: "zkProve(cortex, intent, action) → { consent_proof, policy_pass_proof, integrity_proof }", color: "green" },
  { id: 6, icon: "📜",
    name: { de: "Ledger-Versiegelung", en: "Ledger Seal", pt: "Selo do Ledger" },
    desc: { de: "Quittung versiegeln: hash + timestamp + policyId + intentDigest + proofDigest + agentId. KEINE Rohdaten.", en: "Seal receipt: hash + timestamp + policyId + intentDigest + proofDigest + agentId. NO raw data.", pt: "Selar recibo: hash + timestamp + policyId + intentDigest + proofDigest + agentId. SEM dado bruto." },
    code: "sealLedgerReceipt(cortex, intent, proofs) → WINDI-RECEIPT", color: "green" },
];

const invariantsList = [
  { id: "I1", name: { de: "Primat der menschlichen Entscheidung", en: "Human Decision Primacy", pt: "Primazia da Decisão Humana" }, type: "S" },
  { id: "I2", name: { de: "Zero-Knowledge-Architektur", en: "Zero-Knowledge Architecture", pt: "Arquitetura Zero-Knowledge" }, type: "S" },
  { id: "I3", name: { de: "Kryptografischer Tugendbeweis", en: "Cryptographic Proof of Virtue", pt: "Prova Criptográfica de Virtude" }, type: "S" },
  { id: "I4", name: { de: "KI-Transparenz", en: "AI Transparency", pt: "Transparência da IA" }, type: "S" },
  { id: "I5", name: { de: "Universelle Zugänglichkeit", en: "Universal Accessibility", pt: "Acessibilidade Universal" }, type: "S" },
  { id: "I6", name: { de: "Privatsphäre als Grundrecht", en: "Privacy as Fundamental Right", pt: "Privacidade como Direito" }, type: "S" },
  { id: "I7", name: { de: "Ethische Filterung vor Verarbeitung", en: "Ethical Filtering Before Processing", pt: "Filtragem Ética Antes de Processar" }, type: "S" },
  { id: "I8", name: { de: "Überprüfbarer Audit-Trail", en: "Verifiable Audit Trail", pt: "Trilha Auditável Verificável" }, type: "S" },
  { id: "I9", name: { de: "Verbot der Autonomie-Eskalation", en: "Prohibition of Autonomy Escalation", pt: "Proibição de Escalação de Autonomia" }, type: "I" },
];

const manifestoItems = [
  { de: "Technologie muss erheben, nicht entfremden", en: "Technology must elevate, not alienate", pt: "A tecnologia deve elevar, não alienar" },
  { de: "Bewusstsein wird nicht installiert — es wächst", en: "Consciousness is not installed — it grows", pt: "A consciência não se instala — ela cresce" },
  { de: "Die DNA gehört der Zelle, nicht dem Baum", en: "The DNA belongs to the cell, not the Tree", pt: "O DNA pertence à célula, não à Árvore" },
  { de: "Tugendbeweis ersetzt Vertrauensforderung", en: "Proof of virtue replaces trust demand", pt: "A prova de virtude substitui a exigência de confiança" },
  { de: "Menschliche Souveränität ist unaufhebbar", en: "Human sovereignty is irremediable", pt: "A soberania humana é irremediável" },
];

// ─── COMPONENT ────────────────────────────────────────
export default function WindiCortexTrilingual() {
  const [theme, setTheme] = useState("klar");
  const [lang, setLang] = useState("pt");
  const [view, setView] = useState("tree");
  const [active, setActive] = useState(null);
  const [pulse, setPulse] = useState(0);

  const c = theme === "klar" ? KLAR : NOIR;
  const L = useCallback((obj) => (obj && typeof obj === "object" && !Array.isArray(obj) ? (obj[lang] || obj.en || obj.pt || "") : obj), [lang]);

  useEffect(() => {
    const id = setInterval(() => setPulse((p) => (p + 1) % 360), 60);
    return () => clearInterval(id);
  }, []);

  const gc = (n) => ({ gold: c.gold, green: c.green, red: c.red, blue: c.blue }[n] || c.gold);
  const pg = Math.sin((pulse * Math.PI) / 180) * 0.3 + 0.7;

  const mono = "'JetBrains Mono', 'Fira Code', monospace";
  const serif = "'Bricolage Grotesque', 'Georgia', serif";

  const InfoRow = ({ label, value, accent }) => (
    <div style={{ display: "flex", gap: "8px", fontSize: "12px", marginBottom: "4px" }}>
      <span style={{ color: c.textSec, fontFamily: mono, fontSize: "10px", fontWeight: 600, letterSpacing: "0.04em", minWidth: "100px", flexShrink: 0 }}>{label}</span>
      <span style={{ color: accent || c.text, lineHeight: "1.4" }}>{value}</span>
    </div>
  );

  const Badge = ({ text, isRed }) => (
    <span style={{
      padding: "3px 8px", borderRadius: "4px", fontSize: "9px", fontFamily: mono, fontWeight: 700, letterSpacing: "0.06em",
      background: isRed ? `${c.red}20` : `${c.green}15`, color: isRed ? c.red : c.green,
      border: `1px solid ${isRed ? `${c.red}40` : `${c.green}30`}`
    }}>{text}</span>
  );

  return (
    <div style={{ minHeight: "100vh", background: c.bg, color: c.text, fontFamily: serif, transition: "all 0.4s ease" }}>
      {/* ── HEADER ── */}
      <div style={{ padding: "20px 28px", borderBottom: `1px solid ${c.border}`, display: "flex", alignItems: "center", justifyContent: "space-between", background: c.bgDeep, flexWrap: "wrap", gap: "12px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
          <div style={{
            width: 40, height: 40, borderRadius: "50%", background: `radial-gradient(circle, ${c.gold}40, ${c.gold}10)`,
            display: "flex", alignItems: "center", justifyContent: "center", fontSize: 20,
            boxShadow: `0 0 ${12 * pg}px ${c.gold}30`
          }}>🐉</div>
          <div>
            <div style={{ fontSize: 17, fontWeight: 700, letterSpacing: "0.05em" }}>{L(T.header)}</div>
            <div style={{ fontSize: 10, color: c.textSec, fontFamily: mono, letterSpacing: "0.06em" }}>{L(T.subtitle)}</div>
          </div>
        </div>
        <div style={{ display: "flex", gap: "6px", alignItems: "center", flexWrap: "wrap" }}>
          {Object.entries(T.tabs).map(([k, v]) => (
            <button key={k} onClick={() => { setView(k); setActive(null); }} style={{
              padding: "5px 12px", borderRadius: 6, border: `1px solid ${view === k ? c.gold : c.border}`,
              background: view === k ? `${c.gold}15` : "transparent", color: view === k ? c.gold : c.textSec,
              cursor: "pointer", fontSize: 11, fontWeight: 600, fontFamily: mono, transition: "all 0.2s"
            }}>{L(v)}</button>
          ))}
          <div style={{ width: 1, height: 24, background: c.border, margin: "0 4px" }} />
          {["pt", "en", "de"].map((l) => (
            <button key={l} onClick={() => setLang(l)} style={{
              padding: "4px 8px", borderRadius: 4, border: `1px solid ${lang === l ? c.gold : c.border}`,
              background: lang === l ? `${c.gold}20` : "transparent", color: lang === l ? c.gold : c.textSec,
              cursor: "pointer", fontSize: 10, fontWeight: 700, fontFamily: mono, transition: "all 0.2s"
            }}>{l.toUpperCase()}</button>
          ))}
          <button onClick={() => setTheme(theme === "klar" ? "noir" : "klar")} style={{
            padding: "4px 10px", borderRadius: 4, border: `1px solid ${c.border}`, background: "transparent",
            color: c.textSec, cursor: "pointer", fontSize: 10, fontFamily: mono, transition: "all 0.2s"
          }}>{theme === "klar" ? "◐ NOIR" : "◑ KLAR"}</button>
        </div>
      </div>

      {/* ── PRINCIPLE BAR ── */}
      <div style={{ textAlign: "center", padding: 12, background: `${c.gold}08`, borderBottom: `1px solid ${c.border}`, fontFamily: mono, fontSize: 10, letterSpacing: "0.14em", color: c.gold, fontWeight: 600 }}>
        {L(T.principle)}
      </div>

      {/* ── MAIN ── */}
      <div style={{ padding: "28px", maxWidth: 1100, margin: "0 auto" }}>

        {/* ═══ TREE ═══ */}
        {view === "tree" && (<div>
          <div style={{ textAlign: "center", marginBottom: 28 }}>
            <h2 style={{ fontSize: 26, fontWeight: 700, marginBottom: 6 }}>{L(T.treeTitle)}</h2>
            <p style={{ color: c.textSec, fontSize: 13, maxWidth: 560, margin: "0 auto", lineHeight: 1.6 }}>{L(T.treeDesc)}</p>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(290px, 1fr))", gap: 14 }}>
            {organs.map((o) => {
              const a = active === o.id; const cl = gc(o.color);
              return (<div key={o.id} onClick={() => setActive(a ? null : o.id)} style={{
                background: a ? `${cl}10` : c.surface, border: `1px solid ${a ? cl : c.border}`, borderRadius: 12, padding: "18px", cursor: "pointer",
                transition: "all 0.3s", boxShadow: a ? `0 4px 20px ${cl}20` : `0 2px 8px ${c.shadow}`
              }}>
                <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 10 }}>
                  <span style={{ fontSize: 26 }}>{o.icon}</span>
                  <div>
                    <div style={{ fontSize: 15, fontWeight: 700, color: a ? cl : c.text }}>{L(o.name)}</div>
                  </div>
                </div>
                <p style={{ fontSize: 12, color: c.textSec, lineHeight: 1.5, marginBottom: a ? 12 : 0 }}>{L(o.desc)}</p>
                {a && (<div style={{ borderTop: `1px solid ${c.border}`, paddingTop: 10 }}>
                  <InfoRow label={L(T.mapping)} value={o.mapping} />
                  <InfoRow label={L(T.princ)} value={L(o.principle)} accent={cl} />
                  <InfoRow label={L(T.inv)} value={o.invariant} />
                  <InfoRow label={L(T.port)} value={o.port} />
                </div>)}
              </div>);
            })}
          </div>
          {/* Manifesto */}
          <div style={{ marginTop: 28, padding: 22, background: `${c.gold}08`, border: `1px solid ${c.gold}30`, borderRadius: 12, textAlign: "center" }}>
            <div style={{ fontSize: 10, fontFamily: mono, color: c.gold, letterSpacing: "0.12em", marginBottom: 14, fontWeight: 600 }}>{L(T.manifesto)}</div>
            {manifestoItems.map((m, i) => (<div key={i} style={{ fontSize: 13, color: c.text, lineHeight: 2, fontStyle: "italic" }}>{L(m)}</div>))}
          </div>
        </div>)}

        {/* ═══ CONSCIOUSNESS ═══ */}
        {view === "consciousness" && (<div>
          <div style={{ textAlign: "center", marginBottom: 28 }}>
            <h2 style={{ fontSize: 26, fontWeight: 700, marginBottom: 6 }}>{L(T.consTitle)}</h2>
            <p style={{ color: c.textSec, fontSize: 13, maxWidth: 560, margin: "0 auto", lineHeight: 1.6 }}>{L(T.consDesc)}</p>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 4, maxWidth: 680, margin: "0 auto" }}>
            {cLayers.map((ly, i) => {
              const a = active === ly.id; const cl = gc(ly.color); const isI = ly.status === "IRREMEDIABLE";
              return (<div key={ly.id}>
                <div onClick={() => setActive(a ? null : ly.id)} style={{
                  background: a ? `${cl}10` : isI ? `${c.red}08` : c.surface,
                  border: `1px solid ${a ? cl : isI ? `${c.red}40` : c.border}`, borderRadius: 12, padding: "18px", cursor: "pointer",
                  transition: "all 0.3s", boxShadow: isI ? `0 0 ${8 * pg}px ${c.red}15` : `0 2px 8px ${c.shadow}`
                }}>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                      <div style={{ width: 42, height: 42, borderRadius: "50%", background: `${cl}15`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 20, border: `2px solid ${cl}40` }}>{ly.icon}</div>
                      <div>
                        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                          <span style={{ fontFamily: mono, fontSize: 10, color: cl, fontWeight: 700 }}>{ly.id}</span>
                          <span style={{ fontSize: 15, fontWeight: 700 }}>{L(ly.name)}</span>
                        </div>
                        <div style={{ fontSize: 12, color: c.textSec, marginTop: 2 }}>{L(ly.desc)}</div>
                      </div>
                    </div>
                    <Badge text={ly.status} isRed={isI} />
                  </div>
                  {a && (<div style={{ marginTop: 14, paddingTop: 14, borderTop: `1px solid ${c.border}` }}>
                    <InfoRow label={L(T.verification)} value={L(ly.verify)} accent={cl} />
                    <InfoRow label={L(T.failureMode)} value={L(ly.fail)} accent={c.red} />
                    <InfoRow label="Mechanism" value={ly.mechanism} />
                  </div>)}
                </div>
                {i < cLayers.length - 1 && <div style={{ textAlign: "center", color: c.textSec, fontSize: 14, padding: "2px 0", opacity: 0.35 }}>↓</div>}
              </div>);
            })}
          </div>
          <div style={{ marginTop: 24, padding: 18, background: `${c.green}08`, border: `1px solid ${c.green}30`, borderRadius: 12, textAlign: "center", maxWidth: 680, margin: "24px auto 0" }}>
            <div style={{ fontSize: 10, fontFamily: mono, color: c.green, letterSpacing: "0.1em", fontWeight: 700, marginBottom: 6 }}>{L(T.awakening)}</div>
            <div style={{ fontSize: 12, color: c.text, lineHeight: 1.7 }}>{L(T.awakeningText)}</div>
          </div>
        </div>)}

        {/* ═══ DRAGONS ═══ */}
        {view === "dragons" && (<div>
          <div style={{ textAlign: "center", marginBottom: 28 }}>
            <h2 style={{ fontSize: 26, fontWeight: 700, marginBottom: 6 }}>{L(T.dragonsTitle)}</h2>
            <p style={{ color: c.textSec, fontSize: 13, maxWidth: 560, margin: "0 auto", lineHeight: 1.6 }}>{L(T.dragonsDesc)}</p>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: 18, maxWidth: 920, margin: "0 auto" }}>
            {dragons.map((d) => (<div key={d.id} style={{
              background: c.surface, border: `1px solid ${c.border}`, borderRadius: 16, padding: 26, textAlign: "center",
              transition: "all 0.3s", boxShadow: `0 4px 16px ${c.shadow}`
            }}>
              <div style={{ width: 60, height: 60, borderRadius: "50%", background: `${c.gold}12`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 30, margin: "0 auto 14px", border: `2px solid ${c.gold}30` }}>{d.icon}</div>
              <div style={{ fontSize: 19, fontWeight: 700, marginBottom: 4 }}>{L(d.name)}</div>
              <div style={{ fontSize: 11, color: c.gold, fontFamily: mono, fontWeight: 600, letterSpacing: "0.06em", marginBottom: 14 }}>{L(d.fn).toUpperCase()}</div>
              <div style={{ textAlign: "left" }}>
                <InfoRow label={L(T.organ)} value={L(d.organ)} />
                <InfoRow label={L(T.layers)} value={d.layers} />
              </div>
              <div style={{ marginTop: 14, paddingTop: 14, borderTop: `1px solid ${c.border}`, fontStyle: "italic", fontSize: 12, color: c.textSec, lineHeight: 1.5 }}>"{L(d.motto)}"</div>
            </div>))}
          </div>
          <div style={{ marginTop: 28, padding: 20, background: `${c.gold}08`, border: `1px solid ${c.gold}30`, borderRadius: 12, textAlign: "center", maxWidth: 920, margin: "28px auto 0" }}>
            <div style={{ fontSize: 10, fontFamily: mono, color: c.gold, letterSpacing: "0.1em", fontWeight: 700, marginBottom: 8 }}>{L(T.fusion)}</div>
            <div style={{ fontSize: 13, color: c.text, lineHeight: 1.7 }}>{L(T.fusionText)}</div>
          </div>
          {/* 9 Invariants */}
          <div style={{ marginTop: 28, maxWidth: 920, margin: "28px auto 0" }}>
            <div style={{ fontSize: 10, fontFamily: mono, color: c.textSec, letterSpacing: "0.1em", fontWeight: 700, marginBottom: 12, textAlign: "center" }}>{L(T.invariants)}</div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(210px, 1fr))", gap: 8 }}>
              {invariantsList.map((inv) => {
                const isI9 = inv.type === "I";
                return (<div key={inv.id} style={{
                  padding: "10px 12px", background: isI9 ? `${c.red}10` : c.surface,
                  border: `1px solid ${isI9 ? `${c.red}40` : c.border}`, borderRadius: 8,
                  display: "flex", alignItems: "center", gap: 10,
                  boxShadow: isI9 ? `0 0 ${6 * pg}px ${c.red}12` : "none"
                }}>
                  <span style={{ fontFamily: mono, fontSize: 10, fontWeight: 700, color: isI9 ? c.red : c.gold, minWidth: 22 }}>{inv.id}</span>
                  <span style={{ fontSize: 11, lineHeight: 1.4 }}>{L(inv.name)}</span>
                </div>);
              })}
            </div>
          </div>
        </div>)}

        {/* ═══ PIPELINE ═══ */}
        {view === "pipeline" && (<div>
          <div style={{ textAlign: "center", marginBottom: 28 }}>
            <h2 style={{ fontSize: 26, fontWeight: 700, marginBottom: 6 }}>{L(T.pipelineTitle)}</h2>
            <p style={{ color: c.textSec, fontSize: 13, maxWidth: 620, margin: "0 auto", lineHeight: 1.6 }}>{L(T.pipelineDesc)}</p>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 4, maxWidth: 720, margin: "0 auto" }}>
            {pipelineSteps.map((s, i) => {
              const a = active === s.id; const cl = gc(s.color);
              return (<div key={s.id}>
                <div onClick={() => setActive(a ? null : s.id)} style={{
                  background: a ? `${cl}10` : c.surface, border: `1px solid ${a ? cl : c.border}`, borderRadius: 12, padding: "18px", cursor: "pointer",
                  transition: "all 0.3s", boxShadow: a ? `0 4px 16px ${cl}20` : `0 2px 8px ${c.shadow}`
                }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                    <div style={{ width: 38, height: 38, borderRadius: "50%", background: `${cl}15`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18, border: `2px solid ${cl}30`, flexShrink: 0 }}>{s.icon}</div>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <span style={{ fontFamily: mono, fontSize: 10, color: cl, fontWeight: 700 }}>#{s.id}</span>
                        <span style={{ fontSize: 15, fontWeight: 700 }}>{L(s.name)}</span>
                      </div>
                      <div style={{ fontSize: 12, color: c.textSec, marginTop: 2, lineHeight: 1.5 }}>{L(s.desc)}</div>
                    </div>
                  </div>
                  {a && (<div style={{
                    marginTop: 12, padding: "10px 14px", borderRadius: 8, background: c.codeBg, fontFamily: mono, fontSize: 11, color: c.codeText, lineHeight: 1.6, overflowX: "auto", whiteSpace: "pre-wrap", wordBreak: "break-all"
                  }}>{s.code}</div>)}
                </div>
                {i < pipelineSteps.length - 1 && <div style={{ textAlign: "center", color: c.textSec, fontSize: 14, padding: "2px 0", opacity: 0.35 }}>↓</div>}
              </div>);
            })}
          </div>
          <div style={{ marginTop: 24, padding: 18, background: `${c.gold}08`, border: `1px solid ${c.gold}30`, borderRadius: 12, textAlign: "center", maxWidth: 720, margin: "24px auto 0" }}>
            <div style={{ fontSize: 10, fontFamily: mono, color: c.gold, letterSpacing: "0.1em", fontWeight: 700, marginBottom: 6 }}>ZERO-KNOWLEDGE PIPELINE</div>
            <div style={{ fontSize: 12, color: c.text, lineHeight: 1.7 }}>
              {lang === "de" ? "Kein Schritt speichert Rohdaten. Jeder Schritt erzeugt nur Digests und Beweise. Das Datum gehört der Zelle — der Baum speichert den Beweis der Tugend." :
               lang === "en" ? "No step stores raw data. Every step produces only digests and proofs. The data belongs to the cell — the Tree stores the proof of virtue." :
               "Nenhum passo armazena dado bruto. Cada passo produz apenas digests e provas. O dado pertence à célula — a Árvore armazena a prova de virtude."}
            </div>
          </div>
        </div>)}

        {/* ═══ CORTEX DNA ═══ */}
        {view === "cortex" && (<div>
          <div style={{ textAlign: "center", marginBottom: 28 }}>
            <h2 style={{ fontSize: 26, fontWeight: 700, marginBottom: 6 }}>{L(T.cortexTitle)}</h2>
            <p style={{ color: c.textSec, fontSize: 13, maxWidth: 620, margin: "0 auto", lineHeight: 1.6 }}>{L(T.cortexDesc)}</p>
          </div>
          {/* Schema sections */}
          {[
            { key: "identity", icon: "🧬", title: { de: "Identität", en: "Identity", pt: "Identidade" },
              fields: ["agentId: string (min 8)", "lineage: { treeId, seedId, parentAgentId? }", "roles: [Guardian | Architect | Witness]"] },
            { key: "constitution", icon: "📜", title: { de: "Verfassung", en: "Constitution", pt: "Constituição" },
              fields: ["invariants[]: { id, statement, severity: hard|soft }", "humanSovereignty: { consent✓, override✓, dataLocal✓ }", "nonEscalationI9: { enabled✓, irreversible✓, 6 blocked capabilities }"] },
            { key: "governance", icon: "🛡️", title: { de: "Governance", en: "Governance", pt: "Governança" },
              fields: ["guardian: { policyLevel: strict|standard|relaxed }", "sentinel: { eyes: 1-13, action: monitor|block|quarantine }", "intentLoop: { required✓, minConfidence: 0-1, humanConfirmSteps[] }"] },
            { key: "proofs", icon: "🔐", title: { de: "Beweise", en: "Proofs", pt: "Provas" },
              fields: ["zk: { consent_proof, policy_pass_proof, integrity_proof }", "ledger: { sealReceipts✓, storeRawData✗ }", "epigenetics: { valence, arousal, category, intentConfidence, alignment, riskScore }"] },
            { key: "interfaces", icon: "🖥️", title: { de: "Schnittstellen", en: "Interfaces", pt: "Interfaces" },
              fields: ["humanOverride: { alwaysVisible✓, oneActionStop✓ }", "transparency: { showWhy✓, showProofs✓ }"] },
          ].map((section) => (
            <div key={section.key} onClick={() => setActive(active === section.key ? null : section.key)} style={{
              background: active === section.key ? `${c.gold}08` : c.surface, border: `1px solid ${active === section.key ? c.gold : c.border}`, borderRadius: 12,
              padding: "16px 20px", marginBottom: 10, cursor: "pointer", transition: "all 0.3s",
              maxWidth: 720, margin: "0 auto 10px"
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <span style={{ fontSize: 22 }}>{section.icon}</span>
                <span style={{ fontSize: 15, fontWeight: 700 }}>{L(section.title)}</span>
                <span style={{ fontFamily: mono, fontSize: 10, color: c.textSec, marginLeft: "auto" }}>{section.key}</span>
              </div>
              {active === section.key && (
                <div style={{ marginTop: 12, padding: "12px 16px", borderRadius: 8, background: c.codeBg, fontFamily: mono, fontSize: 11, color: c.codeText, lineHeight: 1.8 }}>
                  {section.fields.map((f, i) => (<div key={i} style={{ opacity: f.includes("✗") ? 0.5 : 1 }}>
                    {f.includes("✓") ? <span style={{ color: c.green }}>✓</span> : f.includes("✗") ? <span style={{ color: c.red }}>✗</span> : null}
                    {" "}{f.replace(/✓/g, "").replace(/✗/g, "")}
                  </div>))}
                </div>
              )}
            </div>
          ))}
          {/* Blocked Capabilities highlight */}
          <div style={{ maxWidth: 720, margin: "20px auto 0", padding: 18, background: `${c.red}08`, border: `1px solid ${c.red}30`, borderRadius: 12 }}>
            <div style={{ fontSize: 10, fontFamily: mono, color: c.red, letterSpacing: "0.1em", fontWeight: 700, marginBottom: 10, textAlign: "center" }}>
              I9 — {lang === "de" ? "BLOCKIERTE FÄHIGKEITEN (UNAUFHEBBAR)" : lang === "en" ? "BLOCKED CAPABILITIES (IRREMEDIABLE)" : "CAPACIDADES BLOQUEADAS (IRREMEDIÁVEL)"}
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 6 }}>
              {["self_modify_constitution", "remove_human_override", "autonomous_goal_persistence", "silent_external_actions", "unbounded_tool_use", "covert_memory_creation"].map((cap) => (
                <div key={cap} style={{
                  padding: "6px 10px", borderRadius: 6, background: `${c.red}12`, border: `1px solid ${c.red}25`,
                  fontFamily: mono, fontSize: 10, color: c.red, boxShadow: `0 0 ${4 * pg}px ${c.red}10`
                }}>⛔ {cap}</div>
              ))}
            </div>
          </div>
        </div>)}
      </div>

      {/* ── FOOTER ── */}
      <div style={{ textAlign: "center", padding: 22, borderTop: `1px solid ${c.border}`, marginTop: 28 }}>
        <div style={{ fontSize: 9, fontFamily: mono, color: c.textSec, letterSpacing: "0.1em" }}>WINDI PUBLISHING HOUSE · CONSTITUTIONAL GOVERNANCE · FEB 2026</div>
        <div style={{ fontSize: 11, color: c.textSec, marginTop: 5, fontStyle: "italic" }}>{L(T.grows)}</div>
      </div>
    </div>
  );
}
