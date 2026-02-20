# 🛡 WINDI Agent — Operational Security Model

**Document:** SECURITY.md  
**Version:** 1.0.0  
**Date:** 2026-02-10  
**Authors:** Three Dragons (Guardian + Architect + Witness)  
**Classification:** Internal — Required reading before production deployment  

> *"The Agent that protects governance must itself be governed."*

---

## 1. Deployment Security

### 1.1 Network Exposure — NEVER expose Flask directly

The WINDI Agent API (port 8091) **MUST NOT** be exposed to the public internet without protection layers.

**Required production stack:**

```
Internet → Nginx (TLS + rate limiting) → localhost:8091 (Flask Agent)
```

**Nginx configuration template:**

```nginx
# /etc/nginx/sites-available/windi-agent
server {
    listen 443 ssl http2;
    server_name agent.windia4desk.tech;

    # TLS (Let's Encrypt or institutional CA)
    ssl_certificate     /etc/letsencrypt/live/agent.windia4desk.tech/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/agent.windia4desk.tech/privkey.pem;
    ssl_protocols       TLSv1.3;
    ssl_ciphers         ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=agent_limit:10m rate=10r/s;
    limit_req zone=agent_limit burst=20 nodelay;

    # IP allowlist (recommended for initial deployment)
    # allow 10.0.0.0/8;      # Internal network
    # allow 87.106.29.233;    # Strato server itself
    # deny all;

    # Request size limit
    client_max_body_size 10M;

    # Timeouts
    proxy_connect_timeout 30s;
    proxy_read_timeout 60s;
    proxy_send_timeout 30s;

    location /agent/ {
        proxy_pass http://127.0.0.1:8091/agent/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Redirect HTTP → HTTPS
server {
    listen 80;
    server_name agent.windia4desk.tech;
    return 301 https://$host$request_uri;
}
```

### 1.2 Authentication

**Phase 2 (current):** Bearer token + IP allowlist

```python
# Required header for all API calls:
Authorization: Bearer <WINDI_AGENT_TOKEN>
```

**Phase 3 (production):** mTLS (mutual TLS)

- Client must present a valid certificate signed by the WINDI Hub CA
- This ensures only authorized nodes can communicate with the Agent
- Aligns with the Node Certificate architecture in Federation Spec §3.2

### 1.3 Flask in Production

**NEVER** use Flask's development server (`app.run()`) in production.

**Required:** Use a production WSGI server:

```bash
# Option A: Gunicorn (recommended)
pip install gunicorn
gunicorn --bind 127.0.0.1:8091 --workers 2 --timeout 60 "agent:create_agent_api(agent)"

# Option B: uWSGI
pip install uwsgi
uwsgi --http 127.0.0.1:8091 --module agent --callable app --processes 2
```

---

## 2. Identity & Authentication

### 2.1 Operator Identity — MUST be verifiable

The `--operator` CLI parameter **MUST NOT** remain a free-form string in production.

**Current (Phase 2 — acceptable for development):**
```bash
python3 agent.py --operator "Human Dragon"
```

**Production (Phase 3 — required):**

Operator identity must be:

| Requirement | Implementation |
|---|---|
| Linked to legal identity | Bound to Node Certificate operator field |
| Cryptographically signed | Operator signs activation with their Ed25519 key |
| Recorded in Manifest | `activated_by_key_fingerprint` field added |
| Verifiable by Hub | Hub can confirm operator authorization |

**Manifest enhancement for production:**

```json
{
  "activated_by": "Jober Moegele Correa",
  "activated_by_role": "Chief Governance Officer",
  "activated_by_key_fingerprint": "SHA256:abc123...",
  "activation_signature": "ed25519:...",
  "operator_certificate_ref": "NODE-CERT-W001-2026"
}
```

### 2.2 API Authentication Middleware

All `/agent/*` endpoints require authentication:

```python
# Authentication check before every request
@app.before_request
def verify_auth():
    if request.endpoint and request.endpoint != 'health':
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not verify_token(token):
            return jsonify({"error": "Unauthorized", "code": "AUTH_REQUIRED"}), 401
```

---

## 3. Logging & Forensic Trail

### 3.1 Immutable Local Log

Every Agent operation generates a log entry that is:

- **Append-only** — entries cannot be modified or deleted
- **Hash-chained** — each entry includes the hash of the previous entry
- **Timestamped** — with monotonic timestamps (not wall clock alone)
- **Signed** — by the Agent's operational key

**Log entry structure:**

```json
{
  "sequence": 1,
  "prev_hash": "0000000000000000000000000000000000000000000000000000000000000000",
  "timestamp": "2026-02-10T09:05:28.123Z",
  "monotonic_ns": 1234567890,
  "operation": "analyze_document",
  "detail_hash": "sha256:...",
  "agent_version": "1.0.0",
  "config_hash": "sha256:...",
  "entry_hash": "sha256(sequence + prev_hash + timestamp + operation + ...)"
}
```

### 3.2 Agent Code Integrity

The Agent Manifest **MUST** include:

