#!/bin/bash
# W-MAIL-DACP-MILTER v1.0 — Postfix Wiring + Milter Installation
# Spec: §227 Section 10.1
#
# This script runs during docker-mailserver startup.
# Installs DACP milter dependencies and wires it into Postfix.

echo "[DACP] Starting DACP milter integration..."

# Install dependencies for pymilter
echo "[DACP] Installing system dependencies..."
apt-get update -qq
apt-get install -y -qq libmilter-dev gcc python3-dev python3-pip >/dev/null 2>&1

# Install Python dependencies
echo "[DACP] Installing Python dependencies..."
pip3 install --quiet --break-system-packages pymilter requests

# Check if milter code is available
MILTER_DIR="/tmp/docker-mailserver/dacp-milter"
if [ ! -d "$MILTER_DIR" ]; then
    echo "[DACP] WARNING: Milter code not found at $MILTER_DIR"
    exit 0
fi

# Start the milter in background
echo "[DACP] Starting DACP milter service..."
cd "$MILTER_DIR"
DOMAIN=windisites.de \
# Use public nginx proxy (container can't reach host ports directly)
LEDGER_URL=https://windi-domain.com \
LEDGER_TIMEOUT=10 \
RATE_LIMIT_PER_MIN=100 \
LOG_PATH=/var/log/mail/dacp-milter.log \
LOG_LEVEL=INFO \
MILTER_SOCKET=inet:8890@127.0.0.1 \
HTTP_ADMIN_PORT=8895 \
DKIM_KEYS_PATH=/tmp/docker-mailserver/opendkim/keys \
python3 dacp_milter.py &

# Wait for milter to start
sleep 3

# Verify milter is running
if ss -tlnp | grep -q ':8890'; then
    echo "[DACP] Milter is running on port 8890"
else
    echo "[DACP] WARNING: Milter failed to start"
    exit 0
fi

# Wire milter into Postfix
echo "[DACP] Wiring milter into Postfix chain..."

# DACP milter socket (localhost since running in same container)
DACP_MILTER="inet:127.0.0.1:8890"

# Get current milters
CURRENT_MILTERS=$(postconf -h smtpd_milters)
echo "[DACP] Current milters: $CURRENT_MILTERS"

# Check if DACP already in chain (idempotency)
if echo "$CURRENT_MILTERS" | grep -q '127.0.0.1:8890'; then
    echo "[DACP] Already configured, skipping"
else
    # Prepend DACP milter (MUST be BEFORE DKIM)
    postconf -e "smtpd_milters = $DACP_MILTER $CURRENT_MILTERS"
    postconf -e "non_smtpd_milters = $DACP_MILTER $CURRENT_MILTERS"
    echo "[DACP] Milter chain updated"
fi

# I14 Enforcement: tempfail if milter crashes (never silent bypass)
postconf -e "milter_default_action = tempfail"

# Verify configuration
echo "[DACP] Final smtpd_milters:"
postconf smtpd_milters

echo "[DACP] Integration complete"
