/**
 * W-UDB-001 — WINDI Unified Dashboard
 * Real-time monitoring with SSE
 * Liga IA+H · Kempten, Bavaria · 2026
 */

// ═══════════════════════════════════════════════════════════════
// I18N — Trilingual Support (DE | EN | PT)
// ═══════════════════════════════════════════════════════════════

const I18N = {
    de: {
        zone_a_name: "FORENSISCHES HUB",
        zone_b_name: "MASSEN-PULS",
        zone_c_name: "LEDGER-INTEGRITÄT",
        seals: "Siegel",
        renders: "Renders",
        last_seal: "Letztes Siegel:",
        queue: "Warteschlange:",
        exceptions: "Ausnahmen:",
        integrity: "Integrität:",
        exceptions_kpi: "Ausnahmen:",
        sovereignty: "Souveränität:",
        kill_switch: "NOTSCHALTER",
        generate_manifest: "TÄGLICHES MANIFEST ERSTELLEN",
        kill_confirm_title: "Notschalter bestätigen",
        kill_confirm_msg: "Dies wird ALLE VD-MASS-Policies sofort aussetzen.",
        reason: "Grund:",
        cancel: "Abbrechen",
        confirm_halt: "HALT BESTÄTIGEN",
        connecting: "Verbindung...",
        connected: "LIVE",
        error: "FEHLER",
        online: "ONLINE",
        down: "OFFLINE",
        loading: "LADEN",
        new_collage: "NEUE COLLAGE",
        create_collage: "Souveräne Collage erstellen",
        collage_desc: "Wählen Sie zwei VD-CUT-Quellen für den forensischen Vergleich.",
        momento_a: "MOMENT A (Links)",
        momento_b: "MOMENT B (Rechts)",
        render_status: "Render-Status:",
        create_and_render: "ERSTELLEN & RENDERN"
    },
    en: {
        zone_a_name: "FORENSIC HUB",
        zone_b_name: "MASS PULSE",
        zone_c_name: "LEDGER INTEGRITY",
        seals: "seals",
        renders: "renders",
        last_seal: "Last seal:",
        queue: "Queue:",
        exceptions: "Exceptions:",
        integrity: "Integrity:",
        exceptions_kpi: "Exceptions:",
        sovereignty: "Sovereignty:",
        kill_switch: "KILL SWITCH",
        generate_manifest: "GENERATE DAILY MANIFEST",
        kill_confirm_title: "Confirm Kill Switch",
        kill_confirm_msg: "This will suspend ALL VD-MASS policies immediately.",
        reason: "Reason:",
        cancel: "Cancel",
        confirm_halt: "CONFIRM HALT",
        connecting: "Connecting...",
        connected: "LIVE",
        error: "ERROR",
        online: "ONLINE",
        down: "DOWN",
        loading: "LOADING",
        new_collage: "NEW COLLAGE",
        create_collage: "Create Sovereign Collage",
        collage_desc: "Select two VD-CUT sources for side-by-side forensic comparison.",
        momento_a: "MOMENTO A (Left)",
        momento_b: "MOMENTO B (Right)",
        render_status: "Render Status:",
        create_and_render: "CREATE & RENDER"
    },
    pt: {
        zone_a_name: "HUB FORENSE",
        zone_b_name: "PULSO DE MASSA",
        zone_c_name: "INTEGRIDADE DO LEDGER",
        seals: "selos",
        renders: "renders",
        last_seal: "Último selo:",
        queue: "Fila:",
        exceptions: "Exceções:",
        integrity: "Integridade:",
        exceptions_kpi: "Exceções:",
        sovereignty: "Soberania:",
        kill_switch: "INTERRUPTOR DE EMERGÊNCIA",
        generate_manifest: "GERAR MANIFESTO DIÁRIO",
        kill_confirm_title: "Confirmar Interruptor de Emergência",
        kill_confirm_msg: "Isto irá suspender TODAS as políticas VD-MASS imediatamente.",
        reason: "Motivo:",
        cancel: "Cancelar",
        confirm_halt: "CONFIRMAR PARAGEM",
        connecting: "A conectar...",
        connected: "AO VIVO",
        error: "ERRO",
        online: "ONLINE",
        down: "OFFLINE",
        loading: "A CARREGAR",
        new_collage: "NOVA COLAGEM",
        create_collage: "Criar Colagem Soberana",
        collage_desc: "Selecione duas fontes VD-CUT para comparação forense lado a lado.",
        momento_a: "MOMENTO A (Esquerda)",
        momento_b: "MOMENTO B (Direita)",
        render_status: "Estado do Render:",
        create_and_render: "CRIAR & RENDERIZAR"
    }
};

