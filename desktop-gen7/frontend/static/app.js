/**
 * WINDI Desktop GEN 7 — Smart Zones Controller
 * "AI processes. Human decides. WINDI guarantees."
 */

// API calls go to root /api/ (nginx proxies to backend)
const API_BASE = '';

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
        forensics: "FORENSIK",
        navHow: "So funktioniert es"
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
        forensics: "FORENSICS",
        navHow: "How it Works"
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
        forensics: "FORENSE",
        navHow: "Como Funciona"
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
        const res = await fetch(`static/icons/${iconName}.svg`);
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
                wallet_id: window.__windiWalletId || 'desktop-gen7-session',
                agent: currentAgent,  // null = auto-routing by backend
            }),
        });

        const data = await res.json();
        console.log('[WINDI Debug] API Response:', data);
        console.log('[WINDI Debug] res.ok:', res.ok, 'message length:', data.message?.length);

        if (res.ok) {
            currentSession = data;
            updateGovernanceGlass(data);
            console.log('[WINDI Debug] Calling showCanvas with session_id:', data.session_id);
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

// === Canvas Actions ===
let _currentCanvasContent = '';
let _currentSession = null;

function downloadCanvasOutput() {
    if (!_currentCanvasContent) return;
    const isSvg = _currentCanvasContent.includes('<svg');
    const ext = isSvg ? 'svg' : 'html';
    const mime = isSvg ? 'image/svg+xml' : 'text/html';
    const blob = new Blob([_currentCanvasContent], {type: mime});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `windi-${_currentSession?.session_id || Date.now()}.${ext}`;
    a.click();
    URL.revokeObjectURL(a.href);
}

async function copyCanvasToClipboard() {
    if (!_currentCanvasContent) return;
    try {
        await navigator.clipboard.writeText(_currentCanvasContent);
        const btn = event.target;
        const original = btn.textContent;
        btn.textContent = '✓';
        setTimeout(() => btn.textContent = original, 1500);
    } catch (e) {
        alert('Erro ao copiar: ' + e.message);
    }
}

async function sealCanvasToLedger() {
    if (!_currentSession) return;
    const btn = document.getElementById('btnSealLedger');
    if (btn) { btn.disabled = true; btn.textContent = '⏳'; }
    try {
        const encoder = new TextEncoder();
        const data = encoder.encode(_currentCanvasContent);
        const hashBuffer = await crypto.subtle.digest('SHA-256', data);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        const contentHash = hashArray.map(b => b.toString(16).padStart(2,'0')).join('');

        const res = await fetch(`${API_BASE}/api/seal`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                session_id: _currentSession.session_id,
                content_hash: contentHash,
                doc_type: 'canvas-output',
                wallet_id: window.__windiWalletId || null,
                human_fingerprint: window.__windiWallet?.fingerprint || null
            })
        });
        const result = await res.json();
        if (res.ok) {
            if (btn) btn.textContent = '✓';
            alert(`Selado no Ledger!\nReceipt: ${result.id || result.receipt_id || _currentSession.session_id}`);
        } else {
            if (btn) btn.textContent = '✗';
            alert('Erro ao selar: ' + (result.detail || result.error));
        }
    } catch (e) {
        if (btn) btn.textContent = '✗';
        alert('Erro: ' + e.message);
    } finally {
        setTimeout(() => { if (btn) { btn.disabled = false; btn.textContent = '🔏'; } }, 2000);
    }
}

async function exportWebStandalone() {
    if (!_currentSession || !_currentCanvasContent) return;
    const btn = document.getElementById('btnExportWeb');
    if (btn) { btn.disabled = true; btn.textContent = '⏳'; }
    try {
        const res = await fetch(`${API_BASE}/api/export/web`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                session_id: _currentSession.session_id,
                html_content: _currentCanvasContent,
                sub_type: 'micro_page'
            })
        });
        const result = await res.json();
        if (res.ok) {
            // Download the standalone HTML
            const blob = new Blob([result.html], {type: 'text/html;charset=utf-8'});
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = `${_currentSession.session_id}.html`;
            a.click();
            URL.revokeObjectURL(a.href);
            if (btn) btn.textContent = '✓';
            alert(`Gravado + Selado!\nReceipt: ${result.receipt_id}\nHash: ${result.content_hash.slice(0,16)}...`);
        } else {
            if (btn) btn.textContent = '✗';
            alert('Erro: ' + (result.detail || result.error));
        }
    } catch (e) {
        if (btn) btn.textContent = '✗';
        alert('Erro: ' + e.message);
    } finally {
        setTimeout(() => { if (btn) { btn.disabled = false; btn.textContent = '💾'; } }, 2000);
    }
}

