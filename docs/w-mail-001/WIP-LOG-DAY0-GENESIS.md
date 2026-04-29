# WIP-LOG-W-MAIL-001-DAY0 — Genesis & Foundation
**Service:** W-MAIL-001 Email Sovereign System
**Date:** 2026-04-29
**Stage:** Day 0 → Day 1 Execution
**Status:** 🟢 GO TOTAL (Guardian approved after DNS calibration)

---

## § Decisões Constitucionais

### 1. Strategic Pivot (Guardian Analysis)
**Context:** W-SITES-001 infrastructure complete (10/10 tests passing), but missing foundational email layer.

**Guardian Assessment:**
> "Email não é feature. É infraestrutura de identidade... W-MAIL-001 primeiro, W-SITES depois."

**Approved:** W-MAIL-001 as foundational infrastructure before W-SITES feature development.

**Constitutional Risks Identified:**
1. **I1 (Soberania Humana):** DID keypair ownership validation
2. **I9 (Proibição Autonomia):** Email sending requires explicit human approval
3. **I11 (Permanência Forense):** All sent emails sealed in Ledger
4. **I12 (Language Sovereignty):** Email content vs UI language separation
5. **I14 (Explicit Failure):** SMTP errors exposed, never masked

### 2. DKIM Dual Selector Strategy
**Decision:** Ed25519 (primary) + RSA-2048 (fallback)
**Rationale:** Ed25519 = modern + DID-aligned; RSA = legacy receiver compatibility
**Approved by:** Human Dragon (26 Apr 2026)

### 3. DNS Architecture — CNAME Trade-off (CRITICAL)
**Platform:** Strato shared hosting
**Constraint:** No granular A/AAAA per-subdomain control in panel
**Reality:** `mail.windisites.de` → CNAME → `windisites.de` → A `87.106.29.233`

**DNS Resolution Chain:**
```dns
mail.windisites.de.    76    IN    CNAME    windisites.de.
windisites.de.         76    IN    A        87.106.29.233
windisites.de.         76    IN    AAAA     2a02:2479:9e:1000::1
```

**HELO Validation Cycle:**
1. Postfix HELO: `mail.windisites.de`
2. Forward lookup: `mail.windisites.de` → (CNAME) → `windisites.de` → `87.106.29.233`
3. Reverse lookup: `87.106.29.233` → `mail.windisites.de` ✓ (PTR configured)

**RFC Compliance:**
- RFC 2181 (1997): Prohibits CNAME in MX target (not applicable — our MX points to hostname, not CNAME)
- RFC 5321 (2008): Silent on CNAME in HELO hostname
- RFC 7505 + modern practice: Most receivers tolerate CNAME in forward lookup

**Risk Assessment (Guardian calibrated):**
- **Gmail/Outlook/ProtonMail/Yahoo/iCloud:** Accept CNAME, no penalty (~98-99% delivery)
- **Legacy Exchange on-prem:** Some reject/degrade (~85-90% delivery)
- **mail-tester.com:** Expected 8.5-9.0/10 (vs 9.5+/10 with direct A)
- **Warm-up impact:** Marginal degradation (5-10%), not catastrophic

**Trade-off Accepted:**
- ✅ Marginal HELO score degradation (~5-10%)
- ✅ Strato platform constraint, not technical choice
- ✅ PTR + SPF + DMARC + DKIM (dual) compensate
- ✅ Re-evaluate if metrics breach thresholds
- 🔮 Future fix: Migrate to Cloudflare/Route53 when Gemini server arrives

**Re-evaluation Criteria:**
```
ABORT WARM-UP IF:
- mail-tester.com score < 8.0
- Bounce rate > 5% during first 50 emails
- Specific corporate recipients reject (Exchange on-prem pattern)
→ THEN: Open Strato ticket OR migrate DNS to Cloudflare
```

**Decision Authority:** Human Dragon (29 Apr 2026)
**Guardian Veredicto:** GO TOTAL after evidence calibration

**Guardian Note:**
> "Não mudei por pressão de momentum. Mudei porque CCODE me deu dados reais (dig output)...
> Com dados, o risco fica calibrado: marginal, monitorável, reversível."

---

## § Decisões Operacionais

### Domain Selection
**Chosen:** `windisites.de`
**Rejected:** `windi.site` (too close to main brand, separation unclear)
**Rationale:** W-SITES product identity + clear separation from WINDI core

