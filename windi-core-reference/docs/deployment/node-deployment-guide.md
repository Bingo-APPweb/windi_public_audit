# WINDI Node Deployment Guide

**For Partners Running Their Own WINDI Node**

This guide is for:
- Banks
- Large enterprises
- Government entities
- Infrastructure providers

...who want to run a sovereign WINDI node that participates in the broader trust ecosystem.

---

## What Is a WINDI Node?

A WINDI Node is a self-hosted trust verification unit that:

- Verifies document integrity
- Applies risk policies
- Maintains forensic audit trails
- Participates in the federated issuer trust network
- Publishes transparency anchors

It allows an organization to verify documents **locally** while remaining interoperable with the global WINDI ecosystem.

```
┌─────────────────────────────────────────────────────────────────┐
│                     YOUR WINDI NODE                             │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │ verification│  │ policy-api  │  │ forensics-api           │ │
│  │ -api :4000  │  │ :4020       │  │ :4010                   │ │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘ │
│         │                │                     │               │
│         └────────────────┼─────────────────────┘               │
│                          │                                      │
│                    ┌─────▼─────┐                               │
│                    │ postgres  │                               │
│                    │ :5432     │                               │
│                    └───────────┘                               │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │ issuer-     │  │transparency-│  │ public-anchor-log       │ │
│  │ registry    │  │ anchor      │  │ :4050                   │ │
│  │ :4030       │  │ :4040       │  │                         │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
│                                                                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼ Federated Trust Network
              ┌────────────────────────────┐
              │  WINDI Global Ecosystem    │
              │  - Central Registry        │
              │  - Public Anchor Log       │
              │  - Other Partner Nodes     │
              └────────────────────────────┘
```

---

## Node Architecture

A full node runs these services:

| Service | Port | Purpose |
|---------|------|---------|
| `verification-api` | 4000 | Cryptographic verification |
| `policy-api` | 4020 | Risk decisions |
| `forensics-api` | 4010 | WCAF event log |
| `issuer-registry` | 4030 | Trust governance |
| `transparency-anchor` | 4040 | Snapshot + anchoring |
| `public-anchor-log` | 4050 | Public transparency log (optional) |
| `audit-report` | 4060 | Generates signed audit reports (optional) |
| `postgres` | 5432 | Persistent storage |

Deployment is handled via: **windi-docker-stack**

---

## Quick Start Deployment

### 1. Clone the stack

```bash
git clone https://github.com/Bingo-APPweb/windi-docker-stack.git
cd windi-docker-stack
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```bash
# Node identity
NODE_ID=partner-bank-xyz
NODE_ROLE=partner

# Database
POSTGRES_PASSWORD=<strong-password>

# Federation
PUBLIC_ANCHOR_LOG_URL=https://anchor.windi.systems
ISSUER_REGISTRY_SYNC_URL=https://registry.windi.systems

# Security
ADMIN_API_KEYS=<generate-secure-keys>

# Localization
DEFAULT_LOCALE=en
```

### 3. Generate attestation key

**Development:**
```bash
./scripts/generate-dev-key.sh
```

**Production (recommended):**
```bash
# Use HSM or cloud KMS
# AWS KMS example:
aws kms create-key --description "WINDI Attestation Key"

# Azure Key Vault example:
az keyvault key create --vault-name windi-vault --name attestation-key --kty RSA
```

### 4. Create secrets directory

```bash
mkdir -p secrets
# Copy your attestation key
cp /path/to/attestation_key.pem secrets/windi_attestation_key.pem
cp /path/to/audit_signing_key.pem secrets/audit_signing_key.pem
```

### 5. Start services

```bash
docker compose up -d --build
```

### 6. Verify deployment

```bash
# Check all services are healthy
docker compose ps

# Test verification API
curl http://localhost:4000/health

# Test policy API
curl http://localhost:4020/health

