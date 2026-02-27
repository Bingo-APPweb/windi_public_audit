# WINDI TASK DIRECTOR v1.0
## Prompt Constitucional de Desenvolvimento Frontend
### "Cada Dragão constrói. O Humano decide. CCode entrega."

---

**Data:** 27 Fevereiro 2026
**Projecto:** WINDI A4Desk — Frontend Administrative Orchestration
**Destino:** Strato Server (windi@87.106.29.233)
**Método:** Dragon escreve código → CCode deploya no Strato
**Prazo:** Launch em 2 meses (Abril 2026)

---

## REGRAS ABSOLUTAS (INVARIANTES)

Antes de qualquer linha de código, TODOS os Dragões respeitam:

```
I1. O template NUNCA decide o nível. A API decide. O template manifesta.
I2. NUNCA separar HTML por tier. UMA Palette para TODOS os tiers.
I3. Hostname detecta tier: clone.*=L | admin.*=M | master.*=H
I4. Zero nomes de marca IA na UI (Claude/GPT/Gemini = Guardian/Architect/Witness)
I5. Segurança invisível — o humano sente fluidez, não arquitetura.
I6. Trilíngue sempre: DE (default) / EN / PT
I7. ss+ps FIRST antes de qualquer patch. Kill nohup zombies → purge __pycache__ → systemd.
I8. CCode: base64 para patches longos, NUNCA heredoc. Limpar output antes de colar.
I9. nginx: injectar ANTES de 'listen 443', NUNCA dentro de outro location. nginx -t PRIMEIRO.
```

---

## MAPA DE SERVIÇOS ACTIVOS (Estado Real 27 Fev 2026)

| Porta | Serviço | Estado | systemd |
|-------|---------|--------|---------|
| 8080 | Governance API | ✅ LIVE | nohup |
| 8085 | HUB BABEL | ✅ LIVE | nohup |
| 8099 | Wallet "O Espelho" | ✅ LIVE | σ |
| 8100 | a4Desk Desktop | ✅ LIVE | σ |
| 8101 | Forensic Ledger | ✅ LIVE | σ (18.238+ receipts) |
| 8102 | Sentinel LAW | ✅ LIVE | σ |
| 8103 | Export Engine | ✅ LIVE | σ |
| 8104 | JMPG Viewer | ✅ LIVE | σ |
| 8105 | Communiqué Engine | ✅ LIVE | σ (v1.1.0) |
| 8106 | Forensic Vault | ✅ LIVE | σ |
| 8107 | Landing P/M/G | ✅ LIVE | σ |
| 8108 | Agent Dragon Server | ✅ LIVE | σ (windi-agent-palette) |
| 8109 | Pulse | ✅ LIVE | — |
| 8112 | Orchestrator | ✅ LIVE | — |

### Cadeia de Dependência
```
Desktop(:8100) → Export(:8103) → Ledger(:8101)
Communiqué(:8105) → Ledger(:8101)
Vault(:8106) → Ledger(:8101) [read-only]
Sentinel LAW(:8102) → Ledger(:8101) [monitors]
Viewer(:8104) → Ledger(:8101) [verifies]
Wallet(:8099) → DID + Ed25519 [standalone]
```

### Palette Wiring (15 WIRED / 5 GAPS)
```
✅ WIRED: Guardian Local, Dragon Chat, I1-I9, L7, Themes,
          Trilingual, StatusBar, DID, OCR escalation,
          SealBadge, GovPanel, IdentityText, DragonProtocol

❌ GAPS:  Communiqué(:8105), Ledger(:8101), Export(:8103),
          Vault(:8106), Wallet(:8099)
```

---

## DOMÍNIOS E TIERS

| Hostname | Tier | Contrato | Perfil UX |
|----------|------|----------|-----------|
| `clone.windia4desk.tech` | L (Personal) | FREE | Minimalista, foco em escrita |
| `admin.windia4desk.tech` | M (Organization) | MED | Colaborativo, foco em gestão |
| `master.windia4desk.tech` | H (Governance) | HIGH | Analítico, foco em auditoria |

---

## ORDEM DE PRODUÇÃO (7 PRODUTOS)

A ordem é constitucional — cada produto depende do anterior.
Cada produto tem um Dragão responsável, critério de aceite, e comandos CCode.

```
P1 ──→ P2 ──→ P3 ──→ P4 ──→ P5 ──→ P6 ──→ P7
Tier   Brain  Pulse  Soul   Nerves Body   Shield
```

---

## P1: TIER DETECTOR
### Dragão Guardian — "Detecção de Identidade"

**O que é:** O primeiro script que roda no mount. Detecta hostname, define tier (L/M/H), e expõe o contrato para toda a aplicação.

**Princípio:** "O hostname é a identidade. A identidade determina o contrato."

**Ficheiro:** `/opt/windi/agent-palette/ui/modules/tier-detector.js`

**Lógica:**
```javascript
// TierDetector — Guardian Product
// Roda UMA vez no mount. Imutável durante a sessão.

function detectTier() {
  const host = window.location.hostname;

  if (host.startsWith('clone') || host === 'localhost') return 'L';
  if (host.startsWith('admin')) return 'M';
  if (host.startsWith('master')) return 'H';

  // Fallback seguro: sempre L (menor privilégio)
  return 'L';
}

function getTierContract(tier) {
  const contracts = {
    L: {
      name: 'Personal',
      maxEndpoints: 36,
      features: ['editor', 'seal', 'did', 'docx_export', 'local_search'],
      llm: { dailyTokens: 5000, dailyRequests: 50 },
      dragons: ['guardian'],
      tabs: ['chat', 'documents', 'files', 'wallet'],
      latencyClass: 'instant',
      sovereignty: 0.93
    },
    M: {
      name: 'Organization',
      maxEndpoints: 65,
      features: ['editor', 'seal', 'did', 'all_exports', 'search_api',
                 'isp', 'collaboration', 'communique', 'history'],
      llm: { dailyTokens: 50000, dailyRequests: 100 },
      dragons: ['guardian', 'architect'],
      tabs: ['chat', 'documents', 'files', 'wallet', 'search', 'products', 'journal', 'history'],
      latencyClass: 'interactive',
      sovereignty: 0.93
    },
    H: {
      name: 'Governance',
      maxEndpoints: 78,
      features: ['*'], // Tudo
      llm: { dailyTokens: 200000, dailyRequests: 500 },
      dragons: ['guardian', 'architect', 'witness'],
      tabs: ['chat', 'documents', 'files', 'wallet', 'search', 'products', 'journal', 'history'],
      governance: true,
      drawer: ['compliance', 'legal_hold', 'retentions', 'merkle', 'audit_exports', 'tribunal'],
      latencyClass: 'audit',
      sovereignty: 0.93
    }
  };
  return contracts[tier] || contracts.L;
}

// Expor globalmente para módulos sem framework
window.WINDI_TIER = detectTier();
window.WINDI_CONTRACT = getTierContract(window.WINDI_TIER);

console.log(`[WINDI] Tier: ${window.WINDI_TIER} | Contract: ${window.WINDI_CONTRACT.name} | Endpoints: ${window.WINDI_CONTRACT.maxEndpoints}`);
```

