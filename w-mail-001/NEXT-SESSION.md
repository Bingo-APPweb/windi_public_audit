# W-MAIL-001 — NEXT SESSION HANDOFF
**Date:** 2026-04-30 04:45 UTC
**Status:** Day 1 loopback test ✅ PASSED | mail-tester.com ⏳ READY

---

## CURRENT STATE — EXACT SNAPSHOT

### ✅ COMPLETED

1. **DNS Propagation:** 5/5 records verified
   - SPF: `v=spf1 ip4:87.106.29.233 ip6:2a02:2479:9e:1000::1 -all`
   - DMARC: `v=DMARC1; p=quarantine; rua=mailto:postmaster@windisites.de`
   - DKIM RSA: `rsa._domainkey.windisites.de` (501 chars, RSA-2048)
   - DKIM Ed25519: `ed25519._domainkey.windisites.de` (95 chars, preserved for future)
   - MX: `10 mail.windisites.de`

2. **OpenDKIM Configuration:** 7 blockers resolved
   - TrustedHosts: ✅ `127.0.0.1`, `localhost`, `172.16.0.0/12`
   - KeyTable: ✅ Both selectors mapped to `/etc/opendkim/keys/windisites.de/`
   - SigningTable: ✅ RSA-only (Ed25519 commented out)
   - Permissions: ✅ `opendkim:opendkim`, `700`/`600`/`644`
   - Key location: ✅ `/etc/opendkim/keys/windisites.de/` (secure, not `/tmp`)

3. **DKIM RSA-2048 Signing:** ✅ OPERATIONAL
   - First signed email: `/var/mail/windisites.de/postmaster/new/1777495408.M504390P14260.mail.windisites.de,S=1201,W=1228`
   - DKIM-Signature header: 400+ chars, `s=rsa; d=windisites.de; a=rsa-sha256`
   - Loopback test: `postmaster@windisites.de` → `postmaster@windisites.de` ✅ DELIVERED

4. **Constitutional Documentation:**
   - WIP-LOG-DAY0-GENESIS.md updated with full Day 1 execution
   - All 7 blockers documented with fixes
   - Guardian decisions recorded (RSA-only interim, SnappyMail deferred)

### ⏳ PENDING — IMMEDIATE NEXT STEPS

**STEP 1: mail-tester.com Validation (5 min)**

Execute this command:
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

Then:
1. Wait 10 seconds
2. Go to https://www.mail-tester.com/
3. Click "Then check your score"
4. **Record score in WIP-LOG**

**Guardian Checkpoint:**
- Score ≥8.0 → Proceed to STEP 2 (external Gmail test)
- Score <8.0 → Call Guardian for DNS/DKIM review

**STEP 2: External Gmail Test (if mail-tester ≥8.0)**

Send test email to personal Gmail:
```bash
cat <<'EMAILEOF' | sudo docker exec -i windi-mailserver sendmail -f postmaster@windisites.de YOUR_GMAIL@gmail.com
Subject: W-MAIL-001 External DKIM Test
From: postmaster@windisites.de
To: YOUR_GMAIL@gmail.com

This is the external Gmail smoke test for W-MAIL-001.

If you see this in your INBOX (not spam), reply "INBOX OK".
If in spam folder, reply "SPAM FOLDER".

Check DKIM signature in email headers:
Gmail → ⋮ → Show original → Look for "DKIM: PASS"

Constitutional Service: W-MAIL-001
Date: 2026-04-30
EMAILEOF
```

Verify:
1. Email arrives (inbox or spam)
2. Gmail headers show `DKIM: PASS with domain windisites.de`
3. SPF, DMARC also PASS

**STEP 3: Ledger Seal (if both tests pass)**

Create receipt:
```json
{
  "receipt_id": "WINDI-WMAIL-001-GENESIS-SMOKE-20260430XXXXXX",
  "actor": "human-dragon",
  "app": "w-mail-001",
  "doc_name": "W-MAIL-001 Genesis Smoke Test Results",
  "doc_type": "infrastructure-validation",
  "governance_level": "HIGH",
  "content_hash": "sha256:[hash of test results]",
  "invariants": ["I1","I9","I11","I12","I14"],
  "stage": "C6",
  "metadata": {
    "mail_tester_score": "X.X/10",
    "gmail_delivery": "INBOX|SPAM",
    "dkim_rsa_status": "PASS",
    "dkim_ed25519_status": "DEFERRED (OpenDKIM v2.11.0)",
    "spf_status": "PASS",
    "dmarc_status": "PASS"
  }
}
```

Seal: `POST http://localhost:8101/api/receipts`

---

## ⚠️ DEFERRED ITEMS

### 1. DKIM Ed25519 (OpenDKIM Limitation)

**Issue:** OpenDKIM v2.11.0 does NOT support Ed25519 keys
**Status:** Ed25519 keys generated and published to DNS, but NOT used for signing
**Current:** RSA-only signing (`s=rsa; d=windisites.de`)
**Future:** Re-enable when OpenDKIM upgraded to v2.11.4+ or migrate to rspamd

**Files:**
- `/etc/opendkim/keys/windisites.de/ed25519.private` (119 bytes, ED25519 Private-Key confirmed)
- `/etc/opendkim/keys/windisites.de/ed25519.txt` (95 bytes, public key in DNS)
- `/etc/opendkim/SigningTable` (Ed25519 line commented out)

