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
        loading: "LADEN"
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
        loading: "LOADING"
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
        loading: "A CARREGAR"
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
