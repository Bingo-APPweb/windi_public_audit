/**
 * WINDI D1 — Export Menu + Language Selector
 * ═══════════════════════════════════════════
 * Trilingual (DE/EN/PT) export dropdown
 * Formats: PDF (M3 Engine), DOCX, Markdown, TXT, HTML
 *
 * PDF uses M3 Export Engine (:8103) with Dynamic Header Seal
 * Other formats use client-side fallback
 */

import { useState, useRef, useEffect } from 'react';

// ═══════════════════════════════════════════
// M3 EXPORT ENGINE CONFIG
// ═══════════════════════════════════════════
const M3_EXPORT_URL = '/desktop/api/export/pdf';

// ═══════════════════════════════════════════
// TRILINGUAL LABELS
// ═══════════════════════════════════════════
const LABELS = {
  de: {
    export: 'Exportieren',
    exportAs: 'Exportieren als',
    pdf: 'PDF mit Governance-Siegel',
    docx: 'Word-Dokument',
    md: 'Markdown',
    txt: 'Nur Text',
    html: 'Webseite',
    print: 'Drucken',
    send: 'Per E-Mail senden',
    sendTo: 'Empfänger E-Mail:',
    sending: 'Wird gesendet…',
    sent: 'Gesendet!',
    sendError: 'Senden fehlgeschlagen',
    save: 'Speichern',
    saved: 'Gespeichert',
    saving: 'Speichert…',
    exporting: 'Exportiert…',
    exportingPdf: 'PDF wird generiert…',
    success: 'Fertig!',
    error: 'Fehler beim Export',
    errorNoReceipt: 'Dokument muss zuerst gespeichert werden',
    newDoc: 'Neues Dokument',
    untitled: 'Unbenannt',
    documents: 'Dokumente',
    governanceTrail: 'Governance-Trail',
    integrityProtected: 'Integrität geschützt',
    changesUnverified: 'Änderungen nicht verifiziert',
    digitallySigned: 'Digital signiert',
    integrityCompromised: 'Integrität gefährdet',
    draft: 'Entwurf',
    verifyIntegrity: 'Integrität prüfen',
    receiptLog: 'Beleg-Protokoll',
    noEvents: 'Keine Governance-Ereignisse aufgezeichnet.',
    currentHash: 'Aktueller Hash',
    integrity: 'Integrität',
    verified: 'Verifiziert',
    documentId: 'Dokument-ID',
    page: 'Seite',
  },
  en: {
    export: 'Export',
    exportAs: 'Export as',
    pdf: 'PDF with Governance Seal',
    docx: 'Word Document',
    md: 'Markdown',
    txt: 'Plain Text',
    html: 'Web Page',
    print: 'Print',
    send: 'Send via Email',
    sendTo: 'Recipient Email:',
    sending: 'Sending…',
    sent: 'Sent!',
    sendError: 'Send failed',
    save: 'Save',
    saved: 'Saved',
    saving: 'Saving…',
    exporting: 'Exporting…',
    exportingPdf: 'Generating PDF…',
    success: 'Done!',
    error: 'Export failed',
    errorNoReceipt: 'Document must be saved first',
    newDoc: 'New Document',
    untitled: 'Untitled',
    documents: 'Documents',
    governanceTrail: 'Governance Trail',
    integrityProtected: 'Integrity protected',
    changesUnverified: 'Changes unverified',
    digitallySigned: 'Digitally signed',
    integrityCompromised: 'Integrity compromised',
    draft: 'Draft',
    verifyIntegrity: 'Verify Integrity',
    receiptLog: 'Receipt Log',
    noEvents: 'No governance events recorded yet.',
    currentHash: 'Current Hash',
    integrity: 'Integrity',
    verified: 'Verified',
    documentId: 'Document ID',
    page: 'Page',
  },
  pt: {
    export: 'Exportar',
    exportAs: 'Exportar como',
    pdf: 'PDF com Selo de Governança',
    docx: 'Documento Word',
    md: 'Markdown',
    txt: 'Texto Puro',
    html: 'Página Web',
    print: 'Imprimir',
    send: 'Enviar por Email',
    sendTo: 'Email do destinatário:',
    sending: 'Enviando…',
    sent: 'Enviado!',
    sendError: 'Falha ao enviar',
    save: 'Salvar',
    saved: 'Salvo',
    saving: 'Salvando…',
    exporting: 'Exportando…',
    exportingPdf: 'Gerando PDF…',
    success: 'Pronto!',
    error: 'Erro ao exportar',
    errorNoReceipt: 'Documento precisa ser salvo primeiro',
    newDoc: 'Novo Documento',
    untitled: 'Sem Título',
    documents: 'Documentos',
    governanceTrail: 'Trilha de Governança',
    integrityProtected: 'Integridade protegida',
    changesUnverified: 'Alterações não verificadas',
    digitallySigned: 'Assinado digitalmente',
    integrityCompromised: 'Integridade comprometida',
    draft: 'Rascunho',
    verifyIntegrity: 'Verificar Integridade',
    receiptLog: 'Log de Recibos',
    noEvents: 'Nenhum evento de governança registrado.',
    currentHash: 'Hash Atual',
    integrity: 'Integridade',
    verified: 'Verificado',
    documentId: 'ID do Documento',
    page: 'Página',
  },
};

