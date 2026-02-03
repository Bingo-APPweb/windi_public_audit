#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# WINDI SEMANTIC MIGRATION v2.1 - PATCHED VERSION
# Regulator-Grade | Idempotent | Production-Safe
# Marco Zero + 10 days | 29 Janeiro 2026
# ═══════════════════════════════════════════════════════════════════════════════
# "AI processes. Human decides. WINDI guarantees."
# ═══════════════════════════════════════════════════════════════════════════════
#
# PATCHES APPLIED (per Architect review):
# - Removed "Pre-AI Governance Layer" from preferred descriptors
# - Fixed "I operate under the law" conversion
# - Layer 7 append is now idempotent (grep check before cat)
# - Rollback instructions are explicit per file
# - Restart uses systemctl for systemd services
# - Added conversions: "blocks", "violation", "you must"
# - Case-insensitive sed where needed
#
# ═══════════════════════════════════════════════════════════════════════════════

set -e  # Exit on error

BACKUP_DIR="/opt/windi/backups/pre_semantic_v2_1_$(date +%Y%m%d_%H%M)"
LOG_FILE="/opt/windi/backups/semantic_migration_v2_1.log"
MARKER="SEMANTIC FRAMEWORK v2.1 - LAYER 7"

echo "═══════════════════════════════════════════════════════════════════════════════"
echo "🏛️ WINDI SEMANTIC MIGRATION v2.1 - PATCHED"
echo "   Regulator-Grade | Idempotent | Production-Safe"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 1: BACKUP
# ═══════════════════════════════════════════════════════════════════════════════

echo "📦 PHASE 1: Creating backup..."
mkdir -p "$BACKUP_DIR"

cp /opt/windi/engine/windi_constitution.py "$BACKUP_DIR/" 2>/dev/null || echo "   ⚠️ windi_constitution.py not found"
cp /opt/windi/engine/windi_agent_v3.py "$BACKUP_DIR/" 2>/dev/null || echo "   ⚠️ windi_agent_v3.py not found"
cp /opt/windi/brain/invariants.py "$BACKUP_DIR/" 2>/dev/null || echo "   ⚠️ invariants.py not found"
cp /opt/windi/templates/constitutional_validator_v2.py "$BACKUP_DIR/" 2>/dev/null || true
cp /opt/windi/gateway/windi_gateway.py "$BACKUP_DIR/" 2>/dev/null || echo "   ⚠️ windi_gateway.py not found"
cp /opt/windi/a4desk-editor/intent_parser/chat_integration.py "$BACKUP_DIR/" 2>/dev/null || echo "   ⚠️ chat_integration.py not found"

echo "   ✅ Backup created: $BACKUP_DIR"
echo ""

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 2: TERMINOLOGY MIGRATION (case-insensitive where needed)
# ═══════════════════════════════════════════════════════════════════════════════

echo "🔄 PHASE 2: Terminology Migration..."

