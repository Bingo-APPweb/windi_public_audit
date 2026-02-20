// ═══════════════════════════════════════════════════════════════════
// WINDI ISP PPT ENGINE — MULTI-ISP DEMO
// Generates governance reports for 3 institutions:
//   1. WINDI Publishing House (Noir + Gold)
//   2. Deutsche Bahn AG (Corporate Red)
//   3. Bundesregierung (Federal Blue + Gold)
//
// Same engine. Same governance. Different identities.
// "O template NUNCA decide o nível. A API decide."
// ═══════════════════════════════════════════════════════════════════

const { WindiPPTEngine, ISPLoader } = require("./isp_ppt_engine");
const path = require("path");

// Shared governance data (same structure, rendered per-ISP)
const GOVERNANCE_DATA = {
  stats: [
    { value: "247", label: "Total Receipts", icon: "file", accent: null },
    { value: "100%", label: "Chain Integrity", icon: "link", accent: null },
    { value: "0", label: "Hash Drift", icon: "fingerprint", accent: null },
    { value: "52ms", label: "P95 Latency", icon: "clock", accent: null },
  ],
  services: [
    { name: "Governance API", port: ":8080", status: "ACTIVE" },
    { name: "Desktop Trinity D1", port: ":8100", status: "ACTIVE" },
    { name: "Forensic Ledger", port: ":8101", status: "ACTIVE" },
    { name: "Sentinel LAW", port: ":8102", status: "ACTIVE" },
    { name: "Export Engine M3", port: ":8103", status: "ACTIVE" },
    { name: "WINDI Wallet", port: ":8099", status: "ACTIVE" },
  ],
  riskData: [
    { label: "R0 Minimal", value: 45, color: "2ECC71" },
    { label: "R1 Low", value: 82, color: "27AE60" },
    { label: "R2 Moderate", value: 63, color: "F1C40F" },
    { label: "R3 Elevated", value: 35, color: "F39C12" },
    { label: "R4 High", value: 17, color: "E67E22" },
    { label: "R5 Critical", value: 5, color: "E74C3C" },
  ],
  submissions: { labels: ["Jan", "Feb (1-17)"], values: [158, 89] },
  insight: "91.1% of all documents classified at R0-R2 risk levels. Only 2.0% classified as R5 Critical — indicating healthy governance posture.",
  layers: [
    { label: "L1 — a4Desk (Edge)", desc: "SGE local processing\nClient-side data sovereignty" },
    { label: "L2 — WINDI Mesh", desc: "Dashboard Controllers\nGovernance orchestration" },
    { label: "L3 — Forensic Ledger", desc: "SHA-256 hashes, Merkle Tree\nVirtue Receipts, ZK Proofs" },
  ],
  complianceItems: [
    { text: "Zero-Knowledge Architecture", status: "ACTIVE" },
    { text: "EU AI Act Alignment", status: "DESIGNED" },
    { text: "BSI C5 Compatibility", status: "READY" },
    { text: "ISO 27001 Framework", status: "PLANNED" },
    { text: "GDPR Data Sovereignty", status: "ACTIVE" },
    { text: "9 Constitutional Invariants", status: "ENFORCED" },
    { text: "I9 Autonomy Prohibition", status: "IRREMEDIABLE" },
    { text: "Sentinel LAW Monitoring", status: "LIVE" },
  ],
  receipt: {
    receiptId: "VR-GOV-REPORT-2026Q1",
    timestamp: "2026-02-17T16:00:00Z",
    ledgerEntry: "#247 — Chain VALID",
  },
};

async function generateForISP(ispId, loader) {
  console.log(`\n${"═".repeat(60)}`);
  console.log(`🏛️  Generating: ${ispId}`);
  console.log(`${"═".repeat(60)}`);

  const isp = loader.load(ispId);
  const engine = new WindiPPTEngine(isp);

  // Initialize (render icons in ISP palette)
  await engine.initialize();
  engine.defineSlideMaster();

  // Set total slides for page numbers
  engine.totalSlides = isp.governance.forensic_receipt ? 4 : 3;

  // Slide 1: Cover
  engine.addCoverSlide(
    "Governance Report",
    `${isp.org_name} — Institutional Integrity & Compliance Overview`,
    "Q1 2026  |  February 17, 2026"
  );

  // Slide 2: Health Overview
  const stats = GOVERNANCE_DATA.stats.map(s => ({
    ...s,
    accent: s.accent || isp.colors[s.icon === "link" ? "success" : "primary"]
  }));
  engine.addHealthSlide(stats, GOVERNANCE_DATA.services);

  // Slide 3: Risk Distribution
  engine.addRiskSlide(
    GOVERNANCE_DATA.riskData,
    GOVERNANCE_DATA.submissions,
    GOVERNANCE_DATA.insight
  );

  // Slide 4: Compliance
  engine.addComplianceSlide(GOVERNANCE_DATA.layers, GOVERNANCE_DATA.complianceItems);

  // Slide 5: Forensic Receipt (if governance level requires it)
  if (isp.governance.forensic_receipt) {
    engine.totalSlides = 5;
    await engine.addForensicReceiptSlide(GOVERNANCE_DATA.receipt);
  }

  // Save
  const outputPath = path.join(__dirname, "output", `WINDI_Report_${ispId}.pptx`);
  return engine.save(outputPath);
}

async function main() {
  console.log("🐉 WINDI ISP PPT ENGINE v1.0 — Multi-ISP Demo");
  console.log("   AI processes. Human decides. WINDI guarantees.\n");

  const loader = new ISPLoader(path.join(__dirname, "isp"));
  const available = loader.listAvailable();
  console.log(`📂 Available ISPs: ${available.join(", ")}\n`);

  const results = [];
  for (const ispId of available) {
    const result = await generateForISP(ispId, loader);
    results.push({ isp: ispId, ...result });
  }

  console.log(`\n${"═".repeat(60)}`);
  console.log("🏆 GENERATION COMPLETE");
  console.log(`${"═".repeat(60)}`);
  results.forEach(r => {
    console.log(`  📄 ${r.isp}: ${(r.size / 1024).toFixed(0)}KB — sha256:${(r.hash || "").substring(0, 16)}...`);
  });
  console.log(`\n  Total: ${results.length} presentations generated`);
  console.log("  Engine: WINDI ISP PPT Engine v1.0");
  console.log("  Principle: Same governance. Different identities. 🐉");
}

main().catch(err => { console.error("❌ Error:", err); process.exit(1); });
