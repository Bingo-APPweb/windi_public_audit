import { useState, useEffect, useRef, useCallback } from "react";

/* ═══════════════════════════════════════════════════════════════════
   WINDI Desktop Trinity — D1 Status Indicator
   "O poder está lá. Mas ele não grita."
   
   Governance States:
     🟢 PROTECTED  — Document integrity verified in Ledger
     🟡 MODIFIED   — Changes pending verification  
     🔵 SIGNED     — Digitally sealed (eIDAS-ready)
     ⚪ IDLE       — No document loaded
   
   Architecture:
     Desktop (:8100) → Ledger (:8101) → Sentinel LAW (:8102)
   ═══════════════════════════════════════════════════════════════════ */

// ── Zustand-like store (self-contained for demo) ──────────────────
const useGovernanceStore = () => {
  const [state, setState] = useState({
    status: "idle",           // idle | modified | saving | protected | signed
    lastReceiptId: null,
    lastHash: null,
    ledgerEntries: [],
    documentContent: "",
    saveTimer: null,
    sentinelOk: true,
    cycleCount: 0,
  });

  const update = useCallback((partial) => {
    setState(prev => ({ ...prev, ...partial }));
  }, []);

  return { ...state, update };
};

// ── Simulated Ledger API (:8101) ──────────────────────────────────
const LedgerAPI = {
  async createReceipt(content) {
    // In production: POST http://localhost:8101/api/receipts
    await new Promise(r => setTimeout(r, 300 + Math.random() * 200));
    const hash = await sha256(content);
    const receiptId = `LE-${new Date().toISOString().replace(/[-:T]/g, '').slice(0, 14)}-${Math.random().toString(36).slice(2, 6).toUpperCase()}`;
    return {
      receipt_id: receiptId,
      hash: hash,
      timestamp: new Date().toISOString(),
      status: "RECEIPT_CREATED",
      chain_valid: true,
    };
  },
  async getHealth() {
    await new Promise(r => setTimeout(r, 50));
    return { status: "operational", chain_integrity: "VALID", unsynced: 0 };
  }
};

