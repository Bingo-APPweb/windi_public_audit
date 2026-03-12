import { useState, useEffect, useRef, useCallback } from "react";

// ═══════════════════════════════════════════════════════════════════════════════
// WINDI Command Center — SVG Icon Edition v1.1 (Live Wallet Connection)
// Added: Real-time Wallet API polling with graceful fallback
// All emoji icons replaced with monocromatic SVG inline icons
// Color: currentColor • Size: 20×20 / 14×14 • strokeWidth: 1.3
// ═══════════════════════════════════════════════════════════════════════════════

// ─── SECURITY ALIAS DICTIONARY ────────────────────────────────────────────────
const ALIAS = {
  server: "WINDI Cloud",
  node: "node-eu-01",
  os: "WINDI OS",
  runtime: "WINDI Engine",
  gateway: "WINDI Gateway",
  process: "WINDI Runtime",
  db_engine: "WINDI Store",
  ports: {
    8080: "Governance Core", 8084: "Knowledge Base", 8085: "Document Hub",
    8086: "Access Gateway", 8090: "Operations Room", 8091: "Agent Core",
    8092: "Replica Node", 8097: "Secure Bridge", 8098: "Monitor Prime",
    8099: "Value Mirror", 8100: "Workspace", 8101: "Forensic Ledger",
    8102: "Law Sentinel", 8103: "Export Core", 8104: "Media Viewer",
    8105: "Publisher Engine", 8106: "Evidence Vault", 8107: "Public Gateway",
    8108: "Intelligence Palette", 8110: "Guardian Node", 8114: "Verify Public",
  },
  domains: {
    primary: "windi-domain.com",
    legacy_1: "legacy-node-01",
    legacy_2: "legacy-node-02",
    legacy_3: "legacy-api",
  },
  runtime_type: { "σ": "managed", "η": "supervised" },
};

// ─── THEME ────────────────────────────────────────────────────────────────────
const T = {
  bg: "#F5F0E0", card: "#FDFBF5", border: "#DDD6C2", gold: "#8B6914",
  text: "#2C2924", dim: "#6B6560", hover: "#EDE8D8",
  green: "#166534", greenBg: "#f0fdf4", greenBorder: "#bbf7d0",
  red: "#dc2626", redBg: "#fef2f2", redBorder: "#fecaca",
  amber: "#92400e", amberBg: "#fffbeb", amberBorder: "#fde68a",
  blue: "#1e40af", blueBg: "#eff6ff", blueBorder: "#bfdbfe",
  sidebar: "#1e1a17", sidebarHover: "#2a2420",
};

