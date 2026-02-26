/* WINDI Tenant Stamp Renderer v1.0.0
   Purpose: Visual tenant stamp for exported documents (JMPG/PDF)
   Style: "Papel moeda" (banknote) — institutional, verifiable
   Themes: KLAR (light) / NOIR (dark)

   26 February 2026 — WINDI Governance Institute
*/

(function initTenantStamp(global) {

  /**
   * Render tenant stamp HTML
   * @param {Object} opts
   * @param {string} opts.tenantId - Tenant identifier
   * @param {string} opts.mode - Segregation mode (default: "forensic-metadata")
   * @param {string} opts.level - Governance level (GOLD, HIGH, MEDIUM)
   * @param {number} opts.isolationScore - Optional isolation score (0-100)
   * @returns {string} HTML string
   */
  function renderTenantStamp({ tenantId, mode = "forensic-metadata", level = "GOLD", isolationScore = null }) {
    const safeTenant = (tenantId || "UNKNOWN").toUpperCase().replace(/[^A-Z0-9_-]/g, "");
    const safeMode = (mode || "forensic-metadata").replace(/[^a-z0-9_-]/gi, "");
    const safeLevel = (level || "GOLD").toUpperCase();

    const scoreHtml = isolationScore !== null
      ? `<span class="windi-tenant-stamp__score" title="Isolation Score">${isolationScore}/100</span>`
      : '';

    return `
      <div class="windi-tenant-stamp" data-level="${safeLevel}">
        <div class="windi-tenant-stamp__top">
          <span class="windi-tenant-stamp__mark">WINDI</span>
          <span class="windi-tenant-stamp__lvl">${safeLevel}</span>
        </div>
        <div class="windi-tenant-stamp__mid">
          <span class="windi-tenant-stamp__label">TENANT</span>
          <span class="windi-tenant-stamp__id">${safeTenant}</span>
        </div>
        <div class="windi-tenant-stamp__bot">
          <span class="windi-tenant-stamp__mode">${safeMode}</span>
          ${scoreHtml}
          <span class="windi-tenant-stamp__micro">EVIDENCE-ANCHORED</span>
        </div>
      </div>
    `;
  }

  /**
   * Build tenant stamp object for JMPG manifest
   * @param {string} tenantId - Tenant identifier
   * @param {Object} opts - Additional options
   * @returns {Object} Stamp object for manifest
   */
  function buildTenantStampManifest(tenantId, opts = {}) {
    const tid = tenantId || "unknown";
    const isoScore = global.WINDI_TenantAudit?.isolationScore?.(tid);

    return {
      tenant: {
        id: tid,
        stamp: `TENANT: ${tid.toUpperCase()}`,
        segregation_mode: opts.mode || "forensic-metadata",
        isolation_score: isoScore?.score || null,
        compliance_pack: opts.compliance_pack || global.WINDI_Tenant?.profile?.compliance_pack || ["GDPR"],
        timestamp: new Date().toISOString(),
        verification: {
          method: "ledger-anchored",
          hash_algorithm: "SHA-256",
          evidence_type: "forensic-metadata"
        }
      }
    };
  }

  /**
   * Inject stamp CSS into document (if not already present)
   */
  function injectStampCSS() {
    if (document.getElementById('windi-tenant-stamp-css')) return;

    const css = `
/* WINDI Tenant Stamp — Paper Money Style */

.windi-tenant-stamp {
  width: 280px;
  border-radius: 12px;
  padding: 10px 12px;
  position: relative;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
  letter-spacing: 0.2px;
  user-select: none;
}

.windi-tenant-stamp::before {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: 12px;
  pointer-events: none;
  opacity: 0.35;
}

/* Layout */
.windi-tenant-stamp__top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 10px;
  text-transform: uppercase;
  opacity: 0.9;
}

.windi-tenant-stamp__mark {
  font-weight: 800;
  letter-spacing: 1px;
}

.windi-tenant-stamp__lvl {
  font-weight: 800;
  padding: 2px 8px;
  border-radius: 999px;
}

.windi-tenant-stamp__mid {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-top: 8px;
}

.windi-tenant-stamp__label {
  font-size: 10px;
  text-transform: uppercase;
  opacity: 0.75;
}

.windi-tenant-stamp__id {
  font-size: 14px;
  font-weight: 900;
  letter-spacing: 0.6px;
}

.windi-tenant-stamp__bot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
  font-size: 9px;
  opacity: 0.8;
}

.windi-tenant-stamp__score {
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.08);
}

.windi-tenant-stamp__micro {
  font-size: 8px;
  letter-spacing: 1px;
  opacity: 0.65;
  text-transform: uppercase;
}

/* KLAR Theme (Light) */
[data-theme="klar"] .windi-tenant-stamp,
.windi-tenant-stamp--klar {
  background: linear-gradient(135deg, #FDFBF5, #F5ECD0);
  border: 1px solid rgba(139, 105, 20, 0.35);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  color: #2C2924;
}

[data-theme="klar"] .windi-tenant-stamp::before,
.windi-tenant-stamp--klar::before {
  border: 2px double rgba(139, 105, 20, 0.35);
  background:
    repeating-linear-gradient(45deg,
      rgba(139, 105, 20, 0.08) 0px,
      rgba(139, 105, 20, 0.08) 2px,
      transparent 2px,
      transparent 6px
    );
}

[data-theme="klar"] .windi-tenant-stamp__lvl,
.windi-tenant-stamp--klar .windi-tenant-stamp__lvl {
  background: rgba(139, 105, 20, 0.12);
  border: 1px solid rgba(139, 105, 20, 0.30);
  color: #8B6914;
}

[data-theme="klar"] .windi-tenant-stamp__id,
.windi-tenant-stamp--klar .windi-tenant-stamp__id {
  color: #2C2924;
}

[data-theme="klar"] .windi-tenant-stamp__score,
.windi-tenant-stamp--klar .windi-tenant-stamp__score {
  background: rgba(139, 105, 20, 0.12);
  color: #8B6914;
}

/* NOIR Theme (Dark) */
[data-theme="noir"] .windi-tenant-stamp,
.windi-tenant-stamp--noir {
  background: linear-gradient(135deg, #0E0E14, #16161F);
  border: 1px solid rgba(212, 168, 67, 0.28);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.45);
  color: #E2E2EA;
}

[data-theme="noir"] .windi-tenant-stamp::before,
.windi-tenant-stamp--noir::before {
  border: 2px double rgba(212, 168, 67, 0.28);
  background:
    radial-gradient(circle at 20% 20%, rgba(212, 168, 67, 0.10), transparent 45%),
    repeating-linear-gradient(90deg,
      rgba(212, 168, 67, 0.06) 0px,
      rgba(212, 168, 67, 0.06) 1px,
      transparent 1px,
      transparent 5px
    );
}

[data-theme="noir"] .windi-tenant-stamp__lvl,
.windi-tenant-stamp--noir .windi-tenant-stamp__lvl {
  background: rgba(212, 168, 67, 0.12);
  border: 1px solid rgba(212, 168, 67, 0.25);
  color: #D4A843;
}

[data-theme="noir"] .windi-tenant-stamp__id,
.windi-tenant-stamp--noir .windi-tenant-stamp__id {
  color: #D4A843;
}

[data-theme="noir"] .windi-tenant-stamp__score,
.windi-tenant-stamp--noir .windi-tenant-stamp__score {
  background: rgba(212, 168, 67, 0.15);
  color: #D4A843;
}

/* Level-specific highlights */
.windi-tenant-stamp[data-level="GOLD"] .windi-tenant-stamp__lvl {
  filter: saturate(1.2);
}

.windi-tenant-stamp[data-level="HIGH"] .windi-tenant-stamp__lvl {
  filter: saturate(1.0);
}

.windi-tenant-stamp[data-level="MEDIUM"] .windi-tenant-stamp__lvl {
  opacity: 0.9;
}

/* Print-friendly adjustments */
@media print {
  .windi-tenant-stamp {
    box-shadow: none !important;
    border-width: 2px !important;
  }
  .windi-tenant-stamp::before {
    opacity: 0.2 !important;
  }
}
    `;

    const style = document.createElement('style');
    style.id = 'windi-tenant-stamp-css';
    style.textContent = css;
    document.head.appendChild(style);
  }

  /**
   * Create a stamp element and return it (DOM node)
   * @param {Object} opts - Same as renderTenantStamp
   * @param {string} theme - 'klar' or 'noir'
   * @returns {HTMLElement}
   */
  function createStampElement(opts, theme = 'klar') {
    injectStampCSS();

    const wrapper = document.createElement('div');
    wrapper.innerHTML = renderTenantStamp(opts);
    const stamp = wrapper.firstElementChild;

    // Apply theme class directly for standalone use
    stamp.classList.add(`windi-tenant-stamp--${theme}`);

    return stamp;
  }

  // Expose API
  global.WINDI_TenantStamp = {
    version: "1.0.0",
    render: renderTenantStamp,
    buildManifest: buildTenantStampManifest,
    injectCSS: injectStampCSS,
    createElement: createStampElement
  };

  console.log('[WINDI] TenantStamp v1.0.0 loaded');

})(window);
