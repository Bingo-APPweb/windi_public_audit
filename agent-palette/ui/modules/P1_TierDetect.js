/**
 * ═══════════════════════════════════════════════════════════════════════════════════
 * WINDI P1 — TierDetect Module
 * Agent Palette UNIFIED · Hostname-based tier detection
 * ═══════════════════════════════════════════════════════════════════════════════════
 * 
 * Detects user tier based on hostname/path:
 * - windi-domain.com/personal/* → FREE
 * - windi-domain.com/org/* → MED
 * - windi-domain.com/* → HIGH
 * - localhost:8108 → HIGH (dev mode)
 * - fallback → FREE
 * 
 * @module P1_TierDetect
 * @version 1.0.0
 */

// ─── TIER CONSTANTS ───────────────────────────────────────────────────────────
export const TIER_FREE = "FREE";
export const TIER_MED = "MED";
export const TIER_HIGH = "HIGH";

// ─── TIER CONFIGURATIONS ──────────────────────────────────────────────────────
const TIER_CONFIGS = {
  [TIER_FREE]: {
    docTypes: ["letter", "email", "note", "memo", "journal", "recipe"],
    exports: ["docx"],
    maxDocs: 5,
    label: "Personal",
    labelDE: "Persönlich",
    labelPT: "Pessoal"
  },
  [TIER_MED]: {
    docTypes: [
      "letter", "email", "note", "memo", "journal", "recipe",
      "report", "contract", "invoice", "protocol", "analysis", "presentation"
    ],
    exports: ["docx", "pdf", "xlsx", "pptx"],
    maxDocs: 50,
    label: "Organization",
    labelDE: "Organisation",
    labelPT: "Organização"
  },
  [TIER_HIGH]: {
    docTypes: [
      "letter", "email", "note", "memo", "journal", "recipe",
      "report", "contract", "invoice", "protocol", "analysis", "presentation",
      "communique", "certificate"
    ],
    exports: ["docx", "pdf", "xlsx", "pptx", "jmpg"],
    maxDocs: -1, // unlimited
    label: "Governance",
    labelDE: "Governance",
    labelPT: "Governança"
  }
};

// ─── DETECTION RULES ──────────────────────────────────────────────────────────
const DETECTION_RULES = [
  // Dev mode: localhost:8108 → HIGH
  {
    test: (hostname, port, path) => hostname === "localhost" && port === "8108",
    tier: TIER_HIGH,
    reason: "dev_mode"
  },
  // Admin domain → HIGH
  {
    test: (hostname, port, path) => hostname === "windi-domain.com",
    tier: TIER_HIGH,
    reason: "admin_domain"
  },
  // Master domain → HIGH
  {
    test: (hostname, port, path) => hostname === "windi-domain.com",
    tier: TIER_HIGH,
    reason: "master_domain"
  },
  // Organization path → MED
  {
    test: (hostname, port, path) => path.startsWith("/org/") || path.startsWith("/organization/"),
    tier: TIER_MED,
    reason: "org_path"
  },
  // Personal path → FREE
  {
    test: (hostname, port, path) => path.startsWith("/personal/") || path.startsWith("/free/"),
    tier: TIER_FREE,
    reason: "personal_path"
  },
  // Palette path on admin → HIGH
  {
    test: (hostname, port, path) => path.startsWith("/palette/"),
    tier: TIER_HIGH,
    reason: "palette_path"
  }
];

/**
 * Detects the current tier based on window.location
 * 
 * @returns {{tier: string, hostname: string, path: string, port: string, reason: string}}
 * 
 * @example
 * const { tier, hostname } = detectTier();
 * console.log(`Running in ${tier} mode on ${hostname}`);
 */
export function detectTier() {
  // Safe fallback for non-browser environments
  if (typeof window === "undefined" || !window.location) {
    return {
      tier: TIER_FREE,
      hostname: "unknown",
      path: "/",
      port: "",
      reason: "no_window"
    };
  }

  const { hostname, pathname, port } = window.location;
  const path = pathname || "/";
  const actualPort = port || (window.location.protocol === "https:" ? "443" : "80");

  // Test each rule in order
  for (const rule of DETECTION_RULES) {
    if (rule.test(hostname, actualPort, path)) {
      return {
        tier: rule.tier,
        hostname,
        path,
        port: actualPort,
        reason: rule.reason
      };
    }
  }

  // Default fallback: FREE
  return {
    tier: TIER_FREE,
    hostname,
    path,
    port: actualPort,
    reason: "fallback"
  };
}

/**
 * Gets the configuration for a specific tier
 * 
 * @param {string} tier - One of TIER_FREE, TIER_MED, TIER_HIGH
 * @returns {{docTypes: string[], exports: string[], maxDocs: number, label: string, labelDE: string, labelPT: string}}
 * 
 * @example
 * const config = getTierConfig(TIER_MED);
 * console.log(`${config.label}: ${config.docTypes.length} doc types available`);
 */
export function getTierConfig(tier) {
  return TIER_CONFIGS[tier] || TIER_CONFIGS[TIER_FREE];
}

/**
 * Checks if a specific feature is available for a tier
 * 
 * @param {string} tier - Current tier
 * @param {string} docType - Document type to check
 * @returns {boolean}
 */
export function isDocTypeAvailable(tier, docType) {
  const config = getTierConfig(tier);
  return config.docTypes.includes(docType);
}

/**
 * Checks if an export format is available for a tier
 * 
 * @param {string} tier - Current tier
 * @param {string} format - Export format to check
 * @returns {boolean}
 */
export function isExportAvailable(tier, format) {
  const config = getTierConfig(tier);
  return config.exports.includes(format);
}

/**
 * Gets the tier required for a specific document type
 * 
 * @param {string} docType - Document type
 * @returns {string} - Required tier (TIER_FREE, TIER_MED, or TIER_HIGH)
 */
export function getRequiredTier(docType) {
  if (TIER_CONFIGS[TIER_FREE].docTypes.includes(docType)) return TIER_FREE;
  if (TIER_CONFIGS[TIER_MED].docTypes.includes(docType)) return TIER_MED;
  if (TIER_CONFIGS[TIER_HIGH].docTypes.includes(docType)) return TIER_HIGH;
  return TIER_HIGH; // Unknown types require highest tier
}

// ─── DEFAULT EXPORT ───────────────────────────────────────────────────────────
export default {
  detectTier,
  getTierConfig,
  isDocTypeAvailable,
  isExportAvailable,
  getRequiredTier,
  TIER_FREE,
  TIER_MED,
  TIER_HIGH
};
