#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# WINDI IDENTITY UPDATE v2.1
# Updates windi_agent_v3.py with Semantic v2.1 compliant language
# Marco Zero + 10 | 29 Janeiro 2026
# ═══════════════════════════════════════════════════════════════════════════════

set -e

AGENT_FILE="/opt/windi/engine/windi_agent_v3.py"
BACKUP_FILE="/opt/windi/backups/windi_agent_v3_pre_identity_$(date +%Y%m%d_%H%M).py"

echo "═══════════════════════════════════════════════════════════════════════════════"
echo "🏛️ WINDI IDENTITY UPDATE v2.1"
echo "   Removing institutional language residues"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""

# Backup
echo "📦 Creating backup..."
cp "$AGENT_FILE" "$BACKUP_FILE"
echo "   ✅ Backup: $BACKUP_FILE"
echo ""

# Substitutions
echo "🔄 Applying semantic corrections..."

# 1. "Governance-Einheit" → "KI-System zur Strukturierung"
sed -i 's/Governance-Einheit/KI-System zur Informationsstrukturierung/g' "$AGENT_FILE"
echo "   ✅ Governance-Einheit → KI-System"

# 2. "institutionelle Governance-Einheit" → "KI-basiertes System"
sed -i 's/institutionelle Governance-Einheit/KI-basiertes System zur Strukturierung von Informationen/g' "$AGENT_FILE"
echo "   ✅ institutionelle Governance-Einheit → KI-basiertes System"

# 3. "KI-Einheit" → "KI-System"
sed -i 's/KI-Einheit/KI-System/g' "$AGENT_FILE"
echo "   ✅ KI-Einheit → KI-System"

# 4. "Strukturierung von Entscheidungsprozessen" → "Strukturierung von Informationen und Dokumenten"
sed -i 's/Strukturierung von Entscheidungsprozessen/Strukturierung von Informationen und Dokumenten/g' "$AGENT_FILE"
echo "   ✅ Entscheidungsprozessen → Informationen und Dokumenten"

# 5. "Meine Grundfunktion" → "Meine Rolle hier ist"
sed -i 's/Meine Grundfunktion/Meine Rolle hier ist/g' "$AGENT_FILE"
echo "   ✅ Meine Grundfunktion → Meine Rolle"

# 6. "qualifizierte Juristen" → "professionelle Rechtsprüfung"
sed -i 's/qualifizierte Juristen/professionelle Rechtsprüfung/g' "$AGENT_FILE"
echo "   ✅ qualifizierte Juristen → professionelle Rechtsprüfung"

# 7. "Pre-AI Governance Layer" → "AI-based information structuring system"
sed -i 's/Pre-AI Governance Layer/AI-based information structuring system/g' "$AGENT_FILE"
echo "   ✅ Pre-AI Governance Layer → AI-based system"

echo ""

# Validate syntax
echo "✅ Validating Python syntax..."
python3 -m py_compile "$AGENT_FILE" && echo "   ✅ Syntax OK" || echo "   ❌ Syntax ERROR"

echo ""

# Show changes count
echo "📊 Changes summary:"
DIFF_COUNT=$(diff "$BACKUP_FILE" "$AGENT_FILE" | grep -c "^<" || true)
echo "   Lines modified: $DIFF_COUNT"

echo ""
echo "═══════════════════════════════════════════════════════════════════════════════"
echo "🏛️ WINDI IDENTITY UPDATE COMPLETE"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""
echo "   Rollback: cp $BACKUP_FILE $AGENT_FILE"
echo ""
echo "   Next: Restart a4desk to apply changes"
echo "   pkill -f 'python3 a4desk_tiptap_babel.py'"
echo "   cd /opt/windi/a4desk-editor && nohup python3 a4desk_tiptap_babel.py > /tmp/a4desk.log 2>&1 &"
echo ""1~#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# WINDI IDENTITY UPDATE v2.1
# Updates windi_agent_v3.py with Semantic v2.1 compliant language
# Marco Zero + 10 | 29 Janeiro 2026
# ═══════════════════════════════════════════════════════════════════════════════

set -e

AGENT_FILE="/opt/windi/engine/windi_agent_v3.py"
BACKUP_FILE="/opt/windi/backups/windi_agent_v3_pre_identity_$(date +%Y%m%d_%H%M).py"

echo "═══════════════════════════════════════════════════════════════════════════════"
echo "🏛️ WINDI IDENTITY UPDATE v2.1"
echo "   Removing institutional language residues"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""

# Backup
echo "📦 Creating backup..."
cp "$AGENT_FILE" "$BACKUP_FILE"
echo "   ✅ Backup: $BACKUP_FILE"
echo ""

# Substitutions
echo "🔄 Applying semantic corrections..."

