#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# 🐉 WINDI — Fallback: Inject receipt_id safety in generate_pdf
# Only run this if the dict() fix did NOT solve it
# ═══════════════════════════════════════════════════════════════════

echo "🐉 Fallback: Hardening generate_pdf receipt_id handling"
echo "═══════════════════════════════════════════════════════"

# Backup
BK="/opt/windi/backups/fallback_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BK"
cp /opt/windi/communique/communique_publisher.py "$BK/"

# Diagnose: show how receipt_id is used in generate_pdf
echo ""
echo "🔍 Current receipt_id usage in publisher:"
grep -n "receipt_id\|receipt\|Receipt" /opt/windi/communique/communique_publisher.py

echo ""
echo "🔍 Current generate_pdf signature:"
grep -n "def generate_pdf" /opt/windi/communique/communique_publisher.py

echo ""
echo "📋 Full publish_communique function (30 lines after def):"
grep -n -A 50 "def publish_communique" /opt/windi/communique/communique_publisher.py | head -60

echo ""
echo "═══════════════════════════════════════════════"
echo "Paste this output back to Claude for targeted surgery"
