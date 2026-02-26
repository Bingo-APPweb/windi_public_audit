/**
 * ═══════════════════════════════════════════════════════════════════════════
 * WINDI DragonClient.js — Gateway para Dragon Server (:8108)
 * "AI processes. Human decides. WINDI guarantees."
 *
 * Fase 0 do LAUNCH Plan: Fundação para integração Frontend ↔ Backend
 * Criado: 26 Fevereiro 2026
 * ═══════════════════════════════════════════════════════════════════════════
 */

class DragonClient {
    constructor(baseUrl = '') {
        // baseUrl vazio = mesmo origin (via proxy ou direto)
        this.baseUrl = baseUrl || '';
        this.timeout = 30000; // 30s default
        this.llmTimeout = 60000; // 60s para LLM
        this.connected = null; // null = unknown, true/false após check
        this.lastCheck = null;
        this.version = '1.0.0';

        // Callbacks para UI updates
        this.onConnectionChange = null;
        this.onError = null;
    }

    // ═══════════════════════════════════════════════════════════════════════
    // CORE FETCH — Base para todas as chamadas
    // ═══════════════════════════════════════════════════════════════════════

    async _fetch(endpoint, options = {}) {
        const controller = new AbortController();
        const timeoutMs = options.timeout || this.timeout;
        const timer = setTimeout(() => controller.abort(), timeoutMs);

        try {
            const response = await fetch(`${this.baseUrl}${endpoint}`, {
                ...options,
                signal: controller.signal,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });
            clearTimeout(timer);

            if (!response.ok) {
                const errorText = await response.text().catch(() => response.statusText);
                throw new Error(`Dragon ${response.status}: ${errorText}`);
            }

            // Connection successful
            if (!this.connected) {
                this.connected = true;
                this.lastCheck = new Date();
                console.log('[DragonClient] Connected to Dragon Server');
                if (this.onConnectionChange) this.onConnectionChange(true);
            }

            return await response.json();

        } catch (error) {
            clearTimeout(timer);

            // Handle abort (timeout)
            if (error.name === 'AbortError') {
                error.message = `Dragon timeout after ${timeoutMs}ms: ${endpoint}`;
            }

            // Connection lost
            if (this.connected !== false) {
                this.connected = false;
                this.lastCheck = new Date();
                console.warn(`[DragonClient] Connection lost: ${error.message}`);
                if (this.onConnectionChange) this.onConnectionChange(false);
            }

            // Notify error callback
            if (this.onError) this.onError(error, endpoint);

            throw error;
        }
    }

    // ═══════════════════════════════════════════════════════════════════════
    // HEALTH & STATUS — Verificação do ecossistema
    // ═══════════════════════════════════════════════════════════════════════

    async health() {
        return this._fetch('/api/dragon/health');
    }

    async constitutionalStatus() {
        return this._fetch('/api/constitutional/status');
    }

    async capabilities() {
        return this._fetch('/api/dragon/capabilities');
    }

    async sovereignty() {
        return this._fetch('/api/dragon/sovereignty');
    }

    async capacityStatus() {
        return this._fetch('/api/capacity/status');
    }

    // ═══════════════════════════════════════════════════════════════════════
    // SGE — Semantic Governance Engine (6-Layer)
    // ═══════════════════════════════════════════════════════════════════════

    async sge(text, options = {}) {
        return this._fetch('/api/dragon/sge', {
            method: 'POST',
            body: JSON.stringify({
                text,
                source: options.source || 'palette-frontend',
                strict: options.strict || false,
                format: options.format || 'json'
            })
        });
    }

    // ═══════════════════════════════════════════════════════════════════════
    // CHAT — LLM Conversacional (Claude Sonnet 4)
    // ═══════════════════════════════════════════════════════════════════════

    async chat(message, context = {}) {
        return this._fetch('/api/dragon/chat', {
            method: 'POST',
            timeout: this.llmTimeout,
            body: JSON.stringify({
                message,
                tier: context.tier || 'HIGH',
                chatType: context.chatType || null,
                intentMode: context.intentMode || 'chat',
                language: context.language || 'de',
                history: context.history || []
            })
        });
    }

    // ═══════════════════════════════════════════════════════════════════════
    // DOCUMENT GENERATION — PDF/DOCX/PPTX/XLSX (Phase 3 LAUNCH Plan)
    // Two-step: POST to generate → GET to download binary
    // ═══════════════════════════════════════════════════════════════════════

