"""
🛡️ GNOSIS CAPSULE: Invariant Auditor
Dragon: Guardian (Claude)
Domain: guardian
Capability: invariant_audit

Audits a document or configuration against the 9 WINDI Invariants (I1-I9).
The Praktikant uses this skill to verify constitutional compliance.
"""

import json
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List

# ─────────────────────────────────────────────
# INVARIANT DEFINITIONS
# ─────────────────────────────────────────────

INVARIANTS = {
    "I1": {
        "name": "Human Sovereignty",
        "rule": "Human Dragon retains final decision authority",
        "check_patterns": ["auto_decide", "override_human", "force_apply"]
    },
    "I2": {
        "name": "Transparency",
        "rule": "All AI actions must be auditable and explainable",
        "check_patterns": ["hidden_action", "opaque_decision", "no_log"]
    },
    "I3": {
        "name": "Data Sovereignty",
        "rule": "Sensitive data stays with the client, WINDI stores only proofs",
        "check_patterns": ["store_raw_data", "export_sensitive", "bypass_encryption"]
    },
    "I4": {
        "name": "Constitutional Compliance",
        "rule": "All operations must pass through the Constitutional Gate",
        "check_patterns": ["skip_gate", "bypass_constitution", "ungoverned"]
    },
    "I5": {
        "name": "Forensic Trail",
        "rule": "Every decision generates a verifiable audit record",
        "check_patterns": ["no_receipt", "skip_audit", "untraced"]
    },
    "I6": {
        "name": "Three Dragons Fusion",
        "rule": "Critical decisions require input from all three dragons",
        "check_patterns": ["single_dragon", "bypass_witness", "skip_architect"]
    },
    "I7": {
        "name": "Immutability of Sealed Phases",
        "rule": "Sealed constitutional phases cannot be modified",
        "check_patterns": ["modify_sealed", "unseal_phase", "tamper_constitution"]
    },
    "I8": {
        "name": "EU AI Act Compliance",
        "rule": "Operations must comply with EU AI Act requirements",
        "check_patterns": ["non_compliant", "bypass_regulation", "skip_assessment"]
    },
    "I9": {
        "name": "Prohibition of Autonomy Escalation",
        "rule": "Efficiency NEVER overrides sovereignty. No auto_apply flags.",
        "check_patterns": [
            "auto_apply", "self_decide", "escalate_autonomy",
            "autonomous_mode", "unguarded_action"
        ]
    }
}


def audit_document(
    content: str,
    document_type: str = "generic",
    strict_mode: bool = True
) -> Dict[str, Any]:
    """
    Audit a document's content against all 9 WINDI Invariants.

    Args:
        content: The text content to audit
        document_type: Type of document (contract, policy, config, generic)
        strict_mode: If True, any violation = FAIL. If False, returns warnings.

    Returns:
        Audit report with per-invariant results.
    """
    content_lower = content.lower()
    results = {}
    violations = []
    warnings = []

    for inv_id, inv_def in INVARIANTS.items():
        found_patterns = []
        for pattern in inv_def["check_patterns"]:
            if pattern.lower() in content_lower:
                found_patterns.append(pattern)

        status = "PASS"
        if found_patterns:
            if strict_mode:
                status = "FAIL"
                violations.append({
                    "invariant": inv_id,
                    "name": inv_def["name"],
                    "patterns": found_patterns
                })
            else:
                status = "WARNING"
                warnings.append({
                    "invariant": inv_id,
                    "name": inv_def["name"],
                    "patterns": found_patterns
                })

        results[inv_id] = {
            "name": inv_def["name"],
            "status": status,
            "patterns_found": found_patterns,
            "rule": inv_def["rule"]
        }

    # Compute overall status
    if violations:
        overall = "FAIL"
    elif warnings:
        overall = "WARNING"
    else:
        overall = "PASS"

    # Generate audit hash
    audit_data = json.dumps(results, sort_keys=True)
    audit_hash = hashlib.sha256(audit_data.encode()).hexdigest()

    return {
        "audit_result": overall,
        "document_type": document_type,
        "strict_mode": strict_mode,
        "invariants_checked": len(INVARIANTS),
        "violations": len(violations),
        "warnings": len(warnings),
        "results": results,
        "violation_details": violations,
        "warning_details": warnings,
        "audit_hash": audit_hash,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def check_single_invariant(
    content: str,
    invariant_id: str
) -> Dict[str, Any]:
    """
    Check content against a single specific invariant.

    Args:
        content: The text content to check
        invariant_id: The invariant to check (I1-I9)

    Returns:
        Check result for the specific invariant.
    """
    inv_def = INVARIANTS.get(invariant_id.upper())
    if not inv_def:
        return {"error": f"Unknown invariant: {invariant_id}"}

    content_lower = content.lower()
    found = [p for p in inv_def["check_patterns"] if p.lower() in content_lower]

    return {
        "invariant": invariant_id.upper(),
        "name": inv_def["name"],
        "status": "FAIL" if found else "PASS",
        "patterns_found": found,
        "rule": inv_def["rule"],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