**Critério de Aceite:**
```
□ hostname clone.* → retorna L
□ hostname admin.* → retorna M
□ hostname master.* → retorna H
□ hostname desconhecido → retorna L (menor privilégio)
□ window.WINDI_TIER acessível globalmente
□ window.WINDI_CONTRACT contém features[], tabs[], llm{}
□ Imutável após mount (não muda durante sessão)
□ Console log confirma detecção
```

**CCode Deploy:**
```bash
# Verificar estado
ss -tlnp | grep 8108
ls -la /opt/windi/agent-palette/ui/modules/ 2>/dev/null || mkdir -p /opt/windi/agent-palette/ui/modules/

# Criar ficheiro (CCode gera via base64)
# base64 -d <<< "BASE64_DO_FICHEIRO" > /opt/windi/agent-palette/ui/modules/tier-detector.js

# Injectar no index.html da Palette (antes do closing </body>)
# <script src="modules/tier-detector.js"></script>

# Teste
curl -s https://admin.windia4desk.tech/palette/ | grep -c "tier-detector"
```

---

## P2: EDITOR CONTEXT + FEATURE RESOLVER
### Dragão Architect — "O Cérebro do Frontend"

**O que é:** Estado global que herda do TierDetector e governa o que cada componente pode fazer. O FeatureResolver traduz contrato em UI.

**Princípio:** "API decide. Template manifesta."

**Ficheiro:** `/opt/windi/agent-palette/ui/modules/editor-context.js`

**Estrutura:**
```javascript
// EditorContext — Architect Product
// Estado reactivo que alimenta TODOS os componentes

const EditorContext = {
  // Herdado do TierDetector
  tier: window.WINDI_TIER,
  contract: window.WINDI_CONTRACT,

  // Estado dinâmico
  role: 'anonymous',          // anonymous → user → editor → admin → compliance → gov_admin
  sovereignty: 0.93,          // Ratio de processamento local
  operationScore: 0,          // Acções realizadas na sessão
  riskScore: 0,               // R0-R5 (SGE layer)

  // Feature flags (resolvidas pelo FeatureResolver)
  features: {},

  // Políticas activas
  policies: [],

  // Idioma (trilíngue)
  lang: detectLanguage(),      // de | en | pt

  // Listeners
  _listeners: [],

  // Métodos
  set(key, value) {
    this[key] = value;
    this._listeners.forEach(fn => fn(key, value));
  },

  onChange(fn) {
    this._listeners.push(fn);
    return () => { this._listeners = this._listeners.filter(l => l !== fn); };
  },

  canAccess(feature) {
    return FeatureResolver.isEnabled(feature, this.tier, this.role);
  },

  getVisibleTabs() {
    return this.contract.tabs || [];
  },

  hasGovernanceDrawer() {
    return this.contract.governance === true;
  }
};

// FeatureResolver — "A API decide, o template manifesta"
const FeatureResolver = {
  isEnabled(feature, tier, role) {
    const contract = getTierContract(tier);

    // H tem tudo
    if (contract.features.includes('*')) return true;

    // Verificar feature no contrato
    if (!contract.features.includes(feature)) return false;

    // Verificar role mínimo para certas features
    const roleGates = {
      'compliance': ['compliance', 'gov_admin'],
      'audit_exports': ['compliance', 'gov_admin'],
      'merkle': ['admin', 'compliance', 'gov_admin'],
      'legal_hold': ['compliance', 'gov_admin'],
      'collaboration': ['editor', 'admin', 'compliance', 'gov_admin'],
      'isp': ['editor', 'admin', 'compliance', 'gov_admin']
    };

    if (roleGates[feature]) {
      return roleGates[feature].includes(role);
    }

    return true;
  },

  resolveUI(tier) {
    const ui = {
      showSovereigntyMeter: true,       // SEMPRE visível
      showSealStatus: true,             // SEMPRE visível
      showIdentityStatus: true,         // SEMPRE visível
      showReceipts: tier !== 'L',       // M + H
      showForensicMeta: tier === 'H',   // só H
      showVersionDiff: tier !== 'L',    // M + H
      showComplianceReports: tier === 'H',
      showMerkleProofs: tier === 'H',
      showAuditTrail: tier === 'H',
      showGovernanceDrawer: tier === 'H',
      showJournal: tier !== 'L',        // M + H
      showProducts: tier !== 'L',       // M + H
      showSearch: true,                 // Todos (local em L, API em M/H)
      searchMode: tier === 'L' ? 'local' : 'api'
    };
    return ui;
  }
};

function detectLanguage() {
  const stored = localStorage.getItem('windi_lang');
  if (stored) return stored;
  const nav = navigator.language.slice(0, 2);
  if (['de', 'en', 'pt'].includes(nav)) return nav;
  return 'de'; // Default: Deutsch
}

// Expor
window.WINDI_CONTEXT = EditorContext;
window.WINDI_FEATURES = FeatureResolver;
window.WINDI_UI = FeatureResolver.resolveUI(window.WINDI_TIER);
```

**Critério de Aceite:**
```
□ EditorContext herda tier/contract do P1
□ FeatureResolver bloqueia features por tier + role
□ canAccess('compliance') → false em L, false em M (sem role), true em H
□ getVisibleTabs() → 4 tabs em L, 8 tabs em M/H
□ hasGovernanceDrawer() → true só em H
□ resolveUI() retorna flags booleanas correctas por tier
□ Idioma detectado automaticamente, override manual persiste
□ onChange() notifica listeners em tempo real
```

