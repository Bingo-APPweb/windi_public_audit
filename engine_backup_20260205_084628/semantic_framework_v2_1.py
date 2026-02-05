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
    "System blocks": "System cannot safely support",
    "blocks": "does not support",
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
    Process longer phrases first to avoid substring conflicts.
    """
    import re
    result = text
    # Sort by length descending to process longer phrases first
    sorted_items = sorted(SEMANTIC_CONVERSIONS.items(), key=lambda x: len(x[0]), reverse=True)
    for control_phrase, support_phrase in sorted_items:
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
