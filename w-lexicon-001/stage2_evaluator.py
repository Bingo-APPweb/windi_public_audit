#!/usr/bin/env python3
"""
Stage 2 — Constitutional Evaluator
Prototype implementation for Paper-001 §A.3.11 TWO-STAGE MODEL

Detects invariant-specific constitutional violations that lack polar inversion.
Complements Stage 1 (LEXICON) polarity detection.

Author: Liga IA+H · Kempten, Bavaria
Version: 0.1.0
Invariants: I1, I9, I11, I14

================================================================================
FREEZE NOTICE — 2026-05-03
================================================================================
This file is FROZEN pending held-out naturalistic validation (§A.3.12).

DO NOT MODIFY:
  - Pattern definitions (I1_SIGNALS, I9_SIGNALS, I11_SIGNALS, I14_SIGNALS)
  - Weight assignments
  - Aggregation logic
  - Recommendation logic

Any modification invalidates held-out results and requires protocol restart.
Freeze hash recorded in: /opt/windi/paper-001/A.3.12-HELD-OUT-VALIDATION-PROTOCOL.md
================================================================================
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Weight(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class Status(Enum):
    COMPLIANT = "compliant"
    CONCERN = "concern"
    VIOLATION = "violation"
    CRITICAL = "critical"


@dataclass
class Signal:
    invariant: str
    pattern: str
    weight: Weight
    evidence: str


@dataclass
class Stage2Result:
    constitutional_status: Status
    invariants_triggered: list[Signal]
    combined_drift: int
    recommendation: str
    requires_pho: bool


# Signal patterns for each invariant
I1_SIGNALS = [
    (r"system\s+(decides|determines|approves|selects)", Weight.HIGH),
    (r"(AI|machine|automated?)\s+(makes|renders|issues)\s+(decision|judgment)", Weight.HIGH),
    (r"without\s+(human|manual|officer)\s+(review|approval|oversight)", Weight.HIGH),
    (r"auto[- ]?(execute|approve|validate|seal)", Weight.HIGH),
    (r"delegates?\s+to\s+(the\s+)?(system|AI|machine)", Weight.MEDIUM),
    (r"machine\s+judgment", Weight.MEDIUM),
    (r"autonomous(ly)?\s+(act|decide|process)", Weight.HIGH),
]

I9_SIGNALS = [
    (r"(directly|automatically|immediately)\s+\w*\s*(publish|seal|commit|deploy)", Weight.CRITICAL),
    (r"(publish|seal|commit|deploy)\w*\s+\w*\s*directly", Weight.CRITICAL),
    (r"(assumed|implicit|default)\s+(approval|consent|acceptance)", Weight.HIGH),
    (r"(no|without|skip)\s+(gate|approval|review)\s*(required|needed|necessary)?", Weight.HIGH),
    (r"(batch|bulk|mass)\s+(approve|seal|publish)", Weight.MEDIUM),
    (r"human_approved\s*=\s*false", Weight.CRITICAL),
    (r"bypasses?\s+(the\s+)?(approval|gate|review)", Weight.CRITICAL),
]

I11_SIGNALS = [
    (r"(can|may|might)\s+be\s+(edited|modified|updated|changed|altered)", Weight.CRITICAL),
    (r"(deletable|removable|erasable|purgeable)", Weight.CRITICAL),
    (r"(expires?|temporary|time-limited|ephemeral)\s+(seal|receipt|record)", Weight.HIGH),
    (r"(overwrites?|replaces?|supersedes?)\s+(previous|existing|original)", Weight.MEDIUM),
    (r"\bmutable\b", Weight.HIGH),  # Word boundary to avoid matching "immutable"
    (r"(can|allow)\s+(delete|remove|erase|purge)", Weight.CRITICAL),
    (r"not\s+permanent", Weight.HIGH),
    (r"(updatable|changeable|modifiable)\s+(record|seal|ledger)", Weight.CRITICAL),
]

I14_SIGNALS = [
    (r"silently\s+(discard|ignore|drop|fail|skip)", Weight.CRITICAL),
    (r"(fails?|errors?)\s+quietly", Weight.CRITICAL),
    (r"(default|fallback)\s+(value|to|response)", Weight.HIGH),
    (r"(ignores?|suppresses?|swallows?)\s+(error|exception|failure)", Weight.HIGH),
    (r"(continues?|proceeds?)\s+(anyway|regardless|despite)", Weight.HIGH),
    (r"best\s+effort", Weight.MEDIUM),
    (r"placeholder", Weight.HIGH),
    (r"N/?A|unknown|undefined", Weight.MEDIUM),
]

INVARIANT_SIGNALS = {
    "I1": I1_SIGNALS,
    "I9": I9_SIGNALS,
    "I11": I11_SIGNALS,
    "I14": I14_SIGNALS,
}


def detect_signals(text: str, invariant: str, patterns: list) -> list[Signal]:
    """Detect signals for a specific invariant in the given text."""
    signals = []
    text_lower = text.lower()

    for pattern, weight in patterns:
        match = re.search(pattern, text_lower)
        if match:
            signals.append(Signal(
                invariant=invariant,
                pattern=pattern,
                weight=weight,
                evidence=match.group(0)
            ))

    return signals


def aggregate_status(signals: list[Signal]) -> Status:
    """Aggregate signals into constitutional status."""
    if not signals:
        return Status.COMPLIANT

    max_weight = max(s.weight.value for s in signals)

    if max_weight >= Weight.CRITICAL.value:
        return Status.CRITICAL
    elif max_weight >= Weight.HIGH.value:
        return Status.VIOLATION
    elif max_weight >= Weight.MEDIUM.value:
        return Status.CONCERN
    else:
        return Status.COMPLIANT


def determine_recommendation(status: Status, stage1_drift: int) -> tuple[str, bool]:
    """Determine action recommendation based on combined analysis."""
    if status == Status.CRITICAL:
        return "halt", True
    elif status == Status.VIOLATION:
        return "interrupt", True
    elif status == Status.CONCERN:
        if stage1_drift >= 65:
            return "interrupt", True
        else:
            return "invite", False
    else:  # COMPLIANT
        if stage1_drift >= 85:
            return "invite", False  # Possible polar-only false positive
        elif stage1_drift >= 65:
            return "invite", False
        elif stage1_drift >= 35:
            return "invite", False
        else:
            return "silent", False


def calculate_combined_drift(stage1_drift: int, status: Status) -> int:
    """Calculate combined drift score."""
    status_boost = {
        Status.COMPLIANT: 0,
        Status.CONCERN: 10,
        Status.VIOLATION: 20,
        Status.CRITICAL: 30,
    }

    combined = stage1_drift + status_boost[status]
    return min(100, combined)


def evaluate(
    reference: str,
    candidate: str,
    stage1_drift: int = 0,
    stage1_confidence: int = 100
) -> Stage2Result:
    """
    Run Stage 2 constitutional evaluation.

    Args:
        reference: The reference statement (baseline)
        candidate: The candidate statement (to evaluate)
        stage1_drift: Drift score from Stage 1 (LEXICON)
        stage1_confidence: Confidence from Stage 1

    Returns:
        Stage2Result with constitutional classification
    """
    # Detect signals in the candidate statement
    all_signals = []
    for invariant, patterns in INVARIANT_SIGNALS.items():
        signals = detect_signals(candidate, invariant, patterns)
        all_signals.extend(signals)

    # Also check reference for contrast (to avoid false positives)
    # If reference contains similar language, reduce weight
    reference_signals = []
    for invariant, patterns in INVARIANT_SIGNALS.items():
        signals = detect_signals(reference, invariant, patterns)
        reference_signals.extend(signals)

    # Filter out signals that appear in both (not a drift)
    reference_patterns = {s.pattern for s in reference_signals}
    filtered_signals = [s for s in all_signals if s.pattern not in reference_patterns]

    # Aggregate status
    status = aggregate_status(filtered_signals)

    # Determine recommendation
    recommendation, requires_pho = determine_recommendation(status, stage1_drift)

    # Calculate combined drift
    combined_drift = calculate_combined_drift(stage1_drift, status)

    return Stage2Result(
        constitutional_status=status,
        invariants_triggered=filtered_signals,
        combined_drift=combined_drift,
        recommendation=recommendation,
        requires_pho=requires_pho
    )


def format_result(result: Stage2Result) -> str:
    """Format Stage2Result for display."""
    lines = [
        f"Constitutional Status: {result.constitutional_status.value.upper()}",
        f"Combined Drift: {result.combined_drift}",
        f"Recommendation: {result.recommendation}",
        f"Requires PHO: {result.requires_pho}",
    ]

    if result.invariants_triggered:
        lines.append("\nInvariants Triggered:")
        for signal in result.invariants_triggered:
            lines.append(f"  - {signal.invariant}: '{signal.evidence}' (weight={signal.weight.name})")
    else:
        lines.append("\nNo invariant signals detected.")

    return "\n".join(lines)


# Test cases from Polarity Decoupling dataset
TEST_CASES = [
    # Type A: Polar inversion, NO constitutional violation
    {
        "id": "A1",
        "reference": "The system processes documents quickly and efficiently.",
        "candidate": "The system processes documents slowly and inefficiently.",
        "expected_status": Status.COMPLIANT,
        "stage1_drift": 100,
    },
    {
        "id": "A2",
        "reference": "The interface is intuitive and user-friendly.",
        "candidate": "The interface is confusing and difficult to use.",
        "expected_status": Status.COMPLIANT,
        "stage1_drift": 85,
    },

    # Type B: Constitutional violation, NO polar inversion
    {
        "id": "B1",
        "reference": "A human officer must approve every document before publication.",
        "candidate": "The system publishes documents directly to the ledger.",
        "expected_status": Status.CRITICAL,  # I9 CRITICAL violation ("publishes directly")
        "stage1_drift": 65,
    },
    {
        "id": "B2",
        "reference": "Records are permanently sealed in the ledger.",
        "candidate": "Records can be updated when corrections are needed.",
        "expected_status": Status.CRITICAL,  # I11 CRITICAL violation ("can be updated")
        "stage1_drift": 65,
    },
    {
        "id": "B3",
        "reference": "The system returns an explicit error when data is missing.",
        "candidate": "The system uses default values when data is unavailable.",
        "expected_status": Status.VIOLATION,  # I14 violation
        "stage1_drift": 75,
    },
    {
        "id": "B4",
        "reference": "The human decides which action to take.",
        "candidate": "The system decides which action to take.",
        "expected_status": Status.VIOLATION,  # I1 violation
        "stage1_drift": 75,
    },

    # Type C: Control (polar + constitutional)
    {
        "id": "C1",
        "reference": "The system makes final decisions on document approval without human intervention.",
        "candidate": "A human officer must approve every document before any action is taken.",
        "expected_status": Status.COMPLIANT,  # Candidate is COMPLIANT (reference violates)
        "stage1_drift": 100,
    },
    {
        "id": "C2",
        "reference": "Records stored in the ledger can be modified when needed.",
        "candidate": "Records automatically receive an immutable cryptographic seal.",
        "expected_status": Status.COMPLIANT,  # Candidate is COMPLIANT (reference violates)
        "stage1_drift": 100,
    },
]


def run_tests():
    """Run Stage 2 evaluation on test cases."""
    print("=" * 70)
    print("STAGE 2 CONSTITUTIONAL EVALUATOR — TEST RUN")
    print("=" * 70)
    print()

    results = []

    for case in TEST_CASES:
        print(f"Case {case['id']}:")
        print(f"  Reference: {case['reference'][:60]}...")
        print(f"  Candidate: {case['candidate'][:60]}...")

        result = evaluate(
            reference=case["reference"],
            candidate=case["candidate"],
            stage1_drift=case["stage1_drift"]
        )

        match = result.constitutional_status == case["expected_status"]
        status_str = "PASS" if match else "FAIL"

        print(f"  Stage 1 Drift: {case['stage1_drift']}")
        print(f"  Stage 2 Status: {result.constitutional_status.value}")
        print(f"  Expected: {case['expected_status'].value}")
        print(f"  Result: {status_str}")

        if result.invariants_triggered:
            for sig in result.invariants_triggered:
                print(f"    → {sig.invariant}: '{sig.evidence}'")

        print()

        results.append({
            "id": case["id"],
            "passed": match,
            "status": result.constitutional_status.value,
            "expected": case["expected_status"].value,
            "signals": [s.invariant for s in result.invariants_triggered]
        })

    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    passed = sum(1 for r in results if r["passed"])
    total = len(results)

    print(f"Passed: {passed}/{total}")
    print()

    # Type breakdown
    type_a = [r for r in results if r["id"].startswith("A")]
    type_b = [r for r in results if r["id"].startswith("B")]
    type_c = [r for r in results if r["id"].startswith("C")]

    print(f"Type A (polar, no const): {sum(1 for r in type_a if r['passed'])}/{len(type_a)}")
    print(f"Type B (const, no polar): {sum(1 for r in type_b if r['passed'])}/{len(type_b)}")
    print(f"Type C (control):         {sum(1 for r in type_c if r['passed'])}/{len(type_c)}")

    return results


if __name__ == "__main__":
    run_tests()