**CCode Deploy:**
```bash
# Depende de P1 estar deployed
grep -c "tier-detector" /opt/windi/agent-palette/ui/index.html || echo "ERRO: P1 não deployed"

# base64 -d <<< "BASE64" > /opt/windi/agent-palette/ui/modules/editor-context.js

# Injectar DEPOIS do tier-detector no index.html
# <script src="modules/editor-context.js"></script>

# Teste
curl -s https://admin.windia4desk.tech/palette/ | grep -c "editor-context"
```

---

## P3: SOVEREIGNTY METER
### Dragão Witness — "O Pulso Visível da Soberania"

**O que é:** Componente visual que mostra em tempo real a % de processamento local. Sempre visível, em todos os tiers.

**Princípio:** "O humano vê transparência. O auditor vê compliance."

**Ficheiro:** `/opt/windi/agent-palette/ui/modules/sovereignty-meter.js`

**Comportamento Visual:**
```
Estado      | Cor        | Label          | Animação
≥90%        | #2D6A4F    | Sovereign      | Pulso suave verde
70-89%      | #D4A017    | Protected      | Pulso amarelo
<70%        | #C62828    | Dependent      | Alerta vermelho
```

**Estrutura:**
```javascript
// SovereigntyMeter — Witness Product
// Observa. Nunca interfere. Sempre reporta.

function createSovereigntyMeter(container) {
  const ctx = window.WINDI_CONTEXT;
  const sovereignty = ctx.sovereignty || 0.93;
  const pct = Math.round(sovereignty * 100);

  const getState = (pct) => {
    if (pct >= 90) return { color: '#2D6A4F', label: 'Sovereign', glow: '0 0 12px rgba(45,106,79,0.4)' };
    if (pct >= 70) return { color: '#D4A017', label: 'Protected', glow: '0 0 12px rgba(212,160,23,0.4)' };
    return { color: '#C62828', label: 'Dependent', glow: '0 0 12px rgba(198,40,40,0.4)' };
  };

  const state = getState(pct);

  const el = document.createElement('div');
  el.className = 'windi-sovereignty-meter';
  el.innerHTML = `
    <div class="sov-ring" style="--pct:${pct}; --color:${state.color}; --glow:${state.glow}">
      <svg viewBox="0 0 36 36" class="sov-svg">
        <path class="sov-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"/>
        <path class="sov-fill" stroke-dasharray="${pct}, 100" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"/>
      </svg>
      <div class="sov-value">${pct}%</div>
    </div>
    <div class="sov-label" style="color:${state.color}">${state.label}</div>
    <div class="sov-sublabel">Local Processing</div>
  `;

  // CSS injection
  if (!document.getElementById('sov-meter-styles')) {
    const style = document.createElement('style');
    style.id = 'sov-meter-styles';
    style.textContent = `
      .windi-sovereignty-meter {
        display: flex; flex-direction: column; align-items: center; gap: 4px;
        font-family: 'Bricolage Grotesque', sans-serif;
      }
      .sov-ring { position: relative; width: 48px; height: 48px; animation: sov-pulse 3s ease-in-out infinite; }
      .sov-svg { width: 100%; height: 100%; transform: rotate(-90deg); }
      .sov-bg { fill: none; stroke: rgba(128,128,128,0.15); stroke-width: 3; }
      .sov-fill { fill: none; stroke: var(--color); stroke-width: 3; stroke-linecap: round;
                   transition: stroke-dasharray 1.5s ease; filter: drop-shadow(var(--glow)); }
      .sov-value { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
                   font-size: 11px; font-weight: 700; font-family: 'JetBrains Mono', monospace; }
      .sov-label { font-size: 10px; font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase; }
      .sov-sublabel { font-size: 9px; opacity: 0.5; }
      @keyframes sov-pulse { 0%,100% { transform: scale(1); } 50% { transform: scale(1.03); } }

      /* Dark mode (NOIR) */
      [data-theme="noir"] .sov-value { color: #F5F0E0; }
      [data-theme="noir"] .sov-sublabel { color: rgba(245,240,224,0.5); }

      /* Light mode (KLAR) */
      [data-theme="klar"] .sov-value { color: #1A1A2E; }
      [data-theme="klar"] .sov-sublabel { color: rgba(26,26,46,0.5); }
    `;
    document.head.appendChild(style);
  }

  container.appendChild(el);

  // Live update via EditorContext
  ctx.onChange((key) => {
    if (key === 'sovereignty') {
      const newPct = Math.round(ctx.sovereignty * 100);
      const newState = getState(newPct);
      el.querySelector('.sov-fill').setAttribute('stroke-dasharray', `${newPct}, 100`);
      el.querySelector('.sov-value').textContent = `${newPct}%`;
      el.querySelector('.sov-label').textContent = newState.label;
      el.querySelector('.sov-label').style.color = newState.color;
    }
  });

  return el;
}

window.WINDI_SovereigntyMeter = createSovereigntyMeter;
```

**Critério de Aceite:**
```
□ Renderiza anel circular com % numérica
□ Verde ≥90%, Amarelo 70-89%, Vermelho <70%
□ Animação pulso suave (3s ciclo)
□ Reactivo: muda quando EditorContext.sovereignty altera
□ Funciona em NOIR (dark) e KLAR (light)
□ Fonts: Bricolage Grotesque + JetBrains Mono
□ Tamanho compacto: 48x48px anel
□ Sem dependências externas
```

---

## P4: BREATHING ORB
### Dragão Architect — "O Ritual de Selagem"

**O que é:** Animação ritual que acompanha a selagem de um documento. O Orb respira enquanto o hash é calculado, brilha quando o selo é aplicado. É o micro-ritual que transforma um acto técnico num momento de soberania.

**Princípio:** "Selo não é automação. Selo é decisão consciente."

**Ficheiro:** `/opt/windi/agent-palette/ui/modules/breathing-orb.js`

**Estados do Orb:**
```
Estado     | Visual                  | Duração   | Trigger
idle       | Orb cinza translúcido   | ∞         | Default
breathing  | Pulsação azul suave     | 2000ms    | Utilizador clica "Seal"
computing  | Rotação + shimmer       | 500-1500ms| Hash SHA-256 em cálculo
sealed     | Flash dourado + expand  | 800ms     | Hash confirmado
verified   | Verde estável + ✓       | 3000ms    | Ledger confirma receipt
error      | Vermelho + shake        | 1500ms    | Falha em qualquer passo
```

**Estrutura:**
```javascript
// BreathingOrb — Architect Product
// O momento em que o humano sela a sua decisão

function createBreathingOrb(container) {
  const el = document.createElement('div');
  el.className = 'windi-orb';
  el.setAttribute('data-state', 'idle');

  el.innerHTML = `
    <div class="orb-glow"></div>
    <div class="orb-core">
      <div class="orb-icon">◉</div>
    </div>
    <div class="orb-ring"></div>
    <div class="orb-label">Ready</div>
  `;

  if (!document.getElementById('orb-styles')) {
    const style = document.createElement('style');
    style.id = 'orb-styles';
    style.textContent = `
      .windi-orb {
        position: relative; display: flex; flex-direction: column;
        align-items: center; gap: 6px; cursor: pointer;
        font-family: 'Bricolage Grotesque', sans-serif;
      }
      .orb-core {
        width: 40px; height: 40px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        background: rgba(128,128,128,0.1); border: 2px solid rgba(128,128,128,0.2);
        transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative; z-index: 2;
      }
      .orb-icon { font-size: 16px; transition: all 0.4s; }
      .orb-glow {
        position: absolute; width: 56px; height: 56px; border-radius: 50%;
        top: -8px; left: 50%; transform: translateX(-50%);
        background: transparent; filter: blur(12px); opacity: 0;
        transition: all 0.8s; z-index: 1;
      }
      .orb-ring {
        position: absolute; width: 48px; height: 48px; border-radius: 50%;
        top: -4px; left: 50%; transform: translateX(-50%);
        border: 1px solid transparent; z-index: 0;
        transition: all 0.6s;
      }
      .orb-label {
        font-size: 9px; text-transform: uppercase; letter-spacing: 1px;
        opacity: 0.6; font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
      }

      /* BREATHING — utilizador clicou Seal */
      .windi-orb[data-state="breathing"] .orb-core {
        border-color: #4A90D9; background: rgba(74,144,217,0.1);
        animation: orb-breathe 2s ease-in-out infinite;
      }
      .windi-orb[data-state="breathing"] .orb-glow {
        opacity: 0.4; background: #4A90D9;
      }
      .windi-orb[data-state="breathing"] .orb-icon { color: #4A90D9; }

      /* COMPUTING — hash a calcular */
      .windi-orb[data-state="computing"] .orb-core {
        border-color: #C5952A; background: rgba(197,149,42,0.1);
      }
      .windi-orb[data-state="computing"] .orb-ring {
        border-color: rgba(197,149,42,0.4);
        animation: orb-spin 1s linear infinite;
      }
      .windi-orb[data-state="computing"] .orb-glow {
        opacity: 0.5; background: #C5952A;
        animation: orb-shimmer 0.8s ease-in-out infinite;
      }

      /* SEALED — hash confirmado */
      .windi-orb[data-state="sealed"] .orb-core {
        border-color: #C5952A; background: rgba(197,149,42,0.15);
        transform: scale(1.15);
      }
      .windi-orb[data-state="sealed"] .orb-glow {
        opacity: 0.7; background: #C5952A;
      }
      .windi-orb[data-state="sealed"] .orb-icon { content: '🔏'; }

      /* VERIFIED — Ledger confirma */
      .windi-orb[data-state="verified"] .orb-core {
        border-color: #2D6A4F; background: rgba(45,106,79,0.1);
      }
      .windi-orb[data-state="verified"] .orb-glow {
        opacity: 0.4; background: #2D6A4F;
      }
      .windi-orb[data-state="verified"] .orb-icon::after { content: ' ✓'; color: #2D6A4F; }

      /* ERROR */
      .windi-orb[data-state="error"] .orb-core {
        border-color: #C62828; background: rgba(198,40,40,0.1);
        animation: orb-shake 0.5s ease-in-out;
      }
      .windi-orb[data-state="error"] .orb-glow {
        opacity: 0.5; background: #C62828;
      }

      @keyframes orb-breathe { 0%,100% { transform: scale(1); } 50% { transform: scale(1.08); } }
      @keyframes orb-spin { from { transform: translateX(-50%) rotate(0deg); } to { transform: translateX(-50%) rotate(360deg); } }
      @keyframes orb-shimmer { 0%,100% { opacity: 0.3; } 50% { opacity: 0.7; } }
      @keyframes orb-shake { 0%,100% { transform: translateX(0); } 25% { transform: translateX(-4px); } 75% { transform: translateX(4px); } }

      /* Theme compatibility */
      [data-theme="noir"] .orb-label { color: rgba(245,240,224,0.6); }
      [data-theme="klar"] .orb-label { color: rgba(26,26,46,0.6); }
    `;
    document.head.appendChild(style);
  }

  container.appendChild(el);

  const labels = { idle: 'Ready', breathing: 'Sealing...', computing: 'Hashing',
                   sealed: 'Sealed', verified: 'Verified', error: 'Failed' };

  return {
    setState(state) {
      el.setAttribute('data-state', state);
      el.querySelector('.orb-label').textContent = labels[state] || state;
      if (state === 'sealed') {
        el.querySelector('.orb-icon').textContent = '🔏';
      } else if (state === 'verified') {
        el.querySelector('.orb-icon').textContent = '✓';
      } else if (state === 'error') {
        el.querySelector('.orb-icon').textContent = '✗';
      } else {
        el.querySelector('.orb-icon').textContent = '◉';
      }
    },

    // Sequência completa de selagem
    async sealSequence(hashFn, ledgerFn) {
      try {
        this.setState('breathing');
        await sleep(1500); // Ritual: deixar o humano sentir o momento

        this.setState('computing');
        const hash = await hashFn(); // SHA-256

        this.setState('sealed');
        await sleep(800); // Flash dourado

        if (ledgerFn) {
          const receipt = await ledgerFn(hash); // POST :8101
          this.setState('verified');
          await sleep(3000);
          this.setState('idle');
          return { hash, receipt };
        }

        await sleep(2000);
        this.setState('idle');
        return { hash };

      } catch (err) {
        this.setState('error');
        await sleep(1500);
        this.setState('idle');
        throw err;
      }
    }
  };
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

window.WINDI_BreathingOrb = createBreathingOrb;
```

**Critério de Aceite:**
```
□ 6 estados visuais distintos (idle→breathing→computing→sealed→verified→error)
□ Sequência breathing dura 1500ms (ritual intencional)
□ Computing mostra rotação + shimmer
□ Sealed faz flash dourado + expand
□ Verified mostra verde + ✓
□ Error faz shake
□ sealSequence() orquestra o fluxo completo
□ Funciona em NOIR e KLAR
□ Tamanho: 40x40px core
```

---

## P5: SERVICE CONNECTORS (OS 5 GAPS)
### Dragão Guardian — "O Sistema Nervoso"

**O que é:** 5 módulos que ligam a Palette aos backends LIVE. Cada connector é uma API bridge com error handling, retry, e fallback.

**Princípio:** "Backend LIVE + Frontend WIRED = Feature real."

**Ficheiro:** `/opt/windi/agent-palette/ui/modules/service-connectors.js`

**Os 5 Connectors:**

```javascript
// ServiceConnectors — Guardian Product
// Cada connector respeita o contrato do tier

const BACKENDS = {
  ledger:     { port: 8101, path: '/api', label: 'Forensic Ledger' },
  export:     { port: 8103, path: '/api', label: 'Export Engine' },
  communique: { port: 8105, path: '/api', label: 'Communiqué Engine' },
  vault:      { port: 8106, path: '/api', label: 'Forensic Vault' },
  wallet:     { port: 8099, path: '/api', label: 'Wallet O Espelho' }
};

class ServiceConnector {
  constructor(serviceKey) {
    this.config = BACKENDS[serviceKey];
    this.baseUrl = ''; // Proxy via nginx, relative URLs
    this.healthy = null;
    this.lastCheck = 0;
  }

  async healthCheck() {
    const now = Date.now();
    if (now - this.lastCheck < 30000) return this.healthy; // Cache 30s

    try {
      const res = await fetch(`${this.getBaseUrl()}/health`, {
        signal: AbortSignal.timeout(3000)
      });
      this.healthy = res.ok;
    } catch {
      this.healthy = false;
    }
    this.lastCheck = now;
    return this.healthy;
  }

  getBaseUrl() {
    // Routing via nginx proxy — paths dependem do domínio
    const paths = {
      ledger: '/suite-api',
      export: '/export',
      communique: '/communique',
      vault: '/vault',
      wallet: '/api/wallet'
    };
    return paths[Object.keys(BACKENDS).find(k => BACKENDS[k] === this.config)] || '';
  }

  async request(endpoint, options = {}) {
    // Verificar tier antes de chamar
    const tier = window.WINDI_TIER;
    const contract = window.WINDI_CONTRACT;

    // Guard: verificar se tier permite este serviço
    const tierGates = {
      communique: ['M', 'H'],
      vault: ['M', 'H'],
      export: ['L', 'M', 'H'],    // Todos exportam
      ledger: ['L', 'M', 'H'],    // Todos selam
      wallet: ['L', 'M', 'H']     // Todos têm identidade
    };

    const serviceKey = Object.keys(BACKENDS).find(k => BACKENDS[k] === this.config);
    const allowed = tierGates[serviceKey] || [];

    if (!allowed.includes(tier)) {
      return { error: 'TIER_BLOCKED', message: `${this.config.label} requires ${allowed.join('/')} tier` };
    }

    try {
      const res = await fetch(`${this.getBaseUrl()}${endpoint}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          'X-WINDI-Tier': tier,
          'X-WINDI-Lang': window.WINDI_CONTEXT?.lang || 'de',
          ...options.headers
        },
        signal: AbortSignal.timeout(options.timeout || 10000)
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();

    } catch (err) {
      console.warn(`[WINDI] ${this.config.label} error:`, err.message);
      return { error: 'SERVICE_ERROR', message: err.message };
    }
  }
}