    async generate(type, data) {
        const validTypes = ['pdf', 'docx', 'pptx', 'xlsx'];
        if (!validTypes.includes(type)) {
            throw new Error(`Invalid document type: ${type}. Valid: ${validTypes.join(', ')}`);
        }

        return this._fetch(`/api/dragon/generate/${type}`, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    /**
     * Download a generated document by its file_id or download_url
     * @param {string} downloadUrl - Full path like /api/dragon/download/WINDI-xxx.pdf
     * @returns {Promise<Blob>} The document as a Blob
     */
    async downloadDocument(downloadUrl) {
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), 60000);

        try {
            const response = await fetch(`${this.baseUrl}${downloadUrl}`, {
                signal: controller.signal
            });
            clearTimeout(timer);

            if (!response.ok) {
                throw new Error(`Download failed: ${response.status}`);
            }

            return await response.blob();
        } catch (error) {
            clearTimeout(timer);
            throw error;
        }
    }

    /**
     * Full pipeline: Generate document → Download → Trigger browser save
     * @param {string} type - Document type: pdf, docx, pptx, xlsx
     * @param {object} data - Document content data
     * @param {string} customFilename - Optional custom filename
     * @returns {Promise<{success, filename, size, file_id, content_hash}>}
     */
    async generateAndDownload(type, data, customFilename = null) {
        try {
            // Step 1: Generate document (returns JSON with download_url)
            const genResult = await this.generate(type, data);

            if (genResult.status !== 'generated' || !genResult.download_url) {
                throw new Error(genResult.message || 'Generation failed - no download URL');
            }

            console.log(`[DragonClient] Document generated: ${genResult.file_id} (${genResult.size} bytes)`);

            // Step 2: Download the binary document
            const blob = await this.downloadDocument(genResult.download_url);

            // Step 3: Trigger browser download
            const filename = customFilename || genResult.file_id || `WINDI_${type}_${Date.now()}.${type}`;
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            a.style.display = 'none';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);

            // Cleanup after download starts
            setTimeout(() => URL.revokeObjectURL(url), 1000);

            return {
                success: true,
                filename: filename,
                size: blob.size,
                file_id: genResult.file_id,
                content_hash: genResult.content_hash,
                dragon: genResult.dragon
            };
        } catch (error) {
            console.error(`[DragonClient] ${type} generation failed:`, error);
            return { success: false, error: error.message, type: type };
        }
    }

    // Convenience methods for each document type
    async generatePDF(data, filename)  { return this.generateAndDownload('pdf', data, filename); }
    async generateDOCX(data, filename) { return this.generateAndDownload('docx', data, filename); }
    async generatePPTX(data, filename) { return this.generateAndDownload('pptx', data, filename); }
    async generateXLSX(data, filename) { return this.generateAndDownload('xlsx', data, filename); }

    // ═══════════════════════════════════════════════════════════════════════
    // SEAL — Versiegelamento de documentos
    // ═══════════════════════════════════════════════════════════════════════

    async seal(document) {
        return this._fetch('/api/dragon/seal', {
            method: 'POST',
            body: JSON.stringify(document)
        });
    }

    // ═══════════════════════════════════════════════════════════════════════
    // DECISION JOURNAL — Rastreabilidade de decisões
    // ═══════════════════════════════════════════════════════════════════════

    decisions = {
        stats: () => this._fetch('/api/dragon/decisions/stats'),
        recent: (limit = 50) => this._fetch(`/api/dragon/decisions/recent?limit=${limit}`),
        autonomy: () => this._fetch('/api/dragon/decisions/autonomy'),
        hesitations: () => this._fetch('/api/dragon/decisions/hesitations'),
    };

    // ═══════════════════════════════════════════════════════════════════════
    // COGNITIVE — Phase 2.5 Intelligence
    // ═══════════════════════════════════════════════════════════════════════

    cognitive = {
        score: () => this._fetch('/api/dragon/cognitive/score'),
        hesitation: () => this._fetch('/api/dragon/cognitive/hesitation'),
        wisdomCandidates: () => this._fetch('/api/dragon/cognitive/wisdom-candidates'),
        wisdomBlocks: () => this._fetch('/api/dragon/cognitive/wisdom-blocks'),
        evolution: () => this._fetch('/api/dragon/cognitive/evolution'),
        outlook: () => this._fetch('/api/dragon/cognitive/outlook'),
        pulse: () => this._fetch('/api/dragon/cognitive/pulse'),
        promoteWisdom: (patternId) => this._fetch('/api/dragon/cognitive/promote-wisdom', {
            method: 'POST',
            body: JSON.stringify({ pattern_id: patternId })
        }),
    };

    // ═══════════════════════════════════════════════════════════════════════
    // COMMUNIQUÉ — Publicação institucional
    // ═══════════════════════════════════════════════════════════════════════

    communique = {
        list: () => this._fetch('/api/dragon/communique/list'),
        stats: () => this._fetch('/api/communique/stats'),
        create: (data) => this._fetch('/api/dragon/communique/create', {
            method: 'POST',
            body: JSON.stringify(data)
        }),
        review: (commId) => this._fetch(`/api/dragon/communique/review/${commId}`, {
            method: 'POST'
        }),
        publish: (commId) => this._fetch(`/api/dragon/communique/publish/${commId}`, {
            method: 'POST'
        }),
    };

    // ═══════════════════════════════════════════════════════════════════════
    // OUTLOOK — Relatórios e status
    // ═══════════════════════════════════════════════════════════════════════

    outlook = {
        status: () => this._fetch('/api/dragon/outlook/status'),
        report: () => this._fetch('/api/dragon/outlook/report.md'),
    };

    // ═══════════════════════════════════════════════════════════════════════
    // UTILITIES — Helpers e checks
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Quick connection check
     * @returns {Promise<boolean>} true if connected, false otherwise
     */
    async ping() {
        try {
            const health = await this.health();
            return health && health.status === 'alive';
        } catch {
            return false;
        }
    }

    /**
     * Full status check - returns comprehensive system state
     */
    async fullStatus() {
        const results = await Promise.allSettled([
            this.health(),
            this.constitutionalStatus(),
            this.sovereignty(),
            this.capacityStatus()
        ]);

        return {
            connected: results[0].status === 'fulfilled',
            health: results[0].value || null,
            constitutional: results[1].value || null,
            sovereignty: results[2].value || null,
            capacity: results[3].value || null,
            timestamp: new Date().toISOString()
        };
    }

    /**
     * Get connection state
     */
    getState() {
        return {
            connected: this.connected,
            lastCheck: this.lastCheck,
            baseUrl: this.baseUrl,
            version: this.version
        };
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// STATUS MONITOR — Polling automático com UI updates
// ═══════════════════════════════════════════════════════════════════════════

class DragonStatusMonitor {
    constructor(client, interval = 30000) {
        this.client = client;
        this.interval = interval;
        this.timer = null;
        this.status = { connected: null };
        this.onUpdate = null;
    }

    start() {
        this.check(); // Imediato
        this.timer = setInterval(() => this.check(), this.interval);
        console.log(`[DragonMonitor] Started (interval: ${this.interval}ms)`);
    }

    stop() {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
            console.log('[DragonMonitor] Stopped');
        }
    }

    async check() {
        try {
            this.status = await this.client.fullStatus();
            if (this.onUpdate) this.onUpdate(this.status);
        } catch (error) {
            this.status = { connected: false, error: error.message };
            if (this.onUpdate) this.onUpdate(this.status);
        }
    }

    getStatus() {
        return this.status;
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// DRAGON ORCHESTRATOR — Sovereign Flow Coordination (Phase 5D)
// "Guardian blocks. Architect builds. Witness records. Vox speaks."
// ═══════════════════════════════════════════════════════════════════════════

class DragonOrchestrator {
    constructor(client) {
        this.client = client;
        this.dragons = {
            guardian:  { id: 'guardian',  icon: '🛡️', label: 'Guardian',  role: 'Protection' },
            architect: { id: 'architect', icon: '🏗️', label: 'Architect', role: 'Construction' },
            witness:   { id: 'witness',   icon: '👁️', label: 'Witness',   role: 'Validation' },
            vox:       { id: 'vox',       icon: '🔊', label: 'Vox',       role: 'Voice' }
        };
        this.activeDragon = null;
        this.flowHistory = [];
        this.voxEnabled = false;
    }

    /**
     * Handover — Transfer control to next Dragon with UI event
     */
    async handover(nextDragonId) {
        const prevDragon = this.activeDragon;
        this.activeDragon = this.dragons[nextDragonId];

        const event = new CustomEvent('dragonHandover', {
            detail: {
                id: nextDragonId,
                dragon: this.activeDragon,
                previous: prevDragon,
                timestamp: performance.now()
            }
        });
        window.dispatchEvent(event);

        console.log(`[Orchestrator] ${this.activeDragon.icon} ${this.activeDragon.label} assumes control`);
        return this.activeDragon;
    }

    /**
     * Execute full Sovereign Flow — The 4-Dragon Pipeline
     * @param {string} userInput - User message
     * @param {object} context - Chat context (tier, language, history)
     * @returns {Promise<{response, decision, metrics}>}
     */
    async executeSovereignFlow(userInput, context = {}) {
        const flowId = Date.now().toString(36);
        const startTime = performance.now();
        const metrics = { flowId, steps: {} };

        try {
            // ═══ STEP 1: GUARDIAN — Risk Analysis & SGE ═══
            await this.handover('guardian');
            const t1 = performance.now();
            const sgeResult = await this.client.sge(userInput, {
                source: 'orchestrator',
                strict: context.tier === 'HIGH'
            });
            metrics.steps.guardian = {
                duration: performance.now() - t1,
                risk: sgeResult.risk,
                score: sgeResult.score
            };

            // Check if Guardian blocks the request
            if (sgeResult.risk === 'blocked') {
                this.emitFlowComplete(metrics, 'blocked');
                return { blocked: true, reason: sgeResult.message, metrics };
            }

            // ═══ STEP 2: ARCHITECT — Cognitive Response ═══
            await this.handover('architect');
            const t2 = performance.now();
            const chatResult = await this.client.chat(userInput, {
                tier: context.tier || 'HIGH',
                language: context.language || 'de',
                history: context.history || [],
                sge: sgeResult // Pass SGE context to chat
            });
            metrics.steps.architect = {
                duration: performance.now() - t2,
                dragon: chatResult.dragon,
                tokens: chatResult.usage
            };

            // ═══ STEP 3: WITNESS — Decision Journal ═══
            await this.handover('witness');
            const t3 = performance.now();
            // Witness observes — decision tracking happens server-side
            const decision = {
                flowId,
                input: userInput.substring(0, 100),
                dragon: chatResult.dragon,
                timestamp: new Date().toISOString()
            };
            metrics.steps.witness = { duration: performance.now() - t3 };

            // ═══ STEP 4: VOX — Voice Synthesis (optional) ═══
            if (this.voxEnabled && chatResult.message) {
                await this.handover('vox');
                const t4 = performance.now();
                try {
                    await this.speak(chatResult.message, chatResult.dragon);
                    metrics.steps.vox = { duration: performance.now() - t4, spoken: true };
                } catch (e) {
                    metrics.steps.vox = { duration: performance.now() - t4, spoken: false, error: e.message };
                }
            }

            // ═══ FLOW COMPLETE ═══
            metrics.totalDuration = performance.now() - startTime;
            this.flowHistory.push({ flowId, metrics, timestamp: Date.now() });
            this.emitFlowComplete(metrics, 'success');

            return { response: chatResult, decision, metrics };

        } catch (error) {
            metrics.totalDuration = performance.now() - startTime;
            metrics.error = error.message;
            this.emitFlowComplete(metrics, 'error');
            throw error;
        }
    }

    /**
     * Speak via Vox (ElevenLabs TTS)
     */
    async speak(text, dragonId = 'guardian') {
        const response = await fetch(`${this.client.baseUrl}/api/dragon/voice/speak`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, dragon: dragonId })
        });

        if (!response.ok) {
            throw new Error(`Vox error: ${response.status}`);
        }

        const audioBlob = await response.blob();
        const url = URL.createObjectURL(audioBlob);
        const audio = new Audio(url);

        // Fade in for sophisticated humility
        audio.volume = 0;
        await audio.play();
        this.fadeIn(audio);

        // Cleanup
        audio.onended = () => URL.revokeObjectURL(url);
    }

    fadeIn(audio, target = 0.8) {
        let vol = 0;
        const interval = setInterval(() => {
            if (vol < target) {
                vol = Math.min(vol + 0.1, target);
                audio.volume = vol;
            } else {
                clearInterval(interval);
            }
        }, 50);
    }

    emitFlowComplete(metrics, status) {
        window.dispatchEvent(new CustomEvent('dragonFlowComplete', {
            detail: { metrics, status, timestamp: Date.now() }
        }));
    }

    enableVox(enabled = true) {
        this.voxEnabled = enabled;
        console.log(`[Orchestrator] Vox ${enabled ? 'enabled' : 'disabled'}`);
    }

    getFlowHistory(limit = 10) {
        return this.flowHistory.slice(-limit);
    }

    getActiveDragon() {
        return this.activeDragon;
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// SINGLETON EXPORT — Instância global pronta para uso
// ═══════════════════════════════════════════════════════════════════════════

// Criar instância singleton
const dragon = new DragonClient();

// Monitor opcional (não iniciado por padrão)
const dragonMonitor = new DragonStatusMonitor(dragon);

// Orchestrator — Sovereign Flow Manager
const dragonOrchestrator = new DragonOrchestrator(dragon);

// Expor para uso global
if (typeof window !== 'undefined') {
    window.dragon = dragon;
    window.dragonMonitor = dragonMonitor;
    window.dragonOrchestrator = dragonOrchestrator;
    window.DragonClient = DragonClient;
    window.DragonStatusMonitor = DragonStatusMonitor;
    window.DragonOrchestrator = DragonOrchestrator;

    console.log('[DragonClient] v1.1.0 loaded — Orchestrator ready');
}

// Export para módulos (se necessário)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        DragonClient,
        DragonStatusMonitor,
        DragonOrchestrator,
        dragon,
        dragonMonitor,
        dragonOrchestrator
    };
}
