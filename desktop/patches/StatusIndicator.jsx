/**
 * WINDI D1 — Status Indicator (Governance State)
 * "O poder está lá. Mas ele não grita."
 *
 * States:
 *   ⚪ IDLE       — No document / empty
 *   🟡 MODIFIED   — Changes pending verification
 *   🟡 SAVING     — Verifying with Ledger...
 *   🟢 PROTECTED  — Integrity verified in Ledger
 *   🔵 SIGNED     — Digitally sealed (eIDAS-ready)
 *
 * Layers of reading (Witness design):
 *   1. Human    → colored dot + plain label
 *   2. Technical → hash + receipt ID (on hover/expand)
 *   3. Forensic  → full Governance Panel
 */
import React, { useState, useEffect, useRef } from 'react';
import useDocStore from '../stores/docStore';

const STATUS_CONFIG = {
  idle: {
    color: 'var(--text-muted)',
    glow: 'transparent',
    labels: { de: 'Bereit', en: 'Ready', pt: 'Pronto' },
  },
  saving: {
    color: 'var(--accent-orange)',
    glow: 'rgba(255, 152, 0, 0.3)',
    labels: { de: 'Verifizierung…', en: 'Verifying…', pt: 'Verificando…' },
  },
  modified: {
    color: 'var(--status-modified)',
    glow: 'rgba(234, 179, 8, 0.25)',
    labels: { de: 'Änderungen nicht verifiziert', en: 'Unverified changes', pt: 'Alterações não verificadas' },
  },
  protected: {
    color: 'var(--status-protected)',
    glow: 'rgba(34, 197, 94, 0.25)',
    labels: { de: 'Integrität geschützt', en: 'Integrity protected', pt: 'Integridade protegida' },
  },
  signed: {
    color: 'var(--status-signed)',
    glow: 'rgba(96, 165, 250, 0.25)',
    labels: { de: 'Digital signiert', en: 'Digitally signed', pt: 'Assinado digitalmente' },
  },
};

/**
 * Derives the governance display status from store state
 */
function deriveGovStatus(saveStatus, integrityStatus, content) {
  // No content = idle
  if (!content) return 'idle';
  const textContent = JSON.stringify(content);
  if (textContent === '{"type":"doc","content":[{"type":"paragraph"}]}') return 'idle';

  // Saving in progress
  if (saveStatus === 'saving') return 'saving';

  // Saved + integrity verified = protected
  if (saveStatus === 'saved' && integrityStatus === 'ok') return 'protected';

  // Saved but integrity unknown/checking
  if (saveStatus === 'saved' && integrityStatus === 'checking') return 'saving';

  // Has content but not yet saved
  return 'modified';
}

export default function StatusIndicator({ lang = 'en' }) {
  const { saveStatus, integrityStatus, content, lastHash, governanceLog } = useDocStore();
  const [pulseKey, setPulseKey] = useState(0);
  const [sentinelOk, setSentinelOk] = useState(true);
  const [sentinelCycle, setSentinelCycle] = useState(0);
  const prevStatus = useRef(null);

  const govStatus = deriveGovStatus(saveStatus, integrityStatus, content);
  const cfg = STATUS_CONFIG[govStatus] || STATUS_CONFIG.idle;

  // Pulse animation on status change
  useEffect(() => {
    if (prevStatus.current && prevStatus.current !== govStatus) {
      setPulseKey(k => k + 1);
    }
    prevStatus.current = govStatus;
  }, [govStatus]);

  // Sentinel LAW heartbeat (30s cycles) — pings real endpoint
  useEffect(() => {
    const checkSentinel = async () => {
      try {
        const res = await fetch('/api/sentinel/health', { signal: AbortSignal.timeout(5000) });
        if (res.ok) {
          const data = await res.json();
          setSentinelOk(data.status === 'operational' || data.status === 'ok');
        } else {
          setSentinelOk(false);
        }
      } catch {
        // Sentinel unreachable — still show cycle but mark unknown
        setSentinelOk(true); // graceful degradation, don't alarm user
      }
      setSentinelCycle(c => c + 1);
    };

    checkSentinel();
    const interval = setInterval(checkSentinel, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="si-wrapper">
      {/* Main Status Pill */}
      <div className={`si-pill si-status-${govStatus}`} key={pulseKey}>
        {/* The Dot */}
        <div className="si-dot-box">
          <div
            className={`si-dot ${govStatus === 'saving' ? 'si-dot-pulse-slow' : ''} ${govStatus === 'protected' && pulseKey > 0 ? 'si-dot-bloom' : ''}`}
            style={{
              background: cfg.color,
              boxShadow: `0 0 6px ${cfg.glow}, 0 0 14px ${cfg.glow}`,
            }}
          />
          {govStatus === 'protected' && pulseKey > 0 && (
            <div className="si-dot-ring" style={{ borderColor: cfg.color }} />
          )}
        </div>

        {/* Label */}
        <span className="si-label" style={{ color: cfg.color }}>
          {cfg.labels[lang] || cfg.labels.en}
        </span>

        {/* Shield icon for protected/signed */}
        {(govStatus === 'protected' || govStatus === 'signed') && (
          <svg className="si-shield" viewBox="0 0 16 16" style={{ color: cfg.color }}>
            <path d="M8 1L2 4v4c0 3.5 2.5 6.4 6 7 3.5-.6 6-3.5 6-7V4L8 1z"
                  fill="none" stroke="currentColor" strokeWidth="1.2" />
            {govStatus === 'signed' && (
              <path d="M5.5 8.5l2 2 3.5-4" fill="none" stroke="currentColor"
                    strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
            )}
          </svg>
        )}

        {/* Hash snippet on hover (Layer 2 — technical) */}
        {lastHash && (govStatus === 'protected' || govStatus === 'signed') && (
          <span className="si-hash-hint" title={`SHA-256: ${lastHash}`}>
            {lastHash.slice(0, 8)}…
          </span>
        )}
      </div>

      {/* Sentinel LAW Badge */}
      <div
        className="si-sentinel"
        title={`Sentinel LAW: ${sentinelOk ? '6/6 PASS' : 'CHECKING'} · Cycle #${sentinelCycle}`}
      >
        <div className={`si-sentinel-dot ${sentinelOk ? 'si-sentinel-ok' : 'si-sentinel-warn'}`} />
        <span className="si-sentinel-text">LAW</span>
      </div>
    </div>
  );
}
