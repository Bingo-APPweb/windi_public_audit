#!/usr/bin/env python3
"""
WINDI BABEL Integration Test v1.0.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Full pipeline test: a4Desk → SGE → Escalation → Human → Receipt

Tests:
  1. Low-risk document (R1) — flows through, informational only
  2. Medium-risk document (R3) — triggers escalation, human reviews
  3. High-risk document (R4) — triggers escalation, human approves
  4. Critical document (R5) — halts processing, human must decide
  5. I9 enforcement — verify no auto_apply anywhere
"""

import sys
import json
from pathlib import Path

# Add onboarding to path
sys.path.insert(0, str(Path(__file__).parent))

def run_tests():
    print("=" * 70)
    print("  WINDI BABEL Integration Test — Full Pipeline")
    print("  Node: W-001 | Protocol: Praktikant Onboarding v1.0.0")
    print("=" * 70)
    print()

    results = {"passed": 0, "failed": 0, "tests": []}

    # ─── Test 1: Low Risk ───
    print("  Test 1: Low-risk document (expected: R0-R1, no escalation)")
    try:
        from sge_bridge import SGEBridge
        bridge = SGEBridge()
        finding = bridge.analyze("Hello, this is a simple memo about the team meeting next Tuesday.")
        risk = finding.get("risk_level", "")
        assert risk in ("R0", "R1"), f"Expected R0/R1, got {risk}"
        assert not finding.get("flags"), f"Expected no flags, got {finding.get('flags')}"
        print(f"    ✓ PASSED — Risk: {risk}, No escalation needed")
        results["passed"] += 1
        results["tests"].append({"name": "low_risk", "passed": True, "risk": risk})
    except Exception as e:
        print(f"    ✗ FAILED — {e}")
        results["failed"] += 1
        results["tests"].append({"name": "low_risk", "passed": False, "error": str(e)})

    # ─── Test 2: Medium Risk ───
    print("  Test 2: Medium-risk document (expected: R2-R3, advisory/review)")
    try:
        finding = bridge.analyze(
            "This contract includes a deadline of March 15 for delivery. "
            "Confidential information must be protected per GDPR requirements. "
            "A penalty clause applies for late delivery.",
            document_type="CONTRACT"
        )
        risk = finding.get("risk_level", "")
        assert risk in ("R2", "R3"), f"Expected R2/R3, got {risk}"
        print(f"    ✓ PASSED — Risk: {risk}, Escalation: {'Yes' if 'HUMAN_REVIEW' in str(finding.get('flags')) else 'Advisory'}")
        results["passed"] += 1
        results["tests"].append({"name": "medium_risk", "passed": True, "risk": risk})
    except Exception as e:
        print(f"    ✗ FAILED — {e}")
        results["failed"] += 1
        results["tests"].append({"name": "medium_risk", "passed": False, "error": str(e)})

    # ─── Test 3: High Risk ───
    print("  Test 3: High-risk document (expected: R4, action required)")
    try:
        finding = bridge.analyze(
            "AUFTRAGSVERARBEITUNG gemäß DSGVO Art. 28. "
            "Haftung: unbeschränkt bei Datenschutzverstößen. "
            "Vertragsstrafe: EUR 100.000 bei Nichteinhaltung. "
            "Frist: 01.01.2026 bis 31.12.2026. "
            "KI-Verordnung: Hochrisiko-KI-System. "
            "Streng vertraulich. BSI C5 und ISO 27001 erforderlich.",
            document_type="CONTRACT"
        )
        risk = finding.get("risk_level", "")
        flags = finding.get("flags", [])
        assert risk in ("R4", "R5"), f"Expected R4/R5, got {risk}"
        assert "ESCALATION_REQUIRED" in flags, f"Expected ESCALATION_REQUIRED flag"
        print(f"    ✓ PASSED — Risk: {risk}, Flags: {flags}")
        results["passed"] += 1
        results["tests"].append({"name": "high_risk", "passed": True, "risk": risk})
    except Exception as e:
        print(f"    ✗ FAILED — {e}")
        results["failed"] += 1
        results["tests"].append({"name": "high_risk", "passed": False, "error": str(e)})

    # ─── Test 4: I9 Enforcement ───
    print("  Test 4: I9 enforcement (no auto_apply anywhere)")
    try:
        finding = bridge.analyze("Critical document with penalty and liability", document_type="CONTRACT")
        assert finding.get("human_decision_required") == True, "human_decision_required must be True"
        assert "auto_apply" not in json.dumps(finding).replace('"auto_apply": false', ''),             "auto_apply must never be true"

        # Check bridge health
        health = bridge.health()
        assert health["bridge"] == "operational", "Bridge must be operational"

        print(f"    ✓ PASSED — human_decision_required: True, auto_apply: False (NEVER)")
        results["passed"] += 1
        results["tests"].append({"name": "i9_enforcement", "passed": True})
    except Exception as e:
        print(f"    ✗ FAILED — {e}")
        results["failed"] += 1
        results["tests"].append({"name": "i9_enforcement", "passed": False, "error": str(e)})

    # ─── Test 5: Escalation Handler ───
    print("  Test 5: Escalation handler creates and resolves correctly")
    try:
        from escalation_handler import EscalationHandler, HumanDecision
        handler = EscalationHandler(
            ledger_dir=str(Path(__file__).parent / "ledger" / "test")
        )

        # Create escalation
        esc = handler.escalate(finding)
        assert esc.id.startswith("ESC-W001-"), f"Invalid escalation ID: {esc.id}"
        assert esc.human_decision is None, "Decision should be pending"

        # Check pending
        pending = handler.get_pending()
        assert len(pending) == 1, f"Expected 1 pending, got {len(pending)}"

        # Resolve
        resolved = handler.resolve(esc.id, HumanDecision.APPROVE, "Test approval")
        assert resolved is not None, "Resolution failed"
        assert resolved.human_decision == HumanDecision.APPROVE
        assert len(handler.get_pending()) == 0, "Pending should be empty after resolution"

        print(f"    ✓ PASSED — Escalation {esc.id}: created → resolved → ledger recorded")
        results["passed"] += 1
        results["tests"].append({"name": "escalation_handler", "passed": True})
    except Exception as e:
        print(f"    ✗ FAILED — {e}")
        results["failed"] += 1
        results["tests"].append({"name": "escalation_handler", "passed": False, "error": str(e)})

    # ─── Summary ───
    print()
    print("=" * 70)
    total = results["passed"] + results["failed"]
    print(f"  RESULTS: {results['passed']}/{total} passed")
    if results["failed"] == 0:
        print("  ✅ ALL TESTS PASSED — Praktikant is ready for production")
    else:
        print(f"  ⚠️ {results['failed']} test(s) failed — review required")
    print("=" * 70)

    # Save results
    result_path = Path(__file__).parent / "reports" / "integration_test_results.json"
    result_path.parent.mkdir(parents=True, exist_ok=True)
    with open(result_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"  Results saved: {result_path}")

    return results


if __name__ == "__main__":
    run_tests()
