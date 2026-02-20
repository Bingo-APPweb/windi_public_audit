/**
 * WINDI D1 — A4 Page Wrapper
 * ═══════════════════════════════════
 * Wraps the Tiptap editor in a paper-like A4 page.
 * Includes: Seal (M3) + Ruler (Witness) + Content + Footer
 * 
 * Reference: LibreOffice Writer page view
 * "The document looks normal. But every letter carries its birth certificate."
 */

import React from 'react';
import DocumentSeal from './DocumentSeal';

// ═══════════════════════════════════════════
// RULER COMPONENT (Witness idea: Integrity Ruler)
// ═══════════════════════════════════════════
function A4Ruler({ integrityState = 'ok' }) {
  // Generate ruler marks (cm scale, A4 = 21cm wide, minus 5cm margins = 16cm content)
  const marks = [];
  const contentWidthCm = 16;
  
  for (let cm = 0; cm <= contentWidthCm; cm++) {
    const pct = (cm / contentWidthCm) * 100;
    marks.push(
      <React.Fragment key={cm}>
        <div
          className="ruler-mark major"
          style={{ left: `${pct}%` }}
        />
        <span
          className="ruler-number"
          style={{ left: `${pct}%` }}
        >
          {cm}
        </span>
        {cm < contentWidthCm && (
          <div
            className="ruler-mark minor"
            style={{ left: `${pct + (100 / contentWidthCm / 2)}%` }}
          />
        )}
      </React.Fragment>
    );
  }

  const stateClass = 
    integrityState === 'ok' ? 'integrity-ok' :
    integrityState === 'pending' ? 'integrity-pending' :
    integrityState === 'compromised' ? 'integrity-compromised' : '';

  return (
    <div className={`a4-ruler ${stateClass}`}>
      <div className="ruler-marks">
        {marks}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════
// PAGE FOOTER
// ═══════════════════════════════════════════
function A4Footer({ docId, pageNum = 1 }) {
  return (
    <div className="a4-page-footer">
      <span className="footer-windi">WINDI Desktop — DOC</span>
      <span>{docId ? `ID: ${docId.substring(0, 8)}…` : ''}</span>
      <span>Seite {pageNum}</span>
    </div>
  );
}

// ═══════════════════════════════════════════
// MAIN A4 PAGE WRAPPER
// ═══════════════════════════════════════════
export default function A4PageWrapper({
  children,
  // Seal props
  sealReceiptId,
  sealHash,
  sealTimestamp,
  sealStatus = 'DRAFT',
  sealSgeScore,
  sealGovernanceLevel,
  sealLang = 'de',
  // Page props
  docId,
  integrityState = 'ok',  // ok | pending | compromised
  showRuler = true,
}) {
  return (
    <div className="a4-page-wrapper">
      {/* ─── Document Seal (M3) — on the paper ─── */}
      <div className="seal-on-paper">
        <DocumentSeal
          receiptId={sealReceiptId}
          integrityHash={sealHash}
          timestamp={sealTimestamp}
          status={sealStatus}
          sgeScore={sealSgeScore}
          governanceLevel={sealGovernanceLevel}
          lang={sealLang}
          ledgerUrl="/desktop/api/ledger/receipts"
        />
      </div>

      {/* ─── Integrity Ruler (Witness) ─── */}
      {showRuler && <A4Ruler integrityState={integrityState} />}

      {/* ─── Document Content ─── */}
      <div className="a4-content">
        {children}
      </div>

      {/* ─── Page Footer ─── */}
      <A4Footer docId={docId} />
    </div>
  );
}
