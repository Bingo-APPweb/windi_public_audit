# KEY_CEREMONY_PROTOCOL.md — Ed25519 Key Generation Ceremony

**Version:** 1.1
**Status:** DRAFT — Awaiting Human Dragon Approval
**Date:** 2026-04-24
**Invariants:** I1, I9, I11

---

## 1. Purpose

This document specifies the exact procedure for generating the WINDI Forensic Ledger
Ed25519 keypair. The ceremony produces `WINDI-KEYGEN-001-20260424`.

**This document must be approved by Human Dragon before execution.**

---

## 2. Open Questions (Human Dragon Decides)

### Q1: Environment

| Option | Description | Trade-off |
|--------|-------------|-----------|
| **A: Strato VPS** | Generate on production server (87.106.29.233) | Simpler, key never leaves server; VPS provider has theoretical access |
| **B: Air-gapped** | Generate on isolated machine, transfer encrypted SK | Higher isolation; requires secure transfer protocol |
| **C: HSM** | Hardware Security Module | Maximum security; requires hardware procurement |

**Recommendation:** Option A (Strato) for initial deployment. Key rotation to HSM can occur later under §-sealed block.

### Q2: Passphrase Delivery

| Option | Description |
|--------|-------------|
| **A: Human Dragon creates** | HD types passphrase directly during ceremony |
| **B: System generates** | System generates high-entropy passphrase, HD memorises/stores |

**Recommendation:** Option A — Human Dragon creates passphrase (I1 sovereignty).

### Q3: Liga IA+H Participation Mode

**Decision:** Asynchronous attestation (pre-review + post-attestation)

| Seq | Role | Phase | Validates |
|-----|------|-------|-----------|
| — | **Human Dragon** | B (sync) | Physical presence, commands, passphrase |
| 1 | **Architect** | A (async) | Technical correctness |
| 2 | **Guardian** | A (async) | I9 compliance + Architect attestation |
| 3 | **Witness** | C (async) | Chain closure: both prior attestations + ceremony observation |

**Rule:** Witness closes the attestation chain. If Witness rejects, ceremony is invalidated
even if Architect + Guardian approved. See `ATTESTATION_FORMAT.md` §1.1.

---

## 3. Cryptographic Specification

### 3.1 Algorithm

| Parameter | Value | Reference |
|-----------|-------|-----------|
| Algorithm | Ed25519 | RFC 8032 |
| Library | PyNaCl | `nacl.signing.SigningKey` |
| Seed entropy | 32 bytes | `os.urandom(32)` via PyNaCl internals |

### 3.1.1 Environment Isolation (Human Dragon Decision Required)

| Option | Pros | Cons |
|--------|------|------|
| **A: System Python** | Simple, always available | Pollutes system, future updates may break |
| **B: Dedicated venv** | Isolated, reproducible, sealable | One more layer to document |

**If Option B (recommended for forensic rigor):**

```bash
python3 -m venv /opt/windi/venv-keygen
source /opt/windi/venv-keygen/bin/activate
pip install pynacl argon2-cffi
pip freeze > /opt/windi/docs/poe-cutover/artifacts/requirements-keygen.txt
```

The venv becomes a ceremony artifact. `requirements-keygen.txt` enters the bootstrap receipt.
Reviewers can recreate the environment byte-for-byte.

**Version pinning is mandatory:** The exact versions of PyNaCl and argon2-cffi
are recorded in the preflight log and become part of the bootstrap receipt hash.

### 3.2 Key Generation Code

```python
from nacl.signing import SigningKey
from nacl.encoding import Base64Encoder
import hashlib

# Generate keypair (PyNaCl uses os.urandom internally)
signing_key = SigningKey.generate()
verify_key = signing_key.verify_key

# Export
sk_bytes = bytes(signing_key)  # 32 bytes seed
pk_bytes = bytes(verify_key)   # 32 bytes public key

# Encode for storage/display
pk_base64 = verify_key.encode(encoder=Base64Encoder).decode('ascii')
pk_fingerprint = "sha256:" + hashlib.sha256(pk_bytes).hexdigest()

print(f"Public Key (base64): {pk_base64}")
print(f"Fingerprint: {pk_fingerprint}")
```

