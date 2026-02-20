/**
 * WINDI Desktop — Forensic Vault Button Integration
 * 
 * Replace the receipt listing in the Desktop with this elegant indicator.
 * Add to your React header component.
 * 
 * Usage:
 *   import VaultButton from './VaultButton';
 *   <VaultButton />
 */

import { useState, useEffect } from 'react';

const VAULT_API = '/vault/api';

export default function VaultButton() {
  const [stats, setStats] = useState({ total: 0, chain_ok: true });
  const [pulse, setPulse] = useState(false);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await fetch(`${VAULT_API}/stats`);
        const data = await res.json();
        setStats(data);
        // Pulse animation when new receipts arrive
        setPulse(true);
        setTimeout(() => setPulse(false), 1000);
      } catch (err) {
        console.warn('Vault stats unavailable:', err);
      }
    };

    fetchStats();
    // Refresh every 60s
    const interval = setInterval(fetchStats, 60000);
    return () => clearInterval(interval);
  }, []);

  const handleClick = () => {
    window.open('/vault/', '_blank');
  };

  return (
    <button
      onClick={handleClick}
      title="Open Forensic Vault — Governance Audit Room"
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        padding: '6px 14px',
        background: 'var(--bg-tertiary, #1a1a1f)',
        border: `1px solid ${stats.chain_ok ? 'var(--gold, #c9a84c)' : 'var(--red, #f87171)'}`,
        borderRadius: '8px',
        color: 'var(--gold, #c9a84c)',
        fontFamily: "'JetBrains Mono', monospace",
        fontSize: '12px',
        fontWeight: 500,
        cursor: 'pointer',
        transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
        animation: pulse ? 'vaultPulse 0.6s ease' : 'none',
        whiteSpace: 'nowrap',
      }}
      onMouseOver={(e) => {
        e.target.style.background = 'var(--gold-dim, #c9a84c22)';
        e.target.style.transform = 'translateY(-1px)';
      }}
      onMouseOut={(e) => {
        e.target.style.background = 'var(--bg-tertiary, #1a1a1f)';
        e.target.style.transform = 'translateY(0)';
      }}
    >
      <span>🔐</span>
      <span>Vault</span>
      <span style={{
        background: stats.chain_ok ? 'var(--green-dim, #4ade8020)' : 'var(--red-dim, #f8717120)',
        color: stats.chain_ok ? 'var(--green, #4ade80)' : 'var(--red, #f87171)',
        padding: '1px 8px',
        borderRadius: '12px',
        fontSize: '11px',
      }}>
        {stats.total?.toLocaleString() || '—'}
      </span>
    </button>
  );
}

/*
 * Add this CSS animation to your global styles:
 *
 * @keyframes vaultPulse {
 *   0% { box-shadow: 0 0 0 0 rgba(201, 168, 76, 0.4); }
 *   70% { box-shadow: 0 0 0 10px rgba(201, 168, 76, 0); }
 *   100% { box-shadow: 0 0 0 0 rgba(201, 168, 76, 0); }
 * }
 */