# Test forensics API
curl http://localhost:4010/health
```

Your node is now running.

---

## Environment Variables Reference

### Core Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `NODE_ID` | `windi-node-1` | Unique node identifier |
| `NODE_ROLE` | `standalone` | `standalone`, `partner`, `central` |
| `NODE_ENV` | `development` | `development`, `production` |

### Database

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_DB` | `windi` | Database name |
| `POSTGRES_USER` | `windi` | Database user |
| `POSTGRES_PASSWORD` | - | Database password (required) |
| `DATABASE_URL` | auto | Full connection string |

### Federation

| Variable | Default | Description |
|----------|---------|-------------|
| `PUBLIC_ANCHOR_LOG_URL` | - | Global transparency log URL |
| `ISSUER_REGISTRY_SYNC_URL` | - | Central registry for sync |
| `REGISTRY_SYNC_INTERVAL` | `3600` | Sync interval in seconds |

### Security

| Variable | Default | Description |
|----------|---------|-------------|
| `ADMIN_API_KEYS` | - | Comma-separated admin keys |
| `WINDI_ATTESTATION_KEY_ID` | `windi-root-2026` | Attestation key identifier |
| `SIGNING_KEY_ID` | `windi-audit-2026` | Audit report signing key ID |

### Service Ports

| Variable | Default | Description |
|----------|---------|-------------|
| `WINDI_VERIFY_PORT` | `4000` | Verification API port |
| `WINDI_POLICY_PORT` | `4020` | Policy API port |
| `WINDI_FORENSICS_PORT` | `4010` | Forensics API port |
| `WINDI_REGISTRY_PORT` | `4030` | Issuer Registry port |
| `WINDI_ANCHOR_PORT` | `4040` | Transparency Anchor port |
| `WINDI_ANCHOR_LOG_PORT` | `4050` | Public Anchor Log port |
| `WINDI_REPORT_PORT` | `4060` | Audit Report port |

---

## Federation Model

A partner node can operate in different modes:

| Capability | Mode | Description |
|------------|------|-------------|
| Use central issuer registry | Default | Trust central WINDI registry |
| Mirror TRUSTED issuers | Optional | Cache trusted issuers locally |
| Maintain private issuers | Supported | Add institution-specific issuers |
| Publish own transparency anchors | Supported | Independent anchor chain |
| Join global transparency log | Recommended | Publish to central log |

### Federation Configuration

```bash
# Full federation (recommended)
NODE_ROLE=partner
ISSUER_REGISTRY_SYNC_URL=https://registry.windi.systems
PUBLIC_ANCHOR_LOG_URL=https://anchor.windi.systems

# Standalone (air-gapped)
NODE_ROLE=standalone
# No sync URLs - fully independent

# Hybrid (private issuers + global trust)
NODE_ROLE=partner
ISSUER_REGISTRY_SYNC_URL=https://registry.windi.systems
ALLOW_PRIVATE_ISSUERS=true
```

---

## Operational vs Forensic Modes

| Mode | Purpose | Services Used |
|------|---------|---------------|
| **Operational** | Real-time `/verify` decisions | verification-api, policy-api, issuer-registry |
| **Forensic** | Historical proof + audit reports | forensics-api, transparency-anchor, audit-report |

A node can operate in both simultaneously.

### Operational Mode Flow

```
Document → Hash → /verify → ALLOW/HOLD/BLOCK
                     ↓
              Policy applied
                     ↓
              WCAF event logged
```

### Forensic Mode Flow

```
WCAF Bundle → transparency-anchor → public-anchor-log
                                          ↓
                                   audit-report
                                          ↓
                                   Signed PDF + JSON
```

---

## Security Responsibilities

Node operators must:

### Key Management

- Protect attestation keys (use HSM/KMS in production)
- Rotate keys periodically
- Never commit keys to version control
- Use separate keys for dev/staging/production

### Database Security

- Use strong passwords
- Enable encryption at rest
- Regular backups (see backup section)
- Restrict network access to database

### Network Security