let currentLang = localStorage.getItem('windi-lang') || 'en';

function setLang(lang) {
    currentLang = lang;
    localStorage.setItem('windi-lang', lang);
    document.getElementById('lang-toggle').value = lang;
    applyI18N();
}

function applyI18N() {
    const texts = I18N[currentLang];
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (texts[key]) {
            el.textContent = texts[key];
        }
    });
}

// ═══════════════════════════════════════════════════════════════
// THEME — NOIR/KLAR Toggle
// ═══════════════════════════════════════════════════════════════

function initTheme() {
    const theme = localStorage.getItem('windi-theme') || 'noir';
    document.documentElement.setAttribute('data-theme', theme);
    updateThemeIcon(theme);
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'noir' ? 'klar' : 'noir';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('windi-theme', next);
    updateThemeIcon(next);
}

function updateThemeIcon(theme) {
    const icon = document.getElementById('theme-icon');
    icon.innerHTML = theme === 'noir' ? '&#9788;' : '&#9789;'; // ☀ or ☽
}

// ═══════════════════════════════════════════════════════════════
// SSE — Real-Time Updates
// ═══════════════════════════════════════════════════════════════

let eventSource = null;
let reconnectAttempts = 0;
const MAX_RECONNECT = 5;

function connectSSE() {
    const statusEl = document.getElementById('connection-status');
    const texts = I18N[currentLang];

    statusEl.className = 'status-indicator';
    statusEl.querySelector('.status-text').textContent = texts.connecting;

    eventSource = new EventSource('/live');

    eventSource.onopen = () => {
        reconnectAttempts = 0;
        statusEl.classList.add('connected');
        statusEl.querySelector('.status-text').textContent = texts.connected;
    };

    eventSource.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            updateDashboard(data);
        } catch (e) {
            console.error('Parse error:', e);
        }
    };

    eventSource.onerror = () => {
        statusEl.classList.remove('connected');
        statusEl.classList.add('error');
        statusEl.querySelector('.status-text').textContent = texts.error;

        eventSource.close();

        if (reconnectAttempts < MAX_RECONNECT) {
            reconnectAttempts++;
            setTimeout(connectSSE, 3000 * reconnectAttempts);
        }
    };
}

// ═══════════════════════════════════════════════════════════════
// DASHBOARD UPDATE
// ═══════════════════════════════════════════════════════════════