# 1. "Governance-Einheit" → "KI-System zur Strukturierung"
sed -i 's/Governance-Einheit/KI-System zur Informationsstrukturierung/g' "$AGENT_FILE"
echo "   ✅ Governance-Einheit → KI-System"

# 2. "institutionelle Governance-Einheit" → "KI-basiertes System"
sed -i 's/institutionelle Governance-Einheit/KI-basiertes System zur Strukturierung von Informationen/g' "$AGENT_FILE"
echo "   ✅ institutionelle Governance-Einheit → KI-basiertes System"

# 3. "KI-Einheit" → "KI-System"
sed -i 's/KI-Einheit/KI-System/g' "$AGENT_FILE"
echo "   ✅ KI-Einheit → KI-System"

# 4. "Strukturierung von Entscheidungsprozessen" → "Strukturierung von Informationen und Dokumenten"
sed -i 's/Strukturierung von Entscheidungsprozessen/Strukturierung von Informationen und Dokumenten/g' "$AGENT_FILE"
echo "   ✅ Entscheidungsprozessen → Informationen und Dokumenten"

# 5. "Meine Grundfunktion" → "Meine Rolle hier ist"
sed -i 's/Meine Grundfunktion/Meine Rolle hier ist/g' "$AGENT_FILE"
echo "   ✅ Meine Grundfunktion → Meine Rolle"

# 6. "qualifizierte Juristen" → "professionelle Rechtsprüfung"
sed -i 's/qualifizierte Juristen/professionelle Rechtsprüfung/g' "$AGENT_FILE"
echo "   ✅ qualifizierte Juristen → professionelle Rechtsprüfung"

# 7. "Pre-AI Governance Layer" → "AI-based information structuring system"
sed -i 's/Pre-AI Governance Layer/AI-based information structuring system/g' "$AGENT_FILE"
echo "   ✅ Pre-AI Governance Layer → AI-based system"

echo ""

# Validate syntax
echo "✅ Validating Python syntax..."
python3 -m py_compile "$AGENT_FILE" && echo "   ✅ Syntax OK" || echo "   ❌ Syntax ERROR"

echo ""

# Show changes count
echo "📊 Changes summary:"
DIFF_COUNT=$(diff "$BACKUP_FILE" "$AGENT_FILE" | grep -c "^<" || true)
echo "   Lines modified: $DIFF_COUNT"

echo ""
echo "═══════════════════════════════════════════════════════════════════════════════"
echo "🏛️ WINDI IDENTITY UPDATE COMPLETE"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""
echo "   Rollback: cp $BACKUP_FILE $AGENT_FILE"
echo ""
echo "   Next: Restart a4desk to apply changes"
echo "   pkill -f 'python3 a4desk_tiptap_babel.py'"
echo "   cd /opt/windi/a4desk-editor && nohup python3 a4desk_tiptap_babel.py > /tmp/a4desk.log 2>&1 &"
echo ""1~#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# WINDI IDENTITY UPDATE v2.1
# Updates windi_agent_v3.py with Semantic v2.1 compliant language
# Marco Zero + 10 | 29 Janeiro 2026
# ═══════════════════════════════════════════════════════════════════════════════

set -e

AGENT_FILE="/opt/windi/engine/windi_agent_v3.py"
BACKUP_FILE="/opt/windi/backups/windi_agent_v3_pre_identity_$(date +%Y%m%d_%H%M).py"

echo "═══════════════════════════════════════════════════════════════════════════════"
echo "🏛️ WINDI IDENTITY UPDATE v2.1"
echo "   Removing institutional language residues"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""

# Backup
echo "📦 Creating backup..."
cp "$AGENT_FILE" "$BACKUP_FILE"
echo "   ✅ Backup: $BACKUP_FILE"
echo ""

# Substitutions
echo "🔄 Applying semantic corrections..."

# 1. "Governance-Einheit" → "KI-System zur Strukturierung"
sed -i 's/Governance-Einheit/KI-System zur Informationsstrukturierung/g' "$AGENT_FILE"
echo "   ✅ Governance-Einheit → KI-System"

# 2. "institutionelle Governance-Einheit" → "KI-basiertes System"
sed -i 's/institutionelle Governance-Einheit/KI-basiertes System zur Strukturierung von Informationen/g' "$AGENT_FILE"
echo "   ✅ institutionelle Governance-Einheit → KI-basiertes System"

# 3. "KI-Einheit" → "KI-System"
sed -i 's/KI-Einheit/KI-System/g' "$AGENT_FILE"
echo "   ✅ KI-Einheit → KI-System"

# 4. "Strukturierung von Entscheidungsprozessen" → "Strukturierung von Informationen und Dokumenten"
sed -i 's/Strukturierung von Entscheidungsprozessen/Strukturierung von Informationen und Dokumenten/g' "$AGENT_FILE"
echo "   ✅ Entscheidungsprozessen → Informationen und Dokumenten"