// Instanciar os 5 connectors
const Connectors = {
  ledger: new ServiceConnector('ledger'),
  export: new ServiceConnector('export'),
  communique: new ServiceConnector('communique'),
  vault: new ServiceConnector('vault'),
  wallet: new ServiceConnector('wallet'),

  // Health check global
  async checkAll() {
    const results = {};
    for (const [key, conn] of Object.entries(this)) {
      if (conn instanceof ServiceConnector) {
        results[key] = await conn.healthCheck();
      }
    }
    return results;
  }
};

// === API DE ALTO NÍVEL ===

// Ledger: selar documento
Connectors.ledger.seal = async function(docHash, metadata) {
  return this.request('/seal', {
    method: 'POST',
    body: JSON.stringify({ hash: docHash, metadata, timestamp: new Date().toISOString() })
  });
};

// Ledger: verificar receipt
Connectors.ledger.verify = async function(receiptId) {
  return this.request(`/verify/${receiptId}`);
};

// Export: gerar PDF/DOCX
Connectors.export.generate = async function(format, content, options = {}) {
  return this.request('/generate', {
    method: 'POST',
    body: JSON.stringify({ format, content, ...options }),
    timeout: 15000 // Export pode demorar
  });
};

// Communiqué: listar artigos
Connectors.communique.listArticles = async function(limit = 20) {
  return this.request(`/articles?limit=${limit}`);
};

