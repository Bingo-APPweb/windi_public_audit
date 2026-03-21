/**
 * WINDI Desktop GEN 7 — Smart Zones Controller
 * "AI processes. Human decides. WINDI guarantees."
 */

// API calls go to root /api/ (nginx proxies to backend)
const API_BASE = '';

// === Tool Routes (D1→D2) ===
const TOOL_ROUTES = {
    'redaktion': '/jornal/',
    'canvas': '/app/#canvas',
    'inspektor': '/verify-public/viewer/v2.2/',
    'verify': '/verify-public/web/'
};

let _toolModeActive = false;
let _d2OriginalContent = null;

function loadToolInD2(toolName) {
    const route = TOOL_ROUTES[toolName];
    if (!route) return;

    // Open in new tab (drag events don't work in iframes)
    window.open(route, '_blank');
}

function exitToolMode() {
    if (!_toolModeActive) return;

    const d2Content = document.querySelector('#zoneD2 .zone-content');
    if (d2Content && _d2OriginalContent) {
        d2Content.innerHTML = _d2OriginalContent;
        _d2OriginalContent = null;
        _toolModeActive = false;
    }
}

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
    const inputEl = document.getElementById('oneTouchInput');
    const btnEl = document.getElementById('oneTouchBtn');
    const lang = localStorage.getItem('windi-lang') || 'en';

    // W-CIA-001 Pre-Flight Check
    const payload = {
        intent: intent?.trim() || '',
        wallet_id: window.__windiWalletId || 'desktop-gen7-session',
        agent: currentAgent,
    };
    const check = CIA.preflight('/api/onetouch/execute', payload, lang);
    if (!check.valid) {
        CIA.showPreflightError(check.error, check.field);
        return;
    }

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

async function copyCanvasToClipboard(e) {
    if (!_currentCanvasContent) return;
    try {
        await navigator.clipboard.writeText(_currentCanvasContent);
        // Fix: use event parameter or fallback to querySelector
        const btn = e?.target || document.querySelector('.canvas-toolbar button[title="Copiar"]');
        if (btn) {
            const original = btn.textContent;
            btn.textContent = '✓';
            setTimeout(() => btn.textContent = original, 1500);
        }
    } catch (err) {
        alert('Erro ao copiar: ' + err.message);
    }
}

async function sealCanvasToLedger() {
    const lang = localStorage.getItem('windi-lang') || 'en';
    const btn = document.getElementById('btnSealLedger');

    // W-CIA-001 Pre-Flight Check
    const payload = { draft_id: _currentSession?.session_id };
    const check = CIA.preflight('/api/seal', payload, lang);
    if (!check.valid) {
        CIA.showPreflightError(check.error, check.field);
        return;
    }

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

            // G4 — Trust increment após seal bem sucedido
            if (window.__windiWalletId) {
                fetch('/api/wallet/trust/event', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        wallet_id: window.__windiWalletId,
                        event_type: 'receipt_created',
                        signal: 1,
                        receipt_id: result.id || result.receipt_id || _currentSession.session_id
                    })
                })
                .then(r => r.json())
                .then(t => {
                    // Atualiza D3 com novo trust
                    const i9El = document.getElementById('govI9');
                    if (i9El && t.trust_score !== undefined) {
                        i9El.textContent = `T${t.trust_level} · ${t.trust_score}`;
                    }
                    console.log('[TRUST] Updated:', t);
                })
                .catch(err => console.log('[TRUST] Update failed (non-blocking):', err));
            }
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
    const lang = localStorage.getItem('windi-lang') || 'en';
    const btn = document.getElementById('btnExportWeb');

    // W-CIA-001 Pre-Flight Check
    const payload = { draft_id: _currentSession?.session_id };
    const check = CIA.preflight('/api/export/web', payload, lang);
    if (!check.valid) {
        CIA.showPreflightError(check.error, check.field);
        return;
    }

    if (!_currentCanvasContent) {
        CIA.showPreflightError(
            lang === 'pt' ? 'Canvas está vazio' : lang === 'de' ? 'Canvas ist leer' : 'Canvas is empty',
            'content'
        );
        return;
    }

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
    const lang = localStorage.getItem('windi-lang') || 'en';
    const btn = document.getElementById('btnPublish');

    // W-CIA-001 Pre-Flight Check
    const payload = { draft_id: _currentSession?.session_id };
    const check = CIA.preflight('/api/publish/web', payload, lang);
    if (!check.valid) {
        CIA.showPreflightError(check.error, check.field);
        return;
    }

    if (!_currentCanvasContent) {
        CIA.showPreflightError(
            lang === 'pt' ? 'Canvas está vazio' : lang === 'de' ? 'Canvas ist leer' : 'Canvas is empty',
            'content'
        );
        return;
    }

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
                <button onclick="copyCanvasToClipboard(event)" title="Copiar">📋</button>
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

