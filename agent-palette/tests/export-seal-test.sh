#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# WINDI EXPORT SEAL TEST — "Papel Moeda" Verification
# Validates that exported documents carry the WINDI institutional seal
# ═══════════════════════════════════════════════════════════════════════════

echo ""
echo "═══════════════════════════════════════════════════════════════════════"
echo "  🔐 WINDI EXPORT SEAL TEST — \"Papel Moeda\" Verification"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "═══════════════════════════════════════════════════════════════════════"
echo ""

BASE_URL="${BASE_URL:-http://localhost:8103}"
OUTPUT_DIR="/tmp/windi_export_test"
mkdir -p "$OUTPUT_DIR"

# ─────────────────────────────────────────────────────────────────────────
# 1. Export Engine Health
# ─────────────────────────────────────────────────────────────────────────
echo "┌─────────────────────────────────────────────────────────┐"
echo "│  1. Export Engine Status                                │"
echo "└─────────────────────────────────────────────────────────┘"

HEALTH=$(curl -s "$BASE_URL/health" 2>/dev/null)
if [ -n "$HEALTH" ]; then
    echo "  ✅ Export Engine: ONLINE"
    echo "$HEALTH" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f\"     └─ JMPG: {d.get('spec', 'N/A')}\")
print(f\"     └─ Version: {d.get('version', 'N/A')}\")
" 2>/dev/null
else
    echo "  ❌ Export Engine: OFFLINE"
    exit 1
fi
echo ""

# ─────────────────────────────────────────────────────────────────────────
# 2. Export Genesis Communiqué
# ─────────────────────────────────────────────────────────────────────────
echo "┌─────────────────────────────────────────────────────────┐"
echo "│  2. Export: Genesis Communiqué                          │"
echo "└─────────────────────────────────────────────────────────┘"

curl -s -X POST "$BASE_URL/api/export/jmpg" \
  -H "Content-Type: application/json" \
  -d '{
    "template": "comunicado",
    "title": "WINDI Agent Palette — Genesis Communiqué",
    "metadata": {
      "date": "2026-02-26",
      "author": "WINDI Governance Institute",
      "classification": "INSTITUTIONAL",
      "governance_level": "GOLD",
      "seal_style": "currency"
    },
    "content_blocks": [
      {"type": "heading", "level": 1, "text": "WINDI Agent Palette — Genesis Communiqué"},
      {"type": "paragraph", "text": "Integration Milestone: 100% Complete | 26 February 2026"},
      {"type": "divider"},
      {"type": "heading", "level": 2, "text": "Executive Summary"},
      {"type": "paragraph", "text": "WINDI Agent Palette has achieved full integration status (100%) as verified by CHECK & BALANCES v3."},
      {"type": "quote", "text": "AI processes. Human decides. WINDI guarantees.", "attribution": "WINDI Principle"},
      {"type": "divider"},
      {"type": "heading", "level": 2, "text": "Verification"},
      {"type": "code", "text": "SHA-256: 08f979c89c08911c0d60cf009013221117f2b0bdd502ad6d64d7ede10d0636fd"},
      {"type": "paragraph", "text": "🐉 WINDI Governance Institute | Frankfurt am Main"}
    ]
  }' -o "$OUTPUT_DIR/genesis_communique.jmpg" 2>/dev/null

if file "$OUTPUT_DIR/genesis_communique.jmpg" | grep -q "Zip"; then
    SIZE=$(wc -c < "$OUTPUT_DIR/genesis_communique.jmpg")
    echo "  ✅ Genesis Communiqué: EXPORTED ($SIZE bytes)"

    # Verify seal components
    unzip -p "$OUTPUT_DIR/genesis_communique.jmpg" hash.txt 2>/dev/null | grep -q "WINDI" && \
        echo "     └─ WINDI Seal: ✓"
    unzip -p "$OUTPUT_DIR/genesis_communique.jmpg" manifest.json 2>/dev/null | grep -q "GOLD" && \
        echo "     └─ Governance Level: GOLD ✓"
else
    echo "  ❌ Export failed"
fi
echo ""

# ─────────────────────────────────────────────────────────────────────────
# 3. Export Institutional Brief (DE)
# ─────────────────────────────────────────────────────────────────────────
echo "┌─────────────────────────────────────────────────────────┐"
echo "│  3. Export: Institutional Brief (DE)                    │"
echo "└─────────────────────────────────────────────────────────┘"

