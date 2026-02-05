/**
 * WINDI Surface Guard (WSG) - DOM Sentinel
 * Vigilância de Mutações em Runtime - EVENT-DRIVEN
 * 
 * v0.1.1 - Otimizado: sem polling fixo, orientado a eventos
 * 
 * "Uma vez que o asset é validado, o perigo passa a ser a manipulação in-page."
 * 
 * @version 0.1.1
 * @author Three Dragons Protocol
 */

(function() {
  'use strict';

  const WSG_SENTINEL_VERSION = '0.1.1';

  // ═══════════════════════════════════════════════════════════════
  // CONFIGURATION
  // ═══════════════════════════════════════════════════════════════

  const SENTINEL_CONFIG = {
    // Seletores de elementos protegidos
    protectedSelectors: [
      '[data-wsg-protect="decision"]',
      '[data-wsg-protect="value"]',
      '[data-wsg-protect="status"]',
      '[data-wsg-protect="signature"]',
      '[data-wsg-protect="governance"]',
      '.sge-risk-indicator',
      '.governance-action-btn',
      '.virtue-badge'
    ],
    
    // Propriedades CSS perigosas
    dangerousProperties: [
      'display', 'visibility', 'opacity', 'z-index',
      'pointer-events', 'position', 'transform', 'clip', 'clip-path'
    ],
    
    // Eventos que disparam overlay scan
    overlayScanTriggers: [
      'focusin',    // Foco em elemento protegido
      'mouseenter', // Hover em elemento protegido
      'click'       // Clique em elemento protegido
    ],
    
    // Debounce para overlay scan (ms)
    overlayScanDebounce: 100,
    
    // Tamanho mínimo de overlay suspeito
    minOverlaySize: 50
  };

  // ═══════════════════════════════════════════════════════════════
  // STATE
  // ═══════════════════════════════════════════════════════════════

  const state = {
    mainObserver: null,
    newElementObserver: null,
    shadowBackups: new WeakMap(),
    initialized: false,
    violations: [],
    pendingOverlayScan: null
  };

  // ═══════════════════════════════════════════════════════════════
  // SERVICE WORKER COMMUNICATION
  // ═══════════════════════════════════════════════════════════════

  function reportToServiceWorker(violation) {
    if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
      const channel = new MessageChannel();
      navigator.serviceWorker.controller.postMessage({
        type: 'WSG_REPORT_DOM_VIOLATION',
        payload: violation
      }, [channel.port2]);
    }
    
    console.warn('[WSG-Sentinel] 🚨 VIOLATION:', violation);
    state.violations.push({ ...violation, timestamp: new Date().toISOString() });
  }

  // ═══════════════════════════════════════════════════════════════
  // SHADOW BACKUP SYSTEM
  // ═══════════════════════════════════════════════════════════════

  function createShadowBackup(element) {
    if (state.shadowBackups.has(element)) return;
    
    const computed = window.getComputedStyle(element);
    const backup = {
      innerHTML: element.innerHTML,
      textContent: element.textContent,
      attributes: {},
      computedStyle: {},
      boundingRect: element.getBoundingClientRect().toJSON()
    };
    
    for (const attr of element.attributes) {
      backup.attributes[attr.name] = attr.value;
    }
    
    for (const prop of SENTINEL_CONFIG.dangerousProperties) {
      backup.computedStyle[prop] = computed.getPropertyValue(prop);
    }
    
    state.shadowBackups.set(element, backup);
  }

  function restoreFromBackup(element) {
    const backup = state.shadowBackups.get(element);
    if (!backup) return false;
    
    element.innerHTML = backup.innerHTML;
    
    for (const [name, value] of Object.entries(backup.attributes)) {
      if (name !== 'data-wsg-restoring') {
        element.setAttribute(name, value);
      }
    }
    
    for (const [prop, value] of Object.entries(backup.computedStyle)) {
      element.style.setProperty(prop, value);
    }
    
    return true;
  }

  // ═══════════════════════════════════════════════════════════════
  // ELEMENT DETECTION
  // ═══════════════════════════════════════════════════════════════

  function isProtectedElement(element) {
    if (!element || element.nodeType !== Node.ELEMENT_NODE) return false;
    
    for (const selector of SENTINEL_CONFIG.protectedSelectors) {
      if (element.matches?.(selector)) return true;
      if (element.closest?.(selector)) return true;
    }
    
    return false;
  }

  function getAllProtectedElements() {
    return document.querySelectorAll(SENTINEL_CONFIG.protectedSelectors.join(', '));
  }

  function getElementSelector(element) {
    if (element.id) return `#${element.id}`;
    
    let path = [];
    let current = element;
    
    while (current && current !== document.body) {
      let selector = current.tagName.toLowerCase();
      if (current.className && typeof current.className === 'string') {
        selector += '.' + current.className.trim().split(/\s+/).slice(0, 2).join('.');
      }
      path.unshift(selector);
      current = current.parentElement;
    }
    
    return path.slice(-3).join(' > '); // Últimos 3 níveis
  }

  // ═══════════════════════════════════════════════════════════════
  // MUTATION AUTHORIZATION
  // ═══════════════════════════════════════════════════════════════

  const WHITELISTED_CLASSES = new Set([
    'loading', 'loaded', 'active', 'inactive', 'hover', 'focus', 
    'disabled', 'enabled', 'open', 'closed', 'expanded', 'collapsed',
    'visible', 'hidden', 'selected', 'highlighted'
  ]);

  function isMutationAuthorized(mutation, element) {
    // Se WSG está restaurando, permitir
    if (element.dataset.wsgRestoring === 'true') return true;
    
    // Whitelist de classes de estado
    if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
      const oldClasses = new Set((mutation.oldValue || '').split(/\s+/).filter(Boolean));
      const newClasses = new Set(element.className.split(/\s+/).filter(Boolean));
      
      // Classes adicionadas
      const added = [...newClasses].filter(c => !oldClasses.has(c));
      // Classes removidas
      const removed = [...oldClasses].filter(c => !newClasses.has(c));
      
      // Se todas as mudanças são whitelisted, permitir
      const allWhitelisted = 
        added.every(c => WHITELISTED_CLASSES.has(c)) &&
        removed.every(c => WHITELISTED_CLASSES.has(c));
      
      if (allWhitelisted) return true;
    }
    
    // Whitelist de atributos de estado
    if (mutation.type === 'attributes') {
      const safeAttributes = new Set(['aria-expanded', 'aria-selected', 'aria-hidden', 'tabindex']);
      if (safeAttributes.has(mutation.attributeName)) return true;
    }
    
    return false;
  }

  // ═══════════════════════════════════════════════════════════════
  // MUTATION HANDLER
  // ═══════════════════════════════════════════════════════════════

  function handleMutations(mutations) {
    for (const mutation of mutations) {
      const element = mutation.target;
      
      if (!isProtectedElement(element)) continue;
      if (isMutationAuthorized(mutation, element)) continue;
      
      // VIOLAÇÃO
      const violation = {
        type: 'DOM_MUTATION',
        mutation_type: mutation.type,
        element_selector: getElementSelector(element),
        attribute_name: mutation.attributeName || null,
        old_value: truncate(mutation.oldValue, 100),
        new_value: truncate(getNewValue(mutation, element), 100),
        protection_level: element.dataset.wsgProtect || 'unknown'
      };
      
      reportToServiceWorker(violation);
      
      // Restaurar
      element.dataset.wsgRestoring = 'true';
      const restored = restoreFromBackup(element);
      delete element.dataset.wsgRestoring;
      
      if (restored) {
        console.log('[WSG-Sentinel] ✓ Element restored');
        showIntegrityAlert(element);
      }
    }
  }

  function getNewValue(mutation, element) {
    switch (mutation.type) {
      case 'attributes':
        return element.getAttribute(mutation.attributeName);
      case 'characterData':
        return element.textContent;
      case 'childList':
        return `+${mutation.addedNodes.length}/-${mutation.removedNodes.length} nodes`;
      default:
        return null;
    }
  }

  function truncate(str, maxLen) {
    if (!str) return str;
    return str.length > maxLen ? str.substring(0, maxLen) + '...' : str;
  }

  // ═══════════════════════════════════════════════════════════════
  // OVERLAY SHIELD (Event-Driven)
  // ═══════════════════════════════════════════════════════════════

  /**
   * Escaneia por overlays quando há evento em elemento protegido
   */
  function scanForOverlays(targetElement) {
    if (!targetElement) return;
    
    const rect = targetElement.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    
    // Elementos no ponto central
    const elementsAtPoint = document.elementsFromPoint(centerX, centerY);
    
    for (const element of elementsAtPoint) {
      // Pular o próprio elemento e ancestrais
      if (element === targetElement || 
          targetElement.contains(element) || 
          element.contains(targetElement)) {
        continue;
      }
      
      // Verificar características de overlay malicioso
      const style = window.getComputedStyle(element);
      const isPositioned = style.position === 'fixed' || style.position === 'absolute';
      const isTransparent = parseFloat(style.opacity) < 0.15;
      const isSized = element.offsetWidth >= SENTINEL_CONFIG.minOverlaySize &&
                      element.offsetHeight >= SENTINEL_CONFIG.minOverlaySize;
      const hasLowPointerEvents = style.pointerEvents === 'none';
      
      // Overlay suspeito: posicionado + transparente + tamanho significativo
      if (isPositioned && isTransparent && isSized && !hasLowPointerEvents) {
        const violation = {
          type: 'OVERLAY_ATTACK',
          overlay_element: getElementSelector(element),
          protected_element: getElementSelector(targetElement),
          overlay_opacity: style.opacity,
          overlay_z_index: style.zIndex,
          overlay_position: style.position
        };
        
        reportToServiceWorker(violation);
        
        // Remover overlay
        element.remove();
        console.warn('[WSG-Sentinel] 🛡️ Malicious overlay removed');
        
        showOverlayAlert(targetElement);
      }
    }
  }

  /**
   * Handler para eventos em elementos protegidos (debounced)
   */
  function handleProtectedEvent(event) {
    if (!event.target || !event.target.closest) return;
    const target = event.target.closest(SENTINEL_CONFIG.protectedSelectors.join(', '));
    if (!target) return;
    
    // Debounce
    if (state.pendingOverlayScan) {
      clearTimeout(state.pendingOverlayScan);
    }
    
    state.pendingOverlayScan = setTimeout(() => {
      scanForOverlays(target);
      state.pendingOverlayScan = null;
    }, SENTINEL_CONFIG.overlayScanDebounce);
  }

  // ═══════════════════════════════════════════════════════════════
  // MUTATION OBSERVER PARA NOVOS OVERLAYS
  // ═══════════════════════════════════════════════════════════════

  /**
   * Detecta quando novos elementos position:fixed/absolute são adicionados
   */
  function handleNewElements(mutations) {
    for (const mutation of mutations) {
      for (const node of mutation.addedNodes) {
        if (node.nodeType !== Node.ELEMENT_NODE) continue;
        
        // Verificar se é potencial overlay
        const style = window.getComputedStyle(node);
        if (style.position === 'fixed' || style.position === 'absolute') {
          if (parseFloat(style.opacity) < 0.15) {
            // Elemento suspeito adicionado - verificar se cobre algum protegido
            const protectedElements = getAllProtectedElements();
            for (const protectedEl of protectedElements) {
              const protectedRect = protectedEl.getBoundingClientRect();
              const nodeRect = node.getBoundingClientRect();
              
              // Verificar interseção
              if (rectsIntersect(protectedRect, nodeRect)) {
                scanForOverlays(protectedEl);
                break;
              }
            }
          }
        }
        
        // Se o novo elemento é protegido, fazer backup
        if (isProtectedElement(node)) {
          createShadowBackup(node);
        }
        
        // Verificar filhos protegidos
        const protectedChildren = node.querySelectorAll?.(
          SENTINEL_CONFIG.protectedSelectors.join(', ')
        );
        if (protectedChildren) {
          protectedChildren.forEach(createShadowBackup);
        }
      }
    }
  }

  function rectsIntersect(r1, r2) {
    return !(r2.left > r1.right || 
             r2.right < r1.left || 
             r2.top > r1.bottom ||
             r2.bottom < r1.top);
  }

  // ═══════════════════════════════════════════════════════════════
  // VISUAL ALERTS
  // ═══════════════════════════════════════════════════════════════

  function showIntegrityAlert(element) {
    showAlert(element, '🛡️ Integridade restaurada', '#ff6b6b');
  }

  function showOverlayAlert(element) {
    showAlert(element, '🛡️ Overlay bloqueado', '#ff9f43');
  }

  function showAlert(element, message, color) {
    const rect = element.getBoundingClientRect();
    
    const alert = document.createElement('div');
    alert.className = 'wsg-integrity-alert';
    alert.textContent = message;
    
    alert.style.cssText = `
      position: fixed;
      top: ${Math.max(10, rect.top - 35)}px;
      left: ${rect.left}px;
      background: ${color};
      color: white;
      padding: 6px 12px;
      border-radius: 6px;
      font-size: 12px;
      font-family: system-ui, sans-serif;
      z-index: 2147483647;
      box-shadow: 0 2px 10px rgba(0,0,0,0.3);
      animation: wsgAlertFade 2.5s forwards;
      pointer-events: none;
    `;
    
    document.body.appendChild(alert);
    setTimeout(() => alert.remove(), 2500);
  }

  function injectStyles() {
    if (document.getElementById('wsg-sentinel-styles')) return;
    
    const style = document.createElement('style');
    style.id = 'wsg-sentinel-styles';
    style.textContent = `
      @keyframes wsgAlertFade {
        0% { opacity: 0; transform: translateY(-10px); }
        10% { opacity: 1; transform: translateY(0); }
        80% { opacity: 1; }
        100% { opacity: 0; transform: translateY(-10px); }
      }
      
      [data-wsg-protect] {
        transition: box-shadow 0.2s ease;
      }
      
      [data-wsg-protect]:focus-visible {
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.4);
      }
    `;
    document.head.appendChild(style);
  }

  // ═══════════════════════════════════════════════════════════════
  // INITIALIZATION
  // ═══════════════════════════════════════════════════════════════

  function initialize() {
    if (state.initialized) return;
    
    console.log(`[WSG-Sentinel] 🔍 Initializing DOM Sentinel v${WSG_SENTINEL_VERSION}`);
    
    injectStyles();
    
    // Backup de elementos protegidos existentes
    const protectedElements = getAllProtectedElements();
    protectedElements.forEach(createShadowBackup);
    console.log(`[WSG-Sentinel] Protecting ${protectedElements.length} elements`);
    
    // Observer principal para mutações em elementos protegidos
    state.mainObserver = new MutationObserver(handleMutations);
    state.mainObserver.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeOldValue: true,
      characterData: true,
      characterDataOldValue: true
    });
    
    // Observer para novos elementos (overlays e protegidos)
    state.newElementObserver = new MutationObserver(handleNewElements);
    state.newElementObserver.observe(document.body, {
      childList: true,
      subtree: true
    });
    
    // Event listeners para overlay scan (event-driven, não polling)
    for (const eventType of SENTINEL_CONFIG.overlayScanTriggers) {
      document.addEventListener(eventType, handleProtectedEvent, { 
        capture: true, 
        passive: true 
      });
    }
    
    state.initialized = true;
    console.log('[WSG-Sentinel] ✓ DOM Sentinel active (event-driven)');
  }

  function shutdown() {
    if (state.mainObserver) state.mainObserver.disconnect();
    if (state.newElementObserver) state.newElementObserver.disconnect();
    
    for (const eventType of SENTINEL_CONFIG.overlayScanTriggers) {
      document.removeEventListener(eventType, handleProtectedEvent, { capture: true });
    }
    
    if (state.pendingOverlayScan) {
      clearTimeout(state.pendingOverlayScan);
    }
    
    state.initialized = false;
    console.log('[WSG-Sentinel] Shutdown complete');
  }

  // ═══════════════════════════════════════════════════════════════
  // PUBLIC API
  // ═══════════════════════════════════════════════════════════════

  window.WSGSentinel = {
    version: WSG_SENTINEL_VERSION,
    initialize,
    shutdown,
    
    protect(element, level = 'standard') {
      element.dataset.wsgProtect = level;
      createShadowBackup(element);
    },
    
    unprotect(element) {
      delete element.dataset.wsgProtect;
      state.shadowBackups.delete(element);
    },
    
    getViolations() {
      return [...state.violations];
    },
    
    getStatus() {
      return {
        version: WSG_SENTINEL_VERSION,
        initialized: state.initialized,
        protectedCount: getAllProtectedElements().length,
        violationCount: state.violations.length,
        mode: 'event-driven'
      };
    },
    
    // Manual overlay scan
    scanOverlays() {
      getAllProtectedElements().forEach(scanForOverlays);
    }
  };

  // ═══════════════════════════════════════════════════════════════
  // AUTO-INIT
  // ═══════════════════════════════════════════════════════════════

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initialize);
  } else {
    initialize();
  }

})();
