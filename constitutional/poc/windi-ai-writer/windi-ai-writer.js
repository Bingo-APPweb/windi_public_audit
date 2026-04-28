/**
 * WINDI AI Writer — Web Component v0.1
 * POC: First MAKEUP Container
 *
 * Invariants: I1, I9, I11 (optional), I14
 *
 * Usage:
 *   <windi-ai-writer
 *     did="did:windi:user-123"
 *     lang="en"
 *     tone="formal"
 *   ></windi-ai-writer>
 */

class WindiAIWriter extends HTMLElement {
  static get observedAttributes() {
    return ['did', 'lang', 'tone', 'mode', 'disabled'];
  }

  constructor() {
    super();
    this.attachShadow({ mode: 'open' });

    // State
    this._state = {
      status: 'idle',      // idle | generating | draft-ready | sealing | sealed | error
      draftId: null,
      content: '',
      contentHash: null,
      tokensUsed: 0,
      error: null
    };

    // I1: Track human presence
    this._humanPresenceConfirmed = false;

    this.render();
    this.setupEventListeners();
  }

  // ─────────────────────────────────────────────
  // LIFECYCLE
  // ─────────────────────────────────────────────

  connectedCallback() {
    this.emit('windi:ready', {
      containerId: 'windi.ai-writer.v1',
      version: '0.1.0'
    });

    // I1: Confirm human presence on first interaction
    this.shadowRoot.addEventListener('click', () => {
      this._humanPresenceConfirmed = true;
    }, { once: true });
  }

  attributeChangedCallback(name, oldValue, newValue) {
    if (oldValue !== newValue) {
      this.render();
    }
  }

  // ─────────────────────────────────────────────
  // GETTERS
  // ─────────────────────────────────────────────

  get did() {
    return this.getAttribute('did');
  }

  get lang() {
    return this.getAttribute('lang') || 'en';
  }

  get tone() {
    return this.getAttribute('tone') || 'formal';
  }

  get mode() {
    return this.getAttribute('mode') || 'draft';
  }

  get disabled() {
    return this.hasAttribute('disabled');
  }

  get gatewayEndpoint() {
    return this.getAttribute('gateway') || '/gateway/call';
  }

  get ledgerEndpoint() {
    return this.getAttribute('ledger') || 'http://localhost:8101/api/receipts';
  }

  // ─────────────────────────────────────────────
  // RENDER
  // ─────────────────────────────────────────────

  render() {
    const i18n = this.getI18n();

    this.shadowRoot.innerHTML = `
      <style>
        ${this.getStyles()}
      </style>

      <div class="windi-ai-writer" part="container">
        <!-- Header with badge -->
        <div class="header">
          <span class="title">${i18n.title}</span>
          <span class="windi-badge">Powered by WINDI</span>
        </div>

        <!-- Prompt Input -->
        <div class="input-section" part="prompt-input">
          <textarea
            id="prompt"
            placeholder="${i18n.placeholder}"
            rows="4"
            ${this.disabled ? 'disabled' : ''}
          ></textarea>
          <div class="input-meta">
            <span class="char-count">0 / 2000</span>
            <select id="tone-select" part="tone-selector">
              <option value="formal" ${this.tone === 'formal' ? 'selected' : ''}>${i18n.tones.formal}</option>
              <option value="casual" ${this.tone === 'casual' ? 'selected' : ''}>${i18n.tones.casual}</option>
              <option value="technical" ${this.tone === 'technical' ? 'selected' : ''}>${i18n.tones.technical}</option>
              <option value="creative" ${this.tone === 'creative' ? 'selected' : ''}>${i18n.tones.creative}</option>
            </select>
          </div>
        </div>

        <!-- Generate Button (I1: requires click) -->
        <button
          id="generate-btn"
          class="btn btn-primary"
          part="generate-button"
          ${this.disabled || !this.did ? 'disabled' : ''}
        >
          <span class="btn-icon">✨</span>
          <span class="btn-text">${i18n.generate}</span>
        </button>

        <!-- Status Indicator -->
        <div class="status" part="status" style="display: ${this._state.status === 'idle' ? 'none' : 'flex'}">
          ${this.renderStatus(i18n)}
        </div>

        <!-- Output Area -->
        <div class="output-section" part="output-area" style="display: ${this._state.content ? 'block' : 'none'}">
          <div class="output-header">
            <span>${i18n.output}</span>
            <span class="tokens">${this._state.tokensUsed} tokens</span>
          </div>
          <div class="output-content" id="output">
            ${this._state.content}
          </div>
          <div class="output-actions">
            <button id="copy-btn" class="btn btn-secondary">
              📋 ${i18n.copy}
            </button>
            <button id="edit-btn" class="btn btn-secondary">
              ✏️ ${i18n.edit}
            </button>
            <!-- I9: Seal requires explicit click -->
            <button
              id="seal-btn"
              class="btn btn-gold"
              part="seal-button"
              ${this._state.status !== 'draft-ready' ? 'disabled' : ''}
            >
              🔏 ${i18n.seal}
            </button>
          </div>
        </div>

        <!-- Receipt Display (after seal) -->
        <div class="receipt-section" style="display: ${this._state.status === 'sealed' ? 'block' : 'none'}">
          <div class="receipt-header">✅ ${i18n.sealed}</div>
          <div class="receipt-id" id="receipt-id"></div>
          <div class="receipt-hash" id="receipt-hash"></div>
          <a class="verify-link" id="verify-link" target="_blank">${i18n.verify}</a>
        </div>

        <!-- Error Display (I14) -->
        <div class="error-section" style="display: ${this._state.status === 'error' ? 'block' : 'none'}">
          <div class="error-icon">⚠️</div>
          <div class="error-message" id="error-message">${this._state.error || ''}</div>
          <button id="retry-btn" class="btn btn-secondary">${i18n.retry}</button>
        </div>

        <!-- DID Warning -->
        ${!this.did ? `
          <div class="warning">
            ⚠️ ${i18n.didRequired}
          </div>
        ` : ''}
      </div>
    `;
  }

