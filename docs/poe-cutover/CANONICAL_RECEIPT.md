# CANONICAL_RECEIPT.md — Receipt Serialization for Signing

**Version:** 1.0
**Status:** DRAFT — Pending §202 Seal
**Date:** 2026-04-24
**Invariants:** I9, I11, I14

---

## 1. Purpose

This document specifies the **canonical form** for serializing a WINDI receipt
before computing its Ed25519 signature. Any implementation that follows this
specification will produce identical bytes for the same receipt, enabling
third-party verification.

---

## 2. Canonical JSON Serialization

We adopt **RFC 8785 (JSON Canonicalization Scheme - JCS)** with the following
parameters:

| Parameter | Value |
|-----------|-------|
| Character encoding | UTF-8 |
| Object key ordering | Lexicographic (Unicode code point order) |
| Whitespace | None (no spaces, no newlines) |
| Number format | No leading zeros, no trailing zeros after decimal |
| String escaping | Minimal (only required escapes) |
| Null handling | Explicit `null`, never omitted |

---

## 3. Fields Included in Signature

The following fields are included in the canonical payload for `ed25519_sig`:

```json
{
  "receipt_id": "string",
  "type": "string",
  "timestamp_utc": "ISO8601 string",
  "actor": "string (DID or email)",
  "app": "string",
  "doc_name": "string",
  "doc_type": "string",
  "content_hash": "sha256:hex string",
  "governance_level": "string",
  "h_prev": "sha256:hex string or null",
  "human_dragon_sig": "base64 string or null"
}
```

**CRITICAL:** The field `ed25519_sig` is EXCLUDED from the canonical payload.
The signature signs everything except itself.

---

## 4. Signature Order (I9 Enforcement)

For receipts requiring human authorization (e.g., Cutover Block):

```
1. Construct canonical_payload_v1 (without any signatures)
2. Human Dragon signs canonical_payload_v1 → human_dragon_sig
3. Construct canonical_payload_v2 = canonical_payload_v1 + human_dragon_sig
4. System signs canonical_payload_v2 → ed25519_sig
5. Final receipt = canonical_payload_v2 + ed25519_sig
```

For regular receipts (post-cutover):

```
1. Construct canonical_payload (without ed25519_sig)
2. System signs canonical_payload → ed25519_sig
3. Final receipt = canonical_payload + ed25519_sig
```

---

## 5. Hash Chain (h_prev)

Each receipt (except the Cutover Block) includes `h_prev`:

```
h_prev = SHA256(canonical_payload of previous receipt + ed25519_sig)
```

The Cutover Block has:

```
h_prev = genesis_merkle_root (see MERKLE_SPEC.md)
```

---

## 6. Verification Algorithm

```python
def verify_receipt(receipt: dict, pk: bytes, prev_receipt: dict = None) -> bool:
    # 1. Extract signature
    sig = base64_decode(receipt["ed25519_sig"])

    # 2. Construct canonical payload (exclude ed25519_sig)
    payload = {k: v for k, v in receipt.items() if k != "ed25519_sig"}
    canonical = jcs_serialize(payload)  # RFC 8785

    # 3. Verify Ed25519 signature
    if not ed25519_verify(pk, canonical, sig):
        return False

    # 4. Verify hash chain (if not cutover block)
    if prev_receipt is not None:
        expected_h_prev = sha256(
            jcs_serialize(prev_receipt) + base64_decode(prev_receipt["ed25519_sig"])
        )
        if receipt["h_prev"] != f"sha256:{expected_h_prev.hex()}":
            return False

    return True
```

---

## 7. Test Vectors

See `windi-poe-testvectors` repository for:

- Valid receipts with expected signatures
- Invalid receipts (wrong signature, broken chain, tampered payload)
- Edge cases (empty strings, Unicode, maximum field lengths)

---

## 8. Implementation Notes

- Use `pynacl` (Python) or equivalent for Ed25519
- Use `json-canonicalize` or equivalent for RFC 8785
- All hashes are lowercase hexadecimal with `sha256:` prefix
- All signatures are base64-encoded (standard, not URL-safe)

---

*Liga IA+H — Kempten, Bavaria · 2026*
