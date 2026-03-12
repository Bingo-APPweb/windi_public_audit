/**
 * W-FERR-001 — Dashboard Component
 * =================================
 * Mini-dashboard para integrar no WINDI Palette.
 */

(function() {
  'use strict';

  const STYLES = `
    .ferreiro-dash {
      position: fixed;
      bottom: 130px;
      left: 68px;
      width: 320px;
      background: #1e293b;
      border-radius: 12px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.4);
      font-family: system-ui, -apple-system, sans-serif;
      z-index: 9999;
      overflow: hidden;
      transition: all 0.3s ease;
    }

    .ferreiro-dash.minimized {
      width: auto;
      height: auto;
    }

    .ferreiro-dash-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px 16px;
      background: #0f172a;
      border-bottom: 1px solid #334155;
    }

    .ferreiro-dash-title {
      display: flex;
      align-items: center;
      gap: 8px;
      color: #f8fafc;
      font-weight: 600;
      font-size: 14px;
    }

    .ferreiro-dash-score {
      font-size: 24px;
      font-weight: bold;
      padding: 2px 10px;
      border-radius: 6px;
    }

    .ferreiro-dash-score.healthy { background: #22c55e20; color: #22c55e; }
    .ferreiro-dash-score.warning { background: #f59e0b20; color: #f59e0b; }
    .ferreiro-dash-score.critical { background: #ef444420; color: #ef4444; }

    .ferreiro-dash-body {
      padding: 16px;
    }

    .ferreiro-dash-section {
      margin-bottom: 12px;
    }

    .ferreiro-dash-section-title {
      color: #94a3b8;
      font-size: 11px;
      text-transform: uppercase;
      margin-bottom: 8px;
    }

    .ferreiro-dash-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 6px 0;
      border-bottom: 1px solid #334155;
    }

    .ferreiro-dash-row:last-child {
      border-bottom: none;
    }

    .ferreiro-dash-label {
      color: #e2e8f0;
      font-size: 13px;
    }

    .ferreiro-dash-value {
      font-size: 13px;
      font-weight: 500;
    }

    .ferreiro-dash-value.ok { color: #22c55e; }
    .ferreiro-dash-value.warning { color: #f59e0b; }
    .ferreiro-dash-value.error { color: #ef4444; }

    .ferreiro-dash-actions {
      display: flex;
      gap: 8px;
      padding: 12px 16px;
      background: #0f172a;
      border-top: 1px solid #334155;
    }

    .ferreiro-dash-btn {
      flex: 1;
      padding: 8px 12px;
      border: none;
      border-radius: 6px;
      font-size: 12px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s;
    }

    .ferreiro-dash-btn-primary {
      background: #3b82f6;
      color: white;
    }

    .ferreiro-dash-btn-primary:hover {
      background: #2563eb;
    }

    .ferreiro-dash-btn-secondary {
      background: #334155;
      color: #e2e8f0;
    }

    .ferreiro-dash-btn-secondary:hover {
      background: #475569;
    }

    .ferreiro-dash-icon {
      width: 20px;
      height: 20px;
    }

    .ferreiro-pulse {
      animation: ferreiro-pulse 2s infinite;
    }

    @keyframes ferreiro-pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    }

    .ferreiro-dash-toggle {
      position: fixed;
      bottom: 80px;
      left: 68px;
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background: #1e293b;
      border: 2px solid #334155;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      z-index: 10000;
      transition: all 0.2s;
    }

    .ferreiro-dash-toggle:hover {
      transform: scale(1.1);
      border-color: #3b82f6;
    }
  `;

  // SVG Icons
  const ICONS = {
    anvil: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" class="ferreiro-dash-icon"><path d="M7 14l5-5 5 5"/><path d="M4 18h16"/><rect x="6" y="10" width="12" height="4" rx="1"/></svg>`,
    check: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="ferreiro-dash-icon"><polyline points="20 6 9 17 4 12"/></svg>`,
    alert: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="ferreiro-dash-icon"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`,
    refresh: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="ferreiro-dash-icon"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>`,
    close: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="ferreiro-dash-icon"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>`
  };

  let dashboardEl = null;
  let toggleEl = null;
  let isVisible = false;

  /**
   * Inject styles
   */
  function injectStyles() {
    if (document.getElementById('ferreiro-dash-styles')) return;

    const style = document.createElement('style');
    style.id = 'ferreiro-dash-styles';
    style.textContent = STYLES;
    document.head.appendChild(style);
  }

  /**
   * Create dashboard HTML
   */
  function createDashboard(data) {
    const score = data?.score || 0;
    const status = score >= 90 ? 'healthy' : score >= 70 ? 'warning' : 'critical';

    const services = data?.services || { ok: 0, total: 0 };
    const manifests = data?.manifests || { ok: 0, total: 0 };
    const code = data?.code || { ok: 0, total: 0 };
    const issues = data?.issues?.length || 0;

    return `
      <div class="ferreiro-dash-header">
        <div class="ferreiro-dash-title">
          ${ICONS.anvil}
          <span>Ferreiro</span>
        </div>
        <div class="ferreiro-dash-score ${status}">${score}%</div>
      </div>

      <div class="ferreiro-dash-body">
        <div class="ferreiro-dash-section">
          <div class="ferreiro-dash-section-title">Services</div>
          <div class="ferreiro-dash-row">
            <span class="ferreiro-dash-label">Status</span>
            <span class="ferreiro-dash-value ${services.ok === services.total ? 'ok' : 'warning'}">
              ${services.ok}/${services.total}
            </span>
          </div>
        </div>

        <div class="ferreiro-dash-section">
          <div class="ferreiro-dash-section-title">Manifests</div>
          <div class="ferreiro-dash-row">
            <span class="ferreiro-dash-label">Valid</span>
            <span class="ferreiro-dash-value ${manifests.ok === manifests.total ? 'ok' : 'warning'}">
              ${manifests.ok}/${manifests.total}
            </span>
          </div>
        </div>

        <div class="ferreiro-dash-section">
          <div class="ferreiro-dash-section-title">Code Quality</div>
          <div class="ferreiro-dash-row">
            <span class="ferreiro-dash-label">Checks</span>
            <span class="ferreiro-dash-value ${code.issues === 0 ? 'ok' : 'warning'}">
              ${code.ok}/${code.total}
            </span>
          </div>
        </div>

        ${issues > 0 ? `
          <div class="ferreiro-dash-section">
            <div class="ferreiro-dash-section-title">Issues</div>
            <div class="ferreiro-dash-row">
              <span class="ferreiro-dash-label">Pending</span>
              <span class="ferreiro-dash-value error">${issues}</span>
            </div>
          </div>
        ` : ''}
      </div>

      <div class="ferreiro-dash-actions">
        <button class="ferreiro-dash-btn ferreiro-dash-btn-primary" onclick="FerreiroUI.runProbe()">
          ${ICONS.refresh} Scan
        </button>
        <button class="ferreiro-dash-btn ferreiro-dash-btn-secondary" onclick="FerreiroUI.hide()">
          ${ICONS.close} Close
        </button>
      </div>
    `;
  }

  /**
   * Create toggle button
   */
  function createToggle() {
    const toggle = document.createElement('div');
    toggle.className = 'ferreiro-dash-toggle';
    toggle.innerHTML = ICONS.anvil;
    toggle.onclick = () => isVisible ? hide() : show();
    return toggle;
  }

  /**
   * Initialize dashboard
   */
  function init() {
    injectStyles();

    // Create toggle
    toggleEl = createToggle();
    document.body.appendChild(toggleEl);

    // Create dashboard (hidden)
    dashboardEl = document.createElement('div');
    dashboardEl.className = 'ferreiro-dash';
    dashboardEl.style.display = 'none';
    document.body.appendChild(dashboardEl);

    // Subscribe to Ferreiro events
    if (window.Ferreiro) {
      window.Ferreiro.subscribe((event, data) => {
        if (event === 'probe') {
          update(data);
        }
      });
    }

    console.log('[FerreiroUI] Dashboard initialized');
  }

  /**
   * Show dashboard
   */
  function show() {
    if (!dashboardEl) return;
    dashboardEl.style.display = 'block';
    isVisible = true;
    toggleEl.style.display = 'none';

    // Load current data
    const status = window.Ferreiro?.getStatus();
    if (status?.lastProbe) {
      update(status.lastProbe);
    } else {
      dashboardEl.innerHTML = createDashboard(null);
    }
  }

  /**
   * Hide dashboard
   */
  function hide() {
    if (!dashboardEl) return;
    dashboardEl.style.display = 'none';
    isVisible = false;
    toggleEl.style.display = 'flex';
  }

  /**
   * Update dashboard with new data
   */
  function update(data) {
    if (!dashboardEl) return;
    dashboardEl.innerHTML = createDashboard(data);
  }

  /**
   * Run probe
   */
  async function runProbe() {
    if (!window.Ferreiro) {
      console.error('[FerreiroUI] Ferreiro not loaded');
      return;
    }

    const results = await window.Ferreiro.probeAll();
    update(results);
  }

  // Export
  const FerreiroUI = {
    init,
    show,
    hide,
    update,
    runProbe
  };

  if (typeof window !== 'undefined') {
    window.FerreiroUI = FerreiroUI;

    // Auto-init on DOM ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', init);
    } else {
      // DOM already ready
      setTimeout(init, 100);
    }
  }

})();