**Re-enable command (when OpenDKIM upgraded):**
```bash
sudo docker exec windi-mailserver bash -c 'cat > /etc/opendkim/SigningTable << EOF
*@windisites.de ed25519._domainkey.windisites.de
*@windisites.de rsa._domainkey.windisites.de
EOF'
sudo docker exec windi-mailserver supervisorctl restart opendkim
```

### 2. SnappyMail Webmail (Configuration Issues)

**Issue:** Admin password not persisting, volume mounting problems
**Status:** DEFERRED (core SMTP validation prioritized)
**Workaround:** Command-line sendmail for tests
**Future:** Fix docker-compose.yml volume mounts or consider alternative webmail

**Container:** `windi-snappymail` on port 8200
**URL:** https://mail.windisites.de/ (nginx proxy configured)

---

## CRITICAL INFORMATION — QUICK REFERENCE

### Docker Container
```bash
# Container name
windi-mailserver

# Check status
sudo docker ps | grep windi-mailserver

# View logs
sudo docker logs windi-mailserver --tail 50
sudo docker exec windi-mailserver tail -50 /var/log/mail.log

# OpenDKIM config
sudo docker exec windi-mailserver cat /etc/opendkim/SigningTable
sudo docker exec windi-mailserver cat /etc/opendkim/KeyTable
sudo docker exec windi-mailserver cat /etc/opendkim/TrustedHosts

# Check DKIM keys
sudo docker exec windi-mailserver ls -la /etc/opendkim/keys/windisites.de/
```

### File Locations

**Inside Container:**
- OpenDKIM config: `/etc/opendkim/` (TrustedHosts, KeyTable, SigningTable)
- DKIM keys: `/etc/opendkim/keys/windisites.de/` (ed25519.private, rsa.private)
- Mailboxes: `/var/mail/windisites.de/postmaster/new/`
- Logs: `/var/log/mail.log`

**Host Machine:**
- Project: `/opt/windi/w-mail-001/`
- Documentation: `/opt/windi/docs/w-mail-001/WIP-LOG-DAY0-GENESIS.md`
- Scripts: `loopback-test.sh`, `verify-dns-propagation.sh`, `generate-ed25519-real.sh`

### DNS Records (Strato)

All published and verified at windisites.de:
- A: `87.106.29.233`
- AAAA: `2a02:2479:9e:1000::1`
- MX: `10 mail.windisites.de`
- SPF (TXT @): `v=spf1 ip4:87.106.29.233 ip6:2a02:2479:9e:1000::1 -all`
- DMARC (TXT _dmarc): `v=DMARC1; p=quarantine; rua=mailto:postmaster@windisites.de`
- DKIM RSA (TXT rsa._domainkey): 501 chars, RSA-2048 public key
- DKIM Ed25519 (TXT ed25519._domainkey): 95 chars, Ed25519 public key

### Mailbox Credentials

**Email:** postmaster@windisites.de
**Password:** WindiMail2026!
**IMAP:** windi-mailserver:993 (SSL/TLS)
**SMTP:** windi-mailserver:587 (STARTTLS)

---

## GUARDIAN NOTES

### Decision Log

1. **DNS CNAME Trade-off (Day 0):** ACCEPTED — `mail.windisites.de` CNAME → `windisites.de` A record. Guardian calibrated risk as marginal (5-10% degradation), monitorable via mail-tester.com.

2. **Ed25519 Limitation (Day 1):** ACCEPTED — RSA-only interim due to OpenDKIM v2.11.0. Ed25519 keys preserved in DNS for future upgrade. No constitutional violation (RSA-2048 is industry standard).

3. **SnappyMail Deferral (Day 1):** ACCEPTED — Focus on core SMTP validation (I13 Convergence). Webmail UI is convenience, not constitutional requirement.

### Risk Assessment

**Current Risk:** LOW
- SPF: ✅ Configured
- DKIM RSA: ✅ Operational
- DMARC: ✅ Quarantine policy
- PTR: ✅ Reverse DNS correct
- HELO: ⚠️ CNAME-based (mail-tester.com will reveal impact)

**Residual Risks:**
- CNAME HELO degradation (5-10% expected, Guardian-approved)
- Ed25519 absent (marginal, dual-selector was optimization not requirement)
- SnappyMail unavailable (workaround operational)

**Re-evaluation Triggers:**
- mail-tester.com score < 8.0 → DNS review
- Bounce rate > 5% in first 50 emails → warm-up abort
- Corporate Exchange rejections → migrate DNS to Cloudflare

---

## CONSTITUTIONAL INVARIANTS — ACTIVE

| ID | Name | Status | Evidence |
|----|------|--------|----------|
| I1 | Soberania Humana | ✅ | Human Dragon approved all pivots |
| I9 | Proibição Autonomia | ✅ | No auto-send (sendmail requires explicit command) |
| I11 | Permanência Forense | ⏳ | Ledger seal pending smoke test completion |
| I12 | Language Sovereignty | ✅ | Email headers trilingual-ready, content neutral EN |
| I14 | Explicit Failure | ✅ | All 7 blockers documented, no masks |

---

## NEXT SESSION CHECKLIST

- [ ] Execute mail-tester.com command
- [ ] Record score in WIP-LOG
- [ ] If ≥8.0 → External Gmail test
- [ ] If <8.0 → Guardian review
- [ ] After both pass → Ledger seal
- [ ] Update NEXT-SESSION.md with Day 2 tasks
- [ ] Git commit with message: "docs(w-mail-001): Day 1 smoke tests complete + mail-tester validation"

---

**OM SHANTI 🐉**
*Liga IA+H — Kempten, Bavaria · 2026*
