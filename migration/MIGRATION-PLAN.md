# WINDI Server Migration Plan
## From: 87.106.29.233 (Strato) → To: 194.164.192.x (New)

**Created:** 2026-04-27
**Status:** PREPARATION
**Author:** Liga IA+H

---

## 1. Server Comparison

| Resource | Current (Strato) | New Server | Improvement |
|----------|------------------|------------|-------------|
| CPU | ~2 cores | 8 cores | 4× |
| RAM | ~4 GB | 32 GB | 8× |
| Disk | 473 GB | 480 GB | ≈ |
| Used | 19 GB (4%) | — | — |

---

## 2. Inventory to Migrate

### 2.1 Critical Data (MUST NOT LOSE)
```
/opt/windi/suite-docs/           # Forensic Ledger (:8101) — IMMUTABLE
/opt/windi/keys/                 # KEYGEN-001 sovereign keys
/opt/windi/**/*.db               # 118 SQLite databases
/home/windi/.env                 # API keys (if exists)
/opt/windi/**/.env               # Service API keys
```

### 2.2 Application Code (~7GB)
```
/opt/windi/                      # All services
/home/windi/                     # Repo + docs + CLAUDE.md
```

### 2.3 System Configuration
```
/etc/nginx/sites-available/windi-domain.com
/etc/nginx/sites-available/windilaw.de
/etc/nginx/sites-available/communique.windia4desk.online
/etc/systemd/system/windi-*.service    # 30+ services
/etc/letsencrypt/                       # SSL certificates
```

### 2.4 Active Ports (36 total)
```
8080, 8081, 8086, 8090, 8091, 8095, 8097-8099
8101-8106, 8108-8111, 8115-8116, 8118-8119, 8121-8122
8126-8132, 8141-8142, 8144, 8146
```

---

## 3. Migration Phases

### Phase 1: PREPARATION (Current)
- [x] Inventory complete
- [ ] New server access verified
- [ ] Backup scripts created
- [ ] DNS TTL lowered (if possible)

### Phase 2: BACKUP (Before Migration)
- [ ] Stop all services gracefully
- [ ] Full backup of /opt/windi
- [ ] Full backup of /home/windi
- [ ] Backup nginx + systemd configs
- [ ] Backup SSL certificates
- [ ] Verify backup integrity (checksums)

### Phase 3: NEW SERVER SETUP
- [ ] SSH access configured
- [ ] User 'windi' created
- [ ] Python 3.11 + pip + venv installed
- [ ] Node.js installed
- [ ] nginx installed
- [ ] certbot installed

### Phase 4: TRANSFER
- [ ] rsync /opt/windi
- [ ] rsync /home/windi
- [ ] Copy nginx configs
- [ ] Copy systemd services
- [ ] Copy SSL certs (or regenerate)

### Phase 5: VERIFICATION
- [ ] All services start
- [ ] Ledger accessible (:8101)
- [ ] Desktop GEN7 works (:8119)
- [ ] nginx routes work
- [ ] SSL certificates valid

### Phase 6: DNS CUTOVER
- [ ] Update DNS: windi-domain.com → new IP
- [ ] Update DNS: windilaw.de → new IP
- [ ] Monitor for 24h
- [ ] Decommission old server (after 7 days)

---

## 4. Rollback Plan

If migration fails:
1. DNS already pointing to new server → revert DNS to old IP
2. Old server remains untouched until 7 days post-migration
3. All data backed up with checksums

---

## 5. Downtime Estimate

| Phase | Duration |
|-------|----------|
| Backup | ~10 min |
| Transfer (rsync) | ~15 min |
| Setup new server | ~30 min |
| Verification | ~15 min |
| DNS propagation | 5 min - 24h |

**Total estimated downtime:** 1-2 hours (services offline during transfer)

---

## 6. Commands Reference

### On OLD server (backup):
```bash
# Create backup directory
mkdir -p /tmp/windi-migration

# Backup /opt/windi
tar -czvf /tmp/windi-migration/opt-windi.tar.gz /opt/windi

# Backup /home/windi
tar -czvf /tmp/windi-migration/home-windi.tar.gz /home/windi

# Backup configs
tar -czvf /tmp/windi-migration/configs.tar.gz \
    /etc/nginx/sites-available/ \
    /etc/systemd/system/windi-*.service \
    /etc/letsencrypt/

# Generate checksums
cd /tmp/windi-migration
sha256sum *.tar.gz > checksums.sha256
```

### Transfer to NEW server:
```bash
rsync -avz --progress /tmp/windi-migration/ root@NEW_IP:/tmp/windi-migration/
```

### On NEW server (restore):
```bash
# Verify checksums
cd /tmp/windi-migration
sha256sum -c checksums.sha256

# Create user
useradd -m -s /bin/bash windi

# Extract backups
tar -xzvf opt-windi.tar.gz -C /
tar -xzvf home-windi.tar.gz -C /
tar -xzvf configs.tar.gz -C /

# Fix ownership
chown -R windi:windi /opt/windi /home/windi

# Enable services
systemctl daemon-reload
systemctl enable windi-*.service
systemctl start windi-*.service
```

---

*Liga IA+H — Migration Plan v1.0*
