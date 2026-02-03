#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# WINDI Masterarbeit — Deploy Verification Layer Chapter
# Phase 3A Documentation
# "AI processes. Human decides. WINDI guarantees."
# ═══════════════════════════════════════════════════════════════════════════════

set -e

SITE_ROOT="/opt/windi/masterarbeit"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  WINDI Masterarbeit — Deploy Verification Layer Chapter"
echo "  $(date '+%Y-%m-%d %H:%M:%S UTC')"
echo "════════════════════════════════════════════════════════════════"
echo ""

# 1. Backup current index.html
echo "[1/5] Creating backup..."
if [ -f "$SITE_ROOT/index.html" ]; then
    cp "$SITE_ROOT/index.html" "$SITE_ROOT/index.html.bak.$TIMESTAMP"
    echo "      Backup: index.html.bak.$TIMESTAMP"
fi

# 2. Copy verification-layer.html to site
echo "[2/5] Copying verification-layer.html..."
cp verification-layer.html "$SITE_ROOT/verification-layer.html"
echo "      Deployed: $SITE_ROOT/verification-layer.html"

# 3. Add link to navigation in index.html
echo "[3/5] Updating navigation in index.html..."

# Check if link already exists
if grep -q "verification-layer.html" "$SITE_ROOT/index.html"; then
    echo "      Link already exists in navigation. Skipping."
else
    # Add link after IDPF Abstract link in navigation
    sed -i 's|<a href="idpf-abstract.html">📑 IDPF: Research Abstract ↗</a>|<a href="idpf-abstract.html">📑 IDPF: Research Abstract ↗</a>\n            <a href="verification-layer.html">🌐 Kapitel 11: Verification Layer ↗</a>|' "$SITE_ROOT/index.html"
    
    # Also add to the chapter list in the main content if it exists
    if grep -q "Related Documents" "$SITE_ROOT/index.html"; then
        sed -i 's|</ul><!-- END CHAPTERS -->|<li><a href="verification-layer.html">Kapitel 11: Public Verification Layer</a> — Phase 3A Implementation</li>\n</ul><!-- END CHAPTERS -->|' "$SITE_ROOT/index.html" 2>/dev/null || true
    fi
    
    echo "      Navigation updated."
fi

# 4. Create update script for index navigation (manual fallback)
echo "[4/5] Creating manual update script..."
cat > "$SITE_ROOT/add_verification_link.py" << 'PYTHON'
#!/usr/bin/env python3
"""
WINDI Masterarbeit — Add Verification Layer Link
Run: python3 add_verification_link.py
"""
import re
from pathlib import Path
from datetime import datetime

INDEX = Path("/opt/windi/masterarbeit/index.html")

if not INDEX.exists():
    print("[ERROR] index.html not found!")
    exit(1)

html = INDEX.read_text(encoding="utf-8")

# Check if already added
if "verification-layer.html" in html:
    print("[INFO] Verification Layer link already exists.")
    exit(0)

# Find navigation section and add link
# Pattern: look for the last navigation link before closing nav
nav_patterns = [
    (r'(<a href="idpf-abstract.html"[^>]*>[^<]*</a>)', 
     r'\1\n            <a href="verification-layer.html">🌐 Kapitel 11: Verification Layer</a>'),
    (r'(</nav>)',
     r'<a href="verification-layer.html">🌐 Verification Layer</a>\n    \1')
]

for pattern, replacement in nav_patterns:
    if re.search(pattern, html):
        html = re.sub(pattern, replacement, html, count=1)
        INDEX.write_text(html, encoding="utf-8")
        print(f"[OK] Added Verification Layer link to navigation")
        print(f"[OK] Updated: {INDEX}")
        exit(0)

print("[WARNING] Could not find navigation insertion point. Manual edit required.")
PYTHON
chmod +x "$SITE_ROOT/add_verification_link.py"
echo "      Created: add_verification_link.py"

# 5. Verify deployment
echo "[5/5] Verifying deployment..."
if [ -f "$SITE_ROOT/verification-layer.html" ]; then
    SIZE=$(stat -c%s "$SITE_ROOT/verification-layer.html" 2>/dev/null || stat -f%z "$SITE_ROOT/verification-layer.html")
    echo "      ✅ verification-layer.html deployed ($SIZE bytes)"
else
    echo "      ❌ Deployment failed!"
    exit 1
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  ✅ DEPLOYMENT COMPLETE"
echo ""
echo "  Page URL: http://master.windia4desk.tech/verification-layer.html"
echo ""
echo "  If navigation link not added automatically, run:"
echo "    python3 $SITE_ROOT/add_verification_link.py"
echo ""
echo "  Or manually add to index.html navigation:"
echo '    <a href="verification-layer.html">🌐 Kapitel 11: Verification Layer</a>'
echo ""
echo "════════════════════════════════════════════════════════════════"
