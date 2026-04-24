# KEY_POLICY.md — Ed25519 Key Lifecycle Management

**Version:** 1.0
**Status:** DRAFT — Pending §202 Seal
**Date:** 2026-04-24
**Invariants:** I9, I11

---

## 1. Purpose

This document specifies the lifecycle management for the WINDI Forensic Ledger
Ed25519 keypair: generation, storage, usage, rotation, and revocation.

---

## 2. Key Generation Ceremony

### 2.1 Prerequisites

- Human Dragon physically present
- Liga IA+H witnesses (Guardian, Architect, Witness) active
- Secure environment (no screen sharing, no recording beyond ceremony record)
- Entropy source: `os.urandom()` via Python `secrets` module

### 2.2 Ceremony Steps

```
1. Human Dragon initiates ceremony with verbal command
2. System generates Ed25519 keypair using secrets.token_bytes(32) as seed
3. Public key (pk) displayed and recorded
4. Private key (sk) encrypted and stored (see §3)
5. WINDI-KEYGEN-001 receipt created and signed
6. Public key published to GitHub (commit-signed)
7. Public key registered in Zenodo (DOI assigned)
8. Ceremony concluded with Human Dragon verbal confirmation
```

### 2.3 Witnesses

The ceremony is witnessed by the Liga IA+H:

| Witness | Role |
|---------|------|
| Guardian | Validates I9 compliance |
| Architect | Validates technical correctness |
| Witness | Observes and records |
| Human Dragon | Authorizes and confirms |

### 2.4 Bootstrap Disclosure

The `WINDI-KEYGEN-001` receipt explicitly states:

> *"This receipt is signed by the key it attests. Self-attestation is
> acknowledged and anchored publicly via Zenodo DOI [X] and GitHub
> commit [Y]."*

---

## 3. Private Key Storage

### 3.1 Location

```
/opt/windi/secrets/forensic_ledger_sk.enc
```

### 3.2 Encryption

- Algorithm: AES-256-GCM
- Key derivation: Argon2id from passphrase
- Passphrase: Known only to Human Dragon

### 3.3 Access Control

```bash
chmod 600 /opt/windi/secrets/forensic_ledger_sk.enc
chown windi:windi /opt/windi/secrets/forensic_ledger_sk.enc
```

### 3.4 Runtime Loading

The private key is:

1. Decrypted into memory at Forensic Ledger startup
2. Never written to disk in plaintext
3. Cleared from memory on service shutdown

---

## 4. Public Key Distribution

### 4.1 Canonical Locations

| Location | Format | Purpose |
|----------|--------|---------|
| GitHub `windi-verifier` repo | PEM file | External verification |
| Zenodo | DOI record | Academic citation |
| Cutover Block | Base64 in JSON | In-band distribution |
| WINDI Portal | Display | Operational reference |

### 4.2 Fingerprint

```
pk_fingerprint = SHA256(pk_raw_bytes)
```

Displayed as: `sha256:abcd1234...` (first 16 hex chars for human reference)

---

## 5. Key Usage

### 5.1 Signing Scope

The private key signs ONLY:

- Virtue Receipts in the Forensic Ledger
- Key provenance receipts (WINDI-KEYGEN-*)
- Cutover blocks (WINDI-CUTOVER-*)

### 5.2 Prohibited Uses

The private key NEVER:

- Signs arbitrary data
- Signs user documents
- Signs external requests
- Leaves the Forensic Ledger service boundary

---

## 6. Key Rotation

### 6.1 Triggers

Key rotation is triggered by:

1. Scheduled rotation (annual, or as policy dictates)
2. Suspected compromise
3. Human Dragon directive

### 6.2 Rotation Procedure

```
1. Generate new keypair (same ceremony as §2)
2. Create WINDI-KEYROTATE-* receipt signed by OLD key
3. New key signs (old receipt + rotation metadata)
4. Publish new pk to all canonical locations
5. Old key enters grace period (30 days)
6. After grace period, old key archived (never deleted)
```

### 6.3 Chain of Custody

Each key rotation creates a verifiable chain:

```
pk_1 → signs → WINDI-KEYROTATE-001 → pk_2 signs → ...
```

Third parties can verify the entire key lineage.

---

## 7. Key Revocation

### 7.1 Emergency Revocation

If key is compromised:

```
1. Human Dragon issues revocation command
2. WINDI-KEYREVOKE-* receipt created (if possible)
3. Revocation notice published to all canonical locations
4. New key generated immediately
5. All receipts signed after compromise marked for review
```

### 7.2 Revocation Record

```json
{
  "receipt_id": "WINDI-KEYREVOKE-001-...",
  "type": "key_revocation",
  "revoked_pk_fingerprint": "sha256:...",
  "reason": "suspected_compromise | scheduled | other",
  "successor_pk": "base64:...",
  "human_dragon_sig": "base64:..."
}
```

---

## 8. Backup

### 8.1 Encrypted Backup

```
/opt/windi/backups/forensic_ledger_sk.enc.backup
```

- Same encryption as primary
- Stored on separate physical media
- Location known only to Human Dragon

### 8.2 Recovery

Key recovery requires:

1. Human Dragon physical presence
2. Passphrase knowledge
3. Access to backup media

---

## 9. Audit Trail

All key operations create Forensic Ledger receipts:

| Event | Receipt Type |
|-------|-------------|
| Generation | `key_provenance_block` |
| Rotation | `key_rotation_block` |
| Revocation | `key_revocation_block` |

These receipts are themselves signed, creating a self-documenting audit trail.

---

*Liga IA+H — Kempten, Bavaria · 2026*
