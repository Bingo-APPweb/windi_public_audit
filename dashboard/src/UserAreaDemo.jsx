import { useState } from "react";

// ═══════════════════════════════════════════════════════════════════════════════
// WINDI User Area Panel — SVG Icon Edition v1.0
// All emoji icons replaced with monocromatic SVG inline icons
// Color: currentColor (inherits from parent) • Size: 20×20 • strokeWidth: 1.3
// ═══════════════════════════════════════════════════════════════════════════════

const TIER_CONFIG = {
  FREE: { label: "FREE", color: "#888", bg: "#f0f0f0", accent: "#666" },
  MED: { label: "MED", color: "#2563eb", bg: "#dbeafe", accent: "#1d4ed8" },
  HIGH: { label: "HIGH", color: "#92400e", bg: "#fef3c7", accent: "#b45309" },
};

const mockUser = {
  name: "Jober M. Correa",
  initials: "JM",
  email: "jober@jomedia.eu",
  did: "did:windi:7f3a...c91b",
  tier: "HIGH",
  pioneer: 1,
  wallet: {
    credits: 847,
    tokens_used: 12340,
    tokens_limit: 50000,
    last_recharge: "2026-03-05",
    plan: "Pioneer HIGH",
    next_billing: "2026-04-01",
  },
  keys: [
    { id: "wk_live_a8f2", label: "Production", active: true },
    { id: "wk_test_c3d1", label: "Sandbox", active: true },
  ],
  gov_score: 97.2,
  receipts: 40918,
  role: "admin",
};

