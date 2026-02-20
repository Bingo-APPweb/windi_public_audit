#!/usr/bin/env node
const { loadJson } = require("../src/loadJson");
const { verifyBundle } = require("../src/verifyBundle");
const { printTimeline } = require("../src/printTimeline");
const { replayBundle } = require("../src/replayBundle");
const { exportBundle } = require("../src/exportBundle");
const { verifyAnchor } = require("../src/verifyAnchor");
const { verifyAndPrint: verifyPdfSimple, verifyPdfFull } = require("../src/verifyPdfSignature");
const { verifyEvidenceCLI } = require("../src/verifyEvidence");

const [,, cmd, file, ...rest] = process.argv;

const HELP = `
WINDI WCAF Toolkit — Auditor's Swiss Army Knife

Usage:
  wcaf verify          <bundle.json>              Verify chain integrity
  wcaf verify-anchor   <bundle.json> [--full]     Verify against public anchor log
  wcaf verify-pdf      <pdf> <sig> <pubkey> [bundle]  Verify PDF + anchor
  wcaf verify-evidence <bundle> <pdf> <sig> <pubkey>  Full CT-style verification
  wcaf timeline        <bundle.json>              Print event timeline
  wcaf replay          <bundle.json>              Reconstruct final state
  wcaf export          <bundle.json>              Re-export with validation report
  wcaf help                                       Show this help

Options:
  --full              Full chain verification (slower, downloads entire log)
  --strict            Enable STH pinning + consistency proofs (split-view protection)
  --log-url=URL       Override public anchor log URL (hash-chain)
  --merkle-url=URL    Override merkle transparency log URL (CT-style)
  --pin-file=PATH     STH pin file location (default: ~/.wcaf/sth-pin.json)

Environment:
  PUBLIC_ANCHOR_LOG_URL   Default hash-chain log URL
  MERKLE_LOG_URL          Default merkle log URL (default: http://localhost:4051)

Examples:
  wcaf verify invoice-audit.json
  wcaf verify-anchor payment-trail.json
  wcaf verify-anchor bundle.json --full --log-url=http://localhost:4050
  wcaf verify-pdf report.pdf report.sig windi-public.pem bundle.json
  wcaf verify-evidence bundle.json report.pdf report.sig audit-key.pem
  wcaf verify-evidence bundle.json report.pdf report.sig key.pem --merkle-url=http://merkle:4051
  wcaf verify-evidence bundle.json report.pdf report.sig key.pem --strict
  wcaf timeline payment-trail.json
  wcaf replay INV-2025-0001.json
`;

if (!cmd || cmd === "help" || cmd === "--help" || cmd === "-h") {
  console.log(HELP);
  process.exit(0);
}

// Parse options early (needed for special commands)
const options = {};
const args = rest.filter(arg => {
  if (arg === "--full") {
    options.fullVerify = true;
    return false;
  }
  if (arg === "--strict") {
    options.strict = true;
    return false;
  }
  if (arg.startsWith("--log-url=")) {
    options.logUrl = arg.split("=")[1];
    return false;
  }
  if (arg.startsWith("--merkle-url=")) {
    options.merkleUrl = arg.split("=")[1];
    return false;
  }
  if (arg.startsWith("--pin-file=")) {
    options.pinFile = arg.split("=")[1];
    return false;
  }
  return true;
});

// Handle verify-pdf separately (different argument pattern)
if (cmd === "verify-pdf") {
  const [pdfPath, sigPath, pubKeyPath, bundlePath] = [file, ...rest];

  if (!pdfPath || !sigPath || !pubKeyPath) {
    console.error("Usage: wcaf verify-pdf <report.pdf> <signature.sig> <public_key.pem> [bundle.json]");
    process.exit(1);
  }

  // If bundle provided, do full verification (signature + anchor)
  if (bundlePath) {
    verifyPdfFull(pdfPath, sigPath, pubKeyPath, bundlePath, options)
      .then(result => process.exit(result.success ? 0 : 2))
      .catch(err => {
        console.error(`Error: ${err.message}`);
        process.exit(1);
      });
    return; // Don't continue to main()
  } else {
    // Just verify signature
    const valid = verifyPdfSimple(pdfPath, sigPath, pubKeyPath);
    process.exit(valid ? 0 : 2);
  }
}

// Handle verify-evidence (CT-style full verification)
if (cmd === "verify-evidence") {
  const [bundlePath, pdfPath, sigPath, pubKeyPath] = [file, ...args];

  if (!bundlePath || !pdfPath || !sigPath || !pubKeyPath) {
    console.error("Usage: wcaf verify-evidence <bundle.json> <report.pdf> <signature.sig> <public_key.pem>");
    console.error("");
    console.error("Options:");
    console.error("  --merkle-url=URL   Override merkle log URL (default: $MERKLE_LOG_URL or localhost:4051)");
    console.error("  --strict           Enable consistency proofs + STH pinning (split-view protection)");
    console.error("  --pin-file=PATH    STH pin file (default: ~/.wcaf/sth-pin.json)");
    process.exit(1);
  }

  verifyEvidenceCLI(bundlePath, pdfPath, sigPath, pubKeyPath, options)
    .then(result => process.exit(result.success ? 0 : 2))
    .catch(err => {
      console.error(`Error: ${err.message}`);
      process.exit(1);
    });
  return; // Don't continue to main()
}

if (!file) {
  console.error("Error: Missing file argument");
  console.log(HELP);
  process.exit(1);
}

async function main() {
  try {
    const bundle = loadJson(file);

    switch (cmd) {
      case "verify":
        verifyBundle(bundle);
        break;
      case "verify-anchor":
        await verifyAnchor(bundle, options);
        break;
      case "timeline":
        printTimeline(bundle);
        break;
      case "replay":
        replayBundle(bundle);
        break;
      case "export":
        exportBundle(bundle, args[0]);
        break;
      default:
        console.error(`Unknown command: ${cmd}`);
        console.log(HELP);
        process.exit(1);
    }
  } catch (err) {
    console.error(`Error: ${err.message}`);
    process.exit(1);
  }
}

main();
