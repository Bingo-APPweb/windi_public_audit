# windi-wcaf-toolkit

Auditor's Swiss Army Knife for WINDI Chain Audit Format.

Part of the **WINDI** (Worldwide Infrastructure for Non-repudiable Document Integrity) ecosystem.

## Installation

```bash
npm install -g windi-wcaf-toolkit
```

Or run locally:

```bash
npm install
npm link
```

## Usage

```bash
wcaf verify   <bundle.json>    # Verify chain integrity
wcaf timeline <bundle.json>    # Print event timeline
wcaf replay   <bundle.json>    # Reconstruct final state
wcaf export   <bundle.json>    # Re-export with validation report
wcaf help                      # Show help
```

## Commands

### `wcaf verify`

Verifies the integrity of a WCAF bundle:

```bash
$ wcaf verify invoice-audit.json

╔══════════════════════════════════════════════════╗
║           WCAF Bundle Verification               ║
╚══════════════════════════════════════════════════╝

Document ID:    INV-2025-0001
Bundle Version: wcaf-bundle-1.0
Event Count:    3

Chain Integrity: ✅ VALID
  Head Hash: abc123...

Attestation:     ✅ Present
  Key ID:   windi-root-2026

Bundle Signature: ✅ Present
  Algorithm: RSA-SHA256

═══════════════════════════════════════════════════
  AUDIT STATUS: ✅ COMPLETE — Ready for submission
═══════════════════════════════════════════════════
```

### `wcaf timeline`

Displays the event timeline:

```bash
$ wcaf timeline invoice-audit.json

╔══════════════════════════════════════════════════╗
║              WCAF Event Timeline                 ║
╚══════════════════════════════════════════════════╝

Document ID: INV-2025-0001
Events: 3

──────────────────────────────────────────────────────────────────────
 #   Timestamp                  Type              Actor
──────────────────────────────────────────────────────────────────────
  0  2026-02-08 12:00:00  VERIFY_RESULT      verification-api
     → verdict: VALID, trust: HIGH
  1  2026-02-08 12:00:02  POLICY_DECISION    policy-engine
     → decision: ALLOW, policy: bank-v3.2
  2  2026-02-08 12:00:05  PAYMENT_ACTION     bank-core
     → action: EXECUTED, ticket: PAY-456
──────────────────────────────────────────────────────────────────────

Chain Info:
  Genesis:    GENESIS
  Head Hash:  def456...
```

### `wcaf replay`

Reconstructs the final state from the timeline:

```bash
$ wcaf replay invoice-audit.json

╔══════════════════════════════════════════════════╗
║           WCAF State Reconstruction              ║
╚══════════════════════════════════════════════════╝

┌─ Verification ─────────────────────────────────────┐
│  Verdict:     VALID
│  Integrity:   INTACT
│  Trust Level: HIGH
└────────────────────────────────────────────────────┘

┌─ Policy Decision ──────────────────────────────────┐
│  Decision:    ALLOW
│  Version:     bank-v3.2
└────────────────────────────────────────────────────┘

┌─ Payment Action ───────────────────────────────────┐
│  Action:      EXECUTED
│  Ticket:      PAY-456
└────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════
  FINAL STATE: ✅ PAYMENT EXECUTED
═══════════════════════════════════════════════════════
```

### `wcaf export`

Re-exports bundle with verification metadata:

```bash
$ wcaf export invoice-audit.json output.json

╔══════════════════════════════════════════════════╗
║           WCAF Bundle Export                     ║
╚══════════════════════════════════════════════════╝

Document ID:     INV-2025-0001
Event Count:     3
Chain Verified:  ✅ Yes
Attestation:     ✅ Present
Bundle Signed:   ✅ Present

Exported to: /path/to/output.json

═══════════════════════════════════════════════════════
  EXPORT STATUS: ✅ SUCCESS
═══════════════════════════════════════════════════════
```

## Dependencies

- `windi-forensics-engine` — Chain verification and replay

## Use Cases

1. **Auditor Review** — Verify bundle integrity before audit submission
2. **Dispute Resolution** — Replay timeline to reconstruct decision history
3. **Compliance Export** — Generate verified export packages
4. **Incident Investigation** — Trace payment decisions through timeline

## License

Apache 2.0 — See [LICENSE](LICENSE)