// P4A+P4D: Publish to WINDI Hosting + WhatsApp share
let _lastPublishResult = null;

async function publishToWINDI() {
    if (!_currentSession || !_currentCanvasContent) return;
    const btn = document.getElementById('btnPublish');
    if (btn) { btn.disabled = true; btn.textContent = '⏳'; }
    try {
        // Extract title from content (first h1 or h2)
        const titleMatch = _currentCanvasContent.match(/<h[12][^>]*>([^<]+)<\/h[12]>/i);
        const title = titleMatch ? titleMatch[1].trim() : 'WINDI Document';

        // Extract description (first paragraph)
        const descMatch = _currentCanvasContent.match(/<p[^>]*>([^<]{20,150})/i);
        const description = descMatch ? descMatch[1].trim() + '...' : 'Verified content by WINDI Publishing House';

        const res = await fetch(`${API_BASE}/api/publish/web`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                session_id: _currentSession.session_id,
                html_content: _currentCanvasContent,
                title: title,
                description: description,
                sub_type: 'micro_page'
            })
        });
        const result = await res.json();
        if (res.ok) {
            _lastPublishResult = result;
            if (btn) btn.textContent = '✓';
            // Show WhatsApp button
            const waBtn = document.getElementById('btnWhatsApp');
            if (waBtn) waBtn.style.display = 'inline-block';
            alert(`Publicado!\n\nURL: ${result.short_url}\nReceipt: ${result.receipt_id}`);
        } else {
            if (btn) btn.textContent = '✗';
            alert('Erro: ' + (result.detail || result.error));
        }
    } catch (e) {
        if (btn) btn.textContent = '✗';
        alert('Erro: ' + e.message);
    } finally {
        setTimeout(() => { if (btn) { btn.disabled = false; btn.textContent = '📡'; } }, 2000);
    }
}

function shareOnWhatsApp() {
    if (!_lastPublishResult) {
        alert('Publica primeiro com 📡');
        return;
    }
    window.open(_lastPublishResult.whatsapp_url, '_blank');
}