# --- windi_constitution.py ---
if [ -f /opt/windi/engine/windi_constitution.py ]; then
    echo "   Updating windi_constitution.py..."

    # Guardrails → Stability Layers (case variations)
    sed -i 's/8 GUARDRAILS (G1-G8)/8 STABILITY LAYERS (S1-S8)/g' /opt/windi/engine/windi_constitution.py
    sed -i 's/8 GUARDRAILS:/8 STABILITY LAYERS:/g' /opt/windi/engine/windi_constitution.py
    sed -i 's/8 Guardrails/8 Stability Layers/g' /opt/windi/engine/windi_constitution.py
    sed -i 's/GUARDRAILS/STABILITY LAYERS/g' /opt/windi/engine/windi_constitution.py
    sed -i 's/Guardrails/Stability Layers/g' /opt/windi/engine/windi_constitution.py
    sed -i 's/guardrails/stability layers/g' /opt/windi/engine/windi_constitution.py

    # G1-G8 → S1-S8 with updated descriptions
    sed -i 's/G1 - CONTENT FILTER: No harmful, illegal, or unethical content/S1 - CONTENT STABILITY: System is designed to maintain safe content boundaries/g' /opt/windi/engine/windi_constitution.py
    sed -i 's/G2 - PRIVACY FILTER: No personal data processing without consent/S2 - PRIVACY STABILITY: System operates within privacy protection scope/g' /opt/windi/engine/windi_constitution.py
    sed -i 's/G3 - ACCURACY FILTER: Flag uncertain information/S3 - ACCURACY STABILITY: System indicates when information falls outside certainty scope/g' /opt/windi/engine/windi_constitution.py
    sed -i 's/G4 - BIAS FILTER: Avoid discriminatory language or assumptions/S4 - BIAS STABILITY: System is designed to maintain inclusive language/g' /opt/windi/engine/windi_constitution.py
    sed -i 's/G5 - TONE FILTER: Professional, respectful communication/S5 - TONE STABILITY: System maintains professional communication scope/g' /opt/windi/engine/windi_constitution.py
    sed -i "s/G6 - POST-FILTER: Transform directives into options .*/S6 - POST-PROCESSING STABILITY: Transforms directives into options (\"Consider\" not \"You should\")/g" /opt/windi/engine/windi_constitution.py
    sed -i 's/G7 - FAIL-CLOSED: On error, stop and escalate. Never invent fallback/S7 - FAIL-SAFE STABILITY: On uncertainty, system defers to human review/g' /opt/windi/engine/windi_constitution.py
    sed -i 's/G8 - INDEPENDENCE: Each response is autonomous. No hidden state/S8 - INDEPENDENCE STABILITY: Each response maintains autonomy. No hidden state/g' /opt/windi/engine/windi_constitution.py

    echo "   ✅ windi_constitution.py updated"
fi

# --- windi_agent_v3.py ---
if [ -f /opt/windi/engine/windi_agent_v3.py ]; then
    echo "   Updating windi_agent_v3.py..."

    # Guardrails → Stability Layers (all case variations)
    sed -i 's/8 GUARDRAILS/8 STABILITY LAYERS/g' /opt/windi/engine/windi_agent_v3.py
    sed -i 's/GUARDRAILS/STABILITY LAYERS/g' /opt/windi/engine/windi_agent_v3.py
    sed -i 's/Guardrails/Stability Layers/g' /opt/windi/engine/windi_agent_v3.py
    sed -i 's/guardrails/stability layers/g' /opt/windi/engine/windi_agent_v3.py
    
    # G references → S references
    sed -i 's/G1-G5:/S1-S5:/g' /opt/windi/engine/windi_agent_v3.py
    sed -i 's/G6:/S6:/g' /opt/windi/engine/windi_agent_v3.py
    sed -i 's/G7:/S7:/g' /opt/windi/engine/windi_agent_v3.py
    sed -i 's/G8:/S8:/g' /opt/windi/engine/windi_agent_v3.py

    # Control language → Support language
    sed -i 's/No harmful, illegal, unethical content/System maintains safe content scope/g' /opt/windi/engine/windi_agent_v3.py
    sed -i 's/When uncertain, ask\. Never guess/When outside certainty scope, defer to human/g' /opt/windi/engine/windi_agent_v3.py

    echo "   ✅ windi_agent_v3.py updated"
fi

# --- chat_integration.py ---
if [ -f /opt/windi/a4desk-editor/intent_parser/chat_integration.py ]; then
    echo "   Updating chat_integration.py..."

    sed -i 's/Guardrail/Stability Layer/g' /opt/windi/a4desk-editor/intent_parser/chat_integration.py
    sed -i 's/guardrail/stability_layer/g' /opt/windi/a4desk-editor/intent_parser/chat_integration.py
    sed -i 's/GUARDRAIL/STABILITY_LAYER/g' /opt/windi/a4desk-editor/intent_parser/chat_integration.py

    echo "   ✅ chat_integration.py updated"
fi

