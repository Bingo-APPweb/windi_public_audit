#!/bin/bash
# ============================================================
# WINDI Server Migration - Phase 2: Setup New Server
# ============================================================
# Run as: root on NEW server
# ============================================================

set -e

echo "============================================"
echo "WINDI NEW SERVER SETUP"
echo "Date: $(date)"
echo "============================================"

echo ""
echo "[1/8] System update..."
apt update && apt upgrade -y

echo ""
echo "[2/8] Installing Python 3.11..."
apt install -y python3 python3-pip python3-venv python3-dev

echo ""
echo "[3/8] Installing Node.js 20.x..."
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs

echo ""
echo "[4/8] Installing nginx..."
apt install -y nginx

echo ""
echo "[5/8] Installing certbot..."
apt install -y certbot python3-certbot-nginx

echo ""
echo "[6/8] Installing additional tools..."
apt install -y git curl wget htop ffmpeg sqlite3 jq

echo ""
echo "[7/8] Creating windi user..."
useradd -m -s /bin/bash windi || echo "User windi already exists"
usermod -aG sudo windi

echo ""
echo "[8/8] Creating directories..."
mkdir -p /opt/windi
chown windi:windi /opt/windi

echo ""
echo "============================================"
echo "NEW SERVER SETUP COMPLETE"
echo "============================================"
echo ""
echo "Versions installed:"
echo "  Python: $(python3 --version)"
echo "  Node: $(node --version)"
echo "  npm: $(npm --version)"
echo "  nginx: $(nginx -v 2>&1)"
echo ""
echo "Next step: Run 03-restore-backup.sh"
echo "============================================"