// Export to global for other components
if (typeof window !== 'undefined') {
  window.__WINDI_LABELS = LABELS;
}

export { LABELS };

// ═══════════════════════════════════════════
// LANGUAGE SELECTOR COMPONENT
// ═══════════════════════════════════════════
export function LangSelector({ lang = 'de', onLangChange }) {
  const langs = ['DE', 'EN', 'PT'];

  return (
    <div className="lang-selector">
      {langs.map(l => (
        <button
          key={l}
          className={lang === l.toLowerCase() ? 'active' : ''}
          onClick={() => onLangChange && onLangChange(l.toLowerCase())}
          title={l === 'DE' ? 'Deutsch' : l === 'EN' ? 'English' : 'Português'}
        >
          {l}
        </button>
      ))}
    </div>
  );
}

// ═══════════════════════════════════════════
// M3 PDF EXPORT (Dynamic Header Seal)
// ═══════════════════════════════════════════
async function exportPdfM3({ title, htmlContent, sealData, lang }) {
  const response = await fetch(M3_EXPORT_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      doc_title: title || 'Untitled Document',
      doc_content_html: htmlContent,
      receipt_id: sealData?.receiptId || '',
      content_hash: sealData?.hash || '',
      timestamp: sealData?.timestamp || new Date().toISOString(),
      status: sealData?.status || 'DRAFT',
      sge_score: sealData?.sgeScore || null,
      risk_level: sealData?.riskLevel || null,
      include_seal: true,
      include_receipt_block: true,
    }),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || `M3 Export failed (${response.status})`);
  }

  // Trigger download
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');

  // Extract filename from Content-Disposition header
  const disposition = response.headers.get('Content-Disposition');
  let filename = `WINDI_${sealData?.receiptId || 'DRAFT'}.pdf`;
  if (disposition) {
    const match = disposition.match(/filename="(.+)"/);
    if (match) filename = match[1];
  }

  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);

  console.log(`✅ M3 Export: ${filename} downloaded`);
  return filename;
}

