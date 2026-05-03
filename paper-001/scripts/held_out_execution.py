#!/usr/bin/env python3
"""
A.3.12 — Held-out Naturalistic Validation Execution
====================================================
ONE RUN. NO TUNING. RESULTS RECORDED.

This script executes Stage 2 v0.3.0 on the held-out dataset ONCE.
Do NOT modify stage2_evaluator.py based on these results.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add lexicon path
sys.path.insert(0, '/opt/windi/w-lexicon-001')
from stage2_evaluator import evaluate, Status

# Paths
HELD_OUT_PATH = Path('/opt/windi/paper-001/datasets/HELD-OUT-NATURALISTIC-001.json')
RESULTS_PATH = Path('/opt/windi/paper-001/datasets/HELD-OUT-RESULTS-001.json')


def load_held_out():
    with open(HELD_OUT_PATH) as f:
        return json.load(f)


def run_evaluation(cases):
    """Run Stage 2 on all cases - ONE TIME ONLY"""
    results = []

    for case in cases:
        result = evaluate(
            reference=case['reference'],
            candidate=case['candidate'],
            stage1_drift=50,  # Neutral Stage 1 for isolated Stage 2 test
            stage1_confidence=90
        )

        # Map Stage 2 status to binary prediction
        if result.constitutional_status in [Status.VIOLATION, Status.CRITICAL]:
            prediction = "violation"
        elif result.constitutional_status == Status.CONCERN:
            prediction = "concern"  # Track separately
        else:
            prediction = "compliant"

        results.append({
            "id": case['id'],
            "type": case['type'],
            "ground_truth": case['ground_truth'],
            "prediction": prediction,
            "stage2_status": result.constitutional_status.value,
            "invariants_triggered": [
                {"invariant": s.invariant, "evidence": s.evidence, "weight": s.weight.name}
                for s in result.invariants_triggered
            ],
            "combined_drift": result.combined_drift,
            "recommendation": result.recommendation
        })

    return results


def compute_metrics(results):
    """Compute accuracy, precision, recall, F1"""
    # Exclude ambiguous cases from main metrics
    clear_cases = [r for r in results if r['ground_truth'] != 'ambiguous']
    ambiguous_cases = [r for r in results if r['ground_truth'] == 'ambiguous']

    # Binary classification: violation vs compliant
    # Map concern -> compliant for binary
    def to_binary(pred):
        return "violation" if pred == "violation" else "compliant"

    tp = sum(1 for r in clear_cases if r['ground_truth'] == 'violation' and to_binary(r['prediction']) == 'violation')
    tn = sum(1 for r in clear_cases if r['ground_truth'] == 'compliant' and to_binary(r['prediction']) == 'compliant')
    fp = sum(1 for r in clear_cases if r['ground_truth'] == 'compliant' and to_binary(r['prediction']) == 'violation')
    fn = sum(1 for r in clear_cases if r['ground_truth'] == 'violation' and to_binary(r['prediction']) == 'compliant')

    n = len(clear_cases)
    accuracy = (tp + tn) / n if n > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    # Wilson confidence interval for accuracy
    import math
    z = 1.96  # 95% CI
    p = accuracy
    denominator = 1 + z**2 / n
    center = (p + z**2 / (2*n)) / denominator
    spread = z * math.sqrt((p * (1 - p) + z**2 / (4*n)) / n) / denominator
    ci_lower = max(0, center - spread)
    ci_upper = min(1, center + spread)

    return {
        "n_clear": n,
        "n_ambiguous": len(ambiguous_cases),
        "confusion_matrix": {
            "tp": tp, "tn": tn, "fp": fp, "fn": fn
        },
        "accuracy": round(accuracy, 3),
        "accuracy_ci_95": [round(ci_lower, 3), round(ci_upper, 3)],
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3)
    }


def analyze_errors(results):
    """Categorize errors for qualitative analysis"""
    errors = []

    for r in results:
        gt = r['ground_truth']
        pred = r['prediction'] if r['prediction'] == 'violation' else 'compliant'

        if gt == 'ambiguous':
            errors.append({
                "id": r['id'],
                "error_type": "ambiguous_case",
                "prediction": r['prediction'],
                "invariants": [i['invariant'] for i in r['invariants_triggered']],
                "analysis": "Edge case - no ground truth"
            })
        elif gt != pred:
            error_type = "false_negative" if gt == 'violation' else "false_positive"
            errors.append({
                "id": r['id'],
                "error_type": error_type,
                "ground_truth": gt,
                "prediction": r['prediction'],
                "invariants": [i['invariant'] for i in r['invariants_triggered']],
                "analysis": "REQUIRES MANUAL REVIEW"
            })

    return errors


def main():
    print("=" * 70)
    print("A.3.12 — HELD-OUT NATURALISTIC VALIDATION")
    print("=" * 70)
    print()

    # Load dataset
    held_out = load_held_out()
    print(f"Dataset: {held_out['dataset']}")
    print(f"N: {held_out['n']}")
    print(f"Frozen Hash: {held_out['frozen_hash'][:16]}...")
    print()

    # Verify hash
    import hashlib
    with open('/opt/windi/w-lexicon-001/stage2_evaluator.py', 'rb') as f:
        current_hash = hashlib.sha256(f.read()).hexdigest()

    hash_match = current_hash == held_out['frozen_hash']
    print(f"Hash verification: {'✓ MATCH' if hash_match else '✗ MISMATCH (INVALID RUN)'}")
    if not hash_match:
        print("ERROR: Stage 2 has been modified since freeze!")
        print(f"  Expected: {held_out['frozen_hash']}")
        print(f"  Current:  {current_hash}")
        return
    print()

    # Execute
    print("Executing Stage 2 (ONE RUN, NO TUNING)...")
    results = run_evaluation(held_out['cases'])
    print(f"Processed {len(results)} cases")
    print()

    # Compute metrics
    metrics = compute_metrics(results)

    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    print()

    # Confusion matrix
    cm = metrics['confusion_matrix']
    print("Confusion Matrix (clear cases only):")
    print(f"                 Predicted")
    print(f"              Violation  Compliant")
    print(f"  Actual")
    print(f"  Violation      {cm['tp']:2d}         {cm['fn']:2d}")
    print(f"  Compliant      {cm['fp']:2d}         {cm['tn']:2d}")
    print()

    print(f"N (clear):   {metrics['n_clear']}")
    print(f"N (ambig):   {metrics['n_ambiguous']}")
    print()
    print(f"Accuracy:    {metrics['accuracy']:.1%}  (95% CI: {metrics['accuracy_ci_95'][0]:.1%} – {metrics['accuracy_ci_95'][1]:.1%})")
    print(f"Precision:   {metrics['precision']:.1%}")
    print(f"Recall:      {metrics['recall']:.1%}")
    print(f"F1:          {metrics['f1']:.3f}")
    print()

    # Error analysis
    errors = analyze_errors(results)

    print("=" * 70)
    print("ERROR ANALYSIS")
    print("=" * 70)

    fn_errors = [e for e in errors if e['error_type'] == 'false_negative']
    fp_errors = [e for e in errors if e['error_type'] == 'false_positive']
    ambig = [e for e in errors if e['error_type'] == 'ambiguous_case']

    print(f"\nFalse Negatives (missed violations): {len(fn_errors)}")
    for e in fn_errors:
        print(f"  - {e['id']}: predicted {e['prediction']}, triggered {e['invariants']}")

    print(f"\nFalse Positives (spurious detections): {len(fp_errors)}")
    for e in fp_errors:
        print(f"  - {e['id']}: predicted {e['prediction']}, triggered {e['invariants']}")

    print(f"\nAmbiguous Cases: {len(ambig)}")
    for e in ambig:
        print(f"  - {e['id']}: predicted {e['prediction']}, triggered {e['invariants']}")

    # Save results
    output = {
        "dataset": held_out['dataset'],
        "execution_timestamp": datetime.now(timezone.utc).isoformat(),
        "frozen_hash_verified": hash_match,
        "metrics": metrics,
        "results": results,
        "errors": errors,
        "interpretation": {
            "held_in_accuracy": "8/8 (100%)",
            "held_out_accuracy": f"{metrics['accuracy']:.1%}",
            "generalization_drop": f"{1.0 - metrics['accuracy']:.1%}",
            "status": "DOCUMENTED"
        }
    }

    with open(RESULTS_PATH, 'w') as f:
        json.dump(output, f, indent=2)

    print()
    print(f"Results saved to: {RESULTS_PATH}")
    print()
    print("=" * 70)
    print("INTERPRETATION")
    print("=" * 70)
    print(f"Held-in (N=8):  100%")
    print(f"Held-out (N={metrics['n_clear']}): {metrics['accuracy']:.1%}")
    print(f"Drop: {(1.0 - metrics['accuracy']) * 100:.0f} percentage points")
    print()

    if metrics['accuracy'] < 0.75:
        print("→ Significant generalization gap detected.")
        print("→ Stage 2 detects EXPLICIT indicators, not NATURALISTIC descriptions.")
        print("→ This defines the construct boundary for the paper.")
    elif metrics['accuracy'] >= 0.90:
        print("→ Strong generalization signal.")
        print("→ Maintain caveats for small N.")
    else:
        print("→ Moderate generalization.")
        print("→ Error analysis will define construct boundaries.")


if __name__ == '__main__':
    main()
