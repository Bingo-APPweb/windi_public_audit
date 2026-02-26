/* WINDI TenantAuditCollector v1.0.0
   Purpose: Forensic tenant isolation telemetry (frontend-side)
   Output: window.WINDI_TenantAudit.*
   No external deps. Safe defaults.

   26 February 2026 — WINDI Governance Institute
*/

(function initTenantAuditCollector(global) {
  const STORE = {
    // session-level
    sessionId: `tenant-audit-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    startedAt: new Date().toISOString(),
    activeTenant: null,

    // per-tenant stats
    tenants: new Map(), // tenantId -> stats

    // cross-tenant incidents
    boundaryAlerts: [], // {ts, from, to, msgId, reason}
    conflicts: [],      // {ts, type, details}
  };

  function ensureTenant(tenantId) {
    const id = tenantId || "unknown";
    if (!STORE.tenants.has(id)) {
      STORE.tenants.set(id, {
        tenantId: id,
        messagesTotal: 0,
        messagesWithTenant: 0,

        receiptsTotal: 0,
        receiptsInstitutional: 0,
        receiptsWithTenant: 0,

        // optional, if you pass com_id or doc ids
        communiques: new Map(), // com_id -> tenantId

        // risk distribution optional
        risk: { R0:0, R1:0, R2:0, R3:0, R4:0, R5:0 },

        boundaryAlerts: 0,
        lastSeenAt: null,
      });
    }
    return STORE.tenants.get(id);
  }

  function nowTs() {
    return new Date().toISOString();
  }

  function normalizeRisk(risk) {
    if (!risk) return "R0";
    const r = String(risk).toUpperCase();
    if (/^R[0-5]$/.test(r)) return r;
    return "R0";
  }

  function setActiveTenant(tenantId, ctx = {}) {
    const to = tenantId || "unknown";
    if (!STORE.activeTenant) {
      STORE.activeTenant = to;
      ensureTenant(to).lastSeenAt = nowTs();
      return { ok: true, firstSet: true, activeTenant: to };
    }

    if (STORE.activeTenant !== to) {
      const from = STORE.activeTenant;
      STORE.activeTenant = to;

      const alert = {
        ts: nowTs(),
        from,
        to,
        msgId: ctx.msgId || null,
        reason: ctx.reason || "Tenant boundary changed within same conversation",
        action: "HUMAN_REVIEW_REQUIRED"
      };
      STORE.boundaryAlerts.push(alert);

      // increment per-tenant counters
      ensureTenant(from).boundaryAlerts += 1;
      ensureTenant(to).boundaryAlerts += 1;

      return { ok: false, boundaryAlert: alert, activeTenant: to };
    }

    ensureTenant(to).lastSeenAt = nowTs();
    return { ok: true, activeTenant: to };
  }

  // Track chat message event (call in handleSend/appendMessage)
  function trackMessage({ tenantId, msgId, role, risk }) {
    const t = ensureTenant(tenantId);
    t.messagesTotal += 1;
    if (tenantId) t.messagesWithTenant += 1;
    t.lastSeenAt = nowTs();

    const rr = normalizeRisk(risk);
    t.risk[rr] = (t.risk[rr] || 0) + 1;

    // update active tenant boundary
    // only enforce boundary checks for user->agent conversational flow
    if (role === "user" || role === "agent" || role === "assistant") {
      return setActiveTenant(tenantId, { msgId });
    }
    return { ok: true };
  }

  // Track ledger receipt event (call when you receive receipt payload)
  // receipt expected shape: { id, governance:{level}, metadata:{tenant_id}, doc:{com_id?}, ... }
  function trackReceipt(receipt) {
    if (!receipt || typeof receipt !== "object") return;

    const meta = receipt.metadata || {};
    const tenantId = meta.tenant_id || meta.tenantId || "unknown";
    const t = ensureTenant(tenantId);

    t.receiptsTotal += 1;

    const govLevel = (receipt.governance && receipt.governance.level) || receipt.governance_level;
    const institutional = govLevel === "HIGH" || govLevel === "GOLD" || govLevel === "MEDIUM";
    if (institutional) t.receiptsInstitutional += 1;

    if (meta.tenant_id || meta.tenantId) t.receiptsWithTenant += 1;
    t.lastSeenAt = nowTs();

    // Conflict detection (optional): same com_id seen with different tenant
    const comId =
      receipt.com_id ||
      (receipt.doc && (receipt.doc.com_id || receipt.doc.id)) ||
      meta.com_id ||
      null;

    if (comId) {
      // If comId is already seen in *another* tenant, flag conflict:
      for (const [otherTenantId, otherStats] of STORE.tenants.entries()) {
        if (otherTenantId === tenantId) continue;
        if (otherStats.communiques && otherStats.communiques.has(comId)) {
          const conflict = {
            ts: nowTs(),
            type: "COMMUNIQUE_TENANT_CONFLICT",
            details: { comId, tenantId, otherTenantId }
          };
          STORE.conflicts.push(conflict);
        }
      }
      t.communiques.set(comId, tenantId);
    }
  }

  function receiptsSummary(tenantId) {
    const t = ensureTenant(tenantId);

    const tenantCoveragePct = t.receiptsInstitutional === 0
      ? 100
      : Math.round((t.receiptsWithTenant / Math.max(1, t.receiptsInstitutional)) * 100);

    const boundaryAlerts = t.boundaryAlerts || 0;

    // conflicts touching this tenant
    const conflicts = STORE.conflicts.filter(c =>
      c.details?.tenantId === tenantId || c.details?.otherTenantId === tenantId
    ).length;

    return {
      tenantId,
      sessionId: STORE.sessionId,
      tenantCoveragePct,
      receiptsInstitutional: t.receiptsInstitutional,
      receiptsWithTenant: t.receiptsWithTenant,
      boundaryAlerts,
      conflicts,
      lastSeenAt: t.lastSeenAt
    };
  }

  // Calculate isolation score (0-100) for auditor demo
  function isolationScore(tenantId) {
    const summary = receiptsSummary(tenantId);

    let score = summary.tenantCoveragePct;

    // Penalize conflicts heavily
    if (summary.conflicts > 0) score -= 40;

    // Penalize boundary alerts
    score -= Math.min(summary.boundaryAlerts * 5, 25);

    score = Math.max(0, Math.min(100, Math.round(score)));

    return {
      score,
      tenantCoveragePct: summary.tenantCoveragePct,
      conflicts: summary.conflicts,
      boundaryAlerts: summary.boundaryAlerts,
      status: score >= 90 ? "excellent" : score >= 70 ? "good" : score >= 50 ? "warning" : "critical"
    };
  }

  function globalSummary() {
    const tenants = [];
    for (const [tenantId] of STORE.tenants.entries()) {
      tenants.push(receiptsSummary(tenantId));
    }

    const totalConflicts = STORE.conflicts.length;
    const totalBoundaryAlerts = STORE.boundaryAlerts.length;

    // overall coverage across all institutional receipts
    let inst = 0, withTenant = 0;
    for (const [, st] of STORE.tenants.entries()) {
      inst += st.receiptsInstitutional || 0;
      withTenant += st.receiptsWithTenant || 0;
    }
    const overallCoveragePct = inst === 0 ? 100 : Math.round((withTenant / Math.max(1, inst)) * 100);

    return {
      sessionId: STORE.sessionId,
      startedAt: STORE.startedAt,
      activeTenant: STORE.activeTenant,
      tenants,
      overallCoveragePct,
      totalConflicts,
      totalBoundaryAlerts
    };
  }

  // Backward-compatible boundary check (used by existing code)
  function checkBoundary(newTenant) {
    return setActiveTenant(newTenant);
  }

  function reset() {
    STORE.tenants.clear();
    STORE.boundaryAlerts.length = 0;
    STORE.conflicts.length = 0;
    STORE.activeTenant = null;
    STORE.sessionId = `tenant-audit-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    STORE.startedAt = new Date().toISOString();
  }

  // Restore from sessionStorage (if persisted)
  function restore() {
    try {
      const saved = sessionStorage.getItem("windi_tenant_audit");
      if (saved) {
        const data = JSON.parse(saved);
        STORE.activeTenant = data.activeTenant || null;
        STORE.boundaryAlerts = data.boundaryAlerts || [];
        STORE.conflicts = data.conflicts || [];
      }
    } catch (e) { /* silent */ }
  }

  // Persist to sessionStorage
  function persist() {
    try {
      sessionStorage.setItem("windi_tenant_audit", JSON.stringify({
        activeTenant: STORE.activeTenant,
        boundaryAlerts: STORE.boundaryAlerts,
        conflicts: STORE.conflicts
      }));
    } catch (e) { /* silent */ }
  }

  // Auto-restore on load
  restore();

  // Auto-persist on boundary alerts
  const originalSetActiveTenant = setActiveTenant;
  function setActiveTenantWithPersist(tenantId, ctx) {
    const result = originalSetActiveTenant(tenantId, ctx);
    if (!result.ok) persist();
    return result;
  }

  // Expose API
  global.WINDI_TenantAudit = {
    version: "1.0.0",
    setActiveTenant: setActiveTenantWithPersist,
    checkBoundary,
    trackMessage,
    trackReceipt,
    receiptsSummary,
    isolationScore,
    globalSummary,
    reset,
    restore,
    persist,
    _debug: () => STORE
  };

  console.log('[WINDI] TenantAuditCollector v1.0.0 loaded');

})(window);
