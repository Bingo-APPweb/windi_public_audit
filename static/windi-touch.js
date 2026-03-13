// ============================================================
// windi-touch.js — WINDI Touch Engine v1.0
// Canvas Gen 7 — Fase 1: Fundação Touch
// Path destino: /opt/windi/static/windi-touch.js
// ============================================================

const WindiTouch = {

  _initialized: false,
  _isTouch: false,

  // ── Inicialização ─────────────────────────────────────────
  init() {
    if (this._initialized) return;
    this._isTouch = this.detectTouch();
    if (this._isTouch) {
      document.documentElement.classList.add('windi-touch');
      document.documentElement.classList.remove('windi-mouse');
    } else {
      document.documentElement.classList.add('windi-mouse');
    }
    this._initialized = true;
    console.log('[WindiTouch] v1.0 init —', this._isTouch ? 'TOUCH' : 'MOUSE');
  },

  // ── Detecção de dispositivo touch ────────────────────────
  detectTouch() {
    return ('ontouchstart' in window)
        || (navigator.maxTouchPoints > 0)
        || (navigator.msMaxTouchPoints > 0);
  },

  isTouch() {
    return this._isTouch;
  },

  // ── Normaliza pointer events (mouse + touch + pen) ───────
  normalizePointer(e) {
    if (e.touches && e.touches.length > 0) {
      return {
        x: e.touches[0].clientX,
        y: e.touches[0].clientY,
        pageX: e.touches[0].pageX,
        pageY: e.touches[0].pageY,
        pressure: e.touches[0].force || 0,
        type: 'touch',
        raw: e
      };
    }
    if (e.changedTouches && e.changedTouches.length > 0) {
      return {
        x: e.changedTouches[0].clientX,
        y: e.changedTouches[0].clientY,
        pageX: e.changedTouches[0].pageX,
        pageY: e.changedTouches[0].pageY,
        pressure: e.changedTouches[0].force || 0,
        type: 'touch-end',
        raw: e
      };
    }
    return {
      x: e.clientX,
      y: e.clientY,
      pageX: e.pageX,
      pageY: e.pageY,
      pressure: e.pressure || 0,
      type: 'mouse',
      raw: e
    };
  },

  // ── Detecção de gesto ─────────────────────────────────────
  detectGesture(startPos, endPos, durationMs) {
    const dx = endPos.x - startPos.x;
    const dy = endPos.y - startPos.y;
    const dist = Math.sqrt(dx * dx + dy * dy);

    if (durationMs > 500 && dist < 10) return 'longpress';
    if (dist < 10) return 'tap';
    if (dist >= 10) return 'drag';
    return 'unknown';
  },

  // ── Garante tap target mínimo 44px ───────────────────────
  tapZoneExpand(element, minSize = 44) {
    const rect = element.getBoundingClientRect();
    const padH = Math.max(0, (minSize - rect.height) / 2);
    const padW = Math.max(0, (minSize - rect.width) / 2);
    element.style.padding = `${padH}px ${padW}px`;
    element.style.margin = `-${padH}px -${padW}px`;
    element.style.cursor = 'pointer';
    element.setAttribute('data-tap-expanded', 'true');
  },

  // ── Aplica tap-expand em todos os elementos de uma zona ──
  expandZone(containerSelector, minSize = 44) {
    const container = document.querySelector(containerSelector);
    if (!container) return;
    const els = container.querySelectorAll('button, [role="button"], .icon-btn, .tool-btn');
    els.forEach(el => this.tapZoneExpand(el, minSize));
  },

  // ── Pinch-to-Zoom engine ──────────────────────────────────
  createPinchZoom(element, opts = {}) {
    const config = {
      minScale: opts.minScale || 0.5,
      maxScale: opts.maxScale || 4.0,
      initialScale: opts.initialScale || 1.0,
      onScaleChange: opts.onScaleChange || null,
    };

    let currentScale = config.initialScale;
    let startDist = 0;
    let startScale = 1;

    function getDistance(touches) {
      const dx = touches[0].clientX - touches[1].clientX;
      const dy = touches[0].clientY - touches[1].clientY;
      return Math.sqrt(dx * dx + dy * dy);
    }

    element.addEventListener('touchstart', (e) => {
      if (e.touches.length === 2) {
        e.preventDefault();
        startDist = getDistance(e.touches);
        startScale = currentScale;
      }
    }, { passive: false });

    element.addEventListener('touchmove', (e) => {
      if (e.touches.length === 2) {
        e.preventDefault();
        const dist = getDistance(e.touches);
        const ratio = dist / startDist;
        currentScale = Math.min(
          config.maxScale,
          Math.max(config.minScale, startScale * ratio)
        );
        if (config.onScaleChange) {
          config.onScaleChange(currentScale);
        }
      }
    }, { passive: false });

    return {
      getScale: () => currentScale,
      setScale: (s) => {
        currentScale = Math.min(config.maxScale, Math.max(config.minScale, s));
        if (config.onScaleChange) config.onScaleChange(currentScale);
      },
      reset: () => {
        currentScale = config.initialScale;
        if (config.onScaleChange) config.onScaleChange(currentScale);
      }
    };
  },

  // ── Long Press listener ───────────────────────────────────
  onLongPress(element, callback, threshold = 500) {
    let timer = null;
    let moved = false;
    let startPos = null;

    const start = (e) => {
      moved = false;
      startPos = WindiTouch.normalizePointer(e);
      timer = setTimeout(() => {
        if (!moved) callback(e);
      }, threshold);
    };

    const cancel = () => {
      if (timer) clearTimeout(timer);
      timer = null;
    };

    const checkMove = (e) => {
      if (!startPos) return;
      const pos = WindiTouch.normalizePointer(e);
      const dx = Math.abs(pos.x - startPos.x);
      const dy = Math.abs(pos.y - startPos.y);
      if (dx > 10 || dy > 10) { moved = true; cancel(); }
    };

    element.addEventListener('touchstart', start, { passive: true });
    element.addEventListener('mousedown', start);
    element.addEventListener('touchmove', checkMove, { passive: true });
    element.addEventListener('mousemove', checkMove);
    element.addEventListener('touchend', cancel);
    element.addEventListener('mouseup', cancel);
    element.addEventListener('touchcancel', cancel);
  },

  // ── Double Tap listener ───────────────────────────────────
  onDoubleTap(element, callback, maxDelay = 300) {
    let lastTap = 0;
    element.addEventListener('touchend', (e) => {
      const now = Date.now();
      if (now - lastTap < maxDelay) {
        e.preventDefault();
        callback(e);
        lastTap = 0;
      } else {
        lastTap = now;
      }
    });
  },

  // ── Utilitário: previne scroll ao arrastar canvas ─────────
  preventScrollOnDrag(element) {
    element.addEventListener('touchmove', (e) => {
      if (e.touches.length === 1) e.preventDefault();
    }, { passive: false });
  }

};

// Auto-init ao carregar
if (typeof window !== 'undefined') {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => WindiTouch.init());
  } else {
    WindiTouch.init();
  }
  window.WindiTouch = WindiTouch;
}
