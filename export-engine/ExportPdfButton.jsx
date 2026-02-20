/**
 * WINDI M3 Export Button Component
 * =================================
 * Drop-in React component for the D1 Desktop Trinity.
 * Sends document content + receipt data to the M3 Export Engine,
 * receives a PDF and triggers browser download.
 *
 * Integration: Add to your D1 toolbar next to the existing Print button.
 *
 * Usage:
 *   import ExportPdfButton from './ExportPdfButton';
 *   <ExportPdfButton store={useDocStore} />
 */

import React, { useState } from 'react';

// ── Configuration ──
const EXPORT_API = '/desktop/api/export/pdf';  // Via nginx proxy
// Fallback for local dev:
// const EXPORT_API = 'http://localhost:8103/api/export/pdf';

/**
 * ExportPdfButton — M3 Export Engine trigger
 *
 * Props:
 *   - getDocContent: () => string  — returns HTML from Tiptap editor
 *   - getReceiptData: () => object — returns { receipt_id, content_hash, timestamp, status }
 *   - docTitle: string — current document title
 */
export default function ExportPdfButton({ getDocContent, getReceiptData, docTitle }) {
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState(null);

  const handleExport = async () => {
    setExporting(true);
    setError(null);

    try {
      const content = getDocContent();
      const receipt = getReceiptData();

      if (!receipt?.receipt_id) {
        throw new Error('Document must be saved and registered before export.');
      }

      const response = await fetch(EXPORT_API, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          doc_title: docTitle || 'Untitled Document',
          doc_content_html: content,
          receipt_id: receipt.receipt_id,
          content_hash: receipt.content_hash || '',
          timestamp: receipt.timestamp || new Date().toISOString(),
          status: receipt.status || 'REGISTERED',
          sge_score: receipt.sge_score || null,
          risk_level: receipt.risk_level || null,
          include_seal: true,
          include_receipt_block: true,
        }),
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `Export failed (${response.status})`);
      }

      // Download the PDF
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');

      // Extract filename from header or build one
      const disposition = response.headers.get('Content-Disposition');
      let filename = `WINDI_${receipt.receipt_id}.pdf`;
      if (disposition) {
        const match = disposition.match(/filename="(.+)"/);
        if (match) filename = match[1];
      }

      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      console.log(`✅ M3 Export: ${filename} downloaded`);

    } catch (err) {
      console.error('M3 Export Error:', err);
      setError(err.message);
    } finally {
      setExporting(false);
    }
  };

  return (
    <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
      <button
        onClick={handleExport}
        disabled={exporting}
        title="Export PDF with WINDI Governance Seal"
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '6px',
          padding: '6px 14px',
          background: exporting ? '#888' : '#C5A55A',
          color: '#0A0A0A',
          border: 'none',
          borderRadius: '4px',
          fontSize: '13px',
          fontWeight: '600',
          fontFamily: "'Outfit', sans-serif",
          cursor: exporting ? 'wait' : 'pointer',
          transition: 'background 0.2s ease',
          opacity: exporting ? 0.7 : 1,
        }}
        onMouseEnter={(e) => {
          if (!exporting) e.target.style.background = '#D4B96E';
        }}
        onMouseLeave={(e) => {
          if (!exporting) e.target.style.background = '#C5A55A';
        }}
      >
        {exporting ? (
          <>
            <span style={{ display: 'inline-block', animation: 'spin 1s linear infinite' }}>⚙️</span>
            Generating...
          </>
        ) : (
          <>📄 Export PDF</>
        )}
      </button>

      {error && (
        <span style={{
          color: '#E74C3C',
          fontSize: '11px',
          maxWidth: '200px',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
        }}>
          ⚠ {error}
        </span>
      )}

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}


/**
 * ── Integration Example ──
 *
 * In your D1 toolbar component:
 *
 *   import ExportPdfButton from './ExportPdfButton';
 *   import { useDocStore } from './store';
 *
 *   function Toolbar() {
 *     const { editor, currentReceipt, docTitle } = useDocStore();
 *
 *     return (
 *       <div className="toolbar">
 *         {/* ... existing buttons ... *\/}
 *
 *         <ExportPdfButton
 *           getDocContent={() => editor?.getHTML() || ''}
 *           getReceiptData={() => currentReceipt}
 *           docTitle={docTitle}
 *         />
 *       </div>
 *     );
 *   }
 *
 * ── Zustand Store Integration ──
 *
 * If using the D1 Zustand store, the receipt data should be
 * available from the last save/register operation:
 *
 *   const currentReceipt = useDocStore(state => state.lastReceipt);
 *   // { receipt_id: "VR-D1-...", content_hash: "9d79...", timestamp: "...", status: "REGISTERED" }
 */
