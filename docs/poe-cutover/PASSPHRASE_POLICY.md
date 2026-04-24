# PASSPHRASE_POLICY.md — Cryptographic Passphrase Management

**Version:** 1.1
**Status:** DRAFT — Awaiting Human Dragon Approval
**Date:** 2026-04-24
**Invariants:** I1, I9, I11

---

## 1. Purpose

This document defines the policy for creating, storing, and recovering
the passphrase that protects the Forensic Ledger Ed25519 private key.

**Critical Question:** If the passphrase is lost, the ENTIRE PoE chain is lost.
This policy ensures recovery is possible while maintaining I1 (Human Sovereignty).

---

## 2. Passphrase Requirements

### 2.1 Minimum Specifications

| Parameter | Requirement |
|-----------|-------------|
| Length | ≥ 20 characters |
| Entropy | ≥ 128 bits effective |
| Character set | Printable ASCII (no emoji, no Unicode) |
| Memorability | Must be memorable to Human Dragon |

### 2.2 Recommended Format

**Option A: Diceware (Recommended)**
```
6+ words from diceware list
Example: "correct horse battery staple anchor vapor"
Entropy: ~77 bits (6 words) to ~90 bits (7 words)
```

**Option B: Passphrase Sentence**
```
Meaningful sentence with modifications
Example: "In2026.WINDI.sealed.the.first.cryptographic.receipt!"
Entropy: Variable, depends on predictability
```

**Option C: High-Entropy Random**
```
Generated string memorized
Example: "Kx9$mP2qL!nR7vF#"
Entropy: High, but hard to memorize
```

**Human Dragon chooses.** Guardian recommends Option A (diceware).

---

## 3. Storage Policy

### 3.1 Primary Storage: Human Memory

The passphrase resides primarily in Human Dragon's memory.
No digital backup of the plaintext passphrase.

### 3.2 Physical Backup: Sealed Envelope

**Purpose:** Recovery if Human Dragon is incapacitated or forgets.

**Procedure:**
1. Human Dragon writes passphrase on paper (handwritten, archival ink)
2. Paper placed in opaque envelope
3. Envelope sealed with tamper-evident seal
4. Envelope signed across seal by Human Dragon
5. Envelope stored in secure physical location
6. Location known only to Human Dragon

**Requirements:**
- Physical location NOT in Strato datacenter
- NOT in any cloud storage
- NOT photographed or digitized
- Accessible only to Human Dragon (or designated heir)

### 3.2.1 Physical Location Options (Human Dragon Decision Required)

| Location | Robustness | Problem |
|----------|------------|---------|
| Home drawer | Low | Fire, theft, forgetting |
| Bank safe deposit | High | Cost, bureaucratic access |
| Home + copy at trusted person | Medium-high | Requires trust in another |
| Home safe (fireproof) | Medium | Better than drawer |

**Decision must be made and executed before ceremony.**
Without physical backup, passphrase is single point of biological failure.

### 3.2.2 Archival Ink Note

Standard ballpoint ink fades in 5-10 years. For archival permanence:
- Use archival-quality pen (pigment-based ink)
- Or black/blue fountain pen ink (iron gall or pigment)
- Avoid cheap ballpoint, gel pens, or pencil

This photograph will be referenced by hash in an academic paper.

### 3.3 Optional: Fragmented Backup

For additional resilience (NOT required for initial deployment):

```
Fragment 1: First half of passphrase → Location A
Fragment 2: Second half of passphrase → Location B
```

**Rule:** Neither fragment alone is useful. Both locations must be secure.

---

## 4. Recovery Scenarios

### 4.1 Scenario: Human Dragon Forgets Passphrase

```
1. Retrieve sealed envelope from secure location
2. Verify seal is intact (no tampering)
3. Open envelope, read passphrase
4. Decrypt private key
5. (Optional) Change passphrase and create new sealed envelope
6. Destroy old envelope contents
```

### 4.2 Scenario: Sealed Envelope Lost/Destroyed

```
If passphrase forgotten AND envelope lost:
  → Private key is UNRECOVERABLE
  → Key rotation required (new keypair)
  → WINDI-KEYROTATE-* receipt created
  → New ceremony, new §-sealed block

This is by design. No backdoor exists.
```

### 4.3 Scenario: Human Dragon Incapacitation

```
Designated successor (if any) can:
  1. Access sealed envelope location
  2. Recover passphrase
  3. Assume custodianship

If no successor designated:
  → Key rotation by new governance structure
  → Constitutional amendment required
```

---

## 5. Passphrase Change Procedure

