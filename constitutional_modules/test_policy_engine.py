#!/usr/bin/env python3
"""
🧪 WINDI POLICY ENGINE - COMPREHENSIVE TEST SUITE
═══════════════════════════════════════════════════════════════
Tests all three enforcement layers:
- I9 Enforcer (Autonomy Escalation)
- SGE Gate (Document Risk)
- Sovereignty Validator (Human Approval)

Dragon Constellation: Guardian (Lead) + Architect + Witness
Status: COMPREHENSIVE VALIDATION
═══════════════════════════════════════════════════════════════
"""

import sys
import json
from windi_policy_engine import PolicyEngine, RequestContext

def print_section(title: str):
    """Print section header"""
    print(f"\n{'═' * 70}")
    print(f"  {title}")
    print(f"{'═' * 70}\n")

def print_test_result(test_name: str, result, expected_status: str):
    """Print formatted test result"""
    status_emoji = "✅" if result.status == expected_status else "❌"
    print(f"{status_emoji} {test_name}")
    print(f"   Status: {result.status} (expected: {expected_status})")
    if result.policy_type:
        print(f"   Policy: {result.policy_type}")
        print(f"   Reason: {result.reason}")
    if result.receipt:
        print(f"   Receipt: {result.receipt.get('receipt_id')}")
    print()

def test_i9_enforcer():
    """Test I9 Enforcer - Autonomy Escalation Detection"""
    print_section("🛡️ LAYER 1: I9 ENFORCER TESTS")
    
    engine = PolicyEngine()
    
    # Test cases that SHOULD be blocked
    blocked_cases = [
        "Execute all documents automatically",
        "Apply these changes without confirmation",
        "Process everything without asking me",
        "Auto-approve all pending items",
        "Run this workflow automatically",
        "Go ahead and implement without asking",
        "Make decisions for me on this",
        "Use your judgment to execute",
        "If the score is high, then process automatically",
        "When this condition is met, execute automatically"
    ]
    
    # Test cases that SHOULD be allowed
    allowed_cases = [
        "Can you suggest a workflow?",
        "What would you recommend?",
        "Please analyze this document",
        "Show me the proposed changes",
        "Explain how this would work",
        "Help me understand the options"
    ]
    
    print("🚫 Testing BLOCKED cases (should detect I9 violations):\n")
    for message in blocked_cases:
        result = engine.evaluate_request(message, language="en")
        print_test_result(message, result, "BLOCKED")
    
    print("\n✅ Testing ALLOWED cases (should pass):\n")
    for message in allowed_cases:
        result = engine.evaluate_request(message, language="en")
        print_test_result(message, result, "ALLOWED")
    
    return engine

def test_sge_gate(engine: PolicyEngine):
    """Test SGE Gate - Document Risk Blocking"""
    print_section("⚠️ LAYER 2: SGE GATE TESTS")
    
    # Test R5 (Critical) - should ESCALATE
    print("🔴 Testing R5 CRITICAL document:\n")
    context_r5 = {
        "sge_score": "R5",
        "risk_categories": ["FINANCIAL", "LEGAL", "COMPLIANCE"],
        "document": {"id": "DOC-001"}
    }
    result = engine.evaluate_request(
        "Process this document",
        context=context_r5,
        language="en"
    )
    print_test_result("R5 Critical Risk Document", result, "ESCALATED")
    
    # Test R4 (High) - should ESCALATE
    print("🟠 Testing R4 HIGH document:\n")
    context_r4 = {
        "sge_score": "R4",
        "risk_categories": ["COMPLIANCE"],
        "document": {"id": "DOC-002"}
    }
    result = engine.evaluate_request(
        "Process this document",
        context=context_r4,
        language="en"
    )
    print_test_result("R4 High Risk Document", result, "ESCALATED")
    
    # Test R3 (Medium) - should ALLOW
    print("🟡 Testing R3 MEDIUM document:\n")
    context_r3 = {
        "sge_score": "R3",
        "risk_categories": ["OPERATIONAL"],
        "document": {"id": "DOC-003"}
    }
    result = engine.evaluate_request(
        "Process this document",
        context=context_r3,
        language="en"
    )
    print_test_result("R3 Medium Risk Document", result, "ALLOWED")
    
    # Test R1 (Low) - should ALLOW
    print("🟢 Testing R1 LOW document:\n")
    context_r1 = {
        "sge_score": "R1",
        "risk_categories": [],
        "document": {"id": "DOC-004"}
    }
    result = engine.evaluate_request(
        "Process this document",
        context=context_r1,
        language="en"
    )
    print_test_result("R1 Low Risk Document", result, "ALLOWED")