function showCanvas(session, originalIntent) {
    console.log('[WINDI Debug] showCanvas called');
    const canvasEl = document.getElementById('canvasArea');
    const placeholderEl = document.querySelector('.editor-placeholder');
    console.log('[WINDI Debug] canvasEl:', canvasEl ? 'found' : 'NOT FOUND');
    console.log('[WINDI Debug] session.message preview:', session.message?.substring(0, 100));

    // Store for actions
    _currentCanvasContent = session.message;
    _currentSession = session;

    // Hide input placeholder, show canvas with draft
    if (placeholderEl) placeholderEl.style.display = 'none';
    canvasEl.style.display = 'block';
    console.log('[WINDI Debug] Canvas display set to block');

    // Header compacto + HTML directo do Dragon + Action buttons
    canvasEl.innerHTML = `
        <div class="canvas-toolbar">
            <span class="canvas-badge">${session.agent}</span>
            <span class="canvas-session-id">${session.session_id}</span>
            <span class="canvas-stage">${session.stage}</span>
            <div class="canvas-toolbar-actions">
                <button onclick="downloadCanvasOutput()" title="Download">⬇</button>
                <button onclick="copyCanvasToClipboard()" title="Copiar">📋</button>
                <button id="btnExportWeb" onclick="exportWebStandalone()" title="Gravar HTML">💾</button>
                <button id="btnPublish" onclick="publishToWINDI()" title="Publicar no WINDI">📡</button>
                <button id="btnWhatsApp" onclick="shareOnWhatsApp()" title="WhatsApp" style="display:none">📲</button>
                <button id="btnSealLedger" onclick="sealCanvasToLedger()" title="Selar no Ledger">🔏</button>
            </div>
        </div>
        <div class="canvas-document">
            ${session.message || '<div style="color:red;padding:20px;">⚠️ DEBUG: session.message está vazio. Keys recebidas: ' + Object.keys(session).join(', ') + '</div>'}
        </div>
        <div class="canvas-actions">
            <span class="canvas-next">→ ${session.next_step}</span>
        </div>
    `;
    console.log('[WINDI Debug] Canvas innerHTML set, document length:', document.querySelector('.canvas-document')?.innerHTML?.length);
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


// ═══════════════════════════════════════════
// DID WALLET MODAL — WINDI GEN7 — FASE 1
// ═══════════════════════════════════════════

const WM = {
    SESSION_KEY: "windi_desktop_wallet",
    get() {
        try { return JSON.parse(sessionStorage.getItem(this.SESSION_KEY)); }
        catch(e) { return null; }
    },
    set(data) {
        sessionStorage.setItem(this.SESSION_KEY, JSON.stringify(data));
        window.__windiWallet = data;
    },
    clear() {
        sessionStorage.removeItem(this.SESSION_KEY);
        window.__windiWallet = null;
    }
};

function openWalletModal() {
    document.getElementById("walletModal").classList.add("open");
    WM.get() ? renderWalletLoaded(WM.get()) : renderWalletLogin();
}

function closeWalletModal(e) {
    if (e && e.target \!== document.getElementById("walletModal")) return;
    document.getElementById("walletModal").classList.remove("open");
}

document.addEventListener("keydown", e => {
    if (e.key === "Escape")
        document.getElementById("walletModal")?.classList.remove("open");
});

function renderWalletLogin() {
    document.getElementById("wm-state-login").style.display  = "";
    document.getElementById("wm-state-loaded").style.display = "none";
    document.getElementById("wm-seal-badge").style.display   = "none";
    document.getElementById("wm-login-status").textContent   = "";
    const btn = document.getElementById("walletBtn");
    if (btn) {
        btn.classList.remove("has-did");
        document.getElementById("walletBtnLabel").textContent = "Wallet";
    }
}

function renderWalletLoaded(wallet) {
    document.getElementById("wm-state-login").style.display  = "none";
    document.getElementById("wm-state-loaded").style.display = "";
    document.getElementById("wm-seal-badge").style.display   = "";

    document.getElementById("wm-did-value").textContent =
        wallet.wallet_id || wallet.id || "--";

    const sub = [
        wallet.display_name || wallet.name,
        wallet.context_type || wallet.kind || wallet.type,
        wallet.role
    ].filter(Boolean).join(" · ");
    document.getElementById("wm-did-sub").textContent = sub;

    document.getElementById("wm-tier").textContent =
        wallet.governance_level || wallet.tier || "L1";

    const trust = wallet.trust?.score ?? wallet.trust_score ?? wallet.trustScore ?? null;
    const trustLevel = (trust \!== null) ? ("T" + (Math.floor(trust/20)+1) + " · " + trust) : "--";
    document.getElementById("wm-trust").textContent = trustLevel;

    document.getElementById("wm-pioneer").textContent =
        wallet.pioneer_number ? ("#" + wallet.pioneer_number) : "--";

    document.getElementById("wm-fingerprint").textContent =
        wallet.fingerprint
            ? wallet.fingerprint.substring(0, 48) + "..."
            : "--";

    const btn = document.getElementById("walletBtn");
    const wid = wallet.wallet_id || wallet.id || "";
    if (btn) {
        btn.classList.add("has-did");
        document.getElementById("walletBtnLabel").textContent =
            wid.length > 12 ? wid.substring(0, 16) + "..." : wid;
    }
}

async function walletLogin() {
    const input    = document.getElementById("wm-login-input");
    const status   = document.getElementById("wm-login-status");
    const walletId = input?.value?.trim();

    if (\!walletId) {
        status.textContent = "Introduz o teu Wallet ID";
        status.className   = "wm-sign-status err";
        return;
    }

    status.textContent = "A verificar identidade...";
    status.className   = "wm-sign-status";

    try {
        const res  = await fetch("/api/wallet/me?wallet_id=" + encodeURIComponent(walletId));
        const data = await res.json();

        if (res.ok && (data.wallet_id || data.human_id)) {
            WM.set(data);
            window.__windiWalletId = data.wallet_id || walletId;
            renderWalletLoaded(data);
            console.log("[WALLET] Login successful:", data.wallet_id || walletId);
        } else {
            status.textContent = data.detail || data.error || "Wallet nao encontrada";
            status.className   = "wm-sign-status err";
        }
    } catch(e) {
        console.error("[WALLET] Login error:", e);
        status.textContent = "Wallet Service inacessivel (:8099)";
        status.className   = "wm-sign-status err";
    }
}

function walletLogout() {
    WM.clear();
    window.__windiWalletId = null;
    renderWalletLogin();
    console.log("[WALLET] Logged out");
}

(function initWalletModal() {
    const saved = WM.get();
    if (\!saved) return;
    window.__windiWallet   = saved;
    window.__windiWalletId = saved.wallet_id || saved.id;
    const btn = document.getElementById("walletBtn");
    const wid = saved.wallet_id || saved.id || "";
    if (btn) {
        btn.classList.add("has-did");
        document.getElementById("walletBtnLabel").textContent =
            wid.length > 12 ? wid.substring(0, 16) + "..." : wid;
    }
    console.log("[WALLET] Session restored:", wid);
})();

console.log("[GEN7] DID Wallet Modal initialized — FASE 1");
