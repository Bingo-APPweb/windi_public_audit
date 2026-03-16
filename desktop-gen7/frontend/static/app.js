/**
 * WINDI Desktop GEN 7 — Smart Zones Controller
 * "AI processes. Human decides. WINDI guarantees."
 */

// Detect base path for subfolder deployment
const API_BASE = window.location.pathname.replace(/\/$/, '');

// === i18n Translations ===
const I18N = {
    de: {
        placeholder: "Was möchten Sie erstellen?",
        hint_auto: "Auto-Routing aktiv — Dragon erkennt Absicht",
        hint_session: "Sitzung {id} erstellt — neuen Auftrag eingeben",
        d1_title: "D1 — Agenten-Korps",
        d2_title: "D2 — Souveräner Editor",
        d3_title: "D3 — Governance-Glas",
        stage: "PHASE",
        session: "SITZUNG",
        hash: "HASH",
        i9gate: "I9-TOR",
        awaiting: "Wartend",
        keys: "Schlüssel",
        constellation: "KONSTELLATION",
        canvas: "LEINWAND",
        forensics: "FORENSIK"
    },
    en: {
        placeholder: "What do you want to create?",
        hint_auto: "Auto-routing enabled — Dragon will detect intent",
        hint_session: "Session {id} created — enter new intent",
        d1_title: "D1 — Agent Corps",
        d2_title: "D2 — Sovereign Editor",
        d3_title: "D3 — Governance Glass",
        stage: "STAGE",
        session: "SESSION",
        hash: "HASH",
        i9gate: "I9 GATE",
        awaiting: "Awaiting",
        keys: "Keys",
        constellation: "CONSTELLATION",
        canvas: "CANVAS",
        forensics: "FORENSICS"
    },
    pt: {
        placeholder: "O que deseja criar?",
        hint_auto: "Roteamento automático — Dragon detecta intenção",
        hint_session: "Sessão {id} criada — novo intent ou trabalhar",
        d1_title: "D1 — Corpo de Agentes",
        d2_title: "D2 — Editor Soberano",
        d3_title: "D3 — Vidro de Governança",
        stage: "FASE",
        session: "SESSÃO",
        hash: "HASH",
        i9gate: "PORTA I9",
        awaiting: "Aguardando",
        keys: "Chaves",
        constellation: "CONSTELAÇÃO",
        canvas: "CANVAS",
        forensics: "FORENSE"
    }
};

// === Agent Name Translations ===
const AGENT_NAMES = {
    de: {
        'W-COMM-001': 'Mitteilung',
        'W-LEGAL-001': 'Justiz',
        'W-NOTARY-001': 'Notariat',
        'W-JOURN-001': 'Journalist',
        'W-AUDIT-001': 'Prüfer',
        'W-COMPLY-001': 'Compliance',
        'W-ACCT-001': 'Buchhalter',
        'GROVE-ARENA': 'Grove Arena'
    },
    en: {
        'W-COMM-001': 'Communiqué',
        'W-LEGAL-001': 'Legal',
        'W-NOTARY-001': 'Notary',
        'W-JOURN-001': 'Journalist',
        'W-AUDIT-001': 'Auditor',
        'W-COMPLY-001': 'Compliance',
        'W-ACCT-001': 'Accountant',
        'GROVE-ARENA': 'Grove Arena'
    },
    pt: {
        'W-COMM-001': 'Comunicado',
        'W-LEGAL-001': 'Jurídico',
        'W-NOTARY-001': 'Notarial',
        'W-JOURN-001': 'Jornalista',
        'W-AUDIT-001': 'Auditor',
        'W-COMPLY-001': 'Conformidade',
        'W-ACCT-001': 'Contabilista',
        'GROVE-ARENA': 'Arena Grove'
    }
};

// Get translated agent name
function getAgentName(agentId) {
    return AGENT_NAMES[currentLang]?.[agentId] || AGENT_NAMES['en']?.[agentId] || agentId;
}

let currentLang = localStorage.getItem('windi-lang') || 'en';

function setLang(lang) {
    currentLang = lang;
    localStorage.setItem('windi-lang', lang);
    applyLang();
    // Highlight active button
    document.querySelectorAll('#langSelector button').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.lang === lang);
    });
    // Reload agent names with new language
    if (typeof loadAgentCorps === 'function') {
        loadAgentCorps();
    }
}

function t(key, vars = {}) {
    let str = I18N[currentLang]?.[key] || I18N['en']?.[key] || key;
    Object.entries(vars).forEach(([k, v]) => {
        str = str.replace(`{${k}}`, v);
    });
    return str;
}

function applyLang() {
    // Update placeholder
    const input = document.getElementById('oneTouchInput');
    if (input) input.placeholder = t('placeholder');

    // Update all elements with data-i18n attribute
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.dataset.i18n;
        el.textContent = t(key);
    });
}

function initLang() {
    const savedLang = localStorage.getItem('windi-lang') || 'en';
    setLang(savedLang);
}