// ─── SVG ICONS (20×20, strokeWidth 1.3, currentColor) ─────────────────────────
const Icons = {
  settings: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" style={{ flexShrink: 0 }}>
      <circle cx="10" cy="10" r="3" stroke="currentColor" strokeWidth="1.3" fill="none"/>
      <path d="M10 2V4M10 16V18M18 10H16M4 10H2M15.5 4.5L14 6M6 14L4.5 15.5M15.5 15.5L14 14M6 6L4.5 4.5"
        stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/>
    </svg>
  ),
  key: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" style={{ flexShrink: 0 }}>
      <circle cx="7" cy="7" r="4" stroke="currentColor" strokeWidth="1.3" fill="none"/>
      <path d="M10 10L17 17M14 17H17V14" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/>
      <circle cx="7" cy="7" r="1.2" fill="currentColor"/>
    </svg>
  ),
  user: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" style={{ flexShrink: 0 }}>
      <circle cx="10" cy="7" r="3.5" stroke="currentColor" strokeWidth="1.3" fill="none"/>
      <path d="M3.5 17.5C3.5 14 6.5 12 10 12C13.5 12 16.5 14 16.5 17.5"
        stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" fill="none"/>
    </svg>
  ),
  shield: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" style={{ flexShrink: 0 }}>
      <path d="M10 2.5L17 5.5V10.5C17 14 13.5 17 10 18C6.5 17 3 14 3 10.5V5.5L10 2.5Z"
        stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round" fill="none"/>
      <path d="M7 10L9 12L13 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  chart: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" style={{ flexShrink: 0 }}>
      <rect x="3" y="3" width="14" height="14" rx="1.5" stroke="currentColor" strokeWidth="1.3" fill="none"/>
      <rect x="5.5" y="10" width="2" height="5" rx="0.5" stroke="currentColor" strokeWidth="1.0" fill="none"/>
      <rect x="9" y="7" width="2" height="8" rx="0.5" stroke="currentColor" strokeWidth="1.0" fill="none"/>
      <rect x="12.5" y="9" width="2" height="6" rx="0.5" stroke="currentColor" strokeWidth="1.0" fill="none"/>
    </svg>
  ),
  robot: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" style={{ flexShrink: 0 }}>
      <rect x="5" y="7" width="10" height="8" rx="2" stroke="currentColor" strokeWidth="1.3" fill="none"/>
      <rect x="8" y="4" width="4" height="3" rx="1" stroke="currentColor" strokeWidth="1.2" fill="none"/>
      <line x1="10" y1="4" x2="10" y2="3" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
      <circle cx="8" cy="11" r="1" fill="currentColor"/>
      <circle cx="12" cy="11" r="1" fill="currentColor"/>
      <line x1="8" y1="13.5" x2="12" y2="13.5" stroke="currentColor" strokeWidth="1.0" strokeLinecap="round"/>
      <line x1="3" y1="10" x2="5" y2="10" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
      <line x1="15" y1="10" x2="17" y2="10" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
    </svg>
  ),
  clipboard: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" style={{ flexShrink: 0 }}>
      <rect x="4" y="4" width="12" height="14" rx="1.5" stroke="currentColor" strokeWidth="1.3" fill="none"/>
      <path d="M7 4V3C7 2.45 7.45 2 8 2H12C12.55 2 13 2.45 13 3V4"
        stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" fill="none"/>
      <line x1="7" y1="8" x2="13" y2="8" stroke="currentColor" strokeWidth="1.0" strokeLinecap="round"/>
      <line x1="7" y1="11" x2="13" y2="11" stroke="currentColor" strokeWidth="1.0" strokeLinecap="round"/>
      <line x1="7" y1="14" x2="10" y2="14" stroke="currentColor" strokeWidth="1.0" strokeLinecap="round"/>
    </svg>
  ),
  gift: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" style={{ flexShrink: 0 }}>
      <rect x="3" y="8" width="14" height="3" rx="1" stroke="currentColor" strokeWidth="1.3" fill="none"/>
      <rect x="4" y="11" width="12" height="6" rx="1" stroke="currentColor" strokeWidth="1.3" fill="none"/>
      <line x1="10" y1="8" x2="10" y2="17" stroke="currentColor" strokeWidth="1.0" strokeLinecap="round"/>
      <path d="M10 8C10 8 8 8 7 6.5C6 5 7 3.5 8.5 4C10 4.5 10 6 10 8"
        stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" fill="none"/>
      <path d="M10 8C10 8 12 8 13 6.5C14 5 13 3.5 11.5 4C10 4.5 10 6 10 8"
        stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" fill="none"/>
    </svg>
  ),
  logout: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" style={{ flexShrink: 0 }}>
      <path d="M7 4H5C4.45 4 4 4.45 4 5V15C4 15.55 4.45 16 5 16H7"
        stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" fill="none"/>
      <path d="M10 10H17M17 10L14 7M17 10L14 13"
        stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  creditCard: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" style={{ flexShrink: 0 }}>
      <rect x="3" y="5" width="14" height="11" rx="1.5" stroke="currentColor" strokeWidth="1.3" fill="none"/>
      <line x1="3" y1="9" x2="17" y2="9" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
      <rect x="12" y="11" width="4" height="2.5" rx="0.5" stroke="currentColor" strokeWidth="1.0" fill="none"/>
      <circle cx="13.5" cy="12.2" r="0.5" fill="currentColor"/>
    </svg>
  ),
  document: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" style={{ flexShrink: 0 }}>
      <path d="M5 3H12.5L16 6.5V17H5V3Z" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round" fill="none"/>
      <path d="M12.5 3V6.5H16" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round" fill="none"/>
      <line x1="7.5" y1="9" x2="13.5" y2="9" stroke="currentColor" strokeWidth="1.0" strokeLinecap="round"/>
      <line x1="7.5" y1="11.5" x2="13.5" y2="11.5" stroke="currentColor" strokeWidth="1.0" strokeLinecap="round"/>
      <line x1="7.5" y1="14" x2="11" y2="14" stroke="currentColor" strokeWidth="1.0" strokeLinecap="round"/>
    </svg>
  ),
  bell: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" style={{ flexShrink: 0 }}>
      <path d="M10 3C7.5 3 5.5 5 5.5 7.5V11L4 13V14H16V13L14.5 11V7.5C14.5 5 12.5 3 10 3Z"
        stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round" fill="none"/>
      <path d="M8 14C8 15.1 8.9 16 10 16C11.1 16 12 15.1 12 14"
        stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" fill="none"/>
      <line x1="10" y1="1.5" x2="10" y2="3" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
    </svg>
  ),
  plus: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" style={{ flexShrink: 0 }}>
      <circle cx="10" cy="10" r="7" stroke="currentColor" strokeWidth="1.3" fill="none"/>
      <line x1="10" y1="6" x2="10" y2="14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
      <line x1="6" y1="10" x2="14" y2="10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
    </svg>
  ),
  idCard: (
    <svg width="18" height="18" viewBox="0 0 20 20" fill="none" style={{ flexShrink: 0 }}>
      <rect x="2" y="4" width="16" height="12" rx="1.5" stroke="currentColor" strokeWidth="1.2" fill="none"/>
      <circle cx="7" cy="9" r="2" stroke="currentColor" strokeWidth="1.0" fill="none"/>
      <path d="M4 14C4 12 5.5 11 7 11C8.5 11 10 12 10 14" stroke="currentColor" strokeWidth="1.0" strokeLinecap="round" fill="none"/>
      <line x1="12" y1="8" x2="16" y2="8" stroke="currentColor" strokeWidth="1.0" strokeLinecap="round"/>
      <line x1="12" y1="11" x2="15" y2="11" stroke="currentColor" strokeWidth="1.0" strokeLinecap="round"/>
    </svg>
  ),
};