// Communiqué: publicar
Connectors.communique.publish = async function(articleData) {
  return this.request('/articles', {
    method: 'POST',
    body: JSON.stringify(articleData)
  });
};

// Vault: buscar evidência
Connectors.vault.getEvidence = async function(hash) {
  return this.request(`/evidence/${hash}`);
};

// Wallet: perfil DID
Connectors.wallet.getProfile = async function() {
  return this.request('/me');
};

// Wallet: Trust Radar
Connectors.wallet.getTrustScore = async function() {
  return this.request('/trust');
};

window.WINDI_Connectors = Connectors;
```

**Critério de Aceite:**
```
□ 5 connectors instanciados (ledger, export, communiqué, vault, wallet)
□ TierGate bloqueia communiqué/vault para tier L
□ Health check com cache 30s
□ Timeout de 3s para health, 10s para requests, 15s para export
□ Headers X-WINDI-Tier e X-WINDI-Lang em todas as requests
□ API de alto nível: seal(), verify(), generate(), listArticles(), publish(), getEvidence(), getProfile(), getTrustScore()
□ Error handling gracioso (retorna objecto com error, nunca crash)
□ Funciona com nginx proxy (URLs relativas)
```

**CCode Deploy (nginx routes necessárias):**
```bash
# Verificar que os backends estão LIVE
for PORT in 8099 8101 8103 8105 8106; do
  curl -s http://localhost:$PORT/health 2>/dev/null | head -1 && echo "✅ :$PORT" || echo "❌ :$PORT"
