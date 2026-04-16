# Changelog

All notable changes to the WINDI Verification API will be documented in this file.

---

## [1.0.0] - 2026-04-16

### Added

- **WPIL Role** — Reposistioned as WINDI Proof Interface Layer entry point
- **Three-level verification**:
  - Level 1: Schema validation against `windi-proof-spec v1.0.0`
  - Level 2: Hash format verification (SHA-256, 64 hex chars)
  - Level 3: Remote ledger confirmation via WINDI Verify Public
- **Endpoints**:
  - `GET /` — Service information
  - `GET /health` — Living Tree compatible health check
  - `POST /verify` — Single receipt verification
  - `POST /verify/receipt` — Alias for /verify
  - `POST /verify/batch` — Batch verification (max 100)
- **Canonicalization** — Deterministic JSON canonicalization per spec
- **Governance awareness** — Checks I9 compliance for HIGH governance
- **Embedded schemas** — No external schema dependency at runtime
- **Structured responses** — Compliant with `verification-result.schema.json`
- **Configuration** — Environment variables for endpoint, mode, logging
- **CORS support** — For browser-based verification

### Changed

- Version bumped to `1.0.0`
- Package renamed to `@windi/verification-api`
- Complete rewrite of verification logic

### Removed

- Stub verification (always returning VALID)
- External schema file dependency

### Security

- Input validation on all endpoints
- Request size limits (1MB)
- Timeout on remote verification (10s)

---

## [0.1.0] - 2026-02-07

### Added

- Initial repository structure
- Basic Express server
- Stub verification endpoint

---

*WINDI Verification API — WPIL Entry Point*
