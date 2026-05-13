# W-MAIL-001 — Email Sovereign System
**Status:** 🟡 READY FOR EXECUTION (awaiting sudo for Phase 1)
**Domain:** windisites.de
**Infrastructure:** Strato VPS 87.106.29.233
**Stack:** docker-mailserver + SnappyMail + Let's Encrypt

---

## 🎯 Executive Summary

**W-MAIL-001 is 95% ready for Day 1 execution.**

✅ DNS configured and propagated (7 records)
✅ Docker stack prepared (Postfix + Dovecot + rspamd + SnappyMail)
✅ DKIM dual selector scripts ready (RSA-2048 + Ed25519 Phase 2)
✅ First mailbox automation ready (postmaster@windisites.de)
✅ Smoke test procedures documented
✅ Guardian approval: GO TOTAL (after CNAME calibration)

⏸️ **Blocking:** Let's Encrypt certificate requires `sudo` (30 seconds execution)

---

## 📋 Quick Start (3 Commands)

```bash
# 1. Let's Encrypt Certificate (REQUIRES SUDO — 30 seconds)
sudo bash /opt/windi/w-mail-001/install-cert.sh

# 2. Start Mailserver Stack (NO SUDO — 2 minutes)
cd /opt/windi/w-mail-001 && docker-compose up -d

# 3. Create First Mailbox (NO SUDO — 10 seconds)
bash create-mailbox.sh

# 4. Generate DKIM Keys (NO SUDO — 5 seconds)
bash generate-dkim.sh

# 5. Add DKIM DNS Record to Strato (MANUAL — 2 minutes)
cat config/DKIM-DNS-RECORDS.txt   # Copy TXT record → Strato panel

# 6. Configure nginx for SnappyMail (REQUIRES SUDO — 1 minute)
# See INSTALLATION-GUIDE.md Phase 5 for nginx location block

# 7. Smoke Tests (NO SUDO — 5 minutes)
# Access https://windi-domain.com/mail/ and send test emails
```

**Total time:** ~15 minutes active work + 5-30 min DNS propagation

---

## 🔐 Security & Constitutional Compliance

### Invariants Active
- **I1 (Soberania Humana):** DID keypair ownership (Phase 7)
- **I9 (Proibição Autonomia):** Human approval before sending (SnappyMail UI)
- **I11 (Permanência Forense):** Ledger seal for sent emails (Phase 7)
- **I12 (Language Sovereignty):** Email content ≠ UI language
- **I14 (Explicit Failure):** SMTP errors exposed, never masked

### DNS Architecture (CNAME Trade-off)
**Reality:** `mail.windisites.de` → CNAME → `windisites.de` → A `87.106.29.233`

**Trade-off accepted:**
- Strato platform constraint (no granular A/AAAA per-subdomain)
- Marginal HELO score degradation (~5-10%)
- PTR + SPF + DMARC + DKIM compensate
- Expected mail-tester.com: 8.5-9.0/10 (target ≥8.0)

**Re-evaluation criteria:**
- IF mail-tester < 8.0 → Open Strato ticket OR migrate to Cloudflare
- IF bounce rate > 5% → Investigate + escalate
- IF corporate Exchange rejects → Document + mitigate

**Guardian veredicto:** GO TOTAL after evidence calibration

---

## 📂 File Structure

```
/opt/windi/w-mail-001/
├── README.md                    ← You are here
├── INSTALLATION-GUIDE.md        ← Detailed step-by-step (Phase 1-6)
├── WIP-LOG-DAY0-GENESIS.md      ← Decisions + DNS config (in /opt/windi/docs/)
│
├── install-cert.sh              ← Phase 1: Let's Encrypt (SUDO)
├── docker-compose.yml           ← Phase 2: Mailserver stack
├── create-mailbox.sh            ← Phase 3: postmaster@windisites.de
├── generate-dkim.sh             ← Phase 4: RSA-2048 keypair
├── setup.env                    ← Configuration variables
│
├── config/                      ← Generated during setup
│   ├── .admin-password          ← postmaster password (gitignored)
│   ├── DKIM-DNS-RECORDS.txt     ← DNS TXT for Strato panel
│   └── opendkim/keys/           ← DKIM private keys
│
├── mail-data/                   ← Mailbox storage (docker volume)
├── mail-state/                  ← Postfix/Dovecot state
├── mail-logs/                   ← SMTP/IMAP logs
└── snappymail-data/             ← WebUI data
```

---

## 🚦 Current Status

