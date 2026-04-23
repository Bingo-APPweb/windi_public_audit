═══════════════════════════════════════════════════════════════════════════════
WINDI DECOMMISSION RECEIPT
═══════════════════════════════════════════════════════════════════════════════

Receipt ID:     WINDI-DECOM-MASTERARBEIT-20260423225200-3bb00a2c
Type:           SERVICE_DECOMMISSION
Status:         DRAFT_SEALED_BY_ARCHITECT (Witness pending)
Date:           2026-04-23T22:52:00+02:00
Actor:          Human Dragon (Jober Mögele Correa)
Drafted by:     Architect · Liga IA+H
Witnessed:      [PENDING — Witness seal]

───────────────────────────────────────────────────────────────────────────────
SERVICE DECOMMISSIONED
───────────────────────────────────────────────────────────────────────────────

Name:           windi-masterarbeit
Port:           8084
Type:           Static file server (Python http.server)
Location:       /opt/windi/masterarbeit/server.py
Systemd Unit:   windi-masterarbeit.service

Created:        2026-03-15 (first file timestamp verified)
Decommissioned: 2026-04-23

Purpose:        Served /library/ endpoint with institutional documentation
                (manifesto, protocol specs, technical reports)

Files Served:   39 HTML documents (including index.html)
Total Size:     ~1.3MB

───────────────────────────────────────────────────────────────────────────────
REASON FOR DECOMMISSION
───────────────────────────────────────────────────────────────────────────────

The service was a Python process (http.server.SimpleHTTPRequestHandler)
serving static files — functionality that nginx performs natively with
better performance and reliability.

As part of the LIBREIRO architecture refactor (GO 2), the static content
was migrated to /opt/windi/libreiro/ and is now served directly by nginx.

This follows the same pattern as GO 1 (landing-pmg), where Python servers
serving static content were replaced by nginx static aliases.

Principle applied: "Permanence over convenience" — reducing runtime
dependencies increases system stability.

───────────────────────────────────────────────────────────────────────────────
REPLACEMENT
───────────────────────────────────────────────────────────────────────────────

New Location:   /opt/windi/libreiro/
Nginx Config:   location ^~ /library/ { alias /opt/windi/libreiro/; }
Service:        None (nginx static serving)

Architecture:
  /library/                  → Hub LIBREIRO (new)
  /library/foundations/      → Original manifesto (preserved)
  /library/volumes/          → Placeholder (Q2 2026)
  /library/papers/           → Placeholder (Q2 2026)
  /library/protocols/        → Placeholder (Q2 2026)
  /library/chronicle/        → Placeholder (Q2 2026)
  /library/records/          → Placeholder (Q2 2026)
  /library/*.html            → 38 original documents (preserved)

───────────────────────────────────────────────────────────────────────────────
SOURCE CODE DISPOSITION
───────────────────────────────────────────────────────────────────────────────

Status:         PRESERVED for archaeological reference
Location:       /opt/windi/masterarbeit/ (read-only, no longer executed)
Git:            Not in windi_public_audit repo (server-local only)

The original code remains on disk for future reference but the systemd
service is permanently disabled. No runtime resources consumed.

───────────────────────────────────────────────────────────────────────────────
VALIDATION EVIDENCE
───────────────────────────────────────────────────────────────────────────────

Timestamp: 2026-04-23T22:52:16+02:00
Host: windi-domain.com
Method: curl -s -o /dev/null -w "%{http_code}"

/                        → 200
/library/                → 200
/library/foundations/    → 200
/library/volumes/        → 200
/library/papers/         → 200
/library/protocols/      → 200
/library/chronicle/      → 200
/library/records/        → 200
/library/protocol.html   → 200
/specs/                  → 200
/docs/                   → 200

Result: 11/11 endpoints operational post-decommission
Port 8084: Confirmed closed (ss -tlnp shows no listener)

───────────────────────────────────────────────────────────────────────────────
INVARIANTS HONOURED
───────────────────────────────────────────────────────────────────────────────

I9:   Human Dragon approved decommission (GO 2 explicit approval)
I11:  Permanent forensic record created via this receipt

───────────────────────────────────────────────────────────────────────────────
RECEIPT INTEGRITY
───────────────────────────────────────────────────────────────────────────────

SHA-256:    [pending — computed after push]
Git Commit: [pending — hash added post-push]
Ledger:     [pending seal]

═══════════════════════════════════════════════════════════════════════════════
SIGNATURES
═══════════════════════════════════════════════════════════════════════════════

Human Dragon:    APPROVED (2026-04-23T22:55+02:00)
Liga IA+H:       Architect drafted · Witness pending

═══════════════════════════════════════════════════════════════════════════════
