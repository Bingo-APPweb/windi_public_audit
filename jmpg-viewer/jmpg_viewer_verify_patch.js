/**
 * WINDI JMPG Viewer — Integrity Verification Patch
 * ==================================================
 * Apply to: /opt/windi/jmpg-viewer/ (port 8104)
 * 
 * This module provides the corrected verification flow:
 * 1. Hash raw .jmpg bytes BEFORE unzipping (bundle_hash)
 * 2. Extract and verify content_hash from blocks
 * 3. Query Ledger for expected hashes
 * 4. Display correct verification state
 */

// ============================================================
// CORE: SHA-256 using Web Crypto API (browser-native, zero deps)
// ============================================================

async function sha256Hex(buffer) {
  const hashBuffer = await crypto.subtle.digest("SHA-256", buffer);
  return Array.from(new Uint8Array(hashBuffer))
    .map(b => b.toString(16).padStart(2, "0"))
    .join("");
}

// ============================================================
// CANONICAL JSON — reproduces Python's json.dumps(obj, separators=(',',':'), sort_keys=True)
// This is CRITICAL for matching the Export Engine's content_hash
// ============================================================

function canonicalJSON(obj) {
  if (obj === null || obj === undefined) return "null";
  if (typeof obj === "boolean") return obj ? "true" : "false";
  if (typeof obj === "number") return JSON.stringify(obj);
  if (typeof obj === "string") return JSON.stringify(obj);
  
  if (Array.isArray(obj)) {
    const items = obj.map(item => canonicalJSON(item));
    return "[" + items.join(",") + "]";
  }
  
  // Object: sort keys alphabetically (like Python's sort_keys=True)
  const keys = Object.keys(obj).sort();
  const pairs = keys.map(k => JSON.stringify(k) + ":" + canonicalJSON(obj[k]));
  return "{" + pairs.join(",") + "}";
}

// ============================================================
// VERIFICATION STATES
// ============================================================

const VerifyState = {
  VERIFIED:           "VERIFIED",           // 🟢 Everything matches
  TAMPERED:           "TAMPERED",           // 🔴 Bundle hash mismatch
  CONTENT_MISMATCH:   "CONTENT_MISMATCH",   // 🟠 Content changed but bundle might be OK
  UNREGISTERED:       "UNREGISTERED",       // ⚠️ Receipt not found in Ledger
  LEDGER_UNREACHABLE: "LEDGER_UNREACHABLE", // ⚪ Cannot reach Ledger
  PENDING:            "PENDING",            // ⏳ Verification in progress
};

const StateConfig = {
  [VerifyState.VERIFIED]: {
    icon: "🟢",
    color: "#22c55e",
    titleDE: "Integrität bestätigt",
    titleEN: "Integrity Verified",
    titlePT: "Integridade verificada",
    showSeal: true,
    showQR: true,
  },
  [VerifyState.TAMPERED]: {
    icon: "🔴",
    color: "#ef4444",
    titleDE: "Integritätsprüfung fehlgeschlagen",
    titleEN: "Integrity Check Failed",
    titlePT: "Verificação de integridade falhou",
    showSeal: false,  // ← CRITICAL: NO green seal on failure
    showQR: false,
  },
  [VerifyState.CONTENT_MISMATCH]: {
    icon: "🟠",
    color: "#f97316",
    titleDE: "Inhalt verändert",
    titleEN: "Content Altered",
    titlePT: "Conteúdo alterado",
    showSeal: false,
    showQR: false,
  },
  [VerifyState.UNREGISTERED]: {
    icon: "⚠️",
    color: "#eab308",
    titleDE: "Nicht im Ledger registriert",
    titleEN: "Not Registered in Ledger",
    titlePT: "Não registrado no Ledger",
    showSeal: false,
    showQR: true,  // QR can still point to verification page
  },
  [VerifyState.LEDGER_UNREACHABLE]: {
    icon: "⚪",
    color: "#6b7280",
    titleDE: "Verifizierung nicht möglich",
    titleEN: "Cannot Verify (Ledger Offline)",
    titlePT: "Não foi possível verificar",
    showSeal: false,
    showQR: false,
  },
};

// ============================================================
// MAIN VERIFICATION FUNCTION
// ============================================================

/**
 * Verify a .jmpg file against the Forensic Ledger.
 * 
 * @param {File|Blob} file - The .jmpg file (from drag-and-drop or file input)
 * @param {string} ledgerBaseUrl - Base URL of the Forensic Ledger (e.g., "/desktop/api/ledger")
 * @returns {Promise<VerifyResult>}
 */
