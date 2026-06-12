#!/bin/bash
# WINDI HIOS - Sync production files to public nginx directory
# Source: /home/windi/hios/cinema/obras/
# Target: /opt/windi/hios/cinema/obras/
#
# Run: bash /home/windi/hios/cinema/scripts/sync-to-public.sh
# Or add to post-commit hook

SOURCE="/home/windi/hios/cinema/obras/w-hios-forensic-unit/production"
TARGET="/opt/windi/hios/cinema/obras/w-hios-forensic-unit/production"

echo "=== WINDI HIOS Sync ==="
echo "Source: $SOURCE"
echo "Target: $TARGET"
echo ""

# Sync only markdown and JSON files (not videos)
rsync -av --include='*.md' --include='*.json' --exclude='*' "$SOURCE/" "$TARGET/"

echo ""
echo "=== Sync complete ==="
echo "Public URL: https://windi-domain.com/hios/cinema/obras/w-hios-forensic-unit/production/"
