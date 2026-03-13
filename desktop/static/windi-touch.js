/**
 * WINDI Touch Engine v1.0.0
 * "AI processes. Human decides. WINDI guarantees."
 *
 * Provides:
 *  1. JS Breakpoint Detection (isMobile, isTablet, isDesktop)
 *  2. Swipe Gesture System (left, right, up, down)
 *  3. Sidebar swipe open/close
 *  4. Bottom nav tab swipe
 *  5. Pull-to-refresh hook (optional)
 *
 * Zero dependencies. Drop-in via <script src="/static/windi-touch.js">
 * Or inject directly into existing HTML files.
 *
 * Usage:
 *   WindiTouch.init({ sidebar: '#sidebar', tabs: '.bottom-nav .nav-item' });
 *   WindiTouch.onSwipe('left', () => { ... });
 *   WindiTouch.breakpoints.isMobile // true/false (reactive)
 */

(function (global) {
  'use strict';

  // ─── BREAKPOINTS ──────────────────────────────────────────────────
  const BP = {
    MOBILE_SM: 480,
    MOBILE:    768,
    TABLET:    1024,
    DESKTOP:   1200,
  };

  // ─── INTERNAL STATE ───────────────────────────────────────────────
  let _touch = { startX: 0, startY: 0, startTime: 0, el: null };
  let _handlers = { left: [], right: [], up: [], down: [], swipe: [] };
  let _bp = {};
  let _bpListeners = [];
  let _config = {
    threshold:     60,    // min px to count as swipe
    maxDuration:   500,   // ms max for swipe
    maxVertical:   100,   // max vertical drift for horizontal swipe
    edgeWidth:     30,    // px from left edge to trigger sidebar open swipe
    sidebarEl:     null,
    sidebarOpen:   null,  // fn() → boolean
    sidebarSetOpen:null,  // fn(bool)
    tabEls:        null,
    tabGetActive:  null,  // fn() → index
    tabSetActive:  null,  // fn(index)
    tabCount:      0,
    debug:         false,
  };

  // ─── BREAKPOINT DETECTION ─────────────────────────────────────────
  function _updateBreakpoints() {
    const w = window.innerWidth;
    const prev = JSON.stringify(_bp);
    _bp = {
      isMobileSm:  w < BP.MOBILE_SM,
      isMobile:    w < BP.MOBILE,
      isTablet:    w >= BP.MOBILE && w < BP.DESKTOP,
      isDesktop:   w >= BP.DESKTOP,
      width:       w,
    };
    if (JSON.stringify(_bp) !== prev) {
      _bpListeners.forEach(fn => fn({ ..._bp }));
      // Dispatch custom event for vanilla HTML files
      document.dispatchEvent(new CustomEvent('windi:breakpoint', {
        detail: { ..._bp }
      }));
      if (_config.debug) console.log('[WindiTouch] Breakpoint:', _bp);
    }
  }

  // ─── TOUCH HANDLERS ───────────────────────────────────────────────
  function _onTouchStart(e) {
    const t = e.touches[0];
    _touch = {
      startX:    t.clientX,
      startY:    t.clientY,
      startTime: Date.now(),
      el:        e.target,
    };
  }

  function _onTouchEnd(e) {
    const t = e.changedTouches[0];
    const dx = t.clientX - _touch.startX;
    const dy = t.clientY - _touch.startY;
    const dt = Date.now() - _touch.startTime;
    const absDx = Math.abs(dx);
    const absDy = Math.abs(dy);

    // Reject if too slow or too vertical
    if (dt > _config.maxDuration) return;
    if (absDx < _config.threshold && absDy < _config.threshold) return;

    let dir = null;

    if (absDx > absDy && absDy < _config.maxVertical) {
      // Horizontal swipe
      dir = dx > 0 ? 'right' : 'left';
    } else if (absDy > absDx) {
      // Vertical swipe
      dir = dy > 0 ? 'down' : 'up';
    }

    if (!dir) return;
    if (_config.debug) console.log('[WindiTouch] Swipe:', dir, { dx, dy, dt });

    // Fire generic handlers
    _handlers.swipe.forEach(fn => fn({ dir, dx, dy, dt, startX: _touch.startX, el: _touch.el }));
    _handlers[dir].forEach(fn => fn({ dx, dy, dt, startX: _touch.startX, el: _touch.el }));

    // ── SIDEBAR LOGIC ──────────────────────────────────────────
    if (_config.sidebarSetOpen && _bp.isMobile) {
      if (dir === 'right' && _touch.startX <= _config.edgeWidth && !_getSidebarOpen()) {
        // Edge swipe right → open sidebar
        _config.sidebarSetOpen(true);
        _haptic('light');
        return;
      }
      if (dir === 'left' && _getSidebarOpen()) {
        // Swipe left → close sidebar
        _config.sidebarSetOpen(false);
        _haptic('light');
        return;
      }
    }

    // ── TAB SWIPE LOGIC ────────────────────────────────────────
    if (_config.tabSetActive && _config.tabCount > 1 && _bp.isMobile) {
      if (dir === 'left' || dir === 'right') {
        const current = _getTabActive();
        const next = dir === 'left'
          ? Math.min(current + 1, _config.tabCount - 1)
          : Math.max(current - 1, 0);
        if (next !== current) {
          _config.tabSetActive(next);
          _haptic('light');
        }
      }
    }
  }

  function _getSidebarOpen() {
    if (typeof _config.sidebarOpen === 'function') return _config.sidebarOpen();
    if (_config.sidebarEl) {
      return _config.sidebarEl.classList.contains('open') ||
             _config.sidebarEl.dataset.open === 'true';
    }
    return false;
  }

  function _getTabActive() {
    if (typeof _config.tabGetActive === 'function') return _config.tabGetActive();
    if (_config.tabEls) {
      const idx = Array.from(_config.tabEls).findIndex(el =>
        el.classList.contains('active') || el.dataset.active === 'true'
      );
      return idx >= 0 ? idx : 0;
    }
    return 0;
  }

  // ─── HAPTIC FEEDBACK (iOS/Android) ────────────────────────────────
  function _haptic(style) {
    if ('vibrate' in navigator) {
      navigator.vibrate(style === 'light' ? 10 : 30);
    }
    // iOS 13+ Haptic via AudioContext pulse (silent but triggers haptic on supported devices)
    try {
      if (window.HapticFeedback) window.HapticFeedback.impact({ style });
    } catch (_) {}
  }

  // ─── SIDEBAR OVERLAY DIMMER ───────────────────────────────────────
  let _dimmer = null;
  function _createDimmer() {
    if (_dimmer) return _dimmer;
    _dimmer = document.createElement('div');
    _dimmer.id = 'windi-touch-dimmer';
    _dimmer.style.cssText = `
      position: fixed; inset: 0; z-index: 999;
      background: rgba(26,18,8,0.4);
      opacity: 0; pointer-events: none;
      transition: opacity 0.25s ease;
      -webkit-tap-highlight-color: transparent;
    `;
    _dimmer.addEventListener('click', () => {
      if (_config.sidebarSetOpen) _config.sidebarSetOpen(false);
    });
    document.body.appendChild(_dimmer);
    return _dimmer;
  }

  function showDimmer() {
    const d = _createDimmer();
    d.style.pointerEvents = 'all';
    requestAnimationFrame(() => { d.style.opacity = '1'; });
  }
  function hideDimmer() {
    if (!_dimmer) return;
    _dimmer.style.opacity = '0';
    _dimmer.style.pointerEvents = 'none';
  }

  // ─── SCROLL LOCK ──────────────────────────────────────────────────
  let _scrollY = 0;
  function lockScroll() {
    _scrollY = window.scrollY;
    document.body.style.overflow = 'hidden';
    document.body.style.position = 'fixed';
    document.body.style.top = `-${_scrollY}px`;
    document.body.style.width = '100%';
  }
  function unlockScroll() {
    document.body.style.overflow = '';
    document.body.style.position = '';
    document.body.style.top = '';
    document.body.style.width = '';
    window.scrollTo(0, _scrollY);
  }

  // ─── PULL TO REFRESH ──────────────────────────────────────────────
  let _ptrActive = false;
  let _ptrHandler = null;
  let _ptrIndicator = null;

  function _initPullToRefresh(scrollEl, onRefresh) {
    if (!scrollEl || typeof onRefresh !== 'function') return;
    _ptrHandler = onRefresh;

    _ptrIndicator = document.createElement('div');
    _ptrIndicator.id = 'windi-ptr';
    _ptrIndicator.innerHTML = `
      <div style="
        display:flex;align-items:center;justify-content:center;
        height:52px;font-size:12px;color:#8B6914;
        font-family:'JetBrains Mono',monospace;letter-spacing:0.05em;
        opacity:0;transition:opacity 0.2s;
      " id="windi-ptr-inner">↓ Aktualisieren</div>`;
    scrollEl.parentNode.insertBefore(_ptrIndicator, scrollEl);

    let startY = 0, pulling = false;
    const inner = _ptrIndicator.querySelector('#windi-ptr-inner');

    scrollEl.addEventListener('touchstart', e => {
      if (scrollEl.scrollTop === 0) {
        startY = e.touches[0].clientY;
        pulling = true;
      }
    }, { passive: true });

    scrollEl.addEventListener('touchmove', e => {
      if (!pulling) return;
      const dy = e.touches[0].clientY - startY;
      if (dy > 10 && dy < 80) {
        inner.style.opacity = String(dy / 80);
        inner.style.transform = `translateY(${dy * 0.3}px)`;
      }
    }, { passive: true });

    scrollEl.addEventListener('touchend', e => {
      if (!pulling) return;
      pulling = false;
      const dy = e.changedTouches[0].clientY - startY;
      inner.style.opacity = '0';
      inner.style.transform = '';
      if (dy > 60) {
        _ptrActive = true;
        inner.textContent = '⟳ Laden…';
        inner.style.opacity = '1';
        onRefresh(() => {
          _ptrActive = false;
          inner.style.opacity = '0';
          inner.textContent = '↓ Aktualisieren';
        });
      }
    }, { passive: true });
  }

  // ─── PUBLIC API ───────────────────────────────────────────────────
  const WindiTouch = {

    /**
     * init(options)
     *
     * options.sidebarEl        — CSS selector or DOM element
     * options.sidebarOpen      — fn() → bool (is sidebar currently open?)
     * options.sidebarSetOpen   — fn(bool) (set sidebar state)
     * options.tabCount         — total number of tabs
     * options.tabGetActive     — fn() → index
     * options.tabSetActive     — fn(index)
     * options.edgeWidth        — px from left edge for sidebar swipe (default 30)
     * options.pullToRefresh    — { el: scrollEl, onRefresh: fn(done) }
     * options.debug            — boolean
     */
    init(options = {}) {
      if (options.sidebarEl) {
        _config.sidebarEl = typeof options.sidebarEl === 'string'
          ? document.querySelector(options.sidebarEl)
          : options.sidebarEl;
      }
      if (options.sidebarOpen)    _config.sidebarOpen    = options.sidebarOpen;
      if (options.sidebarSetOpen) _config.sidebarSetOpen = options.sidebarSetOpen;
      if (options.tabCount)       _config.tabCount       = options.tabCount;
      if (options.tabGetActive)   _config.tabGetActive   = options.tabGetActive;
      if (options.tabSetActive)   _config.tabSetActive   = options.tabSetActive;
      if (options.edgeWidth)      _config.edgeWidth      = options.edgeWidth;
      if (options.debug)          _config.debug          = options.debug;

      if (options.pullToRefresh) {
        const ptr = options.pullToRefresh;
        const el = typeof ptr.el === 'string' ? document.querySelector(ptr.el) : ptr.el;
        _initPullToRefresh(el, ptr.onRefresh);
      }

      // Add touch listeners to document
      document.addEventListener('touchstart', _onTouchStart, { passive: true });
      document.addEventListener('touchend',   _onTouchEnd,   { passive: true });

      // Breakpoint detection
      _updateBreakpoints();
      window.addEventListener('resize', _updateBreakpoints, { passive: true });

      if (_config.debug) console.log('[WindiTouch] Initialized', _config);
      return this;
    },

    /** Register swipe direction handler: 'left' | 'right' | 'up' | 'down' | 'swipe' */
    onSwipe(dir, fn) {
      if (_handlers[dir]) _handlers[dir].push(fn);
      return this;
    },

    /** Register breakpoint change listener */
    onBreakpoint(fn) {
      _bpListeners.push(fn);
      fn({ ..._bp });
      return this;
    },

    /** Current breakpoints (reactive after init) */
    get breakpoints() { return { ..._bp }; },

    /** Show/hide sidebar dimmer overlay */
    showDimmer,
    hideDimmer,

    /** Scroll lock utilities */
    lockScroll,
    unlockScroll,

    /** Haptic feedback */
    haptic: _haptic,

    /** Destroy — removes all listeners */
    destroy() {
      document.removeEventListener('touchstart', _onTouchStart);
      document.removeEventListener('touchend',   _onTouchEnd);
      window.removeEventListener('resize',       _updateBreakpoints);
      _handlers = { left: [], right: [], up: [], down: [], swipe: [] };
      _bpListeners = [];
      if (_dimmer) { _dimmer.remove(); _dimmer = null; }
    },

    /** Version */
    version: '1.0.0',
  };

  global.WindiTouch = WindiTouch;

})(window);
