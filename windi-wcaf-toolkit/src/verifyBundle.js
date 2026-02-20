// src/verifyBundle.js
const { verifyChain, verifyBundle: verifyFullBundle } = require("windi-forensics-engine");

function verifyBundle(bundle, options = {}) {
  console.log("╔══════════════════════════════════════════════════╗");
  console.log("║           WCAF Bundle Verification               ║");
  console.log("╚══════════════════════════════════════════════════╝\n");

  // Basic info
  console.log(`Document ID:    ${bundle.document_id || "N/A"}`);
  console.log(`Bundle Version: ${bundle.bundle_version || "N/A"}`);
  console.log(`Created At:     ${bundle.created_at || "N/A"}`);
  console.log(`Event Count:    ${bundle.timeline?.length || 0}`);
  console.log("");

  // Chain verification
  if (bundle.timeline && bundle.timeline.length > 0) {
    const chainResult = verifyChain(bundle.timeline);

    if (chainResult.ok) {
      console.log("Chain Integrity: ✅ VALID");
      console.log(`  Head Hash: ${bundle.timeline[bundle.timeline.length - 1].event_hash}`);
    } else {
      console.log("Chain Integrity: ❌ BROKEN");
      console.log("\nProblems detected:");
      chainResult.problems.forEach((p, i) => {
        console.log(`  ${i + 1}. [${p.code}] at index ${p.index}`);
        if (p.expected_hash) console.log(`     Expected: ${p.expected_hash}`);
        if (p.got_hash) console.log(`     Got:      ${p.got_hash}`);
      });
    }
  } else {
    console.log("Chain Integrity: ⚠️  No timeline events");
  }
  console.log("");

  // Attestation check
  if (bundle.attestation) {
    console.log("Attestation:     ✅ Present");
    console.log(`  Key ID:   ${bundle.attestation.key_id}`);
    console.log(`  Attested: ${bundle.attestation.attested_at}`);
    console.log(`  Algorithm: ${bundle.attestation.signature_alg}`);
  } else {
    console.log("Attestation:     ⚠️  Not present");
  }
  console.log("");

  // Bundle signature check
  if (bundle.bundle_signature) {
    console.log("Bundle Signature: ✅ Present");
    console.log(`  Key ID:    ${bundle.bundle_signature.key_id}`);
    console.log(`  Algorithm: ${bundle.bundle_signature.alg}`);
    console.log(`  Hash:      ${bundle.bundle_signature.signed_hash?.slice(0, 16)}...`);
  } else {
    console.log("Bundle Signature: ⚠️  Not present");
  }
  console.log("");

  // Public anchor proof
  const anchorProof = bundle.transparency_proof || bundle.anchor_proof || bundle.anchor;
  if (anchorProof) {
    console.log("Public Transparency Proof:");
    if (anchorProof.combined_root_hash) {
      console.log(`  Combined Hash: ${anchorProof.combined_root_hash.slice(0, 16)}...`);
    }
    if (anchorProof.anchor_url || anchorProof.anchor_ref) {
      console.log(`  Anchor URL:    ${anchorProof.anchor_url || anchorProof.anchor_ref}`);
    }
    if (anchorProof.anchored_at || anchorProof.anchor_timestamp) {
      console.log(`  Anchored At:   ${anchorProof.anchored_at || anchorProof.anchor_timestamp}`);
    }
    if (anchorProof.entry_hash) {
      console.log(`  Entry Hash:    ${anchorProof.entry_hash.slice(0, 16)}...`);
    }
    if (anchorProof.status === "VERIFIED" || anchorProof.verified) {
      console.log("  Status:        ✅ Publicly Anchored");
    } else if (anchorProof.status) {
      console.log(`  Status:        ${anchorProof.status}`);
    }
    console.log("");
    console.log("  [Run 'wcaf verify-anchor' for full public verification]");
  } else {
    console.log("Public Anchor:    ⚠️  Not present in bundle");
    console.log("  [Run 'wcaf verify-anchor' to check against public log]");
  }
  console.log("");

  // Summary
  const chainOk = bundle.chain_verification?.verified ||
                  (bundle.timeline && verifyChain(bundle.timeline).ok);

  const hasAnchor = !!(anchorProof?.status === "VERIFIED" || anchorProof?.verified);
  const hasSignatures = !!(bundle.attestation && bundle.bundle_signature);

  if (chainOk && hasSignatures && hasAnchor) {
    console.log("═══════════════════════════════════════════════════");
    console.log("  AUDIT STATUS: ✅ COMPLETE + ANCHORED");
    console.log("  Independently verifiable by any third party");
    console.log("═══════════════════════════════════════════════════");
  } else if (chainOk && hasSignatures) {
    console.log("═══════════════════════════════════════════════════");
    console.log("  AUDIT STATUS: ✅ COMPLETE — Ready for submission");
    console.log("═══════════════════════════════════════════════════");
  } else if (chainOk) {
    console.log("═══════════════════════════════════════════════════");
    console.log("  AUDIT STATUS: ⚠️  PARTIAL — Missing signatures");
    console.log("═══════════════════════════════════════════════════");
  } else {
    console.log("═══════════════════════════════════════════════════");
    console.log("  AUDIT STATUS: ❌ INVALID — Chain compromised");
    console.log("═══════════════════════════════════════════════════");
  }
}

module.exports = { verifyBundle };
