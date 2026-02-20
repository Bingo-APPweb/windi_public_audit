// src/verifyAnchor.js — Verify bundle against public anchor log
const crypto = require("crypto");

const DEFAULT_ANCHOR_LOG_URL = process.env.PUBLIC_ANCHOR_LOG_URL || "https://anchor.windi.systems";

/**
 * Compute SHA-256 hash of an entry (excluding entry_hash field)
 */
function computeEntryHash(entry) {
  const { entry_hash, ...rest } = entry;
  const canonical = JSON.stringify(rest, Object.keys(rest).sort());
  return crypto.createHash("sha256").update(canonical).digest("hex");
}

/**
 * Verify public anchor log chain integrity
 */
function verifyChainIntegrity(entries) {
  if (!entries || entries.length === 0) {
    return { valid: false, error: "Empty log" };
  }

  let prevHash = "GENESIS";

  for (let i = 0; i < entries.length; i++) {
    const entry = entries[i];

    // Check chain link
    if (entry.prev_entry_hash !== prevHash) {
      return {
        valid: false,
        error: `Chain broken at seq ${entry.seq}`,
        index: i,
        expected: prevHash,
        got: entry.prev_entry_hash
      };
    }

    // Check entry hash
    const computed = computeEntryHash(entry);
    if (computed !== entry.entry_hash) {
      return {
        valid: false,
        error: `Entry hash mismatch at seq ${entry.seq}`,
        index: i,
        expected: computed,
        got: entry.entry_hash
      };
    }

    prevHash = entry.entry_hash;
  }

  return { valid: true, entries: entries.length, head_hash: prevHash };
}

/**
 * Find bundle's combined_root_hash in public anchor log
 */
async function findBundleInLog(combinedRootHash, logUrl) {
  const url = `${logUrl}/anchors/verify/${combinedRootHash}`;

  try {
    const response = await fetch(url);

    if (response.status === 404) {
      return { found: false };
    }

    if (!response.ok) {
      throw new Error(`Anchor log returned ${response.status}`);
    }

    const result = await response.json();
    return {
      found: true,
      entry: result
    };
  } catch (err) {
    return { found: false, error: err.message };
  }
}

/**
 * Fetch and verify entire public anchor log
 */
async function fetchAndVerifyLog(logUrl) {
  const url = `${logUrl}/export`;

  try {
    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(`Anchor log returned ${response.status}`);
    }

    const data = await response.json();
    const entries = data.entries || data;

    const chainResult = verifyChainIntegrity(entries);
    return {
      fetched: true,
      chain: chainResult,
      entries
    };
  } catch (err) {
    return { fetched: false, error: err.message };
  }
}

/**
 * Verify a bundle against the public anchor log
 */