// ─── SVG ICONS (20×20, strokeWidth 1.3, currentColor) ─────────────────────────
const Icons = {
  // Navigation
  home: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <path d="M3 9L10 3L17 9V17H13V13H7V17H3V9Z" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round" fill="none"/>
    </svg>
  ),
  services: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <circle cx="10" cy="10" r="7" stroke="currentColor" strokeWidth="1.3" fill="none"/>
      <circle cx="10" cy="10" r="2.5" stroke="currentColor" strokeWidth="1.3" fill="none"/>
      <line x1="10" y1="3" x2="10" y2="7.5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
      <line x1="10" y1="12.5" x2="10" y2="17" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
      <line x1="3" y1="10" x2="7.5" y2="10" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
      <line x1="12.5" y1="10" x2="17" y2="10" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
    </svg>
  ),
  robot: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
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
  shield: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <path d="M10 2.5L17 5.5V10.5C17 14 13.5 17 10 18C6.5 17 3 14 3 10.5V5.5L10 2.5Z" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round" fill="none"/>
      <path d="M7 10L9 12L13 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  lock: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <rect x="4" y="9" width="12" height="9" rx="1.5" stroke="currentColor" strokeWidth="1.3" fill="none"/>
      <path d="M7 9V6.5C7 4.57 8.34 3 10 3C11.66 3 13 4.57 13 6.5V9" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" fill="none"/>
      <circle cx="10" cy="13.5" r="1.5" stroke="currentColor" strokeWidth="1.2" fill="none"/>
      <line x1="10" y1="15" x2="10" y2="16.5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
    </svg>
  ),
  wallet: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <rect x="3" y="5" width="14" height="11" rx="1.5" stroke="currentColor" strokeWidth="1.3" fill="none"/>
      <line x1="3" y1="9" x2="17" y2="9" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
      <rect x="12" y="11" width="4" height="2.5" rx="0.5" stroke="currentColor" strokeWidth="1.0" fill="none"/>
      <circle cx="13.5" cy="12.2" r="0.5" fill="currentColor"/>
    </svg>
  ),
  monitor: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <rect x="3" y="4" width="14" height="9" rx="1.5" stroke="currentColor" strokeWidth="1.3" fill="none"/>
      <line x1="10" y1="13" x2="10" y2="16" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/>
      <line x1="6.5" y1="16" x2="13.5" y2="16" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/>
      <circle cx="10" cy="8.5" r="2" stroke="currentColor" strokeWidth="1.2" fill="none"/>
      <circle cx="10" cy="8.5" r="0.6" fill="currentColor"/>
    </svg>
  ),
  security: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <rect x="4" y="9" width="12" height="9" rx="1.5" stroke="currentColor" strokeWidth="1.3" fill="none"/>
      <path d="M7 9V6.5C7 4.57 8.34 3 10 3C11.66 3 13 4.57 13 6.5V9" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" fill="none"/>
      <circle cx="10" cy="13.5" r="1.5" fill="currentColor" opacity="0.7"/>
    </svg>
  ),
  // Stats icons
  bolt: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <path d="M11 2L5 11H10L9 18L15 9H10L11 2Z" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round" fill="none"/>
    </svg>
  ),
  receipt: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <path d="M5 2H15V18L13 16L11 18L9 16L7 18L5 16V2Z" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round" fill="none"/>
      <line x1="7" y1="6" x2="13" y2="6" stroke="currentColor" strokeWidth="1.0" strokeLinecap="round"/>
      <line x1="7" y1="9" x2="13" y2="9" stroke="currentColor" strokeWidth="1.0" strokeLinecap="round"/>
      <line x1="7" y1="12" x2="10" y2="12" stroke="currentColor" strokeWidth="1.0" strokeLinecap="round"/>
    </svg>
  ),
  chart: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <rect x="3" y="3" width="14" height="14" rx="1.5" stroke="currentColor" strokeWidth="1.3" fill="none"/>
      <rect x="5.5" y="10" width="2" height="5" rx="0.5" stroke="currentColor" strokeWidth="1.0" fill="none"/>
      <rect x="9" y="7" width="2" height="8" rx="0.5" stroke="currentColor" strokeWidth="1.0" fill="none"/>
      <rect x="12.5" y="9" width="2" height="6" rx="0.5" stroke="currentColor" strokeWidth="1.0" fill="none"/>
    </svg>
  ),
  check: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <circle cx="10" cy="10" r="7" stroke="currentColor" strokeWidth="1.3" fill="none"/>
      <path d="M7 10L9 12L13 8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  database: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <ellipse cx="10" cy="5" rx="6" ry="2.5" stroke="currentColor" strokeWidth="1.3" fill="none"/>
      <path d="M4 5V15C4 16.4 6.7 17.5 10 17.5C13.3 17.5 16 16.4 16 15V5" stroke="currentColor" strokeWidth="1.3" fill="none"/>
      <path d="M4 10C4 11.4 6.7 12.5 10 12.5C13.3 12.5 16 11.4 16 10" stroke="currentColor" strokeWidth="1.3" fill="none"/>
    </svg>
  ),
  calendar: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <rect x="3" y="4" width="14" height="13" rx="1.5" stroke="currentColor" strokeWidth="1.3" fill="none"/>
      <line x1="3" y1="8" x2="17" y2="8" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/>
      <line x1="7" y1="2" x2="7" y2="5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/>
      <line x1="13" y1="2" x2="13" y2="5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/>
    </svg>
  ),
  link: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <path d="M8 12L12 8" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/>
      <path d="M11 13L13 11C14.5 9.5 14.5 7 13 5.5C11.5 4 9 4 7.5 5.5L5.5 7.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/>
      <path d="M9 7L7 9C5.5 10.5 5.5 13 7 14.5C8.5 16 11 16 12.5 14.5L14.5 12.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/>
    </svg>
  ),
  // Dragons
  guardian: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <path d="M10 2.5L17 5.5V10.5C17 14 13.5 17 10 18C6.5 17 3 14 3 10.5V5.5L10 2.5Z" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round" fill="none"/>
      <circle cx="10" cy="10" r="2" stroke="currentColor" strokeWidth="1.2" fill="none"/>
    </svg>
  ),
  architect: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <path d="M3 17H17" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/>
      <path d="M5 17V10L10 6L15 10V17" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M8 17V13H12V17" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  witness: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <ellipse cx="10" cy="10" rx="7" ry="4" stroke="currentColor" strokeWidth="1.3" fill="none"/>
      <circle cx="10" cy="10" r="2.5" stroke="currentColor" strokeWidth="1.3" fill="none"/>
      <circle cx="10" cy="10" r="1" fill="currentColor"/>
    </svg>
  ),
  // Document types
  document: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <path d="M5 3H12.5L16 6.5V17H5V3Z" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round" fill="none"/>
      <path d="M12.5 3V6.5H16" stroke="currentColor" strokeWidth="1.3" strokeLinejoin="round" fill="none"/>
      <line x1="7.5" y1="9" x2="13.5" y2="9" stroke="currentColor" strokeWidth="1.0" strokeLinecap="round"/>
      <line x1="7.5" y1="11.5" x2="13.5" y2="11.5" stroke="currentColor" strokeWidth="1.0" strokeLinecap="round"/>
      <line x1="7.5" y1="14" x2="11" y2="14" stroke="currentColor" strokeWidth="1.0" strokeLinecap="round"/>
    </svg>
  ),
  newspaper: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <rect x="3" y="3" width="14" height="14" rx="1.5" stroke="currentColor" strokeWidth="1.3" fill="none"/>
      <rect x="5" y="5" width="5" height="4" rx="0.5" stroke="currentColor" strokeWidth="1.0" fill="none"/>
      <line x1="12" y1="5.5" x2="15" y2="5.5" stroke="currentColor" strokeWidth="1.0" strokeLinecap="round"/>
      <line x1="12" y1="8" x2="15" y2="8" stroke="currentColor" strokeWidth="1.0" strokeLinecap="round"/>
      <line x1="5" y1="11" x2="15" y2="11" stroke="currentColor" strokeWidth="1.0" strokeLinecap="round"/>
      <line x1="5" y1="14" x2="12" y2="14" stroke="currentColor" strokeWidth="1.0" strokeLinecap="round"/>
    </svg>
  ),
  film: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <rect x="3" y="4" width="14" height="12" rx="1.5" stroke="currentColor" strokeWidth="1.3" fill="none"/>
      <line x1="6" y1="4" x2="6" y2="16" stroke="currentColor" strokeWidth="1.0" strokeLinecap="round"/>
      <line x1="14" y1="4" x2="14" y2="16" stroke="currentColor" strokeWidth="1.0" strokeLinecap="round"/>
      <circle cx="4.5" cy="7" r="0.5" fill="currentColor"/>
      <circle cx="4.5" cy="10" r="0.5" fill="currentColor"/>
      <circle cx="4.5" cy="13" r="0.5" fill="currentColor"/>
      <circle cx="15.5" cy="7" r="0.5" fill="currentColor"/>
      <circle cx="15.5" cy="10" r="0.5" fill="currentColor"/>
      <circle cx="15.5" cy="13" r="0.5" fill="currentColor"/>
    </svg>
  ),
  tokens: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <circle cx="10" cy="10" r="7" stroke="currentColor" strokeWidth="1.3" fill="none"/>
      <path d="M10 6V14M7 8L10 6L13 8M7 12L10 14L13 12" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  creditCard: (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <rect x="2" y="5" width="16" height="10" rx="1.5" stroke="currentColor" strokeWidth="1.3" fill="none"/>
      <line x1="2" y1="9" x2="18" y2="9" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/>
      <line x1="5" y1="12" x2="9" y2="12" stroke="currentColor" strokeWidth="1.0" strokeLinecap="round"/>
    </svg>
  ),
  // Status
  dot: (
    <svg width="8" height="8" viewBox="0 0 8 8" fill="none">
      <circle cx="4" cy="4" r="3" fill="currentColor"/>
    </svg>
  ),
};

