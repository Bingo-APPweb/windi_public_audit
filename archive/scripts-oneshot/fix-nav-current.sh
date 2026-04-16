#!/bin/bash
# ══════════════════════════════════════════════════════════════
# Fix: Disable current nav link in Library pages
# ══════════════════════════════════════════════════════════════

DIR="/opt/windi/masterarbeit"

echo "═══════════════════════════════════════════════════════════"
echo "  Adding nav-current style to Library pages"
echo "═══════════════════════════════════════════════════════════"

# 1. Add CSS class for current nav item (after .nav-links a:hover)
echo "🎨 Adding CSS for .nav-current..."

for file in "$DIR"/*.html; do
    # Check if already has nav-current
    if grep -q "nav-current" "$file"; then
        echo "   ⏭️  $(basename "$file") - already has nav-current"
        continue
    fi

    # Add CSS after .nav-links a:hover line
    sed -i '/.nav-links a:hover.*{.*color.*gold.*}/a .nav-links a.nav-current { color: var(--dim); pointer-events: none; opacity: 0.5; }' "$file"

    echo "   ✅ $(basename "$file")"
done

# 2. Add JS to detect and mark current page
echo ""
echo "🔧 Adding JS for current page detection..."

for file in "$DIR"/*.html; do
    # Check if already has the nav current logic
    if grep -q "nav-current" "$file" && grep -q "pathname.includes" "$file"; then
        echo "   ⏭️  $(basename "$file") - already has JS"
        continue
    fi

    # Add JS before </script>
    sed -i 's|</script>|// Mark current nav link\nif(location.pathname.includes("/library/")){\n  document.querySelectorAll(".nav-links a").forEach(function(a){\n    if(a.getAttribute("href")==="/library/" || a.getAttribute("href")==="/library/index.html"){\n      a.classList.add("nav-current");\n    }\n  });\n}\n</script>|' "$file"

    echo "   ✅ $(basename "$file")"
done

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  Verification"
echo "═══════════════════════════════════════════════════════════"

# Verify
CSS_COUNT=$(grep -l "nav-current" "$DIR"/*.html | wc -l)
JS_COUNT=$(grep -l 'pathname.includes' "$DIR"/*.html | wc -l)

echo "📊 Files with CSS: $CSS_COUNT/39"
echo "📊 Files with JS: $JS_COUNT/39"
echo ""
echo "✅ Done!"