function CreditsBar({ used, limit }) {
  const pct = Math.min((used / limit) * 100, 100);
  const color = pct > 80 ? "#ef4444" : pct > 60 ? "#f59e0b" : "#10b981";
  return (
    <div style={{ marginTop: 6 }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 10, color: "#888", marginBottom: 3, fontFamily: "'JetBrains Mono', monospace" }}>
        <span>{used.toLocaleString()} tokens</span>
        <span>{limit.toLocaleString()} limit</span>
      </div>
      <div style={{ height: 4, background: "#e5e0d4", borderRadius: 2, overflow: "hidden" }}>
        <div style={{ height: "100%", width: `${pct}%`, background: color, borderRadius: 2, transition: "width 0.6s ease" }} />
      </div>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <div style={{ padding: "12px 16px" }}>
      {title && (
        <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: "0.12em", color: "#aaa", textTransform: "uppercase", marginBottom: 8, fontFamily: "'JetBrains Mono', monospace" }}>
          {title}
        </div>
      )}
      {children}
    </div>
  );
}

function MenuItem({ icon, label, sublabel, badge, onClick, danger, accent }) {
  const [hov, setHov] = useState(false);
  return (
    <div
      onClick={onClick}
      onMouseEnter={() => setHov(true)}
      onMouseLeave={() => setHov(false)}
      style={{
        display: "flex", alignItems: "center", gap: 10, padding: "8px 10px",
        borderRadius: 8, cursor: "pointer",
        background: hov ? (danger ? "#fef2f2" : "#ede8da") : "transparent",
        transition: "background 0.15s",
      }}
    >
      <span style={{
        width: 20, height: 20, display: "flex", alignItems: "center", justifyContent: "center",
        color: danger ? "#dc2626" : accent ? "#8B6914" : "#6B6560",
        opacity: hov ? 1 : 0.7,
        transition: "opacity 0.15s",
      }}>
        {icon}
      </span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 13, fontWeight: 500, color: danger ? "#dc2626" : accent ? "#92400e" : "#2a2420", fontFamily: "Bricolage Grotesque, sans-serif" }}>
          {label}
        </div>
        {sublabel && (
          <div style={{ fontSize: 10, color: "#999", fontFamily: "'JetBrains Mono', monospace", marginTop: 1 }}>{sublabel}</div>
        )}
      </div>
      {badge && (
        <span style={{ fontSize: 10, fontWeight: 700, background: "#fef3c7", color: "#92400e", padding: "2px 6px", borderRadius: 10, fontFamily: "'JetBrains Mono', monospace" }}>
          {badge}
        </span>
      )}
    </div>
  );
}

function Divider() {
  return <div style={{ height: 1, background: "#e8e2d6", margin: "4px 0" }} />;
}

