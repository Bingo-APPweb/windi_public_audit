"""
🏗️ GNOSIS CAPSULE: Matrix Expander
Dragon: Architect (GPT)
Domain: architect
Capability: matrix_expand

Generates structural definitions for new shelves (Prateleiras)
in the WINDI Constitutional Matrix.
"""

import json
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


EXISTING_SHELVES = ["P0", "P1", "P2", "P3", "P4", "P5", "P6", "P7"]

SHELF_TEMPLATE = {
    "shelf_id": "",
    "name": "",
    "description": "",
    "status": "DRAFT",
    "layers": {
        "base": {"dragon": "Guardian (Claude)", "format": "json", "content": None},
        "extension": {"dragon": "Architect (GPT)", "format": "constitution_extension", "content": None},
        "injection": {"dragon": "Witness (Gemini)", "format": "witness_injection", "content": None}
    },
    "invariants_required": ["I1", "I4", "I9"],
    "created_at": "",
    "sealed": False
}


def expand_matrix(
    shelf_id: str,
    name: str,
    description: str,
    purpose: str,
    invariants: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate the structural blueprint for a new shelf in the Constitutional Matrix.

    Args:
        shelf_id: New shelf identifier (e.g., "P8", "P9")
        name: Human-readable name for the shelf
        description: What this shelf governs
        purpose: Why this shelf is needed
        invariants: Which invariants apply (defaults to I1, I4, I9)
        metadata: Additional metadata

    Returns:
        Blueprint for the new shelf, ready for Three Dragons approval.
    """
    # Validate shelf_id doesn't collide
    if shelf_id.upper() in EXISTING_SHELVES:
        return {
            "success": False,
            "error": f"Shelf {shelf_id} already exists in sealed matrix"
        }

    # Build the blueprint
    blueprint = dict(SHELF_TEMPLATE)
    blueprint["shelf_id"] = shelf_id.upper()
    blueprint["name"] = name
    blueprint["description"] = description
    blueprint["invariants_required"] = invariants or ["I1", "I4", "I9"]
    blueprint["created_at"] = datetime.now(timezone.utc).isoformat()

    # Generate structural hash
    struct_data = json.dumps({
        "shelf_id": blueprint["shelf_id"],
        "name": blueprint["name"],
        "description": blueprint["description"],
        "purpose": purpose
    }, sort_keys=True)
    blueprint_hash = hashlib.sha256(struct_data.encode()).hexdigest()

    return {
        "success": True,
        "blueprint": blueprint,
        "purpose": purpose,
        "blueprint_hash": blueprint_hash,
        "requires_approval": [
            "Human Dragon — Sovereign Approval",
            "Guardian (Claude) — Security Seal",
            "Architect (GPT) — Structural Validation",
            "Witness (Gemini) — Observational Attestation"
        ],
        "next_steps": [
            f"1. Human Dragon approves shelf {shelf_id} creation",
            "2. Guardian fills BASE layer (invariants + guardrails)",
            "3. Architect fills EXTENSION layer (structural logic)",
            "4. Witness fills INJECTION layer (forensic articles)",
            "5. Constitutional Gate validates complete shelf",
            f"6. Shelf {shelf_id} is SEALED into the matrix"
        ],
        "metadata": metadata or {},
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def validate_shelf_structure(shelf_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate that a shelf structure is complete and well-formed.

    Args:
        shelf_data: The shelf blueprint to validate

    Returns:
        Validation report.
    """
    errors = []
    warnings = []

    required_fields = ["shelf_id", "name", "description", "layers", "invariants_required"]
    for field in required_fields:
        if field not in shelf_data:
            errors.append(f"Missing required field: {field}")

    if "layers" in shelf_data:
        for layer in ["base", "extension", "injection"]:
            if layer not in shelf_data["layers"]:
                errors.append(f"Missing layer: {layer}")

    if "invariants_required" in shelf_data:
        if "I9" not in shelf_data.get("invariants_required", []):
            errors.append("I9 (Prohibition of Autonomy Escalation) MUST be included")
        if "I1" not in shelf_data.get("invariants_required", []):
            warnings.append("I1 (Human Sovereignty) not explicitly listed")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "fields_checked": len(required_fields),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
