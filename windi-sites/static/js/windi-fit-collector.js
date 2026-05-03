/**
 * W-FIT-001 Collector — Semantic Event Collection
 * ================================================
 * §5.2 Frontend Collector for Adaptive Maturity System
 *
 * Principles:
 *   1. Semantic events only (never raw keystrokes, mouse moves, or content)
 *   2. DID-gated (no DID = silent no-op)
 *   3. Buffer + flush (batch events to reduce network overhead)
 *   4. Fail-silent (never blocks UX, never shows errors)
 *   5. Self-disable on consent withdrawal
 *
 * Constitutional basis:
 *   - I2: User can see their FIT at /fit/me
 *   - I8: Data minimization (behavior, never content)
 *   - "Measure operational behavior, never human content"
 *
 * Liga IA+H · Kempten, Bavaria · 2026
 * "AI processes. Human decides. WINDI guarantees."
 */

(function(window) {
  'use strict';

  // ═══════════════════════════════════════════════════════════════════════════
  // CONFIGURATION
  // ═══════════════════════════════════════════════════════════════════════════

  const CONFIG = {
    endpoint: '/fit/collect/batch',
    batchSize: 15,           // Flush when buffer reaches this size
    flushInterval: 10000,    // Flush every 10 seconds
    heartbeatInterval: 30000, // Heartbeat every 30 seconds (presence)
    maxRetries: 2,
    debug: false
  };

  // ═══════════════════════════════════════════════════════════════════════════
  // STATE
  // ═══════════════════════════════════════════════════════════════════════════

  let eventBuffer = [];
  let sessionId = null;
  let currentDid = null;
  let currentLayer = 'LIVE';
  let currentSiteId = null;
  let sessionStartTime = null;
  let lastActivityTime = null;
  let flushTimer = null;
  let heartbeatTimer = null;
  let isEnabled = true;

  // ═══════════════════════════════════════════════════════════════════════════
  // INITIALIZATION
  // ═══════════════════════════════════════════════════════════════════════════

  function init() {
    // Generate session ID
    sessionId = crypto.randomUUID ? crypto.randomUUID() : generateUUID();
    sessionStartTime = Date.now();
    lastActivityTime = Date.now();

    // Try to get DID from various sources
    currentDid = getDid();

    // Start timers
    flushTimer = setInterval(flush, CONFIG.flushInterval);
    heartbeatTimer = setInterval(sendHeartbeat, CONFIG.heartbeatInterval);

    // Track session start
    if (currentDid) {
      pushEvent('session.started', {});
    }

    // Cleanup on page unload
    window.addEventListener('beforeunload', function() {
      flush(true); // Sync flush on unload
    });

    log('FIT Collector initialized', { sessionId, did: currentDid });
  }

  function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      var r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  }

  function getDid() {
    // Check multiple sources for DID
    // 1. localStorage (WindiDID)
    try {
      const stored = localStorage.getItem('windi_did');
      if (stored) return stored;
    } catch (e) {}

    // 2. sessionStorage
    try {
      const session = sessionStorage.getItem('windi_desktop_wallet');
      if (session) {
        const parsed = JSON.parse(session);
        if (parsed.did) return parsed.did;
      }
    } catch (e) {}

    // 3. Meta tag
    const metaDid = document.querySelector('meta[name="windi-did"]');
    if (metaDid) return metaDid.content;

    // 4. Window global
    if (window.WINDI_DID) return window.WINDI_DID;

    return null;
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // EVENT COLLECTION
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Push a semantic event to the buffer.
   *
   * ALLOWED EVENTS (semantic, operational):
   *   session.started, session.heartbeat
   *   template.selected
   *   block.added, block.removed
   *   verifier.assigned
   *   document.draft.saved
   *   document.published
   *   error.shown, error.recovered
   *   help.opened, help.closed
   *   verification.url.shared
   *   preview.opened
   *   publish.attempt, publish.success, publish.failed
   *
   * FORBIDDEN (never collect):
   *   mousemove, keypress, clipboard, field text, document body
   */
  function pushEvent(eventType, context, metrics) {
    // DID-gated: no DID = no-op
    if (!currentDid) {
      currentDid = getDid(); // Try again
      if (!currentDid) {
        log('No DID, skipping event', { eventType });
        return;
      }
    }

    // Disabled check
    if (!isEnabled) {
      log('Collector disabled, skipping event', { eventType });
      return;
    }

    lastActivityTime = Date.now();

    const event = {
      session_id: sessionId,
      layer: currentLayer,
      event_type: mapEventType(eventType),
      metrics: {
        duration_ms: metrics?.duration_ms || 0,
        hesitation_ms: metrics?.hesitation_ms || 0,
        input_changes: metrics?.input_changes || 0,
        error_count: metrics?.error_count || 0
      },
      context: {
        component: context?.component || null,
        complexity: context?.complexity || 'low',
        template_id: context?.template_id || null
      },
      metadata: {
        site_id: currentSiteId,
        original_event: eventType,
        timestamp: new Date().toISOString()
      }
    };

    eventBuffer.push(event);
    log('Event buffered', { eventType, bufferSize: eventBuffer.length });

    // Auto-flush if buffer is full
    if (eventBuffer.length >= CONFIG.batchSize) {
      flush();
    }
  }

  /**
   * Map semantic event names to FIT event types.
   */
  function mapEventType(eventName) {
    const mapping = {
      'session.started': 'view',
      'session.heartbeat': 'view',
      'template.selected': 'decision',
      'block.added': 'edit',
      'block.removed': 'edit',
      'verifier.assigned': 'decision',
      'document.draft.saved': 'submit',
      'document.published': 'submit',
      'error.shown': 'error',
      'error.recovered': 'recovery',
      'help.opened': 'view',
      'help.closed': 'view',
      'verification.url.shared': 'submit',
      'preview.opened': 'view',
      'publish.attempt': 'decision',
      'publish.success': 'submit',
      'publish.failed': 'error'
    };
    return mapping[eventName] || 'view';
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // FLUSH (send buffered events to server)
  // ═══════════════════════════════════════════════════════════════════════════

  function flush(sync = false) {
    if (eventBuffer.length === 0) return;
    if (!currentDid) return;

    const batch = [...eventBuffer];
    eventBuffer = [];

    const payload = JSON.stringify({ events: batch });

    if (sync && navigator.sendBeacon) {
      // Sync flush on page unload using sendBeacon
      navigator.sendBeacon(CONFIG.endpoint, payload);
      log('Flushed via sendBeacon', { count: batch.length });
      return;
    }

    // Async fetch
    fetch(CONFIG.endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-WINDI-DID': currentDid
      },
      body: payload,
      keepalive: true
    })
    .then(function(response) {
      if (!response.ok) {
        throw new Error('Flush failed: ' + response.status);
      }
      return response.json();
    })
    .then(function(data) {
      log('Flushed successfully', { collected: data.collected });
    })
    .catch(function(error) {
      // Fail-silent: put events back in buffer for retry
      log('Flush failed, re-buffering', { error: error.message });
      eventBuffer = batch.concat(eventBuffer).slice(0, CONFIG.batchSize * 2);
    });
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // HEARTBEAT (presence tracking)
  // ═══════════════════════════════════════════════════════════════════════════

  function sendHeartbeat() {
    if (!currentDid) return;
    if (!isEnabled) return;

    // Only send heartbeat if user was active recently (within 2 minutes)
    const timeSinceActivity = Date.now() - lastActivityTime;
    if (timeSinceActivity > 120000) {
      log('User inactive, skipping heartbeat');
      return;
    }

    pushEvent('session.heartbeat', {
      component: 'heartbeat'
    }, {
      duration_ms: Date.now() - sessionStartTime
    });
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // PUBLIC API
  // ═══════════════════════════════════════════════════════════════════════════

  const WindiFIT = {
    /**
     * Track a semantic event.
     * @param {string} eventType - One of the allowed event types
     * @param {object} context - { component, complexity, template_id }
     * @param {object} metrics - { duration_ms, input_changes, error_count }
     */
    track: function(eventType, context, metrics) {
      pushEvent(eventType, context, metrics);
    },

    /**
     * Set current layer (LIVE, INTERACTIVE, GUIDED, BUILDER).
     * Called by W-SITES UI based on user state.
     */
    setLayer: function(layer) {
      if (['LIVE', 'INTERACTIVE', 'GUIDED', 'BUILDER'].includes(layer)) {
        currentLayer = layer;
        log('Layer set', { layer });
      }
    },

    /**
     * Set current site ID for context.
     */
    setSiteId: function(siteId) {
      currentSiteId = siteId;
      log('Site ID set', { siteId });
    },

    /**
     * Update DID (e.g., after login).
     */
    setDid: function(did) {
      currentDid = did;
      log('DID set', { did });
    },

    /**
     * Disable collection (consent withdrawal).
     */
    disable: function() {
      isEnabled = false;
      eventBuffer = [];
      if (flushTimer) clearInterval(flushTimer);
      if (heartbeatTimer) clearInterval(heartbeatTimer);
      log('Collector disabled');
    },

    /**
     * Re-enable collection.
     */
    enable: function() {
      isEnabled = true;
      flushTimer = setInterval(flush, CONFIG.flushInterval);
      heartbeatTimer = setInterval(sendHeartbeat, CONFIG.heartbeatInterval);
      log('Collector enabled');
    },

    /**
     * Force flush (e.g., before navigation).
     */
    flush: function() {
      flush();
    },

    /**
     * Get current state (for debugging).
     */
    getState: function() {
      return {
        sessionId,
        did: currentDid,
        layer: currentLayer,
        siteId: currentSiteId,
        bufferSize: eventBuffer.length,
        enabled: isEnabled
      };
    }
  };

  // ═══════════════════════════════════════════════════════════════════════════
  // AUTOMATIC EVENT BINDING (optional, can be disabled)
  // ═══════════════════════════════════════════════════════════════════════════

  function bindAutomaticEvents() {
    // Track help panel open/close
    document.addEventListener('click', function(e) {
      const helpBtn = e.target.closest('[data-fit-help]');
      if (helpBtn) {
        const action = helpBtn.dataset.fitHelp;
        if (action === 'open') {
          WindiFIT.track('help.opened', { component: 'help_panel' });
        } else if (action === 'close') {
          WindiFIT.track('help.closed', { component: 'help_panel' });
        }
      }
    });

    // Track publish button clicks
    document.addEventListener('click', function(e) {
      const publishBtn = e.target.closest('[data-fit-publish]');
      if (publishBtn) {
        WindiFIT.track('publish.attempt', {
          component: 'publish_button',
          complexity: 'high'
        });
      }
    });
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // DEBUG LOGGING
  // ═══════════════════════════════════════════════════════════════════════════

  function log(message, data) {
    if (CONFIG.debug) {
      console.log('[FIT]', message, data || '');
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // EXPOSE & INITIALIZE
  // ═══════════════════════════════════════════════════════════════════════════

  // Expose to global scope
  window.WindiFIT = WindiFIT;

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      init();
      bindAutomaticEvents();
    });
  } else {
    init();
    bindAutomaticEvents();
  }

})(window);
