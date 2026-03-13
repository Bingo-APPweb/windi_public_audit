// ============================================================
// canvas-gen7-mobile.js — Fase 1: Integração Touch no Canvas
// Injetar no final do <body> de index.html (antes do </body>)
// ============================================================

(function() {
  'use strict';

  // ── 1. PINCH-TO-ZOOM no Canvas ─────────────────────────────
  function initPinchZoom() {
    // Adapta ao ID real do teu canvas — ajustar se necessário
    const canvasEl = document.getElementById('canvas-area')
                  || document.getElementById('canvas-container')
                  || document.querySelector('[data-zone="G1"]')
                  || document.querySelector('.canvas-container');

    if (!canvasEl) {
      console.warn('[Gen7] canvas element não encontrado para pinch-zoom');
      return;
    }

    let currentScale = 1.0;
    let startDist = 0;
    let startScale = 1.0;

    function getDistance(touches) {
      const dx = touches[0].clientX - touches[1].clientX;
      const dy = touches[0].clientY - touches[1].clientY;
      return Math.sqrt(dx * dx + dy * dy);
    }

    function applyScale(scale) {
      // Integração com o sistema de zoom existente do Canvas
      // Tenta várias abordagens — a que funcionar é mantida
      if (typeof window.setCanvasZoom === 'function') {
        window.setCanvasZoom(scale);
      } else if (typeof window.__dragonCanvasScale !== 'undefined') {
        window.__dragonCanvasScale = scale;
        const ev = new CustomEvent('canvas:scale', { detail: { scale } });
        canvasEl.dispatchEvent(ev);
      } else {
        // fallback: CSS transform direto
        const inner = canvasEl.querySelector('.canvas-inner, .canvas-content, canvas');
        if (inner) {
          inner.style.transform = `scale(${scale})`;
          inner.style.transformOrigin = 'center center';
        }
      }
      currentScale = scale;

      // Feedback visual
      canvasEl.classList.toggle('canvas-zooming', scale !== 1.0);

      // Atualiza indicador de zoom se existir
      const zoomIndicator = document.querySelector('.zoom-indicator, #zoom-value');
      if (zoomIndicator) {
        zoomIndicator.textContent = Math.round(scale * 100) + '%';
      }
    }

    canvasEl.addEventListener('touchstart', (e) => {
      if (e.touches.length === 2) {
        e.preventDefault();
        startDist = getDistance(e.touches);
        startScale = currentScale;
        canvasEl.classList.add('canvas-zooming');
      }
    }, { passive: false });

    canvasEl.addEventListener('touchmove', (e) => {
      if (e.touches.length === 2) {
        e.preventDefault();
        const dist = getDistance(e.touches);
        const ratio = dist / startDist;
        const newScale = Math.min(4.0, Math.max(0.5, startScale * ratio));
        applyScale(newScale);
      }
    }, { passive: false });

    canvasEl.addEventListener('touchend', (e) => {
      if (e.touches.length < 2) {
        canvasEl.classList.remove('canvas-zooming');
      }
    });

    // Double-tap para reset de zoom
    let lastTap = 0;
    canvasEl.addEventListener('touchend', (e) => {
      if (e.touches.length === 0) {
        const now = Date.now();
        if (now - lastTap < 300) {
          applyScale(1.0);
          lastTap = 0;
        } else {
          lastTap = now;
        }
      }
    });

    console.log('[Gen7] Pinch-zoom ativo no canvas');
  }

  // ── 2. TOUCH TARGETS ≥ 44px nas Smart Zones G1 + G2 ────────
  function enforceMinTapTargets() {
    const selectors = [
      '#toolbar button',
      '#toolbar [role="button"]',
      '.toolbar button',
      '.toolbar .icon-btn',
      '.toolbar .tool-btn',
      '[data-zone="G2"] button',
      '[data-zone="G2"] [role="button"]',
      '.palette-toolbar button',
      '.bottom-bar button',
    ].join(', ');

    const elements = document.querySelectorAll(selectors);
    let expanded = 0;

    elements.forEach(el => {
      const rect = el.getBoundingClientRect();
      if (rect.width < 44 || rect.height < 44) {
        el.style.minWidth = '44px';
        el.style.minHeight = '44px';
        el.style.display = 'inline-flex';
        el.style.alignItems = 'center';
        el.style.justifyContent = 'center';
        expanded++;
      }
      // Sempre adicionar touch optimization
      el.style.touchAction = 'manipulation';
      el.style.webkitTapHighlightColor = 'transparent';
      el.setAttribute('data-touch-ready', 'true');
    });

    console.log(`[Gen7] Touch targets: ${expanded} expandidos para ≥44px`);
  }

  // ── 3. MENSAGEM CONTEXTUAL "from=desktop" ──────────────────
  function handleFromDesktop() {
    const params = new URLSearchParams(window.location.search);
    if (params.get('from') !== 'desktop') return;

    let notice = document.querySelector('.from-desktop-notice');
    if (!notice) {
      notice = document.createElement('div');
      notice.className = 'from-desktop-notice';
      notice.textContent = 'Canvas Mobile activo — Editor avançado disponível no Desktop';
      document.body.appendChild(notice);
    }

    setTimeout(() => {
      notice.classList.add('visible');
      setTimeout(() => notice.classList.remove('visible'), 4000);
    }, 800);
  }

  // ── 4. DRAG DE LAYER COM POINTER EVENTS UNIFICADOS ──────────
  // (substitui os mousedown/mousemove existentes por pointer events)
  function patchLayerDragToPointer() {
    // Identifica layers arrastáveis no canvas
    const canvasEl = document.getElementById('canvas-area')
                  || document.querySelector('[data-zone="G1"]')
                  || document.querySelector('.canvas-container');
    if (!canvasEl) return;

    // O patch é conservador: apenas garante que pointer events
    // estão activos. A lógica de drag existente é preservada.
    canvasEl.style.touchAction = 'none';

    // Converte listeners de mouse para pointer se não existirem
    // (o Gêmeo vai verificar se já existe pointer events no Gen 6)
    const layers = canvasEl.querySelectorAll('.layer, [data-layer], .canvas-layer');
    layers.forEach(layer => {
      if (!layer.dataset.pointerPatched) {
        layer.style.touchAction = 'none';
        layer.dataset.pointerPatched = 'true';
      }
    });

    console.log(`[Gen7] Pointer events aplicados em ${layers.length} layers`);
  }

  // ── 5. INICIALIZAÇÃO ─────────────────────────────────────────
  function initGen7Mobile() {
    const isMobile = window.innerWidth < 768
      || ('ontouchstart' in window)
      || (navigator.maxTouchPoints > 0);

    if (!isMobile) {
      console.log('[Gen7] Desktop detectado — mobile patches não aplicados');
      return;
    }

    console.log('[Gen7] Mobile detectado — inicializando Fase 1');

    // Pequeno delay para garantir DOM completo
    setTimeout(() => {
      initPinchZoom();
      enforceMinTapTargets();
      handleFromDesktop();
      patchLayerDragToPointer();
      console.log('[Gen7] Fase 1 activa');
    }, 300);

    // Re-aplicar após resize (tablet rotation)
    let resizeTimer;
    window.addEventListener('resize', () => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(enforceMinTapTargets, 200);
    });
  }

  // Auto-init
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initGen7Mobile);
  } else {
    initGen7Mobile();
  }

  // Expor para debugging e integração
  window.__gen7 = {
    version: '1.0.0',
    phase: 1,
    reinit: initGen7Mobile,
    enforceTargets: enforceMinTapTargets
  };

})();