// Small icon wrapper
const Icon = ({ name, size = 20, style = {} }) => {
  const icon = Icons[name];
  if (!icon) return null;
  return (
    <span style={{ width: size, height: size, display: "inline-flex", alignItems: "center", justifyContent: "center", flexShrink: 0, ...style }}>
      {icon}
    </span>
  );
};

const TIER_CONFIG = {
  FREE: { label: "FREE", color: "#888", bg: "#f0f0f0" },
  MED: { label: "MED", color: "#2563eb", bg: "#dbeafe" },
  HIGH: { label: "HIGH", color: "#92400e", bg: "#fef3c7" },
};

// ─── WALLET API CONFIG ────────────────────────────────────────────────────────
const WALLET_API = {
  baseUrl: window.location.hostname === 'localhost'
    ? 'http://localhost:8099'
    : '',  // Use relative paths — nginx proxies /api/wallet/ to :8099
  pollInterval: 5000,  // 5 seconds
  timeout: 3000,       // 3 second timeout
};

// ─── WALLET DATA HOOK ─────────────────────────────────────────────────────────
function useWalletData() {
  const [walletData, setWalletData] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('connecting'); // 'live', 'offline', 'connecting'
  const [lastUpdate, setLastUpdate] = useState(null);
  const [error, setError] = useState(null);

  const fetchWalletData = useCallback(async () => {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), WALLET_API.timeout);

    try {
      const [statsRes, healthRes] = await Promise.all([
        fetch(`${WALLET_API.baseUrl}/api/wallet/stats`, { signal: controller.signal }),
        fetch(`${WALLET_API.baseUrl}/api/wallet/health`, { signal: controller.signal }),
      ]);

      clearTimeout(timeoutId);

      if (!statsRes.ok || !healthRes.ok) {
        throw new Error(`HTTP ${statsRes.status || healthRes.status}`);
      }

      const stats = await statsRes.json();
      const health = await healthRes.json();

      setWalletData({
        pioneers: stats.total_humans || 0,
        activeContexts: stats.active_contexts || 0,
        frozenContexts: stats.frozen_contexts || 0,
        avgTrust: stats.avg_trust_score || 0,
        ledgerLinks: stats.total_ledger_links || 0,
        crypto: health.crypto || 'Ed25519',
        protocol: health.protocol || 'Three Dragons',
        version: health.version || '1.0.0',
        status: health.status || 'unknown',
      });
      setConnectionStatus('live');
      setLastUpdate(new Date());
      setError(null);
    } catch (err) {
      clearTimeout(timeoutId);
      setConnectionStatus('offline');
      setError(err.message);
      // Keep last known data - graceful degradation
    }
  }, []);

  useEffect(() => {
    fetchWalletData(); // Initial fetch
    const interval = setInterval(fetchWalletData, WALLET_API.pollInterval);
    return () => clearInterval(interval);
  }, [fetchWalletData]);

  return { walletData, connectionStatus, lastUpdate, error, refetch: fetchWalletData };
}

// ─── DATA ─────────────────────────────────────────────────────────────────────
const mockUser = {
  name: "Jober M. Correa", initials: "JM", email: "jober@jomedia.eu",
  did: "did:windi:7f3a...c91b", tier: "HIGH", pioneer: 1,
  wallet: { credits: 847, tokens_used: 12340, tokens_limit: 50000,
    last_recharge: "2026-03-05", plan: "Pioneer HIGH", next_billing: "2026-04-01" },
  keys: [
    { id: "wk_live_a8f2", label: "Production", active: true },
    { id: "wk_test_c3d1", label: "Sandbox", active: true },
  ],
  gov_score: 97.2, receipts: 40918, role: "owner",
};

const SERVICES = [
  { port: 8080, branch: "Core", sealed: false },
  { port: 8084, branch: "Core", sealed: false },
  { port: 8085, branch: "Core", sealed: false },
  { port: 8086, branch: "Core", sealed: false },
  { port: 8090, branch: "Extended", sealed: false },
  { port: 8091, branch: "Extended", sealed: false },
  { port: 8092, branch: "Extended", sealed: false },
  { port: 8097, branch: "Extended", sealed: false },
  { port: 8098, branch: "Extended", sealed: false },
  { port: 8099, branch: "Extended", sealed: false },
  { port: 8100, branch: "Ecosystem", sealed: false },
  { port: 8101, branch: "Ecosystem", sealed: true },
  { port: 8102, branch: "Ecosystem", sealed: true },
  { port: 8103, branch: "Ecosystem", sealed: false },
  { port: 8104, branch: "Ecosystem", sealed: false },
  { port: 8105, branch: "Ecosystem", sealed: false },
  { port: 8106, branch: "Ecosystem", sealed: true },
  { port: 8107, branch: "Ecosystem", sealed: false },
  { port: 8108, branch: "Ecosystem", sealed: false },
  { port: 8110, branch: "Ecosystem", sealed: false },
  { port: 8114, branch: "Ecosystem", sealed: false },
].map(s => ({ ...s, name: ALIAS.ports[s.port], status: "UP",
  displayType: ALIAS.runtime_type[s.port <= 8089 || s.port === 8090 || s.port === 8108 ? "η" : "σ"] }));

