# W-MAIL-001 Installation Guide
**Service:** Email Sovereign System (windisites.de)
**Date:** 2026-04-29
**Prerequisites:** DNS configured, Docker installed

---

## Pre-Flight Checklist

### DNS Records (verify before installation)
```bash
host -t A windisites.de          # Should return: 87.106.29.233
host -t AAAA windisites.de       # Should return: 2a02:2479:9e:1000::1
host -t MX windisites.de         # Should return: 10 mail.windisites.de
host -t TXT windisites.de        # Should contain SPF + DMARC
host 87.106.29.233               # Should return: mail.windisites.de (PTR)
```

All checks must pass ✅ before proceeding.

---

## Installation Pipeline

### Phase 1: Let's Encrypt Certificate (REQUIRES SUDO)

**Script:** `/opt/windi/w-mail-001/install-cert.sh`

```bash
sudo bash /opt/windi/w-mail-001/install-cert.sh
```

**What it does:**
- Stops nginx temporarily (~30 seconds)
- Requests certificate for mail.windisites.de
- Starts nginx
- Verifies certificate validity

**Expected output:**
```
✅ Certificate obtained successfully
Certificate location:
  Fullchain: /etc/letsencrypt/live/mail.windisites.de/fullchain.pem
  Private:   /etc/letsencrypt/live/mail.windisites.de/privkey.pem
```

