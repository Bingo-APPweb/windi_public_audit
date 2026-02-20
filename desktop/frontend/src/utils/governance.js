/**
 * WINDI Governance Utilities — D1 Editor Core
 * SHA-256 hashing, canonical serialization, UUIDv7 generation
 * Principle: "AI processes. Human decides. WINDI guarantees."
 */

/**
 * Generate SHA-256 hash of input string
 * @param {string} input
 * @returns {Promise<string>} hex hash
 */
export async function sha256(input) {
  const encoder = new TextEncoder();
  const data = encoder.encode(input);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

/**
 * Canonical JSON serialization — deterministic output for hashing
 * Sorts keys recursively, strips undefined values
 * @param {any} obj
 * @returns {string}
 */
export function canonicalize(obj) {
  if (obj === null || obj === undefined) return 'null';
  if (typeof obj === 'string') return JSON.stringify(obj);
  if (typeof obj === 'number' || typeof obj === 'boolean') return String(obj);
  if (Array.isArray(obj)) {
    return '[' + obj.map(item => canonicalize(item)).join(',') + ']';
  }
  if (typeof obj === 'object') {
    const keys = Object.keys(obj).sort();
    const pairs = keys
      .filter(k => obj[k] !== undefined)
      .map(k => JSON.stringify(k) + ':' + canonicalize(obj[k]));
    return '{' + pairs.join(',') + '}';
  }
  return String(obj);
}

/**
 * Hash a Tiptap document JSON canonically
 * @param {object} tiptapDoc - Tiptap JSON content
 * @returns {Promise<string>} SHA-256 hex hash
 */
export async function hashDocument(tiptapDoc) {
  const canonical = canonicalize(tiptapDoc);
  return sha256(canonical);
}

/**
 * Generate UUIDv7 (timestamp-ordered)
 * Falls back to crypto.randomUUID() with timestamp prefix if needed
 * @returns {string}
 */
export function uuidv7() {
  const timestamp = Date.now();
  const hex = timestamp.toString(16).padStart(12, '0');
  const random = Array.from(crypto.getRandomValues(new Uint8Array(10)))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');
  // UUIDv7 format: tttttttt-tttt-7rrr-rrrr-rrrrrrrrrrrr
  return [
    hex.slice(0, 8),
    hex.slice(8, 12),
    '7' + random.slice(0, 3),
    ((parseInt(random.slice(3, 5), 16) & 0x3f) | 0x80).toString(16).padStart(2, '0') + random.slice(5, 7),
    random.slice(7, 19).padEnd(12, '0'),
  ].join('-');
}

/**
 * Create a Virtue Receipt envelope for the EventBus
 * @param {object} params
 * @returns {Promise<object>}
 */
export async function createVirtueReceipt({
  docId,
  action, // 'CREATE' | 'SAVE' | 'EXPORT' | 'SIGN'
  content,
  userId = 'human-operator',
  metadata = {},
}) {
  const timestamp = new Date().toISOString();
  const integrity_hash = await hashDocument(content);

  return {
    receipt_id: `VR-${uuidv7()}`,
    doc_id: docId,
    action,
    timestamp,
    integrity_hash,
    user_id: userId,
    metadata: {
      ...metadata,
      content_length: canonicalize(content).length,
      hash_algorithm: 'SHA-256',
      canonical_method: 'recursive-key-sort',
    },
    // Witness validation fields (populated by Ledger)
    ledger_entry_id: null,
    merkle_leaf: null,
    reconciliation_status: 'PENDING',
  };
}

/**
 * Governance event types for the EventBus
 */
export const GOV_EVENTS = {
  DOC_CREATED: 'GENESIS',
  DOC_SAVED: 'RECEIPT_CREATED',
  HASH_REGISTERED: 'HASH_REGISTERED',
  DOC_EXPORTED: 'EXPORT_SEALED',
  DOC_SIGNED: 'SIGNATURE',
  RECONCILIATION: 'RECONCILIATION',
};