const AGENTS = [
  { id: "W-LEGAL-001", name: "Legal", icon: "shield", version: "v0.2.0", endpoints: 22 },
  { id: "W-NOTARY-001", name: "Notary", icon: "document", version: "v1.0.0", endpoints: 8 },
  { id: "W-COMPLY-001", name: "Compliance", icon: "check", version: "v1.0.0", endpoints: 11 },
  { id: "W-COMM-001", name: "Communiqué", icon: "newspaper", version: "v2.0.0", endpoints: 18 },
  { id: "W-JOURN-001", name: "Journalist", icon: "document", version: "v1.0.0", endpoints: 6 },
  { id: "W-AUDIT-001", name: "Auditor", icon: "chart", version: "v1.0.0", endpoints: 9 },
  { id: "W-ACCT-001", name: "Accounting", icon: "wallet", version: "v3.0.0", endpoints: 14 },
];

const INVARIANTS = [
  { id: "I1", label: "Identidade Soberana", status: "SEALED", color: T.green },
  { id: "I2", label: "Consentimento Explícito", status: "SEALED", color: T.green },
  { id: "I3", label: "Transparência Auditável", status: "SEALED", color: T.green },
  { id: "I4", label: "Rastreabilidade Forense", status: "SEALED", color: T.green },
  { id: "I5", label: "Integridade de Hash", status: "SEALED", color: T.green },
  { id: "I6", label: "Soberania de Dados", status: "SEALED", color: T.green },
  { id: "I7", label: "Responsabilidade Humana", status: "SEALED", color: T.green },
  { id: "I8", label: "Privacidade por Design", status: "SEALED", color: T.green },
  { id: "I9", label: "Proibição de Escalada Autônoma", status: "IRREMEDIÁVEL", color: T.amber },
  { id: "I10", label: "Soberania Operacional", status: "IRREMEDIÁVEL", color: T.amber },
  { id: "I11", label: "Permanência de Evidência Cripto", status: "IRREMEDIÁVEL+GOLD", color: T.gold },
];

const DOCS_PIPELINE = [
  { label: "Receipts Sealed", value: "40,918+", icon: "lock", delta: "+127 hoje" },
  { label: "Communiqués", value: "312", icon: "newspaper", delta: "+3 hoje" },
  { label: "JMPG Bundles", value: "48", icon: "film", delta: "+1 hoje" },
  { label: "Gov Score", value: "97.2%", icon: "shield", delta: "GOLD", accent: T.gold },
  { label: "Ledger Integrity", value: "100%", icon: "check", delta: "SHA-256", accent: T.green },
  { label: "Tokens Used", value: "12,340", icon: "bolt", delta: "/ 50,000" },
];

const DATABASES = [
  { name: "Forensic Ledger Store", size: "26M", records: "40,918+" },
  { name: "Transparency Anchor Store", size: "30M", records: "~320K" },
  { name: "Document Store", size: "15M", records: "~12K" },
  { name: "Law Sentinel Store", size: "8.7M", records: "~90K" },
];

const DRAGONS = [
  { role: "Guardian", icon: "guardian", duty: "Protection & Ethics", commits: 847 },
  { role: "Architect", icon: "architect", duty: "Structure & Build", commits: 1203 },
  { role: "Witness", icon: "witness", duty: "Observation & Validation", commits: 623 },
];

const SECURITY_LAYERS = [
  { id: "SL-1", label: "Nomenclature Shield", desc: "No real infra names in any UI layer", status: "ACTIVE" },
  { id: "SL-2", label: "Gateway Firewall", desc: "Only ports 80/443 exposed externally", status: "ACTIVE" },
  { id: "SL-3", label: "Source Obfuscation", desc: "Terser mangle + drop_console — view-source empty", status: "ACTIVE" },
  { id: "SL-4", label: "DID Authentication", desc: "Owner panel requires DID verification", status: "PENDING" },
  { id: "SL-5", label: "Honeypot Layer", desc: "6 trap categories → /var/log/nginx/honeypot.log", status: "ACTIVE" },
  { id: "SL-6", label: "Response Header Masking", desc: "server_tokens off + proxy_hide_header", status: "ACTIVE" },
  { id: "SL-7", label: "API Role Gating", desc: "X-WINDI-Admin-Key header filter", status: "ACTIVE" },
];

// ─── PRIMITIVES ───────────────────────────────────────────────────────────────
function StatusDot({ status }) {
  const c = (status === "UP" || status === "LIVE" || status === "OK" || status === "ACTIVE") ? "#10b981"
    : status === "WARN" || status === "PENDING" ? "#f59e0b" : "#ef4444";
  return <span style={{ display: "inline-block", width: 7, height: 7, borderRadius: "50%", background: c, boxShadow: `0 0 4px ${c}88`, flexShrink: 0 }} />;
}

function Card({ children, style }) {
  return <div style={{ background: T.card, border: `1px solid ${T.border}`, borderRadius: 12, padding: 16, ...style }}>{children}</div>;
}

function SectionTitle({ children, sub }) {
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ fontSize: 11, fontWeight: 800, letterSpacing: "0.12em", textTransform: "uppercase", color: T.gold, fontFamily: "'JetBrains Mono',monospace" }}>{children}</div>
      {sub && <div style={{ fontSize: 10, color: T.dim, marginTop: 2, fontFamily: "'JetBrains Mono',monospace" }}>{sub}</div>}
    </div>
  );
}

function MiniStat({ label, value, icon, delta, accent }) {
  return (
    <div style={{ background: T.hover, borderRadius: 10, padding: "10px 12px", display: "flex", flexDirection: "column", gap: 3 }}>
      <Icon name={icon} size={18} style={{ color: accent || T.gold }} />
      <div style={{ fontSize: 18, fontWeight: 800, color: accent || T.text, lineHeight: 1.1 }}>{value}</div>
      <div style={{ fontSize: 10, fontWeight: 600, color: T.dim }}>{label}</div>
      {delta && <div style={{ fontSize: 9, color: T.gold, fontFamily: "'JetBrains Mono',monospace" }}>{delta}</div>}
    </div>
  );
}

