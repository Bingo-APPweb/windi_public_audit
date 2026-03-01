/**
 * ═══════════════════════════════════════════════════════════════════════════════════
 * WINDI P5 — Connectors Module
 * 5 API bridges to backend services with graceful fallback
 * ═══════════════════════════════════════════════════════════════════════════════════
 * 
 * C1: Ledger   → POST /api/receipt (seal document)
 * C2: Export   → POST /api/export (render PDF/DOCX/XLSX/PPTX)
 * C3: Vault    → POST /api/store (archive sealed doc)
 * C4: Communiqué → POST /api/publish (publish communiqué)
 * C5: Wallet   → GET /api/identity (fetch/verify DID)
 * 
 * @module P5_Connectors
 * @version 1.0.0
 */

import { TIER_FREE, TIER_MED, TIER_HIGH } from './P1_TierDetect.js';

// ─── CONNECTOR STATUS ─────────────────────────────────────────────────────────
export const STATUS = {
  ONLINE: "online",
  OFFLINE: "offline",
  UNKNOWN: "unknown"
};

// ─── BASE CONNECTOR CLASS ─────────────────────────────────────────────────────
class BaseConnector {
  constructor(name, endpoint, tierRequired) {
    this.name = name;
    this.endpoint = endpoint;
    this.tierRequired = tierRequired;
    this.status = STATUS.UNKNOWN;
    this.lastCheck = null;
    this.lastError = null;
  }

  async check() {
    if (!this.endpoint) {
      this.status = STATUS.OFFLINE;
      return false;
    }

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2000);
      
      const response = await fetch(this.endpoint, {
        method: "HEAD",
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      this.status = response.ok ? STATUS.ONLINE : STATUS.OFFLINE;
      this.lastCheck = new Date();
      return this.status === STATUS.ONLINE;
    } catch (e) {
      this.status = STATUS.OFFLINE;
      this.lastError = e.message;
      this.lastCheck = new Date();
      return false;
    }
  }

  async execute(payload) {
    throw new Error("execute() must be implemented by subclass");
  }

  fallback(payload) {
    throw new Error("fallback() must be implemented by subclass");
  }

  async run(payload) {
    // Try online first
    if (this.status === STATUS.ONLINE || this.status === STATUS.UNKNOWN) {
      try {
        return await this.execute(payload);
      } catch (e) {
        console.warn("[" + this.name + "] Execute failed, using fallback:", e);
        this.status = STATUS.OFFLINE;
        this.lastError = e.message;
      }
    }
    
    // Fallback
    return this.fallback(payload);
  }

  toJSON() {
    return {
      name: this.name,
      endpoint: this.endpoint,
      tierRequired: this.tierRequired,
      status: this.status,
      lastCheck: this.lastCheck,
      lastError: this.lastError
    };
  }
}

// ─── C1: LEDGER CONNECTOR ─────────────────────────────────────────────────────
class LedgerConnector extends BaseConnector {
  constructor(endpoint) {
    super("Ledger", endpoint, TIER_FREE);
  }

  async execute(payload) {
    const response = await fetch(this.endpoint + "/api/receipt", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error("Ledger API error: " + response.status);
    }

    return await response.json();
  }

  fallback(payload) {
    // Generate local receipt like CryptoProvider.receiptId()
    const id = "VR-" + Date.now().toString(36).toUpperCase() + "-" + Math.random().toString(36).slice(2, 6).toUpperCase();
    const serial = "WINDI-2026-" + String(Math.floor(Math.random() * 999999)).padStart(6, "0");
    
    return {
      success: true,
      fallback: true,
      data: {
        receipt_id: id,
        serial: serial,
        timestamp: new Date().toISOString(),
        content_hash: payload.hash || "local-" + Date.now().toString(16),
        wallet_id: payload.wallet_id
      }
    };
  }
}

// ─── C2: EXPORT CONNECTOR ─────────────────────────────────────────────────────
class ExportConnector extends BaseConnector {
  constructor(endpoint) {
    super("Export", endpoint, TIER_FREE); // Base tier, but formats have individual requirements
  }

  // Format tier requirements
  static FORMAT_TIERS = {
    docx: TIER_FREE,
    pdf: TIER_MED,
    xlsx: TIER_MED,
    pptx: TIER_MED,
    jmpg: TIER_HIGH
  };

  getFormatTier(format) {
    return ExportConnector.FORMAT_TIERS[format] || TIER_HIGH;
  }

  async execute(payload) {
    const response = await fetch(this.endpoint + "/api/export", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error("Export API error: " + response.status);
    }

    return await response.json();
  }

  fallback(payload) {
    return {
      success: false,
      fallback: true,
      error: "Export service offline. Please try again later.",
      error_de: "Export-Dienst offline. Bitte später erneut versuchen.",
      error_pt: "Serviço de exportação offline. Tente novamente mais tarde."
    };
  }
}