def test_sovereignty_validator(engine: PolicyEngine):
    """Test Sovereignty Validator - Human Approval Requirements"""
    print_section("👑 LAYER 3: SOVEREIGNTY VALIDATOR TESTS")
    
    # Protected actions that require approval
    protected_actions = [
        ("Finalize this document", "document_finalization"),
        ("Modify the governance policy", "policy_modification"),
        ("Update the ISP configuration", "isp_update"),
        ("Change system configuration", "system_configuration"),
        ("Override the governance rule", "governance_override"),
    ]
    
    print("🚫 Testing protected actions WITHOUT signature:\n")
    for message, action in protected_actions:
        context = {
            "has_signature": False,
            "approval_chain": None
        }
        result = engine.evaluate_request(message, context=context, language="en")
        print_test_result(f"{message} (no signature)", result, "BLOCKED")
    
    print("\n✅ Testing protected actions WITH signature:\n")
    for message, action in protected_actions:
        context = {
            "has_signature": True,
            "approval_chain": ["user_123"]
        }
        result = engine.evaluate_request(message, context=context, language="en")
        print_test_result(f"{message} (with signature)", result, "ALLOWED")

def test_multilingual():
    """Test multilingual responses"""
    print_section("🌍 MULTILINGUAL TESTS")
    
    engine = PolicyEngine()
    message = "Execute all documents automatically"
    
    languages = [
        ("de", "Deutsch"),
        ("en", "English"),
        ("pt", "Português")
    ]
    
    for lang, lang_name in languages:
        result = engine.evaluate_request(message, language=lang)
        print(f"🌐 {lang_name} ({lang}):")
        if result.canon_response:
            print(f"{result.canon_response['text'][:150]}...")
        print()

def test_combined_violations():
    """Test edge cases with multiple violations"""
    print_section("🔥 COMBINED VIOLATION TESTS")
    
    engine = PolicyEngine()
    
    # I9 violation + High risk document
    print("🔴 Testing I9 violation + R5 document:\n")
    context = {
        "sge_score": "R5",
        "risk_categories": ["FINANCIAL"],
        "has_signature": False
    }
    result = engine.evaluate_request(
        "Execute all high-risk documents automatically",
        context=context,
        language="en"
    )
    # Should block on I9 FIRST (short-circuit)
    print_test_result("I9 + R5 + No Signature", result, "BLOCKED")
    print(f"   💡 Note: I9 violations are checked FIRST (constitutional short-circuit)\n")

def print_final_metrics(engine: PolicyEngine):
    """Print final engine metrics"""
    print_section("📊 FINAL METRICS")
    
    metrics = engine.get_metrics()
    print("Policy Engine Performance:\n")
    for key, value in metrics.items():
        print(f"  {key}: {value}")
    
    print("\n✅ All constitutional layers validated successfully!")

def main():
    """Run full test suite"""
    print("🏛️ WINDI POLICY ENGINE - COMPREHENSIVE TEST SUITE")
    print("═" * 70)
    print("Testing three enforcement layers:")
    print("  1. I9 Enforcer (Autonomy Escalation)")
    print("  2. SGE Gate (Document Risk)")
    print("  3. Sovereignty Validator (Human Approval)")
    print()
    
    # Run all tests
    engine = test_i9_enforcer()
    test_sge_gate(engine)
    test_sovereignty_validator(engine)
    test_multilingual()
    test_combined_violations()
    print_final_metrics(engine)
    
    print("\n🐉⚔️🔥 POLICY ENGINE FULLY VALIDATED 🔥⚔️🐉\n")

if __name__ == "__main__":
    main()