If Human Dragon wishes to change passphrase:

```
1. Decrypt private key with current passphrase
2. Re-encrypt with new passphrase
3. Overwrite /opt/windi/secrets/forensic_ledger_sk.enc
4. Create new sealed envelope
5. Destroy old sealed envelope
6. Create WINDI-KEYCHANGE-* receipt (passphrase change, not key rotation)
```

**Note:** Key rotation (new keypair) is different from passphrase change.
Passphrase change does not require new §-sealed block.

---

## 6. What NOT To Do

| Forbidden Action | Reason |
|------------------|--------|
| Store passphrase in cloud | I1 violation: third-party access |
| Store passphrase on server | If server compromised, key compromised |
| Share passphrase with AI | AI cannot hold secrets (context may leak) |
| Email or message passphrase | Interception risk |
| Use password manager | Single point of failure + cloud risk |
| Write on computer/phone | Digital copies multiply uncontrollably |

---

## 7. Ceremony Integration

During Key Ceremony:

```
Phase B, Step B7:
  - System prompts: "Enter passphrase (not echoed):"
  - Human Dragon types passphrase directly
  - Passphrase NEVER displayed or logged
  - Passphrase used immediately for encryption
  - Passphrase cleared from memory after encryption
```

**No passphrase verification step during ceremony.**
Human Dragon must remember exactly what was typed.

---

## 8. Loss Acceptance Statement — PHYSICAL ARTIFACT

The loss acceptance is not a checkbox — it is a **physical artifact** that becomes
part of the bootstrap receipt. This anchors the ceremony to the physical world
and provides juridical protection in future disputes.

### 8.1 Required Text (Handwritten)

```
Eu, Jober Mögele Correa, Human Dragon, aceito que a perda
da passphrase WINDI-KEYGEN-001 resulta na invalidação
irreversível de toda a cadeia PoE dependente desta chave.

Kempten, [DATA]

[ASSINATURA A TINTA]
```

### 8.2 Artifact Creation Procedure

```
1. Write the statement by hand on paper (not printed)
2. Sign with ink at the bottom
3. Date the document
4. Photograph in high resolution (legible)
5. Compute SHA-256 of the photograph file
6. Store photograph at: /opt/windi/docs/poe-cutover/artifacts/loss_acceptance_[YYYYMMDD].jpg
7. Include hash in bootstrap receipt
```

### 8.3 Why Physical?

| Reason | Benefit |
|--------|---------|
| Germanic juridical rigor | Protects against "was it conscious?" disputes |
| Physical anchor | Ceremony is not purely digital |
| Reviewers respect | Academic reviewers value physical evidence |
| I1 reinforcement | Human hand proves human sovereignty |

### 8.4 Artifact in Bootstrap Receipt

```json
{
  "loss_acceptance": {
    "artifact_type": "physical_handwritten_declaration",
    "photo_hash": "sha256:[hash of photograph]",
    "photo_path": "/opt/windi/docs/poe-cutover/artifacts/loss_acceptance_20260424.jpg",
    "language": "pt-BR",
    "signer": "Jober Mögele Correa",
    "role": "Human Dragon",
    "date": "2026-04-24"
  }
}
```

---

## 9. Audit Trail

| Event | Logged? | Receipt? |
|-------|---------|----------|
| Passphrase creation | No (never logged) | No |
| Passphrase entry during ceremony | No | No |
| Passphrase change | No | Yes (WINDI-KEYCHANGE-*) |
| Recovery from envelope | No | Optional incident record |

**Passphrase itself is NEVER in any log, receipt, or artifact.**

---

## 10. Summary

| Item | Policy |
|------|--------|
| Primary storage | Human Dragon memory |
| Backup | Sealed physical envelope |
| Digital backup | FORBIDDEN |
| Cloud backup | FORBIDDEN |
| Recovery if both lost | Key rotation (new keypair) |
| Third-party recovery | IMPOSSIBLE by design |

---

## 11. Human Dragon Checklist

Before ceremony, confirm:

```
[ ] I have chosen a passphrase meeting §2 requirements
[ ] I have memorized the passphrase
[ ] I have prepared a sealed envelope with the passphrase
[ ] I have stored the envelope in a secure physical location
[ ] I have handwritten and signed the loss acceptance declaration (§8)
[ ] I have photographed the loss acceptance declaration
[ ] I have computed the SHA-256 hash of the photograph
[ ] I understand there is no backdoor or recovery without the passphrase
```

---

*Liga IA+H — Kempten, Bavaria · 2026*
*"The key belongs to the Human. The Human belongs to the decision."*