export default function UserAreaDemo() {
  const [open, setOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("main"); // main | wallet | keys
  const u = mockUser;
  const tier = TIER_CONFIG[u.tier];

  return (
    <div style={{ minHeight: "100vh", background: "#f0ebe0", display: "flex", alignItems: "flex-start", justifyContent: "flex-end", padding: 24, fontFamily: "Bricolage Grotesque, sans-serif" }}>
      {/* Trigger Button */}
      <div style={{ position: "relative" }}>
        <button
          onClick={() => { setOpen(!open); setActiveTab("main"); }}
          style={{
            width: 40, height: 40, borderRadius: "50%",
            background: open ? "#2a2420" : "#4a3f35",
            color: "#f5f0e0", border: "2px solid " + (open ? "#8B6914" : "transparent"),
            cursor: "pointer", fontSize: 13, fontWeight: 700,
            display: "flex", alignItems: "center", justifyContent: "center",
            transition: "all 0.2s", boxShadow: open ? "0 0 0 3px rgba(139,105,20,0.2)" : "none",
          }}
        >
          {u.initials}
        </button>

        {/* Panel */}
        {open && (
          <div style={{
            position: "absolute", right: 0, top: 48, width: 300,
            background: "#faf6ee", border: "1px solid #e0d9cc",
            borderRadius: 14, boxShadow: "0 12px 40px rgba(0,0,0,0.15), 0 2px 8px rgba(0,0,0,0.08)",
            overflow: "hidden", zIndex: 100,
            animation: "fadeIn 0.15s ease",
          }}>

            {/* === HEADER IDENTITY === */}
            <div style={{ background: "linear-gradient(135deg, #2a2420 0%, #4a3f35 100%)", padding: "16px 16px 14px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <div style={{
                  width: 44, height: 44, borderRadius: "50%",
                  background: "#8B6914", color: "#f5f0e0",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 14, fontWeight: 700, border: "2px solid rgba(245,240,224,0.2)",
                }}>
                  {u.initials}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ color: "#f5f0e0", fontWeight: 700, fontSize: 14, marginBottom: 2 }}>{u.name}</div>
                  <div style={{ color: "#b8a98a", fontSize: 10, fontFamily: "'JetBrains Mono', monospace" }}>{u.email}</div>
                </div>
                <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 4 }}>
                  <span style={{ fontSize: 9, fontWeight: 800, letterSpacing: "0.1em", background: tier.bg, color: tier.color, padding: "2px 8px", borderRadius: 10 }}>
                    {tier.label}
                  </span>
                  <span style={{ fontSize: 9, color: "#8B6914", fontFamily: "'JetBrains Mono', monospace" }}>
                    Pioneer #{u.pioneer}
                  </span>
                </div>
              </div>
              {/* DID strip */}
              <div style={{ marginTop: 10, padding: "4px 8px", background: "rgba(0,0,0,0.2)", borderRadius: 6, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <span style={{ fontSize: 10, color: "#8B6914", fontFamily: "'JetBrains Mono', monospace", display: "flex", alignItems: "center", gap: 4 }}>
                  <span style={{ color: "#b8a98a" }}>{Icons.idCard}</span> {u.did}
                </span>
                <span style={{ fontSize: 10, color: "#10b981" }}>● verified</span>
              </div>
            </div>

            {/* === NAV TABS === */}
            {activeTab !== "main" && (
              <div style={{ display: "flex", gap: 0, borderBottom: "1px solid #e0d9cc" }}>
                {["main", "wallet", "keys"].map(tab => (
                  <button key={tab} onClick={() => setActiveTab(tab)} style={{
                    flex: 1, padding: "9px 0", fontSize: 11, fontWeight: 600,
                    background: activeTab === tab ? "#faf6ee" : "#f0ebe0",
                    border: "none", borderBottom: activeTab === tab ? "2px solid #8B6914" : "2px solid transparent",
                    cursor: "pointer", color: activeTab === tab ? "#2a2420" : "#999",
                    textTransform: "capitalize", fontFamily: "Bricolage Grotesque, sans-serif",
                  }}>
                    {tab === "main" ? "← Back" : tab}
                  </button>
                ))}
              </div>
            )}

            {/* === MAIN VIEW === */}
            {activeTab === "main" && (
              <>
                {/* Wallet Quick Preview */}
                <div style={{ margin: "12px 12px 0", padding: "10px 12px", background: "#fff8e8", border: "1px solid #f0e4b8", borderRadius: 10 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div>
                      <div style={{ fontSize: 10, color: "#999", fontFamily: "'JetBrains Mono', monospace" }}>WALLET</div>
                      <div style={{ fontSize: 22, fontWeight: 800, color: "#2a2420", lineHeight: 1.1 }}>
                        {u.wallet.credits} <span style={{ fontSize: 12, color: "#8B6914", fontWeight: 600 }}>credits</span>
                      </div>
                    </div>
                    <button onClick={() => setActiveTab("wallet")} style={{
                      fontSize: 11, fontWeight: 700, color: "#8B6914", background: "#fef3c7",
                      border: "none", borderRadius: 8, padding: "6px 12px", cursor: "pointer",
                    }}>
                      Manage →
                    </button>
                  </div>
                  <CreditsBar used={u.wallet.tokens_used} limit={u.wallet.tokens_limit} />
                </div>

                {/* Governance Score */}
                <div style={{ margin: "8px 12px 0", padding: "8px 12px", background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: 10, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div>
                    <div style={{ fontSize: 10, color: "#999", fontFamily: "'JetBrains Mono', monospace" }}>GOV SCORE</div>
                    <div style={{ fontSize: 18, fontWeight: 800, color: "#166534" }}>{u.gov_score}<span style={{ fontSize: 10, fontWeight: 500 }}>%</span></div>
                  </div>
                  <div style={{ textAlign: "right" }}>
                    <div style={{ fontSize: 10, color: "#999", fontFamily: "'JetBrains Mono', monospace" }}>RECEIPTS</div>
                    <div style={{ fontSize: 14, fontWeight: 700, color: "#166534" }}>{u.receipts.toLocaleString()}</div>
                  </div>
                </div>

                <Section title="Account">
                  <MenuItem icon={Icons.settings} label="Settings" sublabel="Preferences, language, notifications" />
                  <MenuItem icon={Icons.key} label="API Keys" sublabel={`${u.keys.length} keys active`} onClick={() => setActiveTab("keys")} />
                  <MenuItem icon={Icons.user} label="Profile & DID" sublabel="Identity, liveness, verification" />
                </Section>

                <Divider />

                {u.role === "admin" && (
                  <>
                    <Section title="Administration">
                      <MenuItem icon={Icons.shield} label="Admin Panel" sublabel="Agents, governance, ledger" accent />
                      <MenuItem icon={Icons.chart} label="Analytics" sublabel="Usage, documents, flows" accent />
                      <MenuItem icon={Icons.robot} label="Agent Corps" sublabel="7 agents running" badge="7" accent />
                    </Section>
                    <Divider />
                  </>
                )}

                <Section>
                  <MenuItem icon={Icons.clipboard} label="View all plans" />
                  <MenuItem icon={Icons.gift} label="Invite & earn" sublabel="Get 100 credits per referral" />
                </Section>

                <Divider />

                <Section>
                  <MenuItem icon={Icons.logout} label="Log out" danger onClick={() => alert("logout")} />
                </Section>
              </>
            )}

            {/* === WALLET VIEW === */}
            {activeTab === "wallet" && (
              <>
                <Section title="Wallet Overview">
                  <div style={{ padding: "12px", background: "#fff8e8", border: "1px solid #f0e4b8", borderRadius: 10, marginBottom: 8 }}>
                    <div style={{ fontSize: 10, color: "#999", fontFamily: "'JetBrains Mono', monospace" }}>AVAILABLE CREDITS</div>
                    <div style={{ fontSize: 32, fontWeight: 800, color: "#2a2420" }}>{u.wallet.credits}</div>
                    <div style={{ fontSize: 11, color: "#8B6914" }}>Plan: {u.wallet.plan}</div>
                  </div>
                  <CreditsBar used={u.wallet.tokens_used} limit={u.wallet.tokens_limit} />
                </Section>

                <Divider />

                <Section title="Billing">
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                    {[
                      { label: "Last recharge", value: u.wallet.last_recharge },
                      { label: "Next billing", value: u.wallet.next_billing },
                    ].map(item => (
                      <div key={item.label} style={{ padding: "8px 10px", background: "#f0ebe0", borderRadius: 8 }}>
                        <div style={{ fontSize: 9, color: "#999", fontFamily: "'JetBrains Mono', monospace" }}>{item.label.toUpperCase()}</div>
                        <div style={{ fontSize: 12, fontWeight: 600, color: "#2a2420", marginTop: 2 }}>{item.value}</div>
                      </div>
                    ))}
                  </div>
                </Section>

                <Divider />

                <Section>
                  <MenuItem icon={Icons.creditCard} label="Add Credits" sublabel="Buy token bundles" accent />
                  <MenuItem icon={Icons.document} label="Payment History" sublabel="Invoices & receipts" />
                  <MenuItem icon={Icons.bell} label="Low Balance Alert" sublabel="Notify at 100 credits" />
                </Section>
              </>
            )}

            {/* === KEYS VIEW === */}
            {activeTab === "keys" && (
              <>
                <Section title="API Keys">
                  {u.keys.map(k => (
                    <div key={k.id} style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 10px", background: "#f0ebe0", borderRadius: 8, marginBottom: 6 }}>
                      <span style={{ fontSize: 8, color: "#10b981", marginTop: 1 }}>●</span>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: 13, fontWeight: 600, color: "#2a2420" }}>{k.label}</div>
                        <div style={{ fontSize: 10, color: "#999", fontFamily: "'JetBrains Mono', monospace" }}>{k.id}</div>
                      </div>
                      <button style={{ fontSize: 10, color: "#dc2626", background: "none", border: "none", cursor: "pointer" }}>Revoke</button>
                    </div>
                  ))}
                </Section>

                <Divider />

                <Section>
                  <MenuItem icon={Icons.plus} label="Generate New Key" sublabel="Scoped permissions available" accent />
                  <MenuItem icon={Icons.clipboard} label="Key Audit Log" sublabel="Access history per key" />
                </Section>
              </>
            )}

            <style>{`
              @import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap');
              @keyframes fadeIn { from { opacity: 0; transform: translateY(-6px); } to { opacity: 1; transform: translateY(0); } }
            `}</style>
          </div>
        )}
      </div>
    </div>
  );
}
