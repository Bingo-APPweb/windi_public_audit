/**
 * WINDI D1 — M3 Document Seal (Dynamic Header)
 * ═══════════════════════════════════════════════
 * Visual reference: LibreOffice mockup with WINDI seal
 * "◆ WINDI | WINDI-MLPLCU00 | 16.2.2026, 20:52:45"
 * 
 * But alive. Clickable. Connected to the Forensic Ledger.
 * "O poder está lá. Mas ele não grita."
 */

import { useState, useEffect, useCallback } from 'react';

// ═══════════════════════════════════════════
// SEAL STATUS DEFINITIONS
// ═══════════════════════════════════════════
const SEAL_STATES = {
  REGISTERED: {
    color: '#22c55e',      // green
    bg: 'rgba(34,197,94,0.08)',
    icon: '🟢',
    label: { de: 'Integrität geschützt', en: 'Integrity protected', pt: 'Integridade protegida' },
  },
  PENDING: {
    color: '#eab308',      // yellow
    bg: 'rgba(234,179,8,0.08)',
    icon: '🟡',
    label: { de: 'Änderungen nicht verifiziert', en: 'Changes unverified', pt: 'Alterações não verificadas' },
  },
  SIGNED: {
    color: '#3b82f6',      // blue
    bg: 'rgba(59,130,246,0.08)',
    icon: '🔵',
    label: { de: 'Digital signiert', en: 'Digitally signed', pt: 'Assinado digitalmente' },
  },
  COMPROMISED: {
    color: '#ef4444',      // red
    bg: 'rgba(239,68,68,0.08)',
    icon: '🔴',
    label: { de: 'Integrität gefährdet', en: 'Integrity compromised', pt: 'Integridade comprometida' },
  },
  DRAFT: {
    color: '#6b7280',      // gray
    bg: 'rgba(107,114,128,0.08)',
    icon: '⚪',
    label: { de: 'Entwurf', en: 'Draft', pt: 'Rascunho' },
  },
};

// ═══════════════════════════════════════════
// HELPER: Format timestamp like LibreOffice mockup
// ═══════════════════════════════════════════
function formatSealTimestamp(isoString) {
  if (!isoString) return '—';
  try {
    const d = new Date(isoString);
    const day = d.getDate().toString().padStart(2, '0');
    const month = (d.getMonth() + 1).toString().padStart(2, '0');
    const year = d.getFullYear();
    const hours = d.getHours().toString().padStart(2, '0');
    const minutes = d.getMinutes().toString().padStart(2, '0');
    const seconds = d.getSeconds().toString().padStart(2, '0');
    return `${day}.${month}.${year}, ${hours}:${minutes}:${seconds}`;
  } catch {
    return '—';
  }
}

// ═══════════════════════════════════════════
// HELPER: Short hash for display
// ═══════════════════════════════════════════
function shortHash(hash) {
  if (!hash) return '—';
  return hash.substring(0, 12) + '…';
}

// ═══════════════════════════════════════════
// HELPER: Generate seal ID from receipt
// ═══════════════════════════════════════════
function sealId(receiptId) {
  if (!receiptId) return 'WINDI-DRAFT';
  // Format like mockup: WINDI-XXXXXXXX
  const short = receiptId.replace('VR-D1-', '').toUpperCase().substring(0, 8);
  return `WINDI-${short}`;
}

