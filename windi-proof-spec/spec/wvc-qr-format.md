# WINDI Verification Code (WVC) — QR Payload Format

Version: 1.0
Status: Normative

## Overview

The WINDI Verification Code (WVC) is a compact, QR-embeddable payload that enables offline verification initiation and online proof lookup.

## WVC String Format

```
WVC1-<BASE32-PAYLOAD>
```

- **Prefix**: `WVC1-` (version 1)
- **Payload**: Base32-encoded binary structure

**Example:**
```
WVC1-KRUGS4ZANFZSAYJAORSXG5BAMEQGEYLTMUZTEIDFNZRW6ZDFMEQHEZLTORUW4ZZAORUGKIDQMF2GK3TN
```

## Binary Payload Structure

The Base32 payload decodes to a binary structure:

| Offset | Size | Field | Description |
|--------|------|-------|-------------|
| 0 | 1 | Version | `0x01` for v1 |
| 1 | 1 | Flags | Feature flags |
| 2 | 16 | Document ID | Truncated SHA-256 of document_id |
| 18 | 16 | Hash Prefix | First 16 bytes of document_hash |
| 34 | 4 | Timestamp | Unix timestamp (uint32) |
| 38 | 8 | Issuer ID | Truncated issuer key ID |
| 46 | 2 | Checksum | CRC-16 of bytes 0-45 |

**Total size**: 48 bytes (encoded: ~77 Base32 characters)

## Flags Byte

| Bit | Name | Description |
|-----|------|-------------|
| 0 | `HAS_SIGNATURE` | Payload includes signature reference |
| 1 | `OFFLINE_ALLOWED` | L1 verification permitted |
| 2 | `HIGH_VALUE` | Requires L3 verification |
| 3-7 | Reserved | Must be 0 |

## Encoding Process

1. Construct binary payload per structure above
2. Compute CRC-16 checksum of bytes 0-45
3. Append checksum bytes (big-endian)
4. Encode entire 48 bytes as Base32 (RFC 4648, no padding)
5. Prepend `WVC1-` prefix

**Pseudocode:**
```javascript
function encodeWVC(proofSet) {
  const buffer = new Uint8Array(48);

  buffer[0] = 0x01;  // Version
  buffer[1] = computeFlags(proofSet);

  // Document ID hash (truncated)
  const docIdHash = sha256(proofSet.document_id);
  buffer.set(docIdHash.slice(0, 16), 2);

  // Document hash prefix
  const docHash = parseHash(proofSet.document_hash);
  buffer.set(docHash.slice(0, 16), 18);

  // Timestamp
  const ts = Math.floor(Date.parse(proofSet.created_at) / 1000);
  new DataView(buffer.buffer).setUint32(34, ts, false);

  // Issuer ID (truncated hash)
  const issuerHash = sha256(proofSet.issuer_key_id);
  buffer.set(issuerHash.slice(0, 8), 38);

  // Checksum
  const crc = crc16(buffer.slice(0, 46));
  new DataView(buffer.buffer).setUint16(46, crc, false);

  return "WVC1-" + base32Encode(buffer);
}
```

## Decoding Process

1. Verify `WVC1-` prefix
2. Decode Base32 payload
3. Verify checksum
4. Extract fields per structure

## QR Code Generation

### Recommended Settings

| Parameter | Value |
|-----------|-------|
| Error Correction | Level M (15%) |
| Encoding | Alphanumeric |
| Minimum Version | 5 |
| Module Size | 3+ pixels |

### Placement

The WVC QR code SHOULD be placed:
- Bottom-right corner of document
- Minimum 10mm x 10mm size
- Clear zone of 4 modules around QR

## Verification Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Scan QR    │────▶│ Parse WVC   │────▶│ API Lookup  │
│  (WVC1-...) │     │ (decode)    │     │ /verify/wvc │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ Verify Hash │
                    │ (document)  │
                    └─────────────┘
```

1. Scan QR code from document
2. Parse WVC string
3. (Optional) Compute document hash locally
4. Call `/verify/wvc` endpoint
5. Compare response with local hash (if computed)

## Compact Mode

For very small QR codes, a further compressed format is available:

```
WVC1S-<BASE32-SHORT>
```

Short format (32 bytes):
- Omits timestamp
- Uses 8-byte hash prefix
- Uses 4-byte issuer ID

## Security Considerations

1. **Not a Signature**: WVC is a lookup key, not a cryptographic proof
2. **Truncation**: Truncated hashes provide ~128 bits of collision resistance
3. **Tampering**: Checksum detects accidental corruption only
4. **Replay**: Timestamp prevents indefinite reuse
5. **Privacy**: WVC does not contain document content