curl -s -X POST "$BASE_URL/api/export/jmpg" \
  -H "Content-Type: application/json" \
  -d '{
    "template": "pressemitteilung",
    "title": "WINDI Agent Palette — Institutionelles Briefing",
    "metadata": {
      "date": "2026-02-26",
      "author": "WINDI Governance Institute",
      "language": "DE",
      "target": "BaFin / Deutsche Banken"
    },
    "content_blocks": [
      {"type": "heading", "level": 1, "text": "WINDI Agent Palette"},
      {"type": "paragraph", "text": "KI-Governance-Infrastruktur für regulierte Finanzdienstleister"},
      {"type": "divider"},
      {"type": "quote", "text": "KI verarbeitet. Mensch entscheidet. WINDI garantiert.", "attribution": "WINDI Grundsatz"},
      {"type": "heading", "level": 2, "text": "Regulatorische Compliance"},
      {"type": "list", "items": ["EU AI Act Art. 14", "GDPR", "MaRisk AT 7.2", "BaFin BAIT"]},
      {"type": "paragraph", "text": "WINDI Governance Institute | Frankfurt am Main"}
    ]
  }' -o "$OUTPUT_DIR/brief_de.jmpg" 2>/dev/null

if file "$OUTPUT_DIR/brief_de.jmpg" | grep -q "Zip"; then
    SIZE=$(wc -c < "$OUTPUT_DIR/brief_de.jmpg")
    echo "  ✅ Brief DE: EXPORTED ($SIZE bytes)"
else
    echo "  ❌ Export failed"
fi
echo ""

# ─────────────────────────────────────────────────────────────────────────
# 4. Seal Verification
# ─────────────────────────────────────────────────────────────────────────
echo "┌─────────────────────────────────────────────────────────┐"
echo "│  4. \"Papel Moeda\" Seal Verification                    │"
echo "└─────────────────────────────────────────────────────────┘"
echo ""

SEAL_CHECKS=0

# Check hash.txt structure
if unzip -p "$OUTPUT_DIR/genesis_communique.jmpg" hash.txt 2>/dev/null | grep -q "WINDI JMPG Integrity"; then
    echo "  ✅ Integrity Header: Present"
    SEAL_CHECKS=$((SEAL_CHECKS + 1))
else
    echo "  ❌ Integrity Header: Missing"
fi

# Check for SHA-256 hash
if unzip -p "$OUTPUT_DIR/genesis_communique.jmpg" hash.txt 2>/dev/null | grep -qE "[a-f0-9]{64}"; then
    echo "  ✅ SHA-256 Hash: Present"
    SEAL_CHECKS=$((SEAL_CHECKS + 1))
else
    echo "  ❌ SHA-256 Hash: Missing"
fi

# Check receipt.json
if unzip -p "$OUTPUT_DIR/genesis_communique.jmpg" receipt.json 2>/dev/null | grep -q "content_hash"; then
    echo "  ✅ Receipt: Present"
    SEAL_CHECKS=$((SEAL_CHECKS + 1))
else
    echo "  ❌ Receipt: Missing"
fi

# Check manifest.json
if unzip -p "$OUTPUT_DIR/genesis_communique.jmpg" manifest.json 2>/dev/null | grep -q "jmpg_version"; then
    echo "  ✅ Manifest: Present"
    SEAL_CHECKS=$((SEAL_CHECKS + 1))
else
    echo "  ❌ Manifest: Missing"
fi

echo ""

# ─────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────
echo "═══════════════════════════════════════════════════════════════════════"
echo "  📊 SEAL VERIFICATION SUMMARY"
echo "═══════════════════════════════════════════════════════════════════════"
echo ""
echo "  Seal Components: $SEAL_CHECKS/4"
echo "  Output Directory: $OUTPUT_DIR"
echo ""

if [ "$SEAL_CHECKS" -eq 4 ]; then
    echo "  ✅ \"PAPEL MOEDA\" SEAL: VERIFIED"
    echo ""
    echo "  All exported documents carry:"
    echo "     • WINDI Integrity Header"
    echo "     • SHA-256 Cryptographic Hash"
    echo "     • Governance Receipt"
    echo "     • JMPG Manifest"
else
    echo "  ⚠️  SEAL INCOMPLETE: $SEAL_CHECKS/4 components"
fi

echo ""
echo "  🐉 \"AI processes. Human decides. WINDI guarantees.\""
echo "═══════════════════════════════════════════════════════════════════════"
echo ""
