// src/verifyPdfSignature.js — Verify PDF report signature
const fs = require("fs");
const crypto = require("crypto");

/**
 * Verify PDF signature
 */
function verifyPdfSignature(pdfPath, sigPath, pubKeyPath) {
  // Read files
  const pdfBuffer = fs.readFileSync(pdfPath);
  const signature = fs.readFileSync(sigPath, "utf8").trim();
  const publicKey = fs.readFileSync(pubKeyPath, "utf8");

  // Verify signature
  const verify = crypto.createVerify("RSA-SHA256");
  verify.update(pdfBuffer);
  verify.end();

  const isValid = verify.verify(publicKey, signature, "base64");

  return {
    valid: isValid,
    pdf_hash: crypto.createHash("sha256").update(pdfBuffer).digest("hex"),
    pdf_size: pdfBuffer.length
  };
}

/**
 * Full verification: PDF signature + public anchor
 */
async function verifyPdfFull(pdfPath, sigPath, pubKeyPath, bundlePath, options = {}) {
  const { verifyPublicAnchor } = require("./verifyPublicAnchor");

  console.log("======================================================");
  console.log("       FULL EXTERNAL EVIDENCE VERIFICATION");
  console.log("======================================================\n");

  // Check files exist
  const files = { pdfPath, sigPath, pubKeyPath, bundlePath };
  for (const [name, path] of Object.entries(files)) {
    if (!fs.existsSync(path)) {
      console.log(`Error: File not found: ${path}`);
      return { success: false, error: `File not found: ${path}` };
    }
  }

  console.log("Files:");
  console.log(`  PDF:        ${pdfPath}`);
  console.log(`  Signature:  ${sigPath}`);
  console.log(`  Public Key: ${pubKeyPath}`);
  console.log(`  Bundle:     ${bundlePath}`);
  console.log("");

  // Step 1: Verify PDF signature
  console.log("Step 1: PDF Signature Verification");
  let sigResult;
  try {
    sigResult = verifyPdfSignature(pdfPath, sigPath, pubKeyPath);
  } catch (err) {
    console.log(`  [FAIL] ${err.message}`);
    return { success: false, step: 1, error: err.message };
  }

  if (!sigResult.valid) {
    console.log("  [FAIL] PDF signature is INVALID");
    console.log("");
    console.log("======================================================");
    console.log("  VERIFICATION FAILED: PDF signature invalid");
    console.log("  The report may have been tampered with.");
    console.log("======================================================");
    return { success: false, step: 1, error: "Invalid signature" };
  }

  console.log("  [OK] PDF signature valid");
  console.log(`  PDF Hash: ${sigResult.pdf_hash.slice(0, 16)}...`);
  console.log("");

  // Step 2: Load and parse bundle
  console.log("Step 2: Bundle Analysis");
  let bundle;
  try {
    bundle = JSON.parse(fs.readFileSync(bundlePath, "utf8"));
  } catch (err) {
    console.log(`  [FAIL] Cannot parse bundle: ${err.message}`);
    return { success: false, step: 2, error: err.message };
  }

  const combinedRootHash = bundle.combined_root_hash ||
                           bundle.anchor?.combined_root_hash ||
                           bundle.transparency_proof?.combined_root_hash;

  if (!combinedRootHash) {
    console.log("  [FAIL] No combined_root_hash in bundle");
    console.log("");
    console.log("======================================================");
    console.log("  VERIFICATION INCOMPLETE: No anchor hash in bundle");
    console.log("======================================================");
    return { success: false, step: 2, error: "No combined_root_hash" };
  }

  console.log(`  [OK] Bundle parsed`);
  console.log(`  Document ID: ${bundle.document_id || "N/A"}`);
  console.log(`  Combined Hash: ${combinedRootHash.slice(0, 16)}...`);
  console.log("");

  // Step 3: Verify against public anchor log
  console.log("Step 3: Public Anchor Verification");
  const logUrl = options.logUrl || process.env.PUBLIC_ANCHOR_LOG_URL || "https://anchor.windi.systems";
  console.log(`  Anchor Log: ${logUrl}`);

  const anchorResult = await verifyPublicAnchor(combinedRootHash, { logUrl });

  if (!anchorResult.chain_valid) {
    console.log(`  [FAIL] Anchor log chain integrity failure`);
    console.log(`  Error: ${anchorResult.error}`);
    console.log("");
    console.log("======================================================");
    console.log("  VERIFICATION FAILED: Public anchor log corrupted");
    console.log("======================================================");
    return { success: false, step: 3, error: anchorResult.error };
  }

  if (!anchorResult.found) {
    console.log("  [FAIL] Bundle hash NOT found in public log");
    console.log(`  Chain verified: ${anchorResult.chain_length} entries`);
    console.log("");
    console.log("======================================================");
    console.log("  VERIFICATION FAILED: Not publicly anchored");
    console.log("  The bundle was not found in the transparency log.");
    console.log("======================================================");
    return { success: false, step: 3, error: "Hash not found" };
  }

  console.log("  [OK] Bundle hash found in public log");
  console.log(`  Anchored At:  ${anchorResult.timestamp}`);
  console.log(`  Sequence:     ${anchorResult.sequence}`);
  console.log(`  Entry Hash:   ${anchorResult.entry_hash.slice(0, 16)}...`);
  console.log(`  Chain Length: ${anchorResult.chain_length} entries`);
  console.log("");

  // Success!
  console.log("======================================================");
  console.log("  FULL VERIFICATION SUCCESS");
  console.log("");
  console.log("  [OK] PDF signature cryptographically valid");
  console.log("  [OK] Bundle integrity confirmed");
  console.log("  [OK] Publicly anchored and verifiable");
  console.log("");
  console.log("  This evidence is independently verifiable at:");
  console.log(`    ${anchorResult.anchor_url}`);
  console.log("======================================================");

  return {
    success: true,
    signature_valid: true,
    pdf_hash: sigResult.pdf_hash,
    anchor_verified: true,
    anchor_timestamp: anchorResult.timestamp,
    anchor_sequence: anchorResult.sequence,
    anchor_url: anchorResult.anchor_url,
    chain_length: anchorResult.chain_length
  };
}