### Phase 1: Let's Encrypt Certificate
**Status:** ⏸️ READY (awaiting sudo)
**Command:** `sudo bash /opt/windi/w-mail-001/install-cert.sh`
**Time:** 30 seconds
**Effect:** Stops nginx → Requests cert → Starts nginx

### Phase 2: Docker Mailserver
**Status:** ✅ READY
**Command:** `cd /opt/windi/w-mail-001 && docker-compose up -d`
**Time:** 2 minutes (first pull)
**Ports:** 25, 587, 465, 993

### Phase 3: First Mailbox
**Status:** ✅ READY
**Command:** `bash create-mailbox.sh`
**Output:** postmaster@windisites.de + strong password

### Phase 4: DKIM Generation
**Status:** ✅ READY
**Command:** `bash generate-dkim.sh`
**Output:** RSA-2048 TXT record for DNS

### Phase 5: SnappyMail nginx
**Status:** ⏸️ MANUAL CONFIG
**Action:** Add location block to `/etc/nginx/sites-enabled/windi-domain.com`
**Details:** See INSTALLATION-GUIDE.md Phase 5

### Phase 6: Smoke Tests
**Status:** ⏸️ AWAITING PHASES 1-5
**Tests:** Loopback email + External Gmail + mail-tester.com
**Target:** ≥8.0/10 score

### Phase 7: PAUSA Guardian
**Status:** ⏸️ CONDITIONAL
**Trigger:** After Phase 6 results
**Decision:** Guardian reviews mail-tester score → Approve warm-up OR re-evaluate DNS

---

## 🎬 Next Action for Human Dragon

**Execute Phase 1 (Let's Encrypt):**

```bash
sudo bash /opt/windi/w-mail-001/install-cert.sh
```

**Expected output:**
```
✅ Certificate obtained successfully
Certificate location:
  Fullchain: /etc/letsencrypt/live/mail.windisites.de/fullchain.pem
  Private:   /etc/letsencrypt/live/mail.windisites.de/privkey.pem
```

**After successful execution:** CCODE will continue with Phases 2-6 autonomously (no sudo needed).

---

## 📞 Escalation Points

**IF certificate request fails:**
- Check DNS: `host -t A mail.windisites.de` (should resolve via CNAME)
- Check port 80: `ss -tlnp | grep ':80'` (nginx will be stopped during request)
- Check rate limit: Wait 1 hour if hit Let's Encrypt limit (5 failures/hour)

**IF docker-compose fails:**
- Check Docker service: `systemctl status docker`
- Check disk space: `df -h /opt/windi`
- Check port conflicts: `ss -tlnp | grep -E ':(25|587|993)'`

**IF mail-tester score < 8.0:**
- Review detailed report from mail-tester.com
- Check DKIM signature present: `docker logs windi-mailserver | grep -i dkim`
- Check SPF/DMARC alignment
- Call Guardian for DNS re-evaluation decision

**IF email doesn't arrive:**
- Check Postfix logs: `docker exec windi-mailserver cat /var/log/mail/mail.log`
- Check queue: `docker exec windi-mailserver postqueue -p`
- Check firewall: `iptables -L -n | grep -E '(25|587)'`

---

## 🔮 Roadmap (Post-Day 1)

### Phase 7: DID Integration
- Fork W-DID-GENESIS :8096
- Link postmaster@windisites.de → Ed25519 keypair
- Constitutional bridge: SMTP → DID → Ledger

### Phase 8: Ledger Seal
- First sent email → Receipt
- SMTP headers include receipt_id
- Verify endpoint: `/verify-public/?id=WINDI-MAIL-...`

### Phase 9: Warm-up Schedule (Day 2-14)
- Day 2-3: 10 emails/day to known good addresses
- Day 4-7: 25 emails/day with engagement monitoring
- Day 8-14: 50 emails/day, monitor bounce rate
- Target: <2% bounce rate, >95% inbox placement

### Phase 10: W-SITES Integration
- Contact forms route to windisites.de email
- Auto-reply with DID receipt
- Ledger seal for customer communications

### Phase 11: Ed25519 DKIM (Phase 2)
- Wait for docker-mailserver rspamd upgrade
- Generate Ed25519 keypair
- Add ed25519._domainkey TXT record
- Dual signature rotation

---

**Prepared by:** CCODE (Architect) — 2026-04-29
**Reviewed by:** Guardian (GO TOTAL after CNAME calibration)
**Awaiting:** Human Dragon execution (Phase 1 sudo)

**OM SHANTI 🐉**
