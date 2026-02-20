# WINDI Roadmap

## Current Status (v0.1.0)

### ✅ Completed

| Component | Status | Description |
|-----------|--------|-------------|
| `windi-reader-sdk` | ✅ | Client SDK with hash, canonicalization |
| `windi-verification-api` | ✅ | Express server with /verify endpoint |
| `windi-policy-engine` | ✅ | Rule-based decision engine |
| `windi-proof-spec` | ✅ | ProofSet schema, canonicalization rules |
| `windi-forensics-engine` | ✅ | Hash chain, attestation, bundle export |
| `windi-wcaf-toolkit` | ✅ | CLI for audit bundle verification |
| `windi-core-reference` | ✅ | Architecture documentation |

### 🔄 In Progress

| Component | Status | Description |
|-----------|--------|-------------|
| E2E Integration | 🔄 | Full flow testing SDK → API → Policy → Forensics |
| PostgreSQL Deployment | 🔄 | Production database setup |

---

## Phase 1: Production Readiness

### 1.1 Issuer Registry

**Priority:** 🔴 Critical

**Goal:** Persistent issuer management with key rotation

**Deliverables:**
- [ ] `windi-issuer-registry` repository
- [ ] PostgreSQL schema for issuers and keys
- [ ] Key rotation support
- [ ] Revocation mechanism
- [ ] REST API for registry management

**Schema:**
```sql
CREATE TABLE issuers (
  id UUID PRIMARY KEY,
  name TEXT NOT NULL,
  status TEXT NOT NULL, -- REGISTERED, TRUSTED, REVOKED
  created_at TIMESTAMPTZ,
  trusted_at TIMESTAMPTZ,
  revoked_at TIMESTAMPTZ
);

CREATE TABLE issuer_keys (
  id UUID PRIMARY KEY,
  issuer_id UUID REFERENCES issuers(id),
  key_id TEXT NOT NULL, -- windi:key:bank-de-2026
  public_key TEXT NOT NULL,
  algorithm TEXT NOT NULL,
  valid_from TIMESTAMPTZ,
  valid_until TIMESTAMPTZ,
  revoked_at TIMESTAMPTZ
);
```

### 1.2 Service Authentication

**Priority:** 🟡 Important

**Goal:** Secure inter-service communication

**Deliverables:**
- [ ] API key management
- [ ] HMAC request signing
- [ ] mTLS option for high-security deployments
- [ ] Rate limiting per API key

### 1.3 Internationalization Pack

**Priority:** 🟢 Enhancement

**Goal:** Multi-language support without core changes

**Deliverables:**
- [ ] `windi-i18n-pack` repository
- [ ] EN/DE/PT dictionaries
- [ ] `translate()` and `translateCodes()` helpers
- [ ] Express middleware
- [ ] React hooks

---

## Phase 2: Enterprise Features

### 2.1 Offline Verification

**Goal:** SDK can verify without API call

**Deliverables:**
- [ ] Local hash verification
- [ ] Cached issuer keys
- [ ] WCAF bundle validation
- [ ] Offline mode flag

### 2.2 Webhook Notifications

**Goal:** Real-time event notifications

**Deliverables:**
- [ ] Webhook registration API
- [ ] Event filtering (BLOCK only, etc.)
- [ ] Retry logic with exponential backoff
- [ ] Webhook signature verification

### 2.3 Batch Processing

**Goal:** High-volume document verification

**Deliverables:**
- [ ] Batch /verify endpoint
- [ ] Async processing queue
- [ ] Progress tracking
- [ ] Batch result export

---

## Phase 3: Compliance & Governance

### 3.1 Trust Framework

**Goal:** Formal governance for issuer trust

**Deliverables:**
- [ ] Trust framework document
- [ ] KYC requirements for TRUSTED status
- [ ] HSM key requirements
- [ ] Annual audit process
- [ ] Trust mark issuance

### 3.2 Transparency Anchoring

**Goal:** External proof of forensic logs

**Deliverables:**
- [ ] Periodic hash publication
- [ ] Certificate Transparency-style log
- [ ] Optional blockchain anchoring
- [ ] Public audit endpoint

### 3.3 Regulatory Reports

**Goal:** Compliance reporting automation

**Deliverables:**
- [ ] DSGVO/GDPR data flow documentation
- [ ] Basel III risk assessment integration
- [ ] EU AI Act transparency reports
- [ ] Audit export templates

---

## Phase 4: Scale & Performance

### 4.1 Distributed Deployment

**Goal:** Multi-region high availability

**Deliverables:**
- [ ] Kubernetes deployment manifests
- [ ] Database replication strategy
- [ ] CDN for static assets
- [ ] Geographic routing

### 4.2 Performance Optimization

**Goal:** Sub-100ms verification latency

**Deliverables:**
- [ ] Redis caching layer
- [ ] Connection pooling
- [ ] Query optimization
- [ ] Load testing suite

### 4.3 Monitoring & Observability

**Goal:** Production visibility

**Deliverables:**
- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] Distributed tracing
- [ ] Alert rules

---

## Version Timeline

| Version | Target | Milestone |
|---------|--------|-----------|
| v0.1.0 | ✅ Done | Core ecosystem complete |
| v0.2.0 | Q2 2026 | Issuer registry, auth |
| v0.3.0 | Q3 2026 | i18n, offline mode |
| v1.0.0 | Q4 2026 | Production ready |
| v1.1.0 | Q1 2027 | Enterprise features |
| v2.0.0 | Q3 2027 | Transparency anchoring |

---

## Contributing

See individual repository CONTRIBUTING.md files for guidelines.

## Contact

- GitHub: https://github.com/Bingo-APPweb
- Security: security@windi.systems
