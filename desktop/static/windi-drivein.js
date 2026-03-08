// ═══════════════════════════════════════════════════════════════════════════
// WINDI DRIVE IN — Production Module for Palette UNIFIED
// ═══════════════════════════════════════════════════════════════════════════
// Purpose:  Subliminal video background layer (5% default, 0→100% slider)
// Inject:   Inside Palette UNIFIED HTML, before </body>
// Video:    /palette/static/dragons-forest.mp4 (loop, muted, autoplay)
// Version:  1.0.0-W
// Date:     2026-02-28
// ═══════════════════════════════════════════════════════════════════════════

(function() {
  'use strict';

  // ── CONFIG ──────────────────────────────────────────────────
  const DRIVE_IN_CONFIG = {
    defaultOpacity: 5,          // Start at 5% — subliminal
    videoSrc: '/palette/static/dragons-forest.mp4',
    fallbackPoster: '',         // Optional: first frame as image
    storageKey: 'windi-drivein-opacity',
    zIndex: 0,                  // Behind everything
    sliderZIndex: 9999,         // Above everything
  };

  // ── RESTORE SAVED OPACITY ──────────────────────────────────
  let currentOpacity = DRIVE_IN_CONFIG.defaultOpacity;
  try {
    const saved = localStorage.getItem(DRIVE_IN_CONFIG.storageKey);
    if (saved !== null) currentOpacity = parseInt(saved, 10);
  } catch(e) {}

  // ── CREATE VIDEO LAYER ─────────────────────────────────────
  const videoLayer = document.createElement('div');
  videoLayer.id = 'windi-drivein-layer';
  videoLayer.style.cssText = `
    position: fixed;
    inset: 0;
    z-index: ${DRIVE_IN_CONFIG.zIndex};
    pointer-events: none;
    opacity: ${currentOpacity / 100};
    transition: opacity 0.5s ease;
    overflow: hidden;
  `;

  const video = document.createElement('video');
  video.id = 'windi-drivein-video';
  video.autoplay = true;
  video.loop = true;
  video.muted = true;
  video.playsInline = true;
  video.setAttribute('playsinline', '');
  video.style.cssText = `
    position: absolute;
    top: 50%; left: 50%;
    transform: translate(-50%, -50%);
    min-width: 100%; min-height: 100%;
    width: auto; height: auto;
    object-fit: cover;
  `;

  const source = document.createElement('source');
  source.src = DRIVE_IN_CONFIG.videoSrc;
  source.type = 'video/mp4';
  video.appendChild(source);

  // Fallback: if video fails, try to play on user interaction
  video.addEventListener('error', function() {
    console.warn('[WINDI Drive In] Video not found at', DRIVE_IN_CONFIG.videoSrc);
    console.warn('[WINDI Drive In] Falling back to particle mode');
    initParticleFallback(videoLayer);
  });

  videoLayer.appendChild(video);
  document.body.insertBefore(videoLayer, document.body.firstChild);

  // Autoplay might be blocked — retry on first interaction
  document.addEventListener('click', function startVideo() {
    video.play().catch(function(){});
    document.removeEventListener('click', startVideo);
  }, { once: true });

  // Try to play immediately
  video.play().catch(function(){});

  // ── CREATE SLIDER CONTROL ──────────────────────────────────
  const slider = document.createElement('div');
  slider.id = 'windi-drivein-slider';
  slider.innerHTML = `
    <span class="windi-di-icon">🐉</span>
    <input type="range" min="0" max="100" value="${currentOpacity}"
           class="windi-di-range" id="windi-di-range" />
    <span class="windi-di-val" id="windi-di-val">${currentOpacity}%</span>
  `;

  // ── SLIDER STYLES ──────────────────────────────────────────
  const style = document.createElement('style');
  style.textContent = `
    #windi-drivein-slider {
      position: fixed;
      bottom: 16px;
      right: 16px;
      z-index: ${DRIVE_IN_CONFIG.sliderZIndex};
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 6px 12px;
      border-radius: 20px;
      background: var(--windi-card, rgba(253,251,245,0.95));
      border: 1px solid var(--windi-border, #DDD6C2);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      box-shadow: 0 2px 12px rgba(0,0,0,0.06);
      opacity: 0.35;
      transition: opacity 0.3s ease, transform 0.2s ease;
      transform: translateY(2px);
      font-family: 'JetBrains Mono', monospace;
      cursor: pointer;
    }
    #windi-drivein-slider:hover,
    #windi-drivein-slider.active {
      opacity: 1;
      transform: translateY(0);
      box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
    .windi-di-icon {
      font-size: 14px;
      line-height: 1;
    }
    .windi-di-range {
      width: 50px;
      height: 3px;
      border-radius: 2px;
      -webkit-appearance: none;
      appearance: none;
      background: linear-gradient(to right,
        var(--windi-gold, #8B6914) ${currentOpacity}%,
        var(--windi-border, #DDD6C2) ${currentOpacity}%);
      outline: none;
      cursor: pointer;
      transition: width 0.3s ease;
    }
    #windi-drivein-slider:hover .windi-di-range,
    #windi-drivein-slider.active .windi-di-range {
      width: 110px;
    }
    .windi-di-range::-webkit-slider-thumb {
      -webkit-appearance: none;
      width: 12px;
      height: 12px;
      border-radius: 50%;
      background: var(--windi-gold, #8B6914);
      cursor: pointer;
      border: 2px solid var(--windi-card, #FDFBF5);
      box-shadow: 0 1px 3px rgba(0,0,0,0.15);
    }
    .windi-di-range::-moz-range-thumb {
      width: 12px;
      height: 12px;
      border-radius: 50%;
      background: var(--windi-gold, #8B6914);
      cursor: pointer;
      border: 2px solid var(--windi-card, #FDFBF5);
    }
    .windi-di-val {
      font-size: 9px;
      color: var(--windi-muted, #6B6560);
      min-width: 28px;
      text-align: right;
      font-family: 'JetBrains Mono', monospace;
    }

    /* NOIR theme adaptation */
    [data-theme="NOIR"] #windi-drivein-slider,
    .noir #windi-drivein-slider {
      background: rgba(22,22,31,0.95);
      border-color: #26263A;
      box-shadow: 0 2px 12px rgba(0,0,0,0.3);
    }
    [data-theme="NOIR"] .windi-di-range,
    .noir .windi-di-range {
      background: linear-gradient(to right, #D4A843 var(--di-pct, 5%), #26263A var(--di-pct, 5%));
    }
    [data-theme="NOIR"] .windi-di-range::-webkit-slider-thumb,
    .noir .windi-di-range::-webkit-slider-thumb {
      background: #D4A843;
      border-color: #16161F;
    }

    /* Mobile: move above bottom nav if exists */
    @media (max-width: 768px) {
      #windi-drivein-slider {
        bottom: 70px;
        right: 12px;
      }
    }
  `;
  document.head.appendChild(style);
  document.body.appendChild(slider);

  // ── SLIDER INTERACTION ─────────────────────────────────────
  const range = document.getElementById('windi-di-range');
  const valDisplay = document.getElementById('windi-di-val');

  function updateOpacity(val) {
    currentOpacity = val;
    videoLayer.style.opacity = val / 100;
    valDisplay.textContent = val + '%';
    range.style.background = `linear-gradient(to right, var(--windi-gold, #8B6914) ${val}%, var(--windi-border, #DDD6C2) ${val}%)`;
    range.style.setProperty('--di-pct', val + '%');
    try { localStorage.setItem(DRIVE_IN_CONFIG.storageKey, val); } catch(e) {}
  }

  range.addEventListener('input', function(e) {
    updateOpacity(parseInt(e.target.value, 10));
    slider.classList.add('active');
  });

  range.addEventListener('change', function() {
    setTimeout(function() { slider.classList.remove('active'); }, 2000);
  });

  slider.addEventListener('mouseenter', function() { slider.classList.add('active'); });
  slider.addEventListener('mouseleave', function() {
    if (document.activeElement !== range) slider.classList.remove('active');
  });

  // ── PARTICLE FALLBACK (when video not available) ───────────
  function initParticleFallback(container) {
    const canvas = document.createElement('canvas');
    canvas.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;';
    container.innerHTML = '';
    container.appendChild(canvas);

    const ctx = canvas.getContext('2d');
    let particles = [];
    const COLORS = ['#8B6914', '#B8860B', '#6B8F5A', '#2A5F3B', '#D4A843'];

    function resize() {
      canvas.width = window.innerWidth * 2;
      canvas.height = window.innerHeight * 2;
      ctx.scale(2, 2);
    }
    resize();
    window.addEventListener('resize', resize);

    // Create mystical particles
    for (let i = 0; i < 80; i++) {
      particles.push({
        x: Math.random() * window.innerWidth,
        y: Math.random() * window.innerHeight,
        vx: (Math.random() - 0.5) * 0.6,
        vy: (Math.random() - 0.5) * 0.3 - 0.15,
        size: Math.random() * 3 + 0.5,
        color: COLORS[Math.floor(Math.random() * COLORS.length)],
        alpha: Math.random() * 0.6 + 0.2,
        pulse: Math.random() * Math.PI * 2,
      });
    }

    function animate() {
      const w = window.innerWidth, h = window.innerHeight;
      ctx.clearRect(0, 0, w, h);

      // Subtle tree silhouettes
      const time = Date.now() * 0.001;
      for (let t = 0; t < 5; t++) {
        const tx = (w / 6) * (t + 1);
        const th = h * 0.35;
        ctx.strokeStyle = 'rgba(42,95,59,0.08)';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(tx, h);
        ctx.lineTo(tx + Math.sin(time * 0.5 + t) * 3, h - th);
        ctx.stroke();

        ctx.fillStyle = 'rgba(90,143,74,0.04)';
        ctx.beginPath();
        ctx.arc(tx, h - th, 20 + t * 5, 0, Math.PI * 2);
        ctx.fill();
      }

      // Dragon silhouette
      for (let d = 0; d < 2; d++) {
        const dx = w * 0.5 + Math.sin(time * 0.25 + d * 2) * w * 0.3;
        const dy = h * 0.2 + Math.cos(time * 0.15 + d) * h * 0.1;
        ctx.fillStyle = 'rgba(139,105,20,0.06)';
        ctx.save();
        ctx.translate(dx, dy);
        ctx.rotate(Math.sin(time * 0.3 + d) * 0.2);
        // Wings
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.quadraticCurveTo(-25, -18, -40, -5);
        ctx.quadraticCurveTo(-25, 4, 0, 0);
        ctx.fill();
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.quadraticCurveTo(25, -18, 40, -5);
        ctx.quadraticCurveTo(25, 4, 0, 0);
        ctx.fill();
        ctx.restore();
      }

      // Particles
      particles.forEach(function(p) {
        p.x += p.vx;
        p.y += p.vy;
        p.pulse += 0.02;
        if (p.x < -10) p.x = w + 10;
        if (p.x > w + 10) p.x = -10;
        if (p.y < -10) p.y = h + 10;
        if (p.y > h + 10) p.y = -10;

        const a = p.alpha * (0.5 + Math.sin(p.pulse) * 0.3);
        ctx.fillStyle = p.color + Math.round(a * 255).toString(16).padStart(2, '0');
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fill();
      });

      requestAnimationFrame(animate);
    }
    animate();
  }

  // ── GLOBAL API ─────────────────────────────────────────────
  window.WINDIDriveIn = {
    setOpacity: updateOpacity,
    getOpacity: function() { return currentOpacity; },
    show: function() { slider.style.display = 'flex'; },
    hide: function() { slider.style.display = 'none'; },
    setVideo: function(src) {
      source.src = src;
      video.load();
      video.play().catch(function(){});
    },
  };

  console.log('[WINDI Drive In] 🐉 Initialized at ' + currentOpacity + '% opacity');

})();
