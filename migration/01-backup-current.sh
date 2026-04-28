#!/bin/bash
# ============================================================
# WINDI Server Migration - Phase 1: Backup Current Server
# ============================================================
# Run as: sudo ./01-backup-current.sh
# Location: Run on OLD server (87.106.29.233)
# ============================================================

set -e

BACKUP_DIR="/tmp/windi-migration-$(date +%Y%m%d-%H%M%S)"
LOG_FILE="$BACKUP_DIR/backup.log"

echo "============================================"
echo "WINDI SERVER BACKUP"
echo "Date: $(date)"
echo "Backup dir: $BACKUP_DIR"
echo "============================================"

# Create backup directory
mkdir -p "$BACKUP_DIR"
exec > >(tee -a "$LOG_FILE") 2>&1

echo ""
echo "[1/7] Stopping services gracefully..."
echo "--------------------------------------"
systemctl list-units --type=service --state=running | grep windi | awk '{print $1}' > "$BACKUP_DIR/running-services.txt"
echo "Services to stop: $(wc -l < "$BACKUP_DIR/running-services.txt")"
# NOTE: Uncomment next line when ready to actually stop
# while read service; do systemctl stop "$service"; done < "$BACKUP_DIR/running-services.txt"
echo "[SIMULATED] Services would be stopped"

echo ""
echo "[2/7] Backing up /opt/windi (~7GB)..."
echo "--------------------------------------"
tar -czvf "$BACKUP_DIR/opt-windi.tar.gz" /opt/windi 2>/dev/null || true
echo "Size: $(du -h "$BACKUP_DIR/opt-windi.tar.gz" | cut -f1)"

echo ""
echo "[3/7] Backing up /home/windi..."
echo "--------------------------------------"
tar -czvf "$BACKUP_DIR/home-windi.tar.gz" /home/windi 2>/dev/null || true
echo "Size: $(du -h "$BACKUP_DIR/home-windi.tar.gz" | cut -f1)"

echo ""
echo "[4/7] Backing up nginx configs..."
echo "--------------------------------------"
tar -czvf "$BACKUP_DIR/nginx-configs.tar.gz" \
    /etc/nginx/sites-available/ \
    /etc/nginx/sites-enabled/ \
    /etc/nginx/nginx.conf 2>/dev/null || true
echo "Done"

echo ""
echo "[5/7] Backing up systemd services..."
echo "--------------------------------------"
mkdir -p "$BACKUP_DIR/systemd"
cp /etc/systemd/system/windi-*.service "$BACKUP_DIR/systemd/" 2>/dev/null || true
tar -czvf "$BACKUP_DIR/systemd-services.tar.gz" -C "$BACKUP_DIR" systemd
echo "Services backed up: $(ls "$BACKUP_DIR/systemd/" | wc -l)"

echo ""
echo "[6/7] Backing up SSL certificates..."
echo "--------------------------------------"
tar -czvf "$BACKUP_DIR/letsencrypt.tar.gz" /etc/letsencrypt 2>/dev/null || true
echo "Done"

echo ""
echo "[7/7] Generating checksums..."
echo "--------------------------------------"
cd "$BACKUP_DIR"
sha256sum *.tar.gz > checksums.sha256
cat checksums.sha256

echo ""
echo "============================================"
echo "BACKUP COMPLETE"
echo "============================================"
echo "Location: $BACKUP_DIR"
echo "Total size: $(du -sh "$BACKUP_DIR" | cut -f1)"
echo ""
echo "Files created:"
ls -lh "$BACKUP_DIR"/*.tar.gz
echo ""
echo "Next step: Transfer to new server with:"
echo "  rsync -avz --progress $BACKUP_DIR/ root@NEW_IP:/tmp/windi-migration/"
echo "============================================"