  renderStatus(i18n) {
    switch (this._state.status) {
      case 'generating':
        return `
          <div class="spinner"></div>
          <span>${i18n.generating}</span>
        `;
      case 'sealing':
        return `
          <div class="spinner"></div>
          <span>${i18n.sealing}</span>
        `;
      default:
        return '';
    }
  }

  // ─────────────────────────────────────────────
  // EVENT LISTENERS
  // ─────────────────────────────────────────────

  setupEventListeners() {
    this.shadowRoot.addEventListener('click', (e) => {
      if (e.target.id === 'generate-btn') {
        this.handleGenerate();
      } else if (e.target.id === 'seal-btn') {
        this.handleSeal();
      } else if (e.target.id === 'copy-btn') {
        this.handleCopy();
      } else if (e.target.id === 'edit-btn') {
        this.handleEdit();
      } else if (e.target.id === 'retry-btn') {
        this.handleRetry();
      }
    });

    // Character counter
    this.shadowRoot.addEventListener('input', (e) => {
      if (e.target.id === 'prompt') {
        const count = e.target.value.length;
        const counter = this.shadowRoot.querySelector('.char-count');
        if (counter) {
          counter.textContent = `${count} / 2000`;
          counter.style.color = count > 1800 ? '#ff6b6b' : 'inherit';
        }
      }
    });
  }

  // ─────────────────────────────────────────────
  // HANDLERS
  // ─────────────────────────────────────────────

  async handleGenerate() {
    // I1: Verify human presence
    if (!this._humanPresenceConfirmed) {
      this.showError('Human presence not confirmed. Please click to interact first.');
      return;
    }

    // I1: Verify DID
    if (!this.did || !this.did.startsWith('did:windi:')) {
      this.showError('Valid DID required for generation.');
      return;
    }

    const promptEl = this.shadowRoot.getElementById('prompt');
    const prompt = promptEl?.value?.trim();

    // I14: Explicit validation
    if (!prompt || prompt.length < 10) {
      this.showError('Prompt must be at least 10 characters.');
      return;
    }

    if (prompt.length > 2000) {
      this.showError('Prompt exceeds 2000 character limit.');
      return;
    }

    this.setState({ status: 'generating', error: null });

    const promptHash = await this.sha256(prompt);
    this.emit('windi:generating', { promptHash, model: 'mistral-large' });

    try {
      const tone = this.shadowRoot.getElementById('tone-select')?.value || this.tone;
      const systemPrompt = this.getSystemPrompt(tone);

      const response = await fetch(this.gatewayEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Gateway-Secret': this.getAttribute('gateway-secret') || ''
        },
        body: JSON.stringify({
          actor: this.did,
          tier: 'MED',
          task: 'chat',
          agent: null,
          prompt: prompt,
          system: systemPrompt,
          language: this.lang
        })
      });