async function verifyJMPG(file, ledgerBaseUrl = "/desktop/api/ledger") {
  const result = {
    state: VerifyState.PENDING,
    receiptId: null,
    bundle: { localHash: null, ledgerHash: null, match: false },
    content: { localHash: null, manifestHash: null, match: false },
    size: { local: null, ledger: null, match: false },
    manifest: null,
    errors: [],
    timestamp: new Date().toISOString(),
  };

  try {
    // ============================================================
    // STEP 1: Hash raw bytes BEFORE unzipping
    // ============================================================
    const rawBuffer = await file.arrayBuffer();
    result.bundle.localHash = await sha256Hex(rawBuffer);
    result.size.local = rawBuffer.byteLength;

    // ============================================================
    // STEP 2: Unzip and extract metadata
    // ============================================================
    let zip;
    try {
      zip = await JSZip.loadAsync(rawBuffer);
    } catch (e) {
      result.state = VerifyState.TAMPERED;
      result.errors.push("Failed to unzip: not a valid JMPG package");
      return result;
    }

    // Read manifest
    const manifestFile = zip.file("manifest.json");
    if (!manifestFile) {
      result.state = VerifyState.TAMPERED;
      result.errors.push("Missing manifest.json in package");
      return result;
    }
    const manifestStr = await manifestFile.async("string");
    const manifest = JSON.parse(manifestStr);
    result.manifest = manifest;
    result.receiptId = manifest.governance?.receipt_id || manifest.package_id;

    // ============================================================
    // STEP 3: Verify content_hash (recalculate from blocks)
    // ============================================================
    const contentFile = zip.file("content.json");
    if (contentFile) {
      const contentStr = await contentFile.async("string");
      const content = JSON.parse(contentStr);
      const blocks = content.blocks || [];
      
      // Canonical JSON — must match Python's json.dumps(blocks, separators=(',',':'), sort_keys=True)
      const canonical = canonicalJSON(blocks);
      result.content.localHash = await sha256Hex(new TextEncoder().encode(canonical));
      result.content.manifestHash = manifest.content_hash;
      result.content.match = result.content.localHash === result.content.manifestHash;
    }

    // ============================================================
    // STEP 4: Query Ledger for expected hashes
    // ============================================================
    try {
      const resp = await fetch(`${ledgerBaseUrl}/api/verify/${result.receiptId}`, {
        signal: AbortSignal.timeout(5000),
      });

      if (resp.ok) {
        const ledger = await resp.json();
        
        // Compare bundle_hash
        if (ledger.bundle_hash) {
          result.bundle.ledgerHash = ledger.bundle_hash;
          result.bundle.match = result.bundle.localHash === ledger.bundle_hash;
        } else {
          // Legacy receipt without bundle_hash — fall back to content_hash only
          result.errors.push("Legacy receipt: no bundle_hash in Ledger (pre-patch)");
          // For legacy, if content matches, we consider it partially verified
        }

        // Compare size
        if (ledger.size_bytes) {
          result.size.ledger = ledger.size_bytes;
          result.size.match = result.size.local === ledger.size_bytes;
        }

        // Determine final state
        if (result.bundle.match && result.content.match) {
          result.state = VerifyState.VERIFIED;
        } else if (!result.bundle.match && ledger.bundle_hash) {
          result.state = VerifyState.TAMPERED;
        } else if (!result.content.match) {
          result.state = VerifyState.CONTENT_MISMATCH;
        } else if (!ledger.bundle_hash && result.content.match) {
          // Legacy: only content_hash available and it matches
          result.state = VerifyState.VERIFIED;
          result.errors.push("Verified via content_hash only (legacy mode)");
        } else {
          result.state = VerifyState.TAMPERED;
        }

      } else if (resp.status === 404) {
        result.state = VerifyState.UNREGISTERED;
        result.errors.push(`Receipt ${result.receiptId} not found in Ledger`);
      } else {
        result.state = VerifyState.LEDGER_UNREACHABLE;
        result.errors.push(`Ledger returned HTTP ${resp.status}`);
      }

    } catch (fetchErr) {
      result.state = VerifyState.LEDGER_UNREACHABLE;
      result.errors.push(`Ledger unreachable: ${fetchErr.message}`);
      
      // Fallback: at least verify content_hash against manifest
      if (result.content.match) {
        result.errors.push("Content hash matches manifest (offline verification)");
      }
    }

  } catch (err) {
    result.state = VerifyState.TAMPERED;
    result.errors.push(`Verification error: ${err.message}`);
  }

  return result;
}

// ============================================================
// UI RENDERING HELPER
// ============================================================

function renderVerificationBanner(result) {
  const config = StateConfig[result.state];
  
  return {
    // Banner
    icon: config.icon,
    color: config.color,
    title: `${config.titleDE} / ${config.titleEN}`,
    
    // Details
    receiptId: result.receiptId,
    bundleHash: result.bundle.localHash,
    
    // What to show/hide
    showGreenSeal: config.showSeal,    // ← Only true for VERIFIED
    showQRCode: config.showQR,
    
    // Debug info (collapsible)
    debug: {
      bundleMatch: result.bundle.match,
      contentMatch: result.content.match,
      sizeMatch: result.size.match,
      localBundleHash: result.bundle.localHash,
      ledgerBundleHash: result.bundle.ledgerHash,
      localContentHash: result.content.localHash,
      manifestContentHash: result.content.manifestHash,
      errors: result.errors,
    },
  };
}

// ============================================================
// EXPORTS (for use in React/Viewer component)
// ============================================================

// If using ES modules:
// export { verifyJMPG, renderVerificationBanner, VerifyState, StateConfig, canonicalJSON, sha256Hex };

// If using script tag:
if (typeof window !== "undefined") {
  window.WINDIVerify = {
    verifyJMPG,
    renderVerificationBanner,
    VerifyState,
    StateConfig,
    canonicalJSON,
    sha256Hex,
  };
}
