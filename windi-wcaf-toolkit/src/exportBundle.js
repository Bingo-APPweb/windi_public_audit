// src/exportBundle.js
const fs = require("fs");
const path = require("path");
const { verifyChain } = require("windi-forensics-engine");

function exportBundle(bundle, outputPath) {
  console.log("╔══════════════════════════════════════════════════╗");
  console.log("║           WCAF Bundle Export                     ║");
  console.log("╚══════════════════════════════════════════════════╝\n");

  // Verify chain before export
  const chainResult = verifyChain(bundle.timeline || []);

  // Create export bundle with verification report
  const exportData = {
    ...bundle,
    export_metadata: {
      exported_at: new Date().toISOString(),
      exported_by: "windi-wcaf-toolkit",
      toolkit_version: "0.1.0",
      chain_verified_at_export: chainResult.ok,
      chain_problems: chainResult.problems.length > 0 ? chainResult.problems : undefined
    }
  };

  // Determine output path
  const outFile = outputPath ||
    `${bundle.document_id || "bundle"}-export-${Date.now()}.json`;
  const resolved = path.resolve(outFile);

  // Write file
  fs.writeFileSync(resolved, JSON.stringify(exportData, null, 2), "utf8");

  console.log(`Document ID:     ${bundle.document_id || "N/A"}`);
  console.log(`Event Count:     ${bundle.timeline?.length || 0}`);
  console.log(`Chain Verified:  ${chainResult.ok ? "✅ Yes" : "❌ No"}`);
  console.log(`Attestation:     ${bundle.attestation ? "✅ Present" : "⚠️  Missing"}`);
  console.log(`Bundle Signed:   ${bundle.bundle_signature ? "✅ Present" : "⚠️  Missing"}`);
  console.log("");
  console.log(`Exported to: ${resolved}`);
  console.log("");

  if (chainResult.ok) {
    console.log("═══════════════════════════════════════════════════════");
    console.log("  EXPORT STATUS: ✅ SUCCESS");
    console.log("═══════════════════════════════════════════════════════");
  } else {
    console.log("═══════════════════════════════════════════════════════");
    console.log("  EXPORT STATUS: ⚠️  EXPORTED WITH CHAIN ERRORS");
    console.log("═══════════════════════════════════════════════════════");
  }
}

module.exports = { exportBundle };
