#!/bin/bash
# ============================================================
# WINDI Server Migration - Phase 3: Restore Backup
# ============================================================
# Run as: root on NEW server
# Expects: /tmp/windi-migration/ with backup files
# ============================================================

set -e

BACKUP_DIR="/tmp/windi-migration"
LOG_FILE="$BACKUP_DIR/restore.log"

echo "============================================"
echo "WINDI BACKUP RESTORE"
echo "Date: $(date)"
echo "Backup dir: $BACKUP_DIR"
echo "============================================"

exec > >(tee -a "$LOG_FILE") 2>&1

echo ""
echo "[1/7] Verifying checksums..."
echo "--------------------------------------"
cd "$BACKUP_DIR"
sha256sum -c checksums.sha256
echo "All checksums verified ✓"

echo ""
echo "[2/7] Extracting /opt/windi..."
echo "--------------------------------------"
tar -xzvf "$BACKUP_DIR/opt-windi.tar.gz" -C / --strip-components=0
chown -R windi:windi /opt/windi
echo "Done"

echo ""
echo "[3/7] Extracting /home/windi..."
echo "--------------------------------------"
tar -xzvf "$BACKUP_DIR/home-windi.tar.gz" -C / --strip-components=0
chown -R windi:windi /home/windi
echo "Done"

echo ""
echo "[4/7] Restoring nginx configs..."
echo "--------------------------------------"
tar -xzvf "$BACKUP_DIR/nginx-configs.tar.gz" -C / --strip-components=0
# Update server IP in nginx configs if needed
echo "nginx configs restored"
nginx -t && echo "nginx config test: OK"

echo ""
echo "[5/7] Restoring systemd services..."
echo "--------------------------------------"
tar -xzvf "$BACKUP_DIR/systemd-services.tar.gz" -C /tmp
cp /tmp/systemd/windi-*.service /etc/systemd/system/
systemctl daemon-reload
echo "Services restored: $(ls /etc/systemd/system/windi-*.service | wc -l)"

echo ""
echo "[6/7] Restoring SSL certificates..."
echo "--------------------------------------"
tar -xzvf "$BACKUP_DIR/letsencrypt.tar.gz" -C / --strip-components=0 2>/dev/null || echo "Note: May need to regenerate SSL with certbot"
echo "Done"

echo ""
echo "[7/7] Enabling and starting services..."
echo "--------------------------------------"
for service in /etc/systemd/system/windi-*.service; do
    name=$(basename "$service")
    systemctl enable "$name" 2>/dev/null || true
done
echo "Services enabled"

echo ""
echo "============================================"
echo "RESTORE COMPLETE"
echo "============================================"
echo ""
echo "Manual steps needed:"
echo "1. Update DNS to point to this server"
echo "2. Regenerate SSL certs if needed:"
echo "   certbot --nginx -d windi-domain.com -d windilaw.de"
echo "3. Start services:"
echo "   systemctl start windi-*.service"
echo "4. Verify Ledger: curl http://localhost:8101/health"
echo "5. Verify Desktop: curl http://localhost:8119/health"
echo ""
echo "============================================"