**Note:** PyNaCl's `SigningKey.generate()` internally calls `os.urandom(32)` for the seed.
This is cryptographically equivalent to `secrets.token_bytes(32)` but uses the
library's native interface, ensuring correct Ed25519 key derivation.

### 3.3 Why PyNaCl, Not Pure secrets

| Approach | Problem |
|----------|---------|
| `secrets.token_bytes(32)` as raw key | Ed25519 keys require specific derivation from seed |
| `SigningKey(seed)` with external seed | Valid but adds unnecessary step |
| `SigningKey.generate()` | Correct: handles seed generation + derivation atomically |

---

## 4. Ceremony Steps

### Phase A: Pre-Ceremony (Asynchronous)

```
A1. Execute PREFLIGHT_CHECKLIST.sh, save log
A2. Human Dragon confirms environment choice (Q1): Strato VPS
A3. Human Dragon confirms passphrase method (Q2): HD creates
A4. Human Dragon confirms Liga participation mode (Q3): Async
A5. Human Dragon prepares loss acceptance artifact (handwritten, signed, photographed)
A6. Architect reviews code + preflight → produces attestation (seq 1)
A7. Guardian reviews I9 compliance + Architect attestation → produces attestation (seq 2)
A8. Human Dragon verifies both attestations have verdict APPROVE
```

**Attestation files stored in:** `/opt/windi/docs/poe-cutover/attestations/`

### Phase B: Ceremony (Synchronous)

```
B1. Human Dragon initiates with verbal command: "Begin Key Ceremony"
B2. System displays ceremony script for review
B3. Human Dragon confirms: "Execute"
B4. System generates Ed25519 keypair
B5. System displays public key (pk) and fingerprint
B6. Human Dragon verifies display, confirms: "Public key acknowledged"
B7. Human Dragon enters passphrase (not echoed)
B8. System encrypts private key with AES-256-GCM + Argon2id
B9. System writes encrypted SK to /opt/windi/secrets/forensic_ledger_sk.enc
B10. System sets permissions: chmod 600, chown windi:windi
B11. Human Dragon confirms: "Storage complete"
B12. System executes POSITIVE OPERATIONALITY TEST (see §6.1)
B13. Human Dragon confirms: "Operationality verified"
```

**B12 is mandatory.** Without positive proof of operationality, we only know a keypair
was generated — not that it functions correctly.

### Phase C: Attestation & Chain Closure (Synchronous)

```
C1. System constructs WINDI-KEYGEN-001-20260424 receipt payload (including all artifact hashes)
C2. Human Dragon signs payload → human_dragon_sig
C3. System signs (payload + human_dragon_sig) → ed25519_sig (THE BOOTSTRAP MOMENT)
C4. System writes receipt to Forensic Ledger
C5. Witness produces attestation (seq 3): validates Architect + Guardian + ceremony observation
C6. System hashes Witness attestation and appends to receipt
C7. Human Dragon concludes: "Ceremony complete"
```

**C3 is the bootstrap moment:** The newly created key signs its own birth certificate.
This self-attestation is acknowledged in `bootstrap_disclosure` field.

**C5 closes the attestation chain.** If Witness verdict is not APPROVE, ceremony is invalid.

### Phase D: Publication (Asynchronous)

```
D1. Commit pk to GitHub (windi-verifier repo, signed commit)
D2. Register pk in Zenodo (DOI assigned)
D3. Update Cutover Block schema with key_provenance_receipt_id
```

---

## 5. Private Key Encryption

### 5.1 Encryption Parameters

| Parameter | Value |
|-----------|-------|
| Algorithm | AES-256-GCM |
| Key derivation | Argon2id |
| Argon2id time cost | 3 |
| Argon2id memory cost | 65536 (64 MB) |
| Argon2id parallelism | 4 |
| Salt | 16 bytes random |
| Nonce | 12 bytes random |

### 5.2 Encryption Code