// === Theme Toggle (KLAR/NOIR) ===
function toggleTheme() {
    const body = document.body;
    const isNoir = body.dataset.theme !== 'klar';
    body.dataset.theme = isNoir ? 'klar' : 'noir';
    document.getElementById('themeIcon').textContent = isNoir ? '☽' : '☀';
    localStorage.setItem('windi-theme', body.dataset.theme);
}

function initTheme() {
    const savedTheme = localStorage.getItem('windi-theme') || 'noir';
    document.body.dataset.theme = savedTheme;
    const icon = document.getElementById('themeIcon');
    if (icon) {
        icon.textContent = savedTheme === 'klar' ? '☽' : '☀';
    }
}

// Agent SVG icons mapping
const AGENT_ICONS = {
    'W-COMM-001': 'communique',
    'W-LEGAL-001': 'justica',
    'W-NOTARY-001': 'notarial',
    'W-JOURN-001': 'journalist',
    'W-AUDIT-001': 'auditor',
    'W-COMPLY-001': 'compliance',
    'W-ACCT-001': 'accountant',
    'GROVE-ARENA': 'grove',
};

// SVG cache to avoid multiple fetches
const svgCache = {};

// Fetch and cache SVG content for inline rendering
async function loadSvgIcon(iconName) {
    if (svgCache[iconName]) {
        return svgCache[iconName];
    }
    try {
        const res = await fetch(`${API_BASE}/static/icons/${iconName}.svg`);
        if (res.ok) {
            const svg = await res.text();
            svgCache[iconName] = svg;
            return svg;
        }
    } catch (e) {
        console.warn(`Failed to load icon: ${iconName}`, e);
    }
    return null;
}

// Get icon HTML (placeholder, will be replaced async)
function getAgentIconPlaceholder(agentId) {
    return '<span class="agent-icon-loading">●</span>';
}

// Load and inject SVG icon into element
async function injectAgentIcon(element, agentId) {
    const iconName = AGENT_ICONS[agentId];
    if (iconName) {
        const svg = await loadSvgIcon(iconName);
        if (svg) {
            element.innerHTML = svg;
            return;
        }
    }
    element.innerHTML = '<span class="agent-icon-fallback">●</span>';
}

// State
let currentSession = null;
let currentAgent = null;

// === Dragon Pulse ===
async function checkDragonPulse() {
    const pulseEl = document.getElementById('dragonPulse');
    const dotEl = pulseEl.querySelector('.pulse-dot');
    const labelEl = pulseEl.querySelector('.pulse-label');

    try {
        const res = await fetch(`${API_BASE}/api/dragon/status`);
        const data = await res.json();

        if (data.pulse === 'ACTIVE') {
            dotEl.className = 'pulse-dot active';
            labelEl.textContent = `Dragon ${data.latency_ms?.toFixed(0) || ''}ms`;
        } else if (data.pulse === 'DEGRADED') {
            dotEl.className = 'pulse-dot degraded';
            labelEl.textContent = 'Dragon (degraded)';
        } else {
            dotEl.className = 'pulse-dot down';
            labelEl.textContent = 'Dragon (down)';
        }
    } catch (e) {
        dotEl.className = 'pulse-dot down';
        labelEl.textContent = 'Dragon (offline)';
    }
}

// === Agent Corps (D1) ===
async function loadAgentCorps() {
    const gridEl = document.getElementById('agentGrid');

    try {
        const res = await fetch(`${API_BASE}/api/agents/status`);
        const data = await res.json();

        gridEl.innerHTML = '';

        for (const [agentId, info] of Object.entries(data.agents)) {
            const card = document.createElement('div');
            card.className = 'agent-card';
            card.dataset.agentId = agentId;

            const statusClass = info.status === 'UP' || info.status === 'GREEN'
                ? ''
                : info.status === 'DEGRADED' ? 'degraded' : 'down';

            card.innerHTML = `
                <div class="agent-icon"></div>
                <div class="agent-name">${getAgentName(agentId)}</div>
                <div class="agent-status ${statusClass}"></div>
            `;

            // Inject SVG icon asynchronously
            const iconEl = card.querySelector('.agent-icon');
            injectAgentIcon(iconEl, agentId);

            card.addEventListener('click', () => selectAgent(agentId));
            gridEl.appendChild(card);
        }
    } catch (e) {
        gridEl.innerHTML = `
            <div class="agent-card">
                <div class="agent-icon">❌</div>
                <div class="agent-name">Failed to load agents</div>
            </div>
        `;
    }
}

function selectAgent(agentId) {
    // Toggle selection - click again to deselect (enable auto-routing)
    if (currentAgent === agentId) {
        currentAgent = null;
        document.querySelectorAll('.agent-card').forEach(card => {
            card.classList.remove('active');
        });
        updateHint(t('hint_auto'));
    } else {
        currentAgent = agentId;
        document.querySelectorAll('.agent-card').forEach(card => {
            card.classList.toggle('active', card.dataset.agentId === agentId);
        });
        const agentName = getAgentName(agentId);
        updateHint(`${agentName} — ${t('hint_auto').split('—')[0].trim()}`);
    }
}

function updateHint(text) {
    const hintEl = document.querySelector('.editor-hint');
    if (hintEl) {
        hintEl.textContent = text;
    }
}

