// ============================================================
// WINDI DAY-BY-DAY — SERVER MOUNT EXAMPLE
// Add to your main Express app on Strato
// ============================================================

const express = require('express');
const app = express();

// Mount the Day-by-Day API aggregator
const dayByDayApi = require('./day-by-day-api');
app.use('/api', dayByDayApi);
app.use('/war-room', express.static('warroom'));

// ── WINDI Dispatcher & PDF Virtue Receipt Engine ──
app.use(express.json());
const pdfRoute = require('./windi-dispatcher/pdf-virtue-receipt');
const dispatchRoute = require('./windi-dispatcher/dispatch-route');
app.use('/api', pdfRoute);
app.use('/api', dispatchRoute);

// ============================================================
// AVAILABLE ENDPOINTS:
//
//   GET  /api/briefing              → Aggregated briefing data
//   GET  /api/briefing?nocache=1    → Force fresh aggregation
//   GET  /api/briefing?director=Dr.+Weber&secretary=S.+Bergmann&meeting=09:30
//   GET  /api/briefing/health       → Source connectivity check
//   POST /api/briefing/notes        → Inject secretary notes
//   POST /api/briefing/agenda       → Inject agenda items
//   POST /api/briefing/actions      → Inject action items
//
// ============================================================
// ENVIRONMENT VARIABLES (optional):
//
//   WINDI_GOVERNANCE_URL=http://127.0.0.1:8080
//   WINDI_SGE_URL=http://127.0.0.1:8083
//   WINDI_LEDGER_URL=http://127.0.0.1:8080
//   WINDI_CACHE_TTL=30000
//   WINDI_TIMEOUT=5000
//   WINDI_DIRECTOR=Dr. M. Weber
//   WINDI_SECRETARY=S. Bergmann
//
// ============================================================
// REACT USAGE:
//
//   import WindiDayByDayLoader from './day-by-day-loader';
//
//   // Basic — fetches from /api/briefing
//   <WindiDayByDayLoader />
//
//   // With overrides
//   <WindiDayByDayLoader
//     apiBase="/api"
//     director="Dr. M. Weber"
//     secretary="S. Bergmann"
//     meeting="09:30"
//     refreshInterval={60000}  // auto-refresh every 60s
//   />
//
// ============================================================
// DATA FLOW:
//
//   ┌──────────────────┐
//   │  React Frontend   │
//   │  (day-by-day-     │
//   │   loader.jsx)     │
//   └────────┬─────────┘
//            │ GET /api/briefing
//            ▼
//   ┌──────────────────┐
//   │  Express Router   │
//   │  (day-by-day-     │
//   │   api.js)         │
//   │                   │
//   │  ┌─ Parallel ──┐  │
//   │  │             │  │
//   │  ▼   ▼   ▼    │  │
//   │ :8080 :8083 LDG │  │
//   │  GOV  SGE  LED  │  │
//   │  │             │  │
//   │  └─ Merge ─────┘  │
//   │       │            │
//   │  Transform to      │
//   │  Day-by-Day Schema │
//   └────────┬───────────┘
//            │ JSON
//            ▼
//   ┌──────────────────┐
//   │  day-by-day-      │
//   │  blank.jsx        │
//   │  (renders report) │
//   └──────────────────┘
//
// ============================================================
// POST EXAMPLES (curl):
//
// Inject secretary notes:
//   curl -X POST http://localhost:8085/api/briefing/notes \
//     -H "Content-Type: application/json" \
//     -d '{"en":"Room B2 reserved 09:30","de":"Raum B2 reserviert 09:30"}'
//
// Inject agenda items:
//   curl -X POST http://localhost:8085/api/briefing/agenda \
//     -H "Content-Type: application/json" \
//     -d '{"items":[{"topic":{"en":"Review contracts","de":"Verträge prüfen"},"owner":"Dr. Weber","pr":"high","dur":"15 min"}]}'
//
// Inject action items:
//   curl -X POST http://localhost:8085/api/briefing/actions \
//     -H "Content-Type: application/json" \
//     -d '{"items":[{"a":{"en":"Sign amendment","de":"Nachtrag unterzeichnen"},"r":"Dr. Weber","dl":"05.02.2026","s":"open"}]}'
//
// ============================================================

// Example: start on port 8085 (or your preferred port)
const PORT = process.env.DAY_BY_DAY_PORT || 8085;
app.listen(PORT, () => {
  console.log(`[WINDI] Day-by-Day API running on :${PORT}`);
  console.log(`[WINDI] Health: http://127.0.0.1:${PORT}/api/briefing/health`);
  console.log(`[WINDI] Briefing: http://127.0.0.1:${PORT}/api/briefing`);
});
