// ═══════════════════════════════════════════════════════════════════════
// WINDI GENESIS ONBOARDING v2.0
// "AI processes. Human decides. WINDI guarantees."
//
// Three Dragons Protocol: Guardian | Architect | Witness
// Phase Integration: Synchronize Pulse → Crystallization → Baptized in Ledger
//
// DESIGN PRINCIPLES:
//   - Internal overlay (no browser popups)
//   - 75% → 100% opacity on interaction
//   - NOIR/KLAR theme inheritance
//   - Trilingual (PT/DE/EN)
//   - RetroactiveSeal for pre-wallet content
// ═══════════════════════════════════════════════════════════════════════

(function() {
  'use strict';

  // ── CONFIGURATION ────────────────────────────────────────────────────
  const GENESIS_CONFIG = {
    API_BASE: '/api/wallet',
    REMINDER_INTERVAL_MS: 3 * 60 * 1000, // 3 minutes
    MAX_REMINDERS: 3,
    ANIMATION_FPS: 60,
    ORB_SIZE: 120,
    STORAGE_KEY: 'windi_genesis_state',
  };

  // ── WAVE PROTOCOL v1.0 ───────────────────────────────────────────────
  // "A porteira antes do cavalo" — Guardian Dragon
  const WAVE_CONFIG = {
    current_wave: 0,
    wave_limits: [10, 50, 200, 500, 1000],
    wave_names: {
      pt: ['Interno', 'Beta', 'Controlado', 'Aberto', 'Escala'],
      de: ['Intern', 'Beta', 'Kontrolliert', 'Offen', 'Skalierung'],
      en: ['Internal', 'Beta', 'Controlled', 'Open', 'Scale'],
    },
    waitlist_enabled: true,
  };

  // ── TRILINGUAL LABELS ────────────────────────────────────────────────
  const GENESIS_LABELS = {
    pt: {
      title: "Baptismo Digital",
      subtitle: "Entrar no Ledger Soberano",
      phase1_title: "Sincronizar Pulso",
      phase1_desc: "O sistema detecta a tua presenca. Respira com o orbe.",
      phase2_title: "Cristalizacao",
      phase2_desc: "A tua identidade esta a formar-se. Aguarda o selo.",
      phase3_title: "Baptizado no Ledger",
      phase3_desc: "Bem-vindo ao ecossistema WINDI. Es soberano.",
      btn_begin: "Iniciar Baptismo",
      btn_continue: "Continuar",
      btn_complete: "Entrar no Ecossistema",
      btn_later: "Mais tarde",
      reminder_gentle: "O Ledger aguarda...",
      reminder_urgent: "Ultima chamada para o Ledger",
      reminder_final: "Genesis encerra em breve",
      email_label: "Email para identidade soberana",
      email_placeholder: "tu@exemplo.com",
      name_label: "Nome (opcional)",
      name_placeholder: "Como queres ser chamado",
      error_email: "Email invalido",
      error_provision: "Erro ao provisionar wallet",
      success: "Wallet provisionada com sucesso!",
      already_registered: "Ja tens uma wallet activa",
      seal_retroactive: "Selando conteudo pre-wallet...",
      seal_complete: "Conteudo ancorado no Ledger",
      health_ok: "Wallet Service activo",
      health_fail: "Wallet Service indisponivel",
      dragon_guardian: "Guardian Dragon protege",
      dragon_architect: "Architect Dragon constroi",
      dragon_witness: "Witness Dragon testemunha",
      // Wave Protocol
      waitlist_title: "Crescimento Controlado",
      waitlist_desc: "O Ledger esta em fase de crescimento controlado.",
      waitlist_status: "Estas na lista de espera — seras notificado quando houver vagas.",
      waitlist_wave: "Wave actual",
      waitlist_next: "Proxima",
      waitlist_btn: "Entrar na Lista de Espera",
      waitlist_email: "Email para notificacao",
      waitlist_success: "Adicionado a lista de espera!",
    },
    de: {
      title: "Digitale Taufe",
      subtitle: "Eintritt in das Souverane Ledger",
      phase1_title: "Puls Synchronisieren",
      phase1_desc: "Das System erkennt deine Prasenz. Atme mit dem Orb.",
      phase2_title: "Kristallisation",
      phase2_desc: "Deine Identitat formt sich. Warte auf das Siegel.",
      phase3_title: "Im Ledger Getauft",
      phase3_desc: "Willkommen im WINDI Okosystem. Du bist souveran.",
      btn_begin: "Taufe Starten",
      btn_continue: "Fortfahren",
      btn_complete: "Okosystem Betreten",
      btn_later: "Spater",
      reminder_gentle: "Das Ledger wartet...",
      reminder_urgent: "Letzter Aufruf fur das Ledger",
      reminder_final: "Genesis endet bald",
      email_label: "E-Mail fur souverane Identitat",
      email_placeholder: "du@beispiel.de",
      name_label: "Name (optional)",
      name_placeholder: "Wie mochtest du genannt werden",
      error_email: "Ungultige E-Mail",
      error_provision: "Fehler bei Wallet-Bereitstellung",
      success: "Wallet erfolgreich bereitgestellt!",
      already_registered: "Du hast bereits eine aktive Wallet",
      seal_retroactive: "Versiegle Pre-Wallet Inhalte...",
      seal_complete: "Inhalte im Ledger verankert",
      health_ok: "Wallet Service aktiv",
      health_fail: "Wallet Service nicht verfugbar",
      dragon_guardian: "Guardian Dragon schutzt",
      dragon_architect: "Architect Dragon baut",
      dragon_witness: "Witness Dragon bezeugt",
      // Wave Protocol
      waitlist_title: "Kontrolliertes Wachstum",
      waitlist_desc: "Das Ledger befindet sich in kontrollierter Wachstumsphase.",
      waitlist_status: "Du bist auf der Warteliste — wir benachrichtigen dich, wenn Platze frei werden.",
      waitlist_wave: "Aktuelle Wave",
      waitlist_next: "Nachste",
      waitlist_btn: "Auf Warteliste setzen",
      waitlist_email: "E-Mail fur Benachrichtigung",
      waitlist_success: "Zur Warteliste hinzugefugt!",
    },
    en: {
      title: "Digital Baptism",
      subtitle: "Enter the Sovereign Ledger",
      phase1_title: "Synchronize Pulse",
      phase1_desc: "The system detects your presence. Breathe with the orb.",
      phase2_title: "Crystallization",
      phase2_desc: "Your identity is forming. Await the seal.",
      phase3_title: "Baptized in Ledger",
      phase3_desc: "Welcome to the WINDI ecosystem. You are sovereign.",
      btn_begin: "Begin Baptism",
      btn_continue: "Continue",
      btn_complete: "Enter Ecosystem",
      btn_later: "Later",
      reminder_gentle: "The Ledger awaits...",
      reminder_urgent: "Last call for the Ledger",
      reminder_final: "Genesis closing soon",
      email_label: "Email for sovereign identity",
      email_placeholder: "you@example.com",
      name_label: "Name (optional)",
      name_placeholder: "What shall we call you",
      error_email: "Invalid email",
      error_provision: "Error provisioning wallet",
      success: "Wallet provisioned successfully!",
      already_registered: "You already have an active wallet",
      seal_retroactive: "Sealing pre-wallet content...",
      seal_complete: "Content anchored in Ledger",
      health_ok: "Wallet Service active",
      health_fail: "Wallet Service unavailable",
      dragon_guardian: "Guardian Dragon protects",
      dragon_architect: "Architect Dragon builds",
      dragon_witness: "Witness Dragon witnesses",
      // Wave Protocol
      waitlist_title: "Controlled Growth",
      waitlist_desc: "The Ledger is in controlled growth phase.",
      waitlist_status: "You're on the waitlist — we'll notify you when spots open.",
      waitlist_wave: "Current Wave",
      waitlist_next: "Next",
      waitlist_btn: "Join Waitlist",
      waitlist_email: "Email for notification",
      waitlist_success: "Added to waitlist!",
    },
  };

  // ── STATE MANAGEMENT ─────────────────────────────────────────────────
  let genesisState = {
    phase: 0,           // 0=not started, 1=sync, 2=crystallize, 3=complete
    email: '',
    name: '',
    walletId: null,
    publicKey: null,
    reminderCount: 0,
    lastReminder: null,
    dismissed: false,
    overlayVisible: false,
    opacity: 0.75,
    theme: 'KLAR',
    lang: 'en',
    healthStatus: null,
    retroactiveHashes: [],
    // Wave Protocol state
    waveCapacity: {
      currentHumans: 0,
      waveLimit: WAVE_CONFIG.wave_limits[WAVE_CONFIG.current_wave],
      currentWave: WAVE_CONFIG.current_wave,
      atCapacity: false,
      onWaitlist: false,
    },
  };

  // ── THEME DEFINITIONS (mirror from Palette) ──────────────────────────
  const GENESIS_THEMES = {
    KLAR: {
      bg: "#F5F0E0", card: "#FDFBF5", overlay: "rgba(245,240,224,0.95)",
      border: "#DDD6C2", gold: "#8B6914", goldGlow: "rgba(139,105,20,0.3)",
      text: "#2C2924", dim: "#6B6560", muted: "#9B958E",
      green: "#1A7A42", red: "#C0392B", blue: "#2563EB",
      orbCore: "#D4A843", orbGlow: "rgba(212,168,67,0.4)",
    },
    NOIR: {
      bg: "#0E0E14", card: "#16161F", overlay: "rgba(14,14,20,0.95)",
      border: "#26263A", gold: "#D4A843", goldGlow: "rgba(212,168,67,0.5)",
      text: "#E2E2EA", dim: "#7A7A96", muted: "#4A4A62",
      green: "#2ECC71", red: "#E74C3C", blue: "#3498DB",
      orbCore: "#D4A843", orbGlow: "rgba(212,168,67,0.6)",
    },
  };

  // ── STORAGE PERSISTENCE ──────────────────────────────────────────────
  function saveState() {
    try {
      localStorage.setItem(GENESIS_CONFIG.STORAGE_KEY, JSON.stringify(genesisState));
    } catch (e) {
      console.warn('[Genesis] Storage save failed:', e);
    }
  }

  function loadState() {
    try {
      const stored = localStorage.getItem(GENESIS_CONFIG.STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        genesisState = { ...genesisState, ...parsed };
      }
    } catch (e) {
      console.warn('[Genesis] Storage load failed:', e);
    }
  }

  // ── API CALLS ────────────────────────────────────────────────────────
  async function checkHealth() {
    try {
      const resp = await fetch(`${GENESIS_CONFIG.API_BASE}/health`);
      const data = await resp.json();
      genesisState.healthStatus = data.status === 'healthy' || data.status === 'ok';

      // Extract humans count for Wave Protocol
      if (typeof data.humans === 'number') {
        genesisState.waveCapacity.currentHumans = data.humans;
        genesisState.waveCapacity.waveLimit = WAVE_CONFIG.wave_limits[WAVE_CONFIG.current_wave];
        genesisState.waveCapacity.currentWave = WAVE_CONFIG.current_wave;
        genesisState.waveCapacity.atCapacity = data.humans >= genesisState.waveCapacity.waveLimit;
      }

      return genesisState.healthStatus;
    } catch (e) {
      genesisState.healthStatus = false;
      return false;
    }
  }

  // ── WAVE PROTOCOL ──────────────────────────────────────────────────────
  function isAtWaveCapacity() {
    return genesisState.waveCapacity.atCapacity && WAVE_CONFIG.waitlist_enabled;
  }

  function getWaveInfo() {
    const wave = genesisState.waveCapacity;
    const lang = genesisState.lang;
    const waveNames = WAVE_CONFIG.wave_names[lang] || WAVE_CONFIG.wave_names.en;
    const nextWave = wave.currentWave + 1;
    const nextLimit = WAVE_CONFIG.wave_limits[nextWave] || '1000+';

    return {
      currentWave: wave.currentWave,
      currentName: waveNames[wave.currentWave] || 'Internal',
      nextWave: nextWave,
      nextName: waveNames[nextWave] || 'Scale',
      currentHumans: wave.currentHumans,
      waveLimit: wave.waveLimit,
      nextLimit: nextLimit,
      spotsRemaining: Math.max(0, wave.waveLimit - wave.currentHumans),
    };
  }

  async function joinWaitlist(email) {
    // Store waitlist email locally (in production, would POST to server)
    try {
      const waitlist = JSON.parse(localStorage.getItem('windi_genesis_waitlist') || '[]');
      if (!waitlist.includes(email)) {
        waitlist.push(email);
        localStorage.setItem('windi_genesis_waitlist', JSON.stringify(waitlist));
      }
      genesisState.waveCapacity.onWaitlist = true;
      genesisState.email = email;
      saveState();
      return true;
    } catch (e) {
      console.warn('[Genesis] Waitlist join failed:', e);
      return false;
    }
  }

  async function checkExistingWallet(email) {
    try {
      const resp = await fetch(`${GENESIS_CONFIG.API_BASE}/me?email=${encodeURIComponent(email)}`);
      if (resp.status === 200) {
        const data = await resp.json();
        return data;
      }
      return null;
    } catch (e) {
      return null;
    }
  }

  async function provisionWallet(email, displayName) {
    try {
      const resp = await fetch(`${GENESIS_CONFIG.API_BASE}/provision`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: email,
          display_name: displayName || email.split('@')[0],
          tier: 'PERSONAL',
          source: 'genesis_palette',
        }),
      });

      if (!resp.ok) {
        const errData = await resp.json().catch(() => ({}));
        throw new Error(errData.error || `HTTP ${resp.status}`);
      }

      const data = await resp.json();
      return data;
    } catch (e) {
      console.error('[Genesis] Provision failed:', e);
      throw e;
    }
  }

  async function retroactiveSeal(hashes) {
    try {
      const resp = await fetch(`${GENESIS_CONFIG.API_BASE}/bridge/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'retroactive_seal',
          hashes: hashes,
          wallet_id: genesisState.walletId,
        }),
      });
      return resp.ok;
    } catch (e) {
      console.warn('[Genesis] Retroactive seal failed:', e);
      return false;
    }
  }

  // ── LIVING ORB ANIMATION ─────────────────────────────────────────────
  class LivingOrb {
    constructor(canvas, theme) {
      this.canvas = canvas;
      this.ctx = canvas.getContext('2d');
      this.theme = GENESIS_THEMES[theme] || GENESIS_THEMES.KLAR;
      this.size = GENESIS_CONFIG.ORB_SIZE;
      this.center = this.size / 2;
      this.phase = 0;
      this.breathePhase = 0;
      this.particlePhase = 0;
      this.running = false;

      canvas.width = this.size;
      canvas.height = this.size;
    }

    start() {
      this.running = true;
      this.animate();
    }

    stop() {
      this.running = false;
    }

    setPhase(phase) {
      this.phase = phase;
    }

    setTheme(themeName) {
      this.theme = GENESIS_THEMES[themeName] || GENESIS_THEMES.KLAR;
    }

    animate() {
      if (!this.running) return;

      const ctx = this.ctx;
      const T = this.theme;

      // Clear
      ctx.clearRect(0, 0, this.size, this.size);

      // Breathing animation
      this.breathePhase += 0.02;
      const breatheScale = 1 + Math.sin(this.breathePhase) * 0.08;
      const baseRadius = 35 * breatheScale;

      // Phase-based intensity
      const intensity = 0.5 + (this.phase * 0.15);

      // Outer glow
      const gradient = ctx.createRadialGradient(
        this.center, this.center, 0,
        this.center, this.center, baseRadius * 1.5
      );
      gradient.addColorStop(0, T.orbCore);
      gradient.addColorStop(0.5, T.orbGlow);
      gradient.addColorStop(1, 'transparent');

      ctx.beginPath();
      ctx.arc(this.center, this.center, baseRadius * 1.5, 0, Math.PI * 2);
      ctx.fillStyle = gradient;
      ctx.globalAlpha = intensity;
      ctx.fill();

      // Core orb
      ctx.beginPath();
      ctx.arc(this.center, this.center, baseRadius * 0.7, 0, Math.PI * 2);
      ctx.fillStyle = T.orbCore;
      ctx.globalAlpha = 0.9;
      ctx.fill();

      // Inner highlight
      ctx.beginPath();
      ctx.arc(this.center - 8, this.center - 8, baseRadius * 0.2, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(255,255,255,0.4)';
      ctx.globalAlpha = 0.6;
      ctx.fill();

      // Particles (phase 2+)
      if (this.phase >= 2) {
        this.particlePhase += 0.03;
        for (let i = 0; i < 8; i++) {
          const angle = (Math.PI * 2 / 8) * i + this.particlePhase;
          const dist = baseRadius * 1.2 + Math.sin(this.particlePhase * 2 + i) * 10;
          const px = this.center + Math.cos(angle) * dist;
          const py = this.center + Math.sin(angle) * dist;

          ctx.beginPath();
          ctx.arc(px, py, 2, 0, Math.PI * 2);
          ctx.fillStyle = T.gold;
          ctx.globalAlpha = 0.6 + Math.sin(this.particlePhase + i) * 0.3;
          ctx.fill();
        }
      }

      // Dragon ring (phase 3)
      if (this.phase >= 3) {
        ctx.strokeStyle = T.gold;
        ctx.lineWidth = 2;
        ctx.globalAlpha = 0.8;
        ctx.beginPath();
        ctx.arc(this.center, this.center, baseRadius * 1.3, 0, Math.PI * 2);
        ctx.stroke();
      }

      ctx.globalAlpha = 1;

      requestAnimationFrame(() => this.animate());
    }
  }

  // ── OVERLAY UI ───────────────────────────────────────────────────────
  let overlayElement = null;
  let orbInstance = null;

  function createOverlay() {
    if (overlayElement) return;

    // Check wave capacity — show waitlist if at limit
    if (isAtWaveCapacity() && !genesisState.walletId) {
      createWaitlistOverlay();
      return;
    }

    const T = GENESIS_THEMES[genesisState.theme];
    const L = GENESIS_LABELS[genesisState.lang] || GENESIS_LABELS.en;

    overlayElement = document.createElement('div');
    overlayElement.id = 'genesis-overlay';
    overlayElement.innerHTML = `
      <style>
        #genesis-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: ${T.overlay};
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 10000;
          opacity: ${genesisState.opacity};
          transition: opacity 0.3s ease;
          font-family: 'Bricolage Grotesque', system-ui, sans-serif;
        }
        #genesis-overlay:hover {
          opacity: 1;
        }
        #genesis-card {
          background: ${T.card};
          border: 1px solid ${T.border};
          border-radius: 16px;
          padding: 32px;
          max-width: 420px;
          width: 90%;
          box-shadow: 0 20px 60px rgba(0,0,0,0.2);
          text-align: center;
        }
        #genesis-title {
          font-size: 24px;
          font-weight: 700;
          color: ${T.gold};
          margin-bottom: 8px;
        }
        #genesis-subtitle {
          font-size: 13px;
          color: ${T.dim};
          margin-bottom: 24px;
        }
        #genesis-orb-container {
          display: flex;
          justify-content: center;
          margin-bottom: 24px;
        }
        #genesis-phase-title {
          font-size: 16px;
          font-weight: 600;
          color: ${T.text};
          margin-bottom: 8px;
        }
        #genesis-phase-desc {
          font-size: 12px;
          color: ${T.muted};
          margin-bottom: 20px;
          line-height: 1.5;
        }
        #genesis-form {
          display: none;
          flex-direction: column;
          gap: 12px;
          margin-bottom: 20px;
        }
        #genesis-form.visible {
          display: flex;
        }
        .genesis-input-group {
          text-align: left;
        }
        .genesis-input-label {
          font-size: 11px;
          font-weight: 600;
          color: ${T.dim};
          margin-bottom: 4px;
          display: block;
        }
        .genesis-input {
          width: 100%;
          padding: 12px 14px;
          border: 1px solid ${T.border};
          border-radius: 8px;
          background: ${T.bg};
          color: ${T.text};
          font-size: 14px;
          font-family: inherit;
          transition: border-color 0.2s;
        }
        .genesis-input:focus {
          outline: none;
          border-color: ${T.gold};
        }
        .genesis-input::placeholder {
          color: ${T.muted};
        }
        #genesis-error {
          color: ${T.red};
          font-size: 12px;
          display: none;
        }
        #genesis-error.visible {
          display: block;
        }
        #genesis-success {
          color: ${T.green};
          font-size: 13px;
          font-weight: 600;
          display: none;
        }
        #genesis-success.visible {
          display: block;
        }
        #genesis-dragons {
          display: flex;
          justify-content: center;
          gap: 20px;
          margin: 16px 0;
          font-size: 11px;
          color: ${T.muted};
        }
        .genesis-dragon {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 4px;
        }
        .genesis-dragon-emoji {
          font-size: 20px;
        }
        #genesis-buttons {
          display: flex;
          gap: 12px;
          justify-content: center;
          margin-top: 20px;
        }
        .genesis-btn {
          padding: 12px 24px;
          border-radius: 8px;
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
          font-family: inherit;
        }
        .genesis-btn-primary {
          background: ${T.gold};
          color: ${genesisState.theme === 'KLAR' ? '#FFF' : T.bg};
          border: none;
        }
        .genesis-btn-primary:hover {
          filter: brightness(1.1);
        }
        .genesis-btn-secondary {
          background: transparent;
          color: ${T.muted};
          border: 1px solid ${T.border};
        }
        .genesis-btn-secondary:hover {
          border-color: ${T.dim};
          color: ${T.dim};
        }
        .genesis-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        #genesis-progress {
          display: flex;
          justify-content: center;
          gap: 8px;
          margin-bottom: 20px;
        }
        .genesis-progress-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: ${T.border};
          transition: background 0.3s;
        }
        .genesis-progress-dot.active {
          background: ${T.gold};
        }
        .genesis-progress-dot.complete {
          background: ${T.green};
        }
        @keyframes genesis-breathe {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.02); }
        }
        @keyframes genesis-pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.6; }
        }
        #genesis-seal-status {
          font-size: 11px;
          color: ${T.muted};
          margin-top: 12px;
          display: none;
        }
        #genesis-seal-status.visible {
          display: block;
          animation: genesis-pulse 1.5s ease-in-out infinite;
        }
      </style>
      <div id="genesis-card">
        <div id="genesis-title">${L.title}</div>
        <div id="genesis-subtitle">${L.subtitle}</div>

        <div id="genesis-progress">
          <div class="genesis-progress-dot" data-phase="1"></div>
          <div class="genesis-progress-dot" data-phase="2"></div>
          <div class="genesis-progress-dot" data-phase="3"></div>
        </div>

        <div id="genesis-orb-container">
          <canvas id="genesis-orb"></canvas>
        </div>

        <div id="genesis-phase-title">${L.phase1_title}</div>
        <div id="genesis-phase-desc">${L.phase1_desc}</div>

        <div id="genesis-form">
          <div class="genesis-input-group">
            <label class="genesis-input-label">${L.email_label}</label>
            <input type="email" id="genesis-email" class="genesis-input" placeholder="${L.email_placeholder}">
          </div>
          <div class="genesis-input-group">
            <label class="genesis-input-label">${L.name_label}</label>
            <input type="text" id="genesis-name" class="genesis-input" placeholder="${L.name_placeholder}">
          </div>
        </div>

        <div id="genesis-error"></div>
        <div id="genesis-success"></div>
        <div id="genesis-seal-status"></div>

        <div id="genesis-dragons">
          <div class="genesis-dragon">
            <span class="genesis-dragon-emoji">🛡️</span>
            <span>Guardian</span>
          </div>
          <div class="genesis-dragon">
            <span class="genesis-dragon-emoji">🏗️</span>
            <span>Architect</span>
          </div>
          <div class="genesis-dragon">
            <span class="genesis-dragon-emoji">👁️</span>
            <span>Witness</span>
          </div>
        </div>

        <div id="genesis-buttons">
          <button class="genesis-btn genesis-btn-secondary" id="genesis-btn-later">${L.btn_later}</button>
          <button class="genesis-btn genesis-btn-primary" id="genesis-btn-action">${L.btn_begin}</button>
        </div>
      </div>
    `;

    document.body.appendChild(overlayElement);

    // Initialize orb
    const canvas = document.getElementById('genesis-orb');
    orbInstance = new LivingOrb(canvas, genesisState.theme);
    orbInstance.setPhase(genesisState.phase);
    orbInstance.start();

    // Bind events
    document.getElementById('genesis-btn-later').addEventListener('click', handleLater);
    document.getElementById('genesis-btn-action').addEventListener('click', handleAction);
    document.getElementById('genesis-email').addEventListener('input', validateEmail);

    // Opacity on interaction
    overlayElement.addEventListener('mouseenter', () => {
      overlayElement.style.opacity = '1';
    });
    overlayElement.addEventListener('mouseleave', () => {
      if (genesisState.phase < 2) {
        overlayElement.style.opacity = String(genesisState.opacity);
      }
    });

    updatePhaseUI();
  }

  // ── WAITLIST OVERLAY (Wave Protocol) ─────────────────────────────────
  function createWaitlistOverlay() {
    if (overlayElement) return;

    const T = GENESIS_THEMES[genesisState.theme];
    const L = GENESIS_LABELS[genesisState.lang] || GENESIS_LABELS.en;
    const waveInfo = getWaveInfo();

    overlayElement = document.createElement('div');
    overlayElement.id = 'genesis-overlay';
    overlayElement.innerHTML = `
      <style>
        #genesis-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: ${T.overlay};
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 10000;
          opacity: ${genesisState.opacity};
          transition: opacity 0.3s ease;
          font-family: 'Bricolage Grotesque', system-ui, sans-serif;
        }
        #genesis-overlay:hover {
          opacity: 1;
        }
        #genesis-card {
          background: ${T.card};
          border: 1px solid ${T.border};
          border-radius: 16px;
          padding: 32px;
          max-width: 420px;
          width: 90%;
          box-shadow: 0 20px 60px rgba(0,0,0,0.2);
          text-align: center;
        }
        #genesis-title {
          font-size: 24px;
          font-weight: 700;
          color: ${T.gold};
          margin-bottom: 8px;
        }
        #genesis-subtitle {
          font-size: 13px;
          color: ${T.dim};
          margin-bottom: 24px;
        }
        .genesis-wave-badge {
          display: inline-block;
          padding: 6px 16px;
          border-radius: 20px;
          background: ${T.gold}15;
          border: 1px solid ${T.gold}30;
          color: ${T.gold};
          font-size: 12px;
          font-weight: 600;
          margin-bottom: 20px;
        }
        .genesis-wave-info {
          display: flex;
          justify-content: center;
          gap: 24px;
          margin: 16px 0;
          font-size: 11px;
          color: ${T.muted};
        }
        .genesis-wave-stat {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 4px;
        }
        .genesis-wave-stat-value {
          font-size: 18px;
          font-weight: 700;
          color: ${T.text};
        }
        .genesis-input-group {
          text-align: left;
          margin-bottom: 16px;
        }
        .genesis-input-label {
          font-size: 11px;
          font-weight: 600;
          color: ${T.dim};
          margin-bottom: 4px;
          display: block;
        }
        .genesis-input {
          width: 100%;
          padding: 12px 14px;
          border: 1px solid ${T.border};
          border-radius: 8px;
          background: ${T.bg};
          color: ${T.text};
          font-size: 14px;
          font-family: inherit;
          transition: border-color 0.2s;
        }
        .genesis-input:focus {
          outline: none;
          border-color: ${T.gold};
        }
        .genesis-input::placeholder {
          color: ${T.muted};
        }
        #genesis-buttons {
          display: flex;
          gap: 12px;
          justify-content: center;
          margin-top: 20px;
        }
        .genesis-btn {
          padding: 12px 24px;
          border-radius: 8px;
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
          font-family: inherit;
        }
        .genesis-btn-primary {
          background: ${T.gold};
          color: ${genesisState.theme === 'KLAR' ? '#FFF' : T.bg};
          border: none;
        }
        .genesis-btn-primary:hover {
          filter: brightness(1.1);
        }
        .genesis-btn-secondary {
          background: transparent;
          color: ${T.muted};
          border: 1px solid ${T.border};
        }
        .genesis-btn-secondary:hover {
          border-color: ${T.dim};
          color: ${T.dim};
        }
        .genesis-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        #genesis-waitlist-success {
          color: ${T.green};
          font-size: 13px;
          font-weight: 600;
          display: none;
          margin-top: 12px;
        }
        #genesis-waitlist-success.visible {
          display: block;
        }
        #genesis-dragons {
          display: flex;
          justify-content: center;
          gap: 20px;
          margin: 16px 0;
          font-size: 11px;
          color: ${T.muted};
        }
        .genesis-dragon {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 4px;
        }
        .genesis-dragon-emoji {
          font-size: 20px;
        }
      </style>
      <div id="genesis-card">
        <div id="genesis-title">${L.waitlist_title}</div>
        <div id="genesis-subtitle">${L.waitlist_desc}</div>

        <div class="genesis-wave-badge">
          Wave ${waveInfo.currentWave}: ${waveInfo.currentName}
        </div>

        <div class="genesis-wave-info">
          <div class="genesis-wave-stat">
            <span class="genesis-wave-stat-value">${waveInfo.currentHumans}</span>
            <span>/ ${waveInfo.waveLimit}</span>
          </div>
          <div class="genesis-wave-stat">
            <span class="genesis-wave-stat-value">${waveInfo.nextName}</span>
            <span>${L.waitlist_next}: ${waveInfo.nextLimit}</span>
          </div>
        </div>

        <p style="font-size: 12px; color: ${T.muted}; margin: 16px 0; line-height: 1.5;">
          ${L.waitlist_status}
        </p>

        <div class="genesis-input-group">
          <label class="genesis-input-label">${L.waitlist_email}</label>
          <input type="email" id="genesis-waitlist-email" class="genesis-input" placeholder="${L.email_placeholder}">
        </div>

        <div id="genesis-waitlist-success">${L.waitlist_success}</div>

        <div id="genesis-dragons">
          <div class="genesis-dragon">
            <span class="genesis-dragon-emoji">🛡️</span>
            <span>Guardian</span>
          </div>
          <div class="genesis-dragon">
            <span class="genesis-dragon-emoji">🏗️</span>
            <span>Architect</span>
          </div>
          <div class="genesis-dragon">
            <span class="genesis-dragon-emoji">👁️</span>
            <span>Witness</span>
          </div>
        </div>

        <div id="genesis-buttons">
          <button class="genesis-btn genesis-btn-secondary" id="genesis-btn-close">${L.btn_later}</button>
          <button class="genesis-btn genesis-btn-primary" id="genesis-btn-waitlist">${L.waitlist_btn}</button>
        </div>
      </div>
    `;

    document.body.appendChild(overlayElement);
    genesisState.overlayVisible = true;

    // Bind events
    document.getElementById('genesis-btn-close').addEventListener('click', () => {
      destroyOverlay();
    });

    document.getElementById('genesis-btn-waitlist').addEventListener('click', async () => {
      const email = document.getElementById('genesis-waitlist-email').value;
      if (/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        const success = await joinWaitlist(email);
        if (success) {
          document.getElementById('genesis-waitlist-success').classList.add('visible');
          document.getElementById('genesis-btn-waitlist').disabled = true;
          setTimeout(() => destroyOverlay(), 2000);
        }
      }
    });

    // Opacity on interaction
    overlayElement.addEventListener('mouseenter', () => {
      overlayElement.style.opacity = '1';
    });
    overlayElement.addEventListener('mouseleave', () => {
      overlayElement.style.opacity = String(genesisState.opacity);
    });
  }

  function destroyOverlay() {
    if (overlayElement) {
      if (orbInstance) {
        orbInstance.stop();
        orbInstance = null;
      }
      overlayElement.remove();
      overlayElement = null;
    }
    genesisState.overlayVisible = false;
  }

  function updatePhaseUI() {
    if (!overlayElement) return;

    const L = GENESIS_LABELS[genesisState.lang] || GENESIS_LABELS.en;
    const phase = genesisState.phase;

    // Progress dots
    document.querySelectorAll('.genesis-progress-dot').forEach((dot, idx) => {
      dot.classList.remove('active', 'complete');
      if (idx + 1 < phase) dot.classList.add('complete');
      else if (idx + 1 === phase) dot.classList.add('active');
    });

    // Phase content
    const titleEl = document.getElementById('genesis-phase-title');
    const descEl = document.getElementById('genesis-phase-desc');
    const formEl = document.getElementById('genesis-form');
    const btnAction = document.getElementById('genesis-btn-action');
    const btnLater = document.getElementById('genesis-btn-later');

    if (phase === 1) {
      titleEl.textContent = L.phase1_title;
      descEl.textContent = L.phase1_desc;
      formEl.classList.add('visible');
      btnAction.textContent = L.btn_continue;
      btnLater.style.display = 'block';
    } else if (phase === 2) {
      titleEl.textContent = L.phase2_title;
      descEl.textContent = L.phase2_desc;
      formEl.classList.remove('visible');
      btnAction.textContent = L.btn_continue;
      btnAction.disabled = true;
      btnLater.style.display = 'none';
    } else if (phase === 3) {
      titleEl.textContent = L.phase3_title;
      descEl.textContent = L.phase3_desc;
      formEl.classList.remove('visible');
      btnAction.textContent = L.btn_complete;
      btnAction.disabled = false;
      btnLater.style.display = 'none';
    }

    if (orbInstance) {
      orbInstance.setPhase(phase);
    }
  }

  function showError(message) {
    const errEl = document.getElementById('genesis-error');
    if (errEl) {
      errEl.textContent = message;
      errEl.classList.add('visible');
    }
  }

  function hideError() {
    const errEl = document.getElementById('genesis-error');
    if (errEl) {
      errEl.classList.remove('visible');
    }
  }

  function showSuccess(message) {
    const succEl = document.getElementById('genesis-success');
    if (succEl) {
      succEl.textContent = message;
      succEl.classList.add('visible');
    }
  }

  function showSealStatus(message) {
    const sealEl = document.getElementById('genesis-seal-status');
    if (sealEl) {
      sealEl.textContent = message;
      sealEl.classList.add('visible');
    }
  }

  function validateEmail() {
    const email = document.getElementById('genesis-email').value;
    const valid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    const btn = document.getElementById('genesis-btn-action');
    if (btn && genesisState.phase === 1) {
      btn.disabled = !valid;
    }
    return valid;
  }

  // ── EVENT HANDLERS ───────────────────────────────────────────────────
  function handleLater() {
    genesisState.dismissed = true;
    genesisState.lastReminder = Date.now();
    saveState();
    destroyOverlay();

    // Schedule reminder
    if (genesisState.reminderCount < GENESIS_CONFIG.MAX_REMINDERS) {
      setTimeout(() => {
        if (!genesisState.walletId) {
          genesisState.reminderCount++;
          genesisState.dismissed = false;
          saveState();
          showReminder();
        }
      }, GENESIS_CONFIG.REMINDER_INTERVAL_MS);
    }
  }

  async function handleAction() {
    const L = GENESIS_LABELS[genesisState.lang] || GENESIS_LABELS.en;
    hideError();

    if (genesisState.phase === 0 || genesisState.phase === 1) {
      // Phase 1 → 2: Validate and provision
      const email = document.getElementById('genesis-email').value;
      const name = document.getElementById('genesis-name').value;

      if (!validateEmail()) {
        showError(L.error_email);
        return;
      }

      genesisState.email = email;
      genesisState.name = name;
      genesisState.phase = 2;
      updatePhaseUI();
      saveState();

      // Check if already registered
      const existing = await checkExistingWallet(email);
      if (existing && existing.wallet_id) {
        genesisState.walletId = existing.wallet_id;
        genesisState.publicKey = existing.public_key;
        showSuccess(L.already_registered);
        genesisState.phase = 3;
        updatePhaseUI();
        saveState();
        return;
      }

      // Provision new wallet
      try {
        const wallet = await provisionWallet(email, name);
        genesisState.walletId = wallet.wallet_id;
        genesisState.publicKey = wallet.public_key;
        showSuccess(L.success);

        // Retroactive seal
        if (genesisState.retroactiveHashes.length > 0) {
          showSealStatus(L.seal_retroactive);
          await retroactiveSeal(genesisState.retroactiveHashes);
          showSealStatus(L.seal_complete);
        }

        genesisState.phase = 3;
        updatePhaseUI();
        saveState();
      } catch (e) {
        showError(L.error_provision + ': ' + e.message);
        genesisState.phase = 1;
        updatePhaseUI();
      }

    } else if (genesisState.phase === 3) {
      // Complete - close overlay
      destroyOverlay();

      // Dispatch completion event
      window.dispatchEvent(new CustomEvent('genesis-complete', {
        detail: {
          walletId: genesisState.walletId,
          publicKey: genesisState.publicKey,
          email: genesisState.email,
        }
      }));
    }
  }

  // ── REMINDER SYSTEM ──────────────────────────────────────────────────
  function showReminder() {
    if (genesisState.walletId || genesisState.overlayVisible) return;

    const L = GENESIS_LABELS[genesisState.lang] || GENESIS_LABELS.en;
    const T = GENESIS_THEMES[genesisState.theme];

    let message;
    if (genesisState.reminderCount === 1) {
      message = L.reminder_gentle;
    } else if (genesisState.reminderCount === 2) {
      message = L.reminder_urgent;
    } else {
      message = L.reminder_final;
    }

    // Create toast reminder
    const toast = document.createElement('div');
    toast.id = 'genesis-reminder';
    toast.style.cssText = `
      position: fixed;
      bottom: 20px;
      right: 20px;
      background: ${T.card};
      border: 1px solid ${T.gold};
      border-radius: 12px;
      padding: 16px 20px;
      display: flex;
      align-items: center;
      gap: 12px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.15);
      z-index: 9999;
      cursor: pointer;
      animation: genesis-breathe 2s ease-in-out infinite;
      font-family: 'Bricolage Grotesque', system-ui, sans-serif;
    `;
    toast.innerHTML = `
      <span style="font-size: 24px;">🐉</span>
      <div>
        <div style="font-size: 13px; font-weight: 600; color: ${T.gold};">${message}</div>
        <div style="font-size: 11px; color: ${T.muted};">Click to continue Genesis</div>
      </div>
    `;

    toast.addEventListener('click', () => {
      toast.remove();
      showOverlay();
    });

    document.body.appendChild(toast);

    // Auto-dismiss after 10s
    setTimeout(() => {
      if (toast.parentNode) {
        toast.remove();
      }
    }, 10000);
  }

  // ── PUBLIC API ───────────────────────────────────────────────────────
  function showOverlay() {
    if (genesisState.walletId && genesisState.phase === 3) {
      // Already complete, just show completion
      genesisState.overlayVisible = true;
      createOverlay();
      return;
    }

    if (genesisState.phase === 0) {
      genesisState.phase = 1;
    }

    genesisState.overlayVisible = true;
    createOverlay();
  }

  function hideOverlay() {
    destroyOverlay();
  }

  function setTheme(themeName) {
    genesisState.theme = themeName;
    if (orbInstance) {
      orbInstance.setTheme(themeName);
    }
    // Recreate overlay if visible
    if (overlayElement) {
      destroyOverlay();
      createOverlay();
    }
  }

  function setLang(lang) {
    genesisState.lang = lang;
    // Recreate overlay if visible
    if (overlayElement) {
      destroyOverlay();
      createOverlay();
    }
  }

  function addRetroactiveHash(hash) {
    if (!genesisState.retroactiveHashes.includes(hash)) {
      genesisState.retroactiveHashes.push(hash);
      saveState();
    }
  }

  function isComplete() {
    return !!genesisState.walletId;
  }

  function getWalletInfo() {
    return {
      walletId: genesisState.walletId,
      publicKey: genesisState.publicKey,
      email: genesisState.email,
    };
  }

  // ── INITIALIZATION ───────────────────────────────────────────────────
  async function init(options = {}) {
    loadState();

    // Apply options
    if (options.theme) genesisState.theme = options.theme;
    if (options.lang) genesisState.lang = options.lang;
    if (options.autoShow === false) return;

    // Check health first
    const healthy = await checkHealth();
    if (!healthy) {
      console.warn('[Genesis] Wallet service unavailable, skipping auto-show');
      return;
    }

    // If not complete and not dismissed, show after delay
    if (!genesisState.walletId && !genesisState.dismissed) {
      setTimeout(() => {
        showOverlay();
      }, options.delay || 2000);
    }
  }

  // ── EXPOSE GLOBAL API ────────────────────────────────────────────────
  window.WINDIGenesis = {
    init,
    show: showOverlay,
    hide: hideOverlay,
    setTheme,
    setLang,
    addRetroactiveHash,
    isComplete,
    getWalletInfo,
    checkHealth,
    getState: () => ({ ...genesisState }),
    // Wave Protocol API
    getWaveInfo,
    isAtCapacity: isAtWaveCapacity,
    joinWaitlist,
    WAVE_CONFIG,
  };

  console.log('[Genesis] WINDI Genesis Onboarding v2.1 + Wave Protocol loaded');

})();