// === C6: Onboard Handler ===
function handleOnboard() {
    const params = new URLSearchParams(window.location.search);
    const tier = params.get('onboard');
    if (!tier) return;

    // Store tier for post-DID flow
    sessionStorage.setItem('windi_onboard_tier', tier);

    // Clean URL without reload
    window.history.replaceState({}, '', window.location.pathname);

    console.log('[GEN7] Onboard tier:', tier);

    // Open wallet modal after short delay
    setTimeout(() => {
        if (typeof openWalletModal === 'function') {
            openWalletModal();
        }
    }, 500);
}

// === Event Listeners ===
document.addEventListener('DOMContentLoaded', () => {
    // Initialize theme and language from localStorage
    initTheme();
    initLang();

    // C6: Onboard flow — open DID modal when ?onboard= parameter present
    handleOnboard();

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
    if (e && e.target !== document.getElementById("walletModal")) return;
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
    const trustLevel = (trust !== null) ? ("T" + (Math.floor(trust/20)+1) + " · " + trust) : "--";
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

    if (!walletId) {
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
    if (!saved) return;
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

// ═══════════════════════════════════════════════════════════
// W-CIA-001 — Ecosystem Health Diagnostics
// "Observa. Regista. Propõe. Aguarda o Toque Soberano."
// ═══════════════════════════════════════════════════════════

const CIA = {
    // Services to monitor
    SERVICES: [
        { name: 'Dragon', endpoint: '/api/dragon/status', expectJson: true, critical: true },
        { name: 'OneTouch', endpoint: '/api/onetouch/execute', method: 'POST', body: '{"intent":"health","wallet_id":"cia"}', expectJson: true, critical: true },
        { name: 'Agents', endpoint: '/api/agents/status', expectJson: true, critical: true },
        { name: 'Ledger', endpoint: '/api/ledger/health', expectJson: true, critical: true },
        { name: 'Export', endpoint: '/api/export/health', expectJson: true, critical: false },
        { name: 'Dispatch', endpoint: '/api/dispatch/health', expectJson: true, critical: false },
        { name: 'Wallet', endpoint: '/api/wallet/health', expectJson: true, critical: false },
    ],

    // Routes to verify (should NOT return 301)
    ROUTES: [
        { name: 'How it Works', path: '/how-it-works/' },
        { name: 'Keys Pricing', path: '/keys/' },
        { name: 'Verify Public', path: '/verify-public/web/' },
        { name: 'Jornal Composer', path: '/jornal/' },
    ],

    state: {
        services: [],
        alerts: [],
        lastCheck: null,
        overallStatus: 'unknown'
    },

    // Check if response is JSON
    isJsonResponse(text) {
        try {
            JSON.parse(text);
            return true;
        } catch (e) {
            return false;
        }
    },

    // Check if response is HTML
    isHtmlResponse(text) {
        return text.trim().startsWith('<!DOCTYPE') || text.trim().startsWith('<html');
    },

    // Run full diagnostics
    async runDiagnostics() {
        this.state.services = [];
        this.state.alerts = [];
        this.state.lastCheck = new Date().toISOString();

        // Check services
        for (const svc of this.SERVICES) {
            const result = await this.checkService(svc);
            this.state.services.push(result);
        }

        // Check routes (should return 200, not 301)
        for (const route of this.ROUTES) {
            const result = await this.checkRoute(route);
            if (result.status !== 'ok') {
                this.state.alerts.push(result);
            }
        }

        // Calculate overall status
        const critical = this.state.services.filter(s => s.critical);
        const criticalDown = critical.filter(s => s.status === 'down').length;
        const anyWarn = this.state.services.some(s => s.status === 'warn');
        const anyAlert = this.state.alerts.length > 0;

        if (criticalDown > 0) {
            this.state.overallStatus = 'down';
        } else if (anyWarn || anyAlert) {
            this.state.overallStatus = 'warn';
        } else {
            this.state.overallStatus = 'ok';
        }

        this.updateIndicator();
        return this.state;
    },

    // Check a single service
    async checkService(svc) {
        const result = {
            name: svc.name,
            endpoint: svc.endpoint,
            critical: svc.critical,
            status: 'unknown',
            detail: '',
            latency: 0
        };

        const start = performance.now();
        try {
            const options = { method: svc.method || 'GET' };
            if (svc.method === 'POST' && svc.body) {
                options.headers = { 'Content-Type': 'application/json' };
                options.body = svc.body;
            }

            const res = await fetch(svc.endpoint, options);
            result.latency = Math.round(performance.now() - start);

            const text = await res.text();

            // Check for HTML response when expecting JSON (BUG DETECTION!)
            if (svc.expectJson && this.isHtmlResponse(text)) {
                result.status = 'down';
                result.detail = 'HTML instead of JSON — route missing?';
                this.state.alerts.push({
                    type: 'json_mismatch',
                    name: svc.name,
                    endpoint: svc.endpoint,
                    message: `${svc.name} returns HTML instead of JSON`,
                    fix: `Check nginx route for ${svc.endpoint}`
                });
            } else if (res.status === 301 || res.status === 302) {
                result.status = 'warn';
                result.detail = `Redirect ${res.status} — route may be missing`;
            } else if (res.ok) {
                result.status = 'ok';
                result.detail = `${result.latency}ms`;
            } else {
                result.status = 'warn';
                result.detail = `HTTP ${res.status}`;
            }
        } catch (e) {
            result.status = 'down';
            result.detail = e.message;
            result.latency = Math.round(performance.now() - start);
        }

        return result;
    },

    // Check a route (should return 200, not redirect)
    async checkRoute(route) {
        const result = {
            type: 'route',
            name: route.name,
            path: route.path,
            status: 'ok',
            message: ''
        };

        try {
            const res = await fetch(route.path, { redirect: 'manual' });
            
            if (res.type === 'opaqueredirect' || res.status === 301 || res.status === 302) {
                result.status = 'warn';
                result.message = `${route.name} redirects (route missing in nginx)`;
                result.fix = `Add location ${route.path} to nginx`;
            } else if (!res.ok) {
                result.status = 'warn';
                result.message = `${route.name} returns HTTP ${res.status}`;
            }
        } catch (e) {
            // Redirect detected as network error with redirect: manual
            result.status = 'warn';
            result.message = `${route.name} check failed: ${e.message}`;
        }

        return result;
    },

    // Update header indicator
    updateIndicator() {
        const dot = document.getElementById('ciaDot');
        const label = document.getElementById('ciaLabel');

        if (!dot || !label) return;

        // Label stays "CIA", dot shows status via color
        label.textContent = 'CIA';
        dot.className = 'cia-dot';

        if (this.state.overallStatus === 'ok') {
            dot.classList.add('ok');
            dot.title = 'All services healthy';
        } else if (this.state.overallStatus === 'warn') {
            dot.classList.add('warn');
            dot.title = 'Some services degraded';
        } else {
            dot.classList.add('down');
            dot.title = 'Critical services down';
        }
    },

    // Render panel content
    renderPanel() {
        const content = document.getElementById('ciaPanelContent');
        const timestamp = document.getElementById('ciaTimestamp');
        if (!content) return;

        // Services section
        let html = '<div class="cia-services">';
        for (const svc of this.state.services) {
            const statusClass = svc.status === 'ok' ? '' : svc.status;
            html += `
                <div class="cia-service ${statusClass}">
                    <div>
                        <div class="cia-service-name">${svc.name}</div>
                        <div class="cia-service-detail">${svc.endpoint}</div>
                    </div>
                    <div class="cia-service-status">${svc.detail || svc.status.toUpperCase()}</div>
                </div>
            `;
        }
        html += '</div>';

        // Alerts section
        if (this.state.alerts.length > 0) {
            html += '<div class="cia-alerts">';
            html += '<div style="font-size:11px;color:var(--gold-light);margin-bottom:8px;font-weight:600;">⚠️ Alerts Detected</div>';
            for (const alert of this.state.alerts) {
                html += `
                    <div class="cia-alert">
                        <span class="cia-alert-icon">🔴</span>
                        <div>
                            <div class="cia-alert-text">${alert.message}</div>
                            ${alert.fix ? `<div class="cia-alert-fix">→ ${alert.fix}</div>` : ''}
                        </div>
                    </div>
                `;
            }
            html += '</div>';
        }

        content.innerHTML = html;

        if (timestamp) {
            timestamp.textContent = this.state.lastCheck
                ? new Date(this.state.lastCheck).toLocaleTimeString()
                : '—';
        }
    },

    // ═══════════════════════════════════════════════════════════
    // W-CIA-001 PRE-FLIGHT CHECK — Sistema de Contenção #2
    // Valida payload ANTES de chamar backend → erro nunca chega
    // ═══════════════════════════════════════════════════════════

    CONTRACTS: {
        '/api/onetouch/execute': {
            required: ['intent'],
            fields: {
                intent: {
                    type: 'string',
                    minLength: 1,
                    error: { pt: 'Diga o que deseja criar', de: 'Was möchten Sie erstellen?', en: 'Tell me what you want to create' }
                }
            }
        },
        '/api/onetouch/seal': {
            required: ['draft_id'],
            fields: {
                draft_id: {
                    type: 'string',
                    error: { pt: 'Nenhum documento para selar', de: 'Kein Dokument zum Versiegeln', en: 'No document to seal' }
                }
            }
        },
        '/api/seal': {
            required: ['draft_id'],
            fields: {
                draft_id: {
                    type: 'string',
                    error: { pt: 'Nenhum documento para selar', de: 'Kein Dokument zum Versiegeln', en: 'No document to seal' }
                }
            }
        },
        '/api/export/web': {
            required: ['draft_id'],
            fields: {
                draft_id: {
                    type: 'string',
                    error: { pt: 'Nenhum documento para exportar', de: 'Kein Dokument zum Exportieren', en: 'No document to export' }
                }
            }
        },
        '/api/publish/web': {
            required: ['draft_id'],
            fields: {
                draft_id: {
                    type: 'string',
                    error: { pt: 'Nenhum documento para publicar', de: 'Kein Dokument zum Veröffentlichen', en: 'No document to publish' }
                }
            }
        },
        '/api/dragon/chat': {
            required: ['message'],
            fields: {
                message: {
                    type: 'string',
                    minLength: 1,
                    error: { pt: 'Mensagem não pode estar vazia', de: 'Nachricht darf nicht leer sein', en: 'Message cannot be empty' }
                }
            }
        }
    },

    /**
     * Pre-flight validation — runs BEFORE any API call
     * @param {string} endpoint - API endpoint path
     * @param {object} payload - Request payload
     * @param {string} lang - Language for error messages (de|en|pt)
     * @returns {{ valid: boolean, error?: string, field?: string }}
     */
    preflight(endpoint, payload, lang = 'en') {
        const contract = this.CONTRACTS[endpoint];
        if (!contract) {
            // No contract = passthrough (no validation)
            return { valid: true };
        }

        const required = contract.required || [];
        const fields = contract.fields || {};

        // Check required fields
        for (const fieldName of required) {
            const value = payload[fieldName];
            const fieldSchema = fields[fieldName] || {};

            // Missing or empty
            if (value === undefined || value === null || value === '') {
                const errorMsg = fieldSchema.error?.[lang] || fieldSchema.error?.en || `${fieldName} is required`;
                return { valid: false, error: errorMsg, field: fieldName };
            }

            // Type check for strings
            if (fieldSchema.type === 'string') {
                if (typeof value !== 'string') {
                    return { valid: false, error: `${fieldName} must be text`, field: fieldName };
                }
                if (fieldSchema.minLength && value.length < fieldSchema.minLength) {
                    const errorMsg = fieldSchema.error?.[lang] || fieldSchema.error?.en || `${fieldName} is too short`;
                    return { valid: false, error: errorMsg, field: fieldName };
                }
            }
        }

        return { valid: true };
    },

    /**
     * Show pre-flight error to user (toast style)
     * @param {string} error - Error message
     * @param {string} field - Field that failed
     */
    showPreflightError(error, field) {
        // Create toast if doesn't exist
        let toast = document.getElementById('cia-preflight-toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'cia-preflight-toast';
            toast.className = 'cia-preflight-toast';
            document.body.appendChild(toast);
        }

        toast.innerHTML = `
            <span class="cia-preflight-icon">⚠️</span>
            <span class="cia-preflight-msg">${error}</span>
        `;
        toast.classList.add('show');

        // Auto-hide after 4 seconds
        setTimeout(() => {
            toast.classList.remove('show');
        }, 4000);

        // Focus the problematic field if it exists
        if (field === 'intent') {
            const input = document.getElementById('oneTouchInput');
            if (input) input.focus();
        }
    }
};

// Toggle CIA panel
function toggleCiaPanel() {
    const panel = document.getElementById('ciaPanel');
    if (!panel) return;

    const isVisible = panel.style.display !== 'none';
    if (isVisible) {
        panel.style.display = 'none';
    } else {
        panel.style.display = 'block';
        CIA.renderPanel();
    }
}

// Run diagnostics and update panel
async function runCiaDiagnostics() {
    const content = document.getElementById('ciaPanelContent');
    if (content) content.innerHTML = '<div class="cia-loading">Running diagnostics...</div>';
    
    await CIA.runDiagnostics();
    CIA.renderPanel();
}

// Initialize CIA on page load
document.addEventListener('DOMContentLoaded', () => {
    // Initial check after 2 seconds (let other things load first)
    setTimeout(() => {
        CIA.runDiagnostics();
    }, 2000);

    // Periodic check every 60 seconds
    setInterval(() => {
        CIA.runDiagnostics();
    }, 60000);
});

console.log('[CIA] W-CIA-001 Health Pulse initialized');
console.log('[CIA] "Observa. Regista. Propõe. Aguarda o Toque Soberano."');