| Field | Purpose |
|---|---|
| `code_hash` | SHA-256 of all Agent source files |
| `invariant_version` | Version hash of the loaded invariant set |
| `constitution_hash` | Hash of the Clone Matrix (P0-P7) being enforced |
| `dependency_hash` | Hash of installed Python packages |

This allows any auditor to verify: *"Was this the exact code that was running when this governance event was processed?"*

### 3.3 Log Rotation & Preservation

```
/opt/windi/agents/constitutional-agent/
├── logs/
│   ├── agent_2026-02-10.jsonl       # Daily log files
│   ├── agent_2026-02-11.jsonl
│   └── ...
├── manifests/
│   ├── manifest_1707555928.json     # Per-session manifests
│   └── ...
└── traces/
    ├── trace_VR-ABC123.json         # Per-receipt Decision Traces
    └── ...
```

**Retention:** Minimum 7 years (aligns with German Handelsgesetzbuch §257 commercial retention requirements and EU AI Act audit requirements).

---

## 4. Endpoint Security

### 4.1 `/agent/analyze` — Input Validation

| Control | Value | Reason |
|---|---|---|
| Max request body | 10 MB | Prevent memory exhaustion |
| Processing timeout | 60 seconds | Prevent resource starvation |
| Rate limit | 10 req/s per client | Prevent abuse |
| Queue depth | 100 pending | Backpressure mechanism |
| Document hash format | SHA-256 hex (64 chars) | Reject malformed input |

### 4.2 `/agent/decision` — Human Decision Recording

This endpoint records sovereign human decisions. Additional controls:

- **Requires elevated authentication** (operator-level, not service-level)
- **Cannot be called by automated systems** without `human_initiated: true`
- **Double-write:** Decision is written to both the receipt and the forensic log
- **Non-reversible:** Once recorded, a decision cannot be modified (only overridden with a new decision event)

### 4.3 Health Endpoint — Public

`/agent/health` is the **only** endpoint that may be called without authentication. It returns only:

```json
{
  "status": "alive",
  "agent": "WINDI Constitutional Execution Agent",
  "version": "1.0.0"
}
```

No internal state, no configuration details, no sensitive information.

---

## 5. Dependency Management

### 5.1 Virtual Environment — Required

```bash
# Create isolated environment
python3 -m venv /opt/windi/venv
source /opt/windi/venv/bin/activate

# Install dependencies
pip install flask gunicorn

# Lock dependencies
pip freeze > /opt/windi/agents/constitutional-agent/requirements.txt
```

**NEVER** use `pip install --break-system-packages` in production.

### 5.2 Dependency Auditing

```bash
# Check for known vulnerabilities
pip install pip-audit
pip-audit

# Generate SBOM (Software Bill of Materials)
pip install cyclonedx-bom
cyclonedx-py -o sbom.json
```

---

## 6. Operational Procedures

### 6.1 Startup Checklist

Before activating the Agent in production:

- [ ] Nginx reverse proxy configured with TLS
- [ ] Authentication tokens generated and distributed
- [ ] Virtual environment created and dependencies installed
- [ ] All 23 invariant tests passing
- [ ] Compliance scan returns 100%
- [ ] Forensic log directory writable
- [ ] Backup of previous Agent version taken
- [ ] Manifest generated and reviewed
- [ ] Operator identity verified

### 6.2 Monitoring

| Metric | Threshold | Action |
|---|---|---|
| Health endpoint response | > 5s | Alert |
| I9 violation detected | Any | IMMEDIATE HALT + Alert |
| Compliance score | < 100% | Investigate |
| Pending escalations | > 10 | Alert operator |
| Error rate | > 5% | Investigate |
| Disk space (logs) | < 1 GB | Rotate logs |

### 6.3 Incident Response

If an I9 violation is detected in production:

1. **HALT** — Agent stops immediately (automatic)
2. **ALERT** — Notify operator and compliance team
3. **PRESERVE** — Forensic log is preserved as evidence
4. **INVESTIGATE** — Determine root cause
5. **REMEDIATE** — Fix and verify before restart
6. **DOCUMENT** — Record incident in governance ledger

An I9 violation in production is a **critical governance incident**, not a software bug.

---

## 7. Compliance Alignment

| Standard | How WINDI Agent Complies |
|---|---|
| **EU AI Act** | Human oversight (Art. 14), logging (Art. 12), transparency (Art. 13) |
| **BSI C5** | Access control, audit logging, incident management |
| **ISO 27001** | Information security management, access control, operations security |
| **GDPR** | Zero-knowledge architecture — no personal data in Agent logs |
| **HGB §257** | 7-year retention of governance-relevant records |

---

## 8. Production Deployment Statement

> *"Production deployments of the WINDI Constitutional Execution Agent must be executed through the WINDI Secure Node Installer, which enforces all security controls defined in this document. Manual deployments are permitted only for development and testing environments."*

---

*WINDI Agent Operational Security Model v1.0.0*  
*Tripartite Governance Framework — Three Dragons Protocol*  
*"The Agent that protects governance must itself be governed."*  
*© 2026 WINDI Publishing House. Kempten (Allgäu), Bavaria, Germany.*
