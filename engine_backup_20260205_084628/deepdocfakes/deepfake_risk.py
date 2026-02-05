"""
WINDI DeepDOCFakes — Deepfake Risk Scoring
=============================================
Computes a deepfake resilience score (0-100) for documents.

Higher score = harder to forge convincingly.

Score components (Guardian model):
    Governance level base     HIGH=40, MEDIUM=25, LOW=10
    Forensic ledger           +15 (HIGH only)
    Identity governance       +10 (MEDIUM/HIGH with active identity)
    Structural hash strict    +10
    Provenance chain          +10
    Four-eyes principle       +5 (HIGH only)
    Tamper evidence           +5 (HIGH only)
    Jurisdiction binding      +5

Feature-based bonuses (Architect model):
    provenance_record required  +15
    registry presence           +10
    embed_pdf_metadata          +5

The two models are harmonised: the base scoring uses
the Guardian model; feature flags provide additional bonuses
for production configuration verification.
"""

from typing import Any, Dict


def compute_resilience_score(
    governance_level: str,
    features: Dict[str, Any]
) -> int:
    """
    Compute deepfake resilience score for a document.
    
    Args:
        governance_level: HIGH, MEDIUM, or LOW
        features: Dict of active security features, e.g.:
            {
                "provenance_record": "required" | "optional",
                "registry": True/False,
                "structural_hash": "strict" | "basic",
                "embed_pdf_metadata": True/False,
                "tamper_evidence": True/False,
                "identity_governance": True/False,
                "forensic_ledger": True/False,
                "four_eyes": True/False,
                "jurisdiction_bound": True/False,
            }
    
    Returns:
        Score 0-100 (higher = more resilient to forgery)
    """
    score = 0
    level = governance_level.upper()
    
    # ─── Base score by governance level ───
    level_scores = {"HIGH": 40, "MEDIUM": 25, "LOW": 10}
    score += level_scores.get(level, 5)
    
    # ─── Security feature bonuses ───
    
    # Forensic ledger (HIGH)
    if features.get("forensic_ledger", level == "HIGH"):
        score += 15
    
    # Four-eyes principle (HIGH)
    if features.get("four_eyes", level == "HIGH"):
        score += 5
    
    # Tamper evidence (HIGH)
    if features.get("tamper_evidence", level == "HIGH"):
        score += 5
    
    # Identity governance (MEDIUM/HIGH with active identity)
    if features.get("identity_governance", False):
        score += 10
    
    # Structural hash
    if features.get("structural_hash") == "strict":
        score += 10
    elif features.get("structural_hash"):
        score += 5
    
    # Provenance chain (always present if record exists)
    if features.get("provenance_record") in ("required", "optional", True):
        score += 5
    
    # Jurisdiction binding
    if features.get("jurisdiction_bound", True):
        score += 5
    
    # PDF metadata embedding
    if features.get("embed_pdf_metadata", False):
        score += 5
    
    return min(100, score)


def resilience_rating(score: int) -> str:
    """Convert numeric score to human-readable rating."""
    if score >= 85:
        return "MAXIMUM — Forensic-grade provenance"
    elif score >= 60:
        return "HIGH — Strong institutional provenance"
    elif score >= 40:
        return "MEDIUM — Standard provenance with identity controls"
    elif score >= 20:
        return "LOW — Basic provenance"
    else:
        return "MINIMAL — Limited provenance markers"


def resilience_factors(
    governance_level: str,
    features: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Return detailed scoring breakdown for audit purposes.
    
    Each factor shows: active (bool), points (int), description (str).
    """
    level = governance_level.upper()
    factors = {}
    
    # Base level
    base = {"HIGH": 40, "MEDIUM": 25, "LOW": 10}.get(level, 5)
    factors["governance_level"] = {
        "value": level,
        "points": base,
        "description": f"Base score for {level} governance level"
    }
    
    # Forensic ledger
    active = features.get("forensic_ledger", level == "HIGH")
    factors["forensic_ledger"] = {
        "active": active,
        "points": 15 if active else 0,
        "description": "Cryptographic forensic ledger with chain of custody"
    }
    
    # Four-eyes
    active = features.get("four_eyes", level == "HIGH")
    factors["four_eyes_principle"] = {
        "active": active,
        "points": 5 if active else 0,
        "description": "Dual-control verification before document sealing"
    }
    
    # Tamper evidence
    active = features.get("tamper_evidence", level == "HIGH")
    factors["tamper_evidence"] = {
        "active": active,
        "points": 5 if active else 0,
        "description": "Cryptographic tamper detection markers"
    }
    
    # Identity governance
    active = features.get("identity_governance", False)
    factors["identity_governance"] = {
        "active": active,
        "points": 10 if active else 0,
        "description": "Institutional identity controlled via license framework"
    }
    
    # Structural hash
    hash_mode = features.get("structural_hash", "")
    factors["structural_hash"] = {
        "active": bool(hash_mode),
        "mode": hash_mode,
        "points": 10 if hash_mode == "strict" else (5 if hash_mode else 0),
        "description": "Canonical structural fingerprint of governance decision"
    }
    
    # Provenance chain
    prov = features.get("provenance_record", "")
    factors["provenance_chain"] = {
        "active": prov in ("required", "optional", True),
        "mode": prov,
        "points": 5 if prov in ("required", "optional", True) else 0,
        "description": "Provenance record with hash chain"
    }
    
    # Jurisdiction
    active = features.get("jurisdiction_bound", True)
    factors["jurisdiction_bound"] = {
        "active": active,
        "jurisdiction": "DE — Federal Republic of Germany",
        "points": 5 if active else 0,
        "description": "Processing bound to German jurisdiction infrastructure"
    }
    
    # PDF metadata
    active = features.get("embed_pdf_metadata", False)
    factors["pdf_metadata"] = {
        "active": active,
        "points": 5 if active else 0,
        "description": "Provenance embedded in PDF XMP/custom metadata"
    }
    
    return factors
