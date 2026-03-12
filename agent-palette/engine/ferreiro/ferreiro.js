/**
 * W-FERR-001 — O Ferreiro
 * =======================
 * Agente de saúde autónomo do WINDI.
 *
 * PRINCÍPIO I9: AI cura o conhecido. Human decide o desconhecido.
 *
 * 4 Níveis de Autonomia:
 *   Level 1: Cura imediata (zombi, manifest)
 *   Level 2: Cura com seal (alzheimer, urls, loop)
 *   Level 3: Proposta ao Human (porta morta, nginx)
 *   Level 4: Alerta crítico (ledger morto, index corrompido)
 */

(function() {
  'use strict';

  const VERSION = '1.0.0';

  // Error catalogue loaded from catalogue.json
  let CATALOGUE = null;

  // Autonomy decision tree
  const AUTONOMY = {
    1: { action: 'CURE_IMMEDIATE', label: 'Cura Imediata' },
    2: { action: 'CURE_WITH_SEAL', label: 'Cura com Registo' },
    3: { action: 'PROPOSE_TO_HUMAN', label: 'Proposta ao Human' },
    4: { action: 'CRITICAL_ALERT', label: 'Alerta Crítico' }
  };

  // State
  const state = {
    lastProbe: null,
    lastHeal: null,
    probeInterval: null,
    listeners: [],
    isRunning: false
  };

  /**
   * Load error catalogue
   */
  async function loadCatalogue() {
    if (CATALOGUE) return CATALOGUE;

    try {
      const response = await fetch('/engine/ferreiro/catalogue.json');
      if (response.ok) {
        CATALOGUE = await response.json();
        console.log('[Ferreiro] Catalogue loaded:', CATALOGUE.version);
        return CATALOGUE;
      }
    } catch (error) {
      console.error('[Ferreiro] Failed to load catalogue:', error);
    }

    // Fallback minimal catalogue
    CATALOGUE = {
      version: '0.0.0',
      errors: [],
      services: [],
      manifests: []
    };

    return CATALOGUE;
  }

  /**
   * Get error definition from catalogue
   */
  function getErrorDef(errorId) {
    if (!CATALOGUE) return null;
    return CATALOGUE.errors.find(e => e.id === errorId) || null;
  }

  /**
   * Run all probes
   */
  async function probeAll() {
    console.log('[Ferreiro] Starting full probe...');
    const startTime = Date.now();

    const results = {
      timestamp: new Date().toISOString(),
      services: null,
      manifests: null,
      code: null,
      issues: [],
      score: 0
    };

    // Run probes in parallel
    const probePromises = [];

    // Services probe
    if (window.FerreiroProbServices) {
      probePromises.push(
        window.FerreiroProbServices.probeAllServices()
          .then(r => { results.services = r; })
          .catch(e => { results.services = { error: e.message }; })
      );
    }

    // Manifests probe
    if (window.FerreiroProbeManifests) {
      probePromises.push(
        window.FerreiroProbeManifests.probeAllManifests()
          .then(r => { results.manifests = r; })
          .catch(e => { results.manifests = { error: e.message }; })
      );
    }

    // Code probe
    if (window.FerreiroProbeCode) {
      probePromises.push(
        window.FerreiroProbeCode.probeAllCode()
          .then(r => { results.code = r; })
          .catch(e => { results.code = { error: e.message }; })
      );
    }

    await Promise.all(probePromises);

    // Collect all issues
    if (results.services && results.services.results) {
      results.issues.push(...results.services.results.filter(r => r.status !== 'OK'));
    }
    if (results.manifests && results.manifests.results) {
      results.issues.push(...results.manifests.results.filter(r => r.status !== 'OK'));
    }
    if (results.code && results.code.results) {
      results.issues.push(...results.code.results.filter(r => r.status === 'ISSUE'));
    }

    // Calculate overall score
    const scores = [];
    if (results.services && results.services.score) scores.push(results.services.score);
    if (results.manifests && results.manifests.score) scores.push(results.manifests.score);
    if (results.code && results.code.score) scores.push(results.code.score);

    results.score = scores.length > 0
      ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length)
      : 0;

    results.duration = Date.now() - startTime;

    // Store and notify
    state.lastProbe = results;
    notifyListeners('probe', results);

    console.log('[Ferreiro] Probe complete:', results.score + '% health,', results.issues.length, 'issues');

    return results;
  }

  /**
   * Diagnose issues and determine actions
   */
  async function diagnose(probeResults) {
    await loadCatalogue();

    const diagnosis = {
      timestamp: new Date().toISOString(),
      issues: [],
      actions: {
        immediate: [],    // Level 1
        withSeal: [],     // Level 2
        proposals: [],    // Level 3
        alerts: []        // Level 4
      }
    };

    for (const issue of probeResults.issues) {
      const errorDef = getErrorDef(issue.errorId);

      if (!errorDef) {
        // Unknown error - escalate to human
        diagnosis.actions.proposals.push({
          issue,
          errorId: 'UNKNOWN',
          reason: 'Erro não catalogado',
          action: 'PROPOSE_TO_HUMAN'
        });
        continue;
      }

      const level = errorDef.level;
      const autonomy = AUTONOMY[level];

      const action = {
        issue,
        errorId: issue.errorId,
        level,
        autonomous: errorDef.autonomous,
        action: autonomy.action,
        label: autonomy.label,
        cure: errorDef.cure
      };

      // Sort into action buckets
      switch (level) {
        case 1:
          diagnosis.actions.immediate.push(action);
          break;
        case 2:
          diagnosis.actions.withSeal.push(action);
          break;
        case 3:
          diagnosis.actions.proposals.push(action);
          break;
        case 4:
          diagnosis.actions.alerts.push(action);
          break;
      }

      diagnosis.issues.push(action);
    }

    console.log('[Ferreiro] Diagnosis:', {
      immediate: diagnosis.actions.immediate.length,
      withSeal: diagnosis.actions.withSeal.length,
      proposals: diagnosis.actions.proposals.length,
      alerts: diagnosis.actions.alerts.length
    });

    return diagnosis;
  }

  /**
   * Execute autonomous cures
   */
  async function heal(diagnosis) {
    const healResults = {
      timestamp: new Date().toISOString(),
      cured: [],
      failed: [],
      proposed: [],
      alerted: []
    };

    // Process Level 1: Immediate cures
    for (const action of diagnosis.actions.immediate) {
      try {
        const result = await executeHeal(action);
        if (result.success) {
          healResults.cured.push(result);
        } else {
          healResults.failed.push(result);
        }
      } catch (error) {
        healResults.failed.push({
          ...action,
          error: error.message
        });
      }
    }

    // Process Level 2: Cures with seal
    for (const action of diagnosis.actions.withSeal) {
      try {
        const result = await executeHeal(action);
        if (result.success) {
          healResults.cured.push(result);
          // Would seal to Ledger here
          if (result.seal) {
            await sealToLedger(result);
          }
        } else {
          healResults.failed.push(result);
        }
      } catch (error) {
        healResults.failed.push({
          ...action,
          error: error.message
        });
      }
    }

    // Level 3: Create proposals (no autonomous action)
    for (const action of diagnosis.actions.proposals) {
      healResults.proposed.push({
        ...action,
        proposal: createProposal(action)
      });
    }

    // Level 4: Send alerts (no autonomous action)
    for (const action of diagnosis.actions.alerts) {
      healResults.alerted.push({
        ...action,
        alert: createAlert(action)
      });
    }

    state.lastHeal = healResults;
    notifyListeners('heal', healResults);

    console.log('[Ferreiro] Heal complete:', healResults.cured.length, 'cured,',
      healResults.proposed.length, 'proposed,', healResults.alerted.length, 'alerts');

    return healResults;
  }

  /**
   * Execute specific heal based on error type
   */
  async function executeHeal(action) {
    const healers = {
      'ZOMBI': window.FerreiroHealZombi?.healZombi,
      'ALZHEIMER': window.FerreiroHealAlzheimer?.healAlzheimer,
      'VEIA_MORTA': window.FerreiroHealUrls?.healUrls,
      'LOOP_SESSION': window.FerreiroHealLoop?.healLoop,
      'MANIFEST_INVALIDO': window.FerreiroHealManifest?.healManifest
    };

    const healer = healers[action.errorId];

    if (!healer) {
      return {
        ...action,
        success: false,
        error: 'No healer available for: ' + action.errorId
      };
    }

    return await healer(action.issue.id || action.issue.service, action.issue);
  }

  /**
   * Create proposal for human review
   */
  function createProposal(action) {
    return {
      type: 'PROPOSAL',
      errorId: action.errorId,
      title: action.issue.name || action.errorId,
      description: action.issue.detail || 'Requer decisão humana',
      options: action.cure?.options || ['Investigar', 'Ignorar'],
      timestamp: new Date().toISOString()
    };
  }

  /**
   * Create critical alert
   */
  function createAlert(action) {
    return {
      type: 'CRITICAL_ALERT',
      errorId: action.errorId,
      title: '⚠️ ' + (action.issue.name || action.errorId),
      description: action.issue.detail || 'ALERTA CRÍTICO',
      escalate: action.cure?.escalate || 'Human Dragon',
      timestamp: new Date().toISOString()
    };
  }

  /**
   * Seal result to Forensic Ledger
   */
  async function sealToLedger(healResult) {
    console.log('[Ferreiro] Sealing to Ledger:', healResult.errorId);

    // Would call Ledger API here
    // const response = await fetch('/api/ledger/seal', {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify({
    //     type: 'FERREIRO_HEAL',
    //     errorId: healResult.errorId,
    //     timestamp: new Date().toISOString(),
    //     detail: healResult.detail
    //   })
    // });

    return { sealed: true, simulated: true };
  }

  /**
   * Full probe → diagnose → heal cycle
   */
  async function runCycle() {
    console.log('[Ferreiro] Running full cycle...');

    const probeResults = await probeAll();
    const diagnosis = await diagnose(probeResults);
    const healResults = await heal(diagnosis);

    return {
      probe: probeResults,
      diagnosis,
      heal: healResults
    };
  }

  /**
   * Start continuous monitoring
   */
  function startMonitoring(intervalMs = 60000) {
    if (state.isRunning) {
      console.log('[Ferreiro] Already running');
      return;
    }

    state.isRunning = true;
    console.log('[Ferreiro] Starting monitoring, interval:', intervalMs + 'ms');

    // Initial run
    runCycle();

    // Schedule periodic runs
    state.probeInterval = setInterval(runCycle, intervalMs);
  }

  /**
   * Stop monitoring
   */
  function stopMonitoring() {
    if (state.probeInterval) {
      clearInterval(state.probeInterval);
      state.probeInterval = null;
    }
    state.isRunning = false;
    console.log('[Ferreiro] Monitoring stopped');
  }

  /**
   * Subscribe to events
   */
  function subscribe(callback) {
    state.listeners.push(callback);
    return () => {
      state.listeners = state.listeners.filter(l => l !== callback);
    };
  }

  /**
   * Notify listeners
   */
  function notifyListeners(event, data) {
    for (const listener of state.listeners) {
      try {
        listener(event, data);
      } catch (e) {
        console.error('[Ferreiro] Listener error:', e);
      }
    }
  }

  /**
   * Get current status
   */
  function getStatus() {
    return {
      version: VERSION,
      isRunning: state.isRunning,
      lastProbe: state.lastProbe,
      lastHeal: state.lastHeal,
      catalogue: CATALOGUE ? CATALOGUE.version : null
    };
  }

  // Export
  const Ferreiro = {
    VERSION,
    loadCatalogue,
    probeAll,
    diagnose,
    heal,
    runCycle,
    startMonitoring,
    stopMonitoring,
    subscribe,
    getStatus,
    getErrorDef
  };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = Ferreiro;
  }

  if (typeof window !== 'undefined') {
    window.Ferreiro = Ferreiro;
  }

})();