function updateDashboard(data) {
    const texts = I18N[currentLang];

    // Zone A
    if (data.zones && data.zones.a) {
        const zoneA = data.zones.a;
        const statusA = document.querySelector('#zone-a-status .status-badge');

        if (zoneA.status === 'ONLINE') {
            statusA.className = 'status-badge online';
            statusA.textContent = texts.online;

            // Update metrics if available
            if (zoneA.data) {
                const seals = zoneA.data.total_seals || zoneA.data.projects_count || '--';
                document.getElementById('zone-a-seals').textContent = seals;
            }
        } else {
            statusA.className = 'status-badge down';
            statusA.textContent = texts.down;
        }
    }

    // Zone B
    if (data.zones && data.zones.b) {
        const zoneB = data.zones.b;
        const statusB = document.querySelector('#zone-b-status .status-badge');

        if (zoneB.status === 'ONLINE') {
            statusB.className = 'status-badge online';
            statusB.textContent = texts.online;

            // Update metrics
            if (zoneB.metrics) {
                const items = zoneB.metrics.items || {};
                const totalRenders = Object.values(items).reduce((a, b) => a + b, 0);
                document.getElementById('zone-b-renders').textContent = totalRenders || '--';

                const batches = zoneB.metrics.batches || {};
                document.getElementById('zone-b-queue').textContent = batches.pending || 0;
            }

            document.getElementById('zone-b-exceptions').textContent = zoneB.pending_exceptions || 0;
        } else {
            statusB.className = 'status-badge down';
            statusB.textContent = texts.down;
        }
    }

    // Zone C
    if (data.zones && data.zones.c) {
        const zoneC = data.zones.c;
        const score = zoneC.integrity_score || 0;

        document.getElementById('integrity-score').textContent = score.toFixed(1) + '%';
        document.getElementById('integrity-bar').style.width = score + '%';

        // Agent dots
        const agents = zoneC.agents || {};
        updateAgentDot('agent-vdcut', agents['VD-CUT']);
        updateAgentDot('agent-vdmass', agents['VD-MASS']);
        updateAgentDot('agent-ledger', agents['LEDGER']);

        // KPIs
        document.getElementById('kpi-integrity').textContent = score.toFixed(1) + '%';
    }

    // Update exception KPI from Zone B
    if (data.zones && data.zones.b) {
        document.getElementById('kpi-exceptions').textContent = data.zones.b.pending_exceptions || 0;
    }
}

function updateAgentDot(elementId, status) {
    const el = document.getElementById(elementId);
    el.classList.remove('online', 'down');
    if (status === 'ONLINE') {
        el.classList.add('online');
    } else {
        el.classList.add('down');
    }
}

// ═══════════════════════════════════════════════════════════════
// EMERGENCY CONTROLS
// ═══════════════════════════════════════════════════════════════

function killSwitch() {
    document.getElementById('kill-modal').style.display = 'flex';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

async function confirmKill() {
    const reason = document.getElementById('kill-reason').value || 'Manual emergency halt';

    // TODO: Get actual actor DID from session
    const actorDid = 'did:windi:JOBER-MOGELE-CORREA-001';

    try {
        const response = await fetch('/emergency/halt', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                actor_did: actorDid,
                reason: reason
            })
        });

        const result = await response.json();

        if (response.ok) {
            alert('KILL SWITCH ACTIVATED\n\nEvent ID: ' + result.event_id);
            closeModal('kill-modal');
        } else {
            alert('ERROR: ' + (result.error || 'Unknown error'));
        }
    } catch (e) {
        alert('Connection error: ' + e.message);
    }
}

async function generateManifest() {
    // TODO: Get actual actor DID from session
    const actorDid = 'did:windi:JOBER-MOGELE-CORREA-001';

    try {
        const response = await fetch('/manifest/daily', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                actor_did: actorDid
            })
        });

        const result = await response.json();

        if (response.ok) {
            alert('DAILY MANIFEST CREATED\n\nDate: ' + result.date +
                  '\nVD-CUT Seals: ' + result.vdcut_seals +
                  '\nVD-MASS Seals: ' + result.vdmass_seals +
                  '\nSuper-Hash: ' + result.super_hash.substring(0, 24) + '...');
        } else {
            alert('ERROR: ' + (result.error || 'Unknown error'));
        }
    } catch (e) {
        alert('Connection error: ' + e.message);
    }
}

// ═══════════════════════════════════════════════════════════════
// COLLAGE CONTROLS (§138)
// ═══════════════════════════════════════════════════════════════

let availableSources = [];

async function loadSources() {
    try {
        const response = await fetch('compose/sources');
        if (response.ok) {
            const data = await response.json();
            availableSources = data.sources || [];
            populateSourceSelects();
        }
    } catch (e) {
        console.error('Failed to load sources:', e);
    }
}

