#!/bin/bash
# W-MAIL-001 — Create First Mailbox (postmaster@windisites.de)
# Run AFTER docker-compose up

set -e
source ./setup.env

echo "═══════════════════════════════════════════════════════════════"
echo "W-MAIL-001 — Creating First Mailbox"
echo "Email: ${ADMIN_EMAIL}"
echo "═══════════════════════════════════════════════════════════════"

# Generate strong password if not exists
if [ ! -f "${ADMIN_PASSWORD_FILE}" ]; then
  echo "[1/3] Generating password..."
  openssl rand -base64 32 > "${ADMIN_PASSWORD_FILE}"
  chmod 600 "${ADMIN_PASSWORD_FILE}"
  echo "✅ Password generated: ${ADMIN_PASSWORD_FILE}"
else
  echo "[1/3] Using existing password from ${ADMIN_PASSWORD_FILE}"
fi

PASSWORD=$(cat "${ADMIN_PASSWORD_FILE}")

# Create mailbox using docker-mailserver CLI
echo "[2/3] Creating mailbox..."
sudo docker exec windi-mailserver setup email add "${ADMIN_EMAIL}" "${PASSWORD}"

if [ $? -eq 0 ]; then
  echo "✅ Mailbox created: ${ADMIN_EMAIL}"
else
  echo "⚠️  Mailbox may already exist or creation failed"
fi

# List all mailboxes
echo "[3/3] Current mailboxes:"
sudo docker exec windi-mailserver setup email list

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ Mailbox Setup Complete"
echo ""
echo "Credentials:"
echo "  Email:    ${ADMIN_EMAIL}"
echo "  Password: (stored in ${ADMIN_PASSWORD_FILE})"
echo ""
echo "IMAP Access:"
echo "  Server:   mail.windisites.de"
echo "  Port:     993 (SSL/TLS)"
echo "  Auth:     ${ADMIN_EMAIL} + password"
echo ""
echo "SnappyMail WebUI:"
echo "  URL:      http://windi-domain.com/mail/"
echo "  Login:    ${ADMIN_EMAIL} + password"
echo "═══════════════════════════════════════════════════════════════"