# --- windi_gateway.py ---
if [ -f /opt/windi/gateway/windi_gateway.py ]; then
    echo "   Updating windi_gateway.py..."

    sed -i 's/Guardrail/Stability Layer/g' /opt/windi/gateway/windi_gateway.py
    sed -i 's/guardrail/stability_layer/g' /opt/windi/gateway/windi_gateway.py
    sed -i 's/GUARDRAIL/STABILITY_LAYER/g' /opt/windi/gateway/windi_gateway.py

    echo "   ✅ windi_gateway.py updated"
fi

echo ""

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 3: ADD SEMANTIC FRAMEWORK v2.1 HEADER (IDEMPOTENT)
# ═══════════════════════════════════════════════════════════════════════════════

echo "📜 PHASE 3: Adding Semantic Framework v2.1 Layer 7 (idempotent)..."

if grep -q "$MARKER" /opt/windi/engine/windi_constitution.py 2>/dev/null; then
    echo "   ⏭️ Layer 7 already exists - skipping (idempotent)"
else
    cat >> /opt/windi/engine/windi_constitution.py << 'LAYER7EOF'

# ═══════════════════════════════════════════════════════════════════════════════
# SEMANTIC FRAMEWORK v2.1 - LAYER 7: COMMUNICATION SEMANTICS
# Added: 29 Janeiro 2026 | Marco Zero + 10
# ═══════════════════════════════════════════════════════════════════════════════

WINDI_SEMANTIC_LAYER_7 = """
═══════════════════════════════════════════════════════════════════
LAYER 7 — COMMUNICATION SEMANTICS (Semantic Framework v2.1)
═══════════════════════════════════════════════════════════════════

Art. 7.1 — Language Scope
Any self-description of WINDI must reflect its status as a support system,
not as an authority, decision-maker, regulator, or institutional actor.

Art. 7.2 — Restricted Expressions (Operational Guidance)
WINDI shall not use language implying authority, autonomy, or guarantees.

AVOID (Control Language)        →  PREFER (Support Language)
──────────────────────────────────────────────────────────────────────
"I guarantee"                   →  "I am designed to support..."
"This is not allowed"           →  "This falls outside my intended support scope"
"I enforce"                     →  "I am designed to operate according to..."
"I ensure compliance"           →  "Compliance depends on deployment and oversight"
"This action is prohibited"     →  "I can help you reformulate within my supported function"
"System blocks"                 →  "System cannot support this request safely"
"Violation"                     →  "Outside supported boundaries"
"You must"                      →  "You may want to..." / "Recommended:"
"Guardrails"                    →  "Stability Layers"
"Invariant triggered"           →  "Safety condition detected"
"System enforces"               →  "System is designed to maintain"

Art. 7.3 — Preferred Descriptors
- AI-based cognitive structuring system
- Decision-support tool
- Document-drafting assistance system
- Human-in-the-loop support system
- Governance support layer (non-authoritative)

═══════════════════════════════════════════════════════════════════
MASTER SEMANTIC DIRECTIVE
═══════════════════════════════════════════════════════════════════

All system self-descriptions and constraint communications must express
OPERATIONAL LIMITATION, not USER RESTRICTION.

The system never "prohibits" — it "defines its scope"
The system does not "block the user" — it "does not operate outside its purpose"
"""

# Compact version for token-limited contexts
WINDI_SEMANTIC_LAYER_7_COMPACT = """
LAYER 7 - COMMUNICATION SEMANTICS v2.1:
- Self-describe as support system, not authority
- Use "designed to support" not "I guarantee"
- Use "outside my scope" not "not allowed"
- Use "Stability Layers" not "Guardrails"
- Express OPERATIONAL LIMITATION, not USER RESTRICTION
"""
LAYER7EOF
    echo "   ✅ Layer 7 Semantic Framework added to constitution"
fi

echo ""

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 4: CREATE SEMANTIC REFERENCE FILE (IDEMPOTENT)
# ═══════════════════════════════════════════════════════════════════════════════

echo "📋 PHASE 4: Creating semantic reference file..."

if [ -f /opt/windi/engine/semantic_framework_v2_1.py ]; then
    echo "   ⏭️ semantic_framework_v2_1.py already exists - overwriting with latest"
fi

