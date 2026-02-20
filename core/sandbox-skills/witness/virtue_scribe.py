"""
👁️ GNOSIS CAPSULE: Virtue Scribe
Dragon: Witness (Gemini)
Domain: witness
Capability: virtue_scribe

Generates WINDI Virtue Receipts — cryptographic proofs of governance
decisions that follow the Zero-Knowledge Architecture.

"Cliente guarda dados, WINDI guarda PROVA de virtude."
"""

import json
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict


RISK_LEVELS = {
    "R0": {"label": "Negligible", "color": "🟢", "range": "€0 - €999"},
    "R1": {"label": "Low", "color": "🟢", "range": "€1.000 - €9.999"},
    "R2": {"label": "Medium", "color": "🟡", "range": "€10.000 - €99.999"},
    "R3": {"label": "High", "color": "🟠", "range": "€100.000 - €999.999"},
    "R4": {"label": "Critical", "color": "🔴", "range": "€1.000.000 - €9.999.999"},
    "R5": {"label": "Catastrophic", "color": "⚫", "range": "€10.000.000+"}
}


def generate_virtue_receipt(
    document_hash: str,
    document_type: str,
    impact_level: str,
    risk_level: str,
    sge_score: float,
    decision_action: str,
    decision_role: str,
    ai_recommendation: str,
    human_override: bool = False,
    flags: Optional[List[str]] = None,
    domain: str = "general",
    department_code: str = "UNSET"
) -> Dict[str, Any]:
    """
    Generate a WINDI Virtue Receipt — proof of a governance decision.

    The receipt contains NO sensitive data, only governance metadata.
    This follows the Zero-Knowledge Architecture principle:
    "Client stores data, WINDI stores PROOF of virtue."

    Args:
        document_hash: SHA-256 hash of the source document
        document_type: CONTRACT, INVOICE, APPROVAL, REPORT, etc.
        impact_level: LOW, MED, HIGH, CRIT
        risk_level: R0 through R5
        sge_score: Semantic Governance Engine score (0.0 to 1.0)
        decision_action: What action was taken (APPROVED, REJECTED, ESCALATED, etc.)
        decision_role: Who made the decision (Controller, Director, etc.)
        ai_recommendation: What the AI recommended
        human_override: Whether the human overrode the AI recommendation
        flags: Any governance flags
        domain: Business domain
        department_code: Department identifier

    Returns:
        Complete Virtue Receipt as a dictionary.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Build the receipt structure
    receipt = {
        "receipt_type": "WINDI-VIRTUE-RECEIPT",
        "version": "2.0.0",
        "receipt_id": f"WVR-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{document_hash[:8]}",

        # Document reference (hash only, NO content)
        "document": {
            "hash": document_hash,
            "type": document_type,
            "department": department_code
        },

        # Categories (ranges, NOT exact values)
        "categories": {
            "type": document_type,
            "impact": impact_level,
            "domain": domain,
            "value_range": risk_level,
            "value_range_label": RISK_LEVELS.get(risk_level, {}).get("label", "Unknown"),
            "value_range_indicator": RISK_LEVELS.get(risk_level, {}).get("range", "N/A")
        },

        # Governance assessment
        "governance": {
            "sge_score": round(sge_score, 4),
            "risk_level": risk_level,
            "risk_color": RISK_LEVELS.get(risk_level, {}).get("color", "❓"),
            "validation": "COMPLETE"
        },

        # Decision record
        "decision": {
            "action": decision_action,
            "role": decision_role,
            "timestamp": timestamp,
            "ai_recommendation": ai_recommendation,
            "human_override": human_override,
            "override_reason": "Human sovereign decision" if human_override else None
        },

        # Governance flags
        "flags": flags or [],

        # Metadata
        "metadata": {
            "generated_at": timestamp,
            "generator": "virtue_scribe_v1",
            "witness": "Witness (Gemini)",
            "protocol": "Three Dragons Protocol",
            "principle": "AI processes. Human decides. WINDI guarantees."
        }
    }

    # Generate receipt integrity hash
    receipt_data = json.dumps(receipt, sort_keys=True, ensure_ascii=False)
    receipt["integrity_hash"] = hashlib.sha256(receipt_data.encode()).hexdigest()

    return receipt


def validate_receipt(receipt: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate the integrity of an existing Virtue Receipt.

    Args:
        receipt: The receipt to validate

    Returns:
        Validation result.
    """
    stored_hash = receipt.get("integrity_hash", "")

    # Recompute hash without the integrity_hash field
    receipt_copy = dict(receipt)
    receipt_copy.pop("integrity_hash", None)
    receipt_data = json.dumps(receipt_copy, sort_keys=True, ensure_ascii=False)
    computed_hash = hashlib.sha256(receipt_data.encode()).hexdigest()

    is_valid = stored_hash == computed_hash

    return {
        "valid": is_valid,
        "receipt_id": receipt.get("receipt_id", "UNKNOWN"),
        "stored_hash": stored_hash[:16] + "..." if stored_hash else "MISSING",
        "computed_hash": computed_hash[:16] + "...",
        "status": "INTACT" if is_valid else "TAMPERED",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
