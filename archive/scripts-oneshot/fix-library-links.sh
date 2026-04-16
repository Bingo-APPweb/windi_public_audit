#!/bin/bash
# ══════════════════════════════════════════════════════════════
# WINDI Library Link Standardization
# Converts relative .html links to absolute /library/ paths
# ══════════════════════════════════════════════════════════════

DIR="/opt/windi/masterarbeit"
BACKUP_DIR="/opt/windi/masterarbeit/.backup-$(date +%Y%m%d_%H%M%S)"

echo "═══════════════════════════════════════════════════════════"
echo "  WINDI Library Link Standardization"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Create backup
echo "📦 Creating backup at $BACKUP_DIR..."
mkdir -p "$BACKUP_DIR"
cp "$DIR"/*.html "$BACKUP_DIR/"
echo "   ✅ Backed up $(ls "$BACKUP_DIR"/*.html | wc -l) files"
echo ""

# Count before
BEFORE=$(grep -oh 'href="[a-z0-9_-]*\.html"' "$DIR"/*.html 2>/dev/null | wc -l)
echo "📊 Relative links before: $BEFORE"
echo ""

# Fix patterns - convert relative .html to /library/*.html
# BUT exclude:
# - Already absolute (starts with /)
# - External (starts with http)
# - Anchors (starts with #)
# - CSS files
# - Data URIs

echo "🔧 Fixing relative links..."

for file in "$DIR"/*.html; do
    # Replace href="something.html" with href="/library/something.html"
    # Only if it's a simple filename (no path, not already absolute)
    sed -i -E 's/href="([a-zA-Z0-9_-]+\.html)"/href="\/library\/\1"/g' "$file"
done

# Count after
AFTER=$(grep -oh 'href="[a-z0-9_-]*\.html"' "$DIR"/*.html 2>/dev/null | wc -l)
echo "📊 Relative links after: $AFTER"
echo ""

# Also fix CSS reference if relative
echo "🔧 Fixing CSS references..."
sed -i 's/href="windi-internal\.css"/href="\/library\/windi-internal.css"/g' "$DIR"/*.html

# Verify
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  Verification"
echo "═══════════════════════════════════════════════════════════"

# Sample check
echo ""
echo "Sample from index.html nav links:"
grep -o 'href="/library/[^"]*"' "$DIR/index.html" | head -5

echo ""
echo "✅ Done! Fixed $((BEFORE - AFTER)) relative links"
echo "📂 Backup: $BACKUP_DIR"