async function sha256(message) {
  const msgBuffer = new TextEncoder().encode(message);
  const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

// ── Status Indicator Component ────────────────────────────────────
const StatusIndicator = ({ status, sentinelOk, lastHash, cycleCount }) => {
  const [pulseKey, setPulseKey] = useState(0);
  const prevStatus = useRef(status);

  useEffect(() => {
    if (prevStatus.current !== status) {
      setPulseKey(k => k + 1);
      prevStatus.current = status;
    }
  }, [status]);

  const config = {
    idle: {
      color: "var(--status-idle)",
      glow: "transparent",
      label: { de: "Bereit", en: "Ready", pt: "Pronto" },
      icon: "○",
    },
    modified: {
      color: "var(--status-modified)",
      glow: "rgba(234, 179, 8, 0.25)",
      label: { de: "Änderungen nicht verifiziert", en: "Unverified changes", pt: "Alterações não verificadas" },
      icon: "◐",
    },
    saving: {
      color: "var(--status-modified)",
      glow: "rgba(234, 179, 8, 0.4)",
      label: { de: "Verifizierung…", en: "Verifying…", pt: "Verificando…" },
      icon: "◑",
    },
    protected: {
      color: "var(--status-protected)",
      glow: "rgba(34, 197, 94, 0.25)",
      label: { de: "Integrität geschützt", en: "Integrity protected", pt: "Integridade protegida" },
      icon: "●",
    },
    signed: {
      color: "var(--status-signed)",
      glow: "rgba(96, 165, 250, 0.25)",
      label: { de: "Digital signiert", en: "Digitally signed", pt: "Assinado digitalmente" },
      icon: "◆",
    },
  };

  const c = config[status] || config.idle;
  const [lang] = useState("en");

  return (
    <div className="status-indicator-wrapper">
      <div className="status-indicator" key={pulseKey}>
        {/* The Dot */}
        <div className="status-dot-container">
          <div
            className={`status-dot ${status === "saving" ? "status-dot-spin" : ""} ${status === "protected" && pulseKey > 0 ? "status-dot-pulse" : ""}`}
            style={{
              background: c.color,
              boxShadow: `0 0 8px ${c.glow}, 0 0 20px ${c.glow}`,
            }}
          />
          {status === "protected" && pulseKey > 0 && (
            <div className="status-dot-ring" style={{ borderColor: c.color }} />
          )}
        </div>

        {/* Label */}
        <span className="status-label" style={{ color: c.color }}>
          {c.label[lang]}
        </span>

        {/* Shield micro-icon for protected/signed */}
        {(status === "protected" || status === "signed") && (
          <svg className="status-shield" viewBox="0 0 16 16" style={{ color: c.color }}>
            <path d="M8 1L2 4v4c0 3.5 2.5 6.4 6 7 3.5-.6 6-3.5 6-7V4L8 1z" 
                  fill="none" stroke="currentColor" strokeWidth="1.2" />
            {status === "signed" && (
              <path d="M5.5 8.5l2 2 3.5-4" fill="none" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
            )}
          </svg>
        )}
      </div>

      {/* Sentinel heartbeat */}
      <div className="sentinel-badge" title={`Sentinel LAW: ${sentinelOk ? 'VALID' : 'ALERT'} · Cycle ${cycleCount}`}>
        <div className={`sentinel-dot ${sentinelOk ? 'sentinel-ok' : 'sentinel-alert'}`} />
        <span className="sentinel-text">LAW</span>
      </div>
    </div>
  );
};

// ── Governance Trail (Right Sidebar) ──────────────────────────────
const GovernanceTrail = ({ entries }) => {
  const [expandedId, setExpandedId] = useState(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [entries.length]);

  if (entries.length === 0) {
    return (
      <div className="trail-empty">
        <svg viewBox="0 0 24 24" className="trail-empty-icon">
          <path d="M12 2L4 6v6c0 5.5 3.4 10.7 8 12 4.6-1.3 8-6.5 8-12V6l-8-4z" 
                fill="none" stroke="currentColor" strokeWidth="1.5" />
        </svg>
        <p>Governance Trail</p>
        <span>Events appear here as you write</span>
      </div>
    );
  }

  return (
    <div className="trail-container">
      <div className="trail-header">
        <svg viewBox="0 0 16 16" className="trail-header-icon">
          <path d="M8 1L2 4v4c0 3.5 2.5 6.4 6 7 3.5-.6 6-3.5 6-7V4L8 1z" 
                fill="none" stroke="var(--gold)" strokeWidth="1.2" />
        </svg>
        <span>Governance Trail</span>
        <span className="trail-count">{entries.length}</span>
      </div>
      <div className="trail-list">
        {entries.map((entry, i) => (
          <div key={entry.receipt_id} className="trail-entry" style={{ animationDelay: `${i * 0.05}s` }}>
            {/* Human-readable layer */}
            <div className="trail-entry-human" onClick={() => setExpandedId(expandedId === entry.receipt_id ? null : entry.receipt_id)}>
              <div className="trail-entry-icon"><svg width="14" height="14" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M10 2L3 5V10C3 14.4 6 18 10 19C14 18 17 14.4 17 10V5L10 2Z"/></svg></div>
              <div className="trail-entry-info">
                <span className="trail-entry-label">
                  {entry.status === "RECEIPT_CREATED" ? "Integrity Checkpoint" : 
                   entry.status === "SIGNED" ? "Digital Seal Applied" : entry.status}
                </span>
                <span className="trail-entry-time">
                  {new Date(entry.timestamp).toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                </span>
              </div>
              <div className={`trail-expand ${expandedId === entry.receipt_id ? 'trail-expand-open' : ''}`}>
                ▸
              </div>
            </div>

            {/* Technical layer (collapsed by default) */}
            {expandedId === entry.receipt_id && (
              <div className="trail-entry-technical">
                <div className="trail-tech-row">
                  <span className="trail-tech-label">Receipt</span>
                  <code className="trail-tech-value">{entry.receipt_id}</code>
                </div>
                <div className="trail-tech-row">
                  <span className="trail-tech-label">SHA-256</span>
                  <code className="trail-tech-value trail-hash">{entry.hash.slice(0, 12)}…{entry.hash.slice(-8)}</code>
                </div>
                <div className="trail-tech-row">
                  <span className="trail-tech-label">Chain</span>
                  <code className="trail-tech-value" style={{ color: entry.chain_valid ? 'var(--status-protected)' : 'var(--status-alert)' }}>
                    {entry.chain_valid ? 'VALID' : 'BROKEN'}
                  </code>
                </div>
              </div>
            )}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
};

// ── Sign Button (A Porta Dourada) ─────────────────────────────────
const SignButton = ({ enabled, onSign, signed }) => {
  const [hover, setHover] = useState(false);
  
  return (
    <button
      className={`sign-button ${enabled ? 'sign-enabled' : ''} ${signed ? 'sign-completed' : ''}`}
      disabled={!enabled || signed}
      onClick={onSign}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      title={signed ? "Sealed with legal validity (eIDAS)" : enabled ? "Seal with legal validity (eIDAS)" : "Write content first"}
    >
      <svg viewBox="0 0 20 20" className="sign-icon">
        <path d="M10 2L3 5.5v5c0 4.1 3 7.5 7 8.5 4-1 7-4.4 7-8.5v-5L10 2z" 
              fill="none" stroke="currentColor" strokeWidth="1.4" />
        {signed && (
          <path d="M7 10.5l2.5 2.5L14 8" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
        )}
      </svg>
      <span>{signed ? "Sealed" : "Sign"}</span>
      {hover && enabled && !signed && (
        <div className="sign-tooltip">Seal with legal validity (eIDAS)</div>
      )}
    </button>
  );
};

// ── Main Desktop D1 Component ─────────────────────────────────────
export default function WindiDesktopD1() {
  const store = useGovernanceStore();
  const [theme, setTheme] = useState("noir");
  const editorRef = useRef(null);
  const autoSaveRef = useRef(null);
  const sentinelRef = useRef(null);

  // ── Auto-save with Ledger integration ───────────────────────────
  const saveToLedger = useCallback(async (content) => {
    if (!content.trim()) return;
    
    store.update({ status: "saving" });
    
    try {
      const receipt = await LedgerAPI.createReceipt(content);
      store.update({
        status: "protected",
        lastReceiptId: receipt.receipt_id,
        lastHash: receipt.hash,
        ledgerEntries: [...store.ledgerEntries, receipt],
      });
    } catch (err) {
      store.update({ status: "modified" });
      console.error("Ledger save failed:", err);
    }
  }, [store.ledgerEntries]);

  // ── Editor change handler ───────────────────────────────────────
  const handleEditorChange = useCallback((e) => {
    const content = e.target.innerText;
    store.update({ documentContent: content, status: content.trim() ? "modified" : "idle" });
    
    // Debounced auto-save (2s after last keystroke)
    if (autoSaveRef.current) clearTimeout(autoSaveRef.current);
    if (content.trim()) {
      autoSaveRef.current = setTimeout(() => saveToLedger(content), 2000);
    }
  }, [saveToLedger]);

  // ── Sign handler ────────────────────────────────────────────────
  const handleSign = useCallback(async () => {
    if (store.status !== "protected") return;
    store.update({ status: "saving" });
    
    await new Promise(r => setTimeout(r, 800));
    const signedEntry = {
      receipt_id: `SEAL-${Date.now().toString(36).toUpperCase()}`,
      hash: store.lastHash,
      timestamp: new Date().toISOString(),
      status: "SIGNED",
      chain_valid: true,
    };
    store.update({
      status: "signed",
      ledgerEntries: [...store.ledgerEntries, signedEntry],
    });
  }, [store.status, store.lastHash, store.ledgerEntries]);

  // ── Sentinel LAW simulation (30s cycles) ────────────────────────
  useEffect(() => {
    const runCycle = () => {
      store.update(prev => ({
        ...prev,
        sentinelOk: true,
        cycleCount: (prev?.cycleCount || store.cycleCount) + 1,
      }));
    };
    runCycle();
    sentinelRef.current = setInterval(runCycle, 30000);
    return () => clearInterval(sentinelRef.current);
  }, []);

  const isNoir = theme === "noir";

  return (
    <div className={`windi-desktop ${isNoir ? '' : 'klar'}`}>
      <style>{`
        /* ═══════════════════════════════════════════════════════════
           WINDI DESIGN SYSTEM — Noir + Klar
           Fonts: Bricolage Grotesque · Outfit · JetBrains Mono
           ═══════════════════════════════════════════════════════════ */
        @import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@300;400;600;700;800&family=Outfit:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

        :root {
          --bg-primary: #0a0a0f;
          --bg-secondary: #111118;
          --bg-card: #18181f;
          --bg-editor: #0e0e14;
          --bg-input: #1e1e28;
          --border: #2a2a3a;
          --border-subtle: #1e1e2e;
          --gold: #c9a84c;
          --gold-light: #e8d48b;
          --gold-dim: #8a7535;
          --gold-glow: rgba(201, 168, 76, 0.12);
          --text-primary: #e2e8f0;
          --text-secondary: #8888a0;
          --text-muted: #555568;
          --status-protected: #22c55e;
          --status-modified: #eab308;
          --status-signed: #60a5fa;
          --status-idle: #555568;
          --status-alert: #ef4444;

          /* R0-R5 Governance Palette (harmonized with Noir) */
          --r0-integrity: #f0e6c8;    /* Pale gold — verified purity */
          --r1-low: #c9a84c;          /* Gold — minimal attention */
          --r2-moderate: #d4943a;     /* Deep amber */
          --r3-alert: #b87333;        /* Burnished copper */
          --r4-high: #a04040;         /* Oxidized red */
          --r5-critical: #8b2020;     /* Deep crimson — not alarm, gravity */
        }

        .klar {
          --bg-primary: #f5f2ec;
          --bg-secondary: #eae6dc;
          --bg-card: #ffffff;
          --bg-editor: #faf8f4;
          --bg-input: #f0ece4;
          --border: #d0ccc0;
          --border-subtle: #e0dcd4;
          --gold: #9a7b10;
          --gold-light: #7a6510;
          --gold-dim: #b8930e;
          --gold-glow: rgba(154, 123, 16, 0.08);
          --text-primary: #1a1a2e;
          --text-secondary: #5a5a6a;
          --text-muted: #8a8a9a;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        .windi-desktop {
          font-family: 'Outfit', sans-serif;
          background: var(--bg-primary);
          color: var(--text-primary);
          height: 100vh;
          display: flex;
          flex-direction: column;
          overflow: hidden;
          transition: background 0.4s ease, color 0.4s ease;
        }

        /* Subtle atmospheric gradient */
        .windi-desktop::before {
          content: '';
          position: fixed;
          inset: 0;
          background: radial-gradient(ellipse at 15% 50%, var(--gold-glow) 0%, transparent 50%),
                      radial-gradient(ellipse at 85% 15%, rgba(201,168,76,0.04) 0%, transparent 40%);
          pointer-events: none;
          z-index: 0;
        }

        /* ── TOP BAR ─────────────────────────────────────────── */
        .topbar {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0 20px;
          height: 48px;
          border-bottom: 1px solid var(--border);
          background: var(--bg-secondary);
          position: relative;
          z-index: 10;
          flex-shrink: 0;
        }

        .topbar-left {
          display: flex;
          align-items: center;
          gap: 16px;
        }

        .topbar-logo {
          font-family: 'Bricolage Grotesque', sans-serif;
          font-weight: 700;
          font-size: 0.95rem;
          color: var(--gold);
          letter-spacing: 0.08em;
          user-select: none;
        }

        .topbar-logo span {
          color: var(--text-muted);
          font-weight: 400;
          font-size: 0.7rem;
          margin-left: 6px;
          letter-spacing: 0;
          font-family: 'JetBrains Mono', monospace;
        }

        .topbar-right {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .topbar-btn {
          padding: 5px 12px;
          background: transparent;
          border: 1px solid var(--border);
          border-radius: 6px;
          color: var(--text-secondary);
          font-family: 'Outfit', sans-serif;
          font-size: 0.72rem;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .topbar-btn:hover {
          border-color: var(--gold);
          color: var(--gold);
        }

        /* ── STATUS INDICATOR ─────────────────────────────────── */
        .status-indicator-wrapper {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .status-indicator {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 4px 12px;
          border-radius: 20px;
          background: rgba(255,255,255,0.03);
          border: 1px solid var(--border-subtle);
          transition: all 0.3s ease;
        }

        .klar .status-indicator {
          background: rgba(0,0,0,0.03);
        }

        .status-dot-container {
          position: relative;
          width: 10px;
          height: 10px;
        }

        .status-dot {
          width: 10px;
          height: 10px;
          border-radius: 50%;
          transition: background 0.4s ease, box-shadow 0.4s ease;
        }

        .status-dot-spin {
          animation: dotSpin 1.2s linear infinite;
        }

        @keyframes dotSpin {
          0% { opacity: 1; }
          50% { opacity: 0.4; }
          100% { opacity: 1; }
        }

        .status-dot-pulse {
          animation: dotPulse 0.6s cubic-bezier(0.22, 1, 0.36, 1) forwards;
        }

        @keyframes dotPulse {
          0% { transform: scale(1); }
          30% { transform: scale(1.4); }
          100% { transform: scale(1); }
        }

        .status-dot-ring {
          position: absolute;
          inset: -4px;
          border: 1.5px solid;
          border-radius: 50%;
          animation: ringExpand 0.8s cubic-bezier(0.22, 1, 0.36, 1) forwards;
          opacity: 0;
        }

        @keyframes ringExpand {
          0% { transform: scale(0.5); opacity: 0.8; }
          100% { transform: scale(2); opacity: 0; }
        }

        .status-label {
          font-family: 'Outfit', sans-serif;
          font-size: 0.72rem;
          font-weight: 500;
          letter-spacing: 0.02em;
          transition: color 0.4s ease;
          white-space: nowrap;
        }

        .status-shield {
          width: 14px;
          height: 14px;
          opacity: 0.7;
          animation: shieldAppear 0.4s ease forwards;
        }

        @keyframes shieldAppear {
          from { opacity: 0; transform: scale(0.8); }
          to { opacity: 0.7; transform: scale(1); }
        }

        /* ── SENTINEL BADGE ───────────────────────────────────── */
        .sentinel-badge {
          display: flex;
          align-items: center;
          gap: 4px;
          padding: 2px 8px;
          border-radius: 4px;
          background: rgba(255,255,255,0.02);
          cursor: default;
        }

        .sentinel-dot {
          width: 5px;
          height: 5px;
          border-radius: 50%;
        }

        .sentinel-ok {
          background: var(--status-protected);
          box-shadow: 0 0 4px rgba(34, 197, 94, 0.4);
          animation: sentinelPulse 30s ease-in-out infinite;
        }

        @keyframes sentinelPulse {
          0%, 97% { opacity: 0.6; }
          98% { opacity: 1; transform: scale(1.3); }
          100% { opacity: 0.6; transform: scale(1); }
        }

        .sentinel-alert {
          background: var(--status-alert);
          animation: sentinelAlert 0.5s ease infinite;
        }

        @keyframes sentinelAlert {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.3; }
        }

        .sentinel-text {
          font-family: 'JetBrains Mono', monospace;
          font-size: 0.58rem;
          color: var(--text-muted);
          letter-spacing: 0.1em;
        }

        /* ── MAIN LAYOUT ──────────────────────────────────────── */
        .main-content {
          flex: 1;
          display: flex;
          overflow: hidden;
          position: relative;
          z-index: 1;
        }

        /* ── EDITOR ───────────────────────────────────────────── */
        .editor-panel {
          flex: 1;
          display: flex;
          flex-direction: column;
          border-right: 1px solid var(--border);
        }

        .editor-toolbar {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 8px 20px;
          border-bottom: 1px solid var(--border-subtle);
          background: var(--bg-secondary);
        }

        .toolbar-btn {
          padding: 4px 8px;
          background: transparent;
          border: 1px solid transparent;
          border-radius: 4px;
          color: var(--text-muted);
          font-size: 0.78rem;
          cursor: pointer;
          transition: all 0.15s ease;
          font-weight: 600;
        }

        .toolbar-btn:hover {
          border-color: var(--border);
          color: var(--text-secondary);
          background: rgba(255,255,255,0.03);
        }

        .toolbar-sep {
          width: 1px;
          height: 16px;
          background: var(--border-subtle);
          margin: 0 4px;
        }

        .editor-area {
          flex: 1;
          padding: 40px 60px;
          overflow-y: auto;
          background: var(--bg-editor);
        }

        .editor-content {
          max-width: 680px;
          margin: 0 auto;
          min-height: 300px;
          font-family: 'Outfit', sans-serif;
          font-size: 1rem;
          line-height: 1.75;
          color: var(--text-primary);
          outline: none;
          caret-color: var(--gold);
        }

        .editor-content:empty::before {
          content: 'Begin typing. Your integrity will be protected automatically.';
          color: var(--text-muted);
          font-style: italic;
          pointer-events: none;
        }

        .editor-content:focus:empty::before {
          content: 'Writing… governance is active.';
        }

        /* ── GOVERNANCE TRAIL (Right Sidebar) ─────────────────── */
        .trail-panel {
          width: 300px;
          display: flex;
          flex-direction: column;
          background: var(--bg-secondary);
          flex-shrink: 0;
        }

        .trail-empty {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          height: 100%;
          text-align: center;
          padding: 20px;
        }

        .trail-empty-icon {
          width: 40px;
          height: 40px;
          color: var(--text-muted);
          opacity: 0.3;
          margin-bottom: 12px;
        }

        .trail-empty p {
          font-family: 'Bricolage Grotesque', sans-serif;
          font-size: 0.85rem;
          font-weight: 600;
          color: var(--text-muted);
          margin-bottom: 4px;
        }

        .trail-empty span {
          font-size: 0.72rem;
          color: var(--text-muted);
          opacity: 0.6;
        }

        .trail-header {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 12px 16px;
          border-bottom: 1px solid var(--border-subtle);
          font-family: 'Bricolage Grotesque', sans-serif;
          font-size: 0.78rem;
          font-weight: 600;
          color: var(--text-secondary);
        }

        .trail-header-icon {
          width: 14px;
          height: 14px;
        }

        .trail-count {
          margin-left: auto;
          font-family: 'JetBrains Mono', monospace;
          font-size: 0.65rem;
          color: var(--gold-dim);
          background: var(--gold-glow);
          padding: 1px 6px;
          border-radius: 10px;
        }

        .trail-list {
          flex: 1;
          overflow-y: auto;
          padding: 8px;
        }

        .trail-entry {
          border-radius: 8px;
          margin-bottom: 4px;
          animation: trailSlideIn 0.3s ease forwards;
          opacity: 0;
          transform: translateY(8px);
        }

        @keyframes trailSlideIn {
          to { opacity: 1; transform: translateY(0); }
        }

        .trail-entry-human {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 10px 12px;
          cursor: pointer;
          border-radius: 8px;
          transition: background 0.15s ease;
        }

        .trail-entry-human:hover {
          background: rgba(255,255,255,0.03);
        }

        .klar .trail-entry-human:hover {
          background: rgba(0,0,0,0.03);
        }

        .trail-entry-icon {
          font-size: 0.85rem;
          flex-shrink: 0;
        }

        .trail-entry-info {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 2px;
          min-width: 0;
        }

        .trail-entry-label {
          font-size: 0.75rem;
          font-weight: 500;
          color: var(--text-primary);
        }

        .trail-entry-time {
          font-family: 'JetBrains Mono', monospace;
          font-size: 0.62rem;
          color: var(--text-muted);
        }

        .trail-expand {
          font-size: 0.65rem;
          color: var(--text-muted);
          transition: transform 0.2s ease;
        }

        .trail-expand-open {
          transform: rotate(90deg);
        }

        /* ── Technical details (collapsed) ────────────────────── */
        .trail-entry-technical {
          padding: 0 12px 10px 38px;
          animation: techReveal 0.2s ease forwards;
        }

        @keyframes techReveal {
          from { opacity: 0; max-height: 0; }
          to { opacity: 1; max-height: 120px; }
        }

        .trail-tech-row {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 3px 0;
        }

        .trail-tech-label {
          font-family: 'Outfit', sans-serif;
          font-size: 0.62rem;
          color: var(--text-muted);
          width: 52px;
          flex-shrink: 0;
        }

        .trail-tech-value {
          font-family: 'JetBrains Mono', monospace;
          font-size: 0.62rem;
          color: var(--text-secondary);
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .trail-hash {
          color: var(--gold-dim);
        }

        /* ── SIGN BUTTON (A Porta Dourada) ────────────────────── */
        .sign-button {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 6px 14px;
          background: transparent;
          border: 1.5px solid var(--border);
          border-radius: 8px;
          color: var(--text-muted);
          font-family: 'Outfit', sans-serif;
          font-size: 0.78rem;
          font-weight: 500;
          cursor: not-allowed;
          transition: all 0.3s ease;
          position: relative;
        }

        .sign-icon {
          width: 16px;
          height: 16px;
        }

        .sign-enabled {
          border-color: var(--gold);
          color: var(--gold);
          cursor: pointer;
          box-shadow: 0 0 0 0 var(--gold-glow);
        }

        .sign-enabled:hover {
          background: var(--gold-glow);
          box-shadow: 0 0 16px var(--gold-glow), 0 0 32px rgba(201,168,76,0.06);
          transform: translateY(-1px);
        }

        .sign-completed {
          border-color: var(--status-signed);
          color: var(--status-signed);
          cursor: default;
        }

        .sign-completed:hover {
          transform: none;
          box-shadow: none;
          background: transparent;
        }

        .sign-tooltip {
          position: absolute;
          bottom: calc(100% + 8px);
          right: 0;
          padding: 6px 10px;
          background: var(--bg-card);
          border: 1px solid var(--border);
          border-radius: 6px;
          font-size: 0.68rem;
          color: var(--text-secondary);
          white-space: nowrap;
          pointer-events: none;
          animation: tooltipFade 0.2s ease forwards;
        }

        @keyframes tooltipFade {
          from { opacity: 0; transform: translateY(4px); }
          to { opacity: 1; transform: translateY(0); }
        }

        /* ── FOOTER STATUS BAR ────────────────────────────────── */
        .footer-bar {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 4px 16px;
          border-top: 1px solid var(--border-subtle);
          background: var(--bg-secondary);
          font-family: 'JetBrains Mono', monospace;
          font-size: 0.6rem;
          color: var(--text-muted);
          flex-shrink: 0;
          position: relative;
          z-index: 1;
        }

        .footer-left, .footer-right {
          display: flex;
          align-items: center;
          gap: 16px;
        }

        /* ── SCROLLBAR ────────────────────────────────────────── */
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }

        /* ── R0-R5 PREVIEW STRIP ──────────────────────────────── */
        .r-scale-strip {
          display: flex;
          gap: 3px;
          padding: 4px 0;
        }

        .r-scale-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          transition: transform 0.2s ease;
        }

        .r-scale-dot:hover {
          transform: scale(1.4);
        }
      `}</style>

      {/* ── TOP BAR ─────────────────────────────────────────── */}
      <div className="topbar">
        <div className="topbar-left">
          <div className="topbar-logo">
            WINDI<span>Desktop D1</span>
          </div>

          {/* ★ THE STATUS INDICATOR ★ */}
          <StatusIndicator
            status={store.status}
            sentinelOk={store.sentinelOk}
            lastHash={store.lastHash}
            cycleCount={store.cycleCount}
          />
        </div>

        <div className="topbar-right">
          {/* R0-R5 Scale Preview */}
          <div className="r-scale-strip" title="SGE Governance Scale (R0-R5)">
            {[
              { level: 'R0', color: 'var(--r0-integrity)', tip: 'R0 — Total Integrity' },
              { level: 'R1', color: 'var(--r1-low)', tip: 'R1 — Low Risk' },
              { level: 'R2', color: 'var(--r2-moderate)', tip: 'R2 — Moderate' },
              { level: 'R3', color: 'var(--r3-alert)', tip: 'R3 — Semantic Alert' },
              { level: 'R4', color: 'var(--r4-high)', tip: 'R4 — High Risk' },
              { level: 'R5', color: 'var(--r5-critical)', tip: 'R5 — Critical' },
            ].map(r => (
              <div
                key={r.level}
                className="r-scale-dot"
                style={{ background: r.color }}
                title={r.tip}
              />
            ))}
          </div>

          <button className="topbar-btn" onClick={() => setTheme(t => t === "noir" ? "klar" : "noir")}>
            {isNoir ? "☀" : "☾"}
          </button>

          <button className="topbar-btn">Export</button>

          <SignButton
            enabled={store.status === "protected"}
            signed={store.status === "signed"}
            onSign={handleSign}
          />
        </div>
      </div>

      {/* ── MAIN CONTENT ────────────────────────────────────── */}
      <div className="main-content">
        {/* Editor */}
        <div className="editor-panel">
          <div className="editor-toolbar">
            <button className="toolbar-btn"><b>B</b></button>
            <button className="toolbar-btn"><i>I</i></button>
            <button className="toolbar-btn"><u>U</u></button>
            <div className="toolbar-sep" />
            <button className="toolbar-btn">H1</button>
            <button className="toolbar-btn">H2</button>
            <div className="toolbar-sep" />
            <button className="toolbar-btn">¶</button>
            <button className="toolbar-btn">≡</button>
          </div>

          <div className="editor-area">
            <div
              ref={editorRef}
              className="editor-content"
              contentEditable
              suppressContentEditableWarning
              onInput={handleEditorChange}
              spellCheck="true"
            />
          </div>
        </div>

        {/* Governance Trail */}
        <div className="trail-panel">
          <GovernanceTrail entries={store.ledgerEntries} />
        </div>
      </div>

      {/* ── FOOTER ──────────────────────────────────────────── */}
      <div className="footer-bar">
        <div className="footer-left">
          <span>D1 Foundation v1.0</span>
          <span>•</span>
          <span>Ledger :8101</span>
          <span>•</span>
          <span>Sentinel :8102</span>
        </div>
        <div className="footer-right">
          <span>{store.ledgerEntries.length} receipts</span>
          <span>•</span>
          <span>LAW cycle #{store.cycleCount}</span>
          <span>•</span>
          <span style={{ color: store.sentinelOk ? 'var(--status-protected)' : 'var(--status-alert)' }}>
            {store.sentinelOk ? '6/6 PASS' : 'VIOLATION'}
          </span>
        </div>
      </div>
    </div>
  );
}