done

# Verificar nginx locations existentes
grep -E "suite-api|/export|/communique|/vault|/wallet" /etc/nginx/sites-enabled/admin.windia4desk.tech

# SEMPRE: sudo nginx -t && sudo systemctl reload nginx
```

---

## P6: LAYER MODEL (TABS + LATÊNCIA + ROLES)
### Dragão Architect — "O Corpo da Experiência"

**O que é:** O sistema de tabs que o utilizador vê, governado pelo EditorContext. Inclui as 3 camadas cognitivas (Generalist/Professional/Governance) com classes de latência.

**Princípio:** "Mesmo software. Experiência adaptativa."

**Ficheiro:** `/opt/windi/agent-palette/ui/modules/layer-model.js`

**Tabs por Tier:**
```
L (Personal):  💬Chat  📄Docs  📁Files  👛Wallet
M (Org):       💬Chat  📄Docs  📁Files  👛Wallet  🔍Search  🛒Products  📰Journal  🕐History
H (Gov):       [todos M] + 🏛️Governance Drawer
```

**Classes de Latência por Tab:**
```
Tab         | Fonte         | Latência    | Comportamento UI
Chat        | local + :8108 | <100ms      | Input local imediato
Docs        | local/API     | <100ms      | Autosave em background
Files       | :8100         | <500ms      | Lista com skeleton loader
Wallet      | :8099         | <100ms      | DID local, Trust via API
Search      | local/:8100   | <500ms      | L=FlexSearch, M/H=API com debounce 300ms
Products    | :8100         | <500ms      | Grid com lazy load
Journal     | :8105         | <3s         | Spinner + progress
History     | :8100/:8101   | <3s         | Skeleton + paginação
Gov Drawer  | :8101/:8102   | >3s         | Background load, nunca bloqueia
```

**Estrutura:**
```javascript
// LayerModel — Architect Product
// Organiza tabs por camada cognitiva, não por microserviço

function createLayerModel(sidebarContainer) {
  const ctx = window.WINDI_CONTEXT;
  const ui = window.WINDI_UI;
  const visibleTabs = ctx.getVisibleTabs();

  const TAB_CONFIG = {
    chat:      { icon: '💬', label: { de: 'Chat', en: 'Chat', pt: 'Chat' }, layer: 'generalist', latency: 'instant' },
    documents: { icon: '📄', label: { de: 'Dokumente', en: 'Documents', pt: 'Documentos' }, layer: 'generalist', latency: 'instant' },
    files:     { icon: '📁', label: { de: 'Dateien', en: 'Files', pt: 'Ficheiros' }, layer: 'generalist', latency: 'interactive' },
    wallet:    { icon: '👛', label: { de: 'Brieftasche', en: 'Wallet', pt: 'Carteira' }, layer: 'generalist', latency: 'instant' },
    search:    { icon: '🔍', label: { de: 'Suche', en: 'Search', pt: 'Busca' }, layer: 'professional', latency: 'interactive' },
    products:  { icon: '🛒', label: { de: 'Produkte', en: 'Products', pt: 'Produtos' }, layer: 'professional', latency: 'interactive' },
    journal:   { icon: '📰', label: { de: 'Journal', en: 'Journal', pt: 'Jornal' }, layer: 'professional', latency: 'process' },
    history:   { icon: '🕐', label: { de: 'Verlauf', en: 'History', pt: 'Histórico' }, layer: 'professional', latency: 'process' }
  };

  const lang = ctx.lang || 'de';

  // Construir sidebar
  const sidebar = document.createElement('nav');
  sidebar.className = 'windi-sidebar';

  let currentLayer = null;

  visibleTabs.forEach(tabKey => {
    const tab = TAB_CONFIG[tabKey];
    if (!tab) return;

    // Separador de camada
    if (tab.layer !== currentLayer) {
      currentLayer = tab.layer;
      if (currentLayer === 'professional') {
        const sep = document.createElement('div');
        sep.className = 'sidebar-separator';
        sidebar.appendChild(sep);
      }
    }

    const btn = document.createElement('button');
    btn.className = `sidebar-tab latency-${tab.latency}`;
    btn.dataset.tab = tabKey;
    btn.dataset.layer = tab.layer;
    btn.innerHTML = `
      <span class="tab-icon">${tab.icon}</span>
      <span class="tab-label">${tab.label[lang]}</span>
    `;

    btn.addEventListener('click', () => {
      sidebar.querySelectorAll('.sidebar-tab').forEach(t => t.classList.remove('active'));
      btn.classList.add('active');
      window.dispatchEvent(new CustomEvent('windi-tab-change', { detail: { tab: tabKey, layer: tab.layer, latency: tab.latency } }));
    });

    sidebar.appendChild(btn);
  });

  // Governance Drawer trigger (só H)
  if (ctx.hasGovernanceDrawer()) {
    const sep = document.createElement('div');
    sep.className = 'sidebar-separator';
    sidebar.appendChild(sep);

    const govBtn = document.createElement('button');
    govBtn.className = 'sidebar-tab sidebar-gov-trigger';
    govBtn.innerHTML = `<span class="tab-icon">🏛️</span><span class="tab-label">Governance</span>`;
    govBtn.addEventListener('click', () => {
      window.dispatchEvent(new CustomEvent('windi-governance-drawer', { detail: { open: true } }));
    });
    sidebar.appendChild(govBtn);
  }

  // CSS
  if (!document.getElementById('layer-model-styles')) {
    const style = document.createElement('style');
    style.id = 'layer-model-styles';
    style.textContent = `
      .windi-sidebar {
        display: flex; flex-direction: column; gap: 2px; padding: 8px 4px;
        font-family: 'Bricolage Grotesque', sans-serif;
      }
      .sidebar-tab {
        display: flex; align-items: center; gap: 10px;
        padding: 10px 14px; border: none; border-radius: 8px;
        cursor: pointer; background: transparent; text-align: left;
        transition: all 0.2s; font-size: 13px;
      }
      .sidebar-tab:hover { background: rgba(128,128,128,0.08); }
      .sidebar-tab.active { background: rgba(197,149,42,0.12); font-weight: 600; }
      .tab-icon { font-size: 16px; width: 24px; text-align: center; }
      .tab-label { flex: 1; }
      .sidebar-separator { height: 1px; background: rgba(128,128,128,0.12); margin: 8px 14px; }
      .sidebar-gov-trigger { border: 1px dashed rgba(197,149,42,0.3); margin-top: auto; }
      .sidebar-gov-trigger:hover { border-color: rgba(197,149,42,0.6); background: rgba(197,149,42,0.05); }

      /* Theme */
      [data-theme="noir"] .sidebar-tab { color: #F5F0E0; }
      [data-theme="klar"] .sidebar-tab { color: #1A1A2E; }
    `;
    document.head.appendChild(style);
  }

  sidebarContainer.appendChild(sidebar);

  // Activar primeira tab
  const firstTab = sidebar.querySelector('.sidebar-tab');
  if (firstTab) firstTab.click();

  return sidebar;
}