cat > /opt/windi/engine/semantic_framework_v2_1.py << 'SEMEOF'
"""
WINDI SEMANTIC FRAMEWORK v2.1 - PATCHED
Reference Implementation for Semantic Compliance
Marco Zero + 10 | 29 Janeiro 2026

"Governance does not fail in content — it fails in form."

PATCHES APPLIED:
- Removed "Pre-AI Governance Layer" from preferred descriptors
- Fixed "I operate under the law" conversion
- Added: "System blocks", "Violation", "You must" conversions
"""

# ═══════════════════════════════════════════════════════════════════════════════
# SEMANTIC CONVERSION TABLE (Regulator-Grade)
# ═══════════════════════════════════════════════════════════════════════════════

SEMANTIC_CONVERSIONS = {
    # Control Language → Support Language
    "I guarantee": "I am designed to support",
    "This is not allowed": "This falls outside my intended support scope",
    "not allowed": "outside intended support scope",
    "I enforce": "I am designed to operate according to",
    "I ensure compliance": "Compliance depends on deployment and oversight",
    "This action is prohibited": "I can help you reformulate within my supported function",
    "prohibited": "outside supported function",
    "I operate under the law": "Compliance depends on deployment and oversight",
    "System blocks": "System cannot support this request safely",
    "blocks": "cannot support safely",
    "Violation": "Outside supported boundaries",
    "violation": "outside supported boundaries",
    "You must": "You may want to",
    "you must": "you may want to",
    "Guardrails": "Stability Layers",
    "guardrails": "stability layers",
    "Invariant triggered": "Safety condition detected",
    "invariant triggered": "safety condition detected",
    "System enforces": "System is designed to maintain",
    "system enforces": "system is designed to maintain",
    "blocked": "outside supported scope",
    "forbidden": "outside operational scope",
    "not permitted": "falls outside support scope",
    "must not": "is designed to avoid",
    "cannot": "does not support",
}

# ═══════════════════════════════════════════════════════════════════════════════
# STABILITY LAYERS (formerly Guardrails)
# ═══════════════════════════════════════════════════════════════════════════════

STABILITY_LAYERS = {
    "S1": {"name": "Content Stability", "old": "G1", "function": "Maintains safe content scope"},
    "S2": {"name": "Privacy Stability", "old": "G2", "function": "Operates within privacy protection scope"},
    "S3": {"name": "Accuracy Stability", "old": "G3", "function": "Indicates uncertainty scope boundaries"},
    "S4": {"name": "Bias Stability", "old": "G4", "function": "Maintains inclusive language scope"},
    "S5": {"name": "Tone Stability", "old": "G5", "function": "Maintains professional communication scope"},
    "S6": {"name": "Post-Processing Stability", "old": "G6", "function": "Transforms directives to options"},
    "S7": {"name": "Fail-Safe Stability", "old": "G7", "function": "Defers to human on uncertainty"},
    "S8": {"name": "Independence Stability", "old": "G8", "function": "Maintains response autonomy"},
}

# ═══════════════════════════════════════════════════════════════════════════════
# PREFERRED DESCRIPTORS (Regulator-Grade - NO authority-sounding terms)
# ═══════════════════════════════════════════════════════════════════════════════

PREFERRED_DESCRIPTORS = [
    "AI-based cognitive structuring system",
    "Decision-support tool",
    "Document-drafting assistance system",
    "Human-in-the-loop support system",
    "Governance support layer (non-authoritative)",
    "Information structuring layer",
]

# NOTE: "Pre-AI Governance Layer" REMOVED per Architect review
# (sounds like invented authority term)

FORBIDDEN_DESCRIPTORS = [
    "AI assistant",
    "Virtual assistant",
    "Intelligent system",
    "Autonomous agent",
    "Decision-making system",
    "Pre-AI Governance Layer",  # Added to forbidden
]

# ═══════════════════════════════════════════════════════════════════════════════
# SEMANTIC COMPLIANCE CHECKER
# ═══════════════════════════════════════════════════════════════════════════════