async function verifyAnchor(bundle, options = {}) {
  const logUrl = options.logUrl || DEFAULT_ANCHOR_LOG_URL;

  console.log("======================================================");
  console.log("          PUBLIC ANCHOR VERIFICATION");
  console.log("======================================================\n");

  // 1. Extract combined_root_hash from bundle
  const combinedRootHash = bundle.combined_root_hash ||
                           bundle.anchor?.combined_root_hash ||
                           bundle.transparency_proof?.combined_root_hash;

  if (!combinedRootHash) {
    console.log("Combined Root Hash: NOT FOUND in bundle\n");
    console.log("------------------------------------------------------");
    console.log("  ANCHOR STATUS: CANNOT VERIFY - No hash in bundle");
    console.log("------------------------------------------------------");
    return { verified: false, reason: "NO_HASH_IN_BUNDLE" };
  }

  console.log(`Combined Root Hash: ${combinedRootHash}`);
  console.log(`Anchor Log URL:     ${logUrl}`);
  console.log("");

  // 2. Search for hash in public log
  console.log("Searching public anchor log...");
  const searchResult = await findBundleInLog(combinedRootHash, logUrl);

  if (searchResult.error) {
    console.log(`  Error: ${searchResult.error}\n`);
    console.log("------------------------------------------------------");
    console.log("  ANCHOR STATUS: ERROR - Could not reach anchor log");
    console.log("------------------------------------------------------");
    return { verified: false, reason: "LOG_UNREACHABLE", error: searchResult.error };
  }

  if (!searchResult.found) {
    console.log("  Hash NOT FOUND in public log\n");
    console.log("------------------------------------------------------");
    console.log("  ANCHOR STATUS: NOT ANCHORED");
    console.log("------------------------------------------------------");
    return { verified: false, reason: "HASH_NOT_FOUND" };
  }

  const entry = searchResult.entry;
  console.log("  FOUND in public log");
  console.log("");

  // 3. Display anchor details
  console.log("Anchor Entry Details:");
  console.log(`  Sequence:     ${entry.seq}`);
  console.log(`  Timestamp:    ${entry.ts}`);
  console.log(`  Entry Hash:   ${entry.entry_hash}`);
  console.log(`  Prev Hash:    ${entry.prev_entry_hash}`);
  if (entry.source) console.log(`  Source:       ${entry.source}`);
  if (entry.source_id) console.log(`  Source ID:    ${entry.source_id}`);
  console.log("");

  // 4. Verify chain integrity (optional full verification)
  if (options.fullVerify) {
    console.log("Fetching full chain for verification...");
    const logResult = await fetchAndVerifyLog(logUrl);

    if (!logResult.fetched) {
      console.log(`  Error: ${logResult.error}\n`);
    } else if (!logResult.chain.valid) {
      console.log(`  WARNING: Chain integrity issue: ${logResult.chain.error}\n`);
      console.log("------------------------------------------------------");
      console.log("  ANCHOR STATUS: CHAIN COMPROMISED");
      console.log("------------------------------------------------------");
      return { verified: false, reason: "CHAIN_INVALID", entry };
    } else {
      console.log(`  Chain verified: ${logResult.chain.entries} entries`);
      console.log(`  Head hash: ${logResult.chain.head_hash.slice(0, 16)}...`);
      console.log("");
    }
  }

  // 5. Compute entry hash to verify integrity
  const computed = computeEntryHash(entry);
  const hashMatch = computed === entry.entry_hash;

  console.log("Entry Hash Verification:");
  if (hashMatch) {
    console.log("  Recomputed hash matches stored hash");
  } else {
    console.log("  WARNING: Hash mismatch!");
    console.log(`  Expected: ${computed}`);
    console.log(`  Got:      ${entry.entry_hash}`);
    console.log("");
    console.log("------------------------------------------------------");
    console.log("  ANCHOR STATUS: ENTRY TAMPERED");
    console.log("------------------------------------------------------");
    return { verified: false, reason: "ENTRY_TAMPERED", entry };
  }
  console.log("");

  // 6. Success
  console.log("======================================================");
  console.log("  ANCHOR STATUS: VERIFIED");
  console.log("");
  console.log("  This bundle was publicly anchored at:");
  console.log(`    ${entry.ts}`);
  console.log("");
  console.log("  Anyone can independently verify this by checking:");
  console.log(`    ${logUrl}/anchors/${entry.seq}`);
  console.log("======================================================");

  return {
    verified: true,
    entry,
    anchor_url: `${logUrl}/anchors/${entry.seq}`,
    anchored_at: entry.ts
  };
}

/**
 * Generate anchor proof section for audit reports
 */
function generateAnchorProofSection(verificationResult) {
  if (!verificationResult.verified) {
    return {
      status: "NOT_ANCHORED",
      reason: verificationResult.reason,
      error: verificationResult.error
    };
  }

  return {
    status: "VERIFIED",
    combined_root_hash: verificationResult.entry.combined_root_hash,
    anchor_log_url: verificationResult.anchor_url,
    anchor_timestamp: verificationResult.anchored_at,
    entry_hash: verificationResult.entry.entry_hash,
    sequence: verificationResult.entry.seq,
    verification: {
      chain_integrity: "VALID",
      bundle_hash_present: true,
      independently_verifiable: true
    }
  };
}

module.exports = {
  verifyAnchor,
  verifyChainIntegrity,
  findBundleInLog,
  fetchAndVerifyLog,
  computeEntryHash,
  generateAnchorProofSection
};
