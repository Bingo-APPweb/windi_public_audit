// ═══════════════════════════════════════════════════════════════════════
// WINDI PALETTE CORE v1.0.0 — Shared Foundation
// "AI processes. Human decides. WINDI guarantees."
// ═══════════════════════════════════════════════════════════════════════

(function() {
  'use strict';

  // ═══════════════════════════════════════════════════════════════════════
  // TENANT PROFILE (Multi-tenant Foundation)
  // ═══════════════════════════════════════════════════════════════════════

  const DEFAULT_TENANT_PROFILE = {
    tenant_id: "windi",
    tenant_name: "WINDI",
    locale: (document.documentElement.lang || navigator.language || "en").replace("_", "-"),
    tone: "professional",
    theme: "klar",
    compliance_pack: ["GDPR", "EU_AI_ACT"],
    retention_policy: "30d",
    regulatory_mode: false,
    isp: {
      vocabulary: {},
      signature_block: {
        en: "AI processes. Human decides. WINDI guarantees.",
        de: "KI verarbeitet. Mensch entscheidet. WINDI garantiert.",
        pt: "IA processa. Humano decide. WINDI garante."
      }
    }
  };

  function loadTenantProfile() {
    try {
      if (window.WINDI_TENANT_PROFILE) return { ...DEFAULT_TENANT_PROFILE, ...window.WINDI_TENANT_PROFILE };
      const raw = localStorage.getItem("windi_tenant_profile");
      if (raw) return { ...DEFAULT_TENANT_PROFILE, ...JSON.parse(raw) };
    } catch (e) { console.warn('[Tenant] Load error:', e); }
    return DEFAULT_TENANT_PROFILE;
  }

  function saveTenantProfile(profile) {
    try { localStorage.setItem("windi_tenant_profile", JSON.stringify(profile)); } catch (e) {}
  }

  const Tenant = {
    profile: loadTenantProfile(),
    setProfile(p) {
      this.profile = { ...DEFAULT_TENANT_PROFILE, ...p };
      saveTenantProfile(this.profile);
      if (window.WINDI_onTenantChange) window.WINDI_onTenantChange(this.profile);
    },
    getEnvelope() {
      const p = this.profile;
      return {
        tenant_id: p.tenant_id,
        locale: p.locale,
        tone: p.tone,
        theme: p.theme,
        compliance_pack: p.compliance_pack,
        regulatory_mode: p.regulatory_mode
      };
    }
  };

  // ═══════════════════════════════════════════════════════════════════════
  // CIRCUIT BREAKER (Resilience)
  // ═══════════════════════════════════════════════════════════════════════

  const CircuitBreaker = {
    failures: 0,
    openUntil: 0,
    lastError: null,
    THRESHOLD: 3,
    TIMEOUT: 60000,

    isOpen() { return Date.now() < this.openUntil; },
    recordSuccess() { this.failures = 0; this.openUntil = 0; this.lastError = null; },
    recordFailure(err) {
      this.failures += 1;
      this.lastError = (err && err.message) ? err.message : String(err || "error");
      if (this.failures >= this.THRESHOLD) {
        this.openUntil = Date.now() + this.TIMEOUT;
        console.warn('[CircuitBreaker] OPEN — resilient mode for 60s');
      }
    },
    modeLabel() { return this.isOpen() ? "RESILIENT" : "ONLINE"; },
    status() {
      return {
        mode: this.modeLabel(),
        failures: this.failures,
        lastError: this.lastError,
        openUntil: this.openUntil > 0 ? new Date(this.openUntil).toISOString() : null
      };
    }
  };

  // ═══════════════════════════════════════════════════════════════════════
  // LANGUAGE DETECTION
  // ═══════════════════════════════════════════════════════════════════════

  const LANG = {
    de: ["der","die","das","und","ist","für","mit","ein","eine","nicht","auf","als","auch","von","ich","wir","sie","er","es","an","bei","nach","über","vor","durch","um","zwischen","unter","können","werden","wurde","sein","haben","wird","aus","oder","aber","zu","im","am","dem","den","des","wie","nur","so","noch","mehr","wenn","hier","bitte","danke","schreib","erstell","erstelle","mach","brief","dokument","bericht","schreiben","verfasse","formuliere","brauche","schick","rechnung","vertrag","memo","protokoll","präsentation","analyse","vorlage"],
    en: ["the","is","are","and","for","with","this","that","from","have","has","was","were","been","will","would","could","should","can","may","must","what","when","where","which","who","how","why","not","but","if","then","than","more","some","any","all","each","every","most","other","into","over","after","before","between","through","during","please","thank","thanks","write","create","make","letter","document","report","contract","invoice","memo","presentation","analysis","draft","send"],
    pt: ["o","a","os","as","de","da","do","em","na","no","para","com","por","que","um","uma","dos","das","seu","sua","seus","suas","este","esta","isso","aqui","onde","quando","porque","como","mais","muito","também","já","ainda","só","sobre","entre","depois","antes","através","durante","obrigado","obrigada","por favor","escreve","cria","faz","carta","documento","relatório","contrato","fatura","memo","apresentação","análise","rascunho","envia","preciso","quero","gostaria","poderia","comuniqué","comunicado"]
  };

  const LANG_AMBIGUOUS = ["a","o","i","e","no","um","me","to","so","do","in","on","an","as","is","or","de","se","la","le","lo"];

  function detectLang(text) {
    const t = text.toLowerCase();
    const words = t.split(/\s+/).filter(w => w.length > 0);
    let scores = { de:0, en:0, pt:0 };
    words.forEach(w => {
      if (LANG_AMBIGUOUS.includes(w)) return;
      for (const [l, markers] of Object.entries(LANG)) {
        if (markers.includes(w)) {
          const idx = markers.indexOf(w);
          scores[l] += (idx < 15 ? 1.5 : 1);
        }
      }
    });
    const sorted = Object.entries(scores).sort((a,b) => b[1] - a[1]);
    return sorted[0][1] > 0 ? sorted[0][0] : null;
  }

  // ═══════════════════════════════════════════════════════════════════════
  // WINDI SOUL (Personality)
  // ═══════════════════════════════════════════════════════════════════════

  const WINDI_SOUL = {
    identity: {
      de: `🐉 Ich bin der **WINDI Agent** — dein Governance-Begleiter.\n\nWINDI: „KI verarbeitet. Mensch entscheidet. WINDI garantiert."`,
      en: `🐉 I'm the **WINDI Agent** — your governance companion.\n\nWINDI: "AI processes. Human decides. WINDI guarantees."`,
      pt: `🐉 Eu sou o **WINDI Agent** — teu companheiro de governança.\n\nWINDI: "IA processa. Humano decide. WINDI garante."`
    },
    greetings: {
      de: ["Hey! 🐉 Wie kann ich dir helfen?", "Servus! 🐉 Was steht an?"],
      en: ["Hey! 🐉 How can I help you?", "Hello! 🐉 What can I do for you?"],
      pt: ["E aí! 🐉 No que posso ajudar?", "Fala! 🐉 O que precisas?"]
    },
    thanks: {
      de: ["Gerne! 🐉", "Kein Ding!"],
      en: ["You're welcome! 🐉", "Anytime!"],
      pt: ["Valeu! 🐉", "Tranquilo!"]
    }
  };

  function chatRespond(chatType, lang) {
    const L = lang || "de";
    const pick = arr => arr[Math.floor(Math.random() * arr.length)];
    switch (chatType) {
      case "greeting": return pick(WINDI_SOUL.greetings[L] || WINDI_SOUL.greetings.de);
      case "identity": return WINDI_SOUL.identity[L] || WINDI_SOUL.identity.de;
      case "thanks": return pick(WINDI_SOUL.thanks[L] || WINDI_SOUL.thanks.de);
      default: return pick(WINDI_SOUL.greetings[L] || WINDI_SOUL.greetings.de);
    }
  }

  // ═══════════════════════════════════════════════════════════════════════
  // DRAGON API CLIENT
  // ═══════════════════════════════════════════════════════════════════════

  const DRAGON_API = '/api/dragon';

  async function dragonChat(message, opts = {}) {
    try {
      const resp = await fetch(DRAGON_API + '/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          tier: opts.tier || 'HIGH',
          chatType: opts.chatType || null,
          intentMode: opts.intentMode || 'chat',
          language: opts.language || 'de',
          history: opts.history || [],
          tenant_id: Tenant.profile.tenant_id
        }),
      });
      if (!resp.ok) throw new Error('API ' + resp.status);
      CircuitBreaker.recordSuccess();
      return await resp.json();
    } catch (err) {
      CircuitBreaker.recordFailure(err);
      console.error('[DragonChat] Error:', err);
      return null;
    }
  }

  async function dragonHealth() {
    try {
      const resp = await fetch(DRAGON_API + '/health');
      return await resp.json();
    } catch (err) {
      return { status: 'unreachable', error: err.message };
    }
  }

  // ═══════════════════════════════════════════════════════════════════════
  // EXPOSE TO GLOBAL
  // ═══════════════════════════════════════════════════════════════════════

  window.WINDI_Core = {
    version: '1.0.0',
    Tenant,
    CircuitBreaker,
    detectLang,
    chatRespond,
    WINDI_SOUL,
    dragonChat,
    dragonHealth
  };

  window.WINDI_Tenant = Tenant;

})();