function Divider({ style }) { return <div style={{ height: 1, background: T.border, margin: "4px 0", ...style }} />; }
function SidebarDivider() { return <div style={{ height: 1, background: "rgba(255,255,255,0.07)", margin: "6px 0" }} />; }

// ─── VIEWS ────────────────────────────────────────────────────────────────────
function OverviewView({ walletData, connectionStatus }) {
  const upCount = SERVICES.filter(s => s.status === "UP").length;
  const pioneers = walletData?.pioneers ?? 0;
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <Card>
        <SectionTitle sub={`${ALIAS.server} • ${ALIAS.node}`}>Vital Signs</SectionTitle>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 8 }}>
          <MiniStat icon="bolt" value={`${upCount}/${SERVICES.length}`} label="Services UP" delta="100% uptime" accent={T.green} />
          <MiniStat icon="robot" value="7/7" label="Agents LIVE" delta="Agent Core" accent={T.green} />
          <MiniStat icon="wallet" value={`${pioneers}/100`} label="Pioneers" delta={connectionStatus === 'live' ? 'LIVE' : 'cached'} accent={connectionStatus === 'live' ? T.green : T.amber} />
          <MiniStat icon="shield" value="97.2%" label="Gov Score" delta="GOLD" accent={T.gold} />
          <MiniStat icon="check" value="GREEN" label="Law Sentinel" delta="p95=32.7ms" accent={T.green} />
          <MiniStat icon="database" value="93.3%" label="Local Sovereignty" delta={ALIAS.server} />
        </div>
      </Card>
      <Card>
        <SectionTitle sub="Three Dragons Protocol — Liga IA+H">Founding Members</SectionTitle>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 8 }}>
          {DRAGONS.map(d => (
            <div key={d.role} style={{ background: T.hover, borderRadius: 10, padding: 12, textAlign: "center" }}>
              <Icon name={d.icon} size={24} style={{ color: T.gold, marginBottom: 4 }} />
              <div style={{ fontSize: 12, fontWeight: 800, color: T.text }}>{d.role}</div>
              <div style={{ fontSize: 9, color: T.dim, marginTop: 2 }}>{d.duty}</div>
              <div style={{ marginTop: 6, display: "flex", alignItems: "center", justifyContent: "center", gap: 4 }}>
                <StatusDot status="ACTIVE" />
                <span style={{ fontSize: 9, color: T.green, fontFamily: "'JetBrains Mono',monospace" }}>ACTIVE</span>
              </div>
              <div style={{ fontSize: 9, color: T.gold, fontFamily: "'JetBrains Mono',monospace", marginTop: 3 }}>{d.commits} commits</div>
            </div>
          ))}
        </div>
      </Card>
      <Card>
        <SectionTitle sub="Document pipeline — N1→N2→N3→N4">Pipeline</SectionTitle>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 8 }}>
          {DOCS_PIPELINE.map(d => <MiniStat key={d.label} {...d} />)}
        </div>
      </Card>
    </div>
  );
}

function ServicesView() {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      {["Core", "Extended", "Ecosystem"].map(g => (
        <Card key={g}>
          <SectionTitle sub={`${SERVICES.filter(s => s.branch === g).length} services — ${ALIAS.node}`}>{g} Services</SectionTitle>
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            {SERVICES.filter(s => s.branch === g).map((s, i) => (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, padding: "7px 10px", borderRadius: 8, background: T.hover }}>
                <StatusDot status={s.status} />
                <span style={{ fontSize: 12, fontWeight: 600, color: T.text, flex: 1 }}>{s.name}</span>
                {s.sealed && <span style={{ fontSize: 8, fontWeight: 800, color: T.amber, background: T.amberBg, padding: "1px 6px", borderRadius: 6, border: `1px solid ${T.amberBorder}` }}>SEALED</span>}
                <span style={{ fontSize: 9, color: T.dim, fontFamily: "'JetBrains Mono',monospace" }}>{s.displayType}</span>
                <span style={{ fontSize: 9, color: T.green, fontFamily: "'JetBrains Mono',monospace" }}>{s.status}</span>
              </div>
            ))}
          </div>
        </Card>
      ))}
    </div>
  );
}