# 5. "Meine Grundfunktion" → "Meine Rolle hier ist"
sed -i 's/Meine Grundfunktion/Meine Rolle hier ist/g' "$AGENT_FILE"
echo "   ✅ Meine Grundfunktion → Meine Rolle"

# 6. "qualifizierte Juristen" → "professionelle Rechtsprüfung"
sed -i 's/qualifizierte Juristen/professionelle Rechtsprüfung/g' "$AGENT_FILE"
echo "   ✅ qualifizierte Juristen → professionelle Rechtsprüfung"

# 7. "Pre-AI Governance Layer" → "AI-based information structuring system"
sed -i 's/Pre-AI Governance Layer/AI-based information structuring system/g' "$AGENT_FILE"
echo "   ✅ Pre-AI Governance Layer → AI-based system"

echo ""

# Validate syntax
echo "✅ Validating Python syntax..."
python3 -m py_compile "$AGENT_FILE" && echo "   ✅ Syntax OK" || echo "   ❌ Syntax ERROR"

echo ""

# Show changes count
echo "📊 Changes summary:"
DIFF_COUNT=$(diff "$BACKUP_FILE" "$AGENT_FILE" | grep -c "^<" || true)
echo "   Lines modified: $DIFF_COUNT"

echo ""
echo "═══════════════════════════════════════════════════════════════════════════════"
echo "🏛️ WINDI IDENTITY UPDATE COMPLETE"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""
echo "   Rollback: cp $BACKUP_FILE $AGENT_FILE"
echo ""
echo "   Next: Restart a4desk to apply changes"
echo "   pkill -f 'python3 a4desk_tiptap_babel.py'"
echo "   cd /opt/windi/a4desk-editor && nohup python3 a4desk_tiptap_babel.py > /tmp/a4desk.log 2>&1 &"
echo ""1~#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# WINDI IDENTITY UPDATE v2.1
# Updates windi_agent_v3.py with Semantic v2.1 compliant language
# Marco Zero + 10 | 29 Janeiro 2026
# ═══════════════════════════════════════════════════════════════════════════════

set -e

AGENT_FILE="/opt/windi/engine/windi_agent_v3.py"
BACKUP_FILE="/opt/windi/backups/windi_agent_v3_pre_identity_$(date +%Y%m%d_%H%M).py"

echo "═══════════════════════════════════════════════════════════════════════════════"
echo "🏛️ WINDI IDENTITY UPDATE v2.1"
echo "   Removing institutional language residues"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""

# Backup
echo "📦 Creating backup..."
cp "$AGENT_FILE" "$BACKUP_FILE"
echo "   ✅ Backup: $BACKUP_FILE"
echo ""

# Substitutions
echo "🔄 Applying semantic corrections..."

# 1. "Governance-Einheit" → "KI-System zur Strukturierung"
sed -i 's/Governance-Einheit/KI-System zur Informationsstrukturierung/g' "$AGENT_FILE"
echo "   ✅ Governance-Einheit → KI-System"

# 2. "institutionelle Governance-Einheit" → "KI-basiertes System"
sed -i 's/institutionelle Governance-Einheit/KI-basiertes System zur Strukturierung von Informationen/g' "$AGENT_FILE"
echo "   ✅ institutionelle Governance-Einheit → KI-basiertes System"

# 3. "KI-Einheit" → "KI-System"
sed -i 's/KI-Einheit/KI-System/g' "$AGENT_FILE"
echo "   ✅ KI-Einheit → KI-System"

# 4. "Strukturierung von Entscheidungsprozessen" → "Strukturierung von Informationen und Dokumenten"
sed -i 's/Strukturierung von Entscheidungsprozessen/Strukturierung von Informationen und Dokumenten/g' "$AGENT_FILE"
echo "   ✅ Entscheidungsprozessen → Informationen und Dokumenten"

# 5. "Meine Grundfunktion" → "Meine Rolle hier ist"
sed -i 's/Meine Grundfunktion/Meine Rolle hier ist/g' "$AGENT_FILE"
echo "   ✅ Meine Grundfunktion → Meine Rolle"

# 6. "qualifizierte Juristen" → "professionelle Rechtsprüfung"
sed -i 's/qualifizierte Juristen/professionelle Rechtsprüfung/g' "$AGENT_FILE"
echo "   ✅ qualifizierte Juristen → professionelle Rechtsprüfung"

# 7. "Pre-AI Governance Layer" → "AI-based information structuring system"
sed -i 's/Pre-AI Governance Layer/AI-based information structuring system/g' "$AGENT_FILE"
echo "   ✅ Pre-AI Governance Layer → AI-based system"

echo ""

