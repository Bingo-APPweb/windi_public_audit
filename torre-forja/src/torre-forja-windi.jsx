import { useState, useEffect, useRef, useCallback } from "react";

// ══════════════════════════════════════════════════════════════════════════
// TORRE DE OBSERVAÇÃO + FORJA WINDI
// Agent Forge — Where Humans Become Creators
// "Observe. Learn. Forge. Deploy."
// ══════════════════════════════════════════════════════════════════════════

// ── Data Constants ────────────────────────────────────────────────────────

const FORGE_STEPS = [
  { id: 1, name: "MINÉRIO", title: "Definir Essência", icon: "⛏", desc: "Escolha o papel constitucional e especialidade do seu Agent", color: "#8B4513" },
  { id: 2, name: "FOGO", title: "Aquecer na Forja", icon: "🔥", desc: "Configure comportamentos, limites e domínio de atuação", color: "#E25822" },
  { id: 3, name: "MARTELO", title: "Moldar Estrutura", icon: "🔨", desc: "Defina ISP templates, SGE rules e pipeline de documentos", color: "#4A6FA5" },
  { id: 4, name: "TÊMPERA", title: "Temperar Governança", icon: "💧", desc: "Sele com Ed25519, configure Sentinel e ative Ledger", color: "#2D6A4F" },
  { id: 5, name: "SELO", title: "Selar & Deploy", icon: "🐉", desc: "Certificação WAQP, atribuição de tier e ativação em campo", color: "#B08D57" },
];

const AGENT_ROLES = [
  { role: "Guardian", icon: "🛡", color: "#2D6A4F", desc: "Protege integridade. Verifica compliance. Bloqueia violações.", examples: "Legal review, GDPR check, contract verification, data anonymization" },
  { role: "Architect", icon: "🏗", color: "#4A6FA5", desc: "Constrói documentos. Formata outputs. Aplica ISP templates.", examples: "Report generation, template application, document formatting, data visualization" },
  { role: "Witness", icon: "👁", color: "#7B5EA7", desc: "Audita processos. Sela provas. Gera Virtue Receipts.", examples: "Audit trail, receipt generation, integrity verification, forensic logging" },
];

const SPECIALTIES = [
  "Legal Compliance", "Financial Reports", "Academic Integrity", "Healthcare Privacy",
  "Technical Documentation", "Supply Chain Audit", "Content Verification", "Impact Reports",
  "HR & Recruitment", "Real Estate Contracts", "Insurance Claims", "Tax Documentation",
  "EU Regulatory", "Environmental Compliance", "IP Protection", "Custom Specialty",
];

const DROPS_PACKAGES = [
  { name: "Spark", drops: 100, price: "€0", tag: "GRÁTIS", desc: "Para experimentar a Forja", includes: ["1 Agent draft", "10 test documents", "Basic ISP access", "Community support"], color: "#2D6A4F", popular: false },
  { name: "Ember", drops: 500, price: "€29", tag: "STARTER", desc: "Para freelancers e pequenos projetos", includes: ["3 Agent slots", "50 docs/day", "All ISP templates", "Sentinel monitoring", "Email support"], color: "#B08D57", popular: false },
  { name: "Blaze", drops: 2000, price: "€99", tag: "POPULAR", desc: "Para empresas e operações sérias", includes: ["10 Agent slots", "200 docs/day", "Custom ISP creation", "Priority Sentinel", "Priority support", "Wisdom Protocol access"], color: "#E25822", popular: true },
  { name: "Inferno", drops: 10000, price: "€399", tag: "ENTERPRISE", desc: "Para infraestrutura institucional", includes: ["Unlimited Agents", "Unlimited docs", "ISP Forja completa", "Dedicated Sentinel", "24/7 support", "Wisdom Protocol full", "White-label option", "API access"], color: "#8B1A1A", popular: false },
];

const FREEMIUM_LIMITS = {
  agents: 1, docsPerDay: 3, ispTemplates: 2, sentinelLevel: "Basic", ledgerRetention: "30 days",
  features: ["1 Agent (any role)", "3 documents/day", "2 ISP templates", "Basic Sentinel", "30-day Ledger", "Community forum"],
  locked: ["Custom ISP", "Priority Sentinel", "Wisdom Protocol", "API access", "White-label", "Unlimited docs"],
};

const LIVE_FORGE_ACTIVITY = [
  { user: "User_München_47", action: "Agent 'DocShield Pro' forged", role: "Guardian", tier: "SILVER", time: "3min" },
  { user: "User_Berlin_12", action: "Testing draft Agent in sandbox", role: "Architect", tier: "—", time: "8min" },
  { user: "User_Hamburg_89", action: "Agent 'FinAudit' promoted to GOLD", role: "Witness", tier: "GOLD", time: "15min" },
  { user: "User_Frankfurt_03", action: "Purchased Blaze package (2000 drops)", role: "—", tier: "—", time: "22min" },
  { user: "User_Köln_55", action: "Agent 'ArchiDoc' deployed to field", role: "Architect", tier: "SILVER", time: "31min" },
  { user: "User_Stuttgart_21", action: "Wallet created — first steps", role: "—", tier: "—", time: "45min" },
  { user: "User_Freiburg_77", action: "Agent 'GreenWatch' passed WAQP eval", role: "Guardian", tier: "BRONZE", time: "1hr" },
];

const ECOSYSTEM_AGENTS = [
  { name: "DocShield", role: "Guardian", creator: "Kanzlei München", level: "GOLD", docs: 3420, govScore: 97, specialty: "Legal Compliance", action: "Contract clause verification" },
  { name: "DataForge", role: "Architect", creator: "Finanz Frankfurt", level: "GOLD", docs: 5890, govScore: 98, specialty: "Financial Reports", action: "Q4 report template generation" },
  { name: "AuditEye", role: "Witness", creator: "Uni Heidelberg", level: "GOLD", docs: 2340, govScore: 99, specialty: "Academic Integrity", action: "Thesis plagiarism audit sealed" },
  { name: "MedGuard", role: "Guardian", creator: "Praxis Stuttgart", level: "SILVER", docs: 1890, govScore: 94, specialty: "Healthcare Privacy", action: "Patient record anonymization" },
  { name: "BlueprintAI", role: "Architect", creator: "Architekten Köln", level: "SILVER", docs: 2780, govScore: 92, specialty: "Technical Drawing", action: "Building plan ISP formatting" },
  { name: "ChainProof", role: "Witness", creator: "Logistik Bremen", level: "SILVER", docs: 1560, govScore: 91, specialty: "Supply Chain", action: "Shipment receipt verification" },
];

const ROLE_COLORS = { Guardian: "#2D6A4F", Architect: "#4A6FA5", Witness: "#7B5EA7" };
const LEVEL_COLORS = { GOLD: "#D4A76A", SILVER: "#A8B4C0", BRONZE: "#CD7F32" };

// ── Utility Components ────────────────────────────────────────────────────

const Pulse = ({ color, size = 8 }) => (
  <span style={{ position: "relative", display: "inline-block", width: size, height: size }}>
    <span style={{ position: "absolute", width: "100%", height: "100%", borderRadius: "50%", background: color, opacity: 0.4, animation: "fPulse 2s ease-in-out infinite" }} />
    <span style={{ position: "absolute", width: "100%", height: "100%", borderRadius: "50%", background: color }} />
  </span>
);

const Badge = ({ color, children, glow }) => (
  <span style={{
    display: "inline-flex", alignItems: "center", gap: 4,
    padding: "2px 8px", borderRadius: 3, fontSize: 9, fontWeight: 700,
    letterSpacing: "0.08em", fontFamily: "'JetBrains Mono', monospace",
    background: `${color}12`, color, border: `1px solid ${color}30`,
    boxShadow: glow ? `0 0 8px ${color}20` : "none",
  }}>{children}</span>
);

// ── FORJA WIZARD ──────────────────────────────────────────────────────────