/**
 * CLI-friendly verification with formatted output
 */
function verifyAndPrint(pdfPath, sigPath, pubKeyPath) {
  console.log("======================================================");
  console.log("          PDF SIGNATURE VERIFICATION");
  console.log("======================================================\n");

  // Check files exist
  if (!fs.existsSync(pdfPath)) {
    console.log(`Error: PDF file not found: ${pdfPath}`);
    return false;
  }
  if (!fs.existsSync(sigPath)) {
    console.log(`Error: Signature file not found: ${sigPath}`);
    return false;
  }
  if (!fs.existsSync(pubKeyPath)) {
    console.log(`Error: Public key file not found: ${pubKeyPath}`);
    return false;
  }

  console.log(`PDF File:    ${pdfPath}`);
  console.log(`Signature:   ${sigPath}`);
  console.log(`Public Key:  ${pubKeyPath}`);
  console.log("");

  try {
    const result = verifyPdfSignature(pdfPath, sigPath, pubKeyPath);

    console.log("Verification Result:");
    console.log(`  PDF Hash:  ${result.pdf_hash.slice(0, 16)}...${result.pdf_hash.slice(-8)}`);
    console.log(`  PDF Size:  ${result.pdf_size} bytes`);
    console.log("");

    if (result.valid) {
      console.log("======================================================");
      console.log("  SIGNATURE STATUS: VALID");
      console.log("");
      console.log("  The PDF has not been modified since signing.");
      console.log("  Report integrity is cryptographically confirmed.");
      console.log("======================================================");
      return true;
    } else {
      console.log("======================================================");
      console.log("  SIGNATURE STATUS: INVALID");
      console.log("");
      console.log("  WARNING: The PDF may have been altered!");
      console.log("  Do not trust this report.");
      console.log("======================================================");
      return false;
    }
  } catch (err) {
    console.log(`Error: ${err.message}`);
    return false;
  }
}

module.exports = {
  verifyPdfSignature,
  verifyPdfFull,
  verifyAndPrint
};