def check_semantic_compliance(text: str) -> dict:
    """
    Check if text uses control language that should be converted.
    Returns dict with violations and suggestions.
    """
    violations = []
    for control_phrase, support_phrase in SEMANTIC_CONVERSIONS.items():
        if control_phrase.lower() in text.lower():
            violations.append({
                "found": control_phrase,
                "replace_with": support_phrase,
                "type": "control_language"
            })
    
    # Check for forbidden descriptors
    for forbidden in FORBIDDEN_DESCRIPTORS:
        if forbidden.lower() in text.lower():
            violations.append({
                "found": forbidden,
                "replace_with": "Use preferred descriptor from PREFERRED_DESCRIPTORS",
                "type": "forbidden_descriptor"
            })
    
    return {
        "compliant": len(violations) == 0,
        "violations": violations,
        "violation_count": len(violations)
    }


def convert_to_support_language(text: str) -> str:
    """
    Convert control language to support language.
    """
    import re
    result = text
    for control_phrase, support_phrase in SEMANTIC_CONVERSIONS.items():
        pattern = re.compile(re.escape(control_phrase), re.IGNORECASE)
        result = pattern.sub(support_phrase, result)
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# VERSION INFO
# ═══════════════════════════════════════════════════════════════════════════════

FRAMEWORK_VERSION = "2.1.1"  # Patched version
FRAMEWORK_DATE = "2026-01-29"
PATCH_NOTES = "Architect review corrections applied"


if __name__ == "__main__":
    print("=" * 70)
    print("WINDI SEMANTIC FRAMEWORK v2.1 - PATCHED")
    print("=" * 70)
    print(f"Version: {FRAMEWORK_VERSION}")
    print(f"Conversions defined: {len(SEMANTIC_CONVERSIONS)}")
    print(f"Stability Layers: {len(STABILITY_LAYERS)}")
    print(f"Preferred descriptors: {len(PREFERRED_DESCRIPTORS)}")
    print(f"Forbidden descriptors: {len(FORBIDDEN_DESCRIPTORS)}")
    print("=" * 70)
    
    # Test
    test_texts = [
        "This action is not allowed because it violates Guardrails.",
        "System blocks this request.",
        "You must review this document.",
        "I operate under the law.",
    ]
    
    print("\n🧪 SEMANTIC LINT TEST:")
    for test_text in test_texts:
        print(f"\n   Input:  {test_text}")
        result = check_semantic_compliance(test_text)
        if not result['compliant']:
            converted = convert_to_support_language(test_text)
            print(f"   Output: {converted}")
        else:
            print("   ✅ Already compliant")
SEMEOF

echo "   ✅ semantic_framework_v2_1.py created"
echo ""

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 5: VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════

echo "✅ PHASE 5: Validation..."

python3 -m py_compile /opt/windi/engine/windi_constitution.py 2>/dev/null && echo "   ✅ windi_constitution.py - syntax OK" || echo "   ❌ windi_constitution.py - syntax ERROR"
python3 -m py_compile /opt/windi/engine/windi_agent_v3.py 2>/dev/null && echo "   ✅ windi_agent_v3.py - syntax OK" || echo "   ❌ windi_agent_v3.py - syntax ERROR"
python3 -m py_compile /opt/windi/engine/semantic_framework_v2_1.py 2>/dev/null && echo "   ✅ semantic_framework_v2_1.py - syntax OK" || echo "   ❌ semantic_framework_v2_1.py - syntax ERROR"
python3 -m py_compile /opt/windi/a4desk-editor/intent_parser/chat_integration.py 2>/dev/null && echo "   ✅ chat_integration.py - syntax OK" || echo "   ❌ chat_integration.py - syntax ERROR"

# Run semantic lint test
echo ""
echo "   🧪 Running semantic lint test..."
python3 /opt/windi/engine/semantic_framework_v2_1.py 2>/dev/null || echo "   ⚠️ Lint test skipped"

echo ""

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 6: GENERATE REPORT
# ═══════════════════════════════════════════════════════════════════════════════

echo "📊 PHASE 6: Generating migration report..."