// ═══════════════════════════════════════════
// DOCUMENT SEAL COMPONENT
// ═══════════════════════════════════════════
export default function DocumentSeal({ 
  receiptId = null,
  integrityHash = null,
  timestamp = null,
  status = 'DRAFT',        // REGISTERED | PENDING | SIGNED | COMPROMISED | DRAFT
  sgeScore = null,
  governanceLevel = null,
  lang = 'de',              // de | en | pt
  onSealClick = null,       // callback when seal is clicked
  ledgerUrl = null,          // URL to open receipt in ledger
}) {
  const [expanded, setExpanded] = useState(false);
  const [pulseActive, setPulseActive] = useState(false);

  const state = SEAL_STATES[status] || SEAL_STATES.DRAFT;

  // Pulse animation when status changes
  useEffect(() => {
    setPulseActive(true);
    const timer = setTimeout(() => setPulseActive(false), 1200);
    return () => clearTimeout(timer);
  }, [status, receiptId]);

  const handleClick = useCallback(() => {
    setExpanded(prev => !prev);
    if (onSealClick) onSealClick({ receiptId, status, integrityHash });
  }, [receiptId, status, integrityHash, onSealClick]);

  const handleLedgerLink = useCallback((e) => {
    e.stopPropagation();
    if (ledgerUrl && receiptId) {
      window.open(`${ledgerUrl}?receipt=${receiptId}`, '_blank');
    }
  }, [ledgerUrl, receiptId]);

  // ─── Styles ───────────────────────────────
  const sealBarStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: '0',
    padding: '6px 16px',
    background: '#1a1a1a',
    borderBottom: `2px solid ${state.color}33`,
    fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
    fontSize: '12px',
    cursor: 'pointer',
    userSelect: 'none',
    transition: 'all 0.3s ease',
    position: 'relative',
    overflow: 'hidden',
  };

  const windiBadgeStyle = {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '6px',
    background: '#c8a000',
    color: '#000',
    padding: '2px 10px',
    borderRadius: '3px',
    fontWeight: '700',
    fontSize: '11px',
    letterSpacing: '1.5px',
    marginRight: '12px',
  };

  const separatorStyle = {
    color: '#555',
    margin: '0 8px',
    fontSize: '10px',
  };

  const receiptIdStyle = {
    color: '#e5e5e5',
    fontWeight: '500',
    fontSize: '11px',
  };

  const timestampStyle = {
    color: '#888',
    fontSize: '11px',
  };

  const statusPillStyle = {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '4px',
    background: state.bg,
    color: state.color,
    padding: '2px 8px',
    borderRadius: '10px',
    fontSize: '10px',
    fontWeight: '600',
    marginLeft: 'auto',
    animation: pulseActive ? 'sealPulse 1.2s ease-out' : 'none',
  };

  const expandedPanelStyle = {
    background: '#111',
    borderBottom: `1px solid ${state.color}22`,
    padding: expanded ? '12px 16px' : '0 16px',
    maxHeight: expanded ? '200px' : '0',
    overflow: 'hidden',
    transition: 'all 0.3s ease',
    fontFamily: "'JetBrains Mono', monospace",
    fontSize: '11px',
  };

  const detailRowStyle = {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '3px 0',
    borderBottom: '1px solid #1a1a1a',
  };

  const detailLabelStyle = {
    color: '#666',
    fontSize: '10px',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  };

  const detailValueStyle = {
    color: '#ccc',
    fontSize: '11px',
    fontFamily: "'JetBrains Mono', monospace",
  };

  const hashClickStyle = {
    color: '#c8a000',
    cursor: 'pointer',
    textDecoration: 'none',
    fontSize: '11px',
    fontFamily: "'JetBrains Mono', monospace",
  };

  // Labels by language
  const labels = {
    de: { hash: 'Integritäts-Hash', level: 'Governance-Stufe', sge: 'SGE-Score', receipt: 'Receipt-ID', verify: 'Im Ledger verifizieren ↗' },
    en: { hash: 'Integrity Hash', level: 'Governance Level', sge: 'SGE Score', receipt: 'Receipt ID', verify: 'Verify in Ledger ↗' },
    pt: { hash: 'Hash de Integridade', level: 'Nível de Governança', sge: 'Score SGE', receipt: 'ID do Recibo', verify: 'Verificar no Ledger ↗' },
  };
  const l = labels[lang] || labels.de;

  return (
    <>
      {/* CSS Animation */}
      <style>{`
        @keyframes sealPulse {
          0% { transform: scale(1); opacity: 1; }
          50% { transform: scale(1.05); opacity: 0.8; }
          100% { transform: scale(1); opacity: 1; }
        }
        .seal-bar:hover {
          background: #1f1f1f !important;
        }
        .seal-bar:hover .seal-chevron {
          color: #c8a000 !important;
        }
        .ledger-link:hover {
          color: #e5c100 !important;
          text-decoration: underline !important;
        }
      `}</style>

      {/* ─── Main Seal Bar ─── */}
      <div className="seal-bar" style={sealBarStyle} onClick={handleClick} title={state.label[lang]}>
        
        {/* Diamond + WINDI Badge */}
        <span style={windiBadgeStyle}>
          <span style={{ fontSize: '10px' }}>◆</span>
          WINDI
        </span>

        {/* Receipt ID */}
        <span style={receiptIdStyle}>{sealId(receiptId)}</span>

        {/* Separator */}
        <span style={separatorStyle}>│</span>

        {/* Timestamp */}
        <span style={timestampStyle}>{formatSealTimestamp(timestamp)}</span>

        {/* Separator */}
        <span style={separatorStyle}>│</span>

        {/* Short Hash */}
        <span style={{ color: '#666', fontSize: '10px', fontFamily: "'JetBrains Mono', monospace" }}>
          {shortHash(integrityHash)}
        </span>

        {/* Status Pill (pushed to right) */}
        <span style={statusPillStyle}>
          <span>{state.icon}</span>
          <span>{state.label[lang]}</span>
        </span>

        {/* Chevron */}
        <span className="seal-chevron" style={{ 
          color: '#444', 
          marginLeft: '8px', 
          fontSize: '10px',
          transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)',
          transition: 'transform 0.3s ease',
        }}>
          ▼
        </span>
      </div>

      {/* ─── Expanded Details Panel ─── */}
      <div style={expandedPanelStyle}>
        {expanded && (
          <div>
            {/* Receipt ID */}
            <div style={detailRowStyle}>
              <span style={detailLabelStyle}>{l.receipt}</span>
              <span style={detailValueStyle}>{receiptId || '—'}</span>
            </div>

            {/* Full Hash */}
            <div style={detailRowStyle}>
              <span style={detailLabelStyle}>{l.hash}</span>
              <span style={{ ...detailValueStyle, fontSize: '10px', wordBreak: 'break-all' }}>
                {integrityHash || '—'}
              </span>
            </div>

            {/* Governance Level */}
            <div style={detailRowStyle}>
              <span style={detailLabelStyle}>{l.level}</span>
              <span style={detailValueStyle}>{governanceLevel || 'LOW'}</span>
            </div>

            {/* SGE Score */}
            {sgeScore !== null && (
              <div style={detailRowStyle}>
                <span style={detailLabelStyle}>{l.sge}</span>
                <span style={detailValueStyle}>{sgeScore.toFixed(2)}</span>
              </div>
            )}

            {/* Verify in Ledger Link */}
            {receiptId && ledgerUrl && (
              <div style={{ ...detailRowStyle, borderBottom: 'none', paddingTop: '8px' }}>
                <span 
                  className="ledger-link"
                  style={hashClickStyle} 
                  onClick={handleLedgerLink}
                >
                  {l.verify}
                </span>
              </div>
            )}
          </div>
        )}
      </div>
    </>
  );
}
