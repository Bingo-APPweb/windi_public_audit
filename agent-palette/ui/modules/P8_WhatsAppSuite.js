/**
 * ═══════════════════════════════════════════════════════════════════════════════
 *  WINDI Palette Module P6: WhatsApp Suite v1.0.0
 *  Supports: Text, Image, Video, Document sending via Dragon Chat :8111
 *  Added: 2026-03-08
 * ═══════════════════════════════════════════════════════════════════════════════
 */

// WhatsApp Suite State
let waCurrentType = 'text';
let waSending = false;

// Translations for WhatsApp Suite
const WA_SUITE_TRANSLATIONS = {
  de: {
    title: 'WhatsApp Suite',
    recipient: 'Empfänger (WhatsApp)',
    recipientPH: '+49 xxx xxx xxxx',
    msgType: 'Nachrichtentyp',
    text: 'Text',
    image: 'Bild',
    video: 'Video',
    document: 'Dokument',
    message: 'Nachricht',
    messagePH: 'Nachricht eingeben...',
    imageUrl: 'Bild-URL',
    imageUrlPH: 'https://beispiel.de/bild.jpg',
    imageNote: 'JPEG/PNG/WebP · max 5MB',
    videoUrl: 'Video-URL',
    videoUrlPH: 'https://beispiel.de/video.mp4',
    videoNote: 'MP4/3GPP · max 16MB',
    docUrl: 'Dokument-URL',
    docUrlPH: 'https://beispiel.de/dokument.pdf',
    docNote: 'PDF/DOCX/JMPG · max 100MB',
    filename: 'Dateiname',
    filenamePH: 'dokument.pdf',
    caption: 'Beschriftung (optional)',
    captionPH: 'Beschriftung hinzufügen...',
    send: 'Senden + Versiegeln',
    sending: 'Sende...',
    success: 'Erfolgreich gesendet',
    sealed: 'Versiegelt',
    error: 'Fehler',
    fieldRequired: 'Empfänger ist erforderlich',
    formatHint: 'Format: +49xxxxxxxxx (mit Landesvorwahl)',
    msgRequired: 'Nachricht darf nicht leer sein',
    urlRequired: 'URL ist erforderlich',
  },
  en: {
    title: 'WhatsApp Suite',
    recipient: 'Recipient (WhatsApp)',
    recipientPH: '+49 xxx xxx xxxx',
    msgType: 'Message Type',
    text: 'Text',
    image: 'Image',
    video: 'Video',
    document: 'Document',
    message: 'Message',
    messagePH: 'Type your message...',
    imageUrl: 'Image URL',
    imageUrlPH: 'https://example.com/image.jpg',
    imageNote: 'JPEG/PNG/WebP · max 5MB',
    videoUrl: 'Video URL',
    videoUrlPH: 'https://example.com/video.mp4',
    videoNote: 'MP4/3GPP · max 16MB',
    docUrl: 'Document URL',
    docUrlPH: 'https://example.com/document.pdf',
    docNote: 'PDF/DOCX/JMPG · max 100MB',
    filename: 'Filename',
    filenamePH: 'document.pdf',
    caption: 'Caption (optional)',
    captionPH: 'Add a caption...',
    send: 'Send + Seal',
    sending: 'Sending...',
    success: 'Sent successfully',
    sealed: 'Sealed',
    error: 'Error',
    fieldRequired: 'Recipient is required',
    formatHint: 'Format: +49xxxxxxxxx (with country code)',
    msgRequired: 'Message cannot be empty',
    urlRequired: 'URL is required',
  },
  pt: {
    title: 'WhatsApp Suite',
    recipient: 'Destinatário (WhatsApp)',
    recipientPH: '+351 xxx xxx xxx',
    msgType: 'Tipo de Mensagem',
    text: 'Texto',
    image: 'Imagem',
    video: 'Vídeo',
    document: 'Documento',
    message: 'Mensagem',
    messagePH: 'Escreve a tua mensagem...',
    imageUrl: 'URL da Imagem',
    imageUrlPH: 'https://exemplo.com/imagem.jpg',
    imageNote: 'JPEG/PNG/WebP · máx 5MB',
    videoUrl: 'URL do Vídeo',
    videoUrlPH: 'https://exemplo.com/video.mp4',
    videoNote: 'MP4/3GPP · máx 16MB',
    docUrl: 'URL do Documento',
    docUrlPH: 'https://exemplo.com/documento.pdf',
    docNote: 'PDF/DOCX/JMPG · máx 100MB',
    filename: 'Nome do ficheiro',
    filenamePH: 'documento.pdf',
    caption: 'Legenda (opcional)',
    captionPH: 'Adicionar legenda...',
    send: 'Enviar + Selar',
    sending: 'A enviar...',
    success: 'Enviado com sucesso',
    sealed: 'Selado',
    error: 'Erro',
    fieldRequired: 'Destinatário é obrigatório',
    formatHint: 'Formato: +351xxxxxxxxx (com código do país)',
    msgRequired: 'Mensagem não pode estar vazia',
    urlRequired: 'URL é obrigatório',
  },
};