**Failure recovery:**
- If port 80 occupied: script handles nginx stop/start
- If domain doesn't resolve: verify DNS propagation first
- If rate limit hit: wait 1 hour (Let's Encrypt limit: 5 failures/hour)

---

### Phase 2: Docker Mailserver Stack

**Directory:** `/opt/windi/w-mail-001/`

```bash
cd /opt/windi/w-mail-001
docker-compose up -d
```

**What it does:**
- Pulls docker-mailserver + SnappyMail images
- Starts Postfix (SMTP), Dovecot (IMAP), rspamd (spam filter)
- Exposes ports: 25, 587, 465, 993
- Mounts Let's Encrypt certificates

**Expected output:**
```
Creating windi-mailserver ... done
Creating windi-snappymail ... done
```

**Verify:**
```bash
docker ps | grep windi-mail
ss -tlnp | grep -E ':(25|587|993)'
```

Should show 2 containers running + 3 ports listening.

---

### Phase 3: First Mailbox Creation

**Script:** `/opt/windi/w-mail-001/create-mailbox.sh`

```bash
cd /opt/windi/w-mail-001
bash create-mailbox.sh
```

**What it does:**
- Generates strong password (stored in `./config/.admin-password`)
- Creates postmaster@windisites.de mailbox
- Lists all mailboxes

**Expected output:**
```
✅ Mailbox created: postmaster@windisites.de

Credentials:
  Email:    postmaster@windisites.de
  Password: (stored in ./config/.admin-password)

IMAP Access:
  Server:   mail.windisites.de
  Port:     993 (SSL/TLS)
```

**Password retrieval:**
```bash
cat /opt/windi/w-mail-001/config/.admin-password
```

---

### Phase 4: DKIM Dual Selector Generation

**Script:** `/opt/windi/w-mail-001/generate-dkim.sh`

```bash
cd /opt/windi/w-mail-001
bash generate-dkim.sh
```

**What it does:**
- Generates RSA-2048 keypair (primary selector: `rsa`)
- Generates Ed25519 keypair (future Phase 2: `ed25519`)
- Outputs DNS TXT record for Strato panel
- Saves instructions to `./config/DKIM-DNS-RECORDS.txt`

**Expected output:**
```
📋 DNS TXT Records — ADD THESE TO STRATO PANEL

Record Name: rsa._domainkey.windisites.de
Record Type: TXT
Record Value: v=DKIM1;k=rsa;p=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...
```

**Action required:**
1. Copy TXT record value from output
2. Go to Strato DNS panel
3. Add TXT record:
   - Name: `rsa._domainkey`
   - Type: TXT
   - Value: (paste full value)
4. Save DNS changes
5. Wait 5-30 min for propagation

**Verify DKIM DNS:**
```bash
host -t TXT rsa._domainkey.windisites.de
```

Should return: `rsa._domainkey.windisites.de descriptive text "v=DKIM1;k=rsa;p=..."`

---

### Phase 5: SnappyMail WebUI (nginx proxy)

**Location:** `/etc/nginx/sites-enabled/windi-domain.com`

**Add this block INSIDE the `server` block:**

```nginx
# W-MAIL-001 — SnappyMail WebUI
location /mail/ {
    proxy_pass http://127.0.0.1:8200/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

**Test + Reload nginx:**
```bash
sudo nginx -t
sudo systemctl reload nginx
```

**Access WebUI:**
- URL: `https://windi-domain.com/mail/`
- Login: `postmaster@windisites.de` + password from `./config/.admin-password`

**First login configuration:**
- IMAP Server: `mail.windisites.de`
- IMAP Port: `993`
- IMAP Security: `SSL/TLS`
- SMTP Server: `mail.windisites.de`
- SMTP Port: `587`
- SMTP Security: `STARTTLS`

---

### Phase 6: Smoke Tests

#### Test 1: Loopback Email (postmaster → postmaster)

**Via SnappyMail:**
1. Login to `https://windi-domain.com/mail/`
2. Compose new email
3. To: `postmaster@windisites.de`
4. Subject: `W-MAIL-001 Loopback Test`
5. Body: `Testing SMTP→IMAP pipeline with DKIM/SPF/DMARC`
6. Send

**Verify:**
- Check Inbox (should arrive within 5 seconds)
- View email source (look for headers)

**Expected headers:**
```
DKIM-Signature: v=1; a=rsa-sha256; c=relaxed/simple; d=windisites.de;
  s=rsa; ...
Authentication-Results: ... dkim=pass
Received-SPF: pass
```

#### Test 2: External Email (postmaster → personal Gmail)

**Send test email to your personal Gmail address:**
- Subject: `W-MAIL-001 External Delivery Test`
- Body: `Testing deliverability to Gmail with full authentication stack`

**Verify:**
1. Check Gmail inbox (not spam)
2. View original message source
3. Look for:
   - `DKIM-Signature: ... d=windisites.de; s=rsa; ...`
   - `SPF: PASS`
   - `DMARC: PASS`

#### Test 3: mail-tester.com Score

**Get unique email address:**
1. Go to: `https://www.mail-tester.com/`
2. Copy generated address (e.g., `test-abc123@mail-tester.com`)

**Send email via SnappyMail:**
- To: (paste mail-tester address)
- Subject: `W-MAIL-001 Reputation Test`
- Body: Plain text message (avoid spam keywords)

**Check score:**
1. Go back to mail-tester.com
2. Click "Then check your score"
3. Wait for analysis

**Expected result:**
- **Target:** ≥ 8.0/10
- **Good:** 8.5-9.0/10 (CNAME trade-off accepted)
- **Excellent:** 9.5+/10 (unlikely with CNAME, but possible)

**If score < 8.0:**
- Check DKIM signature present
- Check SPF alignment
- Check DMARC policy
- Check reverse DNS (PTR)
- Review detailed report for specific issues

---

## PAUSA OBRIGATÓRIA — Guardian Checkpoint

**BEFORE sending first email to real human recipient:**

1. Document mail-tester.com score in WIP-LOG-DAY1
2. Call Guardian with results
3. **IF score < 8.0:** Re-evaluate DNS (Strato ticket or Cloudflare migration)
4. **IF score ≥ 8.0:** Proceed with warm-up plan

**Warm-up plan approved only after Guardian review.**

---

## Troubleshooting

### Ports not listening
```bash
docker logs windi-mailserver
docker exec windi-mailserver ss -tlnp
```

### Certificate not found
```bash
ls -la /etc/letsencrypt/live/mail.windisites.de/
docker exec windi-mailserver ls -la /etc/letsencrypt/live/
```

### DKIM signature missing
```bash
docker exec windi-mailserver cat /tmp/docker-mailserver/opendkim/keys/windisites.de/rsa.txt
docker logs windi-mailserver | grep -i dkim
```

### Email not arriving
```bash
docker logs windi-mailserver | tail -50
docker exec windi-mailserver cat /var/log/mail/mail.log | tail -50
```

---

## File Manifest

```
/opt/windi/w-mail-001/
├── install-cert.sh              # Let's Encrypt (requires sudo)
├── docker-compose.yml           # Mailserver + SnappyMail stack
├── setup.env                    # Configuration variables
├── create-mailbox.sh            # First mailbox creation
├── generate-dkim.sh             # DKIM keypair generation
├── INSTALLATION-GUIDE.md        # This file
├── config/
│   ├── .admin-password          # Generated password (gitignored)
│   ├── DKIM-DNS-RECORDS.txt     # DNS TXT records for Strato
│   └── opendkim/keys/           # DKIM private keys
├── mail-data/                   # Mailbox storage
├── mail-state/                  # Postfix/Dovecot state
└── mail-logs/                   # SMTP/IMAP logs
```

---

## Next Steps After Installation

1. Warm-up schedule (Day 2-14)
2. DID integration (link mailbox → Ed25519 keypair)
3. Ledger seal (first sent email receipt)
4. W-SITES integration (contact forms → windisites.de email)
5. Phase 2: Ed25519 DKIM (when rspamd supports)

---

**Installation prepared by:** CCODE (Architect)
**Reviewed by:** Guardian (approved GO TOTAL after CNAME calibration)
**Human Dragon approval:** Required before Phase 6 → Real emails