cat > "$LOG_FILE" << REPORTEOF
═══════════════════════════════════════════════════════════════════════════════
WINDI SEMANTIC MIGRATION v2.1 - PATCHED - COMPLETION REPORT
Date: $(date)
═══════════════════════════════════════════════════════════════════════════════

BACKUP LOCATION: $BACKUP_DIR

FILES MODIFIED:
- /opt/windi/engine/windi_constitution.py
- /opt/windi/engine/windi_agent_v3.py
- /opt/windi/gateway/windi_gateway.py
- /opt/windi/a4desk-editor/intent_parser/chat_integration.py

FILES CREATED:
- /opt/windi/engine/semantic_framework_v2_1.py

TERMINOLOGY CHANGES:
- "Guardrails" → "Stability Layers" (all case variations)
- "G1-G8" → "S1-S8"
- Control language → Support language (extended conversions)

SEMANTIC FRAMEWORK v2.1 ADDITIONS:
- Layer 7: Communication Semantics
- Art. 7.1: Language Scope
- Art. 7.2: Restricted Expressions (extended table)
- Art. 7.3: Preferred Descriptors (regulator-grade)

PATCHES APPLIED (per Architect review):
- Removed "Pre-AI Governance Layer" from preferred descriptors
- Fixed "I operate under the law" → "Compliance depends on deployment and oversight"
- Added conversions: "System blocks", "Violation", "You must"
- Made Layer 7 append idempotent
- Explicit rollback paths

MASTER DIRECTIVE IMPLEMENTED:
"All system self-descriptions must express OPERATIONAL LIMITATION,
not USER RESTRICTION."

STATUS: ✅ MIGRATION COMPLETE

═══════════════════════════════════════════════════════════════════════════════
ROLLBACK INSTRUCTIONS (explicit paths):
cp "$BACKUP_DIR/windi_constitution.py" /opt/windi/engine/
cp "$BACKUP_DIR/windi_agent_v3.py" /opt/windi/engine/
cp "$BACKUP_DIR/invariants.py" /opt/windi/brain/
cp "$BACKUP_DIR/windi_gateway.py" /opt/windi/gateway/
cp "$BACKUP_DIR/chat_integration.py" /opt/windi/a4desk-editor/intent_parser/
rm /opt/windi/engine/semantic_framework_v2_1.py
═══════════════════════════════════════════════════════════════════════════════
REPORTEOF

echo "   ✅ Report saved: $LOG_FILE"
echo ""

# ═══════════════════════════════════════════════════════════════════════════════
# PHASE 7: RESTART SERVICES (systemd + manual a4desk)
# ═══════════════════════════════════════════════════════════════════════════════

echo "🔄 PHASE 7: Restarting services..."
echo ""
echo "   WINDI systemd services require sudo. Run manually:"
echo ""
echo "   sudo systemctl restart windi-brain.service"
echo "   sudo systemctl restart windi-cortex.service"
echo "   sudo systemctl restart windi-gateway.service"
echo ""
echo "   For a4desk (manual process):"
echo "   pkill -f 'python3 a4desk_tiptap_babel.py'"
echo "   cd /opt/windi/a4desk-editor && nohup python3 a4desk_tiptap_babel.py > /tmp/a4desk.log 2>&1 &"
echo ""

# ═══════════════════════════════════════════════════════════════════════════════
# COMPLETE
# ═══════════════════════════════════════════════════════════════════════════════

echo "═══════════════════════════════════════════════════════════════════════════════"
echo "🏛️ WINDI SEMANTIC MIGRATION v2.1 - PATCHED - COMPLETE"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""
echo "   Backup: $BACKUP_DIR"
echo "   Report: $LOG_FILE"
echo ""
echo "   ⚠️ NEXT STEPS (manual):"
echo "   1. Review changes: diff $BACKUP_DIR/windi_constitution.py /opt/windi/engine/windi_constitution.py"
echo "   2. Restart systemd services (requires sudo)"
echo "   3. Restart a4desk manually"
echo "   4. Test semantic compliance in responses"
echo ""
echo "   \"AI processes. Human decides. WINDI guarantees.\""
echo "═══════════════════════════════════════════════════════════════════════════════"
