// src/verifyPublicAnchor.js — Verify hash against public anchor log with chain integrity
const crypto = require("crypto");

const PUBLIC_ANCHOR_LOG_URL = process.env.PUBLIC_ANCHOR_LOG_URL || "https://anchor.windi.systems";

/**
 * Compute SHA-256 hash
 */
function sha256Hex(data) {
  const str = typeof data === "string" ? data : JSON.stringify(data);
  return crypto.createHash("sha256").update(str).digest("hex");
}

/**
 * Compute entry hash (must match public-anchor-log computation)
 */
function computeEntryHash(entry) {
  const { entry_hash, ...rest } = entry;
  const canonical = JSON.stringify(rest, Object.keys(rest).sort());
  return sha256Hex(canonical);
}

/**
 * Verify public anchor log chain and find hash
 */
async function verifyPublicAnchor(combinedRootHash, options = {}) {
  const logUrl = options.logUrl || PUBLIC_ANCHOR_LOG_URL;

  try {
    // Fetch the entire log
    const response = await fetch(`${logUrl}/export`);

    if (!response.ok) {
      throw new Error(`Anchor log returned ${response.status}`);
    }

    const data = await response.json();
    const entries = data.entries || data;

    if (!entries || entries.length === 0) {
      return { found: false, chain_valid: true, chain_length: 0 };
    }

    // Verify chain integrity while searching
    let prevHash = "GENESIS";
    let foundEntry = null;

    for (const entry of entries) {
      // Check chain link
      if (entry.prev_entry_hash !== prevHash) {
        return {
          found: false,
          chain_valid: false,
          error: `Chain broken at seq ${entry.seq}`,
          expected_prev: prevHash,
          got_prev: entry.prev_entry_hash
        };
      }

      // Check entry hash
      const recomputed = computeEntryHash(entry);
      if (recomputed !== entry.entry_hash) {
        return {
          found: false,
          chain_valid: false,
          error: `Entry hash mismatch at seq ${entry.seq}`,
          expected_hash: recomputed,
          got_hash: entry.entry_hash
        };
      }

      // Check if this is the entry we're looking for
      if (entry.combined_root_hash === combinedRootHash) {
        foundEntry = entry;
      }

      prevHash = entry.entry_hash;
    }

    if (foundEntry) {
      return {
        found: true,
        chain_valid: true,
        chain_length: entries.length,
        timestamp: foundEntry.ts,
        sequence: foundEntry.seq,
        entry_hash: foundEntry.entry_hash,
        anchor_url: `${logUrl}/anchors/${foundEntry.seq}`
      };
    }

    return {
      found: false,
      chain_valid: true,
      chain_length: entries.length
    };
  } catch (err) {
    return {
      found: false,
      chain_valid: false,
      error: err.message
    };
  }
}

/**
 * Quick lookup without full chain verification
 */
async function findInAnchorLog(combinedRootHash, options = {}) {
  const logUrl = options.logUrl || PUBLIC_ANCHOR_LOG_URL;

  try {
    const response = await fetch(`${logUrl}/anchors/verify/${combinedRootHash}`);

    if (response.status === 404) {
      return { found: false };
    }

    if (!response.ok) {
      throw new Error(`Anchor log returned ${response.status}`);
    }

    const entry = await response.json();

    // Verify entry hash
    const recomputed = computeEntryHash(entry);
    if (recomputed !== entry.entry_hash) {
      return {
        found: false,
        error: "Entry hash verification failed"
      };
    }

    return {
      found: true,
      timestamp: entry.ts,
      sequence: entry.seq,
      entry_hash: entry.entry_hash,
      anchor_url: `${logUrl}/anchors/${entry.seq}`
    };
  } catch (err) {
    return {
      found: false,
      error: err.message
    };
  }
}

module.exports = {
  verifyPublicAnchor,
  findInAnchorLog,
  computeEntryHash,
  sha256Hex
};