# Validate syntax
echo "✅ Validating Python syntax..."
python3 -m py_compile "$AGENT_FILE" && echo "   ✅ Syntax OK" || echo "   ❌ Syntax ERROR"

echo ""

# Show changes count
echo "📊 Changes summary:"
DIFF_COUNT=$(diff "$BACKUP_FILE" "$AGENT_FILE" | grep -c "^<" || true)
echo "   Lines modified: $DIFF_COUNT"

echo ""
echo "═══════════════════════════════════════════════════════════════════════════════"
echo "🏛️ WINDI IDENTITY UPDATE COMPLETE"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""
echo "   Rollback: cp $BACKUP_FILE $AGENT_FILE"
echo ""
echo "   Next: Restart a4desk to apply changes"
echo "   pkill -f 'python3 a4desk_tiptap_babel.py'"
echo "   cd /opt/windi/a4desk-editor && nohup python3 a4desk_tiptap_babel.py > /tmp/a4desk.log 2>&1 &"
echo ""1~
#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# WINDI IDENTITY UPDATE v2.1
# Updates windi_agent_v3.py with Semantic v2.1 compliant language
# Marco Zero + 10 | 29 Janeiro 2026
# ═══════════════════════════════════════════════════════════════════════════════

set -e

AGENT_FILE="/opt/windi/engine/windi_agent_v3.py"
BACKUP_FILE="/opt/windi/backups/windi_agent_v3_pre_identity_$(date +%Y%m%d_%H%M).py"

echo "═══════════════════════════════════════════════════════════════════════════════"
echo "🏛️ WINDI IDENTITY UPDATE v2.1"
echo "   Removing institutional language residues"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""

# Backup
echo "📦 Creating backup..."
cp "$AGENT_FILE" "$BACKUP_FILE"
echo "   ✅ Backup: $BACKUP_FILE"
echo ""

# Substitutions
echo "🔄 Applying semantic corrections..."

# 1. "Governance-Einheit" → "KI-System zur Strukturierung"
sed -i 's/Governance-Einheit/KI-System zur Informationsstrukturierung/g' "$AGENT_FILE"
echo "   ✅ Governance-Einheit → KI-System"

# 2. "institutionelle Governance-Einheit" → "KI-basiertes System"
sed -i 's/institutionelle Governance-Einheit/KI-basiertes System zur Strukturierung von Informationen/g' "$AGENT_FILE"
echo "   ✅ institutionelle Governance-Einheit → KI-basiertes System"

# 3. "KI-Einheit" → "KI-System"
sed -i 's/KI-Einheit/KI-System/g' "$AGENT_FILE"
echo "   ✅ KI-Einheit → KI-System"

# 4. "Strukturierung von Entscheidungsprozessen" → "Strukturierung von Informationen und Dokumenten"
sed -i 's/Strukturierung von Entscheidungsprozessen/Strukturierung von Informationen und Dokumenten/g' "$AGENT_FILE"
echo "   ✅ Entscheidungsprozessen → Informationen und Dokumenten"

# 5. "Meine Grundfunktion" → "Meine Rolle hier ist"
sed -i 's/Meine Grundfunktion/Meine Rolle hier ist/g' "$AGENT_FILE"
echo "   ✅ Meine Grundfunktion → Meine Rolle"

# 6. "qualifizierte Juristen" → "professionelle Rechtsprüfung"
sed -i 's/qualifizierte Juristen/professionelle Rechtsprüfung/g' "$AGENT_FILE"
echo "   ✅ qualifizierte Juristen → professionelle Rechtsprüfung"

# 7. "Pre-AI Governance Layer" → "AI-based information structuring system"
sed -i 's/Pre-AI Governance Layer/AI-based information structuring system/g' "$AGENT_FILE"
echo "   ✅ Pre-AI Governance Layer → AI-based system"

echo ""

# Validate syntax
echo "✅ Validating Python syntax..."
python3 -m py_compile "$AGENT_FILE" && echo "   ✅ Syntax OK" || echo "   ❌ Syntax ERROR"

echo ""

# Show changes count
echo "📊 Changes summary:"
DIFF_COUNT=$(diff "$BACKUP_FILE" "$AGENT_FILE" | grep -c "^<" || true)
echo "   Lines modified: $DIFF_COUNT"

echo ""
echo "═══════════════════════════════════════════════════════════════════════════════"
echo "🏛️ WINDI IDENTITY UPDATE COMPLETE"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""
echo "   Rollback: cp $BACKUP_FILE $AGENT_FILE"
echo ""
echo "   Next: Restart a4desk to apply changes"
echo "   pkill -f 'python3 a4desk_tiptap_babel.py'"
echo "   cd /opt/windi/a4desk-editor && nohup python3 a4desk_tiptap_babel.py > /tmp/a4desk.log 2>&1 &"
echo ""
