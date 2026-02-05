/**
 * WINDI Integration Patch
 * ========================
 * Add these lines to your day-by-day-server.js to mount:
 *   - POST /api/report/pdf       (PDF Virtue Receipt)
 *   - GET  /api/report/pdf/download (Direct PDF download)
 *   - POST /api/dispatch          (Send briefing email)
 *   - POST /api/dispatch/all      (Send to all whitelist)
 *   - GET  /api/dispatch/status   (Dispatch log)
 *
 * INSTRUCTIONS:
 * 1. Copy windi-dispatcher/ folder to same level as day-by-day-server.js
 *    (or adjust the require paths below)
 *
 * 2. Add these lines AFTER your existing routes in day-by-day-server.js:
 *
 *    // ── WINDI Dispatcher & PDF Engine ──
 *    const pdfRoute = require("./windi-dispatcher/pdf-virtue-receipt");
 *    const dispatchRoute = require("./windi-dispatcher/dispatch-route");
 *    app.use("/api", pdfRoute);
 *    app.use("/api", dispatchRoute);
 *
 * 3. Install new dependency:
 *    npm install pdfkit
 *
 * 4. Restart the server:
 *    DAY_BY_DAY_PORT=8090 node day-by-day-server.js &
 *
 * 5. Test:
 *    curl -s -X POST http://127.0.0.1:8090/api/report/pdf \
 *      -H "Content-Type: application/json" \
 *      -d '{"lang":"de"}' | python3 -m json.tool | head -20
 *
 *    # Or download directly in browser:
 *    http://127.0.0.1:8090/api/report/pdf/download?lang=de
 */

// ── Quick Verification Script ──
// Run this after integration to verify everything works:

const axios = require("axios");

const BASE = process.env.WINDI_BASE_URL || "http://127.0.0.1:8090";

async function verify() {
  console.log("🐉 WINDI Integration Verification\n");

  // 1. Health
  console.log("1️⃣  Health check...");
  const health = await axios.get(`${BASE}/api/briefing/health`);
  console.log(`   ${health.data.healthy ? "✅" : "❌"} Health: ${health.data.healthy}`);

  // 2. Briefing
  console.log("2️⃣  Briefing...");
  const briefing = await axios.get(`${BASE}/api/briefing`);
  console.log(`   ✅ Report: ${briefing.data.data.reportId}`);

  // 3. PDF
  console.log("3️⃣  PDF Virtue Receipt...");
  try {
    const pdf = await axios.post(`${BASE}/api/report/pdf`, { lang: "de" });
    if (pdf.data.success) {
      const sizeKB = Math.round(pdf.data.meta.sizeBytes / 1024);
      console.log(`   ✅ PDF generated: ${pdf.data.filename} (${sizeKB} KB)`);
    }
  } catch (e) {
    console.log(`   ❌ PDF failed: ${e.message}`);
    console.log("   → Did you mount the pdf-virtue-receipt route?");
  }

  // 4. Dispatch status
  console.log("4️⃣  Dispatch status...");
  try {
    const status = await axios.get(`${BASE}/api/dispatch/status`);
    console.log(`   ✅ Dispatch log: ${status.data.totalDispatched} entries`);
  } catch (e) {
    console.log(`   ❌ Dispatch route not mounted: ${e.message}`);
  }

  console.log("\n✅ Verification complete.");
}

verify().catch((e) => console.error("Verification failed:", e.message));