window.WINDI_LayerModel = createLayerModel;
```

**Critério de Aceite:**
```
□ L vê 4 tabs, M vê 8 tabs, H vê 8 tabs + Governance button
□ Separador visual entre Generalist e Professional layers
□ Labels trilíngues (de/en/pt)
□ Tab activa tem highlight dourado (#C5952A)
□ Governance Drawer aparece só em H com borda dashed
□ CustomEvent 'windi-tab-change' dispara com {tab, layer, latency}
□ CustomEvent 'windi-governance-drawer' dispara para H
□ Funciona em NOIR e KLAR
```

---

## P7: GOVERNANCE DRAWER
### Dragão Witness — "O Escudo de Auditoria"

**O que é:** Painel deslizante (drawer) que aparece APENAS em tier H. Contém compliance status, legal hold, retentions, merkle proofs, audit exports. NÃO é uma tab — é uma camada sobreposta.

**Princípio:** "Não polui a experiência do utilizador comum."

**Ficheiro:** `/opt/windi/agent-palette/ui/modules/governance-drawer.js`

**Conteúdo do Drawer:**
```
├── Compliance Status (I1-I9 invariants)
├── Legal Hold (documentos bloqueados)
├── Retentions (políticas de retenção)
├── Merkle Verification (inclusion proofs)
├── Audit Exports (WCAF format)
└── Tribunal Logs (decisões registadas)
```

**Estrutura:**
```javascript
// GovernanceDrawer — Witness Product
// Só observa. Só verifica. Nunca interfere.

function createGovernanceDrawer() {
  // Só tier H
  if (window.WINDI_TIER !== 'H') return null;

  const drawer = document.createElement('aside');
  drawer.className = 'windi-gov-drawer';
  drawer.setAttribute('data-open', 'false');

  drawer.innerHTML = `
    <div class="gov-drawer-overlay"></div>
    <div class="gov-drawer-panel">
      <header class="gov-header">
        <h2>🏛️ Governance</h2>
        <button class="gov-close">✕</button>
      </header>
      <div class="gov-content">
        <section class="gov-section" id="gov-compliance">
          <h3>Compliance Status</h3>
          <div class="gov-loading">Loading invariants...</div>
        </section>
        <section class="gov-section" id="gov-merkle">
          <h3>Merkle Verification</h3>
          <div class="gov-loading">Loading chain...</div>
        </section>
        <section class="gov-section" id="gov-audit">
          <h3>Audit Exports</h3>
          <div class="gov-loading">Loading exports...</div>
        </section>
      </div>
    </div>
  `;

  // CSS
  if (!document.getElementById('gov-drawer-styles')) {
    const style = document.createElement('style');
    style.id = 'gov-drawer-styles';
    style.textContent = `
      .windi-gov-drawer {
        position: fixed; inset: 0; z-index: 1000;
        pointer-events: none; opacity: 0;
        transition: opacity 0.3s;
      }
      .windi-gov-drawer[data-open="true"] {
        pointer-events: auto; opacity: 1;
      }
      .gov-drawer-overlay {
        position: absolute; inset: 0;
        background: rgba(0,0,0,0.5);
      }
      .gov-drawer-panel {
        position: absolute; right: 0; top: 0; bottom: 0;
        width: 420px; max-width: 90vw;
        background: #1A1A2E; color: #F5F0E0;
        transform: translateX(100%);
        transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        display: flex; flex-direction: column;
        font-family: 'Bricolage Grotesque', sans-serif;
      }
      .windi-gov-drawer[data-open="true"] .gov-drawer-panel {
        transform: translateX(0);
      }
      .gov-header {
        display: flex; align-items: center; justify-content: space-between;
        padding: 16px 20px; border-bottom: 1px solid rgba(197,149,42,0.2);
      }
      .gov-header h2 { font-size: 18px; font-weight: 700; margin: 0; }
      .gov-close {
        background: none; border: none; color: #F5F0E0;
        font-size: 20px; cursor: pointer; opacity: 0.6;
        transition: opacity 0.2s;
      }
      .gov-close:hover { opacity: 1; }
      .gov-content {
        flex: 1; overflow-y: auto; padding: 16px 20px;
      }
      .gov-section {
        margin-bottom: 24px;
      }
      .gov-section h3 {
        font-size: 12px; text-transform: uppercase;
        letter-spacing: 1px; color: #C5952A;
        margin-bottom: 12px; font-weight: 600;
      }
      .gov-loading {
        font-size: 12px; opacity: 0.5;
        font-family: 'JetBrains Mono', monospace;
      }

      /* Light theme */
      [data-theme="klar"] .gov-drawer-panel {
        background: #F5F0E0; color: #1A1A2E;
      }
      [data-theme="klar"] .gov-close { color: #1A1A2E; }
    `;
    document.head.appendChild(style);
  }

  // Toggle listeners
  drawer.querySelector('.gov-close').addEventListener('click', () => {
    drawer.setAttribute('data-open', 'false');
  });
  drawer.querySelector('.gov-drawer-overlay').addEventListener('click', () => {
    drawer.setAttribute('data-open', 'false');
  });

  window.addEventListener('windi-governance-drawer', (e) => {
    drawer.setAttribute('data-open', e.detail.open ? 'true' : 'false');
    if (e.detail.open) loadGovernanceData();
  });

  async function loadGovernanceData() {
    const conn = window.WINDI_Connectors;

    // Compliance via Sentinel LAW (:8102)
    try {
      const compliance = await fetch('/sentinel-law/api/compliance').then(r => r.json());
      document.getElementById('gov-compliance').innerHTML = `
        <h3>Compliance Status</h3>
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px;">
          <div>Invariants: ${compliance.invariants || '9/9'}</div>
          <div>Status: ${compliance.status || 'COMPLIANT'}</div>
        </div>
      `;
    } catch { /* skeleton stays */ }

    // Merkle via Ledger (:8101)
    try {
      const chain = await fetch('/suite-api/chain/status').then(r => r.json());
      document.getElementById('gov-merkle').innerHTML = `
        <h3>Merkle Verification</h3>
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 11px;">
          <div>Chain Height: ${chain.height || 'N/A'}</div>
          <div>Root: ${(chain.root || '').slice(0, 16)}...</div>
        </div>
      `;
    } catch { /* skeleton stays */ }

    // Audit exports placeholder
    document.getElementById('gov-audit').innerHTML = `
      <h3>Audit Exports</h3>
      <button style="background: rgba(197,149,42,0.15); border: 1px solid #C5952A; color: #C5952A; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 12px;">
        Generate WCAF Report
      </button>
    `;
  }

  document.body.appendChild(drawer);
  return drawer;
}

window.WINDI_GovernanceDrawer = createGovernanceDrawer;
```

**Critério de Aceite:**
```
□ Só renderiza em tier H
□ Abre como drawer lateral (overlay + painel)
□ Fecha ao clicar overlay ou botão ✕
□ Carrega dados em background (nunca bloqueia interface)
□ Mostra skeleton enquanto carrega
□ Conecta a Sentinel(:8102) e Ledger(:8101)
□ NÃO aparece como tab na sidebar
□ Funciona em NOIR e KLAR
```

---

## ORDEM DE DEPLOY NO STRATO

```
FASE 1 — FUNDAÇÃO (Guardian + Architect)
  mkdir -p /opt/windi/agent-palette/ui/modules/
  Deploy P1: tier-detector.js
  Deploy P2: editor-context.js
  Inject no index.html
  TESTE: abrir Palette, verificar console → WINDI_TIER + WINDI_CONTRACT

FASE 2 — ALMA VISUAL (Witness + Architect)
  Deploy P3: sovereignty-meter.js
  Deploy P4: breathing-orb.js
  Inject no index.html
  TESTE: meter visível, orb responde a estados

FASE 3 — SISTEMA NERVOSO (Guardian)
  Deploy P5: service-connectors.js
  Configurar nginx proxies (5 locations)
  sudo nginx -t && sudo systemctl reload nginx
  TESTE: Connectors.checkAll() → 5/5 healthy

FASE 4 — CORPO + ESCUDO (Architect + Witness)
  Deploy P6: layer-model.js
  Deploy P7: governance-drawer.js
  Inject no index.html
  TESTE: L=4 tabs, M=8 tabs, H=8 tabs + Governance drawer

FASE 5 — INTEGRAÇÃO FINAL
  Wiring: Seal button → BreathingOrb → Ledger
  Wiring: Tab Journal → Communiqué.listArticles()
  Wiring: Tab Wallet → Wallet.getProfile() + TrustScore
  Wiring: Export → Export.generate()
  SMOKE TEST completo nos 3 hostnames
```

---

## ATRIBUIÇÃO POR DRAGÃO

| Produto | Dragão | Razão |
|---------|--------|-------|
| P1 Tier Detector | Guardian | Segurança: menor privilégio, detecção de identidade |
| P2 Editor Context | Architect | Estrutura: estado global, resolução de features |
| P3 Sovereignty Meter | Witness | Observação: reporta sem interferir |
| P4 Breathing Orb | Architect | Construção: ritual de selagem, UX emocional |
| P5 Service Connectors | Guardian | Segurança: tier gates, error handling, timeouts |
| P6 Layer Model | Architect | Estrutura: tabs, camadas cognitivas, latência |
| P7 Governance Drawer | Witness | Verificação: compliance, merkle, audit |

---

## DESIGN SYSTEM TOKENS

```
CORES:
  Gold:       #C5952A (acento principal, seal, active states)
  Dark:       #1A1A2E (texto NOIR)
  Pergaminho: #F5F0E0 (fundo KLAR)
  Sovereign:  #2D6A4F (verde, ≥90%)
  Protected:  #D4A017 (amarelo, 70-89%)
  Dependent:  #C62828 (vermelho, <70%)

FONTS:
  Display:    'Bricolage Grotesque' (títulos, labels)
  Mono:       'JetBrains Mono' (hashes, valores, código)

THEMES:
  KLAR:  data-theme="klar"  (default, #F5F0E0 pergaminho)
  NOIR:  data-theme="noir"  (dark mode, #1A1A2E)

ANIMAÇÕES:
  Pulso suave:  3s ease-in-out infinite
  Ritual selo:  1500ms breathing + 800ms flash + 3000ms verified
  Transição UI: 0.2s ease (hover, active)
  Shimmer:      0.8s ease-in-out (computing)
```

---

## PROMPT PARA CCODE

Quando usar CCode para deployar cada produto, o prompt base é:

```
TAREFA: Deploy [P_NUMBER] [PRODUCT_NAME] no Strato

CONTEXTO:
- Server: windi@87.106.29.233
- Directório: /opt/windi/agent-palette/ui/modules/
- Estado: P1-P[N-1] já deployed

REGRAS:
1. ss -tlnp | grep 8108 PRIMEIRO (confirmar Dragon UP)
2. Backup: cp index.html index.html.$(date +%Y%m%d_%H%M).bak
3. Criar ficheiro via base64 (NUNCA heredoc para >50 linhas)
4. Injectar <script> no index.html ANTES do </body>
5. Ordem: tier-detector → editor-context → sovereignty-meter → breathing-orb → service-connectors → layer-model → governance-drawer
6. Testar: curl + browser confirm
7. NUNCA modificar ficheiros dos produtos anteriores

CÓDIGO:
[conteúdo do ficheiro JS do produto]

DEPLOY:
[comandos bash específicos]

VERIFICAÇÃO:
[critérios de aceite do produto]
```

---

**Assinatura:**
```
WINDI Task Director v1.0
27 Fevereiro 2026
"Cada Dragão constrói. O Humano decide. CCode entrega."
Sovereignty: ~93% Local
Three Dragons Protocol: Guardian · Architect · Witness
```
