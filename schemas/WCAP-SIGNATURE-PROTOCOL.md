# WCAP Signature Protocol

**Version:** 0.1.0
**Status:** Tijolo Bercario (S247 Lei IV)
**Invariants:** I9, I11

## Canonical Hash Computation

1. Remove `signature` field from manifest
2. Serialize to canonical JSON:
   ```python
   import json
   canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"))
   ```
3. Compute SHA-256:
   ```python
   import hashlib
   hash_hex = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
   manifest_canonical_hash = f"sha256:{hash_hex}"
   ```

## Ed25519 Signature (S205 KEYGEN-001)

1. Issuer loads their Ed25519 private key (derived from DID)
2. Sign the `manifest_canonical_hash` string (not the bytes):
   ```python
   from nacl.signing import SigningKey
   import base64

   signing_key = SigningKey(private_key_bytes)
   signature = signing_key.sign(manifest_canonical_hash.encode("utf-8"))
   signature_b64 = base64.b64encode(signature.signature).decode("ascii")
   public_key_b64 = base64.b64encode(signing_key.verify_key.encode()).decode("ascii")
   ```
3. Populate signature object:
   ```json
   {
     "algorithm": "Ed25519",
     "public_key": "{public_key_b64}",
     "signature_value": "{signature_b64}",
     "signed_at": "2026-05-12T23:30:00Z"
   }
   ```

## Verification (Reader PWA)

1. Extract `signature` from manifest
2. Recompute canonical hash (excluding signature)
3. Verify signature matches declared `manifest_canonical_hash`
4. Verify Ed25519 signature using `public_key`
5. (Optional) Verify `public_key` matches issuer DID in W-DID-GENESIS

## File Structure

```
example.wcap (ZIP)
|-- manifest.json        <- includes manifest_canonical_hash + signature
|-- media/
|   |-- welcome-de.mp3
|   |-- welcome-en.mp3
|   |-- welcome-pt.mp3
|-- transcripts/
    |-- welcome-de.txt
```

## Integrity Chain

```
media/*.mp3 --> content_hash (I11)
     |
     v
manifest.json --> manifest_canonical_hash (I11)
     |
     v
signature.signature_value --> Ed25519(issuer_private_key)
     |
     v
issuer.did --> W-DID-GENESIS verification
```

## Constitutional Guarantees

- **I9:** `human_approved: true` required in governance
- **I11:** Every file has `content_hash`, manifest has `manifest_canonical_hash`
- **I12:** All `name`/`title` fields require `de`, `en`, `pt`
- **I14:** No placeholder values accepted
- **I16:** `gps_never_uploaded: true` and `zone_detection_local: true` mandatory

---
*WINDI Three Dragons Protocol - 2026-05-12*
