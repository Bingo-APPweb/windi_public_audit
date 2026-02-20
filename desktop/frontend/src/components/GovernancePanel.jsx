/**
 * WINDI D1 — Governance Panel
 * Shows audit trail, integrity verification, receipt log
 * "Invisible by default, available when needed"
 */
import React from 'react';
import useDocStore from '../stores/docStore';

export default function GovernancePanel({ visible, onClose }) {
  const { docId, lastHash, integrityStatus, governanceLog, verifyIntegrity } = useDocStore();

  if (!visible) return null;

  return (
    <div className="d1-governance-panel">
      <div className="gov-header">
        <h3>Governance Trail</h3>
        <button className="btn-close" onClick={onClose}>×</button>
      </div>

      <div className="gov-status">
        <div className="gov-stat-row">
          <span className="gov-label">Document</span>
          <span className="gov-value mono">{docId || '—'}</span>
        </div>
        <div className="gov-stat-row">
          <span className="gov-label">Current Hash</span>
          <span className="gov-value mono" title={lastHash}>
            {lastHash ? lastHash.slice(0, 16) + '...' : '—'}
          </span>
        </div>
        <div className="gov-stat-row">
          <span className="gov-label">Integrity</span>
          <span className={`gov-value integrity-${integrityStatus}`}>
            {integrityStatus === 'ok' && '🟢 Verified'}
            {integrityStatus === 'mismatch' && '🔴 MISMATCH — Investigate'}
            {integrityStatus === 'checking' && '⟳ Checking...'}
            {integrityStatus === 'unknown' && '◌ Not verified'}
          </span>
        </div>
        <button className="btn-verify" onClick={verifyIntegrity} disabled={!docId}>
          Verify Integrity
        </button>
      </div>

      <div className="gov-log">
        <h4>Receipt Log ({governanceLog.length})</h4>
        {governanceLog.length === 0 ? (
          <p className="gov-empty">No governance events recorded yet.</p>
        ) : (
          <ul className="receipt-list">
            {[...governanceLog].reverse().map((r, i) => (
              <li key={r.receipt_id || i} className={`receipt-item status-${r.reconciliation_status?.toLowerCase()}`}>
                <div className="receipt-header">
                  <span className="receipt-action">{r.action}</span>
                  <span className={`receipt-status ${r.reconciliation_status?.toLowerCase()}`}>
                    {r.reconciliation_status}
                  </span>
                </div>
                <div className="receipt-details">
                  <span className="mono">{r.integrity_hash?.slice(0, 24)}...</span>
                  <span className="receipt-time">
                    {new Date(r.timestamp).toLocaleTimeString('de-DE')}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