      if (!response.ok) {
        // I14: Explicit failure
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Generation failed: ${response.status}`);
      }

      const data = await response.json();

      // Generate draft ID
      const draftId = `DRAFT-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      const contentHash = await this.sha256(data.content || data.response);

      this.setState({
        status: 'draft-ready',
        draftId: draftId,
        content: data.content || data.response,
        contentHash: contentHash,
        tokensUsed: data.tokens || data.usage?.total_tokens || 0
      });

      this.emit('windi:draft-ready', {
        draftId: draftId,
        content: this._state.content,
        tokens: this._state.tokensUsed
      });

    } catch (error) {
      // I14: Explicit failure, never silent
      this.showError(error.message);
      this.emit('windi:error', { error: error.message, code: 'GENERATION_FAILED' });
    }
  }

  async handleSeal() {
    // I9: Verify explicit human action
    if (!this._humanPresenceConfirmed) {
      this.showError('Human confirmation required for sealing.');
      return;
    }

    // I9: Verify content exists
    if (!this._state.content || !this._state.draftId) {
      this.showError('No content to seal. Generate first.');
      return;
    }

    this.setState({ status: 'sealing' });

    try {
      // Seal to Ledger (I11)
      const response = await fetch(this.ledgerEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          document_type: 'ai-generated-content',
          document_name: `AI Writer Draft ${this._state.draftId}`,
          actor: this.did,
          governance_level: 'STANDARD',
          content_hash: this._state.contentHash,
          invariants_applied: ['I1', 'I9', 'I11', 'I14'],
          metadata: {
            makeup_id: 'windi.ai-writer.v1',
            draft_id: this._state.draftId,
            tokens_used: this._state.tokensUsed,
            language: this.lang
          }
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Seal failed: ${response.status}`);
      }

      const receipt = await response.json();

      this.setState({ status: 'sealed' });

      // Update UI with receipt info
      const receiptIdEl = this.shadowRoot.getElementById('receipt-id');
      const receiptHashEl = this.shadowRoot.getElementById('receipt-hash');
      const verifyLinkEl = this.shadowRoot.getElementById('verify-link');

      if (receiptIdEl) receiptIdEl.textContent = receipt.receipt_id;
      if (receiptHashEl) receiptHashEl.textContent = `SHA-256: ${this._state.contentHash.substring(0, 16)}...`;
      if (verifyLinkEl) verifyLinkEl.href = receipt.verify_url || `https://windi-domain.com/verify-public/?id=${receipt.receipt_id}`;

      this.emit('windi:sealed', {
        receiptId: receipt.receipt_id,
        hash: this._state.contentHash,
        verifyUrl: receipt.verify_url
      });

    } catch (error) {
      // I14: Explicit failure
      this.showError(error.message);
      this.setState({ status: 'draft-ready' }); // Allow retry
      this.emit('windi:error', { error: error.message, code: 'SEAL_FAILED' });
    }
  }

  handleCopy() {
    if (this._state.content) {
      navigator.clipboard.writeText(this._state.content);
      // Visual feedback
      const btn = this.shadowRoot.getElementById('copy-btn');
      if (btn) {
        const original = btn.textContent;
        btn.textContent = '✓ Copied!';
        setTimeout(() => { btn.textContent = original; }, 2000);
      }
    }
  }

  handleEdit() {
    // Move content back to prompt for editing
    const promptEl = this.shadowRoot.getElementById('prompt');
    if (promptEl && this._state.content) {
      promptEl.value = this._state.content;
      this.setState({
        status: 'idle',
        content: '',
        draftId: null,
        contentHash: null
      });
    }
  }

  handleRetry() {
    this.setState({ status: 'idle', error: null });
    this.render();
    this.setupEventListeners();
  }

  // ─────────────────────────────────────────────
  // HELPERS
  // ─────────────────────────────────────────────

  setState(newState) {
    this._state = { ...this._state, ...newState };
    this.render();
    this.setupEventListeners();
  }

  showError(message) {
    this.setState({ status: 'error', error: message });
  }

  emit(eventName, detail) {
    this.dispatchEvent(new CustomEvent(eventName, {
      bubbles: true,
      composed: true,
      detail: detail
    }));
  }

  async sha256(content) {
    const encoder = new TextEncoder();
    const data = encoder.encode(content);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  }

  getSystemPrompt(tone) {
    const toneInstructions = {
      formal: 'Write in a professional, formal tone. Use clear and precise language.',
      casual: 'Write in a friendly, conversational tone. Be approachable and warm.',
      technical: 'Write in a technical, detailed manner. Include relevant specifications.',
      creative: 'Write in an engaging, creative style. Use vivid language and metaphors.'
    };

    const langInstructions = {
      de: 'Schreibe auf Deutsch.',
      en: 'Write in English.',
      pt: 'Escreve em Português.'
    };

    return `You are WINDI AI Writer, a professional text generator.
${toneInstructions[tone] || toneInstructions.formal}
${langInstructions[this.lang] || langInstructions.en}
Generate clear, well-structured content based on the user's request.
Never include personal opinions or biases. Focus on helpful, factual content.
Do not include any meta-commentary about the generation process.`;
  }

  // ─────────────────────────────────────────────
  // I18N
  // ─────────────────────────────────────────────

  getI18n() {
    const translations = {
      de: {
        title: 'AI Writer',
        placeholder: 'Beschreiben Sie, was Sie schreiben möchten...',
        generate: 'Generieren',
        generating: 'Generiert...',
        output: 'Generierter Inhalt',
        copy: 'Kopieren',
        edit: 'Bearbeiten',
        seal: 'Versiegeln (I9)',
        sealing: 'Versiegelt...',
        sealed: 'Im Ledger versiegelt',
        verify: 'Überprüfen →',
        retry: 'Erneut versuchen',
        didRequired: 'DID erforderlich für Generation',
        tones: {
          formal: 'Formell',
          casual: 'Locker',
          technical: 'Technisch',
          creative: 'Kreativ'
        }
      },
      en: {
        title: 'AI Writer',
        placeholder: 'Describe what you want to write...',
        generate: 'Generate',
        generating: 'Generating...',
        output: 'Generated Content',
        copy: 'Copy',
        edit: 'Edit',
        seal: 'Seal (I9)',
        sealing: 'Sealing...',
        sealed: 'Sealed to Ledger',
        verify: 'Verify →',
        retry: 'Retry',
        didRequired: 'DID required for generation',
        tones: {
          formal: 'Formal',
          casual: 'Casual',
          technical: 'Technical',
          creative: 'Creative'
        }
      },
      pt: {
        title: 'AI Writer',
        placeholder: 'Descreva o que deseja escrever...',
        generate: 'Gerar',
        generating: 'Gerando...',
        output: 'Conteúdo Gerado',
        copy: 'Copiar',
        edit: 'Editar',
        seal: 'Selar (I9)',
        sealing: 'Selando...',
        sealed: 'Selado no Ledger',
        verify: 'Verificar →',
        retry: 'Tentar novamente',
        didRequired: 'DID necessário para geração',
        tones: {
          formal: 'Formal',
          casual: 'Casual',
          technical: 'Técnico',
          creative: 'Criativo'
        }
      }
    };

    return translations[this.lang] || translations.en;
  }

  // ─────────────────────────────────────────────
  // STYLES
  // ─────────────────────────────────────────────

  getStyles() {
    return `
      :host {
        display: block;
        font-family: var(--windi-ai-font, 'Inter', -apple-system, sans-serif);
        --primary: var(--windi-ai-primary, #C8A45A);
        --bg: var(--windi-ai-bg, #0B0D14);
        --text: var(--windi-ai-text, #E8E6E1);
        --border: var(--windi-ai-border, #1A1A24);
        --error: #ff6b6b;
        --success: #4CAF50;
      }

      .windi-ai-writer {
        background: var(--bg);
        color: var(--text);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 20px;
      }

      .header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
      }

      .title {
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--primary);
      }

      /* LOCKED: Cannot be hidden via CSS */
      .windi-badge {
        font-size: 0.7rem;
        color: var(--primary);
        opacity: 0.8;
        padding: 2px 6px;
        border: 1px solid var(--primary);
        border-radius: 4px;
      }

      .input-section {
        margin-bottom: 16px;
      }

      textarea {
        width: 100%;
        background: rgba(255,255,255,0.05);
        border: 1px solid var(--border);
        border-radius: 6px;
        color: var(--text);
        padding: 12px;
        font-size: 0.95rem;
        resize: vertical;
        min-height: 100px;
        box-sizing: border-box;
      }

      textarea:focus {
        outline: none;
        border-color: var(--primary);
      }

      textarea::placeholder {
        color: rgba(255,255,255,0.4);
      }

      .input-meta {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 8px;
        font-size: 0.8rem;
      }

      .char-count {
        color: rgba(255,255,255,0.5);
      }

      select {
        background: var(--bg);
        border: 1px solid var(--border);
        color: var(--text);
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
      }

      .btn {
        padding: 12px 24px;
        border: none;
        border-radius: 6px;
        font-size: 0.95rem;
        font-weight: 500;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        transition: all 0.2s;
      }

      .btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }

      .btn-primary {
        background: var(--primary);
        color: #0B0D14;
        width: 100%;
        justify-content: center;
      }

      .btn-primary:hover:not(:disabled) {
        background: #d4b366;
      }

      .btn-secondary {
        background: rgba(255,255,255,0.1);
        color: var(--text);
        border: 1px solid var(--border);
      }

      .btn-secondary:hover:not(:disabled) {
        background: rgba(255,255,255,0.15);
      }

      .btn-gold {
        background: linear-gradient(135deg, var(--primary), #d4b366);
        color: #0B0D14;
        font-weight: 600;
      }

      .btn-gold:hover:not(:disabled) {
        box-shadow: 0 0 20px rgba(200, 164, 90, 0.4);
      }

      .status {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 16px;
        margin: 16px 0;
        background: rgba(200, 164, 90, 0.1);
        border-radius: 6px;
      }

      .spinner {
        width: 20px;
        height: 20px;
        border: 2px solid var(--border);
        border-top-color: var(--primary);
        border-radius: 50%;
        animation: spin 1s linear infinite;
      }

      @keyframes spin {
        to { transform: rotate(360deg); }
      }

      .output-section {
        margin-top: 20px;
        border: 1px solid var(--border);
        border-radius: 6px;
        overflow: hidden;
      }

      .output-header {
        display: flex;
        justify-content: space-between;
        padding: 12px 16px;
        background: rgba(255,255,255,0.05);
        border-bottom: 1px solid var(--border);
        font-size: 0.85rem;
      }

      .tokens {
        color: var(--primary);
      }

      .output-content {
        padding: 16px;
        white-space: pre-wrap;
        line-height: 1.6;
        max-height: 300px;
        overflow-y: auto;
      }

      .output-actions {
        display: flex;
        gap: 8px;
        padding: 12px 16px;
        border-top: 1px solid var(--border);
        background: rgba(255,255,255,0.02);
      }

      .receipt-section {
        margin-top: 20px;
        padding: 20px;
        background: rgba(76, 175, 80, 0.1);
        border: 1px solid var(--success);
        border-radius: 6px;
        text-align: center;
      }

      .receipt-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--success);
        margin-bottom: 12px;
      }

      .receipt-id {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.85rem;
        padding: 8px;
        background: rgba(0,0,0,0.3);
        border-radius: 4px;
        margin-bottom: 8px;
      }

      .receipt-hash {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        color: rgba(255,255,255,0.6);
        margin-bottom: 12px;
      }

      .verify-link {
        color: var(--primary);
        text-decoration: none;
        font-weight: 500;
      }

      .verify-link:hover {
        text-decoration: underline;
      }

      .error-section {
        margin-top: 20px;
        padding: 20px;
        background: rgba(255, 107, 107, 0.1);
        border: 1px solid var(--error);
        border-radius: 6px;
        text-align: center;
      }

      .error-icon {
        font-size: 2rem;
        margin-bottom: 8px;
      }

      .error-message {
        color: var(--error);
        margin-bottom: 16px;
      }

      .warning {
        margin-top: 16px;
        padding: 12px;
        background: rgba(255, 193, 7, 0.1);
        border: 1px solid #ffc107;
        border-radius: 6px;
        font-size: 0.85rem;
        color: #ffc107;
      }
    `;
  }
}

// Register the component
if (!customElements.get('windi-ai-writer')) {
  customElements.define('windi-ai-writer', WindiAIWriter);
}

export { WindiAIWriter };