// ═══════════════════════════════════════════
// EXPORT MENU COMPONENT
// ═══════════════════════════════════════════
export default function ExportMenu({
  lang = 'de',
  docId = null,
  title = 'Untitled',
  content = null,      // Tiptap JSON or HTML content
  getHTML = null,       // function that returns editor HTML
  sealData = null,      // { receiptId, hash, timestamp, status, sgeScore }
}) {
  const [open, setOpen] = useState(false);
  const [exporting, setExporting] = useState(null); // current format being exported
  const [feedback, setFeedback] = useState(null);    // success/error message
  const dropdownRef = useRef(null);
  const l = LABELS[lang] || LABELS.de;

  // Close on outside click
  useEffect(() => {
    function handleClick(e) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setOpen(false);
      }
    }
    if (open) document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [open]);

  // Clear feedback after 2s
  useEffect(() => {
    if (feedback) {
      const t = setTimeout(() => setFeedback(null), 2000);
      return () => clearTimeout(t);
    }
  }, [feedback]);

  const formats = [
    { id: 'pdf',  icon: <svg width="14" height="14" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M4 2H12L16 6V18H4V2Z"/><path d="M12 2V6H16"/></svg>, label: l.pdf,  ext: '.pdf', m3: true },
    { id: 'docx', icon: <svg width="14" height="14" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M4 2H12L16 6V18H4V2Z"/><path d="M12 2V6H16"/><line x1="7" y1="10" x2="13" y2="10"/><line x1="7" y1="13" x2="13" y2="13"/></svg>, label: l.docx, ext: '.docx' },
    { id: 'sep1' },
    { id: 'md',   icon: <svg width="14" height="14" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="14" height="14" rx="2"/><path d="M7 13V7L9 10L11 7V13"/><path d="M13 10L15 7V13"/></svg>, label: l.md,   ext: '.md' },
    { id: 'txt',  icon: <svg width="14" height="14" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M4 2H16V18H4V2Z"/><line x1="7" y1="6" x2="13" y2="6"/><line x1="7" y1="9" x2="13" y2="9"/><line x1="7" y1="12" x2="10" y2="12"/></svg>, label: l.txt,  ext: '.txt' },
    { id: 'html', icon: <svg width="14" height="14" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M7 5L3 10L7 15"/><path d="M13 5L17 10L13 15"/><path d="M11 3L9 17"/></svg>, label: l.html, ext: '.html' },
    { id: 'sep2' },
    { id: 'print', icon: <svg width="14" height="14" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><rect x="4" y="8" width="12" height="8" rx="1"/><path d="M6 8V3H14V8"/><path d="M6 13H14V17H6V13Z"/></svg>, label: l.print, ext: '' },
    { id: 'send',  icon: <svg width="14" height="14" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M4 4L16 10L4 16V10L16 10"/></svg>,  label: l.send,  ext: '', email: true },
  ];

  /**
   * Get current HTML from editor
   */
  function getEditorHTML() {
    if (getHTML) return getHTML();
    const proseMirror = document.querySelector('.a4-page-wrapper .ProseMirror');
    if (proseMirror) return proseMirror.innerHTML;
    if (content && typeof content === 'string') return content;
    return '';
  }

  async function handleExport(format) {
    if (format === 'print') {
      setOpen(false);
      window.print();
      return;
    }

    // ═══════════════════════════════════════
    // SEND VIA EMAIL — Dragon Distribute API
    // ═══════════════════════════════════════
    if (format === 'send') {
      // Check if document is sealed (has valid receipt ID)
      if (!sealData?.receiptId || sealData?.status === 'DRAFT') {
        window.alert(l.errorNoReceipt);
        setOpen(false);
        return;
      }

      const recipient = window.prompt(l.sendTo);
      if (!recipient || !recipient.includes('@')) {
        setOpen(false);
        return;
      }

      setExporting(format);
      try {
        const htmlContent = getEditorHTML();
        const response = await fetch('/api/dragon/distribute', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            recipients: [{ channel: 'email', value: recipient }],
            doc_title: title || l.untitled,
            doc_content: htmlContent,
            receipt_id: sealData.receiptId,
            lang: lang,
          }),
        });

        const data = await response.json();
        if (data.success || data.total_sent > 0) {
          setFeedback('sent');
        } else {
          setFeedback('sendError');
        }
      } catch (err) {
        console.error('Send failed:', err);
        setFeedback('sendError');
      }
      setExporting(null);
      setOpen(false);
      return;
    }

    setExporting(format);

    try {
      // ═══════════════════════════════════════
      // M3 PDF EXPORT — Server-side with Seal
      // ═══════════════════════════════════════
      if (format === 'pdf') {
        const htmlContent = getEditorHTML();

        await exportPdfM3({
          title: title || l.untitled,
          htmlContent,
          sealData,
          lang,
        });

        setFeedback('success');
        setExporting(null);
        setOpen(false);
        return;
      }

      // ═══════════════════════════════════════
      // OTHER FORMATS — Client-side export
      // ═══════════════════════════════════════
      const htmlContent = getEditorHTML();

      // Build seal header for non-PDF exports
      const sealHeader = sealData ? `
        <div style="background:#f5f0e0;padding:8px 20px;font-family:monospace;font-size:11px;border-bottom:1px solid #e0dcd0;margin-bottom:20px;">
          <span style="background:#1a1a1a;color:#c8a000;padding:2px 8px;border-radius:3px;font-weight:700;letter-spacing:1px;">◆ WINDI</span>
          <span style="margin-left:8px;color:#333;">${sealData.receiptId || 'DRAFT'}</span>
          <span style="margin-left:8px;color:#666;">${sealData.timestamp || ''}</span>
          <span style="margin-left:8px;color:#999;">${sealData.hash ? sealData.hash.substring(0, 12) + '…' : ''}</span>
        </div>
      ` : '';

      // Full HTML with seal
      const fullHTML = `<!DOCTYPE html>
<html lang="${lang}">
<head>
  <meta charset="UTF-8">
  <title>${title || l.untitled}</title>
  <style>
    body { font-family: Calibri, Arial, sans-serif; font-size: 11pt; line-height: 1.5; color: #1a1a1a; max-width: 210mm; margin: 20mm auto; padding: 0 25mm; }
    h1 { font-size: 22pt; border-bottom: 2px solid #c8a000; padding-bottom: 8px; }
    h2 { font-size: 16pt; }
    h3 { font-size: 13pt; }
    blockquote { border-left: 3px solid #c8a000; background: #faf8f2; padding: 8px 16px; margin: 12px 0; font-style: italic; }
    table { border-collapse: collapse; width: 100%; }
    th { background: #f5f0e0; border: 1px solid #ddd; padding: 8px 12px; font-weight: 600; }
    td { border: 1px solid #ddd; padding: 8px 12px; }
    code { background: #f0f0f0; padding: 2px 4px; border-radius: 3px; font-family: 'JetBrains Mono', monospace; }
    pre { background: #f5f5f5; border: 1px solid #ddd; padding: 12px; border-radius: 4px; overflow-x: auto; }
    .windi-footer { margin-top: 40px; padding-top: 12px; border-top: 1px solid #eee; font-size: 9px; color: #999; font-family: monospace; text-align: center; }
  </style>
</head>
<body>
  ${sealHeader}
  ${htmlContent}
  <div class="windi-footer">WINDI Desktop — DOC | ${docId ? 'ID: ' + docId.substring(0, 12) : ''} | AI processes. Human decides. WINDI guarantees.</div>
</body>
</html>`;

      clientSideExport(format, fullHTML, title);
      setFeedback('success');

    } catch (err) {
      console.error('Export failed:', err);

      // PDF fallback: if M3 fails, use browser print
      if (format === 'pdf') {
        console.warn('M3 Export unavailable, falling back to browser print');
        try {
          const htmlContent = getEditorHTML();
          clientSideExport('pdf', htmlContent, title);
          setFeedback('success');
        } catch (e2) {
          setFeedback('error');
        }
      } else {
        setFeedback('error');
      }
    }

    setExporting(null);
    setOpen(false);
  }

  function clientSideExport(format, html, docTitle) {
    const filename = docTitle || l.untitled;

    switch (format) {
      case 'html': {
        downloadBlob(html, `${filename}.html`, 'text/html');
        break;
      }
      case 'txt': {
        const tmp = document.createElement('div');
        tmp.innerHTML = html;
        const text = tmp.textContent || tmp.innerText || '';
        downloadBlob(text, `${filename}.txt`, 'text/plain');
        break;
      }
      case 'md': {
        const tmp = document.createElement('div');
        tmp.innerHTML = html;
        let md = '';
        tmp.querySelectorAll('h1,h2,h3,p,li,blockquote,pre,code').forEach(el => {
          const tag = el.tagName.toLowerCase();
          const text = el.textContent.trim();
          if (tag === 'h1') md += `# ${text}\n\n`;
          else if (tag === 'h2') md += `## ${text}\n\n`;
          else if (tag === 'h3') md += `### ${text}\n\n`;
          else if (tag === 'li') md += `- ${text}\n`;
          else if (tag === 'blockquote') md += `> ${text}\n\n`;
          else if (tag === 'pre' || tag === 'code') md += "```\n" + text + "\n```\n\n";
          else if (tag === 'p') md += `${text}\n\n`;
        });
        downloadBlob(md || tmp.textContent, `${filename}.md`, 'text/markdown');
        break;
      }
      case 'pdf': {
        // Fallback: Print to PDF via browser
        const printWin = window.open('', '_blank');
        printWin.document.write(html);
        printWin.document.close();
        setTimeout(() => {
          printWin.print();
          printWin.close();
        }, 500);
        break;
      }
      case 'docx': {
        const docHtml = `<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:w="urn:schemas-microsoft-com:office:word" xmlns="http://www.w3.org/TR/REC-html40">
<head><meta charset="utf-8"><title>${filename}</title>
<!--[if gte mso 9]><xml><w:WordDocument><w:View>Print</w:View></w:WordDocument></xml><![endif]-->
</head><body>${html}</body></html>`;
        downloadBlob(docHtml, `${filename}.docx`, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document');
        break;
      }
    }
  }

  function downloadBlob(content, filename, mimeType) {
    const blob = new Blob([content], { type: mimeType + ';charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  return (
    <div ref={dropdownRef} style={{ position: 'relative', display: 'inline-block' }}>
      <button
        className="btn-export"
        onClick={() => setOpen(!open)}
        title={l.exportAs}
      >
        {exporting === 'pdf' ? l.exportingPdf :
         exporting === 'send' ? l.sending :
         exporting ? l.exporting :
         feedback === 'success' ? '✅ ' + l.success :
         feedback === 'sent' ? '✅ ' + l.sent :
         feedback === 'error' ? '❌ ' + l.error :
         feedback === 'sendError' ? '❌ ' + l.sendError :
         l.export + ' ▾'}
      </button>

      {open && (
        <div className="export-dropdown">
          {formats.map(f => {
            if (f.id.startsWith('sep')) {
              return <div key={f.id} className="export-sep" />;
            }
            return (
              <button
                key={f.id}
                onClick={() => handleExport(f.id)}
                disabled={exporting !== null}
                className={f.m3 ? 'export-m3-item' : ''}
              >
                <span className="export-icon">{f.icon}</span>
                <span className="export-label">{f.label}</span>
                {f.ext && <span className="export-ext">{f.ext}</span>}
                {f.m3 && <span className="export-m3-badge">M3</span>}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