// === One Touch (D2) ===
async function executeOneTouch(intent) {
    if (!intent.trim()) return;

    const inputEl = document.getElementById('oneTouchInput');
    const btnEl = document.getElementById('oneTouchBtn');

    // Disable input during request
    inputEl.disabled = true;
    btnEl.disabled = true;
    btnEl.innerHTML = '<span>⏳</span>';

    try {
        const res = await fetch(`${API_BASE}/api/onetouch/execute`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                intent: intent,
                wallet_id: 'desktop-gen7-session',
                agent: currentAgent,  // null = auto-routing by backend
            }),
        });

        const data = await res.json();

        if (res.ok) {
            currentSession = data;
            updateGovernanceGlass(data);
            showCanvas(data, intent);

            // FIX 2: Clear input but keep it visible for next intent
            inputEl.value = '';
            updateHint(`Session ${data.session_id} created — enter new intent or work in canvas`);
        } else {
            alert(`Error: ${data.detail || 'Unknown error'}`);
        }
    } catch (e) {
        alert(`Network error: ${e.message}`);
    } finally {
        inputEl.disabled = false;
        btnEl.disabled = false;
        btnEl.innerHTML = '<span>→</span>';
        inputEl.focus();
    }
}

function showCanvas(session, originalIntent) {
    const canvasEl = document.getElementById('canvasArea');
    const placeholderEl = document.querySelector('.editor-placeholder');

    // Hide input placeholder, show canvas with draft
    if (placeholderEl) placeholderEl.style.display = 'none';
    canvasEl.style.display = 'block';

    // Show routing info
    const routingInfo = currentAgent
        ? `Manual: ${currentAgent}`
        : `Auto-routed: ${session.agent}`;

    canvasEl.innerHTML = `
        <div class="canvas-session">
            <div class="canvas-header">
                <span class="canvas-badge">${session.agent}</span>
                <span class="canvas-routing">${routingInfo}</span>
            </div>
            <h3 class="canvas-title">Session: ${session.session_id}</h3>
            <p class="canvas-intent">"${originalIntent}"</p>
            <p class="canvas-message">${session.message}</p>
            <p class="canvas-next">→ ${session.next_step}</p>
        </div>
    `;
}

// === Governance Glass (D3) ===
function updateGovernanceGlass(session) {
    // FIX 3: Update all D3 fields with session data
    const stageEl = document.getElementById('govStage');
    const sessionEl = document.getElementById('govSession');
    const hashEl = document.getElementById('govHash');
    const i9El = document.getElementById('govI9');
    const actionsEl = document.getElementById('sealActions');

    if (stageEl) stageEl.textContent = session.stage || '—';
    if (sessionEl) sessionEl.textContent = session.session_id || '—';

    // Generate preview hash from session_id
    if (hashEl) {
        const previewHash = session.session_id
            ? `sha256:${session.session_id.toLowerCase()}...`
            : '—';
        hashEl.textContent = previewHash;
    }

    // FIX 3: I9 Gate status based on stage
    if (i9El) {
        const stage = session.stage || '';
        if (stage.endsWith('5')) {
            // C5, L5, N5 = ready for approval
            i9El.textContent = 'Ready for Approval';
            i9El.style.color = 'var(--gold-light)';
        } else if (stage.endsWith('6')) {
            // C6, L6, N6 = sealed
            i9El.textContent = 'SEALED (I11)';
            i9El.style.color = 'var(--status-green)';
        } else {
            // C1-C4, L1-L4, N1-N4 = in progress
            i9El.textContent = `Awaiting (${stage})`;
            i9El.style.color = 'var(--text-secondary)';
        }
    }

    // Show seal actions only at stage 5
    if (actionsEl) {
        const stage = session.stage || '';
        actionsEl.style.display = stage.endsWith('5') ? 'flex' : 'none';
    }
}

// === Event Listeners ===
document.addEventListener('DOMContentLoaded', () => {
    // Initialize theme and language from localStorage
    initTheme();
    initLang();

    // Initial load
    checkDragonPulse();
    loadAgentCorps();

    // Periodic refresh
    setInterval(checkDragonPulse, 10000);
    setInterval(loadAgentCorps, 30000);

    // One Touch input
    const inputEl = document.getElementById('oneTouchInput');
    const btnEl = document.getElementById('oneTouchBtn');

    inputEl.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            executeOneTouch(inputEl.value);
        }
    });

    btnEl.addEventListener('click', () => {
        executeOneTouch(inputEl.value);
    });

    // Seal actions
    document.getElementById('btnApprove')?.addEventListener('click', () => {
        if (currentSession) {
            alert('I9 Gate: human_approved=true\nSealing to Ledger...');
            // TODO: Implement actual seal via /bridge/publish
        }
    });

    document.getElementById('btnReject')?.addEventListener('click', () => {
        if (currentSession) {
            alert('Session rejected. Returning to draft.');
            // TODO: Implement reject flow
        }
    });

    // Initial hint (uses translation)
    updateHint(t('hint_auto'));
});

console.log('[GEN7] WINDI Desktop GEN 7 initialized');
console.log('[GEN7] "AI processes. Human decides. WINDI guarantees."');