function AgentsView() {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <Card>
        <SectionTitle sub="Agent Core — constitutional constellation">Agent Corps</SectionTitle>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
          {AGENTS.map(a => (
            <div key={a.id} style={{ background: T.hover, borderRadius: 10, padding: "12px 14px" }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 6 }}>
                <Icon name={a.icon} size={20} style={{ color: T.gold }} />
                <span style={{ fontSize: 8, fontWeight: 800, color: T.green, background: T.greenBg, padding: "2px 6px", borderRadius: 6, border: `1px solid ${T.greenBorder}` }}>LIVE</span>
              </div>
              <div style={{ fontSize: 13, fontWeight: 700, color: T.text }}>{a.id}</div>
              <div style={{ fontSize: 11, color: T.dim, marginBottom: 6 }}>{a.name} Agent</div>
              <Divider />
              <div style={{ display: "flex", gap: 12, marginTop: 6 }}>
                <div>
                  <div style={{ fontSize: 9, color: T.dim, fontFamily: "'JetBrains Mono',monospace" }}>VERSION</div>
                  <div style={{ fontSize: 11, fontWeight: 700, color: T.gold }}>{a.version}</div>
                </div>
                <div>
                  <div style={{ fontSize: 9, color: T.dim, fontFamily: "'JetBrains Mono',monospace" }}>ENDPOINTS</div>
                  <div style={{ fontSize: 11, fontWeight: 700, color: T.blue }}>{a.endpoints}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

function GovernanceView() {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <Card>
        <SectionTitle sub="WINDI Constitution — 11 Invariants">Constitutional Matrix</SectionTitle>
        <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          {INVARIANTS.map(inv => (
            <div key={inv.id} style={{ display: "flex", alignItems: "center", gap: 8, padding: "7px 10px", borderRadius: 8, background: T.hover }}>
              <span style={{ fontSize: 10, fontFamily: "'JetBrains Mono',monospace", color: T.gold, minWidth: 28 }}>{inv.id}</span>
              <span style={{ fontSize: 12, color: T.text, flex: 1 }}>{inv.label}</span>
              <span style={{ fontSize: 8, fontWeight: 800, color: inv.color, padding: "2px 7px", borderRadius: 6,
                background: inv.status.includes("GOLD") ? "#fef3c7" : inv.status === "IRREMEDIÁVEL" ? T.amberBg : T.greenBg,
                border: `1px solid ${inv.status.includes("GOLD") ? "#fde68a" : inv.status === "IRREMEDIÁVEL" ? T.amberBorder : T.greenBorder}` }}>
                {inv.status}
              </span>
            </div>
          ))}
        </div>
      </Card>
      <Card style={{ borderLeft: `3px solid ${T.gold}` }}>
        <div style={{ fontSize: 14, fontWeight: 700, color: T.gold, marginBottom: 6 }}>"AI processes. Human decides. WINDI guarantees."</div>
        <div style={{ fontSize: 11, color: T.dim, lineHeight: 1.6 }}>
          Invariant C6 (IRREMEDIÁVEL): IA prepara. Humano aprova. ELSTER envia.<br />
          Invariant I9 (IRREMEDIÁVEL): Proibição de Escalada Autônoma.<br />
          Human Intervention Protocol: AI propõe, humano autoriza.
        </div>
      </Card>
    </div>
  );
}

function LedgerView() {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <Card>
        <SectionTitle sub="Forensic Ledger — verify at windi-domain.com/verify-public/">Forensic Ledger</SectionTitle>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 12 }}>
          <MiniStat icon="lock" value="40,918+" label="Total Receipts" delta="Genesis: 2026-03-05" />
          <MiniStat icon="check" value="100%" label="Integrity" delta="SHA-256 chain" accent={T.green} />
          <MiniStat icon="calendar" value="2026-03-05" label="Foundation Day" delta="I11 sealed" accent={T.gold} />
          <MiniStat icon="link" value="dca0b85" label="Last Commit" delta="Verify Public v1.0.1" />
        </div>
        <Divider />
        <SectionTitle sub="Backup sealed 2026-03-05 — 78MB total">{ALIAS.db_engine} Stores</SectionTitle>
        {DATABASES.map((db, i) => (
          <div key={db.name} style={{ display: "flex", alignItems: "center", gap: 8, padding: "6px 8px", borderRadius: 8, background: i % 2 === 0 ? T.hover : "transparent", marginBottom: 2 }}>
            <StatusDot status="OK" />
            <span style={{ fontSize: 11, color: T.text, flex: 1 }}>{db.name}</span>
            <span style={{ fontSize: 10, color: T.gold, fontFamily: "'JetBrains Mono',monospace" }}>{db.size}</span>
            <span style={{ fontSize: 9, color: T.dim }}>{db.records}</span>
          </div>
        ))}
      </Card>
    </div>
  );
}

