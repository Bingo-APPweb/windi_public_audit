#!/bin/bash
# W-SESSION-001 — Run Sovereign Sessions Migration
# WINDI Publishing House · Kempten, Bavaria · 02 Apr 2026
#
# Usage: bash run-migration.sh
# This will:
#   1. Backup the database
#   2. Apply the sovereign sessions migration
#   3. Optionally enable the feature flag

set -e

cd /opt/windi/windi-travel/identity-gate

DB_FILE="windi_travel_identity.db"
MIGRATION="migrations/001_sovereign_sessions.sql"
BACKUP="windi_travel_identity.db.backup-$(date +%Y%m%d_%H%M%S)"

echo "═══════════════════════════════════════════════════════════"
echo "W-SESSION-001 — Sovereign Sessions Migration"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Check if DB exists
if [ ! -f "$DB_FILE" ]; then
    echo "ERROR: Database $DB_FILE not found!"
    exit 1
fi

# Backup
echo "1. Creating backup..."
cp "$DB_FILE" "$BACKUP"
echo "   Backup created: $BACKUP"

# Apply migration
echo ""
echo "2. Applying migration..."
sqlite3 "$DB_FILE" < "$MIGRATION"
echo "   Migration applied successfully!"

# Verify tables
echo ""
echo "3. Verifying tables..."
sqlite3 "$DB_FILE" "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%session%' OR name LIKE '%device%';"

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "Migration complete!"
echo ""
echo "To enable sovereign sessions, edit .env and set:"
echo "  ENABLE_SOVEREIGN_SESSION=true"
echo ""
echo "Then restart the service:"
echo "  sudo systemctl restart windi-travel-gate"
echo "═══════════════════════════════════════════════════════════"
