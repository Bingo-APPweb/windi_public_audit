import { useState, useEffect, useCallback } from "react";
import WindiDayByDayBlank from "./day-by-day-blank";

// ============================================================
// WINDI DAY-BY-DAY LOADER v1.0
// React Wrapper — Fetches from Express middleware, renders Blank
// "AI processes. Human decides. WINDI guarantees."
//
// USAGE:
//   <WindiDayByDayLoader />
//   <WindiDayByDayLoader apiBase="/api" refreshInterval={60000} />
//   <WindiDayByDayLoader director="Dr. Weber" secretary="S. Bergmann" meeting="09:30" />
// ============================================================

const mono = "'IBM Plex Mono', monospace";

// ============================================================
// STATUS COMPONENT — Shows while loading / on error
// ============================================================

function StatusScreen({ status, message, sources, onRetry }) {
  const isError = status === 'error';
  const isLoading = status === 'loading';

  return (
    <div style={{
      minHeight: "100vh", background: "#eae6de",
      fontFamily: "'Newsreader', Georgia, serif", color: "#1a1814",
      display: "flex", alignItems: "center", justifyContent: "center",
    }}>
      <link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,700&family=IBM+Plex+Mono:wght@400;600;700&display=swap" rel="stylesheet" />

      <div style={{
        background: "#faf8f4", borderRadius: "4px", padding: "40px 48px",
        boxShadow: "0 1px 5px rgba(0,0,0,0.05)", textAlign: "center",
        maxWidth: "440px", width: "100%",
      }}>
        {/* WINDI header */}
        <div style={{ fontSize: "8px", fontFamily: mono, letterSpacing: "3px", color: "#c9a84c", fontWeight: "600", marginBottom: "12px" }}>
          WINDI GOVERNANCE
        </div>

        {/* Status icon */}
        <div style={{ fontSize: "36px", marginBottom: "12px" }}>
          {isLoading ? "◎" : isError ? "◈" : "◉"}
        </div>

        {/* Title */}
        <div style={{ fontSize: "18px", fontWeight: "700", marginBottom: "6px" }}>
          {isLoading ? "Loading Briefing…" : "Connection Issue"}
        </div>

        {/* Message */}
        <div style={{ fontSize: "13px", color: "#8c8578", marginBottom: "16px", lineHeight: 1.5 }}>
          {message}
        </div>

        {/* Source status */}
        {sources && (
          <div style={{ marginBottom: "20px" }}>
            {Object.entries(sources).map(([name, info]) => (
              <div key={name} style={{
                display: "flex", justifyContent: "space-between", alignItems: "center",
                padding: "5px 12px", borderBottom: "1px solid #e8e4dc",
                fontSize: "10px", fontFamily: mono,
              }}>
                <span style={{ color: "#5c5549", textTransform: "uppercase", letterSpacing: "0.5px" }}>
                  {name.replace(/_/g, ' ')}
                </span>
                <span style={{
                  padding: "1px 7px", borderRadius: "3px", fontWeight: "600",
                  background: info.status === 'connected' ? '#f0fdf4' : '#fef2f2',
                  color: info.status === 'connected' ? '#16a34a' : '#dc2626',
                  border: `1px solid ${info.status === 'connected' ? '#bbf7d0' : '#fecaca'}`,
                }}>
                  {info.status === 'connected' ? '● OK' : '○ DOWN'}
                </span>
              </div>
            ))}
          </div>
        )}

        {/* Loading animation */}
        {isLoading && (
          <div style={{ display: "flex", justifyContent: "center", gap: "6px", marginBottom: "16px" }}>
            {[0, 1, 2].map(i => (
              <div key={i} style={{
                width: "6px", height: "6px", borderRadius: "50%", background: "#c9a84c",
                animation: `pulse 1.2s ease-in-out ${i * 0.2}s infinite`,
              }} />
            ))}
          </div>
        )}

        {/* Retry button */}
        {isError && onRetry && (
          <button onClick={onRetry} style={{
            padding: "8px 24px", background: "#1a1814", color: "#faf8f4",
            border: "none", borderRadius: "3px", cursor: "pointer",
            fontSize: "11px", fontWeight: "600", fontFamily: mono, letterSpacing: "0.5px",
          }}>
            RETRY
          </button>
        )}

        {/* Footer */}
        <div style={{ fontSize: "8px", color: "#b0a898", fontFamily: mono, marginTop: "16px" }}>
          Day-by-Day v3.0 · WINDI v1.1 · RFC-003
        </div>
      </div>

      <style>{`
        @keyframes pulse {
          0%, 80%, 100% { opacity: 0.3; transform: scale(0.8); }
          40% { opacity: 1; transform: scale(1.2); }
        }
      `}</style>
    </div>
  );
}

// ============================================================
// MAIN LOADER
// ============================================================

export default function WindiDayByDayLoader({
  apiBase = '/api',            // Base URL for the Express API
  refreshInterval = 0,         // Auto-refresh in ms (0 = disabled)
  director,                    // Override director name
  secretary,                   // Override secretary name
  meeting,                     // Override meeting time
}) {
  const [data, setData] = useState(null);
  const [status, setStatus] = useState('loading'); // loading | ready | error
  const [error, setError] = useState(null);
  const [sources, setSources] = useState(null);

  const fetchBriefing = useCallback(async () => {
    try {
      setStatus('loading');

      // Build query params
      const params = new URLSearchParams();
      if (director)  params.set('director', director);
      if (secretary) params.set('secretary', secretary);
      if (meeting)   params.set('meeting', meeting);

      const url = `${apiBase}/briefing${params.toString() ? '?' + params.toString() : ''}`;
      const res = await fetch(url);

      if (!res.ok) {
        const errBody = await res.json().catch(() => ({}));
        throw new Error(errBody.message || `API returned ${res.status}`);
      }

      const json = await res.json();

      if (!json.success) {
        throw new Error(json.error || 'Unknown API error');
      }

      setData(json.data);
      setSources(json.data._meta?.sources || null);
      setStatus('ready');
      setError(null);
    } catch (err) {
      console.error('[Day-by-Day Loader] Fetch error:', err);
      setError(err.message);
      setStatus('error');

      // Try health check for source status
      try {
        const healthRes = await fetch(`${apiBase}/briefing/health`);
        const health = await healthRes.json();
        setSources(health.sources || null);
      } catch (_) {
        setSources(null);
      }
    }
  }, [apiBase, director, secretary, meeting]);

  // Initial fetch
  useEffect(() => {
    fetchBriefing();
  }, [fetchBriefing]);

  // Auto-refresh
  useEffect(() => {
    if (refreshInterval <= 0 || status === 'loading') return;

    const timer = setInterval(fetchBriefing, refreshInterval);
    return () => clearInterval(timer);
  }, [refreshInterval, fetchBriefing, status]);

  // Status screens
  if (status === 'loading' && !data) {
    return (
      <StatusScreen
        status="loading"
        message="Aggregating governance data from Core, SGE, and Forensic Ledger…"
      />
    );
  }

  if (status === 'error' && !data) {
    return (
      <StatusScreen
        status="error"
        message={error || 'Failed to load briefing data.'}
        sources={sources}
        onRetry={fetchBriefing}
      />
    );
  }

  // Render Blank with real data
  return <WindiDayByDayBlank data={data} />;
}