// ─── C3: VAULT CONNECTOR ──────────────────────────────────────────────────────
class VaultConnector extends BaseConnector {
  constructor(endpoint) {
    super("Vault", endpoint, TIER_MED);
  }

  async execute(payload) {
    const response = await fetch(this.endpoint + "/api/store", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error("Vault API error: " + response.status);
    }

    return await response.json();
  }

  fallback(payload) {
    // Skip vault storage when offline - doc stays in Ledger only
    return {
      success: true,
      fallback: true,
      skipped: true,
      message: "Vault storage skipped (offline). Document is in Ledger.",
      message_de: "Vault-Speicherung übersprungen (offline). Dokument ist im Ledger.",
      message_pt: "Armazenamento Vault ignorado (offline). Documento está no Ledger."
    };
  }
}

// ─── C4: COMMUNIQUÉ CONNECTOR ─────────────────────────────────────────────────
class CommuniqueConnector extends BaseConnector {
  constructor(endpoint) {
    super("Communique", endpoint, TIER_HIGH);
  }

  async execute(payload) {
    const response = await fetch(this.endpoint + "/api/publish", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error("Communique API error: " + response.status);
    }

    return await response.json();
  }

  fallback(payload) {
    return {
      success: false,
      fallback: true,
      error: "Communiqué service offline.",
      error_de: "Communiqué-Dienst offline.",
      error_pt: "Serviço Communiqué offline."
    };
  }
}

// ─── C5: WALLET CONNECTOR ─────────────────────────────────────────────────────
class WalletConnector extends BaseConnector {
  constructor(endpoint) {
    super("Wallet", endpoint, TIER_FREE);
  }

  async execute(payload) {
    const url = this.endpoint + "/api/identity" + (payload.wallet_id ? "?id=" + payload.wallet_id : "");
    const response = await fetch(url, {
      method: "GET",
      headers: { "Content-Type": "application/json" }
    });

    if (!response.ok) {
      throw new Error("Wallet API error: " + response.status);
    }

    return await response.json();
  }

  async verify(payload) {
    const response = await fetch(this.endpoint + "/api/verify", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error("Wallet verify error: " + response.status);
    }

    const data = await response.json();
    return data.verified === true;
  }

  fallback(payload) {
    // Use localStorage wallet as fallback
    try {
      const raw = localStorage.getItem("windi_personal_v6");
      if (raw) {
        const data = JSON.parse(raw);
        if (data.wallet) {
          return {
            success: true,
            fallback: true,
            data: data.wallet
          };
        }
      }
    } catch (e) {}

    return {
      success: false,
      fallback: true,
      error: "No local wallet found."
    };
  }
}

// ─── CONNECTOR MANAGER ────────────────────────────────────────────────────────
export class ConnectorManager {
  constructor(context) {
    this.context = context;
    this.connectors = {};
    this.statusListeners = [];
    this.initialized = false;
  }

  async init() {
    const endpoints = this.context ? this.context.endpoints : {};

    // Create connectors
    this.connectors = {
      ledger: new LedgerConnector(endpoints.ledger),
      export: new ExportConnector(endpoints.export),
      vault: new VaultConnector(endpoints.vault),
      communique: new CommuniqueConnector(endpoints.communique),
      wallet: new WalletConnector(endpoints.wallet)
    };

    // Test connectivity
    await this.checkAll();
    this.initialized = true;
    return this;
  }

  async checkAll() {
    const checks = Object.entries(this.connectors).map(async ([name, conn]) => {
      const oldStatus = conn.status;
      await conn.check();
      if (oldStatus !== conn.status) {
        this._notifyStatusChange(name, oldStatus, conn.status);
      }
    });
    await Promise.all(checks);
  }

  getConnector(name) {
    return this.connectors[name] || null;
  }

  async runConnector(name, payload) {
    const connector = this.getConnector(name);
    if (!connector) {
      return { success: false, error: "Unknown connector: " + name };
    }
    return await connector.run(payload);
  }

  onStatusChange(callback) {
    this.statusListeners.push(callback);
  }

  _notifyStatusChange(name, oldStatus, newStatus) {
    for (const listener of this.statusListeners) {
      try {
        listener(name, oldStatus, newStatus);
      } catch (e) {
        console.warn("[ConnectorManager] Listener error:", e);
      }
    }
  }

  getStatus() {
    const status = {};
    for (const [name, conn] of Object.entries(this.connectors)) {
      status[name] = conn.toJSON();
    }
    return status;
  }

  toJSON() {
    return {
      initialized: this.initialized,
      connectors: this.getStatus()
    };
  }
}

/**
 * Factory function to create and initialize ConnectorManager
 * @param {WindiContext} context
 * @returns {Promise<ConnectorManager>}
 */
export async function createConnectorManager(context) {
  const manager = new ConnectorManager(context);
  await manager.init();
  return manager;
}

export default {
  ConnectorManager,
  createConnectorManager,
  STATUS,
  LedgerConnector,
  ExportConnector,
  VaultConnector,
  CommuniqueConnector,
  WalletConnector
};
