/**
 * ═══════════════════════════════════════════════════════════════════════════════════
 * WINDI P6 — Smart Tabs Module
 * Tier-gated sidebar with intelligent tab visibility
 * ═══════════════════════════════════════════════════════════════════════════════════
 * 
 * Tab visibility by tier:
 * - FREE:  chat, docs, wallet (3 tabs)
 * - MED:   + files, search, history (6 tabs)
 * - HIGH:  + products, journal (8 tabs)
 * 
 * @module P6_Tabs
 * @version 1.1.0 — Templates tab added
 */

const { useState, useEffect } = React;

import { TIER_FREE, TIER_MED, TIER_HIGH } from './P1_TierDetect.js';

// ─── TAB CONFIGURATIONS ───────────────────────────────────────────────────────
const TAB_CONFIGS = {
  chat: {
    id: "chat",
    icon: "💬",
    tier: null, // Always available
    connects: null,
    badgeKey: "unreadCount"
  },
  docs: {
    id: "docs",
    icon: "📄",
    tier: null, // Always available
    connects: null,
    badgeKey: "docCount"
  },
  files: {
    id: "files",
    icon: "📁",
    tier: TIER_MED,
    connects: null,
    badgeKey: "fileCount"
  },
  wallet: {
    id: "wallet",
    icon: "👛",
    tier: null, // Always available
    connects: "Wallet(:8099)",
    badgeKey: "trustScore"
  },
  search: {
    id: "search",
    icon: "🔍",
    tier: TIER_MED,
    connects: null,
    badgeKey: null
  },
  products: {
    id: "products",
    icon: "🛒",
    tier: TIER_HIGH,
    connects: null,
    badgeKey: null
  },
  journal: {
    id: "journal",
    icon: "📰",
    tier: TIER_HIGH,
    connects: "Communique(:8105)",
    badgeKey: null
  },
  history: {
    id: "history",
    icon: "🕐",
    tier: TIER_MED,
    connects: "Ledger(:8101)",
    badgeKey: null
  },
  templates: {
    id: "templates",
    icon: "📋",
    tier: TIER_HIGH,
    connects: "DragonChat(:8111)",
    badgeKey: "templateCount"
  }
};

// Tab order
const TAB_ORDER = ["chat", "docs", "files", "wallet", "search", "products", "journal", "history", "templates"];

// ─── TIER HIERARCHY ───────────────────────────────────────────────────────────
const TIER_LEVEL = {
  [TIER_FREE]: 1,
  [TIER_MED]: 2,
  [TIER_HIGH]: 3
};

// ─── LABELS ───────────────────────────────────────────────────────────────────
const TAB_LABELS = {
  de: {
    chat: "Chat",
    docs: "Dokumente",
    files: "Dateien",
    wallet: "Brieftasche",
    search: "Suche",
    products: "Produkte",
    journal: "Zeitung",
    history: "Verlauf",
    templates: "Vorlagen",
    upgrade: "Upgrade zu",
    locked: "Gesperrt"
  },
  en: {
    chat: "Chat",
    docs: "Documents",
    files: "Files",
    wallet: "Wallet",
    search: "Search",
    products: "Products",
    journal: "Journal",
    history: "History",
    templates: "Templates",
    upgrade: "Upgrade to",
    locked: "Locked"
  },
  pt: {
    chat: "Chat",
    docs: "Documentos",
    files: "Ficheiros",
    wallet: "Carteira",
    search: "Busca",
    products: "Produtos",
    journal: "Jornal",
    history: "Histórico",
    templates: "Modelos",
    upgrade: "Actualizar para",
    locked: "Bloqueado"
  }
};

/**
 * Checks if a tab is available for a given tier
 * @param {string} tabId - Tab identifier
 * @param {string} currentTier - Current user tier
 * @returns {boolean}
 */
export function isTabAvailable(tabId, currentTier) {
  const config = TAB_CONFIGS[tabId];
  if (!config) return false;
  if (!config.tier) return true; // No tier requirement
  
  const currentLevel = TIER_LEVEL[currentTier] || 1;
  const requiredLevel = TIER_LEVEL[config.tier] || 1;
  return currentLevel >= requiredLevel;
}

/**
 * Gets all available tabs for a tier
 * @param {string} tier - User tier
 * @returns {string[]}
 */
export function getAvailableTabs(tier) {
  return TAB_ORDER.filter(tabId => isTabAvailable(tabId, tier));
}

/**
 * SmartTabs React Component
 * Renders tier-aware sidebar
 * 
 * @param {object} props
 * @param {object} props.context - WindiContext instance
 * @param {string} props.activeTab - Currently active tab
 * @param {function} props.onTabChange - Tab change callback
 * @param {object} props.badges - Badge values { unreadCount, docCount, etc }
 * @param {object} props.theme - KLAR/NOIR theme object
 * @param {string} props.lang - Language code
 * @param {boolean} props.expanded - Sidebar expanded state
 * @param {function} props.onToggle - Toggle expansion callback
 */
