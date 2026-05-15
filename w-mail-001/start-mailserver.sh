#!/bin/bash
# W-MAIL-001 — Start Mailserver Stack
# Run with: sudo bash /opt/windi/w-mail-001/start-mailserver.sh

set -e

echo "═══════════════════════════════════════════════════════════════"
echo "W-MAIL-001 — Starting Mailserver Stack"
echo "═══════════════════════════════════════════════════════════════"

# Start Docker service
echo "[1/4] Starting Docker service..."
systemctl start docker
systemctl enable docker
echo "✅ Docker service active"

# Pull images
echo ""
echo "[2/4] Pulling Docker images..."
cd /opt/windi/w-mail-001
docker-compose pull

# Start containers
echo ""
echo "[3/4] Starting containers..."
docker-compose up -d

# Wait for services to be healthy
echo ""
echo "[4/4] Waiting for services to start..."
sleep 10

# Verify
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "Container Status:"
echo "═══════════════════════════════════════════════════════════════"
docker-compose ps

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "Port Status:"
echo "═══════════════════════════════════════════════════════════════"
ss -tlnp | grep -E ':(25|587|465|993|8200)\s' || echo "No ports listening yet (containers may still be starting)"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ Mailserver Stack Started"
echo ""
echo "Next Steps:"
echo "  1. Create first mailbox: bash create-mailbox.sh"
echo "  2. Generate DKIM keys: bash generate-dkim.sh"
echo "  3. Configure SnappyMail nginx proxy"
echo "  4. Run smoke tests"
echo "═══════════════════════════════════════════════════════════════"
