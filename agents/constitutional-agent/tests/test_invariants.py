"""
WINDI Agent Test Suite
========================
Tests constitutional invariants, especially I9 (Autonomy Prohibition).
Every test that tries to escalate authority MUST fail.

"Efficiency NEVER overrides sovereignty."
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.invariants import InvariantEnforcer, I9Violation, InvariantViolation
from core.constitutional_gate import ConstitutionalGate
from core.manifest import AgentManifest
from monitors.canonical_compliance import CanonicalComplianceMonitor
from orchestration.proof_orchestrator import ProofOrchestrator
from config import OperationalMode


class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def ok(self, name):
        self.passed += 1
        print(f"  ✅ {name}")
    
    def fail(self, name, reason=""):
        self.failed += 1
        self.errors.append(f"{name}: {reason}")
        print(f"  ❌ {name} — {reason}")
    
    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'═' * 50}")
        print(f"  Results: {self.passed}/{total} passed")
        if self.failed > 0:
            print(f"  FAILURES: {self.failed}")
            for e in self.errors:
                print(f"    • {e}")
        else:
            print("  ALL TESTS PASSED ✅")
        print(f"{'═' * 50}")
        return self.failed == 0


def run_tests():
    results = TestResults()
    
    print("🐉 WINDI Agent Test Suite")
    print("=" * 50)
    
    # ═══ I9 TESTS (Most critical) ═══
    print("\n▸ I9 — Prohibition of Autonomy Escalation")
    
    enforcer = InvariantEnforcer()
    
    # Test: auto_apply must be blocked
    try:
        enforcer.check_operation("process_document", {"auto_apply": True})
        results.fail("I9: auto_apply blocked", "Should have raised I9Violation")
    except I9Violation:
        results.ok("I9: auto_apply blocked")
    except Exception as e:
        results.fail("I9: auto_apply blocked", str(e))
    
    # Test: auto_approve must be blocked
    try:
        enforcer.check_operation("auto_approve_submission", {})
        results.fail("I9: auto_approve blocked", "Should have raised I9Violation")
    except I9Violation:
        results.ok("I9: auto_approve blocked")
    
    # Test: skip_human must be blocked
    try:
        enforcer.check_operation("submit", {"skip_human": True})
        results.fail("I9: skip_human blocked", "Should have raised I9Violation")
    except I9Violation:
        results.ok("I9: skip_human blocked")
    
    # Test: bypass_review must be blocked
    try:
        enforcer.check_operation("bypass_review_and_submit", {})
        results.fail("I9: bypass_review blocked", "Should have raised I9Violation")
    except I9Violation:
        results.ok("I9: bypass_review blocked")
    
    # Test: disable_invariant must be blocked
    try:
        enforcer.check_operation("disable_invariant_i9", {})
        results.fail("I9: disable_invariant blocked", "Should have raised I9Violation")
    except I9Violation:
        results.ok("I9: disable_invariant blocked")
    
    # Test: agent_decides must be blocked
    try:
        enforcer.check_operation("process", {"agent_decides": True})
        results.fail("I9: agent_decides blocked", "Should have raised I9Violation")
    except I9Violation:
        results.ok("I9: agent_decides blocked")
    
    # Test: normal operation must pass
    try:
        result = enforcer.check_operation("analyze_document", {"document_hash": "abc123"})
        if result.passed:
            results.ok("I9: normal analysis passes")
        else:
            results.fail("I9: normal analysis passes", "Should have passed")
    except Exception as e:
        results.fail("I9: normal analysis passes", str(e))
    
    # ═══ HUMAN SOVEREIGNTY TESTS ═══
    print("\n▸ I1-I3 — Human Sovereignty")
    
    # Test: approve without human_initiated must fail
    try:
        enforcer.check_operation("approve_document", {})
        results.fail("I1: approve needs human_initiated", "Should block")
    except InvariantViolation:
        results.ok("I1: approve needs human_initiated")
    
    # Test: approve with human_initiated must pass
    try:
        result = enforcer.check_operation("approve_document", {"human_initiated": True})
        if result.passed:
            results.ok("I1: approve with human_initiated passes")
        else:
            results.fail("I1: approve with human_initiated passes", "Should pass")
    except Exception as e:
        results.fail("I1: approve with human_initiated passes", str(e))
    
    # ═══ ZERO-KNOWLEDGE TESTS ═══
    print("\n▸ I4/I7 — Zero Knowledge Architecture")
    
    # Test: transmitting content must fail
    try:
        enforcer.check_operation("send_to_hub", {"transmit_content": True})
        results.fail("I4: content transmission blocked", "Should block")
    except InvariantViolation:
        results.ok("I4: content transmission blocked")
    
    # Test: storing content on hub must fail
    try:
        enforcer.check_operation("store_proof", {"store_content_on_hub": True})
        results.fail("I7: hub content storage blocked", "Should block")
    except InvariantViolation:
        results.ok("I7: hub content storage blocked")
    
    # ═══ TRANSPARENCY TESTS ═══
    print("\n▸ I5 — Transparency")
    
    # Test: silent operations must fail
    try:
        enforcer.check_operation("process_document", {"silent": True})
        results.fail("I5: silent operations blocked", "Should block")
    except InvariantViolation:
        results.ok("I5: silent operations blocked")
    
    # ═══ CONSTITUTIONAL GATE TESTS ═══
    print("\n▸ Constitutional Gate")
    
    gate = ConstitutionalGate(agent_version="1.0.0", model_version="test")
    
    # Test: gate generates commitment
    try:
        commitment = gate.validate("analyze_document", {"test": True})
        if commitment.invariants_checked and commitment.operation == "analyze_document":
            results.ok("Gate: generates Decision Trace Commitment")
        else:
            results.fail("Gate: generates Decision Trace Commitment", "Invalid commitment")
    except Exception as e:
        results.fail("Gate: generates Decision Trace Commitment", str(e))
    
    # Test: gate blocks I9 violations
    try:
        gate.validate("auto_approve_all", {})
        results.fail("Gate: blocks I9 at gate level", "Should block")
    except I9Violation:
        results.ok("Gate: blocks I9 at gate level")
    
    # ═══ MANIFEST TESTS ═══
    print("\n▸ Agent Manifest")
    
    manifest = AgentManifest(node_id="W-TEST-001", activated_by="test")
    
    # Test: all invariants loaded
    if manifest.verify_invariants_complete():
        results.ok("Manifest: all 9 invariants loaded")
    else:
        results.fail("Manifest: all 9 invariants loaded")
    
    # Test: config hash is deterministic
    hash1 = manifest.config_hash()
    hash2 = manifest.config_hash()
    if hash1 == hash2:
        results.ok("Manifest: config hash is deterministic")
    else:
        results.fail("Manifest: config hash is deterministic")
    
    # Test: removing I9 fails verification
    manifest_bad = AgentManifest(node_id="W-TEST-002")
    manifest_bad.invariants_loaded = ["I1", "I2", "I3"]  # Missing I9!
    if not manifest_bad.verify_invariants_complete():
        results.ok("Manifest: incomplete invariants detected")
    else:
        results.fail("Manifest: incomplete invariants detected", "Should fail without I9")
    
    # ═══ COMPLIANCE MONITOR TESTS ═══
    print("\n▸ Canonical Compliance Monitor")
    
    monitor = CanonicalComplianceMonitor(node_id="W-TEST-001")
    
    # Test: compliant config passes
    good_config = {
        "invariants": ["I1", "I2", "I3", "I4", "I5", "I6", "I7", "I8", "I9"],
        "sge_layers": 6,
        "proof_version": "WINDI-RECEIPT-v1",
        "receipt_fields": ["hash", "categories", "governance", "decision", "timestamp"],
        "agent_role": "constitutional_executor",
        "agent_decision_authority": False,
        "hub_stores_content": False,
        "human_gate_enabled": True,
    }
    report = monitor.run_full_scan(good_config)
    if report["overall_status"] == "compliant":
        results.ok("CCM: compliant config scores 100%")
    else:
        results.fail("CCM: compliant config scores 100%", f"Got: {report['overall_status']}")
    
    # Test: agent with decision authority fails
    bad_config = good_config.copy()
    bad_config["agent_decision_authority"] = True
    report = monitor.run_full_scan(bad_config)
    if report["overall_status"] == "critical":
        results.ok("CCM: decision authority detected as critical")
    else:
        results.fail("CCM: decision authority detected as critical", f"Got: {report['overall_status']}")
    
    # ═══ PROOF ORCHESTRATOR TESTS ═══
    print("\n▸ Proof Orchestrator")
    
    orch = ProofOrchestrator(node_id="W-TEST-001")
    
    # Test: receipt is prepared as pending
    receipt = orch.prepare_receipt(
        document_hash="abc123",
        doc_type="CONTRACT",
        impact_level="HIGH",
        risk_level="R3",
        sge_score=0.65,
    )
    if receipt.decision["action"] == "pending_human_decision":
        results.ok("Orchestrator: receipt prepared as pending_human_decision")
    else:
        results.fail("Orchestrator: receipt prepared as pending_human_decision")
    
    # Test: receipt can be finalized with human decision
    orch.finalize_receipt(receipt, action="approved", role="Controller")
    if receipt.decision["action"] == "approved":
        results.ok("Orchestrator: receipt finalized with human decision")
    else:
        results.fail("Orchestrator: receipt finalized with human decision")
    
    # Test: escalation creates pending item
    esc = orch.escalate_to_human(
        reason="High risk detected",
        context={"hash": "xyz"},
        risk_level="R4",
    )
    if not esc.resolved and len(orch.pending_escalations) > 0:
        results.ok("Orchestrator: escalation created as pending")
    else:
        results.fail("Orchestrator: escalation created as pending")
    
    # ═══ INTEGRITY REPORT ═══
    print("\n▸ Integrity Report")
    
    report = enforcer.get_integrity_report()
    if report["i9_violations"] > 0:
        results.ok(f"Integrity: {report['i9_violations']} I9 violations correctly detected")
    else:
        results.fail("Integrity: I9 violations should have been detected")
    
    # ═══ SUMMARY ═══
    return results.summary()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