```python
from nacl.signing import SigningKey
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from argon2.low_level import hash_secret_raw, Type
import os
import json

def encrypt_private_key(sk_bytes: bytes, passphrase: str) -> bytes:
    """Encrypt Ed25519 private key with passphrase."""
    salt = os.urandom(16)
    nonce = os.urandom(12)

    # Derive 256-bit key from passphrase
    key = hash_secret_raw(
        secret=passphrase.encode('utf-8'),
        salt=salt,
        time_cost=3,
        memory_cost=65536,
        parallelism=4,
        hash_len=32,
        type=Type.ID
    )

    # Encrypt
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, sk_bytes, None)

    # Package
    envelope = {
        "version": 1,
        "algorithm": "AES-256-GCM",
        "kdf": "argon2id",
        "kdf_params": {
            "time_cost": 3,
            "memory_cost": 65536,
            "parallelism": 4
        },
        "salt": salt.hex(),
        "nonce": nonce.hex(),
        "ciphertext": ciphertext.hex()
    }

    return json.dumps(envelope, indent=2).encode('utf-8')
```

---

## 6. Verification

### 6.1 Positive Operationality Test (MANDATORY — Step B12)

Immediately after key generation, before closing the ceremony:

```python
from nacl.signing import SigningKey, VerifyKey
from nacl.encoding import Base64Encoder
from datetime import datetime, timezone
import hashlib

# Operationality test — proves key is functional, not just generated
timestamp = datetime.now(timezone.utc).isoformat()
test_message = f"WINDI-KEYGEN-001 operational @ {timestamp}".encode('utf-8')

# Sign
signed_message = signing_key.sign(test_message)
signature_bytes = signed_message.signature
message_bytes = signed_message.message

# Verify (must not raise)
verify_key.verify(signed_message)

# Record artifacts for bootstrap receipt
operationality_proof = {
    "test_message": test_message.decode('utf-8'),
    "signature": signature_bytes.hex(),
    "verified": True,
    "timestamp_utc": timestamp
}

print(f"OPERATIONALITY TEST: PASS")
print(f"Message: {test_message.decode()}")
print(f"Signature: {signature_bytes.hex()[:32]}...")
```

**This test proves:**
1. The private key can sign (not corrupted)
2. The public key can verify (matching pair)
3. The timestamp anchors when operationality was confirmed

**All three artifacts** (message, signature, verification result) are included in the bootstrap receipt.

### 6.2 Post-Ceremony Verification

For future verification without the private key:

```python
# Load public key from published source
pk_base64 = "..."  # from GitHub/Zenodo
verify_key = VerifyKey(pk_base64, encoder=Base64Encoder)

# Verify operationality proof from bootstrap receipt
test_message = receipt["operationality_proof"]["test_message"].encode()
signature = bytes.fromhex(receipt["operationality_proof"]["signature"])
verify_key.verify(test_message, signature)  # Raises if invalid

print("Post-ceremony verification: PASS")
```

---

## 7. Rollback

If ceremony fails at any step:

1. Delete any generated files
2. Document failure in incident log
3. Restart from Phase A after root cause analysis

The ceremony is atomic: either all steps complete, or none are persisted.

---

## 8. Approval Checklist

Human Dragon must confirm each before execution:

| # | Item | Status |
|---|------|--------|
| 1 | Environment choice (Q1): Strato VPS | ⬜ |
| 2 | Passphrase method (Q2): HD creates | ⬜ |
| 3 | Liga participation mode (Q3): Async | ⬜ |
| 4 | PREFLIGHT_CHECKLIST.sh executed, all checks PASS | ⬜ |
| 5 | Loss acceptance artifact created (handwritten, signed, photographed) | ⬜ |
| 6 | PASSPHRASE_POLICY.md reviewed and acknowledged | ⬜ |
| 7 | Architect attestation received: verdict APPROVE | ⬜ |
| 8 | Guardian attestation received: verdict APPROVE | ⬜ |
| 9 | KEY_CEREMONY_PROTOCOL.md v1.1 reviewed | ⬜ |
| 10 | Passphrase prepared and memorized | ⬜ |
| 11 | Physical backup envelope prepared | ⬜ |
| 12 | Ready to execute | ⬜ |

When all boxes are checked, Human Dragon commands: **"CONFIRMA KEY CEREMONY"**

---

*Liga IA+H — Kempten, Bavaria · 2026*
