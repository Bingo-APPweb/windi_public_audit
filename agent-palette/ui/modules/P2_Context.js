/**
 * ═══════════════════════════════════════════════════════════════════════════════════
 * WINDI P2 — Context Engine Module
 * Aggregates tier, endpoints, config, wallet, lang, theme
 * ═══════════════════════════════════════════════════════════════════════════════════
 * 
 * Ecosystem Ports:
 * 8099 Wallet "O Espelho" | 8100 Desktop | 8101 Ledger | 8102 Sentinel LAW
 * 8103 Export | 8104 JMPG | 8105 Communiqué | 8106 Vault | 8108 Dragon/Palette | 8109 Pulse
 * 
 * @module P2_Context
 * @version 1.0.0
 */

import { detectTier, getTierConfig, TIER_FREE, TIER_MED, TIER_HIGH } from './P1_TierDetect.js';

// ─── DEFAULT CONFIG (from Editor v6.0) ────────────────────────────────────────
const DEFAULT_CONFIG = {
  VERIFY_BASE_URL: "https://windi-domain.com/verify",
  CRYPTO_MODE: "sim",
  ANON_SECONDS: 300,
  AUTO_SAVE_MS: 5000,
  STORAGE_KEY: "windi_personal_v6"
};

// ─── SERVICE DEFINITIONS ──────────────────────────────────────────────────────
const SERVICES = {
  wallet:     { port: 8099, name: "Wallet O Espelho", tier: TIER_FREE },
  desktop:    { port: 8100, name: "Desktop", tier: TIER_FREE },
  ledger:     { port: 8101, name: "Ledger", tier: TIER_FREE },
  sentinel:   { port: 8102, name: "Sentinel LAW", tier: TIER_MED },
  export:     { port: 8103, name: "Export", tier: TIER_MED },
  jmpg:       { port: 8104, name: "JMPG Viewer", tier: TIER_HIGH },
  communique: { port: 8105, name: "Communiqué", tier: TIER_HIGH },
  vault:      { port: 8106, name: "Vault", tier: TIER_MED },
  dragon:     { port: 8108, name: "Dragon/Palette", tier: TIER_FREE },
  pulse:      { port: 8109, name: "Pulse", tier: TIER_HIGH }
};

const TIER_LEVEL = {
  [TIER_FREE]: 1,
  [TIER_MED]: 2,
  [TIER_HIGH]: 3
};

export class WindiContext {
  constructor() {
    this.tier = TIER_FREE;
    this.tierInfo = null;
    this.tierConfig = null;
    this.endpoints = {};
    this.config = { ...DEFAULT_CONFIG };
    this.wallet = null;
    this.lang = "de";
    this.theme = "KLAR";
    this.initialized = false;
  }

  async init() {
    this.tierInfo = detectTier();
    this.tier = this.tierInfo.tier;
    this.tierConfig = getTierConfig(this.tier);
    this._buildEndpoints();
    this._loadWallet();
    this._detectLanguage();
    this._loadTheme();
    this._applyTierConfig();
    this.initialized = true;
    return this;
  }

  _buildEndpoints() {
    const baseUrl = window.location.protocol === "https:" 
      ? "https://windi-domain.com" 
      : "http://localhost";
    const currentTierLevel = TIER_LEVEL[this.tier];

    for (const [key, service] of Object.entries(SERVICES)) {
      const serviceTierLevel = TIER_LEVEL[service.tier];
      if (currentTierLevel >= serviceTierLevel) {
        if (window.location.hostname === "localhost") {
          this.endpoints[key] = "http://localhost:" + service.port;
        } else {
          this.endpoints[key] = baseUrl + "/" + key;
        }
      } else {
        this.endpoints[key] = null;
      }
    }
  }

  _loadWallet() {
    try {
      const raw = localStorage.getItem(this.config.STORAGE_KEY);
      if (raw) {
        const data = JSON.parse(raw);
        if (data.wallet) this.wallet = data.wallet;
      }
    } catch (e) {
      this.wallet = null;
    }
  }

  _detectLanguage() {
    const navLang = navigator.language || navigator.userLanguage || "de";
    const shortLang = navLang.split("-")[0].toLowerCase();
    this.lang = ["de", "en", "pt"].includes(shortLang) ? shortLang : "de";
    try {
      const raw = localStorage.getItem(this.config.STORAGE_KEY);
      if (raw) {
        const data = JSON.parse(raw);
        if (data.lang && ["de", "en", "pt"].includes(data.lang)) {
          this.lang = data.lang;
        }
      }
    } catch (e) {}
  }

  _loadTheme() {
    try {
      const raw = localStorage.getItem(this.config.STORAGE_KEY);
      if (raw) {
        const data = JSON.parse(raw);
        if (data.theme && ["KLAR", "NOIR"].includes(data.theme)) {
          this.theme = data.theme;
        }
      }
    } catch (e) {}
  }

  _applyTierConfig() {
    if (this.tier === TIER_HIGH && window.crypto && window.crypto.subtle) {
      this.config.CRYPTO_MODE = "real";
    }
    if (this.tier === TIER_MED) {
      this.config.AUTO_SAVE_MS = 10000;
    }
    if (this.tier === TIER_HIGH) {
      this.config.ANON_SECONDS = 180;
    }
  }

  getEndpoint(service) {
    return this.endpoints[service] || null;
  }

  hasService(service) {
    return this.endpoints[service] !== null;
  }

  getAvailableServices() {
    return Object.entries(this.endpoints)
      .filter(([_, url]) => url !== null)
      .map(([name, _]) => name);
  }

  setWallet(wallet, persist = true) {
    this.wallet = wallet;
    if (persist) this._persistData();
  }

  setLanguage(lang, persist = true) {
    if (["de", "en", "pt"].includes(lang)) {
      this.lang = lang;
      if (persist) this._persistData();
    }
  }

  setTheme(theme, persist = true) {
    if (["KLAR", "NOIR"].includes(theme)) {
      this.theme = theme;
      if (persist) this._persistData();
    }
  }

  _persistData() {
    try {
      const data = { wallet: this.wallet, lang: this.lang, theme: this.theme };
      localStorage.setItem(this.config.STORAGE_KEY, JSON.stringify(data));
    } catch (e) {}
  }

  toJSON() {
    return {
      tier: this.tier,
      tierInfo: this.tierInfo,
      tierConfig: this.tierConfig,
      endpoints: this.endpoints,
      config: this.config,
      wallet: this.wallet ? { id: this.wallet.id, trustScore: this.wallet.trustScore } : null,
      lang: this.lang,
      theme: this.theme,
      initialized: this.initialized,
      availableServices: this.getAvailableServices()
    };
  }
}

export async function createContext() {
  const context = new WindiContext();
  await context.init();
  return context;
}

export default { WindiContext, createContext };
