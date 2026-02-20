import { validateProofSet, validateHashFormat } from "../validation/proofsetValidator.js";

export async function verifyDocument(payload) {
  const { document_id, document_hash, issuer_key_id, proof_level = "L2" } = payload;

  // Required fields validation
  if (!document_id || !document_hash) {
    throw new Error("Missing required fields: document_id and document_hash are required");
  }

  // Validate hash format
  validateHashFormat(document_hash);

  // If full ProofSet provided, validate it
  if (payload.version && payload.proof_shelves && payload.created_at) {
    validateProofSet(payload);
  }

  // Stub logic — real verification comes later
  // In production: lookup document_id, compare hashes, verify signature
  return {
    verdict: "VALID",
    integrity: "INTACT",
    trust_level: proof_level,
    issuer_status: issuer_key_id ? "TRUSTED" : "UNKNOWN",
    checks: {
      hash_format_valid: true,
      schema_valid: true,
      signature_valid: true,
      chain_verified: true,
      timestamp_valid: true
    },
    risk_flags: [],
    request_id: `req-${Date.now().toString(36)}`
  };
}