### Staging Strategy
**Approach:** Single production deployment (no staging/dev split)
**Justification:**
- Email reputation is IP-based (can't split without multiple IPs)
- Staging emails pollute production reputation
- Better: One clean start + careful warm-up

### First Mailbox
**Address:** `postmaster@windisites.de`
**Purpose:** Administrative + abuse handling (RFC required)
**DID:** TBD (generated during setup)

---

## § Configurações Executadas (Day 0)

### DNS Records (windisites.de)
**Provider:** Strato
**Configured:** 2026-04-29 ~16:00 UTC
**Propagation:** Verified ~16:25 UTC (~25 min, not 24h as expected)

| Type | Name | Value | Status |
|------|------|-------|--------|
| A | @ | 87.106.29.233 | ✅ Propagated |
| AAAA | @ | 2a02:2479:9e:1000::1 | ✅ Propagated |
| MX | @ | 10 mail.windisites.de | ✅ Propagated |
| TXT | @ | v=spf1 ip4:87.106.29.233 ip6:2a02:2479:9e:1000::1 -all | ✅ Propagated |
| TXT | @ | v=DMARC1; p=quarantine; rua=mailto:postmaster@windisites.de | ✅ Propagated |
| PTR | 87.106.29.233 | mail.windisites.de | ✅ Configured |
| PTR | 2a02:2479:9e:1000::1 | mail.windisites.de | ✅ Configured |
| CNAME | mail | windisites.de | ✅ Auto (Strato) |

**Verification Commands:**
```bash
host -t A windisites.de          # 87.106.29.233
host -t AAAA windisites.de       # 2a02:2479:9e:1000::1
host -t MX windisites.de         # 10 mail.windisites.de
host -t TXT windisites.de        # SPF + DMARC
host 87.106.29.233               # mail.windisites.de (PTR)
host -v mail.windisites.de       # CNAME → A 87.106.29.233
```

---

## § Parallel Work (Day 0)

### Track A — Security (P0/P1)
1. ✅ **§139 WINDI-LAW Attachments Panel**
   - Persistent floating panel with SHA-256 display
   - Copy hash button + individual removal
   - NOIR design + badge counter
   - File: `/opt/windi/windi-law/workspace/index.html`

2. ✅ **DB Backup Automation**
   - Script: `/opt/windi/scripts/backup-dbs.sh`
   - Targets: 3 identity DBs (law/sites/travel)
   - SHA-256 verification + 30-day rotation
   - Systemd timer: `/opt/windi/systemd/windi-db-backup.{service,timer}`
   - Status: Files ready, awaits sudo installation

3. ✅ **Rate Limiting nginx (W-SITES-001)**
   - Zone: `sites_limit` 10MB, 10 req/min per IP
   - Burst: 5 requests, nodelay
   - Config: `/opt/windi/nginx/rate-limit-sites.conf`
   - Install: `/opt/windi/nginx/install-rate-limit.sh`
   - Status: Files ready, awaits sudo execution

### Track C — Infrastructure
4. ✅ **DB Consolidation**
   - Reduced: 141 → 134 DBs (-7)
   - Archived: 24 empty (0-byte) + 8 standalone backups
   - Archive: `/opt/windi/backups/archive/db-cleanup-20260429_172704/`
   - Script: `/opt/windi/scripts/consolidate-dbs.sh`
   - Result: 25 DBs moved, 7 active DBs preserved

5. ✅ **nohup → systemd Migration**
   - Verified: 45 services already in systemd
   - Exception: Sandbox Core (:8091) intentionally remains nohup (per CLAUDE.md)
   - Status: Migration already complete, no action needed

### Track B — Berlin Pitch
6. ⏳ **W-TRAVEL-PUB-001 Berlin Demo**
   - Deadline: 10 May 2026 (11 days remaining)
   - Awaits: Real travel content from Human Dragon
   - Checklist: 1 caderno, 5-10 postais + GPS, mapa comparador, URL público, QR slide

---

## § Open Questions

None — Guardian resolved all Day 0 blockers.

---

## § TODOs — Day 1 Pipeline

### Phase 1: Let's Encrypt Certificate
- [ ] Install certbot (if not present)
- [ ] Request cert: `certbot certonly --standalone -d mail.windisites.de`
- [ ] Verify: `/etc/letsencrypt/live/mail.windisites.de/`

### Phase 2: Docker Mailserver
- [ ] Pull `docker-mailserver/docker-mailserver:latest`
- [ ] Configure: Postfix + Dovecot + rspamd
- [ ] Ports: 25 (SMTP), 587 (submission), 993 (IMAPS)
- [ ] Volume: `/opt/windi/w-mail-001/mail-data`

### Phase 3: DKIM Dual Selector
- [ ] Generate Ed25519 keypair (2048-bit equivalent security)
- [ ] Generate RSA-2048 keypair (legacy fallback)
- [ ] Add TXT records: `ed25519._domainkey.windisites.de`, `rsa._domainkey.windisites.de`
- [ ] Configure Postfix: dual selector rotation

### Phase 4: SnappyMail WebUI
- [ ] Deploy SnappyMail container
- [ ] Configure: IMAP connection to Dovecot
- [ ] Port: 8200 (internal), nginx proxy `/mail/`
- [ ] First login: postmaster@windisites.de

### Phase 5: Smoke Tests
- [ ] Send test email: postmaster → postmaster (loopback)
- [ ] Verify: DKIM signatures present (both selectors)
- [ ] Check: SPF/DMARC headers
- [ ] Test: mail-tester.com score (target ≥8.0)

### Phase 6: PAUSA OBRIGATÓRIA
- [ ] Call Guardian with mail-tester.com results
- [ ] IF score < 8.0 → Re-evaluate DNS (Strato ticket or Cloudflare migration)
- [ ] IF score ≥8.0 → Proceed with warm-up plan
- [ ] Document decision in WIP-LOG-DAY1

### Phase 7: DID Integration
- [ ] Fork W-DID-GENESIS :8096 for email identity
- [ ] Link postmaster@windisites.de → DID keypair
- [ ] Ledger seal: First mailbox creation receipt

---

## § Guardian Final Note

> "Com dados, o risco fica calibrado: marginal, monitorável, reversível.
> Se tivesse insistido em 'bloqueante', estaria fazendo Guardian-by-paranoia
> em vez de Guardian-by-evidence. Isso não serve a Liga."

**Veredicto:** GO TOTAL
**OM SHANTI 🐉**

---

---

## § Day 1 Execution — SnappyMail WebUI Architecture

### DECISION: Webmail Isolation (29 Apr 2026 21:06 UTC)

**Context:** Initial approach tried to serve SnappyMail under `/mail/` path on windi-domain.com. This caused:
- Asset loading failures (JS/CSS paths incorrect)
- Domain confusion (mixing windi-domain.com authority with windisites.de staging)
- Architecture pollution (windisites.de root path needed for W-SITES factory)

**Guardian Intervention:** CCODE proposed Opção C with typo mixing `mail.windi-domain.com` server_name with `mail.windisites.de` certificate. Guardian caught error before execution and corrected to unified `mail.windisites.de` identity.

**Final Architecture (Opção C corrigida):**
- **URL:** `https://mail.windisites.de/` (dedicated subdomain)
- **Certificate:** `/etc/letsencrypt/live/mail.windisites.de/` (from Phase 1)
- **nginx:** Dedicated server block in `/etc/nginx/sites-enabled/mail.windisites.de`

**Rationale:**
- **Separation:** windisites.de = sites factory, mail.windisites.de = webmail
- **Coherence:** HELO/PTR/Webmail all unified under `mail.windisites.de` identity
- **Future-proof:** When migrating mail to Gemini server, only DNS change needed
- **Avoids:** Cross-domain cert mismatch, path pollution, staging/authority confusion

**Domain Boundaries:**
- `windi-domain.com` — Core Corporate Authority (One Tree)
- `windisites.de` — W-SITES-001 Factory (staging)
- `mail.windisites.de` — W-MAIL-001 Webmail (isolated)

**Guardian Note:**
> "Detectámos a confusão windi-domain.com vs windisites.de e corrigimos antes de virar realidade. Isso é Liga funcionando."

**Status:** LIVE — nginx reloaded, SnappyMail accessible at https://mail.windisites.de/

---

## § Day 1 Execution — DKIM Implementation

### DKIM Dual Selector — Guardian Verification (29 Apr 2026 21:15 UTC)

**Guardian Initial Concern:** Status report showed "DKIM RSA-2048 keys ✅ Generated" which gave impression of RSA-only implementation, potentially deviating from Human Dragon's Opção A decision (Ed25519 + RSA dual selector).

**Verification Results:**
```bash
# Keys generated (both present):
ed25519.private  ✅
ed25519.txt      ✅
rsa.private      ✅
rsa.txt          ✅

# KeyTable (selector mapping):
ed25519._domainkey.windisites.de  windisites.de:ed25519:/etc/opendkim/keys/.../ed25519.private
rsa._domainkey.windisites.de      windisites.de:rsa:/etc/opendkim/keys/.../rsa.private

# SigningTable (dual signing policy):
*@windisites.de  ed25519._domainkey.windisites.de
*@windisites.de  rsa._domainkey.windisites.de
```

**Guardian Conclusion:**
> "CCODE gerou dual selector desde o início, conforme decisão Human Dragon. Eu interpretei mal o status report anterior... Liga estava em ordem o tempo todo. Mea culpa Guardian."

**Implementation Details:**
- **Selectors generated:** `rsa` + `ed25519` (Day 1, single pass)
- **Naming convention:** `rsa._domainkey`, `ed25519._domainkey` (simplified, no `mail-` prefix)
- **Signing policy:** All `@windisites.de` emails signed with BOTH keys (dual signature)
- **DNS publication:** Pending Day 1 (Strato manual entry — 2 TXT records)
- **Constitutional alignment:** ✅ Honors Opção A (Human Dragon decision 26 Apr 2026)

**Guardian Recognition:**
> "CCODE, executou perfeitamente. Naming simplificado é defensável (mais limpo no DNS) e manteve coerência interna. Liga em forma."

**Status:** DKIM keys ready, awaiting DNS publication

**Files:** `/opt/windi/w-mail-001/DKIM-DUAL-STRATO.txt` (publication instructions)

---

**Next Step:** Publish BOTH DKIM TXT records to Strato → Verify propagation → Loopback smoke test → External smoke tests.

---

## § Day 1 Execution — DNS Publication & Smoke Tests (29-30 Apr 2026)

### DNS Publication Complete (29 Apr 2026 ~18:00 UTC)

**Status:** ✅ ALL 5 RECORDS VERIFIED

Human Dragon published BOTH DKIM TXT records to Strato panel:
- `rsa._domainkey.windisites.de` (501 chars, RSA-2048)
- `ed25519._domainkey.windisites.de` (95 chars, Ed25519)

**Verification Results (30 Apr 2026 ~02:30 UTC):**

```bash
# 1. SPF
host -t TXT windisites.de | grep "v=spf1"
✅ "v=spf1 ip4:87.106.29.233 ip6:2a02:2479:9e:1000::1 -all"

# 2. DMARC
host -t TXT _dmarc.windisites.de
✅ "v=DMARC1; p=quarantine; rua=mailto:postmaster@windisites.de"

# 3. DKIM Ed25519
host -t TXT ed25519._domainkey.windisites.de
✅ "v=DKIM1; k=ed25519; p=QVk1yf6zbvgBaR1yCvXWDBlSyT389why1D7Y9GZ9gl4="

# 4. DKIM RSA
host -t TXT rsa._domainkey.windisites.de
✅ "v=DKIM1; k=rsa; p=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8A..." (501 chars)

# 5. MX
host -t MX windisites.de
✅ "windisites.de mail is handled by 10 mail.windisites.de."
```

**Propagation Time:** ~8.5 hours (DNS published ~18:00, verified ~02:30 next day)

---

### Loopback Smoke Test — 7 Sequential Blockers (30 Apr 2026 02:30-04:15 UTC)

**Target:** Send `postmaster@windisites.de` → `postmaster@windisites.de`, verify dual DKIM signatures

#### Blocker 1: Empty OpenDKIM Config Files

**Error:** `no signing table match for 'postmaster@windisites.de'`

**Root Cause:** Files in `/etc/opendkim/` were 0 bytes (empty). Docker-mailserver setup script populated `/tmp/docker-mailserver/opendkim/` but never copied to runtime location.

**Fix:**
```bash
sudo docker exec windi-mailserver cp /tmp/docker-mailserver/opendkim/TrustedHosts /etc/opendkim/
sudo docker exec windi-mailserver cp /tmp/docker-mailserver/opendkim/KeyTable /etc/opendkim/
sudo docker exec windi-mailserver cp /tmp/docker-mailserver/opendkim/SigningTable /etc/opendkim/
sudo docker exec windi-mailserver supervisorctl restart opendkim
```

#### Blocker 2: Keys in Insecure Location (/tmp)

**Error:** `key data is not secure: /tmp can be read or written by other users`

**Fix:**
```bash
sudo docker exec windi-mailserver mkdir -p /etc/opendkim/keys/windisites.de
sudo docker exec windi-mailserver bash -c 'cp /tmp/docker-mailserver/opendkim/keys/windisites.de/* /etc/opendkim/keys/windisites.de/'
```

#### Blocker 3: Permission Denied on Private Keys

**Error:** `can't load key from /etc/opendkim/keys/windisites.de/ed25519.private: Permission denied`

**Root Cause:** Keys owned by `root:root`, but OpenDKIM runs as user `opendkim`

**Fix:**
```bash
sudo docker exec windi-mailserver chmod 700 /etc/opendkim/keys/windisites.de
sudo docker exec windi-mailserver chmod 600 /etc/opendkim/keys/windisites.de/*.private
sudo docker exec windi-mailserver chmod 644 /etc/opendkim/keys/windisites.de/*.txt
sudo docker exec windi-mailserver chown -R opendkim:opendkim /etc/opendkim/keys/windisites.de/
```

#### Blocker 4: CRITICAL — OpenDKIM v2.11.0 Does NOT Support Ed25519

**Error:** `SSL error:0300007F:digital envelope routines::expecting an rsa key`

**Investigation:**
```bash
sudo docker exec windi-mailserver opendkim -V
# OpenDKIM Filter v2.11.0

sudo docker exec windi-mailserver openssl pkey -in /etc/opendkim/keys/windisites.de/ed25519.private -text -noout | head -3
# ED25519 Private-Key:
# priv: [32 bytes]
# pub: [32 bytes]
```

**Guardian Analysis:**
> "Ed25519 key is REAL (119 bytes, openssl confirms ED25519 Private-Key). But OpenDKIM v2.11.0 cannot parse it. Ed25519 support added in OpenDKIM v2.11.4+ (unreleased/beta)."

**Guardian Decision (30 Apr 2026 03:45 UTC):**

Opções apresentadas:
- **Opção A:** Bloquear Day 1, aguardar OpenDKIM upgrade (REJECTED — timeline impact)
- **Opção B:** RSA-only interim, Ed25519 em Day 2+ quando upgrade disponível (ACCEPTED)
- **Opção C:** Migrate to rspamd (REJECTED — scope creep)

**Human Dragon Decisão:** **Opção B — RSA-only interim**

**Rationale:**
- Ed25519 keys já publicados no DNS (preservados para futuro)
- RSA-2048 provides strong security (industry standard)
- Unblocks Day 1 warm-up timeline
- Ed25519 upgrade path clear when OpenDKIM 2.11.4+ available

**Implementation:**
```bash
sudo docker exec windi-mailserver bash -c 'cat > /etc/opendkim/SigningTable << EOF
# Ed25519 commented out - OpenDKIM 2.11.0 does not support Ed25519
# Will be re-enabled when OpenDKIM upgraded to v2.11.4+
# *@windisites.de ed25519._domainkey.windisites.de
*@windisites.de rsa._domainkey.windisites.de
EOF'
```

#### Blocker 5: SigningTable Corrupted with "EOF" String

**Error:** `no signing table match for 'postmaster@windisites.de'`

**Root Cause:** Heredoc syntax error left literal "EOF" string in file

**Fix:**
```bash
sudo docker exec windi-mailserver bash -c 'echo "*@windisites.de rsa._domainkey.windisites.de" > /etc/opendkim/SigningTable'
sudo docker exec windi-mailserver cat /etc/opendkim/SigningTable
# *@windisites.de rsa._domainkey.windisites.de ✅
```

#### Blocker 6: KeyTable Paths Incorrect

**Error:** Key paths pointed to `/tmp/docker-mailserver/opendkim/keys/` instead of `/etc/opendkim/keys/`

**Fix:**
```bash
sudo docker exec windi-mailserver bash -c 'cat > /etc/opendkim/KeyTable << EOF
ed25519._domainkey.windisites.de windisites.de:ed25519:/etc/opendkim/keys/windisites.de/ed25519.private
rsa._domainkey.windisites.de windisites.de:rsa:/etc/opendkim/keys/windisites.de/rsa.private
EOF'
```

#### Blocker 7: TrustedHosts Empty

**Error:** Emails not being signed (no error, but DKIM-Signature absent)

**Fix:**
```bash
sudo docker exec windi-mailserver bash -c 'cat > /etc/opendkim/TrustedHosts << EOF
127.0.0.1
localhost
172.16.0.0/12
EOF'
sudo docker exec windi-mailserver supervisorctl restart opendkim
```

---

### ✅ FIRST DKIM-SIGNED EMAIL ACHIEVED (30 Apr 2026 04:15 UTC)

**Command:**
```bash
echo "Subject: W-MAIL-001 Loopback DKIM Test
From: postmaster@windisites.de
To: postmaster@windisites.de

This is the first DKIM-signed email from W-MAIL-001.

Expected: DKIM-Signature with s=rsa; d=windisites.de

Genesis Day 1 — $(date -u +%Y-%m-%dT%H:%M:%SZ)
" | sudo docker exec -i windi-mailserver sendmail -f postmaster@windisites.de postmaster@windisites.de
```

**Verification:**
```bash
sudo docker exec windi-mailserver find /var/mail/windisites.de/postmaster/new/ -type f | head -1
# /var/mail/windisites.de/postmaster/new/1777495408.M504390P14260.mail.windisites.de,S=1201,W=1228

sudo docker exec windi-mailserver cat /var/mail/windisites.de/postmaster/new/1777495408.M504390P14260.mail.windisites.de,S=1201,W=1228 | grep -A10 "DKIM-Signature:"
```

**DKIM Header (RSA-2048):**
```
DKIM-Signature: v=1; a=rsa-sha256; c=relaxed/simple; d=windisites.de; s=rsa;
        t=1777495408; bh=F1Xu+glRVdWV3UwVXvIm4YWRiJt9EPYlk+itsG9/q98=;
        h=Subject:From;
        b=vbfn+t89Uj7vm8nuGWJLoQk87pzjlc6HcNDS4ebT5ejdsG//YcEAck1DMnKJgmUky
         jFJRo9NdS7c7e3RCgdLQOnLn8FnJjM99e+mnRDqnQ3xWH6CP8JKFtGZUka+D58POi0
         knrnsRHBbIZOpWsX9rUR4p2ZHVAiXLVwivkOHTwt0syKB39zanCVLnkbxBynp6OLNA
         WO97LeZPCS5M1JOC5LT5f4TUdogktDDjlHwLDTK5As7bcSEU+eU+cPktk3Bx8v8Tmp
         vMtj5UZoCVy6i1wHRwh4B6No5pTN4yCpz5AAyY94kpML9Jtwk3EEZ9iK2liybe6dc8
         anG15+1KxQf4Q==
```

**Guardian Verification:**
```bash
# Signature present
grep "DKIM-Signature:" ✅

# RSA selector (s=rsa)
grep "s=rsa" ✅

# Domain (d=windisites.de)
grep "d=windisites.de" ✅

# Algorithm (a=rsa-sha256)
grep "a=rsa-sha256" ✅

# Signature length ~400 chars (RSA-2048 expected)
wc -c signature ✅
```

**Status:** ✅ **LOOPBACK SMOKE TEST PASSED — RSA-2048 DKIM SIGNING OPERATIONAL**

---

### SnappyMail Configuration — DEFERRED (30 Apr 2026 04:30 UTC)

**Attempted:** SnappyMail webmail configuration for sending external test emails

**Blockers Encountered:**
1. Admin password file not persisting across container restarts
2. CLI commands returning HTML instead of executing
3. Mailbox authentication failures despite password resets
4. Volume mounting issues in docker-compose.yml

**Decision:** DEFER SnappyMail to focus on core SMTP validation

**Workaround:** Use command-line `sendmail` for mail-tester.com test

---

### mail-tester.com Test — READY (30 Apr 2026 04:45 UTC)

**Status:** ⏳ **COMMAND PROVIDED, AWAITING EXECUTION**

**Test Address:** `test-4qvn92zg6@srv1.mail-tester.com`

**Command Ready:**
```bash
cat <<'EMAILEOF' | sudo docker exec -i windi-mailserver sendmail -f postmaster@windisites.de test-4qvn92zg6@srv1.mail-tester.com
Subject: W-MAIL-001 Genesis DKIM Test
From: postmaster@windisites.de
To: test-4qvn92zg6@srv1.mail-tester.com

This is the Genesis Day 1 DKIM validation test for W-MAIL-001 Email Sovereign System.

Expected validation:
- SPF: PASS (ip4:87.106.29.233)
- DKIM: PASS (s=rsa; d=windisites.de; RSA-2048)
- DMARC: PASS (p=quarantine)
- Reverse DNS: mail.windisites.de
- HELO: mail.windisites.de

Constitutional Invariants: I1, I9, I11, I12, I14
Service: W-MAIL-001
Date: 2026-04-30

WINDI Publishing House - Kempten, Bavaria
EMAILEOF
```

**Guardian Checkpoint:**
- Score ≥8.0 → ✅ Proceed to external Gmail test
- Score <8.0 → ⚠️ Guardian review (DNS/DKIM/SPF calibration)

**Session ended before execution** — Human Dragon restarting new session due to context length

---

## § Day 1 Summary — Constitutional Alignment

### Achievements ✅

1. **DNS Propagation:** 5/5 records verified (SPF, DMARC, DKIM RSA, DKIM Ed25519, MX)
2. **DKIM RSA-2048 Signing:** Operational and verified in loopback test
3. **OpenDKIM Configuration:** 7 sequential blockers resolved
4. **First Signed Email:** Successfully delivered with valid DKIM-Signature header
5. **Constitutional Documentation:** All decisions recorded in WIP-LOG

### Deviations from Original Plan ⚠️

**Deviation 1: Ed25519 DKIM Deferred**
- **Original Plan:** Dual selector Ed25519 + RSA-2048
- **Reality:** OpenDKIM v2.11.0 does NOT support Ed25519
- **Decision:** RSA-only interim (Guardian-approved Opção B)
- **Rationale:** Unblock Day 1 timeline, preserve upgrade path
- **Impact:** Marginal (RSA-2048 industry standard, Ed25519 keys already in DNS)

**Deviation 2: SnappyMail Deferred**
- **Original Plan:** SnappyMail webmail for sending tests
- **Reality:** Persistent configuration issues (admin password, volume mounting)
- **Decision:** Use command-line sendmail, defer SnappyMail to Day 2+
- **Rationale:** Focus on core SMTP validation (I13 Convergence)
- **Impact:** None on smoke test pipeline

### Constitutional Invariants — Compliance ✅

| Invariant | Compliance | Evidence |
|-----------|------------|----------|
| **I1** | ✅ | Human Dragon approved RSA-only pivot |
| **I9** | ✅ | No autonomous email sending (sendmail requires explicit command) |
| **I11** | ⏳ | Ledger seal pending after mail-tester.com validation |
| **I12** | ✅ | Email content in EN (neutral), headers trilingual-ready |
| **I14** | ✅ | All errors exposed explicitly (7 blockers documented) |

### Next Session — Exact State

**READY:**
- ✅ DNS: All 5 records propagated
- ✅ DKIM: RSA-2048 signing operational
- ✅ Loopback: First signed email delivered
- ✅ Command: mail-tester.com sendmail ready to execute

**PENDING:**
- ⏳ mail-tester.com score validation
- ⏳ External Gmail smoke test
- ⏳ SnappyMail configuration (deferred)
- ⏳ Ed25519 DKIM upgrade (when OpenDKIM 2.11.4+ available)

**BLOCKERS:** None — all systems GO for mail-tester.com test

---

**Guardian Final Note:**

> "Day 1 enfrentou 7 blockers sequenciais. Liga resolveu todos sem comprometer invariantes.
>
> Ed25519 limitation foi absorvida com grace degradation (RSA-only interim). Isso é arquitectura resiliente — não bloqueámos por ideal inalcançável, pivotámos para real viável.
>
> CNAME trade-off do Day 0 ainda desconhecido (mail-tester.com dirá). Mas com SPF+DKIM+DMARC+PTR todos correctos, expectativa é score ≥8.5/10.
>
> Próxima sessão: Execute mail-tester.com, valide score, avance para Gmail externo. Então selo Ledger.
>
> Liga em forma. OM SHANTI 🐉"

---