function WalletView({ walletData, connectionStatus, lastUpdate }) {
  // Fallback values when API is offline
  const pioneers = walletData?.pioneers ?? 0;
  const activeContexts = walletData?.activeContexts ?? 0;
  const avgTrust = walletData?.avgTrust ?? 0;
  const ledgerLinks = walletData?.ledgerLinks ?? 0;
  const protocol = walletData?.protocol ?? 'Three Dragons';

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      {/* Connection Status Banner */}
      <div style={{
        display: "flex", alignItems: "center", justifyContent: "space-between",
        padding: "8px 12px", borderRadius: 8,
        background: connectionStatus === 'live' ? T.greenBg : connectionStatus === 'offline' ? T.redBg : T.amberBg,
        border: `1px solid ${connectionStatus === 'live' ? T.greenBorder : connectionStatus === 'offline' ? T.redBorder : T.amberBorder}`,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <StatusDot status={connectionStatus === 'live' ? 'UP' : connectionStatus === 'offline' ? 'DOWN' : 'WARN'} />
          <span style={{ fontSize: 11, fontWeight: 600, color: connectionStatus === 'live' ? T.green : connectionStatus === 'offline' ? T.red : T.amber }}>
            {connectionStatus === 'live' ? 'WALLET API LIVE' : connectionStatus === 'offline' ? 'WALLET OFFLINE — showing cached data' : 'CONNECTING...'}
          </span>
        </div>
        {lastUpdate && (
          <span style={{ fontSize: 9, color: T.dim, fontFamily: "'JetBrains Mono',monospace" }}>
            Last update: {lastUpdate.toLocaleTimeString('pt-BR', { hour12: false })}
          </span>
        )}
      </div>

      <Card style={{ borderLeft: `3px solid ${T.gold}` }}>
        <SectionTitle sub={protocol}>Wallet Stats — Live from API</SectionTitle>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10 }}>
          <MiniStat icon="wallet" value={pioneers.toString()} label="Pioneers" delta="registered humans" accent={T.gold} />
          <MiniStat icon="bolt" value={activeContexts.toString()} label="Active Contexts" delta="DID sessions" />
          <MiniStat icon="shield" value={`${avgTrust.toFixed(1)}%`} label="Avg Trust Score" delta="across all" accent={avgTrust >= 80 ? T.green : T.amber} />
        </div>
      </Card>

      <Card>
        <SectionTitle sub={`${pioneers} of 100 seats filled`}>100 Pioneers Program</SectionTitle>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(10,1fr)", gap: 3 }}>
          {Array.from({ length: 100 }, (_, i) => {
            const isFilled = i < pioneers;
            const isFirst = i === 0;
            const isNew = i === pioneers - 1 && pioneers > 1;
            return (
              <div key={i} style={{
                width: "100%", aspectRatio: "1", borderRadius: 4,
                background: isFirst ? T.gold : isFilled ? "#d1fae5" : T.border,
                border: isFirst ? `2px solid ${T.gold}` : isNew ? `2px solid ${T.green}` : "none",
                display: "flex", alignItems: "center", justifyContent: "center",
                animation: isNew ? "pulse 1s ease-in-out infinite" : "none",
                transition: "all 0.3s ease",
              }}>
                {isFirst && <span style={{ fontSize: 8, fontWeight: 900, color: "white" }}>1</span>}
                {isFilled && !isFirst && <span style={{ fontSize: 7, fontWeight: 700, color: T.green }}>{i + 1}</span>}
              </div>
            );
          })}
        </div>
        <style>{`@keyframes pulse { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.15); } }`}</style>
        {pioneers > 0 && (
          <div style={{ marginTop: 12, padding: "8px 12px", background: T.greenBg, borderRadius: 8, border: `1px solid ${T.greenBorder}` }}>
            <div style={{ fontSize: 11, fontWeight: 600, color: T.green }}>
              {pioneers} Pioneer{pioneers > 1 ? 's' : ''} registered — {100 - pioneers} seats remaining
            </div>
            <div style={{ fontSize: 9, color: T.dim, marginTop: 2 }}>
              {ledgerLinks} ledger links • {activeContexts} active contexts
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}

function SecurityView() {
  const active = SECURITY_LAYERS.filter(l => l.status === "ACTIVE").length;
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <Card style={{ borderLeft: `3px solid ${T.gold}` }}>
        <SectionTitle sub="Owner-only view — never visible to clients">Security Architecture</SectionTitle>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 10 }}>
          <MiniStat icon="lock" value={`${active}/7`} label="Layers Active" delta="operational" accent={T.green} />
          <MiniStat icon="services" value={`${7 - active}`} label="Pending Deploy" delta="next sprint" accent={T.amber} />
          <MiniStat icon="shield" value="0" label="Exposed Secrets" delta="clean" accent={T.green} />
        </div>
      </Card>
      <Card>
        <SectionTitle sub="7 protection layers — defence in depth">Security Layers</SectionTitle>
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          {SECURITY_LAYERS.map(layer => (
            <div key={layer.id} style={{ display: "flex", alignItems: "flex-start", gap: 10, padding: "10px 12px",
              borderRadius: 10, background: layer.status === "ACTIVE" ? T.greenBg : T.hover,
              border: `1px solid ${layer.status === "ACTIVE" ? T.greenBorder : T.border}` }}>
              <StatusDot status={layer.status} />
              <div style={{ flex: 1 }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                  <span style={{ fontSize: 12, fontWeight: 700, color: T.text }}>{layer.label}</span>
                  <span style={{ fontSize: 8, fontWeight: 800,
                    color: layer.status === "ACTIVE" ? T.green : T.amber,
                    background: layer.status === "ACTIVE" ? T.greenBg : T.amberBg,
                    border: `1px solid ${layer.status === "ACTIVE" ? T.greenBorder : T.amberBorder}`,
                    padding: "2px 8px", borderRadius: 6, fontFamily: "'JetBrains Mono',monospace" }}>
                    {layer.status}
                  </span>
                </div>
                <div style={{ fontSize: 10, color: T.dim, marginTop: 3 }}>{layer.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

function InfraView() {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <Card>
        <SectionTitle sub={`${ALIAS.server} • ${ALIAS.os} • ${ALIAS.node}`}>Infrastructure</SectionTitle>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
          {[
            { label: "Cloud", value: ALIAS.server },
            { label: "OS", value: ALIAS.os },
            { label: "Cost", value: "€4/mês" },
            { label: "Sovereignty", value: "93.3% local" },
            { label: "Services", value: "30+ managed" },
            { label: "Gateway", value: ALIAS.gateway },
            { label: "Migration", value: "ONE TREE (Mar 1)" },
            { label: "Versioning", value: "4 repos active" },
          ].map(item => (
            <div key={item.label} style={{ background: T.hover, borderRadius: 8, padding: "8px 10px" }}>
              <div style={{ fontSize: 9, color: T.dim, fontFamily: "'JetBrains Mono',monospace" }}>{item.label.toUpperCase()}</div>
              <div style={{ fontSize: 12, fontWeight: 700, color: T.text }}>{item.value}</div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

// ─── NAV ─────────────────────────────────────────────────────────────────────
const NAV = [
  { id: "overview", icon: "home", label: "Overview" },
  { id: "services", icon: "services", label: "Services" },
  { id: "agents", icon: "robot", label: "Agent Corps" },
  { id: "governance", icon: "shield", label: "Governance" },
  { id: "ledger", icon: "lock", label: "Forensic Ledger" },
  { id: "wallet", icon: "wallet", label: "Wallet" },
  { id: "infra", icon: "monitor", label: "Infrastructure" },
  { id: "security", icon: "security", label: "Security", ownerOnly: true },
];

// ─── ROOT ─────────────────────────────────────────────────────────────────────
export default function App() {
  const [view, setView] = useState("overview");
  const [time, setTime] = useState(new Date());

  // Live Wallet API connection
  const { walletData, connectionStatus, lastUpdate, error } = useWalletData();

  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  const viewMap = {
    overview: <OverviewView walletData={walletData} connectionStatus={connectionStatus} />,
    services: <ServicesView />,
    agents: <AgentsView />,
    governance: <GovernanceView />,
    ledger: <LedgerView />,
    wallet: <WalletView walletData={walletData} connectionStatus={connectionStatus} lastUpdate={lastUpdate} />,
    infra: <InfraView />,
    security: <SecurityView />,
  };

  const isOwner = mockUser.role === "owner";
  const visibleNav = NAV.filter(n => !n.ownerOnly || isOwner);

  return (
    <div style={{ minHeight: "100vh", background: T.bg, display: "flex", fontFamily: "Bricolage Grotesque,sans-serif" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap');
        @keyframes panelIn { from{opacity:0;transform:translateX(-8px) scale(0.98)} to{opacity:1;transform:translateX(0) scale(1)} }
        ::-webkit-scrollbar{width:4px} ::-webkit-scrollbar-track{background:transparent} ::-webkit-scrollbar-thumb{background:#8B691444;border-radius:2px}
      `}</style>

      {/* SIDEBAR */}
      <div style={{ width: 220, background: T.sidebar, display: "flex", flexDirection: "column", position: "sticky", top: 0, height: "100vh", flexShrink: 0, overflowY: "auto" }}>
        <div style={{ padding: "18px 16px 12px" }}>
          <div style={{ fontSize: 17, fontWeight: 900, color: "#f5f0e0", letterSpacing: "0.06em" }}>WINDI</div>
          <div style={{ fontSize: 9, color: T.gold, fontFamily: "'JetBrains Mono',monospace", marginTop: 1 }}>Command Center</div>
        </div>

        <SidebarDivider />

        {/* USER BUTTON */}
        <div style={{ padding: "8px 10px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 10px", borderRadius: 10, background: T.sidebarHover }}>
            <div style={{ width: 34, height: 34, borderRadius: "50%", background: T.gold, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 12, fontWeight: 800, color: "white", flexShrink: 0 }}>JM</div>
            <div style={{ flex: 1, textAlign: "left", minWidth: 0 }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: "#f5f0e0", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>Human Dragon</div>
              <div style={{ fontSize: 8, color: T.gold, fontFamily: "'JetBrains Mono',monospace" }}>Pioneer #1 • OWNER</div>
            </div>
          </div>
        </div>

        <SidebarDivider />

        <nav style={{ flex: 1, padding: "6px 10px", display: "flex", flexDirection: "column", gap: 2 }}>
          {visibleNav.map(n => (
            <button key={n.id} onClick={() => setView(n.id)}
              style={{ display: "flex", alignItems: "center", gap: 9, width: "100%",
                padding: "9px 12px", borderRadius: 8, border: "none", cursor: "pointer", textAlign: "left",
                background: view === n.id ? "#2a2420" : "transparent",
                color: view === n.id ? "#f5f0e0" : n.ownerOnly ? T.gold : T.dim,
                fontSize: 12, fontWeight: view === n.id ? 700 : 500,
                fontFamily: "Bricolage Grotesque,sans-serif", transition: "all 0.12s",
                borderLeft: view === n.id ? `2px solid ${T.gold}` : "2px solid transparent" }}>
              <Icon name={n.icon} size={16} />
              {n.label}
              {n.ownerOnly && <span style={{ marginLeft: "auto", fontSize: 8, color: T.gold, fontFamily: "'JetBrains Mono',monospace", opacity: 0.7 }}>OWNER</span>}
            </button>
          ))}
        </nav>

        <SidebarDivider />

        <div style={{ padding: "10px 14px 16px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 5, marginBottom: 3 }}>
            <StatusDot status="UP" />
            <span style={{ fontSize: 9, color: "#555", fontFamily: "'JetBrains Mono',monospace" }}>ALL SYSTEMS GREEN</span>
          </div>
          <div style={{ fontSize: 8, color: "#3a3530", fontFamily: "'JetBrains Mono',monospace" }}>
            {time.toLocaleTimeString("pt-BR", { hour12: false })}
          </div>
          <div style={{ fontSize: 8, color: "#3a3530", fontFamily: "'JetBrains Mono',monospace" }}>{ALIAS.node}</div>
        </div>
      </div>

      {/* MAIN */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", minHeight: "100vh", overflowY: "auto" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between",
          padding: "16px 24px", position: "sticky", top: 0, background: T.bg, zIndex: 10,
          borderBottom: `1px solid ${T.border}` }}>
          <div>
            <div style={{ fontSize: 20, fontWeight: 900, color: T.text, display: "flex", alignItems: "center", gap: 8 }}>
              <Icon name={NAV.find(n => n.id === view)?.icon} size={20} style={{ color: T.gold }} />
              {NAV.find(n => n.id === view)?.label}
            </div>
            <div style={{ fontSize: 10, color: T.dim, fontFamily: "'JetBrains Mono',monospace", marginTop: 2 }}>
              {ALIAS.domains.primary} • {time.toLocaleDateString("pt-BR", { weekday: "long", day: "numeric", month: "long", year: "numeric" })}
            </div>
          </div>
          <div style={{ display: "flex", gap: 6 }}>
            <div style={{ padding: "4px 12px", background: T.greenBg, border: `1px solid ${T.greenBorder}`, borderRadius: 20, fontSize: 10, fontWeight: 700, color: T.green }}>● LIVE</div>
            <div style={{ padding: "4px 12px", background: T.amberBg, border: `1px solid ${T.amberBorder}`, borderRadius: 20, fontSize: 10, fontWeight: 700, color: T.amber, display: "flex", alignItems: "center", gap: 4 }}>
              <Icon name="shield" size={12} /> GOLD
            </div>
            <div style={{ padding: "4px 12px", background: "#eff6ff", border: `1px solid ${T.blueBorder}`, borderRadius: 20, fontSize: 10, fontWeight: 700, color: T.blue, display: "flex", alignItems: "center", gap: 4 }}>
              <Icon name="lock" size={12} /> SL-{SECURITY_LAYERS.filter(l => l.status === "ACTIVE").length}/7
            </div>
          </div>
        </div>

        <div style={{ padding: "20px 24px 32px" }}>
          {viewMap[view]}
        </div>

        <div style={{ marginTop: "auto", padding: "12px 24px", borderTop: `1px solid ${T.border}`, textAlign: "center" }}>
          <div style={{ fontSize: 9, color: T.dim, fontFamily: "'JetBrains Mono',monospace" }}>
            WINDI Publishing House • Kempten, Bavaria • "AI processes. Human decides. WINDI guarantees." • OM SHANTI
          </div>
        </div>
      </div>
    </div>
  );
}