function populateSourceSelects() {
    const selectA = document.getElementById('source-a');
    const selectB = document.getElementById('source-b');

    if (!selectA || !selectB) return;

    const options = availableSources.map(s => {
        const label = s.id.length > 40 ? s.id.substring(0, 40) + '...' : s.id;
        const size = (s.size / 1024 / 1024).toFixed(1) + 'MB';
        return `<option value="${s.id}">[${s.type}] ${label} (${size})</option>`;
    }).join('');

    const placeholder = '<option value="">-- Select source --</option>';
    selectA.innerHTML = placeholder + options;
    selectB.innerHTML = placeholder + options;
}

function openCollageModal() {
    loadSources();
    document.getElementById('collage-modal').style.display = 'flex';
    document.getElementById('collage-preview').style.display = 'none';
}

async function createCollage() {
    const sourceA = document.getElementById('source-a').value;
    const sourceB = document.getElementById('source-b').value;
    const timestampA = document.getElementById('timestamp-a').value || 'MOMENTO A';
    const timestampB = document.getElementById('timestamp-b').value || 'MOMENTO B';

    if (!sourceA || !sourceB) {
        alert('Please select both sources');
        return;
    }

    if (sourceA === sourceB) {
        alert('Please select different sources for comparison');
        return;
    }

    const actorDid = 'did:windi:JOBER-MOGELE-CORREA-001';

    // Show progress
    document.getElementById('collage-preview').style.display = 'block';
    document.getElementById('render-status').textContent = 'Creating collage...';
    document.getElementById('render-progress').style.width = '10%';

    try {
        // Step 1: Create collage
        const createResponse = await fetch('compose', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                source_a: sourceA,
                source_b: sourceB,
                timestamp_a: timestampA,
                timestamp_b: timestampB,
                actor_did: actorDid
            })
        });

        const createResult = await createResponse.json();

        if (!createResponse.ok) {
            throw new Error(createResult.error || 'Failed to create collage');
        }

        document.getElementById('render-status').textContent = 'Rendering: ' + createResult.collage_id;
        document.getElementById('render-progress').style.width = '30%';

        // Step 2: Render collage
        const renderResponse = await fetch(`compose/${createResult.collage_id}/render`, {
            method: 'POST'
        });

        const renderResult = await renderResponse.json();

        if (renderResult.status === 'COMPLETED') {
            document.getElementById('render-status').textContent = 'COMPLETED!';
            document.getElementById('render-progress').style.width = '100%';

            setTimeout(() => {
                alert('COLLAGE CREATED!\n\n' +
                      'ID: ' + renderResult.collage_id + '\n' +
                      'Hash: ' + renderResult.output_hash.substring(0, 32) + '...\n' +
                      'Size: ' + (renderResult.file_size / 1024 / 1024).toFixed(2) + ' MB');
                closeModal('collage-modal');
            }, 500);
        } else if (renderResult.error) {
            throw new Error(renderResult.error);
        } else {
            document.getElementById('render-status').textContent = renderResult.status || 'Processing...';
        }

    } catch (e) {
        document.getElementById('render-status').textContent = 'ERROR: ' + e.message;
        document.getElementById('render-progress').style.width = '0%';
        console.error('Collage error:', e);
    }
}

// ═══════════════════════════════════════════════════════════════
// INITIALIZATION
// ═══════════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
    // Init theme
    initTheme();

    // Init language
    document.getElementById('lang-toggle').value = currentLang;
    applyI18N();

    // Connect SSE
    connectSSE();

    // Fallback: poll if SSE fails
    setTimeout(() => {
        if (!eventSource || eventSource.readyState === EventSource.CLOSED) {
            console.log('SSE failed, falling back to polling');
            pollData();
        }
    }, 5000);
});

// Fallback polling
async function pollData() {
    try {
        const response = await fetch('/metrics');
        if (response.ok) {
            const data = await response.json();
            updateDashboard({ zones: data.zones });
        }
    } catch (e) {
        console.error('Poll error:', e);
    }

    setTimeout(pollData, 5000);
}

// Close modal on escape
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal').forEach(m => m.style.display = 'none');
    }
});
