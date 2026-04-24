#!/bin/bash
# PREFLIGHT_CHECKLIST.sh — Strato VPS Environment Validation
#
# Version: 1.0
# Status: DRAFT — Awaiting Human Dragon Approval
# Date: 2026-04-24
# Invariants: I9, I11
#
# This script validates the Strato VPS environment before Key Ceremony.
# Output is logged and becomes part of the bootstrap receipt artifacts.
#
# Usage: bash PREFLIGHT_CHECKLIST.sh > preflight_log_$(date +%Y%m%d%H%M%S).txt 2>&1

set -e

echo "=========================================="
echo "WINDI KEY CEREMONY — PREFLIGHT CHECKLIST"
echo "=========================================="
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Host: $(hostname)"
echo "User: $(whoami)"
echo ""

# Track failures
FAILURES=0

check_pass() {
    echo "[✓ PASS] $1"
}

check_fail() {
    echo "[✗ FAIL] $1"
    FAILURES=$((FAILURES + 1))
}

check_warn() {
    echo "[⚠ WARN] $1"
}

# ==========================================
# 1. ENTROPY VALIDATION
# ==========================================
echo "--- 1. ENTROPY VALIDATION ---"

ENTROPY=$(cat /proc/sys/kernel/random/entropy_avail)
echo "Available entropy: $ENTROPY bits"

if [ "$ENTROPY" -ge 256 ]; then
    check_pass "Entropy ≥ 256 bits ($ENTROPY)"
else
    check_fail "Entropy < 256 bits ($ENTROPY) — INSUFFICIENT FOR KEY GENERATION"
fi

# Check /dev/urandom availability
if [ -c /dev/urandom ]; then
    check_pass "/dev/urandom available"
else
    check_fail "/dev/urandom not available"
fi

echo ""

# ==========================================
# 2. CLOCK SYNCHRONIZATION
# ==========================================
echo "--- 2. CLOCK SYNCHRONIZATION ---"

# Check if timedatectl shows synchronized
if command -v timedatectl &> /dev/null; then
    SYNC_STATUS=$(timedatectl show --property=NTPSynchronized --value 2>/dev/null || echo "unknown")
    echo "NTP synchronized: $SYNC_STATUS"

    if [ "$SYNC_STATUS" = "yes" ]; then
        check_pass "System clock synchronized via NTP"
    else
        check_warn "NTP sync status: $SYNC_STATUS — verify manually"
    fi
else
    check_warn "timedatectl not available — verify clock manually"
fi

# Show current time
echo "Current UTC time: $(date -u)"
echo "Current local time: $(date)"

echo ""

# ==========================================
# 3. PYTHON & PYNACL VALIDATION
# ==========================================
echo "--- 3. PYTHON & PYNACL VALIDATION ---"

# Python version
PYTHON_VERSION=$(python3 --version 2>&1)
echo "Python: $PYTHON_VERSION"

if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
    check_pass "Python >= 3.8"
else
    check_fail "Python < 3.8"
fi

# PyNaCl version
PYNACL_VERSION=$(python3 -c "import nacl; print(nacl.__version__)" 2>&1 || echo "NOT INSTALLED")
echo "PyNaCl: $PYNACL_VERSION"

if [ "$PYNACL_VERSION" != "NOT INSTALLED" ]; then
    check_pass "PyNaCl installed ($PYNACL_VERSION)"
else
    check_fail "PyNaCl not installed — run: pip3 install pynacl"
fi

# Cryptography library (for AES-256-GCM)
CRYPTO_VERSION=$(python3 -c "import cryptography; print(cryptography.__version__)" 2>&1 || echo "NOT INSTALLED")
echo "cryptography: $CRYPTO_VERSION"

if [ "$CRYPTO_VERSION" != "NOT INSTALLED" ]; then
    check_pass "cryptography installed ($CRYPTO_VERSION)"
else
    check_fail "cryptography not installed — run: pip3 install cryptography"
fi

# Argon2 library
ARGON2_VERSION=$(python3 -c "import argon2; print(argon2.__version__)" 2>&1 || echo "NOT INSTALLED")
echo "argon2-cffi: $ARGON2_VERSION"

if [ "$ARGON2_VERSION" != "NOT INSTALLED" ]; then
    check_pass "argon2-cffi installed ($ARGON2_VERSION)"
else
    check_fail "argon2-cffi not installed — run: pip3 install argon2-cffi"
fi

echo ""

# ==========================================
# 4. SECRETS DIRECTORY
# ==========================================
echo "--- 4. SECRETS DIRECTORY ---"

SECRETS_DIR="/opt/windi/secrets"