- Run behind reverse proxy (nginx/traefik)
- Enable TLS for all endpoints
- Restrict admin APIs to internal network
- Use firewall rules

### Monitoring

- Monitor service health
- Alert on verification failures
- Track anchor publication
- Audit admin actions

---

## Production Deployment

### 1. TLS Configuration

```yaml
# docker-compose.override.yml
services:
  traefik:
    image: traefik:v2.10
    command:
      - "--providers.docker=true"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.tlschallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.email=admin@yourorg.com"
    ports:
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./letsencrypt:/letsencrypt

  verification-api:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.verify.rule=Host(`verify.yourorg.com`)"
      - "traefik.http.routers.verify.tls.certresolver=letsencrypt"
```

### 2. Resource Limits

```yaml
# docker-compose.override.yml
services:
  postgres:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G

  verification-api:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
```

### 3. Health Monitoring

```yaml
# docker-compose.override.yml
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

---

## Backup and Recovery

### Database Backup

```bash
# Daily backup script
#!/bin/bash
BACKUP_DIR=/var/backups/windi
DATE=$(date +%Y%m%d_%H%M%S)

docker compose exec -T postgres pg_dump -U windi windi | gzip > $BACKUP_DIR/windi_$DATE.sql.gz

# Keep last 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
```

### Anchor Log Backup

```bash
# Export anchor log
curl http://localhost:4050/export > anchor_log_backup.json
```

### Recovery

```bash
# Restore database
gunzip -c windi_backup.sql.gz | docker compose exec -T postgres psql -U windi windi

# Restore anchor log (requires service restart)
# Copy backup to data volume before starting
```

---

## Troubleshooting

### Services won't start

```bash
# Check logs
docker compose logs verification-api
docker compose logs postgres

# Check disk space
df -h

# Check memory
free -m
```

### Database connection issues

```bash
# Test connection
docker compose exec postgres psql -U windi -c "SELECT 1"

# Check if migrations ran
docker compose exec postgres psql -U windi -c "\dt"
```

### Anchor publication failing

```bash
# Check anchor log connectivity
curl http://localhost:4050/health

# Check transparency anchor logs
docker compose logs transparency-anchor

# Manual anchor test
curl -X POST http://localhost:4040/anchor/run
```

---

## Upgrade Procedure

### 1. Backup first

```bash
./scripts/backup.sh
```

### 2. Pull latest images

```bash
docker compose pull
```

### 3. Rolling update

```bash
# Update one service at a time
docker compose up -d --no-deps verification-api
docker compose up -d --no-deps policy-api
# ... etc
```

### 4. Verify

```bash
docker compose ps
curl http://localhost:4000/health
```

---

## What Running a Node Enables

| Without Node | With Node |
|--------------|-----------|
| API consumer only | Sovereign verifier |
| Trusts central infrastructure | Participates in trust network |
| Limited audit scope | Full forensic capability |
| Data leaves your network | Data stays local |
| Dependent on external availability | Self-sufficient operations |

---

## Compliance Considerations

Running a WINDI node helps meet:

| Regulation | How WINDI Helps |
|------------|-----------------|
| **GDPR** | Document hashes only, no PII transmitted |
| **eIDAS** | Qualified timestamp via transparency anchors |
| **SOX** | Complete audit trail in WCAF |
| **Basel III** | Operational risk documentation |
| **MiFID II** | Transaction record keeping |

---

## Support

- Documentation: https://docs.windi.systems
- Partner Portal: https://partners.windi.systems
- Technical Support: partners@windi.systems
- Status Page: https://status.windi.systems

---

## Next Steps

After deploying your node:

1. **Register as Partner** — Contact WINDI to join the federation
2. **Configure Issuers** — Add your trusted document issuers
3. **Integrate Applications** — Connect your ERP/banking systems
4. **Enable Anchoring** — Publish to the global transparency log
5. **Monitor Operations** — Set up alerting and dashboards