/**
 * Get WhatsApp Suite translations for current language
 */
function getWaTranslations(lang) {
  return WA_SUITE_TRANSLATIONS[lang] || WA_SUITE_TRANSLATIONS.en;
}

/**
 * Select message type in WhatsApp Suite
 */
function waSelectType(type) {
  waCurrentType = type;

  // Update button states
  document.querySelectorAll('.wa-type-btn').forEach(btn => {
    const isActive = btn.dataset.type === type;
    btn.classList.toggle('active', isActive);
    btn.style.background = isActive ? 'var(--gold, #8B6914)' : 'transparent';
    btn.style.color = isActive ? '#FFF' : 'var(--dim, #6B6560)';
    btn.style.borderColor = isActive ? 'var(--gold, #8B6914)' : 'var(--border, #DDD6C2)';
  });

  // Show/hide panels
  ['text', 'image', 'video', 'document'].forEach(t => {
    const panel = document.getElementById(`wa-panel-${t}`);
    if (panel) panel.style.display = t === type ? 'block' : 'none';
  });

  clearWaStatus();
}

/**
 * Set status message in WhatsApp Suite
 */
function setWaStatus(msg, type) {
  const el = document.getElementById('wa-status');
  if (!el) return;

  const colors = {
    success: { bg: '#E8F5E9', color: '#2E7D32', border: '#A5D6A7' },
    error: { bg: '#FFEBEE', color: '#C62828', border: '#EF9A9A' },
    warn: { bg: '#FFF8E1', color: '#E65100', border: '#FFE082' },
    info: { bg: '#E3F2FD', color: '#1565C0', border: '#90CAF9' },
  };
  const c = colors[type] || colors.info;

  el.style.display = 'block';
  el.style.background = c.bg;
  el.style.color = c.color;
  el.style.border = `1px solid ${c.border}`;
  el.textContent = msg;
}

/**
 * Clear status message
 */
function clearWaStatus() {
  const el = document.getElementById('wa-status');
  if (el) el.style.display = 'none';
}

/**
 * Clear all WhatsApp Suite input fields
 */
function clearWaFields() {
  const fields = [
    'wa-text-body', 'wa-image-url', 'wa-image-caption',
    'wa-video-url', 'wa-video-caption',
    'wa-doc-url', 'wa-doc-caption', 'wa-doc-filename'
  ];
  fields.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = '';
  });

  const preview = document.getElementById('wa-img-preview');
  if (preview) preview.style.display = 'none';

  clearWaStatus();
}

/**
 * Send WhatsApp message via Dragon Chat API
 */