const ForjaWizard = ({ onClose }) => {
  const [step, setStep] = useState(1);
  const [agentName, setAgentName] = useState("");
  const [selectedRole, setSelectedRole] = useState(null);
  const [selectedSpecialty, setSelectedSpecialty] = useState(null);
  const [agentDesc, setAgentDesc] = useState("");
  const [docLimit, setDocLimit] = useState(10);
  const [showConfirm, setShowConfirm] = useState(false);

  const currentStep = FORGE_STEPS[step - 1];
  const progress = (step / FORGE_STEPS.length) * 100;

  return (
    <div style={{
      background: "linear-gradient(170deg, #1A0E0A 0%, #2A1810 30%, #1A0E0A 100%)",
      borderRadius: 8, maxWidth: 700, width: "95%", maxHeight: "90vh", overflow: "auto",
      border: "2px solid #8B451380", position: "relative",
      boxShadow: "0 20px 80px rgba(139,69,19,0.3), inset 0 1px 0 rgba(255,200,100,0.05)",
    }}>
      {/* Forge ambient glow */}
      <div style={{
        position: "absolute", top: 0, left: "50%", transform: "translateX(-50%)",
        width: "60%", height: 120, pointerEvents: "none",
        background: `radial-gradient(ellipse, ${currentStep.color}15 0%, transparent 70%)`,
        transition: "background 0.8s ease",
      }} />

      {/* Header */}
      <div style={{ padding: "20px 28px 0", position: "relative" }}>
        <button onClick={onClose} style={{
          position: "absolute", top: 16, right: 20, background: "none",
          border: "none", fontSize: 18, color: "#6B4E3A", cursor: "pointer",
        }}>✕</button>

        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4 }}>
          <span style={{ fontSize: 28 }}>⚒</span>
          <div>
            <h2 style={{
              margin: 0, fontSize: 20, fontWeight: 700, color: "#F5E6D0",
              fontFamily: "'Playfair Display', serif",
            }}>FORJA DE AGENTES</h2>
            <div style={{
              fontSize: 9, color: "#B08D57", fontFamily: "'JetBrains Mono', monospace",
              letterSpacing: "0.15em", fontWeight: 600,
            }}>WINDI CONSTITUTIONAL FORGE</div>
          </div>
        </div>

        {/* Progress Bar */}
        <div style={{ margin: "16px 0 6px" }}>
          <div style={{
            display: "flex", justifyContent: "space-between", marginBottom: 8,
          }}>
            {FORGE_STEPS.map((s, i) => (
              <div key={s.id} style={{
                display: "flex", flexDirection: "column", alignItems: "center", flex: 1,
                opacity: step >= s.id ? 1 : 0.35, transition: "opacity 0.4s ease",
              }}>
                <div style={{
                  width: 32, height: 32, borderRadius: "50%",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 14,
                  background: step === s.id
                    ? `radial-gradient(circle, ${s.color}40, ${s.color}15)`
                    : step > s.id ? "rgba(45,106,79,0.15)" : "rgba(255,255,255,0.03)",
                  border: `2px solid ${step === s.id ? s.color : step > s.id ? "#2D6A4F" : "#3A2A1A"}`,
                  transition: "all 0.4s ease",
                  boxShadow: step === s.id ? `0 0 12px ${s.color}30` : "none",
                }}>{step > s.id ? "✓" : s.icon}</div>
                <span style={{
                  fontSize: 7, color: step === s.id ? s.color : "#6B4E3A",
                  fontFamily: "'JetBrains Mono', monospace", fontWeight: 700,
                  letterSpacing: "0.1em", marginTop: 4,
                }}>{s.name}</span>
              </div>
            ))}
          </div>
          <div style={{ height: 3, background: "#2A1810", borderRadius: 2, overflow: "hidden" }}>
            <div style={{
              height: "100%", borderRadius: 2, transition: "width 0.6s ease",
              width: `${progress}%`,
              background: `linear-gradient(90deg, #8B4513, ${currentStep.color}, #D4A76A)`,
            }} />
          </div>
        </div>
      </div>

      {/* Step Content */}
      <div style={{ padding: "20px 28px 24px" }}>

        {/* ── STEP 1: MINÉRIO ── */}
        {step === 1 && (
          <div style={{ animation: "fSlideIn 0.4s ease" }}>
            <div style={{
              fontSize: 11, color: "#C4A882", marginBottom: 20,
              fontFamily: "Georgia, serif", lineHeight: 1.6,
            }}>
              Todo Agent nasce de uma <strong style={{ color: "#F5E6D0" }}>essência</strong>. 
              Escolha o papel constitucional que definirá como seu Agent opera dentro do ecossistema WINDI.
              Este papel é permanente — como DNA.
            </div>

            {/* Agent Name */}
            <div style={{ marginBottom: 20 }}>
              <label style={{
                fontSize: 9, color: "#8B7E6A", fontFamily: "'JetBrains Mono', monospace",
                letterSpacing: "0.1em", fontWeight: 600, display: "block", marginBottom: 6,
              }}>NOME DO AGENT</label>
              <input
                value={agentName} onChange={e => setAgentName(e.target.value)}
                placeholder="Ex: DocShield, FinAudit, MedGuard..."
                style={{
                  width: "100%", padding: "10px 14px", borderRadius: 4,
                  background: "#0D0805", border: "1px solid #3A2A1A",
                  color: "#F5E6D0", fontSize: 14, fontFamily: "'Playfair Display', serif",
                  outline: "none", transition: "border 0.2s",
                }}
                onFocus={e => e.target.style.borderColor = "#B08D57"}
                onBlur={e => e.target.style.borderColor = "#3A2A1A"}
              />
            </div>

            {/* Role Selection */}
            <label style={{
              fontSize: 9, color: "#8B7E6A", fontFamily: "'JetBrains Mono', monospace",
              letterSpacing: "0.1em", fontWeight: 600, display: "block", marginBottom: 10,
            }}>PAPEL CONSTITUCIONAL — THREE DRAGONS PROTOCOL</label>
            <div style={{ display: "flex", gap: 10, marginBottom: 20 }}>
              {AGENT_ROLES.map(r => (
                <div key={r.role}
                  onClick={() => setSelectedRole(r.role)}
                  style={{
                    flex: 1, padding: 16, borderRadius: 6, cursor: "pointer",
                    background: selectedRole === r.role ? `${r.color}15` : "rgba(255,255,255,0.02)",
                    border: `2px solid ${selectedRole === r.role ? r.color : "#2A1810"}`,
                    transition: "all 0.3s ease",
                    boxShadow: selectedRole === r.role ? `0 0 15px ${r.color}15` : "none",
                  }}>
                  <div style={{ fontSize: 28, textAlign: "center", marginBottom: 8 }}>{r.icon}</div>
                  <div style={{
                    fontSize: 14, fontWeight: 700, color: r.color, textAlign: "center",
                    fontFamily: "'JetBrains Mono', monospace", letterSpacing: "0.06em",
                  }}>{r.role}</div>
                  <div style={{
                    fontSize: 10, color: "#8B7E6A", textAlign: "center", marginTop: 6,
                    fontFamily: "Georgia, serif", lineHeight: 1.5,
                  }}>{r.desc}</div>
                  <div style={{
                    fontSize: 8, color: "#5A4A3A", textAlign: "center", marginTop: 8,
                    fontFamily: "'JetBrains Mono', monospace", fontStyle: "italic",
                  }}>{r.examples}</div>
                </div>
              ))}
            </div>

            {/* Specialty */}
            <label style={{
              fontSize: 9, color: "#8B7E6A", fontFamily: "'JetBrains Mono', monospace",
              letterSpacing: "0.1em", fontWeight: 600, display: "block", marginBottom: 8,
            }}>ESPECIALIDADE</label>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
              {SPECIALTIES.map(s => (
                <span key={s} onClick={() => setSelectedSpecialty(s)}
                  style={{
                    padding: "5px 10px", borderRadius: 3, cursor: "pointer",
                    fontSize: 10, fontFamily: "'JetBrains Mono', monospace",
                    background: selectedSpecialty === s ? "rgba(176,141,87,0.15)" : "rgba(255,255,255,0.03)",
                    border: `1px solid ${selectedSpecialty === s ? "#B08D57" : "#2A1810"}`,
                    color: selectedSpecialty === s ? "#D4A76A" : "#6B4E3A",
                    transition: "all 0.2s",
                  }}>{s}</span>
              ))}
            </div>
          </div>
        )}

        {/* ── STEP 2: FOGO ── */}
        {step === 2 && (
          <div style={{ animation: "fSlideIn 0.4s ease" }}>
            <div style={{
              fontSize: 11, color: "#C4A882", marginBottom: 20,
              fontFamily: "Georgia, serif", lineHeight: 1.6,
            }}>
              O fogo da Forja purifica e define os <strong style={{ color: "#F5E6D0" }}>limites de atuação</strong>.
              Seu Agent precisa saber o que pode e o que não pode fazer — essa é a base da governança constitucional.
            </div>

            {/* Agent Description */}
            <label style={{
              fontSize: 9, color: "#8B7E6A", fontFamily: "'JetBrains Mono', monospace",
              letterSpacing: "0.1em", fontWeight: 600, display: "block", marginBottom: 6,
            }}>DESCRIÇÃO DA MISSÃO</label>
            <textarea
              value={agentDesc} onChange={e => setAgentDesc(e.target.value)}
              placeholder="Descreva o que seu Agent faz, para quem serve, e quais problemas resolve..."
              rows={3}
              style={{
                width: "100%", padding: "10px 14px", borderRadius: 4, resize: "vertical",
                background: "#0D0805", border: "1px solid #3A2A1A",
                color: "#F5E6D0", fontSize: 12, fontFamily: "Georgia, serif",
                outline: "none", lineHeight: 1.6,
              }}
            />

            {/* Behavioral Limits */}
            <div style={{ marginTop: 20 }}>
              <label style={{
                fontSize: 9, color: "#8B7E6A", fontFamily: "'JetBrains Mono', monospace",
                letterSpacing: "0.1em", fontWeight: 600, display: "block", marginBottom: 10,
              }}>LIMITES CONSTITUCIONAIS — Automáticos ✓</label>
              <div style={{
                background: "#0D0805", borderRadius: 4, padding: 14,
                border: "1px solid #2A1810",
              }}>
                {[
                  { inv: "I1", name: "Soberania Humana", desc: "Agent nunca decide — apenas propõe", auto: true },
                  { inv: "I5", name: "Separação de Papéis", desc: `Agent opera como ${selectedRole || "..."} exclusivamente`, auto: true },
                  { inv: "I9", name: "Proibição de Autonomia", desc: "IRREMEDIÁVEL — Agent não pode escalar poderes", auto: true, critical: true },
                  { inv: "I3", name: "Prova Criptográfica", desc: "Cada ação gera SHA-256 no Ledger", auto: true },
                  { inv: "I6", name: "Governança Silenciosa", desc: "Proteção opera invisível ao usuário final", auto: true },
                ].map(lim => (
                  <div key={lim.inv} style={{
                    display: "flex", alignItems: "center", gap: 10, padding: "6px 0",
                    borderBottom: "1px solid #1A0E0A",
                  }}>
                    <span style={{
                      fontSize: 9, fontWeight: 700, fontFamily: "'JetBrains Mono', monospace",
                      color: lim.critical ? "#E63946" : "#B08D57", minWidth: 22,
                    }}>{lim.inv}</span>
                    <span style={{ fontSize: 11, color: "#C4A882", flex: 1 }}>
                      <strong style={{ color: lim.critical ? "#E63946" : "#F5E6D0" }}>{lim.name}</strong>
                      <span style={{ color: "#6B4E3A", fontSize: 10 }}> — {lim.desc}</span>
                    </span>
                    <span style={{
                      fontSize: 8, padding: "1px 6px", borderRadius: 2,
                      background: "rgba(74,222,128,0.08)", color: "#4ADE80",
                      fontFamily: "'JetBrains Mono', monospace", fontWeight: 700,
                    }}>AUTO ✓</span>
                  </div>
                ))}
              </div>
              <div style={{
                marginTop: 8, fontSize: 9, color: "#5A4A3A", fontFamily: "'JetBrains Mono', monospace",
                textAlign: "center", fontStyle: "italic",
              }}>
                Estes limites são estruturais — não configuráveis, não opcionais.
              </div>
            </div>
          </div>
        )}

        {/* ── STEP 3: MARTELO ── */}
        {step === 3 && (
          <div style={{ animation: "fSlideIn 0.4s ease" }}>
            <div style={{
              fontSize: 11, color: "#C4A882", marginBottom: 20,
              fontFamily: "Georgia, serif", lineHeight: 1.6,
            }}>
              O martelo molda a <strong style={{ color: "#F5E6D0" }}>capacidade operacional</strong>.
              Defina os templates que seu Agent usa, o nível de análise SGE, e como documentos fluem pelo pipeline.
            </div>

            {/* ISP Templates */}
            <label style={{
              fontSize: 9, color: "#8B7E6A", fontFamily: "'JetBrains Mono', monospace",
              letterSpacing: "0.1em", fontWeight: 600, display: "block", marginBottom: 8,
            }}>ISP TEMPLATES DISPONÍVEIS (Freemium: 2 · Upgrade para mais)</label>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: 20 }}>
              {[
                { name: "EU Standard", grade: "A", usage: "124 agents" },
                { name: "Mittelstand", grade: "A", usage: "203 agents" },
                { name: "Deutsche Bahn", grade: "A", usage: "89 agents", locked: true },
                { name: "Bundesregierung", grade: "A", usage: "67 agents", locked: true },
                { name: "Academic Research", grade: "A", usage: "156 agents", locked: true },
                { name: "Legal Compliance", grade: "A", usage: "98 agents", locked: true },
              ].map((isp, i) => (
                <div key={isp.name} style={{
                  padding: "10px 12px", borderRadius: 4,
                  background: isp.locked ? "rgba(255,255,255,0.01)" : "rgba(45,106,79,0.08)",
                  border: `1px solid ${isp.locked ? "#2A1810" : "#2D6A4F40"}`,
                  opacity: isp.locked ? 0.5 : 1,
                  display: "flex", justifyContent: "space-between", alignItems: "center",
                }}>
                  <div>
                    <div style={{ fontSize: 11, fontWeight: 600, color: isp.locked ? "#5A4A3A" : "#F5E6D0" }}>
                      {isp.locked ? "🔒 " : "✓ "}{isp.name}
                    </div>
                    <div style={{ fontSize: 8, color: "#5A4A3A", fontFamily: "'JetBrains Mono', monospace", marginTop: 2 }}>
                      {isp.usage}
                    </div>
                  </div>
                  <Badge color={isp.locked ? "#5A4A3A" : "#2D6A4F"}>Grade {isp.grade}</Badge>
                </div>
              ))}
            </div>

            {/* SGE Levels */}
            <label style={{
              fontSize: 9, color: "#8B7E6A", fontFamily: "'JetBrains Mono', monospace",
              letterSpacing: "0.1em", fontWeight: 600, display: "block", marginBottom: 8,
            }}>SGE RISK ANALYSIS — 6 Camadas Automáticas</label>
            <div style={{ display: "flex", gap: 6 }}>
              {["R0 Safe", "R1 Low", "R2 Medium", "R3 High", "R4 Critical", "R5 Block"].map((r, i) => (
                <div key={r} style={{
                  flex: 1, textAlign: "center", padding: "8px 4px", borderRadius: 4,
                  background: i < 2 ? "rgba(45,106,79,0.1)" : i < 4 ? "rgba(233,196,106,0.08)" : "rgba(230,57,70,0.08)",
                  border: `1px solid ${i < 2 ? "#2D6A4F30" : i < 4 ? "#E9C46A20" : "#E6394620"}`,
                }}>
                  <div style={{
                    fontSize: 9, fontWeight: 700, fontFamily: "'JetBrains Mono', monospace",
                    color: i < 2 ? "#2D6A4F" : i < 4 ? "#E9C46A" : "#E63946",
                  }}>{r}</div>
                  <div style={{ fontSize: 7, color: "#5A4A3A", marginTop: 2, fontFamily: "'JetBrains Mono', monospace" }}>
                    {i < 2 ? "auto-pass" : i < 4 ? "flag+review" : "auto-block"}
                  </div>
                </div>
              ))}
            </div>

            {/* Doc Limit */}
            <div style={{ marginTop: 20 }}>
              <label style={{
                fontSize: 9, color: "#8B7E6A", fontFamily: "'JetBrains Mono', monospace",
                letterSpacing: "0.1em", fontWeight: 600, display: "block", marginBottom: 6,
              }}>DOCUMENT PIPELINE — Capacidade</label>
              <div style={{
                background: "#0D0805", borderRadius: 4, padding: 14,
                border: "1px solid #2A1810",
              }}>
                <div style={{
                  display: "flex", justifyContent: "space-between", alignItems: "center",
                }}>
                  <span style={{ fontSize: 11, color: "#C4A882" }}>Freemium: 3 docs/dia</span>
                  <span style={{ fontSize: 11, color: "#5A4A3A" }}>→ Flow: D1 → SGE → ISP → Export → Ledger</span>
                </div>
                <div style={{
                  marginTop: 8, fontSize: 9, color: "#B08D57", fontFamily: "'JetBrains Mono', monospace",
                }}>
                  💡 Upgrade via DROPS para aumentar capacidade
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── STEP 4: TÊMPERA ── */}
        {step === 4 && (
          <div style={{ animation: "fSlideIn 0.4s ease" }}>
            <div style={{
              fontSize: 11, color: "#C4A882", marginBottom: 20,
              fontFamily: "Georgia, serif", lineHeight: 1.6,
            }}>
              A têmpera sela a <strong style={{ color: "#F5E6D0" }}>identidade criptográfica</strong>.
              Seu Agent recebe Wallet Ed25519, conexão ao Sentinel, e acesso ao Forensic Ledger. Este passo é irreversível.
            </div>

            {/* Sealing Process */}
            <div style={{
              background: "#0D0805", borderRadius: 6, padding: 20, border: "1px solid #1A3325",
            }}>
              {[
                { label: "Wallet Ed25519", desc: "Identidade criptográfica única e irrevogável", status: "PRONTO", icon: "◈", color: "#B08D57" },
                { label: "Sentinel LAW v2.0", desc: "Monitoramento contínuo com 5-tier escalation", status: "CONECTAR", icon: "△", color: "#4ADE80" },
                { label: "Forensic Ledger", desc: "Virtue Receipts SHA-256 para cada ação", status: "ATIVAR", icon: "⬡", color: "#D4A76A" },
                { label: "WAQP Evaluation", desc: "Teste de compliance constitucional", status: "PENDING", icon: "✦", color: "#7B5EA7" },
                { label: "Tier Assignment", desc: "BRONZE inicial — evolua por performance", status: "AUTO", icon: "★", color: "#CD7F32" },
              ].map((item, i) => (
                <div key={item.label} style={{
                  display: "flex", alignItems: "center", gap: 14, padding: "10px 0",
                  borderBottom: i < 4 ? "1px solid #152820" : "none",
                }}>
                  <div style={{
                    width: 36, height: 36, borderRadius: "50%",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: 16, background: `${item.color}10`, border: `1px solid ${item.color}30`,
                    color: item.color,
                  }}>{item.icon}</div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 12, fontWeight: 600, color: "#F5E6D0" }}>{item.label}</div>
                    <div style={{ fontSize: 10, color: "#5A8B6A" }}>{item.desc}</div>
                  </div>
                  <Badge color={item.color}>{item.status}</Badge>
                </div>
              ))}
            </div>

            {/* Tier Progression */}
            <div style={{
              marginTop: 16, padding: 14, borderRadius: 4,
              background: "rgba(212,167,106,0.05)", border: "1px solid rgba(212,167,106,0.15)",
            }}>
              <div style={{
                fontSize: 9, color: "#B08D57", fontFamily: "'JetBrains Mono', monospace",
                fontWeight: 700, letterSpacing: "0.1em", marginBottom: 8,
              }}>PROGRESSÃO DE TIER</div>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 16 }}>
                {[
                  { tier: "BRONZE", score: "70%+", icon: "◆" },
                  { tier: "SILVER", score: "85%+", icon: "☆" },
                  { tier: "GOLD", score: "95%+", icon: "★" },
                ].map((t, i) => (
                  <div key={t.tier} style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <div style={{ textAlign: "center" }}>
                      <span style={{ fontSize: 18, color: LEVEL_COLORS[t.tier] }}>{t.icon}</span>
                      <div style={{ fontSize: 10, fontWeight: 700, color: LEVEL_COLORS[t.tier], fontFamily: "'JetBrains Mono', monospace" }}>{t.tier}</div>
                      <div style={{ fontSize: 8, color: "#5A4A3A" }}>Gov {t.score}</div>
                    </div>
                    {i < 2 && <span style={{ fontSize: 14, color: "#3A2A1A" }}>→</span>}
                  </div>
                ))}
              </div>
              <div style={{ fontSize: 9, color: "#6B4E3A", textAlign: "center", marginTop: 8, fontFamily: "Georgia, serif" }}>
                Tier evolui automaticamente baseado no Gov Score acumulado pelo Agent em operação.
              </div>
            </div>
          </div>
        )}

        {/* ── STEP 5: SELO ── */}
        {step === 5 && (
          <div style={{ animation: "fSlideIn 0.4s ease" }}>
            <div style={{ textAlign: "center", marginBottom: 20 }}>
              <div style={{ fontSize: 56, marginBottom: 8, filter: "drop-shadow(0 0 20px rgba(176,141,87,0.3))" }}>🐉</div>
              <h3 style={{
                fontSize: 20, fontFamily: "'Playfair Display', serif",
                fontWeight: 700, color: "#F5E6D0", margin: "0 0 4px",
              }}>Seu Agent está pronto para nascer</h3>
              <div style={{
                fontSize: 10, color: "#B08D57", fontFamily: "'JetBrains Mono', monospace",
              }}>Revise e confirme para selar na blockchain constitucional</div>
            </div>

            {/* Agent Summary */}
            <div style={{
              background: "#0D0805", borderRadius: 6, padding: 20, border: "1px solid #3A2A1A",
              marginBottom: 16,
            }}>
              <div style={{
                display: "flex", justifyContent: "space-between", alignItems: "flex-start",
                marginBottom: 14, paddingBottom: 14, borderBottom: "1px solid #1A0E0A",
              }}>
                <div>
                  <div style={{
                    fontSize: 22, fontWeight: 700, color: "#F5E6D0",
                    fontFamily: "'Playfair Display', serif",
                  }}>{agentName || "Meu Agent"}</div>
                  <div style={{
                    fontSize: 10, color: "#6B4E3A", fontFamily: "'JetBrains Mono', monospace", marginTop: 2,
                  }}>AGT-{selectedRole?.toUpperCase().slice(0, 4) || "XXXX"}-NEW</div>
                </div>
                <div style={{ display: "flex", gap: 6 }}>
                  {selectedRole && <Badge color={ROLE_COLORS[selectedRole]} glow>
                    {selectedRole === "Guardian" ? "🛡" : selectedRole === "Architect" ? "🏗" : "👁"} {selectedRole}
                  </Badge>}
                  <Badge color="#CD7F32" glow>◆ BRONZE</Badge>
                </div>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, fontSize: 11 }}>
                {[
                  { label: "Especialidade", value: selectedSpecialty || "—" },
                  { label: "Missão", value: agentDesc || "—" },
                  { label: "ISP Templates", value: "2 (Freemium)" },
                  { label: "Doc Limit", value: "3/dia (Freemium)" },
                  { label: "Sentinel", value: "Basic monitoring" },
                  { label: "Ledger", value: "30-day retention" },
                ].map(f => (
                  <div key={f.label} style={{ padding: "6px 0" }}>
                    <span style={{
                      fontSize: 8, color: "#5A4A3A", fontFamily: "'JetBrains Mono', monospace",
                      letterSpacing: "0.08em", fontWeight: 600,
                    }}>{f.label.toUpperCase()}</span>
                    <div style={{ color: "#C4A882", marginTop: 2 }}>{f.value}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Constitutional Seal */}
            <div style={{
              padding: 14, borderRadius: 4, textAlign: "center",
              background: "rgba(45,106,79,0.08)", border: "1px solid rgba(45,106,79,0.2)",
            }}>
              <div style={{
                fontSize: 9, color: "#4ADE80", fontFamily: "'JetBrains Mono', monospace",
                fontWeight: 700, letterSpacing: "0.1em",
              }}>
                SELO CONSTITUCIONAL
              </div>
              <div style={{ fontSize: 10, color: "#7AAF8A", marginTop: 4, fontFamily: "Georgia, serif" }}>
                Wallet Ed25519 ✓ · Sentinel ✓ · Ledger ✓ · I9 ✓ · WAQP Eval ✓ · Three Dragons ✓
              </div>
            </div>
          </div>
        )}

        {/* Navigation */}
        <div style={{
          display: "flex", justifyContent: "space-between", alignItems: "center",
          marginTop: 24, paddingTop: 16, borderTop: "1px solid #2A1810",
        }}>
          <button
            onClick={() => setStep(Math.max(1, step - 1))}
            disabled={step === 1}
            style={{
              padding: "8px 20px", borderRadius: 4, cursor: step === 1 ? "default" : "pointer",
              background: "transparent", border: "1px solid #3A2A1A",
              color: step === 1 ? "#3A2A1A" : "#8B7E6A", fontSize: 11,
              fontFamily: "'JetBrains Mono', monospace", fontWeight: 600,
              opacity: step === 1 ? 0.3 : 1, transition: "all 0.2s",
            }}>← Voltar</button>

          <div style={{
            fontSize: 9, color: "#5A4A3A", fontFamily: "'JetBrains Mono', monospace",
          }}>Passo {step} de {FORGE_STEPS.length}</div>

          <button
            onClick={() => step < 5 ? setStep(step + 1) : setShowConfirm(true)}
            style={{
              padding: "8px 24px", borderRadius: 4, cursor: "pointer",
              background: step === 5 ? "linear-gradient(135deg, #B08D57, #D4A76A)" : "linear-gradient(135deg, #2D6A4F, #40916C)",
              border: "none", color: step === 5 ? "#1A0E0A" : "#F5E6D0",
              fontSize: 12, fontFamily: "'JetBrains Mono', monospace", fontWeight: 700,
              letterSpacing: "0.06em", transition: "all 0.2s",
              boxShadow: `0 4px 12px ${step === 5 ? "rgba(176,141,87,0.3)" : "rgba(45,106,79,0.3)"}`,
            }}>{step === 5 ? "⚒ SELAR AGENT" : "Próximo →"}</button>
        </div>

        {showConfirm && (
          <div style={{
            marginTop: 16, padding: 16, borderRadius: 6, textAlign: "center",
            background: "rgba(176,141,87,0.08)", border: "2px solid #B08D57",
            animation: "fSlideIn 0.3s ease",
          }}>
            <div style={{ fontSize: 24, marginBottom: 8 }}>⚒🐉</div>
            <div style={{ fontSize: 14, fontWeight: 700, color: "#F5E6D0", fontFamily: "'Playfair Display', serif" }}>
              Agent "{agentName || "Meu Agent"}" forjado com sucesso!
            </div>
            <div style={{ fontSize: 10, color: "#B08D57", marginTop: 4, fontFamily: "'JetBrains Mono', monospace" }}>
              Wallet Ed25519 selado · Sentinel conectado · Ledger ativo · Tier: BRONZE
            </div>
            <div style={{ fontSize: 9, color: "#6B4E3A", marginTop: 8, fontFamily: "Georgia, serif" }}>
              "AI processes. Human decides. WINDI guarantees."
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// ── DROPS & FREEMIUM COMPARISON ───────────────────────────────────────────

const BusinessModelPanel = ({ onOpenForge }) => {
  const [modelView, setModelView] = useState("compare");

  return (
    <div style={{ animation: "fSlideIn 0.3s ease" }}>
      {/* Toggle */}
      <div style={{
        display: "flex", gap: 6, marginBottom: 20, justifyContent: "center",
      }}>
        {[
          { key: "compare", label: "Comparar Modelos" },
          { key: "drops", label: "Pacotes DROPS" },
          { key: "freemium", label: "Freemium Details" },
        ].map(t => (
          <button key={t.key} onClick={() => setModelView(t.key)}
            style={{
              padding: "6px 16px", borderRadius: 3, cursor: "pointer",
              fontSize: 10, fontFamily: "'JetBrains Mono', monospace", fontWeight: 600,
              letterSpacing: "0.06em", border: `1px solid ${modelView === t.key ? "#B08D57" : "#D4C9A8"}`,
              background: modelView === t.key ? "rgba(176,141,87,0.1)" : "transparent",
              color: modelView === t.key ? "#B08D57" : "#8B7E6A",
              transition: "all 0.2s",
            }}>{t.label}</button>
        ))}
      </div>

      {/* ── Compare Models ── */}
      {modelView === "compare" && (
        <div style={{
          display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20,
        }}>
          {/* Freemium Agent */}
          <div style={{
            background: "#FAF6ED", border: "2px solid #2D6A4F", borderRadius: 8,
            padding: 24, position: "relative", overflow: "hidden",
          }}>
            <div style={{
              position: "absolute", top: 0, left: 0, right: 0, height: 4,
              background: "linear-gradient(90deg, #2D6A4F, #40916C)",
            }} />
            <div style={{ textAlign: "center", marginBottom: 16 }}>
              <div style={{ fontSize: 32 }}>🌱</div>
              <h3 style={{
                fontSize: 18, fontFamily: "'Playfair Display', serif",
                fontWeight: 700, color: "#2D6A4F", margin: "8px 0 4px",
              }}>FREEMIUM AGENT</h3>
              <div style={{
                fontSize: 28, fontWeight: 300, color: "#2C2416",
                fontFamily: "'Playfair Display', serif",
              }}>€0 <span style={{ fontSize: 12, color: "#8B7E6A" }}>/ para sempre</span></div>
            </div>

            <div style={{
              fontSize: 11, color: "#6B5E4A", fontFamily: "Georgia, serif",
              textAlign: "center", lineHeight: 1.6, marginBottom: 16,
              padding: "0 8px",
            }}>
              Comece grátis. Crie seu primeiro Agent com governança constitucional completa.
              Perfeito para experimentar e aprender a Forja.
            </div>

            {FREEMIUM_LIMITS.features.map((f, i) => (
              <div key={i} style={{
                display: "flex", alignItems: "center", gap: 8, padding: "5px 0",
                fontSize: 11, color: "#2C2416",
              }}>
                <span style={{ color: "#2D6A4F", fontSize: 10 }}>✓</span> {f}
              </div>
            ))}

            <div style={{ marginTop: 12, paddingTop: 12, borderTop: "1px solid #E8E0C8" }}>
              <div style={{
                fontSize: 9, color: "#8B7E6A", fontFamily: "'JetBrains Mono', monospace",
                fontWeight: 600, marginBottom: 6,
              }}>NÃO INCLUI:</div>
              {FREEMIUM_LIMITS.locked.map((f, i) => (
                <div key={i} style={{
                  display: "flex", alignItems: "center", gap: 8, padding: "3px 0",
                  fontSize: 10, color: "#A09580",
                }}>
                  <span style={{ fontSize: 9 }}>🔒</span> {f}
                </div>
              ))}
            </div>

            <button onClick={onOpenForge} style={{
              width: "100%", marginTop: 16, padding: "12px 0", borderRadius: 4,
              background: "linear-gradient(135deg, #2D6A4F, #40916C)",
              border: "none", color: "#F5E6D0", fontSize: 12, fontWeight: 700,
              fontFamily: "'JetBrains Mono', monospace", cursor: "pointer",
              letterSpacing: "0.06em",
            }}>CRIAR AGENT GRÁTIS</button>
          </div>

          {/* DROPS Model */}
          <div style={{
            background: "#FAF6ED", border: "2px solid #B08D57", borderRadius: 8,
            padding: 24, position: "relative", overflow: "hidden",
          }}>
            <div style={{
              position: "absolute", top: 0, left: 0, right: 0, height: 4,
              background: "linear-gradient(90deg, #B08D57, #E25822, #D4A76A)",
            }} />
            <div style={{
              position: "absolute", top: 12, right: 12, padding: "3px 10px",
              background: "#E25822", borderRadius: 3, fontSize: 8, fontWeight: 700,
              color: "#FFF", fontFamily: "'JetBrains Mono', monospace", letterSpacing: "0.1em",
            }}>RECOMENDADO</div>

            <div style={{ textAlign: "center", marginBottom: 16 }}>
              <div style={{ fontSize: 32 }}>🔥</div>
              <h3 style={{
                fontSize: 18, fontFamily: "'Playfair Display', serif",
                fontWeight: 700, color: "#B08D57", margin: "8px 0 4px",
              }}>DROPS MODEL</h3>
              <div style={{
                fontSize: 16, fontWeight: 300, color: "#2C2416",
                fontFamily: "'Playfair Display', serif",
              }}>A partir de <span style={{ fontSize: 24, fontWeight: 700 }}>€29</span> <span style={{ fontSize: 12, color: "#8B7E6A" }}>/ pacote</span></div>
            </div>

            <div style={{
              fontSize: 11, color: "#6B5E4A", fontFamily: "Georgia, serif",
              textAlign: "center", lineHeight: 1.6, marginBottom: 16,
              padding: "0 8px",
            }}>
              Compre DROPS quando precisar. Sem assinatura. Sem compromisso mensal.
              Cada DROP = capacidade de processamento na Forja.
            </div>

            <div style={{
              background: "rgba(176,141,87,0.06)", borderRadius: 4, padding: 12,
              border: "1px solid rgba(176,141,87,0.15)", marginBottom: 12,
            }}>
              <div style={{
                fontSize: 9, color: "#B08D57", fontFamily: "'JetBrains Mono', monospace",
                fontWeight: 700, letterSpacing: "0.1em", marginBottom: 6,
              }}>COMO DROPS FUNCIONAM</div>
              <div style={{ fontSize: 10, color: "#6B5E4A", lineHeight: 1.6, fontFamily: "Georgia, serif" }}>
                1 DROP = 1 documento processado com governança completa.
                Compre pacotes, use quando quiser. Drops não expiram.
                Quanto maior o pacote, menor o custo por DROP.
              </div>
            </div>

            {[
              "Múltiplos Agents", "Docs ilimitados (com drops)", "Todos ISP templates",
              "Priority Sentinel", "Wisdom Protocol", "API access",
            ].map((f, i) => (
              <div key={i} style={{
                display: "flex", alignItems: "center", gap: 8, padding: "5px 0",
                fontSize: 11, color: "#2C2416",
              }}>
                <span style={{ color: "#B08D57", fontSize: 10 }}>★</span> {f}
              </div>
            ))}

            <button onClick={onOpenForge} style={{
              width: "100%", marginTop: 16, padding: "12px 0", borderRadius: 4,
              background: "linear-gradient(135deg, #B08D57, #D4A76A)",
              border: "none", color: "#1A0E0A", fontSize: 12, fontWeight: 700,
              fontFamily: "'JetBrains Mono', monospace", cursor: "pointer",
              letterSpacing: "0.06em",
            }}>EXPLORAR PACOTES DROPS</button>
          </div>
        </div>
      )}

      {/* ── DROPS Packages ── */}
      {modelView === "drops" && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
          {DROPS_PACKAGES.map(pkg => (
            <div key={pkg.name} style={{
              background: "#FAF6ED", borderRadius: 6, padding: 20, position: "relative",
              border: pkg.popular ? `2px solid ${pkg.color}` : "1px solid #D4C9A8",
              boxShadow: pkg.popular ? `0 4px 20px ${pkg.color}15` : "0 1px 3px rgba(0,0,0,0.04)",
              overflow: "hidden",
            }}>
              {pkg.popular && (
                <div style={{
                  position: "absolute", top: 0, left: 0, right: 0, height: 3,
                  background: `linear-gradient(90deg, ${pkg.color}, ${pkg.color}CC)`,
                }} />
              )}
              <div style={{ textAlign: "center" }}>
                <Badge color={pkg.color}>{pkg.tag}</Badge>
                <h4 style={{
                  fontSize: 18, fontFamily: "'Playfair Display', serif",
                  fontWeight: 700, color: "#2C2416", margin: "10px 0 4px",
                }}>{pkg.name}</h4>
                <div style={{
                  fontSize: 32, fontWeight: 300, color: pkg.color,
                  fontFamily: "'Playfair Display', serif",
                }}>{pkg.price}</div>
                <div style={{
                  fontSize: 10, color: "#B08D57", fontFamily: "'JetBrains Mono', monospace",
                  fontWeight: 600, marginTop: 2,
                }}>{pkg.drops.toLocaleString()} DROPS</div>
                {pkg.drops > 100 && (
                  <div style={{
                    fontSize: 9, color: "#8B7E6A", fontFamily: "'JetBrains Mono', monospace",
                    marginTop: 2,
                  }}>€{(parseFloat(pkg.price.replace("€", "")) / pkg.drops).toFixed(3)}/drop</div>
                )}
                <div style={{
                  fontSize: 10, color: "#6B5E4A", marginTop: 8,
                  fontFamily: "Georgia, serif",
                }}>{pkg.desc}</div>
              </div>

              <div style={{ marginTop: 14, paddingTop: 12, borderTop: "1px solid #E8E0C8" }}>
                {pkg.includes.map((item, i) => (
                  <div key={i} style={{
                    fontSize: 10, color: "#4B4033", padding: "3px 0",
                    display: "flex", alignItems: "center", gap: 6,
                  }}>
                    <span style={{ color: pkg.color, fontSize: 8 }}>●</span> {item}
                  </div>
                ))}
              </div>

              <button style={{
                width: "100%", marginTop: 14, padding: "10px 0", borderRadius: 4,
                background: pkg.popular ? `linear-gradient(135deg, ${pkg.color}, ${pkg.color}CC)` : "transparent",
                border: pkg.popular ? "none" : `1px solid ${pkg.color}`,
                color: pkg.popular ? "#FFF" : pkg.color,
                fontSize: 10, fontWeight: 700, fontFamily: "'JetBrains Mono', monospace",
                cursor: "pointer", letterSpacing: "0.06em",
              }}>
                {pkg.price === "€0" ? "COMEÇAR GRÁTIS" : `COMPRAR ${pkg.drops} DROPS`}
              </button>
            </div>
          ))}
        </div>
      )}

      {/* ── Freemium Details ── */}
      {modelView === "freemium" && (
        <div style={{
          background: "#FAF6ED", border: "1px solid #D4C9A8", borderRadius: 6, padding: 24,
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 20 }}>
            <span style={{ fontSize: 36 }}>🌱</span>
            <div>
              <h3 style={{
                fontSize: 20, fontFamily: "'Playfair Display', serif",
                fontWeight: 700, color: "#2D6A4F", margin: 0,
              }}>Modelo Freemium — Detalhes Completos</h3>
              <div style={{ fontSize: 11, color: "#6B5E4A", fontFamily: "Georgia, serif", marginTop: 2 }}>
                Tudo que precisa para começar. Upgrade só quando quiser.
              </div>
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 }}>
            {/* What You Get */}
            <div style={{
              padding: 16, borderRadius: 4,
              background: "rgba(45,106,79,0.04)", border: "1px solid rgba(45,106,79,0.12)",
            }}>
              <div style={{
                fontSize: 9, color: "#2D6A4F", fontFamily: "'JetBrains Mono', monospace",
                fontWeight: 700, letterSpacing: "0.1em", marginBottom: 10,
              }}>✓ INCLUÍDO GRÁTIS</div>
              {[
                "1 Agent slot (qualquer papel)",
                "3 documentos/dia processados",
                "2 ISP templates trilíngues",
                "Wallet Ed25519 completo",
                "Sentinel Basic monitoring",
                "Forensic Ledger 30 dias",
                "Acesso à Torre de Observação",
                "Community support forum",
                "WAQP certification path",
              ].map((f, i) => (
                <div key={i} style={{
                  fontSize: 10, color: "#2C2416", padding: "4px 0",
                  display: "flex", alignItems: "flex-start", gap: 6,
                }}>
                  <span style={{ color: "#2D6A4F", flexShrink: 0 }}>✓</span> {f}
                </div>
              ))}
            </div>

            {/* The Journey */}
            <div style={{
              padding: 16, borderRadius: 4,
              background: "rgba(176,141,87,0.04)", border: "1px solid rgba(176,141,87,0.12)",
            }}>
              <div style={{
                fontSize: 9, color: "#B08D57", fontFamily: "'JetBrains Mono', monospace",
                fontWeight: 700, letterSpacing: "0.1em", marginBottom: 10,
              }}>🗺 JORNADA DO FREEMIUM</div>
              {[
                { phase: "Dia 1", action: "Cria Wallet · Observa ecossistema" },
                { phase: "Dia 2-3", action: "Forja primeiro Agent · Testa sandbox" },
                { phase: "Semana 1", action: "Processa 21 docs · Recebe Gov Score" },
                { phase: "Semana 2-4", action: "Agent evolui · Tier BRONZE achievable" },
                { phase: "Mês 1+", action: "Decide: manter free ou upgrade DROPS" },
              ].map((j, i) => (
                <div key={i} style={{
                  padding: "6px 0", borderBottom: i < 4 ? "1px solid #E8E0C8" : "none",
                }}>
                  <div style={{
                    fontSize: 9, color: "#B08D57", fontFamily: "'JetBrains Mono', monospace",
                    fontWeight: 600,
                  }}>{j.phase}</div>
                  <div style={{ fontSize: 10, color: "#4B4033", marginTop: 2 }}>{j.action}</div>
                </div>
              ))}
            </div>

            {/* What's Different from Wild */}
            <div style={{
              padding: 16, borderRadius: 4,
              background: "rgba(139,69,19,0.04)", border: "1px solid rgba(139,69,19,0.12)",
            }}>
              <div style={{
                fontSize: 9, color: "#8B4513", fontFamily: "'JetBrains Mono', monospace",
                fontWeight: 700, letterSpacing: "0.1em", marginBottom: 10,
              }}>⚡ VS. AGENT "SELVAGEM"</div>
              {[
                { windi: "Ed25519 sealed identity", wild: "API key descartável" },
                { windi: "Sentinel monitoring 24/7", wild: "Zero monitoring" },
                { windi: "Forensic audit trail", wild: "Sem rastro" },
                { windi: "I9 impossibilidade estrutural", wild: "Prompt injection vuln" },
                { windi: "ISP institutional output", wild: "Output genérico" },
                { windi: "WAQP certification", wild: "Sem certificação" },
              ].map((c, i) => (
                <div key={i} style={{
                  padding: "5px 0", borderBottom: i < 5 ? "1px solid #E8E0C8" : "none",
                }}>
                  <div style={{ fontSize: 10, color: "#2D6A4F", display: "flex", alignItems: "center", gap: 4 }}>
                    <span style={{ fontSize: 8 }}>✓</span> {c.windi}
                  </div>
                  <div style={{ fontSize: 9, color: "#A09580", display: "flex", alignItems: "center", gap: 4, marginTop: 1 }}>
                    <span style={{ fontSize: 8 }}>✗</span> {c.wild}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// ══════════════════════════════════════════════════════════════════════════
// MAIN COMPONENT — TORRE + FORJA
// ══════════════════════════════════════════════════════════════════════════

export default function TorreForjaWindi() {
  const [activeTab, setActiveTab] = useState("observe");
  const [showForge, setShowForge] = useState(false);
  const [time, setTime] = useState(new Date());
  const [tickerIdx, setTickerIdx] = useState(0);
  const [glowAgent, setGlowAgent] = useState(null);

  useEffect(() => {
    const t1 = setInterval(() => setTime(new Date()), 1000);
    const t2 = setInterval(() => setTickerIdx(i => (i + 1) % LIVE_FORGE_ACTIVITY.length), 4000);
    const t3 = setInterval(() => {
      const idx = Math.floor(Math.random() * ECOSYSTEM_AGENTS.length);
      setGlowAgent(ECOSYSTEM_AGENTS[idx].name);
      setTimeout(() => setGlowAgent(null), 2000);
    }, 6000);
    return () => { clearInterval(t1); clearInterval(t2); clearInterval(t3); };
  }, []);

  return (
    <div style={{
      minHeight: "100vh",
      background: "linear-gradient(170deg, #F5F0E0 0%, #EDE7D3 40%, #E8E0C8 100%)",
      fontFamily: "Georgia, serif", color: "#2C2416",
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@300;400;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap');
        @keyframes fPulse { 0%,100% { transform:scale(1);opacity:.4 } 50% { transform:scale(2.2);opacity:0 } }
        @keyframes fSlideIn { from { opacity:0;transform:translateY(8px) } to { opacity:1;transform:translateY(0) } }
        @keyframes fFadeIn { from { opacity:0 } to { opacity:1 } }
        @keyframes fGlow { 0%,100% { box-shadow:0 0 8px rgba(176,141,87,.15) } 50% { box-shadow:0 0 20px rgba(176,141,87,.35) } }
        @keyframes forgeFlicker { 0%,100% { opacity:.8 } 25% { opacity:1 } 50% { opacity:.6 } 75% { opacity:.9 } }
        @keyframes tickerSlide { 0% { transform:translateX(100%) } 100% { transform:translateX(-100%) } }
        .ft-tab { cursor:pointer;padding:8px 18px;border-radius:4px 4px 0 0;font-size:11px;letter-spacing:.08em;text-transform:uppercase;font-family:'JetBrains Mono',monospace;font-weight:600;border:1px solid transparent;border-bottom:none;transition:all .2s;color:#8B7E6A }
        .ft-tab:hover { background:rgba(45,106,79,.04) }
        .ft-tab-active { background:#FAF6ED!important;border-color:#D4C9A8!important;color:#2D6A4F!important }
        .ft-tab-forge { color:#E25822!important }
        .ft-tab-forge.ft-tab-active { color:#E25822!important;border-color:#E25822!important;background:rgba(226,88,34,.04)!important }
        .ft-overlay { position:fixed;inset:0;background:rgba(0,0,0,.7);z-index:100;display:flex;align-items:center;justify-content:center;animation:fFadeIn .3s ease;backdrop-filter:blur(6px) }
        * { box-sizing:border-box;margin:0 }
        ::-webkit-scrollbar { width:6px }
        ::-webkit-scrollbar-track { background:transparent }
        ::-webkit-scrollbar-thumb { background:#D4C9A8;border-radius:3px }
      `}</style>

      {/* ── HEADER ── */}
      <div style={{
        background: "linear-gradient(135deg, #0D1B14 0%, #1B3A2D 50%, #0D1B14 100%)",
        padding: "18px 28px", position: "relative", overflow: "hidden",
        borderBottom: "2px solid #B08D57",
      }}>
        <div style={{
          position: "absolute", inset: 0, pointerEvents: "none", opacity: .02,
          backgroundImage: "repeating-linear-gradient(0deg,transparent,transparent 3px,rgba(74,222,128,.15) 3px,rgba(74,222,128,.15) 4px)",
        }} />
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", position: "relative" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
            <div style={{
              width: 44, height: 44, borderRadius: "50%", display: "flex",
              alignItems: "center", justifyContent: "center", fontSize: 24,
              background: "radial-gradient(circle,rgba(176,141,87,.2) 0%,transparent 70%)",
              border: "2px solid #B08D5740", animation: "fGlow 3s ease-in-out infinite",
            }}>🐉</div>
            <div>
              <h1 style={{
                fontSize: 18, fontWeight: 700, color: "#F5F0E0",
                fontFamily: "'Playfair Display',serif", letterSpacing: ".02em",
              }}>TORRE DE OBSERVAÇÃO + FORJA</h1>
              <div style={{
                fontSize: 9, color: "#B08D57", letterSpacing: ".18em",
                fontFamily: "'JetBrains Mono',monospace", fontWeight: 700, marginTop: 1,
              }}>OBSERVE · APRENDA · FORJE · DEPLOY</div>
            </div>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
            <Badge color="#B08D57">👁 OBSERVATORY + FORGE</Badge>
            <div style={{
              fontSize: 10, color: "#5A8B6A", fontFamily: "'JetBrains Mono',monospace", textAlign: "right",
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <Pulse color="#4ADE80" size={5} />
                <span>LIVE · {time.toLocaleTimeString("de-DE")}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── FORGE ACTIVITY TICKER ── */}
      <div style={{
        background: "#0D1B14", padding: "0 20px", height: 30,
        display: "flex", alignItems: "center", borderBottom: "1px solid #1A3325",
        overflow: "hidden",
      }}>
        <span style={{
          fontSize: 9, color: "#E25822", fontFamily: "'JetBrains Mono',monospace",
          fontWeight: 700, letterSpacing: ".1em", marginRight: 14, flexShrink: 0,
          display: "flex", alignItems: "center", gap: 5,
        }}>
          <span style={{ animation: "forgeFlicker 1.5s ease infinite" }}>⚒</span> FORJA LIVE
        </span>
        {LIVE_FORGE_ACTIVITY.map((ev, i) => (
          <span key={i} style={{
            fontSize: 10, fontFamily: "'JetBrains Mono',monospace",
            color: "#5A8B6A", whiteSpace: "nowrap", marginRight: 24,
            opacity: i === tickerIdx ? 1 : 0.4, transition: "opacity .5s",
            display: "inline-flex", alignItems: "center", gap: 6,
          }}>
            <span style={{ color: "#7AAF8A" }}>{ev.user}</span>
            <span style={{ color: "#4A7B5A" }}>{ev.action}</span>
            {ev.tier !== "—" && <Badge color={LEVEL_COLORS[ev.tier] || "#5A8B6A"}>{ev.tier}</Badge>}
            <span style={{ color: "#2A4B3A" }}>· {ev.time} ago</span>
          </span>
        ))}
      </div>

      {/* ── NAVIGATION ── */}
      <div style={{
        display: "flex", gap: 4, padding: "10px 28px 0",
        borderBottom: "1px solid #D4C9A8",
      }}>
        {[
          { key: "observe", label: "👁 Observar Ecosystem" },
          { key: "forge", label: "⚒ FORJA DE AGENTES", isForge: true },
          { key: "models", label: "💧 Freemium & DROPS" },
        ].map(tab => (
          <div key={tab.key}
            className={`ft-tab ${activeTab === tab.key ? "ft-tab-active" : ""} ${tab.isForge ? "ft-tab-forge" : ""}`}
            onClick={() => setActiveTab(tab.key)}
            style={tab.isForge && activeTab !== tab.key ? {
              background: "rgba(226,88,34,0.04)",
              animation: "forgeFlicker 3s ease infinite",
            } : {}}
          >{tab.label}</div>
        ))}
      </div>

      {/* ── CONTENT ── */}
      <div style={{ padding: "20px 28px", animation: "fFadeIn .4s ease" }}>

        {/* ═══ OBSERVE TAB ═══ */}
        {activeTab === "observe" && (
          <div style={{ animation: "fSlideIn .3s ease" }}>
            {/* Summary */}
            <div style={{
              display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 12, marginBottom: 20,
            }}>
              {[
                { label: "Agents no Ecossistema", value: ECOSYSTEM_AGENTS.length, color: "#2D6A4F" },
                { label: "Docs Processados", value: ECOSYSTEM_AGENTS.reduce((a, e) => a + e.docs, 0).toLocaleString(), color: "#B08D57" },
                { label: "Avg Gov Score", value: `${Math.round(ECOSYSTEM_AGENTS.reduce((a, e) => a + e.govScore, 0) / ECOSYSTEM_AGENTS.length)}%`, color: "#2D6A4F" },
                { label: "Agents Forjados Hoje", value: "3", color: "#E25822" },
              ].map(s => (
                <div key={s.label} style={{
                  background: "linear-gradient(135deg,#FAF6ED,#F0EBD8)", border: "1px solid #D4C9A8",
                  borderRadius: 6, padding: "14px 16px", textAlign: "center",
                }}>
                  <div style={{
                    fontSize: 8, color: "#8B7E6A", fontFamily: "'JetBrains Mono',monospace",
                    letterSpacing: ".1em", fontWeight: 600, textTransform: "uppercase",
                  }}>{s.label}</div>
                  <div style={{
                    fontSize: 28, fontWeight: 300, color: s.color,
                    fontFamily: "'Playfair Display',serif",
                  }}>{s.value}</div>
                </div>
              ))}
            </div>

            {/* Agent Grid */}
            <div style={{
              display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12, marginBottom: 24,
            }}>
              {ECOSYSTEM_AGENTS.map((agent, i) => {
                const isGlowing = glowAgent === agent.name;
                return (
                  <div key={agent.name} style={{
                    background: isGlowing ? "rgba(45,106,79,.05)" : "#FAF6ED",
                    border: `1px solid ${isGlowing ? "rgba(74,222,128,.25)" : "#D4C9A8"}`,
                    borderRadius: 6, padding: 16, transition: "all .4s ease",
                    boxShadow: isGlowing ? "0 0 15px rgba(74,222,128,.08)" : "0 1px 3px rgba(0,0,0,.04)",
                    animation: "fSlideIn .3s ease", animationDelay: `${i * 50}ms`, animationFillMode: "both",
                  }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
                      <div style={{
                        fontSize: 15, fontWeight: 700, color: "#2C2416",
                        fontFamily: "'Playfair Display',serif",
                      }}>{agent.name}</div>
                      <Badge color={LEVEL_COLORS[agent.level]}>
                        {agent.level === "GOLD" ? "★" : "☆"} {agent.level}
                      </Badge>
                    </div>
                    <div style={{ display: "flex", gap: 6, marginBottom: 8 }}>
                      <Badge color={ROLE_COLORS[agent.role]}>
                        {agent.role === "Guardian" ? "🛡" : agent.role === "Architect" ? "🏗" : "👁"} {agent.role}
                      </Badge>
                      <span style={{ fontSize: 9, color: "#8B7E6A", fontFamily: "'JetBrains Mono',monospace" }}>
                        by {agent.creator}
                      </span>
                    </div>
                    <div style={{
                      fontSize: 10, color: "#6B5E4A", fontFamily: "'JetBrains Mono',monospace",
                      padding: "5px 8px", background: "rgba(0,0,0,.02)", borderRadius: 3, marginBottom: 8,
                    }}>⚡ {agent.action}</div>
                    <div style={{
                      display: "flex", justifyContent: "space-between",
                      fontSize: 10, fontFamily: "'JetBrains Mono',monospace", color: "#8B7E6A",
                    }}>
                      <span>{agent.docs.toLocaleString()} docs</span>
                      <span style={{ color: "#2D6A4F", fontWeight: 700 }}>Gov {agent.govScore}%</span>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* CTA to Forge */}
            <div style={{
              background: "linear-gradient(135deg,#2A1810,#3A2218,#2A1810)",
              borderRadius: 8, padding: 28, textAlign: "center",
              border: "2px solid #8B451360", position: "relative", overflow: "hidden",
              cursor: "pointer",
            }} onClick={() => setActiveTab("forge")}>
              <div style={{
                position: "absolute", inset: 0, opacity: .03, pointerEvents: "none",
                backgroundImage: "radial-gradient(ellipse at center,rgba(226,88,34,.4) 0%,transparent 70%)",
              }} />
              <div style={{ position: "relative" }}>
                <div style={{ fontSize: 40, marginBottom: 8, animation: "forgeFlicker 2s ease infinite" }}>⚒🐉</div>
                <h2 style={{
                  fontSize: 22, fontFamily: "'Playfair Display',serif", fontWeight: 700,
                  color: "#F5E6D0", marginBottom: 8,
                }}>Pronto para Forjar seu Agent?</h2>
                <p style={{
                  fontSize: 12, color: "#A08060", fontFamily: "Georgia,serif",
                  lineHeight: 1.6, maxWidth: 500, margin: "0 auto 16px",
                }}>
                  Tudo que vê neste terminal — os Agents, a governança, os selos —
                  pode ser seu. Entre na Forja e crie. A constituição vem embutida.
                </p>
                <div style={{
                  display: "inline-flex", padding: "12px 32px", borderRadius: 4,
                  background: "linear-gradient(135deg,#E25822,#FF6B35)", color: "#FFF",
                  fontSize: 13, fontWeight: 700, fontFamily: "'JetBrains Mono',monospace",
                  letterSpacing: ".06em",
                }}>ENTRAR NA FORJA →</div>
              </div>
            </div>
          </div>
        )}

        {/* ═══ FORGE TAB ═══ */}
        {activeTab === "forge" && (
          <div style={{ animation: "fSlideIn .3s ease" }}>
            {/* Forge intro */}
            <div style={{
              background: "linear-gradient(135deg,#1A0E0A,#2A1810,#1A0E0A)",
              borderRadius: 8, padding: 24, marginBottom: 20,
              border: "1px solid #3A2A1A60", position: "relative", overflow: "hidden",
            }}>
              <div style={{
                position: "absolute", top: "50%", left: "50%", transform: "translate(-50%,-50%)",
                width: 200, height: 200, borderRadius: "50%", pointerEvents: "none",
                background: "radial-gradient(circle,rgba(226,88,34,.06) 0%,transparent 70%)",
              }} />
              <div style={{ position: "relative", textAlign: "center" }}>
                <div style={{ fontSize: 48, marginBottom: 8, animation: "forgeFlicker 2s ease infinite" }}>⚒</div>
                <h2 style={{
                  fontSize: 24, fontFamily: "'Playfair Display',serif", fontWeight: 700,
                  color: "#F5E6D0", marginBottom: 6,
                }}>A FORJA WINDI</h2>
                <div style={{
                  fontSize: 10, color: "#B08D57", fontFamily: "'JetBrains Mono',monospace",
                  letterSpacing: ".15em", fontWeight: 600, marginBottom: 12,
                }}>WINDI PROMPT SERVER · CONSTITUTIONAL AGENT FORGE</div>
                <p style={{
                  fontSize: 12, color: "#A08060", fontFamily: "Georgia,serif",
                  lineHeight: 1.7, maxWidth: 600, margin: "0 auto",
                }}>
                  A Forja é um servidor WINDI PROMPT especialmente projetado para criar Agents constitucionais.
                  Use os serviços WINDI gratuitamente, aprenda como funciona o ecossistema,
                  e quando estiver pronto — forje seu próprio Agent com todos os selos de segurança automaticamente.
                </p>
              </div>
            </div>

            {/* The 5 Forge Steps visual */}
            <div style={{
              display: "flex", gap: 8, marginBottom: 20,
            }}>
              {FORGE_STEPS.map((s, i) => (
                <div key={s.id} style={{
                  flex: 1, textAlign: "center", padding: "16px 8px", borderRadius: 6,
                  background: "#FAF6ED", border: "1px solid #D4C9A8",
                  transition: "all .2s",
                }}>
                  <div style={{
                    width: 40, height: 40, borderRadius: "50%", margin: "0 auto 8px",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: 20, background: `${s.color}10`, border: `2px solid ${s.color}30`,
                  }}>{s.icon}</div>
                  <div style={{
                    fontSize: 9, fontWeight: 700, color: s.color,
                    fontFamily: "'JetBrains Mono',monospace", letterSpacing: ".1em",
                  }}>{s.name}</div>
                  <div style={{
                    fontSize: 11, fontWeight: 600, color: "#2C2416", marginTop: 4,
                  }}>{s.title}</div>
                  <div style={{
                    fontSize: 9, color: "#8B7E6A", marginTop: 4,
                    fontFamily: "Georgia,serif", lineHeight: 1.4,
                  }}>{s.desc}</div>
                </div>
              ))}
            </div>

            {/* Open Forge Button */}
            <div style={{ textAlign: "center" }}>
              <button onClick={() => setShowForge(true)} style={{
                padding: "14px 48px", borderRadius: 6, cursor: "pointer",
                background: "linear-gradient(135deg,#E25822,#FF6B35)",
                border: "none", color: "#FFF", fontSize: 16, fontWeight: 700,
                fontFamily: "'JetBrains Mono',monospace", letterSpacing: ".06em",
                boxShadow: "0 6px 20px rgba(226,88,34,.3)",
                transition: "all .2s",
              }}>
                ⚒ ABRIR A FORJA — CRIAR MEU AGENT
              </button>
              <div style={{
                marginTop: 10, fontSize: 10, color: "#8B7E6A",
                fontFamily: "'JetBrains Mono',monospace",
              }}>Gratuito · Wallet Ed25519 · Sentinel · Ledger · I9 Compliant</div>
            </div>

            {/* Live Forge Activity */}
            <div style={{
              marginTop: 24, background: "#FAF6ED", border: "1px solid #D4C9A8",
              borderRadius: 6, padding: 20,
            }}>
              <div style={{
                fontSize: 9, letterSpacing: ".12em", textTransform: "uppercase",
                color: "#8B7E6A", fontWeight: 600, marginBottom: 14,
                fontFamily: "'JetBrains Mono',monospace",
                display: "flex", alignItems: "center", gap: 8,
              }}>
                <Pulse color="#E25822" /> Atividade da Forja — Outros Humanos Forjando Agora
              </div>
              {LIVE_FORGE_ACTIVITY.map((ev, i) => (
                <div key={i} style={{
                  display: "flex", gap: 14, padding: "8px 0",
                  borderBottom: i < LIVE_FORGE_ACTIVITY.length - 1 ? "1px solid #E8E0C8" : "none",
                  alignItems: "center",
                  animation: "fSlideIn .3s ease", animationDelay: `${i * 40}ms`, animationFillMode: "both",
                }}>
                  <span style={{
                    fontSize: 10, color: "#8B7E6A", fontFamily: "'JetBrains Mono',monospace",
                    minWidth: 50,
                  }}>{ev.time}</span>
                  <span style={{
                    fontSize: 10, color: "#B08D57", fontFamily: "'JetBrains Mono',monospace",
                    fontWeight: 600, minWidth: 130,
                  }}>{ev.user}</span>
                  <span style={{ fontSize: 11, color: "#4B4033", flex: 1 }}>{ev.action}</span>
                  {ev.role !== "—" && <Badge color={ROLE_COLORS[ev.role]}>{ev.role}</Badge>}
                  {ev.tier !== "—" && <Badge color={LEVEL_COLORS[ev.tier]}>{ev.tier}</Badge>}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ═══ MODELS TAB ═══ */}
        {activeTab === "models" && (
          <BusinessModelPanel onOpenForge={() => setShowForge(true)} />
        )}
      </div>

      {/* ── FORGE MODAL ── */}
      {showForge && (
        <div className="ft-overlay" onClick={() => setShowForge(false)}>
          <div onClick={e => e.stopPropagation()}>
            <ForjaWizard onClose={() => setShowForge(false)} />
          </div>
        </div>
      )}

      {/* ── FOOTER ── */}
      <div style={{
        padding: "12px 28px", borderTop: "1px solid #D4C9A8",
        display: "flex", justifyContent: "space-between",
        fontSize: 8, color: "#8B7E6A", fontFamily: "'JetBrains Mono',monospace",
        letterSpacing: ".08em",
      }}>
        <span>WINDI Publishing House · Kempten, Bavaria · Torre+Forja v1.0</span>
        <span>"AI processes. Human decides. WINDI guarantees."</span>
        <span>© 2026 Three Dragons Protocol</span>
      </div>
    </div>
  );
}