export function SmartTabs({ 
  context, 
  activeTab = "chat", 
  onTabChange, 
  badges = {},
  theme,
  lang = "de",
  expanded = false,
  onToggle
}) {
  const [isMobile, setIsMobile] = useState(false);

  const th = theme || {
    gold: "#8B6914",
    success: "#4A7C59",
    dim: "#6B6560",
    text: "#2C2924",
    border: "#DDD6C2",
    sidebarBg: "#EDE8D8",
    sidebarActive: "#F5F0E0"
  };

  const labels = TAB_LABELS[lang] || TAB_LABELS.en;
  const currentTier = context ? context.tier : TIER_FREE;
  const currentTierLevel = TIER_LEVEL[currentTier] || 1;

  // Responsive detection
  useEffect(() => {
    const checkMobile = () => setIsMobile(window.innerWidth < 768);
    checkMobile();
    window.addEventListener("resize", checkMobile);
    return () => window.removeEventListener("resize", checkMobile);
  }, []);

  const handleTabClick = (tabId) => {
    if (isTabAvailable(tabId, currentTier)) {
      if (onTabChange) onTabChange(tabId);
      if (isMobile && onToggle) onToggle(false);
    }
  };

  return (
    <aside style={{
      width: isMobile ? (expanded ? 220 : 0) : 56,
      flexShrink: 0,
      background: th.sidebarBg,
      borderRight: "1px solid " + th.border + "44",
      display: "flex",
      flexDirection: "column",
      transition: "width 0.3s ease",
      overflow: "hidden",
      zIndex: 50,
      position: isMobile ? "absolute" : "relative",
      height: "100%"
    }}>
      {/* Logo */}
      <div style={{
        padding: "12px 0",
        textAlign: "center",
        borderBottom: "1px solid " + th.border + "22"
      }}>
        <span style={{ fontSize: 20 }}>🐉</span>
      </div>

      {/* Tabs */}
      <div style={{
        flex: 1,
        padding: "8px 0",
        display: "flex",
        flexDirection: "column",
        gap: 2
      }}>
        {TAB_ORDER.map(tabId => {
          const config = TAB_CONFIGS[tabId];
          const available = isTabAvailable(tabId, currentTier);
          const isActive = activeTab === tabId;
          const badge = badges[config.badgeKey];
          const requiredTier = config.tier;

          return (
            <button
              key={tabId}
              onClick={() => handleTabClick(tabId)}
              title={available ? labels[tabId] : (labels.upgrade + " " + requiredTier)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                padding: isMobile ? "10px 16px" : "10px 0",
                justifyContent: isMobile ? "flex-start" : "center",
                cursor: available ? "pointer" : "default",
                border: "none",
                background: isActive ? th.sidebarActive : th.sidebarBg,
                color: isActive ? th.gold : (available ? th.dim : th.dim + "66"),
                fontSize: 16,
                borderLeft: isActive ? ("3px solid " + th.gold) : "3px solid transparent",
                transition: "all 0.2s",
                opacity: available ? 1 : 0.4,
                position: "relative"
              }}
            >
              {/* Icon */}
              <span style={{ position: "relative" }}>
                {config.icon}
                {/* Badge */}
                {badge !== undefined && badge > 0 && (
                  <span style={{
                    position: "absolute",
                    top: -4,
                    right: -6,
                    minWidth: 14,
                    height: 14,
                    borderRadius: 7,
                    background: th.gold,
                    color: "#FFF",
                    fontSize: 8,
                    fontWeight: 700,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    padding: "0 3px"
                  }}>
                    {badge > 99 ? "99+" : badge}
                  </span>
                )}
              </span>

              {/* Label (mobile expanded) */}
              {(isMobile && expanded) && (
                <span style={{ fontSize: 12, fontWeight: 600 }}>
                  {labels[tabId]}
                </span>
              )}

              {/* Lock icon for unavailable tabs */}
              {!available && (
                <span style={{
                  position: "absolute",
                  right: isMobile ? 16 : 4,
                  fontSize: 8,
                  color: th.dim
                }}>
                  🔒
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Footer */}
      <div style={{
        padding: "8px",
        borderTop: "1px solid " + th.border + "22",
        display: "flex",
        flexDirection: "column",
        gap: 4,
        alignItems: "center"
      }}>
        {/* Tier indicator */}
        <div style={{
          fontSize: 8,
          color: th.dim,
          fontFamily: "'JetBrains Mono', monospace",
          padding: "2px 6px",
          borderRadius: 4,
          background: th.gold + "15",
          border: "1px solid " + th.gold + "22"
        }}>
          {currentTier}
        </div>
      </div>
    </aside>
  );
}

export default { SmartTabs, isTabAvailable, getAvailableTabs, TAB_CONFIGS };