async function waSendMessage(dragonUrl, lang, flashFn) {
  const t = getWaTranslations(lang);
  const to = (document.getElementById('wa-to')?.value || '').trim();

  if (!to) {
    setWaStatus(`⚠️ ${t.fieldRequired}`, 'warn');
    return;
  }

  if (!/^\+\d{7,15}$/.test(to)) {
    setWaStatus(`⚠️ ${t.formatHint}`, 'warn');
    return;
  }

  const btn = document.getElementById('wa-send-btn');
  if (btn) {
    btn.disabled = true;
    btn.textContent = `⏳ ${t.sending}`;
  }
  setWaStatus(`🔄 ${t.sending}`, 'info');
  waSending = true;

  try {
    let endpoint = '';
    let payload = { to };

    switch (waCurrentType) {
      case 'text': {
        const body = document.getElementById('wa-text-body')?.value?.trim();
        if (!body) throw new Error(t.msgRequired);
        endpoint = '/whatsapp/send';
        payload.message = body;
        break;
      }
      case 'image': {
        const url = document.getElementById('wa-image-url')?.value?.trim();
        const caption = document.getElementById('wa-image-caption')?.value?.trim();
        if (!url) throw new Error(t.urlRequired);
        endpoint = '/whatsapp/send-image';
        payload.image_url = url;
        if (caption) payload.caption = caption;
        break;
      }
      case 'video': {
        const url = document.getElementById('wa-video-url')?.value?.trim();
        const caption = document.getElementById('wa-video-caption')?.value?.trim();
        if (!url) throw new Error(t.urlRequired);
        endpoint = '/whatsapp/send-video';
        payload.video_url = url;
        if (caption) payload.caption = caption;
        break;
      }
      case 'document': {
        const url = document.getElementById('wa-doc-url')?.value?.trim();
        const caption = document.getElementById('wa-doc-caption')?.value?.trim();
        const filename = document.getElementById('wa-doc-filename')?.value?.trim() || 'documento.pdf';
        if (!url) throw new Error(t.urlRequired);
        endpoint = '/whatsapp/send-document';
        payload.doc_url = url;
        payload.filename = filename;
        if (caption) payload.caption = caption;
        break;
      }
    }

    const resp = await fetch(dragonUrl + endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    const data = await resp.json();

    if (data.success) {
      const typeLabel = { text: t.text, image: t.image, video: t.video, document: t.document }[waCurrentType];
      const receiptInfo = data.receipt?.sealed ? ` · 🔒 ${data.receipt.receipt_id}` : '';
      setWaStatus(`✅ ${typeLabel} ${t.success}${receiptInfo}`, 'success');

      // Show seal badge
      const badge = document.getElementById('wa-seal-badge');
      if (badge && data.receipt?.sealed) badge.style.display = 'block';

      // Flash notification if available
      if (flashFn) flashFn(`✅ WhatsApp ${typeLabel} ${t.success}`);

      // Clear fields after delay
      setTimeout(() => clearWaFields(), 3000);
    } else {
      throw new Error(data.error || 'Unknown API error');
    }

  } catch (err) {
    setWaStatus(`❌ ${t.error}: ${err.message || String(err)}`, 'error');
  } finally {
    waSending = false;
    if (btn) {
      btn.disabled = false;
      btn.textContent = `📤 ${t.send}`;
    }
  }
}

/**
 * Initialize image preview on URL blur
 */
function initWaImagePreview() {
  const imgUrlInput = document.getElementById('wa-image-url');
  if (imgUrlInput) {
    imgUrlInput.addEventListener('blur', function() {
      const url = this.value.trim();
      const preview = document.getElementById('wa-img-preview');
      const tag = document.getElementById('wa-img-preview-tag');
      if (url && /\.(jpg|jpeg|png|webp|gif)(\?.*)?$/i.test(url)) {
        if (tag) tag.src = url;
        if (preview) preview.style.display = 'block';
      } else {
        if (preview) preview.style.display = 'none';
      }
    });
  }
}

/**
 * Render WhatsApp Suite panel as HTML string
 * @param {string} lang - Current language (de/en/pt)
 * @param {object} theme - Theme object with color variables
 * @returns {string} HTML string for the panel
 */
function renderWhatsAppSuitePanel(lang, theme) {
  const t = getWaTranslations(lang);
  const th = theme || {
    card: '#FDFBF5',
    border: '#DDD6C2',
    text: '#2C2924',
    dim: '#6B6560',
    input: '#FDFBF5',
    gold: '#8B6914',
    hover: '#F5F0E0',
  };

  return `
    <div id="wa-media-panel" style="
      background: ${th.card};
      border: 1px solid ${th.border};
      border-radius: 12px;
      padding: 20px;
      margin-top: 16px;
      font-family: 'Bricolage Grotesque', sans-serif;
    ">
      <!-- Header -->
      <div style="display:flex; align-items:center; gap:10px; margin-bottom:16px;">
        <span style="font-size:20px;">📲</span>
        <span style="font-weight:600; color:${th.text}; font-size:15px;">${t.title}</span>
        <span id="wa-seal-badge" style="
          display:none;
          margin-left:auto;
          font-size:11px;
          color:${th.gold};
          background:${th.hover};
          border:1px solid ${th.border};
          border-radius:20px;
          padding:2px 10px;
        ">✓ ${t.sealed}</span>
      </div>

      <!-- Recipient -->
      <div style="margin-bottom:12px;">
        <label style="font-size:12px; color:${th.dim}; display:block; margin-bottom:4px;">${t.recipient}</label>
        <input id="wa-to" type="tel" placeholder="${t.recipientPH}" style="
          width:100%; box-sizing:border-box;
          background:${th.input};
          border:1px solid ${th.border};
          border-radius:8px; padding:9px 12px;
          font-size:14px; color:${th.text};
          outline:none;
        "/>
      </div>

      <!-- Type Selector -->
      <div style="margin-bottom:14px;">
        <label style="font-size:12px; color:${th.dim}; display:block; margin-bottom:6px;">${t.msgType}</label>
        <div style="display:flex; gap:8px; flex-wrap:wrap;">
          <button class="wa-type-btn active" data-type="text" onclick="waSelectType('text')" style="
            background:${th.gold}; border:1px solid ${th.gold}; border-radius:20px;
            padding:5px 14px; font-size:12px; color:#FFF; cursor:pointer;
            font-family:'Bricolage Grotesque',sans-serif;">💬 ${t.text}</button>
          <button class="wa-type-btn" data-type="image" onclick="waSelectType('image')" style="
            background:transparent; border:1px solid ${th.border}; border-radius:20px;
            padding:5px 14px; font-size:12px; color:${th.dim}; cursor:pointer;
            font-family:'Bricolage Grotesque',sans-serif;">🖼️ ${t.image}</button>
          <button class="wa-type-btn" data-type="video" onclick="waSelectType('video')" style="
            background:transparent; border:1px solid ${th.border}; border-radius:20px;
            padding:5px 14px; font-size:12px; color:${th.dim}; cursor:pointer;
            font-family:'Bricolage Grotesque',sans-serif;">🎬 ${t.video}</button>
          <button class="wa-type-btn" data-type="document" onclick="waSelectType('document')" style="
            background:transparent; border:1px solid ${th.border}; border-radius:20px;
            padding:5px 14px; font-size:12px; color:${th.dim}; cursor:pointer;
            font-family:'Bricolage Grotesque',sans-serif;">📄 ${t.document}</button>
        </div>
      </div>

      <!-- Panel: Text -->
      <div id="wa-panel-text">
        <label style="font-size:12px; color:${th.dim}; display:block; margin-bottom:4px;">${t.message}</label>
        <textarea id="wa-text-body" rows="4" placeholder="${t.messagePH}" style="
          width:100%; box-sizing:border-box;
          background:${th.input};
          border:1px solid ${th.border};
          border-radius:8px; padding:9px 12px;
          font-size:14px; color:${th.text};
          resize:vertical; outline:none;
        "></textarea>
      </div>

      <!-- Panel: Image -->
      <div id="wa-panel-image" style="display:none;">
        <label style="font-size:12px; color:${th.dim}; display:block; margin-bottom:4px;">
          ${t.imageUrl} <span style="opacity:.6">(${t.imageNote})</span>
        </label>
        <input id="wa-image-url" type="url" placeholder="${t.imageUrlPH}" style="
          width:100%; box-sizing:border-box;
          background:${th.input}; border:1px solid ${th.border};
          border-radius:8px; padding:9px 12px;
          font-size:14px; color:${th.text}; outline:none;
        "/>
        <div id="wa-img-preview" style="
          margin-top:8px; display:none;
          border-radius:8px; overflow:hidden;
          max-height:160px; text-align:center;
          background:${th.hover};
        ">
          <img id="wa-img-preview-tag" style="max-height:160px; max-width:100%; object-fit:contain;" />
        </div>
        <div style="margin-top:8px;">
          <input id="wa-image-caption" type="text" placeholder="${t.captionPH}" style="
            width:100%; box-sizing:border-box;
            background:${th.input}; border:1px solid ${th.border};
            border-radius:8px; padding:8px 12px;
            font-size:13px; color:${th.text}; outline:none;
          "/>
        </div>
      </div>

      <!-- Panel: Video -->
      <div id="wa-panel-video" style="display:none;">
        <label style="font-size:12px; color:${th.dim}; display:block; margin-bottom:4px;">
          ${t.videoUrl} <span style="opacity:.6">(${t.videoNote})</span>
        </label>
        <input id="wa-video-url" type="url" placeholder="${t.videoUrlPH}" style="
          width:100%; box-sizing:border-box;
          background:${th.input}; border:1px solid ${th.border};
          border-radius:8px; padding:9px 12px;
          font-size:14px; color:${th.text}; outline:none;
        "/>
        <div style="margin-top:8px;">
          <input id="wa-video-caption" type="text" placeholder="${t.captionPH}" style="
            width:100%; box-sizing:border-box;
            background:${th.input}; border:1px solid ${th.border};
            border-radius:8px; padding:8px 12px;
            font-size:13px; color:${th.text}; outline:none;
          "/>
        </div>
      </div>

      <!-- Panel: Document -->
      <div id="wa-panel-document" style="display:none;">
        <label style="font-size:12px; color:${th.dim}; display:block; margin-bottom:4px;">
          ${t.docUrl} <span style="opacity:.6">(${t.docNote})</span>
        </label>
        <input id="wa-doc-url" type="url" placeholder="${t.docUrlPH}" style="
          width:100%; box-sizing:border-box;
          background:${th.input}; border:1px solid ${th.border};
          border-radius:8px; padding:9px 12px;
          font-size:14px; color:${th.text}; outline:none;
        "/>
        <div style="margin-top:8px; display:flex; gap:8px;">
          <input id="wa-doc-filename" type="text" placeholder="${t.filenamePH}" style="
            flex:1;
            background:${th.input}; border:1px solid ${th.border};
            border-radius:8px; padding:8px 12px;
            font-size:13px; color:${th.text}; outline:none;
          "/>
          <input id="wa-doc-caption" type="text" placeholder="${t.captionPH}" style="
            flex:1;
            background:${th.input}; border:1px solid ${th.border};
            border-radius:8px; padding:8px 12px;
            font-size:13px; color:${th.text}; outline:none;
          "/>
        </div>
      </div>

      <!-- Status -->
      <div id="wa-status" style="
        display:none; margin-top:12px;
        font-size:12px; padding:8px 12px;
        border-radius:8px; font-family:'JetBrains Mono', monospace;
      "></div>

      <!-- Send Button -->
      <button id="wa-send-btn" style="
        margin-top:14px;
        width:100%;
        background: linear-gradient(135deg, ${th.gold}, #A07820);
        color:#fff;
        border:none; border-radius:8px;
        padding:11px 0; font-size:14px;
        font-weight:600; cursor:pointer;
        font-family:'Bricolage Grotesque', sans-serif;
        transition: opacity .15s;
      ">📤 ${t.send}</button>
    </div>
  `;
}

// Export functions for use in main Palette
if (typeof window !== 'undefined') {
  window.WA_SUITE = {
    render: renderWhatsAppSuitePanel,
    selectType: waSelectType,
    send: waSendMessage,
    initPreview: initWaImagePreview,
    setStatus: setWaStatus,
    clearStatus: clearWaStatus,
    clearFields: clearWaFields,
    getTranslations: getWaTranslations,
  };
}