if [ -d "$SECRETS_DIR" ]; then
    check_pass "Secrets directory exists: $SECRETS_DIR"
else
    echo "Creating secrets directory: $SECRETS_DIR"
    mkdir -p "$SECRETS_DIR"
    check_pass "Secrets directory created: $SECRETS_DIR"
fi

# Check permissions
SECRETS_PERMS=$(stat -c "%a" "$SECRETS_DIR" 2>/dev/null || echo "unknown")
echo "Directory permissions: $SECRETS_PERMS"

if [ "$SECRETS_PERMS" = "700" ]; then
    check_pass "Secrets directory permissions: 700"
else
    check_warn "Secrets directory permissions: $SECRETS_PERMS (recommended: 700)"
    echo "  To fix: chmod 700 $SECRETS_DIR"
fi

# Check owner
SECRETS_OWNER=$(stat -c "%U:%G" "$SECRETS_DIR" 2>/dev/null || echo "unknown")
echo "Directory owner: $SECRETS_OWNER"

echo ""

# ==========================================
# 5. DISK SPACE
# ==========================================
echo "--- 5. DISK SPACE ---"

DISK_AVAIL=$(df -h /opt/windi | tail -1 | awk '{print $4}')
echo "Available disk space on /opt/windi: $DISK_AVAIL"

# Check if at least 100MB available
DISK_KB=$(df /opt/windi | tail -1 | awk '{print $4}')
if [ "$DISK_KB" -ge 102400 ]; then
    check_pass "Disk space ≥ 100MB"
else
    check_warn "Disk space < 100MB — consider cleanup"
fi

echo ""

# ==========================================
# 6. NO CONFLICTING PROCESSES
# ==========================================
echo "--- 6. PROCESS ISOLATION ---"

# Check if any process is already using the secrets file
SK_FILE="$SECRETS_DIR/forensic_ledger_sk.enc"
if [ -f "$SK_FILE" ]; then
    check_warn "Encrypted SK file already exists: $SK_FILE"
    echo "  If re-generating, backup and remove first"
else
    check_pass "No existing SK file (clean generation)"
fi

# Check Forensic Ledger service status
if systemctl is-active --quiet windi-ledger 2>/dev/null; then
    check_warn "windi-ledger service is running — consider stopping during ceremony"
else
    check_pass "windi-ledger service not running (or not systemd)"
fi

echo ""

# ==========================================
# 7. NETWORK ISOLATION (INFORMATIONAL)
# ==========================================
echo "--- 7. NETWORK STATUS (INFORMATIONAL) ---"

# Show active connections (informational only)
echo "Active listening ports:"
ss -tlnp 2>/dev/null | head -20 || netstat -tlnp 2>/dev/null | head -20 || echo "Cannot determine"

echo ""
check_warn "Review: Consider network isolation during key generation (optional)"

echo ""

# ==========================================
# 8. TEST CRYPTO OPERATIONS
# ==========================================
echo "--- 8. CRYPTO SMOKE TEST ---"

SMOKE_TEST=$(python3 << 'EOF'
import sys
try:
    from nacl.signing import SigningKey
    from nacl.encoding import Base64Encoder
    import hashlib

    # Generate test key
    sk = SigningKey.generate()
    vk = sk.verify_key

    # Sign and verify
    message = b"WINDI Preflight Test"
    signed = sk.sign(message)
    vk.verify(signed)

    # Encode
    pk_b64 = vk.encode(encoder=Base64Encoder).decode()
    pk_fp = "sha256:" + hashlib.sha256(bytes(vk)).hexdigest()[:16]

    print(f"Test PK: {pk_b64[:20]}...")
    print(f"Test FP: {pk_fp}")
    print("SMOKE_TEST_PASS")
except Exception as e:
    print(f"SMOKE_TEST_FAIL: {e}")
    sys.exit(1)
EOF
)

echo "$SMOKE_TEST"

if echo "$SMOKE_TEST" | grep -q "SMOKE_TEST_PASS"; then
    check_pass "Ed25519 sign/verify smoke test"
else
    check_fail "Ed25519 smoke test failed"
fi

echo ""

# ==========================================
# SUMMARY
# ==========================================
echo "=========================================="
echo "PREFLIGHT SUMMARY"
echo "=========================================="
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

if [ "$FAILURES" -eq 0 ]; then
    echo ""
    echo "[✓] ALL CHECKS PASSED"
    echo ""
    echo "Environment is ready for Key Ceremony."
    echo "Save this log as artifact for bootstrap receipt."
    exit 0
else
    echo ""
    echo "[✗] $FAILURES CHECK(S) FAILED"
    echo ""
    echo "DO NOT PROCEED with Key Ceremony until failures are resolved."
    exit 1
fi
